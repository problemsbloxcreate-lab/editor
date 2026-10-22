from lib import *
COMP = 4.0   # +12,04 dB: o master dessa sequência estava em -12,04 dB (medido: vine-boom a 0 dB sai -12,0 dB no export; sequência-teste normal: 0 dB)
# 1) limpa o clipe de teste (A5) e apaga a sequência temporária de calibração
run(PRE + '''var st = s.audioTracks[4]; r.n0 = st.clips.numItems; for (var k = st.clips.numItems - 1; k >= 0; k--) st.clips[k].remove(0, 0); r.n1 = st.clips.numItems;
for (var t = 0; t < 7; t++) s.audioTracks[t].setMute(t == 2 ? 1 : 0); r.muted = s.audioTracks[2].isMuted(); return __result(r);''', "clean_test")
tmp = open(os.path.join(HERE, "tmp_cal_id.txt")).read().strip()
run('''var p = app.project; var r = {}; for (var i = 0; i < p.sequences.numSequences; i++) if (p.sequences[i].sequenceID.substr(0, 8) == "%s") { r.name = p.sequences[i].name; try { r.del = p.deleteSequence(p.sequences[i]); } catch (e) { r.err = String(e); } break; }
return __result(r);''' % tmp, "del_tmp")
# 2) +12,04 dB nos clipes existentes de A1, A2 e A4 (inclusive os valores dos keyframes de fade)
for tr in (0, 1, 3):
    run(PRE + '''var C = %f; var st = s.audioTracks[%d]; r.n = 0; r.k = 0;
for (var c = 0; c < st.clips.numItems; c++) { var pr = lvl(st.clips[c]);
  if (pr.isTimeVarying()) { var ks = pr.getKeys(); var vals = []; for (var j = 0; j < ks.length; j++) vals.push(pr.getValueAtKey(ks[j]));
    for (var j2 = 0; j2 < ks.length; j2++) { var nv = Math.min(5.62, vals[j2] * C); pr.setValueAtKey(ks[j2], nv); r.k++; } }
  else { pr.setValue(Math.min(5.62, pr.getValue() * C), true); }
  r.n++; }
return __result(r);''' % (COMP, tr), "comp%d" % tr, 900)
