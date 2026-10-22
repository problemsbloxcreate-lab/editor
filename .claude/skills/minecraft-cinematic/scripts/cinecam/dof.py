"""dof: depth of field from the mod's linear depth stream (gray16, 1/128 block units).

Per frame: circle of confusion from the thin-lens relation coc ~ |1/F - 1/z|*F (0 at the focus plane, ->1 at infinity, >1 close to the
lens, clipped), scaled by `aperture` and the frame width.  Foreground CoC is spread so out-of-focus foreground leaves/trunks get a soft
edge over the sharp subject (the key look of the Bionic forest shot).  Blur is a blend between pre-blurred levels, so cost is
constant per frame.  Input master may be supersampled: both streams are scaled to the output size first.

v0.8 (21/10/2026): same look, ~6-8x faster — gamma via lookup tables, wide blur levels computed at half resolution, the level
blend as a sum of per-level "hat" weights (no (levels,H,W,3) stack), only cv2 calls -> runs on the GPU through OpenCL (cv2.UMat)
when available, CPU otherwise; frames in a small thread pool to overlap decoding/encoding.
"""
from __future__ import annotations

import subprocess
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Sequence

import numpy as np

try:
    import cv2
except ImportError:  # pragma: no cover
    cv2 = None

_TO_LIN = ((np.arange(256) / 255.0) ** 2.2).astype(np.float32)


def _reader(path: str, w: int, h: int, pix: str, ffmpeg: str, scale_flags: str):
    cmd = [ffmpeg, "-v", "error", "-i", path, "-vf", f"scale={w}:{h}:flags={scale_flags}", "-f", "rawvideo", "-pix_fmt", pix, "-"]
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=0)


def _read(p, n) -> Optional[bytearray]:
    """One frame from a raw pipe.  readinto on an unbuffered pipe: ~10x faster than .read(n) with a big buffer on Windows
    (measured 21/10/2026: 180 1080p frames 10.5 s -> 0.9 s)."""
    buf = bytearray(n)
    mv, got = memoryview(buf), 0
    while got < n:
        r = p.stdout.readinto(mv[got:])
        if not r:
            return None
        got += r
    return buf


def _blur(img, r: float, size=None):
    """size=(w,h) is needed for cv2.UMat input (no .shape)."""
    if r <= 0.3:
        return img
    if r < 3.0:
        k = int(r * 3) | 1
        return cv2.GaussianBlur(img, (k, k), r / 1.6)
    w, h = size or (img.shape[1], img.shape[0])                     # wide levels: blur at half size (identical to the eye)
    small = cv2.resize(img, (w // 2, h // 2), interpolation=cv2.INTER_AREA)
    k = int(r * 1.5) | 1
    small = cv2.GaussianBlur(small, (k, k), r / 3.2)
    return cv2.resize(small, (w, h), interpolation=cv2.INTER_LINEAR)


def blur_levels(img, radii: Sequence[float], size=None):
    return [_blur(img, r, size) for r in radii]


def _hat(coc, lo, mid, hi):
    """Linear-interpolation weight of the level at radius `mid` (0 outside [lo, hi]); lo/hi None = open side (weight 1)."""
    w = None
    if lo is not None:
        w = cv2.multiply(cv2.subtract(coc, lo), 1.0 / (mid - lo))
    if hi is not None:
        d = cv2.multiply(cv2.subtract(hi, coc), 1.0 / (hi - mid))
        w = d if w is None else cv2.min(w, d)
    return cv2.min(cv2.max(w, 0.0), 1.0)


def dof_frame(img, z, focus: float, aperture: float, rmax: float, levels: int = 7, size=None):
    """img float32 HxWx3 (0..1, linear light), z float32 HxW in blocks.  Works on numpy arrays or cv2.UMat (OpenCL/GPU):
    only cv2 calls.  Same result as the v0.7 stack/gather version (PSNR > 55 dB)."""
    if focus <= 0 or aperture <= 0.001:
        return img
    zc = cv2.max(z, 0.06)
    coc = cv2.multiply(cv2.absdiff(cv2.divide(1.0, zc), 1.0 / focus), focus)
    coc = cv2.multiply(cv2.min(coc, 1.0), aperture * rmax)       # radius in pixels
    near = cv2.compare(zc, focus * 0.92, cv2.CMP_LT)
    fg = cv2.multiply(coc, cv2.divide(near, 255.0, dtype=cv2.CV_32F))
    fmax = cv2.minMaxLoc(fg)[1]
    if fmax > 0.5:
        coc = cv2.max(coc, cv2.GaussianBlur(fg, (0, 0), max(fmax / 3.0, 1.0)))
    radii = [0.0] + list(np.geomspace(1.2, max(rmax * aperture, 2.0), levels - 1))
    out = None
    for k in range(levels):
        w = _hat(coc, radii[k - 1] if k > 0 else None, radii[k], radii[k + 1] if k < levels - 1 else None)
        if cv2.minMaxLoc(w)[1] <= 0:
            continue
        term = cv2.multiply(img if k == 0 else _blur(img, radii[k], size), cv2.merge([w, w, w]))
        out = term if out is None else cv2.add(out, term)
    return out


_GPU = None


def _use_gpu() -> bool:
    global _GPU
    if _GPU is None:
        _GPU = bool(cv2 is not None and cv2.ocl.haveOpenCL())
        if _GPU:
            cv2.ocl.setUseOpenCL(True)
    return _GPU


def _one(args):
    a, b, w, h, focus, aperture, rmax = args
    img = cv2.LUT(np.frombuffer(a, np.uint8).reshape(h, w, 3), _TO_LIN.reshape(256, 1))
    z = np.frombuffer(b, "<u2").reshape(h, w).astype(np.float32) * (1.0 / 128.0)
    if _use_gpu():
        img, z = cv2.UMat(img), cv2.UMat(z)
    res = dof_frame(img, z, focus, aperture, rmax, size=(w, h))
    o = cv2.convertScaleAbs(cv2.pow(cv2.min(res, (1.0, 1.0, 1.0, 1.0)), 1 / 2.2), alpha=255)   # 3-channel: scalar must be a 4-tuple
    return (o.get() if isinstance(o, cv2.UMat) else o).tobytes()


def apply_dof(master: str, depth: str, focus: Sequence[float], aperture: Sequence[float], out_mkv: str, width: int, height: int,
              fps: float, ffmpeg: str = "ffmpeg", rmax_frac: float = 0.011, progress_every: int = 30, workers: int = 3) -> int:
    """Read both streams, blur per frame (thread pool, order kept), write a lossless RGB master at (width,height).  Returns frames."""
    if cv2 is None:
        raise RuntimeError("opencv (cv2) is required for DoF")
    rd = _reader(master, width, height, "rgb24", ffmpeg, "lanczos")
    dd = _reader(depth, width, height, "gray16le", ffmpeg, "neighbor")
    wr = subprocess.Popen([ffmpeg, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{width}x{height}", "-r", str(fps),
                           "-i", "-", "-c:v", "libx264rgb", "-preset", "ultrafast", "-qp", "0", "-pix_fmt", "rgb24", out_mkv],
                          stdin=subprocess.PIPE)
    n, rmax, done = 0, rmax_frac * width, False
    with ThreadPoolExecutor(max(1, workers)) as ex:
        while not done:
            batch = []
            for _ in range(workers * 2):
                a = _read(rd, width * height * 3)
                b = _read(dd, width * height * 2)
                if a is None or b is None:
                    done = True
                    break
                i = min(n + len(batch), len(focus) - 1)
                batch.append((a, b, width, height, float(focus[i]), float(aperture[i]), rmax))
            for frame in ex.map(_one, batch):
                wr.stdin.write(frame)
            n += len(batch)
    wr.stdin.close()
    wr.wait()
    rd.terminate(); dd.terminate()
    return n
