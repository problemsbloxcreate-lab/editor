"""Dois closes de 3 s da barriga cheia d'água (voxel belly v0.7): A = Patão bebendo de canudinho, B = Problems dando tapinhas."""
from common import *

FPS, T = 60, 3.0
SUB = 2 if (len(sys.argv) > 2 and sys.argv[2] == "draft") else 8
from pathlib import Path


def pulse_keys(a, times, r0, step, out_extra=2.0):
    """Each gulp: the ball swells a notch (out_back) and the water inside sloshes (squash + ripple)."""
    R = r0
    a.key(0.0, vbelly=R, vbelly_out=R - out_extra, vbelly_jig=0.0, vbelly_wave=0.2)
    for tg in times:
        a.key(tg, vbelly=R, vbelly_out=R - out_extra, vbelly_jig=0.0, vbelly_wave=0.2)
        R += step
        a.key(tg + 0.10, ease="out", vbelly=R + 0.25, vbelly_out=R + 0.25 - out_extra, vbelly_jig=-0.10, vbelly_wave=0.5)
        a.key(tg + 0.30, ease="out_back", vbelly=R, vbelly_out=R - out_extra, vbelly_jig=0.0, vbelly_wave=0.25)
        a.wobble("vbelly_jig", tg + 0.10, tg + 0.75, 0.06, 6.5, decay=5.0)
    return R


# ---------------------------------------------------------------- A: Patão
def take_a():
    R0, STEP = 5.3, 0.22
    gulps = [0.15, 0.70, 1.25, 1.80, 2.35]
    pat = Actor("patao", PAT, PAT_POS, yaw=0)
    pat.key(0, head_x=-22, rarm_z=14, larm_z=-14, rarm_x=-8, larm_x=-8, vbelly_y=7.2, vbelly_shine=0.85)
    for tg in gulps:                                  # head nods back a hair on every gulp
        pat.key(tg, head_x=-22).key(tg + 0.12, ease="out", head_x=-28).key(tg + 0.38, head_x=-22)
    Rend = pulse_keys(pat, gulps, R0, STEP)
    pat.wobble("lean", 0.0, T, 1.2, 1.1)
    bp = belly_center(PAT_POS, Rend, Rend - 2.0, 7.2)

    tip = np.array([3053.4, 63.82, -357.8])
    def straw(tm):
        m = mouth_position(pat, tm)
        return tube(tip, m, 0.055, 0.05, 0.6, lift=0.9, push_z=0.0, style=1)
    def water(tm):
        m = mouth_position(pat, tm)
        flow = 0.75 + 0.25 * max(math.sin((tm - 0.1) * 2 * math.pi / 0.55), 0)
        return tube(tip + [0, 0.02, 0], m, 0.036 * flow, 0.03 * flow, 0.95, lift=0.9, push_z=0.0, style=0)
    anim = Anim([pat], beams=[straw, water])

    rig = Rig(fps=FPS, subframes=SUB, shutter=0.5)
    p0 = bp + np.array([1.30, -0.05, 1.30])
    p1 = bp + np.array([0.80, 0.08, 1.38])
    p2 = bp + np.array([0.30, 0.18, 1.30])
    aim = lerp_point(bp + [0.0, 0.26, 0.0], bp + [0.0, 0.07, 0.0], "smooth")
    rig.add(track([p0, p1, p2], aim, T, ease="launch_soft", fov=(52, 44), name="patao_orbit_push")
            .with_roll((-4, 1.5)).with_handheld("subtle", fade=0.15)
            .with_dof(tuple(bp + [0, 0, 0.30]), aperture=0.45))
    return rig, anim, bp


# ---------------------------------------------------------------- B: Problems
def take_b():
    R = 6.1
    hops = [0.70, 1.62]
    pro = Actor("problems", PRO, PAT_POS, yaw=0)      # same spot as Patão (rendered alone) -> same pond/background
    pro.key(0, head_x=14, rarm_z=24, larm_z=-24, rarm_x=-4, larm_x=-4, vbelly=R, vbelly_out=R - 2.0, vbelly_y=7.0,
            vbelly_wave=0.15, vbelly_jig=0.0, vbelly_shine=0.85, hop=0.0)
    pro.wobble("vbelly_jig", 0.0, 0.7, 0.025, 2.2)
    for th in hops:                                   # crouch, little hop, land: the water ball squashes and sloshes
        pro.key(th - 0.16, hop=0.0, vbelly_jig=0.0, vbelly_wave=0.15, rarm_z=24, larm_z=-24)
        pro.key(th - 0.04, ease="out", vbelly_jig=-0.07)
        pro.key(th + 0.12, ease="out", hop=0.2, vbelly_jig=0.12, rarm_z=40, larm_z=-40)
        pro.key(th + 0.26, ease="in", hop=0.0, vbelly_jig=0.05)
        pro.key(th + 0.33, ease="out", vbelly_jig=-0.2, vbelly_wave=0.6, rarm_z=20, larm_z=-20)
        pro.key(th + 0.48, ease="out_back", vbelly_jig=0.07, vbelly_wave=0.35)
        pro.key(th + 0.85, vbelly_jig=0.0, vbelly_wave=0.15, rarm_z=24, larm_z=-24)
        pro.wobble("vbelly_jig", th + 0.48, th + 1.1, 0.06, 7.0, decay=4.5)
        pro.key(th + 0.26, head_x=14).key(th + 0.36, ease="out", head_x=24).key(th + 0.6, head_x=14)
    pro.key(2.35, head_x=14).key(2.7, ease="out_back", head_x=-8)   # looks up at the lens, proud
    bp = belly_center(PAT_POS, R, R - 2.0, 7.0)
    anim = Anim([pro])

    rig = Rig(fps=FPS, subframes=SUB, shutter=0.5)
    p0 = bp + np.array([1.05, 0.52, 1.20])
    p1 = bp + np.array([0.60, 0.46, 1.42])
    p2 = bp + np.array([0.18, 0.40, 1.50])
    aim = lerp_point(bp + [0.0, 0.14, 0.0], bp + [0.0, 0.18, 0.0], "smooth")
    rig.add(track([p0, p1, p2], aim, T, ease="launch_soft", fov=(48, 45), name="problems_truck")
            .with_roll((-3, 1)).with_handheld("subtle", fade=0.15)
            .with_dof(tuple(bp + [0, 0.1, 0.32]), aperture=0.45))
    return rig, anim, bp


if __name__ == "__main__":
    import json
    which = sys.argv[1]
    draft = len(sys.argv) > 2 and sys.argv[2] == "draft"
    rig, anim, bp = (take_a if which == "a" else take_b)()
    name = f"barriga_{which}" + ("_draft" if draft else "")
    out = Path(r"D:/cinecam-out") / name
    out.mkdir(parents=True, exist_ok=True)
    print(plot_rig(rig, str(out / "path.png")))
    info = render(rig, name, scene=SCENE, world=WORLD, settings=settings(False), anim=anim,
                  size=(960, 540) if draft else (1920, 1080), grade="clean", dof=not draft, supersample=1)
    print(json.dumps({k: v for k, v in info.items() if k != "report"}, indent=1))
    print(json.dumps(info.get("report", {}).get("warnings"), indent=1), info.get("report", {}).get("maxWait"))
