import json, math, os, collections
from mapping import *
from voices import db
PLAN = json.load(open(os.path.expanduser("~/Skills/_research/mc-agua-edit/plan.json"), encoding="utf8"))
mine = []
M = PLAN["music"]
for i, m in enumerate(M):
    end = M[i + 1]["t"] if i + 1 < len(M) else PLAN["end"]
    mine.append((m["t"], end, os.path.basename(m["file"]) if m["file"] else "(silêncio)", m.get("src"), m.get("g"), m.get("why", "")))


def lvl(c):
    for comp in c["c"]:
        if comp["n"] == "Volume":
            for p in comp["p"]:
                if p["n"] == "Nível":
                    return ("kf", [(k[0], db(k[1])) for k in p["kf"]]) if "kf" in p else db(p["v"])


def short(n): return n.replace("ES_", "").replace(".mp3", "")[:34]


def fx(c):
    return [comp["n"] for comp in c["c"] if comp["n"] not in ("Volume", "Volume do canal", "Panorâmico")]


if __name__ == "__main__":
    his = []
    for tr in range(3, len(HIS["A"])):
        t = HIS["A"][tr]
        if not t: continue
        for c in t["clips"]:
            if tr == 3 or "Epidemic" in c["f"]:
                his.append((c["s"], c["e"], os.path.basename(c["f"]), c["i"], lvl(c), c["d"], tr, fx(c), c["f"]))
    his.sort()
    print("MINHA (tl antiga -> tl nova):")
    for a, b, n, src, g, why in mine:
        print(" %s-%s -> %s  %-36s src %5s g %s  | %s" % (tc(a), tc(b), tc(old2new(a)), short(n), src, g, why[:50]))
    print("\nDELE (tl nova, faixa A%s):")
    for a, b, n, i, l, d, tr, f, path in his:
        folder = path.split("\\")[-2] if "\\" in path else ""
        print(" A%d %s-%s (%5.1fs) %-36s [%s] in %6.2f lvl %s%s %s" % (tr + 1, tc(a), tc(b), b - a, short(n), folder[:14], i, l, " OFF" if d else "", f))
