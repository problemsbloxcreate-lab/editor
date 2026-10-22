"""Editor Problems — interface local (http://localhost:4790) para soltar um bruto e receber a edição pronta
no Premiere (via MCP Bridge) ou no FilmCraft. Só Python padrão (sem instalar nada).

uso: python server.py [--porta 4790] [--sem-navegador]
"""
import json, os, re, shutil, subprocess, sys, threading, time, urllib.parse, webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

APP = os.path.dirname(os.path.abspath(__file__))
SK = os.path.dirname(APP)
sys.path.insert(0, os.path.join(SK, "scripts"))
import paths as P
CFG = P.cfg()
WORK = P.jobs_dir()
ENTRADA = os.path.join(WORK, "entrada")
VID_EXT = (".mp4", ".mov", ".mkv", ".avi", ".m4v", ".webm")
import seguranca as SEG
PORTA = 4790
JID = re.compile(r"^[A-Za-z0-9_\-]{1,120}$")


def _jid(path):
    j = path.split("/")[3]
    if not JID.match(j) or not os.path.isdir(os.path.join(WORK, j)):
        raise ValueError("job inválido")
    return j
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


def localizar(nome, tamanho=None, max_files=400000):
    """o site só sabe nome + tamanho do bruto: procura nas pastas de gravação desta máquina (paths.recordings_dirs)."""
    nome = os.path.basename(nome or "")
    if not nome: raise ValueError("sem nome")
    achados, n = [], 0
    for raiz in P.recordings_dirs():
        if not os.path.isdir(raiz): continue
        for dp, dns, fs in os.walk(raiz):
            dns[:] = [d for d in dns if not d.startswith((".", "$")) and d not in ("editor-jobs", "node_modules", "cinecam-run")]
            n += len(fs)
            if nome in fs:
                p = os.path.join(dp, nome)
                if tamanho is None or os.path.getsize(p) == int(tamanho): achados.append(p)
            if n > max_files: break
    return sorted(set(achados))


def novo_job(b, quem="local"):
    v = (b.get("video") or "").strip().strip('"')
    if not os.path.isfile(v): raise ValueError("arquivo não encontrado: " + v)
    if not v.lower().endswith(VID_EXT): raise ValueError("não parece um vídeo: " + v)
    base = "".join(ch if ch.isalnum() else "_" for ch in os.path.splitext(os.path.basename(v))[0])[:40]
    jid = time.strftime("%Y%m%d_%H%M%S_") + base
    d = os.path.join(WORK, jid); os.makedirs(d)
    cfg = {"video": os.path.abspath(v), "destino": b.get("destino", "auto"), "notas": (b.get("notas") or "")[:4000],
           "nome": (b.get("nome") or "").strip() or None, "abrir": bool(b.get("abrir", True)), "modelo": b.get("modelo") or None,
           "cinematicas": bool(b.get("cinematicas", True)), "pedido_por": quem, "origem": b.get("origem") or "local"}
    if b.get("plano_web"):                    # plano feito no editor web: o runner converte (plano_web.py) e só monta
        pw = dict(b["plano_web"], bruto=cfg["video"])
        json.dump(pw, open(os.path.join(d, "pedido_web.json"), "w", encoding="utf8"), ensure_ascii=False)
        cfg["modo"] = "montar"; cfg["cinematicas"] = bool(b.get("cinematicas", False))
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

    def cors(self):
        o = self.headers.get("origin")
        if o and o in SEG.origens(PORTA):
            self.send_header("access-control-allow-origin", o); self.send_header("vary", "Origin")
            self.send_header("access-control-allow-headers", "content-type, x-ep-token, x-ep-sessao")
            self.send_header("access-control-allow-methods", "GET, POST, OPTIONS")
            self.send_header("access-control-allow-private-network", "true")      # Chrome/Edge: site público -> rede local
            self.send_header("access-control-max-age", "600")

    def send(self, code, body, ctype="application/json; charset=utf-8"):
        b = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode("utf8")
        self.send_response(code); self.send_header("content-type", ctype); self.send_header("content-length", str(len(b)))
        self.send_header("cache-control", "no-store"); self.send_header("x-content-type-options", "nosniff"); self.cors()
        self.end_headers(); self.wfile.write(b)

    def guard(self, need_auth=True):
        """Host (anti DNS rebinding), Origin (só a página local e o Estúdio) e autenticação. Devolve quem pediu ou None (já respondeu)."""
        if (self.headers.get("host") or "").lower() not in SEG.hosts(PORTA):
            self.send(421, {"erro": "host recusado"}); return None
        o = self.headers.get("origin")
        if o and o not in SEG.origens(PORTA):
            self.send(403, {"erro": "origem recusada"}); return None
        if not need_auth: return "-"
        w = SEG.quem(self.headers)
        if not w: self.send(401, {"erro": "sem autorização: abra pelo Estúdio Problems ou pela página local"}); return None
        return w

    def body(self):
        if "json" not in (self.headers.get("content-type") or ""): raise ValueError("content-type precisa ser application/json")
        n = int(self.headers.get("content-length") or 0)
        if n > 2 << 20: raise ValueError("pedido grande demais")
        return json.loads(self.rfile.read(n) or b"{}")

    def do_OPTIONS(self):
        if not self.guard(need_auth=False): return
        self.send_response(204); self.cors(); self.send_header("content-length", "0"); self.end_headers()

    def do_GET(self):
        u = urllib.parse.urlparse(self.path); q = urllib.parse.parse_qs(u.query)
        if u.path in ("/", "/index.html"):
            if not self.guard(need_auth=False): return
            html = open(os.path.join(APP, "index.html"), encoding="utf8").read().replace("__EP_TOKEN__", SEG.token_local())
            return self.send(200, html.encode("utf8"), "text/html; charset=utf-8")
        if u.path == "/api/ping":                    # o site do Estúdio detecta o serviço (não revela nada)
            if not self.guard(need_auth=False): return
            return self.send(200, {"servico": "estudio-problems-local", "versao": versao()})
        if not self.guard(): return
        try:
            if u.path == "/api/env": return self.send(200, env("force" in q))
            if u.path == "/api/estado": return self.send(200, estado())
            if u.path == "/api/jobs": return self.send(200, jobs())
            if u.path.startswith("/api/job/"):
                jid = _jid(u.path)
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
        if u.path == "/api/sessao":                  # passe do porteiro -> sessão local de 12 h
            if not self.guard(need_auth=False): return
            try: ps = self.body().get("passe") or ""
            except ValueError as e: return self.send(400, {"erro": str(e)})
            email = SEG.conferir_passe(ps, "127.0.0.1:%d" % PORTA)
            if not email: return self.send(401, {"erro": "passe inválido ou vencido"})
            import midia_sync                        # 1ª vez: o mesmo passe pareia este PC com o canal de mídia (token revogável)
            threading.Thread(target=midia_sync.parear, args=(ps,), daemon=True).start()
            return self.send(200, {"sessao": SEG.nova_sessao(email), "email": email, "horas": SEG.SESSAO_H // 3600})
        quem = self.guard()
        if not quem: return
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
            if u.path == "/api/job": return self.send(200, {"id": novo_job(self.body(), quem)})
            if u.path == "/api/localizar":
                b = self.body(); return self.send(200, {"arquivos": localizar(b.get("nome"), b.get("tamanho"))})
            if u.path.startswith("/api/job/") and u.path.endswith("/parar"): parar(_jid(u.path)); return self.send(200, {"ok": True})
            if u.path.startswith("/api/job/") and u.path.endswith("/abrir"): return self.send(200, {"abriu": abrir(_jid(u.path))})
            if u.path == "/api/filmcraft/instalar":
                import filmcraft as fc; app, cli = fc.ensure(); _env_cache["t"] = 0; return self.send(200, {"exe": app})
            return self.send(404, {"erro": "não existe"})
        except Exception as e:
            return self.send(400, {"erro": str(e)})


def versao():
    import atualizar
    return atualizar.versao_atual() if atualizar.instalado_por_git() else "dev"


def estado():
    """painel: versão, conta Claude deste PC (e outros PCs editando com ela agora), pareamento e mídia."""
    import atualizar, midia_sync
    c = midia_sync.conta_claude()
    lp = os.path.join(P.media_dir(), midia_sync.LOCAL_MAN)
    mid = json.load(open(lp, encoding="utf8")).get("versao") if os.path.exists(lp) else None
    st = {}
    try: st = json.load(open(atualizar.ESTADO, encoding="utf8"))
    except (OSError, ValueError): pass
    return {"versao": versao(), "equipe": atualizar.instalado_por_git(), "atualizacao": st, "conta": c,
            "outros_pcs": midia_sync.conta_em_uso(c.get("email"), False) if c.get("email") else [],
            "pareado": bool(midia_sync.token()), "midia": mid, "editando": atualizar.edicao_rodando()}


def vigiar_atualizacoes(srv):
    """instalação da equipe: segue a última versão liberada; ao mudar, encerra com código 3 e o lançador reabre com o código novo."""
    import atualizar
    while True:
        try:
            if atualizar.verificar(log=lambda m: print(m, flush=True)):
                print("versão nova instalada; reiniciando o serviço", flush=True)
                srv.shutdown(); os._exit(3)
            if atualizar.instalado_por_git() and not atualizar.edicao_rodando():     # PC da equipe: mídia nova do canal
                import midia_sync
                midia_sync.sincronizar(log=lambda m: print(m, flush=True))
        except Exception as e:
            print("atualizar:", e, flush=True)
        time.sleep(2 * 3600)


def main():
    global PORTA
    a = sys.argv[1:]
    porta = PORTA = int(a[a.index("--porta") + 1]) if "--porta" in a else int(P.get("porta") or 4790)
    os.makedirs(WORK, exist_ok=True)
    srv = ThreadingHTTPServer(("127.0.0.1", porta), H)
    url = "http://127.0.0.1:%d/" % porta
    SEG.token_local()
    print("Editor Problems em", url, "| jobs em", WORK)
    if "--sem-navegador" not in a: threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    if "--sem-atualizar" not in a:
        threading.Thread(target=vigiar_atualizacoes, args=(srv,), daemon=True).start()
    srv.serve_forever()


if __name__ == "__main__":
    main()
