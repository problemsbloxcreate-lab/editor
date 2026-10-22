"""Verificação do render: loudness/true peak, auditoria dos SFX (pico no SFX vs mix logo antes) e folhas de quadros dos efeitos."""
import json, subprocess, sys, os, re
import numpy as np, soundfile as sf
HERE = os.path.dirname(os.path.abspath(__file__))
REN = sys.argv[1]
wav = os.path.join(HERE, "render16k.wav")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", REN, "-vn", "-ac", "1", "-ar", "16000", wav], check=True)
o = subprocess.run(["ffmpeg", "-hide_banner", "-i", REN, "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
I = re.findall(r"I:\s+(-?[\d.]+) LUFS", o)[-1]; TP = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", o)[-1]
print("LOUDNESS integrado %s LUFS | true peak %s dBFS" % (I, TP))
x, sr = sf.read(wav, dtype="float32")
hop = sr // 100; n = len(x) // hop
pk = 20 * np.log10(np.abs(x[:n * hop]).reshape(n, hop).max(axis=1) + 1e-9)
F = json.load(open(os.path.join(HERE, "sfx_placed.json"), encoding="utf8"))
rows = []
for f in F:
    a = int(f["t"] * 100); b = a + int(min(f["dur"], 0.6) * 100)
    base = pk[max(a - 150, 0):max(a - 10, 1)]
    if len(base) < 20 or b >= n: continue
    d = pk[a:b].max() - np.percentile(base, 95)
    rows.append((d, f["t"], f["name"], f["db"]))
ds = np.array([r[0] for r in rows])
print("SFX: delta de pico vs mix antes (p95): mediana %+.1f dB | p10 %+.1f | p90 %+.1f | n=%d" % (np.median(ds), np.percentile(ds, 10), np.percentile(ds, 90), len(ds)))
print("mais BAIXOS (<-1 dB, provavelmente inaudíveis):")
for r in sorted(rows)[:12]: print("   %+5.1f  %7.2f  %-40s ganho %+.1f" % (r[0], r[1], r[2][:40], r[3]))
print("mais ALTOS (>+7 dB):")
for r in sorted(rows)[-10:]:
    if r[0] > 7: print("   %+5.1f  %7.2f  %-40s ganho %+.1f" % (r[0], r[1], r[2][:40], r[3]))
# silêncio total (buracos) > 0,4 s
q = np.where(pk < -55)[0]; holes = []
if len(q):
    st = q[0]; pv = q[0]
    for i in q[1:]:
        if i != pv + 1:
            if pv - st >= 40: holes.append((st / 100, (pv - st) / 100))
            st = i
        pv = i
print("buracos de silêncio total >=0,4 s:", holes[:10])
