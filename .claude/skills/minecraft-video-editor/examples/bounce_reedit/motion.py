import json, subprocess, numpy as np, sys
d=json.load(open('seq_dump.json',encoding='utf8'))
V1=[r for r in d['V'][0]['rows']]; V2=[r for r in d['V'][1]['rows']]
SRC={0:r"D:\Gravacoes Minecraft\2026-10-04 21-18-44.mp4",1:None}
import glob
p3=glob.glob(r"C:\Users\mathe\Downloads\2026-10-04 21-17-38.mp4")
print(p3)
def active(t):
    for r in V2:
        if r['a']-1e-3<=t<r['b']-1e-3 and not r['off']: return 1,r
    for r in V1:
        if r['a']-1e-3<=t<r['b']-1e-3 and not r['off']: return 0,r
    return None,None
def frames(path,ss,dur,fps=8):
    cmd=['ffmpeg','-v','error','-ss',f'{ss:.3f}','-t',f'{dur:.3f}','-i',path,'-vf',f'fps={fps},scale=160:90,format=gray','-f','rawvideo','-']
    out=subprocess.run(cmd,capture_output=True).stdout
    n=len(out)//(160*90)
    return np.frombuffer(out[:n*160*90],dtype=np.uint8).reshape(n,90,160).astype(np.float32)
def motion(a,b):
    ti,r=active((a+b)/2)
    if r is None: return None
    path=SRC[0] if ti==0 else p3[0]
    ss=r['i']+(a-r['a']); 
    F=frames(path,ss,b-a)
    if len(F)<2: return 0
    return float(np.mean([np.abs(F[i+1]-F[i]).mean() for i in range(len(F)-1)])), ti
if __name__=="__main__":
    gaps=json.load(open('gaps.json'))
    out=[]
    for a,b in gaps:
        m=motion(a,b)
        out.append((a,b,m))
        print("%.2f-%.2f (%.2f) motion %s"%(a,b,b-a,m),flush=True)
    json.dump(out,open('gaps_motion.json','w'))
