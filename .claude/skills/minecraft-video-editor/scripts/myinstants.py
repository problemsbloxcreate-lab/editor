"""Busca e baixa SFX do myinstants.com para a biblioteca da skill.
Uso: python myinstants.py "vine boom" [--n 3] [--tag impacto]
Salva em ../library/sfx/<slug>.mp3 e registra em ../library/sfx/index.json
"""
import argparse, json, os, re, sys, urllib.parse, urllib.request
H = {"User-Agent": "Mozilla/5.0"}
LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "library", "sfx")

def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=30).read()

def search(q):
    html = get("https://www.myinstants.com/en/search/?name=" + urllib.parse.quote_plus(q)).decode("utf8", "ignore")
    seen, out = set(), []
    for m in re.finditer(r"/media/sounds/[^'\"]+?\.mp3", html):
        p = m.group(0)
        if p not in seen:
            seen.add(p); out.append(p)
    return out

def main():
    a = argparse.ArgumentParser(); a.add_argument("query"); a.add_argument("--n", type=int, default=1); a.add_argument("--tag", default="")
    a = a.parse_args()
    os.makedirs(LIB, exist_ok=True)
    idx_path = os.path.join(LIB, "index.json")
    idx = json.load(open(idx_path, encoding="utf8")) if os.path.exists(idx_path) else {}
    for p in search(a.query)[: a.n]:
        name = os.path.basename(p)
        dest = os.path.join(LIB, name)
        if not os.path.exists(dest):
            open(dest, "wb").write(get("https://www.myinstants.com" + p))
        idx[name] = {"query": a.query, "tag": a.tag, "source": "myinstants.com" + p}
        print("ok", name)
    json.dump(idx, open(idx_path, "w", encoding="utf8"), indent=1, ensure_ascii=False)

main()
