"""colisao: membros e itens NUNCA atravessam corpos ou paredes (26/10/2026, regra do dono: "nunca permita isso").

Cinemática igual à do mod (Actors.drawActor + Body: tronco no quadril, cotovelo/joelho com dobra, item na mão) em caixas:
cabeça, tronco, braço (cima/baixo do cotovelo), perna (coxa/canela), item.  Cada caixa vira uma grade de pontos; um ponto dentro
de outra caixa (com tolerância) = atravessou.

    from cinecam.colisao import auto_fix_self, verificar
    auto_fix_self(actor, T)                 # Ator.build() já chama: abre o braço o mínimo e com suavidade até não entrar no corpo
    problemas = verificar(anim, T, solids)  # personagem × personagem, personagem/item × bloco; render() recusa se houver

Tolerâncias (px do modelo, 16 px = 1 bloco): encostar não é atravessar (0,6 px); mão no rosto (facepalm, pensar) pode encostar
até 1,2 px; pé pode afundar 1 px no chão.
"""
from __future__ import annotations

import math
import re
from typing import Dict, List, Optional, Sequence, Set, Tuple

import numpy as np

from .actors import POSE

ARC = 2.0                     # = Body.ARC no mod
TOL = 0.6                     # px
TOL_FACE = 1.2
NON_SOLID = ("air", "water", "lava", "grass", "fern", "flower", "poppy", "dandelion", "tulip", "orchid", "allium", "bluet", "daisy",
             "cornflower", "lily", "rose", "sugar_cane", "dead_bush", "seagrass", "kelp", "torch", "vine", "snow", "sapling",
             "mushroom", "wheat", "carrots", "potatoes", "beetroots", "rail", "button", "pressure_plate", "carpet", "sign", "banner")


# ------------------------------------------------------------------------------------------------------------------ matrizes 4x4
def _T(x, y, z):
    m = np.eye(4); m[:3, 3] = (x, y, z); return m


def _S(x, y, z):
    return np.diag([x, y, z, 1.0])


def _Rx(a):
    c, s = math.cos(a), math.sin(a); m = np.eye(4); m[1, 1], m[1, 2], m[2, 1], m[2, 2] = c, -s, s, c; return m


def _Ry(a):
    c, s = math.cos(a), math.sin(a); m = np.eye(4); m[0, 0], m[0, 2], m[2, 0], m[2, 2] = c, s, -s, c; return m


def _Rz(a):
    c, s = math.cos(a), math.sin(a); m = np.eye(4); m[0, 0], m[0, 1], m[1, 0], m[1, 1] = c, -s, s, c; return m


D2R = math.pi / 180


def _part(px, py, pz, rx, ry, rz, sx=1.0, sy=1.0, sz=1.0):
    """ModelPart.translateAndRotate em pixels: translate, rotationZYX(z, y, x), scale."""
    return _T(px, py, pz) @ _Rz(rz) @ _Ry(ry) @ _Rx(rx) @ _S(sx, sy, sz)


def _lower(yc, a):
    """Body.lowerFrame em pixels (parte de baixo da dobra)."""
    if abs(a) < 1e-5:
        return np.eye(4)
    s0, s1, k = yc - ARC / 2, yc + ARC / 2, a / ARC
    return _T(0, s0 + math.sin(a) / k, (1 - math.cos(a)) / k) @ _Rx(a) @ _T(0, -s1, 0)


# ------------------------------------------------------------------------------------------------------------------- caixas
def boxes(p: np.ndarray, slim: bool = False, item: bool = False) -> Dict[str, Tuple[np.ndarray, np.ndarray, np.ndarray]]:
    """Caixas de um personagem numa linha de canais: nome -> (M mundo←local em BLOCOS, min px, max px)."""
    g = lambda i, d=0.0: float(p[i]) if len(p) > i else d
    sx, sy, sz = (g(4) or 1), (g(5) or 1), (g(6) or 1)
    W = (_T(g(0), g(1) + g(27), g(2)) @ _Ry((180 - g(3)) * D2R) @ _Rx(g(25) * D2R) @ _Rz(g(28) * D2R)
         @ _S(-1, -1, 1) @ _S(sx, sy, sz) @ _T(0, -1.501, 0) @ _S(1 / 16, 1 / 16, 1 / 16))            # → px do modelo
    tor = _T(0, 12, 0) @ _Ry(g(48) * D2R) @ _Rx(g(47) * D2R) @ _Rz(g(49) * D2R) @ _T(0, -12, 0)
    belly = g(22) or 1.0
    spread = (belly - 1.0) * 4.2
    hs = g(24) or 1.0
    out = {}
    out["head"] = (W @ tor @ _part(0, 0, 0, g(7) * D2R, g(8) * D2R, g(9) * D2R, hs, hs, hs), np.array([-4, -8, -4.]), np.array([4, 0, 4.]))
    out["body"] = (W @ tor @ _S(belly, g(23) or 1.0, belly), np.array([-4, 0, -2.]), np.array([4, 12, 2.]))
    ay = 2.5 if slim else 2.0
    w = 3.0 if slim else 4.0
    for side, sgn, i0, ib in (("R", -1, 10, 43), ("L", 1, 13, 44)):
        M = W @ tor @ _part(sgn * (5 + spread), ay, 0, g(i0) * D2R, g(i0 + 1) * D2R, g(i0 + 2) * D2R)
        x0, x1 = ((-3.0, -3.0 + w) if sgn < 0 else (-1.0, -1.0 + w))
        yc = 4.0
        out["arm_up" + side] = (M, np.array([x0, -2, -2.]), np.array([x1, yc - ARC / 2, 2.]))
        Ml = M @ _lower(yc, g(ib) * D2R)
        out["arm_lo" + side] = (Ml, np.array([x0, yc + ARC / 2, -2.]), np.array([x1, 10, 2.]))
        if side == "R" and item and g(26) > 0.01:
            out["item"] = (Ml, np.array([x0 + 0.5, 8.5, -8.0]), np.array([x1 - 0.5, 12.0, 0.0]))
    for side, sgn, i0, ib in (("R", -1, 16, 45), ("L", 1, 19, 46)):
        M = W @ _part(sgn * 1.9, 12, 0, g(i0) * D2R, g(i0 + 1) * D2R, g(i0 + 2) * D2R)
        yc = 6.0
        out["leg_up" + side] = (M, np.array([-2, 0, -2.]), np.array([2, yc - ARC / 2, 2.]))
        out["leg_lo" + side] = (M @ _lower(yc, g(ib) * D2R), np.array([-2, yc + ARC / 2, -2.]), np.array([2, 12, 2.]))
    return out


def _grid(lo, hi, n=3, inset=0.25):
    a = [np.linspace(lo[k] + inset, hi[k] - inset, n) for k in range(3)]
    g = np.stack(np.meshgrid(*a, indexing="ij"), -1).reshape(-1, 3)
    return np.concatenate([g, np.ones((len(g), 1))], 1)


def _inside(Mw_pts: np.ndarray, box, tol: float) -> np.ndarray:
    """Pontos (mundo, homogêneos) dentro da caixa (M, lo, hi) com a tolerância tol px nas faces."""
    M, lo, hi = box
    loc = (np.linalg.inv(M) @ Mw_pts.T).T[:, :3]
    return np.all((loc > lo + tol) & (loc < hi - tol), axis=1)


# pares que não podem se atravessar no MESMO personagem (vizinhos de junta ficam de fora)
SELF_PAIRS = [("arm_loR", "body"), ("arm_loR", "head"), ("arm_loR", "leg_upR"), ("arm_loR", "leg_upL"), ("arm_loR", "arm_loL"),
              ("arm_loR", "arm_upL"), ("arm_upR", "head"),
              ("arm_loL", "body"), ("arm_loL", "head"), ("arm_loL", "leg_upR"), ("arm_loL", "leg_upL"), ("arm_upL", "head"),
              ("item", "body"), ("item", "head"), ("item", "arm_loL"), ("item", "arm_upL"), ("item", "leg_upR"), ("item", "leg_upL"),
              ("leg_loR", "leg_loL")]


def self_hits(p: np.ndarray, slim=False, item=False) -> List[Tuple[str, str]]:
    B = boxes(p, slim, item)
    hits = []
    for a, b in SELF_PAIRS:
        if a not in B or b not in B:
            continue
        Ma, lo, hi = B[a]
        if a.startswith("arm_up"):
            lo = lo.copy(); lo[1] = 1.0          # o topo do ombro encosta na cabeça quando ela gira (igual ao jogo): não conta
        pts = (Ma @ _grid(lo, hi).T).T
        tol = TOL_FACE if b == "head" and a.startswith(("arm_lo", "item")) else TOL
        if _inside(pts, B[b], tol).any():
            hits.append((a, b))
    return hits


# --------------------------------------------------------------------------------------------------------- correção automática
def auto_fix_self(actor, T: float, fps: int = 30, max_iter: int = 4) -> List[Tuple[float, str, str]]:
    """Antebraço/mão/item entrando no próprio corpo: abre o braço (rarm_z/larm_z para FORA, no sentido que afasta) o mínimo que
    resolve, com a correção suavizada no tempo (sem tranco).  Altera actor._ch (Actor assado do atua).  Devolve o que sobrou."""
    if not hasattr(actor, "_ch"):
        return []
    tg, ch = actor._tg, actor._ch
    slim, item = actor.slim, bool(actor.item)
    ts = np.arange(0, T, 1.0 / fps)
    for it in range(max_iter):
        rows = np.stack([np.interp(ts, tg, ch[:, c]) for c in range(ch.shape[1])], 1)
        corr = {"R": {}, "L": {}}
        left = []
        for i, p in enumerate(rows):
            hits = self_hits(p, slim, item)
            for side in ("R", "L"):
                mine = [h for h in hits if h[0] in ("arm_lo" + side, "arm_up" + side) or (side == "R" and h[0] == "item")]
                if not mine:
                    continue
                pre = "rarm" if side == "R" else "larm"
                best = None
                # menor mudança que resolve: abrir/fechar o braço (z), levar à frente/atrás (x), girar (y), relaxar o cotovelo
                for d in (4, 8, 12, 18, 25, 35, 45, 60):
                    for nm in ("_z", "_x", "_y", "_bend"):
                        ci = POSE[pre + nm]
                        for sg in ((1, -1) if nm != "_bend" else (1,)):
                            q = p.copy()
                            if nm == "_bend":
                                q[ci] = q[ci] * max(0.0, 1 - d / 60)
                            else:
                                q[ci] += sg * d
                            if not [h for h in self_hits(q, slim, item) if h[0] in ("arm_lo" + side, "arm_up" + side, "item")]:
                                best = (ci, q[ci] - p[ci]); break
                        if best:
                            break
                    if best:
                        break
                if best is None:
                    left.append((round(float(ts[i]), 3),) + mine[0])
                else:
                    corr[side].setdefault(best[0], np.zeros(len(ts)))[i] = best[1]
        if not any(corr["R"]) and not any(corr["L"]):
            return left
        for side in ("R", "L"):
            for ci, c in corr[side].items():
                # envelope: mantém o valor máximo em volta (±0,12 s) e suaviza (rampa ~0,25 s) — a correção entra antes do contato
                n = int(0.12 * fps)
                env = np.array([c[max(0, i - n):i + n + 1][np.argmax(np.abs(c[max(0, i - n):i + n + 1]))] for i in range(len(c))])
                k = np.hanning(2 * n + 3); k /= k.sum()
                env = np.convolve(env, k, mode="same")
                ch[:, ci] += np.interp(tg, ts, env)
    rows = np.stack([np.interp(ts, tg, ch[:, c]) for c in range(ch.shape[1])], 1)
    return [(round(float(ts[i]), 3),) + h for i, p in enumerate(rows) for h in self_hits(p, slim, item)][:20]


# ------------------------------------------------------------------------------------------------------------- cena inteira
def solids_from_commands(cmds: Sequence[str], center: Sequence[float], r: int = 40, below: int = 6, above: int = 40) -> Dict:
    """Blocos sólidos conhecidos pelos comandos da cena (fill/setblock em ordem; ar e plantas não contam)."""
    cx, cy, cz = (int(math.floor(v)) for v in center)
    x0, y0, z0 = cx - r, cy - below, cz - r
    G = np.zeros((2 * r + 1, below + above + 1, 2 * r + 1), bool)
    known = np.zeros_like(G)
    rx = re.compile(r"^(fill|setblock)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)(?:\s+(-?\d+)\s+(-?\d+)\s+(-?\d+))?\s+(\S+)")
    for c in cmds:
        m = rx.match(c.strip().lstrip("/"))
        if not m:
            continue
        a = [int(v) for v in m.group(2, 3, 4)]
        b = [int(v) for v in m.group(5, 6, 7)] if m.group(5) else a
        solid = solido(m.group(8))
        lo = [max(min(a[0], b[0]) - x0, 0), max(min(a[1], b[1]) - y0, 0), max(min(a[2], b[2]) - z0, 0)]
        hi = [min(max(a[0], b[0]) - x0, G.shape[0] - 1), min(max(a[1], b[1]) - y0, G.shape[1] - 1), min(max(a[2], b[2]) - z0, G.shape[2] - 1)]
        if any(lo[k] > hi[k] for k in range(3)):
            continue
        G[lo[0]:hi[0] + 1, lo[1]:hi[1] + 1, lo[2]:hi[2] + 1] = solid
        known[lo[0]:hi[0] + 1, lo[1]:hi[1] + 1, lo[2]:hi[2] + 1] = True
    return {"grid": G, "origin": np.array([x0, y0, z0])}


def _in_solid(S: Optional[Dict], pts_world: np.ndarray, tol_blocks: float) -> np.ndarray:
    if S is None:
        return np.zeros(len(pts_world), bool)
    G, o = S["grid"], S["origin"]
    hit = np.zeros(len(pts_world), bool)
    # ponto dentro de um bloco sólido mesmo depois de recuar tol para cada lado (encostar não conta)
    for dx in (-tol_blocks, tol_blocks):
        for dy in (-tol_blocks, tol_blocks):
            for dz in (-tol_blocks, tol_blocks):
                q = np.floor(pts_world[:, :3] + [dx, dy, dz]).astype(int) - o
                ok = np.all((q >= 0) & (q < G.shape), axis=1)
                h = np.zeros(len(q), bool)
                h[ok] = G[q[ok, 0], q[ok, 1], q[ok, 2]]
                hit = h if (dx, dy, dz) == (-tol_blocks,) * 3 else (hit & h)
    return hit


def solido(estado: str) -> bool:
    """Bloco que barra o corpo (porta/portão/alçapão aberto deixa passar, como no jogo)."""
    blk = estado.split("[")[0].split("{")[0].replace("minecraft:", "")
    if any(w in blk for w in NON_SOLID):
        return False
    return not (("door" in blk or "fence_gate" in blk) and "open=true" in estado)


def verificar(anim, T: float, solids: Optional[Dict] = None, fps: int = 15, eventos: Sequence = ()) -> List[str]:
    """Problemas da cena (lista vazia = ok): personagem atravessando outro personagem; membro, corpo ou item dentro de bloco.
    eventos = Scene.blocks [t, x, y, z, estado] (blocos que mudam no meio do plano, ex.: a porta da base abrindo)."""
    actors = list(getattr(anim, "actors", []))
    if not actors:
        return []
    ts = np.arange(0, T, 1.0 / fps)
    rows = [a.at(ts) for a in actors]
    out = []
    seen = set()
    ev = []
    if solids is not None and eventos:
        G, o = solids["grid"], solids["origin"]
        for e in sorted(eventos, key=lambda e: e[0]):
            q = np.floor(np.array(e[1:4], float)).astype(int) - o
            if np.all((q >= 0) & (q < G.shape)):
                ev.append((float(e[0]), tuple(q), solido(str(e[4]))))
        orig = {c: bool(G[c]) for _, c, _ in ev}
    for i, t in enumerate(ts):
        if ev:
            now = dict(orig)
            for te, c, sv in ev:
                if te <= t + 1e-6:
                    now[c] = sv
            for c, sv in now.items():
                G[c] = sv
        B = [boxes(rows[k][i], actors[k].slim, bool(actors[k].item)) for k in range(len(actors))]
        for k, bk in enumerate(B):
            for name, (M, lo, hi) in bk.items():
                pts = (M @ _grid(lo, hi).T).T
                # personagem × personagem
                for j, bj in enumerate(B):
                    if j == k:
                        continue
                    for on, ob in bj.items():
                        if _inside(pts, ob, TOL).any():
                            key = (actors[k].name, name, actors[j].name, on)
                            if key not in seen:
                                seen.add(key)
                                out.append(f"{t:.2f}s: {actors[k].name}.{name} atravessa {actors[j].name}.{on}")
                # bloco
                tol = 1.0 / 16 if name.startswith("leg_lo") else TOL / 16
                if _in_solid(solids, pts, tol).any():
                    key = (actors[k].name, name, "bloco")
                    if key not in seen:
                        seen.add(key)
                        out.append(f"{t:.2f}s: {actors[k].name}.{name} dentro de um bloco")
    if ev:
        for c, sv in orig.items():
            G[c] = sv
    return out
