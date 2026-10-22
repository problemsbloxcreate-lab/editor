"""Prepara o mod CineCam numa máquina NOVA (rodar uma vez, com internet).
uso: python setup_cinecam.py [--home D:/cinecam-forge-1.20.1] [--run D:/cinecam-run] [--out D:/cinecam-out]

1. copia assets/cinecam-mod (código ATUAL do mod, v0.7) para --home
2. garante um JDK 17 (o do Gradle em ~/.gradle/jdks, um Temurin 17 instalado, ou instala via winget)
3. gradlew build downloadAssets prepareRunClient — baixa Minecraft 1.20.1 + Forge 47.4.16 (~1-2 GB no ~/.gradle) e compila
   (o render usa `gradlew runClient --offline`, então esse 1º passo ONLINE é obrigatório)
4. grava CINECAM_HOME/RUN/OUT/JAVA_HOME como variáveis do usuário (setx) para o render.py achar tudo
O .jar pronto (assets/cinecam-mod/dist/) serve para pôr numa instância Forge 1.20.1 comum; o render da skill NÃO usa o .jar.
"""
import glob, os, shutil, subprocess, sys

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = sys.argv[1:]


def opt(n, d): return A[A.index(n) + 1] if n in A else d


HOME = os.path.abspath(opt("--home", os.environ.get("CINECAM_HOME", "D:/cinecam-forge-1.20.1")))
RUN = os.path.abspath(opt("--run", os.environ.get("CINECAM_RUN", "D:/cinecam-run")))
OUT = os.path.abspath(opt("--out", os.environ.get("CINECAM_OUT", "D:/cinecam-out")))


def find_jdk17():
    c = sorted(glob.glob(os.path.expanduser("~/.gradle/jdks/temurin17-download/jdk-17*")))
    c += sorted(glob.glob(r"C:\Program Files\Eclipse Adoptium\jdk-17*")) + sorted(glob.glob(r"C:\Program Files\Java\jdk-17*"))
    c += sorted(glob.glob(r"C:\Program Files\Microsoft\jdk-17*"))
    return c[-1] if c else None


def main():
    print("CineCam -> %s | run %s | out %s" % (HOME, RUN, OUT))
    src = os.path.join(SKILL, "assets", "cinecam-mod")
    shutil.copytree(src, HOME, dirs_exist_ok=True, ignore=shutil.ignore_patterns("dist", "build", ".gradle"))
    for d in (RUN, OUT): os.makedirs(d, exist_ok=True)
    jdk = find_jdk17()
    if not jdk:
        print("JDK 17 não encontrado: instalando Temurin 17 pelo winget…")
        subprocess.run(["winget", "install", "-e", "--id", "EclipseAdoptium.Temurin.17.JDK", "--accept-source-agreements", "--accept-package-agreements"])
        jdk = find_jdk17()
    if not jdk: raise SystemExit("instale um JDK 17 (adoptium.net) e rode de novo")
    print("JDK 17:", jdk)
    env = dict(os.environ, JAVA_HOME=jdk, CINECAM_RUN=RUN)
    r = subprocess.run([os.path.join(HOME, "gradlew.bat"), "build", "downloadAssets", "prepareRunClient", "--console=plain"], cwd=HOME, env=env)
    if r.returncode: raise SystemExit("gradle falhou (veja acima). Precisa de internet no 1º build.")
    for k, v in (("CINECAM_HOME", HOME), ("CINECAM_RUN", RUN), ("CINECAM_OUT", OUT), ("CINECAM_JAVA_HOME", jdk)):
        subprocess.run(["setx", k, v], capture_output=True)
    print("OK. CineCam pronto; variáveis CINECAM_* gravadas (reabra o terminal/Claude Code). Teste: python scripts/selftest.py")


if __name__ == "__main__":
    main()
