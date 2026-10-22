"""Ganho de clipe dos SFX — ESTÁTICO (sem keyframes), calibrado pelo que o Matheus deixou na v14 editada por ele (15/10/2026).

História (3 rodadas de feedback):
  v13: normalizava SFX p/ ~-27 LUFS -> "inaudíveis, a faixa dos -22 dB é a média".
  v14b: subi tudo por RMS (tiers -15..-24 dBFS) com teto de pico -2.5 -> passou do ponto: ao editar, ele DESCEU a maioria 6-17 dB (spongebob -13, clown -15, bruh -13,
        scratch -15, suspense -14, anime-wow -12, anvil -10, bamboo -9, drink -6). Deixou como estavam só os impactos curtos (vine-boom, burp, orbs do XP) e quase igual o nintendo-error.
  Resultado dele (render da v14 editada): pico do SFX = pico da fala +0...+3 dB (mediana +2,5; impactos +3...+6), RMS final dos SFX -21...-36 dBFS (a fala fica em ~-20).
  Regra de ouro: o SFX tempera, não compete — ouvir/perceber, mas nunca por cima da voz. E **NUNCA keyframe em SFX**: ganho fixo no clipe (setValue), sem fade/envelope.

Uso:  python sfx_levels.py <plan3.json>   -> p/ cada SFX do plano: ganho de clipe, pico e RMS finais previstos (de onde veio: plano / tabela dele / regra)
      from sfx_levels import gain_for     -> usado pelo build_edit3 (stage b5_sfx)
Prioridade do ganho: x['gain_db'] (explícito) > x['rms_db']+peak_cap (legado) > GAIN_DB[arquivo] (valores dele) > regra por duração (arquivo novo).
"""
import sys, os, json

# ganho de clipe em dB do Premiere (0 dB = sem alteração; 0.17783 linear = 0 dB na convenção do builder) que ELE deixou/escolheu — por arquivo
GAIN_DB = [
    ("anime-shine-sound-2", -6.9),            # abertura (sting) — o shimmer fica ATRÁS da música
    ("anime-shine-sound-effect_QP4", -7.3),   # brilho de revelação (push-in + Brilho cintilante)
    ("anime-wow-sound-effect (1)", -15.5),    # item citado: -10.4 (r1) -> -17.0 (r2, 16/10) -> -15…-19, mediana -15,5 (r3, 20/10)
    ("anime-wow-sound-effect", -15.5),
    ("bamboo-hit", -7.5),                     # bonk: -10.7 (15/10); no vídeo inteiro (20/10) -3,2…-9,5 (mediana -7,5); com record scratch fica -6…-9
    ("record-scratch", -16.0),                # -12,4…-17,2 (20/10)
    ("sudden-suspense", -11.0),               # 20/10: ele SUBIU p/ -11 (o -22,3 de 15/10 ficava inaudível)
    ("nintendo-switch", -3.5),                # bipe de erro curtinho (0,27 s): ficou quase como o meu (-2.3) — bipe curto pode ficar alto
    ("spongebob-fail", -15.0),                # -15.3 na pergunta ("não consegue beber nada?") / -20.0 na punchline ("0,1% de toda a água")
    ("mc-random-drink", -5.5),
    ("cartoon-boing", -2.3),
    ("clown-horn", -19.8),
    ("anvil", -8.0),                          # -10,8 (15/10) -> -7…-8,7 (20/10)
    ("wrong_5", -8.0),                         # com bigorna; -14,8 quando vem junto do zoom 601 % (o visual já pesa)
    ("bruh", -10.6),                           # 20/10: ele SUBIU p/ -9,8…-10,7 (o -18 de 15/10 sumia)
    ("perfect-fart", -10.5),                  # -8.6 / -12.3
    ("vine-boom", -7.1),                      # meu valor, ele manteve
    ("mc-random-burp", 0.8),                  # meu valor, ele manteve
    # --- rodada 2 (16/10): pacote de SFX do B-roll cinemático (arquivos que ELE trouxe; ver references/feedback-timeline-dele-16out.md) ---
    ("19--Whoosh", 0.0),                      # whoosh no início do B-roll (pré-roll ~0,4 s), 0 dB
    ("minecraft_click", 10.0),                # clique de UI do MC (0,8 s): 2 seguidos na abertura, +10 dB (curto e seco, pode ficar alto)
    ("bass-impact", 0.0),                     # impacto grave na revelação do B-roll
    ("impact_water", -10.5),                  # splash (Roblox) junto do bass-impact
    ("minecraft-drinking", -4.6),             # gole longo sobre o B-roll do canudo
    ("fortnite-shield-potion", -4.4),         # poção/beber sustentado (3,8 s) sob o B-roll de abertura
    ("mc-xp-orb", 7.0),                       # meu valor, ele manteve (fade-in de 10 ms JÁ EMBUTIDO no mp3 — sem keyframe, o clique de 1 ms não estoura)
    # --- rodada 3 (20/10, "Bebi toda a água do mundo" inteiro): valores que ELE deixou (references/feedback-timeline-dele-20out.md) ---
    ("mc-ui-toast-challenge", -12.0),         # compra/conquista: -11…-14 (eu punha -6; ele baixou TODOS)
    ("mc-random-splash", -12.0),              # água entrando/sugando: -12 (tibum de verdade -6,5)
    ("mc-random-levelup", -5.5),              # nível/loja liberada -5…-7; "sai do time-lapse" -14,5…-17 (sob a música)
    ("mc-random-orb", 4.2),                   # contador/litros: +3,3…+6,6 (mediana +4,2)
    ("mc-note-pling", -4.6),
    ("mc-random-door_open", -4.3),
    ("mc-random-explode1", -6.7),
    ("mc-random-pop", -3.6),
    ("mc-portal-travel", -10.1),
    ("mc-mob-wither-spawn", -12.6),
    ("metal-gear-alert", -7.8),               # ameaça do vilão (ele SUBIU de -10,8)
    ("taco-bell-bong", -9.5),                 # "esquece essa porcaria", "cloro": -8,3…-10,8
    ("hmmmm", -10.0), ("hm.mp3", -12.1),      # desconfiança (Brucutu/"cadê o robô")
    ("cartoon-slide", -8.8), ("comedy_pop_finger", -9.3), ("sadtrombone", -16.2),
    ("gta-v-wasted", -7.1),                   # morte cômica (SEM o sticker PNG: ele tirou o WASTED.png)
    ("five-nights-at-freddys", -23.0),        # susto cômico: bem baixo
    ("original-sheesh", -14.7),               # ele tirou 4 de 5; só no número grande ("115 mil")
    ("why-are-you-running", -13.0),
    # arquivos NOVOS que ele trouxe (copiados p/ library/sfx com o nome original)
    ("among-us-role-reveal", -3.0),           # ENTRADA/RETORNO DO VILÃO (substituiu TODOS os dun-dun-dun): 0 / -6,8
    ("alert-sound_wTmioMp", -10.5),           # alerta: -9,3 / -11,9
    ("danger-alarm-sound-effect-meme", -17.6),# alarme longo (vilão chegando de novo) — o arquivo é MUITO alto (-1,9 LUFS)
    ("suspense-1_bLEXV6f", -9.8),             # vilão à vista ("Rapaziada, aquele deve ser...")
    ("cinematic-boom", -5.6),                 # revelação do vilão (pacote: boom + cartoon poke + deep impact)
    ("Cartoon poke", -2.0),                   # 0 / -4,0
    ("deep impact", -1.6),
    ("zoom-impacto", -9.8),                   # pacote do número grande (zoom 359 % no contador): zoom-impacto + impacto.wav 0 dB
    ("impacto.wav", 0.0),
    ("2 - whoosh swoosh - long", -8.5),       # whoosh longo de entrada/saída da inserção (promo)
    ("one-piece-corneta", -3.1),              # deboche romântico ("quer que eu te carregue no colo?")
    ("one-piece-toing", -12.1),
    ("guitar-riff-meme", -17.1),              # item épico apresentado ("É o Canudão!")
]

# arquivo NOVO (sem valor dele): alvo de RMS ativo final por duração do trecho usado + teto de pico
RMS_SHORT = -25.0     # impacto/gag curto (<= 0.9 s): bonk, boing, erro, gole, arroto
RMS_LONG = -31.0      # som longo/sustentado (> 0.9 s): fail, stinger, alerta, record scratch — ocupa a banda da fala por mais tempo
PEAK_CAP = -5.0


def table_gain(fn):
    for k, v in GAIN_DB:
        if k in fn: return v
    return None


def gain_for(fn, pk, rm, d, x=None):
    """ganho (dB de clipe) + de onde veio. pk/rm = pico e RMS ativo do trecho usado (sfx_levels do builder), d = duração usada."""
    x = x or {}
    if "gain_db" in x: return x["gain_db"], "plano(gain_db)"
    if "rms_db" in x: return min(x["rms_db"] - rm, x.get("peak_cap", PEAK_CAP) - pk), "plano(rms_db)"
    t = table_gain(os.path.basename(fn))
    if t is not None: return t, "tabela dele"
    return min((RMS_SHORT if d <= 0.9 else RMS_LONG) - rm, PEAK_CAP - pk), "regra (arquivo novo)"


def main():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "build_edit3.py"), encoding="utf8").read().replace("\nmain()\n", "\n")
    ns = {"__name__": "b3", "__file__": os.path.join(os.path.dirname(os.path.abspath(__file__)), "build_edit3.py")}
    sys.argv = ["x"]
    exec(compile(src, "b3", "exec"), ns)
    plan = json.load(open(sys.argv_plan, encoding="utf8"))
    seen = set()
    for x in plan["sfx"]:
        nm = os.path.basename(x["file"]); off = x.get("src_off", 0.0)
        idx = json.load(open(os.path.join(os.path.dirname(x["file"]), "index.json"), encoding="utf8"))
        d = min(x.get("dur", 2.5), idx[nm]["dur"] - off)
        key = (nm, off, round(d, 2))
        if key in seen: continue
        seen.add(key)
        pk, rm = ns["sfx_levels"](x["file"], off, d)
        g, src_ = gain_for(nm, pk, rm, d, x)
        print("%-40s gain %+5.1f dB -> pico %5.1f  rms %5.1f  [%s]%s" % (nm[:40], g, pk + g, rm + g, src_, "  !! pico > -1" if pk + g > -1 else ""))


if __name__ == "__main__":
    sys.argv_plan = sys.argv[1]
    main()
