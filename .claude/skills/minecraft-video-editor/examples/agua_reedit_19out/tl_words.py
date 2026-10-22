"""Palavras em TEMPO DE TIMELINE da Sequência 01 (clone idêntico), a partir das transcrições das fontes + clipes ATIVOS.
D = dublagem (Problems, A1 arquivo 10-14), P = voz provisória ainda ativa na A1, C = call (A2).
Saída: tl_words.json  [[ini, fim, falante, palavra]] e tl_transcript.txt (legível, uma linha por frase)."""
import json
DEC = r"C:\Users\mathe\Skills\_research\mc-decup"
d = json.load(open(DEC + r"\dump.json", encoding="utf8"))[0]
src = {("2026-10-14", 0): DEC + r"\t_dub1.json", ("2026-10-08", 0): DEC + r"\t_raw1.json", ("2026-10-08", 1): DEC + r"\t_raw2.json"}
spk = {("2026-10-14", 0): "D", ("2026-10-08", 0): "P", ("2026-10-08", 1): "C"}
WS = {k: [(w["s"], min(w["e"], w["s"] + 1.0), w["w"].strip()) for w in json.load(open(v, encoding="utf8"))["words"]] for k, v in src.items()}
out = []
for ti in (0, 1):
    for c in d["a"][ti]:
        name, st, en, ip, op, dis = c[:6]
        if dis: continue
        key = (name[:10], ti)
        if key not in WS: continue
        for s, e, w in WS[key]:
            m = (s + e) / 2
            if ip <= m < op:
                out.append([round(st + (s - ip), 3), round(min(st + (e - ip), en), 3), spk[key], w])
out.sort()
json.dump(out, open("tl_words.json", "w", encoding="utf8"), ensure_ascii=False)
lines, cur = [], None
for s, e, k, w in out:
    if cur and (k != cur[1] or s - cur[3] > 0.6 or cur[2][-1:] in ".?!" and s - cur[3] > 0.25):
        lines.append(cur); cur = None
    if cur is None: cur = [s, k, w, e]
    else: cur[2] += " " + w; cur[3] = e
if cur: lines.append(cur)
with open("tl_transcript.txt", "w", encoding="utf8") as f:
    for s, k, txt, e in lines:
        f.write("%02d:%05.2f %s: %s\n" % (int(s // 60), s % 60, k, txt))
print(len(out), "palavras,", len(lines), "linhas")
