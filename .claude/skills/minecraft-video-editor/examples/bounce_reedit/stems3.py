import subprocess, sys, os
BR=os.path.expanduser("~/.claude/skills/minecraft-video-editor/scripts/run_bridge.py")
SEQ="f933b83b"
def run(code, name, to=900):
    p=os.path.join(os.path.dirname(os.path.abspath(__file__)), name+".jsx"); open(p,"w",encoding="utf8").write(code)
    r=subprocess.run([sys.executable,"-X","utf8",BR,p,str(to)],capture_output=True,text=True,encoding="utf8"); print(name, r.stdout[-120:], r.stderr[-200:]); return r
PRE='''var p = app.project; var s = null; for (var i = 0; i < p.sequences.numSequences; i++) if (p.sequences[i].sequenceID.substr(0, 8) == "%s") s = p.sequences[i]; p.openSequence(s.sequenceID);
''' % SEQ
def mutes(m): return PRE+"var M=%s; for (var t=0;t<8;t++) s.audioTracks[t].setMute(M[t]); return __result(M);" % m
def export(out,a,b):
    return PRE+'''s.setInPoint(%f); s.setOutPoint(%f); var preset = new File("C:/Program Files/Adobe/Adobe Premiere Pro 2026/MediaIO/systempresets/3F3F3F3F_57415645/Waveform Audio 48kHz 16-bit.epr");
var r={}; r.exp = s.exportAsMediaDirect(new File("%s").fsName, preset.fsName, 1); return __result(r);''' % (a,b,out)
for name,m in (("voz",[0,0,1,0,1,1,1,1]),("musica",[1,1,1,1,0,1,1,1]),("sfx",[1,1,1,1,1,0,0,0])):
    run(mutes(m),"mut"); run(export("D:/Pobrs/bounce/stem3_%s.wav"%name,0,679.1),"exs")
run(mutes([0,0,1,0,0,0,0,0]),"mut")
