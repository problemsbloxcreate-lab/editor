/* Ponte com o "Estúdio Problems Local" (serviço instalado no PC da pessoa, http://127.0.0.1:4790).
   Edita o vídeo NO PC de quem está usando, com a skill minecraft-video-editor (a mesma do PC do dono): Premiere ou FilmCraft,
   CineCam, músicas e SFX locais, conta do Claude daquele PC.
   - "Editar no meu PC": manda só o NOME e o TAMANHO do bruto; o serviço acha o arquivo nas pastas de gravação e roda a skill inteira.
   - "Montar este plano no meu PC": manda o plano que o Claude da nuvem fez aqui (+ os clipes da V1) para virar projeto do Premiere/FilmCraft.
   Como chega lá (23/10/2026): o site NÃO chama o 127.0.0.1 por baixo (o Chrome/Brave/Safari bloqueiam ou pedem permissão de
   "rede local"). Ele abre a página do serviço numa ABA NOVA com o pedido no #fragmento (não vai para servidor nenhum) junto com um
   passe do porteiro (GET /passe-local, 2 min, só para 127.0.0.1, uso único). A página local confere o passe e só começa depois do
   clique de confirmação lá. Não existe senha nem "modo teste". */
(function () {
	"use strict";
	const LOCAL = "http://127.0.0.1:4790";
	const $ = (s) => document.querySelector(s);
	const b64u = (s) => { const b = new TextEncoder().encode(s); let t = ""; for (let i = 0; i < b.length; i += 0x8000) t += String.fromCharCode.apply(null, b.subarray(i, i + 0x8000)); return btoa(t).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, ""); };

	function msg(t, tipo) { const el = $("#plMsg"); if (el) { el.innerHTML = t; el.className = "status" + (tipo ? " " + tipo : ""); } }

	function bruto() {
		const P = window.ED && ED.P; if (!P) return null;
		const v1 = P.clipes.filter((c) => c.faixa === "V1" && !c.off).sort((a, b) => a.ini - b.ini);
		const m = v1.length && P.midias[v1[0].midia];
		return m ? { nome: m.nome, tamanho: m.tam || null } : null;
	}

	async function mandar(comPlano) {
		const b = bruto();
		if (!b) { msg("Abra o bruto primeiro.", "err"); return; }
		const u = ED.P.ultimoPlano;
		if (comPlano && !u) { msg("Ainda não há plano do Claude neste projeto.", "err"); return; }
		const aba = window.open("about:blank", "_blank");                  // abre JÁ, no clique (senão o navegador bloqueia o pop-up)
		if (!aba) { msg("O navegador bloqueou a aba nova: permita pop-ups deste site e clique de novo.", "err"); return; }
		try { aba.opener = null; aba.document.title = "No meu PC…"; aba.document.body.textContent = "Abrindo o Estúdio Problems Local…"; } catch (_) {}
		try {
			const r = await fetch("/passe-local", { credentials: "include", cache: "no-store" });     // porteiro (mesma origem)
			if (!r.ok) throw new Error(r.status === 401 ? "entre pelo menu do Estúdio de novo" : "o porteiro respondeu " + r.status);
			const { passe } = await r.json();
			const pedido = { nome: b.nome, tamanho: b.tamanho, destino: $("#plDestino").value, cinematicas: $("#plCine").checked, notas: $("#plNotas").value };
			if (comPlano) pedido.plano_web = { plano: u.plano, clipes: u.clipes, vozes: u.vozes };
			aba.location.href = LOCAL + "/ponte#d=" + b64u(JSON.stringify({ passe, pedido }));
			msg("Abri a aba do Estúdio Problems Local: confirme lá. Se ela mostrar \"não foi possível acessar\", o serviço não está instalado ou ligado neste PC.");
		} catch (e) { try { aba.close(); } catch (_) {} msg("Não deu: " + (e.message || e), "err"); }
	}

	function painel() {
		const auto = document.querySelector('[data-painel="auto"]'); if (!auto || $("#plCard")) return;
		const c = document.createElement("div"); c.className = "card"; c.id = "plCard";
		c.innerHTML = `<p class="sub-h">4 · No meu PC (Premiere / FilmCraft)</p>
<p class="hint">Edita com o Estúdio Problems Local instalado neste computador (a skill do editor, a conta do Claude deste PC). Abre uma aba do serviço local para você confirmar.</p>
<div class="linha"><div class="campo"><span>Montar em</span><select id="plDestino"><option value="auto">Automático</option><option value="premiere">Premiere</option><option value="filmcraft">FilmCraft</option></select></div>
  <label class="campo" style="flex-direction:row;align-items:center;gap:6px"><input type="checkbox" id="plCine" checked> Cinemáticas</label></div>
<div class="campo"><span>Notas para o Claude do seu PC</span><textarea id="plNotas" rows="2"></textarea></div>
<div class="linha"><button class="btn primary" type="button" id="plEditar">Editar no meu PC</button><button class="btn" type="button" id="plMontar" title="Monta no Premiere/FilmCraft o plano que o Claude fez aqui">Montar este plano no meu PC</button></div>
<p class="status" id="plMsg"></p>`;
		auto.appendChild(c);
		$("#plEditar").onclick = () => mandar(false);
		$("#plMontar").onclick = () => mandar(true);
	}

	function atualizar() { painel(); const m = $("#plMontar"), P = window.ED && ED.P; if (m) m.disabled = !(P && P.ultimoPlano); }
	addEventListener("DOMContentLoaded", () => setTimeout(atualizar, 600));
	document.addEventListener("click", (e) => { if (e.target.closest && e.target.closest('[data-aba="auto"]')) setTimeout(atualizar, 50); });
	window.PONTE_LOCAL = { atualizar, mandar };
})();
