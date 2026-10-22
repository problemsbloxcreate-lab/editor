from peixe import *
mobs = []
for i, r in enumerate([0, 90, 180]):
    m = Mob(f"f{i}", "minecraft:cod", (FISH[0] - 0.8 + 0.8 * i, FLOOR + 0.13, FISH[2]))
    m.key(0, yaw=35, roll=r, shadow_y=FLOOR, age=1)
    mobs.append(m)
anim = Anim([], mobs=mobs)
print(stills([dict(x=FISH[0] + 0.3, y=FLOOR + 0.9, z=FISH[2] + 1.6, yaw=180, pitch=28, fov=50, t=0)], "fishcal", scene=SCENE_DRY, world=WORLD, settings=settings(True), size=(960, 540), anim=anim))
