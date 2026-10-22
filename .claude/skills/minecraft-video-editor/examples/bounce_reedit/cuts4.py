"""3ª passada de pausas na V3 (tempo ATUAL): respirações/estalos isolados (curtos, fracos, com silêncio dos dois lados, sem palavra do ASR) deixam de contar como fala,
o que abre pausas maiores; corta o miolo (sobra 0,14 / 0,20 / 0,30 s conforme o movimento da imagem). Valida a energia nas bordas de cada corte."""
import json, subprocess
import numpy as np

rm = np.load("D:/Pobrs/bounce/rms6_mat.npy"); rp = np.load("D:/Pobrs/bounce/rms6_ped.npy"); N = min(len(rm), len(rp))
rem1 = sorted((a, b) for a, b, _ in json.load(open("remove.json", encoding="utf8")))
rem2 = sorted(json.load(open("remove2_ok.json")))


def mapper(rem):
    def new(t):
        acc = 0
        for a, b in rem:
            if t >= b: acc += b - a
            elif t > a: acc += t - a; break
            else: break
        return t - acc
    return new


new1, new2 = mapper(rem1), mapper(rem2)
inside = lambda rem, t: any(a < t < b for a, b in rem)
words = []
for n in ("mat", "ped"):
    for w in json.load(open("D:/Pobrs/bounce/asr_%s.json" % n, encoding="utf8"))["words"]:
        if inside(rem1, w["s"]): continue
        t1 = new1(w["s"])
        if inside(rem2, t1): continue
        s = new2(t1); e = s + min(w["e"] - w["s"], 0.45)
        R = rm if n == "mat" else rp          # o Whisper estica a palavra: apara o fim até o último quadro com energia (> -46 dB)
        ia, ib = int(s * 100), min(int(e * 100) + 1, N)
        live = np.where(R[ia:ib] > -46)[0]
        e = s + (live[-1] + 1) / 100 if len(live) else s + 0.05
        words.append((s, e))


def has_word(a, b): return any(s < b + 0.05 and e > a - 0.05 for s, e in words)


on = rm[:N] > -34
for i in range(1, N):
    if not on[i] and on[i - 1] and rm[i] > -42: on[i] = True
for i in range(N - 2, -1, -1):
    if not on[i] and on[i + 1] and rm[i] > -42: on[i] = True
comps = []; i = 0
while i < N:
    if on[i]:
        j = i
        while j < N and on[j]: j += 1
        comps.append((i, j)); i = j
    else: i += 1
breath = np.zeros(N, bool); nb = 0
for k, (i, j) in enumerate(comps):
    dur = (j - i) / 100; pk = rm[i:j].max()
    prev_gap = (i - comps[k - 1][1]) / 100 if k else 9
    next_gap = (comps[k + 1][0] - j) / 100 if k + 1 < len(comps) else 9
    if dur < 0.30 and pk < -27 and prev_gap >= 0.15 and next_gap >= 0.15 and not has_word(i / 100, j / 100) and rp[i:j].max() < -34:
        breath[i:j] = True; nb += 1
print("respirações/estalos isolados:", nb)
act = on & ~breath
act |= rp[:N] > -30
for s, e in words: act[max(int((s - 0.05) * 100), 0):min(int((e + 0.07) * 100), N)] = True

SFX = json.load(open("plan_sfx.json", encoding="utf8"))
sfxw = [(x["t"], x["t"] + x["dur"]) if x["dur"] < 1.0 else (x["t"], x["t"] + 0.35) for x in SFX]
d = json.load(open("seq_dump6.json", encoding="utf8"))
V1, V2 = d["V"][0]["rows"], d["V"][1]["rows"]
SRC = {0: r"D:\Gravacoes Minecraft\2026-10-04 21-18-44.mp4", 1: r"C:\Users\mathe\Downloads\2026-10-04 21-17-38.mp4"}


def active(t):
    for ti, R in ((1, V2), (0, V1)):
        for r in R:
            if r["a"] - 1e-3 <= t < r["b"] - 1e-3 and not r["off"]: return ti, r
    return None, None


def motion(a, b):
    ti, r = active((a + b) / 2)
    if r is None: return 0
    cmd = ["ffmpeg", "-v", "error", "-ss", "%.3f" % (r["i"] + (a - r["a"])), "-t", "%.3f" % (b - a), "-i", SRC[ti], "-vf", "fps=8,scale=160:90,format=gray", "-f", "rawvideo", "-"]
    o = subprocess.run(cmd, capture_output=True).stdout; n = len(o) // 14400
    if n < 2: return 0
    F = np.frombuffer(o[:n * 14400], dtype=np.uint8).reshape(n, 90, 160).astype(np.float32)
    return float(np.mean([np.abs(F[i + 1] - F[i]).mean() for i in range(n - 1)]))


PROT = [(0, 0.3), (611.0, 633.0)]       # pickup do Pedro (tempo atual)
out = []; i = 0
while i < N:
    if not act[i]:
        j = i
        while j < N and not act[j]: j += 1
        a, b = i / 100, j / 100
        if b - a >= 0.28 and not any(a < pb and b > pa for pa, pb in PROT) and b < 639.0:
            mv = motion(a, b)
            keep = 0.14 if mv < 10 else (0.20 if mv < 20 else 0.30)
            if b - a - keep >= 0.12:
                mid = (a + b) / 2; x0, x1 = mid - (b - a - keep) / 2, mid + (b - a - keep) / 2
                if not any(x0 < e and x1 > s for s, e in sfxw):
                    ia, ib = int(round(x0 * 100)), int(round(x1 * 100))
                    ea, eb = rm[ia - 1:ia + 2].max(), rm[ib - 1:ib + 2].max(); pa_, pb_ = rp[ia - 1:ia + 2].max(), rp[ib - 1:ib + 2].max()
                    viol = ea > -40 or eb > -40 or pa_ > -32 or pb_ > -32 or rp[ia:ib].max() > -26
                    if not viol: out.append([round(x0 * 60) / 60, round(x1 * 60) / 60, round(mv, 1), round(b - a, 2)])
        i = j
    else: i += 1
json.dump([[a, b] for a, b, _, _ in out], open("remove3_ok.json", "w"))
print(len(out), "cortes, %.1f s" % sum(b - a for a, b, _, _ in out))
for o in out[:20]: print(o)
