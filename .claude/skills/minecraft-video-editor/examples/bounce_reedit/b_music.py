"""Música por CLIMA (Epidemic local) — plano em tempo ANTIGO (seções do roteiro) -> tempo NOVO pelos cortes. Música em A5 (índice 4); alvo de LUFS do trecho no render."""
import glob, json, os, re, subprocess, sys
from lib import *
ROOT = r"D:\Users\PREDATOR\Documents\Epidemic 2K23 (Pasta de músicas)"
TARGET = float(os.environ.get("MUS_TARGET", "-32"))
COMP = 0.0
def _mp(path):
    rem = sorted((a, b) for a, b, *_ in json.load(open(os.path.join(HERE, path), encoding="utf8")))
    def f(t):
        acc = 0
        for a, b in rem:
            if t >= b: acc += b - a
            elif t > a: acc += t - a; break
            else: break
        return t - acc
    return f
_n1, _n2, _n3 = _mp("remove.json"), _mp("remove2_ok.json"), _mp("remove3_ok.json")
def new(t): return _n3(_n2(_n1(t)))
SEC = [  # (ini_antigo, fim_antigo, prefixo, motivo) — UMA faixa nova a cada mudança de CENA/AMBIENTE/CLIMA (marcadores R005 = takes) e entrando no corte
    (0.0, 22.8, "MUY ANIMADAS/ES_Lifecrash", "intro enérgica (gancho)"),
    (22.8, 85.3, "TROLL/ES_Festive Riot", "o mundo ricocheteando: caos cômico"),
    (85.3, 109.7, "VLOGS/ES_You Seen My Coat", "vaca voando: curiosidade leve"),
    (109.7, 162.6, "TROLL/ES_Happy Shortcut", "gaiola + golem: travessura"),
    (162.6, 205.0, "NUEVAS 2K24/ES_Having Fun", "ovo/dragão/sapos"),
    (205.0, 250.3, "NUEVAS 2K24/ES_Babushka", "limite é distância + camelos"),
    (250.3, 272.2, "NUEVAS 2K24/ES_When the Cats Away", "montaria e ping pong (ainda superfície)"),
    (272.2, 312.7, "2K25/ES_That Thing Behind Us", "MUDOU O AMBIENTE: caverna controlada + Warden nasce (tensão)"),
    (312.7, 345.1, "TROLL/ES_The Olive Branch", "Warden gigante + zumbis patinando (deboche)"),
    (345.1, 403.0, "NUEVAS 2K24/ES_Pretend You", "miniatura / pequeno demais (cômico leve)"),
    (403.0, 422.7, "TROLL/ES_Steps in Time", "Warden arremessado, humilhado (cômico)"),
    (422.7, 455.0, "VLOGS/ES_Your Gain", "novo mod de XP: curiosidade"),
    (455.0, 505.0, "AVENTURAS/ES_The Proving", "piscina de XP: maravilha"),
    (505.0, 546.5, "TENSAS/ES_Desert Hurricanes", "lag: pânico cômico"),
    (546.5, 608.9, "MISTERIO/ES_Into the Wild", "chuva de XP: calma"),
    (608.9, 649.6, "EPICAS/ES_Expedition 13", "blocos e mar de XP: escalada"),
    (649.6, 681.9, "NUEVAS 2K24/ES_Choirs of War", "mais do que aguenta: clímax do lag"),
    (681.9, 697.3, "NUEVAS 2K24/ES_Can_t Dampen", "conquista: acabamos com o Minecraft"),
]
def pick(prefix):
    cat, pre = prefix.split("/")
    h = [f for f in glob.glob(os.path.join(ROOT, cat, pre + "*")) if f.lower().endswith(".mp3")]
    assert h, prefix
    return h[0]
def lufs(path, ss, dur):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-ss", str(ss), "-t", str(dur), "-i", path, "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True, encoding="utf8")
    m = re.findall(r"I:\s+(-?\d+\.\d+) LUFS", r.stderr); return float(m[-1]) if m else -14.0
def dur_of(path):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path], capture_output=True, text=True).stdout.strip())
joins = sorted(set(json.load(open(os.path.join(HERE, "joins3.json")))))
plan = []
for a, b, pre, why in SEC:
    a2, b2 = new(a), new(b)
    if plan:                                           # a faixa nova entra NO corte mais perto (<= 3 s)
        near = [c for c in joins if abs(c - a2) <= 3.0]
        if near: a2 = min(near, key=lambda c: abs(c - a2))
    f = pick(pre); D = dur_of(f)
    plan.append({"a": round(a2, 3), "b": round(b2, 3), "file": f, "prefix": pre, "why": why, "D": D})
for i in range(len(plan) - 1): plan[i]["b"] = plan[i + 1]["a"]
for x in plan:
    ln = x["b"] - x["a"]
    x["src_in"] = 0.0 if ln + 1 < x["D"] else 0.0
    if ln > x["D"] - 1: x["use"] = x["D"] - 1   # faixa curta: usa tudo e o resto fica mudo (raro)
    else: x["use"] = ln
    L = lufs(x["file"], x["src_in"], min(x["use"], 45))
    g_nom = TARGET - L
    x["lufs"] = round(L, 1); x["gdb"] = round(min(g_nom + COMP, 15.0), 2); x["g"] = 10 ** ((x["gdb"] - 15) / 20.0)
    x["name"] = os.path.basename(x["file"])
    print("%7.1f-%7.1f %-34s src %5.1f LUFS %5.1f clip %+5.1f  D=%.0f  %s" % (x["a"], x["b"], x["name"][:34], x["src_in"], L, x["gdb"], x["D"], x["why"]))
json.dump(plan, open(os.path.join(HERE, "plan_music.json"), "w", encoding="utf8"), ensure_ascii=False)
