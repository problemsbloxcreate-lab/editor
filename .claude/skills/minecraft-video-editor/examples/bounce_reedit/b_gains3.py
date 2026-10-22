import json, numpy as np, soundfile as sf
from lib import *
F = json.load(open(os.path.join(HERE, "plan_sfx.json"), encoding="utf8"))
voz, sr = sf.read("D:/Pobrs/bounce/stem3_voz.wav", always_2d=True); sfx, _ = sf.read("D:/Pobrs/bounce/stem3_sfx.wav", always_2d=True)
n = min(len(voz), len(sfx)); voz, sfx = voz[:n], sfx[:n]
db = lambda x: 20 * np.log10(x + 1e-9)
for x in F:
    a = int(x["t"] * sr); b = int((x["t"] + min(x["dur"], 1.5)) * sr)
    ps = db(np.abs(sfx[a:b]).max())
    a2 = int(max(x["t"] - 1.0, 0) * sr); b2 = int((x["t"] + 1.5) * sr)
    seg = np.abs(voz[a2:b2]).max(axis=1); hop = int(0.05 * sr)
    fp = np.array([seg[i:i + hop].max() for i in range(0, max(len(seg) - hop, 1), hop)]); pb = db(np.percentile(fp, 90))
    meas = ps - pb
    tgt = max(-5.0, min(0.5, x["delta"] - 1.5))
    corr = max(-8.0, min(8.0, tgt - meas))
    g = min(x["gdb"] + corr, 15.0)
    x["gdb"] = round(g, 2); x["g"] = 10 ** ((g - 15) / 20.0)
json.dump(F, open(os.path.join(HERE, "plan_sfx.json"), "w", encoding="utf8"), ensure_ascii=False)
G = [{"t": x["t"], "g": x["g"]} for x in F]
run(PRE + '''var G = %s; r.n = 0;
for (var t = 5; t < 8; t++) { var st = s.audioTracks[t]; for (var k = 0; k < st.clips.numItems; k++) { var cl = st.clips[k];
  for (var i = 0; i < G.length; i++) if (Math.abs(G[i].t - cl.start.seconds) < 0.012) { var p2 = lvl(cl); p2.setTimeVarying(false); p2.setValue(G[i].g, true); r.n++; break; } } }
return __result(r);''' % J(G), "gains", 600)
