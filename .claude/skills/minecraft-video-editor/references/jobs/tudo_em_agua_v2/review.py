"""Folhas de revisão da timeline: o que está NA TELA a cada passo (V3 cinemática > V2 gancho/POV > V1), quadro real do bruto.
uso: python review.py [plan.json] [passo_s] [t0] [t1]  -> review/sheet_NN.jpg (10x6 quadros, rótulo tl + fonte + tempo da fonte)"""
import json, os, sys, subprocess
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw
W = os.path.dirname(os.path.abspath(__file__))
P = json.load(open(sys.argv[1] if len(sys.argv) > 1 else os.path.join(W, 'plan.json'), encoding='utf8'))
STEP = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
T0 = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
T1 = float(sys.argv[4]) if len(sys.argv) > 4 else P['dur_tl'] - 12
OUT = os.path.join(W, 'review'); os.makedirs(os.path.join(OUT, 'fr'), exist_ok=True)
RAW = dict(P['raw'])
CINE = 'D:/Pobrs/tudoagua/cine/out'


def at(t):
    for c in P.get('cine', []):
        if c['tl'] <= t < c['tl'] + c['dur']: return ('cine', CINE + '/' + c['id'] + '.mp4', c['pre'] + t - c['tl'], c['id'])
    for h in P.get('hook', []):
        if h['tl'] <= t < h['tl'] + h['dur']: return ('hook', h['file'], t - h['tl'], 'gancho')
    for c in P.get('pov', []):
        if c['tl'] <= t < c['tl'] + c['dur']: return ('pov', RAW[c['src']], c['src_in'] + t - c['tl'], 'POV ' + c['src'])
    for k in P['keeps']:
        if k['tl_in'] <= t < k['tl_out']: return ('v1', RAW[k['src']], k['src_in'] + t - k['tl_in'], k['src'] + ' ' + k['seg'])
    return None


ts = []
t = T0
while t < T1:
    ts.append(round(t, 3)); t += STEP
items = [(t, at(t)) for t in ts]


def grab(it):
    t, a = it
    out = os.path.join(OUT, 'fr', '%08.2f.jpg' % t)
    if a is None or os.path.exists(out): return
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', '%.3f' % a[2], '-i', a[1], '-frames:v', '1', '-vf', 'scale=320:180', '-q:v', '4', out])


with ThreadPoolExecutor(6) as ex: list(ex.map(grab, items))
C, R, w, h = 8, 6, 320, 180
for n in range(0, len(items), C * R):
    sh = Image.new('RGB', (C * w, R * (h + 16)), (20, 20, 20)); d = ImageDraw.Draw(sh)
    for j, (t, a) in enumerate(items[n:n + C * R]):
        x, y = (j % C) * w, (j // C) * (h + 16)
        f = os.path.join(OUT, 'fr', '%08.2f.jpg' % t)
        if os.path.exists(f): sh.paste(Image.open(f), (x, y + 16))
        lab = '%.1f %s %.1f' % (t, a[3] if a else '-', a[2] if a else 0)
        d.text((x + 3, y + 2), lab, fill=(255, 230, 80) if a and a[0] == 'pov' else (255, 255, 255))
    sh.save(os.path.join(OUT, 'sheet_%03d.jpg' % (n // (C * R))), quality=80)
print('folhas', (len(items) + C * R - 1) // (C * R), 'quadros', len(items))
