"""Cena 1 — "E se você pudesse transformar qualquer coisa do seu mundo no minecraft em borracha?" (6 s, 16:9).
Matteeoo ricocheteia num mundo overworld onde tudo é borracha (Gear 5): chão-trampolim com ondas, árvore-mola, abóbora.
"""
import sys, math, random
sys.path.insert(0, r"C:\Users\mathe\.claude\skills\minecraft-cinematic\scripts")
import numpy as np
from PIL import Image
from cinecam import *
from cinecam.camlib import Move

OUT = r"D:/cinecam-out/borracha_c1"
SRC_SKIN = r"C:/Users/mathe/Skills/.bbs-work/aracnofobia/backups/combat-visual-20260920-173511-843/MatteeooHD/Matteeoo.png"
SKIN = OUT + "/matteeoo_orange.png"
FPS, DUR = 30, 6.0
G = 28.0                     # cartoon gravity (blocks/s^2)
GY = 66.0                    # ground top (first free y) after levelling
REG = (222, 296, 262, 330)   # cleared + levelled stage x0 z0 x1 z1


# ----------------------------------------------------------------- skin (warmer orange like refs 2/3, solid lenses)
def make_skin():
    import os
    os.makedirs(OUT, exist_ok=True)
    im = Image.open(SRC_SKIN).convert("RGBA")
    px = im.load()
    W, H = im.size
    for y in range(H):
        for x in range(W):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            if r > g > b and r - b > 40:                       # the brown body tones -> warmer orange
                r2 = min(255, int(r * 1.38 + 12)); g2 = min(255, int(g * 1.22 + 6)); b2 = min(255, int(b * 0.85))
                px[x, y] = (r2, g2, b2, a)
    # lenses: solid black (the dark-grey dots read as dirt at a distance)
    for y in range(24, 28):
        for x in list(range(17, 23)) + list(range(25, 31)):
            r, g, b, a = px[x, y]
            if r < 60 and g < 60 and b < 60:
                px[x, y] = (8, 8, 9, 255)
    im.save(SKIN)


# ----------------------------------------------------------------- choreography (times / contact points)
C0 = dict(p=(236.0, 312.0), t0=0.40, t1=0.62, D=0.40)          # ground trampoline
TREE = (241.0, 309.0)
TREE_TOP_REST = 6.0                                           # blocks above its base (3 logs + 3 leaf layers)
C1 = dict(t0=1.62, t1=1.92, D=0.95)                           # tree canopy
PUMP = (246.0, 312.0)
C2 = dict(t0=3.17, t1=3.37, D=0.62)                           # pumpkin
FIN = (243.0, 317.0)
C3 = dict(t0=4.32, t1=4.62, D=0.36)                           # final landing


def bump(u):            # 0..1 -> 0..1..0 (contact dent)
    u = np.clip(u, 0, 1)
    return np.sin(np.pi * u)


def ring(t, t1, amp, freq, decay):   # post-release rebound: goes UP first (negative dent), damped
    tau = np.maximum(t - t1, 0)
    return np.where(t > t1, -amp * np.exp(-decay * tau) * np.sin(2 * np.pi * freq * tau), 0.0)


# --- ground height field h(x,z,t) (+ = up) on the rubber grid: dents under contacts + travelling radial waves
IMPACTS = [  # (cx, cz, t0, t1, D, wave_amp)
    (C0["p"][0], C0["p"][1], C0["t0"], C0["t1"], C0["D"], 0.30),
    (FIN[0], FIN[1], C3["t0"], C3["t1"], C3["D"], 0.26),
]
# tree and pumpkin also kick small waves into the ground when hit
IMPACTS_SMALL = [(TREE[0], TREE[1], C1["t0"], C1["t1"], 0.16), (PUMP[0], PUMP[1], C2["t0"], C2["t1"], 0.12)]


def ground_h(x, z, t):
    x = np.asarray(x, float); z = np.asarray(z, float); t = np.asarray(t, float)
    h = np.zeros(np.broadcast(x, z, t).shape)
    for cx, cz, t0, t1, D, A in IMPACTS:
        r = np.hypot(x - cx, z - cz)
        u = (t - t0) / (t1 - t0)
        w = np.exp(-(r / 2.3) ** 2)
        h = h - D * w * np.where((u >= 0) & (u <= 1), bump(u), 0.0)
        h = h - D * w * ring(t, t1, 0.55, 2.6, 5.0)                        # centre rebounds up then settles
        tau = t - t0
        k, om = 1.55, 13.0                                                 # wave ~4 blocks long, ~8.4 b/s
        front = np.clip((om / k * tau - r) / 1.5 + 1, 0, 1) * (tau > 0)
        h = h + A * front * np.exp(-2.2 * np.maximum(tau, 0)) * np.exp(-r / 7.0) * np.sin(k * r - om * tau) * np.clip(r / 1.2, 0, 1)
    for cx, cz, t0, t1, A in IMPACTS_SMALL:
        r = np.hypot(x - cx, z - cz)
        tau = t - t0
        k, om = 1.55, 13.0
        front = np.clip((om / k * tau - r) / 1.5 + 1, 0, 1) * (tau > 0)
        h = h + A * front * np.exp(-2.6 * np.maximum(tau, 0)) * np.exp(-r / 6.0) * np.sin(k * r - om * tau)
    return h


def ground_h_soft(x, z, t, dead=0.025):
    """Dead zone: tiny residual waves snap flat so the grid has no seams at rest."""
    h = ground_h(x, z, t)
    return np.sign(h) * np.maximum(np.abs(h) - dead, 0)


def ground_top(x, z, t):
    return GY + ground_h_soft(x, z, t)


# --- tree dynamics: compression (trunk/canopy) and bend angles (deg) at the top
def tree_state(t):
    t = np.asarray(t, float)
    u = (t - C1["t0"]) / (C1["t1"] - C1["t0"])
    inside = (u >= 0) & (u <= 1)
    ks = 1 - 0.42 * np.where(inside, bump(u), 0) + ring(t, C1["t1"], 0.30, 2.4, 4.0) * -1   # canopy squash (rebound >1)
    cs = 1 - 0.20 * np.where(inside, bump(u), 0) + ring(t, C1["t1"], 0.16, 2.0, 3.5) * -1   # trunk compression
    # bend: pushed toward +x/-z by the landing, then springs back past rest throwing him to +x+z
    bx = 16 * np.where(inside, bump(u), 0) + ring(t, C1["t1"], 18, 1.7, 2.6)
    bz = -6 * np.where(inside, bump(u), 0) + ring(t, C1["t1"], -9, 1.7, 2.6)
    idle = 2.2 * np.sin(2 * np.pi * 0.9 * t + 0.4) * np.clip(1 - (t - 1.4) * 2, 0, 1)    # rubbery idle sway before
    return ks, cs, bx + idle, bz


TRUNK_H, CAN_Y = 3, 3          # 3 logs, canopy starts at local y=3
CANOPY = [(dx, 3, dz) for dx in (-1, 0, 1) for dz in (-1, 0, 1)] + [(dx, 4, dz) for dx in (-1, 0, 1) for dz in (-1, 0, 1)] + \
         [(0, 5, 0), (1, 5, 0), (-1, 5, 0), (0, 5, 1), (0, 5, -1)]


def tree_block_fn(lx, ly, lz):
    """Procedural transform for one tree block (rest bottom-centre at base + (lx, ly, lz))."""
    def f(times):
        ks, cs, bx, bz = tree_state(times)
        base_y = ground_top(TREE[0], TREE[1], times)
        H = TRUNK_H * cs + 3 * ks
        if ly < CAN_Y:
            y1 = ly * cs; sy = cs; lat = 1.0
        else:
            y1 = CAN_Y * cs + (ly - CAN_Y) * ks; sy = ks; lat = 1 / np.sqrt(np.maximum(ks, 0.3))
        sxz = 1 / np.sqrt(np.maximum(sy, 0.3))
        fx = np.radians(bx) * (y1 / np.maximum(H, 0.1)); fz = np.radians(bz) * (y1 / np.maximum(H, 0.1))
        dx = np.radians(bx) * y1 ** 2 / (2 * np.maximum(H, 0.1)); dz = np.radians(bz) * y1 ** 2 / (2 * np.maximum(H, 0.1))
        ox, oz = lx * lat, lz * lat
        # lateral offsets ride the local tilt (small-angle): x-offset dips/raises with the bend
        x = TREE[0] + dx + ox * np.cos(fx)
        z = TREE[1] + dz + oz * np.cos(fz)
        y = base_y + y1 - ox * np.sin(fx) - oz * np.sin(fz)
        n = len(times)
        out = np.zeros((n, 9))
        out[:, 0], out[:, 1], out[:, 2] = x, y, z
        out[:, 3] = sxz
        out[:, 4] = sy
        out[:, 5] = out[:, 3]
        out[:, 7] = np.degrees(fz)          # pitch +: top toward +z
        out[:, 8] = -np.degrees(fx)         # roll -: top toward +x
        return out
    return f


def tree_top_y(t):
    ks, cs, bx, bz = tree_state(t)
    return ground_top(TREE[0], TREE[1], t) + TRUNK_H * cs + 3 * ks


def pump_state(t):
    t = np.asarray(t, float)
    u = (t - C2["t0"]) / (C2["t1"] - C2["t0"])
    inside = (u >= 0) & (u <= 1)
    sy = 1 - C2["D"] * np.where(inside, bump(u), 0) + ring(t, C2["t1"], 0.45, 3.0, 4.5) * -1
    sy = sy + 0.05 * np.sin(2 * np.pi * 1.3 * t) * (t < C2["t0"])          # idle jelly breathing
    return np.maximum(sy, 0.25)


def pump_fn(times):
    sy = pump_state(times)
    n = len(times)
    out = np.zeros((n, 9))
    out[:, 0], out[:, 2] = PUMP
    out[:, 1] = ground_top(PUMP[0], PUMP[1], times)
    out[:, 3] = out[:, 5] = 1 / np.sqrt(sy)
    out[:, 4] = sy
    out[:, 6] = 12.0
    return out


def pump_top(t):
    return ground_top(PUMP[0], PUMP[1], t) + pump_state(t)


# ----------------------------------------------------------------- character trajectory (feet), squash/stretch, flips
def arc(p0, p1, t0, t1):
    T = t1 - t0
    p0, p1 = np.array(p0, float), np.array(p1, float)
    v = (p1 - p0) / T
    v[1] = (p1[1] - p0[1] + 0.5 * G * T * T) / T
    def f(t):
        tau = (np.asarray(t, float) - t0)[:, None]
        q = p0[None] + v[None] * tau
        q[:, 1] -= 0.5 * G * tau[:, 0] ** 2
        return q
    return f, v


P_FALL0 = (C0["p"][0] - 0.6, GY + 5.6, C0["p"][1] - 0.4)
SEG = []   # (t0, t1, kind, fn)


def build_path():
    SEG.clear()
    # fall: already moving down at frame 0
    T0 = C0["t0"]
    p1 = (C0["p"][0], GY, C0["p"][1])
    v0y = (P_FALL0[1] - p1[1] - 0.5 * G * T0 * T0) / T0
    def fall(t):
        tau = np.asarray(t, float)[:, None]
        q = np.array(P_FALL0)[None] + (np.array(p1) - np.array(P_FALL0))[None] * (tau / T0)
        q[:, 1] = P_FALL0[1] - v0y * tau[:, 0] - 0.5 * G * tau[:, 0] ** 2
        return q
    SEG.append((0.0, T0, "air", fall))
    SEG.append((C0["t0"], C0["t1"], "c0", None))
    a1, _ = arc((C0["p"][0], GY, C0["p"][1]), (TREE[0], GY + TREE_TOP_REST, TREE[1]), C0["t1"], C1["t0"])
    SEG.append((C0["t1"], C1["t0"], "air", a1))
    SEG.append((C1["t0"], C1["t1"], "c1", None))
    a2, _ = arc((TREE[0], GY + TREE_TOP_REST, TREE[1]), (PUMP[0], GY + 1, PUMP[1]), C1["t1"], C2["t0"])
    SEG.append((C1["t1"], C2["t0"], "air", a2))
    SEG.append((C2["t0"], C2["t1"], "c2", None))
    a3, _ = arc((PUMP[0], GY + 1, PUMP[1]), (FIN[0], GY, FIN[1]), C2["t1"], C3["t0"])
    SEG.append((C2["t1"], C3["t0"], "air", a3))
    SEG.append((C3["t0"], DUR + 1, "c3", None))


def feet(t):
    t = np.atleast_1d(np.asarray(t, float))
    out = np.zeros((len(t), 3))
    for t0, t1, kind, fn in SEG:
        m = (t >= t0) & (t < t1)
        if not m.any():
            continue
        tt = t[m]
        if kind == "air":
            out[m] = fn(tt)
        elif kind == "c0":
            out[m] = np.c_[np.full(len(tt), C0["p"][0]), ground_top(C0["p"][0], C0["p"][1], tt), np.full(len(tt), C0["p"][1])]
        elif kind == "c1":
            out[m] = np.c_[np.full(len(tt), TREE[0]), tree_top_y(tt), np.full(len(tt), TREE[1])]
            ks, cs, bx, bz = tree_state(tt)
            H = TRUNK_H * cs + 3 * ks
            out[m, 0] += np.radians(bx) * H / 2; out[m, 2] += np.radians(bz) * H / 2
        elif kind == "c2":
            out[m] = np.c_[np.full(len(tt), PUMP[0]), pump_top(tt), np.full(len(tt), PUMP[1])]
        elif kind == "c3":
            out[m] = np.c_[np.full(len(tt), FIN[0]), ground_top(FIN[0], FIN[1], tt), np.full(len(tt), FIN[1])]
    out[t < 0] = out[t >= 0][0] if (t >= 0).any() else out[t < 0]
    return out


def contact_u(t):
    """Per time: (squash amount 0..1 during any contact, seconds since last release)."""
    t = np.asarray(t, float)
    sq = np.zeros_like(t); since = np.full_like(t, 9.0)
    for c in (C0, C1, C2, C3):
        u = (t - c["t0"]) / (c["t1"] - c["t0"])
        inside = (u >= 0) & (u <= 1)
        sq = np.maximum(sq, np.where(inside, bump(u), 0))
        s = t - c["t1"]
        since = np.where((s >= 0) & (s < since), s, since)
    return sq, since


def spring(target, dt, omega, zeta):
    """Damped spring follower: zeta<1 overshoots (rubbery follow-through), keeps the motion alive between poses."""
    y = np.empty_like(target); y[0] = target[0]; v = 0.0
    for i in range(1, len(target)):
        acc = omega * omega * (target[i] - y[i - 1]) - 2 * zeta * omega * v
        v += acc * dt
        y[i] = y[i - 1] + v * dt
    return y


def arm_tracks(ts, vy):
    """Both arms, per time: outward angle (deg, 0 = hanging at the side, 90 = T-pose, 180 = straight up; never < 14 so they
    never enter the torso), forward swing rx (deg, negative = forward; windmill spins it), and rubber length."""
    dt = ts[1] - ts[0]
    two = 2 * np.pi
    vs = spring(vy, dt, 25, 1.0)
    o_phys = np.clip(100 - 3.0 * vs, 35, 165)                     # follow-through: rising -> arms trail down, falling -> float up
    oR = o_phys.copy(); oL = o_phys.copy(); rxR = np.zeros_like(ts); rxL = np.zeros_like(ts)
    lR = np.ones_like(ts); lL = np.ones_like(ts)
    def seg(t0, t1):
        return (ts >= t0) & (ts < t1)
    # Arms stay in the side plane (|swing| <= ~25 deg) so the silhouette always reads; never pointing at the lens.
    K = 0.0
    # fall: flailing up, alternating
    m = seg(0, C0["t0"]); tt = ts[m]
    oR[m] = 108 + 16 * np.sin(two * 5.5 * tt); oL[m] = 108 + 16 * np.sin(two * 5.5 * tt + np.pi)
    rxR[m] = -12 * np.sin(two * 4.5 * tt); rxL[m] = 12 * np.sin(two * 4.5 * tt); lR[m] = lL[m] = 1.5
    # ground impact: arms splay with the squash
    m = seg(C0["t0"], C0["t1"]); oR[m] = oL[m] = 70
    # A1: flapping like wings with long rubber arms (in sync), trailing slightly back
    w0, w1 = C0["t1"] + 0.04, C1["t0"] - 0.08
    m = seg(C0["t1"], w1); tt = ts[m] - w0
    flap = np.sin(two * 3.0 * np.maximum(tt, 0) - np.pi / 2)
    oR[m] = 88 + 32 * flap; oL[m] = 88 + 32 * flap
    rxR[m] = rxL[m] = 12
    lR[m] = 1.65 + 0.15 * np.sin(two * 3.0 * tt); lL[m] = 1.65 + 0.15 * np.sin(two * 3.0 * tt + 0.6)
    # tree: arms forward to hug the canopy, then whip up on release
    m = seg(w1, C1["t1"]); rxR[m] = rxL[m] = -55; oR[m] = oL[m] = 40; lR[m] = lL[m] = 1.2
    m = seg(C1["t1"], C1["t1"] + 0.12); rxR[m] = rxL[m] = 0; oR[m] = oL[m] = 115; lR[m] = lL[m] = 1.6
    # A2 flip: pinwheel — long rubber arms straight out, noodle waves
    f0, f1 = C1["t1"] + 0.12, C2["t0"] - 0.05
    m = seg(f0, f1); tt = ts[m] - f0
    oR[m] = 92 + 10 * np.sin(two * 4.2 * tt); oL[m] = 92 + 10 * np.sin(two * 4.2 * tt + 2.1)
    rxR[m] = 12 * np.sin(two * 3.0 * tt); rxL[m] = -12 * np.sin(two * 3.0 * tt + 0.8)
    grow = np.clip(tt / 0.3, 0, 1) * np.clip((f1 - ts[m]) / 0.3, 0, 1)
    lR[m] = 1 + 1.6 * grow + 0.1 * np.sin(two * 5 * tt); lL[m] = 1 + 1.6 * grow + 0.1 * np.sin(two * 5 * tt + 1.2)
    # pumpkin: arms flop out with the squash
    m = seg(f1, C2["t1"]); rxR[m] = rxL[m] = 0; oR[m] = oL[m] = 60
    # A3 twirl: T-pose, long, trailing waves; rise before landing
    g0, g1 = C2["t1"], C3["t0"]
    m = seg(g0, g1); tt = ts[m] - g0
    rise = np.clip((ts[m] - (g1 - 0.25)) / 0.2, 0, 1)
    oR[m] = 96 + 20 * rise + 9 * np.sin(two * 3.6 * tt); oL[m] = 96 + 20 * rise + 9 * np.sin(two * 3.6 * tt + 1.4)
    rxR[m] = 12 * np.sin(two * 2.4 * tt + 0.5); rxL[m] = -12 * np.sin(two * 2.4 * tt)
    lR[m] = lL[m] = 1 + 0.9 * np.clip(tt / 0.25, 0, 1) * (1 - 0.5 * rise)
    # landing: flop
    m = seg(g1, C3["t1"]); rxR[m] = rxL[m] = 0; oR[m] = oL[m] = 70; lR[m] = lL[m] = 0.9
    # hero: wide V, noodle sway (asymmetric phases so it never looks frozen)
    m = ts >= C3["t1"]; tt = ts[m] - C3["t1"]
    oR[m] = 126 + 13 * np.sin(two * 1.5 * tt); oL[m] = 126 + 13 * np.sin(two * 1.5 * tt + 1.9)
    rxR[m] = 10 * np.sin(two * 1.05 * tt); rxL[m] = 10 * np.sin(two * 1.05 * tt + 2.4)
    lR[m] = 2.05 + 0.13 * np.sin(two * 2.1 * tt); lL[m] = 2.05 + 0.13 * np.sin(two * 2.1 * tt + 1.1)
    # rubbery follow-through: underdamped springs on angle/length, firmer on the swing
    oR = np.clip(spring(oR, dt, 34, 0.55), 18, 140); oL = np.clip(spring(oL, dt, 34, 0.55), 18, 140)
    lR = np.clip(spring(lR, dt, 26, 0.5), 0.8, 2.9); lL = np.clip(spring(lL, dt, 26, 0.5), 0.8, 2.9)
    rxR = spring(rxR, dt, 40, 0.8); rxL = spring(rxL, dt, 40, 0.8)
    xR, zR = arm_euler(oR, rxR, -1); xL, zL = arm_euler(oL, rxL, +1)   # calibrated 17/10: +rarm_z = right arm OUT
    return zR, lR, zL, lL, xR, xL


def arm_euler(beta, theta, side):
    """(outward angle beta, swing theta) -> ModelPart (xRot, zRot) in degrees.  The arm direction is built first
    (always beta away from the body, even when it swings over the top) and then converted, because composing raw Euler
    angles flips the tilt to the INSIDE once the arm passes above the shoulder (arm crossing the face/other arm).
    Model space: y down; Rz(c)*Rx(a)*down = (-sin c cos a, cos c cos a, sin a); right arm outward = -x (side=-1, i.e. +zRot)."""
    b = np.radians(beta); th = np.radians(theta)
    d = np.c_[side * np.sin(b), np.cos(b) * np.cos(th), np.cos(b) * np.sin(th)]
    a = np.degrees(np.arcsin(np.clip(d[:, 2], -1, 1)))
    c = np.degrees(np.unwrap(np.arctan2(-d[:, 0], d[:, 1])))
    return a, c


def build_actor():
    a = Actor("matteeoo", SKIN, feet(np.array([0.0]))[0], yaw=-20, hat=True)
    ts = np.round(np.arange(0, DUR + 0.2, 1 / 120), 5)
    P = feet(ts)
    sq, since = contact_u(ts)
    # flight vertical speed for stretch
    vy = np.gradient(P[:, 1], ts)
    airs = np.zeros_like(ts, bool)
    for t0, t1, kind, _ in SEG:
        if kind == "air":
            airs |= (ts >= t0) & (ts < t1)
    stretch = 0.14 * np.clip(np.abs(vy) / 18, 0, 1) * airs
    popd = np.exp(-since * 9) * (since < 1)                            # spring out of each contact
    sy = np.where(sq > 0, 1 - 0.45 * sq, 1 + stretch + 0.22 * popd)
    sy = np.where(ts > C3["t1"], 1 + 0.24 * np.exp(-(ts - C3["t1"]) * 3.2) * np.cos(2 * np.pi * 2.3 * (ts - C3["t1"])), sy)
    sxz = 1 / np.sqrt(np.clip(sy, 0.3, 3))
    legs = np.where(sq > 0, 1 - 0.40 * sq, 1 + 0.10 * popd)   # fake knees: legs compress on contact

    # flip (A2) about the body centre + twirl (A3)
    a2t0, a2t1 = C1["t1"], C2["t0"]
    uf = np.clip((ts - a2t0 - 0.08) / (a2t1 - a2t0 - 0.25), 0, 1)
    flip = -360 * (uf * uf * (3 - 2 * uf))                         # forward flip (lean<0 = forward)
    a3t0, a3t1 = C2["t1"], C3["t0"]
    ut = np.clip((ts - a3t0 - 0.05) / (a3t1 - a3t0 - 0.2), 0, 1)
    twirl = 360 * (ut * ut * (3 - 2 * ut))

    # facing: chest to the camera (so side-plane arms read in silhouette); 3/4 during the flip so the somersault reads
    cp = cam_pos(ts)
    face = np.degrees(np.unwrap(np.arctan2(-(cp[:, 0] - P[:, 0]), cp[:, 2] - P[:, 2])))
    off = smooth_interp(ts, [(0, 12), (C1["t1"], 12), (C1["t1"] + 0.15, -62), (C2["t0"] - 0.1, -62), (C2["t0"] + 0.1, 0), (DUR, 0)])
    face = spring(face, ts[1] - ts[0], 14, 1.0)
    yaw = face + off + twirl
    yaw = np.where(ts > C3["t1"] + 0.3, yaw, yaw)

    # centre-pivot compensation for the flip: feet = centre - c*(cos a*up - sin a*fwd), lean>0 = back
    c = 1.0 * sy
    lean = flip
    ar = np.radians(lean)
    yr = np.radians(yaw)
    fwd = np.c_[-np.sin(yr), np.zeros_like(yr), np.cos(yr)]
    centre = P + np.c_[np.zeros_like(c), c, np.zeros_like(c)]
    up = np.c_[np.zeros_like(c), np.ones_like(c), np.zeros_like(c)]
    feetp = centre - c[:, None] * (np.cos(ar)[:, None] * up - np.sin(ar)[:, None] * fwd)

    # arms / legs choreography (dense channels)
    def ch(*pairs):
        tt, vv = zip(*pairs)
        return np.interp(ts, tt, vv)
    R, Lr, Lo, Ll, Rx, Lx = arm_tracks(ts, vy)
    rleg = ch((0, 12), (0.4, 0), (0.62, -28), (0.9, 25), (1.2, -20), (1.6, 0), (1.92, 0), (2.2, -50), (2.9, -50), (3.15, 0),
              (3.4, -30), (3.8, 30), (4.3, 0), (DUR, 0))
    lleg = ch((0, -12), (0.4, 0), (0.62, 28), (0.9, -25), (1.2, 20), (1.6, 0), (1.92, 0), (2.2, -50), (2.9, -50), (3.15, 0),
              (3.4, 30), (3.8, -30), (4.3, 0), (DUR, 0))
    legz = ch((0, 0), (0.62, 0), (0.75, 18), (1.5, 10), (1.6, 0), (3.4, 0), (3.6, 22), (4.25, 14), (4.35, 0), (4.62, 8), (5.0, 6), (DUR, 6))
    head_x = ch((0, -25), (0.4, -10), (0.62, 10), (0.8, -30), (1.6, -10), (1.9, 15), (2.1, -15), (3.2, 10), (3.4, -25),
                (4.3, -10), (4.5, 12), (4.8, -22), (5.3, -14), (DUR, -18))
    head_z = ch((0, 0), (4.62, 0), (4.95, 10), (5.5, -6), (DUR, 4))
    shadow = ground_top(P[:, 0], P[:, 2], ts)
    for i, t in enumerate(ts):
        a.key(float(t), ease="linear", x=feetp[i, 0], y=feetp[i, 1], z=feetp[i, 2], yaw=yaw[i], lean=lean[i],
              sy=sy[i], sx=sxz[i], sz=sxz[i], rleg_len=legs[i], lleg_len=legs[i],
              rarm_z=R[i], larm_z=Lo[i], rarm_x=Rx[i], larm_x=Lx[i], rarm_len=Lr[i], larm_len=Ll[i],
              rleg_x=rleg[i], lleg_x=lleg[i], rleg_z=legz[i], lleg_z=-legz[i], head_x=head_x[i], head_z=head_z[i],
              shadow_y=float(shadow[i]))
    # jelly body after the final landing
    a.wobble("belly", 4.62, DUR, 0.06, 4.0, 1.5)
    return a, ts, feetp, P


def char_centre(t):
    return feet(t) + np.array([0, 1.05, 0])


# ----------------------------------------------------------------- props: rubber ground grid, tree, pumpkin, extras
GRID = [(x, z) for x in range(230, 251) for z in range(306, 323)]
TREE_CELLS = {(241, 309)}


def ground_prop(x, z):
    cx, cz = x + 0.5, z + 0.5
    def f(times):
        h = ground_h_soft(cx, cz, times)
        sy = np.clip(1 + h, 0.3, 1.8)
        n = len(times)
        out = np.zeros((n, 9))
        out[:, 0], out[:, 1], out[:, 2] = cx, GY - 1, cz
        out[:, 3] = out[:, 5] = np.clip(1 / np.sqrt(sy), 0.9, 1.25)
        out[:, 4] = sy
        return out
    return Prop(f"g_{x}_{z}", "minecraft:grass_block", (cx, GY - 1, cz), fn=f)


def build_props():
    props = [ground_prop(x, z) for (x, z) in GRID]
    for i, (lx, ly, lz) in enumerate([(0, k, 0) for k in range(TRUNK_H)]):
        props.append(Prop(f"log{i}", "minecraft:oak_log[axis=y]", (0, 0, 0), fn=tree_block_fn(lx, ly, lz)))
    for i, (lx, ly, lz) in enumerate(CANOPY):
        props.append(Prop(f"leaf{i}", "minecraft:oak_leaves[persistent=true]", (0, 0, 0), fn=tree_block_fn(lx, ly, lz)))
    props.append(Prop("pumpkin", "minecraft:pumpkin", (PUMP[0], GY, PUMP[1]), fn=pump_fn))
    return props


# ----------------------------------------------------------------- stage commands (clear + level + backdrop trees + decor)
def stage_commands():
    x0, z0, x1, z1 = REG
    cmds = [f"fill {x0} 66 {z0} {x1} 76 {z1} minecraft:air", f"fill {x0} 77 {z0} {x1} 92 {z1} minecraft:air",
            f"fill {x0} 65 {z0} {x1} 65 {z1} minecraft:grass_block", f"fill {x0} 60 {z0} {x1} 64 {z1} minecraft:dirt"]
    # the rubber grid replaces the real top layer (props draw it)
    cmds.append(f"fill 230 65 306 250 65 322 minecraft:air")
    cmds.append(f"fill 230 64 306 250 64 322 minecraft:dirt")
    rnd = random.Random(7)
    trees = [(224, 298, "fancy_oak"), (229, 299, "oak"), (233, 297, "birch"), (237, 299, "oak"), (245, 298, "fancy_oak"),
             (251, 299, "oak"), (255, 297, "birch"), (259, 300, "oak"), (224, 305, "oak"), (225, 312, "birch"), (224, 319, "oak"),
             (258, 306, "oak"), (259, 313, "fancy_oak"), (258, 321, "birch")]
    for x, z, f in trees:
        cmds.append(f"place feature minecraft:{f} {x} 66 {z}")
    flowers = ["minecraft:grass", "minecraft:grass", "minecraft:grass", "minecraft:dandelion", "minecraft:poppy",
               "minecraft:azure_bluet", "minecraft:oxeye_daisy", "minecraft:cornflower"]
    for _ in range(170):
        x, z = rnd.randint(x0 + 1, x1 - 1), rnd.randint(z0 + 1, z1 - 1)
        if 229 <= x <= 251 and 305 <= z <= 323:
            continue
        cmds.append(f"setblock {x} 66 {z} {rnd.choice(flowers)}")
    return cmds


SCENE = Scene(time=4500, weather="clear", anchor=(241, 80, 312), commands=[], settleTicks=160)
WORLD = World(seed=4242)


def settings(frozen=False):
    return Settings(renderDistance=10, simulationDistance=6, worldTicks=not frozen)


# ----------------------------------------------------------------- camera
def lagged_aim(t0, T, lead=0.0, lag=0.10, offset=(0, 0, 0)):
    tt = np.arange(-0.5, DUR + 0.6, 1 / 240)
    c = char_centre(tt)
    sm = c.copy()
    k = 1 - np.exp(-(1 / 240) / lag)
    for i in range(1, len(tt)):
        sm[i] = sm[i - 1] + k * (c[i] - sm[i - 1])
    off = np.array(offset)
    def f(tau):
        t = t0 + np.asarray(tau, float) * T + lead
        return np.c_[np.interp(t, tt, sm[:, 0]), np.interp(t, tt, sm[:, 1]), np.interp(t, tt, sm[:, 2])] + off[None]
    return f


def blend_aim(fa, fb, w_fn):
    def f(tau):
        w = w_fn(np.asarray(tau, float))[:, None]
        return fa(tau) * (1 - w) + fb(tau) * w
    return f


def smooth_interp(tau, knots):
    """Piecewise smoothstep through (tau, value) knots (C1 at knots: zero slope there)."""
    tau = np.asarray(tau, float)
    ks, vs = zip(*knots)
    out = np.full_like(tau, vs[0])
    for (a, va), (b, vb) in zip(knots[:-1], knots[1:]):
        u = np.clip((tau - a) / (b - a), 0, 1); u = u * u * (3 - 2 * u)
        m = tau >= a
        out[m] = (va + (vb - va) * u)[m]
    return out


CAM_KEYS = [  # (t, camera position) — close follow, ~4-5.5 blocks from him
    (0.0, (233.4, 66.5, 315.6)), (0.6, (234.0, 66.65, 315.9)), (1.2, (236.8, 69.6, 314.2)), (1.75, (238.3, 72.7, 313.9)),
    (2.4, (241.0, 73.0, 314.3)), (3.2, (244.1, 68.5, 316.1)), (3.85, (244.8, 67.8, 319.1)), (4.45, (244.1, 66.95, 320.6)),
    (DUR, (243.6, 66.7, 319.85))]


def cam_pos(t):
    from scipy.interpolate import CubicSpline
    kt = np.array([k[0] for k in CAM_KEYS]); kp = np.array([k[1] for k in CAM_KEYS])
    sp = CubicSpline(kt, kp, bc_type=((1, (kp[1] - kp[0]) / (kt[1] - kt[0]) * 0.8), (1, np.zeros(3))))
    return sp(np.clip(np.asarray(t, float), 0, DUR))


def build_rig(subframes=8):
    """One continuous handheld-follow move, time-keyed spline; aim + focus on him (lagged), last second locks on the hero pose."""
    from scipy.interpolate import CubicSpline
    rig = Rig(fps=FPS, subframes=subframes, shutter=0.5)
    kt = np.array([k[0] for k in CAM_KEYS]); kp = np.array([k[1] for k in CAM_KEYS])
    sp = CubicSpline(kt, kp, bc_type=((1, (kp[1] - kp[0]) / (kt[1] - kt[0]) * 0.8), (1, np.zeros(3))))
    base = lagged_aim(0, DUR, lead=0.03, lag=0.12)
    hero = np.array((FIN[0], GY + 1.2, FIN[1]))
    def fn(tau):
        tau = np.asarray(tau, float); t = tau * DUR
        pos = sp(t)
        p = base(tau)
        w = smooth_interp(t, [(0, 0.0), (4.6, 0.0), (5.4, 1.0)])[:, None]
        p = p * (1 - w) + hero[None] * w
        yaw, pitch = look_at(pos, p)
        fwd = forward(yaw, pitch)
        focus = np.sum((char_centre(t) - pos) * fwd, axis=-1)
        return {"x": pos[:, 0], "y": pos[:, 1], "z": pos[:, 2], "yaw": np.degrees(np.unwrap(np.radians(yaw))), "pitch": pitch,
                "roll": smooth_interp(t, [(0, 5), (1.3, -3), (2.5, 6), (3.6, 4), (5.2, 0), (DUR, 0)]),
                "fov": smooth_interp(t, [(0, 74), (0.7, 70), (1.7, 66), (2.5, 70), (3.3, 66), (4.4, 70), (5.5, 57), (DUR, 56)]),
                "focus": np.maximum(focus, 0.5), "aperture": np.full_like(t, 0.32)}
    rig.add(Move(DUR, fn, "follow").with_handheld("subtle"))
    return rig


def build_anim():
    build_path()
    a, *_ = build_actor()
    return Anim([a], props=build_props())


if __name__ == "__main__":
    make_skin()
    build_path()
    print("ok")
