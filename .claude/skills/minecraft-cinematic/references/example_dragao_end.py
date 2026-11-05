"""Portal Macabro — take de 7 s: o Ender Dragon morre no End normal e o End vira vermelho e macabro (05/11/2026).

0,0–3,4 s  contra-plongée do chão da arena: o dragão morrendo no alto, sobre o portal de saída (raios de luz e corpo se
           desfazendo, a morte vanilla), sobe devagar, explosões no fim; some num clarão e o portal ACENDE (roxo) + o ovo.
3,4 s      CORTE.
3,4–7,0 s  do alto, olhando o portal roxo; aos 3,85 s ele fica VERMELHO, as tochas viram de redstone, a corrupção se espalha
           do portal pelo chão (end stone -> nylium/netherrack/pedra-negra/magma), o céu e a névoa viram sangue e as 9 colunas
           de fumaça preta nascem no horizonte; a câmera sobe e recua revelando o End corrompido.

Onde: o vazio do End a 600 blocos do centro (fora da luta de verdade: o servidor não cria dragão), com a arena montada
igual à do take da roda (chão de end stone até além da névoa, 10 pilares de obsidiana, pódio de bedrock vanilla).
O dragão é desenhado pelo CineCam só no cliente (canais morte/asa, v1.3); portal, tochas, partículas, céu e fumaça vêm de
comandos com hora marcada (scene.events, v1.3); a corrupção do chão é de blocos do cliente (scene.blocks).
Portal vermelho = bloco end_gateway com o shader do pacote `portal_vermelho` (o mesmo céu estrelado do portal, em vermelho).
Uso: python dragao.py [rascunho]
"""
import importlib
import json
import math
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".claude/skills/minecraft-cinematic/scripts"))
import numpy as np  # noqa: E402
from cinecam import *  # noqa: E402,F401
R = importlib.import_module("cinecam.render")   # o MÓDULO (o pacote exporta uma função render com o mesmo nome)

RASCUNHO = len(sys.argv) > 1 and sys.argv[1].startswith("rasc")
INST = Path.home() / "AppData/Roaming/ModrinthApp/profiles/Portal Macabro"
MODRINTH = Path.home() / "AppData/Local/Modrinth App/Modrinth App.exe"
INST_ID = "local:7ab5face-e1ca-4a2d-b3b5-8963303e90ab"
CINE_JAR = Path(r"D:\cinecam-forge-1.20.1\build\libs\cinecam-forge-1.20.1-0.1.0.jar")
PACK = Path(__file__).parent / "portal_vermelho"
PACK_NOME = "pm_portal_vermelho"

FPS = 60
SUB = 1 if RASCUNHO else 6
SIZE = (960, 540) if RASCUNHO else (1920, 1080)
NOME = "portal_dragao" + ("_rasc" if RASCUNHO else "")
T1, T2 = 3.4, 3.6
OX, OY, OZ = 600, 64, 0                     # origem do pódio (nível do portal); chão de end stone em y 63
C = np.array([OX + 0.5, float(OY), OZ + 0.5])
T_MORTE_FIM = 3.0                           # dragão some
T_PORTAL = 3.05                             # portal acende (roxo)
T_VERMELHO = 3.85                           # portal fica vermelho + corrupção
DRAGAO_Y0, DRAGAO_Y1 = 64 + 4 + 7.5, 64 + 4 + 11.5   # centro do dragão (sobe 4 blocos morrendo)


def ponto(bearing, r, dy=0.0):
    a = math.radians(bearing)
    return C + np.array([r * math.sin(a), dy, -r * math.cos(a)])


# ----------------------------------------------------------------------------------------------- pódio (EndPodiumFeature)
def podio():
    """Posições do pódio vanilla (1.20.1): anel de bedrock (3,5 > d >= 2,5) no nível da origem, miolo (d < 2,5) = portal,
    bedrock embaixo do miolo, pilar central de 4 bedrocks com 4 tochas na altura +2."""
    miolo, anel = [], []
    for dx in range(-4, 5):
        for dz in range(-4, 5):
            d2 = dx * dx + dz * dz
            if d2 < 6.25:
                miolo.append((dx, dz))
            elif d2 < 12.25:
                anel.append((dx, dz))
    return miolo, anel


MIOLO, ANEL = podio()
PORTAL = [(dx, dz) for dx, dz in MIOLO if (dx, dz) != (0, 0)]      # 20 blocos de portal (o centro é o pilar)
TOCHAS = [((0, -1), "north"), ((0, 1), "south"), ((1, 0), "east"), ((-1, 0), "west")]


def _pilares():
    out = []
    alturas = [30, 22, 34, 18, 27, 32, 20, 25, 36, 16]
    for k in range(10):
        p = ponto(18 + 36 * k, 27 + 3 * ((k * 7) % 3))
        out.append((math.floor(p[0]), math.floor(p[2]), 2 + (k % 2), alturas[k], alturas[k] <= 18))
    return out


PILARES = _pilares()
FUMACAS = [0, 40, 320, 80, 280, 120, 240, 160, 200]                  # as 9 colunas no horizonte (igual ao take da roda)


def comandos():
    cmds = ["gamerule doMobSpawning false", "gamerule doDaylightCycle false", "gamerule doWeatherCycle false",
            "gamerule doFireTick false", "kill @e[type=!player]", "ent scare all off",
            "ent world @a corrompido", "ent fog set 0"]
    E = 136
    for x0, x1 in ((OX - E, OX - 1), (OX, OX + E)):
        for z0, z1 in ((OZ - E, OZ - 1), (OZ, OZ + E)):
            cmds.append(f"fill {x0} 63 {z0} {x1} 63 {z1} minecraft:end_stone")
    cmds.append(f"fill {OX-40} 64 {OZ-40} {OX+40} 76 {OZ+40} minecraft:air")
    # pódio inativo (miolo vazio)
    for dx, dz in MIOLO:
        cmds.append(f"setblock {OX+dx} 63 {OZ+dz} minecraft:bedrock")
    for dx, dz in ANEL:
        cmds.append(f"setblock {OX+dx} 64 {OZ+dz} minecraft:bedrock")
    cmds.append(f"fill {OX} 64 {OZ} {OX} 67 {OZ} minecraft:bedrock")
    for (dx, dz), f in TOCHAS:
        cmds.append(f"setblock {OX+dx} 66 {OZ+dz} minecraft:wall_torch[facing={f}]")
    # pilares de obsidiana com o cristal já destruído (bedrock + fogo no topo), 2 com gaiola
    for x, z, r, h, gaiola in PILARES:
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                if dx * dx + dz * dz <= r * r + r:
                    cmds.append(f"fill {x+dx} 64 {z+dz} {x+dx} {63+h} {z+dz} minecraft:obsidian")
        topo = 64 + h
        if gaiola:
            cmds.append(f"fill {x-2} {topo} {z-2} {x+2} {topo+3} {z+2} minecraft:iron_bars hollow")
        cmds += [f"setblock {x} {topo} {z} minecraft:bedrock", f"setblock {x} {topo+1} {z} minecraft:fire"]
    # 9 colunas de fumaça no horizonte, apagadas até a corrupção
    for k, b in enumerate(FUMACAS):
        p = ponto(b, 70 + 9 * (k % 3))
        cmds.append(f"execute positioned {p[0]:.1f} 64 {p[2]:.1f} run ent smoke place {k + 1}")
    cmds.append("ent smoke all off")
    return cmds


# ----------------------------------------------------------------------------------------------- eventos com hora marcada
def eventos():
    ev = []
    cx, cy, cz = C[0], DRAGAO_Y0 + 3.0, C[2]
    for t, dy in ((2.55, 0.0), (2.75, 1.0), (2.92, 2.0)):          # as explosões do fim da morte vanilla (ticks 180-200)
        ev.append([t, f"particle minecraft:explosion_emitter {cx:.1f} {cy+dy:.1f} {cz:.1f} 4 3 4 0 5 force"])
    ev.append([T_MORTE_FIM, f"particle minecraft:flash {cx:.1f} {cy+2:.1f} {cz:.1f} 0 0 0 0 3 force"])
    ev.append([T_MORTE_FIM, f"particle minecraft:end_rod {cx:.1f} {cy+2:.1f} {cz:.1f} 3 3 3 0.25 260 force"])
    for dx, dz in PORTAL:                                            # o portal de saída acende
        ev.append([T_PORTAL, f"setblock {OX+dx} 64 {OZ+dz} minecraft:end_portal"])
    ev.append([T_PORTAL, f"setblock {OX} 68 {OZ} minecraft:dragon_egg"])
    for dx, dz in PORTAL:                                            # ... e fica VERMELHO (gateway + shader do pacote)
        ev.append([T_VERMELHO, f"setblock {OX+dx} 64 {OZ+dz} minecraft:end_gateway{{Age:100000L}}"])
    for (dx, dz), f in TOCHAS:
        ev.append([T_VERMELHO, f"setblock {OX+dx} 66 {OZ+dz} minecraft:redstone_wall_torch[facing={f}]"])
    ev += [[T_VERMELHO, f"particle minecraft:dust 1 0.05 0.05 3 {C[0]:.1f} 65.2 {C[2]:.1f} 2 0.4 2 0 420 force"],
           [T_VERMELHO, f"particle minecraft:large_smoke {C[0]:.1f} 65.2 {C[2]:.1f} 1.5 0.3 1.5 0.06 160 force"],
           [T_VERMELHO, f"particle minecraft:lava {C[0]:.1f} 65.0 {C[2]:.1f} 1.5 0.2 1.5 0 50 force"]]
    for k in range(1, 11):                                           # céu e névoa de sangue entram em 1 s
        ev.append([round(T_VERMELHO + 0.1 + 0.1 * k, 3), f"ent fog set {k}"])
    for k in range(9):                                               # as colunas nascem no horizonte
        ev.append([round(T_VERMELHO + 0.2 + 0.1 * k, 3), f"ent smoke {k + 1} on"])
    return ev


def corrupcao():
    """Blocos do cliente: o chão vira nylium/netherrack/pedra-negra/magma numa onda que sai do portal."""
    rng = np.random.default_rng(11)
    out = []
    R0, RMAX, VEL = 3.6, 42.0, 24.0
    ilhas = rng.uniform(0, 1, size=(200, 200))
    for _ in range(3):                                               # borra o ruído: manchas em vez de salpico
        ilhas = (ilhas + np.roll(ilhas, 1, 0) + np.roll(ilhas, -1, 0) + np.roll(ilhas, 1, 1) + np.roll(ilhas, -1, 1)) / 5
    ilhas = (np.argsort(np.argsort(ilhas.ravel())) / ilhas.size).reshape(ilhas.shape)   # posição -> proporções exatas

    def tipo(v):
        if v < 0.45:
            return "minecraft:crimson_nylium"
        if v < 0.75:
            return "minecraft:netherrack"
        if v < 0.93:
            return "minecraft:blackstone"
        return "minecraft:magma_block" if v > 0.965 else "minecraft:nether_wart_block"
    for dx in range(-int(RMAX), int(RMAX) + 1):
        for dz in range(-int(RMAX), int(RMAX) + 1):
            d = math.hypot(dx, dz)
            if d < R0 or d > RMAX:
                continue
            if d > RMAX * 0.75 and rng.uniform() < (d - RMAX * 0.75) / (RMAX * 0.25):
                continue                                             # borda irregular
            x, z = OX + dx, OZ + dz
            if any(x0 - r <= x <= x0 + r and z0 - r <= z <= z0 + r for x0, z0, r, _h, _g in PILARES):
                continue
            t = T_VERMELHO + (d - R0) / VEL + rng.uniform(0, 0.07)
            out.append([round(float(t), 4), x, 63, z, tipo(ilhas[dx + 100, dz + 100])])
    return out


# ----------------------------------------------------------------------------------------------- o dragão (cliente)
def dragao():
    m = Mob("dragao", "minecraft:ender_dragon", (C[0], DRAGAO_Y0, C[2]), auto_walk=False)
    m.key(0.0, ease="linear", morte=70, asa=0.30, yaw=180.0, shadow_y=0)
    m.key(T_MORTE_FIM, ease="linear", morte=200, asa=1.05)
    m.key(0.0, y=DRAGAO_Y0)
    m.key(T_MORTE_FIM, ease="in_out", y=DRAGAO_Y1, yaw=196.0)
    m.key(T_MORTE_FIM, ease="hold", sx=0)                            # sumiu
    return m


# ----------------------------------------------------------------------------------------------- câmera
def camera():
    rig = Rig(fps=FPS, subframes=SUB, shutter=0.5)
    # A: contra-plongée do chão, orbitando devagar e chegando; a mira desce do dragão para o portal no fim
    alto, baixo = C + [0, 8.0, 0], C + [0, 3.2, 0]

    def mira_a(tau):
        t = np.asarray(tau) * T1
        s = np.clip((t - 2.55) / 0.85, 0, 1)
        s = s * s * (3 - 2 * s)
        return alto + (baixo - alto) * s[:, None]
    a = orbit(tuple(C), radius=(15.5, 13.0), start_deg=207, end_deg=188, height=(1.4, 2.6), T=T1, ease="smooth",
              fov=(70, 66))
    a = Move(a.duration, lambda tau, base=a: _remira(base.fn(tau), mira_a(tau)), "dragao_a").with_handheld("subtle")
    a = a.with_shake([(2.55, 0.5, 0.25), (2.75, 0.6, 0.25), (2.92, 0.7, 0.3), (3.0, 1.3, 0.45)])
    rig.add(a)
    # B: do alto sobre o portal (roxo -> vermelho), sobe e recua revelando o End corrompido
    pts = [ponto(182, 2.6, 8.0), ponto(181, 6.0, 9.0), ponto(180, 14.0, 11.5), ponto(180, 21.0, 13.0)]
    portal, horizonte = C + [0, 0.8, 0], C + [0, 7.0, -8.0]
    ease_b = (0.42, 0.0, 0.25, 1.0)
    e = ease_fn(ease_b)
    mira_b = lambda tau: portal + (horizonte - portal) * e(np.asarray(tau))[:, None]
    b = track(pts, mira_b, T2, ease=ease_b, fov=(64, 70), roll=(0.0, 0.0))
    b = b.with_shake([(T_VERMELHO - T1, 1.1, 0.4)])
    rig.add(b, cut=True)
    return rig


def _remira(o, alvo):
    from cinecam.camlib import look_at
    pos = np.stack([o["x"], o["y"], o["z"]], axis=-1)
    yaw, pitch = look_at(pos, alvo)
    o = dict(o)
    o["yaw"], o["pitch"] = np.unwrap(np.radians(yaw)) * 180 / np.pi, pitch
    return o


# ----------------------------------------------------------------------------------------------- render na instância
PRESET = {"_desc": "cinemática do dragão (cinecam): End normal em fog 0, céu e névoa de sangue em fog 10 (fade)",
          "fogColor": "#5a0d12", "fog": [170, 90], "fogStart": 0.12, "sky": "#3a0609", "skyAlpha": 0.97,
          "tint": 0.0, "time": -1, "thunder": 0, "fade": True, "smokeColor": "#0a0203",
          "particles": [{"type": "minecraft:white_ash", "rate": 10, "radius": 14, "y": [0, 10]},
                        {"type": "minecraft:ash", "rate": 5, "radius": 14, "y": [0, 10]},
                        {"type": "minecraft:crimson_spore", "rate": 5, "radius": 12, "y": [0, 6]},
                        {"type": "minecraft:smoke", "rate": 2, "radius": 10, "y": [0.1, 1], "ground": True}]}


def run_game_instancia(job_json, mode="film", xmx="4G", timeout_s=3600, log=None):
    """Roda o job dentro da instância (com os mods do vídeo) e devolve tudo como estava: jar, job, preset, pacote, options."""
    if any("profiles\\Portal Macabro" in l for l in _javas()):
        raise RuntimeError("a instância Portal Macabro está aberta: feche o jogo")
    jar = INST / "mods" / CINE_JAR.name
    txt = INST / "cinecam-job.txt"
    wj = INST / "config/portalmacabro/world.json"
    op = INST / "options.txt"
    rp = INST / "resourcepacks" / PACK_NOME
    wj_antes, op_antes = wj.read_text(encoding="utf-8"), op.read_text(encoding="utf-8")
    d = json.loads(wj_antes)
    d["presets"]["corrompido"] = PRESET
    linhas = []
    for l in op_antes.splitlines():
        if l.startswith("resourcePacks:"):
            packs = json.loads(l.split(":", 1)[1])
            packs = [p for p in packs if p != f"file/{PACK_NOME}"] + [f"file/{PACK_NOME}"]
            l = "resourcePacks:" + json.dumps(packs, separators=(",", ":"))
        linhas.append(l)
    antes = {p.name for p in (INST / "saves").iterdir()}
    shutil.copy2(CINE_JAR, jar)
    shutil.rmtree(rp, ignore_errors=True)
    shutil.copytree(PACK, rp)
    txt.write_text(str(job_json), encoding="utf-8")
    wj.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    op.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    try:
        subprocess.Popen([str(MODRINTH), f"modrinth://launch/instance/{INST_ID}"])
        t0, visto = time.time(), False
        while time.time() - t0 < timeout_s:
            time.sleep(5)
            rodando = any("profiles\\Portal Macabro" in l for l in _javas())
            visto = visto or rodando
            if visto and not rodando:
                break
        return 0
    finally:
        for _ in range(10):
            try:
                jar.unlink(missing_ok=True)
                break
            except PermissionError:
                time.sleep(3)
        txt.unlink(missing_ok=True)
        wj.write_text(wj_antes, encoding="utf-8")
        op.write_text(op_antes, encoding="utf-8")
        shutil.rmtree(rp, ignore_errors=True)
        for p in (INST / "saves").iterdir():
            if p.name not in antes and p.name.startswith("cinecam-"):
                shutil.rmtree(p, ignore_errors=True)


def _javas():
    out = subprocess.run(["powershell", "-NoProfile", "-Command",
                          "Get-CimInstance Win32_Process -Filter \"Name='javaw.exe' OR Name='java.exe'\" | ForEach-Object { $_.CommandLine }"],
                         capture_output=True, text=True).stdout
    return out.splitlines()


# grade do take: o "portal" do take da roda SEM o split-tone (deixava o end stone verde-oliva demais), bloom maior nos raios
post.PRESETS["portal_end"] = dict(curves="0/0.01 0.1/0.12 0.5/0.55 0.85/0.88 1/0.97", sat=1.08, contrast=1.06,
                                  bloom=0.24, bloom_radius=30, vignette=0.24, grain=4, sharpen=0.4, ca=1)

if __name__ == "__main__":
    R.run_game = run_game_instancia
    rig = camera()
    scene = Scene(time=6000, weather="clear", dimension="minecraft:the_end", anchor=tuple(C + [0, 8, 10]),
                  commands=comandos(), settleTicks=80, blocks=corrupcao(), events=eventos())
    world = World(mode="fresh", preset="flat", groundY=64, structures=False)
    settings = Settings(renderDistance=8, simulationDistance=6, worldTicks=True, gamma=1.0, clouds=False)
    info = render(rig, NOME, scene=scene, world=world, settings=settings, size=SIZE, grade="portal_end",
                  anim=Anim([], mobs=[dragao()]), blur=not RASCUNHO, dof=False, checar=False)
    print(info.get("final"), info.get("report", {}).get("warnings"))
