"""face: find the eyes and mouth on a skin's 8x8 face so the mod can blink and open the mouth (v1.0, 25/10/2026).

    from cinecam.face import detect
    detect(r".../Problems0.png")   # {"mouth":[x0,y0,x1,y1], "mouthOpen":1, "mouthColor":[r,g,b], "eyes":[[x0,y0,x1,y1],...], "lid":[r,g,b]}

Coordinates are face pixels (x right in the skin image, y down).  The face = skin (8..16, 8..16) under the hat layer (40..48, 8..16).
Heuristic: the skin tone is the most common colour; eyes = pixels in rows 1-5 far from it, split left/right; mouth = such pixels in
rows 5-7 near the middle (if none, a 2 px line on row 6).  Override per character with Actor(face={...}) when a skin is unusual.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Dict, List, Optional

import numpy as np


def _face_rgba(skin: str) -> np.ndarray:
    from PIL import Image
    im = np.asarray(Image.open(skin).convert("RGBA")).astype(np.float32) / 255.0
    face = im[8:16, 8:16].copy()
    if im.shape[0] >= 16 and im.shape[1] >= 48:
        hat = im[8:16, 40:48]
        a = hat[..., 3:4]
        face[..., :3] = face[..., :3] * (1 - a) + hat[..., :3] * a
    return face


def _boxes(mask: np.ndarray) -> List[List[int]]:
    """Connected groups (4-neighbour) -> [x0, y0, x1, y1] (x1/y1 exclusive)."""
    seen = np.zeros_like(mask, dtype=bool)
    out = []
    for y in range(mask.shape[0]):
        for x in range(mask.shape[1]):
            if mask[y, x] and not seen[y, x]:
                st, xs, ys = [(y, x)], [], []
                seen[y, x] = True
                while st:
                    cy, cx = st.pop()
                    xs.append(cx); ys.append(cy)
                    for ny, nx in ((cy + 1, cx), (cy - 1, cx), (cy, cx + 1), (cy, cx - 1)):
                        if 0 <= ny < mask.shape[0] and 0 <= nx < mask.shape[1] and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            st.append((ny, nx))
                out.append([min(xs), min(ys), max(xs) + 1, max(ys) + 1])
    return out


# Hand-checked faces of the turma (25/10/2026, from the 8x8 grids): no blink where the eyes are glasses/visor, no mouth where
# opening it would cut the drawing (Problems' side smile, Brucutu's moustache on the last row).
FACES = {
    "problems0": {"eyes": [[2, 1, 3, 2], [6, 1, 7, 2]], "lid": [0.0, 0.8, 0.8]},
    "kadu2": {"mouth": [3, 6, 5, 7], "mouthColor": [0.12, 0.0, 0.02], "eyes": [[1, 5, 2, 6], [6, 5, 7, 6]], "lid": [0.72, 0.06, 0.09]},
    "mel_player": {"mouth": [2, 6, 6, 7], "mouthColor": [0.25, 0.02, 0.02]},
    "o_stick": {"mouth": [3, 6, 5, 7], "mouthColor": [0.05, 0.12, 0.02], "eyes": [[2, 2, 4, 3], [5, 2, 7, 3]], "lid": [0.86, 0.86, 0.86]},
    "brucutu": {"eyes": [[1, 4, 3, 6], [5, 4, 7, 6]], "lid": [0.86, 0.58, 0.34]},
    "zoom": None,
}


def _layer_z(skin: str) -> float:
    """Face drawn on the hat layer (opaque over the face) -> the rig must sit in front of that layer (0.5 px out)."""
    try:
        from PIL import Image
        im = np.asarray(Image.open(skin).convert("RGBA"))
        return -0.6 if im.shape[0] >= 16 and int((im[9:16, 40:48, 3] > 25).sum()) >= 16 else -0.08
    except Exception:
        return -0.08


@lru_cache(maxsize=64)
def detect(skin: str) -> Optional[Dict]:
    out = _detect(skin)
    if out is not None:
        out = {**out, "z": _layer_z(skin)}
    return out


def _detect(skin: str) -> Optional[Dict]:
    import os
    key = os.path.splitext(os.path.basename(skin))[0].lower()
    if key in FACES:
        f = FACES[key]
        return None if f is None else {**{"mouthOpen": 1.0}, **{k: v for k, v in f.items()}}
    try:
        f = _face_rgba(skin)
    except Exception:
        return None
    rgb = f[..., :3]
    q = (rgb * 15).round().astype(int)
    keys = q[..., 0] * 256 + q[..., 1] * 16 + q[..., 2]
    vals, cnt = np.unique(keys, return_counts=True)
    tone_mask = keys == vals[cnt.argmax()]
    tone = rgb[tone_mask].mean(axis=0)
    dist = np.linalg.norm(rgb - tone, axis=-1)
    odd = dist > 0.22
    upper = odd.copy()
    upper[:1] = False
    upper[6:] = False
    small = [b for b in _boxes(upper) if b[2] - b[0] <= 2 and b[3] - b[1] <= 2]
    pair = None
    for i in range(len(small)):
        for j in range(i + 1, len(small)):
            a, b = sorted((small[i], small[j]))
            if a[1] == b[1] and abs((a[0] + a[2]) - (16 - (b[0] + b[2]))) <= 2 and b[0] - a[2] >= 2:
                pair = [a, b]
    if not pair:
        return None
    return {"eyes": [[float(v) for v in e] for e in pair], "lid": [round(float(c) * 0.92, 3) for c in tone]}


if __name__ == "__main__":
    import sys
    for p in sys.argv[1:]:
        print(p, detect(p))
