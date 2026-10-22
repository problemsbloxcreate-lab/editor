"""Lê a timeline que o Matheus EDITOU e compara com o plano (plan3.json) que eu montei — é como se "aprende" com ele (15/10/2026: ver references/feedback-timeline-dele-15out.md).
Uso:  python timeline_diff.py <SEQ_ID> <plan3.json> [--work <pasta com t1.json t2.json t3.json>] [--out dados.json]
Faz (SÓ LEITURA no Premiere — mas ele costuma editar a própria sequência: CLONE antes se for exportar/mexer):
  1. dump de V/A: cada clipe (início/fim/in/out/arquivo), ganho do clipe + se tem keyframe, desabilitado, efeitos;
  2. mapeia o plano -> a timeline dele pelo TEMPO DA FONTE (cortes dele deslocam tudo): trechos cortados, SFX mantidos/movidos/removidos/novos, ganho que ele deixou x o meu;
  3. distância de cada SFX ao corte mais próximo + frase falada em volta; música (arquivo, in, ganho); clipes de voz/jogo DESABILITADOS (mutes);
  4. grava o JSON estruturado (--out).
Depois: atualizar GAIN_DB em sfx_levels.py, regras no SKILL.md e este diff na referência.
"""
import sys, os, re, json, subprocess, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
JSX = r'''
var p = app.project; var WID = "%s"; var s = null;
for (var i = 0; i < p.sequences.numSequences; i++) if (p.sequences[i].sequenceID == WID) s = p.sequences[i];
function db(v) { return Math.round((20 * Math.log(v) / Math.LN10 + 15) * 10) / 10; }
var r = {name: s.name, end: s.end, V: [], A: []};
function row(cl, aud) {
  var o = {a: cl.start.seconds, b: cl.end.seconds, i: cl.inPoint.seconds, o: cl.outPoint.seconds, n: cl.name, off: !!cl.disabled, mp: "", comps: []};
  try { o.mp = cl.projectItem.getMediaPath(); } catch (e) {}
  try { for (var c = 0; c < cl.components.numItems; c++) { var co = cl.components[c]; var nk = 0;
      for (var q = 0; q < co.properties.numItems; q++) { try { if (co.properties[q].isTimeVarying()) nk++; } catch (e) {} }
      o.comps.push(co.displayName + (nk ? "(kf" + nk + ")" : "")); } } catch (e) {}
  if (aud) { var pr = cl.components[0].properties[1]; o.db = db(pr.getValue()); o.kf = [];
    try { var ks = pr.getKeys(); for (var k = 0; k < ks.length; k++) o.kf.push([Math.round((ks[k].seconds - cl.inPoint.seconds) * 100) / 100, db(pr.getValueAtKey(ks[k]))]); } catch (e) {} }
  else { try { var sc = cl.components[1].properties[1]; o.sc = []; var ks2 = sc.getKeys(); for (var k2 = 0; k2 < ks2.length; k2++) o.sc.push([Math.round((ks2[k2].seconds - cl.inPoint.seconds) * 100) / 100, Math.round(sc.getValueAtKey(ks2[k2]))]); } catch (e) {} }
  return o; }
for (var t = 0; t < s.videoTracks.numTracks; t++) { var rows = []; for (var c = 0; c < s.videoTracks[t].clips.numItems; c++) rows.push(row(s.videoTracks[t].clips[c], false)); r.V.push(rows); }
for (var t2 = 0; t2 < s.audioTracks.numTracks; t2++) { var rows2 = []; for (var c2 = 0; c2 < s.audioTracks[t2].clips.numItems; c2++) rows2.push(row(s.audioTracks[t2].clips[c2], true)); r.A.push(rows2); }
return __result(r);
'''


def main():
    sys.stdout.reconfigure(encoding="utf8")
    a = sys.argv[1:]
    seq, planp = a[0], a[1]
    work = a[a.index("--work") + 1] if "--work" in a else os.getcwd()
    outp = a[a.index("--out") + 1] if "--out" in a else None
    plan = json.load(open(planp, encoding="utf8"))
    tmp = os.path.join(tempfile.gettempdir(), "tl_dump.jsx")
    open(tmp, "w", encoding="utf8").write(JSX % seq)
    subprocess.run([sys.executable, os.path.join(HERE, "run_bridge.py"), tmp, "180"], check=True, capture_output=True)
    d = json.load(open(tmp.replace(".jsx", ".result.json"), encoding="utf8"))
    print("sequência: %s  | duração %.1f s | V%d A%d" % (d["name"], int(d["end"]) / 254016000000.0, len(d["V"]), len(d["A"])))
    words = {}
    for k in ("t1", "t2", "t3"):
        fp = os.path.join(work, k + ".json")
        if os.path.exists(fp): words[k] = sorted((w["s"], w["e"], w["w"].strip()) for w in json.load(open(fp, encoding="utf8"))["words"])
    bruto = [c for c in d["V"][0] if c["mp"].lower().endswith(".mp4") and not c["n"].startswith("Sequência")]
    nested = [c for c in d["V"][0] if c["n"].startswith("Sequência")]
    # trechos de nested contam como cobertos (ele aninha p/ aplicar efeito)
    cover = [(c["i"], c["o"]) for c in bruto] + [(n["i"] + 100.0, n["o"] + 100.0) for n in []]
    def tl2src(t):
        for c in bruto:
            if c["a"] - 1e-3 <= t < c["b"] - 1e-3: return c["i"] + (t - c["a"])
    def p2src(t):
        for k in plan["keeps"]:
            if k["tl_in"] - 1e-3 <= t <= k["tl_out"] + 1e-3: return k["src_in"] + (t - k["tl_in"])
    def src2tl(s):
        for c in bruto:
            if c["i"] - 1e-3 <= s <= c["o"] + 1e-3: return c["a"] + (s - c["i"])
    def say(t, w=1.0):
        s = tl2src(t + 0.05)
        return "" if s is None or "t1" not in words else " ".join(x[2] for x in words["t1"] if s - w <= x[0] <= s + w + 0.2)
    last = max((c["b"] for c in bruto), default=0)
    print("\n== trechos do plano que ele CORTOU (fonte) ==")
    miss = []
    for k in plan["keeps"]:
        t = k["src_in"]
        while t < k["src_out"] - 0.01:
            if src2tl(t + 0.02) is None and p2src and t < (bruto[-1]["o"] if bruto else 0): miss.append(round(t, 2))
            t += 0.04
    grp = []
    for t in miss:
        if grp and t - grp[-1][1] < 0.09: grp[-1][1] = t
        else: grp.append([t, t])
    for g in grp:
        if g[1] - g[0] >= 0.3:
            ws = " ".join(x[2] for x in words.get("t1", []) if g[0] <= x[0] <= g[1] + 0.04)
            dg = g[1] - g[0] + 0.04; hint = "  <- provavelmente o clipe ANINHADO dele (efeito aplicado)" if any(abs(dg - (n["b"] - n["a"])) < 0.4 for n in nested) else ""
            print("  fonte %.2f-%.2f (%.1f s): %s%s" % (g[0], g[1] + 0.04, dg, ws[:90], hint))
    if nested: print("  (clipes aninhados dele: %s — o trecho aninhado vira 'efeito aplicado', veja V0 comps)" % ", ".join("%.1f-%.1f" % (n["a"], n["b"]) for n in nested))
    cuts = [c["a"] for c in bruto]
    print("\n== SFX: plano -> timeline dele (A5..A7 do Premiere = índices 4..6) ==")
    cur = [(c["a"], c["b"], os.path.basename(c["mp"]), c, ti) for ti in range(3, len(d["A"])) for c in d["A"][ti] if not os.path.basename(c["mp"]).startswith("ES_")]
    used = set(); res = []
    for x in sorted(plan["sfx"], key=lambda x: x["tl"]):
        s = p2src(x["tl"]); h = src2tl(s) if s is not None else None; nm = os.path.basename(x["file"])
        best = None
        for j, c in enumerate(cur):
            if c[2] == nm and j not in used and (h is None or abs(c[0] - h) < 3.0):
                if best is None or abs(c[0] - (h or 0)) < abs(cur[best][0] - (h or 0)): best = j
        if best is None:
            if h is not None: print("  REMOVIDO  plano %.2f -> ele %.2f  %-34s %s" % (x["tl"], h, nm[:34], x.get("why", "")[:60]))
            continue
        used.add(best); c = cur[best]
        res.append((x, h, c))
    for x, h, c in res:
        cl = c[3]; near = min(cuts, key=lambda t: abs(t - c[0])) if cuts else c[0]
        print("  %-8s %7.2f (esperado %.2f, d%+.2f) ganho %6.1f dB%s | corte %+.2f | %-32s" % ("OFF" if cl["off"] else "mantido", c[0], h or -1, c[0] - (h or 0), cl["db"], " +KF(meu)" if cl["kf"] else " fixo(dele)", c[0] - near, c[2][:32]))
    print("  -- NOVOS (não vieram do plano):")
    for j, c in enumerate(cur):
        if j not in used:
            cl = c[3]; near = min(cuts, key=lambda t: abs(t - c[0])) if cuts else c[0]
            print("    %7.2f A%d %-38s ganho %6.1f dB%s | corte %+.2f | %s" % (c[0], c[4] + 1, c[2][:38], cl["db"], " KF" if cl["kf"] else "", c[0] - near, say(c[0])[:50]))
    print("\n== música (faixas ES_*) ==")
    music = []
    for ti, trk in enumerate(d["A"]):
        for c in trk:
            if os.path.basename(c["mp"]).startswith("ES_"):
                m = {"track": "A%d" % (ti + 1), "tl": round(c["a"], 2), "fim": round(c["b"], 2), "src_in": round(c["i"], 2), "file": c["mp"], "gain_db": c["db"], "keyframes": bool(c["kf"])}
                music.append(m); print("  A%d %7.2f-%7.2f  %-52s in %6.2f  %6.1f dB%s" % (ti + 1, c["a"], c["b"], os.path.basename(c["mp"])[:52], c["i"], c["db"], " (kf)" if c["kf"] else " fixo"))
    print("\n== clipes de voz/jogo DESABILITADOS (mutes) ==")
    mutes = []
    for ti in range(0, min(3, len(d["A"]))):
        for c in d["A"][ti]:
            if c["off"]:
                tk = {1: "t2", 2: "t3", 0: "t1"}[ti]; ws = " ".join(x[2] for x in words.get(tk, []) if c["i"] - 0.02 <= x[0] < c["o"])
                mutes.append({"track": ti, "a": round(c["a"], 2), "b": round(c["b"], 2), "fala": ws[:80]}); print("  trilha %d (A%d) %6.2f-%6.2f: \"%s\"" % (ti, ti + 1, c["a"], c["b"], ws[:60]))
    print("\n== efeitos/zooms em V1 (Movimento com keyframes) ==")
    for c in d["V"][0]:
        extra = [x for x in c["comps"] if x not in ("Opacidade", "Movimento")]
        if extra or c.get("sc"): print("  %7.2f-%7.2f %s %s" % (c["a"], c["b"], ("zoom " + str(c["sc"])) if c.get("sc") else "", extra))
    if outp:
        json.dump({"dump": d, "music": music, "mutes": mutes}, open(outp, "w", encoding="utf8"), ensure_ascii=False, indent=1)
        print("\nJSON ->", outp)


main()
