"""Classifica o HUMOR de cada faixa/janela de library/music com o AST (AudioSet): Happy/Funny/Sad/Tender/Exciting/Angry/Scary music.
Como não consigo ouvir, isto é a "audição" da skill: escolher música por probabilidade de humor, não só pelo nome da pasta.
Uso: python music_moods.py [--force]  -> library/music_moods.json  {chave: {janelas:[{t, happy, funny,...}], media:{...}}}
Janelas de 10.24 s a cada 5 s, até 150 s da faixa.
"""
import os, sys, json
import numpy as np, librosa, torch
from transformers import ASTFeatureExtractor, ASTForAudioClassification
LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "library", "music")
OUT = os.path.join(LIB, "..", "music_moods.json")
MODEL = "MIT/ast-finetuned-audioset-10-10-0.4593"
WANT = {"Happy music": "happy", "Funny music": "funny", "Sad music": "sad", "Tender music": "tender", "Exciting music": "exciting",
        "Angry music": "angry", "Scary music": "scary", "Video game music": "videogame", "Electronic music": "electronic",
        "Pop music": "pop", "Rock music": "rock", "Orchestra": "orchestra", "Theme music": "theme", "Soundtrack music": "soundtrack",
        "Techno": "techno", "Hip hop music": "hiphop", "Jazz": "jazz", "Ambient music": "ambient", "Drum and bass": "dnb", "House music": "house"}


def main():
    force = "--force" in sys.argv
    fe = ASTFeatureExtractor.from_pretrained(MODEL); m = ASTForAudioClassification.from_pretrained(MODEL).eval()
    id2l = m.config.id2label; idx = {k: [i for i, l in id2l.items() if l == k][0] for k in WANT if k in id2l.values()}
    db = json.load(open(OUT, encoding="utf8")) if os.path.exists(OUT) and not force else {}
    for root, _, files in os.walk(LIB):
        for f in sorted(files):
            if not f.lower().endswith((".mp3", ".m4a", ".wav")): continue
            key = os.path.relpath(root, LIB) + "/" + f
            if key in db: continue
            y, sr = librosa.load(os.path.join(root, f), sr=16000, mono=True, duration=155)
            W = int(10.24 * sr); wins = []
            t = 0
            while t + W <= len(y) + sr:
                seg = y[t:t + W]
                inp = fe(seg, sampling_rate=16000, return_tensors="pt")
                with torch.no_grad(): p = torch.sigmoid(m(**inp).logits[0]).numpy()
                wins.append({"t": round(t / sr, 1), **{WANT[k]: round(float(p[i]), 3) for k, i in idx.items()}})
                t += int(5 * sr)
            mean = {k: round(float(np.mean([w[k] for w in wins])), 3) for k in wins[0] if k != "t"}
            db[key] = {"janelas": wins, "media": mean}
            top = sorted(((v, k) for k, v in mean.items() if k in ("happy", "funny", "sad", "tender", "exciting", "angry", "scary")), reverse=True)[:3]
            print(key, [(k, v) for v, k in top], flush=True)
            json.dump(db, open(OUT, "w", encoding="utf8"), ensure_ascii=False)


main()
