"""Descritores de cada faixa de library/music (tempo, energia, brilho, modo maior/menor, densidade de onsets, trechos, ganho p/ -23 LUFS).
Uso: python music_features.py [--force]   -> library/music_features.json
Serve p/ escolher música por ATRIBUTO (não consigo ouvir): tensão = menor + lento/denso + centroide baixo; cômico = maior + saltitante; etc.
"""
import os, sys, json, subprocess, re
import numpy as np, librosa
LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "library", "music")
OUT = os.path.join(LIB, "..", "music_features.json")
MAJ = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
MIN = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])


def lufs(path):
    p = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True)
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", p.stderr)
    return float(m[-1]) if m else None


def analyze(path):
    y, sr = librosa.load(path, sr=22050, mono=True)
    dur = len(y) / sr
    hop = 512
    rms = librosa.feature.rms(y=y, hop_length=hop)[0]
    cen = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=hop)[0]
    onset = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)
    tempo = float(np.atleast_1d(librosa.beat.beat_track(onset_envelope=onset, sr=sr, hop_length=hop)[0])[0])
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr).mean(axis=1)
    best = (-2, None, None)
    for k in range(12):
        c = np.roll(chroma, -k)
        for name, prof in (("maior", MAJ), ("menor", MIN)):
            r = np.corrcoef(c, prof)[0, 1]
            if r > best[0]: best = (r, k, name)
    # energia por janela de 5 s (dB) p/ achar partes calmas/fortes
    w = int(5 * sr / hop)
    e5 = [float(20 * np.log10(rms[i:i + w].mean() + 1e-9)) for i in range(0, len(rms) - w, w)]
    return {"dur": round(dur, 1), "tempo": round(tempo), "rms_db": round(float(20 * np.log10(rms.mean() + 1e-9)), 1),
            "centroide_hz": round(float(cen.mean())), "onsets_por_s": round(float((onset > onset.mean() + onset.std()).sum()) / dur, 2),
            "modo": best[2], "tom": best[1], "conf_modo": round(float(best[0]), 2), "energia_5s_db": [round(x, 1) for x in e5],
            "dinamica_db": round(float(np.ptp(e5)), 1)}


def main():
    force = "--force" in sys.argv
    db = json.load(open(OUT, encoding="utf8")) if os.path.exists(OUT) and not force else {}
    for root, _, files in os.walk(LIB):
        for f in sorted(files):
            if not f.lower().endswith((".mp3", ".m4a", ".wav")): continue
            p = os.path.join(root, f); cat = os.path.relpath(root, LIB)
            key = cat + "/" + f
            if key in db: continue
            try:
                d = analyze(p); d["lufs"] = lufs(p); d["cat"] = cat; d["arquivo"] = f
                db[key] = d
                print(key, d["dur"], d["tempo"], d["modo"], d["lufs"], flush=True)
            except Exception as e:
                print("ERRO", key, e, flush=True)
            json.dump(db, open(OUT, "w", encoding="utf8"), ensure_ascii=False, indent=1)


main()
