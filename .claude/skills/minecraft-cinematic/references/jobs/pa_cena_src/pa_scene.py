"""Bacia de poças no deserto (recriação do vídeo pa.mp4) + câmera rasante -> plongée geral."""
import math, random
import numpy as np

CX, CZ, G = 2946, -372, 66          # centro da bacia / nível do chão natural
RF = 50                              # raio do disco aplainado

def _noise(theta):
    return 1 + 0.07*math.sin(2*theta+0.6) + 0.05*math.sin(3*theta+2.1) + 0.03*math.sin(5*theta+4.0)

def h_rel(dx, dz):
    """altura relativa (bloco do topo) em G + h_rel, em coordenadas relativas ao centro."""
    r = math.hypot(dx, dz)
    re = r / _noise(math.atan2(dz, dx))
    if re <= 15: return -5
    if re <= 18.8: return -4
    if re <= 22.6: return -3
    if re <= 26.4: return -2
    if re <= 30.2: return -1
    if re <= 34: return 0
    if re <= 38: return 1
    if re <= 42: return 2
    if re <= 46: return 1
    return 0

def top_y(dx, dz):          # bloco do topo (y absoluto)
    return G + h_rel(dx, dz)

def puddles(seed=11):
    rnd = random.Random(seed)
    blobs = []
    spots = [(-3, 2, 4.2), (6, -4, 3.4), (-9, -3, 3.0), (2, 9, 3.2), (9, 6, 2.6), (-5, 9, 2.4), (-10, 6, 2.0), (4, -10, 2.6), (-1, -8, 2.0)]
    for (x, z, r) in spots:
        parts = [(x + rnd.uniform(-1.2, 1.2), z + rnd.uniform(-1.2, 1.2), r*rnd.uniform(0.55, 0.9)) for _ in range(3)]
        blobs.append(parts)
    wet = set()
    for parts in blobs:
        for (x, z, r) in parts:
            for ix in range(int(x-r-1), int(x+r+2)):
                for iz in range(int(z-r-1), int(z+r+2)):
                    if (ix-x)**2 + (iz-z)**2*1.15 <= r*r and h_rel(ix, iz) == -5 and math.hypot(ix, iz) <= 13.5:
                        wet.add((ix, iz))
    return wet

def commands(village=True):
    cmds = []
    rows = {}
    for dz in range(-RF, RF+1):
        hw = int(math.sqrt(RF*RF - dz*dz))
        xs = list(range(-hw, hw+1))
        runs, cur = [], None
        for dx in xs:
            h = h_rel(dx, dz)
            if cur and cur[0] == h: cur[2] = dx
            else:
                cur = [h, dx, dx]; runs.append(cur)
        rows[dz] = (hw, runs)
    for dz, (hw, runs) in rows.items():
        z = CZ + dz
        cmds.append(f"fill {CX-hw} {G-22} {z} {CX+hw} {G-7} {z} minecraft:sandstone")   # base solida (nao cai em caverna)
        cmds.append(f"fill {CX-hw} {G-6} {z} {CX+hw} {G+40} {z} minecraft:air")
        for h, a, b in runs:
            cmds.append(f"fill {CX+a} {G-6} {z} {CX+b} {G+h} {z} minecraft:sand")
    # poças
    wet = puddles()
    byrow = {}
    for (dx, dz) in wet: byrow.setdefault(dz, []).append(dx)
    for dz, xs in byrow.items():
        xs.sort(); s = e = xs[0]
        for x in xs[1:] + [None]:
            if x is not None and x == e + 1: e = x; continue
            cmds.append(f"fill {CX+s} {G-5} {CZ+dz} {CX+e} {G-5} {CZ+dz} minecraft:water")
            if x is not None: s = e = x
    # arbustos secos espalhados (fora das poças)
    rnd = random.Random(5)
    n = 0
    for _ in range(900):
        ang = rnd.uniform(0, 2*math.pi); r = rnd.uniform(4, 44)
        dx, dz = int(r*math.cos(ang)), int(r*math.sin(ang))
        if (dx, dz) in wet or any((dx+a, dz+b) in wet for a in (-1, 0, 1) for b in (-1, 0, 1)): continue
        cmds.append(f"setblock {CX+dx} {G+h_rel(dx, dz)+1} {CZ+dz} minecraft:dead_bush")
        n += 1
        if n >= 60: break
    if village:
        cmds.append(f"place structure minecraft:village_desert {CX-80} {G+4} {CZ-10}")
    return cmds

# ---------------- corredor
T_STOP = 4.6
RUN_V = 5.6
def runner_state(t):
    """posição (x,z) e y dos pés do corredor no instante t (coords relativas ao centro)."""
    tt = min(t, T_STOP)
    z = 44.0 - RUN_V*tt
    return 0.0, z

_ZS = np.arange(-10, 60, 0.05)
_HP = np.array([h_rel(0, int(round(z))) + 1.0 for z in _ZS])
_k = np.exp(-0.5*(np.arange(-30, 31)*0.05/0.45)**2); _k /= _k.sum()
_HS = np.convolve(np.pad(_HP, 30, mode="edge"), _k, mode="valid")

def runner_world(t):
    dx, dz = runner_state(t)
    return (CX+dx, G + float(np.interp(dz, _ZS, _HS)), CZ+dz)
