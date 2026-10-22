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

MOD_HOME = Path(os.environ.get("CINECAM_HOME", "D:/cinecam-forge-1.20.1"))
RUN_HOME = Path(os.environ.get("CINECAM_RUN", "D:/cinecam-run"))
OUT_HOME = Path(os.environ.get("CINECAM_OUT", "D:/cinecam-out"))


@dataclass
class World:
    mode: str = "fresh"               # fresh | copy
    seed: int = 20261015
    preset: str = "normal"            # normal | flat
    structures: bool = True
    copyFrom: Optional[str] = None    # absolute path of a save folder to copy (never opens the original)


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
    env = os.environ.get("CINECAM_JAVA_HOME")
    if env:
        return env
    c = sorted(glob.glob(str(Path.home() / ".gradle/jdks/temurin17-download/jdk-17*")))
    c += sorted(glob.glob(r"C:\Program Files\Eclipse Adoptium\jdk-17*")) + sorted(glob.glob(r"C:\Program Files\Java\jdk-17*"))
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
           "world": asdict(world), "settings": asdict(settings), "scene": sc, "camera": "camera.csv"}
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


def run_game(job_json: Path, mode: str = "film", xmx: str = "4G", timeout_s: int = 3600, log: Optional[Path] = None) -> int:
    """Run the dev client with the mod.  Blocks until Minecraft exits.  Only one run at a time.
    v0.8: the game is launched DIRECTLY with java (the runClient command captured once from gradle --info into
    RUN_HOME/launch.json), so no 1-2 GB gradle JVM sits alive during the render; when the mod source changed, only
    'gradlew classes' runs first.  CINECAM_GRADLE=1 forces the old gradle runClient path."""
    lock = RUN_HOME / "render.lock"
    RUN_HOME.mkdir(parents=True, exist_ok=True)
    if lock.exists() and time.time() - lock.stat().st_mtime < 3 * 3600:
        raise RuntimeError(f"another render seems to be running (lock {lock}); delete it if that is stale")
    lock.write_text(str(os.getpid()))
    try:
        t_start = time.time()
        env = dict(os.environ, JAVA_HOME=_java_home())
        logf = open(log or (job_json.parent / "game.log"), "w", encoding="utf-8", errors="replace")
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
            p = subprocess.Popen(cmd, cwd=str(RUN_HOME), env=env, stdout=logf, stderr=subprocess.STDOUT)
        else:
            p = _gradle(["runClient", "--info", f"-Pxmx={xmx}", f"-Pjob={jarg}", f"-Pmode={mode}"], logf, env)
        try:
            code = p.wait(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            _kill_tree(p.pid)
            raise RuntimeError(f"game run exceeded {timeout_s}s and was killed; see {logf.name}")
        finally:
            logf.close()
        _clean_saves(t_start)
        if not cmd:                                          # first gradle run: keep its java command for the next ones
            try:
                for line in open(logf.name, encoding="utf-8", errors="replace"):
                    if "Starting process" in line and "-Dcinecam.job=" in line:
                        LAUNCH.write_text(json.dumps({"cmd": _split_logged_cmd(line), "stamp": _src_stamp(),
                                                      "captured": time.strftime("%Y-%m-%d %H:%M")}, indent=1), encoding="utf-8")
                        break
            except Exception as e:
                print(f"[cinecam] could not capture the direct launch command: {e}")
        return code
    finally:
        lock.unlink(missing_ok=True)


def _kill_tree(pid: int):
    subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True)


def render(rig: Rig, name: str, scene: Optional[Scene] = None, world: Optional[World] = None, settings: Optional[Settings] = None,
           size: Tuple[int, int] = (1920, 1080), grade: str = "cinematic", letterbox: Optional[float] = None, supersample: int = 1,
           xmx: str = "4G", audio: Optional[str] = None, crf: int = 14, timeout_s: int = 3600, dry_run: bool = False,
           dof: Optional[bool] = None, anim=None) -> Dict:
    """Render a rig to D:/cinecam-out/<name>/<name>.mp4.  Returns a dict with paths and the mod's report."""
    scene, world, settings = scene or Scene(), world or World(), settings or Settings()
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
           "ffmpeg": shutil.which("ffmpeg") or "ffmpeg", "world": asdict(world), "settings": asdict(settings), "scene": sc, "camera": "camera.csv"}
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
           "ffmpeg": shutil.which("ffmpeg") or "ffmpeg", "world": asdict(world), "settings": asdict(settings),
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
           "ffmpeg": shutil.which("ffmpeg") or "ffmpeg", "world": asdict(world), "settings": asdict(settings), "scene": sc,
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
