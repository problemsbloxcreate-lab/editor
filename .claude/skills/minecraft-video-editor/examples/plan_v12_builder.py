"""plan_v12.py — gera plan2.json da reedição dos primeiros ~3 min (fonte 0–213 s) do bruto 2026-10-08.
Feedback do Matheus (15/10/2026, nota 4/10) aplicado: silêncio zero, corte com folga antes da palavra, música por cena (trocas em 15.2 e na 1ª tentativa),
SFX no gatilho certo (14.05), item citado mostrado (canudinho), pergunta retórica = distorção/SFX de meme/P&B/cacho de "?", problema = zoom no HUD + SFX de erro.
"""
import sys, json, os, math
sys.path.insert(0, r'C:\Users\mathe\.claude\skills\minecraft-video-editor\scripts')
import cutengine as ce

W = r'C:\Users\mathe\Skills\_research\mc-test\work'
LIB = r'C:\Users\mathe\.claude\skills\minecraft-video-editor\library'
FPS = 60000 / 1001.0
MUSIC = LIB + r'\music'
SFX = LIB + r'\sfx'
PNG = LIB + r'\png'
feat = json.load(open(LIB + r'\music_features.json', encoding='utf8'))

sp = ce.SpeechMap(W + r'\s1.wav', W + r'\s2.wav', 0, 216)
END_SRC = min(sp.offset_before(213.0) + 0.25, 214.0)
raw = ce.tighten(sp, remove=[(27.6, 40.0)], start=0.33, end=END_SRC)

# --- quantiza no quadro (59.94) -------------------------------------------------
keeps, tl_f = [], 0
for k in raw:
    a = round(k['src_in'] * FPS); b = round(k['src_out'] * FPS)
    if b - a < 2: continue
    keeps.append({'src_in': a / FPS, 'src_out': b / FPS, 'tl_in': tl_f / FPS, 'tl_out': (tl_f + b - a) / FPS})
    tl_f += b - a
DUR = keeps[-1]['tl_out']
rep = ce.validate(sp, keeps)
print('keeps', len(keeps), 'dur_tl %.2f' % DUR, 'junções ruins', sum(r['ruim'] for r in rep))

def T(src):  # tempo de fonte -> timeline (snap p/ próxima keep se removido)
    return ce.src2tl_snap(keeps, src)

def lin_gain(file_rel):  # ganho (dB) p/ cama de música em -31 LUFS
    return round(-31.0 - feat[file_rel]['lufs'], 1)

def mus(cat, name, src_scene, off=0.0, why=''):
    rel = cat + '/' + name
    return {'file': MUSIC + '\\' + cat + '\\' + name, 'tl_in': T(src_scene), 'src_in': off, 'gain_db': lin_gain(rel), 'why': why}

music = [
    mus('2K25', 'ES_Brighter than the Sky - Akibakid.mp3', 0.33, 0, 'A intro/gancho: energética e clara'),
    mus('2K25', 'ES_The Sleepy Sneaky Sway - Luella Gren.mp3', 15.12, 10, 'B 15.1: troca do clima da intro -> deboche/plano suspeito (pedido do Matheus)'),
    mus('2K25', 'ES_That Thing Behind Us - Arylide Fields.mp3', 40.66, 5, 'C 1ª tentativa (retake): tensão/intriga (pedido do Matheus)'),
    mus('2K25', 'ES_Farmer_s Chores - Flickering.mp3', 58.6, 10, 'D "Poça d\'água? é verdade": caça às poças, competição animada'),
    mus('DUDOSAS', 'ES_Uninvited Guests - Etienne Roussel.mp3', 101.4, 0, 'E "Você tá bebendo água?": piada da barriga, desconfiança cômica'),
    mus('AMOR', 'ES_My First My Last (Tribute Version) (Instrumental Version) - Love Beans.mp3', 149.0, 10, 'F "apenas 0,1%": murchou, tristeza irônica'),
    mus('AVENTURAS', 'ES_The Proving Grounds - Dragon Tamer.mp3', 168.6, 5, 'G esperança: "vamos desbloquear maneiras iradas"'),
    mus('2K25', 'ES_The Detective - Flickering.mp3', 190.8, 5, 'H vila: curiosidade/investigação, piada dos 70% de água'),
]

# --- SFX (tempo de fonte ancorado na PALAVRA) -------------------------------------
S = [
    (0.36, 'anime-shine-sound-2.mp3', 0, 'abertura (1ª palavra)'),
    (4.70, 'vine-boom.mp3', 0, '"toda a água do mundo" (impacto)'),
    (6.72, 'zeldaitem.mp3', 0, '"esse canudinho": item citado aparece (item get)'),
    (14.05, 'record-scratch-2.mp3', 0, 'PEDIDO: deboche do Patão em "canudinho aqui?" (era 14.95, tarde)'),
    (15.30, 'sudden-suspense-sound-effect.mp3', -4, '"Você é maluco?": stinger + troca de música'),
    (22.80, 'bonk_BEtiM8g.mp3', -3, '"Essa água do mar aqui já é minha"'),
    (40.80, 'sudden-suspense-sound-effect.mp3', -2, 'entra a música de tensão (1ª tentativa)'),
    (42.30, 'huh-cat.mp3', -3, 'PERGUNTA RETÓRICA "Por que que eu tô tomando?": meme SFX (+distorção +cacho de ?)'),
    (44.85, 'windows-xp-error-sound.mp3', 0, '"Eu não consigo": erro (obstáculo 1)'),
    (51.70, 'erro.mp3', 0, '"Eu não consigo beber": erro (obstáculo 2, zoom no contador 0 L)'),
    (50.35, 'whoosh-sfx.mp3', 0, 'zoom na mensagem "mar liberado nível 6"'),
    (55.85, 'wah-wah-fail.mp3', 0, '"Por que a gente não consegue beber nada?" fim: fail (P&B)'),
    (58.96, 'ding-sound-effect_2.mp3', 0, '"Poça d\'água? É verdade": ideia nova'),
    (72.25, 'bonk_BEtiM8g.mp3', 0, '"Essa poça aqui é minha": posse cômica'),
    (86.00, 'rimshot.mp3', 0, '"Quem esvaziar primeiro ganha": rimshot'),
    (80.10, 'ding-sound-effect_1.mp3', -4, 'contador: "mais de 20 litros"'),
    (93.20, 'ding-sound-effect_1.mp3', -4, 'contador: "mais de 100 litros"'),
    (104.00, 'como-assim.mp3', -2, 'PERGUNTA RETÓRICA "Você tá bebendo água?": meme SFX + distorção'),
    (112.70, 'record-scratch-2.mp3', -3, '"Pera aí" (percebe a própria barriga)'),
    (117.82, 'taco-bell-bong-sfx.mp3', -2, '"olha o tamanho da minha barriga": bong + zoom abaulado'),
    (130.20, 'fails-ohhhh.mp3', -2, 'PERGUNTA RETÓRICA "a gente tá desse jeito?": aww'),
    (132.50, 'rimshot.mp3', -3, '"Imagina quando a gente beber o mar inteiro": ironia'),
    (150.95, 'dun-dun-dun-sound-effect-brass_8nFBccR.mp3', -4, '"apenas 0,1%": a revelação do problema'),
    (168.40, 'sadtrombone.swf.mp3', 0, '"0,1% de toda a água do mundo": trombone triste'),
    (178.60, 'minecraft-levelup.mp3', -4, '"vamos DESBLOQUEAR": level up'),
    (190.90, 'whoosh-sfx.mp3', 0, '"Na vila": novo objetivo'),
    (197.40, 'hm.mp3', -2, 'PERGUNTA "Será que os villagers vão ajudar a gente?": hmm'),
    (200.00, 'roblox-death-sound_1.mp3', 0, '"beber os villagers também?": oof'),
    (210.30, 'bonk_BEtiM8g.mp3', -2, '"mais de 70%, viu, Chique?": fecha a piada'),
]
DURS = {'huh-cat.mp3': 1.7, 'minecraft-levelup.mp3': 2.4, 'ding-sound-effect_1.mp3': 1.6, 'ding-sound-effect_2.mp3': 1.8, 'sadtrombone.swf.mp3': 2.5}
sfx = [dict({'file': SFX + '\\' + f,'tl': round(T(t), 4), 'rel_db': rel, 'why': why}, **({'dur': DURS[f]} if f in DURS else {})) for t, f, rel, why in S]
# duck da música nos SFX de piada/impacto
DUCK = [14.05, 42.3, 72.25, 86.0, 104.0, 117.82, 130.2, 132.5, 150.95, 168.4, 200.0]
ducks = [{'tl': round(T(t), 4), 'dur': 0.9, 'depth_db': 7.0} for t in DUCK]

# --- efeitos de vídeo (curvas em tempo de timeline) -------------------------------
def pop(t_src, s, curv, ramp=0.15, hold=0.35, ret=0.45, fx=960, fy=540, tint=0, why=''):
    t = T(t_src)
    return {'t': t, 'fx': fx, 'fy': fy, 'why': why,
            'keys': [[0, 100, 0, 0, 0], [ramp, s, curv, tint, 0], [ramp + hold, s, curv, tint, 0], [ramp + hold + ret, 100, 0, 0, 0]]}

def dolly(t0_src, t1_src, s1, why='', fx=960, fy=540):
    a, b = T(t0_src), T(t1_src)
    return {'t': a, 'fx': fx, 'fy': fy, 'why': why, 'keys': [[0, 100, 0, 0, 0], [b - a, s1, 0, 0, 0]]}

def hud(t_src, hold, s=230, fx=960, fy=0, ramp=0.35, ret=0.35, why=''):
    return pop(t_src, s, 0, ramp=ramp, hold=hold, ret=ret, fx=fx, fy=fy, why=why)

def bw(t_src, hold, s=108, why=''):
    t = T(t_src)
    return {'t': t, 'fx': 960, 'fy': 540, 'why': why,
            'keys': [[0, 100, 0, 0, 0], [0.12, 103, 0, 100, 0], [hold, s, 0, 100, 0], [hold + 0.2, 100, 0, 0, 0]]}

fx = [
    dolly(0.36, 4.62, 106, 'gancho: push lento'),
    pop(4.70, 138, 0, ramp=0.12, hold=0.25, ret=0.5, why='"toda a água do mundo": soco'),
    pop(14.05, 112, 0, ramp=0.12, hold=0.3, ret=0.45, why='deboche "canudinho aqui?"'),
    pop(15.30, 128, -45, ramp=0.18, hold=0.55, ret=0.5, why='PERGUNTA RETÓRICA "Você é maluco?": distorção'),
    pop(19.30, 116, 0, ramp=0.15, hold=0.4, ret=0.45, why='"Deixa de frescura, Patão!"'),
    dolly(21.4, 27.3, 105, 'primeira investida (suave)'),
    dolly(40.90, 42.20, 104, 'tensão: dolly leve 1'),
    pop(42.30, 138, -45, ramp=0.18, hold=0.55, ret=0.45, why='PERGUNTA RETÓRICA 1 "Por que que eu tô tomando?": distorção + cacho de ?'),
    dolly(43.60, 44.75, 105, 'tensão: dolly leve 2'),
    pop(44.85, 118, 0, ramp=0.12, hold=0.35, ret=0.4, why='obstáculo 1 "Eu não consigo"'),
    dolly(46.1, 50.25, 108, 'tensão: dolly lento 3'),
    hud(50.35, 1.3, s=250, fx=962, fy=944, why='obstáculo 2 "Eu não consigo beber": zoom na mensagem do jogo (visível 50.0-52.4)'),
    bw(54.70, 1.55, why='PERGUNTA RETÓRICA 2 "Por que a gente não consegue beber nada?": P&B + push'),
    pop(58.96, 120, 0, ramp=0.14, hold=0.4, ret=0.45, why='"Poça d\'água? É verdade!"'),
    pop(71.7, 125, 0, ramp=0.14, hold=0.4, ret=0.45, why='"Essa poça aqui é minha"'),
    hud(79.95, 1.5, why='contador: mais de 20 litros'),
    hud(93.10, 1.5, why='contador: mais de 100 litros'),
    pop(104.00, 130, -45, ramp=0.18, hold=0.6, ret=0.5, why='PERGUNTA RETÓRICA "Você tá bebendo água?": distorção'),
    pop(117.82, 160, -55, ramp=0.18, hold=1.0, ret=0.55, fy=600, why='gag da barriga: zoom abaulado'),
    pop(129.85, 128, -40, ramp=0.18, hold=0.55, ret=0.5, why='PERGUNTA RETÓRICA "a gente tá desse jeito?": distorção'),
    hud(150.75, 2.2, why='"apenas 0,1%": mostra o contador'),
    dolly(177.2, 181.5, 106, 'esperança: push lento'),
    pop(195.30, 125, -40, ramp=0.18, hold=0.5, ret=0.5, why='PERGUNTA "Será que os villagers vão ajudar a gente?"'),
]

# --- stickers ----------------------------------------------------------------------
sticks = [
    {'file': PNG + r'\spot_dark.png', 'tl': round(T(6.66), 4), 'dur': 1.85, 'pos': [0.66, 0.50], 'scale': 100, 'rot': 0, 'v': 3, 'fade': 0.18, 'opacity': 100, 'why': 'spotlight no item'},
    {'file': PNG + r'\canudinho.png', 'tl': round(T(6.74), 4), 'dur': 1.75, 'pos': [0.66, 0.50], 'scale': 56, 'rot': -8, 'v': 2, 'why': '"esse canudinho": mostra o item citado'},
    {'file': PNG + r'\interrogacao_cluster.png', 'tl': round(T(42.30), 4), 'dur': 1.5, 'pos': [0.50, 0.70], 'scale': 78, 'rot': 0, 'v': 2, 'why': 'cacho de "?" (ref: pergunta retórica)'},
    {'file': PNG + r'\interrogacao_cluster.png', 'tl': round(T(129.90), 4), 'dur': 1.3, 'pos': [0.50, 0.28], 'scale': 70, 'rot': 3, 'v': 2, 'why': 'cacho de "?" na pergunta retórica 3'},
]

marks = [{'tl': round(m['tl_in'], 3), 'txt': 'MÚSICA: ' + m['why']} for m in music]
marks += [{'tl': round(T(a), 3), 'txt': t} for a, t in [(0.33, 'v12: início sem ruído morto (era 0.0–0.52)'), (27.6, 'v12: bastidor cortado COM folga antes de "Vai!" (corte limpo)'),
                                                         (42.3, 'v12: pergunta retórica = distorção + SFX meme + cacho de ?'), (54.7, 'v12: pergunta retórica = P&B')]]

plan = {'bruto_prefix': '2026-10-08', 'keeps': keeps, 'music': music, 'sfx': sfx, 'ducks': ducks, 'fx': fx, 'stickers': sticks, 'marks': marks,
        'boost_voice_db': 9.0, 'boost_music_db': 3.0, 'limiter': 0.92, 'dur_tl': round(DUR + 0.05, 3)}
out = r'C:\Users\mathe\Skills\_research\mc-test\v12\plan2.json'
json.dump(plan, open(out, 'w', encoding='utf8'), ensure_ascii=False, indent=1)
json.dump(rep, open(r'C:\Users\mathe\Skills\_research\mc-test\v12\junctions.json', 'w'), indent=1)
print('plan2 ->', out, ' musica', len(music), 'sfx', len(sfx), 'fx', len(fx))
for m in music: print('  música tl %.1f  %s' % (m['tl_in'], os.path.basename(m['file'])[:48]))
