from lib import *
rem2 = sorted(json.load(open(os.path.join(HERE, os.environ.get("PASSFILE","remove2_ok.json")))))
def new2(t):
    acc = 0
    for a, b in rem2:
        if t >= b: acc += b - a
        elif t > a: acc += t - a; break
        else: break
    return t - acc
# 1) marcadores: recria nos tempos novos
out = run(PRE + '''var L = []; var m = s.markers.getFirstMarker(); while (m) { L.push([m.start.seconds, m.name, m.comments]); m = s.markers.getNextMarker(m); } r.L = L; return __result(r);''', "mk_read", 120, quiet=True)
L = json.loads(out.strip().splitlines()[-1])["L"]
MK = [{"t": round(new2(t), 3), "name": n, "c": c} for t, n, c in L]
run(PRE + '''var list = []; var m = s.markers.getFirstMarker(); while (m) { list.push(m); m = s.markers.getNextMarker(m); } for (var k = 0; k < list.length; k++) s.markers.deleteMarker(list[k]);
var MK = %s; r.n = 0; for (var q = 0; q < MK.length; q++) { var mk = s.markers.createMarker(MK[q].t); mk.name = MK[q].name; mk.comments = MK[q].c; r.n++; } return __result(r);''' % J(MK), "mk_write", 300)
# 2) planos
P = json.load(open(os.path.join(HERE, "plan_sfx.json"), encoding="utf8"))
for x in P: x["t"] = round(new2(x["t"]), 4)
json.dump(P, open(os.path.join(HERE, "plan_sfx.json"), "w", encoding="utf8"), ensure_ascii=False)
M = json.load(open(os.path.join(HERE, "plan_music.json"), encoding="utf8"))
for x in M: x["a"] = round(new2(x["a"]), 3); x["b"] = round(new2(x["b"]), 3)
json.dump(M, open(os.path.join(HERE, "plan_music.json"), "w", encoding="utf8"), ensure_ascii=False)
V = json.load(open(os.path.join(HERE, "plan_v_raw.json"), encoding="utf8"))
for k in ("zooms", "presets"):
    for x in V[k]: x["t"] = round(new2(x["t"]), 3)
json.dump(V, open(os.path.join(HERE, "plan_v_raw.json"), "w", encoding="utf8"), ensure_ascii=False)
J3 = json.load(open(os.path.join(HERE, "joins3.json"))); json.dump(sorted(round(new2(t), 3) for t in J3) + json.load(open(os.path.join(HERE, "joins_pass_x.json"))), open(os.path.join(HERE, "joins3.json"), "w"))
print("remapeado:", len(MK), "marcadores")
