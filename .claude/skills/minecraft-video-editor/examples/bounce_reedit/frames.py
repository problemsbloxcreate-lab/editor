import json, subprocess, sys, os, glob
d=json.load(open('seq_dump.json',encoding='utf8'))
V1=d['V'][0]['rows']; V2=d['V'][1]['rows']
SRC={0:r"D:\Gravacoes Minecraft\2026-10-04 21-18-44.mp4",1:r"C:\Users\mathe\Downloads\2026-10-04 21-17-38.mp4"}
def active(t):
    for r in V2:
        if r['a']-1e-3<=t<r['b']-1e-3 and not r['off']: return 1,r
    for r in V1:
        if r['a']-1e-3<=t<r['b']-1e-3 and not r['off']: return 0,r
    return None,None
def grab(t,out):
    ti,r=active(t); ss=r['i']+(t-r['a'])
    subprocess.run(['ffmpeg','-y','-v','error','-ss',f'{ss:.3f}','-i',SRC[ti],'-frames:v','1','-vf','scale=480:-1',out])
    return ti
if __name__=="__main__":
    ts=[float(x) for x in sys.argv[2:]]
    outs=[]
    for i,t in enumerate(ts):
        o=f'D:/Pobrs/bounce/f_{i:02d}.jpg'; ti=grab(t,o); outs.append(o); print(t,'POV',ti)
    # contact sheet
    subprocess.run(['ffmpeg','-y','-v','error']+sum([['-i',o] for o in outs],[])+['-filter_complex',f'xstack=inputs={len(outs)}:layout='+'|'.join(f'{(i%3)*480}_{(i//3)*270}' for i in range(len(outs))),'-frames:v','1',sys.argv[1]])
