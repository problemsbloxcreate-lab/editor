import json, os
FR = 1001 / 60000
sn = lambda t: round(t / FR) * FR
blocks = json.load(open('blocks.json', encoding='utf8'))['blocks']
END = 480.0
LIB = r"C:\Users\mathe\.claude\skills\minecraft-video-editor\library"

# ---------- cortes (tempos de FONTE, ancorados em palavras do ASR) ----------
cuts = [(27.9, 40.70, 'bastidor: "corta aí / tu já tá com o canudo / reiniciou" (retake de coordenação); a fala certa recomeça em "Vai!" 40.98'),
        (56.50, 57.45, 'falsa partida t1 "Por que a gente não..." + gagueira t2 "Eu falei" (a fala completa "Esse canudinho aqui, pô, eu falei" é mantida)'),
        (110.32, 112.32, 'falsa partida "Olha o tamanho da pan..." (t2 mudo); mantém "Pera aí"'),
        (350.20, 352.12, 'retake: 1º "O que você tá fazendo? Não, não, não, Bruno Coutinho" (mantém o 2º take limpo; t2 mudo)'),
        (366.55, 372.95, 'fala errada do Brukutu: "3,2,1 / sou contra / espera que vai acontecer" -> mantém a certa "sou a favor"')]
gaps = [(blocks[k][1], blocks[k + 1][0]) for k in range(len(blocks) - 1)]
for a, b in gaps:
    if b - a >= 1.2 and a < END and not any(c[0] - 0.3 <= a <= c[1] for c in cuts):
        cuts.append((a + 0.30, b - 0.20, 'pausa morta %.1fs -> 0.5s' % (b - a)))
for a_, b_ in [(226.25, 227.6)]:  # pausa real por energia de voz (RMS) em A1 e A2, que o ASR escondia
    if not any(c[0] - 0.3 <= a_ <= c[1] for c in cuts): cuts.append((a_ + 0.30, b_ - 0.20, 'pausa morta %.1fs -> 0.5s (RMS)' % (b_ - a_)))
cuts.sort()
cuts = [(sn(a), sn(b), r) for a, b, r in cuts if sn(b) > sn(a)]
keeps = []; cur = 0.0
for a, b, _ in cuts:
    keeps.append((sn(cur), a)); cur = b
keeps.append((sn(cur), sn(END)))
tl = []; t = 0.0
for a, b in keeps:
    tl.append({'src_in': a, 'src_out': b, 'tl_in': t, 'tl_out': t + (b - a)}); t += b - a


def S2T(x):
    for k in tl:
        if k['src_in'] <= x <= k['src_out']: return k['tl_in'] + x - k['src_in']
    for k in tl:
        if x < k['src_in']: return k['tl_in']
    return tl[-1]['tl_out']


# ---------- música: cena -> faixa (tempos de FONTE) ----------
music = [(0, 52.9, '2K25/ES_Last Level Pt. 1 - Heyson.mp3', -8.5, 'hook: desafio engraçado, gamey'),
         (52.9, 109.5, '2K25/ES_Brighter than the Sky - Akibakid.mp3', -8.4, 'entra em "Procura uma poça d água": acham as poças, competição animada'),
         (109.5, 149.2, '2K25/ES_GO - Ballpoint.mp3', -9.1, 'gag da barriga ("Por que eu tô com uma pança gigante"): hype'),
         (149.2, 191.0, '2K25/ES_The Detective - Flickering.mp3', -10.9, 'plot twist "apenas 0,1%" -> decepção/"furada", clima enxerido'),
         (191.0, 236.0, '2K25/ES_Farmer_s Chores - Flickering.mp3', -11.1, 'decidem ir à vila ("Vamos dar uma procurada na vila"): vila/plantação'),
         (236.0, 273.8, 'AVENTURAS/ES_The Adventure of a Lifetime - Grant Newman.mp3', -12.1, 'descoberta da loja ("olha só onde a gente veio parar")'),
         (273.8, 334.4, '2K25/ES_Cheer Up (Instrumental Version) - PW.mp3', -7.0, 'volta p/ testar o copo, bebem juntos'),
         (334.4, 400.0, '2K25/ES_The Sleepy Sneaky Sway - Luella Gren.mp3', -13.0, 'Brucutu aparece e atrapalha: tensão cômica'),
         (400.0, 480.0, '2K25/ES_Let the Good Times Roll - Mary Riddle.mp3', -11.7, 'Brucutu some, voltam a beber, vão à loja (nível 2)')]
TARGET = -31.0
mus = [{'file': os.path.join(LIB, 'music', *f.split('/')), 'src_in': a, 'src_out': b, 'tl_in': S2T(a), 'tl_out': S2T(b),
        'gain_db': round(TARGET - l, 1), 'why': why} for a, b, f, l, why in music]

# ---------- SFX (tempo de FONTE = início da palavra-âncora; fala completa depois) ----------
SF = os.path.join(LIB, 'sfx') + os.sep
sfx_src = [(0.10, 'anime-shine-sound-2.mp3', 'abertura (anime shine)'),
           (4.70, 'vine-boom.mp3', '"toda a água do mundo" (impacto)'),
           (14.95, 'record-scratch-2.mp3', 'freada na reação do amigo ("tá de brincadeira, né? ... Você é maluco?", t2 11.9–15.9)'),
           (52.90, 'whoosh-sfx.mp3', '"Procura uma poça d água" (novo objetivo; troca de música)'),
           (72.70, 'bonk_BEtiM8g.mp3', 'depois de "Essa poça aqui é minha." (posse cômica)'),
           (86.00, 'rimshot.mp3', 'depois de "Quem esvaziar primeiro ganha" (rimshot)'),
           (118.30, 'fails-ohhhh.mp3', 'depois de "olha o tamanho da minha barriga" (piada da barriga)'),
           (153.00, 'jixaw-metal-pipe-falling-sound.mp3', 'depois de "apenas 0,1% de água bebida" (fail)'),
           (168.30, 'sadtrombone.swf.mp3', 'depois de "isso tudo foi apenas 0,1% de toda a água do mundo" (trombone triste, reprise da piada)'),
           (192.30, 'whoosh-sfx.mp3', '"Vamos dar uma procurada na vila" (novo objetivo)'),
           (200.00, 'roblox-death-sound_1.mp3', 'depois de "conseguir beber os villagers também?" (piada)'),
           (237.88, 'anime-wow-sound-effect.mp3', '"olha só onde a gente veio parar" (descoberta)'),
           (251.70, 'vine-boom.mp3', '"É um canudo gigante." (impacto)'),
           (272.30, 'record-scratch-2.mp3', 'depois de "É um copo de água" (anticlímax)'),
           (309.80, 'bonk_BEtiM8g.mp3', 'depois de "Olha isso, é muito devagar" (decepção)'),
           (338.90, 'dun-dun-dun-sound-effect-brass_8nFBccR.mp3', '"o que vocês tão fazendo?" Brucutu aparece (suspense)'),
           (373.14, 'vine-boom.mp3', '"Eu, Brukutu, sou a favor do meio ambiente"'),
           (386.60, 'taco-bell-bong-sfx.mp3', 'depois de "ele consumiu toda a água do mundo"'),
           (442.90, 'fails-ohhhh.mp3', 'depois de "olha o tamanho dessa barriga" (reprise da piada)'),
           (474.46, 'erro.mp3', '"é impressão minha ou bugou" (erro)')]
sfx = [{'file': SF + f, 'src': t_, 'tl': S2T(t_), 'why': w} for t_, f, w in sfx_src]
duck_files = ('fails-ohhhh.mp3', 'jixaw-metal-pipe-falling-sound.mp3', 'taco-bell-bong-sfx.mp3', 'erro.mp3', 'record-scratch-2.mp3', 'roblox-death-sound_1.mp3', 'bonk_BEtiM8g.mp3', 'rimshot.mp3', 'sadtrombone.swf.mp3')
ducks = [{'tl': S2T(t_), 'dur': 1.0, 'depth_db': 9.0} for t_, f, w in sfx_src if f in duck_files]

# ---------- zooms: foco (fx,fy) em px do quadro 1920x1080; s = escala final %; curv = distorção (neg = abaulado) ----------
zooms = [{'src': 0.10, 'hold': 1.1, 's': 112, 'kind': 'push', 'fx': 960, 'fy': 540, 'why': 'abre com shine'},
         {'src': 4.70, 'hold': 0.9, 's': 140, 'kind': 'punch', 'fx': 900, 'fy': 560, 'why': '"toda a água do mundo" (soco no impacto)'},
         {'src': 19.26, 'hold': 0.8, 's': 130, 'kind': 'punch', 'fx': 1180, 'fy': 560, 'why': '"Deixa de frescura, Patão!" (zoom no Patão)'},
         {'src': 48.70, 'hold': 0.7, 's': 125, 'kind': 'punch', 'fx': 960, 'fy': 540, 'why': '"Bora, bora, bora" (fecha o gancho)'},
         {'src': 52.90, 'hold': 0.8, 's': 125, 'kind': 'punch', 'fx': 960, 'fy': 540, 'why': '"Procura uma poça d água" (novo objetivo)'},
         {'src': 70.90, 'hold': 0.8, 's': 125, 'kind': 'punch', 'fx': 960, 'fy': 600, 'why': '"Essa poça aqui é minha" (posse)'},
         {'src': 84.00, 'hold': 0.8, 's': 130, 'kind': 'punch', 'fx': 960, 'fy': 560, 'why': '"Quem esvaziar primeiro ganha" (aposta)'},
         {'src': 117.10, 'hold': 1.2, 's': 150, 'kind': 'punch', 'fx': 960, 'fy': 520, 'curv': -35, 'why': 'gag da barriga: "olha o tamanho da minha barriga" (zoom distorcido)'},
         {'src': 150.00, 'hold': 2.6, 's': 220, 'kind': 'hud', 'fx': 960, 'fy': 0, 'why': 'mostra o contador: "apenas 0,1% de água"'},
         {'src': 192.30, 'hold': 0.8, 's': 125, 'kind': 'punch', 'fx': 960, 'fy': 540, 'why': '"Vamos dar uma procurada na vila" (novo objetivo)'},
         {'src': 237.88, 'hold': 1.2, 's': 135, 'kind': 'dolly', 'fx': 960, 'fy': 560, 'why': 'loja descoberta'},
         {'src': 245.55, 'hold': 1.4, 's': 130, 'kind': 'dolly', 'fx': 960, 'fy': 640, 'why': 'mostra os itens da loja (boia com bomba, mochila)'},
         {'src': 251.70, 'hold': 0.8, 's': 130, 'kind': 'punch', 'fx': 960, 'fy': 600, 'why': '"É um canudo gigante"'},
         {'src': 308.60, 'hold': 0.5, 's': 120, 'kind': 'punch', 'fx': 960, 'fy': 560, 'why': '"é muito devagar" (decepção)'},
         {'src': 328.26, 'hold': 0.8, 's': 125, 'kind': 'punch', 'fx': 960, 'fy': 560, 'curv': -25, 'why': '"virando uma bola imensa" (distorção leve)'},
         {'src': 338.90, 'hold': 1.2, 's': 135, 'kind': 'punch', 'fx': 900, 'fy': 700, 'why': 'Brucutu aparece'},
         {'src': 408.14, 'hold': 0.8, 's': 125, 'kind': 'punch', 'fx': 960, 'fy': 560, 'why': '"virando uma bolota"'},
         {'src': 441.36, 'hold': 1.4, 's': 150, 'kind': 'punch', 'fx': 960, 'fy': 520, 'curv': -35, 'why': 'reprise da barriga: "olha o tamanho dessa barriga" (distorcido)'},
         {'src': 474.46, 'hold': 1.8, 's': 150, 'kind': 'dolly', 'fx': 1400, 'fy': 215, 'why': 'placa 1.500 litros: "bugou?"'}]
for z in zooms: z['tl'] = S2T(z['src'])

# ---------- stickers (PNG em V2) ----------
stickers = [{'file': os.path.join(LIB, 'png', 'interrogacao.png'), 'src': 42.30, 'tl': S2T(42.30), 'dur': 0.9, 'pos': [0.27, 0.66], 'scale': 55, 'why': 't2 "...por que eu tô tomando?" (confusão)'},
            {'file': os.path.join(LIB, 'png', 'interrogacao.png'), 'src': 217.90, 'tl': S2T(217.90), 'dur': 0.9, 'pos': [0.27, 0.66], 'scale': 55, 'why': '"Beber água da plantação?" (dúvida)'}]

# ---------- marcadores REVISAR ----------
marks_src = [(0.0, 'REVISAR: cliques de mouse/teclado/tosse NÃO verificados (não consigo ouvir) — passar o ouvido nas faixas A1/A2'),
             (28.0, 'bastidor cortado (27.9–40.7): "corta aí / tu já tá com o canudo / reiniciou"'),
             (93.0, 'REVISAR: "Já bebi mais de 100 litros" / "Eu já bebi quase 100 litros" (possível take duplicado; não cortei: palavras se sobrepõem no ASR)'),
             (113.7, 'REVISAR: 113.7–127 falas sobrepostas (t1 "pança gigante / olha o tamanho da minha barriga" + t2 "vocês tão barrigudos... tua pança") — ASR confuso'),
             (233.9, 'REVISAR: 233.9–245 ASR confuso (t2 "Olha Pobre olha isso aqui")'),
             (350.0, 'cortei o 1º take de "O que você tá fazendo... Bruno Coutinho" (350.2–352.1) ; "É o C, né, Chique?" repetido em 340.0 NÃO cortado (zoom do Brucutu em cima); conferir se ficou natural'),
             (354.0, 'REVISAR: Brucutu/Pobre falando em cima de t1 354–366 ("Zeradinho... qual que o seu problema / deserto seco")'),
             (366.4, 'cortei fala errada do Brukutu ("sou contra"); conferir se o plano de vídeo pula bem'),
             (153.7, 'REVISAR: "Mas bora continuar bebendo água, galera" / "Bora continuar bebendo" (possível retake de t1)'),
             (213.6, 'REVISAR: "vamos beber a água da plantação" dito por t2 e de novo por t1 ("Beber água da plantação?") — pode ser eco de roteiro, não cortei'),
             (316.0, 'REVISAR: "vamos beber junto com o patrão do poço d água" repetido em 316.0–320.8 (possível retake)'),
             (445.5, 'REVISAR: "A bochecha dele, patão" ×2 (445.5–447.5) e "Isso aqui é músculo" ×2 (t2 449.2–452) — possíveis retakes'),
             (479.0, 'REVISAR: final do trecho: o ASR lê "não tá bugado nada" várias vezes por sobreposição de t1 com t2 ("R$ 1.500,00, Vitor") e pode ler outra palavra; fim da janela de teste (cena continua)')]
marks = [{'tl': S2T(t_), 'txt': x} for t_, x in marks_src]
for tl_, why_ in [(32.8, 'REVISAR: ~2 s sem fala no ASR (pode ser ação do jogo ou fala não transcrita) — decidir ouvindo'),
                  (203.8, 'REVISAR: ~2 s sem fala no ASR (idem)'), (391.5, 'REVISAR: ~2 s sem fala no ASR (idem)')]:
    marks.append({'tl': tl_, 'txt': why_})

out = {'mutes': [], 'keeps': tl, 'cuts': [{'a': a, 'b': b, 'why': r} for a, b, r in cuts], 'music': mus, 'sfx': sfx, 'ducks': ducks,
       'boost_voice_db': 9.0, 'boost_music_db': 3.0, 'limiter': 0.91, 'zooms': zooms, 'stickers': stickers, 'marks': marks, 'dur_tl': tl[-1]['tl_out']}
json.dump(out, open('plan.json', 'w', encoding='utf8'), ensure_ascii=False, indent=1)
print('segmentos', len(tl), 'duracao tl %.1fs (removidos %.1fs)' % (out['dur_tl'], END - out['dur_tl']))
for c in cuts: print('%.2f-%.2f  %s' % (c[0], c[1], c[2][:70]))
for m in mus: print('musica tl %.1f-%.1f (%.1fs) %s' % (m['tl_in'], m['tl_out'], m['tl_out'] - m['tl_in'], os.path.basename(m['file'])))
