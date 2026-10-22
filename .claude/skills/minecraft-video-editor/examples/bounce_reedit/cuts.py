import json, numpy as np
from motion import motion
W=[]
for n in ('mat','ped'):
    for w in json.load(open(r'D:\Pobrs\bounce\asr_%s.json'%n,encoding='utf8'))['words']: W.append((w['s'],w['e']))
rm=np.load(r'D:\Pobrs\bounce\rms_mat.npy'); rp=np.load(r'D:\Pobrs\bounce\rms_ped.npy')
N=min(len(rm),len(rp))
act=np.zeros(N,bool)
for s,e in W:
    act[max(int((s-0.05)*100),0):min(int((e+0.07)*100),N)]=True
act|=rm[:N]>-42
act|=rp[:N]>-30
# fecha buracos de <60ms
i=0
PROT=[(0,0.4),(696.0,719.5)]
def prot(a,b): return any(a<pb and b>pa for pa,pb in PROT)
gaps=[];i=0
while i<N:
    if not act[i]:
        j=i
        while j<N and not act[j]: j+=1
        if (j-i)/100>=0.40: gaps.append((i/100,j/100))
        i=j
    else: i+=1
print(len(gaps), sum(b-a for a,b in gaps))
out=[]
for a,b in gaps:
    if prot(a,b): continue
    m=motion(a,b) if b-a>=0.4 else None
    mv=m[0] if m else 0
    keep=0.16 if mv<10 else (0.30 if mv<20 else 0.45)
    if b-a-keep<0.12: continue
    mid=(a+b)/2
    out.append((round(mid-(b-a-keep)/2,3),round(mid+(b-a-keep)/2,3),round(mv,1)))
json.dump(out,open('micro_cuts.json','w'))
print(len(out), 'remover %.1f s'%sum(b-a for a,b,_ in out))
