"""python run.py draft|final id[,id...]  -> D:/Pobrs/tudoagua/cine/out/<id>[_d].mp4 + folha de quadros"""
import sys, time, shutil, subprocess, json
from agua import *
import scenes
mode = sys.argv[1]; ids = sys.argv[2].split(",")
draft = mode == "draft"
OUT = os.path.join(H, "out"); os.makedirs(OUT, exist_ok=True)
shots, cs = [], []
for i in ids:
    c = scenes.CENAS[i](draft)
    sh = c.shot()                 # assa os atores (c.built) antes da câmera, que mira neles
    if getattr(c, "shot_cam", None): c.shot_cam()
    d = c.rig.sample_frames(); folga = np.array([y - gy(x, z) for x, y, z in zip(d["x"], d["y"], d["z"])])
    k = int(np.argmin(folga)); print("%s: folga mínima da câmera %.2f em t=%.2f (%.1f, %.1f, %.1f)%s" % (i, folga[k], d["t"][k], d["x"][k], d["y"][k], d["z"][k], "  << DENTRO DO CHÃO" if folga[k] < 0.3 else ""), flush=True)
    shots.append(sh); cs.append(c)
t0 = time.time()
infos = render_batch(shots, WORLD, xmx="3G")
for c, i in zip(cs, infos):
    r = {"id": c.nome, "T": c.T, "pre": getattr(c, "pre", 0.0), "ok": i.get("ok"), "error": i.get("error"), "warn": (i.get("report") or {}).get("warnings")}
    if i.get("ok"):
        dst = os.path.join(OUT, c.nome + ("_d" if draft else "") + ".mp4"); shutil.copyfile(i["final"], dst); r["file"] = dst
        n = 10; T = c.T
        sel = "+".join(r"eq(n\,%d)" % int(round(k * (T * c.fps - 1) / (n - 1))) for k in range(n))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", dst, "-vf", "select='%s',scale=480:270,tile=5x2" % sel, "-frames:v", "1", "-q:v", "3", dst[:-4] + ".jpg"])
    print(json.dumps(r, ensure_ascii=False), flush=True)
print("tempo %.0f s" % (time.time() - t0))
