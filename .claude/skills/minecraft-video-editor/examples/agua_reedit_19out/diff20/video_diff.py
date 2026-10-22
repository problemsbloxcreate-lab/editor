import json, os, collections
from mapping import *
PLAN = json.load(open(os.path.expanduser("~/Skills/_research/mc-agua-edit/plan.json"), encoding="utf8"))
BASE = ("Opacidade", "Movimento", "Remapeamento de tempo")


def motion(c):
    o = {}
    for comp in c["c"]:
        if comp["n"] == "Movimento":
            for p in comp["p"]:
                o[p["n"]] = p.get("v", ("kf", p.get("kf")))
        if comp["n"] == "Opacidade":
            for p in comp["p"]:
                if p["n"] == "Opacidade": o["op"] = p.get("v", ("kf", p.get("kf")))
    return o


def fxs(c): return [comp["n"] for comp in c["c"] if comp["n"] not in BASE]


def scale_str(c):
    m = motion(c); s = m.get("Escala")
    if isinstance(s, tuple):
        k = s[1]; return "kf[" + " ".join("%.2f:%.0f" % (x[0] - c["i"], x[1]) for x in k[:8]) + "]"
    if m.get("Dimensionar uniformemente") is False: return "%sx%s" % (m.get("Dimensionar largura"), s)
    return "%.0f" % s if isinstance(s, (int, float)) else str(s)


def pos_str(c):
    p = motion(c).get("Posição")
    if isinstance(p, tuple): return "kf"
    return "%.3f,%.3f" % tuple(p) if p else "?"


def rot(c):
    r = motion(c).get("Rotação")
    return r if not isinstance(r, (int, float)) or abs(r) > 0.01 else 0


V1 = HIS["V"][0]["clips"]


def clip_at(t, tr=0):
    for k, c in enumerate(HIS["V"][tr]["clips"]):
        if c["s"] - 0.02 <= t < c["e"] - 0.001: return k, c
    return None, None


ev = collections.defaultdict(list)
for kind in ("zooms", "stretch", "presets", "reveals"):
    for x in PLAN[kind]:
        tn = old2new(x["t"]) if old2new(x["t"]) is not None else old2new(x["t"] + 0.03)
        if tn is None: print("SEM MAPA", kind, x); continue
        k, c = clip_at(tn + 0.01)
        ev[k].append((kind, x))

lines = []
for k, c in enumerate(V1):
    mine = ev.get(k, [])
    sc = scale_str(c); fx = fxs(c); r = rot(c)
    nonbase = sc not in ("100",) or fx or r or c["d"] or c["n"] != "VIDEO ORIGINAL"
    if not mine and not nonbase: continue
    ms = []
    for kind, x in mine:
        if kind == "zooms": ms.append("Z %s%s" % (x["s"], " r%.1f" % x["ramp"] if x["ramp"] else ""))
        elif kind == "stretch": ms.append("ST %sx%s" % (x["sx"], x["sy"]))
        elif kind == "presets": ms.append("P " + x["name"])
        else: ms.append("RV " + x["kind"])
    why = "; ".join(sorted({x.get("why", "") for _, x in mine}))[:60]
    lines.append("%s %5.2fs | eu: %-34s | ele: %-28s pos %s rot %s fx %s %s%s | %s" % (
        tc(c["s"]), c["e"] - c["s"], ", ".join(ms)[:34], sc[:28], pos_str(c), r, ",".join(fx)[:60], " OFF" if c["d"] else "",
        "" if c["n"] == "VIDEO ORIGINAL" else " [" + c["n"] + "]", why))
print("\n".join(lines))
print("\n== V2..V4 dele")
for tr in range(1, len(HIS["V"])):
    for c in HIS["V"][tr]["clips"]:
        print("V%d %s-%s %-40s in %.2f scale %s pos %s op %s fx %s%s" % (tr + 1, tc(c["s"]), tc(c["e"]), os.path.basename(c["f"])[:40] or c["n"], c["i"], scale_str(c)[:40], pos_str(c),
              str(motion(c).get("op"))[:60], ",".join(fxs(c)), " OFF" if c["d"] else ""))
print("\n== overlays meus")
for o in PLAN["overlays"]:
    print(o["kind"], tc(old2new(o["t"])), o["dur"], os.path.basename(o["file"]), o.get("why", ""))
