"""2ª passada de pausas na V3 (tempo NOVO atual): atividade = energia do mic (hist. -34/-42) | Pedro > -30 | palavras do ASR com duração LIMITADA a 0,45 s (o Whisper estica a última palavra). Corta o miolo da pausa; sobra 0,15/0,28/0,42 s conforme movimento."""
import json, numpy as np, subprocess, sys
rm = np.load("D:/Pobrs/bounce/rms4_mat.npy"); rp = np.load("D:/Pobrs/bounce/rms4_ped.npy"); N = min(len(rm), len(rp))
rem = sorted((a, b) for a, b, _ in json.load(open("remove.json", encoding="utf8")))
def new(t):
    acc = 0
    for a, b in rem:
        if t >= b: acc += b - a
        elif t > a: acc += t - a; break
        else: break
    return t - acc
def inside(t): return any(a < t < b for a, b in rem)
act = np.zeros(N, bool)
# mic: fala/reação com histerese
hi = rm[:N] > -34
on = hi.copy()
for i in range(1, N):
    if not on[i] and on[i - 1] and rm[i] > -42: on[i] = True
for i in range(N - 2, -1, -1):
    if not on[i] and on[i + 1] and rm[i] > -42: on[i] = True
act |= on
act |= rp[:N] > -30
for n in ("mat", "ped"):
    for w in json.load(open(r"D:\Pobrs\bounce\asr_%s.json" % n, encoding="utf8"))["words"]:
        if inside(w["s"]): continue
        s = new(w["s"]); e = s + min(w["e"] - w["s"], 0.45)
        act[max(int((s - 0.05) * 100), 0):min(int((e + 0.07) * 100), N)] = True
# palavras que ficaram só como "cauda" curta (<80 ms) não contam
SFX = json.load(open("plan_sfx.json", encoding="utf8"))
sfxw = [(x["t"], x["t"] + x["dur"]) if x["dur"] < 1.0 else (x["t"], x["t"] + 0.35) for x in SFX]   # SFX longo: pode cortar na cauda (depois de 0,35 s)
d = json.load(open("seq_dump4.json", encoding="utf8"))
V1, V2 = d["V"][0]["rows"], d["V"][1]["rows"]
import glob
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
PROT = [(0, 0.3), (650.0, 672.0)]       # pickup do Pedro
out = []; i = 0
while i < N:
    if not act[i]:
        j = i
        while j < N and not act[j]: j += 1
        a, b = i / 100, j / 100
        if b - a >= 0.28 and not any(a < pb and b > pa for pa, pb in PROT) and b < 679.0:
            mv = motion(a, b) if b - a >= 0.28 else 0
            keep = 0.14 if mv < 10 else (0.20 if mv < 20 else 0.30)
            if b - a - keep >= 0.15:
                mid = (a + b) / 2; x0, x1 = mid - (b - a - keep) / 2, mid + (b - a - keep) / 2
                if not any(x0 < e and x1 > s for s, e in sfxw):
                    out.append([round(x0 * 60) / 60, round(x1 * 60) / 60, round(mv, 1), round(b - a, 2)])
                else: print("pula (SFX dentro):", round(a, 2), round(b, 2))
        i = j
    else: i += 1
json.dump(out, open("remove2.json", "w"))
print(len(out), "cortes, %.1f s" % sum(b - a for a, b, _, _ in out))
for o in out[:60]: print(o)
