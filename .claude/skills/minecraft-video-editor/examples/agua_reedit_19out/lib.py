"""Ponte p/ o clone da Sequência 01 do 'Bebi toda a água do mundo'. Todo JSX checa que o projeto ATIVO é o certo (o QE só age no ativo)."""
import json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
BR = os.path.expanduser("~/.claude/skills/minecraft-video-editor/scripts/run_bridge.py")
SEQ = open(os.path.join(HERE, "seq_id.txt")).read().strip() if os.path.exists(os.path.join(HERE, "seq_id.txt")) else ""
PRE = '''var p = app.project; var r = {};
if (p.path.indexOf("Bebi toda a agua") < 0) throw new Error("PROJETO ATIVO ERRADO: " + p.path);
var WID = "%s"; var s = null; for (var i = 0; i < p.sequences.numSequences; i++) if (p.sequences[i].sequenceID == WID) s = p.sequences[i];
if (!s) throw new Error("sequencia nao achada " + WID);
p.openSequence(WID);
function find(n) { var best = null; function walk(b) { for (var i = 0; i < b.children.numItems; i++) { var c = b.children[i]; if (c.type == 2) walk(c); else if (c.name == n && !best) best = c; } } walk(p.rootItem); return best; }
function lvl(c) { return c.components[0].properties[1]; }
function tc(t, sep) { var n = Math.round(t * 254016000000 / 4237833600);
  // 59,94 DROP-FRAME: pula os rótulos 00-03 a cada minuto, exceto a cada 10 min (o razor do QE lê o timecode exibido)
  var D = Math.floor(n / 35964), M = n %% 35964; n += 36 * D + (M > 3 ? 4 * Math.floor((M - 4) / 3596) : 0);
  var f = n %% 60; var sc = Math.floor(n / 60); var ss = sc %% 60; var mm = Math.floor(sc / 60) %% 60; var hh = Math.floor(sc / 3600);
  function z(x) { return (x < 10 ? "0" : "") + x; } var d = sep || ";"; return z(hh) + d + z(mm) + d + z(ss) + d + z(f); }
function clipAt(tr, t) { for (var k = 0; k < tr.clips.numItems; k++) if (Math.abs(tr.clips[k].start.seconds - t) < 0.012) return k; return -1; }
function comp(c, nm) { for (var u = 0; u < c.components.numItems; u++) if (c.components[u].displayName == nm) return c.components[u]; return null; }
''' % SEQ
lin = lambda db: 10 ** ((db - 15) / 20.0)
J = json.dumps


def run(jsx, name, timeout=300, quiet=False):
    path = os.path.join(HERE, "jsx", name + ".jsx")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf8").write(jsx)
    out = subprocess.run([sys.executable, "-X", "utf8", BR, path, str(timeout)], capture_output=True, text=True, encoding="utf8")
    if out.returncode != 0:
        raise SystemExit(name + " FALHOU: " + (out.stderr or out.stdout)[-900:])
    if not quiet: print(name, "ok:", out.stdout.strip()[:400], flush=True)
    return json.load(open(path.replace(".jsx", ".result.json"), encoding="utf8"))


DUMP_JS = '''var T = 254016000000; function sec(t) { return Math.round(t.ticks / T * 100000) / 100000; }
r.V = []; r.A = [];
for (var t = 0; t < s.videoTracks.numTracks; t++) { var tr = s.videoTracks[t]; var rows = [];
  for (var c = 0; c < tr.clips.numItems; c++) { var k = tr.clips[c]; rows.push([sec(k.start), sec(k.end), sec(k.inPoint), sec(k.outPoint), k.disabled ? 1 : 0, k.name]); } r.V.push(rows); }
for (var t = 0; t < s.audioTracks.numTracks; t++) { var tr = s.audioTracks[t]; var rows = [];
  for (var c = 0; c < tr.clips.numItems; c++) { var k = tr.clips[c]; rows.push([sec(k.start), sec(k.end), sec(k.inPoint), sec(k.outPoint), k.disabled ? 1 : 0, k.name]); } r.A.push(rows); }
r.end = s.end / T; return __result(r);'''


def dump():
    return run(PRE + DUMP_JS, "dump", 300, quiet=True)
