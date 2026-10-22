"""Confere o RENDER contra o plano: transcreve o áudio do render e compara com as palavras esperadas (ASR dos brutos mapeado pelos keeps).
Uso: python verify_render.py <plan3.json> <render.mp4> <work_dir_com_t1.json_t2.json> [--sfx]
Saída: % de palavras esperadas encontradas (±0.6 s) e lista das que sumiram (corte em cima de palavra ou música/SFX cobrindo). --sfx lista SFX do plano com a palavra mais próxima no render.
"""
import sys, json, re, subprocess, os
plan = json.load(open(sys.argv[1], encoding="utf8")); render = sys.argv[2]; work = sys.argv[3]
_st = os.stat(render)       # 21/10: cache pela versão do arquivo (antes: pelo nome — render refeito reaproveitava o ASR velho)
out = os.path.splitext(render)[0] + "_asr_%d_%d.json" % (_st.st_size, int(_st.st_mtime))
if not os.path.exists(out):
    subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "transcribe_tracks.py"), render, out], check=True)
rw = json.load(open(out, encoding="utf8"))["words"]
norm = lambda s: re.sub(r"\W", "", s.lower())
exp = []
for k in ("t1", "t2"):
    for w in json.load(open(os.path.join(work, k + ".json"), encoding="utf8"))["words"]:
        for c in plan["keeps"]:
            if c["src_in"] - 0.02 <= w["s"] and w["e"] <= c["src_out"] + 0.05:
                exp.append((c["tl_in"] + (w["s"] - c["src_in"]), norm(w["w"]), w["w"].strip())); break
exp.sort()
got = [(w["s"], norm(w["w"])) for w in rw]
miss = []
for t, n, raw in exp:
    if len(n) < 3: continue
    if not any(abs(gs - t) <= 0.6 and (gn == n or (len(n) > 4 and (gn.startswith(n[:4]) or n.startswith(gn[:4])))) for gs, gn in got): miss.append((t, raw))
tot = sum(1 for t, n, raw in exp if len(n) >= 3)
print("palavras esperadas (>=3 letras): %d | achadas no render: %d (%.0f%%)" % (tot, tot - len(miss), 100.0 * (tot - len(miss)) / max(tot, 1)))
print("sumidas (podem ser só mascaradas por música/SFX):", " ".join("%s@%.1f" % (r, t) for t, r in miss[:60]))
if "--sfx" in sys.argv:
    for s in plan["sfx"]:
        near = [w["w"].strip() for w in rw if abs(w["s"] - s["tl"]) < 0.7]
        print("SFX %6.2f %-34s palavras perto: %s" % (s["tl"], os.path.basename(s["file"])[:34], " ".join(near)))
