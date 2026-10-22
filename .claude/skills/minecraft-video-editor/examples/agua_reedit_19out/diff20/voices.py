import json, math, collections, os, sys
from mapping import *


def db(l):
    try: return round(20 * math.log10(l) + 15, 2) if l > 0 else -99
    except Exception: return None


def comp_summary(d, tr, label):
    t = d["A"][tr]; print("== %s A%d" % (label, tr + 1), t["name"], "muted", t["muted"], "n", len(t["clips"]), "tx", len(t["tx"]))
    cnt = collections.Counter(); fx = collections.Counter(); kfn = 0; files = collections.Counter(); dis = 0
    params = collections.defaultdict(collections.Counter)
    for c in t["clips"]:
        files[os.path.basename(c["f"])] += 1; dis += c["d"]
        for comp in c.get("c", []):
            fx[comp["n"]] += 1
            if comp["n"] == "Volume":
                for p in comp["p"]:
                    if p["n"] == "Nível":
                        if "kf" in p: kfn += 1
                        else: cnt[db(p["v"])] += 1
            elif comp["n"] not in ("Volume do canal", "Panorâmico", "Panner", "Volume"):
                for p in comp["p"]:
                    params[comp["n"]][(p["n"], json.dumps(p.get("v", p.get("kf")))[:60])] += 1
    print(" files", files.most_common(4), "disabled", dis)
    print(" comps", fx.most_common())
    print(" levels", sorted(cnt.items(), key=lambda x: -x[1])[:15], "| kf", kfn)
    for k, v in params.items():
        print("  FX", k, v.most_common(12))


if __name__ == "__main__":
    for tr in range(3):
        comp_summary(HIS, tr, "DELE")
