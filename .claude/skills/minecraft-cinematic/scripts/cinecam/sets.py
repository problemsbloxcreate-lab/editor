"""sets: rebuild the PLACE of a gameplay moment inside the CineCam world, so a cutaway feels like it happens right there.

    from cinecam.sets import SetBuilder, site
    sb = SetBuilder(site("desert"), r=18)                 # flat patch of the catalogued desert (seed 4242), ground top y known
    sb.kit("desert")                                      # sand floor on sandstone, dead bushes, cacti (as in the video)
    sb.pond(5, -3, 4.5, 3, plants="sugar_cane")           # pond with sugar cane on the rim, like the gameplay's ponds
    sb.mob("camel", -9, -14, yaw=30)                      # still mob in the background (NoAI)
    sb.template("minecraft:village/desert/houses/desert_small_house_1", -14, -10)
    scene = sb.scene(time=5000)                           # Scene(anchor, commands, time, weather)
    feet = sb.feet(0, 0)                                  # where an Actor stands (x+.5, top+1, z+.5)

Local coordinates (dx, dz) are blocks from the site centre; +z = south = the side the default cameras look from.
Every command is plain vanilla (fill/setblock/place/summon) run by the mod as op before the film; fills are split
under 32768 blocks.  Sand/gravel always sit on a solid sub-layer (sand over a cave falls and leaves holes).
Sites come from references/sites_4242.json (built once by scripts/sites_build.py; seed 4242 terrain is the same on
any machine with Minecraft 1.20.1).
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple, Union

import numpy as np

from .render import Scene

_SITES = Path(__file__).resolve().parents[2] / "references" / "sites_4242.json"

# biome -> (top block, sub block, scatter [(block, n)], trees [(feature, n)])
KITS: Dict[str, dict] = {
    "desert": dict(top="sand", sub="sandstone", scatter=[("dead_bush", 7), ("cactus*2", 3)], trees=[], soften=False),
    "beach": dict(top="sand", sub="sandstone", scatter=[("dead_bush", 1)], trees=[], soften=False),
    "badlands": dict(top="red_sand", sub="terracotta", scatter=[("dead_bush", 6), ("cactus*3", 2)], trees=[], soften=False),
    "plains": dict(top="grass_block", sub="dirt", scatter=[("grass", 70), ("dandelion", 6), ("poppy", 5), ("oxeye_daisy", 3)], trees=[("oak", 2)]),
    "sunflower_plains": dict(top="grass_block", sub="dirt", scatter=[("grass", 60), ("sunflower*2", 6)], trees=[]),
    "meadow": dict(top="grass_block", sub="dirt", scatter=[("grass", 80), ("cornflower", 8), ("allium", 5), ("dandelion", 6)], trees=[]),
    "forest": dict(top="grass_block", sub="dirt", scatter=[("grass", 50), ("fern", 10)], trees=[("oak", 7), ("birch", 3)]),
    "flower_forest": dict(top="grass_block", sub="dirt", scatter=[("grass", 30), ("poppy", 10), ("allium", 8), ("azure_bluet", 8), ("tulip", 8)], trees=[("oak", 5)]),
    "birch_forest": dict(top="grass_block", sub="dirt", scatter=[("grass", 50)], trees=[("birch", 9)]),
    "dark_forest": dict(top="grass_block", sub="dirt", scatter=[("grass", 30), ("red_mushroom", 4), ("brown_mushroom", 4)], trees=[("dark_oak", 6)]),
    "taiga": dict(top="grass_block", sub="dirt", scatter=[("fern", 30), ("sweet_berry_bush", 4)], trees=[("spruce", 8)]),
    "snowy_plains": dict(top="snow_block", sub="dirt", scatter=[("snow", 40)], trees=[("spruce", 1)]),
    "snowy_taiga": dict(top="snow_block", sub="dirt", scatter=[("snow", 40)], trees=[("spruce", 7)]),
    "jungle": dict(top="grass_block", sub="dirt", scatter=[("grass", 40), ("fern", 20), ("melon", 2)], trees=[("jungle_tree", 5), ("jungle_bush", 6)]),
    "savanna": dict(top="grass_block", sub="dirt", scatter=[("grass", 60), ("tall_grass*2", 8)], trees=[("acacia", 3)]),
    "swamp": dict(top="grass_block", sub="dirt", scatter=[("grass", 30), ("blue_orchid", 6), ("lily_pad@water", 6)], trees=[("swamp_oak", 3)]),
    "cherry_grove": dict(top="grass_block", sub="dirt", scatter=[("grass", 40), ("pink_petals", 20)], trees=[("cherry", 5)]),
    "mushroom_fields": dict(top="mycelium", sub="dirt", scatter=[("red_mushroom", 6), ("brown_mushroom", 6)], trees=[("huge_red_mushroom", 2), ("huge_brown_mushroom", 1)]),
    "stone": dict(top="stone", sub="stone", scatter=[("cobblestone", 8), ("andesite", 8)], trees=[]),
    "nether": dict(top="netherrack", sub="netherrack", scatter=[("nether_wart_block", 6), ("magma_block", 4), ("fire", 4)], trees=[]),
}


def sites() -> Dict[str, dict]:
    if _SITES.exists():
        return json.loads(_SITES.read_text(encoding="utf-8"))
    return {}


def site(biome: str) -> dict:
    """Catalogued flat site for a biome: {'x','y','z','biome','flat_r'} (y = top ground block).  Falls back to the closest kind."""
    S = sites()
    if biome in S:
        return dict(S[biome], biome=biome)
    aliases = {"snow": "snowy_plains", "snowy": "snowy_plains", "grass": "plains", "field": "plains", "sand": "desert",
               "ocean": "ocean_island", "sea": "ocean_island", "woods": "forest", "red_desert": "badlands", "mesa": "badlands",
               "taiga": "snowy_taiga", "dark_forest": "forest", "cherry_grove": "meadow", "swamp": "plains", "mangrove_swamp": "plains",
               "mushroom_fields": "plains", "beach": "desert", "warm_ocean": "ocean_island", "universe": "end_void", "space": "end_void",
               "village": "plains", "cave": "stony_shore", "mountain": "windswept_hills"}
    b = aliases.get(biome)
    if b and b in S:
        return dict(S[b], biome=b)
    if "desert" in S:
        return dict(S["desert"], biome="desert")
    raise KeyError(f"no catalogued site for '{biome}'; run scripts/sites_build.py or pass an explicit (x, y, z)")


def _fill_chunks(x0, y0, z0, x1, y1, z1, block, extra="") -> List[str]:
    """fill split along z so every command is < 32768 blocks (larger ones fail silently with '-> 0')."""
    x0, x1 = sorted((x0, x1)); y0, y1 = sorted((y0, y1)); z0, z1 = sorted((z0, z1))
    per = max(1, 32000 // ((x1 - x0 + 1) * (y1 - y0 + 1)))
    out, z = [], z0
    while z <= z1:
        ze = min(z1, z + per - 1)
        out.append(f"fill {x0} {y0} {z} {x1} {y1} {ze} minecraft:{block}{(' ' + extra) if extra else ''}")
        z = ze + 1
    return out


class SetBuilder:
    def __init__(self, where: Union[dict, Sequence[float]], r: int = 18, seed: int = 7):
        if isinstance(where, dict):
            self.x, self.gy, self.z = int(where["x"]), int(where["y"]), int(where["z"])
            self.biome = where.get("biome", "desert")
            self.dimension = where.get("dimension", "minecraft:overworld")
        else:
            self.x, self.gy, self.z = int(where[0]), int(where[1]), int(where[2])
            self.biome = "custom"
            self.dimension = "minecraft:overworld"
        self.r = int(r)
        self.rng = np.random.default_rng(seed)
        self.cmds: List[str] = ["gamerule doMobSpawning false", "kill @e[type=!player]"]
        self.marks: Dict[str, np.ndarray] = {}
        self.water_cells: set = set()
        self.occupied: set = set()          # (dx, dz) kept free of scatter (actors, ponds, paths)

    # ---- coordinates
    def w(self, dx: float, dz: float) -> Tuple[int, int]:
        return self.x + int(math.floor(dx)), self.z + int(math.floor(dz))

    def feet(self, dx: float = 0.0, dz: float = 0.0, dy: float = 0.0) -> np.ndarray:
        """World position where an actor's feet stand on the set floor at (dx, dz)."""
        return np.array([self.x + math.floor(dx) + 0.5, self.gy + 1.0 + dy, self.z + math.floor(dz) + 0.5])

    def point(self, dx: float, dy: float, dz: float) -> np.ndarray:
        return np.array([self.x + dx + 0.5, self.gy + 1.0 + dy, self.z + dz + 0.5])

    def mark(self, name: str, dx: float, dz: float, dy: float = 0.0):
        self.marks[name] = self.point(dx, dy, dz)
        return self

    def keep_free_rect(self, dx0: float, dz0: float, dx1: float, dz1: float):
        """Keep a rectangle (local coords) free of scatter/trees — e.g. the corridor between the cast and the cameras."""
        for a in range(int(math.floor(min(dx0, dx1))), int(math.floor(max(dx0, dx1))) + 1):
            for b in range(int(math.floor(min(dz0, dz1))), int(math.floor(max(dz0, dz1))) + 1):
                self.occupied.add((a, b))
        return self

    def keep_free(self, dx: float, dz: float, rad: float = 1.5):
        for a in range(int(-rad) - 1, int(rad) + 2):
            for b in range(int(-rad) - 1, int(rad) + 2):
                if a * a + b * b <= rad * rad:
                    self.occupied.add((int(math.floor(dx)) + a, int(math.floor(dz)) + b))
        return self

    # ---- ground
    def clear(self, r: Optional[int] = None, h: int = 34, margin: int = 6, trees_ring: int = 14):
        """Empty the set volume (r+margin, h blocks high: tall trees go whole) and remove the trees of a wider ring (r+trees_ring),
        so no half-cut tree floats at the edge of the set (seen 21/10 on the plains site)."""
        r = (r or self.r) + margin
        R = r + trees_ring - margin
        for tag in ("leaves", "logs"):
            self.cmds += _fill_chunks(self.x - R, self.gy - 2, self.z - R, self.x + R, self.gy + h, self.z + R, "air", f"replace #minecraft:{tag}")
        self.cmds += _fill_chunks(self.x - r, self.gy + 1, self.z - r, self.x + r, self.gy + h, self.z + r, "air")
        return self

    def floor(self, top: str = "sand", sub: str = "sandstone", depth: int = 3, r: Optional[int] = None, margin: int = 6):
        r = (r or self.r) + margin
        self.cmds += _fill_chunks(self.x - r, self.gy - depth, self.z - r, self.x + r, self.gy - 1, self.z + r, sub)
        self.cmds += _fill_chunks(self.x - r, self.gy, self.z - r, self.x + r, self.gy, self.z + r, top)
        return self

    def kit(self, biome: Optional[str] = None, r: Optional[int] = None, density: float = 1.0, trees: bool = True):
        """ground() + dress() in one go (only for a bare set: ponds/cast added later would get scatter on top)."""
        return self.ground(biome, r).dress(biome, r, density, trees)

    def ground(self, biome: Optional[str] = None, r: Optional[int] = None):
        """Clear the air volume and lay the biome's floor (first; then ponds/templates/cast; then dress())."""
        b = biome or self.biome
        k = KITS.get(b, KITS["plains"])
        if k.get("soften", True):
            self.soften(top=k["top"], r=r)
        return self.clear(r).floor(k["top"], k["sub"], r=r)

    def soften(self, rings=((10, 2), (18, 5), (30, 9)), top: str = "grass_block", r: Optional[int] = None, h: int = 48):
        """Terrace the terrain AROUND the set (ring k: nothing higher than ground+h_k within r+6+d_k), so a hill or cliff behind
        the set becomes a gentle background instead of a wall (seen 21/10 on the plains site).  Trees in that area go too."""
        r = (r or self.r) + 6
        R = r + rings[-1][0]
        for tag in ("leaves", "logs"):
            self.cmds += _fill_chunks(self.x - R, self.gy - 2, self.z - R, self.x + R, self.gy + h, self.z + R, "air", f"replace #minecraft:{tag}")
        for d, hk in rings:
            Rk = r + d
            self.cmds += _fill_chunks(self.x - Rk, self.gy + 1 + hk, self.z - Rk, self.x + Rk, self.gy + h, self.z + Rk, "air")
            for under in ("dirt", "stone", "andesite", "diorite", "granite", "gravel"):
                self.cmds += _fill_chunks(self.x - Rk, self.gy + hk, self.z - Rk, self.x + Rk, self.gy + hk, self.z + Rk, top,
                                          f"replace minecraft:{under}")
        return self

    def dress(self, biome: Optional[str] = None, r: Optional[int] = None, density: float = 1.0, trees: bool = True):
        """Trees + scatter of the biome, avoiding ponds, cast spots and anything marked with keep_free()."""
        b = biome or self.biome
        k = KITS.get(b, KITS["plains"])
        if trees:
            for feat, n in k["trees"]:
                for _ in range(int(round(n * density))):
                    dx, dz = self._free_spot(min_r=7, max_r=(r or self.r) - 2)
                    self.tree(dx, dz, feat)
        for blk, n in k["scatter"]:
            self.scatter(blk, int(round(n * density)), r=r)
        return self

    def _free_spot(self, min_r: float = 0.0, max_r: Optional[float] = None, tries: int = 200) -> Tuple[int, int]:
        max_r = max_r or self.r - 1
        for _ in range(tries):
            a, d = self.rng.uniform(0, 2 * math.pi), math.sqrt(self.rng.uniform(min_r ** 2, max_r ** 2))
            dx, dz = int(round(math.cos(a) * d)), int(round(math.sin(a) * d))
            if (dx, dz) not in self.occupied and (dx, dz) not in self.water_cells:
                self.occupied.add((dx, dz))
                return dx, dz
        return int(max_r), 0

    def scatter(self, block: str, n: int, r: Optional[int] = None, min_r: float = 2.5):
        """'dead_bush', 'cactus*2' (column of 2), 'sunflower*2' (double plant), 'lily_pad@water' (on water cells)."""
        on_water = block.endswith("@water")
        blk = block.replace("@water", "")
        hgt = 1
        if "*" in blk:
            blk, hgt = blk.split("*")[0], int(blk.split("*")[1])
        for _ in range(n):
            if on_water:
                if not self.water_cells:
                    return self
                cells = sorted(self.water_cells)
                dx, dz = cells[int(self.rng.integers(len(cells)))]
                X, Z = self.w(dx, dz)
                self.cmds.append(f"setblock {X} {self.gy + 1} {Z} minecraft:{blk}")
                continue
            dx, dz = self._free_spot(min_r=min_r, max_r=(r or self.r) - 1)
            X, Z = self.w(dx, dz)
            if blk in ("sunflower", "tall_grass", "large_fern", "lilac", "rose_bush", "peony"):
                self.cmds.append(f"setblock {X} {self.gy + 1} {Z} minecraft:{blk}[half=lower]")
                self.cmds.append(f"setblock {X} {self.gy + 2} {Z} minecraft:{blk}[half=upper]")
            elif blk == "snow":
                self.cmds.append(f"setblock {X} {self.gy + 1} {Z} minecraft:snow[layers={int(self.rng.integers(1, 3))}]")
            elif blk == "tulip":
                c = ["red", "orange", "white", "pink"][int(self.rng.integers(4))]
                self.cmds.append(f"setblock {X} {self.gy + 1} {Z} minecraft:{c}_tulip")
            else:
                for k in range(hgt):
                    self.cmds.append(f"setblock {X} {self.gy + 1 + k} {Z} minecraft:{blk}")
        return self

    # ---- features
    def pond(self, dx: float, dz: float, rx: float, rz: float, depth: int = 2, water: bool = True, plants: Optional[str] = "sugar_cane",
             seabed: Sequence[str] = ("seagrass",), name: str = "pond", wobble: float = 0.14, rim: Optional[str] = None,
             plants_front: bool = False):
        """Organic pond: shelf 1 deep + deeper middle.  water=False -> the same hole DRY (a drained pond).
        plants on the rim (sugar_cane needs water next to it), seagrass inside.  Mark '<name>' = centre at the water surface."""
        cx, cz = dx, dz
        for z in range(int(cz - rz - 2), int(cz + rz + 3)):
            for layer, k in ((0, 1.0), (1, 0.62)):
                xs = []
                for x in range(int(cx - rx - 2), int(cx + rx + 3)):
                    ux, uz = (x + 0.5 - cx) / rx, (z + 0.5 - cz) / rz
                    wob = wobble * math.sin(2.1 * x + 0.7 * z) + wobble * 0.7 * math.sin(1.3 * z - 0.9 * x)
                    if ux * ux + uz * uz < (k + wob) ** 2:
                        xs.append(x)
                        self.water_cells.add((x, z)) if layer == 0 else None
                        self.occupied.add((x, z))
                if xs:
                    y = self.gy - layer
                    X0, Z0 = self.w(min(xs), z)
                    X1, _ = self.w(max(xs), z)
                    blk = "water" if water else "air"
                    self.cmds.append(f"fill {X0} {y} {Z0} {X1} {y} {Z0} minecraft:{blk}")
                    if layer == 1 or depth == 1:
                        sub = "sand" if self.biome in ("desert", "beach") else "dirt"
                        self.cmds.append(f"fill {X0} {y - 1} {Z0} {X1} {y - 1} {Z0} minecraft:{sub}")
        if water and seabed:
            cells = [c for c in sorted(self.water_cells) if ((c[0] + 0.5 - cx) / rx) ** 2 + ((c[1] + 0.5 - cz) / rz) ** 2 < 0.35]
            for c in cells[:: max(1, len(cells) // 6)]:
                X, Z = self.w(*c)
                self.cmds.append(f"setblock {X} {self.gy - 1} {Z} minecraft:{seabed[0]}")
        if plants:
            n = 0
            for (x, z) in sorted(self.water_cells):
                for (ax, az) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    q = (x + ax, z + az)
                    if q in self.water_cells or q in self.occupied or n >= 9 or self.rng.random() > 0.18:
                        continue
                    if not plants_front and q[1] > cz:          # near rim = between the pond and the cameras (+z): keep it clear
                        continue
                    X, Z = self.w(*q)
                    h = int(self.rng.integers(2, 4)) if plants == "sugar_cane" else 1
                    for k in range(h):
                        self.cmds.append(f"setblock {X} {self.gy + 1 + k} {Z} minecraft:{plants}")
                    self.occupied.add(q); n += 1
        if rim:
            for (x, z) in sorted(self.water_cells):
                for (ax, az) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    q = (x + ax, z + az)
                    if q not in self.water_cells:
                        X, Z = self.w(*q)
                        self.cmds.append(f"setblock {X} {self.gy} {Z} minecraft:{rim}")
        self.marks[name] = self.point(cx, -1.1, cz)
        return self

    def tree(self, dx: float, dz: float, kind: str = "oak"):
        """place feature (vanilla configured features: oak, birch, spruce, jungle_tree, acacia, dark_oak, cherry, mangrove,
        fancy_oak, swamp_oak, huge_red_mushroom, jungle_bush...)."""
        X, Z = self.w(dx, dz)
        self.keep_free(dx, dz, 2.2)
        self.cmds.append(f"setblock {X} {self.gy} {Z} minecraft:{'mycelium' if 'mushroom' in kind else 'grass_block'}")
        self.cmds.append(f"place feature minecraft:{kind} {X} {self.gy + 1} {Z}")
        return self

    def template(self, tid: str, dx: float, dz: float, rot: str = "none", dy: int = 0):
        """place template (structure pieces, e.g. 'minecraft:village/desert/houses/desert_small_house_1',
        'minecraft:village/plains/houses/plains_small_house_1', 'minecraft:igloo/top').  The piece's corner goes at (dx,dz)."""
        X, Z = self.w(dx, dz)
        self.cmds.append(f"place template {tid} {X} {self.gy + 1 + dy} {Z} {rot}")
        return self

    def structure(self, sid: str, dx: float, dz: float):
        """place structure (whole jigsaw structure, e.g. minecraft:village_desert) — big and random; use far in the background."""
        X, Z = self.w(dx, dz)
        self.cmds.append(f"place structure {sid} {X} {self.gy + 1} {Z}")
        return self

    def mob(self, mtype: str, dx: float, dz: float, yaw: float = 0.0, dy: float = 0.0, nbt: str = ""):
        """Still vanilla mob (NoAI, silent, invulnerable) as set dressing; for an ANIMATED mob use cinecam Mob instead."""
        p = self.point(dx, dy, dz)
        extra = ("," + nbt) if nbt else ""
        self.cmds.append(f"summon minecraft:{mtype} {p[0]:.2f} {p[1]:.2f} {p[2]:.2f} "
                         f"{{NoAI:1b,Silent:1b,Invulnerable:1b,PersistenceRequired:1b,Rotation:[{yaw:.1f}f,0f]{extra}}}")
        return self

    def block(self, dx: int, dy: int, dz: int, blk: str):
        X, Z = self.w(dx, dz)
        self.cmds.append(f"setblock {X} {self.gy + 1 + dy} {Z} minecraft:{blk}")
        return self

    def box(self, dx0: int, dy0: int, dz0: int, dx1: int, dy1: int, dz1: int, blk: str, mode: str = ""):
        X0, Z0 = self.w(dx0, dz0)
        X1, Z1 = self.w(dx1, dz1)
        self.cmds += _fill_chunks(X0, self.gy + 1 + dy0, Z0, X1, self.gy + 1 + dy1, Z1, blk, mode)
        return self

    def raw(self, *cmds: str):
        """Any extra vanilla command (absolute coordinates)."""
        self.cmds += list(cmds)
        return self

    def scene(self, time: int = 6000, weather: str = "clear", anchor: Optional[Sequence[float]] = None, **kw) -> Scene:
        a = anchor if anchor is not None else (self.x, self.gy + 6, self.z)
        return Scene(time=time, weather=weather, anchor=tuple(a), commands=list(self.cmds), **kw)
