import json, os, sys
import numpy as np, soundfile as sf
from scipy.signal import resample_poly
BASE = r"D:\Gravacoes Minecraft\edit\Matteeoo_2026-10-04\sync\audio_full"
OUT = r"D:\Pobrs\bounce"
d = json.load(open("seq_dump6.json", encoding="utf8"))
END = d["end"]
for ti, name in ((0, "mat"), (1, "ped")):
    n16 = int(END * 16000) + 16000
    buf = np.zeros(n16, dtype=np.float32)
    for c in d["A"][ti]["rows"]:
        if c["off"]: continue
        x, sr = sf.read(os.path.join(BASE, c["f"]), start=int(c["i"] * 48000), stop=int(c["o"] * 48000), always_2d=True)
        y = resample_poly(x.mean(axis=1), 1, 3).astype(np.float32)
        a = int(round(c["a"] * 16000))
        buf[a:a + len(y)] += y[:max(0, min(len(y), n16 - a))]
    sf.write(os.path.join(OUT, "tl6_%s.wav" % name), buf, 16000, subtype="PCM_16")
    m = len(buf) // 160
    rms = 20 * np.log10(np.sqrt((buf[:m * 160].reshape(m, 160) ** 2).mean(axis=1)) + 1e-9)
    np.save(os.path.join(OUT, "rms6_%s.npy" % name), rms.astype(np.float32))
    print(name, len(buf) / 16000, "s peak", float(np.abs(buf).max()), flush=True)
