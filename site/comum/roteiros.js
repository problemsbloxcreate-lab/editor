/* Estúdio Problems: dados dos roteiros, usados pelas páginas Roteiro, Gravação e Produção.
   Os roteiros da passagem ficam em roteiros/roteiros.json. Os escritos ou mudados aqui ficam neste navegador
   e, com a senha da equipe, também na nuvem da equipe (Worker sons-problems: /rot/todos, /rot, /sit), para todos verem. */
(function () {
	const RAIZ = new URL("../", document.currentScript.src).href;
	const K_MEUS = "ep:roteiros:meus", K_SIT = "ep:roteiros:status", K_SITQ = "ep:roteiros:status-quando";

	const SITUACOES = [
		["novos", "⏳ Novos roteiros"], ["faltando", "❓ Materiais faltando"], ["aprovado", "🟢 Aprovados"],
		["gravando", "🎙 Gravando"], ["animado", "🎬 Animando no estúdio"], ["postados", "✅ Postados"], ["negados", "💀 Negados"],
	];
	/* cor do nome no Doc e cor da legenda no vídeo */
	const CORES = {
		problems: ["#00ffff", "#19f0f0"], kadu: ["#ff0000", "#ff4040"], kadukos: ["#ff0000", "#ff4040"], stick: ["#00ff00", "#41e05a"],
		mel: ["#ffff00", "#ffe23b"], verity: ["#ffff00", "#ffe23b"], zoom: ["#ff9900", "#ff9a1f"], brucutu: ["#93c47d", "#ffffff"],
		vampira: ["#9900ff", "#c07bff"], jujubinha: ["#ff00ff", "#ff7be0"], melzinha: ["#ff00ff", "#ff7be0"], nissan: ["#ff00ff", "#ff7be0"],
		todos: ["#d9d9d9", "#ffffff"],
	};
	const TURMA = ["Problems", "Kadu", "Stick", "Mel", "Zoom", "Brucutu", "Vampira", "Jujubinha", "Verity", "Todos"];
	const chave = (w) => (w || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").split(/[\s(]/)[0];
	const corDoc = (w) => (CORES[chave(w)] || ["#d9d9d9"])[0];

	const ler = (k, p) => { try { const v = localStorage.getItem(k); return v ? JSON.parse(v) : p; } catch (e) { return p; } };
	const gravar = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} };

	const palavras = (s) => (s || "").split(/\s+/).filter(Boolean).length;
	const durFala = (f) => { const p = palavras(f.text); if (!p) return f.tela ? 1.5 : 0; return Math.max(1.2, p / 2.7 + 0.35); };
	const durTotal = (r) => r.falas.reduce((s, f) => s + durFala(f), 0);
	const mmss = (s) => `${Math.floor(s / 60)}:${String(Math.round(s % 60)).padStart(2, "0")}`;

	let base = null;
	const daPassagem = () => (base = base || fetch(RAIZ + "roteiros/roteiros.json").then((r) => r.json()).then((d) => d.roteiros).catch(() => []));

	/* ---------- nuvem da equipe ---------- */
	const NUVEM = { url: null, estado: "fora" }; // estado: ok | sem-senha | fora
	const senha = () => { try { return localStorage.getItem("estudio.senhaSons") || ""; } catch (e) { return ""; } };
	function definirSenha(s) { try { localStorage.setItem("estudio.senhaSons", s); } catch (e) {} }
	let urlP = null;
	const urlNuvem = () => (urlP = urlP || fetch(RAIZ + "dados/sons-url.json", { cache: "no-store" }).then((r) => r.ok ? r.json() : {}).then((d) => String(d.url || "").replace(/\/$/, "")).catch(() => ""));
	async function nuvem(caminho, op = {}) {
		const u = await urlNuvem(); if (!u) { NUVEM.estado = "fora"; return null; }
		if (!senha()) { NUVEM.estado = "sem-senha"; return null; }
		const ctl = new AbortController(), tm = setTimeout(() => ctl.abort(), op.tempo || 6000);
		try {
			const r = await fetch(u + caminho, { ...op, signal: ctl.signal, headers: { ...(op.headers || {}), "x-senha": senha(), "content-type": "application/json" } });
			if (r.status === 401) { NUVEM.estado = "sem-senha"; NUVEM.erro = "senha da equipe errada"; return null; }
			if (!r.ok) { NUVEM.estado = "fora"; NUVEM.erro = ((await r.json().catch(() => ({}))).erro || "o servidor respondeu " + r.status); return null; }
			NUVEM.erro = "";
			NUVEM.estado = "ok"; return await r.json();
		} catch (e) { NUVEM.estado = "fora"; NUVEM.erro = "não consegui falar com o servidor"; return null; } finally { clearTimeout(tm); }
	}
	const pendentes = {}; // id -> timer (salva na nuvem alguns segundos depois da última mudança)
	function subir(r) {
		clearTimeout(pendentes[r.id]);
		pendentes[r.id] = setTimeout(async () => { delete pendentes[r.id];
			const ok = await nuvem("/rot?id=" + encodeURIComponent(r.id), { method: "PUT", body: JSON.stringify(r) });
			if (ok) { const meus = ler(K_MEUS, []), x = meus.find((m) => m.id === r.id); if (x && x.atualizado === r.atualizado) { x.naNuvem = true; gravar(K_MEUS, meus); } }
		}, 4000);
	}
	/* junta o que está na nuvem com o deste navegador: vale o mais recente */
	async function sincronizar() {
		const d = await nuvem("/rot/todos"); if (!d) return false;
		const meus = ler(K_MEUS, []), porId = new Map(meus.map((r) => [r.id, r])), daNuvem = new Set();
		for (const r of d.roteiros || []) {
			daNuvem.add(r.id); const l = porId.get(r.id);
			if (!l || (r.atualizado || 0) > (l.atualizado || 0)) porId.set(r.id, Object.assign({}, r, { meu: true, naNuvem: true }));
			else if ((l.atualizado || 0) > (r.atualizado || 0)) subir(l);
		}
		for (const [id, l] of porId) if (!daNuvem.has(id)) { if (l.naNuvem) porId.delete(id); else subir(l); } // apagado por alguém / ainda não subiu
		gravar(K_MEUS, [...porId.values()].sort((a, b) => (b.atualizado || 0) - (a.atualizado || 0)));
		const sit = ler(K_SIT, {}), q = ler(K_SITQ, {});
		for (const [id, v] of Object.entries(d.sit || {})) if ((v.quando || 0) > (q[id] || 0)) { sit[id] = v.s; q[id] = v.quando; }
		for (const [id, s] of Object.entries(sit)) if (!d.sit?.[id] || (q[id] || 0) > (d.sit[id].quando || 0)) nuvem("/sit?id=" + encodeURIComponent(id), { method: "PUT", body: JSON.stringify({ s, quando: q[id] || Date.now() }) });
		gravar(K_SIT, sit); gravar(K_SITQ, q);
		return true;
	}
	addEventListener("pagehide", () => { for (const id of Object.keys(pendentes)) { clearTimeout(pendentes[id]); const r = ler(K_MEUS, []).find((x) => x.id === id); if (r && urlP) urlNuvem().then((u) => u && senha() && fetch(u + "/rot?id=" + encodeURIComponent(id), { method: "PUT", keepalive: true, body: JSON.stringify(r), headers: { "x-senha": senha(), "content-type": "application/json" } })); } });

	async function todos() {
		const doc = await daPassagem();
		await sincronizar();
		const sit = ler(K_SIT, {});
		/* o que foi editado aqui substitui a versão da passagem (mesmo id) */
		const meus = ler(K_MEUS, []), ids = new Set(meus.map((r) => r.id));
		return [...meus, ...doc.filter((r) => !ids.has(r.id))].map((r) => Object.assign({}, r, { status: sit[r.id] || r.status }));
	}
	async function um(id) { return (await todos()).find((r) => r.id === id) || null; }
	function mudarSituacao(id, s) {
		const st = ler(K_SIT, {}), q = ler(K_SITQ, {}); st[id] = s; q[id] = Date.now(); gravar(K_SIT, st); gravar(K_SITQ, q);
		nuvem("/sit?id=" + encodeURIComponent(id), { method: "PUT", body: JSON.stringify({ s, quando: q[id] }) });
	}
	function salvarMeu(r) {
		const meus = ler(K_MEUS, []);
		const novo = Object.assign({}, r, { meu: true, atualizado: Date.now(), naNuvem: false });
		const i = meus.findIndex((x) => x.id === r.id);
		if (i >= 0) meus[i] = novo; else meus.unshift(novo);
		gravar(K_MEUS, meus); subir(novo);
	}
	function apagarMeu(id) { gravar(K_MEUS, ler(K_MEUS, []).filter((x) => x.id !== id)); clearTimeout(pendentes[id]); nuvem("/rot?id=" + encodeURIComponent(id), { method: "DELETE" }); }
	function vazio() {
		return { id: "meu-" + Date.now().toString(36), numero: 0, titulo: "", origem: "Escrito no estúdio", status: "novos", tema: "", potencial: "",
			legenda: "", edicao: "", ideia: "", pergunta: "", duracao: "", personagens: "", cenario: "", notas: "",
			falas: [{ who: "Problems", text: "", tela: "" }, { who: "Kadu", text: "", tela: "" }], cenasMinecraft: false, meu: true };
	}
	function exportarMeus() { return JSON.stringify({ tipo: "estudio-problems:roteiros", roteiros: ler(K_MEUS, []), situacao: ler(K_SIT, {}) }, null, 1); }
	function importarMeus(txt) {
		const d = JSON.parse(txt);
		if (d.tipo !== "estudio-problems:roteiros" || !Array.isArray(d.roteiros)) throw new Error("esse arquivo não é uma cópia de roteiros do estúdio");
		const meus = ler(K_MEUS, []);
		for (const r of d.roteiros) { const i = meus.findIndex((x) => x.id === r.id); if (i >= 0) meus[i] = r; else meus.push(r); }
		gravar(K_MEUS, meus); gravar(K_SIT, Object.assign(ler(K_SIT, {}), d.situacao || {}));
		return d.roteiros.length;
	}

	/* corpo do roteiro no formato do Doc da equipe */
	function textoDoc(r) {
		const l = [r.titulo, ""];
		if (r.legenda) l.push("LEGENDA NA TELA: " + r.legenda);
		if (r.edicao) l.push("EDIÇÃO: " + r.edicao);
		if (r.legenda || r.edicao) l.push("");
		for (const f of r.falas) { if (f.who && f.text) l.push(`${f.who}: ${f.text}`); if (f.tela) l.push("    [comentário] " + f.tela); }
		return l.join("\n");
	}
	function textoTabela(r) {
		const o = ["# " + (r.titulo || "Sem título"), ""];
		[["Ideia (até 10 palavras)", r.ideia], ["A pergunta que o menino segura", r.pergunta], ["Duração alvo", r.duracao || `~${Math.round(durTotal(r))} s`],
			["Personagens", r.personagens || [...new Set(r.falas.map((f) => f.who).filter(Boolean))].join(", ")], ["Cenário", r.cenario]]
			.forEach(([k, v]) => o.push(`- **${k}:** ${v || ""}`));
		if (r.legenda) o.push("- **LEGENDA NA TELA:** " + r.legenda);
		if (r.edicao) o.push("- **EDIÇÃO:** " + r.edicao);
		o.push("", "| # | Tempo | TELA (o que o animador mostra) | QUEM | FALA |", "|---|---|---|---|---|");
		let t = 0;
		const cel = (s) => (s || "").replace(/\|/g, "/").replace(/\n/g, " ");
		r.falas.forEach((f, i) => { o.push(`| ${i + 1} | ${mmss(t)} | ${cel(f.tela)} | ${f.who || "—"} | ${cel(f.text)} |`); t += durFala(f); });
		if (r.notas) o.push("", "## Notas para o editor", r.notas);
		return o.join("\n");
	}

	/* lê um roteiro colado: tabela da skill /roteiro, corpo do Doc (Personagem: fala) ou formato dos 15 */
	function importarTexto(txt) {
		const r = vazio(); r.origem = "Colado no estúdio"; r.falas = [];
		const limpa = (s) => s.replace(/\*\*(.+?)\*\*/g, "$1").replace(/(^|\s)_(.+?)_(?=\s|$|[.,!?])/g, "$1$2").trim();
		const campo = (re) => { for (const ln of txt.split("\n")) { const l = ln.replace(/^\s*-\s*/, "").replace(/\*\*/g, ""); const m = l.match(new RegExp("^" + re + "[^:]*:\\s*(.*)$", "i")); if (m) return m[1].trim(); } return ""; };
		const linhas = txt.replace(/\r/g, "").split("\n");
		const t1 = linhas.find((l) => /^#\s+/.test(l)); r.titulo = t1 ? t1.replace(/^#\s+/, "").trim() : "";
		r.ideia = campo("Ideia"); r.pergunta = campo("A pergunta que o menino segura"); r.duracao = campo("Dura[cç][aã]o alvo");
		r.personagens = campo("Personagens"); r.cenario = campo("Cen[aá]rio"); r.tema = campo("Tema");
		r.legenda = campo("LEGENDA NA TELA"); r.edicao = campo("EDI[CÇ][AÃ]O");
		const tab = linhas.filter((l) => /^\s*\|/.test(l) && !/^\s*\|\s*-/.test(l) && !/^\s*\|\s*#\s*\|/.test(l));
		const turma = new Set(TURMA.map((n) => n.toLowerCase()).concat(["kadukos", "noob", "melzinha", "nissan"]));
		if (tab.length >= 2) {
			for (const l of tab) {
				const c = l.trim().replace(/^\||\|$/g, "").split("|").map((x) => x.trim());
				if (c.length < 5) continue;
				const [, , tela, quem, fala] = c;
				if (!quem || /^[—-]$/.test(quem)) r.falas.push({ who: "", text: "", tela: limpa(tela + " " + fala) });
				else r.falas.push({ who: quem, text: limpa(fala), tela: limpa(tela) });
			}
		} else {
			let primeira = true;
			for (const ln0 of linhas) {
				const ln = ln0.trim(); if (!ln) continue;
				if (/^#/.test(ln) || /^-\s*\*\*/.test(ln) || /^(LEGENDA NA TELA|EDI[CÇ][AÃ]O|Refer[eê]ncia)\s*:/i.test(ln)) { primeira = false; continue; }
				const com = ln.match(/^(?:>\s*|\[coment[aá]rio\]\s*)(.+)$/i);
				if (com) { const u = r.falas[r.falas.length - 1]; if (u) u.tela = (u.tela + " " + limpa(com[1])).trim(); else r.falas.push({ who: "", text: "", tela: limpa(com[1]) }); continue; }
				const m = ln.replace(/\*\*/g, "").match(/^([A-Za-zÀ-ÿ ]{2,24}?)\s*(\([^)]*\))?\s*:\s*(.+)$/);
				const nome = m ? m[1].trim() : "";
				if (m && (turma.has(nome.toLowerCase()) || /^[A-ZÀ-Ý]/.test(nome)) && !/^editor|^cenista/i.test(nome)) r.falas.push({ who: nome, text: limpa(m[3]), tela: m[2] ? m[2].replace(/[()]/g, "") : "" });
				else if (primeira && !r.titulo) r.titulo = limpa(ln.replace(/^=+\s*ABA:\s*|\s*=+$/g, ""));
				else r.falas.push({ who: "", text: "", tela: limpa(ln) });
				primeira = false;
			}
		}
		if (!r.titulo) r.titulo = "Roteiro colado";
		if (!r.falas.length) r.falas = vazio().falas;
		return r;
	}

	const REGRAS = `Regras do canal Problems (Shorts animados de Minecraft para meninos de ~9 anos, no celular, às vezes sem som):
- A ideia cabe em 10 palavras e tem uma pergunta que o menino segura até o fim.
- O primeiro frame já mostra o problema. Cada fala faz ele querer a próxima; antes de ele pensar "já entendi", abra uma pergunta nova.
- Falas naturais e encadeadas ("mas", "porque", "então", "é aí que"), palavras simples. O Problems explica com calma; o Kadu reage curto e debochado e chama ele de "Problems".
- Números e objetos concretos ("100 baús", "3 segundos"), nunca "vários".
- Regras reais do Minecraft. O final fecha a pergunta com a lógica da própria história. Nada de "era sonho" ou "era pegadinha".
- Texto na tela sempre que o problema precisar ser entendido sem som.`;
	const FORMATO = `Responda só com o roteiro neste formato (eu colo de volta no Estúdio Problems):
# <Título>
- **Ideia (até 10 palavras):**
- **A pergunta que o menino segura:**
- **Duração alvo:**
- **Personagens:**
- **Cenário:**
- **LEGENDA NA TELA:**
- **EDIÇÃO:**

| # | Tempo | TELA (o que o animador mostra) | QUEM | FALA |
|---|---|---|---|---|
| 1 | 0:00 | ... | ... | ... |`;
	function pedido(tipo, r, ideia) {
		if (tipo === "escrever") return `/roteiro ${ideia || ""}\n\n(Se você não estiver na pasta "Canal Problems - passagem pro Claude", siga isto:)\n${REGRAS}\n\n${FORMATO}`;
		return `/revisar\n\nRevise este roteiro fala por fala, como o menino de 9 anos que está rolando o feed. Diga onde ele sairia e reescreva essas falas. No fim, devolva o roteiro inteiro corrigido.\n\n${REGRAS}\n\n${FORMATO}\n\nRoteiro:\n${textoTabela(r)}`;
	}

	/* barra de etapas do aplicativo Shorts: Produção → Roteiro → Gravação → Shorts (o estúdio de cenas).
	   A Edição (vídeos longos) é outro aplicativo; os dois se escolhem na entrada (inicio/), pelo ⌂. */
	function etapas(atual, id) {
		const q = id ? "?r=" + encodeURIComponent(id) : "";
		const itens = [["producao", "Produção", RAIZ + "producao/"], ["roteiro", "Roteiro", RAIZ + "roteiro/" + q], ["gravacao", "Gravação", RAIZ + "gravacao/" + q], ["video", "Shorts", RAIZ + "?app=shorts"]];
		return '<nav class="etapas" aria-label="Etapas">' + `<a href="${RAIZ}inicio/" title="Início: Shorts ou Edição" aria-label="Início">⌂</a><i>·</i>` + itens.map(([k, n, href], i) =>
			(i ? "<i>›</i>" : "") + `<a href="${href}"${k === atual ? ' class="on" aria-current="page"' : ""}><b>${i + 1}</b>${n}</a>`).join("") + "</nav>";
	}
	const esc = (s) => String(s == null ? "" : s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
	function copiar(t) { return navigator.clipboard.writeText(t).then(() => true, () => false); }
	function baixar(nome, texto) {
		const a = document.createElement("a");
		a.href = URL.createObjectURL(new Blob([texto], { type: "text/plain;charset=utf-8" }));
		a.download = nome; a.click(); setTimeout(() => URL.revokeObjectURL(a.href), 2000);
	}
	const slug = (s) => (s || "roteiro").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 40);

	window.ROTEIROS = { RAIZ, SITUACOES, TURMA, corDoc, durFala, durTotal, mmss, palavras, todos, um, mudarSituacao, salvarMeu, apagarMeu, vazio,
		exportarMeus, importarMeus, textoDoc, textoTabela, importarTexto, pedido, etapas, esc, copiar, baixar, slug, ler, gravar,
		NUVEM, sincronizar, definirSenha, temSenha: () => !!senha(), nuvem };
})();
