"""Canal de MÍDIA do Estúdio Problems Local (22/10/2026): SFX, músicas, skins, promo, extensão do Premiere chegam sozinhos.

    python midia_sync.py                  # sincroniza agora (o server.py faz isso ao iniciar e a cada 2 h, sem edição rodando)
    python midia_sync.py --status         # dispositivo pareado? versão da mídia local x remota
Fluxo:
  - PAREAMENTO: na 1ª vez que o site do Estúdio abre a sessão local (/api/sessao), o serviço troca o mesmo passe do porteiro por um
    token de dispositivo (POST {porteiro}/dispositivo). Fica em %APPDATA%\\EstudioProblems\\dispositivo.json; o ADM pode revogar.
  - DOWNLOAD: {porteiro}/midia/manifesto.json = {"versao", "arquivos": {caminho: {"tam", "sha256"}}}; baixa só o que mudou para
    <media_dir>/<caminho> (arquivo .parte -> confere sha256 -> troca atômica), apaga o que saiu e roda distribuicao/instalar_midia.py
    sobre <media_dir> (mesmo layout da pasta MIDIA_editor do export_midia.py).
  - PUBLICAÇÃO (só ADM): export_midia.py --publicar usa publicar() daqui.
Contrato do porteiro (rotas novas no repositório problemsbloxcreate-lab.github.io/porteiro):
  POST /dispositivo {passe, nome_pc} -> {id, token}
  GET  /midia/<caminho> (Authorization: Bearer <token>, aceita Range)    PUT /midia/<caminho> (ADM; corpo <= 95 MB)
  POST /midia/<caminho>?mpu=criar -> {uploadId};  PUT ?mpu=parte&uploadId=&n= -> {etag};  POST ?mpu=fim&uploadId= {partes:[{n,etag}]}
  DELETE /midia/<caminho> (ADM)
  POST /conta-em-uso {conta, pc, ativo}   GET /conta-em-uso?conta= -> {pcs:[{pc, desde}]}
"""
import hashlib, json, os, socket, subprocess, sys, time, urllib.parse, urllib.request

APP = os.path.dirname(os.path.abspath(__file__))
SK = os.path.dirname(APP)
sys.path.insert(0, os.path.join(SK, "scripts"))
import paths as P

PORTEIRO = (P.get("porteiro_url") or "https://estudio.problemsraiz.workers.dev").rstrip("/")
DISP = os.path.join(P.USER_DIR, "dispositivo.json")
LOCAL_MAN = "manifesto_local.json"
PARTE = 50 * 2 ** 20
LIMITE_PUT = 95 * 2 ** 20


# ---------- porteiro ----------
def token():
    try:
        return json.load(open(DISP, encoding="utf8")).get("token")
    except (OSError, ValueError):
        return None


def _req(metodo, caminho, corpo=None, headers=None, timeout=60, raw=False):
    h = {"user-agent": "EstudioProblemsLocal"}
    if token(): h["authorization"] = "Bearer " + token()
    h.update(headers or {})
    if isinstance(corpo, (dict, list)):
        corpo = json.dumps(corpo).encode("utf8"); h["content-type"] = "application/json"
    r = urllib.request.urlopen(urllib.request.Request(PORTEIRO + caminho, data=corpo, method=metodo, headers=h), timeout=timeout)
    return r if raw else json.loads(r.read() or b"{}")


def parear(passe):
    """troca o passe (2 min) por um token de dispositivo revogável. Sem efeito se já pareado."""
    if token():
        return True
    try:
        r = _req("POST", "/dispositivo", {"passe": passe, "nome_pc": socket.gethostname()})
    except Exception as e:
        print("pareamento falhou:", e, flush=True)
        return False
    os.makedirs(P.USER_DIR, exist_ok=True)
    json.dump({"id": r["id"], "token": r["token"], "quando": time.strftime("%Y-%m-%d %H:%M")}, open(DISP, "w", encoding="utf8"))
    return True


def _q(c):
    return "/midia/" + urllib.parse.quote(c.replace("\\", "/"))


# ---------- download ----------
def _sha(p, cache=None):
    st = os.stat(p)
    k = "%s|%d|%d" % (p, st.st_size, int(st.st_mtime))
    if cache is not None and k in cache:
        return cache[k]
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(8 << 20), b""):
            h.update(b)
    if cache is not None:
        cache[k] = h.hexdigest()
    return h.hexdigest()


def _baixar(c, info, dst):
    tmp = dst + ".parte"
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    feito = os.path.getsize(tmp) if os.path.exists(tmp) else 0
    if feito > info["tam"]:
        os.remove(tmp); feito = 0
    if feito < info["tam"]:
        r = _req("GET", _q(c), headers={"range": "bytes=%d-" % feito} if feito else {}, timeout=120, raw=True)
        modo = "ab" if feito and r.status == 206 else "wb"
        with open(tmp, modo) as f:
            for b in iter(lambda: r.read(4 << 20), b""):
                f.write(b)
    if _sha(tmp) != info["sha256"]:
        os.remove(tmp)
        raise IOError("sha256 não confere: " + c)
    os.replace(tmp, dst)


def sincronizar(log=print, instalar=True):
    if not token():
        log("mídia: PC ainda não pareado (abra o Editor no site do Estúdio uma vez)")
        return False
    raiz = P.media_dir()
    try:
        rem = _req("GET", "/midia/manifesto.json")
    except Exception as e:
        log("mídia: sem acesso ao canal (%s)" % e)
        return False
    lp = os.path.join(raiz, LOCAL_MAN)
    loc = json.load(open(lp, encoding="utf8")) if os.path.exists(lp) else {"arquivos": {}}
    if loc.get("versao") == rem.get("versao"):
        return False
    ra, la = rem.get("arquivos", {}), loc.get("arquivos", {})
    falta = [c for c, i in ra.items() if la.get(c, {}).get("sha256") != i["sha256"] or not os.path.exists(os.path.join(raiz, c))]
    total = sum(ra[c]["tam"] for c in falta)
    log("mídia: versão %s — %d arquivos para baixar (%.0f MB)" % (rem.get("versao"), len(falta), total / 2 ** 20))
    erros = 0
    for i, c in enumerate(falta, 1):
        try:
            _baixar(c, ra[c], os.path.join(raiz, c))
            la[c] = ra[c]
        except Exception as e:
            erros += 1; log("mídia: falhou %s (%s)" % (c, e))
        if i % 50 == 0:
            log("mídia: %d/%d" % (i, len(falta)))
    for c in [c for c in la if c not in ra]:                    # saiu do canal
        try: os.remove(os.path.join(raiz, c))
        except OSError: pass
        la.pop(c, None)
    json.dump({"versao": rem.get("versao") if not erros else loc.get("versao"), "arquivos": la},
              open(lp, "w", encoding="utf8"), ensure_ascii=False)
    if instalar:
        epi = [d for d in (os.listdir(os.path.join(raiz, "epidemic")) if os.path.isdir(os.path.join(raiz, "epidemic")) else [])]
        cmd = [sys.executable, "-X", "utf8", os.path.join(SK, "distribuicao", "instalar_midia.py"), "--origem", raiz, "--skills", P.SKILLS, "--sim", "--sem-checagem"]
        if epi: cmd += ["--epidemic", os.path.join(raiz, "epidemic", epi[0])]
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf8", errors="replace")
        log("mídia: " + (r.stdout or r.stderr).strip()[-400:])
    return not erros


# ---------- publicação (ADM) ----------
def manifesto(pasta, cache_p=None, ignorar=()):
    cache = json.load(open(cache_p, encoding="utf8")) if cache_p and os.path.exists(cache_p) else {}
    arq = {}
    for dp, dns, fs in os.walk(pasta):
        for f in fs:
            p = os.path.join(dp, f)
            c = os.path.relpath(p, pasta).replace("\\", "/")
            if c in ("MANIFESTO.json", LOCAL_MAN) or c.endswith(".parte") or c.startswith(tuple(ignorar)):
                continue
            arq[c] = {"tam": os.path.getsize(p), "sha256": _sha(p, cache)}
    if cache_p:
        json.dump(cache, open(cache_p, "w", encoding="utf8"))
    return arq


def _put(c, p, tam):
    if tam <= LIMITE_PUT:
        with open(p, "rb") as f:
            _req("PUT", _q(c), f.read(), {"content-type": "application/octet-stream"}, timeout=600)
        return
    up = _req("POST", _q(c) + "?mpu=criar")["uploadId"]
    partes = []
    with open(p, "rb") as f:
        for n, b in enumerate(iter(lambda: f.read(PARTE), b""), 1):
            e = _req("PUT", _q(c) + "?mpu=parte&uploadId=%s&n=%d" % (urllib.parse.quote(up), n), b, {"content-type": "application/octet-stream"}, timeout=600)
            partes.append({"n": n, "etag": e["etag"]})
    _req("POST", _q(c) + "?mpu=fim&uploadId=" + urllib.parse.quote(up), {"partes": partes})


def publicar(pasta, log=print, apagar=True, ignorar=()):
    """envia a pasta (layout MIDIA_editor) para o canal: só o que mudou; manifesto por último (quem baixa nunca vê meio-termo)."""
    if not token():
        raise SystemExit("este PC não está pareado com o Estúdio (abra o Editor no site uma vez)")
    loc = manifesto(pasta, P.writable("midia_sha_cache.json"), ignorar)
    try:
        rem = _req("GET", "/midia/manifesto.json").get("arquivos", {})
    except Exception:
        rem = {}
    novos = [c for c, i in loc.items() if rem.get(c, {}).get("sha256") != i["sha256"]]
    log("publicar: %d arquivos novos/alterados (%.0f MB), %d removidos" % (len(novos), sum(loc[c]["tam"] for c in novos) / 2 ** 20,
                                                                          len([c for c in rem if c not in loc])))
    for i, c in enumerate(novos, 1):
        _put(c, os.path.join(pasta, c), loc[c]["tam"])
        if i % 25 == 0: log("publicar: %d/%d" % (i, len(novos)))
    versao = time.strftime("%Y%m%d-%H%M%S")
    _req("PUT", "/midia/manifesto.json", json.dumps({"versao": versao, "arquivos": loc}, ensure_ascii=False).encode("utf8"),
         {"content-type": "application/json"})
    if apagar:
        for c in [c for c in rem if c not in loc]:
            try: _req("DELETE", _q(c))
            except Exception as e: log("publicar: não apaguei %s (%s)" % (c, e))
    log("publicar: mídia versão %s no ar" % versao)
    return versao


# ---------- conta Claude deste PC ----------
def conta_claude():
    import shutil
    exe = shutil.which("claude")
    if exe:
        try:
            r = subprocess.run([exe, "auth", "status"], capture_output=True, text=True, timeout=20, shell=exe.lower().endswith((".cmd", ".bat")))
            d = json.loads(r.stdout)
            return {"logado": bool(d.get("loggedIn")), "email": d.get("email"), "org": d.get("orgName"), "plano": d.get("subscriptionType")}
        except Exception:
            pass
    try:
        o = json.load(open(os.path.join(P.HOME, ".claude.json"), encoding="utf8")).get("oauthAccount") or {}
        return {"logado": bool(o.get("emailAddress")), "email": o.get("emailAddress"), "org": o.get("organizationName"), "plano": None}
    except (OSError, ValueError):
        return {"logado": False, "email": None, "org": None, "plano": None}


def conta_em_uso(conta, ativo):
    """avisa o porteiro (KV, 6 h) que esta conta Claude está editando neste PC; devolve os OUTROS PCs usando a mesma conta."""
    if not token() or not conta:
        return []
    pc = socket.gethostname()
    try:
        _req("POST", "/conta-em-uso", {"conta": conta, "pc": pc, "ativo": bool(ativo)}, timeout=10)
        r = _req("GET", "/conta-em-uso?conta=" + urllib.parse.quote(conta), timeout=10)
        return [x for x in r.get("pcs", []) if x.get("pc") != pc]
    except Exception:
        return []


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf8")
    if "--status" in sys.argv[1:]:
        lp = os.path.join(P.media_dir(), LOCAL_MAN)
        print("pareado:", bool(token()), "| mídia local:", json.load(open(lp, encoding="utf8")).get("versao") if os.path.exists(lp) else None)
        print("conta Claude:", conta_claude())
    else:
        print("mudou" if sincronizar() else "sem mudança")
