"""Prepara o mod CineCam numa máquina NOVA (rodar uma vez, com internet).
uso: python setup_cinecam.py [--home <pasta do mod>] [--run <pasta de execução>] [--out <saída>]
   (padrões: minecraft-video-editor/scripts/paths.py — `python paths.py --show`)

1. copia assets/cinecam-mod (código ATUAL do mod, v0.7) para --home
2. garante um JDK 17 (o do Gradle em ~/.gradle/jdks, um Temurin 17 instalado, ou instala via winget)
3. gradlew build downloadAssets prepareRunClient — baixa Minecraft 1.20.1 + Forge 47.4.16 (~1-2 GB no ~/.gradle) e compila
   (o render usa `gradlew runClient --offline`, então esse 1º passo ONLINE é obrigatório)
4. grava cinecam_home/run/out/java_home na config do usuário (%APPDATA%/EstudioProblems/config.json) — sem setx:
   vale na hora, para o render.py e para o serviço local
O .jar pronto (assets/cinecam-mod/dist/) serve para pôr numa instância Forge 1.20.1 comum; o render da skill NÃO usa o .jar.
"""
import glob, os, shutil, subprocess, sys

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = sys.argv[1:]


def opt(n, d): return A[A.index(n) + 1] if n in A else d


sys.path.insert(0, os.path.join(os.path.dirname(SKILL), "minecraft-video-editor", "scripts"))
import paths as P

HOME = os.path.abspath(opt("--home", P.cinecam("home")))
RUN = os.path.abspath(opt("--run", P.cinecam("run")))
OUT = os.path.abspath(opt("--out", P.cinecam("out")))


def find_jdk17():
    c = sorted(glob.glob(os.path.expanduser("~/.gradle/jdks/temurin17-download/jdk-17*")))
    c += sorted(glob.glob(r"C:\Program Files\Eclipse Adoptium\jdk-17*")) + sorted(glob.glob(r"C:\Program Files\Java\jdk-17*"))
    c += sorted(glob.glob(r"C:\Program Files\Microsoft\jdk-17*")) + sorted(glob.glob(r"C:\Program Files\Zulu\zulu-17*"))
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
    for k, v in (("cinecam_home", HOME), ("cinecam_run", RUN), ("cinecam_out", OUT), ("cinecam_java_home", jdk)):
        P.set_key(k, v)
    print("OK. CineCam pronto; caminhos gravados em", P.USER_CFG, "| Teste: python scripts/selftest.py")


if __name__ == "__main__":
    main()
