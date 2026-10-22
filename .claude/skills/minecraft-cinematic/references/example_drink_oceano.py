"""Problems / Stick / Patão bebendo todo o oceano — takes futuros (4.017 s @60)."""
import sys, math; sys.path.insert(0, r"C:\Users\mathe\.claude\skills\minecraft-cinematic\scripts")
import numpy as np
from cinecam import *
from cinecam.camlib import Move

SK = r"C:/Users/mathe/AppData/Roaming/ModrinthApp/profiles/Construir Pirâmide/config/bbs/assets/models/skins/0.Turma/"
PAT, PRO, STI = SK+"ajudantes/cariocapato.png", SK+"Problems0.png", SK+"O_Stick.png"
Y, Z = 65.0, -194.0
XS, XP, XT = 807.0, 810.0, 813.0            # Stick, Problems, Patão
SEA, DRY = 62.9, 22.0                       # water surface -> everything gone
T_DRINK0, T_DRINK1 = 1.45, 3.35
FPS = 60
A, B, C, D = 87/FPS, 54/FPS, 51/FPS, 49/FPS
TOTAL = A + B + C + D
FLOOR = 49.0

ISLAND = ["fill 805 44 -197 815 64 -191 minecraft:sandstone", "fill 805 64 -197 815 64 -191 minecraft:sand"]

def level(t):
    t = np.asarray(t, float)
    u = np.clip((t - T_DRINK0) / (3.0 - T_DRINK0), 0, 1); s1 = u * u * (3 - 2 * u)
    v = np.clip((t - 3.0) / (T_DRINK1 - 3.0), 0, 1)
    return np.where(t < 3.0, SEA + (FLOOR - SEA) * s1, FLOOR + (DRY - FLOOR) * v)
def prog(t):                         # 0..1 how much water has been swallowed (belly/lean driver)
    return np.clip((SEA - level(t)) / (SEA - FLOOR), 0, 1)

def build_actors():
    stick = Actor("stick", STI, (XS, Y, Z)); prob = Actor("problems", PRO, (XP, Y, Z)); pat = Actor("patao", PAT, (XT, Y, Z))
    for a in (stick, prob, pat):
        a.key(0, head=1.0)
    # --- intro: each one gets a hero moment while the camera passes
    stick.key(0.0, rarm_z=-150, head_z=8, lean=-4).key(0.55, rarm_z=-150, head_z=-8).key(0.9, rarm_z=-10, head_z=0, lean=0)
    stick.wobble("rarm_z", 0.0, 0.75, 22, 3.2)
    stick.key(0.1, ease="hold", hop=0.0).key(0.25, hop=0.18).key(0.4, hop=0.0)
    prob.key(0.0, rarm_z=-8, larm_z=8).key(0.55, rarm_z=-8, larm_z=8, head_x=0).key(0.85, ease="out_back", rarm_z=-35, larm_z=35, head_x=-12, lean=-6, hop=0.0)
    prob.key(1.0, hop=0.28).key(1.15, hop=0.0).key(1.3, rarm_z=-8, larm_z=8, head_x=0, lean=0)
    pat.key(0.0, yaw=-28, rarm_z=-8, larm_z=8).key(0.8, yaw=-28, rarm_z=-8, larm_z=8).key(1.05, ease="out_back", yaw=0, rarm_z=-150, larm_z=150, hop=0.0)
    pat.key(1.2, hop=0.3).key(1.38, hop=0.0).key(1.45, rarm_z=-14, larm_z=14)
    # --- drinking: head back, lean back, belly follows the water that disappears
    k = {"stick": (stick, 2.9), "problems": (prob, 2.7), "patao": (pat, 3.7)}
    for name, (a, bmax) in k.items():
        a.key(T_DRINK0, head_x=0, lean=0)
        a.key(T_DRINK0 + 0.25, ease="out_back", head_x=-48, lean=10, rarm_x=-25, larm_x=-25, rarm_z=-14, larm_z=14)
        ts = np.arange(T_DRINK0, T_DRINK1 + 1e-6, 0.05)
        for t in ts:
            p = float(prog(t))
            a.key(float(t), ease="linear", belly=1 + (bmax - 1) * p, belly_y=1 + 0.30 * p, lean=10 + 9 * p, head=1 + 0.12 * p)
        a.wobble("belly", T_DRINK0 + 0.2, T_DRINK1, 0.06 * (bmax - 1), 7.5, 0.0)
        a.wobble("head_x", T_DRINK0 + 0.25, T_DRINK1, 3.0, 11.0)
    pat.wobble("roll", T_DRINK0 + 0.3, T_DRINK1, 3.0, 5.0, 0.0, 1.0)
    # --- burp / finale
    for i, (name, (a, bmax)) in enumerate(k.items()):
        d = 0.07 * i
        a.key(T_DRINK1 + d, ease="linear", lean=19, head_x=-48)
        a.key(T_DRINK1 + 0.18 + d, ease="out_back", lean=-6, head_x=14, hop=0.0, belly_y=1.3)
        a.key(T_DRINK1 + 0.34 + d, hop=0.45, belly_y=1.0)
        a.key(T_DRINK1 + 0.55 + d, ease="in", hop=0.0, belly_y=0.85)
        a.key(T_DRINK1 + 0.68 + d, ease="out_back", belly_y=1.3)
    pat.key(T_DRINK1 + 0.3, roll=0).key(T_DRINK1 + 0.62, ease="out_back", roll=-18)
    return stick, prob, pat

def build_anim():
    s, p, t = build_actors()
    mouths = []
    def beam_for(a, off_x):
        def f(tm):
            if tm < T_DRINK0 + 0.12 or tm > T_DRINK1 + 0.12: return None
            ramp = float(np.clip((tm - T_DRINK0 - 0.12) / 0.25, 0, 1) * np.clip((T_DRINK1 + 0.12 - tm) / 0.22, 0, 1))
            m = mouth_position(a, tm)
            lv = float(level(tm))
            sx = float(a.at(np.array([0.0]))[0][0]) + off_x
            r1 = 0.40 * ramp; r2 = 0.14 * ramp
            return [sx, lv + 0.2, Z - 17.0, m[0], m[1], m[2], r1, r2, ramp, 8.0, 9.0]
        return f
    beams = [beam_for(s, -4.0), beam_for(p, 0.0), beam_for(t, 4.0)]
    water = WaterRegion((690, -314, 930, -74), 22, 62)
    return Anim([s, p, t], water=water, water_level=lambda tm: float(level(tm)), beams=beams)

def aim_a(tau):
    tau = np.asarray(tau, float)
    pts = np.array([[XS, 66.2, Z], [XP, 66.4, Z], [XT, 66.4, Z]])
    u = np.clip(tau, 0, 1) * 2.0
    i = np.clip(np.floor(u).astype(int), 0, 1)
    f = u - i; f = f * f * (3 - 2 * f)
    return pts[i] * (1 - f)[:, None] + pts[i + 1] * f[:, None]

def build_rig(subframes=8):
    rig = Rig(fps=FPS, subframes=subframes, shutter=0.5)
    rig.add(track([(805.4, 65.8, -189.4), (809.4, 66.0, -189.0), (814.6, 66.2, -189.4)], aim_a, A, ease="launch_soft", fov=(54, 58), name="intro_truck")
            .with_handheld("subtle", fade=0.2))
    lp = rig.last_pose()
    rig.add(track([(lp["x"], lp["y"], lp["z"]), (812.0, 65.8, -189.3), (810.0, 65.9, -188.9)],
                  lerp_point_fn((XT, 66.4, Z), (810.0, 67.2, Z)), B, ease="in_out", fov=(58, 64), name="chug_low")
            .with_roll((0, 4)).with_handheld("subtle", fade=0.2))
    lp = rig.last_pose()
    rig.add(track([(lp["x"], lp["y"], lp["z"]), (810.0, 70.5, -181.0), (810.0, 76.0, -171.0)],
                  lerp_point_fn((810.0, 67.2, Z), (810.0, 61.0, Z - 6)), C, ease="soft_in_out", fov=(64, 82), name="reveal_dry")
            .with_roll((4, -3)).with_handheld("subtle", fade=0.2))
    lp = rig.last_pose()
    rig.add(track([(lp["x"], lp["y"], lp["z"]), (810.2, 66.5, -187.2)],
                  lerp_point_fn((810.0, 61.0, Z - 6), (810.0, 66.3, Z)), D, ease="out", fov=(82, 60), name="belly_shot")
            .with_roll((-3, 3)).with_handheld("breath", fade=0.2))
    return rig

def lerp_point_fn(a, b):
    a, b = np.array(a), np.array(b)
    def f(tau):
        tau = np.asarray(tau, float); e = tau * tau * (3 - 2 * tau)
        return a[None] + (b - a)[None] * e[:, None]
    return f

SCENE = Scene(time=3000, weather="clear", anchor=(810, 80, Z), commands=ISLAND)
WORLD = World(seed=4242)
def settings(frozen=False): return Settings(renderDistance=12, simulationDistance=6, worldTicks=not frozen)
