"""plan_v14.py (17/10/2026) = plan_v13 + ajustes finais do Matheus: (1) SFX audíveis (peak_db por tier) + SFX de Minecraft; (2) nota "takes futuros editor" cortada e a frase seguinte
ilustrada com 5 takes do futuro (flashback + XP a cada corte). Base: plan_v13 — edição final de 5 min (fonte 0–366 s) do bruto 2026-10-08, padrão "teste corrigido" do Matheus.
Parte 1 (tl 0–37.2 s = fonte 0.5–56.1): réplica fiel das decisões dele (cortes, zooms, presets, SFX, músicas, níveis).
Parte 2 (fonte 56.8–366.5): as mesmas regras aplicadas pelo motor (hand-off ~0, mesma pessoa ~0.2 s, Potência constante, zoom que fica, SFX atuais,
música por clima com silêncio no record-scratch, item citado = zoom no item).
"""
import sys, json, os, re
sys.path.insert(0, r'C:\Users\mathe\.claude\skills\minecraft-video-editor\scripts')
import cutengine as ce

W = r'C:\Users\mathe\Skills\_research\mc-test\work'
LIB = r'C:\Users\mathe\.claude\skills\minecraft-video-editor\library'
EPI = r'D:\Users\PREDATOR\Documents\Epidemic 2K23 (Pasta de músicas)'
SFXD = LIB + r'\sfx'
FPS = 60000 / 1001.0
OUTD = r'C:\Users\mathe\Skills\_research\mc-test\v14'
FEATD = r'C:\Users\mathe\Skills\_research\mc-test\v13'
FUT = r'D:\Pobrs\futuros'
END_SRC = 366.5

sp = ce.SpeechMap(W + r'\s1.wav', W + r'\s2.wav', 0, 420)
words = []
for k in ('t1', 't2'):
    for w in json.load(open(W + '\\%s.json' % k, encoding='utf8'))['words']:
        words.append((w['s'], w['e'], w['w'].strip(), k))
words.sort()

# ---------------------------------------------------------------- cortes
U = json.load(open(OUTD + r'\..\v12\cmp\keeps_user.json'))['keeps'][:14]        # decisões do Matheus (fonte 0.517–56.056)
eng = ce.tighten2(sp, start=56.823, end=END_SRC, words=[(w[0], w[1]) for w in words])
# nota de edição do roteiro: "takes futuros, editor" (sussurrada, fonte 177.25–178.15) NÃO vai pro vídeo -> corta; a frase seguinte ("Porque a gente ainda vai...") é ilustrada com takes futuros
NOTE_A, NOTE_B = 177.05, 178.68
eng2, mark_next = [], False
for k in eng:
    k = dict(k)
    if mark_next: k['handoff'] = True; mark_next = False
    if k['src_in'] < NOTE_A < k['src_out']:
        tail = dict(k, src_in=NOTE_B, handoff=True)
        k['src_out'] = NOTE_A
        eng2.append(k)
        if tail['src_out'] > NOTE_B + 0.3: eng2.append(tail)
        else: mark_next = True
    else:
        eng2.append(k)
eng = eng2
src = [(k['src_in'], k['src_out'], False) for k in U] + [(k['src_in'], k['src_out'], k['handoff']) for k in eng]
# xf nos 4 cortes que ele suavizou + hand-offs do motor + a emenda dele/motor
XF_USER = {2, 3, 4, 6}
keeps, tl_f = [], 0
for i, (a, b, hand) in enumerate(src):
    fa, fb = round(a * FPS), round(b * FPS)
    if fb - fa < 2: continue
    xf = (i in XF_USER) if i < 14 else (bool(hand) or i == 14)
    keeps.append({'src_in': fa / FPS, 'src_out': fb / FPS, 'tl_in': tl_f / FPS, 'tl_out': (tl_f + fb - fa) / FPS, 'xf_prev': xf and len(keeps) > 0})
    tl_f += fb - fa

def T(s):
    return ce.src2tl_snap(keeps, s)

def split_at(tl_times):
    global keeps
    for t in sorted(set(round(x, 4) for x in tl_times)):
        for i, k in enumerate(keeps):
            if k['tl_in'] + 0.12 < t < k['tl_out'] - 0.12:
                f = round(t * FPS) / FPS
                a = dict(k, tl_out=f, src_out=k['src_in'] + (f - k['tl_in']))
                b = dict(k, tl_in=f, src_in=k['src_in'] + (f - k['tl_in']), xf_prev=False)
                keeps[i:i + 1] = [a, b]
                break

def snap(t, tol=0.12):
    """se t cai perto de uma fronteira de keep, usa a fronteira (evita clipes minúsculos)"""
    for k in keeps:
        for b in (k['tl_in'], k['tl_out']):
            if abs(b - t) <= tol: return b
    return t

def wt(near, pat, tol=1.0):
    best = None
    for s, e, w, k in words:
        if abs(s - near) <= tol and re.sub(r'\W', '', w.lower()).startswith(re.sub(r'\W', '', pat.lower())) and (not pat.endswith('?') or w.endswith('?')):
            if best is None or abs(s - near) < abs(best - near): best = s
    if best is None:
        print('  [aviso] palavra não achada', pat, near); return near
    return best

# ---------------------------------------------------------------- efeitos de vídeo
fx, presets, stretch, splits = [], [], [], []

def ev(t0, keyrows, fxy=(960, 540), why=''):
    fx.append({'t': t0, 'fx': fxy[0], 'fy': fxy[1], 'keys': keyrows, 'why': why})

def rate(s0):                      # palavras/s nos próximos 1.5 s (ritmo da fala) -> duração da animação do zoom
    n = sum(1 for s, e, w, k in words if s0 <= s < s0 + 1.5)
    return n / 1.5

def Z(s0, S, s1, fxy=(960, 540), mode='anim', dur=None, why=''):
    """zoom que FICA até a fronteira s1 (corte seco de volta). anim = ease-out (rápido que decai); seco = punch estático."""
    t0, t1 = snap(T(s0)), snap(T(s1))
    splits.extend([t0, t1])
    if mode == 'seco':
        ev(t0, [[0, S], [t1 - t0, S]], fxy, why)
        return
    r = rate(s0)
    d = dur or (0.2 if r > 4.2 else 0.32 if r > 2.8 else 0.55)
    rows = [[d * i / 6, 100 + (S - 100) * (1 - (1 - i / 6) ** 3)] for i in range(7)] + [[max(t1 - t0, d + 0.01), S]]
    ev(t0, rows, fxy, why + ' (anim %.2fs, %.1f pal/s)' % (d, r))

# ---- parte 1: tempos de timeline do Matheus (keys dele convertidas p/ foco)
ev(0.0, [[0, 182], [0.434, 100]], (974, 549), 'abertura: zoom-out 182%->100% (+White Flash B)')
ev(1.802, [[0, 103.3], [1.667, 106], [1.747, 100], [1.867, 138], [2.117, 138], [2.617, 100]], (960, 540), 'push lento + pop "toda a água do mundo" (vine boom)')
ev(5.822, [[0, 100], [0.751, 650], [1.552, 650]], (939.8, 684.3), 'item citado: zoom 650% no canudinho do mundo (+spotlight)')
ev(9.826, [[0, 100], [1.218, 131.7]], (960, 540), 'push-in lento antes do deboche')
ev(14.031, [[0, 239], [0.917, 239]], (911.5, 605), 'corte seco 239% no personagem ("vai funcionar")')
fx.append({'t': 16.250, 'fx': 960, 'fy': 540, 'why': 'zoom 254% seguindo o Chique', 'keys': [
    [0, 254, 0, 0, 0, 1103.2, 540], [0.367, 254, 0, 0, 0, 770.0, 540], [0.85, 254, 0, 0, 0, 564.0, 467.3], [1.284, 254, 0, 0, 0, 52.6, 403.0], [1.668, 254, 0, 0, 0, 635.0, 403.0], [1.718, 254, 0, 0, 0, 635.0, 403.0]]})
ev(24.291, [[0, 100.8], [0.584, 102.8]], (960, 540), 'tensão: dolly mínimo na entrada da música')
ev(24.875, [[0, 138], [2.586, 138]], (960, 540), 'tensão: 138% fixo 2.6 s')
ev(27.461, [[0, 100], [0.088, 100], [0.208, 118], [0.558, 118], [0.958, 100]], (960, 540), 'pulso "Eu não consigo"')
ev(28.462, [[0, 119.8], [0.617, 119.8]], (1244, 540), 'obstáculo: 119.8% (+Red Flash B + Impact Shake High)')
fx.append({'t': 29.079, 'fx': 960, 'fy': 540, 'why': 'push lento -> pulso -> zoom 250% na mensagem do jogo', 'keys': [
    [0.017, 101.9, 0, 0, 0, 974, 540], [2.486, 108, 0, 0, 0, 960, 540], [2.586, 100, 0, 0, 0, 960, 540], [2.669, 135.9, 0, 0, 0, 961.6, 944], [2.936, 250, 0, 0, 0, 962, 944],
    [4.236, 250, 0, 0, 0, 962, 944], [4.586, 100, 0, 0, 0, 960, 540]]})
ev(36.001, [[0, 103], [1.236, 107.3]], (960, 540), '"por que a gente não consegue beber nada?": push lento')
presets += [{'name': 'White Flash B', 'tl': 0.0}, {'name': "Lava's VHS", 'tl': 11.044}, {'name': 'Red Flash B', 'tl': 28.462}, {'name': 'Impact Shake High', 'tl': 28.462}]
stretch.append({'tl': 11.044, 'sx': 391, 'sy': 258, 'fx': 915.8, 'fy': 540})
splits += [5.822, 9.826, 14.031, 14.948, 29.079]

# ---- parte 2: âncoras por palavra (fonte)
a = wt(64.54, "d'água", 0.6);  Z(a - 0.04, 125, 67.4, why='"Poça d\'água? É verdade": reação (ideia nova)')
Z(71.7, 118, 74.3, mode='seco', why='"Essa poça aqui é minha": posse escrachada (seco)')
Z(79.95, 230, 81.7, (960, 0), why='contador: mais de 20 litros')
Z(93.10, 230, 94.9, (960, 0), why='contador: mais de 100 litros')
# pergunta debochada "Você tá bebendo água?": VHS esticado + bonk + scratch + música cala (receita do Matheus)
t_v0, t_v1 = snap(T(104.30)), snap(T(105.26)); splits.extend([t_v0, t_v1])
presets.append({'name': "Lava's VHS", 'tl': t_v0}); stretch.append({'tl': t_v0, 'sx': 391, 'sy': 258, 'fx': 915.8, 'fy': 540})
t_g0, t_g1 = snap(T(111.55)), snap(T(113.40)); splits.extend([t_g0, t_g1]); stretch.append({'tl': t_g0, 'sx': 300, 'sy': 210, 'fx': 960, 'fy': 560})
t_b0, t_b1 = snap(T(116.95)), snap(T(119.80)); splits.extend([t_b0, t_b1]); stretch.append({'tl': t_b0, 'sx': 330, 'sy': 225, 'fx': 960, 'fy': 600})
Z(129.4, 125, 131.3, mode='seco', why='"a gente tá desse jeito?": pergunta retórica (seco + huh)')
Z(144.58, 240, 147.0, (960, 0), why='contador: 280 litros')
a_ap = wt(150.9, 'apenas', 1.5)
Z(a_ap - 0.15, 250, a_ap + 2.4, (960, 0), why='"apenas 0,1%": contador (+Red Flash + shake)')
Z(165.30, 250, 168.4, (960, 0), why='"apenas 0,1% de toda a água do mundo": contador')
Z(245.50, 210, 247.6, (960, 330), why='item: boia/mochila na loja')
Z(250.62, 230, 251.95, (960, 420), why='item: "canudo gigante"')
Z(258.55, 230, 259.45, (920, 330), why='item: "buraco negro na boca"')
Z(269.90, 230, 272.85, (1040, 420), why='item: nível 1 "copo de água"')
Z(295.20, 260, 297.30, (1700, 850), why='item: copo na mão')
Z(300.20, 250, 302.5, (960, 0), why='contador subindo (tô bebendo muito mais rápido)')
presets += [{'name': 'Red Flash B', 'tl': snap(T(a_ap - 0.15))}, {'name': 'Impact Shake Mid', 'tl': snap(T(a_ap - 0.15))},
            {'name': 'Impact Shake Low', 'tl': snap(T(337.60))}, {'name': 'Red Flash B', 'tl': snap(T(354.85))}, {'name': 'Impact Shake High', 'tl': snap(T(354.85))}]
splits += [snap(T(337.60)), snap(T(354.85))]
split_at(splits)
# presets/stretch precisam começar em início de clipe: recalcula tl p/ a fronteira exata
for x in presets + stretch: x['tl'] = snap(x['tl'], 0.2)

# ---------------------------------------------------------------- SFX
# v14b: níveis por RMS ATIVO final no mix (rms_db; voz ~ -20 dBFS) com teto de pico (peak_cap). Tiers: impacto -18 | fail -19 | gag -20 | wow -22 | stinger -22/-27 | pop -21 | levelup/toast -21 | orb -22 | gole -24 | scratch -20 | suspense -25
# (peak_db sozinho falhou: SFX esparsos/tonais como o orb do XP têm pico alto e RMS baixo -> inaudíveis; MC tem RMS ~-22..-28 vs 'deg-deg-sussy' -3.5)
sfx = []
def S(tl, f, dur=None, pk=-20.0, off=0.0, why=''):      # pk = RMS ATIVO final (dBFS); teto de pico -2.5 (orb -2.0)
    d = {'file': SFXD + chr(92) + f, 'tl': round(tl, 4), 'why': why, 'rms_db': pk, 'peak_cap': -2.0 if 'xp-orb' in f else -2.5}
    if dur: d['dur'] = dur
    if off: d['src_off'] = off
    sfx.append(d)
# parte 1 (réplica da escolha dele; níveis relativos preservados, mas audíveis)
S(0.0, 'anime-shine-sound-2.mp3', 1.8, pk=-24, off=0.167, why='abertura (+White Flash)')
S(3.537, 'vine-boom.mp3', 1.2, pk=-15, why='"toda a água do mundo"')
S(5.689, 'anime-wow-sound-effect (1).mp3', 3.6, pk=-19, why='item citado: zoom no canudinho')
S(11.044, 'bamboo-hit-anime-bonk-sound.mp3', 0.6, pk=-15, why='deboche: entra o VHS')
S(11.195, 'record-scratch-2.mp3', 0.75, pk=-17, why='record scratch (música cala)')
S(12.279, 'sudden-suspense-sound-effect.mp3', 1.35, pk=-22, why='"Exatamente, você é maluco?"')
S(19.586, 'bonk_BEtiM8g.mp3', 1.19, pk=-15, why='"Isso, bebe água"')
S(25.859, 'huh-cat.mp3', 1.15, pk=-17, off=0.517, why='"Por que que eu tô tomando?": reação huh')
S(27.327, 'windows-xp-error-sound.mp3', 1.13, pk=-15, why='obstáculo: erro 1')
S(28.395, 'wrong_5.mp3', 1.77, pk=-15, why='obstáculo: errado')
S(28.462, 'mc-damage-hit1.mp3', 0.49, pk=-16, why='obstáculo: "oof" do Minecraft (dano)')
S(29.012, 'nintendo-switch-error.mp3', 0.28, pk=-15, why='obstáculo: erro 3')
S(36.169, 'spongebob-fail.mp3', 2.84, pk=-16, why='"beber nada?": fail')
# parte 2 (repertório atual + Minecraft)
S(T(a - 0.02), 'anime-wow-sound-effect.mp3', 2.0, pk=-19, why='"é verdade": ideia nova (poças)')
S(T(71.9), 'bamboo-hit-anime-bonk-sound.mp3', 0.6, pk=-15, why='"Calma aí, não bebe ainda": freio')
S(T(77.95), 'mc-random-drink.mp3', 0.49, pk=-21, why='MC: gole ("já tô bebendo bastante água")')
S(t_v0, 'bamboo-hit-anime-bonk-sound.mp3', 0.6, pk=-15, why='"Você tá bebendo água?": entra o VHS (receita do Matheus)')
S(t_v0 + 0.15, 'record-scratch-2.mp3', 0.75, pk=-17, why='record scratch: música cala')
S(T(88.45), 'mc-random-drink.mp3', 0.49, pk=-21, why='MC: gole ("bebe água")')
S(T(88.95), 'mc-random-drink.mp3', 0.49, pk=-21, why='MC: gole 2')
S(T(wt(112.34, 'pera', .5)), 'mc-mob-villager-no2.mp3', 0.47, pk=-17, why='"Olha o tamanho da pan... Pera aí": Villager "hmm" (MC)')
S(T(117.82), 'cartoon-boing.mp3', 0.78, pk=-17, why='"olha o tamanho da minha barriga": boing')
S(T(117.82) + 0.45, 'mc-random-burp.mp3', 0.32, pk=-17, why='MC: arroto (barriga cheia)')
S(T(120.40), 'clown-horn-short.mp3', 0.6, pk=-17, why='"vocês são tão barrigudos": buzina')
S(T(129.82), 'ceeday-huh-sound-effect.mp3', 1.1, pk=-17, why='"a gente tá desse jeito?": huh')
S(T(a_ap - 0.15), 'mc-random-anvil_land.mp3', 0.77, pk=-15, why='MC: bigorna ("apenas 0,1%" = peso do problema, junto do shake)')
S(T(a_ap), 'wrong_5.mp3', 1.2, pk=-15, why='"apenas 0,1%": o problema')
S(T(167.80), 'spongebob-fail.mp3', 2.6, pk=-16, why='"0,1% de toda a água do mundo": fail')
S(T(171.24), 'bruh-sound-effect_WstdzdM.mp3', 0.82, pk=-17, why='B: "essa furada"')
S(T(189.40), 'mc-mob-villager-yes1.mp3', 0.75, pk=-17, why='"Na vila": Villager "hurr" (MC)')
S(T(wt(195.0, 'gente?', 3)), 'mc-mob-villager-no1.mp3', 0.48, pk=-17, why='"Será que os villagers vão ajudar a gente?": o Villager responde "hmm" (MC)')
S(T(201.5), 'bamboo-hit-anime-bonk-sound.mp3', 0.6, pk=-15, why='"70% de água": bonk')
S(T(wt(217.3, 'plantação', 1.5)), 'bruh-sound-effect_WstdzdM.mp3', 0.82, pk=-17, why='"beber água da plantação?": bruh')
S(T(231.45), 'mc-mob-endermen-portal.mp3', 0.91, pk=-17, why='MC: "Teleporte?" (enderman teleporte)')
S(T(236.28), 'mc-random-levelup.mp3', 1.75, pk=-18, why='MC: level up ("olha só onde a gente veio parar": a loja)')
S(T(245.58), 'mc-random-chestopen.mp3', 0.5, pk=-18, why='MC: baú abrindo (1º item da loja)')
S(T(246.82), 'pop_7e9Is8L.mp3', 0.4, pk=-18, why='item: mochila')
S(T(250.74), 'pop_7e9Is8L.mp3', 0.4, pk=-18, why='item: canudo gigante')
S(T(253.52), 'clown-horn-short.mp3', 0.6, pk=-17, why='"nem cabe na minha boca"')
S(T(258.62), 'pop_7e9Is8L.mp3', 0.4, pk=-18, why='item: buraco negro')
S(T(260.60), 'mc-mob-villager-no2.mp3', 0.47, pk=-17, why='"Como assim?": Villager "hmm" (MC)')
S(T(262.70), 'deg-deg-sussy.mp3', 1.5, pk=-19, why='"esse aqui vai dar ruim": sus')
S(T(263.60), 'mc-mob-creeper-say1.mp3', 0.46, pk=-17, why='MC: creeper hiss ("vai dar ruim")')
S(T(271.30), 'pop_7e9Is8L.mp3', 0.4, pk=-18, why='item: copo de água')
S(T(273.00), 'mc-ui-toast-challenge_complete.mp3', 2.6, pk=-18, why='MC: conquista desbloqueada ("já comprei o meu")')
S(T(295.28), 'pop_7e9Is8L.mp3', 0.4, pk=-18, why='item: copo na mão')
S(T(297.80), 'mc-random-drink.mp3', 0.49, pk=-21, why='MC: gole ("vai bebendo")')
S(T(298.40), 'mc-random-drink.mp3', 0.49, pk=-21, why='MC: gole 2')
S(T(312.18), 'faaah.mp3', 1.6, pk=-16, why='"grande porcaria": fail')
S(T(321.20), 'mc-random-drink.mp3', 0.49, pk=-21, why='MC: gole ("bebe água")')
S(T(321.75), 'mc-random-drink.mp3', 0.49, pk=-21, why='MC: gole 2')
S(T(328.66), 'cartoon-boing.mp3', 0.78, pk=-17, why='"virando uma bola imensa"')
S(T(328.66) + 0.45, 'mc-random-burp.mp3', 0.32, pk=-17, why='MC: arroto (bola imensa)')
S(T(337.62), 'metal-gear-alert-sound-effect_XKoHReZ.mp3', 1.5, pk=-19, why='"a água tá baixando": alerta')
S(T(352.90), 'bruh-sound-effect_WstdzdM.mp3', 0.82, pk=-17, why='"Bruno Coutinho?": bruh')
S(T(354.88), 'gta-v-wasted-death-sound.mp3', 2.6, pk=-16, why='"zeradinho": a poça foi zerada')
S(T(357.00), 'emotional-damage-meme.mp3', 2.2, pk=-16, why='"qual que é o seu problema, cara?"')

# ---------------------------------------------------------------- "takes futuros" (nota do roteiro: "takes futuros, editor" -> ilustrar a frase seguinte com cenas impactantes do futuro do vídeo)
# 5 takes de VÍDEO-SÓ (cortados do bruto, metade do jogo) em V2 com filtro flashback; cada corte = XP do Minecraft (orb com tom subindo); flash branco entra/sai.
FU_B = [178.80, 179.62, 180.55, 181.62, 182.35, 183.60]           # fronteiras na fonte, nas palavras: Porque a gente ainda vai | desbloquear | muitas maneiras iradas | de beber água | inteira do mundo
FU_F = [('futuro_01_t1626.mp4', 'funil sugando o lago (+ barriga cheia)'), ('futuro_02_t1939.mp4', 'canudo gigante listrado entrando'), ('futuro_03_t2136.mp4', 'redemoinho artificial sugando o mar'),
        ('futuro_04_t2138.mp4', 'dois personagens-bola gigantes sobre o globo'), ('futuro_05_t2142.mp4', 'o planeta-bola no céu (clímax)')]
futuros = []
for i, (fn, why) in enumerate(FU_F):
    t0, t1 = T(FU_B[i]), T(FU_B[i + 1])
    f = {'file': FUT + chr(92) + fn, 'tl': round(t0, 4), 'dur': round(t1 - t0, 4), 'off': 1.0, 'zoom': [100, 108 if i == 4 else 106], 'why': why}
    if i == 0: f['preset_in'] = 'White Flash B'
    if i == len(FU_F) - 1: f['preset_out'] = 'White Flash A'
    futuros.append(f)
    S(t0, 'mc-xp-orb-p%d.mp3' % i, 0.7, pk=-17, why='MC: XP no corte do take futuro %d/5' % (i + 1))

# ---------------------------------------------------------------- música
feat = {}
for f in ('mf_a.json', 'mf_b.json', 'mf_c.json'):
    feat.update(json.load(open(FEATD + '\\' + f, encoding='utf8')))
import subprocess
def lufs_of(rel, default=None):
    if rel in feat and feat[rel].get('lufs') is not None: return feat[rel]['lufs']
    path = EPI + chr(92) + rel.replace('/', chr(92))
    r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', path, '-af', 'ebur128', '-f', 'null', '-'], capture_output=True, encoding='utf8', errors='replace')
    m = re.findall(r'I:\s+(-?[\d.]+) LUFS', r.stderr or '')
    v = float(m[-1]) if m else -9.0
    print('  [lufs medido]', rel, v); feat[rel] = {'lufs': v}
    return v
def start_of(rel, default=6.0):
    e = feat.get(rel, {}).get('energia_5s_db')
    if not e: return default
    med = sorted(e)[len(e) // 2]
    for i, v in enumerate(e):
        if i >= 1 and v >= med - 2.5: return float(i * 5)
    return default
def mus(rel, tl_in, tl_out=None, E=-27.0, src_in=None, entry=True, disp=None, fin=0.1, fout=0.2, why=''):
    path = EPI + '\\' + rel.replace('/', '\\')
    assert os.path.exists(path), path
    lu = lufs_of(rel)
    d = {'file': path, 'tl_in': round(tl_in, 4), 'src_in': src_in if src_in is not None else start_of(rel), 'gain_db': round((disp if disp is not None else E - lu) - 3.0, 1), 'fade_in': fin, 'fade_out': fout, 'why': why}
    if tl_out: d['tl_out'] = round(tl_out, 4)
    if entry is True: d['entry'] = [3.5, 3.5]
    elif entry: d['entry'] = entry
    return d
M2K = '2K25/ES_'
music = [
    mus('2K25/ES_Brighter than the Sky - Akibakid.mp3', 0.0, 1.802, src_in=0.601, disp=-14.8, entry=False, fin=0.02, fout=0.1, why='sting da abertura (dele)'),
    mus('MUY ANIMADAS/ES_Lifecrash - Rascal Genius.mp3', 1.802, 11.044, src_in=0.0, disp=-16.2, entry=False, fin=0.1, fout=0.08, why='intro enérgica a partir da 1ª fala do roteiro (dele); cala no record scratch'),
    mus('2K25/ES_The Sleepy Sneaky Sway - Luella Gren.mp3', 12.579, 24.291, src_in=10.043, disp=-15.0, entry=False, fin=0.08, fout=0.1, why='plano suspeito (dele, igual v12)'),
    mus('2K25/ES_That Thing Behind Us - Arylide Fields.mp3', 24.291, 36.37, src_in=5.489, disp=-13.9, entry=[3.6, 4.17], fin=0.05, fout=0.3, why='tensão da 1ª tentativa: entra mais alto (dele)'),
    mus('TROLL/ES_Festive Riot - Harper Rey (1).mp3', T(64.14), T(104.30), why='caça às poças: cômica/saltitante'),
    mus('MISTERIO/ES_Secretly Spying on You - Harper Rey.mp3', T(105.60), T(137.0), why='barriga/desconfiança: sorrateira cômica'),
    mus('NUEVAS 2K24/ES_When the Cats Away - The Fly Guy Five.mp3', T(137.0), T(165.2), E=-28.0, entry=[3.0, 2.5], why='contagem dos litros: cama rítmica'),
    mus('VLOGS/ES_Your Gain - Swif7.mp3', T(174.55), T(213.5), why='esperança + vila: otimista'),
    mus('2K25/ES_Under the Radar - Martin Landstrom.mp3', T(213.70), T(235.6), why='explorando a vila: curiosa/sorrateira'),
    mus('NUEVAS 2K24/ES_Pretend You_re Nice - Stationary Sign.mp3', T(235.80), T(275.4), why='a loja: descoberta alegre'),
    mus('VLOGS/ES_You Seen My Coat - Jon Bjork.mp3', T(275.80), T(330.0), why='testando o copo: groove animado'),
    mus('NUEVAS 2K24/ES_Blame It on Me - Radio Night.mp3', T(330.40), None, E=-25.5, why='Brucutu: conflito cômico/tenso'),
]
DUR = keeps[-1]['tl_out']
marks = [{'tl': round(m['tl_in'], 3), 'txt': 'MÚSICA: ' + m['why']} for m in music]
marks += [{'tl': round(s['tl'], 3), 'txt': 'SFX: ' + s['why']} for s in sfx if s['why'] and s['tl'] > 37]
marks += [{'tl': round(f['t'], 3), 'txt': 'ZOOM: ' + f['why']} for f in fx if f['t'] > 37]
marks.append({'tl': round(futuros[0]['tl'], 3), 'txt': 'TAKES FUTUROS: nota "takes futuros editor" (fonte 177.2-178.2) cortada; frase ilustrada com 5 cenas do futuro (flashback + XP a cada corte)'})
marks += [{'tl': f['tl'], 'txt': 'FUTURO: ' + f['why']} for f in futuros]

plan = {'bruto_prefix': '2026-10-08', 'keeps': keeps, 'music': music, 'sfx': sfx, 'fx': fx, 'presets': presets, 'stretch': stretch,
        'stickers': [{'file': LIB + r'\png\spot_dark.png', 'tl': 5.489, 'dur': 1.852, 'pos': [0.66, 0.50], 'scale': 100, 'rot': 0, 'v': 3, 'fade': 0.18, 'opacity': 100, 'why': 'spotlight no item citado (dele)'}],
        'futuros': futuros, 'marks': marks, 'master_db': -4.0, 'boost_voice_db': 9.0, 'boost_music_db': 3.0, 'limiter': 0.885, 'dur_tl': round(DUR + 0.05, 3), 'xf_frames': 12}
out = OUTD + r'\plan3.json'
json.dump(plan, open(out, 'w', encoding='utf8'), ensure_ascii=False, indent=1)
print('keeps', len(keeps), 'dur_tl %.1f' % DUR, '| xf', sum(1 for k in keeps if k['xf_prev']), '| sfx', len(sfx), '| fx', len(fx), '| presets', len(presets), '| stretch', len(stretch), '| música', len(music))
for m in music: print('  música tl %6.1f-%s  %s (src_in %.0f gain %.1f)' % (m['tl_in'], ('%6.1f' % m['tl_out']) if 'tl_out' in m else '  fim ', os.path.basename(m['file'])[:44], m['src_in'], m['gain_db']))
