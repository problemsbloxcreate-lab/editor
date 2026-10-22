"""Builds references/sites_4242.json: one flat, dry, single-biome patch per biome in the seed-4242 world (the CineCam "studio").

Run once (already done 21/10/2026; seed 4242 terrain is identical on any machine with Minecraft 1.20.1):
    python sites_build.py <queries.json from a scout with 'locate biome ...'>   [--r 14]
Stage 1 (locate) = scout(queries=[...]); stage 2 (this script) = scout maps (generate=True) around each biome point and pick,
per biome, the patch of radius r with the lowest ground-height spread, no water and >= 85 % of that biome.
"""
import json, math, re, sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cinecam import scout, World, Settings, Terrain

OUT = Path(__file__).resolve().parents[1] / "references" / "sites_4242.json"
SKIP = {"lush_caves", "dripstone_caves", "deep_dark", "ocean", "deep_ocean", "frozen_ocean", "river", "grove"}
# hand-picked, proven in real takes: the desert of "Bebi toda a água do mundo" and the ocean island of the takes futuros
KNOWN = {"desert": {"x": 3050, "y": 63, "z": -356, "flat_r": 16, "note": "deserto dos takes do vídeo da água (20/10)"},
         "ocean_island": {"x": 810, "y": 64, "z": -194, "flat_r": 6, "note": "ilha no oceano frio (takes futuros 16/10): fill sandstone 44..64 + sand"},
         "end_void": {"x": 0, "y": 64, "z": 700, "flat_r": 0, "dimension": "minecraft:the_end", "note": "vazio do End = 'universo' (universo_canudo)"}}


def main():
    q = json.load(open(sys.argv[1], encoding="utf-8"))
    r = int(sys.argv[sys.argv.index("--r") + 1]) if "--r" in sys.argv else 14
    pts = {}
    for k, v in q.items():
        m = re.match(r"locate biome minecraft:(\w+)", k)
        if not m or m.group(1) in SKIP or m.group(1) in KNOWN:
            continue
        c = re.search(r"\[(-?\d+), [~\d-]+, (-?\d+)\]", " ".join(v))
        if c:
            pts[m.group(1)] = (int(c.group(1)), int(c.group(2)))
    maps = [{"name": b, "x0": x - 64, "z0": z - 64, "x1": x + 64, "z1": z + 64, "step": 2, "generate": True} for b, (x, z) in pts.items()]
    if "--reuse" in sys.argv:                                   # maps already scouted: only redo the choice
        import glob
        from cinecam.render import OUT_HOME
        res = {"maps": {Path(p).stem.split("_scout_")[1]: p for p in glob.glob(str(OUT_HOME / "sites4242_maps" / "*_scout_*.json"))}}
    else:
      res = scout("sites4242_maps", world=World(seed=4242), anchor=(3000, 80, -350), maps=maps,
                  settings=Settings(renderDistance=4, simulationDistance=4), timeout_s=3600)
    sites = dict(KNOWN)
    for b, path in res["maps"].items():
        t = Terrain.load(path)
        want = [i for i, n in enumerate(t.biomes) if n == "minecraft:" + b]
        if not want:
            continue
        rr = max(1, r // t.step)
        best = None
        water = (t.ground - t.floor) > 0                          # water column above the floor (surface also counts leaves)
        for iz in range(rr, t.h - rr, 2):
            for ix in range(rr, t.w - rr, 2):
                sl = (slice(iz - rr, iz + rr + 1), slice(ix - rr, ix + rr + 1))
                g = t.ground[sl]
                frac = np.isin(t.biome[sl], want).mean()
                if frac < 0.85 or water[sl].any():
                    continue
                score = float(np.std(g)) + 0.15 * float(g.max() - g.min())
                if best is None or score < best[0]:
                    best = (score, iz, ix, int(np.median(g)) - 1, frac)
        if best:
            s, iz, ix, y, frac = best
            sites[b] = {"x": int(t.x0 + ix * t.step), "y": y, "z": int(t.z0 + iz * t.step), "flat_r": r,
                        "spread": round(s, 2), "biome_frac": round(float(frac), 2)}
    OUT.write_text(json.dumps(sites, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(sites, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
