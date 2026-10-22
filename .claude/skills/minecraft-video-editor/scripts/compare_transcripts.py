"""Compara duas transcrições no formato da skill (ex.: motor local × Groq antigo).
uso: python compare_transcripts.py referencia.json nova.json
Mede: diferença de palavras (WER pela sequência normalizada) e erro de tempo de início/fim nas palavras que batem."""
import difflib, json, re, statistics as st, sys, unicodedata


def norm(w):
    w = unicodedata.normalize("NFD", w.lower()); w = "".join(c for c in w if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]", "", w)


def words(p):
    d = json.load(open(p, encoding="utf8"))
    return [(norm(x["w"]), x["s"], x["e"]) for x in d["words"] if norm(x["w"])]


def main():
    A, B = words(sys.argv[1]), words(sys.argv[2])
    sm = difflib.SequenceMatcher(None, [a[0] for a in A], [b[0] for b in B], autojunk=False)
    ds, de, sub, ins, dele = [], [], 0, 0, 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                ds.append(B[j1 + k][1] - A[i1 + k][1]); de.append(B[j1 + k][2] - A[i1 + k][2])
        elif tag == "replace": sub += max(i2 - i1, j2 - j1)
        elif tag == "delete": dele += i2 - i1
        elif tag == "insert": ins += j2 - j1
    wer = (sub + ins + dele) / max(1, len(A))
    ab = lambda v: st.median([abs(x) for x in v]) if v else float("nan")
    print("palavras: ref %d | nova %d | iguais %d" % (len(A), len(B), len(ds)))
    print("diferença (WER vs ref): %.1f%%  (trocas %d, a mais %d, faltando %d)" % (100 * wer, sub, ins, dele))
    print("erro de tempo nas iguais: início mediana %.3f s (p90 %.3f) | fim mediana %.3f s (p90 %.3f) | viés início %+.3f s" % (
        ab(ds), sorted(abs(x) for x in ds)[int(.9 * len(ds))] if ds else 0, ab(de), sorted(abs(x) for x in de)[int(.9 * len(de))] if de else 0, st.median(ds) if ds else 0))


if __name__ == "__main__":
    main()
