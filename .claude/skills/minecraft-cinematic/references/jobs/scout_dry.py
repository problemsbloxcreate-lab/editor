from peixe import *
from cinecam.terrain import Terrain
r = scout("peixe_scout", world=WORLD, anchor=(3048, 70, -350), commands=DRY,
          maps=[{"name": "p", "x0": 3036, "z0": -372, "x1": 3066, "z1": -340, "step": 1}])
t = Terrain.load(r["maps"]["p"])
import json
d = json.load(open(r["maps"]["p"]))
w = d["w"]
for z in range(-356, -342):
    row = []
    for x in range(3040, 3056):
        i = (z - d["z0"]) * w + (x - d["x0"])
        row.append(f'{d["surface"][i]}:{d["ground"][i]}')
    print(z, " ".join(row))
print(r["report"].get("warnings"))
