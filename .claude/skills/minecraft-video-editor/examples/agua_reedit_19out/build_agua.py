"""Monta plan.json no CLONE da Sequência 01 (já decupada). Etapas (em ordem):
  clone, import, tracks, split, zoom, stretch, presets, reveals, overlays, flashback, music, sfx, mutes, bleep, marks
Uso: python build_agua.py etapa[,etapa...]"""
import json, os, sys
from lib import *
sys.path.insert(0, os.path.expanduser("~/.claude/skills/minecraft-video-editor/scripts"))
import berserker as bz
import sfx_timing as sxt
from sfx_levels import gain_for
import importlib.util
spec_ = importlib.util.spec_from_file_location("b3", os.path.expanduser("~/.claude/skills/minecraft-video-editor/scripts/build_edit3.py"))

PLAN = json.load(open(os.path.join(HERE, "plan.json"), encoding="utf8"))
FPS = 254016000000 / 4237833600
SNAP = 0.20            # janela começando a <=0,2 s de um corte encosta no corte (sem micro-clipe)
MINSEG = 0.25
BIN = "Claude edicao 19-out"
ORIG = "e4e82caa-ba38-4688-a7b5-c17a6174f8eb"


def fr(t): return round(round(t * FPS) / FPS, 5)


def v1rows(d): return [r for r in d["V"][0]]


def windows(d):
    """janelas de V1: zoom/stretch/preset/reveal -> (t_ini, t_fim) já encostadas nos cortes existentes"""
    cuts = sorted({r[0] for r in v1rows(d)} | {r[1] for r in v1rows(d)})
    def snap(t):
        c = min(cuts, key=lambda c: abs(c - t))
        return c if abs(c - t) <= SNAP else fr(t)
    def nxt(t):
        return min([c for c in cuts if c > t + 1e-3] or [d["end"]])
    W = []
    for kind in ("zooms", "stretch", "presets", "reveals"):
        for x in PLAN[kind]:
            t = snap(x["t"])
            e = x.get("end")
            if kind == "reveals" and not e: e = x["t"] + (1.2 if x["kind"] == "sparkle" else 2.1)
            end = nxt(t) if not e else min(snap(e), nxt(t))
            if end - t < MINSEG: end = nxt(t)
            W.append({"kind": kind, "x": x, "t": t, "end": end})
    by = {}
    for w in W: by.setdefault(round(w["t"], 3), []).append(w)
    for ws in by.values():
        e = max(w["end"] for w in ws)
        for w in ws: w["end"] = e
    return W


def clip_index(d, t, tr=0):
    for k, r in enumerate(d["V"][tr]):
        if abs(r[0] - t) < 0.012: return k
    return -1


def stage_clone():
    jsx = '''var p = app.project; if (p.path.indexOf("Bebi toda a agua") < 0) throw new Error("PROJETO ATIVO ERRADO: " + p.path);
var o = null; for (var i = 0; i < p.sequences.numSequences; i++) if (p.sequences[i].sequenceID == "%s") o = p.sequences[i];
var before = {}; for (var j = 0; j < p.sequences.numSequences; j++) before[p.sequences[j].sequenceID] = 1;
var r = {ok: o.clone()};
for (var k = 0; k < p.sequences.numSequences; k++) { var q = p.sequences[k]; if (!before[q.sequenceID]) { q.name = "Sequencia 01 - EDICAO Claude 19-out v2"; r.newId = q.sequenceID; } }
return __result(r);''' % ORIG
    r = run(jsx, "clone", 600)
    open(os.path.join(HERE, "seq_id.txt"), "w").write(r["newId"])


def assets():
    f = set()
    for m in PLAN["music"]:
        if m["file"]: f.add(m["file"])
    for x in PLAN["sfx"]: f.add(x["file"])
    for o in PLAN["overlays"]:
        if o["kind"] == "timelapse": f.add(o["file"])
        else: f.add(o["file"])
    if PLAN["bleeps"]: f.add(r"D:\Pobrs\agua\bleep_1k.wav")
    return sorted(f)


def prep_overlays():
    for o in PLAN["overlays"]:
        if o["kind"] == "timelapse":
            o["file"] = r"D:\Pobrs\agua\timelapse1_piscina.mp4" if o["t"] < 800 else r"D:\Pobrs\agua\timelapse2_cachoeira.mp4"


prep_overlays()


def stage_import():
    fs = assets()
    miss = [f for f in fs if not os.path.exists(f)]
    assert not miss, "faltando (trava o Premiere): %s" % miss
    fs = [f.replace("\\", "/") for f in fs]
    run(PRE + '''var bin = null; for (var i = 0; i < p.rootItem.children.numItems; i++) if (p.rootItem.children[i].name == %s) bin = p.rootItem.children[i];
if (!bin) bin = p.rootItem.createBin(%s);
r.imp = p.importFiles(%s, true, bin, false); r.n = bin.children.numItems; return __result(r);''' % (J(BIN), J(BIN), J(fs)), "import", 900)


def stage_tracks():
    run(PRE + '''app.enableQE(); var q = qe.project.getActiveSequence();
var na = s.audioTracks.numTracks; if (na < 9) q.addTracks(0, 0, 9 - na, 1, na, 0, 0, 0);
var nv = s.videoTracks.numTracks; if (nv < 4) q.addTracks(4 - nv, nv, 0, 0, 0, 0, 0, 0);
r.a = s.audioTracks.numTracks; r.v = s.videoTracks.numTracks; return __result(r);''', "tracks", 120)


def stage_split():
    d = dump(); W = windows(d)
    have = {round(r[0], 3) for r in v1rows(d)} | {round(r[1], 3) for r in v1rows(d)}
    ts = sorted({w["t"] for w in W} | {w["end"] for w in W})
    ts = [t for t in ts if all(abs(t - h) > 0.015 for h in have) and 0 < t < d["end"] - 0.05]
    print("razors V1:", len(ts))
    # teste do formato de timecode no 1º corte: confere onde o corte caiu
    for i in range(0, len(ts), 40):
        run(PRE + '''app.enableQE(); var q = qe.project.getActiveSequence(); var T = %s; for (var i = 0; i < T.length; i++) q.getVideoTrackAt(0).razor(tc(T[i]));
return __result(r);''' % J(ts[i:i + 40]), "split", 900)
    d2 = dump()
    starts = [r[0] for r in d2["V"][0]]
    err = [min(abs(s_ - t) for s_ in starts) for t in ts]
    print("V1 clipes: %d -> %d | erro máx. do razor %.4f s" % (len(d["V"][0]), len(d2["V"][0]), max(err) if err else 0))


def motion_pos(fx, fy, sp):
    px = (fx - sp * (fx - 960)) / 1920.0; py = (fy - sp * (fy - 540)) / 1080.0
    # o quadro tem de continuar coberto
    px = min(max(px, (1920 - 960 * sp) / 1920.0), 960 * sp / 1920.0)
    py = min(max(py, (1080 - 540 * sp) / 1080.0), 540 * sp / 1080.0)
    return round(px, 5), round(py, 5)


def stage_zoom():
    d = dump(); W = [w for w in windows(d) if w["kind"] == "zooms" and w["x"]["s"] > 100.5]
    Z = []
    for w in W:
        k = clip_index(d, w["t"])
        if k < 0: print("zoom sem clipe em", w["t"]); continue
        r_ = d["V"][0][k]; dur = r_[1] - r_[0]; x = w["x"]; ip = r_[2]
        s1 = x["s"] / 100.0; ramp = min(x["ramp"], dur * 0.9)
        keys = []
        if ramp <= 0.01:
            px, py = motion_pos(x["fx"], x["fy"], s1); keys = [[ip, x["s"], px, py]]
        else:
            for j in range(7):
                u = j / 6.0; e = 1 - (1 - u) ** 2.4; sp = 1 + (s1 - 1) * e
                px, py = motion_pos(x["fx"], x["fy"], sp)
                keys.append([round(ip + ramp * u, 5), round(100 * sp, 3), px, py])
        Z.append({"k": k, "keys": keys})
    print("zooms:", len(Z))
    run(PRE + '''var Z = %s; var tr = s.videoTracks[0]; r.n = 0;
for (var n = 0; n < Z.length; n++) { var mo = tr.clips[Z[n].k].components[1]; var sc = mo.properties[1], ps = mo.properties[0];
  sc.setTimeVarying(false); ps.setTimeVarying(false); var K = Z[n].keys;
  if (K.length == 1) { sc.setValue(K[0][1], true); ps.setValue([K[0][2], K[0][3]], true); r.n++; continue; }
  sc.setTimeVarying(true); ps.setTimeVarying(true);
  for (var j = 0; j < K.length; j++) { sc.addKey(K[j][0]); sc.setValueAtKey(K[j][0], K[j][1]); ps.addKey(K[j][0]); ps.setValueAtKey(K[j][0], [K[j][2], K[j][3]]); } r.n++; }
return __result(r);''' % J(Z), "zoom", 900)


def stage_stretch():
    d = dump(); ST = []
    for w in [w for w in windows(d) if w["kind"] == "stretch"]:
        k = clip_index(d, w["t"]); x = w["x"]
        if k < 0: print("stretch sem clipe", w["t"]); continue
        px, py = motion_pos(x["fx"], x["fy"], min(x["sx"], x["sy"]) / 100.0)
        ST.append({"k": k, "sx": x["sx"], "sy": x["sy"], "px": px, "py": py})
    run(PRE + '''var ST = %s; var tr = s.videoTracks[0];
for (var n = 0; n < ST.length; n++) { var mo = tr.clips[ST[n].k].components[1]; mo.properties[1].setTimeVarying(false); mo.properties[0].setTimeVarying(false);
  mo.properties[3].setValue(false, true); mo.properties[1].setValue(ST[n].sy, true); mo.properties[2].setValue(ST[n].sx, true); mo.properties[0].setValue([ST[n].px, ST[n].py], true); }
r.n = ST.length; return __result(r);''' % J(ST), "stretch", 300)


def stage_presets():
    d = dump(); SP = []
    for w in [w for w in windows(d) if w["kind"] == "presets"]:
        k = clip_index(d, w["t"]); x = w["x"]
        if k < 0: print("preset sem clipe", w["t"], x["name"]); continue
        r_ = d["V"][0][k]
        SP.append(bz.spec(x["name"], k, r_[2], r_[1] - r_[0], anchor=x.get("anchor"), tscale=x.get("tscale", 1.0)))
    print("presets:", len(SP))
    for i in range(0, len(SP), 25):
        run(PRE + '''app.enableQE(); var q = qe.project.getActiveSequence(); var TRK = 0; var tr = s.videoTracks[0];
''' + bz.APPLY_JS % J(SP[i:i + 25]) + '''return __result(r);''', "presets", 900)


GLV = {"Intensidade": 49.3, "Apenas os destaques": 41, "Especular": 7, "Difusão": 128, "Brilho": 100, "Velocidade do brilho": 100, "Ângulo": 372.5,
       "Escala de resplendor": 25, "Escala cruzada": 93, "Escala de resplendor 1": 50, "Escala de resplendor 2": 40, "Escala cruzada 1": 75, "Escala cruzada 2": 65,
       "Forma": 11, "Colorir": 93, "Variação de cor": 13, "Velocidade de variação": 2, "Remover saturação": 0, "Aberração Cromática": 37, "Modo de mesclagem": 1}


def stage_reveals():
    d = dump(); RV = []
    for w in [w for w in windows(d) if w["kind"] == "reveals"]:
        k = clip_index(d, w["t"]); r_ = d["V"][0][k]
        RV.append({"ci": k, "kind": w["x"]["kind"], "dur": r_[1] - r_[0], "ip": r_[2]})
    run(PRE + '''app.enableQE(); var q = qe.project.getActiveSequence(); var tr = s.videoTracks[0]; var RV = %s; var GLV = %s; r.fail = []; r.n = 0;
function qidx(trk, ci) { var kk = -1; for (var i = 0; i < trk.numItems; i++) { if (String(trk.getItemAt(i).type) != "Empty") kk++; if (kk == ci) return i; } return ci; }
for (var i = 0; i < RV.length; i++) { var R = RV[i]; var c = tr.clips[R.ci]; var t0 = R.ip; var qt = q.getVideoTrackAt(0); var qi = qt.getItemAt(qidx(qt, R.ci));
  if (R.kind == "tilt") { var mo = c.components[1]; var sc = mo.properties[1], rt = mo.properties[4]; sc.setTimeVarying(false);
    sc.setTimeVarying(true); sc.addKey(t0); sc.setValueAtKey(t0, 100); sc.addKey(t0 + R.dur); sc.setValueAtKey(t0 + R.dur, 71);
    rt.setTimeVarying(true); rt.addKey(t0); rt.setValueAtKey(t0, 0); rt.addKey(t0 + R.dur); rt.setValueAtKey(t0 + R.dur, -3.2);
    qi.addVideoEffect(qe.project.getVideoEffectByName("Cor de Lumetri")); var L = comp(c, "Cor de Lumetri"); var sat = L.properties[16];
    sat.setTimeVarying(true); sat.addKey(t0); sat.setValueAtKey(t0, 100); sat.addKey(t0 + R.dur * 0.87); sat.setValueAtKey(t0 + R.dur * 0.87, 27); r.n++; }
  else { qi.addVideoEffect(qe.project.getVideoEffectByName("Brilho cintilante")); var G = comp(c, "Brilho cintilante");
    for (var w = 0; w < G.properties.numItems; w++) { var pp = G.properties[w]; var nm = pp.displayName;
      try { if (GLV.hasOwnProperty(nm)) pp.setValue(GLV[nm], true); else if (nm == "Posição") pp.setValue([0.5, 0.46], true);
        else if (nm == "Área do brilho") { pp.setTimeVarying(true); pp.addKey(t0); pp.setValueAtKey(t0, 6); pp.addKey(t0 + 1.2); pp.setValueAtKey(t0 + 1.2, 19.2); } } catch (e) { r.fail.push(nm + ":" + e); } } r.n++; } }
return __result(r);''' % (J(RV), J(GLV)), "reveals", 600)


def stage_overlays():
    OV = []
    for o in PLAN["overlays"]:
        OV.append({"name": os.path.basename(o["file"]), "t": fr(o["t"]), "dur": o["dur"], "off": o.get("off", 0.0), "v": o["v"] - 1, "pos": o.get("pos"),
                   "scale": o.get("scale"), "z": o.get("zoom"), "echo": o.get("echo_at"), "kind": o["kind"]})
    run(PRE + '''var OV = %s; r.n = 0; r.fail = [];
function put(vt, it, off, dur, t) { it.setInPoint(off, 4); it.setOutPoint(off + dur, 4); vt.overwriteClip(it, t); it.clearInPoint(); it.clearOutPoint();
  var k = clipAt(vt, t); if (k < 0) return null; var c = vt.clips[k]; var e = new Time(); e.seconds = t + dur; c.end = e; return c; }
for (var i = 0; i < OV.length; i++) { var O = OV[i]; var vt = s.videoTracks[O.v]; var it = find(O.name); if (!it) { r.fail.push("sem item " + O.name); continue; }
  var c = put(vt, it, O.kind == "sticker" ? 0 : O.off, O.dur, O.t); if (!c) { r.fail.push("clip " + O.t); continue; }
  var mo = c.components[1]; if (O.pos) mo.properties[0].setValue(O.pos, true); if (O.scale) mo.properties[1].setValue(O.scale, true);
  if (O.z) { var sc = mo.properties[1]; var t0 = c.inPoint.seconds; sc.setTimeVarying(true); sc.addKey(t0); sc.setValueAtKey(t0, O.z[0]); sc.addKey(t0 + O.dur); sc.setValueAtKey(t0 + O.dur, O.z[1]); }
  if (O.kind == "sticker") { var sc2 = mo.properties[1]; var t1 = c.inPoint.seconds; sc2.setTimeVarying(true); var K = [[0, 160], [0.12, 96], [0.2, 102], [0.3, 100]];
    for (var q2 = 0; q2 < K.length; q2++) { sc2.addKey(t1 + K[q2][0]); sc2.setValueAtKey(t1 + K[q2][0], K[q2][1]); } }
  if (O.echo) { var vt2 = s.videoTracks[O.v + 1]; var c2 = put(vt2, it, O.off + O.echo, O.dur - O.echo, O.t + O.echo);
    if (c2) { var t2 = c2.inPoint.seconds; var op = c2.components[0].properties[0]; op.setTimeVarying(true); op.addKey(t2); op.setValueAtKey(t2, 42.3); op.addKey(t2 + 0.27); op.setValueAtKey(t2 + 0.27, 0);
      var s2 = c2.components[1].properties[1]; s2.setTimeVarying(true); s2.addKey(t2); s2.setValueAtKey(t2, 100); s2.addKey(t2 + 0.95); s2.setValueAtKey(t2 + 0.95, 462);
      try { c2.components[0].properties[1].setValue(14, true); } catch (eb) { r.fail.push("blend " + eb); } } }
  r.n++; }
return __result(r);''' % J(OV), "overlays", 900)


def stage_flashback():
    """takes futuros: Lumetri lavado + sépia (V2); flashes branco nas pontas; lavagem branca na revelação das poças (V3)"""
    d = dump()
    FUT = [o for o in PLAN["overlays"] if o["kind"] == "futuro"]
    idx = [clip_index(d, fr(o["t"]), 1) for o in FUT]
    LUM = {"14": 25, "16": 62, "19": 0.5, "20": -8, "22": 15, "23": -8, "24": 25, "40": 35, "110": -2.0, "111": 40, "113": 75}
    run(PRE + '''app.enableQE(); var q = qe.project.getActiveSequence(); var vt = s.videoTracks[1]; var IDX = %s; var LUM = %s; r.n = 0; r.err = "";
function qidx(trk, ci) { var kk = -1; for (var i = 0; i < trk.numItems; i++) { if (String(trk.getItemAt(i).type) != "Empty") kk++; if (kk == ci) return i; } return ci; }
var qt = q.getVideoTrackAt(1);
for (var n = 0; n < IDX.length; n++) { var qi = qt.getItemAt(qidx(qt, IDX[n])); var c = vt.clips[IDX[n]];
  qi.addVideoEffect(qe.project.getVideoEffectByName("Cor de Lumetri")); var L = comp(c, "Cor de Lumetri");
  for (var key in LUM) { try { L.properties[parseInt(key)].setValue(LUM[key], true); } catch (e) { r.err += key + " "; } }
  qi.addVideoEffect(qe.project.getVideoEffectByName("Tonalidade")); var T = comp(c, "Tonalidade");
  T.properties[0].setColorValue(255, 64, 38, 14, true); T.properties[1].setColorValue(255, 255, 240, 205, true); T.properties[2].setValue(48, true); r.n++; }
return __result(r);''' % (J(idx), J(LUM)), "flashback", 600)
    SP = []
    for o, k in zip(FUT, idx):
        for nm, anc in ((o.get("preset_in"), "start"), (o.get("preset_out"), "end")):
            if nm: SP.append(bz.spec(nm, k, o.get("off", 0.0), o["dur"], anchor=anc, tscale=0.45))
    if SP:
        run(PRE + '''app.enableQE(); var q = qe.project.getActiveSequence(); var TRK = 1; var tr = s.videoTracks[1];
''' + bz.APPLY_JS % J(SP) + '''return __result(r);''', "flashes_v2", 600)
    FL = [o for o in PLAN["overlays"] if o.get("flash")]
    for o in FL:
        k = clip_index(d, fr(o["t"]), o["v"] - 1)
        run(PRE + '''app.enableQE(); var q = qe.project.getActiveSequence(); var V = %d; var K = %d; var vt = s.videoTracks[V]; var qt = q.getVideoTrackAt(V);
var kk = -1; for (var i = 0; i < qt.numItems; i++) { var qi = qt.getItemAt(i); if (String(qi.type) == "Empty") continue; kk++; if (kk == K) { qi.addVideoEffect(qe.project.getVideoEffectByName("Tonalidade")); break; } }
var c = vt.clips[K]; var T = comp(c, "Tonalidade"); T.properties[0].setColorValue(255, 255, 255, 255, true); T.properties[1].setColorValue(255, 255, 255, 255, true);
var am = T.properties[2]; var t0 = c.inPoint.seconds; am.setTimeVarying(true); am.addKey(t0); am.setValueAtKey(t0, %s); am.addKey(t0 + %s); am.setValueAtKey(t0 + %s, 0); r.ok = 1;
return __result(r);''' % (o["v"] - 1, k, o["flash"][0], o["flash"][1], o["flash"][1]), "flash_broll", 300)


def music_rows():
    M = PLAN["music"]; rows = []
    for i, m in enumerate(M):
        if not m["file"]: continue
        end = M[i + 1]["t"] if i + 1 < len(M) else PLAN["end"]
        rows.append({"name": os.path.basename(m["file"]), "a": fr(m["t"]), "b": fr(end), "off": m["src"], "g": lin(m["g"]), "file": m["file"]})
    return rows


def stage_music():
    import soundfile as sf
    MM = []
    for r_ in music_rows():
        dur = sf.info(r_["file"]).duration
        if r_["off"] + (r_["b"] - r_["a"]) > dur:      # faixa curta: encurta (não faz loop)
            r_["b"] = fr(r_["a"] + dur - r_["off"] - 0.05)
        MM.append({k: r_[k] for k in ("name", "a", "b", "off", "g")})
    run(PRE + '''var mt = s.audioTracks[3]; for (var k = mt.clips.numItems - 1; k >= 0; k--) mt.clips[k].remove(0, 0);
var M = %s; r.n = 0; r.miss = "";
for (var k = 0; k < M.length; k++) { var it = find(M[k].name); if (!it) { r.miss += M[k].name + "|"; continue; }
  it.setInPoint(M[k].off, 4); it.setOutPoint(M[k].off + M[k].b - M[k].a, 4); mt.overwriteClip(it, M[k].a); it.clearInPoint(); it.clearOutPoint();
  var ci = clipAt(mt, M[k].a); if (ci >= 0) { var cl = mt.clips[ci]; var e = new Time(); e.seconds = M[k].b; cl.end = e; var pr = lvl(cl); pr.setTimeVarying(false); pr.setValue(M[k].g, true); r.n++; } }
return __result(r);''' % J(MM), "music", 900)


def sfx_rows():
    from anchors import CUTS
    import soundfile as sf
    busy = {4: -1.0, 5: -1.0, 6: -1.0, 7: -1.0}; F = []
    for x in sorted(PLAN["sfx"], key=lambda x: x["t"]):
        t = x["t"]
        if x.get("cut"):
            c = min(CUTS, key=lambda c: abs(c - t))
            if -0.35 <= c - t <= 1.5 or abs(c - t) <= 0.35: t = c - x.get("pre", 0.06)
        nm = os.path.basename(x["file"])
        off = sxt.file_onset(x["file"])
        d0 = sf.info(x["file"]).duration
        d = min(x.get("dur", 2.5), d0 - off)
        if "g" in x: g = x["g"]
        else:
            import build_helpers as bh
            g = bh.gain(x["file"], off, d, nm)
        FIX = json.load(open(os.path.join(HERE, "gain_fix.json"))) if os.path.exists(os.path.join(HERE, "gain_fix.json")) else {}
        g = g + FIX.get("%s@%.2f" % (nm, fr(max(0.0, t))), 0.0)      # malha fechada (render v1): alvo +2 dB sobre a voz local (impactos +4)
        tr = next((k for k in (4, 5, 6, 7) if busy[k] <= t - 0.01), None)
        if tr is None: print("sem trilha livre p/", nm, t); continue
        busy[tr] = t + d
        F.append({"name": nm, "t": fr(max(0.0, t)), "dur": round(d, 4), "off": round(off, 4), "tr": tr, "g": lin(g), "db": g, "why": x["why"]})
    return F


def stage_sfx():
    F = sfx_rows()
    json.dump(F, open(os.path.join(HERE, "sfx_placed.json"), "w", encoding="utf8"), ensure_ascii=False, indent=0)
    print("sfx:", len(F))
    for i in range(0, len(F), 60):
        run(PRE + '''var F = %s; r.n = 0; r.miss = "";
for (var q = 0; q < F.length; q++) { var it = find(F[q].name); if (!it) { r.miss += F[q].name + "|"; continue; } var st = s.audioTracks[F[q].tr];
  it.setInPoint(F[q].off, 4); it.setOutPoint(F[q].off + F[q].dur, 4); st.overwriteClip(it, F[q].t); it.clearInPoint(); it.clearOutPoint();
  var ci = clipAt(st, F[q].t); if (ci >= 0) { var pr = lvl(st.clips[ci]); pr.setTimeVarying(false); pr.setValue(F[q].g, true); r.n++; } }
return __result(r);''' % J(F[i:i + 60]), "sfx", 900)


def stage_mutes():
    run(PRE + '''var MU = %s; r.n = 0;
for (var m = 0; m < MU.length; m++) { var tr = s.audioTracks[MU[m].track];
  for (var c = 0; c < tr.clips.numItems; c++) { var cl = tr.clips[c]; var a = cl.start.seconds, b = cl.end.seconds;
    var cov = Math.min(b, MU[m].b) - Math.max(a, MU[m].a); if (cov > 0.5 * (b - a)) { cl.disabled = true; r.n++; } } }
return __result(r);''' % J(PLAN["mutes"]), "mutes", 300)


def stage_bleep():
    for b in PLAN["bleeps"]:
        a, e = fr(b["t"]), fr(b["end"])
        run(PRE + '''app.enableQE(); var q = qe.project.getActiveSequence(); q.getAudioTrackAt(1).razor(tc(%s)); q.getAudioTrackAt(1).razor(tc(%s));
var tr = s.audioTracks[1]; var k = -1; for (var c = 0; c < tr.clips.numItems; c++) if (Math.abs(tr.clips[c].start.seconds - %s) < 0.02) k = c;
if (k >= 0) tr.clips[k].disabled = true; r.k = k;
var it = find("bleep_1k.wav"); var bt = s.audioTracks[8]; it.setInPoint(0, 4); it.setOutPoint(%s, 4); bt.overwriteClip(it, %s); it.clearInPoint(); it.clearOutPoint();
var ci = clipAt(bt, %s); if (ci >= 0) { var pr = lvl(bt.clips[ci]); pr.setTimeVarying(false); pr.setValue(%s, true); }
return __result(r);''' % (a, e, a, round(e - a, 4), a, a, lin(-8.0)), "bleep", 300)


def stage_marks():
    MKS = list(PLAN["marks"])
    for m in PLAN["music"]:
        MKS.append({"t": m["t"], "txt": ("MÚSICA: " + os.path.basename(m["file"])[:60] if m["file"] else "MÚSICA CALA") + " — " + m["why"]})
    for o in PLAN["overlays"]:
        if o["kind"] != "futuro": MKS.append({"t": o["t"], "txt": o["kind"].upper() + ": " + o["why"]})
    for b in PLAN["bleeps"]: MKS.append({"t": b["t"], "txt": "BIPE: " + b["why"]})
    MKS.append({"t": 0.0, "txt": "EDIÇÃO Claude 19/10 — música e SFX são APOSTAS (não ouço); time-lapses nas 2 vagas = hipótese da nota 'time lapse editor'"})
    run(PRE + '''var MK = %s; for (var k = 0; k < MK.length; k++) { var mk = s.markers.createMarker(MK[k].t); mk.name = MK[k].txt.substr(0, 60); mk.comments = MK[k].txt; }
r.n = MK.length; return __result(r);''' % J([{"t": round(m["t"], 4), "txt": m["txt"]} for m in MKS]), "marks", 300)


STAGES = {"clone": stage_clone, "import": stage_import, "tracks": stage_tracks, "split": stage_split, "zoom": stage_zoom, "stretch": stage_stretch,
          "presets": stage_presets, "reveals": stage_reveals, "overlays": stage_overlays, "flashback": stage_flashback, "music": stage_music,
          "sfx": stage_sfx, "mutes": stage_mutes, "bleep": stage_bleep, "marks": stage_marks}

if __name__ == "__main__":
    for st in sys.argv[1].split(","):
        print("==", st, flush=True); STAGES[st]()
