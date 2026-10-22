"""Monta o pacote para instalar a skill em OUTRO computador (rodar na máquina original).
uso: python export_package.py [--out "C:\\Users\\mathe\\Desktop"] [--sem-musicas]
Gera:  minecraft-video-editor_v6_INSTALAR.zip   (skill + dependências + Premiere + memórias + research em texto + instalador)
       minecraft-video-editor_v6_MUSICAS.zip    (biblioteca Epidemic local inteira, ~2 GB; extrair na MESMA pasta do 1º)
Instalação: extrair os dois zips na mesma pasta -> INSTALAR.bat (detalhes no LEIA-ME.md)."""
import json, os, shutil, sys, tempfile, zipfile

SK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOME = os.path.expanduser("~")
CLAUDE = os.path.join(HOME, ".claude")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths as P
CFG = P.cfg()
EPI = P.epidemic_dir()
SKILLS_DIR = CFG.get("skills_dir", os.path.join(HOME, "Skills"))
MEM = os.path.join(CLAUDE, "projects", "C--Users-mathe-Skills", "memory")
MEMORIAS = ["project_mc_video_editor_skill.md", "feedback_mc_video_editor_v11_rejected.md", "feedback_mc_video_editor_v2_corrected.md",
            "feedback_mc_video_editor_r3_20out.md", "feedback_mc_cinematicas_automaticas.md", "feedback_mc_decupagem_pattern.md", "reference_mc_editor_local_assets.md",
            "project_bounce_reedit.md", "project_sem_slots_edit.md", "feedback_minering_reedit_pattern.md",
            "project_minering_matteeoo_finishing_r005.md", "project_estudio_claude_minering.md", "project_cinecam_pa_rasante_plongee.md",
            "project_minecraft_cinematic_skill.md", "project_producao_problems_agent.md", "project_bebi_agua_barriga_closes.md",
            "feedback_motion_camera_integration.md", "feedback_tool_choice_by_result.md"]
RESEARCH = ["mc-test", "mc-decup", "mc-agua-edit", "mc-agua-diff20"]       # só texto (planos, transcrições, diffs, jsx)
TEXT = (".md", ".py", ".jsx", ".js", ".json", ".txt", ".csv", ".log", ".srt", ".npz")
SKIP_DIRS = {"__pycache__", ".git", "frames", "zf_test"}


def cp(src, dst, filt=None):
    for dp, dns, fs in os.walk(src):
        dns[:] = [d for d in dns if d not in SKIP_DIRS]
        for f in fs:
            p = os.path.join(dp, f)
            if filt and not filt(p): continue
            q = os.path.join(dst, os.path.relpath(p, src)); os.makedirs(os.path.dirname(q), exist_ok=True); shutil.copy2(p, q)


def zipdir(src, out, store_ext=(".mp3", ".mp4", ".wav", ".m4a", ".png", ".jpg", ".npz", ".gz", ".zip")):
    n = 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, allowZip64=True, compresslevel=6) as z:
        for dp, _, fs in os.walk(src):
            for f in fs:
                p = os.path.join(dp, f)
                z.write(p, os.path.relpath(p, src), compress_type=zipfile.ZIP_STORED if f.lower().endswith(store_ext) else zipfile.ZIP_DEFLATED); n += 1
    return n


def main():
    out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else os.path.join(HOME, "Desktop")
    tmp = tempfile.mkdtemp(prefix="mve_pkg_")
    P = os.path.join(tmp, "pacote")
    print("montando em", P)
    cp(SK, os.path.join(P, "skill", "minecraft-video-editor"), lambda p: not p.endswith("config.json"))
    for f in os.listdir(os.path.join(SK, "distribuicao")): shutil.copy2(os.path.join(SK, "distribuicao", f), os.path.join(P, f))
    for d in ("watch", "minecraft-cinematic"): cp(os.path.join(CLAUDE, "skills", d), os.path.join(P, "dependencias", "skills", d))
    t = os.path.join(P, "dependencias", "skills", "coelho-no-japao-editor", "references"); os.makedirs(t, exist_ok=True)
    shutil.copy2(os.path.join(CLAUDE, "skills", "coelho-no-japao-editor", "references", "premiere-transport.md"), t)
    os.makedirs(os.path.join(P, "dependencias", "agents"), exist_ok=True)
    shutil.copy2(os.path.join(CLAUDE, "agents", "producao-problems.md"), os.path.join(P, "dependencias", "agents"))
    cp(os.path.join(os.environ["APPDATA"], "Adobe", "CEP", "extensions", "MCPBridgeCEP"), os.path.join(P, "dependencias", "premiere", "MCPBridgeCEP"))
    prf = os.path.join(HOME, "Documents", "Adobe", "Premiere Pro", "26.0", "Profile-mathe", "Effect Presets and Custom Items.prfpset")
    if os.path.exists(prf): shutil.copy2(prf, os.path.join(P, "dependencias", "premiere"))
    os.makedirs(os.path.join(P, "memoria"), exist_ok=True)
    idx = open(os.path.join(MEM, "MEMORY.md"), encoding="utf8").read().splitlines()
    keep = []
    for f in MEMORIAS:
        if os.path.exists(os.path.join(MEM, f)):
            shutil.copy2(os.path.join(MEM, f), os.path.join(P, "memoria")); keep += [l for l in idx if "(%s)" % f in l]
    open(os.path.join(P, "memoria", "MEMORY_trecho.md"), "w", encoding="utf8").write("\n".join(keep) + "\n")
    for r in RESEARCH:
        src = os.path.join(SKILLS_DIR, "_research", r)
        if os.path.isdir(src): cp(src, os.path.join(P, "research", r), lambda p: p.lower().endswith(TEXT) and os.path.getsize(p) < 25e6)
    z1 = os.path.join(out, "minecraft-video-editor_v6_INSTALAR.zip")
    print("zip 1:", z1, zipdir(P, z1), "arquivos", round(os.path.getsize(z1) / 1e6), "MB")
    if "--sem-musicas" not in sys.argv:
        M = os.path.join(tmp, "musicas")
        os.makedirs(os.path.join(M, "MUSICAS"))
        z2 = os.path.join(out, "minecraft-video-editor_v6_MUSICAS.zip")
        n = 0
        with zipfile.ZipFile(z2, "w", zipfile.ZIP_STORED, allowZip64=True) as z:
            base = os.path.basename(EPI.rstrip("\\/"))
            for dp, _, fs in os.walk(EPI):
                for f in fs:
                    p = os.path.join(dp, f); z.write(p, os.path.join("MUSICAS", base, os.path.relpath(p, EPI))); n += 1
        print("zip 2:", z2, n, "arquivos", round(os.path.getsize(z2) / 1e6), "MB")
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
