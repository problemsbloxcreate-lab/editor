"""Caminhos da skill nesta máquina — fonte ÚNICA (Estúdio Problems Local, 22/10/2026).

    import paths as P;  P.work_dir(), P.epidemic_dir(), P.cinecam("home"), P.cache_dir("clap"), P.cfg()
    python paths.py --show            # imprime tudo (use isto em vez de copiar caminhos do SKILL.md)
    python paths.py --set work_dir E:\\Pobrs

Configuração do USUÁRIO fica fora do repositório (o git pull nunca briga com ela):
    %APPDATA%\\EstudioProblems\\config.json      (migrado do antigo <skill>/config.json, que continua valendo como reserva)
Caches gerados em uso:   %LOCALAPPDATA%\\EstudioProblems\\cache\\<nome>
Padrões numa máquina nova: tudo dentro de %USERPROFILE%\\EstudioProblems; numa máquina antiga, as pastas que já existem (D:\\cinecam-*).
Nunca gravar caminho desta máquina dentro de arquivo versionado da skill.
"""
import json, os, sys

SCRIPTS = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(SCRIPTS)                                  # .../minecraft-video-editor
SKILLS = os.path.dirname(SKILL)                                   # pasta que tem as duas skills (~/.claude/skills ou <repo>/.claude/skills)
CINEMATIC = os.path.join(SKILLS, "minecraft-cinematic")
HOME = os.path.expanduser("~")
APPDATA = os.environ.get("APPDATA") or os.path.join(HOME, "AppData", "Roaming")
LOCALAPPDATA = os.environ.get("LOCALAPPDATA") or os.path.join(HOME, "AppData", "Local")
USER_DIR = os.path.join(APPDATA, "EstudioProblems")
USER_CFG = os.path.join(USER_DIR, "config.json")
LEGACY_CFG = os.path.join(SKILL, "config.json")
CACHE = os.path.join(LOCALAPPDATA, "EstudioProblems", "cache")

_cfg = None


def _load(p):
    try:
        return json.load(open(p, encoding="utf8"))
    except (OSError, ValueError):
        return {}


def cfg(reload=False):
    """config do usuário por cima da antiga da skill (a antiga só completa chaves que faltam)."""
    global _cfg
    if _cfg is None or reload:
        c = _load(LEGACY_CFG)
        c.update(_load(USER_CFG))
        if not os.path.exists(USER_CFG) and c:                     # migração: 1ª vez copia a antiga para fora do repo
            try:
                os.makedirs(USER_DIR, exist_ok=True)
                json.dump(c, open(USER_CFG, "w", encoding="utf8"), ensure_ascii=False, indent=1)
            except OSError:
                pass
        _cfg = c
    return _cfg


def set_key(k, v):
    c = _load(USER_CFG)
    c[k] = v
    os.makedirs(USER_DIR, exist_ok=True)
    json.dump(c, open(USER_CFG, "w", encoding="utf8"), ensure_ascii=False, indent=1)
    cfg(reload=True)


def get(k, default=None):
    v = os.environ.get("EP_" + k.upper()) or cfg().get(k)
    return v if v else default


def work_dir():
    return get("work_dir", os.path.join(HOME, "EstudioProblems"))


def jobs_dir():
    return os.path.join(work_dir(), "editor-jobs")


def epidemic_dir():
    return get("epidemic_dir", os.path.join(media_dir(), "epidemic"))


def media_dir():
    """mídia sincronizada pelo Estúdio (SFX, skins, promo...) quando vem do canal de mídia."""
    return get("media_dir", os.path.join(work_dir(), "midia"))


def skills_dir():
    return get("skills_dir", os.path.join(HOME, "Skills"))


def recordings_dirs():
    """pastas onde procurar o bruto pelo nome (ponte com o site)."""
    v = get("gravacoes_dirs") or []
    if isinstance(v, str):
        v = [v]
    vids = os.path.join(HOME, "Videos")
    return [d for d in v + [work_dir(), vids, os.path.join(HOME, "Desktop"), os.path.join(HOME, "Downloads")] if d]


_CINE_LEGACY = {"home": r"D:\cinecam-forge-1.20.1", "run": r"D:\cinecam-run", "out": r"D:\cinecam-out"}
_CINE_NAME = {"home": "cinecam-forge-1.20.1", "run": "cinecam-run", "out": "cinecam-out"}


def cinecam(which):
    """which = home | run | out | java_home | skins.  env CINECAM_* > config > pasta antiga existente > work_dir."""
    env = os.environ.get("CINECAM_" + which.upper())
    if env:
        return env
    v = cfg().get("cinecam_" + which)
    if v:
        return v
    if which == "skins":
        s = os.path.join(media_dir(), "skins")
        return s if os.path.isdir(os.path.join(s, "0.Turma")) else ""
    if which == "java_home":
        return ""
    old = _CINE_LEGACY[which]
    if os.path.isdir(old):
        return old
    return os.path.join(work_dir(), _CINE_NAME[which])


def cinecam_env():
    """variáveis para passar ao claude -p / subprocessos (substitui o setx do setup_cinecam)."""
    e = {}
    for w in ("home", "run", "out", "java_home", "skins"):
        v = cinecam(w)
        if v:
            e["CINECAM_" + w.upper()] = v
    return e


def cache_dir(name=""):
    d = os.path.join(CACHE, name) if name else CACHE
    os.makedirs(d, exist_ok=True)
    return d


def cached(name, packaged):
    """arquivo de cache gravável: lê o do usuário se existir, senão o padrão empacotado na skill (só leitura)."""
    p = os.path.join(cache_dir(), name)
    return p if os.path.exists(p) or not os.path.exists(packaged) else packaged


def writable(name):
    return os.path.join(cache_dir(), name)


def show():
    rows = [("skill", SKILL), ("skill cinematic", CINEMATIC), ("config do usuário", USER_CFG), ("cache", CACHE),
            ("work_dir", work_dir()), ("jobs", jobs_dir()), ("epidemic_dir", epidemic_dir()), ("media_dir", media_dir()),
            ("skills_dir", skills_dir())] + [("cinecam " + w, cinecam(w)) for w in ("home", "run", "out", "java_home", "skins")]
    for k, v in rows:
        print("%-20s %s%s" % (k, v, "" if not v or os.path.exists(v) else "   (não existe)"))


if __name__ == "__main__":
    a = sys.argv[1:]
    if "--set" in a:
        i = a.index("--set")
        set_key(a[i + 1], a[i + 2])
    show()
