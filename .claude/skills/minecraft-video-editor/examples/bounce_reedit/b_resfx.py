from lib import *
F = json.load(open(os.path.join(HERE, "plan_sfx.json"), encoding="utf8"))
run(PRE + '''for (var t = 5; t < 8; t++) { var st = s.audioTracks[t]; for (var k = st.clips.numItems - 1; k >= 0; k--) st.clips[k].remove(0, 0); } r.n = s.audioTracks[5].clips.numItems; return __result(r);''', "sfxclear", 300)
G = [{"name": x["name"], "t": x["t"], "dur": x["dur"], "off": x.get("off", 0.0), "tr": x["tr"], "g": x["g"]} for x in F]
run(PRE + '''var F = %s; r.miss = ""; r.n = 0;
for (var q = 0; q < F.length; q++) { var it = find(F[q].name); if (!it) { r.miss += F[q].name + "|"; continue; } var st = s.audioTracks[F[q].tr];
  it.setInPoint(F[q].off, 4); it.setOutPoint(F[q].off + F[q].dur, 4); st.overwriteClip(it, F[q].t); it.clearInPoint(); it.clearOutPoint();
  var cl = null; for (var c = 0; c < st.clips.numItems; c++) if (Math.abs(st.clips[c].start.seconds - F[q].t) < 0.01) cl = st.clips[c];
  if (cl) { var pr = lvl(cl); pr.setTimeVarying(false); pr.setValue(F[q].g, true); r.n++; } }
r.a6 = s.audioTracks[5].clips.numItems; r.first = s.audioTracks[5].clips[0].start.seconds; return __result(r);''' % J(G), "sfxplace2", 900)
