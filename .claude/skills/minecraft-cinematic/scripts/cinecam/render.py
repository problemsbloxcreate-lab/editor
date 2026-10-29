"""render: write job + camera table, run the real Minecraft client through the CineCam mod, then finish with ffmpeg.

Typical use (see SKILL.md):

    from cinecam import *
    rig = Rig(fps=30, subframes=8)
    rig.add(crane(...)); rig.add(orbit(...))
    result = render(rig, "intro", scene=Scene(commands=[...], anchor=(0, 80, 0)), size=(1920, 1080), grade="cinematic")
"""
from __future__ import annotations

import ctypes
import numpy as np
import glob
import json
import os
import shutil
import subprocess
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from .camlib import Rig
from . import post as _post
from . import dof as _dof
from . import actors as _actors

def _cine_path(which: str, legacy: str) -> str:
    """env CINECAM_* > config do usuário (minecraft-video-editor/scripts/paths.py) > pasta antiga."""
    import sys
    ed = Path(__file__).resolve().parents[3] / "minecraft-video-editor" / "scripts"
    if ed.is_dir() and str(ed) not in sys.path:
        sys.path.append(str(ed))
    try:
        import paths as _paths
        return _paths.cinecam(which) or legacy
    except ImportError:
        return os.environ.get("CINECAM_" + which.upper()) or legacy


MOD_HOME = Path(_cine_path("home", "D:/cinecam-forge-1.20.1"))
RUN_HOME = Path(_cine_path("run", "D:/cinecam-run"))
OUT_HOME = Path(_cine_path("out", "D:/cinecam-out"))


@dataclass
class World:
    mode: str = "fresh"               # fresh | copy
    seed: int = 20261015
    preset: str = "normal"            # normal | flat
    structures: bool = True
    copyFrom: Optional[str] = None    # absolute path of a save folder to copy (never opens the original)
    groundY: Optional[int] = None     # v1.1 (preset flat): grama com o topo nesta altura no mundo TODO (Shorts: 64 = chão do estúdio)


@dataclass
class Settings:
    renderDistance: int = 16
    simulationDistance: int = 8
    worldTicks: bool = True           # False = frozen world (stills / architectural shots); True = clouds, water, mobs move with film time
    gamma: float = 0.5
    mipmap: int = 4
    biomeBlend: int = 7
    clouds: bool = True
    particles: bool = True


@dataclass
class Scene:
    time: int = 6000                  # world day time (0 sunrise, 6000 noon, 12000 sunset, 18000 midnight)
    weather: str = "clear"
    dimension: str = "minecraft:overworld"   # minecraft:the_end = purple void sky, no ground (build with commands)
    anchor: Optional[Sequence[float]] = None      # where the invisible spectator sits (chunks load around it); default = first camera sample
    commands: List[str] = field(default_factory=list)
    settleTicks: int = 100
    sunScale: float = 1.0             # >1 = vanilla sun texture drawn bigger at the real sun position (silhouette shots)
    sunTint: Sequence[float] = (1.0, 0.86, 0.52)   # big-sun colour when using the vanilla texture
    sunTexture: Optional[str] = None  # RGBA PNG for the big sun (straight alpha: exact colours, e.g. warm halo)
    preloadTimeoutSec: int = 300
    fog: Optional[Sequence[float]] = None           # v1.1: [perto, longe, r, g, b] em blocos/0..1 (névoa fixa da cena)
    blocks: List = field(default_factory=list)       # v1.1: [t, x, y, z, "minecraft:oak_door[...,open=true]"] = blocos que mudam no plano


def available_ram_gb() -> float:
    class MS(ctypes.Structure):
        _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong), ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong), ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong), ("sullAvailExtendedVirtual", ctypes.c_ulonglong)]
    s = MS(); s.dwLength = ctypes.sizeof(MS)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(s))
    return s.ullAvailPhys / 2 ** 30


def free_gb(path: str) -> float:
    return shutil.disk_usage(path).free / 2 ** 30


def _java_home() -> str:
    env = _cine_path("java_home", "")
    if env:
        return env
    c = sorted(glob.glob(str(Path.home() / ".gradle/jdks/temurin17-download/jdk-17*")))
    for pf in (r"C:\Program Files\Eclipse Adoptium", r"C:\Program Files\Java", r"C:\Program Files\Microsoft",
               r"C:\Program Files\Zulu", r"C:\Program Files\Amazon Corretto"):
        c += sorted(glob.glob(pf + r"\jdk-17*")) + sorted(glob.glob(pf + r"\zulu-17*"))
    if c:
        return c[-1]
    raise RuntimeError("JDK 17 not found; set CINECAM_JAVA_HOME")


def _write_job(rig: Rig, name: str, scene: Scene, world: World, settings: Settings, size: Tuple[int, int], out_dir: Path,
               job_dir: Path, codec: str = "lossless", depth: bool = False, anim=None) -> Path:
    job_dir.mkdir(parents=True, exist_ok=True)
    rig.write_csv(str(job_dir / "camera.csv"), height=size[1])
    sc = asdict(scene)
    if sc.get("anchor") is None:
        sc.pop("anchor")
    job = {"name": name, "out": str(out_dir).replace("\\", "/"), "width": size[0], "height": size[1], "fps": rig.fps,
           "subframes": rig.subframes, "ffmpeg": shutil.which("ffmpeg") or "ffmpeg", "codec": codec, "depth": depth,
           "world": {k: v for k, v in asdict(world).items() if v is not None}, "settings": asdict(settings), "scene": sc, "camera": "camera.csv"}
    if anim is not None:
        anim.write(str(job_dir / "anim.json"), _actors.row_times(rig), rig.subframes)
        job["anim"] = "anim.json"
    p = job_dir / "job.json"
    p.write_text(json.dumps(job, indent=1), encoding="utf-8")
    return p


LAUNCH = RUN_HOME / "launch.json"


def _src_stamp() -> str:
    import hashlib
    h = hashlib.sha1()
    for f in sorted((MOD_HOME / "src").rglob("*")):
        if f.is_file():
            st = f.stat()
            h.update(f"{f.relative_to(MOD_HOME)}:{st.st_size}:{int(st.st_mtime)}".encode())
    for f in ("build.gradle", "gradle.properties"):
        if (MOD_HOME / f).exists():
            h.update((MOD_HOME / f).read_bytes())
    return h.hexdigest()


def _split_logged_cmd(line: str) -> List[str]:
    """Gradle --info logs the runClient command space-joined and unquoted: split at ' -opt' boundaries so paths with spaces
    survive; '-Dk=v', '-Xmx..', '-XX:..' are single tokens, every other option is 'opt value'."""
    import re
    body = line.split(" Command: ", 1)[1].strip()
    exe, rest = body.split(" -", 1)
    toks = [exe]
    for part in re.split(r" (?=--?[A-Za-z])", "-" + rest):
        if re.match(r"-(D|X|ea|da|server|client)", part) and not part.startswith("--"):
            toks.append(part)
        else:
            k, _, v = part.partition(" ")
            toks.append(k)
            if k in ("-cp", "-classpath") and " " in v:          # '-cp <classpath> <main class>': the main class follows the classpath
                v, main = v.rsplit(" ", 1)
                toks += [v, main]
            elif v:
                toks.append(v)
    return toks


def _clean_saves(since: float):
    """Delete the throw-away worlds this run created (saves/cinecam-*; ~20-60 MB each, 1.7 GB had piled up by 21/10/2026).
    Only folders created during THIS run (the render lock guarantees no other run is writing).  CINECAM_KEEP_SAVES=1 keeps them."""
    if os.environ.get("CINECAM_KEEP_SAVES") == "1":
        return
    for d in (RUN_HOME / "saves").glob("cinecam-*"):
        try:
            if d.is_dir() and d.stat().st_ctime >= since - 5:
                shutil.rmtree(d, ignore_errors=True)
        except OSError:
            pass


def _gradle(args: List[str], logf, env) -> subprocess.Popen:
    return subprocess.Popen([str(MOD_HOME / "gradlew.bat")] + args + ["--offline", "--console=plain"], cwd=str(MOD_HOME), env=env,
                            stdout=logf, stderr=subprocess.STDOUT)


def _sincroniza_mod():
    """PC da equipe: MOD_HOME é a cópia que o setup_cinecam fez na instalação; quando a skill atualiza (tag nova), o código do mod
    em assets/cinecam-mod muda e a cópia ficava velha (Python novo + mod velho = canais desalinhados, sem chão em todo lugar).
    Copia o que mudou — só arquivo da skill MAIS NOVO que o da cópia, então edição feita direto em MOD_HOME (PC do dono) fica."""
    src = Path(__file__).resolve().parents[2] / "assets" / "cinecam-mod"
    try:
        if not src.is_dir() or not MOD_HOME.is_dir() or src.resolve() == MOD_HOME.resolve():
            return
    except OSError:
        return
    n = 0
    for a in [*(src / "src").rglob("*"), *(src / f for f in ("build.gradle", "gradle.properties", "settings.gradle"))]:
        if not a.is_file():
            continue
        b = MOD_HOME / a.relative_to(src)
        if b.exists() and (b.stat().st_mtime >= a.stat().st_mtime or b.read_bytes() == a.read_bytes()):
            continue
        b.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(a, b)
        n += 1
    if n:
        print(f"[cinecam] código do mod atualizado pela skill ({n} arquivos): recompila agora")


def _launch(job_json: Path, mode: str, xmx: str, logf, env: Dict) -> Tuple[subprocess.Popen, bool]:
    """Start the dev client for job_json (direct java when launch.json is known; else gradle runClient).  Returns (process, direct)."""
    _sincroniza_mod()
    jarg = str(job_json).replace(chr(92), '/')
    cmd = None
    if os.environ.get("CINECAM_GRADLE") != "1" and LAUNCH.exists():
        L = json.loads(LAUNCH.read_text(encoding="utf-8"))
        stamp = _src_stamp()
        if L.get("stamp") != stamp:                     # mod changed: recompile classes only (gradle exits right after)
            if _gradle(["classes"], logf, env).wait() == 0:
                L["stamp"] = stamp
                LAUNCH.write_text(json.dumps(L, indent=1), encoding="utf-8")
            else:
                L = None
        if L:
            cmd = []
            for t in L["cmd"]:
                if t.startswith("-Dcinecam.job="): t = "-Dcinecam.job=" + jarg
                elif t.startswith("-Dcinecam.mode="): t = "-Dcinecam.mode=" + mode
                elif t.startswith("-Xmx"): t = "-Xmx" + xmx
                cmd.append(t)
            env["MOD_CLASSES"] = ";".join("cinecam%%" + str(MOD_HOME / d) for d in ("build/resources/main", "build/classes/java/main"))
    if cmd:
        return subprocess.Popen(cmd, cwd=str(RUN_HOME), env=env, stdout=logf, stderr=subprocess.STDOUT), True
    return _gradle(["runClient", "--info", f"-Pxmx={xmx}", f"-Pjob={jarg}", f"-Pmode={mode}"], logf, env), False


def _capture_launch(logname: str):
    """First gradle run: keep its java command for the next (direct) launches."""
    try:
        for line in open(logname, encoding="utf-8", errors="replace"):
            if "Starting process" in line and "-Dcinecam.job=" in line:
                LAUNCH.write_text(json.dumps({"cmd": _split_logged_cmd(line), "stamp": _src_stamp(),
                                              "captured": time.strftime("%Y-%m-%d %H:%M")}, indent=1), encoding="utf-8")
                break
    except Exception as e:
        print(f"[cinecam] could not capture the direct launch command: {e}")


def _pid_vivo(lock: Path) -> bool:
    """Lock de um processo que morreu (serviço fechado à força) não segura mais o render."""
    try:
        pid = int(lock.read_text().strip())
    except (OSError, ValueError):
        return True
    if pid == os.getpid():
        return False
    h = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)        # PROCESS_QUERY_LIMITED_INFORMATION
    if not h:
        return False
    code = ctypes.c_ulong()
    ctypes.windll.kernel32.GetExitCodeProcess(h, ctypes.byref(code))
    ctypes.windll.kernel32.CloseHandle(h)
    return code.value == 259                                             # STILL_ACTIVE


def _take_lock() -> Path:
    lock = RUN_HOME / "render.lock"
    RUN_HOME.mkdir(parents=True, exist_ok=True)
    if lock.exists() and time.time() - lock.stat().st_mtime < 3 * 3600 and _pid_vivo(lock):
        raise RuntimeError(f"another render seems to be running (lock {lock}); delete it if that is stale")
    lock.write_text(str(os.getpid()))
    return lock


def run_game(job_json: Path, mode: str = "film", xmx: str = "4G", timeout_s: int = 3600, log: Optional[Path] = None) -> int:
    """Run the dev client with the mod.  Blocks until Minecraft exits.  Only one run at a time.
    v0.8: the game is launched DIRECTLY with java (the runClient command captured once from gradle --info into
    RUN_HOME/launch.json), so no 1-2 GB gradle JVM sits alive during the render; when the mod source changed, only
    'gradlew classes' runs first.  CINECAM_GRADLE=1 forces the old gradle runClient path."""
    lock = _take_lock()
    try:
        t_start = time.time()
        env = dict(os.environ, JAVA_HOME=_java_home(), CINECAM_RUN=str(RUN_HOME))
        logf = open(log or (job_json.parent / "game.log"), "w", encoding="utf-8", errors="replace")
        p, direct = _launch(job_json, mode, xmx, logf, env)
        try:
            code = p.wait(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            _kill_tree(p.pid)
            raise RuntimeError(f"game run exceeded {timeout_s}s and was killed; see {logf.name}")
        finally:
            logf.close()
        _clean_saves(t_start)
        if not direct:
            _capture_launch(logf.name)
        return code
    finally:
        lock.unlink(missing_ok=True)


def _kill_tree(pid: int):
    subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True)


def checar_colisao(anim, rig: Rig, scene: Optional[Scene]) -> List[str]:
    """26/10 (dono: "nunca permita"): membro/item atravessando corpo, outro personagem ou bloco da cena → lista de problemas."""
    if anim is None or not getattr(anim, "actors", None):
        return []
    from .colisao import verificar, solids_from_commands
    sc = scene or Scene()
    anchor = sc.anchor
    if anchor is None:
        p = rig.sample_frames()
        anchor = (float(p["x"][0]), float(p["y"][0]), float(p["z"][0]))
    S = solids_from_commands(sc.commands, anchor) if sc.commands else None
    probs = verificar(anim, rig.duration, S, eventos=sc.blocks)
    for a in anim.actors:
        probs += [f"{t:.2f}s: {a.name}.{p1} atravessa o próprio {p2}" for (t, p1, p2) in getattr(a, "colisao_resto", [])][:3]
    return probs


def render(rig: Rig, name: str, scene: Optional[Scene] = None, world: Optional[World] = None, settings: Optional[Settings] = None,
           size: Tuple[int, int] = (1920, 1080), grade: str = "cinematic", letterbox: Optional[float] = None, supersample: int = 1,
           xmx: str = "4G", audio: Optional[str] = None, crf: int = 14, timeout_s: int = 3600, dry_run: bool = False,
           dof: Optional[bool] = None, anim=None, blur: bool = True, checar: bool = True) -> Dict:
    """Render a rig to <CINECAM_OUT>/<name>/<name>.mp4.  Returns a dict with paths and the mod's report.
    blur=False: sem motion blur (obturador 0; os subframes continuam só como anti-aliasing).  dof=False: sem desfoque de lente/
    profundidade de campo mesmo se os movimentos tiverem with_dof.  checar=True: recusa se algo atravessa corpo/bloco."""
    scene, world, settings = scene or Scene(), world or World(), settings or Settings()
    if not blur:
        rig.shutter = 0.0
    if checar:
        probs = checar_colisao(anim, rig, scene)
        if probs:
            raise ValueError("colisão (nunca permitido): " + "; ".join(probs[:8]))
    out_dir = OUT_HOME / name
    job_dir = RUN_HOME / "jobs" / name
    out_dir.mkdir(parents=True, exist_ok=True)
    W, H = size[0] * supersample, size[1] * supersample
    rows = rig.sample_rows()
    use_dof = bool((rows["focus"] > 0).any() and (rows["aperture"] > 0).any()) if dof is None else dof
    job = _write_job(rig, name, scene, world, settings, (W, H), out_dir, job_dir, depth=use_dof, anim=anim)
    info = {"job": str(job), "out_dir": str(out_dir), "frames": rig.n_frames, "rows": rig.n_frames * rig.subframes}
    if dry_run:
        return info
    ram = available_ram_gb()
    if ram < 2.5:
        print(f"[cinecam] WARNING: only {ram:.1f} GB RAM available; close other apps or expect swapping/slow render")
    if free_gb(str(RUN_HOME)) < 8:
        raise RuntimeError("less than 8 GB free on the render drive")
    t0 = time.time()
    code = run_game(job, "film", xmx, timeout_s)
    rep_path = out_dir / f"{name}_report.json"
    if not rep_path.exists():
        raise RuntimeError(f"no report written (exit {code}); see {job_dir / 'game.log'}")
    rep = json.loads(rep_path.read_text(encoding="utf-8"))
    info["report"] = rep
    info["game_seconds"] = round(time.time() - t0, 1)
    if not rep.get("ok"):
        raise RuntimeError(f"render failed: {rep.get('error')}; see {job_dir / 'game.log'}")
    master = rep["output"]
    final = str(out_dir / f"{name}.mp4")
    scale = f"{size[0]}:{size[1]}" if supersample > 1 else None
    if use_dof:
        c = np.arange(rig.n_frames) * rig.subframes + rig.subframes // 2
        dmaster = str(out_dir / f"{name}_dof.mkv")
        n = _dof.apply_dof(master, str(out_dir / f"{name}_depth.mkv"), rows["focus"][c], rows["aperture"][c], dmaster,
                           size[0], size[1], rig.fps)
        info["dof_frames"] = n
        master, scale = dmaster, None
    _post.finish(master, final, preset=grade, letterbox=letterbox, crf=crf, width=size[0], height=size[1],
                 scale=scale, audio=audio, fps=rig.fps)
    info["master"] = master
    info["final"] = final
    return info


def stills(poses: Sequence[Dict[str, float]], name: str, scene: Optional[Scene] = None, world: Optional[World] = None,
           settings: Optional[Settings] = None, size: Tuple[int, int] = (1280, 720), xmx: str = "3G", timeout_s: int = 1800,
           anim=None) -> List[str]:
    """Render single frames at the given poses (dicts with x,y,z,yaw,pitch,roll,fov) to PNG.  Fast way to scout framing."""
    scene, world, settings = scene or Scene(), world or World(), settings or Settings()
    settings = Settings(**{**asdict(settings), "worldTicks": False})
    out_dir = OUT_HOME / name
    job_dir = RUN_HOME / "jobs" / name
    job_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(job_dir / "camera.csv", "w") as f:
        f.write("t,x,y,z,yaw,pitch,roll,fov\n")
        for i, p in enumerate(poses):
            f.write(f"{i / 30:.5f},{p['x']},{p['y']},{p['z']},{p['yaw']},{p['pitch']},{p.get('roll', 0)},{p.get('fov', 70)}\n")
    sc = asdict(scene)
    if sc.get("anchor") is None:
        p0 = poses[0]
        sc["anchor"] = [p0["x"], p0["y"], p0["z"]]
    job = {"name": name, "out": str(out_dir).replace("\\", "/"), "width": size[0], "height": size[1], "fps": 30, "subframes": 1,
           "ffmpeg": shutil.which("ffmpeg") or "ffmpeg", "world": {k: v for k, v in asdict(world).items() if v is not None}, "settings": asdict(settings), "scene": sc, "camera": "camera.csv"}
    if anim is not None:   # each pose may carry "t": the animation time at which actors/water are evaluated
        anim.write(str(job_dir / "anim.json"), np.array([float(p.get("t", 0.0)) for p in poses]), 1)
        job["anim"] = "anim.json"
    jp = job_dir / "job.json"
    jp.write_text(json.dumps(job, indent=1), encoding="utf-8")
    code = run_game(jp, "stills", xmx, timeout_s)
    files = sorted(glob.glob(str(out_dir / "stills" / "frame_*.png")))
    if not files:
        raise RuntimeError(f"no stills produced (exit {code}); see {job_dir / 'game.log'}")
    return files


def scout(name: str, world: Optional[World] = None, anchor: Sequence[float] = (0, 100, 0), maps: Sequence[Dict] = (),
          queries: Sequence[str] = (), settings: Optional[Settings] = None, commands: Sequence[str] = (), xmx: str = "3G",
          timeout_s: int = 1800) -> Dict:
    """Terrain / structure scouting without filming.  maps=[{"name":"a","x0":-128,"z0":-128,"x1":128,"z1":128,"step":2,"generate":False}],
    queries=["locate structure #minecraft:village", "locate biome minecraft:cherry_grove"].
    Returns {"queries": {...}, "maps": {name: path_to_json}}.  Load maps with cinecam.terrain.Terrain.load."""
    world, settings = world or World(), settings or Settings(renderDistance=10, simulationDistance=6, worldTicks=True)
    out_dir = OUT_HOME / name
    job_dir = RUN_HOME / "jobs" / name
    job_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    (job_dir / "camera.csv").write_text("t,x,y,z,yaw,pitch,roll,fov\n0,%s,%s,%s,0,0,0,70\n" % tuple(anchor), encoding="utf-8")
    job = {"name": name, "out": str(out_dir).replace("\\", "/"), "width": 640, "height": 360, "fps": 30, "subframes": 1,
           "ffmpeg": shutil.which("ffmpeg") or "ffmpeg", "world": {k: v for k, v in asdict(world).items() if v is not None}, "settings": asdict(settings),
           "scene": {"anchor": list(anchor), "commands": list(commands), "settleTicks": 40}, "camera": "camera.csv",
           "scout": {"maps": list(maps), "queries": list(queries)}}
    jp = job_dir / "job.json"
    jp.write_text(json.dumps(job, indent=1), encoding="utf-8")
    code = run_game(jp, "scout", xmx, timeout_s)
    rep = out_dir / f"{name}_report.json"
    if not rep.exists():
        raise RuntimeError(f"scout produced no report (exit {code}); see {job_dir / 'game.log'}")
    res: Dict = {"report": json.loads(rep.read_text(encoding="utf-8")), "maps": {}, "queries": {}}
    q = out_dir / f"{name}_queries.json"
    if q.exists():
        res["queries"] = json.loads(q.read_text(encoding="utf-8"))
    for m in maps:
        p = out_dir / f"{name}_scout_{m['name']}.json"
        if p.exists():
            res["maps"][m["name"]] = str(p)
    return res


# ----------------------------------------------------------------------------------------------------------- batch (v0.8)
@dataclass
class Shot:
    """One shot of a batch.  Film: rig (+anim).  Stills: poses (dicts x,y,z,yaw,pitch,roll?,fov?,t?)."""
    name: str
    rig: Optional[Rig] = None
    poses: Optional[List[Dict[str, float]]] = None
    scene: Optional[Scene] = None
    settings: Optional[Settings] = None
    anim: object = None
    size: Tuple[int, int] = (1920, 1080)
    grade: str = "clean"
    letterbox: Optional[float] = None
    supersample: int = 1
    dof: Optional[bool] = None
    crf: int = 14
    extra: Optional[dict] = None          # post.finish extra filter params
    blur: bool = True                     # False = sem motion blur (obturador 0; subframes só para anti-aliasing)


def _write_stills_job(sh: "Shot", world: World, out_dir: Path, job_dir: Path) -> Path:
    scene, settings = sh.scene or Scene(), sh.settings or Settings()
    settings = Settings(**{**asdict(settings), "worldTicks": False})
    job_dir.mkdir(parents=True, exist_ok=True)
    with open(job_dir / "camera.csv", "w") as f:
        f.write("t,x,y,z,yaw,pitch,roll,fov\n")
        for i, p in enumerate(sh.poses):
            f.write(f"{i / 30:.5f},{p['x']},{p['y']},{p['z']},{p['yaw']},{p['pitch']},{p.get('roll', 0)},{p.get('fov', 70)}\n")
    sc = asdict(scene)
    if sc.get("anchor") is None:
        sc["anchor"] = [sh.poses[0]["x"], sh.poses[0]["y"], sh.poses[0]["z"]]
    job = {"name": sh.name, "out": str(out_dir).replace("\\", "/"), "width": sh.size[0], "height": sh.size[1], "fps": 30, "subframes": 1,
           "ffmpeg": shutil.which("ffmpeg") or "ffmpeg", "world": {k: v for k, v in asdict(world).items() if v is not None}, "settings": asdict(settings), "scene": sc,
           "camera": "camera.csv", "mode": "stills"}
    if sh.anim is not None:
        sh.anim.write(str(job_dir / "anim.json"), np.array([float(p.get("t", 0.0)) for p in sh.poses]), 1)
        job["anim"] = "anim.json"
    jp = job_dir / "job.json"
    jp.write_text(json.dumps(job, indent=1), encoding="utf-8")
    return jp


def _post_shot(sh: "Shot", info: Dict) -> Dict:
    rep, out_dir = info["report"], Path(info["out_dir"])
    if sh.poses is not None:
        info["stills"] = sorted(glob.glob(str(out_dir / "stills" / "frame_*.png")))
        return info
    rows = sh.rig.sample_rows()
    master, scale = rep["output"], (f"{sh.size[0]}:{sh.size[1]}" if sh.supersample > 1 else None)
    if info["dof"]:
        c = np.arange(sh.rig.n_frames) * sh.rig.subframes + sh.rig.subframes // 2
        dmaster = str(out_dir / f"{sh.name}_dof.mkv")
        info["dof_frames"] = _dof.apply_dof(master, str(out_dir / f"{sh.name}_depth.mkv"), rows["focus"][c], rows["aperture"][c],
                                            dmaster, sh.size[0], sh.size[1], sh.rig.fps)
        master, scale = dmaster, None
    info["final"] = _post.finish(master, str(out_dir / f"{sh.name}.mp4"), preset=sh.grade, letterbox=sh.letterbox, crf=sh.crf,
                                 width=sh.size[0], height=sh.size[1], scale=scale, fps=sh.rig.fps, extra=sh.extra)
    info["master"] = master
    return info


def render_batch(shots: Sequence["Shot"], world: Optional[World] = None, xmx: str = "3G", timeout_s: Optional[int] = None,
                 post_workers: int = 2, log=print, retry: int = 1) -> List[Dict]:
    """Render many shots (film and/or stills) in ONE Minecraft session, same world (v0.8 of the mod: job 'next' queue).
    Saves the ~55 s boot (gradle + game + world) of every shot after the first.  Each shot keeps its own scene
    (anchor, time, weather, commands), settings, size and anim; the world (seed/copy) is the first shot's.
    Returns one info dict per shot ({"ok", "final"|"stills", "report", "error"?}); a failed shot does not stop the others."""
    world = world or World()
    shots = list(shots)
    jobs, infos = [], []
    bad = []
    for sh in shots:                       # 26/10: colisão é erro de direção — recusa o lote antes de abrir o jogo
        if sh.rig is not None:
            if not sh.blur:
                sh.rig.shutter = 0.0
            pr = checar_colisao(sh.anim, sh.rig, sh.scene)
            if pr:
                bad.append(f"{sh.name}: " + "; ".join(pr[:5]))
    if bad:
        raise ValueError("colisão (nunca permitido): " + " | ".join(bad))
    for sh in shots:
        out_dir, job_dir = OUT_HOME / sh.name, RUN_HOME / "jobs" / sh.name
        out_dir.mkdir(parents=True, exist_ok=True)
        for old in glob.glob(str(out_dir / f"{sh.name}_report.json")):
            os.remove(old)
        if sh.poses is not None:
            for old in glob.glob(str(out_dir / "stills" / "frame_*.png")):
                os.remove(old)
            jp, use_dof = _write_stills_job(sh, world, out_dir, job_dir), False
        else:
            rows = sh.rig.sample_rows()
            use_dof = bool((rows["focus"] > 0).any() and (rows["aperture"] > 0).any()) if sh.dof is None else sh.dof
            W, H = sh.size[0] * sh.supersample, sh.size[1] * sh.supersample
            jp = _write_job(sh.rig, sh.name, sh.scene or Scene(), world, sh.settings or Settings(), (W, H), out_dir, job_dir,
                            depth=use_dof, anim=sh.anim)
            j = json.loads(jp.read_text(encoding="utf-8")); j["mode"] = "film"; jp.write_text(json.dumps(j, indent=1), encoding="utf-8")
        jobs.append(jp)
        infos.append({"name": sh.name, "job": str(jp), "out_dir": str(out_dir), "dof": use_dof, "ok": False})
    first = json.loads(jobs[0].read_text(encoding="utf-8"))
    first["next"] = [str(p).replace("\\", "/") for p in jobs[1:]]
    jobs[0].write_text(json.dumps(first, indent=1), encoding="utf-8")
    ram = available_ram_gb()
    if ram < 2.5:
        log(f"[cinecam] WARNING: only {ram:.1f} GB RAM available; expect swapping")
    if free_gb(str(RUN_HOME)) < 8:
        raise RuntimeError("less than 8 GB free on the render drive")
    film_s = sum((sh.rig.duration if sh.rig is not None else 0) * (sh.rig.subframes if sh.rig is not None else 0) for sh in shots)
    timeout_s = timeout_s or int(600 + 120 * len(shots) + 6 * film_s)
    t0 = time.time()
    log(f"[cinecam] batch of {len(shots)} shots in one session")
    code = run_game(jobs[0], "film", xmx, timeout_s, log=RUN_HOME / "jobs" / shots[0].name / "game.log")
    game_s = round(time.time() - t0, 1)
    ready = []
    for sh, info in zip(shots, infos):
        rp = Path(info["out_dir"]) / f"{sh.name}_report.json"
        if not rp.exists():
            info["error"] = f"no report (exit {code}); see {RUN_HOME / 'jobs' / shots[0].name / 'game.log'}"
            continue
        info["report"] = json.loads(rp.read_text(encoding="utf-8"))
        if not info["report"].get("ok"):
            info["error"] = info["report"].get("error")
            continue
        ready.append((sh, info))
    from concurrent.futures import ThreadPoolExecutor
    def _one(a):
        sh, info = a
        try:
            _post_shot(sh, info); info["ok"] = True
        except Exception as e:
            info["error"] = f"post: {e}"
        return info
    with ThreadPoolExecutor(max(1, post_workers)) as ex:
        list(ex.map(_one, ready))
    for info in infos:
        info["game_seconds_batch"] = game_s
    failed = [k for k, i in enumerate(infos) if not i["ok"] and "post:" not in str(i.get("error"))]
    if failed and retry > 0:                           # e.g. RAM spike of another app killed the encoder: redo only those, new session
        log(f"[cinecam] retrying {len(failed)} failed shot(s): " + ", ".join(infos[k]["name"] for k in failed))
        again = render_batch([shots[k] for k in failed], world, xmx, timeout_s, post_workers, log, retry - 1)
        for k, i in zip(failed, again):
            infos[k] = i
    log(f"[cinecam] batch done in {round(time.time() - t0)} s (game {game_s} s): " + ", ".join(f"{i['name']}={'ok' if i['ok'] else i.get('error')}" for i in infos))
    return infos


class Sessao:
    """v1.1 (26/10/2026) — UMA sessão do Minecraft aberta para várias cenas que chegam aos poucos (produção ao vivo dos Shorts).
    A 1ª cena abre o jogo; as próximas entram pela pasta de entrada do mod (<RUN>/inbox/<n>.go) sem fechar/abrir o jogo nem
    recarregar o mundo (~55 s a menos por cena).  Fecha sozinha depois de `idle_s` sem cena ou com .close().

        with Sessao(World(seed=4242)) as s:
            info = s.render(Shot(...))          # bloqueia até o MP4 da cena ficar pronto (pós: DoF, grade, encode)
    Colisão é conferida antes (recusa como render()).  Só uma sessão/render por vez (render.lock)."""

    def __init__(self, world: Optional[World] = None, xmx: str = "3G", idle_s: int = 900, log=print):
        self.world, self.xmx, self.idle_s, self.log = world or World(), xmx, idle_s, log
        self.p: Optional[subprocess.Popen] = None
        self.lock: Optional[Path] = None
        self.inbox = RUN_HOME / "inbox"
        self.seq = 0
        self.t_start = 0.0
        self.logf = None

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()

    @property
    def aberta(self) -> bool:
        return self.p is not None and self.p.poll() is None

    def _job(self, sh: "Shot") -> Tuple[Path, Dict]:
        out_dir, job_dir = OUT_HOME / sh.name, RUN_HOME / "jobs" / sh.name
        out_dir.mkdir(parents=True, exist_ok=True)
        for old in glob.glob(str(out_dir / f"{sh.name}_report.json")):
            os.remove(old)
        if not sh.blur:
            sh.rig.shutter = 0.0
        rows = sh.rig.sample_rows()
        use_dof = bool((rows["focus"] > 0).any() and (rows["aperture"] > 0).any()) if sh.dof is None else sh.dof
        W, H = sh.size[0] * sh.supersample, sh.size[1] * sh.supersample
        jp = _write_job(sh.rig, sh.name, sh.scene or Scene(), self.world, sh.settings or Settings(), (W, H), out_dir, job_dir,
                        depth=use_dof, anim=sh.anim)
        j = json.loads(jp.read_text(encoding="utf-8"))
        j.update(mode="film", inbox=str(self.inbox).replace("\\", "/"), idleSec=int(self.idle_s))
        jp.write_text(json.dumps(j, indent=1), encoding="utf-8")
        return jp, {"name": sh.name, "job": str(jp), "out_dir": str(out_dir), "dof": use_dof, "ok": False}

    def render(self, sh: "Shot", timeout_s: Optional[int] = None, post: bool = True) -> Dict:
        """post=False: devolve logo que o jogo termina a cena; rode Sessao.pos(sh, info) depois (em paralelo com a próxima)."""
        pr = checar_colisao(sh.anim, sh.rig, sh.scene)
        if pr:
            raise ValueError("colisão (nunca permitido): " + "; ".join(pr[:8]))
        jp, info = self._job(sh)
        rp = Path(info["out_dir"]) / f"{sh.name}_report.json"
        t0 = time.time()
        if not self.aberta:
            self._abrir(jp)
        else:
            self.inbox.mkdir(parents=True, exist_ok=True)
            self.seq += 1
            tmp = self.inbox / f"{self.seq:06d}.tmp"
            tmp.write_text(str(jp), encoding="utf-8")
            tmp.replace(self.inbox / f"{self.seq:06d}.go")          # atômico: o mod nunca lê um arquivo pela metade
        limite = timeout_s or int(240 + 8 * sh.rig.duration * sh.rig.subframes)
        while not rp.exists():
            if not self.aberta:
                info["error"] = f"o jogo fechou (código {self.p.returncode if self.p else '?'}); veja {self.logf.name if self.logf else 'game.log'}"
                self._fechou()
                return info
            if time.time() - t0 > limite:
                info["error"] = f"cena passou de {limite} s"
                self.close(force=True)
                return info
            time.sleep(0.5)
        time.sleep(0.3)                                             # o mod termina de gravar o relatório
        info["report"] = json.loads(rp.read_text(encoding="utf-8"))
        info["game_seconds"] = round(time.time() - t0, 1)
        if not info["report"].get("ok"):
            info["error"] = info["report"].get("error")
            return info
        info["_game_ok"] = True
        return self.pos(sh, info) if post else info

    @staticmethod
    def pos(sh: "Shot", info: Dict) -> Dict:
        """Pós da cena (DoF, grade, encode do MP4 final) — pode rodar numa thread enquanto o jogo faz a próxima."""
        if not info.get("_game_ok"):
            return info
        t0 = time.time()
        try:
            _post_shot(sh, info)
            info["ok"] = True
        except Exception as e:
            info["error"] = f"post: {e}"
        info["post_seconds"] = round(time.time() - t0, 1)
        return info

    def _abrir(self, jp: Path):
        if available_ram_gb() < 2.5:
            self.log(f"[cinecam] WARNING: only {available_ram_gb():.1f} GB RAM available; expect swapping")
        if free_gb(str(RUN_HOME)) < 8:
            raise RuntimeError("less than 8 GB free on the render drive")
        self.inbox.mkdir(parents=True, exist_ok=True)
        for f in list(self.inbox.glob("*.go")) + list(self.inbox.glob("stop")):
            f.unlink(missing_ok=True)
        self.lock = _take_lock()
        self.t_start = time.time()
        env = dict(os.environ, JAVA_HOME=_java_home(), CINECAM_RUN=str(RUN_HOME))
        self.logf = open(RUN_HOME / "sessao.log", "w", encoding="utf-8", errors="replace")
        self.p, self._direct = _launch(jp, "film", self.xmx, self.logf, env)
        self.log("[cinecam] sessão aberta (o jogo fica aberto entre as cenas)")

    def _fechou(self):
        if self.logf:
            self.logf.close()
            if not getattr(self, "_direct", True):
                _capture_launch(self.logf.name)
            self.logf = None
        if self.lock:
            self.lock.unlink(missing_ok=True)
            self.lock = None
        if self.t_start:
            _clean_saves(self.t_start)
            self.t_start = 0.0
        self.p = None

    def close(self, force: bool = False):
        if self.p is None:
            return
        if self.aberta and not force:
            self.inbox.mkdir(parents=True, exist_ok=True)
            (self.inbox / "stop").write_text("1", encoding="utf-8")
            try:
                self.p.wait(timeout=60)
            except subprocess.TimeoutExpired:
                force = True
        if force and self.aberta:
            _kill_tree(self.p.pid)
        self._fechou()
