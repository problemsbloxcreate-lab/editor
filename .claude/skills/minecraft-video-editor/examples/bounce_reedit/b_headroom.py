import json, sys, numpy as np, soundfile as sf
from lib import *
mix = sys.argv[1]; LIM = float(sys.argv[2]) if len(sys.argv) > 2 else -1.5
F = json.load(open(os.path.join(HERE, "plan_sfx.json"), encoding="utf8"))
new, sr = sf.read(mix, always_2d=True)
db = lambda x: 20 * np.log10(x + 1e-9)
n_adj = 0
for x in F:
    a = int(x["t"] * sr); b = int((x["t"] + x["dur"]) * sr)
    pk = db(np.abs(new[a:b]).max())
    if pk > LIM:
        cut = min(6.0, pk - LIM + 0.8)
        x["gdb"] = round(x["gdb"] - cut, 2); x["g"] = 10 ** ((x["gdb"] - 15) / 20.0); n_adj += 1
        print("%.2f %s pico %.1f -> -%.1f dB" % (x["t"], x["key"], pk, cut))
print("ajustados", n_adj)
json.dump(F, open(os.path.join(HERE, "plan_sfx.json"), "w", encoding="utf8"), ensure_ascii=False)
G = [{"t": x["t"], "g": x["g"]} for x in F]
run(PRE + '''var G = %s; r.n = 0;
for (var t = 4; t < 7; t++) { var st = s.audioTracks[t]; for (var k = 0; k < st.clips.numItems; k++) { var cl = st.clips[k];
  for (var i = 0; i < G.length; i++) if (Math.abs(G[i].t - cl.start.seconds) < 0.012) { var p2 = lvl(cl); p2.setTimeVarying(false); p2.setValue(G[i].g, true); r.n++; break; } } }
return __result(r);''' % J(G), "gains", 600)
# onde o mix passa de -1.0 fora dos SFX (base)
base, _ = sf.read(r"D:\Pobrs\bounce\base_mix.wav", always_2d=True); base = base * 4.0
hot = np.where(np.abs(base).max(axis=1) > 10 ** (-1.0 / 20))[0]
print("amostras do base > -1 dBFS:", len(hot), "em", sorted({round(h / sr, 1) for h in hot[::200]})[:20])
