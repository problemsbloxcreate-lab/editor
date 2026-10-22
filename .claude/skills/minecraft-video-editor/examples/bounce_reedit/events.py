"""Eventos de edição (SFX / zoom / presets) do "Vídeo 2 - Bounce" (Matteeoo + Pedro). Tempos = segundos da timeline ATUAL (não há cortes novos).
Cada evento: dica de tempo t + frase q + quem fala (M = Matteo/A1, P = Pedro/A2) para ancorar na PALAVRA pelo ASR; at: start | end | abs; off em s; snap=True encosta no corte (<= 0,9 s depois / 0,25 s antes)."""
import difflib, json, os, re, unicodedata

WORDS = {}


def norm(s):
    s = unicodedata.normalize("NFD", s.lower())
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in s if unicodedata.category(c) != "Mn"))


def load_words():
    for who, fn in (("M", "asr_mat.json"), ("P", "asr_ped.json")):
        W = json.load(open(os.path.join(r"D:\Pobrs\bounce", fn), encoding="utf8"))["words"]
        WORDS[who] = sorted((norm(w["w"]), w["s"], w["e"]) for w in W if norm(w["w"]))
        WORDS[who].sort(key=lambda w: w[1])


def find_phrase(t, q, who, win=(-4.0, 8.0)):
    toks = [norm(x) for x in q.split() if norm(x)]
    n = len(toks)
    W = [w for w in WORDS[who] if t + win[0] <= w[1] <= t + win[1]]
    best, bs = None, 0.0
    for i in range(len(W)):
        seq = W[i:i + n + 2]
        j, hit, first, last = 0, 0, None, None
        for w in seq:
            if j < n and difflib.SequenceMatcher(None, w[0], toks[j]).ratio() >= 0.75:
                if first is None: first = w
                last = w; hit += 1; j += 1
        sc = hit / n - 0.01 * abs(W[i][1] - t) / 10
        if hit >= max(1, round(n * 0.7)) and sc > bs:
            best, bs = (first[1], last[2]), sc
    return best


SFX = {   # chave -> (arquivo, opções)
    "vine": ("vine-boom.mp3", {}), "bonk": ("bamboo-hit-anime-bonk-sound.mp3", {}), "scratch": ("record-scratch-2.mp3", {}),
    "bruh": ("bruh-sound-effect-1.mp3", {}), "boing": ("cartoon-boing.mp3", {}), "sponge": ("spongebob-fail.mp3", {}),
    "wow": ("anime-wow-sound-effect (1).mp3", {}), "shine2": ("anime-shine-sound-2.mp3", {}), "shineq": ("anime-shine-sound-effect_QP4mAaX (1).mp3", {}),
    "nerr": ("nintendo-switch-error.mp3", {}), "anvil": ("mc-random-anvil_land.mp3", {}), "oof": ("sm64_mario_oof.mp3", {}), "hurt": ("mc-damage-hit1.mp3", {}),
    "tadaa": ("tadaa.mp3", {}), "levelup": ("mc-random-levelup.mp3", {}), "toast": ("mc-ui-toast-challenge_complete.mp3", {"dur": 4.0}),
    "cow": ("mc-mob-cow-say1.mp3", {}), "chicken": ("mc-mob-chicken-say1.mp3", {}), "zombie": ("mc-mob-zombie-say1.mp3", {}), "pig": ("mc-mob-pig-say1.mp3", {}),
    "sheep": ("mc-mob-sheep-say1.mp3", {}), "bat": ("mc-mob-bat-idle1.mp3", {}), "cat": ("mc-mob-cat-meow1.mp3", {}), "dragon": ("mc-mob-enderdragon-growl1.mp3", {"dur": 2.4}),
    "wither": ("mc-mob-wither-spawn.mp3", {"dur": 2.6}), "splash": ("mc-random-splash.mp3", {}), "glass": ("mc-random-glass1.mp3", {}), "break": ("mc-random-break.mp3", {}),
    "drown": ("mc-entity-player-hurt-drown1.mp3", {}), "pling": ("mc-note-pling.mp3", {}), "click": ("minecraft_click.mp3", {}),
    "pop": ("pop_7e9Is8L.mp3", {}), "slip": ("cartoonslip.mp3", {}), "slide": ("slide-whistle.mp3", {"dur": 1.2}), "dun": ("dun-dun-dun-sound-effect-brass_8nFBccR.mp3", {"dur": 2.2}),
    "impact": ("bass-impact.mp3", {"dur": 2.4}),
    "orb0": ("mc-xp-orb-p0.mp3", {}), "orb1": ("mc-xp-orb-p1.mp3", {}), "orb2": ("mc-xp-orb-p2.mp3", {}), "orb3": ("mc-xp-orb-p3.mp3", {}), "orb4": ("mc-xp-orb-p4.mp3", {}),
}

# (t_dica, frase, quem, âncora, off, sfx, motivo, snap)
S = [
    (2.4, "itemzinho", "M", "start", 0.0, "wow", "item citado ('esse itemzinho') = wow", False),
    (8.7, "pulei", "M", "start", 0.0, "boing", "pulou ao pegar a ovelha", True),
    (12.8, "ovelha", "P", "start", 0.0, "sheep", "a ovelha flutuando", True),
    (36.0, "ficou louco", "M", "end", 0.0, "vine", "o mundo já ficou louco (tese do item)", True),
    (44.0, "água", "M", "start", 0.0, "splash", "quicou até na água", True),
    (47.4, "desliguei", "M", "start", 0.0, "click", "desliga o mod (clique de UI)", True),
    (51.7, "Boing", "M", "start", 0.0, "boing", "Boing, boing, boing (callback falado)", False),
    (51.7, "Boing", "M", "start", 0.42, "pop", "boing #2", False),
    (51.7, "Boing", "M", "start", 0.84, "pop", "boing #3", False),
    (57.5, "bullying com os iron golem", "M", "end", 0.05, "bonk", "bullying com o iron golem", True),
    (63.0, "bugs de textura", "M", "start", 0.0, "nerr", "bug de textura", True),
    (76.2, "quicando aqui dentro", "P", "start", 0.0, "boing", "Pedro quicando dentro do cercado", True),
    (85.7, "essa vaca", "P", "start", 0.0, "cow", "o que aconteceu com essa vaca", True),
    (100.5, "vaca", "P", "start", 0.0, "slide", "a vaca tá voando", True),
    (101.9, "Sumiu", "P", "start", 0.0, "pop", "a vaca sumiu", True),
    (120.5, "pior tipo de ser humano", "M", "end", 0.05, "vine", "pior tipo de ser humano que existe (punchline)", True),
    (123.5, "atropelou", "P", "start", 0.0, "oof", "o golem atropelou o Pedro", True),
    (148.7, "vidros deformam", "M", "start", 0.0, "glass", "os vidros deformam", True),
    (163.0, "taquei o ovo", "M", "start", 0.3, "chicken", "taquei o ovo (ovo não quebra)", True),
    (166.0, "não quebrou", "M", "end", 0.05, "bonk", "o ovo não quebrou", True),
    (173.0, "ovo do dragão", "P", "start", 0.0, "dragon", "achou o ovo do dragão", True),
    (180.5, "dragão aqui", "P", "end", 0.05, "dun", "tem 10 dragões aqui", True),
    (187.0, "quebram os vidros", "M", "start", 0.45, "glass", "os dragões quebram os vidros", True),
    (198.9, None, None, "abs", 0.0, "pop", "taca o sapo", False),
    (210.28, None, None, "abs", 0.0, "orb0", "contagem das quicadas: 3", False),
    (212.36, None, None, "abs", 0.0, "orb1", "contagem: 5", False),
    (214.24, None, None, "abs", 0.0, "orb2", "contagem: 7", False),
    (215.76, None, None, "abs", 0.0, "orb4", "contagem: 9", False),
    (217.0, "não é limite de quicada", "M", "start", -0.15, "nerr", "hipótese errada: não é limite de quicada", True),
    (242.0, "infinito", "M", "end", 0.0, "vine", "sapo infinito (fim da frase)", True),
    (265.1, "doidão", "M", "start", 0.0, "boing", "o camelo doidão", True),
    (269.4, "pingue-pongue", "P", "start", 0.0, "pop", "ping pong com o camelo", True),
    (279.2, "começar a quicar", "M", "end", 0.05, "bonk", "controlado até você começar a quicar", True),
    (291.2, None, None, "abs", 0.0, "wither", "o Warden nasce (payoff do suspense)", False),
    (307.4, "Aperta K", "M", "start", 0.6, "click", "aperta K p/ desativar o mod", True),
    (316.4, "muito grande", "P", "start", 0.0, "impact", "o Warden ficou GIGANTE (revelação)", True),
    (332.2, "zumbi", "M", "start", 0.0, "zombie", "esse zumbi", True),
    (336.0, None, None, "abs", 0.0, "slip", "zumbis patinando", True),
    (346.5, "pequenininho", "P", "start", 0.0, "pop", "ele ficou pequenininho", True),
    (349.5, "filhotinho", "P", "start", 0.0, "cat", "filhotinho (fofura)", True),
    (362.9, "nem dá pra ver", "M", "end", 0.0, "pop", "minúsculo: nem dá pra ver", True),
    (368.3, "limite pras coisas", "M", "end", 0.05, "vine", "tem que ter limite pras coisas", True),
    (371.7, "lagou", "M", "end", 0.0, "nerr", "esse até lagou", True),
    (393.4, "preso", "M", "start", 0.0, "anvil", "extremamente preso", True),
    (395.2, "redemoinho", "M", "start", 0.0, "break", "redemoinho de blocos", True),
    (405.4, "subiu", "P", "start", 0.0, "orb0", "o Warden subiu (escalada): degrau 1", False),
    (407.3, "subindo", "P", "start", 0.0, "orb2", "escalada: degrau 2", False),
    (408.5, "escalou", "P", "start", 0.0, "orb4", "escalada: degrau 3", False),
    (410.8, "bola de bolinha", "M", "start", 0.0, "boing", "virou uma bola", True),
    (416.7, "vergonha", "M", "end", 0.0, "sponge", "olha que vergonha (humilhado)", True),
    (420.9, "morcego", "M", "start", 0.0, "bat", "não, morcego!", False),
    (422.7, None, None, "abs", 0.0, "levelup", "anuncia o mod de XP (virada de bloco)", True),
    (446.6, None, None, "abs", 0.0, "orb1", "lotado de XP", True),
    (466.4, "cristalzinho", "M", "end", 0.0, "pling", "XP parece um cristalzinho", True),
    (503.1, "piscinona", "M", "end", 0.0, "splash", "uma piscinona de XP", True),
    (509.2, "tá travando", "M", "start", 0.0, "nerr", "começa a travar (lag)", True),
    (525.0, "Lagou tudo", "P", "start", 0.0, "sponge", "lagou tudo", True),
    (528.6, "afogado", "M", "start", 0.0, "drown", "afogado em XP", True),
    (545.0, "Barra XP", "M", "start", 0.0, "orb3", "barra de XP", True),
    (552.0, "amassando", "P", "start", 0.0, "hurt", "o Warden amassando o Pedro", True),
    (558.9, "mergulhei", "P", "start", 0.0, "splash", "mergulhei no XP", True),
    (571.6, "chovendo", "P", "start", 0.0, "orb0", "chove XP", True),
    (587.8, "tem um limite", "M", "end", 0.05, "bonk", "tá, tem um limite", True),
    (593.2, "bonito", "P", "start", 0.0, "shine2", "que bonito (chuva de XP)", True),
    (630.0, "Ai", "M", "start", 0.0, "oof", "dano ('Ai!')", True),
    (634.0, "tankável", "M", "end", 0.05, "vine", "tá tankável (punchline)", True),
    (640.1, "mar de XP", "M", "start", 0.0, "levelup", "mar de XP", True),
    (652.2, "lagado", "M", "start", 0.0, "nerr", "tá muito lagado", True),
    (665.2, None, None, "abs", 0.0, "pig", "porco no XP", True),
    (684.5, "2 FPS", "M", "end", 0.0, "sponge", "até os porcos voando tá a 2 FPS", True),
    (690.4, "Nós conseguimos", "M", "start", 0.0, "toast", "conquista: acabar com o Minecraft (toast)", True),
]

# zooms que FICAM (ease-out): (t, frase, quem, âncora, off, ramp, s1 % sobre a base, hold, motivo)
Z = [
    (2.4, "itemzinho", "M", "start", -0.3, 1.0, 126, 2.4, "item citado: zoom que fica"),
    (173.0, "ovo do dragão", "P", "start", 0.0, 0.9, 118, 3.5, "achou o ovo do dragão"),
    (316.4, "muito grande", "P", "start", 0.0, 0.7, 124, 3.2, "Warden gigante"),
    (410.5, "bola de bolinha", "M", "start", 0.0, 3.0, 118, 7.0, "humilhado: push-in lento"),
    (640.1, "mar de XP", "M", "start", 0.0, 2.6, 118, 6.0, "mar de XP"),
    (690.4, "Nós conseguimos", "M", "start", 0.0, 2.0, 121, 4.5, "nós conseguimos acabar com o Minecraft"),
]

# presets BERSERKER (aplicados no clipe que COMEÇA em t): (t, frase, quem, âncora, off, nome, len, anchor, motivo)
P = [
    (509.2, "tá travando", "M", "start", 0.0, "Red Flash B", 2.0, "start", "lag começa"),
    (509.2, "tá travando", "M", "start", 0.0, "Impact Shake Mid", 2.0, "start", "lag começa"),
    (530.2, "lagado", "P", "start", 0.0, "VHS", 3.0, "start", "tudo lagado"),
    (652.2, "lagado", "M", "start", 0.0, "VHS", 2.5, "start", "tá muito lagado"),
    (684.0, "2 FPS", "M", "start", 0.0, "Impact Shake High", 2.5, "start", "2 FPS"),
    (316.4, "muito grande", "P", "start", 0.0, "White Flash B", 1.5, "start", "Warden gigante"),
    (336.5, "humilhados", "M", "start", 0.0, "VHS", 3.0, "start", "zumbis eternamente humilhados"),
    (416.7, "vergonha", "M", "end", -0.4, "VHS", 2.5, "start", "olha que vergonha"),
]


import numpy as np
sys_path = os.path.expanduser("~/.claude/skills/minecraft-video-editor/scripts")
import sys as _sys
_sys.path.insert(0, sys_path)
import sfx_timing as TM
RMS = {"M": np.load("D:/Pobrs/bounce/rms_mat.npy"), "P": np.load("D:/Pobrs/bounce/rms_ped.npy")}


def anchor(t, q, who, at, off):
    if q:
        r = find_phrase(t, q, who)
        if r is None: return None
        # o ASR atrasa o início (até 0,26 s no meio de frase) e estica o fim: refinar pela energia do mic ANTES de somar o offset
        raw = TM.refine_end(RMS[who], r[1]) if at == "end" else TM.refine_start(RMS[who], r[0])
        return raw + off
    return t + off


def resolve():
    load_words()
    out, bad = [], []
    for t, q, who, at, off, key, why, snap in S:
        a = anchor(t, q, who, at, off)
        if a is None:
            bad.append((t, q, who, why)); a = t + off
        f, opt = SFX[key]
        out.append({"t": round(a, 3), "key": key, "file": f, "opt": opt, "why": why, "snap": snap, "hint": t, "q": q})
    plan = {"zooms": [], "presets": [], "bad": []}
    for t, q, who, at, off, ramp, s1, hold, why in Z:
        a = anchor(t, q, who, at, off)
        if a is None: plan["bad"].append(("zoom", t, q, why)); a = t + off
        plan["zooms"].append({"t": round(a, 3), "ramp": ramp, "s1": s1, "hold": hold, "why": why})
    for t, q, who, at, off, name, ln, anc, why in P:
        a = anchor(t, q, who, at, off)
        if a is None: plan["bad"].append(("preset", t, q, why)); a = t + off
        plan["presets"].append({"name": name, "t": round(a, 3), "len": ln, "anchor": anc, "why": why})
    return out, bad, plan


if __name__ == "__main__":
    o, b, p = resolve()
    for x in sorted(o, key=lambda x: x["t"]): print("%8.2f (dica %6.1f) %-8s %s %s" % (x["t"], x["hint"], x["key"], "" if x["q"] is None or abs(x["t"] - x["hint"]) < 2.5 else "  <<< DESVIO %.1f" % (x["t"] - x["hint"]), x["why"]))
    print(len(o), "SFX; não resolvidas:", b)
    for z in p["zooms"]: print("zoom %.2f %.1fs->%d%% hold %.1f %s" % (z["t"], z["ramp"], z["s1"], z["hold"], z["why"]))
    for z in p["presets"]: print("preset %.2f %s %s" % (z["t"], z["name"], z["why"]))
    print(p["bad"])
