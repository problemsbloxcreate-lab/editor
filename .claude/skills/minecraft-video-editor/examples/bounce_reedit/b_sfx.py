from lib import *
import sfx_plan
F, vp = sfx_plan.plan()
json.dump(F, open(os.path.join(HERE, "plan_sfx.json"), "w", encoding="utf8"), ensure_ascii=False)
json.dump(vp, open(os.path.join(HERE, "plan_v_raw.json"), "w", encoding="utf8"), ensure_ascii=False)
files = sorted({x["path"] for x in F})
for f in files: assert os.path.exists(f), f
run(PRE + "r.imp = p.importFiles(%s, true, p.rootItem, false); return __result(r);" % J(files), "sfx_import", 400)
G = [{"name": x["name"], "t": x["t"], "dur": x["dur"], "tr": x["tr"], "g": x["g"]} for x in F]
run(PRE + '''var F = %s; r.miss = ""; r.n = 0;
for (var q = 0; q < F.length; q++) { var it = find(F[q].name); if (!it) { r.miss += F[q].name + "|"; continue; } var st = s.audioTracks[F[q].tr];
  it.setInPoint(0, 4); it.setOutPoint(F[q].dur, 4); st.overwriteClip(it, F[q].t); it.clearInPoint(); it.clearOutPoint();
  var cl = null; for (var c = 0; c < st.clips.numItems; c++) if (Math.abs(st.clips[c].start.seconds - F[q].t) < 0.01) cl = st.clips[c];
  if (cl) { var pr = lvl(cl); pr.setTimeVarying(false); pr.setValue(F[q].g, true); r.n++; } }
return __result(r);''' % J(G), "sfx_place", 900)
