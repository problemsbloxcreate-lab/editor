"""Estágios de VÍDEO do Bounce na clone: split (razor nos limites das janelas), zoom (ease-out que fica), presets (BERSERKER). Uso: python b_vis.py split,zoom,presets"""
import json, os, sys
from lib import *
sys.path.insert(0, os.path.expanduser("~/.claude/skills/minecraft-video-editor/scripts"))
import berserker as bz
FPS = 60.0
def snap(t): return round(t * FPS) / FPS

def dump():
    src = open(os.path.join(HERE, "..", "fulldump.jsx"), encoding="utf8").read().replace("__WID__", SEQ)
    open(os.path.join(HERE, "_dump.jsx"), "w", encoding="utf8").write(src)
    run(src, "dump", 400, quiet=True)
    return json.load(open(os.path.join(HERE, "_dump.result.json"), encoding="utf8"))

def visible(d, t):
    for ti in (1, 0):
        for k, c in enumerate(d["V"][ti]["rows"]):
            if c["a"] - 1e-3 <= t < c["b"] - 1e-3 and not c["off"]: return ti, k, c
    return None, None, None

def base_of(c):
    for co in c["c"]:
        if co["n"] == "Movimento":
            sc = [p for p in co["p"] if p["n"] == "Escala"][0]; ps = [p for p in co["p"] if p["n"] == "Posição"][0]
            s0 = sc["k"][0][1] if sc.get("k") else sc["v"]
            p0 = ps["k"][0][1] if ps.get("k") else ps["v"]
            return s0, p0
    return 100.0, [0.5, 0.5]

def windows(d, plan):
    """[(t, fim, tipo, item)] com fim limitado ao clipe visível que começa em t (nunca atravessa corte)"""
    W = []
    for z in plan["zooms"]:
        t = snap(z["t"]); ti, k, c = visible(d, t + 0.01)
        end = snap(min(t + z["hold"], c["b"])); W.append({"t": t, "end": end, "kind": "zoom", "z": z})
    for p in plan["presets"]:
        t = snap(p["t"]); ti, k, c = visible(d, t + 0.01)
        end = snap(min(t + p["len"], c["b"])); W.append({"t": t, "end": end, "kind": "preset", "p": p})
    # janelas com o mesmo início (zoom+preset): une no maior fim (um clipe só)
    byt = {}
    for w in W: byt.setdefault(w["t"], []).append(w)
    for t, ws in byt.items():
        e = max(w["end"] for w in ws)
        for w in ws: w["end"] = e
    return W

def main():
    stages = sys.argv[1].split(",")
    plan = json.load(open(os.path.join(HERE, "plan_v_raw.json"), encoding="utf8"))
    d = dump()
    W = windows(d, plan)
    if "split" in stages:
        ts = set()
        for w in W: ts.add(w["t"]); ts.add(w["end"])
        allb = {round(c["a"], 3) for t in d["V"] for c in t["rows"]} | {round(c["b"], 3) for t in d["V"] for c in t["rows"]}
        ts = sorted(t for t in ts if not any(abs(t - b) < 0.02 for b in allb))
        print("razors de vídeo:", len(ts), ts)
        for i in range(0, len(ts), 40):
            run(PRE + '''app.enableQE(); var q = qe.project.getActiveSequence(); var T = %s; for (var i = 0; i < T.length; i++) { q.getVideoTrackAt(0).razor(tc(T[i])); q.getVideoTrackAt(1).razor(tc(T[i])); } return __result(r);''' % J(ts[i:i + 40]), "split", 600)
        d = dump()
    if "zoom" in stages:
        Z = []
        for w in W:
            if w["kind"] != "zoom": continue
            z = w["z"]; t0 = w["t"]; ti, k, c = visible(d, t0 + 0.01)
            if c is None or abs(c["a"] - t0) > 0.03: print("zoom sem clipe começando em", t0, c and c["a"]); continue
            dur = c["b"] - c["a"]; ramp = min(z["ramp"], dur)
            s0, p0 = base_of(c)
            fx, fy = 0.5, 0.5
            n = 6; keys = []
            for j in range(n + 1):
                u = j / n; e = 1 - (1 - u) ** 2.2; zz = 1 + (z["s1"] / 100.0 - 1) * e
                keys.append([round(c["i"] + ramp * u, 4), round(s0 * zz, 3), round(fx + (p0[0] - fx) * zz, 5), round(fy + (p0[1] - fy) * zz, 5)])
            keys.append([round(c["i"] + dur - 0.001, 4), keys[-1][1], keys[-1][2], keys[-1][3]])
            Z.append({"tr": ti, "t": c["a"], "keys": keys, "s0": s0, "p0": p0})
        print("zooms:", len(Z))
        run(PRE + '''var Z = %s; r.n = 0;
function clipAt(tr, t) { for (var k = 0; k < tr.clips.numItems; k++) { var c = tr.clips[k]; if (Math.abs(c.start.seconds - t) < 0.012) return k; } return -1; }
for (var n = 0; n < Z.length; n++) { var tr = s.videoTracks[Z[n].tr]; var k = clipAt(tr, Z[n].t); if (k < 0) continue; var mo = tr.clips[k].components[1]; var sc = mo.properties[1], ps = mo.properties[0];
  sc.setTimeVarying(false); ps.setTimeVarying(false); sc.setValue(Z[n].s0, true); ps.setValue(Z[n].p0, true);
  sc.setTimeVarying(true); ps.setTimeVarying(true);
  for (var j = 0; j < Z[n].keys.length; j++) { var K = Z[n].keys[j]; sc.addKey(K[0]); sc.setValueAtKey(K[0], K[1]); ps.addKey(K[0]); ps.setValueAtKey(K[0], [K[2], K[3]]); } r.n++; }
return __result(r);''' % J(Z), "zoom", 900)
    if "presets" in stages:
        by_tr = {0: [], 1: []}
        for w in W:
            if w["kind"] != "preset": continue
            p = w["p"]; t0 = w["t"]; ti, k, c = visible(d, t0 + 0.01)
            if c is None or abs(c["a"] - t0) > 0.03: print("preset sem clipe começando em", t0); continue
            ln = c["b"] - c["a"]
            by_tr[ti].append((k, bz.spec(p["name"], k, c["i"], ln, anchor=p.get("anchor"), tscale=p.get("tscale", 1.0))))
        for ti, items in by_tr.items():
            if not items: continue
            SP = [sp for k, sp in items]
            run(PRE + '''app.enableQE(); var q = qe.project.getActiveSequence(); var TRK = %d; var tr = s.videoTracks[%d];
''' % (ti, ti) + bz.APPLY_JS % J(SP) + '''return __result(r);''', "presets%d" % ti, 900)

main()
