"""Descritores das faixas da biblioteca Epidemic LOCAL (paths.epidemic_dir()).
Uso: python music_features_local.py <saida.json> <pasta1> [pasta2 ...]   (nomes de pasta de clima; reaproveita analyze() de music_features.py)
Várias instâncias em paralelo (uma por grupo de pastas) -> juntar os JSONs depois.
"""
import os, sys, json, importlib.util
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
BASE = paths.epidemic_dir()
spec = importlib.util.spec_from_file_location("mf", os.path.join(os.path.dirname(os.path.abspath(__file__)), "music_features.py"))
src = open(spec.origin, encoding="utf8").read().replace("\nmain()", "\n")
ns = {"__file__": spec.origin, "__name__": "mf"}
exec(compile(src, spec.origin, "exec"), ns)
out = sys.argv[1]
db = json.load(open(out, encoding="utf8")) if os.path.exists(out) else {}
for cat in sys.argv[2:]:
    d = os.path.join(BASE, cat)
    for f in sorted(os.listdir(d)):
        if not f.lower().endswith((".mp3", ".m4a", ".wav")): continue
        key = cat + "/" + f
        if key in db: continue
        try:
            r = ns["analyze"](os.path.join(d, f)); r["lufs"] = ns["lufs"](os.path.join(d, f)); r["cat"] = cat; r["arquivo"] = f
            db[key] = r
            print(key, r["dur"], r["tempo"], r["modo"], r["lufs"], flush=True)
        except Exception as e:
            print("ERRO", key, e, flush=True)
        json.dump(db, open(out, "w", encoding="utf8"), ensure_ascii=False, indent=1)
