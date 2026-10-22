from lib import *
rem = sorted((a, b) for a, b, _ in json.load(open(os.path.join(HERE, "remove.json"), encoding="utf8")))
def new(t):
    acc = 0
    for a, b in rem:
        if t >= b: acc += b - a
        elif t > a: acc += t - a; break
        else: break
    return t - acc
# o buraco de 4,6 s que fechei (extract) não entra no mapa; calcular juntas a partir do dump real
d = json.load(open(os.path.join(HERE, "seq_dump3.json"), encoding="utf8"))
rows = d["A"][0]["rows"]
joins = [round(b["a"], 3) for a, b in zip(rows, rows[1:]) if abs(a["b"] - b["a"]) < 0.01 and abs(a["o"] - b["i"]) > 0.03]
print(len(joins), "juntas de corte em A1")
json.dump(joins, open(os.path.join(HERE, "joins3.json"), "w"))
for i in range(0, len(joins), 60):
    run(PRE + '''var JN = %s; var trn = qe.project.getAudioTransitionByName("Potência constante"); r.n = 0; r.err = "";
app.enableQE(); var q = qe.project.getActiveSequence();
for (var t = 0; t < 2; t++) { var qt = q.getAudioTrackAt(t);
  for (var i2 = 0; i2 < qt.numItems; i2++) { var it = qt.getItemAt(i2); if (String(it.type) == "Empty") continue; var st = it.start.secs; var hit = false;
    for (var j = 0; j < JN.length; j++) if (Math.abs(st - JN[j]) < 0.02) { hit = true; break; }
    if (hit) { try { it.addTransition(trn, true, "00:00:00:08"); r.n++; } catch (e) { r.err += i2 + ":" + e + " "; } } } }
return __result(r);''' % J(joins[i:i + 60]), "xf", 900)
