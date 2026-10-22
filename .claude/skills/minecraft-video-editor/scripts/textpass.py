"""Passada de TEXTO da decupagem (19/10/2026) — o que o Matheus tira por CONTEXTO antes de qualquer corte de silêncio
(padrão medido na Sequência 01 do "Bebi toda a água do mundo": references/decupagem-matheus-19out.md).

Entrada: palavras do ASR por faixa de voz [(ini, fim, faixa, palavra), ...] (faixa 1 = POV, 2 = call).
Saída:   lista de remoções [{"a": fim da palavra mantida anterior, "b": início da próxima palavra mantida, "why": ..., "text": ...}]
         em tempo de FONTE — o cutengine.tighten3 refina as bordas pela energia.

Regras (ordem):
  1. bastidor   — contagem "3, 2, 1", "pode falar/gravar", "corta aí", "falar de novo", "reiniciou", "buguei", a call combinando quem fala
  2. retake     — frase recomeçada (mesmo início / alta semelhança em <= 15 s, mesmo falante): fica o ÚLTIMO take, a largada falsa sai
                  (inclusive o recomeço DENTRO da mesma frase: "Enquanto vocês estão sugando Enquanto vocês estão sugando aqui")
  3. gaguejo    — palavra de função repetida com pausa ("e… e vamos", "o… o problema"): fica a 2ª
  4. muleta     — muleta no início da frase separada por pausa ("É, | mas…", "Olha, | …") e frases só de muleta ("É.", "É verdade" eco)
Uso:  python textpass.py t1.json t2.json A B [--json out.json]
"""
import json, re, sys, unicodedata
from difflib import SequenceMatcher

MAXW = 1.0                # duração máx. de uma palavra do ASR
UTT_GAP = 0.45            # pausa que separa frases do mesmo falante
RETAKE_GAP = 3.0          # pausa máx. entre a largada falsa e o take bom
RESTART = ["corta ai", "reiniciou", "reiniciar", "falar de novo", "deixa eu falar de novo", "pera ai de novo", "de novo de novo",
           "deixa eu repetir", "vou repetir", "errei"]
BASTIDOR = ["3 2 1", "tres dois um", "pode falar", "pode gravar", "corta ai", "falar de novo", "deixa eu falar de novo",
            "reiniciou", "reiniciar", "buguei", "era tu que ia falar", "tu que ia falar", "voce que ia falar", "pera ai de novo",
            "depois que o patrao falar", "depois que o patao falar", "pode ir pode ir", "vamos la espera", "como e que ta o bruto",
            "ta gravando", "ta gravando ai", "pode comecar", "de novo de novo", "deixa eu repetir", "vou repetir", "errei"]
FUNC = {"e", "o", "a", "os", "as", "eu", "que", "mas", "e", "ai", "se", "de", "pra", "para", "um", "uma", "no", "na", "do", "da",
        "tem", "vai", "ta", "isso", "essa", "esse", "quer", "so", "a gente"}
EXPR = {"bebe", "agua", "vai", "pera", "calma", "nao", "olha", "isso", "bora", "vem", "caraca", "ai", "bebendo", "sugando", "vamos"}
# ^ palavras que a turma repete por ÊNFASE ("pera aí, pera aí", "tô bebendo, tô bebendo") — não contam como recomeço
FILL = {"e", "eh", "ai", "entao", "tipo", "mano", "meu", "ne", "olha", "quer", "mas", "agora", "aqui", "galera", "bom", "ah", "ha",
        "hum", "o", "oi", "po", "cara", "pois", "isso", "beleza", "verdade", "ue", "hein", "enfim"}
FILL_LEAD = {"e", "eh", "ai", "entao", "tipo", "mano", "meu", "olha", "quer", "mas", "bom", "ah", "ha", "hum", "o", "po", "cara", "ue", "enfim"}


def norm(w):
    w = unicodedata.normalize("NFD", w.lower())
    w = "".join(c for c in w if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9%]+", "", w)


def load_words(paths):
    W = []
    for k, p in enumerate(paths, 1):
        for w in json.load(open(p, encoding="utf8"))["words"]:
            n = norm(w["w"])
            # o Whisper estica o fim da palavra antes de silêncio (até 9 s visto aqui): limita a ~1 s
            s0, e0 = float(w["s"]), float(w["e"])
            if n: W.append((s0, min(e0, s0 + MAXW), k, n, w["w"].strip()))
    W.sort()
    return W


def utterances(W):
    U = []
    for k in sorted({w[2] for w in W}):
        cur = []
        for w in (x for x in W if x[2] == k):
            if cur and w[0] - cur[-1][1] > UTT_GAP:
                U.append(cur); cur = []
            cur.append(w)
        if cur: U.append(cur)
    U.sort(key=lambda u: u[0][0])
    return U


def _toks(ws): return [w[3] for w in ws]


def _similar(a, b):
    """a = largada falsa?  b = take bom?"""
    if len(a) == 0 or len(b) == 0: return False
    if len(a) >= 2 and a[:2] == b[:2] and SequenceMatcher(None, a, b[:len(a) + 2]).ratio() >= 0.5: return True
    if len(a) <= 3 and b[:len(a)] == a and len(b) > len(a): return True            # "Aqui galera" -> "Aqui galera eu acho que…"
    if len(a) >= 3 and SequenceMatcher(None, a, b[:len(a) + 2]).ratio() >= 0.62: return True
    return False


def find_removals(W, A=None, B=None):
    if A is not None: W = [w for w in W if A <= w[0] < B]
    U = utterances(W)
    rem = []   # (idx_first_removed_word_in_W, idx_last_removed, why)
    idx = {id(w): i for i, w in enumerate(W)}
    def add(ws_from, ws_to, why):
        rem.append((idx[id(ws_from)], idx[id(ws_to)], why))
    def solo(w0, w1):
        """remoção de UM falante só vale se nenhuma palavra da outra voz cai no intervalo (senão cortaria a outra voz)"""
        k = w0[2]
        return not any(w[2] != k and w[1] > w0[0] + 0.02 and w[0] < w1[1] - 0.02 for w in W)
    # 1) bastidor: a frase inteira. Se é "corta / reiniciou / de novo", o take RECOMEÇA: sai também desde a frase do POV
    #    (até 20 s antes) que é refeita depois, até o início da refeita.
    for ui, u in enumerate(U):
        t = " ".join(_toks(u))
        tt = " " + t + " "
        if any(" " + p + " " in tt for p in BASTIDOR):
            # só as SENTENÇAS (pontuação do ASR) que contêm o bastidor: a mesma frase longa da call pode seguir em conteúdo
            toks = _toks(u)
            ends = [i for i, w in enumerate(u) if re.search(r"[.?!]$", w[4])]
            def sent(i):
                s = max([e + 1 for e in ends if e < i] or [0]); e = min([e for e in ends if e >= i] or [len(u) - 1]); return s, e
            for p in BASTIDOR:
                pt = p.split()
                for i in range(len(toks) - len(pt) + 1):
                    if toks[i:i + len(pt)] == pt:
                        s0_, _ = sent(i); _, e1_ = sent(i + len(pt) - 1)
                        add(u[s0_], u[e1_], "bastidor")
            if any(" " + p + " " in tt for p in RESTART):
                before = [x for x in U[:ui] if x[0][2] == 1 and u[0][0] - x[0][0] <= 20]
                after = [x for x in U[ui + 1:] if x[0][2] == 1 and x[0][0] - u[-1][1] <= 25]
                done = False
                for x in before:
                    for y in after:
                        if len(set(_toks(x))) > 2 and _similar(_toks(x), _toks(y)):
                            rem.append((idx[id(x[0])], idx[id(y[0])] - 1, "bastidor-retake")); done = True; break
                    if done: break
    # 1b) dois bastidores a <= 15 s um do outro: tudo entre eles é bastidor ("corta aí … reiniciou")
    bast = [r for r in rem if r[2] == "bastidor"]
    for (a0, a1, _), (b0, b1, _) in zip(bast, bast[1:]):
        if W[b0][0] - W[a1][1] <= 15: rem.append((a0, b1, "bastidor"))
    # 2a) retake entre frases do mesmo falante. POV (faixa 1, segue roteiro): qualquer recomeço parecido.
    #     Call (faixa 2): só se a 1ª for INCOMPLETA (mais curta e não repetida inteira) — a call repetir a fala de propósito
    #     ("eu não tinha pensado nisso" ×2, "não quero ficar barrigudo" ×2) é piada e FICA.
    for i, u in enumerate(U):
        for v in U[i + 1:i + 6]:
            if v[0][2] != u[0][2]: continue
            if v[0][0] - u[-1][1] > RETAKE_GAP: break      # recomeço é colado; frases parecidas longe são frases novas
            a, b = _toks(u), _toks(v)
            if len(set(a)) <= 2: continue                    # "não, não, não" / "vai, vai" = ênfase
            if len(b) < len(a): continue                     # o take bom não é mais curto que a largada falsa
            if u[0][2] != 1 and not (len(a) < len(b) and b[:len(a)] != a): continue
            if a == b[:len(a)] and len(a) >= 4 and u[0][2] != 1: continue
            if _similar(a, b):
                # tudo entre o início da largada falsa e o início do take bom sai (inclui conversa no meio)
                j0 = idx[id(u[0])]; j1 = idx[id(v[0])] - 1
                if j1 >= j0: rem.append((j0, j1, "retake"))
                break
    # 2b) recomeço dentro da mesma frase: n-grama de 3 que reaparece logo depois, com a 1ª ocorrência INCOMPLETA
    #     (repetição exata da frase inteira = ênfase, fica)
    for u in U:
        if u[0][2] != 1: continue                            # call: "já tá gigante, já tá rechonchudo" é paralelismo, não recomeço
        t = _toks(u); i = 0
        while i < len(t) - 3:
            hit = None
            pov = u[0][2] == 1
            for j in range(i + 2, min(len(t) - 1, i + 11)):
                L = j - i
                g2 = t[i:i + 2]
                same2 = g2 == t[j:j + 2] and len(set(g2)) == 2 and not all(x in FUNC or x in EXPR for x in g2)
                if not same2: continue
                if t[i:j] == t[j:j + L]:
                    # repetiu igual: ênfase se a frase acaba ali; recomeço (POV) se o 2º take CONTINUA além do 1º
                    if pov and len(t) - (j + L) >= 2: hit = j
                    break
                if len(t) - j < L - 2: break                 # o 2º é o fragmento, não o take bom
                if t[i:i + 3] == t[j:j + 3] or SequenceMatcher(None, t[i:j], t[j:j + L + 1]).ratio() >= 0.5:
                    hit = j; break
            if hit is not None and solo(u[i], u[hit - 1]):
                rem.append((idx[id(u[i])], idx[id(u[hit - 1])], "retake-interno")); i = hit
            else: i += 1
    # 3) gaguejo: palavra de função repetida com pausa (compara a grafia original: "ó o" não é gaguejo)
    for a, b in zip(W, W[1:]):
        ga, gb = re.sub(r"[^\w]", "", a[4].lower()), re.sub(r"[^\w]", "", b[4].lower())
        if a[2] == b[2] and ga == gb and a[3] in FUNC and b[0] - a[1] >= 0.10 and solo(a, a):
            add(a, a, "gaguejo")
    # 4) muletas
    for u in U:
        t = _toks(u)
        if len(t) <= 2 and all(x in FILL for x in t):
            if solo(u[0], u[-1]): add(u[0], u[-1], "muleta-só")
            continue
        if len(u) >= 3 and t[0] in FILL_LEAD and u[1][0] - u[0][1] >= 0.15 and solo(u[0], u[0]):
            add(u[0], u[0], "muleta-início")
    # junta e converte para tempo (a = fim da palavra mantida anterior, b = início da próxima mantida)
    rem.sort()
    merged = []
    for j0, j1, why in rem:
        if merged and j0 <= merged[-1][1] + 1:
            merged[-1] = (merged[-1][0], max(merged[-1][1], j1), merged[-1][2] if why in merged[-1][2] else merged[-1][2] + "+" + why)
        else: merged.append((j0, j1, why))
    out = []
    for j0, j1, why in merged:
        s0 = W[j0][0]; e1 = max(w[1] for w in W[j0:j1 + 1])
        a = max([w[1] for w in W[:j0] if w[1] <= s0 + 0.02] or [s0 - 0.05])
        b = min([w[0] for w in W[j1 + 1:] if w[0] >= e1 - 0.02] or [e1 + 0.05])
        a = min(max(a, s0 - 0.6), s0)           # se a palavra anterior está longe, o silêncio fica p/ o motor
        b = max(min(b, e1 + 0.6), e1)
        out.append({"a": round(a, 3), "b": round(b, 3), "s0": round(s0, 3), "e1": round(e1, 3), "why": why,
                    "text": " ".join(w[4] for w in W[j0:j1 + 1])})
    return out


if __name__ == "__main__":
    t1, t2, A, B = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
    R = find_removals(load_words([t1, t2]), A, B)
    for r in R: print("%8.2f-%8.2f  %-22s %s" % (r["a"], r["b"], r["why"], r["text"]))
    print(len(R), "remoções; %.1f s" % sum(r["b"] - r["a"] for r in R))
    if "--json" in sys.argv: json.dump(R, open(sys.argv[sys.argv.index("--json") + 1], "w", encoding="utf8"), ensure_ascii=False, indent=1)
