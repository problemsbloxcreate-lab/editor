"""Reajuste em malha fechada dos ganhos de SFX a partir do render (audit): clip_novo = clip + (alvo - medido), alvo = delta planejado + 0.8; teto de pico -4 dBFS; teto de clipe +15 dB."""
import json, sys, numpy as np, soundfile as sf
from lib import *
mix = sys.argv[1]
F = json.load(open(os.path.join(HERE, "plan_sfx.json"), encoding="utf8"))
base, sr = sf.read(r"D:\Pobrs\bounce\base_mix.wav", always_2d=True)
new, _ = sf.read(mix, always_2d=True)
n = min(len(base), len(new)); base = base[:n] * 4.0; new = new[:n]; sfx = new - base
def db(x): return 20 * np.log10(x + 1e-9)
out = []
for x in F:
    a = int(x["t"] * sr); b = int((x["t"] + min(x["dur"], 1.5)) * sr)
    ps = db(np.abs(sfx[a:b]).max())
    a2 = int(max(x["t"] - 1.0, 0) * sr); b2 = int((x["t"] + 1.5) * sr)
    seg = np.abs(base[a2:b2]).max(axis=1); hop = int(0.05 * sr)
    fp = np.array([seg[i:i + hop].max() for i in range(0, len(seg) - hop, hop)]); pb = db(np.percentile(fp, 90))
    meas = ps - pb
    tgt = x["delta"] + 0.8
    corr = max(-7.0, min(7.0, tgt - meas))
    g = x["gdb"] + corr
    # teto de pico absoluto do SFX (-4 dBFS) e do clipe (+15)
    over = (ps + corr) - (-4.0)
    if over > 0: g -= over
    g = min(g, 15.0)
    out.append((x["t"], x["key"], round(meas, 1), round(tgt, 1), round(g - x["gdb"], 1)))
    x["gdb_old"] = x["gdb"]; x["gdb"] = round(g, 2); x["g"] = 10 ** ((g - 15) / 20.0)
json.dump(F, open(os.path.join(HERE, "plan_sfx.json"), "w", encoding="utf8"), ensure_ascii=False)
for o in out:
    if abs(o[4]) >= 3: print(o)
G = [{"t": x["t"], "g": x["g"]} for x in F]
run(PRE + '''var G = %s; r.n = 0;
for (var t = 4; t < 7; t++) { var st = s.audioTracks[t]; for (var k = 0; k < st.clips.numItems; k++) { var cl = st.clips[k];
  for (var i = 0; i < G.length; i++) if (Math.abs(G[i].t - cl.start.seconds) < 0.012) { var p2 = lvl(cl); p2.setTimeVarying(false); p2.setValue(G[i].g, true); r.n++; break; } } }
return __result(r);''' % J(G), "gains", 600)
