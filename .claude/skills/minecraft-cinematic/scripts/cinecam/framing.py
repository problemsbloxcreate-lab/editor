"""framing: objective checks of a shot BEFORE rendering (references/enquadramento.md §3a, §3c, §3d, §3g).

Matheus (21/10/2026): "evite ao máximo filmar os personagens de LADO — sempre de FRENTE ou 45°; de costas evitar também, mas não
tanto quanto de lado" + "NUNCA MAIS item que não esteja perfeitamente encaixado".

Horizontal angle θ between a character's facing (body / face) and the direction character -> camera:
    frente 0-25 (26/10: o padrão) | 3/4 25-50 (só até ~35°) | tolerável 50-60 | PERFIL 60-120 (forbidden) | costas-3/4 120-150 | COSTAS 150-180
Per role: SUBJECT face θ <= 50° in >= 90 % of its screen time; anyone with >= 10 % of frame height: no PROFILE > 10 % of its
screen time; back only for characters in `allow_back` (OTS shoulder, turn-reveal, walking away).
Also: no "slice at the frame edge" (a character is either >= 92 % inside the frame or out), subject >= 15 % of the frame height
on the last frame.

    rep = check_shot(rig, stage, subject="problems")
    ok, why = verdict(rep, allow_back=stage.allow_back)
"""
from __future__ import annotations

import math
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

from .camlib import forward
from .kin import KActor

ZONES = [("frente", 0, 25), ("3/4", 25, 50), ("tolerável", 50, 60), ("PERFIL", 60, 120), ("costas-3/4", 120, 150), ("COSTAS", 150, 181)]


def zone(angle: float) -> str:
    for name, a, b in ZONES:
        if a <= angle < b:
            return name
    return "COSTAS"


def horizontal_angle(facing: np.ndarray, to_cam: np.ndarray) -> float:
    a = np.array([facing[0], facing[2]]); b = np.array([to_cam[0], to_cam[2]])
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na < 1e-6 or nb < 1e-6:
        return 0.0
    return math.degrees(math.acos(max(-1.0, min(1.0, (a @ b) / (na * nb)))))


def _basis(yaw, pitch):
    f = np.asarray(forward(yaw, pitch), float)
    r = np.cross(f, [0, 1.0, 0]); r /= max(np.linalg.norm(r), 1e-9)
    u = np.cross(r, f)
    return f, r, u


def project(cam, f, r, u, fov_v, P, aspect=16 / 9):
    """Screen coords (sx, sy in 0..1 from the top-left) of points P (n,3); z<=0.05 -> nan."""
    v = np.atleast_2d(P) - cam
    z = v @ f
    tv = math.tan(math.radians(fov_v) / 2); th = tv * aspect
    with np.errstate(divide="ignore", invalid="ignore"):
        sx = 0.5 + 0.5 * (v @ r) / (z * th)
        sy = 0.5 - 0.5 * (v @ u) / (z * tv)
    bad = z <= 0.05
    sx[bad] = np.nan; sy[bad] = np.nan
    return sx, sy


def _corners(k: KActor, t: float) -> np.ndarray:
    pts = []
    for c, ax, h in k.boxes(t).values():
        for sx in (-1, 1):
            for sy in (-1, 1):
                for sz in (-1, 1):
                    pts.append(c + ax @ (h * np.array([sx, sy, sz])))
    return np.array(pts)


def check_shot(rig, actors, subject: Optional[str] = None, step: int = 2) -> Dict[str, dict]:
    """actors: Stage (uses .actors) or {name: Actor}.  subject defaults to the first actor.  Samples every `step` frames."""
    acts = getattr(actors, "actors", actors)
    subject = subject or (next(iter(acts)) if acts else None)
    d = rig.sample_frames()
    nF = len(d["t"])
    out = {}
    for name, a in acts.items():
        k = KActor(a)
        rows = []
        last_h = 0.0
        for i in list(range(0, nF, step)) + [nF - 1]:
            t = float(d["t"][i])
            cam = np.array([d["x"][i], d["y"][i], d["z"][i]])
            f, r, u = _basis(d["yaw"][i], d["pitch"][i])
            sx, sy = project(cam, f, r, u, d["fov"][i], _corners(k, t))
            if np.isnan(sx).all():
                continue
            x0, x1, y0, y1 = np.nanmin(sx), np.nanmax(sx), np.nanmin(sy), np.nanmax(sy)
            ix = max(0.0, min(1.0, x1) - max(0.0, x0))
            f_in = ix / max(x1 - x0, 1e-9)                # LATERAL fraction inside: a body cut by the bottom edge is a normal
            if max(0.0, min(1.0, y1) - max(0.0, y0)) <= 0:  # medium/close shot; a sliver at a SIDE edge is the error
                f_in = 0.0
            hfrac = min(y1, 1) - max(y0, 0)
            if i == nF - 1:
                last_h = max(0.0, hfrac) if f_in > 0.5 else 0.0
                if i % step:
                    continue
            if f_in <= 0.0 or np.isnan(sx).any():
                continue
            ch = k.chest(t); hc = k.head_center(t)
            c_, ax_, h_ = k.boxes(t)["head"]
            top = [c_ + ax_ @ (h_ * np.array([sx_, sy_, sz_])) for sx_ in (-1, 1) for sy_ in (-1, 1) for sz_ in (-1, 1)]
            hy = project(cam, f, r, u, d["fov"][i], np.array(top))[1]
            head_cut = bool(np.nanmin(hy) < 0.0)                       # any part of the head above the top edge
            rows.append((t, horizontal_angle(k.body_dir(t), cam - ch), horizontal_angle(k.face_dir(t), cam - hc), f_in, hfrac, head_cut))
        if not rows:
            out[name] = {"on_screen": 0.0, "subject": name == subject}
            continue
        body = np.array([x[1] for x in rows]); face = np.array([x[2] for x in rows])
        big = [x for x in rows if x[4] >= 0.10]
        zs = [zone(x[1]) for x in big] or ["frente"]
        out[name] = {"subject": name == subject, "on_screen": round(len(rows) * step / max(nF, 1), 2),
                     "body_deg": [round(float(body.min()), 1), round(float(np.median(body)), 1), round(float(body.max()), 1)],
                     "face_deg": [round(float(face.min()), 1), round(float(np.median(face)), 1), round(float(face.max()), 1)],
                     "face_ok50": round(float(np.mean(face <= 50)), 2),
                     "face_ok30": round(float(np.mean(face <= 30)), 2),
                     "side": round(float(np.mean([35 < x[1] < 150 for x in big])) if big else 0.0, 2),
                     "zones": {z: round(zs.count(z) / len(zs), 2) for z in dict.fromkeys(zs)},
                     "slice": round(float(np.mean([0.0 < x[3] < 0.92 for x in rows])), 2),
                     "head_cut": round(float(np.mean([x[5] for x in rows])), 2),
                     "height_last": round(last_h, 2)}
    return out


def verdict(rep: Dict[str, dict], max_profile: float = 0.10, max_back: float = 0.35, allow_back=(), max_slice: float = 0.15,
            max_side: float = 0.15) -> Tuple[bool, List[str]]:
    """26/10 (dono): personagem "meio lateral" (45–60°) não fica bom em vídeo de Minecraft — corpo a mais de 35° da lente em
    > max_side do tempo reprova; o sujeito precisa do rosto a ≤ 30° em 85 % do tempo (antes 50°)."""
    why = []
    for name, r in rep.items():
        if r.get("subject") and not r.get("on_screen"):
            why.append(f"{name} (sujeito) não aparece no quadro")
            continue
        if not r.get("on_screen"):
            continue
        z = r["zones"]
        if z.get("PERFIL", 0) > max_profile and name not in allow_back:
            why.append(f"{name}: de PERFIL em {z['PERFIL']:.0%} do tempo em tela (corpo {r['body_deg']}°)")
        back = z.get("COSTAS", 0) + z.get("costas-3/4", 0)
        if back > max_back and name not in allow_back:
            why.append(f"{name}: de COSTAS em {back:.0%} do tempo em tela")
        if r.get("subject") and r.get("face_ok30", r["face_ok50"]) < 0.85 and name not in allow_back:
            why.append(f"{name} (sujeito): rosto a mais de 30° da lente em {1 - r.get('face_ok30', 0):.0%} do tempo (rosto {r['face_deg']}°)")
        if r.get("side", 0) > max_side and name not in allow_back:
            why.append(f"{name}: meio de lado (corpo > 35° da lente) em {r['side']:.0%} do tempo (corpo {r['body_deg']}°) — enquadre de frente")
        if r["slice"] > max_slice and name not in allow_back:
            why.append(f"{name}: cortado na borda do quadro em {r['slice']:.0%} do tempo (inteiro ou fora)")
        if r.get("subject") and r.get("head_cut", 0) > 0.10:
            why.append(f"{name} (sujeito): cabeça cortada no topo do quadro em {r['head_cut']:.0%} do tempo (headroom, §3c)")
        if r.get("subject") and r["height_last"] < 0.15:
            why.append(f"{name} (sujeito): só {r['height_last']:.0%} da altura no último quadro (mín. 15 %)")
    return (not why), why
