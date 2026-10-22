from lib import *
for tr in (0, 1, 3, 4, 5, 6, 7):
    run(PRE + '''var C = 0.25; var st = s.audioTracks[%d]; r.n = 0;
for (var c = 0; c < st.clips.numItems; c++) { var pr = lvl(st.clips[c]);
  if (pr.isTimeVarying()) { var ks = pr.getKeys(); var vals = []; for (var j = 0; j < ks.length; j++) vals.push(pr.getValueAtKey(ks[j]));
    for (var j2 = 0; j2 < ks.length; j2++) pr.setValueAtKey(ks[j2], vals[j2] * C); }
  else pr.setValue(pr.getValue() * C, true);
  r.n++; }
return __result(r);''' % tr, "uncomp%d" % tr, 900)
# atualiza os ganhos nominais gravados nos planos
for fn in ("plan_sfx.json", "plan_music.json"):
    P = json.load(open(os.path.join(HERE, fn), encoding="utf8"))
    for x in P: x["gdb"] = round(x["gdb"] - 12.04, 2); x["g"] = 10 ** ((x["gdb"] - 15) / 20.0)
    json.dump(P, open(os.path.join(HERE, fn), "w", encoding="utf8"), ensure_ascii=False)
