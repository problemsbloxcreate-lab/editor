"""terrain: read the mod's scout JSON, draw a hill-shaded top-down map with world coordinates, query heights.

    t = Terrain.load(".../x_scout_a.json")
    t.save_map("map.png")                      # open it to pick locations; axes are real world x / z
    t.ground_at(120, -40)                      # terrain height (top of ground, trees ignored)
    t.clearance(rig)                           # min height of the camera above ground along a rig
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np


@dataclass
class Terrain:
    x0: int
    z0: int
    step: int
    w: int
    h: int
    surface: np.ndarray       # first free y above the top block (trees/water included)
    ground: np.ndarray        # same, leaves ignored
    floor: np.ndarray         # ocean floor
    rgb: np.ndarray           # map colour of the top block, 0xRRGGBB
    biome: np.ndarray
    biomes: List[str]

    @staticmethod
    def load(path: str) -> "Terrain":
        d = json.load(open(path, encoding="utf-8"))
        w, h = d["w"], d["h"]
        f = lambda k: np.array(d[k], dtype=int).reshape(h, w)
        return Terrain(d["x0"], d["z0"], d["step"], w, h, f("surface"), f("ground"), f("floor"), f("rgb"), f("biome"), d["biomes"])

    # -- geometry
    @property
    def extent(self):
        return (self.x0 - self.step / 2, self.x0 + (self.w - 0.5) * self.step, self.z0 + (self.h - 0.5) * self.step, self.z0 - self.step / 2)

    def _idx(self, x, z):
        ix = np.clip(np.round((np.asarray(x) - self.x0) / self.step).astype(int), 0, self.w - 1)
        iz = np.clip(np.round((np.asarray(z) - self.z0) / self.step).astype(int), 0, self.h - 1)
        return iz, ix

    def ground_at(self, x, z):
        iz, ix = self._idx(x, z)
        return self.ground[iz, ix]

    def surface_at(self, x, z):
        iz, ix = self._idx(x, z)
        return self.surface[iz, ix]

    def biome_at(self, x, z) -> str:
        iz, ix = self._idx(x, z)
        b = int(self.biome[iz, ix])
        return self.biomes[b] if b >= 0 else "unloaded"

    def clearance(self, rig, use_surface: bool = True) -> Dict:
        """Camera height above terrain along a rig (frame rate).  use_surface counts trees as obstacles."""
        d = rig.sample_frames()
        g = (self.surface if use_surface else self.ground)
        iz, ix = self._idx(d["x"], d["z"])
        clr = d["y"] - g[iz, ix]
        i = int(np.argmin(clr))
        return {"min_clearance": float(clr.min()), "at_t": float(d["t"][i]), "at_xyz": (float(d["x"][i]), float(d["y"][i]), float(d["z"][i])),
                "below_ground_frames": int((clr < 0.3).sum())}

    # -- image
    def image(self, shade: float = 1.0) -> np.ndarray:
        """Hill-shaded colour image (h,w,3) floats 0..1; unloaded cells are dark grey."""
        r = ((self.rgb >> 16) & 255) / 255.0
        g = ((self.rgb >> 8) & 255) / 255.0
        b = (self.rgb & 255) / 255.0
        img = np.stack([r, g, b], axis=-1)
        H = self.ground.astype(float)
        H[H < -900] = np.nan
        dzdx = np.zeros_like(H); dzdz = np.zeros_like(H)
        dzdx[:, 1:-1] = (H[:, 2:] - H[:, :-2]) / 2
        dzdz[1:-1, :] = (H[2:, :] - H[:-2, :]) / 2
        light = np.nan_to_num(-(dzdx * 0.7 + dzdz * 0.7) / max(self.step, 1), nan=0.0)
        k = np.clip(0.9 + shade * 0.45 * light, 0.5, 1.12)[..., None]
        water = (self.surface > self.floor) & (self.surface - self.floor >= 1) & (self.floor > -900)
        depth = np.clip((self.surface - self.floor) / 20.0, 0, 1)[..., None]
        img = np.where(water[..., None], img * (1 - 0.55 * depth), img * k)
        img[self.surface < -900] = 0.15
        return np.clip(img, 0, 1)

    def save_map(self, path: str, points: Optional[np.ndarray] = None, labels: Optional[List[str]] = None, title: str = "", grid: int = 16,
                 path_xz: Optional[np.ndarray] = None) -> str:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(12, 12 * self.h / max(self.w, 1)), dpi=72)
        ax.imshow(self.image(), extent=self.extent, origin="upper", interpolation="nearest")
        x0, x1, z1, z0 = self.extent
        gstep = max(grid, int(round(max(x1 - x0, z1 - z0) / 12 / grid)) * grid)
        ax.set_xticks(np.arange(np.ceil(x0 / gstep) * gstep, x1, gstep))
        ax.set_yticks(np.arange(np.ceil(z0 / gstep) * gstep, z1, gstep))
        ax.grid(color="white", alpha=.25, lw=.6)
        ax.tick_params(labelsize=7)
        if path_xz is not None:
            ax.plot(path_xz[:, 0], path_xz[:, 1], "-", color="red", lw=1.5)
        if points is not None:
            for i, (px, pz) in enumerate(points):
                ax.plot(px, pz, "o", color="yellow", ms=5)
                if labels:
                    ax.annotate(labels[i], (px, pz), color="yellow", fontsize=8, xytext=(4, 4), textcoords="offset points")
        ax.set_title(title or f"terrain {self.w}x{self.h} step {self.step}  (x east →, z south ↓)", fontsize=9)
        fig.tight_layout()
        fig.savefig(path)
        plt.close(fig)
        return path
