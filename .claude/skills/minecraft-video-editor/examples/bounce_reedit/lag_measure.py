import json, os, subprocess, numpy as np, soundfile as sf, tempfile, sys
sys.path.insert(0,'.')
import events as E
LIB=os.path.expanduser("~/.claude/skills/minecraft-video-editor/library/sfx")
rm=np.load('D:/Pobrs/bounce/rms_mat.npy'); rp=np.load('D:/Pobrs/bounce/rms_ped.npy')
def energy_onset(R,t,lo=0.45,hi=0.10):
    i0=int(max(t-lo,0)*100); i1=int((t+hi)*100)
    seg=R[i0:i1]
    if len(seg)<10: return None
    floor=np.percentile(R[max(i0-60,0):i0+5],20) if i0>60 else -60
    thr=max(-38,floor+14)
    idx=np.where(seg>thr)[0]
    return (i0+idx[0])/100 if len(idx) else None
def file_onset(fn):
    tmp=os.path.join(tempfile.gettempdir(),'onset.wav')
    subprocess.run(['ffmpeg','-y','-loglevel','error','-t','1.5','-i',os.path.join(LIB,fn),'-vn','-ac','1','-ar','48000',tmp],check=True)
    x,sr=sf.read(tmp); a=np.abs(x); pk=a.max(); thr=max(10**(-45/20),pk*10**(-30/20))
    idx=np.where(a>thr)[0]; return idx[0]/sr if len(idx) else 0.0
ev,bad,vp=E.resolve()
rows=[]
for x in ev:
    if x['q'] is None: continue
    R=rm if (x['who'] if 'who' in x else 'M')=='M' else rp
rows=[]
from events import S
for (t,q,who,at,off,key,why,snap),x in zip(S,sorted(ev,key=lambda z:0)) if False else []: pass
# reconstruir who por evento
who_of={(s[0],s[5]):s[2] for s in S}
asr_late=[];file_on=[];tot=[]
for x in ev:
    if x['q'] is None or who_of.get((x['hint'],x['key']))!='M': continue
    at=[s[3] for s in S if s[0]==x['hint'] and s[5]==x['key']][0]
    if at!='start': continue
    on=energy_onset(rm,x['t'])
    if on is None: continue
    fo=file_onset(x['file'])
    asr_late.append(x['t']-on); file_on.append(fo); tot.append(x['t']+fo-on)
print(len(tot),'eventos (M, âncora start): ASR atrasa %.2f s (mediana); início audível do arquivo +%.2f s; SFX audível chega %.2f s DEPOIS da fala (mediana, p25 %.2f p75 %.2f)'%(np.median(asr_late),np.median(file_on),np.median(tot),np.percentile(tot,25),np.percentile(tot,75)))
