"""Portal Macabro — take de 7 s: o Problems no centro de uma roda com os 9 monstros (04/11/2026).

0,0–3,0 s  plano fechado no Problems (câmera na altura do rosto, push-in em arco, fogo de alma e monstros em bokeh atrás),
           ele fala "Eu conversei com as entidades de terror do Minecraft".
3,0 s      CORTE seco com tranco de impacto.
3,0–7,0 s  a câmera sai baixa do pé dele, recua por entre o Verity Demon e o Muffin (passam rente à lente), sobe e abre na
           roda inteira; no meio o foco salta para o Obsessed atrás dele e volta para o Problems.
Cenário (05/11): arena da batalha do End - chão inteiro de end stone (sem grama nem vazio à vista), anel de 10 pilares de
obsidiana com cristal do End no topo (2 com gaiola), postes com lanterna de alma em volta do Problems. Clima: preset
"circulo" (céu e névoa cor de sangue mesmo no End, cinzas e esporos no ar, fumaça rasteira) e 9 colunas de fumaça pretas
no horizonte (uma atrás de cada monstro).

Renderiza DENTRO da instância "Portal Macabro" (os mods de terror, os modelos BBS e o nosso mod): o jar do CineCam entra
na instância só durante o render (lê o job de cinecam-job.txt) e sai depois, junto com o mundo temporário.
Uso: python circulo.py [rascunho]
"""
import math
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".claude/skills/minecraft-cinematic/scripts"))
import numpy as np  # noqa: E402
from cinecam import *  # noqa: E402,F401
import importlib  # noqa: E402
R = importlib.import_module("cinecam.render")   # o MÓDULO (o pacote exporta uma função render com o mesmo nome)
from cinecam.atua import Ator  # noqa: E402
from cinecam.turma import skin  # noqa: E402

RASCUNHO = len(sys.argv) > 1 and sys.argv[1].startswith("rasc")
INST = Path.home() / "AppData/Roaming/ModrinthApp/profiles/Portal Macabro"
MODRINTH = Path.home() / "AppData/Local/Modrinth App/Modrinth App.exe"
INST_ID = "local:7ab5face-e1ca-4a2d-b3b5-8963303e90ab"
CINE_JAR = Path(r"D:\cinecam-forge-1.20.1\build\libs\cinecam-forge-1.20.1-0.1.0.jar")

FPS = 60
SUB = 1 if RASCUNHO else 6
SIZE = (960, 540) if RASCUNHO else (1920, 1080)
NOME = "portal_circulo" + ("_rasc" if RASCUNHO else "")
T1, T2 = 3.0, 4.0
C = np.array([0.5, 64.0, 0.5])          # pés do Problems (mundo plano; o chão de end stone fica em y 63)
RAIO = 7.0

# bearing (0 = norte, 90 = leste), monstro: atrás do Problems no close (norte) ficam os mais icônicos.
# Etiqueta entN da fase OBRIGATÓRIA: o mod do vídeo some com todo monstro sem tag "ent..." (Pacman descarregado, 67/Muffin
# somem, Obsessed roda o próprio despawn) - só o monstro do diretor fica.
MONSTROS = [
    (0, "obsessed", None),       # mob do CineCam (ver MOBS_CLIENTE)
    (40, "horse", 'summon creepyhorse:creepy_horse {p} {{Tags:["pm_cine","ent3"],NoAI:1b,Silent:1b,Invulnerable:1b,PersistenceRequired:1b,Rotation:[{yaw}f,0f]}}'),
    (320, "idol", None),           # mob do CineCam (ver MOBS_CLIENTE)
    (80, "pacman", 'summon pacman:pacman {p} {{Tags:["pm_cine","ent4"],NoAI:1b,Silent:1b,Invulnerable:1b,PersistenceRequired:1b,Rotation:[{yaw}f,0f]}}'),
    (280, "67", 'summon sixtysevenentity:sixty_seven_entity {p} {{Tags:["pm_cine","ent6"],NoAI:1b,Silent:1b,Invulnerable:1b,PersistenceRequired:1b,Rotation:[{yaw}f,0f]}}'),
    (120, "gato", "execute positioned {p} run function portalmacabro:gato"),
    (240, "mimicer", "execute positioned {p} run function portalmacabro:mimicer"),
    (160, "verity", 'summon verity:verity_demon {p} {{Tags:["pm_cine","ent2"],NoAI:1b,Silent:1b,Invulnerable:1b,PersistenceRequired:1b,Rotation:[{yaw}f,0f]}}'),
    (200, "muffin", 'summon dexter:dexter {p} {{Tags:["pm_cine","ent7"],NoAI:1b,Silent:1b,Invulnerable:1b,PersistenceRequired:1b,Rotation:[{yaw}f,0f]}}'),
]
# Obsessed e Idol se apagam sozinhos no servidor nesse mundo de render (mesmo com ent1/ent8, NoAI ou variantes "model" e
# "display": diagnóstico 04/11, D:/cinecam-out/portal_circulo_diag*). Então o CineCam desenha os dois SÓ no cliente
# (actors.Mob: entidade criada no client, com o modelo e as animações do próprio mod). Altura real da caixa (bytecode do
# registro do mod): o mod do CineCam põe os pés em y - altura/2.
MOBS_CLIENTE = {"obsessed": ("the_obsessed:idk_spider_threatening", 1.99), "idol": ("the_idol_v2:idol_chase", 0.9)}


def ponto(bearing, r, dy=0.0):
    a = math.radians(bearing)
    return C + np.array([r * math.sin(a), dy, -r * math.cos(a)])


def _pilares():
    """10 pilares (x, z, raio, altura, gaiola) num anel de ~28 blocos: fora da roda e do caminho da câmera (r <= 15,5)."""
    out = []
    alturas = [30, 22, 34, 18, 27, 32, 20, 25, 36, 16]
    for k in range(10):
        b = 18 + 36 * k
        p = ponto(b, 27 + 3 * ((k * 7) % 3))
        out.append((math.floor(p[0]), math.floor(p[2]), 2 + (k % 2), alturas[k], alturas[k] <= 18))
    return out


PILARES = _pilares()


def yaw_para_centro(p):
    d = C - p
    return math.degrees(math.atan2(-d[0], d[2]))


def comandos():
    cx, cz = int(C[0] - 0.5), int(C[2] - 0.5)
    cmds = ["gamerule doMobSpawning false", "gamerule doDaylightCycle false", "gamerule doWeatherCycle false",
            "time set 12500", "weather clear", "ent scare all off", "ent world @a circulo", "ent fog set 2",
            "kill @e[type=!player]"]
    # arena da batalha do End (05/11, Matheus): chão INTEIRO de end stone até além da névoa (225x225, em 4 fills de
    # < 32768 blocos) - nenhum pedaço de grama/vazio aparece, nem do alto
    E = 112
    for x0, x1 in ((cx - E, cx - 1), (cx, cx + E)):
        for z0, z1 in ((cz - E, cz - 1), (cz, cz + E)):
            cmds.append(f"fill {x0} 63 {z0} {x1} 63 {z1} minecraft:end_stone")
    cmds.append(f"fill {cx-17} 64 {cz-17} {cx+17} 72 {cz+17} minecraft:air")
    # 9 colunas de fumaça do mod no horizonte, uma atrás de cada monstro (o placar do vídeo)
    for k, (b, _n, _c) in enumerate(MONSTROS):
        p = ponto(b, 70 + 9 * (k % 3))
        cmds.append(f"execute positioned {p[0]:.1f} 64 {p[2]:.1f} run ent smoke place {k + 1}")
    cmds.append("ent smoke all on")
    # anel de fogo azul (alma) em volta do Problems
    # 8 postes de pedra-negra com lanterna de alma (sem fumaça: fogueira enchia o plano aberto de fumaça branca)
    for i in range(8):
        p = ponto(i * 45 + 22.5, 4.3)
        x, z = math.floor(p[0]), math.floor(p[2])
        cmds += [f"setblock {x} 64 {z} minecraft:polished_blackstone_wall", f"setblock {x} 65 {z} minecraft:soul_lantern"]
    # luz invisível: rosto do Problems; cada monstro com luz de frente (baixa e alta, lado do centro) + contorno atrás
    cmds.append(f"setblock {cx} 66 {cz+2} minecraft:light[level=11]")
    for b, _n, _c in MONSTROS:
        for r, dy, lv in ((RAIO - 1.3, 1.0, 15), (RAIO - 1.3, 3.0, 15), (RAIO + 1.2, 2.0, 12)):
            p = ponto(b, r, dy)
            cmds.append(f"setblock {math.floor(p[0])} {math.floor(p[1])} {math.floor(p[2])} minecraft:light[level={lv}]")
    # pilares de obsidiana do End (no lugar das árvores secas): anel de 10 em volta da arena, como na luta do dragão,
    # cada um com cristal do End no topo; os 2 mais baixos com gaiola de barras de ferro
    for x, z, r, h, gaiola in PILARES:
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                if dx * dx + dz * dz <= r * r + r:
                    cmds.append(f"fill {x+dx} 64 {z+dz} {x+dx} {63+h} {z+dz} minecraft:obsidian")
        topo = 64 + h
        if gaiola:
            cmds.append(f"fill {x-2} {topo} {z-2} {x+2} {topo+3} {z+2} minecraft:iron_bars hollow")
        cmds.append(f'summon end_crystal {x+0.5} {topo} {z+0.5} {{ShowBottom:1b,Invulnerable:1b,Tags:["pm_cine"]}}')
    # os nove, virados pro centro
    for b, n, c in MONSTROS:
        if c is None:
            continue
        p = ponto(b, RAIO)
        yaw = yaw_para_centro(p)
        cmds.append(c.format(p=f"{p[0]:.2f} {p[1]:.2f} {p[2]:.2f}", yaw=f"{yaw:.1f}"))
    for tag, b in (("ent5", 120), ("ent9", 240)):
        p = ponto(b, RAIO)
        cmds.append(f"data merge entity @e[tag={tag},limit=1] {{NoAI:1b,Silent:1b}}")
        cmds.append(f"tp @e[tag={tag},limit=1] {p[0]:.2f} {p[1]:.2f} {p[2]:.2f} facing {C[0]} {C[1]+1.5} {C[2]}")
    return cmds


def mobs_cliente():
    out = []
    for b, n, _c in MONSTROS:
        if n not in MOBS_CLIENTE:
            continue
        tipo, h = MOBS_CLIENTE[n]
        p = ponto(b, RAIO)
        m = Mob(n, tipo, (p[0], p[1] + h / 2, p[2]), auto_walk=False)
        m.key(0.0, yaw=yaw_para_centro(p), shadow_y=p[1])
        out.append(m)
    return out


def problems():
    p = Ator("problems", skin("problems"), tuple(C), yaw=0, energy=1.15)
    p.pose(0.0, "smug")
    p.talk(0.25, 3.0, text="Eu conversei com as entidades de terror do Minecraft")
    p.pose(1.5, "mostra")
    p.pose(3.15, "abraca")       # braços abertos: "olha quem tá aqui"
    # olha para os dois do lado da câmera (cabeça ±20°: o rosto continua de frente para a lente)
    p.look(3.35, ponto(160, RAIO, 2.3), 0.6)
    p.look(4.7, ponto(200, RAIO, 1.6), 0.7)
    p.look(5.9, None)
    p.pose(6.0, "smug")
    return p.build(T1 + T2)


def com_foco(move, inicial, racks, aperture):
    """Foco por pontos do mundo: começa em `inicial`; cada (t0, t1, ponto) puxa o foco até o ponto entre t0 e t1 (segundos
    do plano), interpolando em dioptrias (1/z), como um follow-focus de verdade."""
    from cinecam.camlib import forward
    dur = move.duration

    def f(o, tau):
        o = dict(o)
        t = tau * dur
        pos = np.stack([o["x"], o["y"], o["z"]], axis=-1)
        fwd = forward(o["yaw"], o["pitch"])
        dist = lambda p: np.maximum(np.sum((np.asarray(p, float)[None, :] - pos) * fwd, axis=-1), 0.2)
        inv = 1.0 / dist(inicial)
        for a, b, p in racks:
            s = np.clip((t - a) / (b - a), 0.0, 1.0)
            s = s * s * (3 - 2 * s)
            inv = (1 - s) * inv + s / dist(p)
        o["focus"] = 1.0 / inv
        a0, a1 = aperture
        o["aperture"] = a0 + (a1 - a0) * np.clip(tau, 0, 1)
        return o
    return move.map(f)


def camera():
    rig = Rig(fps=FPS, subframes=SUB, shutter=0.5)
    face = C + [0, 1.52, 0]
    # A: close no rosto, push-in em ARCO (193° -> 182°): o bokeh do fogo e dos monstros desliza atrás dele
    a = track([ponto(193, 2.95, 1.63), ponto(187, 2.45, 1.62), ponto(182, 2.05, 1.6)], tuple(face), T1, ease="smooth",
              fov=(50, 46)).with_handheld("subtle").with_dof(focus=tuple(face), aperture=0.6)
    rig.add(a)
    # B: sai baixa do pé dele, recua por entre o Verity Demon (160) e o Muffin (200), sobe e abre na roda inteira
    # termina NO EIXO (180°): o Problems fica no vão entre o Verity Demon (160) e o Muffin (200), sem ninguém na frente
    pts = [ponto(184, 3.3, 0.75), ponto(181, 6.6, 1.95), ponto(180, 11.2, 5.2), ponto(180, 15.5, 8.6)]
    peito, centro = C + [0, 1.25, 0], C + [0, 0.6, -0.8]
    sai = (0.2, 0.5, 0.25, 1.0)          # sai com velocidade do corte e assenta devagar (sem o ataque seco do launch)
    e = ease_fn(sai)
    mira = lambda tau: peito + (centro - peito) * e(np.asarray(tau))[:, None]
    b = track(pts, mira, T2, ease=sai, fov=(66, 56), roll=(-3.0, 0.0)).with_shake([(0.0, 0.9, 0.28)])
    # foco salta pelas camadas da roda: Problems -> Gato (mais perto, à direita) -> Cavalo (branco, lá atrás) -> Problems
    gato, cavalo = ponto(120, RAIO, 1.6), ponto(40, RAIO, 2.2)
    b = com_foco(b, tuple(face), [(0.85, 1.35, gato), (1.8, 2.35, cavalo), (2.95, 3.5, face)], aperture=(0.62, 0.34))
    rig.add(b, cut=True)
    return rig


# Hora 12500 (05/11): luz do céu 7 - o end stone aparece claro até a névoa (a 18000 o chão longe das luzes ficava preto e
# parecia vazio); o preset pinta o céu de vermelho por cima.
# Clima só deste take: céu e névoa cor de sangue CLAROS o bastante para as colunas de fumaça (quase pretas) virarem
# silhueta contra o céu; cinzas claras e esporos no ar. Entra no world.json da instância durante o render e sai depois.
PRESET = {"_desc": "take do circulo (cinecam): ceu de sangue, fumaca preta em silhueta, cinzas claras e esporos",
          "fogColor": "#5a0d12", "fog": [80, 34], "fogStart": 0.1, "sky": "#3a0609", "skyAlpha": 0.97,
          "grass": "#5c5c57", "foliage": "#3b3b38", "tint": 0.0, "time": 12500, "thunder": 0, "fade": False,
          "smokeColor": "#0a0203",
          "particles": [{"type": "minecraft:white_ash", "rate": 10, "radius": 14, "y": [0, 10]},
                        {"type": "minecraft:ash", "rate": 5, "radius": 14, "y": [0, 10]},
                        {"type": "minecraft:crimson_spore", "rate": 4, "radius": 12, "y": [0, 6]},
                        {"type": "minecraft:smoke", "rate": 2, "radius": 10, "y": [0.1, 1], "ground": True}]}


def run_game_instancia(job_json, mode="film", xmx="4G", timeout_s=3600, log=None):
    """Roda o job dentro da instância do Modrinth (com os mods do vídeo) e devolve tudo como estava."""
    import json
    if any("profiles\\Portal Macabro" in l for l in _javas()):
        raise RuntimeError("a instância Portal Macabro está aberta: feche o jogo")
    jar = INST / "mods" / CINE_JAR.name
    txt = INST / "cinecam-job.txt"
    wj = INST / "config/portalmacabro/world.json"
    wj_antes = wj.read_text(encoding="utf-8")
    d = json.loads(wj_antes)
    d["presets"]["circulo"] = PRESET
    antes = {p.name for p in (INST / "saves").iterdir()}
    shutil.copy2(CINE_JAR, jar)
    txt.write_text(str(job_json), encoding="utf-8")
    wj.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
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
        for p in (INST / "saves").iterdir():           # só o mundo temporário que o CineCam criou agora
            if p.name not in antes and p.name.startswith("cinecam-"):
                shutil.rmtree(p, ignore_errors=True)


def _javas():
    out = subprocess.run(["powershell", "-NoProfile", "-Command",
                          "Get-CimInstance Win32_Process -Filter \"Name='javaw.exe' OR Name='java.exe'\" | ForEach-Object { $_.CommandLine }"],
                         capture_output=True, text=True).stdout
    return out.splitlines()


# grade do take: o "cinematic" com o pé e os meios levantados (a noite de sangue ficava turva), bloom maior nas lanternas
post.PRESETS["portal"] = dict(curves="0/0.01 0.1/0.13 0.5/0.56 0.85/0.88 1/0.97", sat=1.1, contrast=1.06, split_tone=True,
                              bloom=0.22, bloom_radius=28, vignette=0.24, grain=4, sharpen=0.4, ca=1)

if __name__ == "__main__":
    R.run_game = run_game_instancia
    rig = camera()
    scene = Scene(time=12500, weather="clear", anchor=tuple(C + [0, 4, 4]), commands=comandos(), settleTicks=80)
    world = World(mode="fresh", preset="flat", groundY=64, structures=False)
    settings = Settings(renderDistance=8, simulationDistance=6, worldTicks=True, gamma=1.0, clouds=False)
    info = render(rig, NOME, scene=scene, world=world, settings=settings, size=SIZE, grade="portal",
                  anim=Anim([problems()], mobs=mobs_cliente()), blur=not RASCUNHO, dof=None, checar=False)
    print(info.get("final"), info.get("report", {}).get("warnings"))
