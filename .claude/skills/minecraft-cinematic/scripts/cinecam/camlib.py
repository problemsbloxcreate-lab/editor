"""camlib: camera language for Minecraft cinematics.

Conventions (Minecraft): x = east, y = up, z = south.  yaw 0 looks toward +z (south), yaw 90 looks toward -x
(west), yaw -90 looks toward +x (east).  pitch is positive when looking DOWN.  roll in degrees.

Design: a shot is a chain of Moves.  A Move is a duration plus a vectorised function of normalised time
tau in [0,1] that returns arrays x,y,z,yaw,pitch,roll,fov.  "Where the camera goes" (a Path3D) is kept
separate from "how fast it goes" (an easing curve on arc length), which is how a cinematographer thinks
about a dolly or crane move.  Modifiers (handheld, lag, bank, shake...) wrap a Move and return a Move.
A Rig stitches Moves together, samples them at fps*subframes rows (for motion blur), checks continuity and
writes camera.csv for the CineCam mod.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple, Union

import numpy as np

Arr = np.ndarray
FIELDS = ("x", "y", "z", "yaw", "pitch", "roll", "fov")
EXTRA = {"focus": -1.0, "aperture": 0.0}     # depth of field: focus distance in blocks (-1 = off), aperture 0..1

# --------------------------------------------------------------------------- easing


def cubic_bezier(x1: float, y1: float, x2: float, y2: float) -> Callable[[Arr], Arr]:
    """CSS-style cubic-bezier easing, vectorised.  Solves x(t)=u by bisection (monotonic for x1,x2 in [0,1])."""

    def f(u):
        u = np.clip(np.asarray(u, dtype=float), 0.0, 1.0)
        lo = np.zeros_like(u)
        hi = np.ones_like(u)
        for _ in range(42):
            t = (lo + hi) * 0.5
            x = 3 * (1 - t) ** 2 * t * x1 + 3 * (1 - t) * t ** 2 * x2 + t ** 3
            lo = np.where(x < u, t, lo)
            hi = np.where(x < u, hi, t)
        t = (lo + hi) * 0.5
        return 3 * (1 - t) ** 2 * t * y1 + 3 * (1 - t) * t ** 2 * y2 + t ** 3

    return f


def _smoother(u):
    u = np.clip(np.asarray(u, dtype=float), 0, 1)
    return u * u * u * (u * (u * 6 - 15) + 10)


def _out_expo(u):
    u = np.clip(np.asarray(u, dtype=float), 0, 1)
    return np.where(u >= 1, 1.0, (1 - 2.0 ** (-10 * u)) / (1 - 2.0 ** -10))


EASES: Dict[str, Callable[[Arr], Arr]] = {
    "linear": lambda u: np.clip(np.asarray(u, dtype=float), 0, 1),
    "in": cubic_bezier(0.42, 0, 1, 1),
    "out": cubic_bezier(0, 0, 0.58, 1),
    "in_out": cubic_bezier(0.42, 0, 0.58, 1),
    "smooth": _smoother,                                  # smootherstep: zero velocity AND acceleration at both ends
    "soft_in_out": cubic_bezier(0.3, 0, 0.3, 1),          # gentle, long shoulders (reveals, slow cranes)
    "out_expo": _out_expo,                                # arrives hard, settles very slowly
    # "launch": the Bionic-style arrival: very fast attack that decelerates for the rest of the shot.
    "launch": cubic_bezier(0.04, 0.78, 0.16, 1.0),
    "launch_soft": cubic_bezier(0.12, 0.6, 0.2, 1.0),
    "whip": cubic_bezier(0.75, 0.0, 0.18, 1.0),           # violent pan: slow start, huge peak speed, decelerated landing
    "in_quart": cubic_bezier(0.5, 0, 0.75, 0),
    "out_back": cubic_bezier(0.2, 0.9, 0.3, 1.12),        # slight overshoot then settle (punch-ins)
}

EaseSpec = Union[str, Callable[[Arr], Arr], Tuple[float, float, float, float]]


def ease_fn(spec: EaseSpec) -> Callable[[Arr], Arr]:
    if callable(spec):
        return spec
    if isinstance(spec, str):
        if spec not in EASES:
            raise KeyError(f"unknown ease '{spec}'. Available: {sorted(EASES)}")
        return EASES[spec]
    return cubic_bezier(*spec)


# --------------------------------------------------------------------------- vectors / angles


def v3(p) -> Arr:
    a = np.asarray(p, dtype=float)
    if a.shape != (3,):
        raise ValueError(f"expected 3 numbers, got {p!r}")
    return a


def forward(yaw, pitch) -> Arr:
    """Unit look vector for Minecraft yaw/pitch (degrees).  Returns shape (...,3)."""
    y = np.radians(np.asarray(yaw, dtype=float))
    p = np.radians(np.asarray(pitch, dtype=float))
    return np.stack([-np.sin(y) * np.cos(p), -np.sin(p), np.cos(y) * np.cos(p)], axis=-1)


def look_at(pos, target) -> Tuple[Arr, Arr]:
    """Yaw/pitch (degrees) that make a camera at pos look at target.  Accepts (...,3) arrays."""
    d = np.asarray(target, dtype=float) - np.asarray(pos, dtype=float)
    dx, dy, dz = d[..., 0], d[..., 1], d[..., 2]
    yaw = np.degrees(np.arctan2(-dx, dz))
    horiz = np.hypot(dx, dz)
    pitch = -np.degrees(np.arctan2(dy, horiz))
    return yaw, pitch


def unwrap_deg(a: Arr) -> Arr:
    return np.degrees(np.unwrap(np.radians(a)))


def fov_for_framing(subject_height: float, distance: float, frame_fraction: float = 0.5, vertical: bool = True) -> float:
    """Vertical FOV (degrees, what Minecraft calls FOV) so a subject of given height fills frame_fraction of the frame at distance."""
    return math.degrees(2 * math.atan((subject_height / frame_fraction) / (2 * distance)))


# --------------------------------------------------------------------------- spline path


class Path3D:
    """Centripetal Catmull-Rom spline through waypoints, re-parameterised by arc length (u in [0,1])."""

    def __init__(self, pts: Sequence[Sequence[float]], closed: bool = False, alpha: float = 0.5, per_seg: int = 160):
        P = np.asarray(pts, dtype=float)
        if P.ndim != 2 or P.shape[1] != 3 or len(P) < 2:
            raise ValueError("Path3D needs >= 2 waypoints of 3 numbers")
        if len(P) == 2:                     # a straight line
            t = np.linspace(0, 1, per_seg * 2)
            dense = P[0][None] * (1 - t)[:, None] + P[1][None] * t[:, None]
        else:
            if closed:
                ext = np.vstack([P[-1], P, P[0], P[1]])
            else:
                ext = np.vstack([2 * P[0] - P[1], P, 2 * P[-1] - P[-2]])
            segs = []
            for i in range(1, len(ext) - 2):
                p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
                segs.append(self._cr_segment(p0, p1, p2, p3, alpha, per_seg))
            dense = np.vstack(segs)
        seglen = np.linalg.norm(np.diff(dense, axis=0), axis=1)
        s = np.concatenate([[0.0], np.cumsum(seglen)])
        self.length = float(s[-1]) if s[-1] > 0 else 1e-9
        self._s = s / self.length
        self._dense = dense
        self.waypoints = P

    @staticmethod
    def _cr_segment(p0, p1, p2, p3, alpha, n):
        def knot(ti, a, b):
            return ti + max(np.linalg.norm(b - a), 1e-6) ** alpha
        t0 = 0.0
        t1 = knot(t0, p0, p1)
        t2 = knot(t1, p1, p2)
        t3 = knot(t2, p2, p3)
        t = np.linspace(t1, t2, n, endpoint=False)[:, None]
        a1 = (t1 - t) / (t1 - t0) * p0 + (t - t0) / (t1 - t0) * p1
        a2 = (t2 - t) / (t2 - t1) * p1 + (t - t1) / (t2 - t1) * p2
        a3 = (t3 - t) / (t3 - t2) * p2 + (t - t2) / (t3 - t2) * p3
        b1 = (t2 - t) / (t2 - t0) * a1 + (t - t0) / (t2 - t0) * a2
        b2 = (t3 - t) / (t3 - t1) * a2 + (t - t1) / (t3 - t1) * a3
        c = (t2 - t) / (t2 - t1) * b1 + (t - t1) / (t2 - t1) * b2
        return np.vstack([c, p2[None]]) if False else c

    def at(self, u) -> Arr:
        u = np.clip(np.asarray(u, dtype=float), 0.0, 1.0)
        return np.stack([np.interp(u, self._s, self._dense[:, k]) for k in range(3)], axis=-1)

    def tangent(self, u) -> Arr:
        u = np.asarray(u, dtype=float)
        h = 1.0 / max(len(self._s) - 1, 1) * 3
        a = self.at(np.clip(u - h, 0, 1))
        b = self.at(np.clip(u + h, 0, 1))
        d = b - a
        n = np.linalg.norm(d, axis=-1, keepdims=True)
        return d / np.where(n < 1e-9, 1.0, n)


# --------------------------------------------------------------------------- Move


Aim = Union[Sequence[float], Callable[[Arr], Arr], None]


@dataclass
class Move:
    """duration seconds + fn(tau array in [0,1]) -> dict of arrays (FIELDS)."""
    duration: float
    fn: Callable[[Arr], Dict[str, Arr]]
    name: str = "move"

    def eval(self, tau) -> Dict[str, Arr]:
        tau = np.clip(np.asarray(tau, dtype=float), 0.0, 1.0)
        out = self.fn(tau)
        for k in FIELDS:
            out[k] = np.broadcast_to(np.asarray(out[k], dtype=float), tau.shape).copy()
        for k, dv in EXTRA.items():
            out[k] = np.broadcast_to(np.asarray(out.get(k, dv), dtype=float), tau.shape).copy()
        return out

    def start_pose(self) -> Dict[str, float]:
        return {k: float(v[0]) for k, v in self.eval(np.array([0.0])).items() if k in FIELDS}

    def end_pose(self) -> Dict[str, float]:
        return {k: float(v[0]) for k, v in self.eval(np.array([1.0])).items() if k in FIELDS}

    # ---- modifiers (each returns a new Move)
    def map(self, f: Callable[[Dict[str, Arr], Arr], Dict[str, Arr]], name: Optional[str] = None) -> "Move":
        base = self
        return Move(self.duration, lambda tau: f(base.fn(tau), tau), name or self.name)

    def with_roll(self, roll: Union[float, Callable[[Arr], Arr], Tuple[float, float]], ease: EaseSpec = "smooth", add: bool = False) -> "Move":
        """Set (or add to) roll.  roll: constant, (from,to) tuple eased over the move, or callable(tau)."""
        e = ease_fn(ease)

        def r(tau):
            if callable(roll):
                return roll(tau)
            if isinstance(roll, tuple):
                return roll[0] + (roll[1] - roll[0]) * e(tau)
            return np.full_like(tau, float(roll))

        def f(o, tau):
            o = dict(o)
            o["roll"] = (o["roll"] if add else 0.0) + r(tau)
            return o
        return self.map(f)

    def with_fov(self, fov: Union[float, Callable[[Arr], Arr], Tuple[float, float]], ease: EaseSpec = "smooth") -> "Move":
        e = ease_fn(ease)

        def r(tau):
            if callable(fov):
                return fov(tau)
            if isinstance(fov, tuple):
                return fov[0] + (fov[1] - fov[0]) * e(tau)
            return np.full_like(tau, float(fov))

        def f(o, tau):
            o = dict(o)
            o["fov"] = r(tau)
            return o
        return self.map(f)

    def with_dof(self, focus, aperture: Union[float, Tuple[float, float]] = 0.5, ease: EaseSpec = "smooth") -> "Move":
        """Depth of field.  focus: distance in blocks | (from,to) rack focus eased over the move | a world point (sharp on that point, even as the
        camera moves).  aperture 0..1 (0.2 = subtle, 0.5 = shallow cinematic, 0.9 = tilt-shift/macro) or (from,to).  Needs render(..., dof=True)."""
        e = ease_fn(ease)
        base = self

        def f(o, tau):
            o = dict(o)
            if isinstance(focus, (tuple, list)) and len(focus) == 2:
                fd = focus[0] + (focus[1] - focus[0]) * e(tau)
            elif isinstance(focus, (tuple, list)) and len(focus) == 3:
                p = np.asarray(focus, dtype=float)
                pos = np.stack([o["x"], o["y"], o["z"]], axis=-1)
                fwd = forward(o["yaw"], o["pitch"])
                fd = np.sum((p[None, :] - pos) * fwd, axis=-1)          # distance along the view axis (what the depth buffer stores)
            else:
                fd = np.full_like(tau, float(focus))
            o["focus"] = np.maximum(fd, 0.2)
            o["aperture"] = (aperture[0] + (aperture[1] - aperture[0]) * e(tau)) if isinstance(aperture, tuple) else np.full_like(tau, float(aperture))
            return o
        return self.map(f)

    def with_time_ease(self, ease: EaseSpec) -> "Move":
        """Re-time the move: tau' = ease(tau).  Use to change HOW FAST it plays without changing the path."""
        e = ease_fn(ease)
        base = self
        return Move(self.duration, lambda tau: base.fn(e(tau)), self.name)

    def with_handheld(self, preset: Union[str, Tuple[float, float, float]] = "handheld", seed: int = 7, fade: float = 0.0) -> "Move":
        """Add smooth handheld drift.  preset in HANDHELD or (angle_deg, pos_blocks, base_hz)."""
        ang, pos, hz = HANDHELD[preset] if isinstance(preset, str) else preset
        dur = self.duration
        rng = np.random.default_rng(seed)
        ph = rng.uniform(0, 2 * math.pi, size=(6, 3))
        fr = np.array([1.0, 1.73, 2.91])
        am = np.array([1.0, 0.5, 0.25]); am = am / am.sum()
        chan_hz = hz * rng.uniform(0.85, 1.2, size=6)

        def noise(t, c):
            return sum(am[k] * np.sin(2 * math.pi * chan_hz[c] * fr[k] * t + ph[c, k]) for k in range(3))

        def f(o, tau):
            t = tau * dur
            o = dict(o)
            w = np.ones_like(tau)
            if fade > 0:
                w = np.minimum(1.0, np.minimum(t / fade, (dur - t) / fade))
            o["yaw"] = o["yaw"] + ang * 1.0 * noise(t, 0) * w
            o["pitch"] = o["pitch"] + ang * 0.8 * noise(t, 1) * w
            o["roll"] = o["roll"] + ang * 0.6 * noise(t, 2) * w
            # position noise in camera space would need the basis; world-space noise of ~cm is visually equivalent
            o["x"] = o["x"] + pos * noise(t, 3) * w
            o["y"] = o["y"] + pos * 1.2 * noise(t, 4) * w
            o["z"] = o["z"] + pos * noise(t, 5) * w
            return o
        return self.map(f)

    def with_shake(self, hits: Iterable[Tuple[float, float, float]], freq: float = 9.0, seed: int = 3) -> "Move":
        """Impact shakes: hits = [(time_seconds_in_move, amplitude_degrees, decay_seconds), ...]."""
        hits = list(hits)
        dur = self.duration
        rng = np.random.default_rng(seed)
        dirs = [rng.uniform(-1, 1, size=3) for _ in hits]

        def f(o, tau):
            t = tau * dur
            o = dict(o)
            for (t0, amp, dec), d in zip(hits, dirs):
                dt = t - t0
                env = np.where(dt >= 0, np.exp(-np.maximum(dt, 0) / max(dec, 1e-3)), 0.0)
                osc = np.sin(2 * math.pi * freq * np.maximum(dt, 0))
                o["yaw"] = o["yaw"] + amp * d[0] * env * osc
                o["pitch"] = o["pitch"] + amp * d[1] * env * osc
                o["roll"] = o["roll"] + amp * 0.6 * d[2] * env * osc
            return o
        return self.map(f)

    def with_lag(self, smooth_time: float = 0.18) -> "Move":
        """Critically-damped smoothing of yaw/pitch/roll/fov: the camera 'follows' with weight instead of snapping to the aim.
        Larger smooth_time = heavier camera.  Position is untouched."""
        base = self
        dur = self.duration
        hz = 600.0
        n = max(int(dur * hz) + 1, 2)
        tau_g = np.linspace(0, 1, n)
        raw = base.eval(tau_g)
        dt = dur / (n - 1)
        out = {k: raw[k].copy() for k in FIELDS}
        omega = 2.0 / max(smooth_time, 1e-3)
        for k in ("yaw", "pitch", "roll", "fov"):
            x = raw[k].copy()
            y = x[0]
            v = 0.0
            sm = np.empty_like(x)
            for i in range(n):
                tgt = x[i]
                e = omega * dt
                expo = 1.0 / (1.0 + e + 0.48 * e * e + 0.235 * e * e * e)
                change = y - tgt
                temp = (v + omega * change) * dt
                v = (v - omega * temp) * expo
                y = tgt + (change + temp) * expo
                sm[i] = y
            out[k] = sm

        def f(tau):
            return {k: np.interp(tau, tau_g, out[k]) for k in FIELDS}
        return Move(dur, f, self.name)

    def with_bank(self, k: float = 0.35, max_deg: float = 25.0, smooth: float = 0.25) -> "Move":
        """Bank (roll) into turns like an aircraft: roll proportional to yaw rate.  Positive k rolls toward the turn."""
        base = self
        dur = self.duration
        n = max(int(dur * 200) + 1, 3)
        tau_g = np.linspace(0, 1, n)
        raw = base.eval(tau_g)
        yaw_rate = np.gradient(raw["yaw"], dur / (n - 1))
        roll = np.clip(-k * yaw_rate, -max_deg, max_deg)
        win = max(int(smooth * 200), 1)
        roll = np.convolve(np.pad(roll, win, mode="edge"), np.ones(2 * win + 1) / (2 * win + 1), mode="same")[win:-win]
        extra = lambda tau: np.interp(tau, tau_g, roll)

        def f(o, tau):
            o = dict(o)
            o["roll"] = o["roll"] + extra(tau)
            return o
        return self.map(f)

    def offset(self, dx=0.0, dy=0.0, dz=0.0) -> "Move":
        def f(o, tau):
            o = dict(o)
            o["x"] = o["x"] + dx
            o["y"] = o["y"] + dy
            o["z"] = o["z"] + dz
            return o
        return self.map(f)


HANDHELD = {
    "locked":   (0.0, 0.0, 0.5),
    "breath":   (0.06, 0.004, 0.35),    # barely alive tripod/gimbal
    "subtle":   (0.14, 0.012, 0.55),    # gimbal
    "handheld": (0.35, 0.03, 0.8),      # documentary
    "run":      (0.9, 0.08, 1.9),       # chasing the character
}

# --------------------------------------------------------------------------- Rig


@dataclass
class _Seg:
    move: Move
    start: float
    cut: bool


class Rig:
    """Chains Moves, samples them, checks them, writes camera.csv."""

    def __init__(self, fps: float = 30.0, subframes: int = 8, shutter: float = 0.5, default_fov: float = 70.0):
        self.fps = float(fps)
        self.subframes = int(subframes)
        self.shutter = float(shutter)
        self.default_fov = default_fov
        self._segs: List[_Seg] = []
        self._t = 0.0

    # ---- building
    def add(self, move: Move, cut: bool = False) -> "Rig":
        """Append a move.  cut=True declares a hard cut before it (no continuity required, blur never crosses it)."""
        n = round(move.duration * self.fps)
        if n < 1:
            raise ValueError(f"move '{move.name}' is shorter than one frame")
        move = Move(n / self.fps, move.fn, move.name)         # snap to whole frames so cuts land on frame edges
        self._segs.append(_Seg(move, self._t, cut or not self._segs))
        self._t += move.duration
        return self

    @property
    def duration(self) -> float:
        return self._t

    def last_pose(self) -> Dict[str, float]:
        """End pose of the most recently added move (use it to start the next move seamlessly)."""
        return self._segs[-1].move.end_pose()

    @property
    def n_frames(self) -> int:
        return int(round(self._t * self.fps))

    # ---- sampling
    def _eval_at(self, times: Arr) -> Dict[str, Arr]:
        out = {k: np.zeros_like(times) for k in list(FIELDS) + list(EXTRA)}
        owner = np.zeros(times.shape, dtype=int)
        starts = np.array([s.start for s in self._segs])
        for i, s in enumerate(self._segs):
            end = s.start + s.move.duration
            m = (times >= s.start - 1e-9) & ((times < end - 1e-9) | (i == len(self._segs) - 1))
            owner[m] = i
        for i, s in enumerate(self._segs):
            m = owner == i
            if not m.any():
                continue
            tl = np.clip(times[m] - s.start, 0.0, s.move.duration)
            r = s.move.eval(tl / s.move.duration)
            for k in out:
                out[k][m] = r[k]
        return out

    def frame_times(self) -> Arr:
        return np.arange(self.n_frames) / self.fps

    def sample_frames(self) -> Dict[str, Arr]:
        t = self.frame_times()
        d = self._eval_at(t)
        d["t"] = t
        return d

    def sample_rows(self) -> Dict[str, Arr]:
        """Rows for the renderer: frames*subframes samples spread across the shutter window.
        Rows are clamped to the segment that owns the frame, so motion blur never straddles a cut."""
        F, S = self.n_frames, self.subframes
        ft = self.frame_times()
        if S == 1:
            t = ft
            d = self._eval_at(t)
            d["t"] = t
            return d
        offs = (np.arange(S) + 0.5) / S - 0.5                      # [-0.5, 0.5)
        t = (ft[:, None] + offs[None, :] * self.shutter / self.fps).reshape(-1)
        t_eval = t.copy()
        # clamp to owning segment
        for s in self._segs:
            lo, hi = s.start, s.start + s.move.duration
            fm = (ft >= lo - 1e-9) & (ft < hi - 1e-9)
            idx = np.repeat(fm, S)
            t_eval[idx] = np.clip(t[idx], lo, hi - 1e-6)
        d = self._eval_at(t_eval)
        d["t"] = t - (t[0] if t[0] < 0 else 0.0)                    # film clock must start at 0 and stay monotonic
        d["t"] = np.maximum.accumulate(d["t"])
        return d

    def write_csv(self, path: str, height: Optional[int] = None) -> int:
        """height = output height in px (render() passes it): with >= 4 subframes every subframe gets a sub-pixel aim offset
        (Halton 2,3, +-0.5 px), so the motion-blur average is also an 8x anti-aliasing of block edges (v0.8, free)."""
        d = self.sample_rows()
        n = len(d["t"])
        S = self.subframes
        if height and S >= 4:
            def halton(i, b):
                f, r = 1.0, 0.0
                while i > 0:
                    f /= b; r += f * (i % b); i //= b
                return r
            jx = np.array([halton(k + 1, 2) - 0.5 for k in range(S)])
            jy = np.array([halton(k + 1, 3) - 0.5 for k in range(S)])
            deg = d["fov"] / float(height)                       # degrees per pixel at the centre of the frame
            d["yaw"] = d["yaw"] + np.tile(jx, n // S) * deg
            d["pitch"] = d["pitch"] + np.tile(jy, n // S) * deg
        with open(path, "w", newline="") as f:
            f.write("t,x,y,z,yaw,pitch,roll,fov,focus,aperture\n")
            for i in range(n):
                f.write(",".join(f"{d[k][i]:.6f}" for k in ("t", "x", "y", "z", "yaw", "pitch", "roll", "fov", "focus", "aperture")) + "\n")
        return n

    # ---- analysis
    def analyze(self, speed_limit: float = 250.0, ang_limit: float = 240.0) -> Dict:
        """Physical sanity report at frame rate.  Speeds in blocks/s, angles in deg/s."""
        d = self.sample_frames()
        dt = 1.0 / self.fps
        pos = np.stack([d["x"], d["y"], d["z"]], axis=1)
        cuts = {int(round(s.start * self.fps)) for s in self._segs if s.cut}
        vel = np.gradient(pos, dt, axis=0)
        speed = np.linalg.norm(vel, axis=1)
        acc = np.gradient(vel, dt, axis=0)
        jerk = np.gradient(acc, dt, axis=0)
        yawr = np.gradient(unwrap_deg(d["yaw"]), dt)
        pitr = np.gradient(d["pitch"], dt)
        rollr = np.gradient(d["roll"], dt)
        fovr = np.gradient(d["fov"], dt)
        angspeed = np.hypot(yawr, pitr)
        mask = np.ones(len(speed), dtype=bool)
        jmask = np.ones(len(speed), dtype=bool)
        for c in cuts:                                              # ignore frames around hard cuts; a shot may start mid-move
            mask[max(c - 2, 0):c + 3] = False
            jmask[max(c - 2, 0):c + int(0.4 * self.fps) + 1] = False
        warns = []
        # continuity at non-cut joins
        for s_prev, s in zip(self._segs, self._segs[1:]):
            if s.cut:
                continue
            a = s_prev.move.end_pose()
            b = s.move.start_pose()
            dp = math.dist((a["x"], a["y"], a["z"]), (b["x"], b["y"], b["z"]))
            dyaw = abs(((a["yaw"] - b["yaw"] + 180) % 360) - 180)
            dpit = abs(a["pitch"] - b["pitch"])
            if dp > 0.06 or dyaw > 0.6 or dpit > 0.6:
                warns.append(f"join {s_prev.move.name}->{s.move.name} at {s.start:.2f}s is not continuous (pos gap {dp:.2f} blocks, yaw {dyaw:.1f} deg, pitch {dpit:.1f} deg). Declare cut=True or fix the move.")
        if mask.any():
            if speed[mask].max() > speed_limit:
                warns.append(f"peak speed {speed[mask].max():.0f} blocks/s (> {speed_limit:.0f}): fine for an aerial swoop, but check it is intended; at this speed the world reads as a smear unless motion blur (subframes>=8) is on")
            if angspeed[mask].max() > ang_limit:
                t = d["t"][mask][np.argmax(angspeed[mask])]
                warns.append(f"peak angular speed {angspeed[mask].max():.0f} deg/s at {t:.2f}s; fine for a whip (<0.3 s) but nauseating if sustained")
            # sustained high angular speed
            hi = angspeed > ang_limit * 0.6
            run = 0
            for i in range(len(hi)):
                run = run + 1 if hi[i] and mask[i] else 0
                if run > self.fps * 0.5:
                    warns.append(f"angular speed stays above {ang_limit * 0.6:.0f} deg/s for >0.5 s around {d['t'][i]:.2f}s")
                    break
            jm = np.linalg.norm(jerk, axis=1)
            # a smooth move has jerk concentrated at the start/end of eased segments; flag isolated spikes
            med = np.median(jm[mask]) + 1e-6
            spikes = np.where((jm > med * 25) & jmask & (jm > 400))[0]
            if len(spikes):
                warns.append(f"jerk spikes at t={[round(float(d['t'][i]), 2) for i in spikes[:6]]} s (velocity changes abruptly: look for a join or an ease that starts non-zero)")
        return {
            "frames": self.n_frames, "duration": self.duration, "fps": self.fps,
            "max_speed": float(speed[mask].max()) if mask.any() else 0.0,
            "max_angular_speed": float(angspeed[mask].max()) if mask.any() else 0.0,
            "max_roll": float(np.abs(d["roll"]).max()),
            "fov_range": (float(d["fov"].min()), float(d["fov"].max())),
            "warnings": warns,
            "_series": {"t": d["t"], "pos": pos, "speed": speed, "angspeed": angspeed, "yawr": yawr, "pitr": pitr,
                        "rollr": rollr, "fovr": fovr, "roll": d["roll"], "fov": d["fov"], "yaw": d["yaw"], "pitch": d["pitch"],
                        "jerk": np.linalg.norm(jerk, axis=1), "cuts": sorted(cuts)},
        }


# --------------------------------------------------------------------------- helpers shared by moves


def make_aim(aim: Aim, pos_fn: Callable[[Arr], Arr]) -> Callable[[Arr], Tuple[Arr, Arr]]:
    """Turn an aim spec into a function tau -> (yaw, pitch).  aim: point | callable(tau)->point | None (look along path)."""
    if aim is None:
        raise ValueError("aim=None needs a path tangent; use track(..., aim='forward')")
    if callable(aim):
        return lambda tau: look_at(pos_fn(tau), aim(tau))
    pt = v3(aim)
    return lambda tau: look_at(pos_fn(tau), pt[None, :])
