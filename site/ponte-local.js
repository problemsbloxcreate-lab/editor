/* Ponte com o "Estúdio Problems Local" (serviço instalado no PC da pessoa, http://127.0.0.1:4790).
   Edita o vídeo NO PC de quem está usando, com a skill minecraft-video-editor (a mesma do PC do dono): Premiere ou FilmCraft,
   CineCam, músicas e SFX locais, conta do Claude daquele PC.
   - "Editar no meu PC": manda só o NOME e o TAMANHO do bruto; o serviço acha o arquivo nas pastas de gravação e roda a skill inteira.
   - "Montar este plano no meu PC": manda o plano que o Claude da nuvem fez aqui (+ os clipes da V1) para virar projeto do Premiere/FilmCraft.
   Segurança: o serviço só aceita esta origem e um passe do porteiro (GET /passe-local, 2 min, só para 127.0.0.1) trocado por
   uma sessão local de 12 h. Sem passe não há ponte: não existe senha nem "modo teste". */
(function () {
	"use strict";
	const LOCAL = "http://127.0.0.1:4790";
	const $ = (s) => document.querySelector(s);
	const esc = (t) => String(t == null ? "" : t).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
	let sessao = sessionStorage.getItem("ep-local-sessao") || "", ativo = false, jobAtual = null, desde = 0, timer = 0;

	async function local(caminho, op) {
		op = Object.assign({ headers: {} }, op || {});
		op.headers = Object.assign({ "x-ep-sessao": sessao }, op.headers);
		const r = await fetch(LOCAL + caminho, op);
		const j = await r.json().catch(() => ({}));
		if (r.status === 401 && caminho !== "/api/sessao") { sessao = ""; sessionStorage.removeItem("ep-local-sessao"); throw Object.assign(new Error(j.erro || "sem autorização"), { auth: true }); }
		if (!r.ok) throw new Error(j.erro || "erro " + r.status);
		return j;
	}

	async function entrar() {
		if (sessao) return true;
		const r = await fetch("/passe-local", { credentials: "include", cache: "no-store" });       // porteiro (mesma origem)
		if (!r.ok) throw new Error(r.status === 404 ? "o porteiro ainda não tem a rota /passe-local" : "entre pelo menu do Estúdio de novo (" + r.status + ")");
		const { passe } = await r.json();
		const s = await local("/api/sessao", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ passe }) });
		sessao = s.sessao; sessionStorage.setItem("ep-local-sessao", sessao);
		return true;
	}

	async function comSessao(fn) {
		try { await entrar(); return await fn(); }
		catch (e) { if (!e.auth) throw e; await entrar(); return await fn(); }
	}

	function msg(t, tipo) { const el = $("#plMsg"); if (el) { el.innerHTML = t; el.className = "status" + (tipo ? " " + tipo : ""); } }

	function bruto() {
		const P = window.ED && ED.P; if (!P) return null;
		const v1 = P.clipes.filter((c) => c.faixa === "V1" && !c.off).sort((a, b) => a.ini - b.ini);
		const m = v1.length && P.midias[v1[0].midia];
		return m ? { nome: m.nome, tamanho: m.tam || null, v1 } : null;
	}

	async function acharBruto() {
		const b = bruto(); if (!b) throw new Error("abra o bruto primeiro");
		const r = await local("/api/localizar", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ nome: b.nome, tamanho: b.tamanho }) });
		if (!r.arquivos.length) throw new Error("não achei <b>" + esc(b.nome) + "</b> nas pastas de gravação deste PC (Vídeos, Área de Trabalho, Downloads e a pasta de trabalho). Copie o bruto para uma delas e tente de novo.");
		if (r.arquivos.length === 1) return r.arquivos[0];
		const i = prompt("Achei mais de um arquivo igual. Qual uso?\n" + r.arquivos.map((a, k) => k + 1 + ") " + a).join("\n"), "1");
		const a = r.arquivos[(parseInt(i, 10) || 1) - 1]; if (!a) throw new Error("cancelado"); return a;
	}

	async function mandar(comPlano) {
		const bt = comPlano ? $("#plMontar") : $("#plEditar"); bt.disabled = true;
		try {
			await comSessao(async () => {
				const est = await local("/api/estado");
				if (est.conta && !est.conta.logado) throw new Error("o Claude Code deste PC não está logado: abra um terminal, rode <b>claude</b> e entre com a conta da equipe");
				if ((est.outros_pcs || []).length && !confirm("A conta Claude deste PC (" + (est.conta.email || "?") + ") já está editando em " + est.outros_pcs.map((x) => x.pc).join(", ") + ". O limite de uso é dividido entre os dois. Começar mesmo assim?")) throw new Error("cancelado");
				msg("Procurando o bruto neste PC…");
				const video = await acharBruto();
				const pedido = { video, destino: $("#plDestino").value, cinematicas: $("#plCine").checked, notas: $("#plNotas").value, origem: "estudio" };
				if (comPlano) {
					const u = ED.P.ultimoPlano; if (!u) throw new Error("ainda não há plano do Claude neste projeto");
					pedido.plano_web = { plano: u.plano, clipes: u.clipes, vozes: u.vozes };
				}
				const r = await local("/api/job", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(pedido) });
				jobAtual = r.id; desde = 0; ED.P.jobLocal = jobAtual; ED.salvarLogo && ED.salvarLogo();
				msg("Começou no seu PC. Pode fechar esta aba: a edição continua lá."); acompanhar();
			});
		} catch (e) { msg("Não deu: " + (e.message || e), "err"); }
		bt.disabled = false;
	}

	function acompanhar() {
		clearInterval(timer);
		timer = setInterval(async () => {
			if (!jobAtual) return clearInterval(timer);
			try {
				const r = await comSessao(() => local("/api/job/" + encodeURIComponent(jobAtual) + "?desde=" + desde));
				desde += r.eventos.length;
				const ult = r.eventos.filter((e) => e.tipo === "claude" || e.tipo === "info" || e.tipo === "erro").pop();
				const st = r.status || {};
				if (ult) $("#plLog").textContent = String(ult.texto || ult.msg || "").slice(0, 400);
				const est = st.estado || "…";
				if (est === "aguardando limite") msg("A conta do Claude deste PC chegou no limite; continua sozinha às " + esc(st.retoma || "?") + ".", "warn");
				else if (est === "pronto") { clearInterval(timer); msg("Pronto no seu PC" + (st.destino ? " (" + esc(st.destino) + ")" : "") + ". <button class='btn small' id='plAbrir'>Abrir</button>", "ok"); $("#plAbrir").onclick = () => comSessao(() => local("/api/job/" + jobAtual + "/abrir", { method: "POST" })); if (r.resumo) $("#plLog").textContent = r.resumo.slice(0, 1200); }
				else if (est === "erro" || est === "parado" || est === "terminado sem projeto") { clearInterval(timer); msg("Terminou: " + esc(est) + (st.erro ? " — " + esc(st.erro) : ""), "err"); }
				else msg("No seu PC: " + esc(est) + (st.destino ? " · " + esc(st.destino) : ""));
			} catch (e) { msg("Perdi o contato com o serviço local: " + esc(e.message || e), "err"); }
		}, 4000);
	}

	function painel() {
		const auto = document.querySelector('[data-painel="auto"]'); if (!auto || $("#plCard")) return;
		const c = document.createElement("div"); c.className = "card"; c.id = "plCard";
		c.innerHTML = `<p class="sub-h">4 · No meu PC (Premiere / FilmCraft)</p>
<p class="hint" id="plHint">Procurando o Estúdio Problems Local neste computador…</p>
<div id="plCorpo" hidden>
  <div class="linha"><div class="campo"><span>Montar em</span><select id="plDestino"><option value="auto">Automático</option><option value="premiere">Premiere</option><option value="filmcraft">FilmCraft</option></select></div>
  <label class="campo" style="flex-direction:row;align-items:center;gap:6px"><input type="checkbox" id="plCine" checked> Cinemáticas</label></div>
  <div class="campo"><span>Notas para o Claude do seu PC</span><textarea id="plNotas" rows="2"></textarea></div>
  <div class="linha"><button class="btn primary" type="button" id="plEditar">Editar no meu PC</button><button class="btn" type="button" id="plMontar" title="Monta no Premiere/FilmCraft o plano que o Claude fez aqui">Montar este plano no meu PC</button></div>
  <p class="status" id="plMsg"></p><pre class="hint" id="plLog" style="white-space:pre-wrap;max-height:180px;overflow:auto"></pre>
</div>`;
		auto.appendChild(c);
		$("#plEditar").onclick = () => mandar(false);
		$("#plMontar").onclick = () => mandar(true);
	}

	async function detectar() {
		painel();
		try {
			const r = await fetch(LOCAL + "/api/ping", { cache: "no-store" });
			const j = await r.json();
			ativo = j.servico === "estudio-problems-local";
		} catch (_) { ativo = false; }
		const h = $("#plHint"); if (!h) return;
		if (!ativo) { h.innerHTML = "O Estúdio Problems Local não está rodando neste PC. Instale pelo menu do Estúdio (Editor › Instalar no meu PC) ou abra-o. No Chrome/Edge, se aparecer o pedido de acesso à <b>rede local</b>, permita para este site."; return; }
		h.textContent = "Estúdio Problems Local encontrado (versão " + (await fetch(LOCAL + "/api/ping").then((r) => r.json()).then((j) => j.versao).catch(() => "?")) + ").";
		$("#plCorpo").hidden = false;
		try { const est = await comSessao(() => local("/api/estado")); h.textContent += est.conta && est.conta.email ? " Conta Claude: " + est.conta.email + (est.midia ? " · mídia " + est.midia : "") : " Claude Code sem login neste PC."; } catch (_) {}
		const P = window.ED && ED.P;
		$("#plMontar").disabled = !(P && P.ultimoPlano);
		if (P && P.jobLocal && !jobAtual) { jobAtual = P.jobLocal; acompanhar(); }
	}

	addEventListener("DOMContentLoaded", () => setTimeout(detectar, 600));
	document.addEventListener("click", (e) => { if (e.target.closest && e.target.closest('[data-aba="auto"], [data-painel-btn="auto"]')) setTimeout(detectar, 50); });
	window.PONTE_LOCAL = { detectar };
})();
