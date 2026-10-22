from lib import *
vp = json.load(open(os.path.join(HERE, "plan_v_raw.json"), encoding="utf8"))
F = json.load(open(os.path.join(HERE, "plan_sfx.json"), encoding="utf8"))
MK = [{"t": 0.0, "txt": "V2 (Claude 16/10): +71 SFX (A5-A6, ganho fixo, sem keyframe), 6 zooms que ficam, 8 presets BERSERKER (lag/VHS/flash). ATENCAO: o master dessa sequência estava em -12 dB; compensei +12,04 dB nos clipes (voz, música, SFX). Se zerar o master, tire o +12 dB."}]
for z in vp["zooms"]: MK.append({"t": round(z["t"], 3), "txt": "ZOOM %d%% (ease-out, fica): %s" % (z["s1"], z["why"])})
for p in vp["presets"]: MK.append({"t": round(p["t"], 3), "txt": "%s: %s" % (p["name"], p["why"])})
MK.sort(key=lambda m: m["t"])
run(PRE + '''var MK = %s; r.n = 0; for (var k = 0; k < MK.length; k++) { var mk = s.markers.createMarker(MK[k].t); mk.name = MK[k].txt.substr(0, 120); mk.comments = MK[k].txt; r.n++; }
return __result(r);''' % J(MK), "marks", 300)
