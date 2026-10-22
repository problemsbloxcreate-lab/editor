"""Editor Problems — interface local (http://localhost:4790) para soltar um bruto e receber a edição pronta
no Premiere (via MCP Bridge) ou no FilmCraft. Só Python padrão (sem instalar nada).

uso: python server.py [--porta 4790] [--sem-navegador]
"""
import json, os, shutil, subprocess, sys, threading, time, urllib.parse, webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

APP = os.path.dirname(os.path.abspath(__file__))
SK = os.path.dirname(APP)
sys.path.insert(0, os.path.join(SK, "scripts"))
CFG = json.load(open(os.path.join(SK, "config.json"), encoding="utf8")) if os.path.exists(os.path.join(SK, "config.json")) else {}
WORK = os.path.join(CFG.get("work_dir") or os.path.join(os.path.expanduser("~"), "Pobrs"), "editor-jobs")
ENTRADA = os.path.join(WORK, "entrada")
VID_EXT = (".mp4", ".mov", ".mkv", ".avi", ".m4v", ".webm")
_env_cache = {"t": 0, "v": None}


def env(force=False):
    import destino as de
    if force or time.time() - _env_cache["t"] > 20:
        _env_cache["v"] = de.ambiente(); _env_cache["t"] = time.time()
    e = dict(_env_cache["v"]); e["auto"] = de.decidir("auto", e)
    return e


def jobs():
    out = []
    if not os.path.isdir(WORK): return out
    for d in sorted(os.listdir(WORK), reverse=True):
        p = os.path.join(WORK, d)
        if d == "entrada" or not os.path.exists(os.path.join(p, "job.json")): continue
        st = json.load(open(os.path.join(p, "status.json"), encoding="utf8")) if os.path.exists(os.path.join(p, "status.json")) else {}
        jb = json.load(open(os.path.join(p, "job.json"), encoding="utf8"))
        out.append({"id": d, "video": os.path.basename(jb["video"]), "destino_pedido": jb.get("destino"), **st})
    return out[:30]


def eventos(jid, desde=0):
    p = os.path.join(WORK, jid, "eventos.jsonl")
    if not os.path.exists(p): return []
    lines = open(p, encoding="utf8").read().splitlines()
    return [json.loads(l) for l in lines[desde:] if l.strip()]


def novo_job(b):
    v = (b.get("video") or "").strip().strip('"')
    if not os.path.isfile(v): raise ValueError("arquivo não encontrado: " + v)
    if not v.lower().endswith(VID_EXT): raise ValueError("não parece um vídeo: " + v)
    base = "".join(ch if ch.isalnum() else "_" for ch in os.path.splitext(os.path.basename(v))[0])[:40]
    jid = time.strftime("%Y%m%d_%H%M%S_") + base
    d = os.path.join(WORK, jid); os.makedirs(d)
    cfg = {"video": os.path.abspath(v), "destino": b.get("destino", "auto"), "notas": (b.get("notas") or "")[:4000],
           "nome": (b.get("nome") or "").strip() or None, "abrir": bool(b.get("abrir", True)), "modelo": b.get("modelo") or None,
           "cinematicas": bool(b.get("cinematicas", True))}
    json.dump(cfg, open(os.path.join(d, "job.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
    flags = (subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS) if os.name == "nt" else 0
    subprocess.Popen([sys.executable, "-X", "utf8", os.path.join(APP, "runner.py"), d], cwd=d, creationflags=flags,
                     stdout=open(os.path.join(d, "runner.log"), "w"), stderr=subprocess.STDOUT, close_fds=True)
    return jid


def parar(jid):
    st = os.path.join(WORK, jid, "status.json")
    s = json.load(open(st, encoding="utf8")) if os.path.exists(st) else {}
    for k in ("claude_pid", "pid"):
        if s.get(k): subprocess.run(["taskkill", "/F", "/T", "/PID", str(s[k])], capture_output=True)
    s.update(estado="parado"); json.dump(s, open(st, "w", encoding="utf8"), ensure_ascii=False)


def abrir(jid):
    s = json.load(open(os.path.join(WORK, jid, "status.json"), encoding="utf8"))
    r = s.get("resultado")
    if not r: raise ValueError("este job ainda não tem resultado")
    if r.endswith(".fcproj"):
        import filmcraft as fc; fc.open_app(r)
    else:
        os.startfile(r)                 # .prproj abre no Premiere
    return r


class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def send(self, code, body, ctype="application/json; charset=utf-8"):
        b = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode("utf8")
        self.send_response(code); self.send_header("content-type", ctype); self.send_header("content-length", str(len(b)))
        self.send_header("cache-control", "no-store"); self.end_headers(); self.wfile.write(b)

    def body(self):
        n = int(self.headers.get("content-length") or 0)
        return json.loads(self.rfile.read(n) or b"{}")

    def do_GET(self):
        u = urllib.parse.urlparse(self.path); q = urllib.parse.parse_qs(u.query)
        try:
            if u.path in ("/", "/index.html"):
                return self.send(200, open(os.path.join(APP, "index.html"), "rb").read(), "text/html; charset=utf-8")
            if u.path == "/api/env": return self.send(200, env("force" in q))
            if u.path == "/api/jobs": return self.send(200, jobs())
            if u.path.startswith("/api/job/"):
                jid = u.path.split("/")[3]
                st = os.path.join(WORK, jid, "status.json")
                s = json.load(open(st, encoding="utf8")) if os.path.exists(st) else {}
                resumo = os.path.join(WORK, jid, "RESUMO.md")
                return self.send(200, {"status": s, "eventos": eventos(jid, int(q.get("desde", ["0"])[0])),
                                       "resumo": open(resumo, encoding="utf8").read() if os.path.exists(resumo) else None})
            return self.send(404, {"erro": "não existe"})
        except Exception as e:
            return self.send(500, {"erro": str(e)})

    def do_POST(self):
        u = urllib.parse.urlparse(self.path); q = urllib.parse.parse_qs(u.query)
        try:
            if u.path == "/api/upload":            # o navegador manda o arquivo arrastado (cópia em editor-jobs/entrada)
                nome = os.path.basename(q.get("nome", ["video.mp4"])[0]); os.makedirs(ENTRADA, exist_ok=True)
                dst = os.path.join(ENTRADA, nome); n = int(self.headers.get("content-length") or 0)
                with open(dst, "wb") as f:
                    left = n
                    while left > 0:
                        b = self.rfile.read(min(left, 8 << 20))
                        if not b: break
                        f.write(b); left -= len(b)
                return self.send(200, {"video": dst, "bytes": n})
            if u.path == "/api/job": return self.send(200, {"id": novo_job(self.body())})
            if u.path.startswith("/api/job/") and u.path.endswith("/parar"): parar(u.path.split("/")[3]); return self.send(200, {"ok": True})
            if u.path.startswith("/api/job/") and u.path.endswith("/abrir"): return self.send(200, {"abriu": abrir(u.path.split("/")[3])})
            if u.path == "/api/filmcraft/instalar":
                import filmcraft as fc; app, cli = fc.ensure(); _env_cache["t"] = 0; return self.send(200, {"exe": app})
            return self.send(404, {"erro": "não existe"})
        except Exception as e:
            return self.send(400, {"erro": str(e)})


def main():
    a = sys.argv[1:]
    porta = int(a[a.index("--porta") + 1]) if "--porta" in a else 4790
    os.makedirs(WORK, exist_ok=True)
    srv = ThreadingHTTPServer(("127.0.0.1", porta), H)
    url = "http://localhost:%d/" % porta
    print("Editor Problems em", url, "| jobs em", WORK)
    if "--sem-navegador" not in a: threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    srv.serve_forever()


if __name__ == "__main__":
    main()
