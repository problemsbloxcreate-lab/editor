"""Cinemáticas automáticas (regra 20): animações CineCam recriando o LUGAR do vídeo, inseridas como B-roll em V3.

Etapas (todas na pasta do job; tempos de TIMELINE do plan3):
  python cinematicas.py slots   <plan3.json> <t1.json> [t2.json] [--out DIR]      -> DIR/slots.json  (onde entram: densidade da regra 20)
  python cinematicas.py context <slots.json> <bruto.mp4> <plan3.json>               -> DIR/ctx_<id>.jpg + stats (lugar, hora, bioma) + turma.png
  (EU escrevo DIR/cards.json: uma ficha por slot — ver references/cinematicas.md e minecraft-cinematic/references/enquadramento.md)
  python cinematicas.py check   <cards.json>                                       -> valida enquadramento + itens SEM renderizar
  python cinematicas.py render  <cards.json> stills|draft|final [--only c01,c03]   -> renders numa sessão só + folhas p/ conferir
  python cinematicas.py insert  <plan3.json> <cards.json>                            -> brolls V3 + mutes A2/A3 + whoosh + marcadores

Densidade (pedido do Matheus, 21/10/2026): o 1º minuto é onde mais tem (3–5); depois 1 a cada 60–120 s (média ~90 s).
"""
import json, math, os, re, shutil, subprocess, sys, unicodedata
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
SK = os.path.dirname(HERE)
CINE = os.path.join(os.path.dirname(SK), "minecraft-cinematic", "scripts")
SFX = os.path.join(SK, "library", "sfx")


def norm(s):
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")


# palavras que pedem imagem (ação, lugar, coisa, exagero) — peso 2; reação/ênfase — peso 1
VISUAL = set(norm(w) for w in """beber bebe bebendo bebi bebeu agua poca pocas mar oceano rio lago piscina cachoeira canudo canudinho comer come comendo
comi pular pula pulando voar voa voando explodir explode explodiu tnt cair cai caiu queda correr corre correndo construir constroi construi casa
casinha vila aldeia castelo torre gigante enorme gigantesco mundo inteiro imagina imagine morrer morri morreu matar matou dragao monstro zumbi
creeper esqueleto lava fogo ouro diamante esmeralda ferro comprar compra comprei loja item espada picareta barriga encher cheio cheia seco seca secou
sumiu fugir foge esconder escondido achar achei encontrei descobrir misterio segredo armadilha preso nadar afundar crescer cresceu virar virou
transformar universo espaco lua sol deserto floresta neve caverna mina portal nether end bau tesouro chuva tempestade raio""".split())
EMPH = set(norm(w) for w in "caraca nossa olha olhem gente galera meu deus socorro uau incrivel impossivel absurdo todo toda tudo nunca".split())


def load_words(paths):
    W = []
    for k, p in enumerate(paths):
        d = json.load(open(p, encoding="utf8"))
        for w in d.get("words", []):
            W.append((float(w["s"]), float(w["e"]), w["w"], k))
    return sorted(W)


def src_to_tl(keeps, s):
    for k in keeps:
        if k["src_in"] - 1e-3 <= s < k["src_out"]:
            return k["tl_in"] + (s - k["src_in"])
    return None


def tl_to_src(keeps, t):
    for k in keeps:
        if k["tl_in"] - 1e-3 <= t < k["tl_out"] + 1e-3:
            return k["src_in"] + (t - k["tl_in"])
    best = min(keeps, key=lambda k: min(abs(t - k["tl_in"]), abs(t - k["tl_out"])))
    return best["src_in"] if abs(t - best["tl_in"]) < abs(t - best["tl_out"]) else best["src_out"]


def sentences(keeps, W):
    tw = []
    for s, e, w, k in W:
        t = src_to_tl(keeps, s)
        if t is not None:
            tw.append((t, t + (e - s), w, k))
    tw.sort()
    out, cur = [], []
    for x in tw:
        if cur and (x[0] - cur[-1][1] > 0.6 or x[3] != cur[-1][3]):
            out.append(cur); cur = []
        cur.append(x)
        if re.search(r"[.!?]$", x[2]):
            out.append(cur); cur = []
    if cur:
        out.append(cur)
    S = []
    for c in out:
        txt = " ".join(x[2] for x in c)
        toks = re.findall(r"[a-z0-9]+", norm(txt))
        vis = [t for t in toks if t in VISUAL]
        emph = [t for t in toks if t in EMPH]
        S.append({"tl_in": round(c[0][0], 3), "tl_out": round(c[-1][1], 3), "text": txt, "spk": c[0][3], "visual": vis, "emph": emph,
                  "words": [(round(x[0], 3), x[2]) for x in c]})
    return S


def score(s, t_intro=60.0):
    d = s["tl_out"] - s["tl_in"]
    sc = 2.0 * len(set(s["visual"])) + 0.6 * len(set(s["emph"])) + (0.8 if re.search(r"[!?]", s["text"]) else 0)
    sc += 1.0 if re.search(r"\d", s["text"]) else 0
    sc += 1.0 if s["tl_in"] < t_intro else 0
    sc -= 2.0 if d < 1.1 else 0
    sc -= 3.0 if "editor" in norm(s["text"]) else 0
    return round(sc, 2)


def busy_ranges(plan):
    """Trechos onde NÃO entra cinemática: takes futuros, B-rolls já planejados, promo/end card (±8 s), time-lapse."""
    R = []
    for f in plan.get("futuros", []):
        R.append((f["tl"] - 2, f["tl"] + f.get("dur", 1) + 2))
    for b in plan.get("brolls", []):
        pad = 8 if re.search(r"promo|endcard|insercoes", b["file"], re.I) else 2
        if not str(b.get("why", "")).startswith("CINE"):
            R.append((b["tl"] - pad, b["tl"] + b["dur"] + pad))
    end = plan.get("dur_tl") or (plan["keeps"][-1]["tl_out"] if plan.get("keeps") else 0)
    if end > 180:                                   # vídeo de verdade: tchau + tela final no fim
        R.append((end - 18, end + 1))
    return R


def pick_slots(S, plan, intro_n=(3, 5), intro_end=60.0, body_gap=(60.0, 120.0), min_gap_intro=6.0, breath=2.0):
    busy = busy_ranges(plan)
    free = lambda a, b: all(b <= x or a >= y for x, y in busy)
    for s in S:
        s["score"] = score(s)
    end = plan.get("dur_tl") or plan["keeps"][-1]["tl_out"]
    cand = [s for s in S if s["tl_in"] >= 1.5 and s["score"] > 0 and free(s["tl_in"], s["tl_in"] + 2.0)]
    chosen = []
    intro = sorted([s for s in cand if s["tl_in"] < intro_end], key=lambda s: -s["score"])
    for s in intro:
        if len(chosen) >= intro_n[1]:
            break
        ok = lambda c: abs(s["tl_in"] - c["tl_in"]) >= min_gap_intro and (s["tl_in"] >= c["tl_in"] + min(c["tl_out"] - c["tl_in"], 3.4) + breath
                                                                            or c["tl_in"] >= s["tl_in"] + min(s["tl_out"] - s["tl_in"], 3.4) + breath)
        if all(ok(c) for c in chosen):
            chosen.append(s)
    last = max([c["tl_in"] for c in chosen] + [intro_end - body_gap[0] * 0.5])
    while True:
        lo, hi = last + body_gap[0], last + body_gap[1]
        if lo > end - 20:
            break
        win = [s for s in cand if lo <= s["tl_in"] <= hi]
        if not win:
            last = lo
            continue
        best = max(win, key=lambda s: s["score"] - 0.01 * abs(s["tl_in"] - (lo + hi) / 2))
        chosen.append(best)
        last = best["tl_in"]
    chosen.sort(key=lambda s: s["tl_in"])
    out = []
    for i, s in enumerate(chosen):
        d = s["tl_out"] - s["tl_in"]
        t0 = s["tl_in"]
        if d > 3.4 and s["visual"]:                      # longa: começa um pouco antes da 1ª palavra visual
            kw = next((t for t, w in s["words"] if re.sub(r"[^a-z0-9]", "", norm(w)) in VISUAL), t0)
            t0 = max(s["tl_in"], kw - 0.35)
        dur = round(min(max(s["tl_out"] - t0, 1.6), 3.4), 2)
        out.append({"id": "c%02d" % (i + 1), "tl": round(t0, 3), "dur": dur, "intro": s["tl_in"] < intro_end, "text": s["text"],
                    "score": s["score"], "visual": sorted(set(s["visual"])), "sentence": [s["tl_in"], s["tl_out"]]})
    return out


def cmd_slots(a):
    plan = json.load(open(a[0], encoding="utf8"))
    W = load_words([p for p in a[1:] if p.endswith(".json")])
    outdir = a[a.index("--out") + 1] if "--out" in a else os.path.join(os.path.dirname(os.path.abspath(a[0])), "cine")
    os.makedirs(outdir, exist_ok=True)
    S = sentences(plan["keeps"], W)
    slots = pick_slots(S, plan)
    for s in slots:                                       # contexto de fala em volta (o que acontece na cena)
        s["before"] = " ".join(x["text"] for x in S if s["tl"] - 12 <= x["tl_in"] < s["tl"])[-400:]
        s["after"] = " ".join(x["text"] for x in S if s["tl"] + s["dur"] <= x["tl_in"] < s["tl"] + s["dur"] + 8)[:300]
    json.dump({"slots": slots, "candidates": sorted(S, key=lambda s: -s.get("score", 0))[:60]}, open(os.path.join(outdir, "slots.json"), "w", encoding="utf8"),
              ensure_ascii=False, indent=1)
    for s in slots:
        print("%s  %7.2f s  %.2f s  [%s]  %s" % (s["id"], s["tl"], s["dur"], ",".join(s["visual"]), s["text"][:110]))
    print("-> %s (%d slots; %d no 1º minuto). Os 60 melhores candidatos também estão no arquivo: troque um slot se outra frase ilustrar melhor."
          % (os.path.join(outdir, "slots.json"), len(slots), sum(1 for s in slots if s["intro"])))


# ------------------------------------------------------------------------------------------------ context
def _probe_w(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0", path],
                       capture_output=True, text=True)
    w, h = (int(x) for x in r.stdout.strip().split(",")[:2])
    return w, h


def _frame(bruto, t, out, crop):
    vf = (crop + "," if crop else "") + "scale=480:270"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "%.3f" % max(t, 0), "-i", bruto, "-frames:v", "1", "-vf", vf, out], check=False)
    return out


def scene_stats(paths):
    """Pistas objetivas do lugar: frações de areia/grama/água/neve/pedra/escuro abaixo do horizonte + cor do céu (hora)."""
    import numpy as np
    from PIL import Image
    acc = {}
    sky = []
    for p in paths:
        if not os.path.exists(p):
            continue
        a = np.asarray(Image.open(p).convert("RGB")).astype(float)
        top, low = a[:80], a[110:250]
        r, g, b = low[..., 0], low[..., 1], low[..., 2]
        lum = (r + g + b) / 3
        mx, mn = np.maximum(np.maximum(r, g), b), np.minimum(np.minimum(r, g), b)
        sat = (mx - mn) / np.maximum(mx, 1)
        cls = {
            "areia": (r > g) & (g > b) & (lum > 140) & (sat < 0.45),
            "grama": (g > r * 1.08) & (g > b * 1.1) & (lum > 50),
            "agua": (b > r * 1.25) & (b > g * 1.02) & (lum > 40),
            "neve": (lum > 205) & (sat < 0.1),
            "pedra": (sat < 0.12) & (lum > 70) & (lum < 170),
            "escuro": lum < 38,
            "lava/vermelho": (r > 170) & (r > g * 1.6) & (r > b * 1.6),
            "terra/madeira": (r > g) & (g > b) & (lum < 140) & (lum > 50) & (sat > 0.25),
        }
        for k, m in cls.items():
            acc[k] = acc.get(k, 0) + float(m.mean())
        sky.append(top.reshape(-1, 3).mean(0))
    n = max(1, len(paths))
    frac = {k: round(v / n, 2) for k, v in sorted(acc.items(), key=lambda x: -x[1])}
    s = (sum(sky) / max(1, len(sky))) if sky else [0, 0, 0]
    sr, sg, sb = s
    hora = "noite" if (sr + sg + sb) / 3 < 50 else ("por do sol/amanhecer" if sr > sb * 0.95 and sr > 120 else "dia")
    bio = max([("desert", frac.get("areia", 0)), ("plains", frac.get("grama", 0)), ("snowy_plains", frac.get("neve", 0)),
               ("ocean_island", frac.get("agua", 0) * 0.8), ("stony_shore", frac.get("pedra", 0) * 0.7)], key=lambda x: x[1])[0]
    return {"frac": frac, "ceu_rgb": [int(sr), int(sg), int(sb)], "hora": hora, "bioma_sugerido": bio,
            "time_sugerido": {"dia": 5000, "noite": 18000, "por do sol/amanhecer": 12300}[hora]}


def cmd_context(a):
    sl = json.load(open(a[0], encoding="utf8"))
    slots = sl["slots"] if isinstance(sl, dict) else sl
    bruto, plan = a[1], json.load(open(a[2], encoding="utf8"))
    outdir = os.path.dirname(os.path.abspath(a[0]))
    w, h = _probe_w(bruto)
    crop = "crop=%d:%d:%d:0" % (w // 2, h, w // 2) if w >= 2 * h * 1.7 else ""     # 3840x1080: jogo na metade direita
    jobs = []
    for s in slots:
        ts = [s["tl"] - 1.5, s["tl"], s["tl"] + s["dur"] / 2, s["tl"] + s["dur"]]
        s["_frames"] = [os.path.join(outdir, "_f_%s_%d.jpg" % (s["id"], i)) for i in range(4)]
        for t, p in zip(ts, s["_frames"]):
            jobs.append((bruto, tl_to_src(plan["keeps"], t), p, crop))
    with ThreadPoolExecutor(4) as ex:
        list(ex.map(lambda j: _frame(*j), jobs))
    for s in slots:
        out = os.path.join(outdir, "ctx_%s.jpg" % s["id"])
        ins = sum([["-i", p] for p in s["_frames"]], [])
        subprocess.run(["ffmpeg", "-v", "error", "-y"] + ins + ["-filter_complex", "hstack=4", out], check=False)
        s["ctx"] = out
        s["stats"] = scene_stats(s["_frames"])
        for p in s.pop("_frames"):
            try: os.remove(p)
            except OSError: pass
        print("%s %7.2f s  %s | %s | %s" % (s["id"], s["tl"], s["stats"]["bioma_sugerido"], s["stats"]["hora"],
                                          ", ".join("%s %.0f%%" % (k, v * 100) for k, v in list(s["stats"]["frac"].items())[:4])))
        print("    \"%s\"  -> %s" % (s["text"][:100], out))
    json.dump(sl, open(a[0], "w", encoding="utf8"), ensure_ascii=False, indent=1)
    sys.path.insert(0, CINE)
    from cinecam.turma import cast_sheet
    print("turma (quem é quem):", cast_sheet(os.path.join(outdir, "turma.png")))


# ------------------------------------------------------------------------------------------------ render
def _sheet(mp4, out, n=6):
    d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", mp4], capture_output=True, text=True).stdout or 0)
    fps = max(n / max(d, 0.1), 0.1)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mp4, "-vf", "fps=%.4f,scale=480:-2,tile=%dx1" % (fps, n), "-frames:v", "1", out], check=False)
    return out


def cmd_render(a):
    cards_path, q = a[0], a[1]
    cards = json.load(open(cards_path, encoding="utf8"))
    cards = cards["cards"] if isinstance(cards, dict) else cards
    if "--only" in a:
        keep = set(a[a.index("--only") + 1].split(","))
        cards = [c for c in cards if c["id"] in keep]
    outdir = os.path.dirname(os.path.abspath(cards_path))
    prefix = re.sub(r"[^A-Za-z0-9]", "", os.path.basename(os.path.dirname(outdir)))[-14:] + "_"
    sys.path.insert(0, CINE)
    from cinecam.auto import render_cards
    infos = render_cards(cards, q, prefix=prefix)
    res = []
    for c, i in zip(cards, infos):
        r = {"id": c["id"], "ok": i["ok"], "error": i.get("error")}
        if i["ok"] and q == "stills":
            sh = os.path.join(outdir, "st_%s.jpg" % c["id"])
            ins = sum([["-i", p] for p in i["stills"]], [])
            subprocess.run(["ffmpeg", "-v", "error", "-y"] + ins + ["-filter_complex", "hstack=%d,scale=1440:-2" % len(i["stills"]), sh], check=False)
            r["sheet"] = sh
        elif i["ok"]:
            dst = os.path.join(outdir, "%s%s.mp4" % (c["id"], "" if q == "final" else "_" + q))
            shutil.copyfile(i["final"], dst)
            r["file"] = dst
            r["sheet"] = _sheet(dst, os.path.join(outdir, "%s_%s.jpg" % (c["id"], q)))
            if q == "final":
                rep = i.get("report", {})
                r["warnings"] = rep.get("warnings")
        res.append(r)
        print(json.dumps(r, ensure_ascii=False))
    json.dump(res, open(os.path.join(outdir, "render_%s.json" % q), "w", encoding="utf8"), ensure_ascii=False, indent=1)


# ------------------------------------------------------------------------------------------------ insert
WHOOSH = "19--Whoosh 39.wav"


def _sfx_file(stem):
    if os.path.isabs(stem) and os.path.exists(stem):
        return stem
    for f in os.listdir(SFX):
        if f == stem or os.path.splitext(f)[0] == stem:
            return os.path.join(SFX, f)
    raise FileNotFoundError("SFX não achado na biblioteca: " + stem)


def cmd_insert(a):
    plan_path, cards_path = a[0], a[1]
    plan = json.load(open(plan_path, encoding="utf8"))
    shutil.copyfile(plan_path, plan_path + ".antes_cine.bak")
    cards = json.load(open(cards_path, encoding="utf8"))
    cards = cards["cards"] if isinstance(cards, dict) else cards
    outdir = os.path.dirname(os.path.abspath(cards_path))
    for k in ("brolls", "mutes", "sfx", "marks"):                 # refazer limpo (rodar 2x não duplica)
        plan[k] = [x for x in plan.get(k, []) if not str(x.get("why", x.get("txt", ""))).startswith("CINE")]
    n = 0
    for c in cards:
        f = os.path.join(outdir, c["id"] + ".mp4")
        if not os.path.exists(f) or c.get("skip"):
            print("pulando", c["id"], "(sem render final)" if not os.path.exists(f) else "(skip)")
            continue
        tl, dur = float(c["tl"]), float(c.get("tl_dur", c["dur"]))
        why = "CINE %s: %s" % (c["id"], c.get("why", "")[:120])
        b = {"file": f, "tl": tl, "dur": dur, "v": 3, "why": why}
        if c.get("flash", c.get("intro", False)):
            b["flash"] = [0.55, 0.3]
        plan["brolls"].append(b)
        for tr in (1, 2):                                        # A2 call / A3 jogo calados sob a cinemática (A1 nunca)
            if c.get("mute", True):
                plan["mutes"].append({"track": tr, "a": tl - 0.02, "b": tl + dur, "why": why})
        if c.get("whoosh", True):
            plan["sfx"].append({"file": _sfx_file(WHOOSH), "tl": round(tl - 0.25, 3), "why": why + " (whoosh de entrada)"})
        for stem, off in c.get("sfx", []):
            plan["sfx"].append({"file": _sfx_file(stem), "tl": round(tl + float(off), 3), "why": why})
        plan["marks"].append({"tl": tl, "txt": why})
        n += 1
    plan["sfx"].sort(key=lambda x: x["tl"])
    json.dump(plan, open(plan_path, "w", encoding="utf8"), ensure_ascii=False, indent=1)
    print("%d cinemáticas no plano (%s); backup em %s" % (n, plan_path, plan_path + ".antes_cine.bak"))


def cmd_check(a):
    """Valida as fichas SEM renderizar (enquadramento: ninguém de perfil, rosto do sujeito <= 50°, ninguém cortado na lateral;
    itens encaixados).  Ficha recusada = refazer blocking/câmera antes de gastar render."""
    cards = json.load(open(a[0], encoding="utf8"))
    cards = cards["cards"] if isinstance(cards, dict) else cards
    sys.path.insert(0, CINE)
    from cinecam.auto import check_card
    bad = 0
    for c in cards:
        pr = check_card(c)
        bad += bool(pr)
        print("%s  %s" % (c["id"], "OK" if not pr else "RECUSADA: " + pr[0]))
    print("%d/%d fichas aprovadas" % (len(cards) - bad, len(cards)))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    cmd = sys.argv[1]
    {"slots": cmd_slots, "context": cmd_context, "check": cmd_check, "render": cmd_render, "insert": cmd_insert}[cmd](sys.argv[2:])
