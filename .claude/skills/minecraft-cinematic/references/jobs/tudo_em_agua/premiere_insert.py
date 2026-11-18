"""Insere as cinemáticas CineCam na sequência (V3), ajusta o gancho (V2/SFX) e marca.
uso: python cine_insert.py check | go
Não mexe em V1 nem nas vozes: a cinemática cobre a imagem e a fala continua por baixo."""
import json, os, sys, shutil
MODE = sys.argv[1] if len(sys.argv) > 1 else 'check'
sys.argv = [sys.argv[0]]
from build import run, pre_seq, HEAD, J, bn, lin, bz
sys.path.insert(0, r'C:\Users\mathe\.claude\skills\minecraft-video-editor\scripts')
import sfx_timing as T
CINE = r'D:\Pobrs\tudoagua\cine\out'
LIBS = r'C:\Users\mathe\.claude\skills\minecraft-video-editor\library\sfx'
OV = r'D:\Pobrs\tudoagua\overlays'
# id, tl, dur, pre (in-point no arquivo), flash (None | tscale), porquê
C = [
    ('h1', 0.00, 3.80, 0.0, 1.0, 'gancho: a gota cai e o contagio toma a vila (e se o Minecraft todo virasse agua?)'),
    ('h2', 5.70, 2.50, 0.0, 0.6, 'gancho: os dois fugindo da parede de agua'),
    ('h3', 13.67, 2.75, 0.0, 0.6, 'gancho: a 1a esponja e os 3 feixes'),
    ('h4', 22.78, 2.15, 0.0, 0.6, 'gancho: o Creeper de agua gigante cresce atras deles'),
    ('c1', 82.25, 3.04, 0.6, None, 'ACAO: Pedro surfando a crista (Gabriel Medina)'),
    ('c5', 345.50, 3.30, 0.0, None, 'ACAO: a pedra da montanha vira agua (AGORA: PEDRA)'),
    ('c6', 445.10, 3.60, 0.0, 0.6, 'ACAO: o Creeper de agua explode e a onda engole o Pedro'),
    ('c9', 670.30, 2.70, 0.0, 0.6, 'ACAO: o Pedro vira agua (Avatar das Aguas)'),
    ('c11', 828.10, 3.90, 0.0, None, 'ACAO: o Creeper cresce ate o ceu (gigantesco problema)'),
    ('c14', 1007.68, 3.47, 0.0, None, 'ACAO: o mundo volta numa onda verde (a vila reaparecendo)'),
]
WH = os.path.join(LIBS, '19--Whoosh 39.wav'); SPL = os.path.join(LIBS, 'mc-random-splash.mp3')
SF = [  # arquivo, tl do som audível, ganho dB, dur
    (WH, 82.25 - 0.25, 0.0, 1.2), (WH, 828.10 - 0.25, 0.0, 1.2), (WH, 1007.68 - 0.25, 0.0, 1.2),
    (SPL, 1.27, -9.0, 1.6),            # a gota bate no chão (no lugar do pavio de creeper que abria o gancho antigo)
]
files = [os.path.join(CINE, c[0] + '.mp4') for c in C]
for f in files + [WH, SPL, os.path.join(OV, 'hook_02_A_2224.mp4')]:
    assert os.path.exists(f), 'falta ' + f

if MODE == 'check':
    W = [[x[1] - 0.2, x[1] + x[3]] for x in SF] + [[0.0, 0.6]]
    r = run(pre_seq() + '''r.path = p.path; r.seq = s.name; r.nv = s.videoTracks.numTracks; r.v3 = s.videoTracks[2].clips.numItems; r.v2 = [];
var v2 = s.videoTracks[1]; for (var i = 0; i < v2.clips.numItems; i++) r.v2.push([v2.clips[i].name, Math.round(v2.clips[i].start.seconds * 100) / 100, Math.round(v2.clips[i].end.seconds * 100) / 100]);
r.sfx = []; var W = %s; for (var t = 5; t <= 8; t++) { var at = s.audioTracks[t]; for (var i = 0; i < at.clips.numItems; i++) { var c = at.clips[i];
  for (var k = 0; k < W.length; k++) if (c.end.seconds > W[k][0] - 0.1 && c.start.seconds < W[k][1] + 0.1) r.sfx.push([t, c.name, Math.round(c.start.seconds * 100) / 100, Math.round(c.end.seconds * 100) / 100]); } }
r.a = []; for (var t = 0; t < s.audioTracks.numTracks; t++) r.a.push(s.audioTracks[t].clips.numItems);
r.vv = []; for (var t = 0; t < s.videoTracks.numTracks; t++) r.vv.push(s.videoTracks[t].clips.numItems);
r.mk = s.markers.numMarkers; return __result(r);''' % J(W), 'cine_check', 300)
    print(json.dumps(r, ensure_ascii=False, indent=1)[:4000])
    sys.exit()

# ---- go
r0 = run(pre_seq() + 'p.save(); r.path = p.path; return __result(r);', 'cine_save0', 300)
src = r0['path']; bak = src.replace('.prproj', ' BACKUP-antes-cinematicas-18nov.prproj')
if not os.path.exists(bak):
    shutil.copyfile(src, bak); print('backup', bak)
# 1) importar
run(HEAD + '''var F = %s; var bin = null; for (var i = 0; i < p.rootItem.children.numItems; i++) if (p.rootItem.children[i].name == "Cinematicas" && p.rootItem.children[i].type == 2) bin = p.rootItem.children[i];
if (!bin) bin = p.rootItem.createBin("Cinematicas"); var need = []; for (var k = 0; k < F.length; k++) { var nm = F[k].split("\\\\").pop(); if (!find(nm)) need.push(F[k]); }
if (need.length) p.importFiles(need, true, bin, false); r.imported = need.length; return __result(r);''' % J(files + [WH, SPL]), 'cine_import', 600)
# 2) V3: cinemáticas (+ V2: a montanha virando água em 8,2–10,9, já que 5,7–8,2 agora é a cinemática h2)
CL = [{'name': c[0] + '.mp4', 't': c[1], 'dur': c[2], 'pre': c[3]} for c in C]
run(pre_seq() + '''var CL = %s; var vt = s.videoTracks[2]; r.n = 0; r.fail = [];
r.a0 = []; for (var t = 0; t < s.audioTracks.numTracks; t++) r.a0.push(s.audioTracks[t].clips.numItems);
function clipAt(vt, t) { for (var j = 0; j < vt.clips.numItems; j++) if (Math.abs(vt.clips[j].start.seconds - t) < 0.02) return vt.clips[j]; return null; }
for (var k = 0; k < CL.length; k++) { var it = find(CL[k].name); if (!it) { r.fail.push("sem " + CL[k].name); continue; }
  it.setInPoint(CL[k].pre, 4); it.setOutPoint(CL[k].pre + CL[k].dur, 4); vt.overwriteClip(it, CL[k].t); it.clearInPoint(); it.clearOutPoint();
  var c = clipAt(vt, CL[k].t); if (!c) { r.fail.push("clip " + CL[k].name); continue; } var e = new Time(); e.seconds = CL[k].t + CL[k].dur; c.end = e; r.n++; }
var v2 = s.videoTracks[1]; var m = find("hook_02_A_2224.mp4"); if (m) { m.setInPoint(0, 4); m.setOutPoint(2.7, 4); v2.overwriteClip(m, 8.2); m.clearInPoint(); m.clearOutPoint();
  var c2 = clipAt(v2, 8.2); if (c2) { var e2 = new Time(); e2.seconds = 10.9; c2.end = e2; r.v2 = c2.name; } }
r.v3 = vt.clips.numItems; r.a1 = []; for (var t = 0; t < s.audioTracks.numTracks; t++) r.a1.push(s.audioTracks[t].clips.numItems);
return __result(r);''' % J(CL), 'cine_v3', 900)
# 3) flash branco: as 4 do gancho + explosão do creeper e transformação do Pedro (já tinham flash na V1, agora coberta)
SP = [bz.spec("White Flash B", ci=i, clip_in=c[3], clip_len=c[2], anchor='start', tscale=c[4]) for i, c in enumerate(C) if c[4]]
run(pre_seq() + '''app.enableQE(); var q = qe.project.getActiveSequence(); var TRK = 2; var tr = s.videoTracks[2];
''' + bz.APPLY_JS % J(SP) + '''return __result(r);''', 'cine_flash', 600)
# 4) SFX: pavio de creeper do início (0,03 s) desligado; splash da gota; whoosh antes das cinemáticas do miolo sem SFX no corte
F = []
for f, tl, g, d in SF:
    off = T.file_onset(f); F.append({'name': bn(f), 't': round(tl, 3), 'dur': d, 'off': round(off, 4), 'g': lin(g)})
run(pre_seq() + '''var F = %s; r.off = []; r.put = []; r.fail = [];
for (var t = 5; t <= 8; t++) { var at = s.audioTracks[t]; for (var i = 0; i < at.clips.numItems; i++) { var c = at.clips[i]; if (c.start.seconds < 0.3 && c.name.indexOf("fuse") >= 0) { c.disabled = true; r.off.push(c.name); } } }
function free(t, a, b) { var at = s.audioTracks[t]; for (var i = 0; i < at.clips.numItems; i++) { var c = at.clips[i]; if (c.end.seconds > a - 0.02 && c.start.seconds < b + 0.02) return false; } return true; }
for (var q2 = 0; q2 < F.length; q2++) { var it = find(F[q2].name); if (!it) { r.fail.push(F[q2].name); continue; } var tr = -1; for (var t = 5; t <= 8; t++) if (free(t, F[q2].t, F[q2].t + F[q2].dur)) { tr = t; break; }
  if (tr < 0) { r.fail.push("sem faixa " + F[q2].t); continue; } var st = s.audioTracks[tr];
  it.setInPoint(F[q2].off, 4); it.setOutPoint(F[q2].off + F[q2].dur, 4); st.overwriteClip(it, F[q2].t); it.clearInPoint(); it.clearOutPoint();
  var cl = null; for (var c = 0; c < st.clips.numItems; c++) if (Math.abs(st.clips[c].start.seconds - F[q2].t) < 0.01) cl = st.clips[c];
  if (cl) { var pr = lvl(cl); pr.setTimeVarying(false); pr.setValue(F[q2].g, true); r.put.push([tr, F[q2].name, F[q2].t]); } else r.fail.push("clip sfx " + F[q2].t); }
return __result(r);''' % J(F), 'cine_sfx', 600)
# 5) marcadores + salvar
MK = [{'t': c[1], 'txt': 'CINE %s: %s' % (c[0], c[5])} for c in C]
run(pre_seq() + '''var MK = %s; for (var k = 0; k < MK.length; k++) { var mk = s.markers.createMarker(MK[k].t); mk.name = MK[k].txt; mk.comments = MK[k].txt; }
r.n = MK.length; p.save(); return __result(r);''' % J(MK), 'cine_marks', 300)
