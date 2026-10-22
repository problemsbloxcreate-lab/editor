"""preview: draw the camera path and its motion curves so you can judge a move BEFORE spending game time.

plot_rig(rig, "path.png") writes one PNG with: top-down path with look direction arrows, side view,
speed / angular speed, roll & fov, jerk.  Read the PNG and fix what looks wrong (kinks, sudden speed changes,
sustained spin, a camera that dives into terrain).
"""
from __future__ import annotations

from typing import Optional

import numpy as np

from .camlib import Rig, forward


def plot_rig(rig: Rig, out_png: str, terrain: Optional[dict] = None, title: str = "", arrows_every: float = 0.4) -> dict:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rep = rig.analyze()
    s = rep["_series"]
    t, pos = s["t"], s["pos"]
    import textwrap
    fig = plt.figure(figsize=(17, 10), dpi=72, constrained_layout=True)
    gs = fig.add_gridspec(3, 3, height_ratios=[1.3, 1, 1])

    ax = fig.add_subplot(gs[0:2, 0])
    sc = ax.scatter(pos[:, 0], pos[:, 2], c=t, s=8, cmap="viridis")
    step = max(int(arrows_every * rig.fps), 1)
    f = forward(s["yaw"], s["pitch"])
    ax.quiver(pos[::step, 0], pos[::step, 2], f[::step, 0], f[::step, 2], color="crimson", angles="xy", scale_units="xy",
              scale=0.18, width=0.004)
    for c in s["cuts"]:
        if 0 < c < len(t):
            ax.plot(pos[c, 0], pos[c, 2], "kx", ms=10)
    ax.set_title("top-down: x east →, z south ↓ (arrows = look dir, x = cut)", fontsize=9)
    ax.invert_yaxis(); ax.set_aspect("equal", adjustable="datalim"); ax.grid(alpha=.3)
    fig.colorbar(sc, ax=ax, label="t (s)", fraction=0.04)
    if terrain is not None and "xs" in terrain:
        ax.imshow(terrain["img"], extent=terrain["extent"], origin="upper", alpha=0.55, zorder=0)

    ax = fig.add_subplot(gs[0:2, 1])
    ax.plot(pos[:, 0], pos[:, 1], label="x-y")
    ax.plot(pos[:, 2], pos[:, 1], label="z-y")
    ax.set_title("side views (height y)"); ax.grid(alpha=.3); ax.legend()

    ax = fig.add_subplot(gs[0, 2])
    ax.plot(t, s["speed"], color="tab:blue")
    ax.set_title(f"speed blocks/s  (max {rep['max_speed']:.1f})"); ax.grid(alpha=.3)
    ax = fig.add_subplot(gs[1, 2])
    ax.plot(t, s["yawr"], label="yaw °/s"); ax.plot(t, s["pitr"], label="pitch °/s"); ax.plot(t, s["rollr"], label="roll °/s", alpha=.6)
    ax.set_title(f"angular rates (max {rep['max_angular_speed']:.0f} °/s)"); ax.grid(alpha=.3); ax.legend(fontsize=7)

    ax = fig.add_subplot(gs[2, 0])
    ax.plot(t, s["roll"], label="roll °", color="tab:green"); ax.plot(t, s["fov"], label="fov °", color="tab:orange")
    ax.set_title("roll & fov"); ax.grid(alpha=.3); ax.legend()
    ax = fig.add_subplot(gs[2, 1])
    ax.plot(t, s["jerk"], color="tab:red"); ax.set_yscale("symlog", linthresh=10)
    ax.set_title("|jerk| (spikes = joins or hard starts)", fontsize=9); ax.grid(alpha=.3)
    ax = fig.add_subplot(gs[2, 2]); ax.axis("off")
    txt = [title or "camera report", f"{rep['frames']} frames  {rep['duration']:.2f}s @ {rep['fps']:.0f}fps",
           f"fov {rep['fov_range'][0]:.0f}-{rep['fov_range'][1]:.0f}  max roll {rep['max_roll']:.1f}°"]
    txt += ["", "WARNINGS:" if rep["warnings"] else "no warnings"]
    for w in rep["warnings"]:
        txt += textwrap.wrap("• " + w, 70, subsequent_indent="  ")
    ax.text(0, 1, "\n".join(txt), va="top", family="monospace", fontsize=8)
    fig.savefig(out_png)
    plt.close(fig)
    rep.pop("_series", None)
    return rep
