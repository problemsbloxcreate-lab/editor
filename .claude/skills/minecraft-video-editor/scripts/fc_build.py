"""Monta a edição no FILMCRAFT (alternativa ao Premiere) a partir do MESMO plan3.json do build_edit3.py.

uso: python fc_build.py <plan3.json> <bruto.mp4> <saida.fcproj> [--open] [--export out.mp4] [--seq-name nome]

Mapeamento (Premiere -> FilmCraft, tudo editável depois no FilmCraft):
  keeps        -> timeline.place do bruto em V1 + A1..A3 (as 3 faixas de áudio do bruto: voz, call, jogo); xf_prev -> Constant Power (xf_frames) nos 3 áudios
  enquadramento-> bruto 3840x1080: Motion position (0,540) = metade DIREITA (jogo) no quadro 1920x1080
  fx (zooms)   -> Motion scale/position com keyframes (mesma conta do build_edit3: px = fx*(1-s), py = fy - s*(fy-540)); o ease-out vem das chaves amostradas
  stretch      -> Motion uniform_scale=false, scale (altura) / scale_width
  presets      -> berserker.spec (o mesmo catálogo do .prfpset) traduzido efeito a efeito: Tint, Transform, Mirror, Wave Warp, Noise, Color Emboss,
                  Basic 3D, Drop Shadow, Opacity, Motion, Lumetri (saturação), Fast Blur, Mosaic; o que não tiver equivalente vai para o relatório
  music        -> A4, ganho FIXO (gain_db + boost_music_db + master_db), sem fade
  sfx          -> A5..A7, mesmas regras do build_edit3 (cut:true encosta no corte, apara o silêncio inicial, ganho da tabela GAIN_DB / gain_for)
  mutes        -> clip.enable (desliga) nos clipes de A2/A3 que começam em [a,b)
  reveals      -> sparkle = Glint com intensidade animada; tilt = encolhe 100->71 %, gira 0->-3.2 graus e dessatura (Lumetri) em ~2 s
  futuros      -> vídeo-só em V2 + flashback (Tint sépia 48 % + Lumetri quente/lavado + vinheta) + zoom lento + presets nas pontas
  brolls       -> vídeo-só em V3 (pos/scale/flash Tint branco que decai; echo em V4)
  marks        -> markers.add
  vozes        -> plan['voice_db'] = [A1, A2, A3] (padrão 0) + Hard Limiter nos 3 (regra 6b: dublagem/call niveladas)
"""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import filmcraft as fc
import berserker as bz
import sfx_timing as _sfxt
from sfx_levels import gain_for, table_gain

T = 254016000000
SFXLIB = os.path.join(HERE, "..", "library", "sfx")
tk = lambda s: int(round(s * T))
W, H = 1920, 1080


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height,r_frame_rate:format=duration", "-of", "json", path],
                         capture_output=True, text=True).stdout
    d = json.loads(out); v = next((s for s in d["streams"] if s["codec_type"] == "video"), {})
    n, dd = (v.get("r_frame_rate") or "60/1").split("/")
    return {"w": v.get("width", 0), "h": v.get("height", 0), "fps": float(n) / float(dd or 1), "dur": float(d["format"].get("duration", 0)),
            "audio": sum(1 for s in d["streams"] if s["codec_type"] == "audio")}


def sfx_levels(path, off=0.0, dur=None):
    """(pico, RMS ativo) do trecho usado — igual ao build_edit3"""
    import wave, tempfile
    import numpy as np
    # 21/10: PCM pelo pipe (antes um WAV temporário de nome fixo no C: — dois jobs ao mesmo tempo se atropelavam)
    cmd = ["ffmpeg", "-loglevel", "error"] + (["-ss", str(off)] if off else []) + (["-t", str(dur)] if dur else []) + ["-i", path, "-vn", "-ac", "1", "-ar", "44100", "-f", "f32le", "-"]
    d = np.clip(np.frombuffer(subprocess.run(cmd, check=True, capture_output=True).stdout, dtype=np.float32), -1, 1).astype(np.float64)   # = o int16 de antes (calibração igual)
    if len(d) < 441: return -6.0, -20.0
    pk = 20 * np.log10(np.abs(d).max() + 1e-9); hop = 882; n = len(d) // hop
    fr = np.array([np.sqrt((d[i * hop:(i + 1) * hop] ** 2).mean()) for i in range(max(n, 1))])
    act = fr > fr.max() * 10 ** (-35 / 20.0)
    return float(pk), float(20 * np.log10(np.sqrt((fr[act] ** 2).mean()) + 1e-9))


def interp(keys, t):
    if t <= keys[0][0]: return keys[0][1:]
    if t >= keys[-1][0]: return keys[-1][1:]
    for a, b in zip(keys, keys[1:]):
        if a[0] <= t <= b[0]:
            u = 0 if b[0] == a[0] else (t - a[0]) / (b[0] - a[0])
            return tuple(a[i] + (b[i] - a[i]) * u for i in range(1, len(a)))


def hexcolor(c):  # [A,R,G,B] 0-255
    return "#%02x%02x%02x" % tuple(int(x) for x in c[1:4])


# Premiere (matchName, índice do parâmetro) -> (efeito FilmCraft, parâmetro, conversão)
PT = lambda v: [v[0] * W, v[1] * H] if isinstance(v, list) else v           # ponto normalizado do quadro -> pixels
MAP = {
    "AE.ADBE Tint": ("tint", {0: "black", 1: "white", 2: "amount"}),
    "AE.ADBE Geometry2": ("transform", {0: ("anchor", PT), 1: ("position", PT), 2: "uniform_scale", 3: "scale_height", 4: "scale_width", 5: "skew",
                                        6: "skew_axis", 7: "rotation", 8: "opacity", 10: "shutter_angle"}),
    "AE.ADBE Mirror": ("mirror", {0: ("center", PT), 1: "angle"}),
    "AE.ADBE Wave Warp": ("wave_warp", {1: "height", 2: "width", 3: "direction", 4: "speed"}),
    "AE.ADBE Noise": ("noise", {0: "amount", 2: "clip"}),
    "AE.ADBE Color Emboss": ("color_emboss", {0: "direction", 1: "relief", 2: "contrast", 3: "blend"}),
    "AE.ADBE Basic 3D": ("basic_3d", {0: "swivel", 1: "tilt", 2: "distance"}),
    "AE.ADBE Drop Shadow": ("drop_shadow", {0: "color", 1: "opacity", 2: "direction", 3: "distance", 4: "softness", 5: "only"}),
    "AE.ADBE Opacity": ("opacity", {0: "opacity"}),
    "AE.ADBE Fast Blur": ("gaussian_blur", {0: "blurriness"}),
    "AE.ADBE Mosaic": ("mosaic", {0: "horizontal", 1: "vertical"}),
    "AE.ADBE Lumetri": ("lumetri", {16: "saturation"}),
}


class Builder:
    def __init__(s, plan, bruto, proj, seq_name):
        s.plan, s.bruto, s.proj, s.seq_name = plan, os.path.abspath(bruto), os.path.abspath(proj), seq_name
        s.steps, s.report, s.items = [], [], {}
        s.nfx = {}                                     # clipe -> nº de efeitos já aplicados (o k-ésimo aplicado fica no índice k; motion/opacity/time_remap vêm depois)
        s.info = probe(s.bruto)

    def add(s, cid, **p): s.steps.append({"id": cid, "params": p})

    def flush(s, new=False):
        if not s.steps: return []
        out = fc.run(s.proj, s.steps, new=new, keep_going=True)
        bad = [o for o in out if not o.get("ok", True)]
        for b in bad: s.report.append("FilmCraft recusou %s: %s" % (b.get("id"), str(b.get("error"))[:160]))
        s.steps = []
        return out

    def apply(s, clip, effect):
        """aplica o efeito e devolve o ÍNDICE dele no clipe (pelo nome, o FilmCraft sempre pega o 1º do tipo)"""
        s.add("effects.apply", clips=[clip], effect=effect)
        i = s.nfx.get(clip, 0); s.nfx[clip] = i + 1
        return i

    def setp(s, clip, effect, param, value, t=None):
        p = {"clip": clip, "effect": effect, "param": param, "value": value}
        if t is not None: p.update(time=tk(t), keyframe=True)
        s.add("effects.setParam", **p)

    # ---------- 0. projeto, mídia, sequência ----------
    def setup(s):
        P = s.plan
        files = [s.bruto] + sorted({m["file"] for m in P.get("music", [])} | {x["file"] for x in P.get("sfx", [])} |
                                   {x["file"] for x in P.get("futuros", [])} | {x["file"] for x in P.get("brolls", [])})
        miss = [f for f in files if not os.path.exists(f)]
        if miss: raise SystemExit("arquivos inexistentes: %s" % miss[:5])
        for f in files: s.add("file.import", paths=[os.path.abspath(f)])
        out = s.flush(new=True)
        for f, o in zip(files, out):
            ids = (o.get("result") or {}).get("items") or []
            if ids: s.items[os.path.abspath(f)] = ids[0]
        fps = round(s.info["fps"], 3) or 60
        nv = max([3] + [x.get("v", 3) + (1 if x.get("echo") else 0) for x in P.get("brolls", [])])
        s.add("file.newSequence", name=s.seq_name, width=W, height=H, fps=fps, video=nv, audio=8)
        s.flush()

    # ---------- 1. cortes ----------
    def keeps(s):
        it = s.items[s.bruto]
        for k in s.plan["keeps"]:
            s.add("timeline.place", item=it, track="V1", audioTrack="A1", seconds=round(k["tl_in"], 5), sourceIn=tk(k["src_in"]), duration=tk(k["src_out"] - k["src_in"]))
        out = s.flush()
        s.kc = []                                      # por keep: [v, a1, a2, a3]
        for o in out:
            if o.get("id") == "timeline.place": s.kc.append((o.get("result") or {}).get("clips") or [])
        if len(s.kc) != len(s.plan["keeps"]): s.report.append("cortes colocados %d de %d" % (len(s.kc), len(s.plan["keeps"])))

    def clip_at(s, tl):
        for i, k in enumerate(s.plan["keeps"]):
            if abs(k["tl_in"] - tl) < 0.02: return i
        for i, k in enumerate(s.plan["keeps"]):
            if k["tl_in"] - 0.02 <= tl < k["tl_out"]: return i
        return None

    # ---------- 2. enquadramento + zoom + stretch ----------
    def framing(s):
        P, wide = s.plan, s.info["w"] >= 2 * W - 10
        evs = []
        for e in P.get("fx", []):
            dfx, dfy = e.get("fx", 960), e.get("fy", 540)
            pts = [(e["t"] + k[0], float(k[1]), float(k[5]) if len(k) > 5 else dfx, float(k[6]) if len(k) > 6 else dfy) for k in e["keys"]]
            evs.append(pts)
        for i, k in enumerate(P["keeps"]):
            if i >= len(s.kc) or not s.kc[i]: continue
            v = s.kc[i][0]
            rows = []
            for pts in evs:
                t0, t1 = pts[0][0], pts[-1][0]
                if t1 <= k["tl_in"] + 1e-6 or t0 >= k["tl_out"] - 1e-6: continue
                ts = sorted({max(t0, k["tl_in"]), min(t1, k["tl_out"])} | {p[0] for p in pts if k["tl_in"] < p[0] < k["tl_out"]})
                for t in ts:
                    sc, fx_, fy_ = interp(pts, t); sp = sc / 100.0
                    # foco (fx,fy) fica parado no quadro: bruto largo -> âncora no centro da fonte (1920), jogo = metade direita
                    px = fx_ * (1 - sp) if wide else fx_ - sp * (fx_ - 960)
                    rows.append((t, sc, [px, fy_ - sp * (fy_ - 540)]))
            if not rows:
                s.setp(v, "motion", "position", [0.0, 540.0] if wide else [960.0, 540.0])
                continue
            for t, sc, (px, py) in rows:
                s.setp(v, "motion", "scale", round(sc, 3), t)
                s.setp(v, "motion", "position", [round(px, 2), round(py, 2)], t)
        for x in P.get("stretch", []):
            i = s.clip_at(x["tl"])
            if i is None: s.report.append("stretch sem clipe em %.2f" % x["tl"]); continue
            v = s.kc[i][0]; sx, sy = x["sx"] / 100.0, x["sy"] / 100.0
            s.setp(v, "motion", "uniform_scale", False)
            s.setp(v, "motion", "scale", x["sy"]); s.setp(v, "motion", "scale_width", x["sx"])
            px = x["fx"] * (1 - sx) if wide else x["fx"] - sx * (x["fx"] - 960)
            s.setp(v, "motion", "position", [round(px, 2), round(x["fy"] - sy * (x["fy"] - 540), 2)])
        s.flush()

    # ---------- 3. presets BERSERKER traduzidos ----------
    def preset(s, clip, name, t_clip0, clip_len, anchor=None, tscale=1.0):
        try: sp = bz.spec(name, 0, 0.0, clip_len, anchor=anchor, tscale=tscale)
        except KeyError as e: s.report.append(str(e)); return
        for F in sp["fx"]:
            m = MAP.get(F["match"])
            if not m: s.report.append("preset %s: efeito sem equivalente no FilmCraft (%s) — pulado" % (name, F["name"])); continue
            eff, pmap = m
            ref = eff if eff in ("motion", "opacity") else s.apply(clip, eff)
            for prm in F["params"]:
                tgt = pmap.get(prm["i"])
                if not tgt: continue
                pname, conv = (tgt if isinstance(tgt, tuple) else (tgt, None))
                if "color" in prm: s.setp(clip, ref, pname, hexcolor(prm["color"])); continue
                if "keys" in prm:
                    for kt, kv in prm["keys"]:
                        s.setp(clip, ref, pname, conv(kv) if conv else kv, t_clip0 + kt)
                else:
                    v = prm["v"]; s.setp(clip, ref, pname, conv(v) if conv else v)

    def presets(s):
        for x in s.plan.get("presets", []):
            i = s.clip_at(x["tl"])
            if i is None: s.report.append("preset %s sem clipe em %.2f" % (x["name"], x["tl"])); continue
            k = s.plan["keeps"][i]
            s.preset(s.kc[i][0], x["name"], k["tl_in"], k["tl_out"] - k["tl_in"], x.get("anchor"), x.get("tscale", 1.0))
        s.flush()

    # ---------- 4. música, SFX, vozes, mutes ----------
    def audio(s):
        P = s.plan
        master = P.get("master_db", 0.0); boost_m = P.get("boost_music_db", 0.0) + master
        ms = P.get("music", [])
        for i, m in enumerate(ms):
            end = m.get("tl_out", ms[i + 1]["tl_in"] if i + 1 < len(ms) else P["dur_tl"])
            s.add("timeline.place", item=s.items[os.path.abspath(m["file"])], track="A4", seconds=round(m["tl_in"], 5),
                  sourceIn=tk(m.get("src_in", 0.0)), duration=tk(end - m["tl_in"]))
        out = s.flush()
        mclips = [((o.get("result") or {}).get("clips") or [None])[0] for o in out if o.get("id") == "timeline.place"]
        for m, c in zip(ms, mclips):
            if c is not None: s.add("clip.audioGain", clips=[c], mode="set", db=round(m["gain_db"] + boost_m, 2))
        cuts = [k["tl_in"] for k in P["keeps"][1:]]
        busy, rows = {"A5": -1.0, "A6": -1.0, "A7": -1.0, "A8": -1.0}, []
        for x in P.get("sfx", []):
            if x.get("cut") and cuts:
                b = min(cuts, key=lambda c: abs(c - x["tl"]))
                if abs(b - x["tl"]) <= 1.5: x["tl"] = max(0.0, b - x.get("pre", 0.06))
        idx = json.load(open(os.path.join(SFXLIB, "index.json"), encoding="utf8"))
        for x in sorted(P.get("sfx", []), key=lambda x: x["tl"]):
            nm = os.path.basename(x["file"]); d0 = (idx.get(nm) or {}).get("dur") or probe(x["file"])["dur"]
            off = x["src_off"] if "src_off" in x else (0.0 if x.get("no_trim") else _sfxt.file_onset(x["file"]))
            d = min(x.get("dur", min(d0 - off, 2.5)), d0 - off)
            tr = next((t for t in busy if busy[t] <= x["tl"] + 1e-6), None)
            if tr is None: s.report.append("sem faixa livre p/ SFX %s em %.2f" % (nm, x["tl"])); continue
            busy[tr] = x["tl"] + d
            if "gain_db" in x: g = x["gain_db"]
            else:
                g = table_gain(nm) if "rms_db" not in x else None          # tabela dele: sem medir o arquivo
                if g is None:
                    pk, rm = sfx_levels(x["file"], off, d); g, _ = gain_for(nm, pk, rm, d, x)
            rows.append((x, tr, off, d, g))
            s.add("timeline.place", item=s.items[os.path.abspath(x["file"])], track=tr, seconds=round(x["tl"], 5), sourceIn=tk(off), duration=tk(d))
        out = s.flush()
        sclips = [((o.get("result") or {}).get("clips") or [None])[0] for o in out if o.get("id") == "timeline.place"]
        for (x, tr, off, d, g), c in zip(rows, sclips):
            if c is not None: s.add("clip.audioGain", clips=[c], mode="set", db=round(g, 2))   # ganho FIXO, nunca keyframe
        s.add("sequence.linkedSelection", on=False)      # ganho/mute por faixa: com o vínculo ligado o FilmCraft aplica no vídeo e nos 3 áudios juntos
        vdb = P.get("voice_db", [0.0, 0.0, 0.0])
        for kc in s.kc:
            for j, c in enumerate(kc[1:4]):
                if vdb[j]: s.add("clip.audioGain", clips=[c], mode="set", db=vdb[j])
                s.apply(c, "hard_limiter")
        off = []
        for mu in P.get("mutes", []):
            j = mu["track"]                                # 1 = call (A2), 2 = jogo (A3)
            for k, kc in zip(P["keeps"], s.kc):
                if mu["a"] - 1e-3 <= k["tl_in"] < mu["b"] and len(kc) > j + 1: off.append(kc[j + 1])
        if off:                                            # alterna (ligado -> desligado); sem Linked Selection, senão desliga o vídeo e a voz vinculados
            s.add("clip.enable", clips=off)
        s.add("sequence.linkedSelection", on=True)
        fr = P.get("xf_frames", 12)
        for k, kc in zip(P["keeps"], s.kc):
            if k.get("xf_prev"):
                for c in kc[1:4]: s.add("sequence.applyAudioTransition", clip=c, effect="constant_power", frames=fr, edge="in")
        s.flush()

    # ---------- 5. reveals, futuros, brolls, marcadores ----------
    def overlays(s):
        P = s.plan
        for R in P.get("reveals", []):
            i = s.clip_at(R["tl"])
            if i is None: s.report.append("reveal sem clipe em %.2f" % R["tl"]); continue
            v, t0 = s.kc[i][0], P["keeps"][i]["tl_in"]
            if R["kind"] == "sparkle":
                g = s.apply(v, "glint")
                s.setp(v, g, "intensity", 30, t0); s.setp(v, g, "intensity", 100, t0 + R.get("gdur", 1.2))
                s.setp(v, g, "length", 30, t0); s.setp(v, g, "length", 90, t0 + R.get("gdur", 1.2))
            elif R["kind"] == "tilt":
                d = R.get("dur", 2.1)
                s.setp(v, "motion", "position", [960, 540]); s.setp(v, "motion", "anchor", [2880 if s.info["w"] >= 3800 else s.info["w"] / 2, 540])
                s.setp(v, "motion", "scale", 100, t0); s.setp(v, "motion", "scale", R.get("scale", 71), t0 + d)
                s.setp(v, "motion", "rotation", 0, t0); s.setp(v, "motion", "rotation", R.get("rot", -3.2), t0 + d)
                lu = s.apply(v, "lumetri")
                s.setp(v, lu, "saturation", 100, t0); s.setp(v, lu, "saturation", R.get("sat", 27), t0 + d)
        s.flush()
        for x in P.get("futuros", []):
            s.add("timeline.place", item=s.items[os.path.abspath(x["file"])], track="V2", seconds=round(x["tl"], 5), sourceIn=tk(x.get("off", 0.0)), duration=tk(x["dur"]), audio=False)
        out = s.flush()
        fcl = [((o.get("result") or {}).get("clips") or [None])[0] for o in out if o.get("id") == "timeline.place"]
        for x, c in zip(P.get("futuros", []), fcl):
            if c is None: continue
            z = x.get("zoom", [100, 106]); s.setp(c, "motion", "scale", z[0], x["tl"]); s.setp(c, "motion", "scale", z[1], x["tl"] + x["dur"])
            lu = s.apply(c, "lumetri")
            for pn, pv in (("temperature", 25), ("saturation", 62), ("contrast", -8), ("faded_film", 35), ("vignette_amount", -2.0)): s.setp(c, lu, pn, pv)
            ti = s.apply(c, "tint")
            s.setp(c, ti, "black", "#40260e"); s.setp(c, ti, "white", "#fff0cd"); s.setp(c, ti, "amount", 48)
            if x.get("preset_in"): s.preset(c, x["preset_in"], x["tl"], x["dur"], "start")
            if x.get("preset_out"): s.preset(c, x["preset_out"], x["tl"], x["dur"], "end")
        s.flush()
        for x in P.get("brolls", []):
            s.add("timeline.place", item=s.items[os.path.abspath(x["file"])], track="V%d" % x.get("v", 3), seconds=round(x["tl"], 5), sourceIn=tk(x.get("off", 0.0)), duration=tk(x["dur"]), audio=False)
        out = s.flush()
        bcl = [((o.get("result") or {}).get("clips") or [None])[0] for o in out if o.get("id") == "timeline.place"]
        for x, c in zip(P.get("brolls", []), bcl):
            if c is None: continue
            if x.get("pos"): s.setp(c, "motion", "position", [x["pos"][0] * W, x["pos"][1] * H])
            if x.get("scale"): s.setp(c, "motion", "scale", x["scale"])
            if x.get("flash"):
                a0, fd = x["flash"]
                ti = s.apply(c, "tint")
                s.setp(c, ti, "black", "#ffffff"); s.setp(c, ti, "white", "#ffffff")
                s.setp(c, ti, "amount", a0, x["tl"]); s.setp(c, ti, "amount", 0, x["tl"] + fd)
            if x.get("echo"): s.report.append("broll echo em %.2f: refazer à mão no FilmCraft (cópia em V%d)" % (x["tl"], x.get("v", 3) + 1))
        for m in P.get("marks", []):
            s.add("markers.add", target="program", time=tk(m["tl"]), name=m["txt"][:60], comment=m["txt"])
        s.flush()

    def master(s):
        """Hard Limiter no bus Mix: entrega com true peak <= -1 dBTP (regra 6b; o mix dele saiu +0,4 = "faltou de leve").
        Medido no 1º job da interface (20/10): sem ele o pico dava 0,0 dBTP; com max -1,5 dB -> -1,5 dBTP."""
        s.add("mixer.addInsert", strip="Mix", effect="hard_limiter", slot=0)
        s.add("mixer.setInsert", strip="Mix", slot=0, params={"max": s.plan.get("master_ceiling_db", -1.5)})
        s.flush()

    def build(s):
        s.setup(); s.keeps(); s.framing(); s.presets(); s.audio(); s.overlays(); s.master()
        s.add("file.save"); s.flush()
        return s.report


def main():
    a = sys.argv[1:]
    if len(a) < 3: sys.exit(__doc__)
    plan = json.load(open(a[0], encoding="utf8"))
    name = a[a.index("--seq-name") + 1] if "--seq-name" in a else "EDICAO Claude (FilmCraft)"
    b = Builder(plan, a[1], a[2], name)
    rep = b.build()
    print("projeto:", os.path.abspath(a[2]))
    for r in rep: print("  !", r)
    if "--export" in a:
        rc, out, err = fc.cli("--project", os.path.abspath(a[2]), "export", os.path.abspath(a[a.index("--export") + 1]), "--allow-offline")
        print("export:", rc, (out or err)[-300:])
    if "--open" in a: fc.open_app(os.path.abspath(a[2]))


if __name__ == "__main__":
    main()
