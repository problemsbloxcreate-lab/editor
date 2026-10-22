"""Take de 2 s p/ 01;26;17–01;28;17: poça totalmente seca, um peixinho se debatendo sem água nenhuma."""
from common import *
from pathlib import Path
import json

FPS, T = 60, 2.0
MODE = sys.argv[1] if len(sys.argv) > 1 else "draft"     # stills | draft | final
SUB = {"draft": 2, "final": 8}.get(MODE, 1)

FLOOR = 62.0                                  # top of the pit's sand bottom (first free y)
FISH = np.array([3047.5, FLOOR, -349.4])

# the same desert set, but every pond is drained: an organic dry pond bed (1-deep shelf + 2-deep middle), zero water anywhere
PC = (3047.5, -349.5)


def pond_cmds():
    """Row-by-row fills of a wobbly elliptical pond: shelf (y63 air) and a deeper middle (y62 air too)."""
    cmds = []
    for z in range(-357, -341):
        for layer, k in ((63, 1.0), (62, 0.62)):
            xs = []
            for x in range(3038, 3058):
                dx, dz = (x + 0.5 - PC[0]) / 7.0, (z + 0.5 - PC[1]) / 4.8
                wob = 0.13 * math.sin(2.1 * x + 0.7 * z) + 0.09 * math.sin(1.3 * z - 0.9 * x)
                if dx * dx + dz * dz < (k + wob) ** 2:
                    xs.append(x)
            if xs:
                cmds.append(f"fill {min(xs)} {layer} {z} {max(xs)} {layer} {z} minecraft:air")
    return cmds


DRY = [c for c in SET if "water" not in c] + pond_cmds() + [
    f"fill {POND[0]} 62 {POND[1]} {POND[2]} 63 {POND[3]} minecraft:air",   # the ponds of the belly takes, also dry
    "fill 3057 62 -357 3060 63 -350 minecraft:air",
    "setblock 3042 63 -351 minecraft:dead_horn_coral[waterlogged=false]", "setblock 3052 63 -347 minecraft:dead_bubble_coral[waterlogged=false]",
    "setblock 3050 62 -352 minecraft:dead_brain_coral[waterlogged=false]", "setblock 3043 63 -347 minecraft:dead_bush",
    "setblock 3056 62 -355 minecraft:dead_bush",
    "fill 3030 58 -380 3070 66 -356 minecraft:air replace minecraft:water",   # 2 halves, <32768 blocks each
    "fill 3030 58 -355 3070 66 -330 minecraft:air replace minecraft:water",
    "gamerule doMobSpawning false", "kill @e[type=!player]",                   # no stray rabbits/items in the wide shot
]
SCENE_DRY = Scene(time=5000, weather="clear", anchor=(3048, 70, -350), commands=DRY)

HOPS = [(0.06, 0.30, 0.34, 180, 25), (0.50, 0.22, 0.30, -180, -40), (0.92, 0.36, 0.36, 180, 30),
        (1.40, 0.18, 0.28, -180, -20), (1.76, 0.12, 0.22, 0, 15)]    # (start, height, duration, roll turn, yaw turn)


def fish_fn(times):
    t = np.asarray(times, float)
    out = np.zeros((len(t), 12))
    y = np.zeros_like(t); roll = np.zeros_like(t); yaw = np.full_like(t, 35.0); sq = np.ones_like(t)   # roll 0 = on its side (vanilla cod renderer out of water)
    x = np.full_like(t, FISH[0]); z = np.full_like(t, FISH[2])
    r0, w0 = 0.0, 35.0
    for (t0, h, d, dr, dw) in HOPS:
        u = np.clip((t - t0) / d, 0, 1)
        air = (t >= t0) & (t <= t0 + d)
        y += np.where(air, 4 * h * u * (1 - u), 0.0)                 # ballistic arc
        e = u * u * (3 - 2 * u)
        roll += np.where(t >= t0, dr * e, 0.0)                         # flips onto the other side in the air
        yaw += np.where(t >= t0, dw * e, 0.0)
        land = t - (t0 + d)
        sq *= np.where((land > 0) & (land < 0.16), 1 - 0.35 * np.sin(np.pi * np.clip(land / 0.16, 0, 1)), 1.0)  # splat on landing
        x += np.where(t >= t0, 0.07 * np.sign(dw) * e, 0.0)           # drifts a little each flop
    out[:, 0] = x; out[:, 1] = FLOOR + 0.13 + y; out[:, 2] = z
    out[:, 3] = yaw; out[:, 5] = roll
    out[:, 6] = 1.0 + 0.5 * (1 - sq); out[:, 7] = sq; out[:, 8] = 1.0 + 0.5 * (1 - sq)
    out[:, 9] = FLOOR
    out[:, 11] = 1.0 + 70.0 * t                                        # tail flaps ~3.5x faster than vanilla: desperate
    return out


def build():
    fish = Mob("peixe", "minecraft:cod", FISH, fn=fish_fn)
    anim = Anim([], mobs=[fish])
    rig = Rig(fps=FPS, subframes=SUB, shutter=0.5)
    f = FISH + [0, 0.15, 0]
    # WIDE (feedback 20/10: "plano mais aberto, a poça toda seca e o peixe pequeno dentro"): high on the rim, slow drift
    p0 = f + np.array([4.6, 3.5, 6.4])
    p1 = f + np.array([3.1, 3.3, 6.1])
    aim = lerp_point(f + [0.3, 0.1, -1.4], f + [0.0, 0.1, -1.5], "smooth")
    rig.add(track([p0, p1], aim, T, ease="smooth", fov=(60, 57), name="dry_pond_wide")
            .with_handheld("subtle", fade=0.1))
    return rig, anim


if __name__ == "__main__":
    rig, anim = build()
    if MODE == "stills":
        rows = rig.sample_rows()
        idx = [0, len(rows["t"]) // 2, len(rows["t"]) - 1]
        poses = [dict(x=rows["x"][i], y=rows["y"][i], z=rows["z"][i], yaw=rows["yaw"][i], pitch=rows["pitch"][i],
                      roll=rows["roll"][i], fov=rows["fov"][i], t=float(rows["t"][i])) for i in idx]
        poses.append(dict(x=FISH[0] + 0.0, y=FLOOR + 0.5, z=FISH[2] + 1.1, yaw=180, pitch=20, fov=50, t=0.4))
        print(stills(poses, "peixe_st", scene=SCENE_DRY, world=WORLD, settings=settings(True), size=(960, 540), anim=anim))
    else:
        name = "peixe_seco" + ("_draft" if MODE == "draft" else "")
        out = Path("D:/cinecam-out") / name; out.mkdir(parents=True, exist_ok=True)
        print(plot_rig(rig, str(out / "path.png")))
        info = render(rig, name, scene=SCENE_DRY, world=WORLD, settings=settings(False), anim=anim,
                      size=(960, 540) if MODE == "draft" else (1920, 1080), grade="clean", dof=MODE == "final")
        print(json.dumps({k: v for k, v in info.items() if k != "report"}, indent=1))
        print(info.get("report", {}).get("warnings"), info.get("report", {}).get("maxWait"))
