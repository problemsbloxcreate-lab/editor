import json
import numpy as np
MACRO = [(102.45, 109.5, "vaca: Pedro repete 'voando/flutuando' 3x; fica até 'Sumiu'"),
         (119.0, 119.8, "'Eu vou, mano' repetido"), (128.0, 128.95, "'Vou pegar ele no ar' x3"),
         (169.0, 172.1, "gaguejo 'Ah, tem um... Oxi...'"), (350.0, 353.8, "tentativa picotada 'me prendi... pulo infinito'"),
         (383.5, 388.9, "enrolação do buraco + 'pensa num'"), (470.7, 471.5, "'Eu vou ir longe agora' repetido"),
         (475.7, 481.9, "tangente Nemo (Pedro não lembra)"), (483.3, 486.0, "tangente Nemo"),
         (511.4, 512.3, "'tá travando' repetido"), (516.2, 519.3, "'Nossa senhora' (3ª reação igual)")]
rm = np.load("D:/Pobrs/bounce/rms_mat.npy"); rp = np.load("D:/Pobrs/bounce/rms_ped.npy"); NN = min(len(rm), len(rp))
V = np.maximum(rm[:NN], rp[:NN]); Vs = np.convolve(V, np.ones(5) / 5, mode="same")


def best(t, w=0.35):
    i0, i1 = int((t - w) * 100), int((t + w) * 100)
    return (i0 + int(np.argmin(Vs[i0:i1]))) / 100


cuts = []
for a, b, why in MACRO:
    a2, b2 = best(a), best(b)
    if b2 - a2 > 0.3: cuts.append([a2, b2, "macro: " + why])
for a, b, mv in json.load(open("micro_cuts.json")):
    if any(a < cb and b > ca for ca, cb, _ in cuts): continue
    cuts.append([a, b, "pausa (mov %.0f)" % mv])
cuts.sort()
S = lambda t: round(t * 60) / 60
out = []
for a, b, w in cuts:
    a, b = S(a), S(b)
    if b - a < 0.1 or a >= 726.6: continue
    if out and a < out[-1][1] + 0.02:
        out[-1][1] = max(out[-1][1], b); continue
    out.append([a, b, w])
json.dump(out, open("remove.json", "w"), ensure_ascii=False)
print(len(out), "cortes, %.1f s" % sum(b - a for a, b, _ in out))
for c in out:
    if c[2].startswith("macro"): print(c)
