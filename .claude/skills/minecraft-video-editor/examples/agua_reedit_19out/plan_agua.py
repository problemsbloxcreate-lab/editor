"""PLANO de edição — 'Bebi toda a água do mundo' (Sequência 01 decupada pelo Matheus, 19:43). Gera plan.json.
Tempos = TIMELINE. Âncoras por palavra (anchors.A). Regras: skill minecraft-video-editor (v5.1 + decupagem 19/10).
HUD (contador de água) = topo centro (960, 40); personagem ~ (960, 560); hotbar/nome do item ~ (900, 1010)."""
import json, os
from anchors import A, mmss, cut_near, clip_at, END

MUS = r"D:\Users\PREDATOR\Documents\Epidemic 2K23 (Pasta de músicas)"
SFX = os.path.expanduser(r"~\.claude\skills\minecraft-video-editor\library\sfx")
PNG = os.path.expanduser(r"~\.claude\skills\minecraft-video-editor\library\png")
HUD, FACE, HOT = (960, 0), (960, 560), (900, 1010)      # HUD: foco na borda de cima (senão a 1ª linha do contador corta)

music, zooms, stretch, presets, sfx, reveals, marks, overlays, mutes, bleeps = [], [], [], [], [], [], [], [], [], []


def track(folder, title):
    d = os.path.join(MUS, folder)
    for f in sorted(os.listdir(d)):
        core = f[3:] if f.startswith("ES_") else f
        if core.lower().startswith(title.lower() + " - ") or core.lower().startswith(title.lower() + "."): return os.path.join(d, f)
    for f in sorted(os.listdir(d)):
        if title.lower() in f.lower(): return os.path.join(d, f)
    raise FileNotFoundError(folder + "/" + title)


def M(t, folder, title, src=0.0, g=-26.0, why=""):
    music.append({"t": t, "file": track(folder, title), "src": src, "g": g, "why": why})


def MOFF(t, why=""):            # música cala (record scratch / punchline)
    music.append({"t": t, "file": None, "why": why})


def Z(t, s, ramp=0.0, f=FACE, end=None, why=""):
    """zoom no V1 a partir de t: ramp=0 -> corte seco; ramp>0 -> ease-out que FICA; end = volta em corte seco (razor)"""
    zooms.append({"t": t, "s": s, "ramp": ramp, "fx": f[0], "fy": f[1], "end": end, "why": why})


def STR(t, end, sx=391, sy=258, f=FACE, why=""):
    stretch.append({"t": t, "end": end, "sx": sx, "sy": sy, "fx": f[0], "fy": f[1], "why": why})


def P(t, name, end=None, anchor=None, tscale=1.0, why=""):
    presets.append({"t": t, "name": name, "end": end, "anchor": anchor, "tscale": tscale, "why": why})


def S(t, name, g=None, cut=False, pre=0.06, dur=None, why=""):
    x = {"t": t, "file": os.path.join(SFX, name), "cut": cut, "pre": pre, "why": why}
    if g is not None: x["g"] = g
    if dur: x["dur"] = dur
    sfx.append(x)


def NOP(*a, **k): pass


def MK(t, txt): marks.append({"t": t, "txt": txt})


# ---------------- receitas (padrão aprovado + referência) ----------------
def item(t, f=HOT, s=320, why="item citado"):
    Z(t, s, 1.0, f, why=why); S(t, "anime-wow-sound-effect (1).mp3", -17.0, why=why)


def hud(t, good=True, s=260, why="número no HUD"):
    Z(t, min(s, 230), 0.0, HUD, end=t + 1.6, why=why)        # referência: zoom SECO ~200 % no contador, segura e sai no corte
    if good: S(t, "mc-random-orb.mp3", 4.0, why=why)


def ruim(t, why="número/fato que pesa"):          # 0,1% / 2,5% / voltou a 100 %
    P(t, "Red Flash B", why=why); P(t, "Impact Shake High", why=why)
    S(t, "mc-random-anvil_land.mp3", -10.8, why=why); S(t + 0.35, "wrong_5.mp3", -8.1, why=why)


def deboche(t, end, why="pergunta debochada"):
    STR(t, end, why=why); P(t, "VHS", end=end, why=why)
    S(t, "bamboo-hit-anime-bonk-sound.mp3", -10.7, why=why); S(t + 0.05, "record-scratch-2.mp3", -17.0, why=why)


def fail(t, end, why="falha"):
    P(t, "Red Flash B", why=why); S(t, "spongebob-fail.mp3", -17.0, why=why)      # referência: falha = flash vermelho que some em ~1 s


def punch(t, s=240, end=None, f=FACE, snd=None, g=None, why="reação"):
    Z(t, s, 0.0, f, end=end, why=why)
    if snd: S(t, snd, g, cut=True, why=why)


def vilao(t, why="Brucutu"):
    P(t, "Red Flash B", why=why)
    S(t, "dun-dun-dun-sound-effect-brass_8nFBccR.mp3", -14.0, why=why)


def loja(t, why="loja/itens novos"):
    P(t, "White Flash B", why=why); S(t, "anime-shine-sound-effect_QP4mAaX (1).mp3", -7.3, why=why)


def nivel(t, why="nível liberado"):
    S(t, "mc-random-levelup.mp3", -6.0, why=why); P(t, "Green Flash B", why=why)      # referência: novidade = flash verde


def compra(t, why="comprou"):
    S(t, "mc-ui-toast-challenge_complete.mp3", -6.0, why=why); P(t, "Green Flash B", why=why)   # referência: compra = flash verde


# =====================================================================================
# 0:00–0:36  GANCHO (denso)
t_eu = A("eu, Patão e Chique", "0:01")
t_us = A("usando apenas esse canudinho", "0:05")
M(0.0, "2K25", "Brighter than the Sky", 0.0, -24, "sting de abertura (aprovado)")
M(1.8018, "MUY ANIMADAS", "Lifecrash", 0.0, -25, "intro enérgica (aprovado)")
P(0.0, "White Flash B", why="abertura"); Z(0.0, 100, why="base")
S(0.0, "anime-shine-sound-2.mp3", -6.9, why="abertura")
overlays.append({"kind": "broll", "file": r"D:\cinecam-out\takes_futuros_oceano\takes_futuros_oceano.mp4", "t": t_eu, "dur": round(t_us - t_eu, 3), "off": 0.0, "v": 3,
                 "echo_at": 0.55, "why": "TESE: beber toda a água do mundo (B-roll aprovado na v14)"})
S(t_eu - 0.38, "19--Whoosh 39.wav", 0.0, why="whoosh antes do B-roll")
S(A("vamos beber toda a água do mundo", "0:02"), "vine-boom.mp3", -7.1, why="tese")
S(t_eu + 0.4, "fortnite-shield-potion-fortnite-battle-royale-gaming-sound-effect-hd-sound-effect_rnYyvja.mp3", -4.4, why="poção sob o B-roll")
mutes.append({"track": 2, "a": t_eu - 0.05, "b": t_us, "why": "jogo sob o B-roll"})
item(t_us - 0.16, HOT, 330, "canudinho: corte p/ o item antes da frase")
t_bb = A("Beber toda a água do mundo com esse", "0:09", spk="C")
t_can = A("canudinho aqui", "0:11", spk="C")
overlays.append({"kind": "broll", "file": r"D:\cinecam-out\universo_canudo\universo_canudo.mp4", "t": t_bb, "dur": round(t_can - t_bb, 3), "off": 0.83, "v": 3, "why": "canudo x universo"})
S(t_bb - 0.12, "minecraft-drinking-sound-effect.mp3", -4.6, why="gole antes do B-roll do canudo")
S(t_can - 0.05, "nintendo-switch-error.mp3", -3.3, why="dúvida")
t_mal = A("Você é maluco", "0:12", spk="C")
deboche(t_mal - 0.05, A("Você é maluco", "0:12", spk="C", end=True) + 0.25, "Você é maluco? (deboche)")
MOFF(t_mal - 0.05, "record scratch: música cala")
t_ex = A("Exatamente, Patão", "0:14")
M(t_ex, "2K25", "Sleepy Sneaky Sway", 0.0, -25, "aprovado")
punch(t_ex, 235, why="Exatamente (convicção)")
t_fr = A("Deixa de frescura", "0:16", spk="C")
punch(t_fr, 245, why="call: deixa de frescura")
t_mar = A("Essa água do mar aqui já é minha", "0:20", spk="C")
S(t_mar, "minecraft-drinking-sound-effect.mp3", -5.5, why="1 gole")
t_n6 = A("no nível 6", "0:26")
hud(t_n6 - 0.4, good=False, why="obstáculo: mensagem 'liberado no nível 6'")
S(t_n6 - 0.4, "nintendo-switch-error.mp3", -3.2, why="obstáculo")
t_pq = A("Por que a gente não consegue beber nada", "0:28")
fail(t_pq, A("Ah, droga", "0:29", end=True) + 0.1, "não consegue beber (falha)")
MOFF(t_pq, "falha: música cala")
t_sorte = A("Por sorte a gente tem uma poça", "0:32", spk="C")
M(t_sorte, "TROLL", "Festive Riot", 0.0, -25, "caça às poças (aprovado)")
t_poca = A("Poça d'água? Caraca, é verdade", "0:36")
punch(t_poca, 230, snd="vine-boom.mp3", g=-7.1, why="Poça d'água?!")
t_olha = A("Olha só o tanto de poça d'água", "0:38")
overlays.append({"kind": "broll", "file": r"D:\cinecam-out\pa_rasante_plongee\pa_rasante_plongee.mp4", "t": t_olha, "dur": 3.0, "off": 3.59, "v": 3,
                 "pos": [0.5, 0.266], "scale": 150.8, "flash": [70, 0.9], "why": "revelação das poças (aprovado)"})
S(t_olha, "bass-impact.mp3", 0.0, why="revelação"); S(t_olha, "impact_water.mp3", -10.5, why="revelação"); S(t_olha, "19--Whoosh 39.wav", 0.0, why="revelação")
mutes.append({"track": 2, "a": t_olha - 0.05, "b": t_olha + 3.0, "why": "jogo sob o B-roll"})
t_minha = A("Essa poça aqui é minha", "0:42")
M(t_minha, "NUEVAS 2K24", "When the Cats Away", 5.0, -26, "corrida de beber (aprovado)")
punch(t_minha, 238, why="essa poça é minha")
t_20 = A("foram mais de 20 litros", "0:47")
hud(t_20, why="20 litros")
t_100 = A("quase 100 litros", "0:59")
hud(t_100, why="quase 100 litros")
S(A("Quem esvaziar primeiro", "0:50"), "mc-note-pling.mp3", -6.0, why="desafio")

# 1:03–1:57  BARRIGA / 0,1 %
t_rep = A("você só não reparou uma coisa", "1:04")
Z(t_rep, 122, 1.2, FACE, why="revelação: push-in"); reveals.append({"t": t_rep, "kind": "sparkle", "why": "você só não reparou"})
S(t_rep, "anime-shine-sound-effect_QP4mAaX (1).mp3", -7.3, why="revelação")
M(t_rep, "MISTERIO", "Mitch the Snitch", 44.4, -27, "desconfiança/barriga (aprovado)")
t_tam = A("Olha o tamanho da", "1:07")
punch(t_tam, 250, snd="cartoon-boing.mp3", g=-2.3, why="olha o tamanho da pança")
t_gig = A("Por que eu tô com uma pança gigante também", "1:09")
punch(t_gig, 245, why="pança gigante também?"); S(t_gig + 1.4, "perfect-fart-sound-effect-hd_128k.mp3", -8.6, why="piada de barriga")
t_tao = A("Vocês são tão barrigudos", "1:15", spk="C")
reveals.append({"t": t_tao, "kind": "tilt", "why": "vocês são tão barrigudos (murchar)"})
S(t_tao, "clown-horn-short.mp3", -19.8, cut=True, why="gag barriga")
M(t_tao + 2.0, "TROLL", "Happy Shortcut", 0.0, -26, "gag cômico (aprovado)")
t_imag = A("Imagina quando a gente beber o mar inteiro", "1:26")
Z(t_imag, 118, 1.6, FACE, why="imagina... (ênfase lenta)")
S(A("bebendo água", "1:28"), "mc-random-burp.mp3", 0.8, why="barriga cheia")
t_280 = A("280 litros", "1:37")
hud(t_280 - 0.3, why="280 litros")
t_001 = A("apenas 0,01%", "1:39")
hud(t_001, good=False, s=240, why="0,01%: decepção")
S(t_001 + 0.2, "bruh-sound-effect-1.mp3", -18.0, why="decepção")
t_01 = A("apenas 0,1%", "1:48")
ruim(t_01, "apenas 0,1% de toda a água do mundo")
MOFF(t_01, "punchline")
M(A("apenas 0,1%", "1:48", end=True) + 1.0, "TROLL", "The Olive Branch", 0.0, -25, "decepção (aprovado)")
t_fur = A("esse vídeo era uma furada", "1:52", spk="C")
punch(t_fur, 240, snd="bruh-sound-effect-1.mp3", g=-18.0, why="furada")
t_fn = A("Porada nada, patão", "1:55")
M(t_fn, "VLOGS", "Your Gain", 10.0, -25, "esperança (aprovado)")
# TAKES FUTUROS — vaga que ele deixou: V1 desabilitado em 117,07–120,90
FUT = [(r"D:\Pobrs\futuros\futuro_01_t1626.mp4", 0.76), (r"D:\Pobrs\futuros\futuro_02_t1939.mp4", 0.76), (r"D:\Pobrs\futuros\futuro_03_t2136.mp4", 0.76),
       (r"D:\Pobrs\futuros\futuro_04_t2138.mp4", 0.76), (r"D:\Pobrs\futuros\futuro_05_t2142.mp4", 0.79)]
tf = 117.06695
for i, (f, d) in enumerate(FUT):
    overlays.append({"kind": "futuro", "file": f, "t": round(tf, 4), "dur": d, "off": 1.0, "v": 2, "zoom": [100, 106 if i < 4 else 108],
                     "preset_in": "White Flash B" if i == 0 else None, "preset_out": "White Flash A" if i == len(FUT) - 1 else None, "why": "takes futuros"})
    S(tf - 0.02, "mc-xp-orb-p%d.mp3" % i, 7.0, why="orb XP a cada corte dos takes")
    tf += d
MK(117.07, "TAKES FUTUROS (vaga do V1 desabilitado): 5 takes do clímax c/ flashback sépia + orbs")

# 2:01–2:51  VILA / BAÚ / LOJA
t_70 = A("feitos em 70% de água", "2:13")
Z(t_70, 125, 0.9, FACE, why="70% de água (ênfase)")
S(t_70 + 0.9, "mc-mob-villager-idle1.mp3", -12.0, why="ÚNICO villager do vídeo: fala dos villagers")
t_pl = A("beber a água da plantação", "2:21", spk="C")
punch(t_pl, 240, why="beber a água da plantação?")
t_esq = A("Esquece essa porcaria aí", "2:27", spk="C")
S(t_esq, "taco-bell-bong-sfx.mp3", -12.0, cut=True, why="esquece essa porcaria")
t_bau = A("baú aqui", "2:33")
S(t_bau - 0.2, "mc-random-chestopen.mp3", -4.0, why="baú")
t_tel = A("Teleporter", "2:33")
item(t_tel, HOT, 300, "item: teleporter")
t_loja = A("olha só onde a gente veio parar", "2:37")
loja(t_loja, "chegou na LOJA"); reveals.append({"t": t_loja, "kind": "sparkle", "why": "loja"})
Z(t_loja, 120, 1.4, FACE, why="revelação da loja")
M(t_loja, "TROLL", "Hot Piece for Sale", 0.0, -26, "loja")
t_cg = A("canudo gigante", "2:47")
punch(t_cg, 250, snd="anime-wow-sound-effect (1).mp3", g=-17.0, why="canudo gigante")
S(A("nem cabe na minha boca", "2:49") + 0.2, "cartoon-boing.mp3", -2.3, why="gag")
t_bn = A("Buraco negro na boca? Como assim", "2:53")
deboche(t_bn, A("Como assim", "2:54", end=True) + 0.25, "buraco negro na boca?!")
MOFF(t_bn, "scratch")
t_ruim = A("Esse vai dar ruim", "2:56", spk="C")
punch(t_ruim, 245, snd="sudden-suspense-sound-effect.mp3", g=-22.3, why="vai dar ruim")
M(A("pois é", "2:57"), "NUEVAS 2K24", "Having Fun", 0.0, -26, "compra e teste do copo")
t_copo = A("nível É 1 um copo de E água", "3:00")
item(t_copo, HOT, 300, "copo d'água nível 1")
compra(A("eu já comprei", "3:02"), "comprou o copo")

# 3:07–3:50  TESTE DO COPO / BOLA
t_n6b = A("é só no nível 6", "3:14")
hud(t_n6b, good=False, s=230, why="mar só no nível 6")
t_cp = A("um copo d'água", "3:21")
S(t_cp, "minecraft-drinking-sound-effect.mp3", -5.5, why="gole")
t_dev = A("Não é rápido não, é devagar", "3:28")
fail(t_dev, A("é devagar", "3:29", end=True) + 0.15, "copo é devagar")
MOFF(t_dev, "falha")
M(A("achando a grande porcaria", "3:30", spk="C"), "TROLL", "The Blame Is on Me", 0.0, -26, "gag")
t_acel = A("acelerando", "3:34", spk="C")
Z(t_acel, 118, 1.0, FACE, why="acelerando")
t_bola = A("tá todo mundo engordando", "3:43")
punch(t_bola, 240, snd="cartoon-boing.mp3", g=-2.3, why="virou uma bola")
S(A("virou uma bola imensa", "3:45") + 0.4, "mc-random-burp.mp3", 0.8, why="barriga cheia")
t_ab = A("a nossa água tá abaixando", "3:51")
S(t_ab - 0.5, "record-scratch-2.mp3", -17.0, cut=True, why="peraí... virada")
MOFF(t_ab - 0.5, "virada de clima")
Z(t_ab, 130, 1.2, FACE, why="tensão")
S(t_ab, "sudden-suspense-sound-effect.mp3", -22.3, why="suspeita")

# 3:53–4:22  BRUCUTU
t_dia = A("tamanho de diamante", "3:59", spk="C")
M(t_ab - 0.5 + 1.5, "2K25", "That Thing Behind Us", 0.0, -25, "virada: água baixando -> vilão (faixa aprovada)")
t_bru = A("O que você tá fazendo, Brucutu", "4:03")
vilao(t_bru, "Brucutu aparece")
punch(t_bru + 0.05, 245, why="Brucutu")
t_zer = A("Zeradinho", "4:06")
deboche(t_zer, A("Qual que é o seu problema, cara", "4:08", end=True), "Zeradinho? qual o seu problema")
t_meio = A("sou a favor do meio ambiente", "4:09", spk="C")
punch(t_meio, 235, why="Brucutu: meio ambiente")
t_idi = A("idiotas", "4:13", spk="C")
S(t_idi, "metal-gear-alert-sound-effect_XKoHReZ.mp3", -14.0, why="ameaça")
t_cons = A("consumiu toda a água do mundo", "4:20")
hud(t_cons, good=False, s=240, why="Brucutu bebeu tudo: HUD")
t_norm = A("voltei ao normal", "4:21")
fail(t_norm, t_norm + 1.2, "voltei ao normal (perdeu tudo)")
MOFF(t_norm, "falha")
t_out = A("Quer saber? Eu vou pra outra área", "4:23")
M(t_out, "TROLL", "The Wager", 0.0, -26, "recomeço")

# 4:32–5:10  BARRIGA 2 / MÚSCULO
t_bol = A("Já tô virando uma bolota", "4:35")
punch(t_bol, 240, snd="perfect-fart-sound-effect-hd_128k.mp3", g=-12.3, why="virando bolota")
t_nq = A("Não, não, não quero ficar barrigudo", "4:41", spk="C")
M(A("não quero mais beber água", "4:38", spk="C"), "TROLL", "Bumblebee", 0.0, -26, "Patão não quer")
punch(t_nq, 248, why="não quero ficar barrigudo")
t_buraco = A("o tamanho desse buraco", "4:49")
Z(t_buraco, 125, 1.1, FACE, why="tamanho do buraco")
t_gig2 = A("eu tô gigante", "4:54")
punch(t_gig2, 240, snd="cartoon-boing.mp3", g=-2.3, why="tô gigante")
t_col = A("Tá colossal", "5:03", spk="C")
S(t_col, "original-sheesh.mp3", -16.0, cut=True, why="colossal")
t_mus = A("Isso aqui é músculo", "5:06", spk="C")
punch(t_mus, 250, why="isso aqui é músculo")
S(t_mus + 0.1, "vine-boom.mp3", -7.1, why="músculo (punchline)")

# 5:08–5:53  LOJA 2 / RIO
t_l2 = A("Vamos logo pra loja", "5:09")
M(A("Olha só, galera. Já dá pra desbloquear", "5:12"), "NUEVAS 2K24", "Cheat Sheet", 0.0, -26, "loja nível 2")
loja(A("Olha só, galera. Já dá pra desbloquear", "5:12"), "itens nível 2")
t_ch = A("chapéu de e líquidos", "5:18")
item(t_ch, HOT, 300, "chapéu de líquidos")
t_bomba = A("bomba d'água", "5:17")
compra(A("agora eu vou pegar a", "5:21"), "pegou a bomba")
t_bug = A("tá bugado", "5:26")
S(t_bug, "nintendo-switch-error.mp3", -3.2, cut=True, why="bugado")
t_1500 = A("é 1.500", "5:27", spk="C")
hud(t_1500, good=False, s=230, why="custa 1.500")
t_feio = A("Deus do céu mas que negócio feio é esse", "5:33")
deboche(t_feio, A("negócio feio é esse chique", "5:34", end=True) + 0.2, "que negócio feio é esse")
t_rio = A("rio não tá liberado", "5:46")
fail(t_rio, A("rio não tá liberado", "5:46", end=True) + 0.8, "rio bloqueado")
MOFF(t_rio, "falha")
t_pisc = A("como assim a piscina", "5:54")
M(t_pisc, "NUEVAS 2K24", "Surfer", 0.0, -26, "piscina!")
punch(t_pisc, 235, snd="anime-wow-sound-effect (1).mp3", g=-17.0, why="piscina")

# 5:53–6:57  PISCINA / ABERRAÇÃO
t_cab = A("se eu usar esse negócio na cabeça", "6:04")
item(t_cab, HOT, 280, "chapéu na cabeça + boia")
t_ent = A("tá entrando muita", "6:07")
S(t_ent, "mc-random-splash.mp3", -6.0, why="água entrando"); NOP(t_ent, "Fullscreen Shake - Low Fast", end=t_ent + 1.5, why="sugando")
t_3mil = A("3 mil litros de água", "6:23")
hud(t_3mil, why="3 mil litros")
t_ult = A("É só beber o último e pronto", "6:31")
S(A("e pronto", "6:32"), "mc-ui-toast-challenge_complete.mp3", -6.0, why="piscina completa")
t_bem = A("Eu não estou nem um pouco bem", "6:37")
M(A("Galera, é o seguinte", "6:36"), "TROLL", "Bring In the Clowns", 0.0, -26, "aberração cômica")
punch(t_bem, 250, why="não tô bem")
t_ab2 = A("que aberração é essa", "6:40")
STR(t_ab2, t_ab2 + 1.3, 300, 210, FACE, why="aberração (distorção)"); S(t_ab2, "five-nights-at-freddys-full-scream-sound_2.mp3", -24.0, why="aberração (susto cômico)")
t_sai = A("Como é que a gente sai da piscina", "6:45")
Z(t_sai, 120, 1.2, FACE, why="como sai?")
t_pens = A("eu não tinha pensado nisso", "6:49", spk="C")
punch(t_pens, 245, snd="bruh-sound-effect-1.mp3", g=-18.0, why="não tinha pensado nisso")

# 6:57–7:43  LOJA 3 (mochila) / BRUCUTU ENCHE
t_pr = A("Aquele deve ser muito melhor", "7:03")
M(A("Vamos galera pegar o próximo item da loja", "6:58", spk="C"), "TENSAS", "Get in and Go", 0.0, -26, "corrida p/ loja antes do Brucutu")
t_bx = A("já tá baixando água", "7:08")
hud(t_bx, good=False, s=240, why="água baixando")
t_comp = A("compra logo", "7:10")
NOP(t_comp, "Fullscreen Shake - Mid Fast", end=t_comp + 1.2, why="pressa")
t_moc = A("mochila aspiradora", "7:16")
item(t_moc, HOT, 300, "mochila aspiradora"); compra(t_moc - 0.3)
t_volta = A("problema é que ele já tá voltando", "7:18")
vilao(t_volta, "Brucutu devolvendo a água")
M(t_volta, "MISTERIO", "Hide and Sneak", 0.0, -27, "Brucutu enchendo/esconder")
t_arm = A("piscina com aquela arminha", "7:22")
Z(t_arm, 160, 0.8, FACE, end=t_arm + 2.0, why="arminha do Brucutu")
t_esc = A("esconde, esconde", "7:36")
punch(t_esc, 230, snd="why-are-you-running-sound-effect-hd_2yraBjq.mp3", g=-14.0, why="esconde!")
t_desc = A("essa arma está descarregando", "7:38", spk="C")
S(t_desc, "mc-random-click.mp3", 4.0, why="arma descarregou")

# 7:43–8:59  SUGAR TUDO / 25 MIL
t_hora = A("nossa hora", "7:44")
M(A("Agora galera que ele vai recarregar", "7:43"), "EPICAS", "Heroes of Speed", 0.0, -26, "ação: sugar rápido")
P(t_hora, "Impact Shake Low", why="nossa hora")
t_rap = A("mochila aspiradora é muito rápida", "7:51")
NOP(t_rap, "Fullscreen Shake - Low Fast", end=t_rap + 1.8, why="sugando rápido"); S(t_rap, "mc-random-splash.mp3", -6.0, why="sugando")
t_rob = A("pegar o item ainda mais roubado", "7:55")
S(A("olha isso", "7:57"), "original-sheesh.mp3", -16.0, why="roubado")
t_10 = A("gente vai esvaziar umas 10 piscinas agora", "8:02", spk="C")
punch(t_10, 240, why="10 piscinas")
t_blo = A("Quebrar volta o bloco na mão", "8:09")
S(t_blo, "sm64_mario_oof.mp3", -12.0, cut=True, why="de novo o bloco")
t_ape = A("a gente não aprende mesmo", "8:12", spk="C")
punch(t_ape, 240, why="não aprende mesmo")
M(A("vamos fazer diferente", "8:20"), "NUEVAS 2K24", "Rush Hour Shift", 0.0, -26, "cada um esvazia uma piscina")
t_ult2 = A("isso aqui é a última piscina", "8:45")
Z(t_ult2, 118, 1.0, FACE, why="última piscina")
t_viz = A("tá tudo vazio", "8:49")
S(t_viz, "tadaa.mp3", -12.0, why="tudo vazio")
t_25 = A("25 mil litros de água", "8:55")
hud(t_25, good=True, s=250, why="precisa de 25 mil")
t_236 = A("23.600 Porcaria", "8:57")
hud(t_236 - 0.2, good=False, s=270, why="só 23.600")
S(A("Porcaria", "8:58"), "spongebob-fail.mp3", -20.0, why="quase")
MOFF(A("Porcaria", "8:58"), "falha")

# 8:59–9:41  BRUCUTU / DENGUE
M(A("Que palhaçada é essa", "9:09", spk="C"), "TROLL", "Sneaky Grandma", 0.0, -26, "desculpa da dengue")
t_pal = A("Que palhaçada é essa", "9:09", spk="C")
vilao(t_pal, "Brucutu volta")
t_plan = A("tem eu tenho um plano", "9:13")
punch(t_plan, 235, why="tenho um plano")
t_den = A("combatendo a dengue", "9:21")
punch(t_den, 245, snd="deg-deg-sussy.mp3", g=-14.0, why="mentira da dengue")
t_nin = A("Ninguém aqui bebe água", "9:30", spk="C")
STR(t_nin, t_nin + 1.4, 330, 230, why="ninguém bebe água, né? (desconfiança)")
S(t_nin, "hmmmm_7rRG5zE.mp3", -16.0, why="desconfiança")
t_clo = A("cheia de cloro", "9:34", spk="C")
S(t_clo, "taco-bell-bong-sfx.mp3", -12.0, why="cloro")

# 9:41–10:50  AMORZINHO / PARQUE
t_fer = A("A gente tá ferrado", "9:50")
S(t_fer, "sadtrombone.swf.mp3", -18.0, why="ferrado")
t_amo = A("Meu amorzinho", "9:52", spk="C")
M(t_amo, "AMOR", "Love Dust", 0.0, -26, "personagem apaixonada (romance cômico)")
P(t_amo, "Pink Glow", end=t_amo + 2.0, why="amorzinho"); Z(t_amo, 125, 1.0, FACE, why="amorzinho")
t_xox = A("Xoxozinho, eu tô aqui", "9:54", spk="C")
punch(t_xox, 245, snd="anime-wow-sound-effect (1).mp3", g=-17.0, why="xoxozinho")
t_esc2 = A("se Nós esconde", "9:57")
S(t_esc2, "why-are-you-running-sound-effect-hd_2yraBjq.mp3", -14.0, why="se esconde")
t_bal = A("tô parecendo um balão", "10:04")
punch(t_bal, 240, snd="cartoon-boing.mp3", g=-2.3, why="balão")
t_lin = A("você fica linda de qualquer jeito", "10:06", spk="C")
P(t_lin, "Pink Glow", end=t_lin + 1.8, why="linda"); S(t_lin, "anime-shine-sound-2.mp3", -12.0, why="linda")
t_pq2 = A("parque aquático Que tem muita água", "10:10", spk="C")
item(t_pq2, FACE, 140, "parque aquático")
t_col2 = A("me carregar o colo", "10:34")
punch(t_col2, 240, why="carregar no colo")
t_brp = A("esse parque aquático é do Burucutu", "10:38", spk="C")
vilao(t_brp, "o parque é do Brucutu")
M(t_brp, "TENSAS", "Make No Mistakes", 0.0, -26, "parque do vilão")
t_nha = A("Nha, nha, nha", "10:48", spk="C")
S(t_nha, "clown-horn-short.mp3", -19.8, why="deboche nha nha")

# 10:50–11:44  PARQUE DE FACHADA / LOJA 3
t_ent2 = A("Parece só que a entrada é", "10:57")
M(A("eu vou ficar gigante", "10:50"), "MISTERIO", "Sneaky Town", 0.0, -27, "no parque do Brucutu")
t_pp = A("Que poça d'água, parceiro", "11:05", spk="C")
deboche(t_pp, A("tu quer ficar bebendo poça d'água", "11:07", spk="C", end=True), "parque aquático e bebe poça?")
t_fach = A("é de fachada", "11:13")
punch(t_fach, 240, snd="bruh-sound-effect-1.mp3", g=-18.0, why="de fachada")
t_l3 = A("itens do nível 3 foram desbloqueados", "11:24")
M(A("perder tempo vou logo", "11:22"), "NUEVAS 2K24", "Dine-o-Matic", 0.0, -26, "loja nível 3")
nivel(t_l3, "nível 3")
t_cap = A("capacete com O calha", "11:27")
item(t_cap, HOT, 300, "capacete com calha")
t_gc = A("guarda-chuva invertido o funil gigante", "11:28")
S(t_gc, "mc-note-pling.mp3", -6.0, why="itens")
t_fon = A("pegar a água da fonte", "11:37", spk="C")
punch(t_fon, 235, why="água da fonte")
t_esp = A("sou esperto", "11:43", spk="C")
S(t_esp, "original-sheesh.mp3", -16.0, why="esperto")

# 11:44–12:41  PARQUE: NOVOS ITENS / TIME-LAPSE / 2,5 %
t_per = A("perfeito. Agora vamos voltar", "11:45")
t_gc2 = A("guarda-chuva isso", "11:57")
M(A("Olha isso, galera", "11:58"), "NUEVAS 2K24", "Speed Devil", 0.0, -26, "sugando rápido")
P(A("Olha isso, galera", "11:58"), "Fullscreen Shake - Low Fast", end=A("Olha isso, galera", "11:58") + 2.0, why="sugando")
S(A("Olha isso, galera", "11:58"), "mc-random-splash.mp3", -6.0, why="sugando")
t_bo = A("se eu colocar a boia aqui ainda", "12:03")
item(t_bo, HOT, 260, "boia")
t_din = A("vai dar muito dinheiro", "12:15")
S(t_din, "tadaa.mp3", -12.0, why="dinheiro")
# TIME-LAPSE 1 (vaga 738,70–744,76: ele pôs um trecho provisório; nota 'time lapse editor' no bruto ~1107)
overlays.append({"kind": "timelapse", "src": [1104.05, 1161.29], "t": 738.70, "dur": 6.06, "v": 2, "why": "TIME-LAPSE: sugando a piscina (nota 'time lapse editor')"})
S(738.70 - 0.3, "19--Whoosh 39.wav", -3.0, why="entra o time-lapse"); S(744.76 - 0.05, "mc-random-levelup.mp3", -8.0, why="sai do time-lapse")
mutes.append({"track": 1, "a": 738.6, "b": 744.7, "why": "call sob o time-lapse (ele já tinha desabilitado)"})
t_sug = A("sugamos toda a", "12:26")
compra(t_sug)
t_tam2 = A("olha o tamanho que a gente", "12:27")
punch(t_tam2, 240, snd="cartoon-boing.mp3", g=-2.3, why="tamanho")
t_25p = A("consumiu 2,5% Do mundo", "12:37", spk="C")
ruim(t_25p, "só 2,5% do mundo")
MOFF(t_25p, "punchline")
t_np = A("Mas não tem problema não", "12:41")
M(t_np, "VLOGS", "Can_t Run", 0.0, -26, "esperança: cachoeiras")
t_cach = A("já liberou as cachoeiras", "12:44")
nivel(t_cach, "cachoeiras liberadas")
t_fg = A("Dá pra desbloquear o funil gigante", "12:48")
item(t_fg, HOT, 280, "funil gigante")

# 12:57–14:15  CACHOEIRA / BRUCUTU BOMBA D'ÁGUA
t_che = A("chegamos Olha galera só o tamanho dessa cachoeira", "13:01")
M(t_che, "EPICAS", "Expedition 13", 0.0, -26, "cachoeira!")
P(t_che, "White Flash B", why="cachoeira"); Z(t_che, 125, 1.5, FACE, why="tamanho da cachoeira")
S(t_che, "19--Whoosh 39.wav", -3.0, why="cachoeira")
t_fun = A("testar logo o funil gigante", "13:04")
S(t_fun + 1.0, "mc-random-splash.mp3", -6.0, why="funil")
t_acc = A("está acelerando", "13:18", spk="C")
NOP(t_acc, "Fullscreen Shake - Mid Fast", end=t_acc + 1.5, why="acelerando")
t_115 = A("115 mil litros", "13:29")
hud(t_115, why="115 mil litros"); S(t_115 + 0.3, "original-sheesh.mp3", -16.0, why="115 mil")
t_men = A("Os mentirosos da piscina", "13:33", spk="C")
vilao(t_men, "mentirosos da piscina")
M(A("Olha o que eu tô vendo aqui", "13:31", spk="C"), "TENSAS", "Weapon of Choice", 0.0, -26, "Brucutu volta")
t_pist = A("pistolinha de água", "13:42")
punch(t_pist, 240, why="pistolinha")
t_bd = A("bomba d'água", "13:48", spk="C")
P(t_bd, "Impact Shake High", why="bomba d'água"); S(t_bd, "bass-impact.mp3", -2.0, why="bomba"); S(t_bd, "impact_water.mp3", -10.5, why="bomba")
Z(t_bd, 150, 0.6, FACE, why="bomba d'água")
t_bd2 = A("Bomba d'água?", "13:49")
punch(t_bd2, 250, why="Bomba d'água?!")
t_para = A("Para, Brucutu, para, para, para", "13:53")
NOP(t_para, "Angry Shake Mid", end=t_para + 1.6, why="para!")
t_100p = A("de novo 100% de água", "14:01")
ruim(t_100p, "voltou a 100% de água")
MOFF(t_100p, "punchline")
t_esm = A("voltei a ser o próprio Esmagro", "14:03")
punch(t_esm, 240, snd="spongebob-fail.mp3", g=-17.0, why="voltou a ser magro")
t_mp = A("meter o pé daqui", "14:07")
M(t_mp - 0.3, "TROLL", "Swagger Stagger", 0.0, -26, "fuga")

# 14:15–15:07  ENGANAR O BRUCUTU / TIME-LAPSE 2
t_eng = A("Isso de fugir era só pra poder enganar o Brukutu", "14:16")
M(t_eng, "MISTERIO", "Detective Gang", 0.0, -27, "plano esperto")
Z(t_eng, 125, 1.4, FACE, why="plano")
S(A("enganar o Brukutu", "14:17"), "deg-deg-sussy.mp3", -14.0, why="esperto")
t_ind = A("tá indo embora, galera", "14:31")
S(t_ind, "mc-random-door_open.mp3", -6.0, why="foi embora")
t_150 = A("150 mil litros de água", "14:40")
hud(t_150, why="precisa de 150 mil")
t_tib = A("Tibum", "14:47")
S(t_tib, "mc-random-splash.mp3", -4.0, cut=True, why="tibum"); P(t_tib, "Impact Shake Low", why="tibum")
t_trab = A("Tirando água até da pedra", "14:59", spk="C")
punch(t_trab, 240, why="tirando água da pedra")
overlays.append({"kind": "timelapse", "src": [1438.70, 1690.69], "t": 902.25, "dur": 5.47, "v": 2, "why": "TIME-LAPSE: sugando a cachoeira (vaga que ele deixou)"})
S(902.25 - 0.3, "19--Whoosh 39.wav", -3.0, why="entra o time-lapse"); S(907.72 - 0.05, "mc-random-levelup.mp3", -8.0, why="sai do time-lapse")
mutes.append({"track": 1, "a": 902.2, "b": 907.7, "why": "call sob o time-lapse"})

# 15:07–16:43  GIGANTES / LOJA / RIOS
t_sug2 = A("gente sugou toda a cachoeira", "15:08")
M(t_sug2 - 0.3, "TROLL", "Human Cannon", 0.0, -26, "gigantes cômicos")
compra(t_sug2)
t_3b = A("Três blocos de altura", "15:11")
punch(t_3b, 240, snd="cartoon-boing.mp3", g=-2.3, why="3 blocos de altura")
t_oc = A("bochecha parece meu óculos", "15:17", spk="C")
STR(t_oc, t_oc + 1.3, 300, 220, why="bochecha = óculos (distorção)"); S(t_oc, "comedy_pop_finger_in_mouth_001.mp3", -10.0, why="bochecha")
t_lj = A("vamos na loja", "15:23")
t_3i = A("comprar três itens novos", "15:30")
M(A("Mas pelo menos agora", "15:29"), "NUEVAS 2K24", "Megapixel", 0.0, -26, "loja: robô/portal/barragem")
loja(t_3i, "3 itens novos")
t_rb = A("Robô, mergulhador", "15:33")
item(t_rb, HOT, 280, "robô mergulhador")
t_vdd = A("beber água de verdade", "15:39")
Z(t_vdd, 125, 0.8, FACE, why="de verdade")
t_vam = A("Vamos!", "15:41", spk="C")
M(t_vam, "NUEVAS 2K24", "Play Me Like That Video Game", 0.0, -26, "testando nos rios")
t_mer = A("robô mergulha, robô mergulha", "15:47")
S(t_mer, "mc-random-splash.mp3", -6.0, why="robô")
t_nqm = A("Ele não quer mergulhar não", "15:51")
punch(t_nqm, 240, snd="bruh-sound-effect-1.mp3", g=-18.0, why="não quer mergulhar")
t_asp = A("tá funcionando, ele tá aspirando", "15:59")
Z(t_asp, 140, 0.8, FACE, why="funcionou"); S(t_asp, "tadaa.mp3", -12.0, why="funcionou")
t_vel = A("olha a velocidade", "16:11", spk="C")
NOP(t_vel, "Fullscreen Shake - Mid Fast", end=t_vel + 1.5, why="velocidade")
t_bel = A("rio já foi pro belé, Léo", "16:19")
S(t_bel, "cartoon-slide.mp3", -10.0, why="beleléu"); punch(t_bel, 235, why="beleléu")
t_rob2 = A("Cadê meu robô", "16:24")
S(t_rob2, "hm.mp3", -14.0, why="cadê o robô")
t_tm = A("Daqui a pouco eu vou estar do tamanho do mundo", "16:38")
Z(t_tm, 130, 1.3, FACE, why="tamanho do mundo")
t_20p = A("mais de 20% da água do mundo", "16:46")
hud(t_20p, why="20% do mundo")

# 16:43–17:41  1,5 MILHÃO / NÍVEIS 5-6 / LAGO
t_4b = A("tô do tamanho de 4 blocos", "16:59")
punch(t_4b, 238, why="4 blocos")
t_15m = A("1 milhão e meio de água", "17:01")
hud(t_15m, why="1,5 milhão")
t_n5 = A("liberou o próximo nível", "17:06", spk="C")
nivel(t_n5, "próximo nível")
t_nv5 = A("nível 5", "17:12")
S(t_nv5, "mc-random-levelup.mp3", -8.0, why="nível 5")
t_rd = A("redemoinho artificial o buraco negro na boca", "17:17")
loja(t_rd, "itens finais")
M(t_rd, "2K25", "Last Level Pt. 1", 0.0, -26, "níveis finais")
t_cgg = A("Vou pegar o canudo gigante", "17:22")
item(t_cgg, HOT, 300, "canudo gigante")
t_cnd = A("Canudão", "17:24", spk="C")
punch(t_cnd, 245, snd="vine-boom.mp3", g=-7.1, why="Canudão!")
t_lag = A("é sugar esse lago inteiro", "17:31")
M(A("Agora vambora, galera", "17:29"), "EPICAS", "Three Zillion Sharks", 0.0, -26, "sugar o lago")
t_mq = A("Meu Deus, que isso", "17:34")
P(t_mq, "White Flash B", why="canudo gigante sugando"); Z(t_mq, 135, 1.0, FACE, why="que isso!")
S(t_mq, "bass-impact.mp3", -4.0, why="canudo gigante")
t_mi = A("Tá sugando o mar inteiro", "17:35")
NOP(t_mi, "Fullscreen Shake - High Fast", end=t_mi + 1.6, why="sugando o mar")

# 17:41–18:45  DRAGA / 50-70 % / BRUCUTU DESISTE E MORRE
t_dg = A("testar minha draga sugadora", "17:49")
item(t_dg, HOT, 280, "draga sugadora")
t_2ao = A("eu suco os dois ao mesmo tempo", "18:01")
S(t_2ao, "original-sheesh.mp3", -16.0, why="os dois ao mesmo tempo")
t_50 = A("50% da água", "18:06", spk="C")
hud(t_50, why="50%")
t_70 = A("Já foi 70% da", "18:15")
hud(t_70, why="70%")
t_oqv = A("O que vocês estão fazendo", "18:18", spk="C")
vilao(t_oqv, "Brucutu chega de novo")
M(t_oqv, "2K25", "That Thing Behind Us", 30.0, -26, "vilão (2ª vez)")
t_qui = A("Fica quieto, Naniaco", "18:25", spk="C")
M(A("Às vezes a gente tem que admitir", "18:26", spk="C"), "TRISTE", "Sadness", 0.0, -26, "Brucutu desiste (drama cômico)")
Z(A("coisas que não podem ser salvas", "18:28", spk="C"), 130, 2.0, FACE, why="drama")
t_des = A("desisto", "18:31", spk="C")
S(t_des, "sadtrombone.swf.mp3", -18.0, why="desisto")
t_sau = A("Usa como é que é saudável", "18:33")
punch(t_sau, 238, why="hidratar seu corpo")
t_bru2 = A("Suga água do mundo", "18:36")
S(t_bru2, "minecraft-drinking-sound-effect.mp3", -4.6, why="Brucutu bebe")
t_mor = A("ele morreu", "18:45")
MOFF(t_mor - 0.6, "punchline: Brucutu morreu")
overlays.append({"kind": "sticker", "file": os.path.join(PNG, "wasted_overlay.png"), "t": t_mor, "dur": 1.6, "v": 2, "why": "WASTED (ele morreu)"})
S(t_mor, "gta-v-wasted-death-sound.mp3", -10.0, why="wasted")
P(t_mor, "VHS", end=t_mor + 1.6, why="wasted")

# 18:45–19:43  OCEANO / CLÍMAX / FIM
t_vl = A("vamos voltar loja", "18:46")
M(A("Bom, de qualquer forma", "18:45"), "2K25", "GO", 0.0, -26, "loja final")
t_rd2 = A("Redemon artificial", "18:49")
item(t_rd2, HOT, 280, "redemoinho artificial"); compra(t_rd2 + 0.6)
t_bnb = A("E o buraco negro da boca", "18:50")
compra(t_bnb + 0.4)
t_oce = A("Vamos direto pro peróceano", "18:55")
M(t_oce, "LEGENDARIAS", "The Triumph", 0.0, -25, "CLÍMAX: oceano")
P(t_oce, "White Flash B", why="oceano")
t_prep = A("Senhores, vocês estão preparados", "18:59")
Z(t_prep, 130, 1.2, FACE, why="preparados?"); S(t_prep, "loud-dramatic-stinger.mp3", -16.0, why="preparados")
t_red = A("redemoinho artificial", "19:03")
S(t_red + 1.0, "mc-portal-travel.mp3", -10.0, why="redemoinho")
t_toma = A("Vou colocar ele bem aqui. Toma", "19:05")
NOP(t_toma + 1.2, "Fullscreen Shake - High Fast", end=t_toma + 3.0, why="redemoinho sugando")
t_bnb2 = A("quero usar o buraco negro na Pronto, boca", "19:13")
P(t_bnb2, "Red Flash B", why="buraco negro"); S(t_bnb2, "mc-mob-wither-spawn.mp3", -14.0, why="buraco negro")
t_oc2 = A("oceano inteiro vai ser sugado", "19:15")
Z(t_oc2, 140, 1.0, FACE, why="oceano sugado"); NOP(t_oc2, "Fullscreen Shake - High Slow", end=t_oc2 + 2.5, why="oceano sugado")
t_exp = A("eu tô explodindo", "19:22")
P(t_exp, "Impact Shake High", why="explodindo"); S(t_exp, "mc-random-explode1.mp3", -10.0, why="explodindo")
t_mm = A("tô ficando maior que o mundo", "19:24")
Z(t_mm, 150, 1.4, FACE, why="maior que o mundo")
t_fud = A("gente tá se fudindo", "19:29", spk="C")
bleeps.append({"t": A("fudindo", "19:30", spk="C") - 0.03, "end": A("fudindo", "19:30", spk="C", end=True) + 0.03, "why": "palavrão da call (canal infantil)"})
t_tod = A("A gente bebeu toda a água do mundo", "19:32")
P(t_tod, "White Flash B", why="conseguiu"); S(t_tod, "mc-ui-toast-challenge_complete.mp3", -4.0, why="conquista"); S(t_tod + 0.2, "mc-random-levelup.mp3", -6.0, why="conquista")
t_pla = A("virou planeta de", "19:36")
punch(t_pla, 230, snd="vine-boom.mp3", g=-7.1, why="viramos um planeta de água")
M(A("Agora a gente vai ter que ficar assim", "19:39"), "2K25", "Cheer Up", 0.0, -26, "final")
t_tch = A("Tchau", "19:42")
S(t_tch, "mc-random-pop.mp3", -6.0, why="tchau")

# =====================================================================================
music.sort(key=lambda m: m["t"])
_fix = []
for i, m in enumerate(music):                     # referência: a música cala 0,8–2,2 s na piada e VOLTA
    if m["file"] is None and i > 0 and i + 1 < len(music) and music[i + 1]["t"] - m["t"] > 2.0:
        if music[i + 1]["t"] - m["t"] <= 4.5:      # a próxima faixa entra mais cedo (1,5 s após a pausa)
            music[i + 1]["t"] = round(m["t"] + 1.5, 3); continue
        pv = next(x for x in reversed(music[:i]) if x["file"])
        _fix.append({"t": round(m["t"] + 1.5, 3), "file": pv["file"], "src": round(pv["src"] + m["t"] + 1.5 - pv["t"], 3), "g": pv["g"], "why": "volta após a pausa"})
music += _fix; music.sort(key=lambda m: m["t"])
plan = {"music": music, "zooms": sorted(zooms, key=lambda z: z["t"]), "stretch": stretch, "presets": sorted(presets, key=lambda p: p["t"]),
        "sfx": sorted(sfx, key=lambda s: s["t"]), "reveals": reveals, "overlays": overlays, "mutes": mutes, "bleeps": bleeps,
        "marks": marks, "end": END}
json.dump(plan, open("plan.json", "w", encoding="utf8"), ensure_ascii=False, indent=1)
print("música %d | zooms %d | stretch %d | presets %d | sfx %d | reveals %d | overlays %d | mutes %d | bleeps %d" % (
    len(music), len(zooms), len(stretch), len(presets), len(sfx), len(reveals), len(overlays), len(mutes), len(bleeps)))
