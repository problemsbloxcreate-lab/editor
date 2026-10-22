"""Busca por clima: python clap_query.py "prompt1" "prompt2" ... [--top N] [--exclude substr,substr] [--cats PASTA,PASTA]
Usa os índices clap_*.npz em --dir (padrão: library/clap da skill). Pontua cada faixa = max das 3 janelas da similaridade(áudio, texto) − média dos prompts-ruído."""
import sys, glob, json, numpy as np, os
args = sys.argv[1:]
def opt(n, d=None):
    if n in args:
        i = args.index(n); v = args[i + 1]; del args[i:i + 2]; return v
    return d
top = int(opt("--top", 6)); excl = [x for x in (opt("--exclude", "") or "").split(",") if x]; cats = [x for x in (opt("--cats", "") or "").split(",") if x]
d = opt("--dir", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "library", "clap")); neg = opt("--neg", "")
keys, embs = [], []
for f in glob.glob(os.path.join(d, "clap_*.npz")):
    z = np.load(f, allow_pickle=True); keys += list(z["keys"]); embs += list(z["embs"])
# 21/10: vetores de texto em cache (library/clap/text_cache.json): prompt repetido não carrega torch + modelo (~1,2 GB, 10-20 s);
# os que faltam são calculados de uma vez com o modelo carregado 1 vez (mesmo cálculo de antes, prompt a prompt).
CACHE = os.path.join(d, "text_cache.json")
try: cache = json.load(open(CACHE, encoding="utf8"))
except (OSError, ValueError): cache = {}
miss = [p for p in args if p not in cache]
if miss:
    import torch
    from transformers import ClapModel, ClapProcessor
    m = ClapModel.from_pretrained("laion/clap-htsat-unfused").eval(); pr = ClapProcessor.from_pretrained("laion/clap-htsat-unfused")
    def tf(txts):
        with torch.no_grad(): t = m.get_text_features(**pr(text=txts, return_tensors="pt", padding=True))
        t = getattr(t, "pooler_output", t)
        return torch.nn.functional.normalize(t, dim=-1).numpy()
    for p in miss: cache[p] = [round(float(x), 6) for x in tf([p])[0]]
    try: json.dump(cache, open(CACHE, "w", encoding="utf8"))
    except OSError: pass
for p in args:
    tv = np.array(cache[p], dtype=np.float32)
    sc = []
    for k, e in zip(keys, embs):
        if cats and k.split("/")[0] not in cats: continue
        if any(x in k for x in excl): continue
        s = e @ tv
        sc.append((float(s.max() * 0.5 + s.mean() * 0.5), k))
    sc.sort(reverse=True)
    print("## " + p)
    for s, k in sc[:top]: print("   %.3f  %s" % (s, k))
