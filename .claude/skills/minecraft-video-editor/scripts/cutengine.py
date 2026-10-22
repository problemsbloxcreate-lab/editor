"""Motor de cortes de ritmo: tira TODA lacuna de fala (silêncio/ruído) e valida que nenhum corte pega início/fim de palavra.

Lição (Matheus, 15/10/2026, nota 4/10 no teste de 8 min): "silêncio de 0,5 s mata o ritmo" — v0 deixava pausas de 0,5 s
e cortava em cima de palavra. Regra nova: toda lacuna >= GMIN vira PAD_AFTER+PAD_BEFORE (~0,16 s); cortes só em silêncio
das DUAS vozes (checado por RMS), com folga antes do ataque da próxima palavra.

API:
    sp = SpeechMap(s1_wav, s2_wav, t0, t1)           # RMS 10 ms das 2 faixas de voz, máscara de fala com histerese
    keeps = tighten(sp, remove=[(a,b),...], start=None, end=None)   # lista [{src_in,src_out,tl_in,tl_out}]
    report = validate(sp, keeps)                      # RMS nas bordas de cada corte (deve ser < -45 dB nas duas vozes)
    src2tl(keeps, t)                                  # tempo de fonte -> tempo de timeline (ou None se removido)
CLI:  python cutengine.py s1.wav s2.wav T0 T1   -> imprime lacunas >= 0.22 s
"""
import numpy as np, soundfile as sf, sys, json

HOP = 0.01
ON, OFF = -38.0, -46.0          # dBFS RMS: quadro "fala" (ataque) / extensão de cauda e ataque
GMIN = 0.22                     # lacuna mínima p/ cortar
PAD_BEFORE, PAD_AFTER = 0.09, 0.10   # sobra antes do ataque / depois da cauda
EDGE_DB = -42.0                 # limite de RMS nas bordas de corte (ambas as vozes)


def _rms_db(path, a, b):
    """RMS em dB por janela de HOP.  21/10: lê em float32 por blocos (36 min estéreo: ~3 GB de pico -> ~50 MB) e guarda em cache
    ao lado do WAV (chave = tamanho/mtime/trecho), então rodar o plano de novo não relê o áudio."""
    import os
    st = os.stat(path)
    cache = "%s.rms_%d_%d_%.3f_%.3f_%g.npy" % (path, st.st_size, int(st.st_mtime), a, b, HOP)
    if os.path.exists(cache):
        return np.load(cache)
    fs = sf.info(path).samplerate      # 19/10: aceita WAV de qualquer taxa (antes supunha 48 kHz)
    n = int(HOP * fs)
    out = []
    for blk in sf.blocks(path, blocksize=n * 6000, start=int(a * fs), stop=int(b * fs), always_2d=True, dtype="float32"):
        x = blk.mean(axis=1)
        m = len(x) // n
        if m:
            out.append(20 * np.log10(np.sqrt((x[:m * n].reshape(m, n) ** 2).mean(axis=1)) + 1e-9))
    r = np.concatenate(out) if out else np.zeros(0)
    try:
        np.save(cache, r)
    except OSError:
        pass
    return r


class SpeechMap:
    def __init__(self, s1, s2, t0=0.0, t1=None, on=ON, off=OFF):
        import soundfile
        dur = soundfile.info(s1).duration
        self.t0, self.t1 = t0, min(t1 or dur, dur)
        self.r1 = _rms_db(s1, self.t0, self.t1)
        self.r2 = _rms_db(s2, self.t0, self.t1)
        n = min(len(self.r1), len(self.r2))
        self.r1, self.r2 = self.r1[:n], self.r2[:n]
        self.v = np.maximum(self.r1, self.r2)
        act = self.v > on
        ext = act.copy()
        for i in range(1, n):
            if not ext[i] and ext[i - 1] and self.v[i] > off: ext[i] = True
        for i in range(n - 2, -1, -1):
            if not ext[i] and ext[i + 1] and self.v[i] > off: ext[i] = True
        self.speech = ext
        self.n = n

    def idx(self, t):
        return int(round((t - self.t0) / HOP))

    def gaps(self, a=None, b=None, gmin=GMIN):
        """lista de (ini, fim) em s de fonte onde não há fala, >= gmin."""
        a = self.t0 if a is None else a; b = self.t1 if b is None else b
        i, n, out = self.idx(a), min(self.idx(b), self.n), []
        i = max(i, 0)
        while i < n:
            if not self.speech[i]:
                j = i
                while j < n and not self.speech[j]: j += 1
                if (j - i) * HOP >= gmin: out.append((self.t0 + i * HOP, self.t0 + j * HOP))
                i = j
            else: i += 1
        return out

    def onset_after(self, t):
        """primeiro quadro de fala >= t (s)"""
        i = max(self.idx(t), 0)
        while i < self.n and not self.speech[i]: i += 1
        return self.t0 + i * HOP

    def offset_before(self, t):
        """fim (exclusivo) do último quadro de fala <= t"""
        i = min(self.idx(t), self.n - 1)
        while i > 0 and not self.speech[i]: i -= 1
        return self.t0 + (i + 1) * HOP

    def edge_db(self, t, w=0.03):
        a, b = max(self.idx(t - w), 0), min(self.idx(t + w) + 1, self.n)
        return float(self.r1[a:b].max()), float(self.r2[a:b].max())



def _quiet(sp, t, lo, hi):
    """ponto mais silencioso (RMS máx ±15 ms das 2 vozes) em [lo,hi], preferindo o mais perto de t"""
    best, bt = None, t
    k = lo
    while k <= hi + 1e-9:
        d = max(sp.edge_db(k, 0.015))
        score = (d > EDGE_DB, d if d > EDGE_DB else 0.0, abs(k - t))
        if best is None or score < best: best, bt = score, k
        k += HOP
    return bt


def tighten(sp, remove=(), start=None, end=None, gmin=GMIN, pad_before=PAD_BEFORE, pad_after=PAD_AFTER, protect=()):
    """Devolve keeps [{src_in, src_out, tl_in, tl_out}] cobrindo [start,end] sem as lacunas e sem os 'remove' (cortes de conteúdo).
    protect = [(a,b)] lacunas que NÃO devem ser encurtadas (pausa dramática de piada)."""
    if start is None: start = max(sp.t0, sp.onset_after(sp.t0) - pad_before)   # tira o ruído morto antes da 1ª palavra
    end = sp.t1 if end is None else end
    cuts = []  # intervalos removidos [a,b]
    # 1) cortes de conteúdo: aparam nas bordas de fala vizinhas
    for a, b in sorted(remove):
        a2 = sp.offset_before(a) + pad_after if not sp.speech[sp.idx(a)] else a
        b2 = sp.onset_after(b) - pad_before if not sp.speech[sp.idx(b)] else b
        cuts.append((a2, max(a2, b2)))
    # 2) lacunas
    for g0, g1 in sp.gaps(start, end, gmin):
        if any(p0 <= g0 and g1 <= p1 for p0, p1 in protect): continue
        c0, c1 = _quiet(sp, g0 + pad_after, g0 + 0.04, g0 + pad_after + 0.12), _quiet(sp, g1 - pad_before, g1 - pad_before - 0.12, g1 - 0.05)
        if c1 - c0 > 0.02: cuts.append((c0, c1))
    # início: corta tudo antes de 'start'
    if start > sp.t0: cuts.append((sp.t0, start))
    cuts.sort()
    merged = []
    for c in cuts:
        if merged and c[0] <= merged[-1][1] + 1e-6: merged[-1] = (merged[-1][0], max(merged[-1][1], c[1]))
        else: merged.append(c)
    keeps, pos, tl = [], sp.t0, 0.0
    for c0, c1 in merged:
        if c0 > pos + 1e-6:
            keeps.append({"src_in": pos, "src_out": c0, "tl_in": tl, "tl_out": tl + (c0 - pos)}); tl += c0 - pos
        pos = max(pos, c1)
    if end > pos + 1e-6: keeps.append({"src_in": pos, "src_out": end, "tl_in": tl, "tl_out": tl + (end - pos)})
    return keeps


def src2tl(keeps, t):
    for k in keeps:
        if k["src_in"] - 1e-9 <= t <= k["src_out"] + 1e-9: return k["tl_in"] + (t - k["src_in"])
    return None


def src2tl_snap(keeps, t):
    """como src2tl, mas se t caiu num trecho removido, devolve o início da próxima keep"""
    for k in keeps:
        if t <= k["src_out"]: return k["tl_in"] + max(0.0, t - k["src_in"])
    return keeps[-1]["tl_out"]


def validate(sp, keeps, thr=EDGE_DB):
    """para cada junção de corte: RMS máx (±30 ms) de s1/s2 no fim da keep i e no início da keep i+1. Marca 'RUIM' se > thr."""
    rep = []
    for i in range(len(keeps) - 1):
        a, b = keeps[i]["src_out"], keeps[i + 1]["src_in"]
        ea, eb = sp.edge_db(a), sp.edge_db(b)
        bad = max(ea) > thr or max(eb) > thr
        rep.append({"i": i, "src_out": round(a, 3), "src_in": round(b, 3), "out_db": [round(x, 1) for x in ea], "in_db": [round(x, 1) for x in eb], "ruim": bad})
    return rep


# ---------------------------------------------------------------------------------------------------------------
# v2 (16/10/2026) — padrão medido na sequência "teste corrigido" do Matheus (nota alta):
#   troca de falante (hand-off) = lacuna ~0 (0-0,09 s); mesma pessoa pausando = ~0,2 s; corte de entrada no 1º quadro do ataque.
#   Cortes apertados são suavizados por TRANSIÇÃO DE ÁUDIO "Potência constante" (0,2-0,3 s centrada no corte) nas 3 faixas do bruto.
HANDOFF_GMIN = 0.15
HANDOFF_TAIL = 0.04      # sobra após a cauda quando o falante muda
HANDOFF_LEAD = 0.015     # sobra antes do ataque quando o falante muda (~1 quadro)


def _speaker(sp, a, b):
    i, j = max(sp.idx(a), 0), min(max(sp.idx(b), sp.idx(a) + 1), sp.n)
    return 1 if sp.r1[i:j].mean() >= sp.r2[i:j].mean() else 2


def tighten2(sp, remove=(), start=None, end=None, protect=(), same_gmin=GMIN, handoff_gmin=HANDOFF_GMIN, words=None, min_keep=0.5):
    """Como tighten(), mas speaker-aware. Devolve keeps com 'xf_prev': True (junção não contígua -> aplicar Potência constante)
    e 'handoff': True/False."""
    if start is None: start = max(sp.t0, sp.onset_after(sp.t0) - 0.02)
    end = sp.t1 if end is None else end
    cuts = []
    for a, b in sorted(remove):
        a2 = sp.offset_before(a) + 0.09 if not sp.speech[sp.idx(a)] else a
        b2 = sp.onset_after(b) - 0.02 if not sp.speech[sp.idx(b)] else b
        cuts.append((a2, max(a2, b2), None))
    for g0, g1 in sp.gaps(start, end, min(same_gmin, handoff_gmin)):
        if any(p0 <= g0 and g1 <= p1 for p0, p1 in protect): continue
        spk0, spk1 = _speaker(sp, g0 - 0.15, g0), _speaker(sp, g1, g1 + 0.15)
        hand = spk0 != spk1
        if not hand and (g1 - g0) < same_gmin: continue
        if hand:
            c0, c1 = g0 + HANDOFF_TAIL, g1 - HANDOFF_LEAD
        else:
            c0 = _quiet(sp, g0 + PAD_AFTER, g0 + 0.04, g0 + PAD_AFTER + 0.12)
            c1 = _quiet(sp, g1 - PAD_BEFORE, g1 - PAD_BEFORE - 0.12, g1 - 0.05)
        if c1 - c0 > 0.02: cuts.append((c0, c1, hand))
    if start > sp.t0: cuts.append((sp.t0, start, None))
    cuts.sort(key=lambda c: c[0])
    merged = []
    for c in cuts:
        if merged and c[0] <= merged[-1][1] + 1e-6: merged[-1] = (merged[-1][0], max(merged[-1][1], c[1]), merged[-1][2] if merged[-1][2] is not None else c[2])
        else: merged.append(c)
    # fragmentos: ping-pong rápido de falas picota o áudio. (a) trecho curto SEM palavra no ASR = ruído -> some junto com os 2 cortes vizinhos;
    # (b) trecho curto COM palavra -> desfaz o menor dos 2 cortes vizinhos (volta a pausa natural) p/ não picotar.
    if words is not None:
        changed = True
        while changed and len(merged) >= 2:
            changed = False
            for i in range(len(merged) - 1):
                a, b = merged[i][1], merged[i + 1][0]
                if b - a >= min_keep: continue
                has_word = any(a - 0.05 <= ws < b for ws, we in words)
                if not has_word and b - a < 0.45:
                    merged[i:i + 2] = [(merged[i][0], merged[i + 1][1], merged[i + 1][2])]
                else:
                    ca, cb = merged[i][1] - merged[i][0], merged[i + 1][1] - merged[i + 1][0]
                    del merged[i if ca <= cb else i + 1]
                changed = True; break
    keeps, pos, tl, prev_hand = [], sp.t0, 0.0, None
    for c0, c1, hand in merged:
        if c0 > pos + 1e-6:
            keeps.append({"src_in": pos, "src_out": c0, "tl_in": tl, "tl_out": tl + (c0 - pos), "handoff": prev_hand, "xf_prev": bool(keeps)}); tl += c0 - pos
        pos = max(pos, c1); prev_hand = bool(hand)
    if end > pos + 1e-6: keeps.append({"src_in": pos, "src_out": end, "tl_in": tl, "tl_out": tl + (end - pos), "handoff": prev_hand, "xf_prev": bool(keeps)})
    return keeps


# ---------------------------------------------------------------------------------------------------------------
# v3 (19/10/2026) — padrão medido na DECUPAGEM PROFISSIONAL do Matheus (vídeo inteiro "Bebi toda a água do mundo",
# references/decupagem-matheus-19out.md): entrada no 1º quadro do som (≤10–20 ms), saída 20–50 ms depois do fim do som,
# lacuna 0,03–0,07 s para QUALQUER falante (o v2 deixava ~0,19 s no mesmo falante). Os cortes de CONTEÚDO vêm da
# passada de texto (textpass.find_removals: bastidor, retake, gaguejo, muleta) e têm as bordas refinadas pela energia.
LEAD3, TAIL3, GMIN3 = 0.015, 0.020, 0.10      # calibrado 19/10 contra a Sequência 01 (|Δ| entrada 33 ms, saída 51 ms)
ON3, OFF3 = -38.0, -46.0                      # faixas cruas do bruto (mic POV sem gate); -50 só em faixa com gate


def _edge_out(sp, a, s0, tail):
    """corte de SAÍDA antes de um trecho removido: a = fim (ASR) da palavra mantida, s0 = início (ASR) da 1ª removida.
    Procura o 1º quadro sem fala depois da palavra mantida (o ASR estica o fim -> começa a busca 0,25 s antes)."""
    i0, i1 = max(sp.idx(a - 0.25), 0), min(sp.idx(max(s0, a) + 0.08), sp.n - 1)
    for i in range(i0, i1 + 1):
        if not sp.speech[i] and (i == 0 or sp.speech[i - 1] or i == i0):
            if sp.t0 + i * HOP >= a - 0.25:
                return min(sp.t0 + i * HOP + tail, max(s0, a))
    j0, j1 = max(sp.idx(a - 0.08), 0), min(sp.idx(max(s0, a) + 0.08), sp.n - 1)   # sem silêncio: no vale de energia
    return sp.t0 + (j0 + int(np.argmin(sp.v[j0:j1 + 1]))) * HOP if j1 > j0 else a


def _edge_in(sp, b, e1, lead):
    """corte de ENTRADA depois de um trecho removido: b = início (ASR) da palavra mantida, e1 = fim (ASR) da última removida.
    Volta do início da palavra até o 1º quadro do ataque (o ASR atrasa o início em até ~0,26 s)."""
    i = min(sp.idx(b + 0.05), sp.n - 1)
    lo = max(sp.idx(min(e1, b) - 0.05), 0)
    if not sp.speech[i]:
        while i < min(sp.idx(b + 0.3), sp.n - 1) and not sp.speech[i]: i += 1
    k = i
    while k > lo and sp.speech[k - 1]: k -= 1
    if k > lo: return sp.t0 + k * HOP - lead
    j0, j1 = max(sp.idx(min(e1, b) - 0.08), 0), min(sp.idx(b + 0.05), sp.n - 1)
    return sp.t0 + (j0 + int(np.argmin(sp.v[j0:j1 + 1]))) * HOP if j1 > j0 else b


def tighten3(sp, remove=(), start=None, end=None, protect=(), gmin=GMIN3, lead=LEAD3, tail=TAIL3, words=None, min_keep=0.5):
    """remove = [{"a","b",...}] da textpass (ou tuplas (a,b) já em silêncio). Devolve keeps como tighten2 (xf_prev, handoff)."""
    if start is None: start = max(sp.t0, sp.onset_after(sp.t0) - lead)
    end = sp.t1 if end is None else end
    cuts = []
    for r in remove:
        if isinstance(r, dict):
            a, b = r["a"], r["b"]
            s0 = r.get("s0", a); e1 = r.get("e1", b)
            c0, c1 = _edge_out(sp, a, max(s0, a), tail), _edge_in(sp, b, min(e1, b), lead)
        else:
            c0, c1 = r
        if c1 > c0: cuts.append((c0, c1, None))
    for g0, g1 in sp.gaps(start, end, gmin):
        if any(p0 <= g0 and g1 <= p1 for p0, p1 in protect): continue
        hand = _speaker(sp, g0 - 0.15, g0) != _speaker(sp, g1, g1 + 0.15) if g0 - 0.15 > sp.t0 and g1 + 0.15 < sp.t1 else None
        c0, c1 = g0 + tail, g1 - lead
        if c1 - c0 > 0.02: cuts.append((c0, c1, hand))
    if start > sp.t0: cuts.append((sp.t0, start, None))
    cuts.sort(key=lambda c: c[0])
    merged = []
    for c in cuts:
        if merged and c[0] <= merged[-1][1] + 1e-6:
            merged[-1] = (merged[-1][0], max(merged[-1][1], c[1]), merged[-1][2] if merged[-1][2] is not None else c[2])
        else: merged.append(c)
    if words is not None:   # mesma regra de fragmento do v2
        changed = True
        while changed and len(merged) >= 2:
            changed = False
            for i in range(len(merged) - 1):
                a, b = merged[i][1], merged[i + 1][0]
                if b - a >= min_keep: continue
                has_word = any(a - 0.05 <= ws < b for ws, we in words)
                if not has_word and b - a < 0.45:
                    merged[i:i + 2] = [(merged[i][0], merged[i + 1][1], merged[i + 1][2])]
                else:
                    ca, cb = merged[i][1] - merged[i][0], merged[i + 1][1] - merged[i + 1][0]
                    del merged[i if ca <= cb else i + 1]
                changed = True; break
    keeps, pos, tl, prev_hand = [], sp.t0, 0.0, None
    for c0, c1, hand in merged:
        if c0 > pos + 1e-6:
            keeps.append({"src_in": pos, "src_out": c0, "tl_in": tl, "tl_out": tl + (c0 - pos), "handoff": prev_hand, "xf_prev": bool(keeps)}); tl += c0 - pos
        pos = max(pos, c1); prev_hand = bool(hand)
    if end > pos + 1e-6: keeps.append({"src_in": pos, "src_out": end, "tl_in": tl, "tl_out": tl + (end - pos), "handoff": prev_hand, "xf_prev": bool(keeps)})
    return keeps


if __name__ == "__main__":
    sp = SpeechMap(sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4]))
    gs = sp.gaps()
    print(len(gs), "lacunas >=", GMIN, "s; soma", round(sum(b - a for a, b in gs), 1), "s")
    for a, b in gs: print("%8.2f-%8.2f  %.2fs" % (a, b, b - a))
