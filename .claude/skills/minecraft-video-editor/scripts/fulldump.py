"""Dump completo (clipes + componentes + keyframes + marcadores) de uma sequência do projeto ativo.
uso: python fulldump.py <SEQ_ID> <saida.json> [--tracks V0,V1,A0..] [--lite]"""
import json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
BR = os.path.join(HERE, "run_bridge.py")

JS = r'''var p = app.project; var WID = "%(sid)s"; var s = null;
for (var i = 0; i < p.sequences.numSequences; i++) if (p.sequences[i].sequenceID == WID) s = p.sequences[i];
if (!s) throw new Error("seq nao achada");
var T = 254016000000; function sec(t) { return Math.round(t.ticks / T * 100000) / 100000; }
var LITE = %(lite)s; var WANT = "%(want)s";
function val(v) { if (v === null || typeof v === "undefined") return null; if (typeof v == "number" || typeof v == "boolean" || typeof v == "string") return v;
  if (v instanceof Array) { var o = []; for (var i = 0; i < v.length; i++) o.push(val(v[i])); return o; } try { return String(v); } catch (e) { return null; } }
function comps(k) { var out = []; for (var u = 0; u < k.components.numItems; u++) { var c = k.components[u]; var cp = {n: c.displayName, m: c.matchName, p: []};
  for (var q = 0; q < c.properties.numItems; q++) { var pr = c.properties[q]; var e = {n: pr.displayName};
    try { if (pr.isTimeVarying()) { var ks = pr.getKeys(); e.kf = []; for (var z = 0; z < ks.length; z++) e.kf.push([Math.round(ks[z].seconds * 10000) / 10000, val(pr.getValueAtKey(ks[z]))]); }
          else e.v = val(pr.getValue()); } catch (er) { e.err = 1; }
    cp.p.push(e); } out.push(cp); } return out; }
function path(k) { try { return k.projectItem ? k.projectItem.getMediaPath() : ""; } catch (e) { return ""; } }
function dumpTrack(tr, tag) { var rows = []; for (var c = 0; c < tr.clips.numItems; c++) { var k = tr.clips[c];
  var o = {s: sec(k.start), e: sec(k.end), i: sec(k.inPoint), o: sec(k.outPoint), d: k.disabled ? 1 : 0, n: k.name, f: path(k)};
  try { o.spd = k.getSpeed(); } catch (e) {} try { o.rev = k.isSpeedReversed(); } catch (e) {}
  if (!LITE) o.c = comps(k); rows.push(o); }
  var tx = []; try { for (var c = 0; c < tr.transitions.numItems; c++) { var x = tr.transitions[c]; tx.push([sec(x.start), sec(x.end), x.name]); } } catch (e) {}
  return {tag: tag, name: tr.name, muted: (function(){ try { return tr.isMuted(); } catch (e) { return null; } })(), clips: rows, tx: tx}; }
var r = {name: s.name, end: s.end / T, V: [], A: [], mk: []};
for (var t = 0; t < s.videoTracks.numTracks; t++) { var tg = "V" + t; if (WANT == "" || WANT.indexOf(tg) >= 0) r.V.push(dumpTrack(s.videoTracks[t], tg)); else r.V.push(null); }
for (var t = 0; t < s.audioTracks.numTracks; t++) { var tg = "A" + t; if (WANT == "" || WANT.indexOf(tg) >= 0) r.A.push(dumpTrack(s.audioTracks[t], tg)); else r.A.push(null); }
var m = s.markers.getFirstMarker(); var guard = 0; while (m && guard < 2000) { r.mk.push([m.start.seconds, m.end.seconds, m.name, m.comments]); m = s.markers.getNextMarker(m); guard++; }
return __result(r);'''


def main():
    sid, out = sys.argv[1], sys.argv[2]
    want = ""; lite = "false"
    if "--tracks" in sys.argv: want = sys.argv[sys.argv.index("--tracks") + 1]
    if "--lite" in sys.argv: lite = "true"
    js = os.path.join(HERE, "jsx", "fd_%s.jsx" % os.path.basename(out).replace(".json", ""))
    os.makedirs(os.path.dirname(js), exist_ok=True)
    open(js, "w", encoding="utf8").write(JS % {"sid": sid, "want": want, "lite": lite})
    r = subprocess.run([sys.executable, "-X", "utf8", BR, js, "900"], capture_output=True, text=True, encoding="utf8")
    if r.returncode: raise SystemExit((r.stderr or r.stdout)[-1500:])
    d = json.load(open(js.replace(".jsx", ".result.json"), encoding="utf8"))
    json.dump(d, open(out, "w", encoding="utf8"), ensure_ascii=False)
    print(out, d["name"], "end", round(d["end"], 2), "V", [len(t["clips"]) if t else None for t in d["V"]], "A", [len(t["clips"]) if t else None for t in d["A"]], "mk", len(d["mk"]))


if __name__ == "__main__":
    main()
