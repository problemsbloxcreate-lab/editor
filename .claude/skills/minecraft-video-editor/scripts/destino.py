"""Onde a edição vai ser montada: Premiere (via MCP Bridge) ou FilmCraft.

Regra (pedido do Matheus, 20/10/2026): se houver Premiere instalado E a ponte MCP Bridge responder -> Premiere;
senão -> FilmCraft (baixa o portátil oficial sozinho se não houver). O usuário pode forçar 'premiere' ou 'filmcraft'.

uso: python destino.py [auto|premiere|filmcraft]      -> imprime o JSON do ambiente e a decisão
     from destino import ambiente, decidir
"""
import glob, json, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def premiere_instalado():
    roots = [os.environ.get("ProgramFiles", r"C:\Program Files") + r"\Adobe"]
    hits = []
    for r in roots: hits += glob.glob(os.path.join(r, "Adobe Premiere Pro*", "Adobe Premiere Pro.exe"))
    return sorted(hits)[-1] if hits else None


def premiere_aberto():
    try:
        out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq Adobe Premiere Pro.exe", "/NH"], capture_output=True, text=True, timeout=10).stdout
        return "Adobe Premiere Pro.exe" in out
    except Exception:
        return False


def ponte_viva(timeout=6):
    """manda um JSX mínimo pela pasta da MCP Bridge; True se o painel do Premiere respondeu"""
    js = os.path.join(tempfile.gettempdir(), "mve_ping.jsx")
    open(js, "w", encoding="utf8").write('return __result({v: app.version, projeto: app.project ? app.project.path : ""});')
    try:
        r = subprocess.run([sys.executable, os.path.join(HERE, "run_bridge.py"), js, str(timeout)], capture_output=True, text=True, timeout=timeout + 5)
        if r.returncode == 0:
            res = js.replace(".jsx", ".result.json")
            return json.load(open(res, encoding="utf8")) if os.path.exists(res) else {"ok": True}
    except Exception:
        pass
    return None


def ambiente(testar_ponte=True):
    import filmcraft as fc
    app, cli = fc.where()
    pr = premiere_instalado()
    aberto = premiere_aberto() if pr else False
    ponte = ponte_viva() if (pr and aberto and testar_ponte) else None
    return {"premiere": {"instalado": bool(pr), "exe": pr, "aberto": aberto, "ponte": bool(ponte), "info": ponte},
            "filmcraft": {"instalado": bool(app), "exe": app, "cli": cli},
            "claude": bool(shutil_which("claude"))}


def shutil_which(x):
    import shutil
    return shutil.which(x)


def decidir(pref="auto", env=None):
    env = env or ambiente()
    p = env["premiere"]
    if pref == "premiere":
        if p["ponte"]: return "premiere", "Premiere aberto e ponte MCP respondendo"
        if not p["instalado"]: return None, "Premiere não está instalado nesta máquina — escolha FilmCraft ou Automático"
        return None, "Premiere instalado, mas a ponte não respondeu: abra o Premiere e o painel Janela > Extensões > MCP Bridge"
    if pref == "filmcraft": return "filmcraft", "escolhido por você"
    if p["instalado"] and p["ponte"]: return "premiere", "Premiere instalado e ponte MCP respondendo"
    why = "Premiere não instalado" if not p["instalado"] else ("Premiere fechado" if not p["aberto"] else "ponte MCP do Premiere não respondeu")
    return "filmcraft", why + " → abrindo no FilmCraft"


if __name__ == "__main__":
    env = ambiente()
    d, why = decidir(sys.argv[1] if len(sys.argv) > 1 else "auto", env)
    print(json.dumps({"ambiente": env, "destino": d, "motivo": why}, ensure_ascii=False, indent=1))
