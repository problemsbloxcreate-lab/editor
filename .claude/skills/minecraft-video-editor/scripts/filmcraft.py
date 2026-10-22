"""Ponte com o FilmCraft (editor não-linear open source, github.com/storytold/filmcraft) — alternativa ao Premiere.

- acha o FilmCraft instalado (MSI em Program Files, portátil em %LOCALAPPDATA%\\mve-tools) ou baixa o portátil oficial
  do release do GitHub (confere o SHA256SUMS do release);
- roda comandos pelo CLI headless (`filmcraft-cli --project p.fcproj run -`, uma linha JSON por comando);
- abre o projeto pronto na janela do FilmCraft.

uso:  python filmcraft.py where | ensure | open <proj.fcproj> | run <proj.fcproj> <script.jsonl> | inspect <proj.fcproj> [sequence|project]
      from filmcraft import ensure, run, inspect, open_app
"""
import hashlib, json, os, subprocess, sys, urllib.request, zipfile

VERSION = "0.9.0"
REPO = "storytold/filmcraft"
TOOLS = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "mve-tools")
PORTABLE = os.path.join(TOOLS, "filmcraft-%s-windows-x64-portable" % VERSION)
ZIPNAME = "filmcraft-%s-windows-x64-portable.zip" % VERSION
URL = "https://github.com/%s/releases/download/v%s/" % (REPO, VERSION)


def where():
    """(filmcraft.exe, filmcraft-cli.exe) ou (None, None)"""
    cands = [os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "FilmCraft"), PORTABLE]
    for d in cands:
        a, c = os.path.join(d, "filmcraft.exe"), os.path.join(d, "filmcraft-cli.exe")
        if os.path.exists(a) and os.path.exists(c): return a, c
    return None, None


def _get(url, dst):
    req = urllib.request.Request(url, headers={"User-Agent": "mve-filmcraft"})
    with urllib.request.urlopen(req, timeout=600) as r, open(dst, "wb") as f:
        while True:
            b = r.read(1 << 20)
            if not b: break
            f.write(b)


def ensure(log=print):
    """garante o FilmCraft: usa o instalado/portátil; senão baixa o portátil oficial (70 MB) e confere o SHA256"""
    app, cli = where()
    if app: return app, cli
    os.makedirs(os.path.join(TOOLS, "dl"), exist_ok=True)
    z = os.path.join(TOOLS, "dl", ZIPNAME); sums = os.path.join(TOOLS, "dl", "SHA256SUMS.txt")
    log("baixando FilmCraft %s (release oficial, ~70 MB)…" % VERSION)
    _get(URL + "SHA256SUMS.txt", sums); _get(URL + ZIPNAME, z)
    want = next((l.split()[0] for l in open(sums, encoding="utf8") if l.strip().endswith(ZIPNAME)), None)
    got = hashlib.sha256(open(z, "rb").read()).hexdigest()
    if not want or want.lower() != got.lower():
        os.remove(z); raise RuntimeError("SHA256 do FilmCraft não confere — download descartado")
    zipfile.ZipFile(z).extractall(TOOLS)
    app, cli = where()
    if not app: raise RuntimeError("FilmCraft extraído mas não encontrado em " + PORTABLE)
    log("FilmCraft pronto em " + os.path.dirname(app))
    return app, cli


def run(project, steps, save=True, new=False, keep_going=False):
    """roda comandos [{id, params}] no projeto; new=True cria o .fcproj. Devolve a lista de resultados (1 por linha)."""
    _, cli = ensure()
    args = [cli]
    args += ["--save-as", project] if new else (["--project", project] + (["--save"] if save else []))
    if keep_going: args.append("--keep-going")
    args += ["run", "-"]
    inp = "\n".join(json.dumps(s, ensure_ascii=False) for s in steps) + "\n"
    p = subprocess.run(args, input=inp.encode("utf8"), capture_output=True)
    out = []
    for l in p.stdout.decode("utf8", "replace").splitlines():
        try: out.append(json.loads(l))
        except ValueError: pass
    bad = [o for o in out if not o.get("ok", True)]
    if bad and not keep_going:
        raise RuntimeError("FilmCraft: %s falhou: %s" % (bad[0].get("id"), bad[0].get("error")))
    return out


def cli(*args):
    _, c = ensure()
    p = subprocess.run([c, *args], capture_output=True)
    return p.returncode, p.stdout.decode("utf8", "replace"), p.stderr.decode("utf8", "replace")


def inspect(project, what="sequence"):
    rc, out, err = cli("--project", project, "inspect", what)
    if rc: raise RuntimeError(err or out)
    return json.loads(out)


def open_app(project=None):
    app, _ = ensure()
    subprocess.Popen([app] + ([project] if project else []), close_fds=True)


if __name__ == "__main__":
    a = sys.argv[1:]
    cmd = a[0] if a else "where"
    if cmd == "where": print(where())
    elif cmd == "ensure": print(ensure())
    elif cmd == "open": open_app(a[1] if len(a) > 1 else None)
    elif cmd == "inspect": print(json.dumps(inspect(a[1], a[2] if len(a) > 2 else "sequence"), indent=1, ensure_ascii=False)[:20000])
    elif cmd == "run":
        steps = [json.loads(l) for l in open(a[2], encoding="utf8") if l.strip()]
        for r in run(a[1], steps): print(json.dumps(r, ensure_ascii=False)[:400])
