"""Instala a pasta de MÍDIA do editor (gerada por export_midia.py) nesta máquina.  Só Python padrão.

    python instalar_midia.py [--skills C:\\Users\\voce\\.claude\\skills] [--epidemic "D:\\Musicas\\Epidemic 2K23 (Pasta de músicas)"]

Copia só o que falta ou mudou (pode rodar de novo com uma pasta mais nova):
  skills/*          -> <skills>  (library do editor, skins do cinematic)
  epidemic/<pasta>  -> --epidemic (padrão: Documentos\\<mesmo nome>) e grava epidemic_dir no config.json do editor
  modelos/huggingface/hub -> %HF_HOME%\\hub ou ~/.cache/huggingface/hub  (Whisper + CLAP: nada para baixar)
  ferramentas/filmcraft-* -> %LOCALAPPDATA%\\mve-tools\\
  premiere/MCPBridgeCEP   -> %APPDATA%\\Adobe\\CEP\\extensions\\ (+ PlayerDebugMode=1 nas versões CSXS 9-14)
  premiere/*.prfpset      -> Documents\\Adobe\\Premiere Pro\\<versão>\\Profile-*\\ (se o Premiere já tiver sido aberto)
"""
import glob, json, os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
HOME = os.path.expanduser("~")
A = sys.argv[1:]
opt = lambda n, d: A[A.index(n) + 1] if n in A else d


def same(a, b):
    try:
        sa, sb = os.stat(a), os.stat(b)
        return sa.st_size == sb.st_size and int(sa.st_mtime) == int(sb.st_mtime)
    except OSError:
        return False


def put(src, dst):
    n = 0
    if not os.path.exists(src):
        return 0
    for dp, _, fs in os.walk(src):
        for f in fs:
            p = os.path.join(dp, f)
            q = os.path.join(dst, os.path.relpath(p, src))
            if not same(p, q):
                os.makedirs(os.path.dirname(q), exist_ok=True)
                shutil.copy2(p, q); n += 1
    return n


skills = os.path.abspath(opt("--skills", os.path.join(HOME, ".claude", "skills")))
print("== Mídia do editor ->", skills)
if not os.path.isdir(os.path.join(skills, "minecraft-video-editor")):
    print("ATENÇÃO: não achei a skill em %s. Instale o código primeiro (GitHub) ou passe --skills." % skills)
for name in ("minecraft-video-editor", "minecraft-cinematic"):
    print("  %-26s %5d arquivos" % (name, put(os.path.join(HERE, "skills", name), os.path.join(skills, name))))

epi_src = glob.glob(os.path.join(HERE, "epidemic", "*"))
if epi_src:
    epi = os.path.abspath(opt("--epidemic", os.path.join(HOME, "Documents", os.path.basename(epi_src[0]))))
    print("  Epidemic -> %s: %d arquivos" % (epi, put(epi_src[0], epi)))
    cfgp = os.path.join(skills, "minecraft-video-editor", "config.json")
    cfg = json.load(open(cfgp, encoding="utf8")) if os.path.exists(cfgp) else {}
    cfg["epidemic_dir"] = epi
    if os.path.isdir(os.path.dirname(cfgp)):
        json.dump(cfg, open(cfgp, "w", encoding="utf8"), ensure_ascii=False, indent=1)
        print("  config.json: epidemic_dir =", epi)

hub = os.path.join(os.environ.get("HF_HOME", os.path.join(HOME, ".cache", "huggingface")), "hub")
print("  modelos (Whisper + CLAP) -> %s: %d arquivos" % (hub, put(os.path.join(HERE, "modelos", "huggingface", "hub"), hub)))

tools = os.path.join(os.environ.get("LOCALAPPDATA", os.path.join(HOME, "AppData", "Local")), "mve-tools")
for d in glob.glob(os.path.join(HERE, "ferramentas", "*")):
    print("  %s -> %s: %d arquivos" % (os.path.basename(d), tools, put(d, os.path.join(tools, os.path.basename(d)))))

cep = os.path.join(HERE, "premiere", "MCPBridgeCEP")
if os.path.isdir(cep):
    dst = os.path.join(os.environ.get("APPDATA", ""), "Adobe", "CEP", "extensions", "MCPBridgeCEP")
    print("  extensão do Premiere (MCP Bridge): %d arquivos" % put(cep, dst))
    for v in range(9, 15):
        subprocess.run(["reg", "add", r"HKCU\Software\Adobe\CSXS.%d" % v, "/v", "PlayerDebugMode", "/t", "REG_SZ", "/d", "1", "/f"],
                       capture_output=True)
prf = os.path.join(HERE, "premiere", "Effect Presets and Custom Items.prfpset")
if os.path.exists(prf):
    profs = glob.glob(os.path.join(HOME, "Documents", "Adobe", "Premiere Pro", "*", "Profile-*"))
    if profs:
        for p in profs:
            shutil.copy2(prf, p)
        print("  presets BERSERKER copiados para %d perfil(is) do Premiere" % len(profs))
    else:
        print("  presets BERSERKER: abra o Premiere uma vez e rode de novo (não há perfil ainda)")

doc = os.path.join(skills, "minecraft-video-editor", "scripts", "doctor.py")
if os.path.exists(doc):
    print("\n== Checagem")
    subprocess.run([sys.executable, "-X", "utf8", doc])
input("\nPronto. Enter para fechar.") if sys.stdin.isatty() and "--sim" not in A else None
