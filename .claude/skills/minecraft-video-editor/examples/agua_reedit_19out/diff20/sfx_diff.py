import json, os, collections
from mapping import *
from voices import db
from music_diff import lvl
MINE = json.load(open(os.path.expanduser("~/Skills/_research/mc-agua-edit/sfx_placed.json"), encoding="utf8"))
for m in MINE: m["tn"] = old2new(m["t"]) if old2new(m["t"]) is not None else old2new(m["t"] + 0.05)

his = []
for tr in range(4, len(HIS["A"])):
    t = HIS["A"][tr]
    if not t: continue
    for c in t["clips"]:
        if "Epidemic" in c["f"]: continue
        his.append({"name": os.path.basename(c["f"]), "t": c["s"], "e": c["e"], "i": c["i"], "lvl": lvl(c), "d": c["d"], "tr": tr,
                    "fx": [comp["n"] for comp in c["c"] if comp["n"] not in ("Volume", "Volume do canal", "Panorâmico")]})
his.sort(key=lambda x: x["t"])

used = set(); rows = []
for m in MINE:
    best = None
    for j, h in enumerate(his):
        if j in used or h["name"] != m["name"] or m["tn"] is None: continue
        dt = h["t"] - m["tn"]
        if abs(dt) < 4 and (best is None or abs(dt) < abs(best[1])): best = (j, dt)
    if best: used.add(best[0]); rows.append((m, his[best[0]], best[1]))
    else: rows.append((m, None, None))
new = [h for j, h in enumerate(his) if j not in used]

out = []
kept = moved = removed = off = regain = 0
for m, h, dt in rows:
    if h is None:
        removed += 1; out.append("REMOVIDO  %s %-42s %5.1f dB | %s" % (tc(m["tn"]), m["name"][:42], m["db"], m["why"][:60])); continue
    g = h["lvl"]; flag = []
    if h["d"]: flag.append("DESABILITADO"); off += 1
    if isinstance(g, (int, float)) and abs(g - m["db"]) > 0.6: flag.append("ganho %+.1f -> %+.1f" % (m["db"], g)); regain += 1
    elif not isinstance(g, (int, float)): flag.append("ganho %s" % (g,))
    if abs(dt) > 0.04: flag.append("moveu %+.2fs" % dt); moved += 1
    if abs((h["e"] - h["t"]) - m["dur"]) > 0.05: flag.append("dur %.2f->%.2f" % (m["dur"], h["e"] - h["t"]))
    if h["fx"]: flag.append("fx " + ",".join(h["fx"]))
    if not flag: kept += 1
    out.append("%-9s %s %-42s | %s | %s" % ("mantido" if not flag else "ALTERADO", tc(h["t"]), m["name"][:42], "; ".join(flag), m["why"][:50]))
for h in new:
    out.append("NOVO      %s %-42s %s dur %.2f in %.2f A%d%s %s" % (tc(h["t"]), h["name"][:42], h["lvl"], h["e"] - h["t"], h["i"], h["tr"] + 1, " OFF" if h["d"] else "", ",".join(h["fx"])))
print("meus %d | dele %d | intactos %d | removidos %d | desabilitados %d | reganho %d | movidos %d | novos %d" % (len(MINE), len(his), kept, removed, off, regain, moved, len(new)))
for l in sorted(out, key=lambda s: s.split()[1] if len(s.split()) > 1 else ""):
    print(l)
