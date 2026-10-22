"""Pasta de MÍDIA autônoma para outro PC (pedido do Matheus, 22/10/2026): "quando for pra outro PC vou te pedir a pasta das mídias,
me mande sempre atualizada e sem nenhuma dependência".  O CÓDIGO vai pelo GitHub (sync_github.py); esta pasta leva TUDO que fica fora
dele, com o próprio instalador (só Python padrão):

    python export_midia.py [--out D:\\Pobrs\\MIDIA_editor] [--sem-modelos] [--sem-epidemic]

Conteúdo (a lista de mídia da skill = exatamente o que o sync_github.py EXCLUI, para as duas nunca divergirem):
  skills/minecraft-video-editor/library/...   músicas da skill, SFX, promo/tela final, overlays PNG
  skills/minecraft-cinematic/assets/skins/     skins da turma
  epidemic/<pasta>                             biblioteca Epidemic inteira (config.json -> epidemic_dir)
  modelos/huggingface/hub/                     Whisper large-v3-turbo + CLAP (sem baixar nada na outra máquina)
  ferramentas/filmcraft-...                    FilmCraft portátil
  premiere/                                    extensão MCPBridgeCEP + presets BERSERKER (.prfpset)
  INSTALAR_MIDIA.bat + instalar_midia.py + LEIA-ME.txt + MANIFESTO.json
Incremental: rodar de novo só copia o que mudou e apaga o que saiu (a pasta fica sempre igual à desta máquina).
"""
import datetime, glob, json, os, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SK = os.path.dirname(HERE)
SKILLS = os.path.dirname(SK)
HOME = os.path.expanduser("~")
sys.path.insert(0, HERE)
import sync_github as SG

CFG = json.load(open(os.path.join(SK, "config.json"), encoding="utf8")) if os.path.exists(os.path.join(SK, "config.json")) else {}
NOT_MEDIA = ["config.json", "scripts/cinecam/acts_v1_backup.py"]                 # excluídos do GitHub mas que não são mídia
MODELS = ["models--mobiuslabsgmbh--faster-whisper-large-v3-turbo", "models--laion--clap-htsat-unfused"]


def same(a, b):
    try:
        sa, sb = os.stat(a), os.stat(b)
        return sa.st_size == sb.st_size and int(sa.st_mtime) == int(sb.st_mtime)
    except OSError:
        return False


class Mirror:
    def __init__(self, out):
        self.out, self.keep, self.copied, self.bytes = out, set(), 0, 0

    def file(self, src, rel):
        dst = os.path.join(self.out, rel)
        self.keep.add(os.path.normcase(os.path.abspath(dst)))
        self.bytes += os.path.getsize(src)
        if not same(src, dst):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            self.copied += 1

    def tree(self, src, rel, filt=None):
        for dp, dns, fs in os.walk(src):
            dns[:] = [d for d in dns if d != "__pycache__"]
            for f in fs:
                p = os.path.join(dp, f)
                r = os.path.relpath(p, src).replace("\\", "/")
                if filt and not filt(r):
                    continue
                self.file(p, os.path.join(rel, r))

    def prune(self):
        gone = 0
        for dp, dns, fs in os.walk(self.out, topdown=False):
            for f in fs:
                p = os.path.normcase(os.path.abspath(os.path.join(dp, f)))
                if p not in self.keep:
                    os.remove(p); gone += 1
            if dp != self.out and not os.listdir(dp):
                os.rmdir(dp)
        return gone


def main():
    a = sys.argv[1:]
    out = a[a.index("--out") + 1] if "--out" in a else os.path.join(CFG.get("work_dir", r"D:\Pobrs"), "MIDIA_editor")
    os.makedirs(out, exist_ok=True)
    M = Mirror(out)
    parts = {}
    # 1) mídia das skills = o que o GitHub não leva
    for name, pats in SG.SOURCES.items():
        src = os.path.join(SKILLS, name)
        before = M.bytes
        M.tree(src, os.path.join("skills", name),
               lambda r, pats=pats: SG.excluded(r, pats) and r not in NOT_MEDIA and not any(
                   __import__("fnmatch").fnmatch(r, p) for p in SG.ALWAYS_OUT))
        parts["skills/" + name] = M.bytes - before
    # 2) Epidemic
    epi = CFG.get("epidemic_dir")
    if "--sem-epidemic" not in a and epi and os.path.isdir(epi):
        before = M.bytes
        M.tree(epi, os.path.join("epidemic", os.path.basename(epi.rstrip("\\/"))))
        parts["epidemic"] = M.bytes - before
    # 3) modelos (transcrição + busca de música): a outra máquina não baixa nada
    hub = os.path.join(os.environ.get("HF_HOME", os.path.join(HOME, ".cache", "huggingface")), "hub")
    if "--sem-modelos" not in a:
        for m in MODELS:
            if os.path.isdir(os.path.join(hub, m)):
                before = M.bytes
                M.tree(os.path.join(hub, m), os.path.join("modelos", "huggingface", "hub", m))
                parts["modelos/" + m] = M.bytes - before
    # 4) FilmCraft portátil
    for d in glob.glob(os.path.join(os.environ.get("LOCALAPPDATA", ""), "mve-tools", "filmcraft-*-portable")):
        before = M.bytes
        M.tree(d, os.path.join("ferramentas", os.path.basename(d)))
        parts["ferramentas/" + os.path.basename(d)] = M.bytes - before
    # 5) Premiere: extensão da ponte + presets
    cep = os.path.join(os.environ.get("APPDATA", ""), "Adobe", "CEP", "extensions", "MCPBridgeCEP")
    if os.path.isdir(cep):
        M.tree(cep, os.path.join("premiere", "MCPBridgeCEP"))
    for prf in glob.glob(os.path.join(HOME, "Documents", "Adobe", "Premiere Pro", "*", "Profile-*", "Effect Presets and Custom Items.prfpset")):
        M.file(prf, os.path.join("premiere", "Effect Presets and Custom Items.prfpset"))
        break
    # 6) instalador + leia-me + manifesto
    dist = os.path.join(SK, "distribuicao")
    M.file(os.path.join(dist, "instalar_midia.py"), "instalar_midia.py")
    M.file(os.path.join(dist, "INSTALAR_MIDIA.bat"), "INSTALAR_MIDIA.bat")
    gone = M.prune() if "--sem-epidemic" not in a and "--sem-modelos" not in a else 0
    man = {"gerado": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "origem": os.environ.get("COMPUTERNAME", ""),
           "epidemic_nome": os.path.basename((epi or "").rstrip("\\/")), "partes_MB": {k: round(v / 2 ** 20) for k, v in parts.items()},
           "total_MB": round(M.bytes / 2 ** 20)}
    json.dump(man, open(os.path.join(out, "MANIFESTO.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
    open(os.path.join(out, "LEIA-ME.txt"), "w", encoding="utf8").write(
        "MÍDIA do editor (minecraft-video-editor + minecraft-cinematic) — gerada em %s\n\n"
        "1. Instale o código primeiro (GitHub problemsbloxcreate-lab/editor, pasta .claude/skills, copiada para ~/.claude/skills).\n"
        "2. Dê dois cliques em INSTALAR_MIDIA.bat (ou: python instalar_midia.py [--skills C:\\...\\.claude\\skills] [--epidemic D:\\Musicas]).\n"
        "   Ele copia cada parte para o lugar certo (só o que falta ou mudou), grava o epidemic_dir no config.json e instala a extensão\n"
        "   do Premiere. Pode rodar de novo quando receber uma pasta mais nova.\n"
        "3. Confira com: python ~/.claude/skills/minecraft-video-editor/scripts/doctor.py\n\n"
        "Conteúdo: %s\nTotal: %d MB\n" % (man["gerado"], json.dumps(man["partes_MB"], ensure_ascii=False), man["total_MB"]))
    print("Pasta de mídia:", out)
    print("  %d MB no total; %d arquivos copiados agora; %d removidos (saíram da skill)" % (man["total_MB"], M.copied, gone))
    for k, v in man["partes_MB"].items():
        print("  %-60s %6d MB" % (k, v))


if __name__ == "__main__":
    main()
