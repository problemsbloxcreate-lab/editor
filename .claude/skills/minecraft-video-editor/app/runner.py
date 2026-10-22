"""Executa UM job de edição em segundo plano (chamado pelo server.py; roda solto do navegador).

1. decide o destino (destino.py): Premiere (instalado + ponte MCP respondendo) ou FilmCraft;
2. roda o Claude Code sem janela (`claude -p`, stream-json) com a skill minecraft-video-editor no bruto;
3. registra tudo em <job>/eventos.jsonl e o estado em <job>/status.json (a interface lê esses dois);
4. no fim abre o resultado: FilmCraft -> abre o .fcproj; Premiere -> já está no projeto novo do job.

uso: python runner.py <pasta_do_job>
"""
import json, os, re, signal, subprocess, sys, time

APP = os.path.dirname(os.path.abspath(__file__))
SK = os.path.dirname(APP)
sys.path.insert(0, os.path.join(SK, "scripts"))


def now(): return time.strftime("%H:%M:%S")


class Job:
    def __init__(s, d):
        s.d = d; s.cfg = json.load(open(os.path.join(d, "job.json"), encoding="utf8"))
        s.ev = open(os.path.join(d, "eventos.jsonl"), "a", encoding="utf8")

    def status(s, **kw):
        p = os.path.join(s.d, "status.json")
        st = json.load(open(p, encoding="utf8")) if os.path.exists(p) else {}
        st.update(kw); st["atualizado"] = now()
        json.dump(st, open(p + ".tmp", "w", encoding="utf8"), ensure_ascii=False); os.replace(p + ".tmp", p)

    def log(s, tipo, txt):
        s.ev.write(json.dumps({"t": now(), "tipo": tipo, "txt": txt[:2000]}, ensure_ascii=False) + "\n"); s.ev.flush()


PROMPT = """Você está rodando SEM ninguém olhando (job da interface "Editor Problems"). Não faça perguntas: decida pelo padrão da skill e registre as apostas em marcadores.

Use a skill minecraft-video-editor (leia SKILL.md e as referências que ela manda ler) e edite o bruto abaixo de ponta a ponta, com a mesma qualidade de quando o Matheus pede no chat.

- Bruto: {video}
- Pasta do job (trabalhe e grave tudo aqui: transcrições, plan3.json, renders): {job}
- DESTINO: {destino}  ({motivo})
- Nome da edição: {nome}
- Notas do Matheus: {notas}

Montagem:
{montagem}

Cinemáticas (regra 20 da skill, references/cinematicas.md): {cine}

Ao terminar, grave {job}\\RESUMO.md em português: o que foi feito, decisões, apostas e o que conferir. Linhas curtas de progresso no chat ajudam (a interface mostra).
"""

MONT_FC = """- Gere o plano no formato plan3.json (o mesmo do build_edit3.py) em {job}\\plan3.json.
- Monte no FilmCraft: python "{sk}\\scripts\\fc_build.py" "{job}\\plan3.json" "{video}" "{job}\\{nome}.fcproj" --seq-name "{nome}"
- Confira 4–6 quadros com: filmcraft-cli render (veja scripts/filmcraft.py) e corrija o plano se algo sair errado. NÃO abra a janela do FilmCraft (a interface abre no fim)."""

MONT_PR = """- Prepare um projeto NOVO no Premiere (não mexa no projeto que já estava aberto): python "{sk}\\scripts\\pr_prepare.py" "{video}" "{job}" --nome "{nome}"  (devolve seq_id)
- Gere o plan3.json em {job}\\plan3.json (bruto_prefix = nome do arquivo do bruto) e monte: python "{sk}\\scripts\\build_edit3.py" "{job}\\plan3.json" <seq_id>
- O Premiere só age no projeto ATIVO e o Matheus pode estar usando outro projeto ao mesmo tempo: antes de cada build confira app.project.path == o .prproj do job (premiere.json); se não for, reative com app.openDocument(<.prproj do job>). Nunca altere nem feche o outro projeto.
- Em JSX escreva caminhos SEMPRE com barra normal ("D:/Pobrs/...") ou json.dumps: "D:\\Pobrs\\..." com barra simples vira escape no JavaScript e o openDocument devolve false (travou o 1º job do Premiere em 20/10).
- NÃO feche o projeto do job: deixe-o aberto (o Matheus revisa nele); ao terminar, só reative o projeto que estava ativo antes (app.openDocument do caminho dele) para devolver a tela.
- Salve o projeto (app.project.save()) e confira quadros exportando um trecho curto."""


CINE_ON = """LIGADAS (padrão). Com o plan3 fechado e ANTES do build: python "{sk}/scripts/cinematicas.py" slots → context → escreva {job}/cine/cards.json (recriar o LUGAR da cena com a turma certa; ler references/cinematicas.md e minecraft-cinematic/references/enquadramento.md: NUNCA personagem de perfil, frente ou 45°, gestos expressivos, item encaixado) → check (corrija toda ficha recusada) → render stills (olhe TODAS) → render final (run_in_background; ~1 min por cinemática; abre o Minecraft sozinho) → insert. Se faltar RAM e alguma falhar 2×, siga a edição sem ela e anote no RESUMO."""


LIMITE = re.compile(r"(session|usage|rate) limit|limite de uso", re.I)


def segundos_ate_reset(msg):
    """'... resets 6:50am (America/Sao_Paulo)' / 'resets 7pm' -> segundos até lá (+90 s de folga); sem horário legível = 30 min."""
    mm = re.search(r"resets\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", msg, re.I)
    if not mm:
        return 1800
    h, mi, ap = int(mm.group(1)), int(mm.group(2) or 0), (mm.group(3) or "").lower()
    if ap == "pm" and h < 12: h += 12
    if ap == "am" and h == 12: h = 0
    agora = time.localtime()
    alvo = time.mktime((agora.tm_year, agora.tm_mon, agora.tm_mday, h, mi, 0, 0, 0, -1))
    if alvo <= time.time():
        alvo += 86400
    return min(max(alvo - time.time() + 90, 60), 6 * 3600)


def main():
    job = Job(os.path.abspath(sys.argv[1])); c = job.cfg
    job.status(estado="decidindo destino", pid=os.getpid(), inicio=now())
    import destino as de
    env = de.ambiente()
    dest, why = de.decidir(c.get("destino", "auto"), env)
    if not dest:
        job.log("erro", why); job.status(estado="erro", erro=why); return
    if dest == "filmcraft":
        import filmcraft as fc
        try: fc.ensure(log=lambda m: job.log("info", m))
        except Exception as e: job.log("erro", "FilmCraft: %s" % e); job.status(estado="erro", erro=str(e)); return
    job.log("info", "Destino: %s — %s" % ("Premiere" if dest == "premiere" else "FilmCraft", why))
    job.status(estado="editando", destino=dest, motivo=why)
    nome = c.get("nome") or "EDICAO_" + os.path.splitext(os.path.basename(c["video"]))[0][:40]
    fmt = dict(video=c["video"], job=job.d, destino=dest.upper(), motivo=why, nome=nome, notas=c.get("notas") or "(nenhuma)", sk=SK)
    fmt["montagem"] = (MONT_FC if dest == "filmcraft" else MONT_PR).format(**fmt)
    fmt["cine"] = CINE_ON.format(**fmt) if c.get("cinematicas", True) else "DESLIGADAS nesta edição (o Matheus desmarcou): não gere cinemáticas."
    prompt = PROMPT.format(**fmt)
    open(os.path.join(job.d, "prompt.txt"), "w", encoding="utf8").write(prompt)
    import shutil
    exe = shutil.which("claude") or "claude"
    cmd = [exe, "-p", "--output-format", "stream-json", "--verbose",                       # o prompt vai pelo stdin (sem problema de aspas/quebras)
           "--permission-mode", "acceptEdits", "--allowedTools", "Bash,Read,Write,Edit,Glob,Grep,Skill,TodoWrite",
           "--add-dir", os.path.dirname(os.path.abspath(c["video"])), "--add-dir", SK,
           "--add-dir", os.path.join(os.path.dirname(SK), "minecraft-cinematic")]          # cinemáticas (regra 20): referências e exemplos
    if c.get("modelo"): cmd += ["--model", c["modelo"]]
    flags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
    sess, custo, retomadas, texto = None, 0.0, 0, prompt
    while True:                                   # 21/10: limite de uso da conta -> espera o reset e retoma a MESMA sessão (--resume)
        run_cmd = cmd + (["--resume", sess] if retomadas and sess else [])
        p = subprocess.Popen(run_cmd, cwd=job.d, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, creationflags=flags,
                             shell=exe.lower().endswith((".cmd", ".bat")))
        p.stdin.write(texto.encode("utf8")); p.stdin.close()
        job.status(claude_pid=p.pid)
        limite = None
        for raw in p.stdout:
            line = raw.decode("utf8", "replace").strip()
            if not line: continue
            try: m = json.loads(line)
            except ValueError: job.log("saida", line); continue
            sess = m.get("session_id") or sess
            t = m.get("type")
            if t == "assistant":
                for b in (m.get("message") or {}).get("content", []):
                    if b.get("type") == "text" and b.get("text", "").strip():
                        job.log("claude", b["text"].strip())
                        if LIMITE.search(b["text"]): limite = b["text"]
                    elif b.get("type") == "tool_use":
                        inp = b.get("input") or {}
                        det = inp.get("description") or inp.get("command") or inp.get("file_path") or inp.get("skill") or ""
                        job.log("ferramenta", "%s: %s" % (b.get("name"), str(det)[:220]))
            elif t == "result":
                custo += m.get("total_cost_usd") or 0.0
                r = m.get("result") or ""
                job.log("fim", r[:1500])
                if LIMITE.search(r): limite = r
                job.status(custo_usd=round(custo, 2), turnos=m.get("num_turns"), erro_claude=bool(m.get("is_error")), sessao=sess)
        rc = p.wait()
        if limite and sess and retomadas < 8:
            espera = segundos_ate_reset(limite)
            volta = time.strftime("%H:%M", time.localtime(time.time() + espera))
            job.log("info", "Limite de uso da conta Claude atingido. Espero até %s e continuo a mesma sessão de onde parou." % volta)
            job.status(estado="aguardando limite", retoma=volta)
            time.sleep(espera)
            retomadas += 1
            texto = ("O limite de uso da conta acabou de resetar. Continue este job exatamente de onde parou: antes de refazer qualquer etapa, "
                     "confira na pasta do job o que já está pronto (transcrições, plan3.json, cine/*.mp4, projeto). Vá até o fim: projeto montado, "
                     "conferido e RESUMO.md.")
            job.status(estado="editando", retoma=None)
            continue
        break
    if rc:
        job.log("erro", "Claude Code terminou com código %d" % rc); job.status(estado="erro", erro="claude saiu com %d" % rc); return
    res = None
    if dest == "filmcraft":
        fcp = os.path.join(job.d, nome + ".fcproj")
        if os.path.exists(fcp):
            res = fcp
            if c.get("abrir", True):
                import filmcraft as fc
                fc.open_app(fcp); job.log("info", "Abrindo no FilmCraft: " + fcp)
    else:
        pj = os.path.join(job.d, "premiere.json")
        res = json.load(open(pj, encoding="utf8")).get("projeto") if os.path.exists(pj) else None
        job.log("info", "Pronto no Premiere: " + str(res))
    job.status(estado="pronto" if res else "terminado sem projeto", resultado=res, fim=now())


if __name__ == "__main__":
    try: main()
    except Exception as e:
        try: Job(os.path.abspath(sys.argv[1])).status(estado="erro", erro=repr(e)[:500])
        except Exception: pass
        raise
