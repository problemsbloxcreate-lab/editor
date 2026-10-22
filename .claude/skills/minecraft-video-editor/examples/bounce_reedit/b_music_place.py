from lib import *
run(PRE + '''app.enableQE(); var q = qe.project.getActiveSequence(); var n0 = s.audioTracks.numTracks;
if (n0 < 8) { q.addTracks(0, 0, 8 - n0, 1, n0, 0, 0, 0); if (s.audioTracks.numTracks == n0) q.addTracks(0, 0, 8 - n0, 0, n0, 0, 0, 0); }
r.a = s.audioTracks.numTracks; return __result(r);''', "tracks8", 120)
run(PRE + '''var st = s.audioTracks[4]; for (var k = st.clips.numItems - 1; k >= 0; k--) st.clips[k].remove(0, 0); r.n = st.clips.numItems; return __result(r);''', "muclear", 300)
M = json.load(open(os.path.join(HERE, "plan_music.json"), encoding="utf8"))
files = sorted({m["file"].replace("\\", "/") for m in M})
run(PRE + "r.imp = p.importFiles(%s, true, p.rootItem, false); return __result(r);" % J(files), "mus_import", 600)
MM = [{"name": m["name"], "a": m["a"], "b": m["b"], "off": m["src_in"], "g": m["g"]} for m in M]
run(PRE + '''var mt = s.audioTracks[4]; var M = %s; r.n = 0; r.miss = "";
for (var k = 0; k < M.length; k++) { var it = find(M[k].name); if (!it) { r.miss += M[k].name + "|"; continue; }
  it.setInPoint(M[k].off, 4); it.setOutPoint(M[k].off + M[k].b - M[k].a, 4); mt.overwriteClip(it, M[k].a); it.clearInPoint(); it.clearOutPoint();
  var cl = null; for (var c = 0; c < mt.clips.numItems; c++) if (Math.abs(mt.clips[c].start.seconds - M[k].a) < 0.02) cl = mt.clips[c];
  if (cl) { var pr = lvl(cl); pr.setTimeVarying(false); pr.setValue(M[k].g, true); r.n++; } }
return __result(r);''' % J(MM), "mus_place", 900)
