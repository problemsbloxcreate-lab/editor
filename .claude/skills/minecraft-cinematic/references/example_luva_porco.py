"""Cena 3 (final) — "E a gente criou esse item que tudo que ela toca, vira borracha!"
Matteeoo pousa (chão de borracha afunda + ondas), tira a Luva Elástica (modelo real do mod rubberflux) do bolso, estica o braço
até um porco, o porco vira borracha, ele gira e arremessa: o porco ricocheteia árvore -> parede -> árvore -> chão e para aos pés dele.
"""
import sys, math, random
sys.path.insert(0, r"C:\Users\mathe\.claude\skills\minecraft-cinematic\scripts")
sys.path.insert(0, r"C:\Users\mathe\AppData\Local\Temp\claude\C--Users-mathe-Skills\9241dd35-0dcc-47dd-801e-fe2e4981f49a\scratchpad")
import numpy as np
from cinecam import *
from cinecam.camlib import Move
from borracha_c1 import make_skin, SKIN, spring, smooth_interp, REG, GY, bump, ring

OUT = r"D:/cinecam-out/borracha_c3"
FPS, DUR = 30, 7.0
GLOVE = "model:cinecam:item/elastic_glove"
L = np.array([238.0, GY, 312.0])                 # landing spot (feet)
PIG0 = np.array([241.3, GY + 0.45, 314.4])       # pig body centre, grazing
T1, T2 = (246.0, 309.0), (244.0, 305.0)          # rubber trees (block coords)
WALL_X, WALL_Z, WALL_Y = 250, range(310, 316), range(66, 70)

# ------------------------------------------------------------------ timeline
T_LAND0, T_LAND1 = 0.55, 0.82
T_POCKET, T_PULL, T_SHOW = 1.25, 1.60, 1.90
T_REACH, T_TOUCH, T_RETRACT, T_SPIN, T_REL = 2.55, 2.85, 3.00, 3.30, 3.85
CUT1 = 2.55


def unit(v):
    v = np.asarray(v, float); return v / np.linalg.norm(v, axis=-1, keepdims=True)


def basis(yaw):
    y = np.radians(yaw)
    f = np.stack([-np.sin(y), np.zeros_like(y), np.cos(y)], -1)
    left = np.stack([np.cos(y), np.zeros_like(y), np.sin(y)], -1)
    return f, left


def shoulder(feet, yaw, sy=1.0):
    f, left = basis(yaw)
    return feet + np.stack([np.zeros_like(yaw), 1.375 * np.asarray(sy) + 0 * yaw, np.zeros_like(yaw)], -1) - left * 0.3125


def arm_aim(feet, yaw, target, sy=1.0):
    """(xRot, zRot, length) for the RIGHT arm so the hand reaches target (calibrated: +zRot = out, xRot -90 = forward)."""
    S = shoulder(feet, yaw, sy)
    w = target - S
    n = np.linalg.norm(w, axis=-1)
    f, left = basis(yaw)
    Lc = np.sum(w * left, -1); U = w[..., 1]; F = np.sum(w * f, -1)
    a = np.degrees(np.arcsin(np.clip(-F / n, -1, 1)))
    c = np.degrees(np.arctan2(-Lc, -U))
    return a, c, n / 0.75


def hand_pos(feet, yaw, a, c, length, sy=1.0):
    S = shoulder(feet, yaw, sy)
    f, left = basis(yaw)
    ar, cr = np.radians(a), np.radians(c)
    dm = np.stack([-np.sin(cr) * np.cos(ar), np.cos(cr) * np.cos(ar), np.sin(ar)], -1)   # model space: x=left, y=down, z=back
    up = np.array([0, 1.0, 0])
    d = left * dm[..., :1] - up * dm[..., 1:2] - f * dm[..., 2:3]
    return S + d * (0.75 * np.asarray(length))[..., None]


# ------------------------------------------------------------------ pig flight: release -> T1 -> wall -> T2 -> ground -> hop -> rest
HIT = [  # (time, pig centre at contact, contact normal (outward from surface))
    (4.25, np.array([245.5, 67.6, 309.7]), np.array([-1.0, 0, 0])),     # T1 trunk west face
    (4.62, np.array([249.5, 68.3, 313.0]), np.array([-1.0, 0, 0])),     # wall west face
    (5.20, np.array([244.95, 68.1, 306.3]), unit([0.6, 0, 0.8])),       # T2 trunk south-east face
    (5.72, np.array([239.6, GY + 0.30, 309.8]), np.array([0, 1.0, 0])),  # ground
    (6.10, np.array([239.2, GY + 0.36, 310.7]), np.array([0, 1.0, 0])),  # small hop
]
REST = np.array([239.2, GY + 0.45, 310.8])
STICK = 0.07                                     # contact dwell (pig flattened against the surface)


def pig_state(t, rel_pos, rel_t=T_REL):
    """Free-flight pig after release. Returns centre, velocity, squash axis/amount, tumble angles."""
    t = np.atleast_1d(np.asarray(t, float))
    pts = [(rel_t, rel_pos, None)] + HIT
    pos = np.zeros((len(t), 3)); sq = np.zeros(len(t)); nrm = np.zeros((len(t), 3)); nrm[:, 1] = 1
    vel = np.zeros((len(t), 3)); g = 7.0
    for k in range(len(pts) - 1):
        ta, pa, _ = pts[k]; tb, pb, nb = pts[k + 1]
        ta2 = ta + (STICK if k > 0 else 0.0)
        m = (t >= ta2) & (t < tb)
        T = tb - ta2
        v0 = (pb - pa) / T; v0 = v0 + np.array([0, 0.5 * g * T, 0])
        tau = t[m] - ta2
        pos[m] = pa + v0 * tau[:, None] - np.array([0, 0.5 * g, 0]) * (tau ** 2)[:, None]
        vel[m] = v0 - np.array([0, g, 0]) * tau[:, None]
        mc = (t >= tb) & (t < tb + STICK)
        u = (t[mc] - tb) / STICK
        pos[mc] = pb - nb * 0.18 * np.sin(np.pi * u)[:, None]          # presses into the surface
        sq[mc] = np.sin(np.pi * u); nrm[mc] = nb
    tl = HIT[-1][0] + STICK
    m = t >= tl
    u = np.clip((t[m] - tl) / 0.35, 0, 1); e = 1 - (1 - u) ** 3
    pos[m] = HIT[-1][1] + (REST - HIT[-1][1]) * e[:, None]
    return pos, vel, sq, nrm


# ------------------------------------------------------------------ Matteeoo
def feet_fall(t):
    t = np.asarray(t, float)
    y0, T = GY + 7.0, T_LAND0
    v0 = (7.0 - 0.5 * 26 * T * T) / T
    y = np.where(t < T, y0 - v0 * t - 0.5 * 26 * t * t, GY)
    x = np.where(t < T, L[0] - 1.2 + 1.2 * np.clip(t / T, 0, 1), L[0])
    return np.stack([x, y, np.full_like(t, L[2])], -1)


def ground_h(x, z, t):
    """Rubber ground: landing dent + waves, pig ground bounces (smaller)."""
    x = np.asarray(x, float); z = np.asarray(z, float); t = np.asarray(t, float)
    h = np.zeros(np.broadcast(x, z, t).shape)
    imp = [(L[0], L[2], T_LAND0, T_LAND1, 0.5, 0.3, 2.3), (HIT[3][1][0], HIT[3][1][2], HIT[3][0], HIT[3][0] + STICK, 0.28, 0.14, 1.4),
           (HIT[4][1][0], HIT[4][1][2], HIT[4][0], HIT[4][0] + STICK, 0.14, 0.06, 1.2)]
    for cx, cz, t0, t1, D, A, rad in imp:
        r = np.hypot(x - cx, z - cz)
        u = (t - t0) / (t1 - t0)
        w = np.exp(-(r / rad) ** 2)
        h = h - D * w * np.where((u >= 0) & (u <= 1), bump(u), 0.0) - D * w * ring(t, t1, 0.5, 2.6, 5.0)
        tau = t - t0; k, om = 1.55, 13.0
        front = np.clip((om / k * tau - r) / 1.5 + 1, 0, 1) * (tau > 0)
        h = h + A * front * np.exp(-2.2 * np.maximum(tau, 0)) * np.exp(-r / 7.0) * np.sin(k * r - om * tau) * np.clip(r / 1.2, 0, 1)
    return np.sign(h) * np.maximum(np.abs(h) - 0.025, 0)


def build_actor_and_pig():
    ts = np.round(np.arange(0, DUR + 0.2, 1 / 120), 5)
    dt = ts[1] - ts[0]
    two = 2 * np.pi
    feet = feet_fall(ts)
    feet[:, 1] = np.where(ts >= T_LAND0, GY + ground_h(L[0], L[2], ts), feet[:, 1])
    # squash & stretch / superhero landing
    land = np.clip((ts - T_LAND0) / (T_LAND1 - T_LAND0), 0, 1)
    inl = (ts >= T_LAND0) & (ts <= T_LAND1)
    sy = np.where(ts < T_LAND0, 1.18, 1.0)
    sy = np.where(inl, 1 - 0.38 * np.sin(np.pi * land) ** 0.7, sy)
    sy = np.where((ts > T_LAND1) & (ts < T_LAND1 + 0.5), 0.86 + 0.14 * np.clip((ts - T_LAND1) / 0.4, 0, 1), sy)
    sy = spring(sy, dt, 38, 0.45)
    legs = np.where(inl, 1 - 0.32 * np.sin(np.pi * land), 1.0); legs = spring(legs, dt, 36, 0.6)
    lean = smooth_interp(ts, [(0, 0), (T_LAND0, 0), (T_LAND0 + 0.12, -22), (T_LAND1 + 0.2, -10), (T_POCKET, 0), (T_SHOW, 6), (T_REACH, 0), (DUR, 0)])
    # facing: toward camera-ish at first, toward pig for the grab, spin for the throw, then watch the pig
    yaw_cam = 35.0
    to_pig = math.degrees(math.atan2(-(PIG0[0] - L[0]), PIG0[2] - L[2]))
    spin = 450 * np.clip((ts - T_SPIN) / (T_REL - T_SPIN), 0, 1) ** 1.3
    yaw = smooth_interp(ts, [(0, yaw_cam), (T_REACH - 0.05, yaw_cam), (T_REACH + 0.15, to_pig), (DUR, to_pig)]) + spin
    # after the throw: turn to follow the pig, end facing camera laughing
    rel_yaw = to_pig + 450
    yaw = np.where(ts > T_REL, smooth_interp(ts, [(T_REL, rel_yaw), (T_REL + 0.5, rel_yaw - 30), (5.6, rel_yaw - 30), (6.4, 360 + yaw_cam), (DUR, 360 + yaw_cam)]), yaw)
    yaw = spring(yaw, dt, 22, 1.0)

    # -------- right arm (glove hand): pocket -> pull -> show -> reach pig -> retract -> T-spin -> throw -> laugh
    from borracha_c1 import arm_euler
    nR = len(ts)
    bR = np.full(nR, 25.0); thR = np.zeros(nR)
    def seg(a, b): return (ts >= a) & (ts < b)
    m = seg(0, T_LAND0); bR[m] = 120 + 15 * np.sin(two * 5 * ts[m]); thR[m] = -10
    m = seg(T_LAND0, T_POCKET); bR[m] = 75; thR[m] = 10
    m = seg(T_POCKET, T_PULL); bR[m] = 12; thR[m] = 18                   # hand into the pocket
    m = seg(T_PULL, T_REACH); bR[m] = 32; thR[m] = -112                   # glove up by the face, toward camera
    bR = spring(bR, dt, 30, 0.6); thR = spring(thR, dt, 30, 0.7)
    xR, zR = arm_euler(bR, thR, -1)
    lenR = np.ones(nR)
    item = np.zeros(nR)
    item = np.where(ts >= T_PULL + 0.04, 1.0, 0.0)
    item = item + np.where(ts >= T_PULL + 0.04, 0.45 * np.exp(-(ts - T_PULL - 0.04) * 7) * np.cos(two * 3 * (ts - T_PULL - 0.04)), 0)
    item = np.where(ts >= T_PULL + 0.04, np.maximum(item * np.clip((ts - T_PULL - 0.04) / 0.06, 0, 1), 0), 0)
    # reach & grab: aim at the pig, length grows (rubber arm), pig rides the glove back
    pig_pos = np.repeat(PIG0[None], nR, 0)
    m = seg(T_REACH, T_TOUCH + 0.15)
    u = np.clip((ts[m] - T_REACH) / (T_TOUCH - T_REACH), 0, 1); e = 1 - (1 - u) ** 2.2
    S = shoulder(feet[m], yaw[m], sy[m])
    wv = PIG0 + np.array([0, 0.1, 0]) - S
    dist = np.linalg.norm(wv, axis=1, keepdims=True)
    tgt = S + wv / dist * np.maximum(e[:, None] * dist, 0.75)          # never shorter than the natural arm
    a, c, ln = arm_aim(feet[m], yaw[m], tgt, sy[m])
    xR[m], zR[m], lenR[m] = a, c, np.maximum(ln, 1.0)
    m = seg(T_TOUCH + 0.15, T_SPIN)                                      # retract: pig pulled to the hand
    u = np.clip((ts[m] - T_TOUCH - 0.15) / (T_SPIN - T_TOUCH - 0.15), 0, 1); e = u * u * (3 - 2 * u)
    f, left = basis(yaw[m])
    near = shoulder(feet[m], yaw[m], sy[m]) - left * 0.9 + f * 0.5 + np.array([0, -0.1, 0])
    tgt = (PIG0 + np.array([0, 0.1, 0])) * (1 - e[:, None]) + near * e[:, None]
    a, c, ln = arm_aim(feet[m], yaw[m], tgt, sy[m])
    xR[m], zR[m], lenR[m] = a, c, np.maximum(ln, 1.0)
    pig_pos[m] = tgt
    m = seg(T_SPIN, T_REL)                                               # spin: arm out, longer (centrifugal), pig at the glove
    u = np.clip((ts[m] - T_SPIN) / 0.12, 0, 1)
    xR[m] = xR[m] * 0 + (-8) * u + xR[np.argmax(ts >= T_SPIN) - 1] * (1 - u)
    zR[m] = 88 * u + zR[np.argmax(ts >= T_SPIN) - 1] * (1 - u)
    lenR[m] = 1.25 + 0.6 * np.clip((ts[m] - T_SPIN) / (T_REL - T_SPIN), 0, 1)
    pig_pos[m] = hand_pos(feet[m], yaw[m], xR[m], zR[m], lenR[m] + 0.35, sy[m])
    rel_pos = pig_pos[np.argmax(ts >= T_REL) - 1].copy()
    # after release: arm follows through then the V laugh (both arms)
    m = ts >= T_REL
    bpost = smooth_interp(ts[m], [(T_REL, 88), (T_REL + 0.25, 70), (5.9, 60), (6.4, 125), (DUR, 128)])
    tpost = smooth_interp(ts[m], [(T_REL, -40), (T_REL + 0.3, -20), (5.9, -30), (6.4, -5), (DUR, -5)])
    xa, za = arm_euler(bpost, tpost, -1)
    xR[m], zR[m] = xa, za
    lenR[m] = smooth_interp(ts[m], [(T_REL, 1.85), (T_REL + 0.3, 1.0), (6.3, 1.0), (6.6, 1.5), (DUR, 1.55)])
    # smooth the joins (keep the rubber overshoot)
    xR = spring(xR, dt, 45, 0.75); zR = spring(zR, dt, 45, 0.75); lenR = np.clip(spring(lenR, dt, 40, 0.55), 0.8, 6.0)
    # left arm: balance / hand on hip, flails on landing, V at the end
    bL = smooth_interp(ts, [(0, 125), (T_LAND0, 125), (T_LAND0 + 0.1, 80), (T_POCKET, 40), (T_REACH, 35), (T_SPIN, 70), (T_REL, 95),
                            (T_REL + 0.4, 45), (5.9, 40), (6.4, 125), (DUR, 130)])
    tL = smooth_interp(ts, [(0, -10), (T_LAND0, 10), (T_POCKET, 25), (T_REACH, 30), (T_SPIN, 0), (DUR, -5)])
    bL = bL + 7 * np.sin(two * 1.5 * ts) * (ts > 6.4)
    bL = np.clip(spring(bL, dt, 30, 0.6), 18, 140); tL = spring(tL, dt, 30, 0.7)
    xL, zL = arm_euler(bL, tL, +1)
    lenL = smooth_interp(ts, [(0, 1), (6.3, 1), (6.6, 1.5), (DUR, 1.55)])
    rleg = smooth_interp(ts, [(0, -25), (T_LAND0, -10), (T_LAND0 + 0.1, -35), (T_LAND1 + 0.3, -8), (T_POCKET, 0), (DUR, 0)])
    lleg = smooth_interp(ts, [(0, 20), (T_LAND0, 10), (T_LAND0 + 0.1, 30), (T_LAND1 + 0.3, 6), (T_POCKET, 0), (DUR, 0)])
    legz = smooth_interp(ts, [(0, 8), (T_LAND0, 4), (T_LAND0 + 0.1, 16), (T_POCKET, 6), (DUR, 6)])
    head_x = smooth_interp(ts, [(0, -20), (T_LAND0, 0), (T_LAND0 + 0.1, 20), (T_LAND1 + 0.3, 5), (T_POCKET, 18), (T_PULL, 10), (T_SHOW, -8),
                                (T_REACH, 5), (T_REL, 0), (6.3, 0), (6.5, -25), (DUR, -20)])
    head_x = head_x + 5 * np.sin(two * 3.0 * ts) * (ts > 6.5)                          # laughing
    head_y = smooth_interp(ts, [(0, 0), (T_POCKET, -20), (T_PULL + 0.1, -25), (T_SHOW, -10), (T_REACH, 0), (DUR, 0)])

    # -------- pig: grazing -> touched (becomes rubber: jelly) -> carried -> flight/bounces -> dizzy rest
    pos_f, vel_f, sq_f, n_f = pig_state(ts, rel_pos)
    fl = ts >= T_REL
    pig_pos[fl] = pos_f[fl]
    psx = np.ones(nR); psy = np.ones(nR); psz = np.ones(nR)
    touch = ts - T_TOUCH
    jel = np.where(touch > 0, 0.35 * np.exp(-touch * 5) * np.sin(two * 4.5 * touch), 0)
    psy = psy + jel; psx = psx - 0.5 * jel; psz = psz - 0.5 * jel
    sp = np.linalg.norm(vel_f, axis=1)
    st = np.clip(sp / 16, 0, 1) * 0.45 * fl                              # stretch along velocity (world axes approx.)
    vd = np.abs(vel_f) / np.maximum(sp, 1e-6)[:, None]
    for i, arr in enumerate((psx, psy, psz)):
        arr += np.where(fl, st * (vd[:, i] * 1.6 - 0.5), 0)
    for i, arr in enumerate((psx, psy, psz)):                            # flatten against contacts along the normal
        arr *= np.where(fl, 1 - 0.55 * sq_f * np.abs(n_f[:, i]) + 0.25 * sq_f * (1 - np.abs(n_f[:, i])), 1)
    rest = ts - (HIT[-1][0] + STICK)
    wob = np.where(rest > 0, 0.22 * np.exp(-rest * 3) * np.sin(two * 3.2 * rest), 0)
    psy += wob; psx -= 0.5 * wob; psz -= 0.5 * wob
    pig_pos[:, 1] += np.where(rest > 0, (psy - 1) * 0.45, 0)
    pyaw = np.full(nR, 120.0)
    pyaw = np.where(ts > T_TOUCH, 120 + 40 * np.clip((ts - T_TOUCH) / 0.4, 0, 1), pyaw)
    proll = np.zeros(nR); ppitch = np.zeros(nR)
    tumble = np.cumsum(np.where(fl & (sq_f == 0) & (ts < HIT[-1][0]), 1, 0)) * dt
    proll = np.where(fl, 560 * tumble, 0); ppitch = np.where(fl, 230 * tumble, 0)
    proll = np.where(ts > HIT[3][0], 360 * np.round(560 * tumble[np.argmax(ts > HIT[3][0])] / 360) + 0 * proll, proll)
    ppitch = np.where(ts > HIT[3][0], 360 * np.round(230 * tumble[np.argmax(ts > HIT[3][0])] / 360) + 0 * ppitch, ppitch)
    proll = spring(proll, dt, 30, 1.0); ppitch = spring(ppitch, dt, 30, 1.0)
    pyaw = np.where(ts > HIT[3][0], spring(np.where(ts > HIT[3][0], 375.0, pyaw), dt, 10, 1.0), pyaw)   # ends facing the camera
    swing = np.where((ts > T_TOUCH) & (ts < HIT[-1][0] + 0.4), 0.09, 0.0) + np.where(ts > HIT[-1][0] + 0.4, 0.02, 0.0)

    actor = Actor("matteeoo", SKIN, feet[0], yaw=yaw_cam, hat=True, item=GLOVE)
    shadow = GY + ground_h(L[0], L[2], ts)
    for i, t in enumerate(ts):
        actor.key(float(t), ease="linear", x=feet[i, 0], y=feet[i, 1], z=feet[i, 2], yaw=yaw[i], lean=lean[i],
                  sy=sy[i], sx=1 / math.sqrt(max(sy[i], 0.4)), sz=1 / math.sqrt(max(sy[i], 0.4)), rleg_len=legs[i], lleg_len=legs[i],
                  rarm_x=xR[i], rarm_z=zR[i], rarm_len=lenR[i], larm_x=xL[i], larm_z=zL[i], larm_len=lenL[i],
                  rleg_x=rleg[i], lleg_x=lleg[i], rleg_z=legz[i], lleg_z=-legz[i], head_x=head_x[i], head_y=head_y[i],
                  item=item[i], shadow_y=float(shadow[i]))
    pig_rows = np.zeros((nR, 11))
    pig_rows[:, 0:3] = pig_pos; pig_rows[:, 3] = pyaw; pig_rows[:, 4] = ppitch; pig_rows[:, 5] = proll
    pig_rows[:, 6] = np.clip(psx, 0.35, 2.2); pig_rows[:, 7] = np.clip(psy, 0.35, 2.2); pig_rows[:, 8] = np.clip(psz, 0.35, 2.2)
    pig_rows[:, 9] = GY + ground_h(pig_pos[:, 0], pig_pos[:, 2], ts); pig_rows[:, 10] = swing
    def pig_fn(times):
        return np.stack([np.interp(times, ts, pig_rows[:, k]) for k in range(11)], -1)
    pig = Mob("pig", "minecraft:pig", PIG0, fn=pig_fn)
    return actor, pig, ts, feet, pig_pos, rel_pos


# ------------------------------------------------------------------ props: rubber ground, 2 rubber trees, rubber wall
GRID = [(x, z) for x in range(232, 245) for z in range(306, 319)]
TRUNK_H = 4
CANOPY = [(dx, 4, dz) for dx in (-1, 0, 1) for dz in (-1, 0, 1)] + [(dx, 5, dz) for dx in (-1, 0, 1) for dz in (-1, 0, 1)] + \
         [(0, 6, 0), (1, 6, 0), (-1, 6, 0), (0, 6, 1), (0, 6, -1)]


def ground_prop(x, z):
    cx, cz = x + 0.5, z + 0.5
    def f(times):
        h = ground_h(cx, cz, times)
        sy = np.clip(1 + h, 0.3, 1.8)
        out = np.zeros((len(times), 9))
        out[:, 0], out[:, 1], out[:, 2] = cx, GY - 1, cz
        out[:, 3] = out[:, 5] = np.clip(1 / np.sqrt(sy), 0.9, 1.25); out[:, 4] = sy
        return out
    return Prop(f"g_{x}_{z}", "minecraft:grass_block", (cx, GY - 1, cz), fn=f)


def tree_dyn(hit_t, push_dir, t):
    """Impact on the trunk: bends away from the hit (+ springs back past rest), canopy jiggles."""
    t = np.asarray(t, float)
    tau = t - hit_t
    env = np.where(tau > 0, np.exp(-tau * 2.8), 0)
    bend = np.where(tau > 0, 20 * np.sin(np.minimum(tau, 0.12) / 0.12 * np.pi / 2) * (tau < 0.12) + 20 * env * np.cos(2 * np.pi * 1.6 * np.maximum(tau - 0.12, 0)) * (tau >= 0.12), 0)
    idle = 1.5 * np.sin(2 * np.pi * 0.8 * t + push_dir[0])
    ks = 1 + np.where(tau > 0, 0.18 * np.exp(-tau * 4) * np.sin(2 * np.pi * 3 * tau), 0)
    return bend * push_dir[0] + idle, bend * push_dir[1], ks


def tree_block(base, hit_t, push_dir, lx, ly, lz, kind):
    bx0, bz0 = base[0] + 0.5, base[1] + 0.5
    def f(times):
        bx, bz, ks = tree_dyn(hit_t, push_dir, times)
        H = TRUNK_H + 3 * ks
        y1 = ly if ly < TRUNK_H else TRUNK_H + (ly - TRUNK_H) * ks
        sy = 1.0 if ly < TRUNK_H else ks
        fx = np.radians(bx) * y1 / H; fz = np.radians(bz) * y1 / H
        dx = np.radians(bx) * y1 ** 2 / (2 * H); dz = np.radians(bz) * y1 ** 2 / (2 * H)
        out = np.zeros((len(times), 9))
        out[:, 0] = bx0 + dx + lx * np.cos(fx); out[:, 2] = bz0 + dz + lz * np.cos(fz)
        out[:, 1] = GY + y1 - lx * np.sin(fx) - lz * np.sin(fz)
        sxz = 1 / np.sqrt(np.maximum(sy, 0.3))
        out[:, 3] = sxz; out[:, 4] = sy; out[:, 5] = sxz
        if kind == "log" and ly == 1:                                    # the hit log dents along the push direction
            u = (np.asarray(times) - hit_t) / STICK
            d = np.where((u >= 0) & (u <= 1), np.sin(np.pi * np.clip(u, 0, 1)), 0) * 0.35
            out[:, 3] *= 1 - d * abs(push_dir[0]); out[:, 5] *= 1 - d * abs(push_dir[1])
        out[:, 7] = np.degrees(fz); out[:, 8] = -np.degrees(fx)
        return out
    return f


def wall_block(x, y, z):
    hit_t, hp = HIT[1][0], HIT[1][1]
    def f(times):
        t = np.asarray(times, float)
        r = math.hypot(y + 0.5 - hp[1], z + 0.5 - hp[2])
        w = math.exp(-(r / 1.5) ** 2)
        u = (t - hit_t) / STICK
        d = 0.5 * w * np.where((u >= 0) & (u <= 1), np.sin(np.pi * np.clip(u, 0, 1)), 0)
        tau = t - hit_t - STICK
        d = d + np.where(tau > 0, -0.3 * w * np.exp(-tau * 4.5) * np.sin(2 * np.pi * 2.6 * tau), 0)   # springs back, wobbles
        k, om = 1.8, 14.0
        d = d + np.where(t > hit_t, 0.08 * np.exp(-3 * np.maximum(t - hit_t, 0)) * np.sin(k * r - om * (t - hit_t)) * (r > 0.8), 0)
        out = np.zeros((len(t), 9))
        out[:, 0] = x + 0.5 + d / 2; out[:, 1] = y; out[:, 2] = z + 0.5
        out[:, 3] = 1 - d; out[:, 4] = 1 + 0.4 * d; out[:, 5] = 1 + 0.4 * d
        return out
    return f


def build_props():
    props = [ground_prop(x, z) for (x, z) in GRID]
    for base, hit, push in ((T1, HIT[0][0], (1.0, 0.0)), (T2, HIT[2][0], (-0.6, -0.8))):
        for k in range(TRUNK_H):
            props.append(Prop(f"log_{base}_{k}", "minecraft:oak_log[axis=y]", (0, 0, 0), fn=tree_block(base, hit, push, 0, k, 0, "log")))
        for j, (lx, ly, lz) in enumerate(CANOPY):
            props.append(Prop(f"leaf_{base}_{j}", "minecraft:oak_leaves[persistent=true]", (0, 0, 0), fn=tree_block(base, hit, push, lx, ly, lz, "leaf")))
    for z in WALL_Z:
        for y in WALL_Y:
            props.append(Prop(f"wall_{y}_{z}", "minecraft:stone_bricks", (WALL_X + 0.5, y, z + 0.5), fn=wall_block(WALL_X, y, z)))
    return props


def stage_commands():
    x0, z0, x1, z1 = REG
    cmds = [f"fill {x0} 66 {z0} {x1} 76 {z1} minecraft:air", f"fill {x0} 77 {z0} {x1} 92 {z1} minecraft:air",
            f"fill {x0} 65 {z0} {x1} 65 {z1} minecraft:grass_block", f"fill {x0} 60 {z0} {x1} 64 {z1} minecraft:dirt",
            "fill 232 65 306 244 65 318 minecraft:air"]
    trees = [(224, 298, "fancy_oak"), (229, 299, "oak"), (233, 297, "birch"), (237, 299, "oak"), (249, 298, "fancy_oak"),
             (255, 297, "birch"), (259, 300, "oak"), (224, 305, "oak"), (225, 312, "birch"), (224, 319, "oak"),
             (258, 306, "oak"), (256, 319, "fancy_oak"), (258, 326, "birch"), (230, 326, "oak"), (247, 327, "birch")]
    for x, z, f in trees:
        cmds.append(f"place feature minecraft:{f} {x} 66 {z}")
    rnd = random.Random(23)
    flowers = ["minecraft:grass", "minecraft:grass", "minecraft:grass", "minecraft:dandelion", "minecraft:poppy",
               "minecraft:azure_bluet", "minecraft:oxeye_daisy", "minecraft:cornflower"]
    for _ in range(190):
        x, z = rnd.randint(x0 + 1, x1 - 1), rnd.randint(z0 + 1, z1 - 1)
        if 231 <= x <= 252 and 300 <= z <= 319:
            continue
        cmds.append(f"setblock {x} 66 {z} {rnd.choice(flowers)}")
    return cmds


SCENE_ANCHOR = (241, 80, 311)
WORLD = World(seed=4242)


def settings(frozen=False):
    return Settings(renderDistance=10, simulationDistance=6, worldTicks=not frozen)


# ------------------------------------------------------------------ camera
_CACHE = {}


def anim_data():
    if "d" not in _CACHE:
        _CACHE["d"] = build_actor_and_pig()
    return _CACHE["d"]


def interp3(ts, arr, t):
    return np.stack([np.interp(t, ts, arr[:, k]) for k in range(3)], -1)


def lag(ts, arr, tau):
    out = arr.copy(); k = 1 - math.exp(-(ts[1] - ts[0]) / tau)
    for i in range(1, len(arr)):
        out[i] = out[i - 1] + k * (arr[i] - out[i - 1])
    return out


def spline(keys):
    from scipy.interpolate import CubicSpline
    kt = np.array([k[0] for k in keys]); kp = np.array([k[1] for k in keys])
    sp = CubicSpline(kt, kp, bc_type="natural")
    return lambda t: sp(np.clip(t, kt[0], kt[-1]))


def build_rig(subframes=8):
    actor, pig, ts, feet, pig_pos, rel = anim_data()
    rig = Rig(fps=FPS, subframes=subframes, shutter=0.5)
    body = feet + np.array([0, 1.1, 0])
    glove = body.copy()
    # shot 1: low under the fall -> landing -> push in on the glove reveal
    p1 = spline([(0.0, (235.1, 66.45, 315.7)), (T_LAND1, (235.4, 66.55, 315.35)), (T_PULL, (235.9, 67.0, 315.0)), (CUT1, (236.5, 67.55, 314.7))])
    aim1 = lag(ts, body, 0.08)
    aim_show = L + np.array([0.25, 1.75, 0.45])
    def fn1(tau):
        t = tau * CUT1
        pos = p1(t)
        a = interp3(ts, aim1, t)
        w = smooth_interp(t, [(0, 0), (T_PULL - 0.2, 0), (T_SHOW, 1), (CUT1, 1)])[:, None]
        a = a * (1 - w) + aim_show[None] * w
        yaw, pitch = look_at(pos, a)
        fwd = forward(yaw, pitch)
        return {"x": pos[:, 0], "y": pos[:, 1], "z": pos[:, 2], "yaw": np.degrees(np.unwrap(np.radians(yaw))), "pitch": pitch,
                "roll": smooth_interp(t, [(0, 4), (T_LAND0, -3), (T_LAND1, 2), (CUT1, 0)]),
                "fov": smooth_interp(t, [(0, 74), (T_LAND1, 70), (T_PULL, 60), (CUT1, 52)]),
                "focus": np.maximum(np.sum((a - pos) * fwd, -1), 0.5), "aperture": np.full_like(t, 0.35)}
    rig.add(Move(CUT1, fn1, "land_glove").with_handheld("subtle"))
    # shot 2 (continuous to the end): side-on for the rubber arm grab and the spin, then follow the ricochets, settle on both
    p2 = spline([(CUT1, (237.4, 67.9, 318.9)), (T_SPIN, (237.0, 68.3, 319.3)), (T_REL, (237.2, 68.7, 319.2)), (4.35, (241.8, 69.2, 318.0)),
                 (5.0, (242.8, 69.4, 317.0)), (5.5, (242.0, 68.8, 316.8)), (6.2, (239.3, 67.8, 316.4)), (DUR, (238.6, 67.4, 315.6))])
    mid = (feet + np.array([0, 1.0, 0])) * 0.5 + (pig_pos) * 0.5
    follow = lag(ts, pig_pos, 0.06)
    both = (feet + np.array([0, 1.0, 0])) * 0.55 + pig_pos * 0.45
    T2D = DUR - CUT1
    def fn2(tau):
        t = CUT1 + tau * T2D
        pos = p2(t)
        a_mid = interp3(ts, lag(ts, mid, 0.1), t); a_pig = interp3(ts, follow, t); a_both = interp3(ts, lag(ts, both, 0.15), t)
        w1 = smooth_interp(t, [(CUT1, 0), (T_REL - 0.05, 0), (T_REL + 0.12, 1), (5.75, 1), (6.25, 0), (DUR, 0)])[:, None]
        w2 = smooth_interp(t, [(CUT1, 0), (5.75, 0), (6.25, 1), (DUR, 1)])[:, None]
        a = a_mid * (1 - w1) + a_pig * w1
        a = a * (1 - w2) + a_both * w2
        yaw, pitch = look_at(pos, a)
        fwd = forward(yaw, pitch)
        return {"x": pos[:, 0], "y": pos[:, 1], "z": pos[:, 2], "yaw": np.degrees(np.unwrap(np.radians(yaw))), "pitch": pitch,
                "roll": smooth_interp(t, [(CUT1, -2), (T_REL, 5), (4.7, -4), (5.5, 3), (DUR, 0)]),
                "fov": smooth_interp(t, [(CUT1, 58), (T_SPIN, 60), (T_REL, 68), (5.6, 68), (DUR, 56)]),
                "focus": np.maximum(np.sum((a - pos) * fwd, -1), 0.5), "aperture": np.full_like(t, 0.25)}
    rig.add(Move(T2D, fn2, "grab_throw_ricochet").with_handheld("subtle"), cut=True)
    return rig


def build_anim():
    actor, pig, *_ = anim_data()
    return Anim([actor], props=build_props(), mobs=[pig])


if __name__ == "__main__":
    actor, pig, ts, feet, pig_pos, rel = anim_data()
    print("release", np.round(rel, 2))
    for t in [0, 0.5, 0.7, 1.7, 2.7, 2.85, 3.1, 3.5, 3.85, 4.25, 4.62, 5.2, 5.72, 6.1, 6.6]:
        i = np.argmin(abs(ts - t)); print(t, "feet", np.round(feet[i], 2), "pig", np.round(pig_pos[i], 2))
