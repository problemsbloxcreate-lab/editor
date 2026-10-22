from lib import *
# 1) apaga a música antiga de A4 (mantém o pickup do Pedro P3)
run(PRE + '''var st = s.audioTracks[3]; r.n0 = st.clips.numItems; r.del = 0;
for (var k = st.clips.numItems - 1; k >= 0; k--) { if (st.clips[k].name.indexOf("P3_a0") < 0) { st.clips[k].remove(0, 0); r.del++; } }
r.n1 = st.clips.numItems; return __result(r);''', "oldmusic")
# 2) +12,04 dB (master -12 dB) em A1, A2 e no pickup
for tr in (0, 1, 3):
    run(PRE + '''var C = 4.0; var st = s.audioTracks[%d]; r.n = 0;
for (var c = 0; c < st.clips.numItems; c++) { var pr = lvl(st.clips[c]);
  if (pr.isTimeVarying()) { var ks = pr.getKeys(); var vals = []; for (var j = 0; j < ks.length; j++) vals.push(pr.getValueAtKey(ks[j]));
    for (var j2 = 0; j2 < ks.length; j2++) pr.setValueAtKey(ks[j2], Math.min(5.62, vals[j2] * C)); }
  else pr.setValue(Math.min(5.62, pr.getValue() * C), true);
  r.n++; }
return __result(r);''' % tr, "comp%d" % tr, 900)
# 3) trilhas A5..A7
run(PRE + '''app.enableQE(); var q = qe.project.getActiveSequence(); var n0 = s.audioTracks.numTracks;
if (n0 < 7) { q.addTracks(0, 0, 7 - n0, 1, n0, 0, 0, 0); if (s.audioTracks.numTracks == n0) q.addTracks(0, 0, 7 - n0, 0, n0, 0, 0, 0); }
r.a = s.audioTracks.numTracks; r.muted = s.audioTracks[2].isMuted(); return __result(r);''', "tracks", 120)
