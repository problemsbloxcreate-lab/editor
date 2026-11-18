"""Passe 2 de corte (18/11 noite, feedback do Matheus: "MUITOS silêncios e cenas erradas passaram nos cortes").
Lê keeps_v1.json (a decupagem entregue) e reaperta:
  * fala = Silero VAD de todas as vozes da fonte ∪ palavras do ASR (máx. 0,45 s cada, com energia);
  * pausa entre falas > PMAX -> corta, deixando fim real + TAIL e ataque - LEAD (pausa final ~0,09 s);
  * janela de ação (protegida no cuts.py) sem fala -> no máximo ACT s, o trecho de MAIS movimento da imagem;
  * clipe sem fala nenhuma (aéreo) -> no máximo SOLO s de mais movimento;
  * cortes do REMOVE (tempo de fonte) = cenas erradas / bastidor achados na revisão visual.
Saída: keeps.json (+ relatório)."""
import json, os, sys, re
import numpy as np
W = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, W)
from cuts import SRC, SEG, FPS
import pov

PMAX, TAIL, LEAD = 0.22, 0.06, 0.03
ACT, SOLO = 1.0, 2.0
K0 = json.load(open(os.path.join(W, 'keeps_v1.json')))
PROT = {s[0]: s[5] for s in SEG}
REMOVE = json.load(open(os.path.join(W, 'remove.json'))) if os.path.exists(os.path.join(W, 'remove.json')) else []   # [[src, a, b, porquê]]
VS = {'A': 'A', 'C': 'C', 'B': 'B'}

# movimento da imagem (miniaturas 4 qps da varredura)
MOV = {}
for s in 'ABC':
    p = os.path.join(W, 'scan', s + '_thumb.npy')
    if os.path.exists(p):
        th = np.load(p, mmap_mode='r').astype(np.float32)
        d = np.abs(np.diff(th, axis=0)).mean(axis=(1, 2, 3))
        MOV[s] = np.concatenate([[0], d])


def motion(src, a, b):
    m = MOV.get(src)
    if m is None: return 0.0
    i0, i1 = int(a * 4), max(int(a * 4) + 1, int(b * 4))
    return float(m[i0:i1].mean()) if i0 < len(m) else 0.0


def best_window(src, a, b, L):
    """janela de L s dentro de [a, b] com mais movimento (passo 0,05)"""
    if b - a <= L: return a, b
    best, bt = -1, a
    for t in np.arange(a, b - L + 1e-6, 0.05):
        v = motion(src, t, t + L)
        if v > best: best, bt = v, t
    return bt, bt + L


VADT = json.load(open(os.path.join(W, 'vad.json')))


def speech(src, a, b):
    """fala = Silero VAD (todas as vozes da fonte) ∪ palavras do ASR que o VAD da MESMA faixa confirma (±0,15 s) —
    a faixa do PC (jogo alto) gera palavras fantasmas que seguravam as pausas."""
    S = SRC[src]
    iv = [(s_, e) for s_, e in S['vad'] if e > a and s_ < b]
    for w in S['words']:
        if w['e'] < a or w['s'] > b: continue
        e = min(w['e'], w['s'] + 0.45)
        tv = VADT[S['v'][w['tr']]]
        if any(s_ - 0.15 < e and w['s'] < e_ + 0.15 for s_, e_ in tv if e_ > w['s'] - 1 and s_ < e + 1):
            iv.append((w['s'], e))
    iv.sort()
    m = []
    for s_, e in iv:
        if m and s_ <= m[-1][1] + 0.02: m[-1][1] = max(m[-1][1], e)
        else: m.append([s_, e])
    return [(max(s_, a), min(e, b)) for s_, e in m if min(e, b) > max(s_, a)]


def inprot(seg, a, b):
    return any(b > p0 - 0.3 and a < p1 + 0.3 for p0, p1 in PROT.get(seg, []))


def removed(src, a, b):
    """subtrai os trechos de REMOVE de [a, b]"""
    out = [(a, b)]
    for s, x0, x1, why in REMOVE:
        if s != src: continue
        nx = []
        for p, q in out:
            if x1 <= p or x0 >= q: nx.append((p, q)); continue
            if x0 > p: nx.append((p, x0))
            if x1 < q: nx.append((x1, q))
        out = nx
    return out


GUI_SPEECH = []
new, rep = [], {'gui_s': 0.0, 'pausas': 0, 'acao': 0, 'solo': 0, 'cortado_s': 0.0, 'remove_s': 0.0}
prev_action = False
for k in K0:
    src, a, b = k['src'], k['src_in'], k['src_out']
    pieces = []
    if k['seg'] in ('hook', 'endbg'):
        pieces = [(a, b)]; prev_action = False
    else:
        sp = speech(src, a, b)
        if not sp:
            L = SOLO if not inprot(k['seg'], a, b) else ACT
            if prev_action and inprot(k['seg'], a, b): L = 0.0
            if L > 0: pieces = [best_window(src, a, b, L)]; rep['solo'] += 1
            prev_action = L > 0
        else:
            # entrada: até o ataque - LEAD (ação antes da fala, se protegida e o clipe anterior não deu ação)
            if sp[0][0] - a > LEAD + 0.04:
                if inprot(k['seg'], a, sp[0][0]) and sp[0][0] - a > 0.6 and not prev_action:
                    pieces.append(best_window(src, a, sp[0][0] - LEAD, ACT)); rep['acao'] += 1
                cur_a = sp[0][0] - LEAD
            else:
                cur_a = a
            for i in range(len(sp) - 1):
                e, s_ = sp[i][1], sp[i + 1][0]
                if s_ - e <= PMAX: continue
                pieces.append((cur_a, e + TAIL))
                if inprot(k['seg'], e, s_) and s_ - e > ACT + 0.2:
                    pieces.append(best_window(src, e + TAIL, s_ - LEAD, ACT)); rep['acao'] += 1
                else:
                    rep['pausas'] += 1
                cur_a = s_ - LEAD
            last = sp[-1][1]
            prev_action = False
            if b - last > TAIL + 0.04:
                pieces.append((cur_a, last + TAIL))
                if inprot(k['seg'], last, b) and b - last > 0.6:
                    pieces.append(best_window(src, last + TAIL, b, ACT)); rep['acao'] += 1; prev_action = True
            else:
                pieces.append((cur_a, b))
    # junta pedaços contíguos, aplica REMOVE, descarta < 4 quadros
    pieces.sort()
    mg = []
    for p, q in pieces:
        if mg and p <= mg[-1][1] + 1e-3: mg[-1] = (mg[-1][0], max(mg[-1][1], q))
        else: mg.append((p, q))
    fin = []
    for p, q in mg:
        for p2, q2 in removed(src, p, q):
            if k['seg'] in ('hook',): fin.append((p2, q2)); continue
            # tela proibida (painel/menu) sem a outra câmera limpa -> sai
            # sem a outra câmera: sem fala sai; com fala fica (o plano recebe um plano de corte da mesma câmera por cima)
            cut = [(x, y) for x, y in pov.bad_spans(src, p2, q2) if not pov.alt_clean(src, x, y) and not speech(src, x, y)]
            cur = [(p2, q2)]
            for x, y in cut:
                spk = speech(src, x, y)
                if spk and False: GUI_SPEECH.append((k['seg'], src, round(x, 2), round(y, 2), [(round(a_, 2), round(b_, 2)) for a_, b_ in spk]))
                nx = []
                for a_, b_ in cur:
                    if y <= a_ or x >= b_: nx.append((a_, b_)); continue
                    if x > a_: nx.append((a_, x))
                    if y < b_: nx.append((y, b_))
                cur = nx
                rep['gui_s'] += y - x
            fin += cur
    rep['remove_s'] += sum(q - p for p, q in mg) - sum(q - p for p, q in fin)
    first = True
    for p, q in fin:
        fa, fb = round(p * FPS), round(q * FPS)
        if fb - fa < 4: continue
        new.append({'src': src, 'src_in': fa / FPS, 'src_out': fb / FPS, 'seg': k['seg'], 'seg_start': bool(k.get('seg_start')) and first, 'xf_prev': True})
        first = False
    rep['cortado_s'] += (b - a) - sum(q - p for p, q in fin)

tl = 0.0
for i, k in enumerate(new):
    k['tl_in'] = round(tl, 6); tl += k['src_out'] - k['src_in']; k['tl_out'] = round(tl, 6)
    k['xf_prev'] = i > 0
json.dump(new, open(os.path.join(W, 'keeps.json'), 'w'), indent=1)
for g in GUI_SPEECH: print('TELA PROIBIDA SOBRE FALA', g)
print('clipes %d -> %d | timeline %.1f -> %.1f s' % (len(K0), len(new), K0[-1]['tl_out'], tl), rep)
