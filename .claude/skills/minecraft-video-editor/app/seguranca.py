"""Segurança do serviço local (Estúdio Problems Local, 22/10/2026). O server.py só faz algo para:
  1. a PÁGINA LOCAL (http://127.0.0.1:4790/): recebe um token aleatório desta instalação embutido no HTML
     (%APPDATA%\\EstudioProblems\\local_token). Outro site não consegue ler esse HTML (sem CORS para ele + Host conferido).
  2. o SITE DO ESTÚDIO (https://estudio.problemsraiz.workers.dev): manda um passe do porteiro (GET /passe-local, 2 min,
     host 127.0.0.1:<porta>, assinado ECDSA P-256) em POST /api/sessao e recebe uma sessão local de 12 h ligada ao e-mail.
Contra DNS rebinding: Host tem de ser 127.0.0.1/localhost na porta do serviço. Contra outros sites: Origin fora da lista -> 403.
Não existe senha, bypass nem "modo teste" (mesma regra do porteiro).
"""
import base64, hmac, json, os, secrets, threading, time, urllib.request

import paths as P

PORTEIRO = (P.get("porteiro_url") or "https://estudio.problemsraiz.workers.dev").rstrip("/")
TOKEN_FILE = os.path.join(P.USER_DIR, "local_token")
KEY_FILE = os.path.join(P.USER_DIR, "porteiro_chave.json")
SESSAO_H = 12 * 3600
_lock = threading.Lock()
_sessoes = {}                      # token -> {"email", "exp"}
_chave = {"k": None, "t": 0}


def origens(porta):
    o = {"http://127.0.0.1:%d" % porta, "http://localhost:%d" % porta, PORTEIRO}
    extra = P.get("origens_extra") or []
    return o | set(extra if isinstance(extra, list) else [extra])


def hosts(porta):
    return {"127.0.0.1:%d" % porta, "localhost:%d" % porta}


def token_local():
    try:
        t = open(TOKEN_FILE, encoding="ascii").read().strip()
        if len(t) >= 32:
            return t
    except OSError:
        pass
    os.makedirs(P.USER_DIR, exist_ok=True)
    t = secrets.token_urlsafe(32)
    open(TOKEN_FILE, "w", encoding="ascii").write(t)
    return t


def _b64u(s):
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def _chave_publica():
    with _lock:
        if _chave["k"] and time.time() - _chave["t"] < 3600:
            return _chave["k"]
        jwk = None
        try:
            with urllib.request.urlopen(urllib.request.Request(PORTEIRO + "/chave-publica", headers={"user-agent": "EstudioProblemsLocal"}), timeout=8) as r:
                jwk = json.loads(r.read())
            os.makedirs(P.USER_DIR, exist_ok=True)
            json.dump(jwk, open(KEY_FILE, "w", encoding="utf8"))
        except Exception:
            if os.path.exists(KEY_FILE):          # sem internet: última chave conhecida
                jwk = json.load(open(KEY_FILE, encoding="utf8"))
        if not jwk:
            raise RuntimeError("não consegui a chave pública do porteiro")
        from cryptography.hazmat.primitives.asymmetric import ec
        nums = ec.EllipticCurvePublicNumbers(int.from_bytes(_b64u(jwk["x"]), "big"), int.from_bytes(_b64u(jwk["y"]), "big"), ec.SECP256R1())
        _chave.update(k=nums.public_key(), t=time.time())
        return _chave["k"]


def conferir_passe(passe, host):
    """devolve o e-mail se o passe é do porteiro, vale para este host e não venceu; senão None."""
    try:
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import ec, utils
        dados, ass = passe.split(".")
        sig = _b64u(ass)
        if len(sig) != 64:
            return None
        der = utils.encode_dss_signature(int.from_bytes(sig[:32], "big"), int.from_bytes(sig[32:], "big"))
        _chave_publica().verify(der, dados.encode("ascii"), ec.ECDSA(hashes.SHA256()))
        p = json.loads(_b64u(dados))
        if p.get("e") and p.get("h") == host and float(p.get("x", 0)) > time.time():
            return p["e"]
    except Exception:
        return None
    return None


def nova_sessao(email):
    t = secrets.token_urlsafe(32)
    with _lock:
        now = time.time()
        for k in [k for k, v in _sessoes.items() if v["exp"] < now]:
            del _sessoes[k]
        _sessoes[t] = {"email": email, "exp": now + SESSAO_H}
    return t


def quem(headers):
    """'local' (página local), o e-mail (sessão do Estúdio) ou None."""
    tk = headers.get("x-ep-token")
    if tk and hmac.compare_digest(tk, token_local()):
        return "local"
    s = headers.get("x-ep-sessao")
    if s:
        with _lock:
            v = _sessoes.get(s)
        if v and v["exp"] > time.time():
            return v["email"]
    return None
