"""Índice CLAP (laion/clap-htsat-unfused) da biblioteca Epidemic local: embeddings de áudio (3 janelas de 10 s por faixa) p/ buscar música por CLIMA em texto
("tense suspenseful music", "funny sneaky comedic music"...). Eu não ouço; isto é a aproximação mais fiel de "ouvir" que tenho.
Uso: python clap_index.py <saida.npz> <pasta1> [pasta2 ...]      busca: python clap_query.py "prompt" [pasta ...]
"""
import os, sys, json, numpy as np, librosa, torch
from transformers import ClapModel, ClapProcessor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
BASE = paths.epidemic_dir()
out = sys.argv[1]
m = ClapModel.from_pretrained("laion/clap-htsat-unfused").eval(); pr = ClapProcessor.from_pretrained("laion/clap-htsat-unfused")
keys, embs = [], []
if os.path.exists(out):
    z = np.load(out, allow_pickle=True); keys, embs = list(z["keys"]), list(z["embs"])
done = set(keys)
for cat in sys.argv[2:]:
    for f in sorted(os.listdir(os.path.join(BASE, cat))):
        if not f.lower().endswith((".mp3", ".wav", ".m4a")): continue
        key = cat + "/" + f
        if key in done: continue
        try:
            dur = librosa.get_duration(path=os.path.join(BASE, cat, f))
            offs = [max(0, dur * q - 5) for q in (0.2, 0.5, 0.8)] if dur > 40 else [0]
            ys = [librosa.load(os.path.join(BASE, cat, f), sr=48000, offset=o, duration=10)[0] for o in offs]
            inp = pr(audio=ys, sampling_rate=48000, return_tensors="pt")
            with torch.no_grad(): e = m.get_audio_features(**inp).pooler_output
            e = torch.nn.functional.normalize(e, dim=-1).numpy()
            keys.append(key); embs.append(e)
            print(key, e.shape, flush=True)
            np.savez(out, keys=np.array(keys, dtype=object), embs=np.array(embs, dtype=object))
        except Exception as ex:
            print("ERRO", key, ex, flush=True)
