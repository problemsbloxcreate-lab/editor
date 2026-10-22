"""Monta a edição no Premiere (MCP Bridge) a partir de um plan3.json — v3 (16/10/2026), padrão medido na sequência "teste corrigido" do Matheus.

Uso: python build_edit3.py <plan3.json> <SEQUENCE_ID> [--import] [--export out.mp4] [--stop-after bN] [--only b3a,b9]

Novidades da v3 (sobre build_edit2.py):
 - keeps com 'xf_prev': Transição de áudio "Potência constante" (0.2 s centrada no corte) nas 3 faixas do bruto (stage b9_xfade) — é o que deixa os cortes apertados (hand-off ~0 s) soarem limpos;
 - fx: curvas por evento com foco por chave ([dt, scale, curv, tint, vig, fx?, fy?]) -> zoom que ACOMPANHA o personagem; ease-out amostrado (zoom rápido que decai e FICA até o próximo corte; sem "zoom e volta");
 - 'stretch': escala NÃO uniforme (ex.: 391x258) para a distorção da pergunta retórica/gag; 'presets': presets BERSERKER (Lava's ...) recriados via berserker.py (flash, shake, VHS...);
 - música: tl_out explícito (silêncio de record-scratch), 'entry' (entrada mais alta nos primeiros s), sem duck por padrão; SFX: abs_db (nível absoluto exibido) e src_off;
 - tudo editável; marcadores com o porquê.

plan3.json (tempos em s de TIMELINE, exceto src_*):
  src_full true -> bruto 1920x1080 de quadro inteiro (OBS sem a câmera ao lado; ex. "Programei trolagem" 21/10): Posição base [.5,.5] e zoom/stretch com o pivô certo
  keeps    [{src_in, src_out, tl_in, tl_out, xf_prev?}]      (splits contíguos já incluídos)
  music    [{file, tl_in, tl_out?, src_in?, gain_db, fade_in?, fade_out?, entry?:[boost_db, dur]}]
  sfx      [{file, tl, dur?, src_off?, gain_db? | rms_db?(+peak_cap?) | peak_db? | rel_db? | abs_db?, cut?, pre?, why}]
           ganho FIXO no clipe (NUNCA keyframe): sem gain_db usa a tabela GAIN_DB do sfx_levels.py (valores do Matheus) e, p/ arquivo novo, a regra por duração.
           cut:true -> ENCOSTA o SFX no corte mais próximo (±1.5 s): tl = corte - pre (pre padrão 0.06 s) — padrão dele: SFX nasce no corte, não no meio da palavra.
  fx       [{t, fx?, fy?, keys:[[dt, scale, curv, tint, vig, fx?, fy?]], why}]     (eventos não podem se sobrepor)
  stretch  [{tl, sx, sy, fx, fy}]                         (clipe V1 que COMEÇA em tl)
  presets  [{name, tl, anchor?}]                           (clipe V1 que COMEÇA em tl; anchor 'start'|'end')
  mutes    [{track:1|2, a, b, why}]                       (desabilita clipes de A2 call / A3 jogo que COMEÇAM em [a,b); A1 = voz principal nunca)
  reveals  [{tl, kind:'sparkle'|'tilt', pos?, area?, gdur?, scale?, rot?, sat?}]   (clipe V1 que COMEÇA em tl; sparkle = Brilho cintilante; tilt = encolhe+gira+dessatura; ver stage b6f)
  stickers [{file, tl, dur, pos, scale, rot?, v, fade?, opacity?}]
  futuros  [{file, tl, dur, off?, zoom?:[s0,s1], preset_in?, preset_out?, why}]   ("takes futuros": clipes de VÍDEO SÓ (sem áudio!) em V2 com filtro flashback; ver stage b6c)
  brolls   [{file, tl, dur, off?, v?:3, pos?:[x,y], scale?, flash?:[amt0, dur], echo?:{at, dur, op, scale:[s0,s1], sdur, odur, blend?}, why}]
           B-ROLL CINEMÁTICO (render do CineCam / skill minecraft-cinematic; vídeo-só) em V3 POR CIMA do jogo — padrão dele (16/10); ver stage b6h e references/feedback-timeline-dele-16out.md.
           flash = Tonalidade branco->branco com quantidade amt0 -> 0 em dur s (lavagem branca que some: revelação). echo = cópia do trecho em V+1 (opacidade op->0 em odur, escala s0->s1 em sdur, modo de mesclagem 'blend').
           Combine com plan['mutes'] (silencie A2/A3 do bruto sob o B-roll) e com SFX de pacote (whoosh 0,4 s antes + impacto no início).
  marks    [{tl, txt}]   boost_voice_db, boost_music_db, limiter, dur_tl, xf_frames (padrão 12)
"""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import berserker as bz
BRIDGE = os.path.join(HERE, "run_bridge.py")
SFXLIB = os.path.join(HERE, "..", "library", "sfx")
SFX_TARGET_LUFS = -26.0
lin = lambda db: 10 ** ((db - 15) / 20.0)
J = json.dumps

PRE = '''var p = app.project; var WID = %s;
var s = null; for (var i = 0; i < p.sequences.numSequences; i++) if (p.sequences[i].sequenceID == WID) s = p.sequences[i];
p.openSequence(WID);
function find(n) { for (var i = 0; i < p.rootItem.children.numItems; i++) if (p.rootItem.children[i].name == n) return p.rootItem.children[i]; return null; }
function lvl(c) { return c.components[0].properties[1]; }
var r = {};
'''


def only_ok(name):
    if "--only" in sys.argv:
        return any(name.startswith(x) for x in sys.argv[sys.argv.index("--only") + 1].split(","))
    return True


import pr_names


def run(jsx, name, timeout=300):
    if not only_ok(name): return ""
    path = os.path.join(os.getcwd(), name + ".jsx")
    open(path, "w", encoding="utf8").write(pr_names.wrap(jsx))      # Premiere em qualquer idioma (nomes PT -> nomes desta máquina)
    out = subprocess.run([sys.executable, BRIDGE, path, str(timeout)], capture_output=True, text=True, encoding="utf8")
    if out.returncode != 0:
        raise SystemExit(name + " FALHOU: " + (out.stderr or out.stdout)[-800:])
    print(name, "ok:", out.stdout.strip()[:300])
    if "--stop-after" in sys.argv and name.startswith(sys.argv[sys.argv.index("--stop-after") + 1]):
        print("parando após", name); sys.exit(0)
    return out.stdout


import sfx_timing as _sfxt
from sfx_levels import gain_for, table_gain     # ganho ESTÁTICO dos SFX (tabela calibrada pelo Matheus em 15/10; ver sfx_levels.py)


def sfx_meta(name):
    idx = json.load(open(os.path.join(SFXLIB, "index.json"), encoding="utf8"))
    m = idx.get(name, {})
    if m.get("lufs") is not None and m.get("dur") is not None: return m["lufs"], m["dur"]
    raise SystemExit("SFX sem lufs/dur no index.json: " + name)


_pk_cache = {}


def sfx_levels(path, off=0.0, dur=None):
    """(pico dBFS, RMS 'ativo' dBFS) do trecho realmente usado do SFX. RMS ativo = RMS dos quadros de 20 ms que estão a <=35 dB do quadro mais forte
    (SFX esparsos/tonais como o orb do XP têm pico alto e RMS baixo: normalizar por PICO os deixa inaudíveis — erro medido em 15/10). Pico = total do trecho (SFX não têm fade/keyframe no Premiere)."""
    import wave, tempfile
    import numpy as np
    key = (path, round(off, 3), None if dur is None else round(dur, 3))
    if key in _pk_cache: return _pk_cache[key]
    # 21/10: PCM pelo pipe (antes um WAV temporário de nome fixo no C: — dois jobs ao mesmo tempo se atropelavam)
    cmd = ["ffmpeg", "-loglevel", "error"] + (["-ss", str(off)] if off else []) + (["-t", str(dur)] if dur else []) + ["-i", path, "-vn", "-ac", "1", "-ar", "44100", "-f", "f32le", "-"]
    d = np.clip(np.frombuffer(subprocess.run(cmd, check=True, capture_output=True).stdout, dtype=np.float32), -1, 1).astype(np.float64)   # = o int16 de antes (calibração igual)
    if len(d) < 441: _pk_cache[key] = (-6.0, -20.0); return _pk_cache[key]
    pk = 20 * np.log10(np.abs(d).max() + 1e-9)       # SFX entram SEM fade (sem keyframe): o clique inicial conta (os orbs do XP já têm 10 ms de fade-in embutido no mp3)
    hop = 882; n = len(d) // hop
    fr = np.array([np.sqrt((d[i * hop:(i + 1) * hop] ** 2).mean()) for i in range(max(n, 1))])
    act = fr > fr.max() * 10 ** (-35 / 20.0)
    rms = 20 * np.log10(np.sqrt((fr[act] ** 2).mean()) + 1e-9)
    _pk_cache[key] = (float(pk), float(rms))
    return _pk_cache[key]


def sfx_peak(path, off=0.0, dur=None):
    return sfx_levels(path, off, dur)[0]


def interp(keys, t):
    """keys = [(t, s, curv, tint, vig, fx, fy)] ordenado; linear em t (segura nas pontas)"""
    if t <= keys[0][0]: return keys[0][1:]
    if t >= keys[-1][0]: return keys[-1][1:]
    for a, b in zip(keys, keys[1:]):
        if a[0] <= t <= b[0]:
            u = 0 if b[0] == a[0] else (t - a[0]) / (b[0] - a[0])
            return tuple(a[i] + (b[i] - a[i]) * u for i in range(1, 7))


OX = 0.0   # 0 = bruto 3840x1080 com o jogo na metade direita (Posição [0, .5]); 960 = bruto 1920x1080 de quadro inteiro (plan['src_full'], Posição [.5, .5]) — 21/10/2026


def fx_clips(plan):
    keeps = plan["keeps"]
    evs = []
    for e in plan.get("fx", []):
        dfx, dfy = e.get("fx", 960), e.get("fy", 540)
        rows = [list(k) + [0, 0, 0][:max(0, 5 - len(k))] for k in e["keys"]]      # [dt, scale] basta; curv/tint/vig = 0
        pts = [(e["t"] + k[0], float(k[1]), float(k[2]), float(k[3]), float(k[4]), float(k[5]) if len(k) > 5 else dfx, float(k[6]) if len(k) > 6 else dfy) for k in rows]
        evs.append({"pts": pts, "why": e.get("why", "")})
    evs.sort(key=lambda e: e["pts"][0][0])
    for a, b in zip(evs, evs[1:]):
        assert a["pts"][-1][0] <= b["pts"][0][0] + 1e-3, "fx sobrepostos: %s (%.2f) / %s (%.2f)" % (a["why"], a["pts"][-1][0], b["why"], b["pts"][0][0])
    out = {}
    for ci, k in enumerate(keeps):
        rows = []
        for e in evs:
            t0, t1 = e["pts"][0][0], e["pts"][-1][0]
            if t1 <= k["tl_in"] + 1e-6 or t0 >= k["tl_out"] - 1e-6: continue
            ts = sorted({max(t0, k["tl_in"]), min(t1, k["tl_out"])} | {p[0] for p in e["pts"] if k["tl_in"] < p[0] < k["tl_out"]})
            for t in ts:
                s, curv, tint, vig, fx, fy = interp(e["pts"], t)
                sp = s / 100.0
                x = (fx * (1 - sp) + OX * sp) / 1920.0
                y = (fy - sp * (fy - 540)) / 1080.0
                rows.append([round(k["src_in"] + (t - k["tl_in"]), 5), round(s, 3), round(x, 5), round(y, 5), round(curv, 3), round(tint, 2), round(vig, 3)])
        if rows: out[ci] = rows
    return out


def clip_at(keeps, tl):
    for i, k in enumerate(keeps):
        if abs(k["tl_in"] - tl) < 0.02: return i
    raise SystemExit("nenhum clipe V1 começa em tl=%.3f" % tl)


def main():
    global OX
    plan = json.load(open(sys.argv[1], encoding="utf8"))
    wid = sys.argv[2]
    OX = 960.0 if plan.get("src_full") else 0.0
    pre = PRE % J(wid)
    master = plan.get("master_db", 0.0)            # música+SFX (o render do Matheus fica ~-18 LUFS/-3.9 dBFS: master_db -4 + limiter 0.58 na voz)
    boost_v = plan.get("boost_voice_db", 9.0)      # voz: o nível final é ditado pelo Limitador pesado (amplitude máxima) -> baixe 'limiter', não o ganho
    boost_m = plan.get("boost_music_db", 3.0) + master
    item_prefix = plan.get("bruto_prefix", "2026-10-08")
    keeps = plan["keeps"]
    if "--import" in sys.argv:
        files = sorted({m["file"] for m in plan["music"]} | {x["file"] for x in plan["sfx"]} | {x["file"] for x in plan.get("stickers", [])} | {x["file"] for x in plan.get("futuros", [])} | {x["file"] for x in plan.get("brolls", [])})
        for f in files:
            assert os.path.exists(f), "arquivo inexistente (trava o Premiere com diálogo!): " + f
        run(pre + "r.imp = p.importFiles(%s, true, p.rootItem, false); return __result(r);" % J(files), "b0_import", 240)
    # 1) limpar + segmentos
    segs = [[k["src_in"], k["src_out"], k["tl_in"]] for k in keeps]
    run(pre + '''function clr(tr) { for (var i = tr.clips.numItems - 1; i >= 0; i--) tr.clips[i].remove(0, 0); }
for (var v = 0; v < s.videoTracks.numTracks; v++) clr(s.videoTracks[v]);
for (var a = 0; a < s.audioTracks.numTracks; a++) clr(s.audioTracks[a]);
var m0 = s.markers.getFirstMarker(); while (m0) { s.markers.deleteMarker(m0); m0 = s.markers.getFirstMarker(); }
var item = null; for (var i = 0; i < p.rootItem.children.numItems; i++) if (p.rootItem.children[i].name.indexOf(%s) == 0 && p.rootItem.children[i].type == 1) { item = p.rootItem.children[i]; break; }
var segs = %s;
for (var k = 0; k < segs.length; k++) { item.setInPoint(segs[k][0], 4); item.setOutPoint(segs[k][1], 4); s.videoTracks[0].overwriteClip(item, segs[k][2]); }
item.clearInPoint(); item.clearOutPoint();
function fix(tr) { for (var k = 0; k + 1 < tr.clips.numItems; k++) { var g = tr.clips[k + 1].start.seconds - tr.clips[k].end.seconds; if (g > 0.0005 && g < 0.5) { var e = new Time(); e.seconds = tr.clips[k + 1].start.seconds; tr.clips[k].end = e; } } }   // vão >= 0,5 s = buraco proposital (promo/tela final entram depois)
fix(s.videoTracks[0]); for (var t = 0; t < 3; t++) fix(s.audioTracks[t]);
r.v1 = s.videoTracks[0].clips.numItems; r.a1 = s.audioTracks[0].clips.numItems; r.itemName = item.name; return __result(r);''' % (J(item_prefix), J(segs)), "b1_segments", 900)
    # 2) faixas extras (V: 3 mínimas; brolls pedem V3 (+V4 se tiver 'echo'))
    NV = max([3, plan.get("vtracks", 3)] + [x.get("v", 3) + (1 if x.get("echo") else 0) for x in plan.get("brolls", [])])
    NA = 4 + plan.get("sfx_tracks", 3)
    run(pre + '''if (s.audioTracks.numTracks < %d) { app.enableQE(); var q = qe.project.getActiveSequence(); q.addTracks(0, 0, %d - s.audioTracks.numTracks, 0, s.audioTracks.numTracks - 1, 0, 0, 0); }
if (s.videoTracks.numTracks < %d) { app.enableQE(); var q2 = qe.project.getActiveSequence(); q2.addTracks(%d - s.videoTracks.numTracks, s.videoTracks.numTracks, 0, 0, 0, 0, 0, 0); }
r.n = s.audioTracks.numTracks; r.vn = s.videoTracks.numTracks; return __result(r);''' % ((NA, NA, NV, NV)), "b2_tracks", 60)
    # 3) enquadramento base + zoom
    FX = fx_clips(plan)
    need_lens = sorted(i for i, rows in FX.items() if any(abs(r[4]) > 1e-6 for r in rows))
    need_tint = sorted(i for i, rows in FX.items() if any(r[5] > 1e-6 for r in rows))
    run(pre + '''var tr = s.videoTracks[0]; var FX = %s;
for (var c = 0; c < tr.clips.numItems; c++) { var mo = tr.clips[c].components[1]; mo.properties[1].setTimeVarying(false); mo.properties[0].setTimeVarying(false); mo.properties[1].setValue(100, true); mo.properties[0].setValue([%s, 0.5], true); }
for (var ci in FX) { var rows = FX[ci]; var mo2 = tr.clips[parseInt(ci)].components[1]; var sc = mo2.properties[1], ps = mo2.properties[0];
  sc.setTimeVarying(true); ps.setTimeVarying(true);
  for (var k = 0; k < rows.length; k++) { var f = rows[k]; sc.addKey(f[0]); sc.setValueAtKey(f[0], f[1]); ps.addKey(f[0]); ps.setValueAtKey(f[0], [f[2], f[3]]); } }
return __result(r);''' % (J(FX), OX / 1920.0), "b3a_zoom", 900)
    # 3b) escala não uniforme (distorção de pergunta retórica / gag)
    if plan.get("stretch"):
        ST = []
        for x in plan["stretch"]:
            ci = clip_at(keeps, x["tl"]); sx, sy = x["sx"] / 100.0, x["sy"] / 100.0
            ST.append({"ci": ci, "sx": x["sx"], "sy": x["sy"], "px": round((x["fx"] * (1 - sx) + OX * sx) / 1920.0, 5), "py": round((x["fy"] - sy * (x["fy"] - 540)) / 1080.0, 5)})
        run(pre + '''var tr = s.videoTracks[0]; var ST = %s;
for (var n = 0; n < ST.length; n++) { var mo = tr.clips[ST[n].ci].components[1];
  mo.properties[1].setTimeVarying(false); mo.properties[0].setTimeVarying(false);
  mo.properties[3].setValue(false, true); mo.properties[1].setValue(ST[n].sy, true); mo.properties[2].setValue(ST[n].sx, true); mo.properties[0].setValue([ST[n].px, ST[n].py], true); }
return __result(r);''' % J(ST), "b3b_stretch", 120)
    if "--no-names" not in sys.argv and only_ok("b3c_names"):      # V1 já montada: confere/descobre os nomes dos efeitos neste Premiere
        try: pr_names.ensure(log=lambda m: print(m))
        except Exception as e: print("aviso pr_names.ensure:", str(e)[:300])
    for name, idxs, match, prop, col, fxname in (("b3c_lens", need_lens, "PR.ADBE Lens Distortion", 0, 4, "Distorção de lente"),
                                                  ("b3d_tint", need_tint, "AE.ADBE Tint", 2, 5, "Tonalidade")):
        if not idxs: continue
        run(pre + '''app.enableQE(); var q = qe.project.getActiveSequence(); var FX = %s; var IDX = %s; var tr = s.videoTracks[0];
var fxo = qe.project.getVideoEffectByName(%s);
for (var n = 0; n < IDX.length; n++) { var ci = IDX[n]; q.getVideoTrackAt(0).getItemAt(ci).addVideoEffect(fxo);
  var cl = tr.clips[ci]; var comp = null; for (var cc = 0; cc < cl.components.numItems; cc++) if (cl.components[cc].matchName == %s) comp = cl.components[cc];
  var pr = comp.properties[%d]; pr.setTimeVarying(true); var rows = FX[ci];
  for (var k = 0; k < rows.length; k++) { pr.addKey(rows[k][0]); pr.setValueAtKey(rows[k][0], %s); } }
r.n = IDX.length; return __result(r);''' % (J(FX), J(idxs), J(fxname), J(match), prop, "rows[k][%d]" % col), name, 600)
    # 3e) presets BERSERKER
    if plan.get("presets"):
        SP = []
        for x in plan["presets"]:
            ci = clip_at(keeps, x["tl"]); k = keeps[ci]
            SP.append(bz.spec(x["name"], ci, k["src_in"], k["tl_out"] - k["tl_in"], anchor=x.get("anchor"), t_start=x.get("t_start", 0.0)))
        run(pre + '''app.enableQE(); var q = qe.project.getActiveSequence(); var tr = s.videoTracks[0];
''' + bz.APPLY_JS % J(SP) + '''return __result(r);''', "b3e_presets", 900)
    # 4) música A4
    ms = plan["music"]
    M = []
    for i, m in enumerate(ms):
        end = m.get("tl_out", ms[i + 1]["tl_in"] if i + 1 < len(ms) else plan["dur_tl"])
        g = lin(m["gain_db"] + boost_m)
        M.append({"name": os.path.basename(m["file"]), "a": round(m["tl_in"], 5), "b": round(end, 5), "g": g, "off": m.get("src_in", 0.0),
                  "fin": m.get("fade_in", 0.08), "fout": m.get("fade_out", 0.15),
                  "entry": [lin(m["gain_db"] + boost_m + m["entry"][0]), m["entry"][1]] if m.get("entry") else None})
    FADE = '''function fades(c, g, tin, tout) { var pr = lvl(c); pr.setTimeVarying(true); var z = 0.0005; var dur = c.end.seconds - c.start.seconds;
  var t0 = c.inPoint.seconds; var pts = [[t0, z], [t0 + tin, g], [t0 + dur - tout, g], [t0 + dur, z]];
  for (var i = 0; i < pts.length; i++) { pr.addKey(pts[i][0]); pr.setValueAtKey(pts[i][0], pts[i][1]); } }
'''
    run(pre + FADE + '''var mt = s.audioTracks[3]; var M = %s;
for (var k = 0; k < M.length; k++) { var it = find(M[k].name); it.setInPoint(M[k].off, 4); it.setOutPoint(M[k].off + M[k].b - M[k].a, 4); mt.overwriteClip(it, M[k].a); it.clearInPoint(); it.clearOutPoint(); }
for (var k2 = 0; k2 < M.length; k2++) { var e = new Time(); e.seconds = M[k2].b; mt.clips[k2].end = e; }
for (var k3 = 0; k3 < M.length; k3++) { var c3 = mt.clips[k3]; var pr3 = lvl(c3); pr3.setTimeVarying(true); var z = 0.0005; var dur3 = c3.end.seconds - c3.start.seconds; var t0 = c3.inPoint.seconds;
  var pts = M[k3].entry ? [[0, z], [M[k3].fin, M[k3].entry[0]], [M[k3].entry[1], M[k3].entry[0]], [M[k3].entry[1] + 1.2, M[k3].g]] : [[0, z], [M[k3].fin, M[k3].g]];
  pts.push([dur3 - M[k3].fout, M[k3].g]); pts.push([dur3, z]);
  for (var i = 0; i < pts.length; i++) { pr3.addKey(t0 + pts[i][0]); pr3.setValueAtKey(t0 + pts[i][0], pts[i][1]); } }
r.n = mt.clips.numItems; return __result(r);''' % J(M), "b4_music", 600)
    # 5) SFX A5..A7
    SFXT = tuple(range(4, 4 + plan.get("sfx_tracks", 3)))      # A5.. (padrão 3 faixas; motion/cards com pacote de SFX pedem mais)
    F, busy = [], {t: -1.0 for t in SFXT}
    cuts = [k["tl_in"] for k in keeps[1:]]
    for x in plan["sfx"]:
        if x.get("cut") and cuts:
            b = min(cuts, key=lambda c: abs(c - x["tl"]))
            if abs(b - x["tl"]) <= 1.5: x["tl"] = max(0.0, b - x.get("pre", 0.06))
    for x in sorted(plan["sfx"], key=lambda x: x["tl"]):
        nm = os.path.basename(x["file"]); l, d0 = sfx_meta(nm); l = max(l, -35.0); off = x["src_off"] if "src_off" in x else (0.0 if x.get("no_trim") else _sfxt.file_onset(x["file"])); d = min(x.get("dur", min(d0 - off, 2.5)), d0 - off)   # apara o silêncio inicial do arquivo (0,03-0,18 s): o som começa NO clipe
        tr = next(t for t in SFXT if busy[t] <= x["tl"] + 1e-6)
        busy[tr] = x["tl"] + d
        if "peak_db" in x:      # legado v4: pico FINAL no mix
            g = lin(x["peak_db"] - sfx_peak(x["file"], off, d))
        elif "abs_db" in x or "rel_db" in x:   # legado v3
            g = lin(x["abs_db"] + master) if "abs_db" in x else lin(SFX_TARGET_LUFS + boost_m - l + x.get("rel_db", 0.0))
        else:                   # atual: gain_db explícito > rms_db(+peak_cap) > tabela dele (GAIN_DB) > regra por duração
            if "rms_db" not in x and "gain_db" not in x and table_gain(nm) is not None:   # tabela dele: não precisa medir o arquivo
                gdb = table_gain(nm)
            else:
                pk, rm = sfx_levels(x["file"], off, d)
                gdb, _src = gain_for(nm, pk, rm, d, x)
            g = lin(gdb)
        F.append({"name": nm, "t": round(x["tl"], 5), "dur": d, "off": off, "tr": tr, "g": g})
    run(pre + '''var F = %s; var cnt = {};
for (var q = 0; q < F.length; q++) { var it = find(F[q].name); var st = s.audioTracks[F[q].tr]; it.setInPoint(F[q].off, 4); it.setOutPoint(F[q].off + F[q].dur, 4); st.overwriteClip(it, F[q].t); it.clearInPoint(); it.clearOutPoint();
  var cl = null; for (var c = 0; c < st.clips.numItems; c++) if (Math.abs(st.clips[c].start.seconds - F[q].t) < 0.01) cl = st.clips[c];
  if (cl) { var pr = lvl(cl); pr.setTimeVarying(false); pr.setValue(F[q].g, true); }   // ganho FIXO: nunca keyframe em SFX (pedido do Matheus 15/10)
  cnt[F[q].tr] = (cnt[F[q].tr] || 0) + 1; }
r.cnt = cnt; return __result(r);''' % J(F), "b5_sfx", 900)
    # 6a) limitador nas 3 faixas do bruto
    run(pre + '''app.enableQE(); var q = qe.project.getActiveSequence(); var fx = qe.project.getAudioEffectByName("Limitador pesado"); var n = 0;
for (var t = 0; t < %d; t++) { var tr = s.audioTracks[t]; var qt = q.getAudioTrackAt(t); var map = []; for (var qi = 0; qi < qt.numItems; qi++) if (String(qt.getItemAt(qi).type) != "Empty") map.push(qi);
  for (var k = 0; k < tr.clips.numItems; k++) { qt.getItemAt(map[k]).addAudioEffect(fx);
    var c = tr.clips[k]; for (var cc = 0; cc < c.components.numItems; cc++) if (c.components[cc].matchName == "e0b23f05-f1a7-4ef7-9b50-7ec3e3002058") { c.components[cc].properties[1].setValue(%s, true); n++; }
    c.components[0].properties[1].setValue(%s, true); } }
r.limiters = n; return __result(r);''' % (plan.get("limiter_tracks", 3), plan.get("limiter", 0.92), lin(boost_v)), "b6a_limiter", 1800)
    # 6b) stickers (spotlight etc.)
    if plan.get("stickers"):
        ST = [{"name": os.path.basename(x["file"]), "t": round(x["tl"], 5), "dur": x["dur"], "pos": x["pos"], "sc": x["scale"], "rot": x.get("rot", 0), "v": x.get("v", 2) - 1, "fade": x.get("fade", 0), "op": x.get("opacity", 100)} for x in plan["stickers"]]
        run(pre + '''var ST = %s;
for (var k = 0; k < ST.length; k++) { var vt = s.videoTracks[ST[k].v]; var it = find(ST[k].name); vt.overwriteClip(it, ST[k].t);
  var c = null; for (var j = 0; j < vt.clips.numItems; j++) if (Math.abs(vt.clips[j].start.seconds - ST[k].t) < 0.01) c = vt.clips[j];
  var e = new Time(); e.seconds = ST[k].t + ST[k].dur; c.end = e; var mo = c.components[1]; mo.properties[0].setValue(ST[k].pos, true);
  var sc = mo.properties[1]; var rt = mo.properties[4]; var t0 = c.inPoint.seconds; var S = ST[k].sc, R = ST[k].rot, D = ST[k].dur;
  if (ST[k].fade > 0) { sc.setTimeVarying(false); sc.setValue(S, true); rt.setTimeVarying(false); rt.setValue(R, true); var op = c.components[0].properties[0]; op.setTimeVarying(true); var F = ST[k].fade;
    var OK = [[0, 0], [F, ST[k].op], [D - F, ST[k].op], [D, 0]]; for (var o = 0; o < OK.length; o++) { op.addKey(t0 + OK[o][0]); op.setValueAtKey(t0 + OK[o][0], OK[o][1]); } continue; }
  sc.setTimeVarying(true); rt.setTimeVarying(true);
  var K = [[0, 0, R - 8], [0.10, S * 1.22, R + 4], [0.20, S * 0.94, R - 2], [0.30, S, R], [D - 0.18, S, R + 1], [D, 0, R + 6]];
  for (var q = 0; q < K.length; q++) { sc.addKey(t0 + K[q][0]); sc.setValueAtKey(t0 + K[q][0], K[q][1]); rt.addKey(t0 + K[q][0]); rt.setValueAtKey(t0 + K[q][0], K[q][2]); } }
r.n = ST.length; return __result(r);''' % J(ST), "b6b_stickers", 300)
    # 6c) "takes futuros": clipes de vídeo-só em V2 com filtro flashback (Lumetri lavado/quente + vinheta) + zoom lento + flashes BERSERKER nas pontas
    if plan.get("futuros"):
        FU = [{"name": os.path.basename(x["file"]), "t": round(x["tl"], 5), "dur": x["dur"], "off": x.get("off", 0.0), "z": x.get("zoom", [100, 106])} for x in plan["futuros"]]
        for x in FU: assert os.path.exists(next(y["file"] for y in plan["futuros"] if os.path.basename(y["file"]) == x["name"])), x["name"]
        run(pre + '''var FU = %s; var vt = s.videoTracks[1]; var n = 0;
for (var k = 0; k < FU.length; k++) { var it = find(FU[k].name); it.setInPoint(FU[k].off, 4); it.setOutPoint(FU[k].off + FU[k].dur, 4); vt.overwriteClip(it, FU[k].t); it.clearInPoint(); it.clearOutPoint();
  var c = null; for (var j = 0; j < vt.clips.numItems; j++) if (Math.abs(vt.clips[j].start.seconds - FU[k].t) < 0.01) c = vt.clips[j];
  var e = new Time(); e.seconds = FU[k].t + FU[k].dur; c.end = e; var mo = c.components[1]; var sc = mo.properties[1]; var t0 = c.inPoint.seconds;
  sc.setTimeVarying(true); sc.addKey(t0); sc.setValueAtKey(t0, FU[k].z[0]); sc.addKey(t0 + FU[k].dur); sc.setValueAtKey(t0 + FU[k].dur, FU[k].z[1]); n++; }
r.n = n; r.v3 = vt.clips.numItems; return __result(r);''' % J(FU), "b6c_futuros", 600)
        LUM = plan.get("flashback_lumetri", {"14": 25, "16": 62, "19": 0.5, "20": -8, "22": 15, "23": -8, "24": 25, "40": 35, "110": -2.0, "111": 40, "113": 75})
        TINT = plan.get("flashback_tint", {"b": [255, 64, 38, 14], "w": [255, 255, 240, 205], "amt": 48})       # sépia: preto->marrom, branco->creme
        order = [x for x in sorted(plan["futuros"], key=lambda x: x["tl"])]
        ci = lambda tl: next(i for i, x in enumerate(order) if abs(x["tl"] - tl) < 1e-6)
        run(pre + '''app.enableQE(); var q = qe.project.getActiveSequence(); var vt = s.videoTracks[1]; var LUM = %s; var TINT = %s; var n = 0;
var qt = q.getVideoTrackAt(1); var kk = 0;
for (var i = 0; i < qt.numItems; i++) { var qi = qt.getItemAt(i); if (String(qi.type) == "Empty") continue; qi.addVideoEffect(qe.project.getVideoEffectByName("Cor de Lumetri")); var L = EP_comp(vt.clips[kk], "Cor de Lumetri");
  for (var key in LUM) { try { L.properties[parseInt(key)].setValue(LUM[key], true); n++; } catch (e) { r.err = (r.err || "") + key + ":" + e + " "; } }
  qi.addVideoEffect(qe.project.getVideoEffectByName("Tonalidade")); var T = EP_comp(vt.clips[kk], "Tonalidade"); kk++;
  try { T.properties[0].setColorValue(TINT.b[0], TINT.b[1], TINT.b[2], TINT.b[3], true); T.properties[1].setColorValue(TINT.w[0], TINT.w[1], TINT.w[2], TINT.w[3], true); T.properties[2].setValue(TINT.amt, true); n++; } catch (e2) { r.err = (r.err || "") + "tint:" + e2 + " "; } }
r.n = n; return __result(r);''' % (J(LUM), J(TINT)), "b6d_flashback", 600)
        SP = []
        for x in order:
            k = ci(x["tl"]); dur = x["dur"]
            for nm, anc in ((x.get("preset_in"), "start"), (x.get("preset_out"), "end")):
                if nm: SP.append(bz.spec(nm, k, x.get("off", 0.0), dur, anchor=anc, tscale=x.get("flash_scale", 0.45)))
        if SP:
            run(pre + '''app.enableQE(); var q = qe.project.getActiveSequence(); var TRK = 1; var tr = s.videoTracks[1];
''' + bz.APPLY_JS % J(SP) + '''return __result(r);''', "b6e_flashes", 600)
    # 6f) reveals — receitas copiadas da timeline do Matheus (15/10): 'sparkle' = Brilho cintilante (Glint) com a área crescendo 6->19 (o push-in 100->122 % vai em plan['fx']) + SFX anime-shine + troca de música;
    #     'tilt' = o clipe ENCOLHE 100->71 % girando 0->-3.2 deg e dessatura 100->27 (pivô no centro do quadro: âncora 0.75/0.5 no bruto 3840x1080) — piada "dutch/murchar". O clipe tem de COMEÇAR em tl (use split_at no plano).
    if plan.get("reveals"):
        RV = []
        for x in plan["reveals"]:
            ci = clip_at(keeps, x["tl"]); k = keeps[ci]
            RV.append({"ci": ci, "kind": x["kind"], "dur": round(k["tl_out"] - k["tl_in"], 5), "scale": x.get("scale", 71), "rot": x.get("rot", -3.2), "sat": x.get("sat", 27),
                       "pos": x.get("pos", [0.752, 0.459]), "area": x.get("area", [6, 19.2]), "gdur": x.get("gdur", 1.2)})
        GLV = plan.get("glint_params", {"Intensidade": 49.3, "Apenas os destaques": 41, "Especular": 7, "Difusão": 128, "Brilho": 100, "Velocidade do brilho": 100, "Ângulo": 372.5,
                                         "Escala de resplendor": 25, "Escala cruzada": 93, "Escala de resplendor 1": 50, "Escala de resplendor 2": 40, "Escala cruzada 1": 75, "Escala cruzada 2": 65,
                                         "Forma": 11, "Colorir": 93, "Variação de cor": 13, "Velocidade de variação": 2, "Remover saturação": 0, "Aberração Cromática": 37, "Modo de mesclagem": 1})
        run(pre + '''app.enableQE(); var q = qe.project.getActiveSequence(); var tr = s.videoTracks[0]; var RV = %s; var GLV = %s; r.fail = []; r.n = 0;
function comp(c, nm) { return EP_comp(c, nm); }
for (var i = 0; i < RV.length; i++) { var R = RV[i]; var c = tr.clips[R.ci]; var t0 = c.inPoint.seconds; var qi = q.getVideoTrackAt(0).getItemAt(R.ci);
  if (R.kind == "tilt") {
    var mo = c.components[1]; mo.properties[1].setTimeVarying(false); mo.properties[0].setTimeVarying(false);
    mo.properties[5].setValue([0.75, 0.5], true); mo.properties[0].setValue([0.5, 0.5], true);
    var sc = mo.properties[1], rt = mo.properties[4];
    sc.setTimeVarying(true); sc.addKey(t0); sc.setValueAtKey(t0, 100); sc.addKey(t0 + R.dur); sc.setValueAtKey(t0 + R.dur, R.scale);
    rt.setTimeVarying(true); rt.addKey(t0); rt.setValueAtKey(t0, 0); rt.addKey(t0 + R.dur); rt.setValueAtKey(t0 + R.dur, R.rot);
    qi.addVideoEffect(qe.project.getVideoEffectByName("Cor de Lumetri")); var L = comp(c, "Cor de Lumetri"); if (!L) { r.fail.push("sem Lumetri"); continue; } var sat = L.properties[16];
    sat.setTimeVarying(true); sat.addKey(t0); sat.setValueAtKey(t0, 100); sat.addKey(t0 + R.dur * 0.87); sat.setValueAtKey(t0 + R.dur * 0.87, R.sat); r.n++;
  } else if (R.kind == "sparkle") {
    qi.addVideoEffect(qe.project.getVideoEffectByName("Brilho cintilante")); var G = comp(c, "Brilho cintilante");
    if (!G) { r.fail.push("sem Brilho cintilante neste Premiere"); continue; }
    for (var w = 0; w < G.properties.numItems; w++) { var pp = G.properties[w]; var nm = EP_pt(G, w);
      try {
        if (GLV.hasOwnProperty(nm)) pp.setValue(GLV[nm], true);
        else if (nm == "Posição") pp.setValue(R.pos, true);
        else if (nm == "Área do brilho") { pp.setTimeVarying(true); pp.addKey(t0); pp.setValueAtKey(t0, R.area[0]); pp.addKey(t0 + R.gdur); pp.setValueAtKey(t0 + R.gdur, R.area[1]); }
      } catch (e) { r.fail.push(nm + ":" + e); } } r.n++; } }
return __result(r);''' % (J(RV), J(GLV)), "b6f_reveals", 600)
    # 6g) mutes — padrão dele (15/10): DESABILITA o clipe inteiro (não apaga) da faixa da call (A2) ou do jogo (A3) que disputa com a piada/voz principal; A1 (voz principal) nunca.
    #     plan['mutes'] = [{track: 1|2, a, b, why}]  (índice 0-based da faixa de áudio; todo clipe que começa em [a, b) fica desabilitado)
    if plan.get("mutes"):
        run(pre + '''var MU = %s; r.n = 0;
for (var m = 0; m < MU.length; m++) { var tr = s.audioTracks[MU[m].track];
  for (var c = 0; c < tr.clips.numItems; c++) { var cl = tr.clips[c]; if (cl.start.seconds >= MU[m].a - 0.02 && cl.start.seconds < MU[m].b - 0.02) { cl.disabled = true; r.n++; } } }
return __result(r);''' % J(plan["mutes"]), "b6g_mutes", 300)
    # 6h) B-ROLL cinemático (render do CineCam, vídeo-só) em V3 por cima do jogo — padrão dele (16/10, intro do vídeo da água): o plano b-roll entra na hora da frase que ele ilustra,
    #     cobre o jogo (mute A2/A3 sob ele via plan['mutes']), abre com whoosh/impacto (SFX do plano) e pode ter 'flash' (lavagem branca que decai = Tonalidade branco->branco 70->0 em 0,9 s) e 'echo' (cópia ampliada em V4).
    if plan.get("brolls"):
        BR = [{"name": os.path.basename(x["file"]), "t": round(x["tl"], 5), "dur": x["dur"], "off": x.get("off", 0.0), "v": x.get("v", 3) - 1,
               "pos": x.get("pos"), "scale": x.get("scale"), "flash": x.get("flash"), "echo": x.get("echo")} for x in plan["brolls"]]
        for x in plan["brolls"]: assert os.path.exists(x["file"]), x["file"]
        run(pre + '''var BR = %s; r.n = 0; r.fail = [];
function clipAt(vt, t) { for (var j = 0; j < vt.clips.numItems; j++) if (Math.abs(vt.clips[j].start.seconds - t) < 0.01) return vt.clips[j]; return null; }
function put(vt, it, off, dur, t) { it.setInPoint(off, 4); it.setOutPoint(off + dur, 4); vt.overwriteClip(it, t); it.clearInPoint(); it.clearOutPoint();
  var c = clipAt(vt, t); if (c) { var e = new Time(); e.seconds = t + dur; c.end = e; } return c; }
for (var k = 0; k < BR.length; k++) { var B = BR[k]; var vt = s.videoTracks[B.v]; var it = find(B.name);
  if (!it) { r.fail.push("sem item " + B.name); continue; }
  var c = put(vt, it, B.off, B.dur, B.t); if (!c) { r.fail.push("clip " + B.t); continue; }
  var mo = c.components[1]; if (B.pos) mo.properties[0].setValue(B.pos, true); if (B.scale) mo.properties[1].setValue(B.scale, true);
  if (B.echo) { var E = B.echo; var vt2 = s.videoTracks[B.v + 1]; var c2 = put(vt2, it, B.off + E.at, E.dur, B.t + E.at);
    if (c2) { var t2 = c2.inPoint.seconds; var op = c2.components[0].properties[0]; op.setTimeVarying(true); op.addKey(t2); op.setValueAtKey(t2, E.op); op.addKey(t2 + E.odur); op.setValueAtKey(t2 + E.odur, 0);
      var sc2 = c2.components[1].properties[1]; sc2.setTimeVarying(true); sc2.addKey(t2); sc2.setValueAtKey(t2, E.scale[0]); sc2.addKey(t2 + E.sdur); sc2.setValueAtKey(t2 + E.sdur, E.scale[1]);
      if (E.blend != null) { try { c2.components[0].properties[1].setValue(E.blend, true); } catch (eb) { r.fail.push("blend:" + eb); } } } }
  r.n++; }
return __result(r);''' % J(BR), "b6h_brolls", 600)
        FL = [b for b in BR if b["flash"]]
        if FL:
            run(pre + '''app.enableQE(); var q = qe.project.getActiveSequence(); var FL = %s; r.n = 0; r.fail = [];
for (var k = 0; k < FL.length; k++) { var B = FL[k]; var vt = s.videoTracks[B.v]; var idx = -1;
  for (var j = 0; j < vt.clips.numItems; j++) if (Math.abs(vt.clips[j].start.seconds - B.t) < 0.01) idx = j;
  if (idx < 0) { r.fail.push("sem clip " + B.t); continue; }
  var qt = q.getVideoTrackAt(B.v); var kk = -1;
  for (var i = 0; i < qt.numItems; i++) { var qi = qt.getItemAt(i); if (String(qi.type) == "Empty") continue; kk++; if (kk == idx) { qi.addVideoEffect(qe.project.getVideoEffectByName("Tonalidade")); break; } }
  var c = vt.clips[idx]; var T = EP_comp(c, "Tonalidade");
  if (!T) { r.fail.push("sem Tonalidade " + B.t); continue; }
  T.properties[0].setColorValue(255, 255, 255, 255, true); T.properties[1].setColorValue(255, 255, 255, 255, true);
  var am = T.properties[2]; var t0 = c.inPoint.seconds; am.setTimeVarying(true); am.addKey(t0); am.setValueAtKey(t0, B.flash[0]); am.addKey(t0 + B.flash[1]); am.setValueAtKey(t0 + B.flash[1], 0); r.n++; }
return __result(r);''' % J(FL), "b6i_flash", 300)
    # 7) marcadores
    run(pre + '''var MK = %s; for (var k = 0; k < MK.length; k++) { var mk = s.markers.createMarker(MK[k].t); mk.name = MK[k].txt; mk.comments = MK[k].txt; }
r.n = MK.length; return __result(r);''' % J([{"t": round(m["tl"], 4), "txt": m["txt"]} for m in plan.get("marks", [])]), "b7_marks", 120)
    # 9) transições de áudio Potência constante nos cortes apertados (por último: não desloca índices QE dos passos acima)
    XF = [i for i, k in enumerate(keeps) if k.get("xf_prev")]
    fr = plan.get("xf_frames", 12)
    if XF:
        run(pre + '''app.enableQE(); var q = qe.project.getActiveSequence(); var t = qe.project.getAudioTransitionByName("Potência constante"); var XF = %s; var n = 0;
for (var tt = 0; tt < %d; tt++) { var qt = q.getAudioTrackAt(tt); var map = []; for (var qi = 0; qi < qt.numItems; qi++) if (String(qt.getItemAt(qi).type) != "Empty") map.push(qi);   // QE conta os vãos como itens
  for (var k = 0; k < XF.length; k++) { try { qt.getItemAt(map[XF[k]]).addTransition(t, true, "00:00:00:%02d"); n++; } catch (e) { r.err = (r.err || "") + tt + ":" + XF[k] + " " + e + "; "; } } }
var cnt = []; for (var a = 0; a < 3; a++) cnt.push(s.audioTracks[a].transitions.numItems);
r.n = n; r.cnt = cnt; return __result(r);''' % (J(XF), plan.get("limiter_tracks", 3), fr), "b9_xfade", 900)
    if "--export" in sys.argv:
        outp = sys.argv[sys.argv.index("--export") + 1].replace("\\", "/")
        run(pre + '''s.setInPoint(0); s.setOutPoint(%s);
var preset = new File(%s);   // adobe_presets.py acha o preset em qualquer versão instalada
r.exp = s.exportAsMediaDirect(new File(%s).fsName, preset.fsName, 1); return __result(r);''' % (plan["dur_tl"], J(__import__("adobe_presets").h264_preset() or ""), J(outp)), "b8_export", 3000)


main()
