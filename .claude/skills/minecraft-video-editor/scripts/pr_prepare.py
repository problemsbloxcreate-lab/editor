"""Prepara o Premiere para montar um bruto NOVO sem mexer no projeto que o Matheus está usando:
cria um projeto novo (fica ativo no Premiere; o outro continua aberto), importa o bruto e cria a sequência 1920x1080 na taxa do bruto.
Devolve o ID da sequência para o build_edit3.py.

uso: python pr_prepare.py <bruto.mp4> <pasta_do_job> [--nome EDICAO_x]
saída (stdout, JSON): {"projeto": ..., "seq_id": ..., "item": ...}
"""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
BR = os.path.join(HERE, "run_bridge.py")


def run(js, name, job, timeout=300):
    p = os.path.join(job, name + ".jsx")
    open(p, "w", encoding="utf8").write(js)
    r = subprocess.run([sys.executable, "-X", "utf8", BR, p, str(timeout)], capture_output=True, text=True, encoding="utf8")
    if r.returncode: raise SystemExit(name + " falhou: " + (r.stderr or r.stdout)[-600:])
    return json.load(open(p.replace(".jsx", ".result.json"), encoding="utf8"))


def main():
    a = sys.argv[1:]
    bruto, job = os.path.abspath(a[0]), os.path.abspath(a[1])
    nome = a[a.index("--nome") + 1] if "--nome" in a else "EDICAO_" + os.path.splitext(os.path.basename(bruto))[0][:40]
    os.makedirs(job, exist_ok=True)
    proj = os.path.join(job, nome + ".prproj")
    J = json.dumps
    r1 = run('''var ok = app.newProject(%s); var r = {ok: ok, path: app.project.path}; return __result(r);''' % J(proj.replace("\\", "/")), "pr_new", job, 120)
    r2 = run('''var p = app.project; if (p.path.replace(/\\\\/g, "/").toLowerCase() != %s.toLowerCase()) throw new Error("projeto ativo errado: " + p.path);
p.importFiles([%s], true, p.rootItem, false);
var it = null; for (var i = 0; i < p.rootItem.children.numItems; i++) if (p.rootItem.children[i].type == 1) it = p.rootItem.children[i];
var s = p.createNewSequenceFromClips(%s, [it], p.rootItem);
var st = s.getSettings(); st.videoFrameWidth = 1920; st.videoFrameHeight = 1080; s.setSettings(st);
p.save();
return __result({seq_id: s.sequenceID, item: it.name, w: s.frameSizeHorizontal, h: s.frameSizeVertical});''' % (J(proj.replace("\\", "/")), J(bruto.replace("\\", "/")), J(nome)), "pr_seq", job, 600)
    out = {"projeto": proj, "seq_id": r2.get("seq_id"), "item": r2.get("item"), "frame": [r2.get("w"), r2.get("h")]}
    json.dump(out, open(os.path.join(job, "premiere.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
