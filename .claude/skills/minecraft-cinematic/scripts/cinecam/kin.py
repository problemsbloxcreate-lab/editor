"""kin: exact forward/inverse kinematics of the CineCam player model (same transforms as Actors.drawActor in the mod).

Why (21/10/2026, Matheus): "NUNCA MAIS item que não esteja perfeitamente encaixado" — a straw went through a head because it was
aimed at an approximate mouth from behind.  Every prop that touches a character must be computed FROM the posed limbs here, every
frame, and checked with `clearance()` before rendering.

    from cinecam.kin import KActor
    k = KActor(actor)                       # wraps an Actor (keys already set)
    k.hand(t, "R"), k.mouth(t), k.face_dir(t), k.body_dir(t), k.head_center(t)
    x, z = k.arm_aim(t, target, "R")        # rarm_x / rarm_z that point the right arm at target (y rot 0)
    k.clearance(t, p0, p1)                  # min distance (blocks) from segment p0-p1 to head/torso/limbs boxes (negative = inside)

Model space (px, 16 px = 1 block before actor scale): x = model LEFT is +x, y DOWN, z BACK (face at z=-4).
Pivots: head (0,0,0) box (-4..4, -8..0, -4..4); body box (-4..4, 0..12, -2..2); right arm pivot (-5,2,0) box (-3..1, -2..10, -2..2);
left arm pivot (5,2,0) box (-1..3, -2..10, -2..2); legs pivots (-1.9,12,0)/(1.9,12,0) boxes (-2..2, 0..12, -2..2).
World = T(feet + hop) · Ry(180-yaw) · Rx(lean) · Rz(roll) · S(-1,-1,1) · S(sx,sy,sz) · T(0,-1.501,0) · part(pivot, Rz·Ry·Rx).
"""
from __future__ import annotations

import math
from typing import Dict, Sequence, Tuple

import numpy as np

from .actors import POSE

PX = 1.0 / 16.0


def _rx(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def _ry(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def _rz(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


PARTS = {   # pivot px, rotation channels, box (min, max) px in part space
    "head": ((0, 0, 0), ("head_x", "head_y", "head_z"), ((-4, -8, -4), (4, 0, 4))),
    "body": ((0, 0, 0), None, ((-4, 0, -2), (4, 12, 2))),
    "rarm": ((-5, 2, 0), ("rarm_x", "rarm_y", "rarm_z"), ((-3, -2, -2), (1, 10, 2))),
    "larm": ((5, 2, 0), ("larm_x", "larm_y", "larm_z"), ((-1, -2, -2), (3, 10, 2))),
    "rleg": ((-1.9, 12, 0), ("rleg_x", "rleg_y", "rleg_z"), ((-2, 0, -2), (2, 12, 2))),
    "lleg": ((1.9, 12, 0), ("lleg_x", "lleg_y", "lleg_z"), ((-2, 0, -2), (2, 12, 2))),
}


class KActor:
    def __init__(self, actor):
        self.a = actor

    def row(self, t: float) -> np.ndarray:
        """Pose row at t, cached per actor until its keys/wobbles change (the checks ask for the same t many times)."""
        a = self.a
        sig = sum(len(v) for v in a.keys.values()) * 1000 + len(a.wobbles)
        cache = a.__dict__.setdefault("_kin_cache", {})
        if cache.get("_sig") != sig:
            cache.clear(); cache["_sig"] = sig
        key = round(float(t), 6)
        r = cache.get(key)
        if r is None:
            if len(cache) > 4000:
                cache.clear(); cache["_sig"] = sig
            r = cache[key] = a.at(np.array([float(t)]))[0]
        return r

    # ---- transforms
    def _root(self, r) -> Tuple[np.ndarray, np.ndarray]:
        """(3x3 M, origin) mapping model-BLOCK coords (already /16) to world."""
        g = lambda k: r[POSE[k]]
        sx, sy, sz = (g("sx") or 1), (g("sy") or 1), (g("sz") or 1)
        R = _ry(math.radians(180.0 - g("yaw")))
        if g("lean"):
            R = R @ _rx(math.radians(g("lean")))
        if g("roll"):
            R = R @ _rz(math.radians(g("roll")))
        M = R @ np.diag([-1.0, -1.0, 1.0]) @ np.diag([sx, sy, sz])
        origin = np.array([g("x"), g("y") + g("hop"), g("z")]) + M @ np.array([0.0, -1.501, 0.0])
        return M, origin

    def _part(self, r, name):
        pivot, ch, _ = PARTS[name]
        piv = np.array(pivot, float)
        if name in ("rarm", "larm"):                      # fat belly pushes the arms out (mod: spread = (belly-1)*4.2 px)
            spread = ((r[POSE["belly"]] or 1) - 1) * 4.2
            piv[0] += -spread if name == "rarm" else spread
        Rp = np.eye(3)
        if ch:
            x, y, z = (math.radians(r[POSE[c]]) for c in ch)
            Rp = _rz(z) @ _ry(y) @ _rx(x)
        return piv, Rp

    def point(self, t: float, part: str, local_px: Sequence[float]) -> np.ndarray:
        """World position of a point given in a part's local px (e.g. hand = arm local (-1, 10, 0))."""
        r = self.row(t)
        M, o = self._root(r)
        piv, Rp = self._part(r, part)
        loc = np.array(local_px, float)
        if part in ("rarm", "larm"):                     # rubber arm length (len channel): stretch along the arm only
            L = r[POSE["rarm_len" if part == "rarm" else "larm_len"]] or 1.0
            loc = loc.copy(); loc[1] = -2 + (loc[1] + 2) * L
        if part == "head":
            loc = loc * (r[POSE["head"]] or 1.0)
        return o + M @ ((piv + Rp @ loc) * PX)

    def hand(self, t: float, side: str = "R") -> np.ndarray:
        return self.point(t, "rarm", (-1, 10.5, 0)) if side == "R" else self.point(t, "larm", (1, 10.5, 0))

    def grip(self, t: float, side: str = "R") -> np.ndarray:
        """Centre of the closed hand (where a held straw/stick/rope passes): 2 px above the arm end, inside the hand block."""
        return self.point(t, "rarm", (-1, 8.5, 0)) if side == "R" else self.point(t, "larm", (1, 8.5, 0))

    def mouth(self, t: float) -> np.ndarray:
        return self.point(t, "head", (0, -2.0, -4.15))

    def head_center(self, t: float) -> np.ndarray:
        return self.point(t, "head", (0, -4, 0))

    def chest(self, t: float) -> np.ndarray:
        return self.point(t, "body", (0, 4, -2.2))

    def face_dir(self, t: float) -> np.ndarray:
        d = self.point(t, "head", (0, -4, -5)) - self.head_center(t)
        return d / np.linalg.norm(d)

    def body_dir(self, t: float) -> np.ndarray:
        d = self.point(t, "body", (0, 6, -3)) - self.point(t, "body", (0, 6, 0))
        d[1] = 0
        return d / max(np.linalg.norm(d), 1e-9)

    def shoulder(self, t: float, side: str = "R") -> np.ndarray:
        return self.point(t, "rarm" if side == "R" else "larm", (0, 0, 0))

    # ---- inverse kinematics
    def arm_aim(self, t: float, target, side: str = "R", local=None) -> Tuple[float, float, float]:
        """(x_rot, z_rot, reach) in degrees for the arm so the HAND points at target (y_rot = 0).  reach = distance / arm length:
        > 1 means the target is out of reach (move the actor or the target, or use *_len for a rubber arm)."""
        r = self.row(t)
        M, o = self._root(r)
        name = "rarm" if side == "R" else "larm"
        piv, _ = self._part(r, name)
        S = o + M @ (piv * PX)
        w = np.linalg.solve(M, np.asarray(target, float) - S) / PX       # model px, relative to the pivot
        hand_local = np.array(local if local is not None else [-1.0 if side == "R" else 1.0, 10.5, 0.0], float)
        n = np.linalg.norm(w)
        d = w / max(n, 1e-9)
        # Rz(z)·Rx(x)·(0,1,0) = (-sin z cos x, cos z cos x, sin x); the hand sits 1 px off the arm axis, so iterate a few times
        # until the HAND (not the axis) points at the target (error < 0.05 deg)
        aim = d.copy()
        h = hand_local / np.linalg.norm(hand_local)
        for _ in range(6):
            x = math.asin(max(-1.0, min(1.0, aim[2])))
            z = math.atan2(-aim[0], aim[1])
            e = _rz(z) @ _rx(x) @ h
            aim = aim + (d - e)
            aim /= np.linalg.norm(aim)
        return math.degrees(x), math.degrees(z), n / np.linalg.norm(hand_local)

    # ---- collision
    def boxes(self, t: float) -> Dict[str, Tuple[np.ndarray, np.ndarray, np.ndarray]]:
        """Oriented boxes in world: name -> (centre, axes 3x3 (columns, unit), half-sizes)."""
        r = self.row(t)
        M, o = self._root(r)
        out = {}
        for name, (_, _, (lo, hi)) in PARTS.items():
            piv, Rp = self._part(r, name)
            lo, hi = np.array(lo, float), np.array(hi, float)
            if name in ("rarm", "larm"):
                L = r[POSE["rarm_len" if name == "rarm" else "larm_len"]] or 1.0
                hi = hi.copy(); hi[1] = -2 + (hi[1] + 2) * L
            if name == "head":
                k = r[POSE["head"]] or 1.0
                lo, hi = lo * k, hi * k
            c_loc = (lo + hi) / 2
            A = M @ Rp * PX                               # columns = world vectors of the part's x/y/z px axes
            c = o + M @ ((piv + Rp @ c_loc) * PX)
            scale = np.linalg.norm(A, axis=0)
            out[name] = (c, A / scale, (hi - lo) / 2 * scale)
        return out

    def clearance(self, t: float, p0, p1, parts: Sequence[str] = ("head", "body", "rarm", "larm"), samples: int = 24,
                  skip_ends: float = 0.0) -> Tuple[float, str]:
        """Smallest signed distance (blocks) from the segment p0->p1 to the given parts' boxes (negative = the segment goes
        INSIDE the part).  skip_ends: ignore that length at both ends (where the prop legitimately touches the hand/mouth)."""
        p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
        L = np.linalg.norm(p1 - p0)
        B = self.boxes(t)
        bel = self.belly_sphere(t) if "body" in parts else None
        best, who = 9e9, ""
        for s in np.linspace(0, 1, samples):
            if skip_ends and (s * L < skip_ends or (1 - s) * L < skip_ends):
                continue
            p = p0 + (p1 - p0) * s
            for name in parts:
                c, ax, h = B[name]
                q = np.abs(ax.T @ (p - c)) - h
                d = np.linalg.norm(np.maximum(q, 0)) + min(q.max(), 0)
                if d < best:
                    best, who = d, name
            if bel is not None:
                d = np.linalg.norm(p - bel[0]) - bel[1]
                if d < best:
                    best, who = d, "barriga"
        return float(best), who

    def belly_sphere(self, t: float):
        """(centre, radius) of the v0.7 voxel water belly, or None."""
        r = self.row(t)
        R = r[POSE["vbelly"]]
        if R <= 0.05:
            return None
        out, cy = r[POSE["vbelly_out"]], r[POSE["vbelly_y"]] or 7.0
        c = self.point(t, "body", (0, cy, -(2 + out - R)))
        M, _ = self._root(r)
        return c, R * PX * float(np.cbrt(abs(np.linalg.det(M))))
