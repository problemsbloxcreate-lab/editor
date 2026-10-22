"""Cena 2 — Matteeoo corre, salta (borracha) e fica na frente do SOL, a silhueta se intensifica (ref: Luffy Gear 5 moon scene).
3 planos com corte seco (como a ref): A corrida+salto por trás (câmera baixa) | B colado no corpo voando, gira até a contraluz |
C tele de baixo: sol enorme, ele sobe pra dentro do sol e fica pairando em pose Nika; flash branco + raios + halo (pós).
"""
import sys, math, random
sys.path.insert(0, r"C:\Users\mathe\.claude\skills\minecraft-cinematic\scripts")
sys.path.insert(0, r"C:\Users\mathe\AppData\Local\Temp\claude\C--Users-mathe-Skills\9241dd35-0dcc-47dd-801e-fe2e4981f49a\scratchpad")
import numpy as np
from cinecam import *
from cinecam.camlib import Move
from borracha_c1 import make_skin, SKIN, spring, arm_euler, smooth_interp, REG, GY

OUT = r"D:/cinecam-out/borracha_c2"
FPS, DUR = 30, 6.0
TIME = 1370                         # sun ~33 deg above the east horizon
CUT1, CUT2 = 1.7, 3.0
LANE_Z = 312.0


def sun_dir(t=TIME):
    """Vanilla LevelRenderer: Ry(-90)*Rx(celestial*360)*(0,1,0) -> (-sin a, cos a, 0)."""
    d = (t / 24000.0 - 0.25) % 1.0
    g = 0.5 - math.cos(d * math.pi) / 2
    c = (2 * d + g) / 3
    a = 2 * math.pi * c
    v = np.array([-math.sin(a), math.cos(a), 0.0])
    return v / np.linalg.norm(v)


SUN = sun_dir()
APEX = np.array([256.0, 78.0, LANE_Z])
SUN_SCALE = 2.7                     # vanilla sun drawn 3.7x bigger (mod) so it fills the tele shot like the ref's moon
CAM_C = APEX + np.array([0, 1.05, 0]) - SUN * 17.0   # shot C camera: his body centre dead centre in the sun


# ----------------------------------------------------------------- character path (cheated across cuts like the ref)
RUN0, RUNV = 231.0, 6.5
T_CROUCH, T_TAKE = 1.15, 1.35
TAKE = np.array([RUN0 + RUNV * T_CROUCH + 0.8, GY, LANE_Z])
V1 = np.array([8.5, 14.0, 0.0]); G1 = 8.0     # floaty rubber super-jump
C_START = APEX + np.array([0.0, -4.6, -4.4])      # shot C: enters the sun from lower-LEFT (north), moving screen-right like shot B


def feet(t):
    t = np.atleast_1d(np.asarray(t, float))
    out = np.zeros((len(t), 3))
    run = t < T_CROUCH
    out[run] = np.c_[RUN0 + RUNV * t[run], np.full(run.sum(), GY), np.full(run.sum(), LANE_Z)]
    cr = (t >= T_CROUCH) & (t < T_TAKE)
    u = (t[cr] - T_CROUCH) / (T_TAKE - T_CROUCH)
    out[cr] = np.c_[RUN0 + RUNV * T_CROUCH + 0.8 * np.sin(u * np.pi / 2), np.full(cr.sum(), GY), np.full(cr.sum(), LANE_Z)]
    fl = (t >= T_TAKE) & (t < CUT2 - 0.015)
    tau = t[fl] - T_TAKE
    out[fl] = TAKE[None] + V1[None] * tau[:, None] - np.c_[np.zeros_like(tau), 0.5 * G1 * tau ** 2, np.zeros_like(tau)]
    c = t >= CUT2 - 0.015                                   # shot C: rises into the sun, decelerates, hangs
    w = np.clip((t[c] - CUT2) / 0.95, 0, 1)
    e = 1 - (1 - w) ** 3
    p = C_START[None] + (APEX - C_START)[None] * e[:, None]
    h = np.maximum(t[c] - CUT2 - 0.95, 0)
    p[:, 1] += 0.18 * np.sin(2 * np.pi * 0.7 * h) + 0.08 * h
    p[:, 2] += 0.12 * h                                          # keeps drifting screen-right, slowly
    out[c] = p
    return out


def centre(t):
    return feet(t) + np.array([0, 1.05, 0])


def build_actor():
    a = Actor("matteeoo", SKIN, feet(np.array([0.0]))[0], yaw=-90, hat=True)
    ts = np.round(np.arange(0, DUR + 0.2, 1 / 120), 5)
    dt = ts[1] - ts[0]
    P = feet(ts)
    two = 2 * np.pi
    run = ts < T_CROUCH
    ph = two * 3.1 * ts
    # legs: run cycle -> crouch -> air split -> Nika (one knee up)
    rleg = np.where(run, 58 * np.sin(ph), 0.0); lleg = np.where(run, -58 * np.sin(ph), 0.0)
    air = ts >= T_TAKE
    rleg = np.where(air, smooth_interp(ts, [(T_TAKE, 0), (T_TAKE + 0.2, -75), (CUT2, -70), (CUT2 + 0.5, -80), (DUR, -72)]), rleg)
    lleg = np.where(air, smooth_interp(ts, [(T_TAKE, 0), (T_TAKE + 0.2, 55), (CUT2, 50), (CUT2 + 0.5, 45), (DUR, 40)]), lleg)
    rleg = spring(rleg, dt, 30, 0.7); lleg = spring(lleg, dt, 30, 0.7)
    # arms (direction space: beta = away from body, theta = forward(-)/back(+) swing)
    bR = np.where(run, 22.0, 0); bL = bR.copy()
    thR = np.where(run, -62 * np.sin(ph), 0); thL = -thR
    cr = (ts >= T_CROUCH) & (ts < T_TAKE)
    bR[cr] = bL[cr] = 30; thR[cr] = thL[cr] = 70                     # wind-up: arms swing back
    m = (ts >= T_TAKE) & (ts < CUT2)
    tt = ts[m] - T_TAKE
    bR[m] = 26; bL[m] = 24                                          # arms swing in the body's side plane -> read in profile
    thR[m] = -105 + 12 * np.sin(two * 2.2 * tt); thL[m] = 70 + 12 * np.sin(two * 2.2 * tt + 1)  # leap: one arm reaching ahead, one back
    m = ts >= CUT2
    tt = ts[m] - CUT2
    k = np.clip(tt / 0.9, 0, 1)
    bR[m] = 26; bL[m] = 24                                          # profile silhouette: one arm up-forward, one up-back
    thR[m] = -105 - 45 * k + 8 * np.sin(two * 1.3 * tt); thL[m] = 70 + 55 * k + 8 * np.sin(two * 1.3 * tt + 1.8)
    bR = np.clip(spring(bR, dt, 30, 0.6), 18, 140); bL = np.clip(spring(bL, dt, 30, 0.6), 18, 140)
    thR = spring(thR, dt, 34, 0.8); thL = spring(thL, dt, 34, 0.8)
    xR, zR = arm_euler(bR, thR, -1); xL, zL = arm_euler(bL, thL, +1)
    alen = smooth_interp(ts, [(0, 1.0), (T_TAKE, 1.0), (T_TAKE + 0.25, 1.35), (CUT2 - 0.05, 1.35), (CUT2, 1.2), (CUT2 + 1.0, 1.9), (DUR, 1.95)])
    alen = alen + 0.08 * np.sin(two * 2.0 * ts) * (ts > CUT2 + 1.0)
    # body: lean into the run, squash on the crouch, stretch on launch (rubber)
    lean = np.where(run, -14.0, 0)
    lean = np.where(cr, -24.0, lean)
    lean = np.where(air, smooth_interp(ts, [(T_TAKE, -24), (T_TAKE + 0.3, -18), (CUT2 - 0.02, -14), (CUT2, -26), (CUT2 + 0.95, -4), (DUR, 2)]), lean)
    lean = spring(lean, dt, 22, 0.9)
    sy = np.ones_like(ts)
    sy = np.where(cr, 1 - 0.28 * np.sin(np.clip((ts - T_CROUCH) / (T_TAKE - T_CROUCH), 0, 1) * np.pi / 2), sy)
    pop = np.exp(-np.maximum(ts - T_TAKE, 0) * 6) * air
    sy = np.where(air, 1 + 0.3 * pop, sy)
    sy = spring(sy, dt, 40, 0.5)
    sxz = 1 / np.sqrt(np.clip(sy, 0.5, 2))
    legs = np.where(cr, 0.8, 1.0); legs = spring(legs, dt, 40, 0.6)
    hop = np.where(run, 0.13 * np.abs(np.sin(ph)), 0.0)
    head_x = smooth_interp(ts, [(0, -4), (T_CROUCH, 6), (T_TAKE, -10), (CUT2, -14), (CUT2 + 0.9, -24), (DUR, -20)])
    head_x = head_x + 4 * np.sin(two * 1.1 * ts) * (ts > CUT2 + 0.9)
    # facing: run east (yaw -90); in the air turn 3/4 so the silhouette reads (legs split + V arms)
    yaw = np.where(ts >= CUT2 - 0.015, smooth_interp(ts, [(0, 0), (CUT2, 0), (DUR, -6)]), -90.0)   # A/B face travel (east); C profile, facing screen-right
    # silhouette: backlit already running toward the sun; deepens as he crosses into it
    sil = smooth_interp(ts, [(0, 0.35), (T_TAKE, 0.4), (CUT1, 0.62), (CUT1 + 0.25, 0.7), (CUT1 + 0.75, 0.92), (CUT2, 0.95), (CUT2 + 0.8, 0.97), (DUR, 0.97)])
    shadow = np.where(P[:, 1] < GY + 7, GY, 0.0)
    for i, t in enumerate(ts):
        a.key(float(t), ease="linear", x=P[i, 0], y=P[i, 1], z=P[i, 2], yaw=yaw[i], lean=lean[i], hop=hop[i],
              sy=sy[i], sx=sxz[i], sz=sxz[i], rleg_len=legs[i], lleg_len=legs[i],
              rarm_x=xR[i], rarm_z=zR[i], larm_x=xL[i], larm_z=zL[i], rarm_len=alen[i], larm_len=alen[i],
              rleg_x=rleg[i], lleg_x=lleg[i], rleg_z=6, lleg_z=-6, head_x=head_x[i], silhouette=sil[i], shadow_y=float(shadow[i]))
    return a


# ----------------------------------------------------------------- stage
def stage_commands():
    x0, z0, x1, z1 = REG
    cmds = [f"fill {x0} 66 {z0} {x1} 76 {z1} minecraft:air", f"fill {x0} 77 {z0} {x1} 92 {z1} minecraft:air",
            f"fill {x0} 65 {z0} {x1} 65 {z1} minecraft:grass_block", f"fill {x0} 60 {z0} {x1} 64 {z1} minecraft:dirt"]
    trees = [(224, 298, "fancy_oak"), (229, 299, "oak"), (233, 297, "birch"), (237, 299, "oak"), (245, 298, "fancy_oak"),
             (251, 299, "oak"), (255, 297, "birch"), (224, 305, "oak"), (225, 312, "birch"), (224, 319, "oak"),
             (258, 304, "oak"), (258, 322, "birch"), (226, 326, "oak"), (236, 327, "birch"), (247, 326, "oak")]          # (258,304)/(258,322) sit low in the corners of the sun shot like the ref's rocks
    for x, z, f in trees:
        cmds.append(f"place feature minecraft:{f} {x} 66 {z}")
    rnd = random.Random(11)
    flowers = ["minecraft:grass", "minecraft:grass", "minecraft:grass", "minecraft:tall_grass", "minecraft:dandelion",
               "minecraft:poppy", "minecraft:oxeye_daisy", "minecraft:cornflower"]
    for _ in range(220):
        x, z = rnd.randint(x0 + 1, x1 - 1), rnd.randint(z0 + 1, z1 - 1)
        if abs(z - LANE_Z) <= 1 and x < 250:
            continue
        f = rnd.choice(flowers)
        if f == "minecraft:tall_grass":
            cmds.append(f"setblock {x} 66 {z} minecraft:tall_grass[half=lower]"); cmds.append(f"setblock {x} 67 {z} minecraft:tall_grass[half=upper]")
        else:
            cmds.append(f"setblock {x} 66 {z} {f}")
    return cmds


SCENE_ANCHOR = (245, 80, LANE_Z)
WORLD = World(seed=4242)


def settings(frozen=False):
    return Settings(renderDistance=10, simulationDistance=6, worldTicks=not frozen, clouds=False)   # clouds would cross the sun silhouette


# ----------------------------------------------------------------- camera: 3 shots, hard cuts
def aim_fn(t0, T, lag=0.06, offset=(0, 0, 0)):
    tt = np.arange(t0 - 0.4, t0 + T + 0.2, 1 / 240)
    c = centre(tt)
    sm = c.copy(); k = 1 - np.exp(-(1 / 240) / lag)
    for i in range(1, len(tt)):
        sm[i] = sm[i - 1] + k * (c[i] - sm[i - 1])
    off = np.array(offset)
    return lambda t: np.c_[np.interp(t, tt, sm[:, 0]), np.interp(t, tt, sm[:, 1]), np.interp(t, tt, sm[:, 2])] + off[None]


def shot(t0, t1, pos_fn, aim, fov_knots, roll_knots, name, focus=True, aperture=0.3):
    T = t1 - t0
    def fn(tau):
        t = t0 + np.asarray(tau, float) * T
        pos = pos_fn(t)
        yaw, pitch = look_at(pos, aim(t))
        f = forward(yaw, pitch)
        out = {"x": pos[:, 0], "y": pos[:, 1], "z": pos[:, 2], "yaw": np.degrees(np.unwrap(np.radians(yaw))), "pitch": pitch,
               "roll": smooth_interp(t, roll_knots), "fov": smooth_interp(t, fov_knots)}
        if focus:
            out["focus"] = np.maximum(np.sum((centre(t) - pos) * f, axis=-1), 0.5)
            out["aperture"] = np.full_like(t, aperture)
        return out
    return Move(T, fn, name)


def spline_pos(keys):
    from scipy.interpolate import CubicSpline
    kt = np.array([k[0] for k in keys]); kp = np.array([k[1] for k in keys])
    sp = CubicSpline(kt, kp, bc_type="natural")
    return lambda t: sp(np.clip(t, kt[0], kt[-1]))


def build_rig(subframes=8):
    rig = Rig(fps=FPS, subframes=subframes, shutter=0.5)
    # A: low behind-left, he runs away toward the sun and leaps; camera tilts up to follow (sun enters frame)
    posA = spline_pos([(0.0, (227.6, 66.45, 313.1)), (0.8, (230.4, 66.5, 313.2)), (1.3, (232.3, 66.55, 313.1)), (CUT1, (233.3, 66.6, 313.0))])
    rig.add(shot(0.0, CUT1, posA, aim_fn(0, CUT1, lag=0.08, offset=(0, 0.1, 0)), [(0, 66), (1.2, 64), (CUT1, 70)], [(0, -3), (CUT1, 4)],
                 "A_run_leap").with_handheld("subtle"))
    # B: glued to his body in flight, orbiting from his side to the anti-sun side -> close silhouette against the sun
    def posB(t):
        c = centre(t)
        u = np.clip((t - CUT1) / (CUT2 - CUT1), 0, 1); u = u * u * (3 - 2 * u)
        off = np.array([-0.9, -0.8, 2.7])[None] * (1 - u)[:, None] + np.array([0.7, -1.4, 2.3])[None] * u[:, None]
        return c + off
    rig.add(shot(CUT1, CUT2, posB, aim_fn(CUT1, CUT2 - CUT1, lag=0.03, offset=(0.35, 0, 0)), [(CUT1, 76), (CUT2, 68)], [(CUT1, 8), (CUT2, -5)],
                 "B_flight_close", aperture=0.45).with_handheld((0.6, 0.5, 2.5)), cut=True)
    # C: telephoto from below — the sun fills the frame, he rises into it and hangs; slow push-in
    posC = lambda t: CAM_C[None] + (SUN * 1.6)[None] * smooth_interp(t, [(CUT2, 0), (DUR, 1)])[:, None] + np.array([0, 0, 0.0])[None]
    sunpt = lambda t: np.repeat((CAM_C + SUN * 60)[None], len(np.atleast_1d(t)), 0)
    aimC = lambda t: sunpt(t) * 0.85 + centre(t) * 0.15
    rig.add(shot(CUT2, DUR, posC, aimC, [(CUT2, 44), (DUR, 33)], [(CUT2, -2), (DUR, 1.5)], "C_sun", focus=False)
            .with_handheld("breath"), cut=True)
    return rig


def build_anim():
    return Anim([build_actor()])


if __name__ == "__main__":
    print("sun dir", SUN, "elev", math.degrees(math.asin(SUN[1])), "CAM_C", CAM_C)
