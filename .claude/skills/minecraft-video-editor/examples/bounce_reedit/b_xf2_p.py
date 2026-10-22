from lib import *
rem2 = sorted(json.load(open(os.path.join(HERE, os.environ.get("PASSFILE","remove2_ok.json")))))
def new2(t):
    acc = 0
    for a, b in rem2:
        if t >= b: acc += b - a
        elif t > a: acc += t - a; break
        else: break
    return t - acc
joins = [round(new2(a), 3) for a, b in rem2]
json.dump(joins, open(os.path.join(HERE, "joins_pass_x.json"), "w"))
print(len(joins), "novas juntas")
TR = [0, 1, 4, 5, 6]      # A1, A2, música (A5), SFX (A6, A7): só onde há clipe começando na junta
for i in range(0, len(joins), 50):
    run(PRE + '''var JN = %s; var trn = qe.project.getAudioTransitionByName("Potência constante"); r.n = 0; r.err = "";
app.enableQE(); var q = qe.project.getActiveSequence(); var TRK = %s;
for (var tt = 0; tt < TRK.length; tt++) { var qt = q.getAudioTrackAt(TRK[tt]);
  for (var i2 = 0; i2 < qt.numItems; i2++) { var it = qt.getItemAt(i2); if (String(it.type) == "Empty") continue; var st = it.start.secs; var hit = false;
    for (var j = 0; j < JN.length; j++) if (Math.abs(st - JN[j]) < 0.02) { hit = true; break; }
    if (hit) { try { it.addTransition(trn, true, "00:00:00:08"); r.n++; } catch (e) { r.err += i2 + ":" + e + " "; } } } }
return __result(r);''' % (J(joins[i:i + 50]), J(TR)), "xf2", 900)
