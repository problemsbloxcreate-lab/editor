"""acts v2 (21/10/2026): blocking, expressive acting and camera placement for short cutaway shots inside a rebuilt set.

Feedback that shaped v2 (Matheus, 21/10/2026, see references/enquadramento.md):
  * NEVER film a character in PROFILE — front or ~45° (3/4); back is to be avoided too (less than profile).  -> blocking is "open to
    the camera" (bodies cheat toward the lens, heads do the looking) and every camera is placed RELATIVE TO THE CHARACTER'S FACING
    (azimuth `az`: 0 = straight in front, 30-45 = three-quarter), never at fixed world coordinates.  framing.check_shot verifies it.
  * Animate MORE: big, asymmetric arm gestures, body lean/bounce, head tilts, anticipation -> overshoot -> follow-through
    (refs: youtube shorts f_eC3Mt1XFY, MBKcIm7IsJk).
  * NEVER a prop that is not glued to the right limb: props are computed from the posed model every frame (cinecam.kin) and
    collision-checked (self.checks -> auto.py refuses the shot).

    st = Stage(sb, T=3.0)                                    # audience = 0: the cameras live on the +z side, actors face +z
    st.add("problems", 0, 0); st.add("stick", -2, 0.4, face="problems")   # stick cheats: body <=35° off the lens, head looks
    st.talk("problems", 0.1, 2.0); st.present("stick", 0.6); st.celebrate("*", 2.1)
    rig = cam_hero_low(st, 3.0)                              # placed from the cast's facing, not from world axes

Conventions (calibrated 21/10 in a front still): actor yaw 0 faces +z; head_x<0 looks UP, head_z tilts; RIGHT arm: x=-90 forward,
-180 up, z+ = out to the side (T at +90), y+ = swings OUT, y- = swings IN across the chest; LEFT arm mirrors (z-, y- out, y+ in);
lean>0 leans BACK; roll tilts the whole body sideways; hop in blocks.
"""
from __future__ import annotations

import math
from typing import Dict, List, Optional, Sequence, Union

import numpy as np

from .actors import Actor, Anim, Mob, Prop, POSE, tube
from .camlib import Rig
from .kin import KActor
from .moves import track, crane, dolly_zoom, lerp_point
from .turma import skin as _skin

V = np.asarray
HEAD_Y_SIGN = 1.0          # head_y uses Minecraft netHeadYaw sign (target yaw - body yaw); verified in still 21/10/2026
CHEAT = 35.0               # max body turn away from the lens when a character faces someone/something (theatre "cheat out")
BODY_K = 0.45              # the body takes 45 % of the target's angle off the lens axis ...
FACE_MAX = 50.0            # ... the face goes at most 50° off the lens (beyond 60° = profile = forbidden) ...
HEAD_MAX = 40.0            # ... and the head alone turns at most 40° from the body (enquadramento.md §3a)
PRESENT_BEYOND = 110.0     # a target more than this off the lens axis is NOT looked at: presenter pose instead


def yaw_to(frm, to) -> float:
    d = V(to, float) - V(frm, float)
    return math.degrees(math.atan2(-d[0], d[2]))


def _wrap(a: float) -> float:
    return (a + 180.0) % 360.0 - 180.0


def _yaw_vec(yaw: float) -> np.ndarray:
    y = math.radians(yaw)
    return np.array([-math.sin(y), 0.0, math.cos(y)])


def _rot_y(v: np.ndarray, deg: float) -> np.ndarray:
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return np.array([v[0] * c + v[2] * s, v[1], -v[0] * s + v[2] * c])


class Stage:
    """Cast + beats on a set.  Times in seconds of the shot (0..T).  audience = the yaw a character has when facing the cameras."""

    def __init__(self, sb, T: float, audience: float = 0.0):
        self.sb, self.T, self.audience = sb, float(T), float(audience)
        self.actors: Dict[str, Actor] = {}
        self.yaw: Dict[str, float] = {}
        self.mobs: List[Mob] = []
        self.props: List[Prop] = []
        self.beams: list = []
        self.water = None
        self.checks: list = []           # (label, fn() -> [problems]) run by auto.py before rendering
        self.allow_back: set = set()     # characters that may be seen from behind in this shot (over-the-shoulder, walking away)

    # ---- cast
    def add(self, who: str, dx: float, dz: float, yaw: Optional[float] = None, face: Optional[str] = None, name: Optional[str] = None,
            item: Optional[str] = None, scale: float = 1.0, idle: bool = True, dy: float = 0.0, hat: bool = False,
            energy: float = 1.0, cheat: bool = True) -> Actor:
        """face: 'camera' (default) | actor | mark | point.  With cheat=True the body turns at most CHEAT° away from the lens and the
        head completes the look (open blocking); cheat=False only with a reason (the camera must then come round to that side)."""
        name = name or who
        pos = self.sb.feet(dx, dz, dy)
        target = None
        if yaw is None:
            if face in (None, "camera"):
                yaw = self.audience
            else:
                target = self.where(face)
                yaw = yaw_to(pos, target)
                if cheat:
                    yaw = self._cheat_body(yaw)
        a = Actor(name, _skin(who), pos, yaw=yaw, item=item, hat=hat)
        if item:
            a.key(0.0, item=1.0)                    # the item channel is its SCALE (default 0 = hidden)
        if scale != 1.0:
            a.key(0.0, sx=scale, sy=scale, sz=scale)
        if idle:
            a.idle(0.0, self.T + 1.0, amp=1.5 * energy)
        self.actors[name], self.yaw[name] = a, yaw
        self.sb.keep_free(dx, dz, 1.3)
        if target is not None:
            self.look(name, face, 0.0, dur=0.01)
        return a

    def _cheat(self, yaw: float) -> float:
        rel = max(-CHEAT, min(CHEAT, _wrap(yaw - self.audience)))
        return self.audience + rel

    def _cheat_body(self, yaw_target: float) -> float:
        d = _wrap(yaw_target - self.audience)
        return self.audience + max(-CHEAT, min(CHEAT, BODY_K * d))

    def get(self, who: Union[str, Sequence[str]]) -> List[str]:
        if who == "*":
            return list(self.actors)
        return [who] if isinstance(who, str) else list(who)

    def k(self, name: str) -> KActor:
        return KActor(self.actors[name])

    def pos(self, name: str, t: float = 0.0) -> np.ndarray:
        r = self.actors[name].at(np.array([t]))[0]
        return r[:3].copy()

    def head(self, name: str, t: float = 0.0) -> np.ndarray:
        return self.k(name).head_center(t)

    def where(self, target) -> np.ndarray:
        """'camera' | actor name | set mark | (dx, dz) | (dx, dy, dz) | world point (len 3 with big values)."""
        if isinstance(target, str):
            if target in self.actors:
                return self.head(target)
            if target in self.sb.marks:
                return self.sb.marks[target]
            if target == "camera":
                c = self.center() if self.actors else self.sb.point(0, 0, 0)
                return c + _yaw_vec(self.audience) * 8 + [0, 1.5, 0]
            raise KeyError(f"unknown target {target}")
        if isinstance(target, np.ndarray):              # numpy = world point (lists/tuples = local set coordinates)
            return target.astype(float)
        t = list(target)
        if len(t) == 2:
            return self.sb.point(t[0], 0.5, t[1])
        if max(abs(v) for v in t) > 200:
            return V(t, float)
        return self.sb.point(t[0], t[1], t[2])

    def center(self, names: Optional[Sequence[str]] = None, t: float = 0.0) -> np.ndarray:
        names = names or list(self.actors)
        return np.mean([self.pos(n, t) for n in names], axis=0)

    # ---- key helpers
    @staticmethod
    def _keyval(a: Actor, ch: str, t: float) -> float:
        """Value of a channel at t from KEYS only (no wobble/idle), to start a new move from where the last one left it."""
        wob, a.wobbles = a.wobbles, []
        try:
            return float(a.at(np.array([t]))[0][POSE[ch]])
        finally:
            a.wobbles = wob

    def _move(self, a: Actor, t: float, dur: float, ease: str = "out_back", **vals):
        """From the current key values at t to vals at t+dur."""
        a.key(t, **{c: self._keyval(a, c, t) for c in vals})
        a.key(t + dur, ease=ease, **vals)

    def _pose(self, n: str, t: float, dur: float, pose: dict, anticip: Optional[dict] = None, hold_wobble: Sequence = (),
              rest: Optional[dict] = None, att: float = 0.16, ease: str = "out_back"):
        """Gesture envelope: (anticipation ~0.09 s) -> pose with overshoot -> held with life -> release (follow-through)."""
        a = self.actors[n]
        t0 = t
        if anticip:
            self._move(a, t0, 0.09, "out", **anticip)
            t0 += 0.09
        self._move(a, t0, att, ease, **pose)
        hold_end = t + max(dur, att + 0.1)
        a.key(hold_end, **pose)
        for ch, amp, f in hold_wobble:
            a.wobble(ch, t0 + att, hold_end, amp, f, ramp=0.12)
        rest = rest if rest is not None else {c: 0.0 for c in pose}
        if hold_end < self.T + 0.4:
            a.key(hold_end + 0.32, ease="smooth", **rest)
        return self

    # ---- blocking beats
    def turn(self, who, at, t: float, dur: float = 0.35, cheat: bool = True):
        for n in self.get(who):
            y = yaw_to(self.pos(n, t), self.where(at))
            if cheat:
                y = self._cheat_body(y)
            y = self.yaw[n] + _wrap(y - self.yaw[n])
            self.actors[n].key(t, yaw=self.yaw[n]).key(t + dur, ease="out", yaw=y)
            self.yaw[n] = y
        return self

    def look(self, who, at, t: float, dur: float = 0.3, hold_s: Optional[float] = None):
        """Cheated look (enquadramento.md §3a): the FACE turns toward the target but at most FACE_MAX° off the lens, the head
        at most HEAD_MAX° from the body; a target more than PRESENT_BEYOND° off the lens is not looked at (use present_to)."""
        for n in self.get(who):
            a = self.actors[n]
            h, p = self.head(n, t), self.where(at)
            d = _wrap(yaw_to(h, p) - self.audience)
            if abs(d) > PRESENT_BEYOND:
                continue
            face = self.audience + max(-FACE_MAX, min(FACE_MAX, d))
            rel = max(-HEAD_MAX, min(HEAD_MAX, _wrap(face - self.yaw[n])))
            dd = p - h
            pitch = max(-35, min(30, -math.degrees(math.atan2(dd[1], math.hypot(dd[0], dd[2])))))
            self._move(a, t, dur, "out", head_y=HEAD_Y_SIGN * rel, head_x=pitch)
            if hold_s:
                a.key(t + dur + hold_s, head_y=HEAD_Y_SIGN * rel, head_x=pitch).key(t + dur + hold_s + dur, ease="smooth", head_y=0, head_x=0)
        return self

    def present_to(self, who, at, t: float, dur: float = 1.2):
        """Presenter pose (replaces turning to point at something behind / far off-axis): body stays open to the lens, the arm on
        the object's side opens diagonally back-out toward it, head 20° toward it (§4.1-13)."""
        for n in self.get(who):
            p = self.where(at)
            d = _wrap(yaw_to(self.pos(n, t), p) - self.yaw[n])
            on_left = d < 0                     # yaw grows toward the character's RIGHT (facing +z: -x); calibrated with look() 21/10
            arm = dict(larm_x=-62, larm_z=-68) if on_left else dict(rarm_x=-62, rarm_z=68)
            zc = "larm_z" if on_left else "rarm_z"
            self._pose(n, t, dur, dict(arm, head_y=HEAD_Y_SIGN * (20 if on_left else -20), lean=-3),
                       anticip=dict(lean=3), hold_wobble=[(zc, -6 if on_left else 6, 1.8)])
        return self

    def walk(self, who, to, t0: float, t1: float, run: bool = False, via: Sequence = ()):
        """Walk/run along (via..., to) in local (dx, dz).  Body faces the way it walks (the camera must then be in FRONT of the
        motion: cam_truck(follow=...)), legs/arms swing big, body bobs."""
        for n in self.get(who):
            a = self.actors[n]
            p0 = self.pos(n, t0)
            pts = [p0] + [self.sb.feet(*q) for q in list(via) + [to]]
            seg = [np.linalg.norm((pts[i + 1] - pts[i])[[0, 2]]) for i in range(len(pts) - 1)]
            L = max(sum(seg), 1e-6)
            tt, acc = [t0], 0.0
            for s in seg:
                acc += s
                tt.append(t0 + (t1 - t0) * acc / L)
            for i in range(1, len(pts)):
                y = yaw_to(pts[i - 1], pts[i])
                y = self.yaw[n] + _wrap(y - self.yaw[n])
                a.key(max(0.0, tt[i - 1] - 0.12), yaw=self.yaw[n]).key(tt[i - 1] + 0.1, ease="out", yaw=y)
                self.yaw[n] = y
                e = "smooth" if len(pts) == 2 else ("in" if i == 1 else ("out" if i == len(pts) - 1 else "linear"))
                a.key(tt[i - 1], x=pts[i - 1][0], z=pts[i - 1][2]).key(tt[i], ease=e, x=pts[i][0], z=pts[i][2])
            v = L / max(t1 - t0, 1e-3)
            amp, cyc = (60.0, 1.7) if run else (42.0, 1.25)
            f = max(1.3, v / cyc)
            ramp = min(0.25, (t1 - t0) / 4)
            a.wobble("rleg_x", t0, t1, amp, f, ramp=ramp).wobble("lleg_x", t0, t1, amp, f, phase=math.pi, ramp=ramp)
            a.wobble("rarm_x", t0, t1, amp * 1.1, f, phase=math.pi, ramp=ramp).wobble("larm_x", t0, t1, amp * 1.1, f, ramp=ramp)
            a.wobble("hop", t0, t1, 0.05, 2 * f, phase=-math.pi / 2, ramp=ramp)                     # bob on every step
            a.wobble("roll", t0, t1, 3.0 if run else 2.0, f, ramp=ramp)                              # weight shifts side to side
            L = -12 if run else -4
            self._move(a, t0, 0.2, "out", lean=L)
            a.key(t1 - 0.05, lean=L).key(t1 + 0.25, ease="out_back", lean=0)
        return self

    def hop(self, who, t: float, h: float = 0.35, n: int = 1, gap: float = 0.45):
        for name in self.get(who):
            a = self.actors[name]
            for k in range(n):
                tk = t + k * gap
                up = 0.16 + h * 0.25
                a.key(tk - 0.08, sy=1.0, sx=1.0, sz=1.0).key(tk, ease="out", sy=0.92, sx=1.04, sz=1.04)        # crouch (anticipation)
                a.key(tk + 0.06, ease="out", sy=1.05, sx=0.98, sz=0.98)                                      # stretch on take-off
                a.key(tk + 2 * up, sy=1.0, sx=1.0, sz=1.0).key(tk + 2 * up + 0.07, ease="out", sy=0.88, sx=1.06, sz=1.06)
                a.key(tk + 2 * up + 0.25, ease="out_back", sy=1.0, sx=1.0, sz=1.0)                        # landing squash
                a.key(tk, hop=0.0).key(tk + up, ease="out", hop=h).key(tk + 2 * up, ease="in", hop=0.0)
                a.wobble("lean", tk + 2 * up, tk + 2 * up + 0.35, 3.0, 6.0, decay=8)                 # landing follow-through
        return self

    # ---- expressive gestures (see references/enquadramento.md § atuação)
    def present(self, who, t: float, dur: float = 1.0, energy: float = 1.0):
        """Both arms open toward the lens ("olha isso!"): the most used pose in the refs."""
        e = energy
        for n in self.get(who):
            self._pose(n, t, dur, dict(rarm_x=-80 * e, rarm_y=24, larm_x=-80 * e, larm_y=-24, lean=-7 * e, head_x=-5, head_z=6),
                       anticip=dict(rarm_x=12, larm_x=12, lean=4), hold_wobble=[("rarm_x", 5, 2.2), ("larm_x", 5, 2.2)],
                       rest=dict(rarm_x=0, rarm_y=0, larm_x=0, larm_y=0, lean=0, head_x=0, head_z=0))
        return self

    def wave(self, who, t: float, dur: float = 1.2, energy: float = 1.0):
        for n in self.get(who):
            a = self.actors[n]
            self._pose(n, t, dur, dict(rarm_x=-168, rarm_z=32, larm_z=-14, head_z=9), anticip=dict(rarm_x=10),
                       hold_wobble=[("rarm_z", 26 * energy, 3.2), ("roll", 2.5, 1.6)],
                       rest=dict(rarm_x=0, rarm_z=0, larm_z=0, head_z=0))
        return self

    def point(self, who, at, t: float, dur: float = 1.2):
        """Right arm points at a target (IK: the arm really points there); body cheats toward it, head looks."""
        for n in self.get(who):
            self.turn(n, at, t, 0.22)
            self.look(n, at, t, 0.25)
            k, p = self.k(n), self.where(at)
            x, z, _ = k.arm_aim(t + 0.3, p, "R")
            self._pose(n, t + 0.05, dur, dict(rarm_x=x, rarm_z=z, lean=-5), anticip=dict(rarm_x=8), hold_wobble=[("rarm_x", 3, 2.5)],
                       rest=dict(rarm_x=0, rarm_z=0, lean=0))
        return self

    def point_cam(self, who, t: float, dur: float = 1.0):
        """Points straight at the lens and leans into it ("você!")."""
        return self.point(who, "camera", t, dur)

    def hands_together(self, who, t: float, dur: float = 1.0):
        """Hands joined in front of the chest (cute / pleading / plotting)."""
        for n in self.get(who):
            self._pose(n, t, dur, dict(rarm_x=-62, rarm_y=-34, larm_x=-62, larm_y=34, head_z=10), hold_wobble=[("hop", 0.03, 3.0)],
                       rest=dict(rarm_x=0, rarm_y=0, larm_x=0, larm_y=0, head_z=0))
        return self

    def _hand_to(self, n: str, t: float, local_head_or_body: tuple, part: str, side: str = "R"):
        k = self.k(n)
        p = k.point(t, part, local_head_or_body)
        x, z, _ = k.arm_aim(t, p, side, local=(-1 if side == "R" else 1, 8.5, 0))
        return x, z

    def facepalm(self, who, t: float, dur: float = 1.0):
        for n in self.get(who):
            self._move(self.actors[n], t, 0.18, "out", head_x=14, lean=-4)
            x, z = self._hand_to(n, t + 0.18, (0, -4.5, -6.0), "head")
            self._pose(n, t, dur, dict(rarm_x=x, rarm_z=z), hold_wobble=[("head_y", 6, 2.0)], rest=dict(rarm_x=0, rarm_z=0))
            self.actors[n].key(t + dur + 0.3, ease="smooth", head_x=0, lean=0)
        return self

    def think(self, who, t: float, dur: float = 1.2):
        for n in self.get(who):
            self._move(self.actors[n], t, 0.25, "out", head_x=-10, head_z=10)
            x, z = self._hand_to(n, t + 0.25, (0, -0.4, -5.0), "head")
            self._pose(n, t, dur, dict(rarm_x=x, rarm_z=z, larm_x=-38, larm_y=36), hold_wobble=[("head_z", 3, 0.8)],
                       rest=dict(rarm_x=0, rarm_z=0, larm_x=0, larm_y=0))
            self.actors[n].key(t + dur + 0.3, ease="smooth", head_x=0, head_z=0)
        return self

    def shrug(self, who, t: float, dur: float = 0.8):
        for n in self.get(who):
            self._pose(n, t, dur, dict(rarm_x=-28, rarm_z=42, larm_x=-28, larm_z=-42, head_z=14, head_x=-6),
                       anticip=dict(hop=0.0), rest=dict(rarm_x=0, rarm_z=0, larm_x=0, larm_z=0, head_z=0, head_x=0))
            self.hop(n, t + 0.02, h=0.08)
        return self

    def celebrate(self, who, t: float, dur: float = 1.2, hops: int = 2):
        """Asymmetric V (main arm higher, the other 0.1 s late), shaking 3.6 Hz, head back, hops with squash (§4.2 alegria);
        neighbours mirror each other and start 0.15 s apart (anti-twinning)."""
        for i, n in enumerate(self.get(who)):
            tt = t + 0.15 * i
            m = 1 if i % 2 == 0 else -1
            G = dict(rarm_x=-156, rarm_z=36) if m == 1 else dict(larm_x=-156, larm_z=-36)
            S = dict(larm_x=-132, larm_z=-30) if m == 1 else dict(rarm_x=-132, rarm_z=30)
            gz, sz = ("rarm_z", "larm_z") if m == 1 else ("larm_z", "rarm_z")
            self._pose(n, tt, dur, dict(G, head_x=-16, lean=6), anticip=dict(lean=-6),
                       hold_wobble=[(gz, 18 * m, 3.6), ("head_z", 10, 1.8)], rest=dict({c: 0.0 for c in G}, head_x=0, lean=0))
            self._pose(n, tt + 0.1, dur - 0.1, S, hold_wobble=[(sz, -14 * m, 3.6)], rest={c: 0.0 for c in S})
            self.hop(n, tt + 0.12, h=0.42, n=hops, gap=0.5)
        return self

    def excited(self, who, t0: float, t1: float):
        """Pumping fists + bouncing (vibrating with joy)."""
        for n in self.get(who):
            a = self.actors[n]
            self._move(a, t0, 0.15, "out", rarm_x=-70, larm_x=-70, rarm_z=12, larm_z=-12, head_x=-8)
            a.wobble("rarm_x", t0 + 0.15, t1, 42, 3.4, ramp=0.1).wobble("larm_x", t0 + 0.15, t1, 42, 3.4, phase=math.pi, ramp=0.1)
            k = t0 + 0.1
            while k < t1 - 0.2:
                self.hop(n, k, h=0.16)
                k += 0.36
            a.key(t1, rarm_x=-70, larm_x=-70).key(t1 + 0.3, ease="smooth", rarm_x=0, larm_x=0, rarm_z=0, larm_z=0, head_x=0)
        return self

    def laugh(self, who, t0: float, t1: float):
        for n in self.get(who):
            a = self.actors[n]
            k = self.k(n)
            xr, zr = self._hand_to(n, t0, (0, 8, -3.5), "body", "R")
            xl, zl = self._hand_to(n, t0, (0, 8, -3.5), "body", "L")
            self._move(a, t0, 0.2, "out_back", lean=12, head_x=-20, rarm_x=xr, rarm_z=zr, larm_x=xl, larm_z=zl)
            a.wobble("lean", t0 + 0.2, t1, 4.0, 7.0, ramp=0.1).wobble("head_x", t0 + 0.2, t1, 5.0, 7.0, ramp=0.1)
            a.key(t1, lean=12, head_x=-20, rarm_x=xr, rarm_z=zr, larm_x=xl, larm_z=zl)
            a.key(t1 + 0.35, ease="smooth", lean=0, head_x=0, rarm_x=0, rarm_z=0, larm_x=0, larm_z=0)
        return self

    def angry(self, who, t: float, dur: float = 1.2):
        for n in self.get(who):
            self._pose(n, t, dur, dict(lean=-11, head_x=12, rarm_x=14, rarm_z=13, larm_x=14, larm_z=-13), anticip=dict(lean=4),
                       hold_wobble=[("roll", 2.5, 9.0), ("rarm_z", 4, 9.0), ("larm_z", -4, 9.0)],
                       rest=dict(lean=0, head_x=0, rarm_x=0, rarm_z=0, larm_x=0, larm_z=0))
            self.hop(n, t + 0.05, h=0.1)
        return self

    def shock(self, who, t: float, hold_s: float = 1.0):
        """Startle (§4.2 susto): freeze 0.05 s -> jolt back (lean +16, hop 0.2, a step back), main arm up-out, the other smaller,
        8 Hz tremble that decays; moving hold."""
        for n in self.get(who):
            a = self.actors[n]
            self._pose(n, t + 0.05, hold_s + 0.1, dict(lean=16, rarm_x=-62, rarm_z=82, larm_x=-28, larm_z=-52, head_x=-15, head_z=8),
                       att=0.12, rest=dict(lean=0, rarm_x=0, rarm_z=0, larm_x=0, larm_z=0, head_x=0, head_z=0))
            for ch, amp in (("lean", 2.6), ("rarm_z", 5), ("larm_z", -4), ("head_x", 2.5)):
                a.wobble(ch, t + 0.17, t + 0.17 + hold_s, amp, 8.0, decay=4.5, ramp=0.05)
            self.hop(n, t + 0.05, h=0.2)
            back = -_yaw_vec(self.yaw[n]) * 0.3
            p = self.pos(n, t)
            a.key(t + 0.05, x=p[0], z=p[2]).key(t + 0.3, ease="out", x=p[0] + back[0], z=p[2] + back[2])
        return self

    def nod(self, who, t: float, n: int = 2):
        for name in self.get(who):
            a = self.actors[name]
            for k in range(n):
                tk = t + k * 0.3
                a.key(tk, head_x=0).key(tk + 0.12, ease="out", head_x=16).key(tk + 0.28, ease="smooth", head_x=0)
        return self

    def headshake(self, who, t: float, dur: float = 0.8):
        for name in self.get(who):
            self.actors[name].wobble("head_y", t, t + dur, 26, 3.0, ramp=0.1)
        return self

    def lean_in(self, who, t: float, dur: float = 1.0):
        for n in self.get(who):
            self._pose(n, t, dur, dict(lean=-15, head_z=9, head_x=-6), rest=dict(lean=0, head_z=0, head_x=0))
        return self

    def talk(self, who, t0: float, t1: float, energy: float = 1.0, emphatic: bool = False):
        """Speaking (§4.2 fala): the main arm OPENS (z, reads from the front) and beats ±15° at ~1.8 Hz, the other arm smaller and
        late; the main arm switches every ~1.2 s; head nods on stresses (~3 Hz) + slow turns and tilts; body sways and leans in.
        emphatic=True: both arms big (argument)."""
        e = energy * (1.25 if emphatic else 1.0)
        rest_all = dict(rarm_x=0, rarm_y=0, rarm_z=0, larm_x=0, larm_y=0, larm_z=0)
        for i, n in enumerate(self.get(who)):
            a = self.actors[n]
            self._move(a, t0, 0.2, "out", lean=-4 * e - (4 if emphatic else 0))
            k, j = t0, i
            while k < t1 - 0.2:
                seg_end = min(t1, k + 1.2)
                if j % 2 == 0:
                    G = dict(rarm_x=-48 * e, rarm_z=24 * e, rarm_y=10); S = dict(larm_x=-16 * e, larm_z=-10 * e)
                    gz, szc, sg = "rarm_z", "larm_z", 1
                else:
                    G = dict(larm_x=-48 * e, larm_z=-24 * e, larm_y=-10); S = dict(rarm_x=-16 * e, rarm_z=10 * e)
                    gz, szc, sg = "larm_z", "rarm_z", -1
                if emphatic:
                    S = {c: v * 3.0 for c, v in S.items()}
                full = dict(rest_all); full.update(G); full.update(S)
                self._move(a, k, 0.15, "out_back", **full)
                a.wobble(gz, k + 0.15, seg_end, 15 * e * sg, 1.8, ramp=0.1)
                a.wobble(szc, k + 0.25, seg_end, -6 * e * sg, 1.8, phase=1.0, ramp=0.1)
                a.key(seg_end, **full)
                j += 1
                k = seg_end
            a.wobble("head_x", t0, t1, 7 * e, 3.0, ramp=0.15).wobble("head_y", t0, t1, 8 * e, 0.9, ramp=0.2)
            a.wobble("head_z", t0, t1, 5 * e, 0.6, ramp=0.2).wobble("yaw", t0, t1, 6.0, 0.7, ramp=0.2)
            a.wobble("hop", t0, t1, 0.02 * e, 1.8, phase=-math.pi / 2, ramp=0.2)
            a.key(t1 + 0.3, ease="smooth", lean=0, **rest_all)
        return self

    def fall(self, who, t: float, back: bool = True):
        for n in self.get(who):
            a = self.actors[n]
            L = 90 if back else -90
            a.key(t, lean=0).key(t + 0.32, ease="in", lean=L).key(t + 0.42, ease="out", lean=L * 0.92).key(t + 0.55, ease="smooth", lean=L)
            a.key(t, rarm_z=0, larm_z=0).key(t + 0.3, ease="out", rarm_z=60, larm_z=-60)
        return self

    # ---- props glued to limbs
    def drink(self, who, src="pond", t0: float = 0.0, t1: Optional[float] = None, belly: bool = True, gulps: int = 5,
              r0: float = 5.3, step: float = 0.22, side: str = "R"):
        """Drinking with a STRAIGHT straw, glued: it leaves the FRONT of the mouth, goes down to the water IN FRONT of the drinker and
        passes through the closed hand (arm solved by IK at 30 Hz, so the hand follows the straw as the head nods).  The drinker
        turns to face the nearest water in front; the water belly (v0.7) grows a notch per gulp.  A clearance check is registered:
        the straw may touch only the mouth (end) and the gripping hand."""
        t1 = self.T if t1 is None else t1
        for n in self.get(who):
            a, k = self.actors[n], self.k(n)
            feet = self.pos(n, t0)
            tip = self._water_in_front(n, t0)
            want = _wrap(yaw_to(feet, tip) - self.yaw[n])
            if abs(want) > 8:
                self.turn(n, tip, max(0.0, t0 - 0.25), 0.2, cheat=False)
            arm = "rarm" if side == "R" else "larm"
            a.wobbles = [w for w in a.wobbles if not w[0].startswith(arm)]          # nothing may pull the hand off the straw
            self._move(a, t0, 0.18, "out", head_x=12)
            gt = list(np.linspace(t0 + 0.2, t1 - 0.35, gulps))
            for tg in gt:
                a.key(tg, head_x=12).key(tg + 0.12, ease="out", head_x=18).key(tg + 0.38, head_x=12)
            if belly:
                R = r0
                a.key(0.0, vbelly=R, vbelly_out=R - 2.0, vbelly_y=7.2, vbelly_shine=0.85, vbelly_jig=0.0, vbelly_wave=0.2)
                for tg in gt:
                    a.key(tg, vbelly=R, vbelly_out=R - 2.0, vbelly_jig=0.0, vbelly_wave=0.2)
                    R += step
                    a.key(tg + 0.10, ease="out", vbelly=R + 0.25, vbelly_out=R - 1.75, vbelly_jig=-0.10, vbelly_wave=0.5)
                    a.key(tg + 0.30, ease="out_back", vbelly=R, vbelly_out=R - 2.0, vbelly_jig=0.0, vbelly_wave=0.25)
                    a.wobble("vbelly_jig", tg + 0.10, tg + 0.75, 0.06, 6.5, decay=5.0)
            # hand on the straw: grip point = where the straw is one arm-length from the shoulder (bisection), IK every 1/30 s
            loc = (-1 if side == "R" else 1, 8.5, 0)
            reach = np.linalg.norm(np.array(loc)) / 16.0
            ts = np.arange(max(0.0, t0 - 0.05), min(self.T + 0.2, t1 + 0.05) + 1e-9, 1 / 30)
            keys = []
            for tm in ts:
                M = k.mouth(tm)
                S = k.shoulder(tm, side)
                sy_t = float(k.row(tm)[POSE["sy"]] or 1)
                lo, hi = 0.12, 0.9
                for _ in range(30):
                    g = (lo + hi) / 2
                    if np.linalg.norm(M + (tip - M) * g - S) < reach * sy_t:
                        lo = g
                    else:
                        hi = g
                G = M + (tip - M) * lo
                x, z, _ = k.arm_aim(tm, G, side, local=loc)
                keys.append((tm, x, z))
            for tm, x, z in keys:
                a.key(tm, ease="linear", **{arm + "_x": x, arm + "_z": z, arm + "_y": 0.0})
            a.key(t1 + 0.35, ease="smooth", **{arm + "_x": 0.0, arm + "_z": 0.0})
            def straw_fn(tm, k=k, tip=tip):
                if tm < t0 - 0.05 or tm > t1 + 0.05:
                    return None
                return tube(k.mouth(tm), tip, 0.05, 0.05, 0.62, style=1)
            def water_fn(tm, k=k, tip=tip):
                if tm < t0 + 0.05 or tm > t1:
                    return None
                flow = 0.75 + 0.25 * max(math.sin((tm - 0.1) * 2 * math.pi / 0.55), 0)
                return tube(tip, k.mouth(tm), 0.032 * flow, 0.028 * flow, 0.95, style=0)
            self.beams += [straw_fn, water_fn]
            others = [x for x in ("head", "body", "rarm", "larm") if x != arm]
            def check(n=n, k=k, tip=tip, others=others):
                bad = []
                to_w = tip - k.chest(t0); to_w[1] = 0
                if np.degrees(np.arccos(np.clip(k.body_dir(t0) @ (to_w / max(np.linalg.norm(to_w), 1e-9)), -1, 1))) > 70:
                    bad.append(f"a água não está À FRENTE de {n} (ponha a lagoa na frente dele, do lado da câmera)")
                for tm in np.linspace(t0, t1, 12):
                    c, part = k.clearance(tm, k.mouth(tm), tip, parts=others, skip_ends=0.07)
                    if c < 0.0:
                        bad.append(f"canudo de {n} atravessa {part} em t={tm:.2f}s ({c:+.3f})")
                    g = k.grip(tm, side)
                    M = k.mouth(tm); u = (tip - M) / np.linalg.norm(tip - M)
                    off = np.linalg.norm((g - M) - u * ((g - M) @ u))
                    if off > 0.06:
                        bad.append(f"mão de {n} fora do canudo em t={tm:.2f}s ({off:.3f} bloco)")
                return bad[:6]
            self.checks.append((f"canudo {n}", check))
        return self

    def _water_in_front(self, n: str, t: float) -> np.ndarray:
        """Water cell (surface - 0.3) closest to 1.5 blocks in front of the actor's feet; the straw goes there."""
        feet = self.pos(n, t)
        want = feet + _yaw_vec(self.yaw[n]) * 1.5
        cells = getattr(self.sb, "water_cells", set())
        if not cells:
            return want + [0, 0.5, 0]
        best = min(cells, key=lambda c: (self.sb.x + c[0] + 0.5 - want[0]) ** 2 + (self.sb.z + c[1] + 0.5 - want[2]) ** 2)
        return np.array([self.sb.x + best[0] + 0.5, self.sb.gy + 0.55, self.sb.z + best[1] + 0.5])

    def mob(self, mtype: str, dx: float, dz: float, fn=None, yaw: float = 0.0, dy: float = 0.0) -> Mob:
        """Animated vanilla mob (client-side, no AI).  fn(times)->(n,12) for procedural motion, else keys on the returned Mob."""
        p = self.sb.feet(dx, dz, dy)
        m = Mob(f"mob{len(self.mobs)}", "minecraft:" + mtype.replace("minecraft:", ""), p + [0, 0.5, 0], fn=fn)
        if fn is None:
            m.key(0.0, yaw=yaw)
        self.mobs.append(m)
        return m

    def anim(self) -> Anim:
        return Anim(list(self.actors.values()), water=self.water[0] if self.water else None,
                    water_level=self.water[1] if self.water else None, beams=self.beams, mobs=self.mobs, props=self.props)

    def run_checks(self) -> List[str]:
        out = []
        for label, fn in self.checks:
            out += fn()
        return out


# ------------------------------------------------------------------------------------------------- cameras
# Every camera is placed from the SUBJECT'S FRAME: c = centre of the subjects (feet), F = their mean facing (horizontal).
# az = azimuth of the camera around them, 0 = straight in front, + = toward the subjects' LEFT (screen right from the lens),
# kept within ±45° (3/4).  side=-1 mirrors.  Heights are above the feet (character = 2 blocks; eyes ~1.62).

def _dof(mv, focus_pt, ap):
    return mv.with_dof(tuple(V(focus_pt, float)), aperture=ap) if ap else mv


def subject_frame(st: Stage, names=None, t: float = 0.0):
    names = names or list(st.actors)
    if not names:
        return st.sb.point(0, -1, 0), _yaw_vec(st.audience)
    c = st.center(names, t)
    F = np.sum([KActor(st.actors[n]).body_dir(t) for n in names], axis=0)
    F[1] = 0
    if np.linalg.norm(F) < 0.3:
        F = _yaw_vec(st.audience)
    return c, F / np.linalg.norm(F)


def _at(c, F, az, dist, h):
    return c + _rot_y(F, az) * dist + np.array([0.0, h, 0.0])


def aim_height(d: float, fov: float, group: bool = False) -> float:
    """Height above the feet to aim at so the eyes land on the upper third (enquadramento.md §3c): 1.72 - d·tan(fov/6);
    groups / full shots: ~1.05."""
    return 1.05 if group else max(0.9, 1.72 - d * math.tan(math.radians(fov) / 6))


def _spread(st: Stage, names=None) -> float:
    names = names or list(st.actors)
    if len(names) < 2:
        return 0.0
    P = np.array([st.pos(n) for n in names])
    return float(np.max(np.linalg.norm(P[:, None, :] - P[None, :, :], axis=-1)))


def fit_dist(st: Stage, names, fov_v: float, margin: float = 1.6) -> float:
    """Distance so the whole group (+margin) fits the frame width with 7 % safety each side (no slice at a side edge, §3d)."""
    hfov = 2 * math.degrees(math.atan(math.tan(math.radians(fov_v) / 2) * 16 / 9))
    return (_spread(st, names) + margin) / (2 * math.tan(math.radians(hfov) / 2) * 0.86)


def cam_hero_low(st: Stage, T: float, names=None, fps: int = 60, sub: int = 8, az=(18, 6), d0: float = 6.0, d1: float = 4.2,
                 h=(0.45, 0.8), aim_h: float = 1.35, fov=(60, 50), ap: float = 0.3, roll=(-3.5, 0.0), side: int = 1) -> Rig:
    """Low hero angle on the subject(s), FRONT/3-4, looking slightly UP, slow push-in with a small arc. Intros, thesis, group."""
    c, F = subject_frame(st, names)
    # the whole group must fit the frame WIDTH at the end of the push (no character sliced at a side edge, §3d)
    hfov1 = 2 * math.degrees(math.atan(math.tan(math.radians(fov[1]) / 2) * 16 / 9))
    fit = (_spread(st, names) + 1.6) / (2 * math.tan(math.radians(hfov1) / 2) * 0.86)
    d1 = max(d1, fit); d0 = max(d0, d1 + 1.0)
    pts = [_at(c, F, side * az[0], d0, h[0]), _at(c, F, side * (az[0] + az[1]) / 2, (d0 + d1) / 2, (h[0] + h[1]) / 2),
           _at(c, F, side * az[1], d1, h[1])]
    grp = len(names or list(st.actors)) > 1
    aim = lerp_point(c + [0, aim_height(d0, fov[0], grp), 0], c + [0, aim_height(d1, fov[1], grp), 0], "smooth")
    mv = track(pts, aim, T, ease="launch_soft", fov=fov, name="hero_low").with_roll(roll).with_handheld("subtle", fade=0.15)
    return Rig(fps=fps, subframes=sub, shutter=0.5).add(_dof(mv, c + [0, aim_h, 0], ap))


def cam_orbit_push(st: Stage, T: float, names=None, fps: int = 60, sub: int = 8, az=(40, 12), r0: float = 4.6, r1: float = 3.0,
                   h=(1.9, 1.5), fov=(56, 48), ap: float = 0.3, side: int = 1) -> Rig:
    """Orbit IN FRONT of the subject while closing in (reveal a character / an object in a hand), from 3/4 toward the front."""
    c, F = subject_frame(st, names)
    r1 = max(r1, fit_dist(st, names, fov[1])); r0 = max(r0, r1 + 1.0)
    pts = []
    for u in np.linspace(0, 1, 5):
        e = u * u * (3 - 2 * u)
        pts.append(_at(c, F, side * (az[0] + (az[1] - az[0]) * e), r0 + (r1 - r0) * e, h[0] + (h[1] - h[0]) * e))
    aim = c + [0, 1.25, 0]
    mv = track(pts, aim, T, ease="launch_soft", fov=fov, name="orbit_push").with_handheld("subtle", fade=0.15).with_roll((-2.5, 1.0))
    return Rig(fps=fps, subframes=sub, shutter=0.5).add(_dof(mv, aim, ap))


def cam_establish(st: Stage, T: float, focus=None, fps: int = 60, sub: int = 8, az=(28, 14), high: float = 10.0, far: float = 16.0,
                  near: float = 6.5, low: float = 2.4, fov=(70, 56), side: int = 1) -> Rig:
    """Establishing crane IN FRONT of the cast: from high and far (the whole place) down to them — a new place / opening."""
    c, F = subject_frame(st)
    tgt = c + [0, 1.2, 0] if focus is None else V(st.where(focus), float)
    p0, p1 = _at(c, F, side * az[0], far, high), _at(c, F, side * az[1], near, low)
    mv = crane(tuple(p0), tuple(p1), tuple(tgt), T, arc=2.0, ease="launch", fov=fov).with_handheld("subtle", fade=0.2)
    return Rig(fps=fps, subframes=sub, shutter=0.5).add(mv)


def cam_reveal(st: Stage, T: float, target, names=None, over: Optional[str] = None, fps: int = 60, sub: int = 8, az: float = 20,
               fov=(58, 60), side: int = 1) -> Rig:
    """Crane-up reveal FROM THE FRONT: starts low and close on the character(s) (faces in frame), rises and pulls back so the
    target BEHIND them (waterfall, pool, village) appears over their heads.  Put the target behind the cast (opposite the lens)."""
    names = names or ([over] if over else None)
    c, F = subject_frame(st, names)
    tg = V(st.where(target), float)
    d0 = max(2.6, fit_dist(st, names, fov[0]))
    p0, p1 = _at(c, F, side * az, d0, 0.7), _at(c, F, side * az * 0.6, max(5.4, d0 + 2.4), 3.1)
    aim = lerp_point(c + [0, 1.35, 0], (c + [0, 1.2, 0]) * 0.35 + tg * 0.65, "soft_in_out")
    mv = track([p0, (p0 + p1) / 2 + [0, 0.3, 0], p1], aim, T, ease="soft_in_out", fov=fov, name="reveal").with_handheld("subtle")
    return Rig(fps=fps, subframes=sub, shutter=0.5).add(mv)


def cam_truck(st: Stage, T: float, names=None, fps: int = 60, sub: int = 8, dist: float = 4.2, arc: float = 22.0, h: float = 1.2,
              fov=(52, 50), follow: Optional[str] = None, lead_az: float = 35.0, ap: float = 0.25, side: int = 1) -> Rig:
    """Arc truck IN FRONT of the subjects (az -arc -> +arc).  follow=actor: the camera rides AHEAD of a walker at lead_az from its
    direction of motion (3/4 front), never beside it (beside = profile)."""
    if follow:
        ts = np.linspace(0, T, 7)
        P = [st.pos(follow, t) for t in ts]
        mvd = P[-1] - P[0]; mvd[1] = 0
        mvd = mvd / max(np.linalg.norm(mvd), 1e-6)
        pts = [p + _rot_y(mvd, side * lead_az) * dist + [0, h, 0] for p in P]
        aim = lerp_point(P[0] + [0, 1.15, 0], P[-1] + [0, 1.15, 0], "linear")
        mv = track(pts, aim, T, ease="linear", fov=fov, name="truck_follow").with_handheld("subtle").with_lag(0.12)
        return Rig(fps=fps, subframes=sub, shutter=0.5).add(mv)
    c, F = subject_frame(st, names)
    pts = [_at(c, F, side * a, dist, h) for a in np.linspace(-arc, arc, 4)]
    aim = c + [0, 1.25, 0]
    mv = track(pts, aim, T, ease="smooth", fov=fov, name="truck").with_handheld("subtle")
    return Rig(fps=fps, subframes=sub, shutter=0.5).add(_dof(mv, aim, ap))


def cam_close(st: Stage, T: float, focus=None, who: Optional[str] = None, fps: int = 60, sub: int = 8, az=(24, 6), d0: float = 1.8,
              d1: float = 1.35, height: float = 0.12, fov=(50, 44), ap: float = 0.45, side: int = 1) -> Rig:
    """Close-up from the FRONT/3-4 with a small arc push.  focus = point/mark/actor (default: chest of `who` or of the cast)."""
    names = [who] if who else None
    c, F = subject_frame(st, names)
    if focus is None:                               # a character: head + chest/belly in frame, eyes on the upper third (§3c)
        f = (st.k(who).chest(0) if who else c + [0, 1.0, 0])
        base = np.array([f[0], c[1], f[2]])
        a0, a1 = aim_height(d0, fov[0]), aim_height(d1, fov[1])
        p0 = _at(base, F, side * az[0], d0, a0 + height)
        p1 = _at(base, F, side * (az[0] + az[1]) / 2, (d0 + d1) / 2, (a0 + a1) / 2 + height)
        p2 = _at(base, F, side * az[1], d1, a1 + height)
        aim = lerp_point(base + [0, a0, 0], base + [0, a1, 0], "smooth")
    else:
        f = V(st.where(focus) if not isinstance(focus, np.ndarray) else focus, float)
        base = np.array([f[0], c[1], f[2]])
        p0 = _at(base, F, side * az[0], d0, f[1] - c[1] + height)
        p1 = _at(base, F, side * (az[0] + az[1]) / 2, (d0 + d1) / 2, f[1] - c[1] + height + 0.05)
        p2 = _at(base, F, side * az[1], d1, f[1] - c[1] + height + 0.1)
        aim = lerp_point(f + [0, 0.15, 0], f + [0, 0.04, 0], "smooth")
    mv = track([p0, p1, p2], aim, T, ease="launch_soft", fov=fov, name="close").with_roll((-3.5, 1.2)).with_handheld("subtle", fade=0.15)
    return Rig(fps=fps, subframes=sub, shutter=0.5).add(_dof(mv, f, ap))


def cam_plongee(st: Stage, T: float, focus=None, fps: int = 60, sub: int = 8, az: float = 18, height: float = 8.0, back: float = 5.0,
                drift: float = 10.0, fov=(60, 57), side: int = 1) -> Rig:
    """High angle on the whole situation (dry pond, pool, field), from the FRONT of the cast, slow drift."""
    c, F = subject_frame(st)
    tgt = c + [0, 0.6, 0] if focus is None else V(st.where(focus), float)
    p0, p1 = _at(c, F, side * az, back, height), _at(c, F, side * (az - drift), back * 0.92, height - 0.4)
    mv = track([p0, p1], lerp_point(tgt + [0.2, 0, 0], tgt, "smooth"), T, ease="smooth", fov=fov, name="plongee").with_handheld("subtle", fade=0.1)
    return Rig(fps=fps, subframes=sub, shutter=0.5).add(mv)


def cam_dolly_shock(st: Stage, T: float, who: str, fps: int = 60, sub: int = 8, d0: float = 2.4, d1: float = 5.0, fov0: float = 40.0,
                    az: float = 0.0, side: int = 1) -> Rig:
    """Vertigo (dolly zoom) on a shocked face, dead FRONT: background stretches, face stays."""
    c, F = subject_frame(st, [who])
    h = st.head(who)
    base = np.array([h[0], c[1], h[2]])
    p0, p1 = _at(base, F, side * az, d0, h[1] - c[1] + 0.05), _at(base, F, side * az, d1, h[1] - c[1] + 0.15)
    mv = dolly_zoom(tuple(p0), tuple(p1), tuple(h), T, fov0=fov0, ease="smooth")
    return Rig(fps=fps, subframes=sub, shutter=0.5).add(mv)


def cam_ots(st: Stage, T: float, over: str, to: str, fps: int = 60, sub: int = 8, fov=(46, 42), ap: float = 0.35, side: int = 1) -> Rig:
    """Over-the-shoulder (dialogue): behind `over`'s shoulder (allowed back-3/4 — it is a frame edge), on `to`'s face (front/3-4).
    Registers `over` in st.allow_back."""
    st.allow_back.add(over)
    a, b = st.head(over), st.head(to)
    d = b - a; d[1] = 0; d /= max(np.linalg.norm(d), 1e-6)
    sideways = np.array([d[2], 0, -d[0]]) * side
    p0 = a - d * 1.1 + sideways * 0.55 + [0, 0.05, 0]
    p1 = a - d * 0.9 + sideways * 0.5 + [0, 0.02, 0]
    mv = track([p0, p1], b + [0, -0.1, 0], T, ease="smooth", fov=fov, name="ots").with_handheld("subtle")
    return Rig(fps=fps, subframes=sub, shutter=0.5).add(_dof(mv, b, ap))


CAMS = {"hero_low": cam_hero_low, "orbit_push": cam_orbit_push, "establish": cam_establish, "reveal": cam_reveal,
        "truck": cam_truck, "close": cam_close, "plongee": cam_plongee, "dolly_shock": cam_dolly_shock, "ots": cam_ots}
