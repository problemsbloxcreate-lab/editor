"""Checagem objetiva do resultado (sem ouvir): lacunas de fala na VOZ reconstruída a partir dos keeps do plano + loudness/true peak do render.
Uso: python check_final.py <plan2.json> <s1.wav> <s2.wav> [render.mp4]
Falha (exit 1) se sobrar lacuna de fala > MAXGAP (0.32 s) — regra do Matheus: "silêncio mata o ritmo".
"""
import sys, json, subprocess, re
import numpy as np, soundfile as sf
MAXGAP = 0.32
plan = json.load(open(sys.argv[1], encoding="utf8"))
s1, s2 = sys.argv[2], sys.argv[3]
ON, OFF = -38.0, -46.0
HOP = 0.01
FS = sf.info(s1).samplerate            # 21/10: taxa real do WAV (antes supunha 48 kHz)
def seg(path, a, b):
    x, sr = sf.read(path, start=int(a * FS), stop=int(b * FS), always_2d=True, dtype="float32"); return x.mean(axis=1)
v1 = np.concatenate([seg(s1, k["src_in"], k["src_out"]) for k in plan["keeps"]])
v2 = np.concatenate([seg(s2, k["src_in"], k["src_out"]) for k in plan["keeps"]])
n = int(HOP * FS); m = min(len(v1), len(v2)) // n
db = lambda v: 20 * np.log10(np.sqrt((v[:m * n].reshape(m, n) ** 2).mean(axis=1)) + 1e-9)
v = np.maximum(db(v1), db(v2))
act = v > ON; ext = act.copy()
for i in range(1, m):
    if not ext[i] and ext[i - 1] and v[i] > OFF: ext[i] = True
for i in range(m - 2, -1, -1):
    if not ext[i] and ext[i + 1] and v[i] > OFF: ext[i] = True
gaps, i = [], 0
while i < m:
    if not ext[i]:
        j = i
        while j < m and not ext[j]: j += 1
        gaps.append((i * HOP, j * HOP)); i = j
    else: i += 1
big = [(a, b) for a, b in gaps if b - a > MAXGAP]
print("duração %.2f s | lacunas de fala: %d (>=0.2s: %d) | maior %.2f s | soma %.1f s" % (m * HOP, len(gaps), sum(1 for a, b in gaps if b - a >= 0.2), max([b - a for a, b in gaps] or [0]), sum(b - a for a, b in gaps)))
for a, b in big: print("  LACUNA %.2f-%.2f (%.2fs) na timeline" % (a, b, b - a))
if len(sys.argv) > 4:
    p = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", sys.argv[4], "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True)
    I = re.findall(r"I:\s+(-?[\d.]+) LUFS", p.stderr); tp = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", p.stderr)
    print("render: %s LUFS integrado, true peak %s dBTP" % (I[-1] if I else "?", tp[-1] if tp else "?"))
sys.exit(1 if big else 0)
