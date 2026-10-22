import json, sys, numpy as np, soundfile as sf
F=json.load(open('plan_sfx.json',encoding='utf8'))
base,sr=sf.read(r'D:\Pobrs\bounce\base_mix.wav',always_2d=True)
new,_=sf.read(sys.argv[1] if len(sys.argv)>1 else r'D:\Pobrs\bounce\mix1.wav',always_2d=True)
n=min(len(base),len(new)); base=base[:n]*4.0; new=new[:n]
sfx=new-base
def pk(x): return 20*np.log10(np.abs(x).max()+1e-9)
rows=[]
for x in F:
    a=int(x['t']*sr); b=int((x['t']+min(x['dur'],1.5))*sr)
    ps=pk(sfx[a:b]); a2=int(max(x['t']-0.6,0)*sr); b2=int((x['t']+1.4)*sr)
    seg=np.abs(base[a2:b2]).max(axis=1); hop=int(0.05*sr); fp=np.array([seg[i:i+hop].max() for i in range(0,len(seg)-hop,hop)]); pb=20*np.log10(np.percentile(fp,90)+1e-9); rows.append((x['t'],x['key'],ps,pb,ps-pb,x['gdb']))
d=np.array([r[4] for r in rows])
print('delta SFX-pico vs mix local: mediana %.1f  p10 %.1f p90 %.1f'%(np.median(d),np.percentile(d,10),np.percentile(d,90)))
for r in rows: print('%7.2f %-8s sfx %6.1f  mix %6.1f  delta %+5.1f  (clip %+.1f)%s'%(r[0],r[1],r[2],r[3],r[4],r[5],'  <<< ALTO' if r[4]>6 else ('  <<< BAIXO' if r[4]<-3 else '')))
print('pico global novo %.1f ; sem SFX %.1f'%(pk(new),pk(base)))
