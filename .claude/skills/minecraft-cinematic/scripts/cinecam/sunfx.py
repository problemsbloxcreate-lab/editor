"""Sun FX for silhouette shots (post, per frame): god rays occluded by the character, flash, anime starburst, halo.

    sun_fx(master, out_mkv, rig, sun_dir, W, H, fx=lambda t: dict(rays=.., flash=.., burst=.., halo=..))
Sun screen position: analytic projection of the sun direction with each frame's camera, refined on the frame
(yellow core bbox near the estimate) so roll / handheld never misplace the ray origin.
"""
import subprocess
import numpy as np
import cv2


def cam_basis(yaw, pitch):
    y, p = np.radians(yaw), np.radians(pitch)
    f = np.array([-np.sin(y) * np.cos(p), -np.sin(p), np.cos(y) * np.cos(p)])
    r = np.array([-np.cos(y), 0.0, -np.sin(y)])
    u = np.cross(r, f)
    return f, r, u


def project(d, yaw, pitch, roll, fov, W, H):
    f, r, u = cam_basis(yaw, pitch)
    if roll:
        a = np.radians(roll)
        r, u = r * np.cos(a) + u * np.sin(a), u * np.cos(a) - r * np.sin(a)
    df = d @ f
    if df <= 0.05:
        return None
    tv = np.tan(np.radians(fov) / 2); th = tv * W / H
    return np.array([W / 2 + (d @ r) / df / th * W / 2, H / 2 - (d @ u) / df / tv * H / 2])


def sun_mask(img):
    """Warm sun core/halo coverage 0..1 (excludes white clouds and blue sky by R-B and brightness)."""
    R, G, B = img[..., 0], img[..., 1], img[..., 2]
    warm = np.clip((R - B - 0.10) / 0.25, 0, 1)
    bright = np.clip((np.minimum(R, G) - 0.84) / 0.12, 0, 1)      # hot core only (the orange halo would flood the frame)
    return warm * bright


def radial_blur(src, c, length=0.45, n=28):
    h, w = src.shape[:2]
    acc = np.zeros_like(src)
    tot = 0.0
    for i in range(n):
        s = 1.0 - length * i / n
        M = np.array([[s, 0, c[0] * (1 - s)], [0, s, c[1] * (1 - s)]], np.float32)
        wgt = (1 - i / n) ** 1.4
        acc += cv2.warpAffine(src, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT) * wgt
        tot += wgt
    return acc / tot


def starburst(h, w, c, t_rel, n=7, seed=3, colors=((1.0, 0.92, 0.55), (0.70, 1.0, 0.55), (1.0, 0.75, 0.45))):
    """Anime light beams from the sun: shoot out to the frame edge (~0.18 s), then fade and thin."""
    rng = np.random.default_rng(seed)
    angs = np.sort(rng.uniform(0, 2 * np.pi, n)) + rng.uniform(-0.2, 0.2, n)
    img = np.zeros((h, w, 3), np.float32)
    reach = np.clip(t_rel / 0.18, 0, 1) * 1.6 * max(w, h)
    fade = np.clip(1 - (t_rel - 0.25) / 1.1, 0, 1)
    if fade <= 0:
        return img
    for k, a in enumerate(angs):
        wid = (0.022 + 0.018 * rng.random()) * (0.4 + 0.6 * fade)
        p1 = np.array(c) + reach * np.array([np.cos(a - wid), np.sin(a - wid)])
        p2 = np.array(c) + reach * np.array([np.cos(a + wid), np.sin(a + wid)])
        poly = np.array([c, p1, p2], np.int32)
        col = np.array(colors[k % len(colors)], np.float32) * fade
        cv2.fillConvexPoly(img, poly, col.tolist(), lineType=cv2.LINE_AA)
    img = cv2.GaussianBlur(img, (0, 0), 1.5 + 3 * (1 - fade))
    return img


def sun_fx(master, out_mkv, frames, sun_dir, W, H, fps, fx, ffmpeg="ffmpeg", debug_dir=None):
    """frames: dict of arrays (x,y,z,yaw,pitch,roll,fov) per output frame; fx(t) -> dict(rays, flash, burst_t0, halo)."""
    rd = subprocess.Popen([ffmpeg, "-v", "error", "-i", master, "-vf", f"scale={W}:{H}:flags=area", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                          stdout=subprocess.PIPE, bufsize=10 ** 8)
    wr = subprocess.Popen([ffmpeg, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-",
                           "-c:v", "libx264rgb", "-qp", "0", "-preset", "ultrafast", out_mkv], stdin=subprocess.PIPE)
    n = len(frames["yaw"])
    hw, hh = W // 2, H // 2
    warm = np.array([1.0, 0.86, 0.55], np.float32)
    prev_c = None
    for i in range(n):
        buf = rd.stdout.read(W * H * 3)
        if len(buf) < W * H * 3:
            break
        img = np.frombuffer(buf, np.uint8).reshape(H, W, 3).astype(np.float32) / 255.0
        t = i / fps
        p = fx(t)
        if p.get("gamma", 1.0) != 1.0 or p.get("sat", 1.0) != 1.0:      # deepen the sky before adding light (ref: dark blue sky)
            img = np.clip(img, 0, 1) ** p.get("gamma", 1.0)
            g = img.mean(2, keepdims=True)
            img = np.clip(g + (img - g) * p.get("sat", 1.0), 0, 1)
        if p.get("sky", 0) > 0:                                      # deepen only sky-blue pixels (and the lilac fringe)
            R, G, B = img[..., 0], img[..., 1], img[..., 2]
            m = np.clip((B - R + 0.02) / 0.25, 0, 1) * np.clip((B - 0.35) / 0.3, 0, 1) * p["sky"]
            img = img * (1 - m[..., None] * np.array([0.55, 0.38, 0.12], np.float32))
        c = project(sun_dir, frames["yaw"][i], frames["pitch"][i], frames["roll"][i], frames["fov"][i], W, H)
        small = cv2.resize(img, (hw, hh), interpolation=cv2.INTER_AREA)
        m = sun_mask(small)
        if c is not None and m.sum() > 30:                       # refine on the visible core
            ys, xs = np.nonzero(m > 0.6)
            if len(xs) > 20:
                cc = np.array([(xs.min() + xs.max()) / 2 * 2, (ys.min() + ys.max()) / 2 * 2])
                if np.linalg.norm(cc - c) < 0.25 * W:
                    c = cc
        if c is not None:
            c = c if prev_c is None or np.linalg.norm(c - prev_c) > 0.2 * W else 0.6 * c + 0.4 * prev_c
            prev_c = c
        out = img.copy()
        if c is not None and p.get("rays", 0) > 0:
            src = small * m[..., None]
            rays = radial_blur(src, (c[0] / 2, c[1] / 2), length=p.get("ray_len", 0.5))
            rays = cv2.resize(rays, (W, H), interpolation=cv2.INTER_LINEAR)
            out += rays * warm * p["rays"]
        if c is not None and p.get("halo", 0) > 0:
            q = cv2.resize(m, (W // 8, H // 8), interpolation=cv2.INTER_AREA)
            q = cv2.GaussianBlur(q, (0, 0), W * 0.03 / 8)
            out += cv2.resize(q, (W, H), interpolation=cv2.INTER_LINEAR)[..., None] * warm * p["halo"]
        if c is not None and p.get("burst_t", -1) >= 0:
            sb = starburst(hh, hw, (float(c[0]) / 2, float(c[1]) / 2), p["burst_t"])
            out += cv2.resize(sb, (W, H), interpolation=cv2.INTER_LINEAR) * p.get("burst", 1.0)
        if p.get("flash", 0) > 0:
            lum = img.mean(2, keepdims=True)
            out = out + p["flash"] * (1.0 - out) * np.clip(lum * 1.6, 0, 1) ** 0.7
        out = np.clip(out, 0, 1)
        wr.stdin.write((out * 255 + 0.5).astype(np.uint8).tobytes())
        if debug_dir and i % 15 == 0:
            cv2.imwrite(f"{debug_dir}/fx_{i:03d}.jpg", cv2.cvtColor((out * 255).astype(np.uint8), cv2.COLOR_RGB2BGR))
    wr.stdin.close(); wr.wait(); rd.wait()
    return out_mkv
