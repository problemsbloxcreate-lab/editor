"""Monta a edição no Premiere (MCP Bridge) a partir de um plan2.json — v2 (15/10/2026, pós-feedback "nota 4/10").

Uso: python build_edit2.py <plan2.json> <SEQUENCE_ID> [--import] [--export out.mp4] [--stop-after bN]

Diferenças da v1 (build_edit.py):
 - efeitos de vídeo são CURVAS em tempo de TIMELINE ("fx"), amostradas por clipe: um zoom/dolly pode atravessar cortes sem "pulo" de escala;
 - novos efeitos: Tonalidade (P&B por keyframe de "Quantidade de tom"), Distorção de lente (curvatura). Spotlight = PNG radial (spot_dark.png) com fade, NÃO o efeito Vinheta (borra e é imprevisível);
 - stickers com pop + rotação (pergunta retórica = cacho de "?" gigantes, item citado = sticker do item);
 - música com src_in (ponto de entrada na faixa) e fades; SFX em até 3 faixas (A5..A7) p/ não se sobrescreverem;
 - SFX_META vem de library/sfx/index.json (lufs, dur).

plan2.json (tempos em segundos de TIMELINE, exceto src_*):
  keeps   [{src_in, src_out, tl_in, tl_out}]   (use cutengine.tighten; quantize no quadro)
  music   [{file, tl_in, src_in?, gain_db, why}]   (fim = início da próxima; último vai até dur_tl)
  sfx     [{file, tl, dur?, rel_db?, why}]
  ducks   [{tl, dur, depth_db}]
  fx      [{t, kind, fx?, fy?, keys:[[dt, scale, curv, tint, vig], ...], why}]   (scale em %, curv em Lente (neg=abaulado), tint 0-100, vig 0-1)
  stickers[{file, tl, dur, pos:[x,y], scale, rot?, v:2|3, why}]
  marks   [{tl, txt}]
Lições herdadas: keyframes de componente usam tempo da MÍDIA (inPoint + offset); nível de áudio 0 dB = 0.17783; sequência por ID.
"""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
BRIDGE = os.path.join(HERE, "run_bridge.py")
SFXLIB = os.path.join(HERE, "..", "library", "sfx")
OLD_META = {"anime-shine-sound-2.mp3": (-19.2, 2.0), "vine-boom.mp3": (-8.9, 1.25), "fails-ohhhh.mp3": (-13.2, 2.5),
            "anime-wow-sound-effect.mp3": (-15.3, 2.5), "dun-dun-dun-sound-effect-brass_8nFBccR.mp3": (-5.0, 3.0), "erro.mp3": (-13.6, 0.99),
            "record-scratch-2.mp3": (-10.5, 0.78), "jixaw-metal-pipe-falling-sound.mp3": (-11.6, 2.0), "taco-bell-bong-sfx.mp3": (-12.3, 1.9),
            "whoosh-sfx.mp3": (-20.8, 0.97), "bonk_BEtiM8g.mp3": (-17.6, 1.2), "rimshot.mp3": (-10.3, 1.9), "sadtrombone.swf.mp3": (-13.9, 2.5),
            "roblox-death-sound_1.mp3": (-18.8, 1.0)}
SFX_TARGET_LUFS = -23.0
lin = lambda db: 10 ** ((db - 15) / 20.0)
J = json.dumps

PRE = '''var p = app.project; var WID = %s;
var s = null; for (var i = 0; i < p.sequences.numSequences; i++) if (p.sequences[i].sequenceID == WID) s = p.sequences[i];
p.openSequence(WID);
function find(n) { for (var i = 0; i < p.rootItem.children.numItems; i++) if (p.rootItem.children[i].name == n) return p.rootItem.children[i]; return null; }
function lvl(c) { return c.components[0].properties[1]; }
var r = {};
'''


import pr_names


def run(jsx, name, timeout=300):
    path = os.path.join(os.getcwd(), name + ".jsx")
    open(path, "w", encoding="utf8").write(pr_names.wrap(jsx))      # Premiere em qualquer idioma (nomes PT -> nomes desta máquina)
    out = subprocess.run([sys.executable, BRIDGE, path, str(timeout)], capture_output=True, text=True, encoding="utf8")
    if out.returncode != 0:
        raise SystemExit(name + " FALHOU: " + (out.stderr or out.stdout)[-800:])
    print(name, "ok:", out.stdout.strip()[:300])
    if "--stop-after" in sys.argv and name.startswith(sys.argv[sys.argv.index("--stop-after") + 1]):
        print("parando após", name); sys.exit(0)
    return out.stdout


def sfx_meta(name):
    idx = json.load(open(os.path.join(SFXLIB, "index.json"), encoding="utf8"))
    m = idx.get(name, {})
    if m.get("lufs") is not None and m.get("dur") is not None: return m["lufs"], m["dur"]
    return OLD_META[name]


def interp(keys, t):
    """keys = [(t, s, curv, tint, vig)] ordenado; valor interpolado linear em t (segura nas pontas)"""
    if t <= keys[0][0]: return keys[0][1:]
    if t >= keys[-1][0]: return keys[-1][1:]
    for a, b in zip(keys, keys[1:]):
        if a[0] <= t <= b[0]:
            u = 0 if b[0] == a[0] else (t - a[0]) / (b[0] - a[0])
            return tuple(a[i] + (b[i] - a[i]) * u for i in range(1, 5))


def fx_clips(plan):
    """curvas de efeito (tempo de timeline) -> keyframes por clipe (tempo de MÍDIA). Eventos NÃO podem se sobrepor."""
    keeps = plan["keeps"]
    evs = []
    for e in plan.get("fx", []):
        pts = [(e["t"] + k[0], float(k[1]), float(k[2]), float(k[3]), float(k[4])) for k in e["keys"]]
        evs.append({"fx": e.get("fx", 960), "fy": e.get("fy", 540), "pts": pts, "why": e.get("why", "")})
    evs.sort(key=lambda e: e["pts"][0][0])
    for a, b in zip(evs, evs[1:]):
        assert a["pts"][-1][0] <= b["pts"][0][0] + 1e-6, "fx sobrepostos: %s / %s" % (a["why"], b["why"])
    out = {}
    for ci, k in enumerate(keeps):
        rows = []
        for e in evs:
            t0, t1 = e["pts"][0][0], e["pts"][-1][0]
            if t1 <= k["tl_in"] or t0 >= k["tl_out"]: continue
            ts = sorted({max(t0, k["tl_in"]), min(t1, k["tl_out"])} | {p[0] for p in e["pts"] if k["tl_in"] < p[0] < k["tl_out"]})
            for t in ts:
                s, curv, tint, vig = interp(e["pts"], t)
                sp = s / 100.0
                x = e["fx"] * (1 - sp) / 1920.0
                y = (e["fy"] - sp * (e["fy"] - 540)) / 1080.0
                rows.append([round(k["src_in"] + (t - k["tl_in"]), 5), round(s, 3), round(x, 5), round(y, 5), round(curv, 3), round(tint, 2), round(vig, 3)])
        if rows: out[ci] = rows
    return out


def main():
    plan = json.load(open(sys.argv[1], encoding="utf8"))
    wid = sys.argv[2]
    pre = PRE % J(wid)
    boost_v = plan.get("boost_voice_db", 9.0)
    boost_m = plan.get("boost_music_db", 3.0)
    item_prefix = plan.get("bruto_prefix", "2026-10-08")
    keeps = plan["keeps"]
    if "--import" in sys.argv:
        files = sorted({m["file"] for m in plan["music"]} | {x["file"] for x in plan["sfx"]} | {x["file"] for x in plan.get("stickers", [])})
        run(pre + "r.imp = p.importFiles(%s, true, p.rootItem, false); return __result(r);" % J(files), "b0_import", 180)
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
function fix(tr) { for (var k = 0; k + 1 < tr.clips.numItems; k++) { var g = tr.clips[k + 1].start.seconds - tr.clips[k].end.seconds; if (g > 0.0005) { var e = new Time(); e.seconds = tr.clips[k + 1].start.seconds; tr.clips[k].end = e; } } }
fix(s.videoTracks[0]); for (var t = 0; t < 3; t++) fix(s.audioTracks[t]);
r.v1 = s.videoTracks[0].clips.numItems; r.a1 = s.audioTracks[0].clips.numItems; r.itemName = item.name; return __result(r);''' % (J(item_prefix), J(segs)), "b1_segments", 400)
    # 2) faixas extras (música/SFX)
    run(pre + '''if (s.audioTracks.numTracks < 7) { app.enableQE(); var q = qe.project.getActiveSequence(); q.addTracks(0, 0, 7 - s.audioTracks.numTracks, 0, s.audioTracks.numTracks - 1, 0, 0, 0); }
if (s.videoTracks.numTracks < 3) { app.enableQE(); var q2 = qe.project.getActiveSequence(); q2.addTracks(3 - s.videoTracks.numTracks, s.videoTracks.numTracks, 0, 0, 0, 0, 0, 0); }
r.n = s.audioTracks.numTracks; r.vn = s.videoTracks.numTracks; return __result(r);''', "b2_tracks", 60)
    # 3) enquadramento base + efeitos (curvas) por clipe
    FX = fx_clips(plan)
    need_lens = sorted(i for i, rows in FX.items() if any(abs(r[4]) > 1e-6 for r in rows))
    need_tint = sorted(i for i, rows in FX.items() if any(r[5] > 1e-6 for r in rows))
    run(pre + '''var tr = s.videoTracks[0]; var FX = %s;
for (var c = 0; c < tr.clips.numItems; c++) { var mo = tr.clips[c].components[1]; mo.properties[1].setTimeVarying(false); mo.properties[0].setTimeVarying(false); mo.properties[1].setValue(100, true); mo.properties[0].setValue([0, 0.5], true); }
for (var ci in FX) { var rows = FX[ci]; var mo2 = tr.clips[parseInt(ci)].components[1]; var sc = mo2.properties[1], ps = mo2.properties[0];
  sc.setTimeVarying(true); ps.setTimeVarying(true);
  for (var k = 0; k < rows.length; k++) { var f = rows[k]; sc.addKey(f[0]); sc.setValueAtKey(f[0], f[1]); ps.addKey(f[0]); ps.setValueAtKey(f[0], [f[2], f[3]]); } }
return __result(r);''' % J(FX), "b3a_zoom", 300)
    for name, idxs, match, prop, col, fxname, base in (("b3b_lens", need_lens, "PR.ADBE Lens Distortion", 0, 4, "Distorção de lente", 0),
                                                         ("b3c_tint", need_tint, "AE.ADBE Tint", 2, 5, "Tonalidade", 0)):
        if not idxs: continue
        run(pre + '''app.enableQE(); var q = qe.project.getActiveSequence(); var FX = %s; var IDX = %s; var tr = s.videoTracks[0];
var fxo = qe.project.getVideoEffectByName(%s);
for (var n = 0; n < IDX.length; n++) { var ci = IDX[n]; q.getVideoTrackAt(0).getItemAt(ci).addVideoEffect(fxo);
  var cl = tr.clips[ci]; var comp = null; for (var cc = 0; cc < cl.components.numItems; cc++) if (cl.components[cc].matchName == %s) comp = cl.components[cc];
  var pr = comp.properties[%d]; pr.setTimeVarying(true); var rows = FX[ci];
  for (var k = 0; k < rows.length; k++) { pr.addKey(rows[k][0]); pr.setValueAtKey(rows[k][0], %s); } }
r.n = IDX.length; return __result(r);''' % (J(FX), J(idxs), J(fxname), J(match), prop,
                                              "rows[k][%d]" % col), name, 300)
    # 4) música A4
    ms = plan["music"]
    M = []
    for i, m in enumerate(ms):
        end = ms[i + 1]["tl_in"] if i + 1 < len(ms) else plan["dur_tl"]
        g = lin(m["gain_db"] + boost_m)
        dk = []
        for d in plan.get("ducks", []):
            if m["tl_in"] + 0.3 < d["tl"] < end - 0.3:
                off = d["tl"] - m["tl_in"]; gd = g * 10 ** (-d["depth_db"] / 20.0)
                dk += [[round(off - 0.1, 4), g], [round(off + 0.05, 4), gd], [round(off + d["dur"], 4), gd], [round(off + d["dur"] + 0.35, 4), g]]
        M.append({"name": os.path.basename(m["file"]), "a": round(m["tl_in"], 5), "b": round(end, 5), "g": g, "duck": dk, "off": m.get("src_in", 0.0),
                  "fin": m.get("fade_in", 0.08), "fout": m.get("fade_out", 0.12)})
    FADE = '''function fades(c, g, tin, tout) { var pr = lvl(c); pr.setTimeVarying(true); var z = 0.0005; var dur = c.end.seconds - c.start.seconds;
  var t0 = c.inPoint.seconds; var pts = [[t0, z], [t0 + tin, g], [t0 + dur - tout, g], [t0 + dur, z]];
  for (var i = 0; i < pts.length; i++) { pr.addKey(pts[i][0]); pr.setValueAtKey(pts[i][0], pts[i][1]); } }
'''
    run(pre + FADE + '''var mt = s.audioTracks[3]; var M = %s;
for (var k = 0; k < M.length; k++) { var it = find(M[k].name); it.setInPoint(M[k].off, 4); it.setOutPoint(M[k].off + M[k].b - M[k].a, 4); mt.overwriteClip(it, M[k].a); it.clearInPoint(); it.clearOutPoint(); }
for (var k2 = 0; k2 < M.length; k2++) { var e = new Time(); e.seconds = M[k2].b; mt.clips[k2].end = e; }
for (var k3 = 0; k3 < M.length; k3++) { fades(mt.clips[k3], M[k3].g, M[k3].fin, M[k3].fout); var pr3 = lvl(mt.clips[k3]); var b3 = mt.clips[k3].inPoint.seconds;
  for (var d3 = 0; d3 < M[k3].duck.length; d3++) { pr3.addKey(b3 + M[k3].duck[d3][0]); pr3.setValueAtKey(b3 + M[k3].duck[d3][0], M[k3].duck[d3][1]); } }
r.n = mt.clips.numItems; return __result(r);''' % J(M), "b4_music", 300)
    # 5) SFX A5..A7 (distribui p/ não sobrescrever)
    F, busy = [], {4: -1.0, 5: -1.0, 6: -1.0}
    for x in sorted(plan["sfx"], key=lambda x: x["tl"]):
        nm = os.path.basename(x["file"]); l, d0 = sfx_meta(nm); d = min(x.get("dur", d0), d0)
        tr = next(t for t in (4, 5, 6) if busy[t] <= x["tl"] + 1e-6)
        busy[tr] = x["tl"] + d
        F.append({"name": nm, "t": round(x["tl"], 5), "dur": d, "tr": tr, "g": lin(SFX_TARGET_LUFS + boost_m - l + x.get("rel_db", 0.0))})
    run(pre + FADE + '''var F = %s; var cnt = {4: 0, 5: 0, 6: 0};
for (var q = 0; q < F.length; q++) { var it = find(F[q].name); var st = s.audioTracks[F[q].tr]; it.setInPoint(0.0, 4); it.setOutPoint(F[q].dur, 4); st.overwriteClip(it, F[q].t); it.clearInPoint(); it.clearOutPoint();
  var cl = null; for (var c = 0; c < st.clips.numItems; c++) if (Math.abs(st.clips[c].start.seconds - F[q].t) < 0.01) cl = st.clips[c];
  if (cl) fades(cl, F[q].g, 0.01, Math.min(0.3, F[q].dur / 2)); cnt[F[q].tr]++; }
r.cnt = cnt; return __result(r);''' % J(F), "b5_sfx", 300)
    # 6a) limitador nas 3 faixas do bruto
    run(pre + '''app.enableQE(); var q = qe.project.getActiveSequence(); var fx = qe.project.getAudioEffectByName("Limitador pesado"); var n = 0;
for (var t = 0; t < 3; t++) { var tr = s.audioTracks[t];
  for (var k = 0; k < tr.clips.numItems; k++) { q.getAudioTrackAt(t).getItemAt(k).addAudioEffect(fx);
    var c = tr.clips[k]; for (var cc = 0; cc < c.components.numItems; cc++) if (c.components[cc].matchName == "e0b23f05-f1a7-4ef7-9b50-7ec3e3002058") { c.components[cc].properties[1].setValue(%s, true); n++; }
    c.components[0].properties[1].setValue(%s, true); } }
r.limiters = n; return __result(r);''' % (plan.get("limiter", 0.93), lin(boost_v)), "b6a_limiter", 600)
    # 6b) stickers (V2/V3): pop + wobble
    if plan.get("stickers"):
        ST = [{"name": os.path.basename(x["file"]), "t": round(x["tl"], 5), "dur": x["dur"], "pos": x["pos"], "sc": x["scale"], "rot": x.get("rot", 0), "v": x.get("v", 2) - 1, "fade": x.get("fade", 0), "op": x.get("opacity", 100)} for x in plan["stickers"]]
        run(pre + '''var ST = %s;
for (var k = 0; k < ST.length; k++) { var vt = s.videoTracks[ST[k].v]; var it = find(ST[k].name); vt.overwriteClip(it, ST[k].t);
  var c = null; for (var j = 0; j < vt.clips.numItems; j++) if (Math.abs(vt.clips[j].start.seconds - ST[k].t) < 0.01) c = vt.clips[j];
  var e = new Time(); e.seconds = ST[k].t + ST[k].dur; c.end = e; var mo = c.components[1]; mo.properties[0].setValue(ST[k].pos, true);
  var sc = mo.properties[1]; sc.setTimeVarying(true); var rt = mo.properties[4]; rt.setTimeVarying(true); var t0 = c.inPoint.seconds; var S = ST[k].sc, R = ST[k].rot, D = ST[k].dur;
  if (ST[k].fade > 0) { sc.setTimeVarying(false); sc.setValue(S, true); rt.setTimeVarying(false); rt.setValue(R, true); var op = c.components[0].properties[0]; op.setTimeVarying(true); var F = ST[k].fade;
    var OK = [[0, 0], [F, ST[k].op], [D - F, ST[k].op], [D, 0]]; for (var o = 0; o < OK.length; o++) { op.addKey(t0 + OK[o][0]); op.setValueAtKey(t0 + OK[o][0], OK[o][1]); } continue; }
  var K = [[0, 0, R - 8], [0.10, S * 1.22, R + 4], [0.20, S * 0.94, R - 2], [0.30, S, R], [D - 0.18, S, R + 1], [D, 0, R + 6]];
  for (var q = 0; q < K.length; q++) { sc.addKey(t0 + K[q][0]); sc.setValueAtKey(t0 + K[q][0], K[q][1]); rt.addKey(t0 + K[q][0]); rt.setValueAtKey(t0 + K[q][0], K[q][2]); } }
r.n = ST.length; return __result(r);''' % J(ST), "b6b_stickers", 180)
    # 7) marcadores
    run(pre + '''var MK = %s; for (var k = 0; k < MK.length; k++) { var mk = s.markers.createMarker(MK[k].t); mk.name = MK[k].txt; mk.comments = MK[k].txt; }
r.n = MK.length; return __result(r);''' % J([{"t": round(m["tl"], 4), "txt": m["txt"]} for m in plan.get("marks", [])]), "b7_marks", 60)
    if "--export" in sys.argv:
        outp = sys.argv[sys.argv.index("--export") + 1].replace("\\", "/")
        run(pre + '''s.setInPoint(0); s.setOutPoint(%s);
var preset = new File(%s);   // adobe_presets.py acha o preset em qualquer versão instalada
r.exp = s.exportAsMediaDirect(new File(%s).fsName, preset.fsName, 1); return __result(r);''' % (plan["dur_tl"], J(__import__("adobe_presets").h264_preset() or ""), J(outp)), "b8_export", 1800)


main()
