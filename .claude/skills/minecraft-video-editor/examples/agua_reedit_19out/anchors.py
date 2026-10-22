"""Âncoras por PALAVRA em tempo de timeline + refino pela energia da voz da timeline (A1 dub ∪ A2 call) + cortes do V1."""
import json, re, unicodedata, numpy as np
DEC = r"C:\Users\mathe\Skills\_research\mc-decup"
HERE = r"C:\Users\mathe\Skills\_research\mc-agua-edit"
W = json.load(open(HERE + r"\tl_words.json", encoding="utf8"))
VOX = np.maximum(np.load(DEC + r"\tl_A1.rms.npy"), np.load(DEC + r"\tl_A2.rms.npy"))
_d = json.load(open(DEC + r"\dump.json", encoding="utf8"))[0]
CUTS = sorted({round(c[1], 4) for c in _d["v"][0]} - {0.0})          # inícios dos clipes de V1 = cortes
V1 = [(c[1], c[2], c[3], c[4], c[5]) for c in _d["v"][0]]             # (start, end, in, out, disabled)
END = _d["end"]


def norm(w):
    w = unicodedata.normalize("NFD", w.lower())
    return re.sub(r"[^a-z0-9%]+", "", "".join(c for c in w if unicodedata.category(c) != "Mn"))


NW = [(w[0], w[1], w[2], norm(w[3])) for w in W]


def refine(t, back=0.3, fwd=0.12, thr=-45):
    """início real da fala perto de t (o ASR atrasa): 1º quadro > thr a partir de t-back, se houver silêncio antes"""
    i0, i1 = int((t - back) * 100), int((t + fwd) * 100)
    seg = VOX[max(i0, 0):i1]
    on = np.where(seg > thr)[0]
    if len(on) == 0: return t
    # procura o começo do trecho com som que contém/segue t
    k = int((t - (t - back)) * 100)
    k = min(k, len(seg) - 1)
    if seg[k] > thr:
        while k > 0 and seg[k - 1] > thr: k -= 1
    else:
        nxt = on[on >= k]
        k = nxt[0] if len(nxt) else on[-1]
    return round(max(i0, 0) / 100 + k / 100, 3)


def A(phrase, near, win=12.0, spk=None, end=False):
    """tempo (timeline) do início (ou fim) da 1ª ocorrência de 'phrase' mais perto de 'near' (s ou 'mm:ss')."""
    if isinstance(near, str):
        m, s = near.split(":"); near = int(m) * 60 + float(s)
    toks = [norm(x) for x in phrase.split() if norm(x)]
    best = None
    for i in range(len(NW)):
        if abs(NW[i][0] - near) > win: continue
        if spk and NW[i][2] != spk: continue
        # casa a sequência permitindo palavras da OUTRA voz intercaladas
        j, k, last = i, 0, None
        while j < len(NW) and k < len(toks) and NW[j][0] - NW[i][0] < 6:
            if NW[j][3] == toks[k] and (k == 0 or NW[j][2] == NW[i][2]): last = j; k += 1
            elif k == 0: break
            j += 1
        if k == len(toks):
            d = abs(NW[i][0] - near)
            if best is None or d < best[0]: best = (d, i, last)
    if best is None: raise KeyError("frase não achada: %r perto de %.1f" % (phrase, near))
    _, i, last = best
    return round(NW[last][1], 3) if end else refine(NW[i][0])


def cut_near(t, maxd=1.5):
    c = min(CUTS, key=lambda c: abs(c - t))
    return c if abs(c - t) <= maxd else None


def clip_at(t):
    for v in V1:
        if v[0] - 1e-3 <= t < v[1] - 1e-3: return v
    return None


def mmss(t): return "%d:%05.2f" % (int(t // 60), t % 60)
