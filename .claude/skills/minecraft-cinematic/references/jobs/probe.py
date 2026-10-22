from peixe import *
cmds = DRY + ["execute if block 3047 62 -349 minecraft:water run say W62", "execute if block 3047 63 -349 minecraft:water run say W63",
              "execute if block 3047 62 -349 minecraft:air run say A62", "execute if block 3047 61 -349 minecraft:sand run say S61",
              "execute if block 3047 61 -349 minecraft:water run say W61"]
sc = Scene(time=5000, weather="clear", anchor=(3048, 70, -350), commands=cmds)
print(stills([dict(x=3047.5, y=64.5, z=-346.5, yaw=180, pitch=35, fov=60, t=0)], "peixe_probe", scene=sc, world=WORLD, settings=settings(True), size=(640, 360)))
