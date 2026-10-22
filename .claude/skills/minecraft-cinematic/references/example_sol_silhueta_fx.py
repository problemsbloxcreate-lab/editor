import sys, json, os, time; sys.path.insert(0, '.')
from borracha_c2 import *
from cinecam import post
import post_sun

T_LOCK = 3.95          # he locks into the sun centre -> flash + burst


def fx(t):
    if t < CUT1:
        return dict(rays=0.22, halo=0.05, ray_len=0.4, gamma=1.12, sat=1.08, sky=0.45)
    if t < CUT2:
        u = (t - CUT1) / (CUT2 - CUT1)
        return dict(rays=0.25 + 0.15 * u, halo=0.05, ray_len=0.45, gamma=1.15 + 0.1 * u, sat=1.1, sky=0.55 + 0.2 * u)
    d = dict(rays=0.3, halo=0.06, ray_len=0.5, gamma=1.35, sat=1.12, sky=0.9)
    pre = np.clip((t - (T_LOCK - 0.2)) / 0.2, 0, 1)
    d["flash"] = float(0.92 * np.exp(-((t - T_LOCK) / 0.07) ** 2) + 0.25 * pre * (t < T_LOCK))
    if t >= T_LOCK:
        k = t - T_LOCK
        d["rays"] = float(0.35 + 0.45 * np.exp(-k * 2.2))
        d["ray_len"] = 0.6
        d["burst_t"] = float(k)
        d["burst"] = 0.75
        d["halo"] = float(0.06 + 0.12 * np.clip((k - 0.3) / 0.6, 0, 1))
    return d


if __name__ == "__main__":
    info = json.load(open(OUT + "/render_info.json"))
    master = info["master"]
    rig = build_rig(subframes=8)
    fr = rig.sample_frames()
    dbg = OUT + "/fxdbg"; os.makedirs(dbg, exist_ok=True)
    t0 = time.time()
    fxm = post_sun.sun_fx(master, OUT + "/borracha_c2_fx.mkv", fr, SUN, 1920, 1080, FPS, fx, debug_dir=dbg)
    post.PRESETS["sunlit"] = dict(sat=1.12, contrast=1.10, gamma=0.98, bloom=0.05, bloom_radius=24, vignette=0.32, sharpen=0.4, grain=3)
    post.finish(fxm, OUT + "/borracha_c2.mp4", preset="sunlit", crf=14, width=1920, height=1080, fps=FPS)
    print("done", round(time.time() - t0))
