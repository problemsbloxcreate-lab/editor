import json, os, subprocess, re, sys
from music_diff import lvl
from mapping import HIS
rows = []
for tr in (3, 6):
    for c in HIS["A"][tr]["clips"]:
        if "Epidemic" not in c["f"] or c["e"] - c["s"] < 3: continue
        l = lvl(c); l = l[1][0][1] if isinstance(l, tuple) else l
        out = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-ss", str(c["i"]), "-t", str(min(c["e"] - c["s"], 30)), "-i", c["f"], "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True, encoding="utf8", errors="ignore").stderr
        m = re.findall(r"I:\s+(-?[\d.]+) LUFS", out)
        L = float(m[-1]) if m else None
        rows.append((l, L, os.path.basename(c["f"])[3:32], c["s"]))
import statistics as st
for l, L, n, s in sorted(rows, key=lambda r: r[3]):
    print("%6.1f dB  track %6.1f LUFS  -> efetivo %6.1f  %s %.0f" % (l, L, l + L - 15 if L else 0, n, s))
eff = [l + L - 15 for l, L, n, s in rows if L]
print("efetivo mediana %.1f  p10 %.1f  p90 %.1f" % (st.median(eff), sorted(eff)[len(eff)//10], sorted(eff)[9*len(eff)//10]))
