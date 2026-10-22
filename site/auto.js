/* Edição automática da aba Edição.
   1) Ritmo: porte do cutengine do editor (tighten2, ciente de quem fala): troca de falante = lacuna ~0,06 s; mesma pessoa = ~0,2 s;
      corte entra no começo da palavra; trecho curto (< 0,5 s) com fala não picota, sem fala some.
   2) Transcrição: Whisper no próprio navegador (o mesmo reconhecedor da aba Shorts), voz principal + call.
   3) Edição completa: manda a transcrição para o Claude (Action "Editar vídeo longo (Claude)") e aplica o plano que volta:
      cortes de repetição, zooms, efeitos, SFX (ganho fixo da tabela do editor), música por clima, mutes da call/jogo e marcadores. */
(function () {
	"use strict";
	const $ = (s) => document.querySelector(s), clamp = (v, a, b) => Math.max(a, Math.min(b, v));
	const HOP = 0.01;

	/* ---------- mapa de fala de uma faixa (RMS 10 ms) ---------- */
	function limiares(rms) {
		const v = Array.from(rms).filter((x) => x > -100).sort((a, b) => a - b);
		if (!v.length) return { on: -38, off: -46 };
		const p = (q) => v[Math.min(v.length - 1, Math.floor(q * v.length))];
		const on = clamp(Math.max(p(0.92) - 20, p(0.15) + 10), -48, -26);
		return { on, off: on - 8 };
	}
	function mascara(rms) {
		const { on, off } = limiares(rms), n = rms.length, m = new Uint8Array(n);
		for (let i = 0; i < n; i++) m[i] = rms[i] > on ? 1 : 0;
		for (let i = 1; i < n; i++) if (!m[i] && m[i - 1] && rms[i] > off) m[i] = 1;
		for (let i = n - 2; i >= 0; i--) if (!m[i] && m[i + 1] && rms[i] > off) m[i] = 1;
		// tira estalos isolados (< 60 ms)
		for (let i = 0; i < n;) { if (!m[i]) { i++; continue; } let j = i; while (j < n && m[j]) j++; if ((j - i) * HOP < 0.06) m.fill(0, i, j); i = j; }
		return m;
	}

	/* trechos a manter de [s0,s1) (tempo de fonte), cientes de quem fala */
	function manter(ms, s0, s1, opc) {
		opc = Object.assign({ troca: 0.06, mesma: 0.2, minCorte: 0.12, frag: 0.5, antes: 0.09, depois: 0.15 }, opc || {});
		ms = ms.filter(Boolean);
		const i0 = Math.max(0, Math.floor(s0 / HOP)), i1 = Math.min(Math.max(0, ...ms.map((m) => m.length)), Math.ceil(s1 / HOP));
		const quem = (i) => { let q = 0; for (let k = 0; k < ms.length && k < 30; k++) if (ms[k][i]) q |= 1 << k; return q; };
		// segmentos de fala (união das vozes)
		const segs = [];
		for (let i = i0; i < i1;) { if (!quem(i)) { i++; continue; } let j = i, q = 0; while (j < i1 && quem(j)) { q |= quem(j); j++; } segs.push({ a: i * HOP, b: j * HOP, q, qa: quem(i), qb: quem(j - 1) }); i = j; }
		if (!segs.length) return [];
		const keeps = [];
		let cur = { a: Math.max(s0, segs[0].a - opc.antes), b: 0 };
		for (let k = 0; k < segs.length; k++) {
			const s = segs[k], nx = segs[k + 1];
			if (!nx) { cur.b = Math.min(s1, s.b + opc.depois); keeps.push(cur); break; }
			const gap = nx.a - s.b, troca = !(s.qb & nx.qa);
			const alvo = troca ? opc.troca : opc.mesma;
			if (gap - alvo < opc.minCorte) continue; // pausa já curta: fica
			// sobra metade antes e metade depois (no começo da próxima palavra fica bem colado)
			const fim = s.b + Math.min(alvo * 0.55, 0.1), ini = nx.a - Math.max(alvo * 0.45, troca ? 0.02 : 0.08);
			cur.b = fim; keeps.push(cur); cur = { a: ini, b: 0 };
		}
		// fragmentos: < 0,5 s com fala desfaz o corte (junta com o próximo); sem fala some
		const temFala = (a, b) => { for (let i = Math.floor(a / HOP); i < Math.ceil(b / HOP); i++) if (quem(i)) return true; return false; };
		const out = [];
		for (let k = 0; k < keeps.length; k++) {
			const q = keeps[k];
			if (q.b - q.a < opc.frag) {
				if (!temFala(q.a, q.b)) continue;
				if (k + 1 < keeps.length) { keeps[k + 1].a = q.a; continue; }
				if (out.length) { out[out.length - 1].b = q.b; continue; }
			}
			out.push(q);
		}
		return out;
	}
	window.ED_CORTE = { mascara, manter, limiares };

	/* ---------- máscara de fala de cada personagem, já no tempo da linha do tempo ---------- */
	function rmsDoClipe(c) { const rt = ED.RT[c.midia]; if (!rt) return null; if (rt.buf) return rt.rms; const a = rt.aud && rt.aud[c.trilha || 0]; return a ? a.rms : null; }
	function vozesFala() { return ED.P.vozes.filter((v) => v.papel !== "jogo" && ED.ganhoFaixa(v.id) > 0); }
	function mascaraTL(vid, n) {
		const m = new Uint8Array(n), cache = new Map();
		for (const c of ED.P.clipes) {
			if (c.faixa !== vid || c.off) continue;
			const rms = rmsDoClipe(c); if (!rms) continue;
			if (!cache.has(rms)) cache.set(rms, mascara(rms));
			const ms = cache.get(rms), vel = c.vel || 1;
			const a = Math.max(0, Math.floor(c.ini / HOP)), b = Math.min(n, Math.ceil((c.ini + c.dur) / HOP));
			for (let i = a; i < b; i++) { const k = Math.floor((c.fonte + (i * HOP - c.ini) * vel) / HOP); if (ms[k]) m[i] = 1; }
		}
		return m;
	}
	/* corta trechos da linha do tempo em todas as faixas e puxa o resto (a música segue contínua) */
	function cortarTrechos(lista) {
		const P = ED.P;
		const iv = lista.filter((x) => x.b - x.a > 0.02).sort((x, y) => x.a - y.a), m = [];
		for (const x of iv) { if (m.length && x.a <= m[m.length - 1].b + 1e-6) m[m.length - 1].b = Math.max(m[m.length - 1].b, x.b); else m.push({ a: x.a, b: x.b }); }
		for (let q = m.length - 1; q >= 0; q--) {
			const { a, b } = m[q], d = b - a, novos = [];
			for (const c of P.clipes) {
				const e = c.ini + c.dur, vel = c.vel || 1;
				if (e <= a) { novos.push(c); continue; }
				if (c.ini >= b) { c.ini -= d; novos.push(c); continue; }
				if (c.faixa === "MUS" && c.ini < a) { c.dur = Math.max(0.2, c.dur - (Math.min(e, b) - a)); novos.push(c); continue; }
				if (c.ini < a) novos.push(Object.assign(JSON.parse(JSON.stringify(c)), { dur: a - c.ini }));
				if (e > b) novos.push(Object.assign(JSON.parse(JSON.stringify(c)), { id: ED.rid(), ini: a, dur: e - b, fonte: (c.fonte || 0) + (c.midia ? (b - c.ini) * vel : 0) }));
			}
			P.clipes = novos;
			for (const mk of P.marcadores) if (mk.t >= b) mk.t -= d; else if (mk.t > a) mk.t = a;
		}
		// religa os pedaços do bruto que ficaram com o mesmo trecho (vídeo + vozes andam juntos)
		const porTempo = {};
		for (const c of P.clipes) if ((c.faixa === "V1" || ED.ehVoz(c.faixa)) && c.midia) { const k = c.ini.toFixed(3) + "@" + c.dur.toFixed(3); (porTempo[k] = porTempo[k] || []).push(c); }
		for (const k in porTempo) { const l = ED.rid(); for (const c of porTempo[k]) c.link = l; }
		return m.reduce((x, y) => x + (y.b - y.a), 0);
	}
	function cortarSilencios() {
		const P = ED.P, T = ED.total(), vs = vozesFala();
		if (!T || !vs.length) { ED.aviso("Abra o bruto primeiro", "O corte de ritmo usa as faixas de voz dos personagens."); return; }
		const n = Math.ceil(T / HOP) + 1, masks = vs.map((v) => mascaraTL(v.id, n));
		if (!masks.some((m) => m.some(Boolean))) { ED.aviso("Não achei fala", "As faixas de voz estão em silêncio (ou marcadas como som do jogo)."); return; }
		const ks = manter(masks, 0, T);
		const tirar = []; let pos = 0;
		for (const k of ks) { if (k.a > pos + 0.02) tirar.push({ a: pos, b: k.a }); pos = k.b; }
		if (T > pos + 0.02) tirar.push({ a: pos, b: T });
		let tirado = 0;
		ED.mexer(() => { tirado = cortarTrechos(tirar); ED.ED.sel.clear(); });
		ED.caber();
		ED.status(`Ritmo: ${Math.max(0, ks.length - 1)} cortes entre ${vs.length} ${vs.length > 1 ? "vozes" : "voz"}, ${Math.round(tirado)} s de pausa a menos (${ED.tcode(T, P.fps)} → ${ED.tcode(ED.total(), P.fps)})`, "ok");
	}
	$("#autoCortes").onclick = cortarSilencios;

	/* ---------- transcrição (Whisper no navegador) ---------- */
	const WH = { ver: "wb-q8-1", tjs: "https://cdn.jsdelivr.net/npm/@xenova/transformers@2.17.2", mark: "/__whisper__/", base: "https://estudio.invalid/__whisper__/",
		files: [["config.json", 2248], ["generation_config.json", 3776], ["preprocessor_config.json", 339], ["tokenizer.json", 2480466], ["tokenizer_config.json", 282683], ["ort-wasm-simd.wasm", 10014674], ["onnx/encoder_model_quantized.onnx", 23200850, "encoder", 2], ["onnx/decoder_model_merged_quantized.onnx", 53707539, "decoder", 5]], blobs: null, worker: null };
	const whUrl = (p) => new URL("whisper/" + p, location.href).href;
	const cache = (() => { let p = null; const ab = () => p || (p = new Promise((ok, no) => { const r = indexedDB.open("ep-whisper-edicao", 1); r.onupgradeneeded = () => r.result.createObjectStore("f"); r.onsuccess = () => ok(r.result); r.onerror = () => no(r.error); })); const op = async (m, fn) => { const d = await ab(); return new Promise((ok, no) => { const tx = d.transaction("f", m), r = fn(tx.objectStore("f")); tx.oncomplete = () => ok(r && r.result); tx.onerror = () => no(tx.error); }); }; return { get: (k) => op("readonly", (s) => s.get(k)), set: (k, v) => op("readwrite", (s) => s.put(v, k)) }; })();
	async function whFiles(onp) {
		if (WH.blobs) return WH.blobs; const out = {}; let done = 0;
		for (const [f, size, part, n] of WH.files) {
			let b = await cache.get(WH.ver + ":" + f).catch(() => null);
			if (!(b && b.size === size)) { const ps = []; for (let i = 0; i < (n || 1); i++) { const r = await fetch(whUrl(part ? part + "." + i + ".wasm" : f)); if (!r.ok) throw new Error("faltou o arquivo do reconhecedor " + f); ps.push(await r.blob()); } b = new Blob(ps); await cache.set(WH.ver + ":" + f, b).catch(() => {}); }
			out[f] = b; done += size; if (onp) onp(done / WH.files.reduce((a, x) => a + x[1], 0));
		}
		return (WH.blobs = out);
	}
	function nucleo(scope) {
		let pipe = null;
		return async function (msg, post) {
			scope.__whF = msg.files;
			if (!scope.__whP) { scope.__whP = true; const of = scope.fetch.bind(scope), MARK = msg.mark; scope.fetch = function (u, o) { const s = typeof u === "string" ? u : (u && u.url) || String(u), i = s.indexOf(MARK); if (i < 0) return of(u, o); const f = s.slice(i + MARK.length).split("?")[0].replace(/^Xenova\/whisper-base\//, ""), b = scope.__whF && scope.__whF[f]; if (!b) return Promise.resolve(new Response("", { status: 404 })); return Promise.resolve(new Response(b, { status: 200, headers: { "Content-Type": /\.wasm$/.test(f) ? "application/wasm" : /\.json$/.test(f) ? "application/json" : "application/octet-stream" } })); }; }
			if (!pipe) { post({ st: "load" }); const T = await import(msg.tjs), E = T.env; E.allowLocalModels = true; E.allowRemoteModels = false; E.useBrowserCache = false; E.localModelPath = msg.base; const ow = E.backends.onnx.wasm; ow.wasmPaths = msg.base; ow.numThreads = 1; ow.proxy = false; pipe = await T.pipeline("automatic-speech-recognition", "Xenova/whisper-base", { quantized: true }); }
			const A = msg.audio, SR = 16000, out = [];
			for (let i = 0; i < msg.win.length; i++) {
				const [a, b] = msg.win[i]; post({ st: "asr", i, n: msg.win.length });
				const seg = A.subarray(Math.max(0, Math.floor((a - msg.off) * SR)), Math.min(A.length, Math.ceil((b - msg.off) * SR))); if (seg.length < SR * 0.2) continue;
				const r = await pipe(seg, { language: "portuguese", task: "transcribe", return_timestamps: "word" });
				for (const c of r.chunks || []) { if (!c.text || !c.text.trim() || !c.timestamp || c.timestamp[0] == null) continue; const s0 = c.timestamp[0], s1 = c.timestamp[1] != null ? c.timestamp[1] : s0 + 0.3; out.push({ t: c.text.trim(), a: +(a + s0).toFixed(2), b: +(a + Math.min(Math.max(s1, s0 + 0.02), b - a)).toFixed(2) }); }
			}
			return out;
		};
	}
	function rodarWorker(msg, onp) {
		return new Promise((ok, no) => {
			if (!WH.worker) WH.worker = new Worker(URL.createObjectURL(new Blob(["const run=(" + nucleo.toString() + ")(self);self.onmessage=e=>{run(e.data,m=>self.postMessage(m)).then(w=>self.postMessage({st:'done',words:w}),err=>self.postMessage({st:'err',err:String(err&&err.message||err)}));};"], { type: "text/javascript" })), { type: "module" });
			const w = WH.worker; w.onmessage = (e) => { const m = e.data || {}; if (m.st === "done") ok(m.words || []); else if (m.st === "err") no(new Error(m.err)); else if (onp) onp(m); }; w.onerror = (e) => no(new Error(e.message || "o reconhecedor não abriu"));
			w.postMessage(msg, [msg.audio.buffer]);
		});
	}
	/* o reconhecedor às vezes entra em loop ("não, não, não…" dezenas de vezes): corta repetições além de 3
	   (de uma palavra ou de um pedaço de 2 a 4 palavras) */
	function semLoop(ws) {
		const nrm = (t) => t.toLowerCase().replace(/[^\p{L}\p{N}]+/gu, "");
		let out = ws.slice();
		for (let n = 1; n <= 4; n++) {
			const r = []; let i = 0;
			while (i < out.length) {
				const g = out.slice(i, i + n).map((w) => nrm(w.t)).join(" ");
				let k = 1; while (i + (k + 1) * n <= out.length && out.slice(i + k * n, i + (k + 1) * n).map((w) => nrm(w.t)).join(" ") === g) k++;
				const max = n === 1 ? 3 : 2;
				if (g && k > max) { r.push(...out.slice(i, i + max * n)); i += k * n; } else { r.push(out[i]); i++; }
			}
			out = r;
		}
		return out;
	}
	/* janelas de até 14 s cortadas nas pausas, só onde há fala (janela longa favorece o loop do reconhecedor) */
	function janelas(m, s0, s1) {
		const W = [], MAX = 14; let cur = null;
		for (let i = Math.floor(s0 / HOP); i < Math.ceil(s1 / HOP);) { if (!m[i]) { i++; continue; } let j = i; while (j < m.length && m[j]) j++; const a = Math.max(s0, i * HOP - 0.25), b = Math.min(s1, j * HOP + 0.25); if (cur && b - cur[0] <= MAX) cur[1] = b; else { if (cur) W.push(cur); if (b - a > MAX) { for (let x = a; x < b; x += MAX) W.push([x, Math.min(b, x + MAX)]); cur = null; } else cur = [a, b]; } i = j; }
		if (cur) W.push(cur); return W;
	}
	/* transcreve cada personagem na sua faixa; as palavras ficam guardadas no tempo da FONTE (seguem os cortes feitos depois) */
	async function transcrever() {
		const P = ED.P, vs = vozesFala(), T = ED.total();
		if (!T || !vs.length) { ED.aviso("Abra o bruto primeiro", "A transcrição usa as faixas de voz dos personagens."); return null; }
		const pr = $("#trProg"), bar = pr.querySelector("i"); pr.hidden = false;
		const res = { v: 2, palavras: [] };
		try {
			ED.status("Baixando o reconhecedor de fala (só na primeira vez)…");
			const files = await whFiles((f) => { bar.style.width = (f * 20).toFixed(0) + "%"; });
			const n = Math.ceil(T / HOP) + 1;
			for (let vi = 0; vi < vs.length; vi++) {
				const v = vs[vi], m = mascaraTL(v.id, n), win = janelas(m, 0, T);
				if (!win.length) continue;
				// áudio da faixa em 16 kHz, no tempo da linha do tempo (só onde tem fala)
				const off = win[0][0], fim = win[win.length - 1][1], N = Math.ceil((fim - off) * 16000), a16 = new Float32Array(N);
				for (const c of P.clipes) {
					if (c.faixa !== v.id || c.off) continue;
					const rt = ED.RT[c.midia]; if (!rt) continue;
					const aud = rt.buf ? null : rt.aud && rt.aud[c.trilha || 0], buf = rt.buf, ch = buf && buf.getChannelData(0), sr = buf ? buf.sampleRate : aud && aud.sr, vel = c.vel || 1;
					const a = Math.max(0, Math.floor((c.ini - off) * 16000)), b = Math.min(N, Math.ceil((c.ini + c.dur - off) * 16000));
					for (let i = a; i < b; i++) { const s0 = c.fonte + ((off + i / 16000) - c.ini) * vel, k = Math.floor(s0 * sr); a16[i] += buf ? (ch[k] || 0) : aud ? (aud.pcm[k] || 0) / 32768 : 0; }
				}
				const words = await rodarWorker({ files, mark: WH.mark, base: WH.base, tjs: WH.tjs, audio: a16, win, off }, (pg) => { if (pg.st === "asr") { bar.style.width = (20 + ((vi + pg.i / pg.n) / vs.length) * 80).toFixed(0) + "%"; ED.status(`Transcrevendo ${v.nome}: trecho ${pg.i + 1} de ${pg.n}`); } else if (pg.st === "load") ED.status("Carregando o reconhecedor…"); });
				// guarda cada palavra presa ao clipe de onde veio (mídia + faixa do bruto + tempo da fonte)
				for (const w of semLoop(words)) {
					const c = P.clipes.find((q) => q.faixa === v.id && !q.off && w.a >= q.ini && w.a < q.ini + q.dur); if (!c) continue;
					const vel = c.vel || 1, fa = c.fonte + (w.a - c.ini) * vel, fb = c.fonte + (Math.min(w.b, c.ini + c.dur) - c.ini) * vel;
					res.palavras.push({ t: w.t, m: c.midia, tr: c.trilha || 0, a: +fa.toFixed(2), b: +fb.toFixed(2), voz: v.id });
				}
			}
			P.transcricao = res; ED.salvarLogo();
			ED.status(`Transcrição pronta: ${res.palavras.length} palavras de ${vs.length} ${vs.length > 1 ? "personagens" : "personagem"}`, "ok");
			return res;
		} catch (e) { console.error(e); ED.aviso("A transcrição parou", String(e.message || e)); return null; }
		finally { pr.hidden = true; bar.style.width = "0"; }
	}
	$("#autoTranscrever").onclick = transcrever;

	/* ---------- frases no tempo atual da linha do tempo, com o nome do personagem ---------- */
	function paraTL(w) {
		for (const c of ED.P.clipes) {
			if (c.off || c.midia !== w.m || (c.trilha || 0) !== w.tr || !(c.faixa === w.voz || ED.ehVoz(c.faixa))) continue;
			const vel = c.vel || 1; if (w.a >= c.fonte && w.a < c.fonte + c.dur * vel) return { a: c.ini + (w.a - c.fonte) / vel, b: c.ini + (Math.min(w.b, c.fonte + c.dur * vel) - c.fonte) / vel, faixa: c.faixa };
		}
		return null;
	}
	function frasesTL() {
		const T = ED.P.transcricao; if (!T || !T.palavras) return [];
		const nome = (id) => (ED.P.vozes.find((v) => v.id === id) || {}).nome || id;
		const porVoz = {};
		for (const w of T.palavras) { const p = paraTL(w); if (!p) continue; (porVoz[p.faixa] = porVoz[p.faixa] || []).push({ t: w.t, a: p.a, b: p.b }); }
		const out = [];
		for (const id in porVoz) {
			let cur = null;
			for (const w of porVoz[id].sort((x, y) => x.a - y.a)) { if (cur && w.a - cur.b < 0.6 && cur.t.length < 160) { cur.t += " " + w.t; cur.b = w.b; } else { if (cur) out.push(cur); cur = { quem: nome(id), faixa: id, a: w.a, b: w.b, t: w.t }; } }
			if (cur) out.push(cur);
		}
		return out.sort((x, y) => x.a - y.a).map((f) => ({ quem: f.quem, faixa: f.faixa, a: +f.a.toFixed(2), b: +f.b.toFixed(2), t: f.t }));
	}

	/* ---------- legendas automáticas: até 4 palavras por vez, na cor do personagem ---------- */
	function legendas() {
		const T = ED.P.transcricao; if (!T || !T.palavras || !T.palavras.length) { ED.aviso("Transcreva primeiro (📝 Transcrever)", ""); return 0; }
		const ws = []; for (const w of T.palavras) { if (/^\s*[\[(♪].*[\])♪]?\s*$/.test(w.t)) continue; const p = paraTL(w); if (p) ws.push({ t: w.t, a: p.a, b: p.b, faixa: p.faixa }); }
		ws.sort((x, y) => x.a - y.a);
		const grupos = []; let g = null;
		for (const w of ws) {
			if (g && w.faixa === g.faixa && w.a - g.b < 0.4 && g.n < 4 && !/[.!?]$/.test(g.t)) { g.t += " " + w.t; g.b = w.b; g.n++; }
			else { if (g) grupos.push(g); g = { faixa: w.faixa, a: w.a, b: w.b, t: w.t, n: 1 }; }
		}
		if (g) grupos.push(g);
		const cor = (id) => (ED.FAIXAS.find((f) => f.id === id) || {}).cor || "#ffffff";
		ED.mexer(() => {
			ED.P.clipes = ED.P.clipes.filter((c) => !c.leg);
			// cada personagem segue até a próxima fala DELE; se outro falar junto, a legenda dele sobe uma linha
			const linhas = [0.76, 0.68, 0.6], ocup = linhas.map(() => -1);
			grupos.forEach((q, i) => {
				const prox = grupos.slice(i + 1).find((o) => o.faixa === q.faixa), fim = Math.min(q.b + 0.15, prox ? prox.a : Infinity);
				let L = ocup.findIndex((t) => t <= q.a + 1e-3); if (L < 0) L = 0;
				ocup[L] = fim;
				ED.P.clipes.push({ id: ED.rid(), faixa: "T", leg: true, ini: +q.a.toFixed(3), dur: +Math.max(0.2, fim - q.a).toFixed(3), txt: { texto: q.t.trim().toUpperCase(), cor: cor(q.faixa), tam: 64, x: 0.5, y: linhas[L], anim: "corte", contorno: "#0a0a0a" } });
			});
		});
		ED.status(grupos.length + " legendas criadas (refazer apaga as antigas)", "ok");
		return grupos.length;
	}
	$("#autoLegendas").onclick = legendas;

	/* ---------- edição completa com o Claude ---------- */
	const msg = (t, tipo) => { const el = $("#autoMsg"); el.textContent = t; el.className = "status" + (tipo ? " " + tipo : ""); };
	async function editarComClaude() {
		const P = ED.P;
		if (!P.clipes.some((c) => c.faixa === "V1")) { ED.aviso("Abra o bruto primeiro", ""); return; }
		if (!window.ROTEIROS || !ROTEIROS.temSenha()) { ED.aviso("Precisa da senha da equipe", "Entre com a senha da equipe na aba Shorts (Efeitos › Sons da equipe) neste navegador; a Edição usa a mesma."); return; }
		if (!P.transcricao) { msg("Transcrevendo primeiro…"); if (!(await transcrever())) return; }
		const frases = frasesTL();
		const bib = (ED.BIB.itens || []).map((x) => (x.papel === "MUS" ? "MUS|" : "SFX|") + x.pasta + x.nome);
		const pedido = { id: P.id, nome: P.nome, duracao: +ED.total().toFixed(2), fps: P.fps, vozes: P.vozes.map((v) => ({ faixa: v.id, personagem: v.nome, papel: v.papel })), frases, sfx: bib.filter((x) => x.startsWith("SFX|")).map((x) => x.slice(4)).slice(0, 600), pastasMusica: [...new Set(bib.filter((x) => x.startsWith("MUS|")).map((x) => x.slice(4).split("/").slice(0, -1).join("/")))].slice(0, 80), musicas: bib.filter((x) => x.startsWith("MUS|")).map((x) => x.slice(4)).slice(0, 900) };
		msg("Mandando para o Claude…");
		const r = await ROTEIROS.nuvem("/edicao?id=" + encodeURIComponent(P.id), { method: "POST", body: JSON.stringify(pedido), tempo: 20000 });
		if (!r) { msg("Não consegui mandar: " + (ROTEIROS.NUVEM.erro || "sem conexão"), "err"); return; }
		msg("O Claude está editando (leva alguns minutos). Pode continuar mexendo; o plano entra sozinho quando chegar.");
		P.claude = { quando: r.quando }; ED.salvarLogo();
		esperarPlano(r.quando);
	}
	let espera = 0;
	function esperarPlano(desde) {
		clearInterval(espera);
		const t0 = Date.now();
		espera = setInterval(async () => {
			const r = await ROTEIROS.nuvem("/edicao?id=" + encodeURIComponent(ED.P.id), { tempo: 10000 });
			if (r && r.status === "erro") { clearInterval(espera); msg("O Claude não conseguiu: " + (r.erro || ""), "err"); return; }
			if (r && r.plano && r.plano.quando >= desde) { clearInterval(espera); aplicarPlano(r.plano); return; }
			if (Date.now() - t0 > 60 * 60e3) { clearInterval(espera); msg("Sem resposta em 1 hora. Tente de novo.", "err"); }
			else msg(`O Claude está editando… ${Math.round((Date.now() - t0) / 60000)} min`);
		}, 15000);
	}

	/* aplica o plano: tudo é adicionado primeiro e os cortes de conteúdo entram por último (puxando o resto) */
	async function aplicarPlano(pl) {
		const P = ED.P, BIB = ED.BIB, faltas = [];
		// guarda o plano cru + a V1 de antes dele: a ponte local (ponte-local.js) monta o mesmo plano no Premiere/FilmCraft do PC
		P.ultimoPlano = { plano: JSON.parse(JSON.stringify(pl)), vozes: P.vozes.map((v) => ({ faixa: v.id })),
			clipes: P.clipes.filter((c) => c.faixa === "V1" && !c.off).map((c) => ({ tl_in: +c.ini.toFixed(4), tl_out: +(c.ini + c.dur).toFixed(4), src_in: +(c.fonte || 0).toFixed(4) })) };
		const achar = (papel, nome, pasta) => {
			const l = BIB.itens.filter((x) => x.papel === papel), n = String(nome || "").toLowerCase();
			return l.find((x) => (x.pasta + x.nome).toLowerCase() === n) || l.find((x) => x.nome.toLowerCase() === n) || l.find((x) => n && x.nome.toLowerCase().includes(n)) || (pasta ? l.find((x) => x.pasta.toLowerCase().includes(String(pasta).toLowerCase())) : null);
		};
		const sfxMid = {}, musMid = {};
		for (const s of pl.sfx || []) { const x = achar("SFX", s.arquivo || s.nome); if (x) { const key = x.papel + "|" + x.pasta + x.nome; if (!sfxMid[key]) sfxMid[key] = await BIB.importar(key); s._mid = sfxMid[key]; } else faltas.push({ t: s.t, txt: "SFX " + (s.arquivo || s.nome) }); }
		for (const m of pl.musicas || []) { const x = achar("MUS", m.arquivo, m.pasta); if (x) { const key = x.papel + "|" + x.pasta + x.nome; if (!musMid[key]) musMid[key] = await BIB.importar(key); m._mid = musMid[key]; } else faltas.push({ t: m.a, txt: "Música " + (m.arquivo || "") + (m.clima ? " (" + m.clima + ")" : "") }); }
		ED.mexer(() => {
			const add = (c) => { c.id = ED.rid(); P.clipes.push(c); return c; };
			for (const z of pl.zooms || []) add({ faixa: "Z", ini: z.a, dur: Math.max(0.2, z.b - z.a), p: { de: z.de || 1, para: z.para || 1.25, paraY: z.paraY || undefined, anim: z.anim || 0, fx: z.fx == null ? 0.5 : z.fx, fy: z.fy == null ? 0.5 : z.fy }, nota: z.motivo });
			for (const f of pl.efeitos || []) if (["flash", "shake", "vhs", "flashback", "tilt", "brilho", "pb", "vinheta", "preto"].includes(f.tipo)) add({ faixa: "FX", tipo: f.tipo, ini: f.a, dur: Math.max(0.1, f.dur || 1), p: f.p || {}, nota: f.motivo });
			// takes futuros: cenas de mais pra frente do próprio vídeo, só imagem, na V2 (por cima do bruto)
			for (const tk of pl.takes || []) {
				const v = ED.clipeEm("V1", tk.de); if (!v || !(tk.dur > 0.1)) continue;
				add({ faixa: "V2", midia: v.midia, ini: tk.a, dur: tk.dur, fonte: v.fonte + (tk.de - v.ini), enq: v.enq, tr: { s: 1, x: 0, y: 0, op: 1 }, nota: tk.motivo || "take futuro" });
			}
			for (const t of pl.textos || []) add({ faixa: "T", ini: t.a, dur: Math.max(0.3, t.dur || 1.5), txt: { texto: t.texto, cor: t.cor || "#ffffff", tam: t.tam || 110, x: 0.5, y: t.y || 0.2, anim: "pop" } });
			for (const s of pl.sfx || []) { if (!s._mid) continue; const m = P.midias[s._mid]; add({ faixa: "SFX", midia: s._mid, ini: Math.max(0, s.t - (s.pre || 0)), dur: Math.min(m.dur || 1, s.dur || m.dur || 1), fonte: 0, vol: s.ganho != null ? s.ganho : ED.ganhoPadrao(m), nota: s.motivo }); }
			for (const m of pl.musicas || []) { if (!m._mid) continue; const md = P.midias[m._mid], d = Math.min(m.b - m.a, (md.dur || 0) - (m.de || 0)); if (d > 0.5) add({ faixa: "MUS", midia: m._mid, ini: m.a, dur: d, fonte: m.de || 0, vol: m.ganho != null ? m.ganho : -26, nota: m.clima }); }
			for (const mk of pl.marcadores || []) P.marcadores.push({ id: ED.rid(), t: mk.t, txt: mk.txt || "" });
			for (const f of faltas) P.marcadores.push({ id: ED.rid(), t: f.t || 0, txt: "Faltou na biblioteca: " + f.txt, cor: "#ff8a3d" });
			// mutes: desliga a call/jogo só no trecho (corta o clipe nas bordas)
			for (const mu of pl.mutes || []) {
				const fx = (P.vozes.find((v) => v.id === mu.faixa) || P.vozes.find((v) => v.nome.toLowerCase() === String(mu.faixa || mu.quem || "").toLowerCase()) || {}).id;
				if (!fx || fx === (P.vozes[0] || {}).id && !mu.forcar) continue; // nunca a voz principal
				for (const c of P.clipes.filter((q) => q.faixa === fx && q.ini < mu.b && q.ini + q.dur > mu.a)) {
					const a = Math.max(c.ini, mu.a), b = Math.min(c.ini + c.dur, mu.b), partes = [];
					if (a > c.ini + 0.01) partes.push([c.ini, a, false]); partes.push([a, b, true]); if (b < c.ini + c.dur - 0.01) partes.push([b, c.ini + c.dur, false]);
					P.clipes = P.clipes.filter((q) => q !== c);
					for (const [x, y, off] of partes) P.clipes.push(Object.assign(JSON.parse(JSON.stringify(c)), { id: ED.rid(), ini: x, dur: y - x, fonte: c.fonte + (x - c.ini), off: off || c.off, link: undefined }));
				}
			}
			// cortes de conteúdo (repetição, nota do roteiro para o editor): entram por último e puxam o resto
			cortarTrechos((pl.cortes || []).map((c) => ({ a: c.a, b: c.b })));
		});
		if (P.claude) P.claude.aplicado = true; ED.salvarLogo();
		ED.caber();
		const n = (pl.takes || []).length + (pl.zooms || []).length + (pl.efeitos || []).length + (pl.sfx || []).length + (pl.musicas || []).length;
		msg(`Plano aplicado: ${n} itens, ${(pl.cortes || []).length} cortes de conteúdo${faltas.length ? ", " + faltas.length + " itens faltaram na biblioteca (marcadores)" : ""}.` + (pl.resumo ? " " + pl.resumo : ""), "ok");
	}
	$("#autoClaude").onclick = editarComClaude;
	// a página foi fechada enquanto o Claude editava: volta a esperar o plano ao abrir
	setTimeout(() => { const c = ED.P.claude; if (c && !c.aplicado && Date.now() - c.quando < 6 * 3600e3 && window.ROTEIROS && ROTEIROS.temSenha()) { msg("Esperando o plano do Claude…"); esperarPlano(c.quando); } }, 4000);
	window.ED_AUTO = { cortarSilencios, transcrever, frasesTL, legendas, semLoop, aplicarPlano, manter, mascara };
})();
