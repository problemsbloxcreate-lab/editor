"""actors: keyframed player-model characters (any skin PNG), water-level drain and water beams, rendered by the CineCam mod.

    from cinecam import *
    a = Actor("problems", r"C:/.../Problems0.png", pos=(810, 64, -194), yaw=0)
    a.key(0.0, head_x=0).key(0.6, ease="out_back", head_x=-35, rarm_x=-20)        # values hold between keys
    a.wobble("belly", 1.0, 3.0, amp=0.05, freq=9)                                  # additive procedural shake
    anim = Anim([a], water=WaterRegion(box=(700, -300, 900, -90), y_min=44, y_max=62), water_level=lambda t: 62.6 - 4 * t)
    render(rig, "name", ..., anim=anim)

Pose conventions (degrees, blocks; Minecraft yaw: 0 faces +z/south):
  x,y,z feet | yaw | sx,sy,sz scale about the feet | head_x/y/z (x<0 looks UP) | rarm_x/y/z, larm_x/y/z (x=-90 points forward, -180 straight up)
  rleg_*, lleg_* | belly (torso x/z scale) | belly_y | head (head scale) | lean (about the feet, X axis) | item (0/1 held item) | hop (blocks) | roll.
  bright (fullbright) | rarm_len larm_len rleg_len lleg_len (rubber limbs: y scale from shoulder/hip) | shadow_y (blob shadow on that ground y) | silhouette 0..1 (backlit: model darkens to near black).
  v0.7 voxel belly (the in-game "full of water" look): vbelly = ball radius in model px (0 off) | vbelly_y centre px below the neck (7)
  | vbelly_out px it bulges past the torso front (3) | vbelly_wave slosh ripple amplitude px | vbelly_jig squash/stretch (+ taller) | vbelly_vox cube size px (1) | vbelly_shine 0..1 moving water glints.
  v1.0 body (one bending mesh per limb, like Mine-imator): rarm_bend larm_bend (elbow, deg, NEGATIVE = forearm forward) |
  rleg_bend lleg_bend (knee, deg, POSITIVE = shin backward) | torso_x (lean forward +) torso_y (twist) torso_z (side) about the hip |
  mouth 0..1 (open) | blink 0..1 — face rects come from Actor(face="auto") = cinecam.face.detect(skin).
Model is 2.0 blocks tall (no vanilla 0.9375 scale).  item = registry id or "model:cinecam:item/elastic_glove" (models in the
mod's assets); the `item` channel is the held item's SCALE (0 hidden, 1 normal; animate it for a pull-out "pop").  Actor(hat=True) adds a 3D crown+brim textured from the skin's head top.

Props (v0.4): any block model as a rubbery object, pivot = bottom centre of the block.
    g = Prop("ground", "minecraft:grass_block", pos=(x, y, z)).key(1.0, sy=0.5, sx=1.4, sz=1.4).key(1.3, ease="out_back", sy=1, sx=1, sz=1)
    Prop(..., fn=lambda times: array(n, 9))  # procedural: x,y,z,sx,sy,sz,yaw,pitch,roll per time (e.g. a bending tree segment)
    Anim([actor], props=[g, ...])
"""
from __future__ import annotations

import json
import math
import zlib
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np

from .camlib import ease_fn

PN, BN, PRN = 52, 16, 9
POSE = dict(x=0, y=1, z=2, yaw=3, sx=4, sy=5, sz=6, head_x=7, head_y=8, head_z=9,
            rarm_x=10, rarm_y=11, rarm_z=12, larm_x=13, larm_y=14, larm_z=15,
            rleg_x=16, rleg_y=17, rleg_z=18, lleg_x=19, lleg_y=20, lleg_z=21,
            belly=22, belly_y=23, head=24, lean=25, item=26, hop=27, roll=28, bright=29,
            rarm_len=30, larm_len=31, rleg_len=32, lleg_len=33, shadow_y=34, silhouette=35,
            vbelly=36, vbelly_y=37, vbelly_out=38, vbelly_wave=39, vbelly_jig=40, vbelly_vox=41, vbelly_shine=42,
            rarm_bend=43, larm_bend=44, rleg_bend=45, lleg_bend=46, torso_x=47, torso_y=48, torso_z=49, mouth=50, blink=51)
_DEFAULTS = {"sx": 1, "sy": 1, "sz": 1, "belly": 1, "belly_y": 1, "head": 1,
             "rarm_len": 1, "larm_len": 1, "rleg_len": 1, "lleg_len": 1,
             "vbelly_y": 7, "vbelly_out": 3, "vbelly_vox": 1}
PROP = dict(x=0, y=1, z=2, sx=3, sy=4, sz=5, yaw=6, pitch=7, roll=8)


class _Keyed:
    FIELDS: Dict[str, int] = {}
    WIDTH = 0

    def _init_keys(self):
        self.keys: Dict[str, List[Tuple[float, float, str]]] = {f: [] for f in self.FIELDS}
        self.wobbles: List[Tuple[str, float, float, float, float, float, float]] = []

    def key(self, t: float, ease: str = "smooth", **vals):
        """Set channels at time t; the channel eases from its previous key to this value with `ease`
        (smooth | out_back | out | in | in_out | linear | hold = keep old value until t, then jump)."""
        for k, v in vals.items():
            if k not in self.FIELDS:
                raise KeyError(f"unknown field {k}; have {sorted(self.FIELDS)}")
            self.keys[k].append((float(t), float(v), ease))
            self.keys[k].sort(key=lambda a: a[0])
        return self

    def wobble(self, field: str, t0: float, t1: float, amp: float, freq: float, decay: float = 0.0, phase: float = 0.0,
               ramp: float = 0.08):
        """Additive sine on a channel between t0 and t1 (decay>0: exponential fade-out; ramp = fade in/out seconds)."""
        if field not in self.FIELDS:
            raise KeyError(f"unknown field {field}")
        self.wobbles.append((field, t0, t1, amp, freq, decay, phase, ramp))
        return self

    def at(self, times: np.ndarray) -> np.ndarray:
        n = len(times)
        out = np.zeros((n, self.WIDTH))
        for f, idx in self.FIELDS.items():
            ks = self.keys[f]
            if not ks:
                out[:, idx] = _DEFAULTS.get(f, 0.0)
                continue
            col = np.full(n, ks[0][1])
            for (t0, v0, _), (t1, v1, e) in zip(ks[:-1], ks[1:]):
                if e == "hold":
                    m = times >= t1
                    col[m] = v1
                    continue
                u = np.clip((times - t0) / max(t1 - t0, 1e-9), 0, 1)
                w = ease_fn(e)(u)
                m = times >= t0
                col[m] = (v0 + (v1 - v0) * w)[m]
            col[times >= ks[-1][0]] = ks[-1][1]
            out[:, idx] = col
        for f, t0, t1, amp, freq, decay, ph, ramp in self.wobbles:
            m = (times >= t0) & (times <= t1)
            tt = times[m] - t0
            env = np.exp(-decay * tt) if decay > 0 else 1.0
            fade = np.clip(np.minimum(tt / ramp, (t1 - times[m]) / ramp), 0, 1)
            fade = fade * fade * (3 - 2 * fade)
            out[m, self.FIELDS[f]] += amp * env * fade * np.sin(2 * np.pi * freq * tt + ph)
        return out


class Actor(_Keyed):
    FIELDS, WIDTH = POSE, PN

    def __init__(self, name: str, skin: str, pos: Sequence[float], yaw: float = 0.0, slim: bool = False, item: Optional[str] = None,
                 hat: bool = False, face="auto"):
        self.name, self.skin, self.slim, self.item, self.hat = name, skin, slim, item, hat
        if face == "auto":
            from .face import detect
            face = detect(skin)
        self.face = face
        self._init_keys()
        self.key(0.0, x=pos[0], y=pos[1], z=pos[2], yaw=yaw)

    def idle(self, t0: float, t1: float, amp: float = 1.0, seed: int = 0):
        """Life between keyed actions (v0.8): breathing, a slow head drift, weight shift and arm sway with per-actor phases,
        so nobody stands frozen like a statue in a 2-6 s close shot.  Additive: keys still drive the big moves."""
        rng = np.random.default_rng(zlib.crc32(f"{self.name}:{seed}".encode()))   # stable across runs (draft = final)
        ph = lambda: float(rng.uniform(0, 2 * np.pi))
        r = 0.4
        self.wobble("belly", t0, t1, 0.012 * amp, 0.27, phase=ph(), ramp=r)
        self.wobble("head_x", t0, t1, 1.8 * amp, 0.23, phase=ph(), ramp=r)
        self.wobble("head_y", t0, t1, 2.6 * amp, 0.13, phase=ph(), ramp=r)
        self.wobble("lean", t0, t1, 0.9 * amp, 0.17, phase=ph(), ramp=r)
        p = ph()
        self.wobble("rarm_z", t0, t1, 1.6 * amp, 0.27, phase=p, ramp=r)
        self.wobble("larm_z", t0, t1, -1.6 * amp, 0.27, phase=p, ramp=r)
        self.wobble("rarm_x", t0, t1, 1.2 * amp, 0.19, phase=ph(), ramp=r)
        self.wobble("larm_x", t0, t1, 1.2 * amp, 0.21, phase=ph(), ramp=r)
        return self


class Prop(_Keyed):
    """A block model drawn as a squashy object (no collision, nothing in the world).  Pivot = bottom centre.
    Keys: x y z sx sy sz yaw pitch roll.  sx=0 hides it.  fn(times)->(n,9) overrides keys (procedural chains/trees)."""
    FIELDS, WIDTH = PROP, PRN

    def __init__(self, name: str, block: str, pos: Sequence[float], fn: Optional[Callable[[np.ndarray], np.ndarray]] = None):
        self.name, self.block, self.fn = name, block, fn
        self._init_keys()
        self.key(0.0, x=pos[0], y=pos[1], z=pos[2], sx=1, sy=1, sz=1)

    def at(self, times: np.ndarray) -> np.ndarray:
        if self.fn is not None:
            return np.asarray(self.fn(np.asarray(times, float)), float).reshape(len(times), PRN)
        return super().at(times)


MOB = dict(x=0, y=1, z=2, yaw=3, pitch=4, roll=5, sx=6, sy=7, sz=8, shadow_y=9, walk=10, age=11, walk_amt=12, head_yaw=13, head_pitch=14,
           rema=15)                       # v1.1: barco — ângulo do remo (rad, 0 = parado)
MBN = 16
# altura (blocos) da caixa de cada mob vanilla: o centro fica em pés + altura/2 (antes tudo ia a +0,5 e o creeper afundava 0,35)
MOB_H = {"boat": 0.5625, "creeper": 1.7, "zombie": 1.95, "husk": 1.95, "drowned": 1.95, "skeleton": 1.99, "stray": 1.99, "wither_skeleton": 2.4,
         "pig": 0.9, "cow": 1.4, "mooshroom": 1.4, "sheep": 1.3, "chicken": 0.7, "spider": 0.9, "cave_spider": 0.5,
         "villager": 1.95, "wandering_trader": 1.95, "witch": 1.95, "pillager": 1.95, "vindicator": 1.95, "evoker": 1.95,
         "wolf": 0.85, "cat": 0.7, "ocelot": 0.7, "fox": 0.7, "rabbit": 0.5, "horse": 1.6, "donkey": 1.5, "llama": 1.87,
         "enderman": 2.9, "iron_golem": 2.7, "snow_golem": 1.9, "slime": 0.52, "magma_cube": 0.52, "blaze": 1.8, "piglin": 1.95,
         "zombified_piglin": 1.95, "hoglin": 1.4, "goat": 1.3, "frog": 0.5, "axolotl": 0.42, "turtle": 0.4, "panda": 1.25,
         "polar_bear": 1.4, "bee": 0.6, "parrot": 0.9, "allay": 0.6, "warden": 2.9, "camel": 2.375, "sniffer": 1.75}


class Mob(_Keyed):
    """A vanilla mob ("minecraft:pig"...) drawn by the mod with ITS OWN model and animation (quadruped legs, creeper's 4 legs,
    spider's 8, chicken wings...), never added to the world.  x,y,z = body CENTRE (use Mob.feet(...) to stand it on the ground);
    sx/sy/sz squash along WORLD axes (impacts), then yaw/pitch/roll tumble; sx=0 hides; head_yaw/head_pitch = look (deg).
    v1.0.2: the walk cycle comes from the DISTANCE walked, with the vanilla formula (amount = lerp(0.4) to min(4·blocks/tick, 1),
    position += amount per tick) — never a step per render pass (that ran 6-10x too fast with subframes and jittered).
    age = entity tickCount (20·t by default: tails/wings/idle anims at game speed).  fn(times)->(n,15|12) overrides keys."""
    FIELDS, WIDTH = MOB, MBN

    def __init__(self, name: str, type: str, pos: Sequence[float], fn: Optional[Callable[[np.ndarray], np.ndarray]] = None,
                 auto_walk: bool = True, age_rate: float = 20.0):
        self.name, self.type, self.fn = name, type, fn
        self.auto_walk, self.age_rate = auto_walk, age_rate
        self._init_keys()
        self.key(0.0, x=pos[0], y=pos[1], z=pos[2], sx=1, sy=1, sz=1)

    @staticmethod
    def height(type: str) -> float:
        return MOB_H.get(type.replace("minecraft:", ""), 1.0)

    @classmethod
    def feet(cls, name: str, type: str, feet: Sequence[float], **kw) -> "Mob":
        """Mob standing with its feet at `feet` (x, ground y, z)."""
        f = np.asarray(feet, float)
        return cls(name, type, (f[0], f[1] + cls.height(type) / 2, f[2]), **kw)

    def _raw(self, times: np.ndarray) -> np.ndarray:
        if self.fn is not None:
            r = np.asarray(self.fn(np.asarray(times, float)), float).reshape(len(times), -1)
            if r.shape[1] < MBN:
                r = np.concatenate([r, np.zeros((len(times), MBN - r.shape[1]))], axis=1)
            return r
        return super().at(times)

    def at(self, times: np.ndarray) -> np.ndarray:
        times = np.asarray(times, float)
        out = self._raw(times)
        if self.age_rate and not self.keys["age"] and (self.fn is None or not np.any(out[:, MOB["age"]])):
            out[:, MOB["age"]] = self.age_rate * times
        if self.auto_walk and not self.keys["walk"] and len(times):
            t_end = float(times.max()) + 0.1
            tk = np.arange(0.0, t_end + 0.05, 0.05)                 # game ticks
            g = self._raw(tk)
            d = np.hypot(np.diff(g[:, 0], prepend=g[0, 0]), np.diff(g[:, 2], prepend=g[0, 2]))
            amt = np.zeros(len(tk)); pos = np.zeros(len(tk)); a = 0.0; ps = 0.0
            for i in range(len(tk)):
                a += (min(d[i] * 4.0, 1.0) - a) * 0.4
                ps += a
                amt[i], pos[i] = a, ps
            out[:, MOB["walk"]] = np.interp(times, tk, pos)
            out[:, MOB["walk_amt"]] = np.interp(times, tk, amt)
        return out


@dataclass
class WaterRegion:
    box: Tuple[int, int, int, int]      # x0, z0, x1, z1
    y_min: int
    y_max: int
    center: Tuple[float, float] = (0.0, 0.0)   # funnel centre (x, z)


class Anim:
    """Everything the mod animates besides the camera.  Rows are aligned with camera.csv."""

    def __init__(self, actors: Sequence[Actor] = (), water: Optional[WaterRegion] = None,
                 water_level: Optional[Callable[[float], float]] = None,
                 funnel: Optional[Callable[[float], float]] = None,
                 beams: Sequence[Callable[[float], Optional[Sequence[float]]]] = (), props: Sequence[Prop] = (),
                 mobs: Sequence["Mob"] = ()):
        self.actors, self.water, self.water_level, self.beams = list(actors), water, water_level, list(beams)
        self.props = list(props)
        self.mobs = list(mobs)
        self.funnel = funnel

    def write(self, path: str, times: np.ndarray, subframes: int = 1) -> int:
        n = len(times)
        poses = [a.at(times) for a in self.actors]
        pposes = [p.at(times) for p in self.props]
        mposes = [m.at(times) for m in self.mobs]
        S = max(1, subframes)
        rows = []
        for i in range(n):
            r: Dict = {}
            if self.water_level is not None:
                tc = float(times[(i // S) * S + S // 2]) if S > 1 and (i // S) * S + S // 2 < n else float(times[i])
                r["w"] = round(float(self.water_level(tc)), 4)
                if self.funnel is not None:
                    r["f"] = round(float(self.funnel(tc)), 5)
            if self.actors:
                r["a"] = [[round(float(v), 4) for v in p[i]] for p in poses]
            if self.props:
                r["p"] = [[round(float(v), 4) for v in p[i]] for p in pposes]
            if self.mobs:
                r["m"] = [[round(float(v), 4) for v in p[i]] for p in mposes]
            bl = []
            for b in self.beams:
                v = b(float(times[i]))
                if v is not None:
                    bl.append([round(float(x), 4) for x in v])
            if bl:
                r["b"] = bl
            rows.append(r)
        doc = {"actors": [{"name": a.name, "skin": a.skin.replace("\\", "/"), "slim": a.slim, "item": a.item, "hat": a.hat,
                           **({"face": a.face} if getattr(a, "face", None) else {})} for a in self.actors],
               "props": [{"name": p.name, "block": p.block} for p in self.props],
               "mobs": [{"name": m.name, "type": m.type} for m in self.mobs], "rows": rows}
        if self.water is not None:
            doc["water"] = {"box": list(self.water.box), "yMin": self.water.y_min, "yMax": self.water.y_max, "center": list(self.water.center)}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(doc, f, separators=(",", ":"))
        return n


def row_times(rig) -> np.ndarray:
    """Un-shifted animation time of every camera row (frame centre +- shutter)."""
    ft = rig.frame_times()
    S = rig.subframes
    if S == 1:
        return ft
    offs = (np.arange(S) + 0.5) / S - 0.5
    return (ft[:, None] + offs[None, :] * rig.shutter / rig.fps).reshape(-1).clip(min=0.0)


def mouth_position(a: Actor, t: float, forward: float = 0.27, up: float = 0.12) -> np.ndarray:
    """World position of the actor's mouth at time t — exact model kinematics (cinecam.kin).  21/10/2026: the old formula had
    the yaw sign inverted (mouth BEHIND the head for any yaw != 0/180) — the cause of a straw going through a head."""
    from .kin import KActor
    return KActor(a).mouth(t)


def tube(p0, p2, r1, r2, alpha=1.0, lift=0.0, push_z=0.0, style=2, color=(1, 1, 1), segments=0):
    """One beam/tube vector.  style 0 = shimmering water, 1 = red/white straw stripes, 2 = plain colour."""
    return [p0[0], p0[1], p0[2], p2[0], p2[1], p2[2], r1, r2, alpha, lift, push_z, color[0], color[1], color[2], style, segments]


def bent_straw(p_tip, p_mouth):
    """Control-point params (lift, push_z) that make a quadratic tube rise straight up from p_tip and bend into p_mouth
    (a bendy drinking straw)."""
    lift = (p_mouth[1] - p_tip[1]) / 2.0
    push = (p_tip[2] - p_mouth[2]) / 2.0
    return lift, push
