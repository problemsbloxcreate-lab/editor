"""Extrai sons REAIS do Minecraft (da instalação local do Modrinth App) para library/sfx/ como mp3 e registra no index.json.
Uso: python mc_sounds_extract.py            (extrai o conjunto curado abaixo)
     python mc_sounds_extract.py --ladder       (gera mc-xp-orb-p0..p4: orb com tom subindo, p/ 'takes futuros')
     python mc_sounds_extract.py random/orb random/levelup   (nomes extras relativos a minecraft/sounds/, sem .ogg)
Os nomes saem como mc-<pasta>-<arquivo>.mp3. Premiere NÃO importa .ogg -> sempre converte p/ mp3.
Fonte: %APPDATA%/ModrinthApp/meta/assets/indexes/<maior>.json + objects/<2 primeiros do hash>/<hash>.
"""
import os, sys, json, glob, subprocess, re

ASSETS = os.path.join(os.environ["APPDATA"], "ModrinthApp", "meta", "assets")
LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "library", "sfx")
# nome -> (tag, uso no vídeo)
CURATED = {
    "random/orb": ("xp", "XP do Minecraft: cada corte de 'takes futuros' / item coletado / achado"),
    "random/levelup": ("xp", "level up: conquista, upgrade comprado, ideia nova"),
    "ui/toast/challenge_complete": ("xp", "conquista desbloqueada (toast de advancement)"),
    "random/burp": ("piada", "arroto: depois de beber muita água"),
    "random/drink": ("piada", "gole: beber água"),
    "random/splash": ("piada", "splash na água"),
    "random/eat1": ("piada", "comer/mastigar"),
    "random/pop": ("piada", "pop de item"),
    "random/explode1": ("impacto", "explosão curta (TNT/creeper)"),
    "random/fuse": ("suspense", "pavio do TNT/creeper: vai dar ruim"),
    "random/anvil_land": ("impacto", "bigorna caindo: peso/derrota"),
    "random/anvil_use": ("impacto", "bigorna usando"),
    "random/anvil_break": ("impacto", "bigorna quebra"),
    "random/break": ("dano", "ferramenta quebrando"),
    "random/glass1": ("dano", "vidro quebrando"),
    "random/chestopen": ("revelacao", "baú abrindo: revelação de item"),
    "random/door_open": ("transicao", "porta abrindo"),
    "random/click": ("piada", "clique de UI"),
    "mob/villager/no1": ("piada", "Villager 'hmm' negativo: pergunta/dúvida/recusa"),
    "mob/villager/no2": ("piada", "Villager 'hmm' 2"),
    "mob/villager/yes1": ("piada", "Villager 'hurr' positivo"),
    "mob/villager/haggle1": ("piada", "Villager negociando"),
    "mob/villager/idle1": ("piada", "Villager idle: 'e aí?'"),
    "mob/villager/death": ("dano", "Villager morrendo"),
    "mob/villager/hit1": ("dano", "Villager apanhando"),
    "mob/creeper/say1": ("suspense", "creeper hiss: sssss"),
    "mob/creeper/death": ("dano", "creeper morrendo"),
    "mob/zombie/say1": ("susto", "zumbi grunhindo"),
    "mob/pig/say1": ("piada", "porquinho"),
    "mob/cow/say1": ("piada", "vaca"),
    "mob/sheep/say1": ("piada", "ovelha"),
    "mob/chicken/say1": ("piada", "galinha"),
    "mob/cat/meow1": ("piada", "gato miando"),
    "mob/ghast/scream1": ("susto", "ghast gritando"),
    "mob/ghast/moan1": ("suspense", "ghast gemendo"),
    "mob/enderdragon/growl1": ("susto", "dragão rugindo"),
    "mob/wither/spawn": ("susto", "wither spawn: chefão/problema gigante"),
    "mob/endermen/portal": ("transicao", "enderman teleporte"),
    "mob/bat/idle1": ("piada", "morcego"),
    "damage/hit1": ("dano", "'oof' clássico do Minecraft"),
    "damage/hit2": ("dano", "'oof' 2"),
    "damage/fallbig": ("dano", "queda grande"),
    "entity/player/hurt/drown1": ("dano", "afogando (engasgo): beber água demais"),
    "entity/player/hurt/fire_hurt1": ("dano", "pegando fogo"),
    "item/totem/use_totem": ("revelacao", "totem da imortalidade: salvo / virada"),
    "item/trident/thunder1": ("impacto", "trovão do tridente"),
    "note/bass": ("piada", "note block grave"),
    "note/bell": ("piada", "note block sino"),
    "note/pling": ("piada", "note block pling"),
    "note/harp": ("piada", "note block harpa"),
    "portal/travel": ("transicao", "portal do Nether"),
}


def newest_index():
    idx = sorted(glob.glob(os.path.join(ASSETS, "indexes", "*.json")), key=lambda p: -json.load(open(p, encoding="utf8")).__len__() if False else -os.path.getsize(p))
    return json.load(open(idx[0], encoding="utf8"))["objects"]


def ladder():
    """escada de XP: random/orb transposto +0,+2,+4,+5,+7 semitons (cada corte de 'takes futuros' sobe de tom, como juntar orbs)"""
    src = os.path.join(LIB, "mc-random-orb.mp3"); idxp = os.path.join(LIB, "index.json")
    index = json.load(open(idxp, encoding="utf8"))
    for n, st in enumerate((0, 2, 4, 5, 7)):
        out = "mc-xp-orb-p%d.mp3" % n; dst = os.path.join(LIB, out)
        f = 2 ** (st / 12.0)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-af", "asetrate=%d,aresample=44100,afade=t=in:d=0.010" % round(44100 * f), "-b:a", "192k", dst], check=True)
        d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", dst], capture_output=True, text=True).stdout.strip() or 0)
        index[out] = {"query": "minecraft xp orb +%d semitons" % st, "tag": "xp", "source": "derivado de random/orb", "use": "XP a cada corte dos takes futuros (degrau %d de 5)" % (n + 1), "lufs": -20.0, "dur": round(d, 2)}
        print("OK", out, round(d, 2))
    json.dump(index, open(idxp, "w", encoding="utf8"), ensure_ascii=False, indent=1)


def main():
    if "--ladder" in sys.argv: return ladder()
    objs = newest_index()
    wanted = {n: ("minecraft", "") for n in sys.argv[1:]} if len(sys.argv) > 1 else CURATED
    idxp = os.path.join(LIB, "index.json")
    index = json.load(open(idxp, encoding="utf8"))
    for name, (tag, use) in wanted.items():
        key = "minecraft/sounds/%s.ogg" % name
        if key not in objs:
            print("NAO ACHEI", key); continue
        h = objs[key]["hash"]; src = os.path.join(ASSETS, "objects", h[:2], h)
        out = "mc-" + name.replace("/", "-") + ".mp3"
        dst = os.path.join(LIB, out)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "ogg", "-i", src, "-ar", "44100", "-ac", "2", "-b:a", "192k", dst], check=True)
        # duração + LUFS
        d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", dst], capture_output=True, text=True).stdout.strip() or 0)
        p = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", dst, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True, encoding="utf8", errors="replace").stderr
        m = re.search(r"I:\s+(-?[\d.]+) LUFS", p[p.rfind("Summary"):]) if "Summary" in p else None
        index[out] = {"query": "minecraft " + name, "tag": tag, "source": "Minecraft assets (local) " + key, "use": use, "lufs": float(m.group(1)) if m else -30.0, "dur": round(d, 2)}
        print("OK", out, round(d, 2), index[out]["lufs"])
    json.dump(index, open(idxp, "w", encoding="utf8"), ensure_ascii=False, indent=1)


main()
