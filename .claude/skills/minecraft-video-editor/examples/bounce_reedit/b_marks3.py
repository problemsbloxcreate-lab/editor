from lib import *
vp = json.load(open(os.path.join(HERE, "plan_v_raw.json"), encoding="utf8"))
M = json.load(open(os.path.join(HERE, "plan_music.json"), encoding="utf8"))
rem = sorted((a, b, w) for a, b, w in json.load(open(os.path.join(HERE, "remove.json"), encoding="utf8")))
def new(t):
    acc = 0
    for a, b, _ in rem:
        if t >= b: acc += b - a
        elif t > a: acc += t - a; break
        else: break
    return t - acc
MK = [{"t": 0.0, "txt": "V3 (Claude 16/10): -47,5 s de cortes (46), música Epidemic por clima (cama -14 dB sob a voz), 56 SFX (ganho fixo), 6 zooms, 8 presets. NIVEL: os clipes seguem a convenção (voz -1,7 dB / Pedro -5,4 dB); o MASTER da sequência está abaixo de 0 dB (mexeram nele): zere o fader master antes de exportar."}]
for a, b, w in rem:
    if w.startswith("macro") and b - a >= 0.8: MK.append({"t": round(new(a), 3), "txt": "CORTE %.1fs: %s" % (b - a, w[7:]) })
for m in M: MK.append({"t": round(m["a"], 3), "txt": "MÚSICA: %s — %s" % (m["name"][:40], m["why"])})
for z in vp["zooms"]: MK.append({"t": round(z["t"], 3), "txt": "ZOOM %d%% (ease-out, fica): %s" % (z["s1"], z["why"])})
for p in vp["presets"]: MK.append({"t": round(p["t"], 3), "txt": "%s: %s" % (p["name"], p["why"])})
MK.sort(key=lambda m: m["t"])
run(PRE + '''var MK = %s; r.n = 0; for (var k = 0; k < MK.length; k++) { var mk = s.markers.createMarker(MK[k].t); mk.name = MK[k].txt.substr(0, 120); mk.comments = MK[k].txt; r.n++; }
return __result(r);''' % J(MK), "marks", 300)
