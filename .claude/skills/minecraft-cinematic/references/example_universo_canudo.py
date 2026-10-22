"""Patão gigante no universo bebendo de canudinho toda a água de um 'mundo' flutuante — 3 s @60."""
import sys, math; sys.path.insert(0, r"C:\Users\mathe\.claude\skills\minecraft-cinematic\scripts")
import numpy as np
from cinecam import *

SK = r"C:/Users/mathe/AppData/Roaming/ModrinthApp/profiles/Construir Pirâmide/config/bbs/assets/models/skins/0.Turma/"
PAT = SK + "ajudantes/cariocapato.png"
FPS = 60
A, B, C = 54 / FPS, 72 / FPS, 54 / FPS
TOTAL = A + B + C                      # 3.0 s

CX, CZ = 0, 700                        # centre of the floating world slab (The End void, far from the main island)
HALF = 48                              # slab = 96 x 96
R = 30                                 # ocean basin radius
SEA_TOP = 65.0                         # water surface height
TIP = (2.0, 61.0, 702.0)               # where the straw sits in the sea
GIANT = dict(x=0.0, y=40.0, z=640.0, s=50.0)   # Patão: feet position + scale (2-block model * 50 = 100 blocks tall)


def world_commands():
    c = []
    x0, x1, z0, z1 = CX - HALF, CX + HALF - 1, CZ - HALF, CZ + HALF - 1
    # inverted-pyramid underside (floating chunk look)
    for k in range(1, 9):
        c.append(f"fill {x0 + 4*k} {44 - k} {z0 + 4*k} {x1 - 4*k} {44 - k} {z1 - 4*k} minecraft:stone" if k < 6 else
                 f"fill {x0 + 4*k} {44 - k} {z0 + 4*k} {x1 - 4*k} {44 - k} {z1 - 4*k} minecraft:deepslate")
    for zz in range(z0, z1 + 1, 16):
        c.append(f"fill {x0} 44 {zz} {x1} 62 {min(zz + 15, z1)} minecraft:stone")
    c.append(f"fill {x0} 63 {z0} {x1} 65 {z1} minecraft:dirt")
    c.append(f"fill {x0} 66 {z0} {x1} 66 {z1} minecraft:grass_block")
    for dz in range(-R, R + 1):
        hw = int(math.sqrt(R * R - dz * dz))
        z = CZ + dz
        c.append(f"fill {CX - hw} 59 {z} {CX + hw} 66 {z} minecraft:air")
        c.append(f"fill {CX - hw} 57 {z} {CX + hw} 58 {z} minecraft:sand")
        c.append(f"fill {CX - hw} 59 {z} {CX + hw} 64 {z} minecraft:water")
    for (tx, tz, f) in [(-38, 668, "oak"), (36, 672, "fancy_oak"), (-40, 730, "birch"), (38, 736, "oak"), (-12, 744, "fancy_oak"),
                        (20, 662, "birch"), (-30, 700, "oak"), (42, 704, "birch")]:
        c.append(f"place feature minecraft:{f} {CX + tx} 67 {tz}")
    for lx in range(CX - 44, CX + 46, 11):
        for lz in range(CZ - 44, CZ + 46, 11):
            c.append(f"setblock {lx} 70 {lz} minecraft:light[level=15]")
    rng = np.random.default_rng(11)
    for _ in range(260):
        sx = int(rng.uniform(-135, 135)); sz = int(rng.uniform(520, 600)); sy = int(rng.uniform(30, 250))
        c.append(f"setblock {sx} {sy} {sz} minecraft:end_rod[facing={rng.choice(['up','down','north','south','east','west'])}]")
    return c


def smooth(u):
    u = np.clip(u, 0, 1); return u * u * (3 - 2 * u)


def level(t):                          # water surface at the funnel centre
    return SEA_TOP + (45.0 - SEA_TOP) * smooth((np.asarray(t, float) - 0.12) / (2.35 - 0.12))


def funnel(t):                         # whirlpool depression: surface rises with distance from the straw
    return 0.36 * float(smooth(np.asarray(t, float) / 0.55))


def prog(t):
    return float(np.clip((SEA_TOP - level(t)) / (SEA_TOP - 50.0), 0, 1))


def build_giant():
    g = Actor("patao", PAT, (GIANT["x"], GIANT["y"], GIANT["z"]), yaw=0)
    s = GIANT["s"]
    g.key(0.0, sx=s, sy=s, sz=s, bright=1, head_x=14, rarm_z=-18, larm_z=18, rarm_x=-8, larm_x=-8)
    ts = np.arange(0.0, 2.45, 0.05)
    for t in ts:
        p = prog(t)
        g.key(float(t), ease="linear", belly=1 + 2.1 * p, belly_y=1 + 0.35 * p, head=1.0 + 0.06 * p, head_x=14 - 6 * p)
    g.wobble("head", 0.25, 2.3, 0.045, 5.5)
    g.wobble("belly", 0.4, 2.35, 0.07, 6.5)
    g.wobble("rarm_z", 0.2, 2.4, 6, 2.3)
    g.wobble("larm_z", 0.2, 2.4, 6, 2.3, 0.0, 1.5)
    # last gulp, then big satisfied "ahh" with cheeks blowing out
    g.key(2.45, ease="out", head_x=-28, head=1.28, belly=3.1, belly_y=1.35)
    g.key(2.7, ease="out_back", head_x=-34, head=1.12, belly=3.25, belly_y=1.42, rarm_x=-30, larm_x=-30)
    g.key(3.0, ease="smooth", head_x=-24, head=1.0, belly=3.2, belly_y=1.4)
    g.wobble("belly", 2.5, 3.0, 0.12, 8.0, 2.5)
    return g


def build_anim():
    g = build_giant()

    def straw_beams(tm):
        out = []
        alive = tm < 2.55
        if not alive:
            return out
        m = mouth_position(g, tm)
        tip = (TIP[0], TIP[1], TIP[2])
        lift, push = bent_straw(tip, m)
        ramp = float(np.clip(tm / 0.12, 0, 1))
        out.append(tube(tip, m, 1.45, 1.45, alpha=0.5 * ramp, lift=lift, push_z=push, style=1, segments=70))
        wf = float(np.clip((2.45 - tm) / 0.25, 0, 1)) * ramp
        out.append(tube(tip, m, 1.1, 1.1, alpha=1.0 * wf, lift=lift, push_z=push, style=0, segments=70))
        return out

    # the Anim beam API takes one callable per beam; wrap the two straw layers
    beams = [lambda tm: (straw_beams(tm) or [None])[0], lambda tm: (straw_beams(tm) + [None, None])[1]]
    water = WaterRegion((CX - R - 2, CZ - R - 2, CX + R + 2, CZ + R + 2), 55, 65, center=(TIP[0], TIP[2]))
    return Anim([g], water=water, water_level=lambda t: float(level(t)), funnel=funnel, beams=beams)


def lerp_point_fn(a, b, e=smooth):
    a, b = np.array(a, float), np.array(b, float)

    def f(tau):
        tau = np.asarray(tau, float)
        return a[None] + (b - a)[None] * e(tau)[:, None]
    return f


def build_rig(subframes=8):
    rig = Rig(fps=FPS, subframes=subframes, shutter=0.5)
    rig.add(track([(15.0, 68.6, 718.0), (7.0, 69.4, 716.5), (-6.0, 71.0, 711.0)], lerp_point_fn((2.0, 72.0, 700.0), (1.0, 84.0, 690.0)), A,
                  ease="launch_soft", fov=(60, 68), name="surface").with_roll((4, -3)).with_handheld("subtle", fade=0.2))
    lp = rig.last_pose()
    rig.add(track([(lp["x"], lp["y"], lp["z"]), (22.0, 90.0, 760.0), (34.0, 100.0, 790.0)],
                  lerp_point_fn((1.0, 84.0, 690.0), (0.0, 94.0, 682.0)), B, ease="soft_in_out", fov=(68, 58), name="reveal")
            .with_roll((-3, 2)).with_handheld("subtle", fade=0.2))
    lp = rig.last_pose()
    rig.add(track([(lp["x"], lp["y"], lp["z"]), (14.0, 118.0, 740.0), (3.0, 134.0, 693.0)],
                  lerp_point_fn((0.0, 94.0, 682.0), (0.0, 128.0, 653.0)), C, ease="out", fov=(58, 52), name="face_push")
            .with_roll((2, -4)).with_handheld("breath", fade=0.2))
    return rig


SCENE = Scene(weather="clear", anchor=(CX, 95, CZ), commands=world_commands(), dimension="minecraft:the_end", settleTicks=300)
WORLD = World(seed=4242)


def settings(frozen=False):
    return Settings(renderDistance=12, simulationDistance=6, worldTicks=not frozen, gamma=1.0, clouds=False, particles=False)
