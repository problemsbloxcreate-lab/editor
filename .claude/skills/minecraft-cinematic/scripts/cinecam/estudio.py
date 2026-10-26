"""estudio: renderiza no CineCam uma cena EXPORTADA do estúdio do Shorts (CINE_EXPORT, site/index.html), exatamente como ela está
lá (26/10/2026, regra do dono: "manter todo o fluxo; só o visual passa a ser feito pela skill cinematic").

O estúdio continua mandando em tudo: câmera final (manual, planos, zoom/distância/altura, tremor), atuação e ossos de cada um, skin
escolhida (inclusive a troca "só nesta cena"), item na mão, mobs, hora e lua, blocos do mapa do vídeo. Aqui só se traduz para o
Minecraft de verdade (corpo que dobra, luz real, motion blur/desfoque opcionais, anti-aliasing) — nada é redirigido.  Cor, filtros,
brilho, visual, legendas e inserts continuam no estúdio, por cima do vídeo (MINE_LINHA).

    from cinecam.estudio import shot_da_cena, comandos_do_mundo
    sh = shot_da_cena(cena, mundo, efeitos={"blur": True, "dof": False}, pasta_skins=...)
    Sessao(...).render(sh)

Coordenadas: estúdio (x, y, z) em blocos, y=0 = pés no chão (grama em y=-1) → jogo (x, y+64, z).  Ossos já vêm na convenção do
ModelPart (ZYX, graus); dobra (cotovelo/joelho) em graus com o sinal do Body; tronco = [frente, torção, lado] do estúdio.
"""
from __future__ import annotations

import base64
import hashlib
import math
import os
import zlib
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

from .actors import Anim, Mob, POSE, PN
from .atua import _Baked
from .camlib import Move, Rig
from .render import Scene, Settings, Shot
from .sets import _fill_chunks

Y_OFF = 64
HZ = 120
# tipo do estúdio (MOB_DEF) → entidade do jogo
MOBS = {"zumbi": "zombie", "husk": "husk", "afogado": "drowned", "esqueleto": "skeleton", "stray": "stray",
        "witherEsqueleto": "wither_skeleton", "creeper": "creeper", "porco": "pig", "vaca": "cow", "ovelha": "sheep",
        "galinha": "chicken", "lobo": "wolf", "gato": "cat", "aranha": "spider", "aranhaCaverna": "cave_spider", "slime": "slime",
        "enderman": "enderman", "golem": "iron_golem", "aldeao": "villager", "zumbiAldeao": "zombie_villager", "piglin": "piglin",
        "bruxa": "witch", "ghast": "ghast", "blaze": "blaze", "coelho": "rabbit", "abelha": "bee", "pillager": "pillager",
        "vindicador": "vindicator", "evocador": "evoker", "golemNeve": "snow_golem", "ursoPolar": "polar_bear", "raposa": "fox",
        "cavalo": "horse", "panda": "panda", "papagaio": "parrot", "wither": "wither", "warden": "warden", "polvo": "squid",
        "cabra": "goat", "lhama": "llama", "tartaruga": "turtle", "axolote": "axolotl", "morcego": "bat", "golfinho": "dolphin",
        "dragao": "ender_dragon", "magma": "magma_cube", "phantom": "phantom", "shulker": "shulker"}


# ------------------------------------------------------------------------------------------------------------ interpolação
def _catmull(t_src: np.ndarray, v: np.ndarray, t_dst: np.ndarray) -> np.ndarray:
    """Catmull-Rom (uniforme no índice) de uma série amostrada a fps fixo: velocidade contínua entre os quadros do estúdio
    (a linear quebrava o movimento a cada 1/30 s e o motion blur mostrava a quina)."""
    n = len(t_src)
    if n < 3:
        return np.stack([np.interp(t_dst, t_src, v[:, c]) for c in range(v.shape[1])], 1)
    dt = (t_src[-1] - t_src[0]) / (n - 1)
    u = np.clip((t_dst - t_src[0]) / dt, 0, n - 1 - 1e-9)
    i = np.floor(u).astype(int)
    f = (u - i)[:, None]
    P = np.concatenate([v[:1], v, v[-1:]], 0)
    p0, p1, p2, p3 = P[i], P[i + 1], P[i + 2], P[i + 3]
    return 0.5 * ((2 * p1) + (-p0 + p2) * f + (2 * p0 - 5 * p1 + 4 * p2 - p3) * f ** 2 + (-p0 + 3 * p1 - 3 * p2 + p3) * f ** 3)


def _unwrap_cols(a: np.ndarray, cols: Sequence[int]):
    for c in cols:
        a[:, c] = np.degrees(np.unwrap(np.radians(a[:, c])))


# ------------------------------------------------------------------------------------------------------------ mundo
def comandos_do_mundo(M: Dict, margem: int = 120) -> List[str]:
    """Blocos do vídeo → comandos do jogo (y + 64).  Blocos soltos viram fills por fileira (rápido); fora da área, um chão de
    grama até `margem` para o horizonte não ficar vazio (o estúdio também tem chão em volta)."""
    cmds: List[str] = ["gamerule doMobSpawning false", "gamerule doDaylightCycle false", "gamerule doWeatherCycle false",
                       "kill @e[type=!player]"]
    bl = M.get("blocos") or []
    fills = M.get("fills") or []
    xs = [b[0] for b in bl] + [f[0] for f in fills] + [f[3] for f in fills]
    zs = [b[2] for b in bl] + [f[2] for f in fills] + [f[5] for f in fills]
    if not xs:
        return cmds
    x0, x1, z0, z1 = min(xs), max(xs), min(zs), max(zs)
    X0, X1, Z0, Z1 = x0 - margem, x1 + margem, z0 - margem, z1 + margem
    # terreno limpo + chão em volta (o mundo do jogo é plano: só o que o estúdio tem aparece)
    cmds += _fill_chunks(X0, Y_OFF - 1, Z0, X1, Y_OFF - 1, Z1, "grass_block")
    cmds += _fill_chunks(X0, Y_OFF - 4, Z0, X1, Y_OFF - 2, Z1, "dirt")
    cmds += _fill_chunks(x0 - 2, Y_OFF, z0 - 2, x1 + 2, Y_OFF + 40, z1 + 2, "air")
    for f in fills:
        nm = str(f[6]).replace("minecraft:", "")
        cmds += _fill_chunks(int(f[0]), int(f[1]) + Y_OFF, int(f[2]), int(f[3]), int(f[4]) + Y_OFF, int(f[5]), nm)
    # blocos soltos: agrupa fileiras em x do mesmo bloco (y, z iguais e x seguidos) — 5–20x menos comandos
    rows: Dict[Tuple[int, int, str], List[int]] = {}
    for b in bl:
        rows.setdefault((int(b[1]), int(b[2]), str(b[3]).replace("minecraft:", "")), []).append(int(b[0]))
    tail: List[str] = []
    for (y, z, nm), xs_ in rows.items():
        xs_ = sorted(set(xs_))
        a = p = xs_[0]
        for x in xs_[1:] + [None]:
            if x is not None and x == p + 1:
                p = x
                continue
            cmd = (f"setblock {a} {y + Y_OFF} {z} minecraft:{nm}" if a == p else f"fill {a} {y + Y_OFF} {z} {p} {y + Y_OFF} {z} minecraft:{nm}")
            # o que depende de apoio (flor, tocha, porta, trigo, escada de mão) vai por último, depois do chão e das paredes
            (tail if any(w in nm for w in ("torch", "door", "flower", "grass", "poppy", "dandelion", "wheat", "ladder", "lantern",
                                           "carpet", "rail", "sapling", "button", "lever", "sign", "pane", "fence")) else cmds).append(cmd)
            if x is not None:
                a = p = x
    return cmds + tail


# ------------------------------------------------------------------------------------------------------------ skins
def _skin_png(k: str, d: str, pasta: str) -> str:
    os.makedirs(pasta, exist_ok=True)
    p = os.path.join(pasta, k + ".png")
    if not os.path.exists(p):
        raw = base64.b64decode(d.split(",", 1)[1])
        with open(p, "wb") as f:
            f.write(raw)
    return p


def _blink(nome: str, tg: np.ndarray) -> np.ndarray:
    rng = np.random.default_rng(zlib.crc32(("blink:" + nome).encode()))
    b = np.zeros(len(tg))
    t = float(rng.uniform(0.3, 1.4))
    while t < tg[-1]:
        u = tg - t
        b = np.maximum(b, np.where((u >= 0) & (u < 0.05), u / 0.05, 0))
        b = np.maximum(b, np.where((u >= 0.05) & (u < 0.09), 1.0, 0))
        b = np.maximum(b, np.where((u >= 0.09) & (u < 0.17), 1 - (u - 0.09) / 0.08, 0))
        t += float(rng.uniform(2.2, 4.6))
    return b


# ------------------------------------------------------------------------------------------------------------ cena
def _atores(X: Dict, tq: np.ndarray, tg: np.ndarray, pasta_skins: str) -> List[_Baked]:
    Q = X["quadros"]
    nomes: List[str] = []
    for q in Q:
        for n in q["g"]:
            if n not in nomes:
                nomes.append(n)
    out = []
    for nome in nomes:
        rows = np.zeros((len(Q), PN))
        vis = np.zeros(len(Q))
        skin, item, slim = None, None, False
        last = None
        for i, q in enumerate(Q):
            g = q["g"].get(nome) or last
            if g is None:
                continue
            if nome in q["g"]:
                vis[i] = 1
                last = g
            r = rows[i]
            r[POSE["x"]], r[POSE["y"]], r[POSE["z"]] = g["p"][0], g["p"][1] + Y_OFF, g["p"][2]
            r[POSE["yaw"]] = g["yaw"]
            r[POSE["lean"]], r[POSE["roll"]] = -g.get("rx", 0.0), -g.get("rz", 0.0)
            e = g.get("esc") or [1, 1, 1]
            r[POSE["sx"]], r[POSE["sy"]], r[POSE["sz"]] = e
            O = g["ossos"]
            for ch, k in (("head", "cabeca"), ("rarm", "braco_d"), ("larm", "braco_e"), ("rleg", "perna_d"), ("lleg", "perna_e")):
                r[POSE[ch + "_x"]], r[POSE[ch + "_y"]], r[POSE[ch + "_z"]] = O[k]
            d = g.get("dobra") or [0, 0, 0, 0]
            r[POSE["rarm_bend"]], r[POSE["larm_bend"]], r[POSE["rleg_bend"]], r[POSE["lleg_bend"]] = d
            tr = g.get("tronco") or [0, 0, 0]
            r[POSE["torso_x"]], r[POSE["torso_y"]], r[POSE["torso_z"]] = tr[0], -tr[1], -tr[2]
            r[POSE["hop"]] = g.get("dy", 0.0)
            r[POSE["item"]] = 1.0 if g.get("mao") else 0.0
            if g.get("mao") and not item:
                item = "minecraft:" + g["mao"][0].replace("minecraft:", "")
            if g.get("skin") and not skin:
                skin = g["skin"]
        for c in ("belly", "belly_y", "head", "rarm_len", "larm_len", "rleg_len", "lleg_len"):
            rows[:, POSE[c]] = 1.0
        rows[:, POSE["vbelly_y"]], rows[:, POSE["vbelly_out"]], rows[:, POSE["vbelly_vox"]] = 7, 3, 1
        _unwrap_cols(rows, [POSE[n] for n in POSE if n.endswith(("_x", "_y", "_z")) and n not in ("x", "y", "z")] + [POSE["yaw"]])
        ch = _catmull(tq, rows, tg)
        # quem não está no quadro some (escala 0) — sem interpolar a entrada/saída
        v = np.interp(tg, tq, vis) > 0.5
        for c in ("sx", "sy", "sz"):
            ch[:, POSE[c]] = np.where(v, ch[:, POSE[c]], 0.0)
        ch[:, POSE["item"]] = np.interp(tg, tq, rows[:, POSE["item"]])
        ch[:, POSE["blink"]] = _blink(nome, tg)
        ch[:, POSE["mouth"]] = 0.0
        ground = float(np.min(rows[vis > 0, POSE["y"]])) if vis.any() else Y_OFF
        ch[:, POSE["shadow_y"]] = np.where(v, ground, 0.0)
        sk = (X.get("skins") or {}).get(skin) if skin else None
        if not sk:
            continue
        a = _Baked(nome, _skin_png(skin, sk["d"], pasta_skins), tuple(rows[0, :3]), float(rows[0, 3]), bool(sk.get("slim")), item,
                   False, "auto")
        _pe_no_chao(ch, tg, ground, bool(sk.get("slim")))
        a.set_grid(tg, ch)
        from .colisao import auto_fix_self
        a.colisao_resto = auto_fix_self(a, float(tg[-1]))
        out.append(a)
    return out


def _pe_no_chao(ch: np.ndarray, tg: np.ndarray, ground: float, slim: bool):
    """Pé nunca afunda no chão: o joelho do Minecraft (dobra de 2 px) desce um pouco diferente do estúdio; quando a ponta da
    canela passa do chão, o corpo sobe exatamente o que afundou (suavizado, sem tranco).  Só perto do chão (pulo não mexe)."""
    from .colisao import boxes
    step = max(1, int(HZ / 30))
    idx = np.arange(0, len(tg), step)
    lift = np.zeros(len(idx))
    for j, i in enumerate(idx):
        p = ch[i]
        if p[POSE["sx"]] <= 0.01 or p[POSE["y"]] + p[POSE["hop"]] > ground + 0.3:
            continue
        B = boxes(p, slim)
        low = 1e9
        for part in ("leg_loR", "leg_loL"):
            M, lo, hi = B[part]
            for x in (lo[0], hi[0]):
                for z in (lo[2], hi[2]):
                    low = min(low, (M @ np.array([x, hi[1], z, 1.0]))[1])
        lift[j] = max(0.0, ground - low)
    if not lift.any():
        return
    k = np.hanning(7); k /= k.sum()
    env = np.convolve(np.maximum.accumulate(lift[::-1])[::-1] * 0 + lift, k, mode="same")
    env = np.maximum(env, lift)
    ch[:, POSE["hop"]] += np.interp(tg, tg[idx], env)


def _mobs(X: Dict, tq: np.ndarray, falta: List[str]) -> List[Mob]:
    Q = X["quadros"]
    keys: List[str] = []
    for q in Q:
        for m in q.get("m", []):
            if m["k"] not in keys:
                keys.append(m["k"])
    out = []
    for k in keys:
        tipo = k.split("|")[0]
        mc = MOBS.get(tipo)
        if not mc:
            falta.append(f"mob {tipo} sem equivalente no jogo")
            continue
        h = Mob.height(mc)
        rows = np.zeros((len(Q), 15))
        last = None
        for i, q in enumerate(Q):
            m = next((x for x in q.get("m", []) if x["k"] == k), None)
            if m is None:
                if last is not None:
                    rows[i] = last; rows[i, 6:9] = 0
                continue
            e = m.get("esc", 1.0)
            rows[i, 0], rows[i, 1], rows[i, 2] = m["p"][0], m["p"][1] + Y_OFF + h * e / 2, m["p"][2]
            rows[i, 3] = m["yaw"]
            rows[i, 5] = -m.get("rz", 0.0)
            rows[i, 6:9] = e
            rows[i, 9] = m["p"][1] + Y_OFF
            last = rows[i].copy()
        rows[:, 3] = np.degrees(np.unwrap(np.radians(rows[:, 3])))

        def fn(times, rows=rows):
            o = np.stack([np.interp(times, tq, rows[:, c]) for c in range(15)], 1)
            vis = np.interp(times, tq, (rows[:, 6] > 0).astype(float)) > 0.5
            o[:, 6:9] = np.where(vis[:, None], o[:, 6:9], 0.0)
            o[:, 11] = 0.0                       # idade: Mob.at põe 20·t
            return o
        out.append(Mob(k.replace("|", "_"), "minecraft:" + mc, tuple(rows[0, :3]), fn=fn))
    return out


def _camera(X: Dict, tq: np.ndarray, atores: Sequence[_Baked], efeitos: Dict) -> Move:
    Q = X["quadros"]
    P = np.array([q["cam"]["p"] for q in Q], float)
    L = np.array([q["cam"]["l"] for q in Q], float)
    F = np.array([[q["cam"]["fov"], q["cam"].get("roll", 0.0)] for q in Q], float)
    T = float(X["dur"])
    dof = bool(efeitos.get("dof")) or X.get("visual") == "bonito"

    def fn(tau):
        t = np.asarray(tau, float) * T
        p = _catmull(tq, P, t)
        l = _catmull(tq, L, t)
        fr = np.stack([np.interp(t, tq, F[:, 0]), np.interp(t, tq, F[:, 1])], 1)
        d = l - p
        yaw = np.degrees(np.unwrap(np.arctan2(-d[:, 0], d[:, 2])))
        pitch = -np.degrees(np.arctan2(d[:, 1], np.hypot(d[:, 0], d[:, 2])))
        o = {"x": p[:, 0], "y": p[:, 1] + Y_OFF, "z": p[:, 2], "yaw": yaw, "pitch": pitch, "roll": -fr[:, 1], "fov": fr[:, 0]}
        if dof and atores:
            # foco no personagem mais perto do centro da tela (o estúdio não tem foco próprio; é o que o olho segue)
            fw = d / (np.linalg.norm(d, axis=1, keepdims=True) + 1e-9)
            best = np.full(len(t), 1e9); foc = np.full(len(t), 4.0)
            for a in atores:
                q = a.at(t)
                h = np.stack([q[:, 0], q[:, 1] - Y_OFF + 1.5, q[:, 2]], 1)
                v = h - p
                dist = np.linalg.norm(v, axis=1)
                ang = np.arccos(np.clip(np.sum(v * fw, 1) / (dist + 1e-9), -1, 1))
                vis = q[:, POSE["sx"]] > 0.01
                sel = vis & (ang < best)
                best = np.where(sel, ang, best); foc = np.where(sel, dist, foc)
            o["focus"] = np.maximum(foc, 0.5)
            o["aperture"] = np.full(len(t), 0.25)
        return o
    return Move(T, fn, "estudio")


def shot_da_cena(X: Dict, M: Optional[Dict], efeitos: Optional[Dict] = None, pasta_skins: str = ".", qualidade: str = "final",
                 nome: Optional[str] = None) -> Tuple[Shot, List[str]]:
    """Cena exportada → Shot (1080×1920, 30 fps, duração exata).  Devolve (shot, falta): `falta` não vazia = a cena tem algo que
    o Minecraft ainda não desenha (fica no 3D do estúdio)."""
    ef = {"blur": True, "dof": False, **(efeitos or {})}
    falta = list(X.get("falta") or [])
    fps = int(X.get("fps", 30))
    T = float(X["dur"])
    tq = np.arange(len(X["quadros"])) / fps
    tg = np.arange(0, T + 0.25, 1.0 / HZ)
    atores = _atores(X, tq, tg, pasta_skins)
    mobs = _mobs(X, tq, falta)
    rascunho = qualidade != "final"
    rig = Rig(fps=fps, subframes=1 if rascunho else 6, shutter=0.5)
    rig.add(_camera(X, tq, atores, {**ef, "dof": ef["dof"] and not rascunho}))
    q0 = X["quadros"][0]
    nev = next((q.get("nev") for q in X["quadros"] if q.get("nev")), None)      # névoa do estúdio (nevoa/paisagem/shot.fog)
    hora = q0.get("h")
    time_ = (int(hora) if hora is not None else 6000) + 24000 * int(q0.get("lua") or 0)
    cmds = comandos_do_mundo(M) if M else []
    c = np.mean([q0["cam"]["p"]] + [g["p"] for g in q0["g"].values()], axis=0)
    scene = Scene(time=time_, weather="clear", anchor=(float(c[0]), float(c[1]) + Y_OFF + 4, float(c[2])), commands=cmds, settleTicks=40,
                  fog=list(nev) if nev else None)
    gama = X.get("gama", 1.0)                                                  # brilho do jogo escolhido no estúdio (-1 = luz total)
    sh = Shot(nome or f"est_{X.get('id', 'x')}_{int(X.get('n', 0)):02d}", rig=rig, scene=scene,
              settings=Settings(renderDistance=8, simulationDistance=6, worldTicks=True, gamma=1.0 if gama is None or gama < 0 else float(gama)),
              anim=Anim(atores, mobs=mobs), size=(540, 960) if rascunho else (1080, 1920), grade="clean",
              blur=bool(ef["blur"]) and not rascunho, dof=(ef["dof"] or X.get("visual") == "bonito") and not rascunho)
    return sh, falta
