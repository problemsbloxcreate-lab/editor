"""Instalador da skill minecraft-video-editor (v6) em outro computador Windows.

uso (na pasta extraída do pacote):
  python instalar.py                       # pergunta as pastas e instala tudo
  python instalar.py --epidemic "E:\\Musicas\\Epidemic 2K23 (Pasta de músicas)" --work "E:\\Pobrs" --skills "C:\\Users\\voce\\Skills" --sim
opções: --home <pasta do usuário> (teste) · --sim (não pergunta nada) · --no-pip · --no-model · --no-registry · --force (sobrescreve memórias)

O que faz:
 1. copia a skill e as dependências para ~/.claude (skills, agents)
 2. copia as músicas Epidemic (se a pasta MUSICAS do 2º zip estiver ao lado) para --epidemic
 3. troca os caminhos da máquina original (C:\\Users\\mathe, D:\\Pobrs, D:\\Users\\PREDATOR\\...Epidemic...) pelos daqui, em todos os textos/scripts
 4. instala a extensão MCP Bridge do Premiere + PlayerDebugMode no registro (HKCU)
 5. memórias do Claude na pasta do projeto (~/.claude/projects/<chave da pasta Skills>/memory)
 6. pip install -r requirements.txt, baixa o modelo CLAP (1,2 GB) e o de transcrição (whisper-large-v3-turbo, 1,6 GB; local, sem chave)
 7. roda scripts/doctor.py
"""
import json, os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
A = sys.argv[1:]
SIM = "--sim" in A


def opt(name, default):
    return A[A.index(name) + 1] if name in A else default


def ask(q, default):
    if SIM: return default
    v = input("%s\n  [Enter = %s]: " % (q, default)).strip().strip('"')
    return v or default


def yes(q, default=True):
    if SIM: return default
    v = input(q + (" [S/n]: " if default else " [s/N]: ")).strip().lower()
    return default if not v else v.startswith("s") or v.startswith("y")


HOME = os.path.abspath(opt("--home", os.path.expanduser("~")))
ORIG = {"home": r"C:\Users\mathe", "epidemic": r"D:\Users\PREDATOR\Documents\Epidemic 2K23 (Pasta de músicas)",
        "work": r"D:\Pobrs", "cinecam": r"D:\cinecam-out", "cinemod": r"D:\cinecam-forge-1.20.1", "cinerun": r"D:\cinecam-run",
        "skins": r"C:\Users\mathe\AppData\Roaming\ModrinthApp\profiles\Construir Pirâmide\config\bbs\assets\models\skins",
        "skins2": r"C:\Users\mathe\AppData\Roaming\ModrinthApp\profiles\Template Forge 09.26\config\bbs\assets\models\skins",
        "proj":"C--Users-mathe-Skills"}

print("=== Instalador minecraft-video-editor v6 ===\nUsuário: %s\n" % HOME)
SKILLS = os.path.abspath(ask("Pasta de trabalho do Claude (onde você abre o Claude Code; os _research ficam nela):", opt("--skills", os.path.join(HOME, "Skills"))))
EPI = os.path.abspath(ask("Pasta da biblioteca Epidemic (músicas por clima):", opt("--epidemic", os.path.join(HOME, "Documents", "Epidemic 2K23 (Pasta de músicas)"))))
WORK = os.path.abspath(ask("Pasta de trabalho de mídia (renders, takes, time-lapses — equivale ao D:\\Pobrs):", opt("--work", os.path.join(HOME, "Pobrs"))))
CINE = os.path.join(WORK, "cinecam-out")
PROJ = re.sub(r"[^A-Za-z0-9]", "-", SKILLS)   # chave de projeto do Claude Code
CLAUDE = os.path.join(HOME, ".claude")


def variants(old, new):
    """o mesmo caminho escrito de 4 jeitos (\\, \\\\ em JSON/JS, / e escape de JSON com ensure_ascii)"""
    out = [(old, new), (old.replace("\\", "\\\\"), new.replace("\\", "\\\\")), (old.replace("\\", "/"), new.replace("\\", "/"))]
    oa = json.dumps(old)[1:-1]; na = json.dumps(new)[1:-1]
    if (oa, na) not in out: out.append((oa, na))
    return out


REPL = []
CINEMOD = os.path.join(WORK, "cinecam-forge-1.20.1"); CINERUN = os.path.join(WORK, "cinecam-run")
SKINS = os.path.join(HOME, ".claude", "skills", "minecraft-cinematic", "assets", "skins")
for k, new in (("skins", SKINS), ("skins2", SKINS), ("epidemic", EPI), ("cinemod", CINEMOD), ("cinerun", CINERUN), ("cinecam", CINE), ("work", WORK), ("home", HOME)):   # ordem: o mais específico primeiro
    if ORIG[k] != new: REPL += variants(ORIG[k], new)
if ORIG["proj"] != PROJ: REPL.append((ORIG["proj"], PROJ))
TEXT = (".md", ".py", ".jsx", ".js", ".json", ".txt", ".ps1", ".sh", ".bat", ".html", ".xml", ".csv", ".log", ".gradle", ".properties", ".toml")


def patch_tree(root):
    n = 0
    if not REPL: return 0
    for dp, _, fs in os.walk(root):
        for f in fs:
            if not f.lower().endswith(TEXT): continue
            p = os.path.join(dp, f)
            try: s = open(p, encoding="utf8").read()
            except Exception: continue
            t = s
            for a, b in REPL: t = t.replace(a, b)
            if t != s:
                open(p, "w", encoding="utf8").write(t); n += 1
    return n


def copytree(src, dst):
    if not os.path.exists(src): print("  (não veio no pacote: %s)" % src); return False
    shutil.copytree(src, dst, dirs_exist_ok=True); return True


# 1. skill + dependências
print("\n[1] Skill e dependências -> %s" % CLAUDE)
dst_skill = os.path.join(CLAUDE, "skills", "minecraft-video-editor")
copytree(os.path.join(HERE, "skill", "minecraft-video-editor"), dst_skill)
for d in os.listdir(os.path.join(HERE, "dependencias", "skills")):
    copytree(os.path.join(HERE, "dependencias", "skills", d), os.path.join(CLAUDE, "skills", d))
copytree(os.path.join(HERE, "dependencias", "agents"), os.path.join(CLAUDE, "agents"))
copytree(os.path.join(HERE, "research"), os.path.join(SKILLS, "_research"))
for d in (WORK, CINE): os.makedirs(d, exist_ok=True)

# 2. músicas
mus = os.path.join(HERE, "MUSICAS", "Epidemic 2K23 (Pasta de músicas)")
if os.path.isdir(mus):
    print("[2] Copiando músicas Epidemic -> %s (2 GB, aguarde)" % EPI)
    copytree(mus, EPI)
elif os.path.isdir(EPI):
    print("[2] Músicas: usando a pasta existente %s" % EPI)
else:
    print("[2] ATENÇÃO: músicas não encontradas. Extraia o zip *_MUSICAS.zip AQUI (fica a pasta MUSICAS ao lado deste instalador) e rode de novo.")

# 3. caminhos
print("[3] Ajustando caminhos da máquina original:")
for a, b in REPL[:: max(1, len(REPL) // 6)]: print("    %s -> %s" % (a, b))
n = sum(patch_tree(r) for r in (dst_skill, os.path.join(CLAUDE, "agents"), os.path.join(SKILLS, "_research"),
                               *[os.path.join(CLAUDE, "skills", d) for d in os.listdir(os.path.join(HERE, "dependencias", "skills"))]))
json.dump({"epidemic_dir": EPI, "work_dir": WORK, "skills_dir": SKILLS, "cinecam_out": CINE},
          open(os.path.join(dst_skill, "config.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
print("    %d arquivos ajustados; config.json gravado" % n)

# 4. Premiere
print("[4] Premiere: extensão MCP Bridge + presets")
appdata = os.environ.get("APPDATA") if "--home" not in A else os.path.join(HOME, "AppData", "Roaming")
cep = os.path.join(appdata, "Adobe", "CEP", "extensions", "MCPBridgeCEP")
copytree(os.path.join(HERE, "dependencias", "premiere", "MCPBridgeCEP"), cep)
print("    extensão em %s" % cep)
if "--no-registry" not in A and "--home" not in A:
    try:
        import winreg
        for v in range(9, 15):
            k = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Adobe\CSXS.%d" % v)
            winreg.SetValueEx(k, "PlayerDebugMode", 0, winreg.REG_SZ, "1")
        print("    PlayerDebugMode=1 em HKCU\\Software\\Adobe\\CSXS.9..14")
    except Exception as e:
        print("    não consegui gravar o registro (%s) — faça à mão (LEIA-ME)" % e)
print("    presets BERSERKER: o builder recria pelo library/berserker_presets.json; para tê-los também no painel,")
print("    no Premiere: Efeitos > Presets > botão direito > Importar presets > dependencias\\premiere\\Effect Presets and Custom Items.prfpset")

# 5. memórias
mem_dst = os.path.join(CLAUDE, "projects", PROJ, "memory")
print("[5] Memórias -> %s" % mem_dst)
os.makedirs(mem_dst, exist_ok=True)
idx_lines = []
for f in sorted(os.listdir(os.path.join(HERE, "memoria"))):
    if f == "MEMORY_trecho.md":
        idx_lines = [l for l in open(os.path.join(HERE, "memoria", f), encoding="utf8") if l.startswith("- [")]; continue
    d = os.path.join(mem_dst, f)
    if os.path.exists(d) and "--force" not in A: continue
    s = open(os.path.join(HERE, "memoria", f), encoding="utf8").read()
    for a, b in REPL: s = s.replace(a, b)
    open(d, "w", encoding="utf8").write(s)
idx = os.path.join(mem_dst, "MEMORY.md")
cur = open(idx, encoding="utf8").read() if os.path.exists(idx) else "# Memory Index\n\n"
add = [l for l in idx_lines if l.split("](")[1].split(")")[0] not in cur]
open(idx, "w", encoding="utf8").write(cur.rstrip("\n") + "\n" + "".join(add))
print("    %d linhas novas no MEMORY.md" % len(add))

# 6. Python, modelo, chave
if "--no-pip" not in A and yes("[6] Instalar os pacotes Python (pip install -r requirements.txt)?"):
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", os.path.join(HERE, "requirements.txt")])
if "--no-model" not in A and yes("    Baixar agora o modelo CLAP (busca de música por clima, 1,2 GB)?"):
    subprocess.run([sys.executable, "-c", "from transformers import ClapModel, ClapProcessor as P; ClapModel.from_pretrained('laion/clap-htsat-unfused'); P.from_pretrained('laion/clap-htsat-unfused'); print('modelo CLAP ok')"])
if "--no-model" not in A and yes("    Baixar agora o modelo de transcrição (whisper-large-v3-turbo, 1,6 GB)?"):
    subprocess.run([sys.executable, "-c", "from faster_whisper import WhisperModel; WhisperModel('large-v3-turbo', device='cpu', compute_type='int8'); print('modelo de transcrição ok')"])

# 6b. CineCam (B-roll cinemático): JDK 17 + 1º build online do mod (~1-2 GB de downloads no ~/.gradle)
setup = os.path.join(CLAUDE, "skills", "minecraft-cinematic", "scripts", "setup_cinecam.py")
if "--home" not in A and os.path.exists(setup) and ("--cinecam" in A or yes("    Preparar o mod CineCam agora (B-roll; baixa JDK 17 + Minecraft/Forge, ~1-2 GB)?", default=not SIM)):
    subprocess.run([sys.executable, "-X", "utf8", setup, "--home", CINEMOD, "--run", CINERUN, "--out", CINE])
else:
    print("    CineCam: depois rode  python \"%s\" --home \"%s\" --run \"%s\" --out \"%s\"" % (setup, CINEMOD, CINERUN, CINE))

# 6c. atalho da interface (arrastar o bruto -> Premiere ou FilmCraft)
if "--home" not in A and yes("    Criar atalho 'Editor Problems' na Área de Trabalho?"):
    bat = os.path.join(dst_skill, "app", "ABRIR_EDITOR.bat")
    desk = os.path.join(HOME, "Desktop")
    try:
        ps = ("$s=(New-Object -ComObject WScript.Shell).CreateShortcut('%s');$s.TargetPath='%s';$s.WorkingDirectory='%s';$s.Save()"
              % (os.path.join(desk, "Editor Problems.lnk"), bat, os.path.dirname(bat)))
        subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True)
        print("    atalho criado na Área de Trabalho")
    except Exception as e:
        print("    não consegui criar o atalho (%s): abra %s" % (e, bat))

# 7. checagem
print("\n[7] Checagem final:\n")
subprocess.run([sys.executable, "-X", "utf8", os.path.join(dst_skill, "scripts", "doctor.py")])
print("\nPronto. Abra o Claude Code em %s e peça: \"edita esse bruto do Problems\". Se algo deu FALTA, veja o LEIA-ME." % SKILLS)
