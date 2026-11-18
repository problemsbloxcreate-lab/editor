"""Telas proibidas (painel de direção, pausa, opções, inventário) e escolha de POV por trecho.
gui(src) -> array bool 4 qps; choose(keeps, locked) -> lista de capas de POV (V2, vídeo-só)."""
import os, json
import numpy as np
W = os.path.dirname(os.path.abspath(__file__))
FPS_SCAN = 4
# sincronia de IMAGEM (média dos dois sentidos da voz pelo Discord: atraso ~0,16 s)
OFF_AB = 4.455        # B = A + 4,455
OFF_CB = 3495.615     # B = C + 3495,615
DUR = {'A': 2317.0, 'B': 4055.78, 'C': 526.7}
_G = {}


def classes(src):
    """por amostra (4 qps): 0 jogo, 1 painel de direção, 2 menu escuro sem inventário (pausa/opções/área de trabalho/menu radial), 3 inventário"""
    if ('c', src) in _G: return _G[('c', src)]
    th = np.load(os.path.join(W, 'scan', src + '_thumb.npy'), mmap_mode='r')
    f = np.load(os.path.join(W, 'scan', src + '_feat.npy'))
    out = np.zeros(len(th), np.int8)
    for i0 in range(0, len(th), 2000):
        im = th[i0:i0 + 2000].astype(np.int16)
        r, g, b = im[..., 0], im[..., 1], im[..., 2]
        lum = 0.299 * r + 0.587 * g + 0.114 * b
        gray = (np.abs(r - g) < 10) & (np.abs(g - b) < 12) & (lum > 80) & (lum < 140)
        gtop = gray[:, :22].mean(axis=(1, 2)); gbot = gray[:, 22:].mean(axis=(1, 2))
        lumbot = lum[:, 22:].mean(axis=(1, 2))
        satp = im.max(3) - im.min(3); sat = satp.mean(axis=(1, 2))
        lg = ((lum > 170) & (satp < 20))[:, 10:45, 30:66].mean(axis=(1, 2))
        dark, chat = f[i0:i0 + 2000, 5], f[i0:i0 + 2000, 6]
        panel = (gtop > 0.3) & (gbot < 0.12) & (lumbot < 60)          # painel de direção (1440p): botões no topo, mundo escurecido embaixo
        g_mid = gray[:, 6:42].mean(axis=(1, 2)); g_low = gray[:, 48:].mean(axis=(1, 2)); l_low = lum[:, 48:].mean(axis=(1, 2))
        panel |= (g_mid > 0.35) & (g_low < 0.05) & (l_low < 45)        # painel na tela de 1080p (ocupa até ~80% da altura)
        menu = (dark >= 0.5) & (sat <= 17) & (chat >= 0.7)             # tela escurecida e sem cor
        white = ((lum > 200) & (satp < 40)).mean(axis=(1, 2)) >= 0.4   # câmera dentro da espuma/neve: tela branca
        c = np.zeros(len(im), np.int8)
        c[white] = 4; c[menu] = 2; c[menu & (lg > 0.04)] = 3; c[panel] = 1
        out[i0:i0 + 2000] = c
    _G[('c', src)] = out
    return out


# trechos que eu vi na revisão e que o detector não pega (tempo da fonte)
MANUAL_BAD = [('B', 2752.6, 2756.15, 'chat com /tp depois de renascer')]
# inventário que é CONTEÚDO (o Pedro fabricando o balde enquanto explica)
ALLOW_INV = [('B', 1331.0, 1342.0)]


def gui(src):
    """amostras PROIBIDAS: painel, menu escuro, tela branca, inventário (menos ALLOW_INV) e MANUAL_BAD"""
    if src in _G: return _G[src]
    c = classes(src)
    bad = (c == 1) | (c == 2) | (c == 4) | (c == 3)
    for s_, a, b in ALLOW_INV:
        if s_ == src: bad[int(a * FPS_SCAN):int(b * FPS_SCAN)] &= (c[int(a * FPS_SCAN):int(b * FPS_SCAN)] != 3)
    for s_, a, b, why in MANUAL_BAD:
        if s_ == src: bad[int(a * FPS_SCAN):int(np.ceil(b * FPS_SCAN))] = True
    o2 = bad.copy(); o2[1:] |= bad[:-1]; o2[:-1] |= bad[1:]   # folga de 1 amostra (a miniatura vem ~0,25 s adiantada)
    _G[src] = o2
    return o2


def bad_frac(src, a, b):
    g = gui(src)
    i0, i1 = int(np.floor(a * FPS_SCAN)), int(np.ceil(b * FPS_SCAN))
    if i0 >= len(g) or i1 <= 0: return 1.0
    s = g[max(0, i0):min(len(g), i1)]
    return float(s.mean()) if len(s) else 1.0


def alt_of(src, t):
    """(fonte alternativa, tempo) da outra câmera no mesmo instante, ou None"""
    if src == 'A':
        tb = t + OFF_AB
        return ('B', tb) if 0 <= tb < DUR['B'] - 0.5 else None
    if src == 'C':
        tb = t + OFF_CB
        return ('B', tb) if 0 <= tb < DUR['B'] - 0.5 else None
    if src == 'B':
        ta = t - OFF_AB
        if 0 <= ta < DUR['A'] - 0.5: return ('A', ta)
        tc = t - OFF_CB
        if 0 <= tc < DUR['C'] - 0.5: return ('C', tc)
    return None


def speakers(src, a, b, V):
    """(segundos de fala do Matteo, do Pedro) no trecho"""
    tr = {'A': ('A1', 'A3'), 'C': ('C1', 'C3')}.get(src)
    if not tr: return 0.0, 0.0
    def sec(name):
        return sum(max(0.0, min(e, b) - max(s, a)) for s, e in V[name] if e > a and s < b)
    return sec(tr[0]), sec(tr[1])


def bad_spans(src, a, b):
    """trechos [x, y] de [a, b] (tempo da fonte) com tela proibida"""
    g = gui(src)
    out = []
    i0, i1 = max(0, int(np.floor(a * FPS_SCAN))), min(len(g), int(np.ceil(b * FPS_SCAN)))
    for i in range(i0, i1):
        if g[i]:
            x, y = max(a, i / FPS_SCAN - 0.15), min(b, (i + 1) / FPS_SCAN + 0.15)
            if out and x <= out[-1][1] + 0.05: out[-1][1] = y
            else: out.append([x, y])
    return out


def clean(src, a, b):
    """jogo puro (sem nenhuma tela por cima) em [a, b] da fonte"""
    c = classes(src); g = gui(src)
    i0, i1 = int(np.floor(a * FPS_SCAN)) - 1, int(np.ceil(b * FPS_SCAN)) + 1
    if i0 < 0 or i1 > len(c): return False
    return bool((c[i0:i1] == 0).all() and not g[i0:i1].any())


def alt_clean(src, a, b):
    s = alt_of(src, a); e = alt_of(src, b)
    if not s or not e or s[0] != e[0]: return None
    return s if clean(s[0], s[1], s[1] + (b - a)) else None


def cutaway(src, x, y, reach=6.0):
    """plano de corte da MESMA câmera (fora de sincronia, fala continua por baixo): janela limpa de mesmo tamanho perto de [x, y]"""
    L = y - x
    for d in np.arange(0.3, reach, 0.25):
        for t in (y + d, x - d - L):
            if t >= 0 and clean(src, t, t + L): return (src, float(t))
    return None


def choose(units, V, locked, skip):
    """units: keeps do plano (tl_in/tl_out/src/src_in/src_out). locked(u) = zoom/preset ativo (fica a câmera da fonte);
    skip(u) = coberto (gancho/cinemática) -> ignora. Devolve capas [{'src','src_in','tl','dur','why'}] para a V2."""
    cov = []
    # 1) obrigatórias: tela proibida na fonte e a outra câmera limpa
    for u in units:
        if skip(u): continue
        for x, y in bad_spans(u['src'], u['src_in'], u['src_out']):
            who = 'Matteo' if u['src'] != 'B' else 'Pedro'
            ac = alt_clean(u['src'], x, y)
            if ac: cov.append({'src': ac[0], 'src_in': ac[1], 'tl': u['tl_in'] + (x - u['src_in']), 'dur': y - x, 'why': 'tela de menu/painel na câmera do ' + who + ' -> outra câmera', 'force': True}); continue
            cw = cutaway(u['src'], x, y)
            if cw: cov.append({'src': cw[0], 'src_in': cw[1], 'tl': u['tl_in'] + (x - u['src_in']), 'dur': y - x, 'why': 'tela de menu/painel na câmera do ' + who + ' -> plano de corte da mesma câmera', 'force': True, 'cutaway': True})
            else: print('SEM CAPA para tela proibida', u['src'], round(x, 2), round(y, 2))
    # 2) alternância por quem fala + ritmo
    state, run0 = 'own', 0.0
    for u in units:
        if skip(u) or u['src'] == 'B' or u.get('seg') in ('aer', 'endbg'):
            state, run0 = 'own', u['tl_out']; continue
        d = u['tl_in'] - run0
        m, p = speakers(u['src'], u['src_in'], u['src_out'], V)
        ps = p / (m + p) if m + p > 0.4 else None
        ac = alt_clean(u['src'], u['src_in'], u['src_out'])
        lk = locked(u)
        prev = state
        if state == 'own':
            if ac and not lk and ((ps is not None and ps >= 0.6 and d >= 2.0) or (d >= 15.0 and (ps is None or ps > 0.15))):
                state, run0 = 'alt', u['tl_in']
        else:
            if not ac or lk or (ps is not None and ps <= 0.3 and d >= 2.5) or d >= 9.0:
                state, run0 = 'own', u['tl_in']
        if state == 'alt':
            if prev != 'alt': runid = u['tl_in']
            why = 'Pedro fala' if (ps or 0) >= 0.6 else 'alternância de POV'
            if cov and not cov[-1].get('force') and abs(cov[-1]['tl'] + cov[-1]['dur'] - u['tl_in']) < 1e-3 and cov[-1]['src'] == ac[0] and abs(cov[-1]['src_in'] + cov[-1]['dur'] - ac[1]) < 0.02:
                cov[-1]['dur'] += u['tl_out'] - u['tl_in']
            else:
                cov.append({'src': ac[0], 'src_in': ac[1], 'tl': u['tl_in'], 'dur': u['tl_out'] - u['tl_in'], 'why': why, 'force': False, 'run': runid})
    # 3) limpeza: une capas da mesma câmera que se tocam ou se sobrepõem; capas de ritmo < 1,6 s saem
    cov.sort(key=lambda c: c['tl'])
    out = []
    for c in cov:
        if out and out[-1]['src'] == c['src'] and c['tl'] <= out[-1]['tl'] + out[-1]['dur'] + 0.6 \
                and abs((c['src_in'] - c['tl']) - (out[-1]['src_in'] - out[-1]['tl'])) < 0.02:
            end = max(out[-1]['tl'] + out[-1]['dur'], c['tl'] + c['dur'])
            out[-1]['dur'] = end - out[-1]['tl']; out[-1]['force'] = out[-1]['force'] or c['force']
            if c['force'] and 'painel' not in out[-1]['why']: out[-1]['why'] += ' + ' + c['why']
        else:
            out.append(dict(c))
    runs = {}
    for c in out:
        if 'run' in c: runs[c['run']] = runs.get(c['run'], 0) + c['dur']
    out = [c for c in out if c['force'] or runs.get(c.get('run'), 0) >= 1.6]
    return out
