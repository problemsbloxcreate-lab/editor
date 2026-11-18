import numpy as np, soundfile as sf, json
from scipy.signal import fftconvolve
SR = 48000; H = 480   # envelope 100 Hz
def env(path, t0, d):
    x, sr = sf.read(path, start=int(t0 * SR), frames=int(d * SR), dtype='float32')
    x = x[:len(x) // H * H].reshape(-1, H)
    e = np.log10((x ** 2).mean(1) + 1e-9)
    return (e - e.mean()) / (e.std() + 1e-9)
def lag(a, b, maxl=300):   # retorna l tal que b[t+l] ~ a[t]  (em 0,01 s)
    c = fftconvolve(b, a[::-1], mode='full'); mid = len(a) - 1
    seg = c[mid - maxl: mid + maxl + 1]; i = int(np.argmax(seg)); return (i - maxl) / 100.0, float(seg[i] / len(a))
V = json.load(open('vad.json'))
def onlyspk(tr_on, tr_off, t0, t1):
    """segundos (100 Hz) onde só tr_on fala"""
    pass
res = []
for t0 in (300, 700, 1000, 1400, 1700, 2000, 2250):
    a1 = env('A/s1.wav', t0, 60); a3 = env('A/s3.wav', t0, 60)
    b = env('B/s1.wav', t0 + 4.62 - 3, 66)
    lm, cm = lag(a1, b); lp, cp = lag(a3, b)
    res.append((t0, round(lm - 3, 3), round(cm, 3), round(lp - 3, 3), round(cp, 3)))
    print(t0, 'Matteo(A1)->B: +%.2f (r %.2f)   PC(A3)->B: +%.2f (r %.2f)' % (lm - 3 + 4.62, cm, lp - 3 + 4.62, cp))
for t0 in (60, 200, 400):
    c1 = env('C/s1.wav', t0, 60); c3 = env('C/s3.wav', t0, 60)
    b = env('B/s1.wav', t0 + 3495.77 - 3, 66)
    lm, cm = lag(c1, b); lp, cp = lag(c3, b)
    print('C', t0, 'Matteo(C1)->B: +%.2f (r %.2f)   PC(C3)->B: +%.2f (r %.2f)' % (lm - 3 + 3495.77, cm, lp - 3 + 3495.77, cp))
