"""post: ffmpeg-only finishing (grade, bloom, vignette, grain, lens fringing, letterbox) from the lossless master.

A grade preset is a dict; presets compose a filter graph.  Everything is deterministic and needs only ffmpeg.
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Dict, Optional

PRESETS: Dict[str, dict] = {
    # insert (v0.8): cutaway INSIDE a gameplay video — keeps the vanilla colours the gameplay has, adds the film touch:
    # highlight roll-off (sky/sand/water never clip hard), a hair of toe, soft bloom, light lens vignette; no grain/sharpen/CA
    "insert": dict(curves="0/0 0.05/0.04 0.5/0.5 0.9/0.875 1/0.965", sat=1.04, contrast=1.02, bloom=0.07, bloom_radius=22, vignette=0.12),
    # clean: only proper encode.  Use for gameplay-style shots / when shaders already provide the look.
    "clean": dict(),
    # punchy YouTube Minecraft look (like the Bionic / Problems refs): saturated, contrasty, slight bloom
    "punchy": dict(sat=1.18, contrast=1.08, gamma=0.98, bloom=0.12, bloom_radius=18, vignette=0.18, sharpen=0.6, grain=0),
    # toon: bright comedic Minecraft look - saturated, almost no haze
    "toon": dict(sat=1.12, contrast=1.07, gamma=1.0, bloom=0.04, bloom_radius=14, vignette=0.12, sharpen=0.5, grain=0),
    # cinematic: filmic S-curve, teal shadows / warm highlights, vignette, grain, soft bloom
    "cinematic": dict(sat=1.05, contrast=1.12, gamma=1.0, split_tone=True, bloom=0.16, bloom_radius=26, vignette=0.32, grain=5, sharpen=0.4, ca=1),
    "moody": dict(sat=0.88, contrast=1.18, gamma=0.94, split_tone=True, bloom=0.2, bloom_radius=30, vignette=0.45, grain=7, sharpen=0.3, ca=1, cool=True),
    "golden": dict(sat=1.12, contrast=1.08, gamma=1.0, warm=True, bloom=0.22, bloom_radius=34, vignette=0.28, grain=4, sharpen=0.4),
    "horror": dict(sat=0.7, contrast=1.25, gamma=0.88, cool=True, bloom=0.2, bloom_radius=22, vignette=0.6, grain=9, sharpen=0.2, ca=2),
}


def build_filter(p: dict, width: int, height: int, letterbox: Optional[float] = None, fps: Optional[float] = None) -> str:
    chain = []
    if p.get("curves"):
        chain.append(f"curves=all='{p['curves']}'")
    if p.get("denoise"):
        chain.append("hqdn3d=1.5:1.5:6:6")
    eq = []
    if "contrast" in p: eq.append(f"contrast={p['contrast']}")
    if "sat" in p: eq.append(f"saturation={p['sat']}")
    if "gamma" in p: eq.append(f"gamma={p['gamma']}")
    if eq:
        chain.append("eq=" + ":".join(eq))
    if p.get("split_tone"):
        chain.append("colorbalance=rs=-0.05:gs=0.0:bs=0.07:rm=0.0:gm=0.0:bm=0.03:rh=0.07:gh=0.02:bh=-0.07")
    if p.get("warm"):
        chain.append("colorbalance=rs=0.04:bs=-0.05:rm=0.05:bm=-0.05:rh=0.08:gh=0.03:bh=-0.09")
    if p.get("cool"):
        chain.append("colorbalance=rs=-0.06:bs=0.08:rm=-0.04:bm=0.06:rh=-0.02:bh=0.04")
    if p.get("ca"):
        chain.append(f"rgbashift=rh=-{p['ca']}:bh={p['ca']}:edge=smear")
    base = ",".join(chain) if chain else "null"
    bloom = p.get("bloom", 0)
    if bloom:
        r = p.get("bloom_radius", 20)
        g = (f"[0:v]{base},split[a][b];[b]curves=all='0/0 0.72/0 0.9/0.35 1/1',gblur=sigma={r}[bl];"
             f"[a][bl]blend=all_mode=screen:all_opacity={bloom}[bb]")
        tail = "[bb]"
    else:
        g = f"[0:v]{base}[bb]"
        tail = "[bb]"
    post = []
    if p.get("vignette"):
        # forward = darken the corners (backward, used until 20/10/2026, BRIGHTENED them: measured 128 -> 255 in the corners)
        post.append(f"vignette=angle={0.25 + p['vignette'] * 0.8:.3f}:mode=forward")
    if p.get("sharpen"):
        post.append(f"unsharp=5:5:{p['sharpen']}:5:5:0")
    if p.get("grain"):
        post.append(f"noise=alls={p['grain']}:allf=t+u")
    if letterbox:
        h2 = int(round(width / letterbox / 2) * 2)
        post.append(f"crop={width}:{h2}")
    post.append("scale=out_color_matrix=bt709:out_range=tv,format=yuv420p,setparams=colorspace=bt709:color_primaries=bt709:color_trc=bt709:range=tv")   # tagged BT.709 like the OBS gameplay (no hue shift in Premiere)
    return g + f";{tail}" + ",".join(post) + "[out]"


def finish(master: str, out_mp4: str, preset: str = "cinematic", letterbox: Optional[float] = None, crf: int = 14,
           width: int = 1920, height: int = 1080, ffmpeg: str = "ffmpeg", scale: Optional[str] = None,
           audio: Optional[str] = None, fps: Optional[float] = None, extra: Optional[dict] = None) -> str:
    """Master (lossless) -> final mp4.  scale='1920:1080' downsamples a supersampled master with lanczos (free anti-aliasing)."""
    p = dict(PRESETS[preset]) if preset in PRESETS else {}
    if extra:
        p.update(extra)
    fg = build_filter(p, width, height, letterbox)
    if scale:
        fg = fg.replace("[0:v]", f"[0:v]scale={scale}:flags=lanczos,", 1)
    cmd = [ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-i", master]
    if audio:
        cmd += ["-i", audio]
    cmd += ["-filter_complex", fg, "-map", "[out]"]
    if audio:
        cmd += ["-map", "1:a", "-c:a", "aac", "-b:a", "256k", "-shortest"]
    cmd += ["-c:v", "libx264", "-preset", "slow", "-crf", str(crf), "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv"]
    if fps:
        cmd += ["-r", str(fps)]
    cmd += [out_mp4]
    Path(out_mp4).parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("ffmpeg post failed:\n" + r.stderr[-2000:] + "\n" + " ".join(cmd))
    return out_mp4
