"""Checagem completa do ambiente da skill minecraft-video-editor (rodar em qualquer máquina).
uso: python doctor.py [--epidemic "D:\\...\\Epidemic 2K23 (Pasta de músicas)"] [--bridge]   (--bridge testa a ponte com o Premiere ABERTO)
Saída: OK / AVISO / FALTA por item, com a correção. Código de saída 0 se nada essencial faltar."""
import importlib, json, os, shutil, subprocess, sys

SK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOME = os.path.expanduser("~")
res = []


def add(level, item, detail="", fix=""):
    res.append((level, item, detail, fix))


def cfg():
    p = os.path.join(SK, "config.json")
    return json.load(open(p, encoding="utf8")) if os.path.exists(p) else {}


def main():
    C = cfg()
    epi = C.get("epidemic_dir")
    if "--epidemic" in sys.argv: epi = sys.argv[sys.argv.index("--epidemic") + 1]
    # 1. Python + pacotes
    v = sys.version_info
    add("OK" if v >= (3, 10) else "FALTA", "Python %d.%d" % v[:2], "", "instalar Python 3.11+ (python.org) e marcar 'Add to PATH'")
    for mod, pipname, need in [("numpy", "numpy", 1), ("scipy", "scipy", 1), ("soundfile", "soundfile", 1), ("librosa", "librosa", 1),
                               ("PIL", "pillow", 1), ("cv2", "opencv-python", 0), ("requests", "requests", 1), ("dotenv", "python-dotenv", 0), ("faster_whisper", "faster-whisper", 1),
                               ("torch", "torch", 0), ("transformers", "transformers", 0), ("yt_dlp", "yt-dlp", 0)]:
        try:
            m = importlib.import_module(mod); add("OK", "pacote " + pipname, getattr(m, "__version__", ""))
        except Exception as e:
            add("FALTA" if need else "AVISO", "pacote " + pipname, str(e)[:80], "pip install " + pipname + ("" if need else "   (torch/transformers = busca de música por CLAP)"))
    # 2. ffmpeg
    for b in ("ffmpeg", "ffprobe"):
        p = shutil.which(b)
        add("OK" if p else "FALTA", b, p or "", "winget install Gyan.FFmpeg   (depois reabrir o terminal)")
    font = r"C:\Windows\Fonts\arial.ttf"
    add("OK" if os.path.exists(font) else "AVISO", "fonte arial.ttf (grade do zoom_focus_sheet)", font, "ajustar FONT em scripts/zoom_focus_sheet.py")
    # 3. skill e bibliotecas
    L = os.path.join(SK, "library")
    def cnt(d, ext): return len([f for f in os.listdir(d) if f.lower().endswith(ext)]) if os.path.isdir(d) else 0
    add("OK" if os.path.exists(os.path.join(SK, "SKILL.md")) else "FALTA", "SKILL.md", SK)
    n = cnt(os.path.join(L, "sfx"), (".mp3", ".wav"))
    add("OK" if n >= 120 else "FALTA", "SFX em library/sfx", "%d arquivos" % n, "recopiar library/sfx do pacote")
    n = cnt(os.path.join(L, "clap"), ".npz")
    add("OK" if n >= 3 else "AVISO", "índice CLAP library/clap", "%d .npz" % n)
    for f in ("berserker_presets.json", "insercoes/promo_ate_dia_31.mp4", "insercoes/endcard_veja_mais_videos.mp4"):
        add("OK" if os.path.exists(os.path.join(L, f)) else "FALTA", "library/" + f)
    # 4. biblioteca Epidemic
    if epi and os.path.isdir(epi):
        mp3 = sum(len([f for f in fs if f.lower().endswith(".mp3")]) for _, _, fs in os.walk(epi))
        miss = [d for d in ("TROLL", "MISTERIO", "TENSAS", "VLOGS", "NUEVAS 2K24", "2K25", "EPICAS", "MUY ANIMADAS") if not os.path.isdir(os.path.join(epi, d))]
        add("OK" if mp3 >= 370 and not miss else "AVISO", "biblioteca Epidemic", "%s — %d mp3%s" % (epi, mp3, (" | faltam pastas " + ",".join(miss)) if miss else ""),
            "extrair o zip de músicas nessa pasta (ou rodar o instalador com --epidemic)")
    else:
        add("FALTA", "biblioteca Epidemic", str(epi), "extrair o zip *_MUSICAS e rodar o instalador (grava epidemic_dir em config.json)")
    # 5. dependências de outras skills
    for rel, why in [(".claude/skills/watch/SKILL.md", "assistir vídeos de referência"),
                     (".claude/skills/coelho-no-japao-editor/references/premiere-transport.md", "regras da ponte do Premiere"),
                     (".claude/skills/minecraft-cinematic/SKILL.md", "B-roll CineCam (regra 14)"),
                     (".claude/agents/producao-problems.md", "orquestrador do canal")]:
        p = os.path.join(HOME, rel)
        add("OK" if os.path.exists(p) else "AVISO", rel.split("/")[2] + " — " + why, "", "copiar de dependencias/ do pacote")
    # transcrição: mesmo motor do Estúdio Problems, local (faster-whisper large-v3-turbo)
    try:
        import faster_whisper, ctranslate2
        n = ctranslate2.get_cuda_device_count()
        add("OK", "transcrição local (faster-whisper %s)" % faster_whisper.__version__, "placa NVIDIA: %s" % ("sim" if n else "não — vai pelo processador, mais lento"))
    except Exception as e:
        add("FALTA", "transcrição local (faster-whisper)", str(e)[:80], "python -m pip install faster-whisper nvidia-cublas-cu12 nvidia-cudnn-cu12")
    mw = os.path.join(HOME, ".cache", "huggingface", "hub", "models--mobiuslabsgmbh--faster-whisper-large-v3-turbo")
    add("OK" if os.path.isdir(mw) else "AVISO", "modelo whisper-large-v3-turbo baixado", mw, "baixa sozinho na 1ª transcrição (1,6 GB) ou rode o instalador")
    # 6. Premiere
    sys.path.insert(0, os.path.join(SK, "scripts"))
    import adobe_presets as ap
    h = ap.h264_preset(); w = ap.wav_preset()
    add("OK" if h else "FALTA", "Premiere Pro (preset H264 Match Source)", h or "", "instalar o Premiere Pro (2024+)")
    add("OK" if w else "AVISO", "preset Waveform Audio 48kHz", w or "")
    cep = os.path.join(os.environ.get("APPDATA", ""), "Adobe", "CEP", "extensions", "MCPBridgeCEP", "CSXS", "manifest.xml")
    add("OK" if os.path.exists(cep) else "FALTA", "extensão MCPBridgeCEP", cep, "rodar o instalador (copia para %APPDATA%\\Adobe\\CEP\\extensions)")
    try:
        import winreg
        dbg = []
        for vv in range(9, 15):
            try:
                k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Adobe\CSXS.%d" % vv)
                if str(winreg.QueryValueEx(k, "PlayerDebugMode")[0]) == "1": dbg.append(vv)
            except OSError: pass
        add("OK" if dbg else "FALTA", "PlayerDebugMode (extensão sem assinatura)", "CSXS " + ",".join(map(str, dbg)), "rodar o instalador (grava HKCU\\Software\\Adobe\\CSXS.9..14 PlayerDebugMode=1)")
    except ImportError:
        add("AVISO", "registro do Windows", "não é Windows")
    hf = os.path.join(HOME, ".cache", "huggingface", "hub", "models--laion--clap-htsat-unfused")
    add("OK" if os.path.isdir(hf) else "AVISO", "modelo CLAP baixado", hf, "baixa sozinho no 1º clap_query (1,2 GB) ou rodar o instalador sem --no-model")
    mc = os.path.join(os.environ.get("APPDATA", ""), "ModrinthApp", "meta", "assets")
    add("OK" if os.path.isdir(mc) else "AVISO", "assets do Minecraft (só p/ extrair SFX novos do jogo)", mc, "opcional: os SFX de MC já vêm prontos em library/sfx")
    # 6b. CineCam (B-roll)
    cm = os.environ.get("CINECAM_HOME") or os.path.join(C.get("work_dir", r"D:\Pobrs"), "cinecam-forge-1.20.1")
    if not os.path.isdir(cm) and os.path.isdir(r"D:\cinecam-forge-1.20.1"): cm = r"D:\cinecam-forge-1.20.1"
    add("OK" if os.path.exists(os.path.join(cm, "gradlew.bat")) else "AVISO", "mod CineCam (B-roll, regra 14)", cm,
        "python ~/.claude/skills/minecraft-cinematic/scripts/setup_cinecam.py (1ª vez, com internet)")
    import glob as _g
    jdk = _g.glob(os.path.join(HOME, ".gradle", "jdks", "temurin17-download", "jdk-17*")) + _g.glob(r"C:\Program Files\Eclipse Adoptium\jdk-17*") + _g.glob(r"C:\Program Files\Java\jdk-17*")
    add("OK" if jdk or os.environ.get("CINECAM_JAVA_HOME") else "AVISO", "JDK 17 (CineCam)", (jdk or [""])[-1], "setup_cinecam.py instala (winget Temurin 17)")
    sk = os.path.join(HOME, ".claude", "skills", "minecraft-cinematic", "assets", "skins")
    add("OK" if os.path.isdir(sk) else "AVISO", "skins da turma (CineCam)", sk)
    # 6b2. cinemáticas automáticas (regra 20)
    cs = os.path.join(HOME, ".claude", "skills", "minecraft-cinematic", "scripts")
    try:
        sys.path.insert(0, cs)
        from cinecam.turma import skins_root as _sr
        from cinecam.sets import sites as _sites
        add("OK", "skins usadas pelas cinemáticas", str(_sr()))
        n = len(_sites())
        add("OK" if n >= 10 else "FALTA", "locações catalogadas (seed 4242)", "%d biomas" % n, "minecraft-cinematic/references/sites_4242.json")
    except Exception as e:
        add("FALTA", "biblioteca cinecam (cinemáticas, regra 20)", str(e)[:100])
    try:
        import cv2 as _cv
        add("OK" if _cv.ocl.haveOpenCL() else "AVISO", "GPU p/ o DoF das cinemáticas (OpenCL)", "sim" if _cv.ocl.haveOpenCL() else "não: DoF no processador (mais lento)")
    except Exception as e:
        add("FALTA", "opencv (DoF das cinemáticas)", str(e)[:80], "pip install opencv-python")
    rn = os.environ.get("CINECAM_RUN") or (r"D:\cinecam-run" if os.path.isdir(r"D:\cinecam-run") else os.path.join(C.get("work_dir", r"D:\Pobrs"), "cinecam-run"))
    add("OK" if os.path.exists(os.path.join(rn, "launch.json")) else "AVISO", "CineCam lançamento direto (sem gradle no render)",
        os.path.join(rn, "launch.json"), "criado sozinho no 1º render (via gradle)")
    # 6c. interface + FilmCraft + Claude Code (regra 19)
    import shutil as _sh
    add("OK" if _sh.which("claude") else "AVISO", "Claude Code no PATH (interface Editor Problems roda a skill em segundo plano)", _sh.which("claude") or "", "instalar o Claude Code e logar")
    try:
        import filmcraft as _fc
        a_, c_ = _fc.where()
        add("OK" if a_ else "AVISO", "FilmCraft (destino sem Premiere)", a_ or "", "baixa sozinho no 1º job sem Premiere (70 MB) ou: python scripts/filmcraft.py ensure")
    except Exception as e:
        add("AVISO", "FilmCraft", str(e)[:80])
    add("OK" if os.path.exists(os.path.join(SK, "app", "server.py")) else "FALTA", "interface Editor Problems (app/)", os.path.join(SK, "app", "ABRIR_EDITOR.bat"))
    # 7. ponte viva
    if "--bridge" in sys.argv:
        import tempfile
        js = os.path.join(tempfile.gettempdir(), "mve_doctor_ping.jsx")
        open(js, "w", encoding="utf8").write('return __result({v: app.version, p: app.project ? app.project.name : ""});')
        r = subprocess.run([sys.executable, os.path.join(SK, "scripts", "run_bridge.py"), js, "15"], capture_output=True, text=True)
        add("OK" if r.returncode == 0 else "FALTA", "ponte MCP com o Premiere", (r.stdout or r.stderr).strip()[-160:],
            "abrir o Premiere > Janela > Extensões > MCP Bridge (o painel precisa ficar aberto)")
    # relatório
    bad = 0
    for lv, it, d, fx in res:
        print("[%-5s] %-55s %s" % (lv, it, d))
        if lv != "OK" and fx: print("         -> " + fx)
        bad += lv == "FALTA"
    print("\n%d itens, %d FALTA, %d AVISO" % (len(res), bad, sum(1 for r in res if r[0] == "AVISO")))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
