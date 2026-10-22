"""Monta a edição no Premiere (via MCP Bridge) a partir de um plan.json.

Uso: python build_edit.py <plan.json> <SEQUENCE_ID> [--import] [--export out.mp4]

plan.json (tempos de FONTE em s, exceto onde dito 'tl' = timeline):
  keeps  [{src_in, src_out, tl_in, tl_out}]   trechos mantidos do bruto (1 clipe c/ todas as faixas)
  zooms  [{src, tl, hold, s, kind: push|punch|hud|dolly, why}]
  music  [{file, tl_in, tl_out, gain_db}]     gain_db = ganho p/ ficar ~15 dB sob a voz
  sfx    [{file, tl, why}]  (+ sfx_meta no plan: nome -> [lufs, dur])   -> ver SFX_META abaixo
  mutes  [{track:'A2', tl_a, tl_b}]           silencia uma faixa (keyframe de volume, restaurável)
  marks  [{tl, txt}]                          marcadores de revisão

Lições (Premiere 2026 via ExtendScript):
 - keyframes de componente usam tempo da MÍDIA (inPoint + offset no clipe), não da sequência;
 - Nível de áudio: valor linear, 0 dB = 0.17783; valor = 10^((dB-15)/20);
 - sempre endereçar a sequência por ID (activeSequence pode não ser a esperada);
 - clip.end = Time fecha buracos de 1 frame entre segmentos;
 - zoom centrado: Position_x = 0.5*(1-s), y = 0.5 (bruto 3840x1080, metade direita = jogo, Position base [0,0.5]).
"""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
BRIDGE = os.path.join(HERE, "run_bridge.py")
# rimshot: LUFS declarado -10.3 (real -14.3, pico +2.0 dBFS no arquivo): -4 dB extra evita clipar
# dun-dun-dun: LUFS declarado -5.0 (real -9.0) de propósito: metais têm pico alto e clipavam a 313s; -4 dB extra resolve
SFX_META = {"anime-shine-sound-2.mp3": (-19.2, 2.0), "vine-boom.mp3": (-8.9, 1.25), "fails-ohhhh.mp3": (-13.2, 2.5),
            "anime-wow-sound-effect.mp3": (-15.3, 2.5), "dun-dun-dun-sound-effect-brass_8nFBccR.mp3": (-5.0, 3.0), "erro.mp3": (-13.6, 0.99),
            "record-scratch-2.mp3": (-10.5, 0.78), "jixaw-metal-pipe-falling-sound.mp3": (-11.6, 2.0), "taco-bell-bong-sfx.mp3": (-12.3, 1.9),
            "whoosh-sfx.mp3": (-20.8, 0.97), "bonk_BEtiM8g.mp3": (-17.6, 1.2), "rimshot.mp3": (-10.3, 1.9), "sadtrombone.swf.mp3": (-13.9, 2.5), "roblox-death-sound_1.mp3": (-18.8, 1.0)}
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
        print("parando após", name); sys.exit(0)  # depuração: monta só até esta etapa
    return out.stdout


def ease(u):
    return 1 - (1 - u) ** 3


def zoom_keys(plan):
    """Zoom ancorado num ponto de foco (fx,fy) em px do quadro 1920x1080: o ponto fica parado e o resto cresce
    (nunca expõe borda). Bruto 3840x1080, Position base [0,0.5]:  x = fx*(1-s)/1920 ,  y = (fy - s*(fy-540))/1080."""
    keeps, res = plan["keeps"], []
    for z in plan["zooms"]:
        S, t0, hold, kind = z["s"], z["tl"], z["hold"], z["kind"]
        fx, fy = z.get("fx", 960), z.get("fy", 540)
        ramp = {"push": 0.9, "punch": 0.15, "hud": 0.5, "dolly": 1.4}[kind]
        ret = {"push": 0.5, "punch": 0.4, "hud": 0.5, "dolly": 0.6}[kind]
        n = 1 if ramp <= 0.2 else 5
        steps = [(0, 100.0)] + [(ramp * i / n, 100 + (S - 100) * ease(i / n)) for i in range(1, n + 1)]
        if hold > ramp:
            steps.append((hold, float(S)))
        steps.append((max(hold, ramp) + ret, 100.0))
        ci = [i for i, k in enumerate(keeps) if k["tl_in"] <= t0 < k["tl_out"]][0]
        k = keeps[ci]
        if t0 + steps[-1][0] > k["tl_out"] - 0.05:
            print("AVISO: zoom cruza corte:", z["why"])
        kf, cv = [], []
        for off, sc in steps:
            sp = sc / 100.0
            x = fx * (1 - sp) / 1920.0
            y = (fy - sp * (fy - 540)) / 1080.0
            tm = round(k["src_in"] + (t0 - k["tl_in"]) + off, 5)
            kf.append([tm, round(sc, 3), round(x, 5), round(y, 5)])
            if "curv" in z:  # distorção de lente (negativo = abaulado) acompanha a escala
                cv.append([tm, round(z["curv"] * (sc - 100) / (S - 100), 3)])
        res.append({"clip": ci, "kf": kf, "curv": cv, "why": z["why"]})
    return res


def main():
    plan = json.load(open(sys.argv[1], encoding="utf8"))
    wid = sys.argv[2]
    pre = PRE % J(wid)
    boost_v = plan.get("boost_voice_db", plan.get("boost_db", 0.0))  # ganho (dB) das 3 faixas do bruto ANTES do limitador (compensa achatamento)
    boost = plan.get("boost_music_db", plan.get("boost_db", 0.0))  # ganho (dB) de música e SFX (mantém proporção voz/música)
    item_prefix = plan.get("bruto_prefix", "2026-10-08")
    if "--import" in sys.argv:
        files = sorted({m["file"] for m in plan["music"]} | {x["file"] for x in plan["sfx"]} | {x["file"] for x in plan.get("stickers", [])})
        run(pre + "r.imp = p.importFiles(%s, true, p.rootItem, false); return __result(r);" % J(files), "b0_import", 120)
    # 1) limpar + segmentos
    segs = [[k["src_in"], k["src_out"], k["tl_in"]] for k in plan["keeps"]]
    run(pre + '''function clr(tr) { for (var i = tr.clips.numItems - 1; i >= 0; i--) tr.clips[i].remove(0, 0); }
for (var v = 0; v < s.videoTracks.numTracks; v++) clr(s.videoTracks[v]);
for (var a = 0; a < s.audioTracks.numTracks; a++) clr(s.audioTracks[a]);
var m0 = s.markers.getFirstMarker(); while (m0) { s.markers.deleteMarker(m0); m0 = s.markers.getFirstMarker(); }
var item = null; for (var i = 0; i < p.rootItem.children.numItems; i++) if (p.rootItem.children[i].name.indexOf(%s) == 0) item = p.rootItem.children[i];
var segs = %s;
for (var k = 0; k < segs.length; k++) { item.setInPoint(segs[k][0], 4); item.setOutPoint(segs[k][1], 4); s.videoTracks[0].overwriteClip(item, segs[k][2]); }
item.clearInPoint(); item.clearOutPoint();
function fix(tr) { for (var k = 0; k + 1 < tr.clips.numItems; k++) { var g = tr.clips[k + 1].start.seconds - tr.clips[k].end.seconds; if (g > 0.0005) { var e = new Time(); e.seconds = tr.clips[k + 1].start.seconds; tr.clips[k].end = e; } } }
fix(s.videoTracks[0]); for (var t = 0; t < 3; t++) fix(s.audioTracks[t]);
r.v1 = s.videoTracks[0].clips.numItems; return __result(r);''' % (J(item_prefix), J(segs)), "b1_segments", 300)
    # 2) faixas extras (música/SFX) se faltarem
    run(pre + '''if (s.audioTracks.numTracks < 7) { app.enableQE(); var q = qe.project.getActiveSequence(); q.addTracks(0, 0, 7 - s.audioTracks.numTracks, 0, s.audioTracks.numTracks - 1, 0, 0, 0); }
r.n = s.audioTracks.numTracks; return __result(r);''', "b2_tracks", 60)
    # 3) enquadramento + zooms
    Z = zoom_keys(plan)
    run(pre + '''var tr = s.videoTracks[0];
for (var c = 0; c < tr.clips.numItems; c++) { var mo = tr.clips[c].components[1]; mo.properties[1].setTimeVarying(false); mo.properties[0].setTimeVarying(false); mo.properties[1].setValue(100, true); mo.properties[0].setValue([0, 0.5], true); }
var Z = %s;
for (var z = 0; z < Z.length; z++) { var mo2 = tr.clips[Z[z].clip].components[1]; var sc = mo2.properties[1], ps = mo2.properties[0];
  sc.setTimeVarying(true); ps.setTimeVarying(true);
  for (var k = 0; k < Z[z].kf.length; k++) { var f = Z[z].kf[k]; sc.addKey(f[0]); sc.setValueAtKey(f[0], f[1]); ps.addKey(f[0]); ps.setValueAtKey(f[0], [f[2], f[3]]); } }
// distorção de lente (só onde há curv): efeito via QE, keyframes de Curvatura (negativo = abaulado)
app.enableQE(); var q = qe.project.getActiveSequence(); var fxl = qe.project.getVideoEffectByName("Distorção de lente"); var added = {};
for (var z2 = 0; z2 < Z.length; z2++) { if (!Z[z2].curv.length) continue; var ci = Z[z2].clip;
  if (!added[ci]) { q.getVideoTrackAt(0).getItemAt(ci).addVideoEffect(fxl); added[ci] = true; }
  var cl = tr.clips[ci]; var le = null; for (var cc = 0; cc < cl.components.numItems; cc++) if (cl.components[cc].matchName == "PR.ADBE Lens Distortion") le = cl.components[cc];
  var cp = le.properties[0]; cp.setTimeVarying(true);
  for (var kk = 0; kk < Z[z2].curv.length; kk++) { cp.addKey(Z[z2].curv[kk][0]); cp.setValueAtKey(Z[z2].curv[kk][0], Z[z2].curv[kk][1]); } }
return __result(r);''' % J(Z), "b3_zooms", 120)
    # 4) música A4
    ms = plan["music"]
    M = []
    for i, m in enumerate(ms):
        end = ms[i + 1]["tl_in"] if i + 1 < len(ms) else plan["dur_tl"]
        g = lin(m["gain_db"] + boost)
        dk = []
        for d in plan.get("ducks", []):  # duck da música nos gags (SFX de piada): -depth dB por dur s
            if m["tl_in"] + 0.3 < d["tl"] < end - 0.3:
                off = d["tl"] - m["tl_in"]; gd = g * 10 ** (-d["depth_db"] / 20.0)
                dk += [[round(off - 0.1, 4), g], [round(off + 0.05, 4), gd], [round(off + d["dur"], 4), gd], [round(off + d["dur"] + 0.35, 4), g]]
        M.append({"name": os.path.basename(m["file"]), "a": round(m["tl_in"], 5), "b": round(end, 5), "g": g, "duck": dk})
    FADE = '''function fades(c, g, tin, tout) { var pr = lvl(c); pr.setTimeVarying(true); var z = 0.0005; var dur = c.end.seconds - c.start.seconds;
  var t0 = c.inPoint.seconds; var pts = [[t0, z], [t0 + tin, g], [t0 + dur - tout, g], [t0 + dur, z]];
  for (var i = 0; i < pts.length; i++) { pr.addKey(pts[i][0]); pr.setValueAtKey(pts[i][0], pts[i][1]); } }
'''
    run(pre + FADE + '''var mt = s.audioTracks[3]; var M = %s;
for (var k = 0; k < M.length; k++) { var it = find(M[k].name); it.setInPoint(0.0, 4); it.setOutPoint(M[k].b - M[k].a, 4); mt.overwriteClip(it, M[k].a); it.clearInPoint(); it.clearOutPoint(); }
for (var k2 = 0; k2 < M.length; k2++) { var e = new Time(); e.seconds = M[k2].b; mt.clips[k2].end = e; }
for (var k3 = 0; k3 < M.length; k3++) { fades(mt.clips[k3], M[k3].g, 0.08, 0.12); var pr3 = lvl(mt.clips[k3]); var b3 = mt.clips[k3].inPoint.seconds;
  for (var d3 = 0; d3 < M[k3].duck.length; d3++) { pr3.addKey(b3 + M[k3].duck[d3][0]); pr3.setValueAtKey(b3 + M[k3].duck[d3][0], M[k3].duck[d3][1]); } }
r.n = mt.clips.numItems; return __result(r);''' % J(M), "b4_music", 300)
    # 5) SFX A5
    F = []
    for x in plan["sfx"]:
        nm = os.path.basename(x["file"]); l, d = SFX_META[nm]
        F.append({"name": nm, "t": round(x["tl"], 5), "dur": d, "g": lin(SFX_TARGET_LUFS + boost - l)})
    run(pre + FADE + '''var st = s.audioTracks[4]; var F = %s;
for (var q = 0; q < F.length; q++) { var it = find(F[q].name); it.setInPoint(0.0, 4); it.setOutPoint(F[q].dur, 4); st.overwriteClip(it, F[q].t); it.clearInPoint(); it.clearOutPoint(); }
for (var q2 = 0; q2 < F.length; q2++) fades(st.clips[q2], F[q2].g, 0.01, Math.min(0.3, F[q2].dur / 2));
r.n = st.clips.numItems; return __result(r);''' % J(F), "b5_sfx", 300)
    # 6) mutes de faixa (keyframes de volume; restaurável)
    run(pre + '''var UN = 0.17782794; var Z0 = 0.0005; var MU = %s; var log = [];
for (var m = 0; m < MU.length; m++) { var ti = parseInt(MU[m].track.substring(1)) - 1; var tr = s.audioTracks[ti];
  for (var c = 0; c < tr.clips.numItems; c++) { var cl = tr.clips[c]; var cs = cl.start.seconds, ce = cl.end.seconds;
    if (ce <= MU[m].a || cs >= MU[m].b) continue; var pr = lvl(cl); pr.setTimeVarying(true); var base = cl.inPoint.seconds - cs; var K = [];
    if (MU[m].a > cs) { K.push([MU[m].a - 0.03, UN]); K.push([MU[m].a, Z0]); } else K.push([cs, Z0]);
    if (MU[m].b < ce) { K.push([MU[m].b, Z0]); K.push([MU[m].b + 0.03, UN]); } else K.push([ce, Z0]);
    for (var k = 0; k < K.length; k++) { pr.addKey(base + K[k][0]); pr.setValueAtKey(base + K[k][0], K[k][1]); } log.push([MU[m].track, c]); } }
r.log = log; return __result(r);''' % J([{"track": m["track"], "a": round(m["tl_a"], 4), "b": round(m["tl_b"], 4)} for m in plan.get("mutes", [])]), "b6_mutes", 120)
    # 6a) limitador pesado nas 3 faixas do bruto (picos de grito). Medido (janela 100-250s, boost +3.5): 0.90 -> -18.0 LUFS/pico -3.7; 0.93 -> -16.2 LUFS/pico -1.0 (escolhido); 0.95 -> -15.0/+0.1 (clipa)
    run(pre + '''app.enableQE(); var q = qe.project.getActiveSequence(); var fx = qe.project.getAudioEffectByName("Limitador pesado"); var n = 0;
for (var t = 0; t < 3; t++) { var tr = s.audioTracks[t];
  for (var k = 0; k < tr.clips.numItems; k++) { q.getAudioTrackAt(t).getItemAt(k).addAudioEffect(fx);
    var c = tr.clips[k]; for (var cc = 0; cc < c.components.numItems; cc++) if (c.components[cc].matchName == "e0b23f05-f1a7-4ef7-9b50-7ec3e3002058") { c.components[cc].properties[1].setValue(%s, true); n++; }
    c.components[0].properties[1].setValue(%s, true); } }
r.limiters = n; return __result(r);''' % (plan.get("limiter", 0.93), lin(boost_v)), "b6a_limiter", 180)
    # 6b) stickers PNG em V2 (pop de escala; posição em fração do quadro)
    if plan.get("stickers"):
        ST = [{"name": os.path.basename(x["file"]), "t": round(x["tl"], 5), "dur": x["dur"], "pos": x["pos"], "sc": x["scale"]} for x in plan["stickers"]]
        run(pre + '''var ST = %s; var v2 = s.videoTracks[1];
for (var k = 0; k < ST.length; k++) { var it = find(ST[k].name); v2.overwriteClip(it, ST[k].t); var c = v2.clips[k];
  var e = new Time(); e.seconds = ST[k].t + ST[k].dur; c.end = e; var mo = c.components[1]; mo.properties[0].setValue(ST[k].pos, true);
  var sc = mo.properties[1]; sc.setTimeVarying(true); var t0 = c.inPoint.seconds; var K = [[0, 0], [0.12, ST[k].sc * 1.2], [0.25, ST[k].sc], [ST[k].dur - 0.15, ST[k].sc], [ST[k].dur, 0]];
  for (var j = 0; j < K.length; j++) { sc.addKey(t0 + K[j][0]); sc.setValueAtKey(t0 + K[j][0], K[j][1]); } }
r.n = v2.clips.numItems; return __result(r);''' % J(ST), "b6b_stickers", 120)
    # 7) marcadores
    run(pre + '''var MK = %s; for (var k = 0; k < MK.length; k++) { var mk = s.markers.createMarker(MK[k].t); mk.name = MK[k].txt; mk.comments = MK[k].txt; }
r.n = MK.length; return __result(r);''' % J([{"t": round(m["tl"], 4), "txt": m["txt"]} for m in plan["marks"]]), "b7_marks", 60)
    # 8) export opcional
    if "--export" in sys.argv:
        outp = sys.argv[sys.argv.index("--export") + 1].replace("\\", "/")
        run(pre + '''s.setInPoint(0); s.setOutPoint(%s);
var preset = new File(%s);   // adobe_presets.py acha o preset em qualquer versão instalada
r.exp = s.exportAsMediaDirect(new File(%s).fsName, preset.fsName, 1); return __result(r);''' % (plan["dur_tl"], J(__import__("adobe_presets").h264_preset() or ""), J(outp)), "b8_export", 1200)


main()
