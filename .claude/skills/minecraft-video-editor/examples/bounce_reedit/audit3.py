import json, sys, numpy as np, soundfile as sf, subprocess
F=json.load(open('plan_sfx.json',encoding='utf8'))
def rd(n): x,sr=sf.read('D:/Pobrs/bounce/stem3_%s.wav'%n,always_2d=True); return x,sr
voz,sr=rd('voz'); mus,_=rd('musica'); sfx,_=rd('sfx')
n=min(len(voz),len(mus),len(sfx)); voz,mus,sfx=voz[:n],mus[:n],sfx[:n]
db=lambda x:20*np.log10(x+1e-9)
def lufs(path):
    r=subprocess.run(['ffmpeg','-hide_banner','-nostats','-i',path,'-af','ebur128','-f','null','-'],capture_output=True,text=True)
    import re; return re.findall(r'I:\s+(-?\d+\.\d+) LUFS',r.stderr)[-1]
print('LUFS voz',lufs('D:/Pobrs/bounce/stem3_voz.wav'),'musica',lufs('D:/Pobrs/bounce/stem3_musica.wav'))
E=lambda x:10*np.log10((x**2).mean())
print('energia: musica vs voz %.1f dB ; sfx vs voz %.1f dB'%(E(mus)-E(voz),E(sfx)-E(voz)))
rows=[]
for x in F:
    a=int(x['t']*sr); b=int((x['t']+min(x['dur'],1.5))*sr)
    ps=db(np.abs(sfx[a:b]).max())
    a2=int(max(x['t']-1.0,0)*sr); b2=int((x['t']+1.5)*sr)
    seg=np.abs(voz[a2:b2]).max(axis=1); hop=int(0.05*sr)
    fp=np.array([seg[i:i+hop].max() for i in range(0,max(len(seg)-hop,1),hop)]); pb=db(np.percentile(fp,90))
    rows.append((x['t'],x['key'],ps,pb,ps-pb,x['gdb'],x['delta']))
d=np.array([r[4] for r in rows]); print('SFX pico vs voz p90: mediana %.1f p10 %.1f p90 %.1f'%(np.median(d),np.percentile(d,10),np.percentile(d,90)))
if len(sys.argv)>1:
    for r in rows: print('%7.2f %-8s sfx %6.1f voz %6.1f delta %+5.1f (clip %+.1f, delta plano %+.1f)'%r)
