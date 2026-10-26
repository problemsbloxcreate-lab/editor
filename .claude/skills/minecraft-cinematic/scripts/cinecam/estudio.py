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

from .actors import Anim, Mob, POSE, PN, MBN
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


def _pchip(t_src: np.ndarray, v: np.ndarray, t_dst: np.ndarray) -> np.ndarray:
    """Cúbica monótona (Fritsch–Butland) entre os quadros do estúdio: passa por todos e NUNCA passa do ponto.  A Catmull-Rom
    ultrapassava nos degraus de pose do estúdio (a pose troca num quadro) e o membro ia e voltava — o "rollback" do preview."""
    n = len(t_src)
    if n < 3:
        return np.stack([np.interp(t_dst, t_src, v[:, c]) for c in range(v.shape[1])], 1)
    h = (t_src[-1] - t_src[0]) / (n - 1)
    d = np.diff(v, axis=0) / h
    m = np.zeros_like(v)
    a, b = d[:-1], d[1:]
    same = a * b > 0
    m[1:-1] = np.where(same, 2 * a * b / np.where(same, a + b, 1.0), 0.0)
    m[0], m[-1] = d[0], d[-1]
    m[0] = np.where(m[0] * d[0] > 0, m[0], 0.0)
    m[-1] = np.where(m[-1] * d[-1] > 0, m[-1], 0.0)
    u = np.clip((t_dst - t_src[0]) / h, 0, n - 1 - 1e-9)
    i = np.floor(u).astype(int)
    f = (u - i)[:, None]
    y0, y1, m0, m1 = v[i], v[i + 1], m[i] * h, m[i + 1] * h
    f2, f3 = f * f, f * f * f
    return (2 * f3 - 3 * f2 + 1) * y0 + (f3 - 2 * f2 + f) * m0 + (-2 * f3 + 3 * f2) * y1 + (f3 - f2) * m1


def _cortes(P: np.ndarray, lim: float) -> List[int]:
    """Quadros j em que a posição salta para j+1 mais que `lim` blocos (teleporte do estúdio: pérola, montagem, troca de lugar)."""
    if len(P) < 2:
        return []
    d = np.linalg.norm(np.diff(np.asarray(P, float), axis=0), axis=1)
    out = []
    for j in range(len(d)):
        viz = [d[k] for k in (j - 1, j + 1) if 0 <= k < len(d)]
        ref = max(viz) if viz else 0.0
        # teleporte = pulo ISOLADO: muito maior que o passo dos quadros vizinhos (barco a 72 blocos/s anda 2,4 por quadro
        # todo quadro — isso é movimento, não corte)
        if d[j] > lim and d[j] > 3.0 * ref + 0.5:
            out.append(j)
    return out


def _por_trechos(tq: np.ndarray, rows: np.ndarray, tg: np.ndarray, cortes: Sequence[int], fn) -> np.ndarray:
    """fn(tq, rows, tg) em cada trecho entre cortes: nada é interpolado ATRAVÉS de um teleporte (antes o personagem deslizava
    24 blocos em 1/30 s e o motion blur mostrava o rastro).  O corte cai no meio entre os dois quadros — fora da janela do
    obturador (±8 ms do centro), então nenhum quadro mistura os dois lugares."""
    if not cortes:
        return fn(tq, rows, tg)
    out = np.zeros((len(tg), rows.shape[1]))
    ed = [0] + [j + 1 for j in cortes] + [len(tq)]
    tc = [-np.inf] + [(tq[j] + tq[j + 1]) / 2 for j in cortes] + [np.inf]
    for a, b, t0, t1 in zip(ed[:-1], ed[1:], tc[:-1], tc[1:]):
        m = (tg >= t0) & (tg < t1)
        if m.any():
            out[m] = fn(tq[a:b], rows[a:b], tg[m])
    return out


def _suaviza_degraus(rows: np.ndarray, cols: Sequence[int], sigma: float = 1.0):
    """Gaussiana curta (σ = 1 quadro ≈ 33 ms) nos ângulos do corpo: o salto de pose que o estúdio faz num único quadro vira
    uma transição de ~0,1 s; o peso da gaussiana é todo positivo, então nada passa do ponto.  Posição/altura não entram
    (pé no chão e tempo dos contatos ficam exatos)."""
    if len(rows) < 3:
        return
    r = int(np.ceil(3 * sigma))
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2)
    k /= k.sum()
    for c in cols:
        x = np.pad(rows[:, c], r, mode="edge")
        rows[:, c] = np.convolve(x, k, mode="valid")


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
def _atores(X: Dict, tq: np.ndarray, tg: np.ndarray, pasta_skins: str, falta: Optional[List[str]] = None) -> List[_Baked]:
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
            if g.get("mao"):
                it = "minecraft:" + g["mao"][0].replace("minecraft:", "")
                if item and it != item and falta is not None and f"{nome} troca o item da mão" not in falta:
                    falta.append(f"{nome} troca o item da mão")     # o ator do CineCam tem um item só por plano
                item = item or it
                if len(g["mao"]) > 1 and falta is not None and f"{nome} segura dois itens" not in falta:
                    falta.append(f"{nome} segura dois itens")
            if g.get("skin"):
                if skin and g["skin"] != skin and falta is not None and f"{nome} troca de skin" not in falta:
                    falta.append(f"{nome} troca de skin")
                skin = skin or g["skin"]
        for c in ("belly", "belly_y", "head", "rarm_len", "larm_len", "rleg_len", "lleg_len"):
            rows[:, POSE[c]] = 1.0
        rows[:, POSE["vbelly_y"]], rows[:, POSE["vbelly_out"]], rows[:, POSE["vbelly_vox"]] = 7, 3, 1
        ang = [POSE[n] for n in POSE if n.endswith(("_x", "_y", "_z")) and n not in ("x", "y", "z")] + [POSE["yaw"]]
        _unwrap_cols(rows, ang)
        cru = rows.copy()
        sua = ang + [POSE[n] for n in ("rarm_bend", "larm_bend", "rleg_bend", "lleg_bend", "lean", "roll")]
        cortes = _cortes(rows[:, [POSE["x"], POSE["y"], POSE["z"]]], 1.5)

        def _trecho(sg):
            def fn(tq_s, r_s, tg_s):
                r2 = r_s.copy()
                _suaviza_degraus(r2, sua, sg)
                return _pchip(tq_s, r2, tg_s)
            return fn
        ch = _por_trechos(tq, cru, tg, cortes, _trecho(1.0))
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
        from .atua import snaps
        a.colisao_resto = auto_fix_self(a, float(tg[-1]))
        # trava do "rollback" (26/10): nenhum membro pode ir-e-voltar; sobrou tranco → suaviza mais forte (σ 1,8 e 2,6 quadros)
        tcorte = [(tq[j] + tq[j + 1]) / 2 for j in cortes]
        _semcorte = lambda L: [x for x in L if all(abs(x[0] - tc) > 1.5 / fps for tc in tcorte)]
        fps = int(X.get("fps", 30))
        a.trancos = _semcorte(snaps(a, float(X["dur"])))
        for sg in (1.8, 2.6):
            if not a.trancos:
                break
            ch2 = _por_trechos(tq, cru, tg, cortes, _trecho(sg))
            for c in ("sx", "sy", "sz"):
                ch2[:, POSE[c]] = ch[:, POSE[c]]
            for c in ("item", "blink", "mouth", "shadow_y"):
                ch2[:, POSE[c]] = ch[:, POSE[c]]
            _pe_no_chao(ch2, tg, ground, bool(sk.get("slim")))
            a.set_grid(tg, ch2)
            a.colisao_resto = auto_fix_self(a, float(tg[-1]))
            a.trancos = _semcorte(snaps(a, float(X["dur"])))
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


def _barco(X: Dict, tq: np.ndarray) -> Optional[Mob]:
    """O barco do estúdio (cópia do BoatRenderer: mesma translação/escala/rotação) vira a entidade barco do jogo: posição da
    entidade, rotação total do estúdio = 180° − yaw do mob (o renderer do barco já gira 180°), escala (o barco "pula" para
    aparecer) e o remo no mesmo ângulo (rowPaddles do estúdio: t·7 enquanto rema)."""
    Q = X["quadros"]
    if not any(q.get("barco") for q in Q):
        return None
    h = Mob.height("boat")
    rows = np.zeros((len(Q), MBN))
    last = None
    for i, q in enumerate(Q):
        b = q.get("barco")
        if not b:
            if last is not None:
                rows[i] = last; rows[i, 6:9] = 0
            continue
        e = float(b.get("esc", 1.0))
        rows[i, 0], rows[i, 1], rows[i, 2] = b["p"][0], b["p"][1] + Y_OFF + h * e / 2, b["p"][2]
        rows[i, 3] = 180.0 - float(b["ry"])
        rows[i, 6:9] = e
        rows[i, 15] = float(b.get("rema", 0.0))
        last = rows[i].copy()
    if last is None:
        return None
    first = next(i for i, q in enumerate(Q) if q.get("barco"))
    rows[:first] = rows[first]; rows[:first, 6:9] = 0
    rows[:, 3] = np.degrees(np.unwrap(np.radians(rows[:, 3])))
    cc = _cortes(rows[:, :3], 1.5)

    def fn(times, rows=rows):
        o = _por_trechos(tq, rows, np.asarray(times, float), cc, lambda a, r, b: np.stack([np.interp(b, a, r[:, c]) for c in range(MBN)], 1))
        vis = np.interp(times, tq, (rows[:, 6] > 0).astype(float)) > 0.5
        o[:, 6:9] = np.where(vis[:, None], o[:, 6:9], 0.0)
        r = np.interp(times, tq, rows[:, 15])            # remo: contínuo enquanto rema; parado = 0 exato
        o[:, 15] = np.where(np.interp(times, tq, (rows[:, 15] != 0).astype(float)) > 0.5, r, 0.0)
        o[:, 11] = 0.0
        return o
    return Mob("barco", "minecraft:boat", tuple(rows[0, :3]), fn=fn)


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
        rows = np.zeros((len(Q), MBN))
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
            o = np.stack([np.interp(times, tq, rows[:, c]) for c in range(MBN)], 1)
            vis = np.interp(times, tq, (rows[:, 6] > 0).astype(float)) > 0.5
            o[:, 6:9] = np.where(vis[:, None], o[:, 6:9], 0.0)
            o[:, 11] = 0.0                       # idade: Mob.at põe 20·t
            return o
        out.append(Mob(k.replace("|", "_"), "minecraft:" + mc, tuple(rows[0, :3]), fn=fn))
    return out


def _base_mc(yaw, pitch, roll):
    """Frente e "para cima" da câmera do CineCam para (yaw, pitch, roll) em graus (yaw 0 = +z, pitch + = para baixo)."""
    y, p, r = np.radians(yaw), np.radians(pitch), np.radians(roll)
    h = np.stack([-np.sin(y), np.zeros_like(y), np.cos(y)], -1)
    f = h * np.cos(p)[..., None] + np.stack([0 * y, -np.sin(p), 0 * y], -1)
    u0 = h * np.sin(p)[..., None] + np.stack([0 * y, np.cos(p), 0 * y], -1)
    s0 = np.cross(f, u0)
    u = u0 * np.cos(r)[..., None] - s0 * np.sin(r)[..., None]
    return f, u


def _orienta(d: np.ndarray, up: np.ndarray):
    """(frente, para cima) do estúdio → (yaw, pitch, roll) do CineCam.  Perto da vertical o yaw sai do "para cima" (olhando reto
    para baixo, o topo da tela aponta para onde a câmera "está virada"); longe dela, da frente.  Contínuo, sem o giro
    de 90° em 90° que a conta antiga dava na vista de cima (cena "linha dos 300 blocos")."""
    f = d / (np.linalg.norm(d, axis=1, keepdims=True) + 1e-12)
    u = up - np.sum(up * f, 1, keepdims=True) * f
    u /= np.linalg.norm(u, axis=1, keepdims=True) + 1e-12
    sp = np.clip(-f[:, 1], -1, 1)
    cp = np.sqrt(1 - sp ** 2)
    pitch = np.degrees(np.arcsin(sp))
    hf = f[:, [0, 2]] / (cp[:, None] + 1e-12)
    hu = (f * cp[:, None] + u * sp[:, None])[:, [0, 2]]
    hu /= np.linalg.norm(hu, axis=1, keepdims=True) + 1e-12
    w = np.clip((cp - 0.02) / 0.06, 0, 1)[:, None]          # só nos últimos ~5° antes da vertical
    w = w * w * (3 - 2 * w)
    hv = hf * w + hu * (1 - w)
    yaw = np.degrees(np.unwrap(np.arctan2(-hv[:, 0], hv[:, 1])))
    f0, u0 = _base_mc(yaw, pitch, np.zeros_like(yaw))
    roll = np.degrees(np.unwrap(np.arctan2(-np.sum(np.cross(u0, u) * f0, 1), np.sum(u0 * u, 1))))
    return yaw, pitch, roll


def confere_camera(X: Dict, sh) -> List[str]:
    """Trava (26/10, "nunca sem chão"): a câmera que vai para o Minecraft aponta para o MESMO lugar que a do estúdio em todo
    quadro (frente < 1,5°, topo da tela < 3°).  Erro aqui = a cena não é desenhada (fica no 3D), nunca sai torta."""
    Q = X["quadros"]
    if not Q or not all("u" in q["cam"] for q in Q):
        return []
    fps = int(X.get("fps", 30))
    T = float(X["dur"])
    mv = sh.rig_camera
    rows = mv.eval(np.clip(np.arange(len(Q)) / fps / T, 0, 1))
    out = []
    for i, q in enumerate(Q):
        k = i
        f1, u1 = _base_mc(np.array([rows["yaw"][k]]), np.array([rows["pitch"][k]]), np.array([rows["roll"][k]]))
        d = np.subtract(q["cam"]["l"], q["cam"]["p"])
        f = d / (np.linalg.norm(d) + 1e-12)
        u = np.asarray(q["cam"]["u"], float)
        u = u - np.dot(u, f) * f
        u /= np.linalg.norm(u) + 1e-12
        ef = np.degrees(np.arccos(np.clip(np.dot(f, f1[0]), -1, 1)))
        eu = np.degrees(np.arccos(np.clip(np.dot(u, u1[0]), -1, 1)))
        if ef > 1.5 or eu > 3.0:
            out.append(f"quadro {i}: frente {ef:.1f}°, topo {eu:.1f}°")
    return out


def distancia_visao(X: Dict) -> Tuple[int, float]:
    """(chunks de distância, maior distância câmera→chão visível em blocos) para enxergar o chão que a câmera do estúdio
    enxerga (a vista de cima a 300 blocos precisa de ~18 chunks e de névoa empurrada para longe)."""
    far = 0.0
    far3 = 0.0
    for q in X["quadros"][::3]:
        c = q["cam"]
        p = np.asarray(c["p"], float)
        d = np.subtract(c["l"], p)
        f = d / (np.linalg.norm(d) + 1e-12)
        u = np.asarray(c.get("u") or [0, 1, 0], float)
        u = u - np.dot(u, f) * f
        u /= np.linalg.norm(u) + 1e-12
        rt = np.cross(f, u)
        tv = np.tan(np.radians(float(c.get("fov", 70)) / 2))
        for sx in (-1, 0, 1):
            for sy in (-1, 0, 1):
                r = f + u * sy * tv + rt * sx * tv * 9 / 16
                if r[1] < -1e-3 and p[1] > 40:         # câmera alta, raio que desce: onde bate no chão (y = 0 do estúdio)
                    hit = p + r * (-p[1] / r[1])
                    if np.linalg.norm(hit - p) > 3 * p[1]:
                        continue                          # quase no horizonte: o estúdio também some na névoa
                    far = max(far, min(400.0, float(np.hypot(*(hit - p)[[0, 2]]))))
                    far3 = max(far3, min(500.0, float(np.linalg.norm(hit - p))))
    # o jogo corta pela distância EM LINHA RETA (não só na horizontal): a 300 blocos de altura o chão está a ~300–390 blocos
    return int(np.clip(np.ceil(max(far, far3) / 16) + 2, 8, 32)), far3


def _camera(X: Dict, tq: np.ndarray, atores: Sequence[_Baked], efeitos: Dict) -> Move:
    Q = X["quadros"]
    P = np.array([q["cam"]["p"] for q in Q], float)
    L = np.array([q["cam"]["l"] for q in Q], float)
    F = np.array([[q["cam"]["fov"], q["cam"].get("roll", 0.0)] for q in Q], float)
    T = float(X["dur"])
    dof = bool(efeitos.get("dof")) or X.get("visual") == "bonito"

    U = np.array([q["cam"]["u"] for q in Q], float) if all("u" in q["cam"] for q in Q) else None

    cc = _cortes(P, 3.0)

    def fn(tau):
        t = np.asarray(tau, float) * T
        p = _por_trechos(tq, P, t, cc, _pchip)
        l = _por_trechos(tq, L, t, cc, _pchip)
        fr = np.stack([np.interp(t, tq, F[:, 0]), np.interp(t, tq, F[:, 1])], 1)
        d = l - p
        if U is not None:
            yaw, pitch, roll = _orienta(d, _por_trechos(tq, U, t, cc, _pchip))
        else:                                       # exportação antiga (sem cam.u): só serve longe da vertical
            yaw = np.degrees(np.unwrap(np.arctan2(-d[:, 0], d[:, 2])))
            pitch = -np.degrees(np.arctan2(d[:, 1], np.hypot(d[:, 0], d[:, 2])))
            roll = -fr[:, 1]
        o = {"x": p[:, 0], "y": p[:, 1] + Y_OFF, "z": p[:, 2], "yaw": yaw, "pitch": pitch, "roll": roll, "fov": fr[:, 0]}
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


def _portas(X: Dict, tq: np.ndarray) -> List:
    """Portas que abrem/fecham na cena (estúdio: a da base em "sair da base") → Scene.blocks: no instante em que a porta do estúdio
    passa da metade, a do Minecraft abre (porta do jogo não tem meio-termo)."""
    est: Dict[Tuple[int, int], List] = {}
    for i, q in enumerate(X["quadros"]):
        for x, z, a, f, h in q.get("portas") or []:
            est.setdefault((int(x), int(z)), [f, h, np.zeros(len(tq))])[2][i] = a
    ev = []
    for (x, z), (f, h, a) in est.items():
        aberta = a >= 0.5
        for i in range(len(tq)):
            if (i == 0 and aberta[0]) or (i > 0 and aberta[i] != aberta[i - 1]):
                for y, half in ((1, "lower"), (2, "upper")):
                    ev.append([float(tq[i]), x, y + Y_OFF, z, f"minecraft:oak_door[half={half},facing={f},hinge={h},open={str(bool(aberta[i])).lower()}]"])
    return ev


def shot_da_cena(X: Dict, M: Optional[Dict], efeitos: Optional[Dict] = None, pasta_skins: str = ".", qualidade: str = "final",
                 nome: Optional[str] = None) -> Tuple[Shot, List[str]]:
    """Cena exportada → Shot (1080×1920, 30 fps, duração exata).  Devolve (shot, falta): `falta` não vazia = a cena tem algo que
    o Minecraft ainda não desenha (fica no 3D do estúdio)."""
    ef = {"blur": True, "dof": False, **(efeitos or {})}
    falta = list(X.get("falta") or [])
    fps = int(X.get("fps", 30))
    T = float(X["dur"])
    # só os quadros DENTRO da cena: o último do estúdio antigo (≤ 26/10) caía no começo da cena seguinte (outro lugar) e borrava o fim
    X = dict(X, quadros=[q for i, q in enumerate(X["quadros"]) if i / fps <= T + 1e-6])
    tq = np.arange(len(X["quadros"])) / fps
    tg = np.arange(0, T + 0.25, 1.0 / HZ)
    atores = _atores(X, tq, tg, pasta_skins, falta)
    mobs = _mobs(X, tq, falta)
    bt = _barco(X, tq)
    if bt is not None:
        mobs.append(bt)
    rascunho = qualidade != "final"
    rig = Rig(fps=fps, subframes=1 if rascunho else 6, shutter=0.5)
    mv = _camera(X, tq, atores, {**ef, "dof": ef["dof"] and not rascunho})
    rig.add(mv)
    q0 = X["quadros"][0]
    nev = next((q.get("nev") for q in X["quadros"] if q.get("nev")), None)      # névoa do estúdio (nevoa/paisagem/shot.fog)
    hora = q0.get("h")
    time_ = (int(hora) if hora is not None else 6000) + 24000 * int(q0.get("lua") or 0)
    cmds = comandos_do_mundo(M) if M else []
    c = np.mean([q0["cam"]["p"]] + [g["p"] for g in q0["g"].values()], axis=0)
    # câmera alta (vista de cima): o chão fica a centenas de blocos — a névoa do jogo apagaria tudo e as nuvens (y 192) ficariam na
    # frente; o estúdio mostra o mapa limpo.  Névoa vai para além do chão mais longe visto; nuvens só com a câmera abaixo delas.
    rd, longe = distancia_visao(X)
    alta = max(q["cam"]["p"][1] for q in X["quadros"]) + Y_OFF > 170
    if not nev and longe > rd * 16 * 0.7:
        nev = [round(longe * 1.15, 1), round(longe * 1.5, 1)]
    if alta:                                   # vista de cima: o servidor manda os chunks em volta da câmera, não do elenco
        cc = np.mean([q["cam"]["p"] for q in X["quadros"]], axis=0)
        c = np.array([cc[0], 6.0, cc[2]])
    scene = Scene(time=time_, weather="clear", anchor=(float(c[0]), float(c[1]) + Y_OFF + 4, float(c[2])), commands=cmds, settleTicks=40,
                  fog=list(nev) if nev else None, blocks=_portas(X, tq))
    gama = X.get("gama", 1.0)                                                  # brilho do jogo escolhido no estúdio (-1 = luz total)
    sh = Shot(nome or f"est_{X.get('id', 'x')}_{int(X.get('n', 0)):02d}", rig=rig, scene=scene,
              settings=Settings(renderDistance=rd, simulationDistance=6, clouds=not alta, worldTicks=True, gamma=1.0 if gama is None or gama < 0 else float(gama)),
              anim=Anim(atores, mobs=mobs), size=(540, 960) if rascunho else (1080, 1920), grade="clean",
              blur=bool(ef["blur"]) and not rascunho, dof=(ef["dof"] or X.get("visual") == "bonito") and not rascunho)
    if falta:
        return sh, falta
    tr = [f"{a.name} {t:.2f}s {k}" for a in atores for (t, k, _) in getattr(a, "trancos", [])]
    if tr:
        raise ValueError("tranco (vai-e-volta) na animação: " + "; ".join(tr[:4]))
    sh.rig_camera = mv
    errc = confere_camera(X, sh)
    if errc:
        raise ValueError("câmera do Minecraft diferente da do estúdio: " + "; ".join(errc[:3]))
    if not all("u" in q["cam"] for q in X["quadros"]) and any(
            abs(np.subtract(q["cam"]["l"], q["cam"]["p"])[1]) > 0.97 * np.linalg.norm(np.subtract(q["cam"]["l"], q["cam"]["p"])) for q in X["quadros"]):
        falta.append("câmera na vertical (exportação antiga, recarregue o estúdio)")
    return sh, falta
