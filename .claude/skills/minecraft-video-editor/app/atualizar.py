"""Atualizador do Estúdio Problems Local (22/10/2026): a skill da equipe segue a última versão LIBERADA pelo Matheus.

    python atualizar.py              # confere e atualiza agora (se nenhuma edição estiver rodando)
    python atualizar.py --status     # versão instalada / disponível
    python atualizar.py --voltar     # volta para a versão anterior (se a nova der problema)
O server.py chama verificar() ao iniciar e a cada 2 h. Só age quando a skill está num clone git do repositório
problemsbloxcreate-lab/editor (instalação da equipe); no PC do Matheus (skill em ~/.claude/skills, sem git) não faz nada.
Versões liberadas = tags "local-vAAAA.MM.DD.N" (sync_github.py --liberar). Nunca roda `git clean`: mídia, caches e configs
ficam fora do controle do git e não são tocados; arquivos versionados são sempre os da tag (checkout -f).
"""
import json, os, re, subprocess, sys, time

APP = os.path.dirname(os.path.abspath(__file__))
SK = os.path.dirname(APP)
sys.path.insert(0, os.path.join(SK, "scripts"))
import paths as P

REPO_SLUG = "problemsbloxcreate-lab/editor"
TAG = re.compile(r"^local-v(\d{4})\.(\d{2})\.(\d{2})\.(\d+)$")
ESTADO = os.path.join(P.USER_DIR, "atualizacao.json")
OCUPADO = ("decidindo destino", "editando", "aguardando limite")


def git(*a, check=False):
    return subprocess.run(["git", "-C", SK] + list(a), capture_output=True, text=True, encoding="utf8", errors="replace", check=check)


def instalado_por_git():
    r = git("rev-parse", "--show-toplevel")
    if r.returncode:
        return False
    url = git("remote", "get-url", "origin").stdout.strip().lower()
    return REPO_SLUG in url


def versao_atual():
    r = git("describe", "--tags", "--exact-match", "HEAD")
    if r.returncode == 0:
        return r.stdout.strip()
    r = git("rev-parse", "--short", "HEAD")
    return ("dev-" + r.stdout.strip()) if r.returncode == 0 else "dev"


def _key(t):
    m = TAG.match(t)
    return tuple(int(x) for x in m.groups()) if m else None


def ultima_liberada():
    tags = [t for t in git("tag", "--list", "local-v*").stdout.split() if _key(t)]
    return max(tags, key=_key) if tags else None


def edicao_rodando():
    jd = P.jobs_dir()
    if not os.path.isdir(jd):
        return False
    for d in os.listdir(jd):
        st = os.path.join(jd, d, "status.json")
        try:
            s = json.load(open(st, encoding="utf8"))
        except (OSError, ValueError):
            continue
        if s.get("estado") in OCUPADO and time.time() - os.path.getmtime(st) < 6 * 3600:
            return True
    return False


def _salvar(**kw):
    s = {}
    try:
        s = json.load(open(ESTADO, encoding="utf8"))
    except (OSError, ValueError):
        pass
    s.update(kw)
    os.makedirs(P.USER_DIR, exist_ok=True)
    json.dump(s, open(ESTADO, "w", encoding="utf8"), ensure_ascii=False, indent=1)
    return s


def _deps_mudaram(a, b):
    r = git("diff", "--name-only", a, b, "--", "distribuicao/requirements-lock.txt")   # relativo à skill (git -C SK)
    return bool(r.stdout.strip())


def _instalar_deps():
    lock = os.path.join(SK, "distribuicao", "requirements-lock.txt")
    uv = subprocess.run(["where", "uv"], capture_output=True, text=True).stdout.split("\n")[0].strip()
    cmd = [uv, "pip", "install", "--python", sys.executable, "-r", lock] if uv else [sys.executable, "-m", "pip", "install", "-r", lock]
    return subprocess.run(cmd, capture_output=True, text=True).returncode == 0


def ir_para(tag, log=print):
    antes = git("rev-parse", "HEAD").stdout.strip()
    r = git("-c", "advice.detachedHead=false", "checkout", "-f", tag)
    if r.returncode:
        log("atualizar: checkout %s falhou: %s" % (tag, r.stderr.strip()[-300:]))
        return False
    depois = git("rev-parse", "HEAD").stdout.strip()
    if antes != depois and _deps_mudaram(antes, depois):
        log("atualizar: bibliotecas Python mudaram, instalando…")
        if not _instalar_deps():
            log("atualizar: falhou instalar as bibliotecas; voltando")
            git("checkout", "-f", antes)
            return False
    _salvar(anterior=antes, atual=tag, quando=time.strftime("%Y-%m-%d %H:%M"))
    log("atualizar: agora em %s" % tag)
    return antes != depois


def verificar(log=print):
    """True se mudou de versão (o server.py reinicia sozinho)."""
    if not instalado_por_git():
        return False
    if edicao_rodando():
        log("atualizar: edição em andamento, deixo para depois")
        return False
    f = git("fetch", "--tags", "--force", "--quiet", "origin")
    if f.returncode:
        log("atualizar: sem conexão com o GitHub (%s)" % f.stderr.strip()[-160:])
        return False
    t = ultima_liberada()
    if t and t == _salvar().get("pulada"):            # o usuário voltou desta versão: espera a próxima liberação
        return False
    if not t or t == versao_atual():
        _salvar(verificado=time.strftime("%Y-%m-%d %H:%M"), disponivel=t)
        return False
    return ir_para(t, log)


def voltar(log=print):
    s = _salvar()
    if not s.get("anterior"):
        log("não há versão anterior registrada")
        return False
    _salvar(pulada=versao_atual())
    return ir_para(s["anterior"], log)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf8")
    a = sys.argv[1:]
    if "--status" in a:
        print("instalação da equipe (git):", instalado_por_git())
        print("versão:", versao_atual(), "| última liberada (local):", ultima_liberada())
    elif "--voltar" in a:
        voltar()
    else:
        print("mudou" if verificar() else "sem mudança")
