"""Plano do EDITOR WEB (aba Edição do Estúdio, skill editar-longo) -> plan3.json desta skill (Estúdio Problems Local, 22/10/2026).

    python plano_web.py <pedido.json> <saida_plan3.json>
pedido.json (mandado pela ponte do site, server.py /api/job com "plano_web"):
    {"bruto": "<caminho local do bruto>", "plano": {...plano.json do editor web...},
     "clipes": [{"tl_in", "tl_out", "src_in"}],   # V1 do editor web DEPOIS do corte de ritmo (linha do tempo atual)
     "vozes": [{"faixa": "A1"}, {"faixa": "A2"}, ...]}   # ordem das faixas de áudio do bruto (A1 = voz principal)
Regras: os 'cortes' do plano web são aplicados aqui (tiram trechos da linha do tempo e puxam o resto); todo tempo do plano web
é da linha do tempo ANTES desses cortes.  O que não tem equivalente no plan3 (pb, vinheta, preto, textos) vira marcador.
"""
import json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import paths as P

PRESET = {"flash": "White Flash B", "flash_vermelho": "Red Flash B", "flash_verde": "Green Flash B", "shake": "Impact Shake Low", "vhs": "VHS"}


class Linha:
    """mapa linha do tempo web (antes dos cortes) -> linha do tempo final, e -> tempo no bruto."""

    def __init__(self, clipes, cortes):
        self.cl = sorted(({"tl_in": float(c["tl_in"]), "tl_out": float(c["tl_out"]), "src_in": float(c["src_in"])} for c in clipes), key=lambda c: c["tl_in"])
        cs = sorted((float(c["a"]), float(c["b"])) for c in cortes if float(c["b"]) > float(c["a"]))
        self.cortes = []
        for a, b in cs:                                   # junta cortes sobrepostos
            if self.cortes and a <= self.cortes[-1][1]:
                self.cortes[-1][1] = max(self.cortes[-1][1], b)
            else:
                self.cortes.append([a, b])

    def tl(self, t):
        """tempo final (None se cair dentro de um corte)."""
        d = 0.0
        for a, b in self.cortes:
            if t >= b: d += b - a
            elif t > a: return None
        return round(t - d, 4)

    def tl_after(self, t):
        """como tl(), mas um tempo dentro de um corte vai para o fim do corte (início do que sobra)."""
        for a, b in self.cortes:
            if a < t < b: t = b
        return self.tl(t)

    def src(self, t):
        for c in self.cl:
            if c["tl_in"] - 1e-6 <= t < c["tl_out"] + 1e-6:
                return round(c["src_in"] + t - c["tl_in"], 4)
        return None

    def keeps(self):
        out = []
        for c in self.cl:
            segs = [(c["tl_in"], c["tl_out"])]
            for a, b in self.cortes:                      # tira os cortes de dentro de cada clipe
                nxt = []
                for s, e in segs:
                    if b <= s or a >= e: nxt.append((s, e)); continue
                    if a > s: nxt.append((s, a))
                    if b < e: nxt.append((b, e))
                segs = nxt
            for s, e in segs:
                if e - s < 0.02: continue
                src0 = c["src_in"] + s - c["tl_in"]
                out.append({"src_in": round(src0, 4), "src_out": round(src0 + e - s, 4), "tl_in": self.tl(s), "tl_out": round(self.tl(s) + e - s, 4),
                            "xf_prev": bool(out) and abs(out[-1]["src_out"] - src0) > 0.02})     # corte de conteúdo = transição curta de áudio
        return out


def split_at(keeps, t):
    """garante um clipe V1 que COMEÇA em t (presets/reveals/stretch exigem)."""
    for i, k in enumerate(keeps):
        if abs(k["tl_in"] - t) < 0.02: return k["tl_in"]
        if k["tl_in"] < t < k["tl_out"] - 0.05:
            d = t - k["tl_in"]
            a = dict(k, src_out=round(k["src_in"] + d, 4), tl_out=round(t, 4))
            b = dict(k, src_in=round(k["src_in"] + d, 4), tl_in=round(t, 4), xf_prev=False)
            keeps[i:i + 1] = [a, b]
            return round(t, 4)
    return None


def zoom_keys(de, para, anim, dur, fx, fy, para_y=None):
    """ease-out amostrado (padrão da skill: zoom rápido que decai e FICA); scale em %, foco em px do quadro 1920x1080."""
    s0, s1 = de * 100.0, para * 100.0
    if anim <= 0.01:
        return [[0.0, s1, 0, 0, 0, fx, fy], [round(max(dur, 0.05), 3), s1, 0, 0, 0, fx, fy]]
    n = max(2, int(math.ceil(anim / 0.25)))
    ks = [[round(anim * i / n, 3), round(s0 + (s1 - s0) * (1 - (1 - i / n) ** 3), 2), 0, 0, 0, fx, fy] for i in range(n + 1)]
    if dur > anim + 0.05:
        ks.append([round(dur, 3), s1, 0, 0, 0, fx, fy])
    return ks


def _local(arquivo, raiz, sub=None):
    """caminho do plano web (servidor de sons / biblioteca) -> arquivo desta máquina, pelo nome."""
    nome = os.path.basename(str(arquivo).replace("\\", "/"))
    for base in ([os.path.join(raiz, sub)] if sub else []) + [raiz]:
        p = os.path.join(base, nome)
        if os.path.exists(p): return p
    for dp, _, fs in os.walk(raiz):
        if nome in fs: return os.path.join(dp, nome)
    return None


def converter(pedido):
    W = pedido["plano"]
    L = Linha(pedido["clipes"], W.get("cortes", []))
    keeps = L.keeps()
    sfx_dir = os.path.join(P.SKILL, "library", "sfx")
    epi = P.epidemic_dir()
    faixas = [v.get("faixa") for v in pedido.get("vozes", [])] or ["A1", "A2", "A3"]
    out = {"keeps": keeps, "fx": [], "stretch": [], "presets": [], "music": [], "sfx": [], "mutes": [], "reveals": [], "futuros": [], "marks": [],
           "origem": "editor web (plano_web.py)", "resumo_web": W.get("resumo", "")}
    falta = []

    def mark(t, txt):
        tt = L.tl_after(t)
        if tt is not None: out["marks"].append({"tl": tt, "txt": txt})

    for z in W.get("zooms", []):
        a, b = L.tl_after(float(z["a"])), L.tl(float(z["b"])) or L.tl_after(float(z["b"]))
        if a is None or b is None or b <= a: continue
        fx, fy = 1920 * float(z.get("fx", 0.5)), 1080 * float(z.get("fy", 0.5))
        if z.get("paraY"):
            t = split_at(keeps, a)
            if t is not None:
                out["stretch"].append({"tl": t, "sx": round(float(z["para"]) * 100), "sy": round(float(z["paraY"]) * 100), "fx": round(fx), "fy": round(fy), "why": z.get("motivo", "")})
            continue
        out["fx"].append({"t": a, "keys": zoom_keys(float(z.get("de", 1)), float(z["para"]), float(z.get("anim", 0)), b - a, round(fx, 1), round(fy, 1)),
                          "why": z.get("motivo", "")})
    for e in W.get("efeitos", []):
        tipo, t = e.get("tipo"), L.tl_after(float(e["a"]))
        if t is None: continue
        p = e.get("p") or {}
        if tipo in ("flash", "shake", "vhs"):
            nm = PRESET[tipo]
            if tipo == "flash" and str(p.get("cor", "")).lower() in ("#ff2a2a", "vermelho", "red"): nm = PRESET["flash_vermelho"]
            t = split_at(keeps, t)
            if t is not None: out["presets"].append({"name": nm, "tl": t, "why": e.get("motivo", "")})
        elif tipo in ("brilho", "tilt"):
            t = split_at(keeps, t)
            if t is None: continue
            r = {"tl": t, "kind": "sparkle" if tipo == "brilho" else "tilt", "why": e.get("motivo", "")}
            if tipo == "brilho" and "fx" in p: r["pos"] = [round(0.5 + float(p["fx"]) * 0.5, 4), float(p.get("fy", 0.5))]   # bruto 3840: jogo na metade direita
            out["reveals"].append(r)
        elif tipo == "flashback":
            pass                                              # vem junto dos takes (futuros já recebem o filtro flashback)
        else:
            mark(float(e["a"]), "EFEITO %s (%.1f s) do plano web: %s" % (tipo, float(e.get("dur", 0)), e.get("motivo", "")))
    for s in W.get("sfx", []):
        f = _local(s["arquivo"], sfx_dir)
        t = L.tl_after(float(s["t"]) - float(s.get("pre", 0.06)))
        if t is None: continue
        if not f: falta.append(s["arquivo"]); mark(float(s["t"]), "SFX faltando nesta máquina: " + os.path.basename(s["arquivo"])); continue
        out["sfx"].append({"file": f, "tl": max(0.0, t), "why": s.get("motivo", "")})
    for m in W.get("musicas", []):
        f = _local(m["arquivo"], epi, m.get("pasta"))
        a, b = L.tl_after(float(m["a"])), L.tl_after(float(m["b"]))
        if a is None or b is None or b <= a: continue
        if not f: falta.append(m["arquivo"]); mark(float(m["a"]), "MÚSICA faltando nesta máquina: " + os.path.basename(m["arquivo"])); continue
        out["music"].append({"file": f, "tl_in": a, "tl_out": b, "src_in": float(m.get("de", 0)), "gain_db": float(m.get("ganho", -26)),
                             "fade_in": 0.04, "fade_out": 0.1, "why": "%s/%s" % (m.get("pasta", ""), m.get("clima", ""))})
    for m in W.get("mutes", []):
        tr = faixas.index(m["faixa"]) if m.get("faixa") in faixas else None
        a, b = L.tl_after(float(m["a"])), L.tl_after(float(m["b"]))
        if not tr or a is None or b is None or b <= a: continue          # faixa 0 (voz principal) nunca
        for t in (a, b): split_at(keeps, t)
        out["mutes"].append({"track": tr, "a": a, "b": b, "why": m.get("motivo", "")})
    for i, k in enumerate(sorted(W.get("takes", []), key=lambda x: float(x["a"]))):
        t, src = L.tl_after(float(k["a"])), L.src(float(k["de"]))
        if t is None or src is None: continue
        out["futuros"].append({"file": pedido["bruto"], "tl": t, "dur": float(k.get("dur", 0.8)), "off": src, "v": 2, "zoom": [100, 106],
                               "preset_in": "White Flash B" if i == 0 else None, "preset_out": None, "why": k.get("motivo", "take futuro")})
    for x in W.get("textos", []):
        mark(float(x["a"]), "TEXTO: %s (%s, %.1f s)" % (x.get("texto", ""), x.get("cor", ""), float(x.get("dur", 1.5))))
    for x in W.get("marcadores", []):
        mark(float(x["t"]), x.get("txt", ""))
    out["keeps"] = sorted(keeps, key=lambda k: k["tl_in"])
    out["dur_tl"] = out["keeps"][-1]["tl_out"] if out["keeps"] else 0.0
    out["bruto_prefix"] = os.path.basename(pedido["bruto"])
    out["faltando"] = sorted(set(falta))
    return out


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf8")
    ped = json.load(open(sys.argv[1], encoding="utf8"))
    plan = converter(ped)
    json.dump(plan, open(sys.argv[2], "w", encoding="utf8"), ensure_ascii=False, indent=1)
    print("plan3: %d keeps, %d zooms, %d presets, %d reveals, %d sfx, %d músicas, %d mutes, %d takes, %d marcadores; faltando %d arquivos"
          % tuple([len(plan[k]) for k in ("keeps", "fx", "presets", "reveals", "sfx", "music", "mutes", "futuros", "marks")] + [len(plan["faltando"])]))
