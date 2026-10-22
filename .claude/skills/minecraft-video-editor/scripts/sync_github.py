"""Sincroniza as skills com o GitHub (pedido do Matheus, 22/10/2026): problemsbloxcreate-lab/editor, pasta .claude/skills/.

SEMPRE que a skill minecraft-video-editor ou a minecraft-cinematic mudar, rodar no fim da tarefa:
    python sync_github.py -m "o que mudou"            # copia, commita e envia (git pull --rebase antes, regra do repo)
    python sync_github.py --dry-run                   # só mostra o que mudaria
    python sync_github.py -m "..." --liberar          # + libera esta versão para os PCs da equipe (tag local-vAAAA.MM.DD.N)
SÓ libere quando o Matheus aprovar: a equipe recebe a versão liberada sozinha (Estúdio Problems Local / app/atualizar.py).
O repositório é PÚBLICO e é do app "Editor Problems (vídeo longo)": vai SÓ código e documentação. Ficam de fora (EXCLUDE):
músicas Epidemic (licenciadas), SFX (inclui sons da Mojang e memes), vídeos de promo/tela final, overlays PNG (textura de UI do
Minecraft, WASTED do GTA), skins da turma, config.json da máquina, caches.  Nunca chaves/senhas/e-mails (o script recusa se achar).
Clone local: config.json -> "github_repo_dir" (padrão C:\\Users\\mathe\\Skills\\repos\\editor).
"""
import fnmatch, json, os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SK = os.path.dirname(HERE)
SKILLS = os.path.dirname(SK)
REPO_URL = "problemsbloxcreate-lab/editor"
sys.path.insert(0, HERE)
import paths as P
CFG = P.cfg()
REPO = os.environ.get("EDITOR_REPO") or CFG.get("github_repo_dir") or os.path.join(os.path.expanduser("~"), "Skills", "repos", "editor")

SOURCES = {
    "minecraft-video-editor": ["library/music/*", "library/sfx/*", "!library/sfx/index.json", "library/insercoes/*", "library/png/*",
                               "config.json"],
    "minecraft-cinematic": ["assets/skins/*", "scripts/cinecam/acts_v1_backup.py"],
}
ALWAYS_OUT = ["*/__pycache__/*", "__pycache__/*", "*.pyc", "*.rms_*.npy", "*_asr_*.json", ".DS_Store", "Thumbs.db"]
SECRET = re.compile(r"gsk_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,}|gh[opsu]_[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_-]{30,}|xox[bp]-[0-9A-Za-z-]{10,}"
                    r"|[A-Za-z0-9._%+-]+@(gmail|hotmail|outlook|yahoo|icloud)\.com")
MAX_FILE = 20 * 2 ** 20


def excluded(rel, pats):
    rel = rel.replace("\\", "/")
    if any(fnmatch.fnmatch(rel, p) for p in ALWAYS_OUT):
        return True
    keep = [p[1:] for p in pats if p.startswith("!")]
    if any(fnmatch.fnmatch(rel, p) for p in keep):
        return False
    return any(fnmatch.fnmatch(rel, p) for p in pats if not p.startswith("!"))


def git(*a, check=True, capture=False):
    r = subprocess.run(["git", "-C", REPO] + list(a), capture_output=True, text=True, encoding="utf8", errors="replace")
    if check and r.returncode:
        raise SystemExit("git %s falhou:\n%s" % (" ".join(a), r.stderr or r.stdout))
    return r.stdout if capture else r


def mirror(name, pats, dry):
    src, dst = os.path.join(SKILLS, name), os.path.join(REPO, ".claude", "skills", name)
    want = {}
    for dp, dns, fs in os.walk(src):
        for f in fs:
            p = os.path.join(dp, f)
            rel = os.path.relpath(p, src).replace("\\", "/")
            if excluded(rel, pats):
                continue
            if os.path.getsize(p) > MAX_FILE:
                print("  PULADO (> 20 MB):", name + "/" + rel)
                continue
            want[rel] = p
    problems = []
    for rel, p in want.items():
        if rel.endswith((".py", ".md", ".json", ".jsx", ".js", ".txt", ".html", ".bat", ".java", ".gradle", ".properties", ".toml")):
            try:
                txt = open(p, encoding="utf8", errors="ignore").read()
            except OSError:
                continue
            m = SECRET.search(txt)
            if m:
                problems.append("%s/%s: %s…" % (name, rel, m.group(0)[:12]))
    if problems:
        raise SystemExit("RECUSADO: parece haver chave/token/e-mail:\n  " + "\n  ".join(problems))
    changed = 0
    if not dry:
        os.makedirs(dst, exist_ok=True)
        for dp, dns, fs in os.walk(dst, topdown=False):            # remove o que saiu da skill (espelho)
            for f in fs:
                rel = os.path.relpath(os.path.join(dp, f), dst).replace("\\", "/")
                if rel not in want:
                    os.remove(os.path.join(dp, f)); changed += 1
            if dp != dst and not os.listdir(dp):
                os.rmdir(dp)
        for rel, p in want.items():
            q = os.path.join(dst, rel)
            if not os.path.exists(q) or open(q, "rb").read() != open(p, "rb").read():
                os.makedirs(os.path.dirname(q), exist_ok=True)
                shutil.copy2(p, q); changed += 1
    print("  %s: %d arquivos (%d alterados)" % (name, len(want), changed))
    return want


def main():
    a = sys.argv[1:]
    dry = "--dry-run" in a
    msg = a[a.index("-m") + 1] if "-m" in a else "Skills: atualização"
    if not os.path.isdir(os.path.join(REPO, ".git")):
        os.makedirs(os.path.dirname(REPO), exist_ok=True)
        subprocess.run(["gh", "repo", "clone", REPO_URL, REPO], check=True)
    if not dry:
        git("checkout", "main")
        git("pull", "--rebase", "--autostash")
    print("Repositório:", REPO)
    for name, pats in SOURCES.items():
        mirror(name, pats, dry)
    if not dry:                                                       # modelo de config sem caminhos desta máquina
        ex = os.path.join(REPO, ".claude", "skills", "minecraft-video-editor", "config.example.json")
        json.dump({"epidemic_dir": "<pasta da biblioteca Epidemic>", "work_dir": "<pasta de trabalho de mídia>",
                   "skills_dir": "<pasta de trabalho do Claude>", "github_repo_dir": "<clone deste repositório>"},
                  open(ex, "w", encoding="utf8"), ensure_ascii=False, indent=1)
    if dry:
        return
    git("add", "-A", ".claude/skills/minecraft-video-editor", ".claude/skills/minecraft-cinematic")
    st = git("status", "--porcelain", ".claude/skills/minecraft-video-editor", ".claude/skills/minecraft-cinematic", capture=True)
    ahead = git("rev-list", "--count", "origin/main..HEAD", capture=True).strip()
    if not st.strip() and ahead in ("", "0"):
        print("Nada mudou: o GitHub já está igual à skill.")
        if "--liberar" in a:
            liberar()
        return
    if st.strip():
        print(st.strip()[:3000])
        git("commit", "-m", msg + "\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>")
    else:
        print("Sem mudança nova; enviando %s commit(s) que estavam pendentes." % ahead)
    if "--no-push" in a:
        print("Commit feito (sem enviar).")
        return
    r = git("push", "origin", "main", check=False)
    if r.returncode:
        git("pull", "--rebase", "--autostash")
        r = git("push", "origin", "main", check=False)
    if r.returncode:
        raise SystemExit("push falhou (permissão? conta do gh?):\n" + (r.stderr or r.stdout))
    print("Enviado: https://github.com/%s/tree/main/.claude/skills" % REPO_URL)
    if "--liberar" in a:
        liberar()


def liberar():
    """marca o HEAD da main como versão LIBERADA para a equipe (o atualizador dos PCs só segue estas tags)."""
    import datetime, re
    git("fetch", "--tags", "--quiet", "origin", check=False)
    hoje = datetime.date.today().strftime("%Y.%m.%d")
    ns = [int(m.group(1)) for t in git("tag", "--list", "local-v%s.*" % hoje, capture=True).split() for m in [re.match(r"local-v[\d.]+\.(\d+)$", t)] if m]
    tag = "local-v%s.%d" % (hoje, max(ns, default=0) + 1)
    git("tag", "-a", tag, "-m", "Estúdio Problems Local: versão liberada para a equipe")
    r = git("push", "origin", tag, check=False)
    if r.returncode:
        raise SystemExit("push da tag falhou:\n" + (r.stderr or r.stdout))
    print("Liberada para a equipe:", tag, "(os PCs atualizam sozinhos em até 2 h, sem edição rodando)")


if __name__ == "__main__":
    main()
