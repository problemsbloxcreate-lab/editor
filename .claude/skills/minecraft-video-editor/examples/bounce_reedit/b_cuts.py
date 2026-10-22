from lib import *
rem = json.load(open(os.path.join(HERE, "remove.json"), encoding="utf8"))
cuts = sorted([[a, b] for a, b, _ in rem], reverse=True)
JSX = PRE + '''app.enableQE(); var q = qe.project.getActiveSequence();
var cuts = @@CUTS@@; r.end0 = s.end / 254016000000.0; r.rm = 0;
var tracks = []; for (var v = 0; v < s.videoTracks.numTracks; v++) tracks.push(s.videoTracks[v]); for (var u = 0; u < s.audioTracks.numTracks; u++) tracks.push(s.audioTracks[u]);
for (var c = 0; c < cuts.length; c++) { var a = cuts[c][0], b = cuts[c][1];
  q.razor(tc(b)); q.razor(tc(a));
  for (var t = 0; t < tracks.length; t++) { var tr = tracks[t];
    for (var k = tr.clips.numItems - 1; k >= 0; k--) { var cl = tr.clips[k];
      if (cl.end.seconds < a - 0.01) break;
      if (cl.start.seconds >= a - 0.004 && cl.end.seconds <= b + 0.004) { cl.remove(1, 1); r.rm++; } } } }
r.end1 = s.end / 254016000000.0;
return __result(r);'''
for i in range(0, len(cuts), 10):
    out = run(JSX.replace("@@CUTS@@", J(cuts[i:i + 10])), "cuts", 900)
tot = sum(b - a for a, b in cuts); print("remover %.1f s -> fim previsto %.2f" % (tot, 726.667 - tot))
json.dump([[a, b] for a, b in sorted(cuts)], open(os.path.join(HERE, "applied_cuts.json"), "w"))
