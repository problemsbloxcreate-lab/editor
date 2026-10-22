import json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
BR = os.path.expanduser("~/.claude/skills/minecraft-video-editor/scripts/run_bridge.py")
SEQ = open(os.path.join(HERE, "seq_id.txt")).read().strip()[:8] if os.path.exists(os.path.join(HERE, "seq_id.txt")) else "53124cf7"
PRE = '''var p = app.project; var WID = "%s"; var s = null; var r = {};
for (var i = 0; i < p.sequences.numSequences; i++) if (p.sequences[i].sequenceID.substr(0, 8) == WID) s = p.sequences[i];
p.openSequence(s.sequenceID);
function find(n) { for (var i = 0; i < p.rootItem.children.numItems; i++) if (p.rootItem.children[i].name == n) return p.rootItem.children[i]; return null; }
function lvl(c) { return c.components[0].properties[1]; }
function tc(t) { var fr = Math.round(t * 60); var f = fr %% 60; var sec = Math.floor(fr / 60); var ss = sec %% 60; var mm = Math.floor(sec / 60) %% 60; var hh = Math.floor(sec / 3600);
  function z(n) { return (n < 10 ? "0" : "") + n; } return z(hh) + ":" + z(mm) + ":" + z(ss) + ":" + z(f); }
''' % SEQ
lin = lambda db: 10 ** ((db - 15) / 20.0)
J = json.dumps
def run(jsx, name, timeout=300, quiet=False):
    path = os.path.join(HERE, "_" + name + ".jsx")
    open(path, "w", encoding="utf8").write(jsx)
    out = subprocess.run([sys.executable, "-X", "utf8", BR, path, str(timeout)], capture_output=True, text=True, encoding="utf8")
    if out.returncode != 0:
        raise SystemExit(name + " FALHOU: " + (out.stderr or out.stdout)[-900:])
    if not quiet: print(name, "ok:", out.stdout.strip()[:400], flush=True)
    return out.stdout
