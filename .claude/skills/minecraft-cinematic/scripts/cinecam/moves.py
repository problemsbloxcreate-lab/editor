"""moves: the camera vocabulary.  Every function returns a Move (see camlib).

Think like a cinematographer: choose the PATH (where the lens travels), the AIM (what it looks at), the EASE
(how the speed is distributed over the path) and the FRAMING (fov).  Aim is a fixed point, a callable
tau -> point (the target moves), or 'forward' (look along the path, for fly-throughs).
"""
from __future__ import annotations

import math
from typing import Callable, Optional, Sequence, Tuple, Union

import numpy as np

from .camlib import (EaseSpec, Move, Path3D, Arr, ease_fn, look_at, unwrap_deg, v3)

Num2 = Union[float, Tuple[float, float]]


def _lerp_spec(spec: Num2, e: Callable[[Arr], Arr], tau: Arr) -> Arr:
    if isinstance(spec, (tuple, list)):
        return spec[0] + (spec[1] - spec[0]) * e(tau)
    return np.full_like(tau, float(spec))


def lerp_point(a, b, ease: EaseSpec = "smooth") -> Callable[[Arr], Arr]:
    """Aim target that slides from a to b (a 'pan' done by moving the look-at point)."""
    a, b = v3(a), v3(b)
    e = ease_fn(ease)
    return lambda tau: a[None, :] + (b - a)[None, :] * e(tau)[:, None]


def _aim_angles(aim, path: Path3D, u: Arr, tau: Arr, pos: Arr):
    if isinstance(aim, str) and aim == "forward":
        t = path.tangent(u)
        yaw = np.degrees(np.arctan2(-t[:, 0], t[:, 2]))
        pitch = -np.degrees(np.arctan2(t[:, 1], np.hypot(t[:, 0], t[:, 2])))
        return unwrap_deg(yaw), pitch
    if callable(aim):
        yaw, pitch = look_at(pos, aim(tau))
        return unwrap_deg(yaw), pitch
    yaw, pitch = look_at(pos, v3(aim)[None, :])
    return unwrap_deg(yaw), pitch


def track(points: Sequence[Sequence[float]], aim, T: float, ease: EaseSpec = "smooth",
          fov: Num2 = 70.0, roll: Num2 = 0.0, fov_ease: EaseSpec = "smooth", roll_ease: EaseSpec = "smooth",
          name: str = "track") -> Move:
    """Generic move: spline through points, eased progress along it, aimed at aim."""
    path = Path3D(points)
    e = ease_fn(ease)
    fe, re_ = ease_fn(fov_ease), ease_fn(roll_ease)

    def fn(tau):
        u = e(tau)
        pos = path.at(u)
        yaw, pitch = _aim_angles(aim, path, u, tau, pos)
        return {"x": pos[:, 0], "y": pos[:, 1], "z": pos[:, 2], "yaw": yaw, "pitch": pitch,
                "roll": _lerp_spec(roll, re_, tau), "fov": _lerp_spec(fov, fe, tau)}
    return Move(T, fn, name)


def hold(pos, aim, T: float, fov: float = 70.0, roll: float = 0.0, name: str = "hold") -> Move:
    """Locked-off frame.  Add .with_handheld('breath') so it does not look dead."""
    return track([pos, v3(pos) + 1e-3], aim, T, ease="linear", fov=fov, roll=roll, name=name)


def push_in(pos0, pos1, aim, T: float, ease: EaseSpec = "launch", **kw) -> Move:
    """Dolly toward (or away from, if pos1 is farther) the subject.  'launch' = fast attack, long deceleration."""
    return track([pos0, pos1], aim, T, ease=ease, name=kw.pop("name", "push_in"), **kw)


def truck(pos0, pos1, aim, T: float, ease: EaseSpec = "smooth", **kw) -> Move:
    """Lateral slide while keeping the subject framed: maximum parallax between near and far objects."""
    return track([pos0, pos1], aim, T, ease=ease, name=kw.pop("name", "truck"), **kw)


def crane(pos0, pos1, aim, T: float, arc: float = 0.0, ease: EaseSpec = "launch", **kw) -> Move:
    """Rise/descend with optional outward bulge.  arc>0 lifts the middle (swooping descent: cinematic aerial -> ground)."""
    p0, p1 = v3(pos0), v3(pos1)
    mid = (p0 + p1) / 2 + np.array([0.0, arc, 0.0])
    pts = [p0, mid, p1] if arc else [p0, p1]
    return track(pts, aim, T, ease=ease, name=kw.pop("name", "crane"), **kw)


def orbit(center, radius: Num2, start_deg: float, end_deg: float, height: Num2, T: float,
          ease: EaseSpec = "smooth", look_offset=(0.0, 0.0, 0.0), fov: Num2 = 70.0, roll: Num2 = 0.0,
          name: str = "orbit") -> Move:
    """Circle a subject.  Bearing a: camera = center + r*(sin a, h, -cos a)  =>  a=0 camera NORTH of subject looking south,
    a=90 camera EAST looking west, a=180 camera SOUTH looking north, a=270 camera WEST looking east.
    radius/height/fov/roll may be (from,to) tuples: a spiral in/out gives the classic reveal."""
    c = v3(center)
    lo = v3(look_offset)
    e = ease_fn(ease)

    def fn(tau):
        u = e(tau)
        a = np.radians(start_deg + (end_deg - start_deg) * u)
        r = _lerp_spec(radius, e, tau)
        h = _lerp_spec(height, e, tau)
        pos = np.stack([c[0] + r * np.sin(a), c[1] + h, c[2] - r * np.cos(a)], axis=-1)
        tgt = (c + lo)[None, :]
        yaw, pitch = look_at(pos, tgt)
        return {"x": pos[:, 0], "y": pos[:, 1], "z": pos[:, 2], "yaw": unwrap_deg(yaw), "pitch": pitch,
                "roll": _lerp_spec(roll, ease_fn("smooth"), tau), "fov": _lerp_spec(fov, ease_fn("smooth"), tau)}
    return Move(T, fn, name)


def pan(pos, angles0: Tuple[float, float], angles1: Tuple[float, float], T: float, ease: EaseSpec = "smooth",
        fov: Num2 = 70.0, roll: Num2 = 0.0, name: str = "pan") -> Move:
    """Camera fixed in space, rotating from (yaw0,pitch0) to (yaw1,pitch1).  Use the shortest way: yaw is not wrapped."""
    p = v3(pos)
    e = ease_fn(ease)

    def fn(tau):
        u = e(tau)
        return {"x": np.full_like(tau, p[0]), "y": np.full_like(tau, p[1]), "z": np.full_like(tau, p[2]),
                "yaw": angles0[0] + (angles1[0] - angles0[0]) * u, "pitch": angles0[1] + (angles1[1] - angles0[1]) * u,
                "roll": _lerp_spec(roll, ease_fn("smooth"), tau), "fov": _lerp_spec(fov, ease_fn("smooth"), tau)}
    return Move(T, fn, name)


def whip(pos, angles0: Tuple[float, float], angles1: Tuple[float, float], T: float = 0.22, fov: Num2 = 70.0, name: str = "whip") -> Move:
    """Whip pan: slow start, brutal peak speed, decelerated landing.  Pair with a hard cut mid-whip and a second whip that
    continues in the same direction for an invisible transition (see recipes).  Needs subframes>=8 for real blur."""
    return pan(pos, angles0, angles1, T, ease="whip", fov=fov, name=name)


def dolly_zoom(pos0, pos1, subject, T: float, fov0: float = 60.0, ease: EaseSpec = "smooth", name: str = "dolly_zoom") -> Move:
    """Vertigo effect: dolly while changing fov so the subject keeps the same size and the background stretches."""
    s = v3(subject)
    p0, p1 = v3(pos0), v3(pos1)
    d0 = np.linalg.norm(s - p0)
    k = d0 * math.tan(math.radians(fov0) / 2)
    e = ease_fn(ease)

    def fn(tau):
        u = e(tau)
        pos = p0[None, :] + (p1 - p0)[None, :] * u[:, None]
        d = np.linalg.norm(s[None, :] - pos, axis=1)
        yaw, pitch = look_at(pos, s[None, :])
        return {"x": pos[:, 0], "y": pos[:, 1], "z": pos[:, 2], "yaw": unwrap_deg(yaw), "pitch": pitch,
                "roll": np.zeros_like(tau), "fov": np.degrees(2 * np.arctan(k / d))}
    return Move(T, fn, name)


def through(points: Sequence[Sequence[float]], T: float, ease: EaseSpec = "smooth", fov: Num2 = 75.0,
            bank: float = 0.35, lag: float = 0.22, look_ahead: Optional[float] = None, name: str = "through") -> Move:
    """Fly through a corridor of waypoints like a drone: looks along the path, banks into turns, aim lags a little."""
    m = track(points, "forward", T, ease=ease, fov=fov, name=name)
    if lag > 0:
        m = m.with_lag(lag)
    if bank:
        m = m.with_bank(bank)
    return m


def chase(subject_points: Sequence[Sequence[float]], behind: float, height: float, T: float, ease: EaseSpec = "linear",
          side: float = 0.0, aim_height: float = 1.0, fov: Num2 = 75.0, lag: float = 0.3, name: str = "chase") -> Move:
    """Follow a subject that travels along subject_points: camera sits behind/above it and looks at it."""
    sp = Path3D(subject_points)
    e = ease_fn(ease)

    def fn(tau):
        u = e(tau)
        s = sp.at(u)
        t = sp.tangent(u)
        back = -t.copy()
        back[:, 1] = 0
        n = np.linalg.norm(back, axis=1, keepdims=True)
        back = back / np.where(n < 1e-6, 1, n)
        right = np.stack([-back[:, 2], np.zeros(len(tau)), back[:, 0]], axis=-1)
        pos = s + back * behind + right * side + np.array([0, height, 0.0])
        yaw, pitch = look_at(pos, s + np.array([0, aim_height, 0.0]))
        return {"x": pos[:, 0], "y": pos[:, 1], "z": pos[:, 2], "yaw": unwrap_deg(yaw), "pitch": pitch,
                "roll": np.zeros_like(tau), "fov": _lerp_spec(fov, ease_fn("smooth"), tau)}
    m = Move(T, fn, name)
    return m.with_lag(lag) if lag > 0 else m


def parallax_pass(pos0, pos1, aim, T: float, occluder_note: str = "", ease: EaseSpec = "smooth", **kw) -> Move:
    """A truck whose purpose is to slide PAST near foreground objects (leaves, a tree trunk, a pillar).  Place the camera
    path so it passes within 1-3 blocks of the occluder: the foreground blurs/slides and the subject is revealed behind it."""
    return truck(pos0, pos1, aim, T, ease=ease, name=kw.pop("name", "parallax_pass"), **kw)


def orbit_from(pose: dict, center, sweep_deg: float, T: float, radius_end: Optional[float] = None, height_end: Optional[float] = None,
               ease: EaseSpec = "smooth", look_offset=(0.0, 0.0, 0.0), fov: Optional[Num2] = None, roll: Num2 = 0.0,
               name: str = "orbit_from") -> Move:
    """Orbit that STARTS exactly at `pose` (e.g. rig.last_pose()) so the join with the previous move is seamless.
    sweep_deg > 0 sweeps the bearing in the positive direction (see orbit for the bearing convention)."""
    c = v3(center)
    dx, dy, dz = pose["x"] - c[0], pose["y"] - c[1], pose["z"] - c[2]
    r0 = math.hypot(dx, dz)
    a0 = math.degrees(math.atan2(dx, -dz))
    return orbit(c, (r0, radius_end if radius_end is not None else r0), a0, a0 + sweep_deg,
                 (dy, height_end if height_end is not None else dy), T, ease=ease, look_offset=look_offset,
                 fov=fov if fov is not None else pose["fov"], roll=roll, name=name)


def from_pose(pose: dict, points_after: Sequence[Sequence[float]], aim, T: float, **kw) -> Move:
    """track() whose path begins at `pose` (e.g. rig.last_pose()) and continues through points_after."""
    return track([(pose["x"], pose["y"], pose["z"])] + [tuple(p) for p in points_after], aim, T, **kw)
