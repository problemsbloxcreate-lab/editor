/* Aba Edição do Estúdio Problems: editor de vídeo próprio para os vídeos LONGOS do canal.
   Faixas: T (texto), FX (efeitos por cima de tudo, como camada de ajuste), Z (zoom do bruto), V2 (por cima), V1 (bruto),
   A1 (voz POV), A2 (call), A3 (jogo), SFX, MUS (música). O bruto entra como V1 + A1..A3 ligados (cortam e andam juntos).
   Tudo fica salvo neste navegador (IndexedDB); os arquivos grandes ficam no PC e são reabertos pelo próprio navegador. */
(function () {
	"use strict";
	const $ = (s, r) => (r || document).querySelector(s), $$ = (s, r) => Array.from((r || document).querySelectorAll(s));
	const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
	const rid = () => Math.random().toString(36).slice(2, 10);
	const dbLin = (db) => Math.pow(10, db / 20);
	const easeOut = (u) => 1 - Math.pow(1 - clamp(u, 0, 1), 3);
	const tcode = (t, fps) => { t = Math.max(0, t); const h = Math.floor(t / 3600), m = Math.floor((t % 3600) / 60), s = Math.floor(t % 60), f = Math.floor((t % 1) * (fps || 30)); return [h, m, s].map((x) => String(x).padStart(2, "0")).join(":") + ":" + String(f).padStart(2, "0"); };
	const curto = (t) => { t = Math.max(0, t); const m = Math.floor(t / 60), s = t % 60; return m + ":" + (s < 10 ? "0" : "") + s.toFixed(1); };

	/* ---------- faixas ---------- */
	/* faixas de voz são dinâmicas: uma por personagem (P.vozes), vindas das faixas do bruto ou de arquivos de voz separados */
	const TOPO = [
		{ id: "T", tipo: "texto", nome: "Texto", h: 26 },
		{ id: "FX", tipo: "fx", nome: "Efeitos", h: 26 },
		{ id: "Z", tipo: "zoom", nome: "Zoom", h: 26 },
		{ id: "V2", tipo: "video", nome: "V2 · Por cima", h: 36 },
		{ id: "V1", tipo: "video", nome: "V1 · Bruto", h: 44 },
	];
	const FIM = [{ id: "SFX", tipo: "audio", nome: "SFX", h: 30 }, { id: "MUS", tipo: "audio", nome: "Música", h: 30 }];
	let FAIXAS = [];
	const ehVoz = (id) => /^A\d+$/.test(id);
	const PERSONAGENS = ["Problems", "Patão", "Kadu", "Stick", "Mel", "Zoom", "Brucutu", "Vampira", "Jujubinha", "Verity", "Xinglau", "Lajota", "Guima"];
	const PALETA = ["#19f0f0", "#7bd88f", "#ff6b6b", "#ffcf4a", "#c07bff", "#ff9a1f", "#ff7be0", "#9ad0ff"];
	function corVoz(v, i) { if (v.papel === "jogo") return "#8c93a3"; try { const c = window.ROTEIROS && ROTEIROS.corDoc(v.nome); if (c && c !== "#d9d9d9") return c; } catch (_) {} if (/^pat/i.test(v.nome)) return "#ffd23f"; return PALETA[i % PALETA.length]; }
	function montarFaixas() {
		if (!P.vozes || !P.vozes.length) P.vozes = [{ id: "A1", nome: "Problems", papel: "voz" }, { id: "A2", nome: "Call", papel: "voz" }, { id: "A3", nome: "Jogo", papel: "jogo" }];
		FAIXAS = TOPO.concat(P.vozes.map((v, i) => ({ id: v.id, tipo: "audio", voz: true, papel: v.papel, nome: v.nome, h: v.papel === "jogo" ? 28 : 34, cor: corVoz(v, i) })), FIM);
		for (const f of FAIXAS) if (f.cor) COR[f.id] = f.cor;
	}
	function novaVoz(nome, papel) { let n = 1; while (P.vozes.some((v) => v.id === "A" + n)) n++; const v = { id: "A" + n, nome: nome || "Voz " + n, papel: papel || "voz" }; P.vozes.push(v); montarFaixas(); cabecalhos(); return v; }
	const FX_NOMES = { flash: "Flash", shake: "Tremor", vhs: "VHS", flashback: "Flashback", tilt: "Murchar", brilho: "Revelação", pb: "P&B", vinheta: "Vinheta", preto: "Passagem pelo preto", cor: "Cor" };
	const COR = { T: "#e8c547", FX: "#b07cff", Z: "#3d9bff", V2: "#4fb0c6", V1: "#3a8fb7", SFX: "#ff8a3d", MUS: "#d65db1" };

	/* ---------- estado ---------- */
	const novoProjeto = () => ({ v: 1, id: rid(), nome: "Sem nome", fps: 30, w: 1920, h: 1080, midias: {}, clipes: [], marcadores: [], faixas: {}, transcricao: null });
	let P = novoProjeto();
	const RT = {}; // runtime por mídia: {file, mp4, aud:[{sr,pcm,rms}], buf, img, vids, dur}
	const ED = { t: 0, tocando: false, sel: new Set(), pps: 60, scroll: 0, ima: true, desfazer: [], refazer: [], copia: null, alvoFoco: null };
	window.ED_ESTADO = { get P() { return P; }, RT, ED };

	function status(txt, tipo) { const el = $("#status"); el.textContent = txt || ""; el.style.color = tipo === "err" ? "var(--warn)" : tipo === "ok" ? "var(--ok)" : ""; }
	/* pergunta com botões próprios; devolve a chave escolhida (ou null se fechar) */
	function perguntar(t, p, botoes) {
		return new Promise((ok) => {
			const d = $("#dlgQ"); $("#dlgQT").textContent = t; $("#dlgQP").textContent = p || "";
			const l = $("#dlgQB"); l.replaceChildren(...botoes.map(([k, n], i) => { const b = document.createElement("button"); b.type = "button"; b.className = "btn" + (i === 0 ? " primary" : ""); b.textContent = n; b.onclick = () => { d.close(); ok(k); }; return b; }));
			d.onclose = () => ok(null); d.showModal();
		});
	}
	function aviso(t, p) { $("#dlgT").textContent = t; $("#dlgP").textContent = p || ""; $("#dlg").showModal(); }
	$("#dlgOk").onclick = () => $("#dlg").close();

	const total = () => P.clipes.reduce((m, c) => Math.max(m, c.ini + c.dur), 0);
	const faixa = (id) => FAIXAS.find((f) => f.id === id) || { id, tipo: ehVoz(id) ? "audio" : "fx", nome: id, h: 30 };
	const fstate = (id) => P.faixas[id] || (P.faixas[id] = { mudo: false, oculto: false });

	/* ---------- desfazer ---------- */
	function foto() { return JSON.stringify({ c: P.clipes, m: P.marcadores, v: P.vozes, f: P.faixas }); }
	function voltarFoto(s) { P.clipes = s.c; P.marcadores = s.m; if (s.v) P.vozes = s.v; if (s.f) P.faixas = s.f; montarFaixas(); cabecalhos(); }
	function mexer(fn) {
		ED.desfazer.push(foto()); if (ED.desfazer.length > 120) ED.desfazer.shift(); ED.refazer = [];
		fn(); depoisDeMexer();
	}
	function depoisDeMexer() { P.clipes.sort((a, b) => a.ini - b.ini); salvarLogo(); redesenharTudo(); if (ED.tocando) reprogramarAudio(); }
	function desfazer() { if (!ED.desfazer.length) return; ED.refazer.push(foto()); voltarFoto(JSON.parse(ED.desfazer.pop())); ED.sel.clear(); depoisDeMexer(); }
	function refazer() { if (!ED.refazer.length) return; ED.desfazer.push(foto()); voltarFoto(JSON.parse(ED.refazer.pop())); ED.sel.clear(); depoisDeMexer(); }

	/* ---------- banco (IndexedDB): projeto, alças dos arquivos e blobs pequenos ---------- */
	const DB = (() => {
		let p = null;
		const abrir = () => p || (p = new Promise((ok, no) => { const r = indexedDB.open("ep-edicao", 1); r.onupgradeneeded = () => r.result.createObjectStore("k"); r.onsuccess = () => ok(r.result); r.onerror = () => no(r.error); }));
		const op = async (modo, fn) => { const d = await abrir(); return new Promise((ok, no) => { const tx = d.transaction("k", modo), st = tx.objectStore("k"), r = fn(st); tx.oncomplete = () => ok(r && r.result); tx.onerror = () => no(tx.error); }); };
		return { get: (k) => op("readonly", (s) => s.get(k)), set: (k, v) => op("readwrite", (s) => s.put(v, k)), del: (k) => op("readwrite", (s) => s.delete(k)), chaves: () => op("readonly", (s) => s.getAllKeys()) };
	})();
	let tSalvar = 0;
	function salvarLogo() { clearTimeout(tSalvar); tSalvar = setTimeout(salvarJa, 700); }
	// cada projeto fica guardado em "proj:<id>" e aparece na tela inicial (lista "lista", com nome, data, duração e miniatura)
	async function salvarJa() {
		try { await DB.set("proj:" + P.id, JSON.stringify(P)); await DB.set("atual", P.id); await guardaNaLista(); return true; }
		catch (e) { status("Não consegui salvar neste navegador: " + e.message, "err"); return false; }
	}
	// "Sair da conta" (botão da conta): salva o projeto aberto antes de sair
	(window.ESTUDIO_AO_SAIR ||= []).push(async () => { if (!P || !(P.clipes?.length || Object.keys(P.midias || {}).length)) return true; clearTimeout(tSalvar); return salvarJa(); }); // projeto vazio: nada a salvar
	const LISTA = { async ler() { try { return (await DB.get("lista")) || []; } catch (_) { return []; } }, gravar: (l) => DB.set("lista", l) };
	let ultimaMini = 0;
	function miniatura() { try { const c = document.createElement("canvas"); c.width = 320; c.height = 180; const g = c.getContext("2d"); g.drawImage($("#tela"), 0, 0, 320, 180);
		const d = g.getImageData(0, 0, 320, 180).data; let soma = 0; for (let i = 0; i < d.length; i += 400) soma += d[i] + d[i + 1] + d[i + 2];
		if (soma < 30) return null; // tela preta (vídeo ainda não carregou): não vira miniatura
		return c.toDataURL("image/jpeg", 0.7); } catch (_) { return null; } }
	async function guardaNaLista() {
		const temAlgo = P.clipes.length || Object.keys(P.midias || {}).length; if (!temAlgo) return; // projeto vazio não entra no histórico
		const l = await LISTA.ler(), i = l.findIndex((x) => x.id === P.id), velho = l[i] || {};
		const m = { id: P.id, nome: P.nome || "Sem nome", mod: Date.now(), dur: total(), clipes: P.clipes.length, thumb: velho.thumb || null };
		if (P.clipes.length && Date.now() - ultimaMini > 15000) { const t = miniatura(); if (t) { m.thumb = t; ultimaMini = Date.now(); } }
		if (i >= 0) l[i] = m; else l.unshift(m);
		l.sort((a, b) => b.mod - a.mod); await LISTA.gravar(l);
	}

	/* ---------- áudio (prévia) ---------- */
	let AC = null, MASTER = null, fontes = [], a0 = 0, t0 = 0, agenda = 0;
	function ac() {
		if (AC) return AC;
		AC = new AudioContext({ sampleRate: 48000, latencyHint: "interactive" });
		const lim = AC.createDynamicsCompressor(); lim.threshold.value = -3; lim.knee.value = 0; lim.ratio.value = 20; lim.attack.value = 0.003; lim.release.value = 0.12;
		MASTER = AC.createGain(); MASTER.connect(lim); lim.connect(AC.destination);
		ED.medidor = AC.createAnalyser(); ED.medidor.fftSize = 1024; lim.connect(ED.medidor);
		return AC;
	}
	/* pedaço de áudio de um clipe [s0,s1) em tempo de FONTE, como AudioBuffer (bruto: mono Int16 → float) */
	function bufferDe(c, s0, s1) {
		const rt = RT[c.midia]; if (!rt) return null;
		if (rt.buf) { // arquivo de áudio (SFX/música) já decodificado
			const b = rt.buf, sr = b.sampleRate, i0 = Math.max(0, Math.floor(s0 * sr)), i1 = Math.min(b.length, Math.ceil(s1 * sr));
			if (i1 <= i0) return null;
			const out = AC.createBuffer(b.numberOfChannels, i1 - i0, sr);
			for (let ch = 0; ch < b.numberOfChannels; ch++) out.copyToChannel(b.getChannelData(ch).subarray(i0, i1), ch);
			return out;
		}
		const a = rt.aud && rt.aud[c.trilha || 0]; if (!a) return null;
		const sr = a.sr, i0 = Math.max(0, Math.floor(s0 * sr)), i1 = Math.min(a.pcm.length, Math.ceil(s1 * sr));
		if (i1 <= i0) return null;
		const out = AC.createBuffer(1, i1 - i0, sr), d = out.getChannelData(0);
		for (let i = i0; i < i1; i++) d[i - i0] = a.pcm[i] / 32768;
		return out;
	}
	/* vizinhos colados na mesma faixa (para a transição de áudio "Potência constante" de 0,2 s centrada no corte) */
	const XF = 0.1;
	function colado(c, lado) {
		if (!ehVoz(c.faixa)) return false;
		const t = lado < 0 ? c.ini : c.ini + c.dur;
		return P.clipes.some((o) => o !== c && o.faixa === c.faixa && !o.off && Math.abs((lado < 0 ? o.ini + o.dur : o.ini) - t) < 1e-3);
	}
	function tocarClipe(c, deT, ate) {
		const tl0 = Math.max(c.ini, deT), tl1 = c.ini + c.dur;
		if (tl1 <= tl0) return;
		const xi = colado(c, -1) && tl0 === c.ini ? XF : 0, xo = colado(c, 1) ? XF : 0;
		const vel = c.vel || 1, fs = c.fonte + ((tl0 - c.ini) - xi) * vel, fe = c.fonte + (c.dur + xo) * vel;
		const CH = 10 * vel; // pedaços de até 10 s, preparados só quando estão chegando
		let resta = false;
		for (let s = fs; s < fe; s += CH) {
			const chave = c.id + ":" + s.toFixed(3);
			if (jaTocou.has(chave)) continue;
			if (c.ini + (s - c.fonte) / vel > ate) { resta = true; break; }
			jaTocou.add(chave);
			const e = Math.min(fe, s + CH), b = bufferDe(c, s, e); if (!b) continue;
			const src = AC.createBufferSource(); src.buffer = b; src.playbackRate.value = vel;
			const g = AC.createGain(), vol = dbLin(c.vol || 0) * ganhoFaixa(c.faixa);
			const quando = a0 + (c.ini + (s - c.fonte) / vel - t0);
			g.gain.value = vol;
			// curvas de potência constante nas bordas coladas; bordas soltas ganham 8 ms (sem estalo)
			const durB = (e - s) / vel, ini = s === fs, fim = e === fe;
			if (ini) { const d = xi ? 2 * XF : 0.008; const curva = new Float32Array(32); for (let k = 0; k < 32; k++) curva[k] = vol * (xi ? Math.sin((k / 31) * Math.PI / 2) : k / 31); try { g.gain.setValueCurveAtTime(curva, Math.max(AC.currentTime, quando), Math.min(d, durB)); } catch (_) {} }
			if (c.faixa !== "SFX" && c.fadeIn && ini) { try { g.gain.cancelScheduledValues(0); g.gain.setValueAtTime(0, Math.max(AC.currentTime, quando)); g.gain.linearRampToValueAtTime(vol, Math.max(AC.currentTime, quando) + c.fadeIn); } catch (_) {} }
			if (c.faixa !== "SFX" && c.fadeOut && fim) { try { g.gain.setValueAtTime(vol, Math.max(AC.currentTime, quando + durB - c.fadeOut)); g.gain.linearRampToValueAtTime(0, quando + durB); } catch (_) {} }
			else if (fim && !/^(SFX)$/.test(c.faixa)) { const d = xo ? 2 * XF : 0.008; const curva = new Float32Array(32); for (let k = 0; k < 32; k++) curva[k] = vol * (xo ? Math.cos((k / 31) * Math.PI / 2) : 1 - k / 31); try { g.gain.setValueCurveAtTime(curva, Math.max(AC.currentTime, quando + durB - d), d); } catch (_) {} }
			src.connect(g); g.connect(MASTER);
			const off = Math.max(0, AC.currentTime - quando);
			if (off >= durB) continue;
			src.start(Math.max(AC.currentTime, quando), off * vel);
			fontes.push(src);
		}
		return resta;
	}
	let jaTocou = new Set();
	function programarAte(ate) {
		for (const c of P.clipes) {
			if (c.off || jaTocou.has(c.id) || faixa(c.faixa).tipo !== "audio") continue;
			if (c.ini + c.dur <= t0 - 0.01 || c.ini > ate) continue;
			if (!tocarClipe(c, t0, ate)) jaTocou.add(c.id);
		}
	}
	function pararAudio() { for (const s of fontes) { try { s.stop(); } catch (_) {} } fontes = []; jaTocou = new Set(); }
	function reprogramarAudio() { if (!ED.tocando) return; const t = tempoAgora(); pararAudio(); t0 = t; a0 = AC.currentTime + 0.05; ED.t = t; programarAte(t + 12); }
	function tempoAgora() { return ED.tocando ? t0 + (AC.currentTime - a0) : ED.t; }
	function tocar() {
		if (ED.tocando) return pausar();
		if (!P.clipes.length) return;
		ac(); AC.resume();
		if (ED.t >= total() - 0.02) ED.t = 0;
		ED.tocando = true; t0 = ED.t; a0 = AC.currentTime + 0.08; jaTocou = new Set();
		programarAte(ED.t + 12);
		clearInterval(agenda); agenda = setInterval(() => { if (ED.tocando) programarAte(tempoAgora() + 12); }, 500);
		$("#bPlay").textContent = "❚❚"; prepararVideos(true);
	}
	function pausar() { if (!ED.tocando) return; ED.t = tempoAgora(); ED.tocando = false; pararAudio(); clearInterval(agenda); $("#bPlay").textContent = "▶"; for (const id in RT) (RT[id].vids || []).forEach((v) => v.pause()); }
	function irPara(t) { const tocava = ED.tocando; if (tocava) pausar(); ED.t = clamp(t, 0, Math.max(0, total())); if (tocava) tocar(); else { prepararVideos(false); } }

	/* ---------- vídeo (prévia): 2 elementos <video> por mídia, um tocando e o outro já buscando o próximo clipe ---------- */
	function vidsDe(mid) {
		const rt = RT[mid]; if (!rt || !rt.url) return null;
		if (!rt.vids) rt.vids = [0, 1, 2].map(() => { const v = document.createElement("video"); v.src = rt.url; v.muted = true; v.preload = "auto"; v.playsInline = true; v.dataset.clip = ""; for (const ev of ["seeked", "loadeddata", "canplay"]) v.addEventListener(ev, () => { ED.sujo = true; }); return v; });
		return rt.vids;
	}
	function clipeEm(fid, t) { let r = null; for (const c of P.clipes) if (c.faixa === fid && !c.off && t >= c.ini && t < c.ini + c.dur) r = c; return r; }
	function proximoClipe(fid, t, mid) { let r = null; for (const c of P.clipes) if (c.faixa === fid && !c.off && c.midia === mid && c.ini > t && (!r || c.ini < r.ini)) r = c; return r; }
	function elementoPara(c, t, tocando) {
		const vs = vidsDe(c.midia); if (!vs) return null;
		let v = vs.find((x) => x.dataset.clip === c.id);
		const vel = c.vel || 1, st = c.fonte + (t - c.ini) * vel;
		if (!v) {
			// não rouba o vídeo de outro clipe que está na tela agora (V1 e V2 podem usar o mesmo bruto) nem o já preparado
			const ocupados = new Set(necessarios(t).map((q) => q.c.id).filter((id) => id !== c.id));
			v = vs.find((x) => !ocupados.has(x.dataset.clip) && x.dataset.clip !== (ED._prox && ED._prox[c.midia])) || vs.find((x) => !ocupados.has(x.dataset.clip)) || vs[0];
			v.dataset.clip = c.id; v.currentTime = st;
		}
		if (tocando) { if (v.playbackRate !== vel) v.playbackRate = vel; if (v.paused) v.play().catch(() => {}); if (Math.abs(v.currentTime - st) > 0.25 * vel) v.currentTime = st; }
		else { if (!v.paused) v.pause(); if (Math.abs(v.currentTime - st) > 0.5 / P.fps) v.currentTime = st; }
		return v;
	}
	function prepararVideos(tocando) {
		const t = ED.tocando ? tempoAgora() : ED.t;
		ED._prox = {};
		for (const fid of ["V1", "V2"]) {
			const c = clipeEm(fid, t); if (!c || !RT[c.midia] || !RT[c.midia].url) continue;
			const v = elementoPara(c, t, tocando);
			const nx = proximoClipe(fid, t, c.midia);
			if (nx && nx.ini - t < 2) {
				const vs = vidsDe(c.midia), na = new Set(["V1", "V2"].map((f) => { const q = clipeEm(f, t); return q ? q.id : null; })), o = vs.find((x) => x !== v && !na.has(x.dataset.clip));
				if (o && o.dataset.clip !== nx.id) { o.pause(); o.dataset.clip = nx.id; o.currentTime = nx.fonte; }
				ED._prox[c.midia] = nx.id;
			}
		}
	}

	/* ---------- desenho do quadro (prévia e exportação usam o mesmo) ---------- */
	const tela = $("#tela"), g = tela.getContext("2d");
	const camada = document.createElement("canvas"), gc = camada.getContext("2d");
	function enqDe(c, w, h) { const e = c.enq; if (e) return e; return w / h > 3 ? { x: 0.5, y: 0, w: 0.5, h: 1 } : { x: 0, y: 0, w: 1, h: 1 }; }
	function zoomEm(t) {
		const z = clipeEm("Z", t); if (!z) return null;
		const p = z.p || {}, u = p.anim > 0 ? easeOut((t - z.ini) / p.anim) : 1;
		const s = (p.de || 1) + ((p.para || 1.25) - (p.de || 1)) * u, sy = p.paraY ? (p.de || 1) + (p.paraY - (p.de || 1)) * u : s;
		let fx = p.fx == null ? 0.5 : p.fx, fy = p.fy == null ? 0.5 : p.fy;
		if (p.fx2 != null) { const q = clamp((t - z.ini) / z.dur, 0, 1), e = q * q * (3 - 2 * q); fx += (p.fx2 - fx) * e; fy += ((p.fy2 == null ? fy : p.fy2) - fy) * e; } // pan: o foco anda junto
		return { s, sy, fx, fy };
	}
	/* fonte(c) devolve a imagem do clipe no tempo t (prévia: <video>/<img>; exportação: VideoFrame) */
	function desenharQuadro(ctx, W, H, t, fonte) {
		if (camada.width !== W || camada.height !== H) { camada.width = W; camada.height = H; }
		gc.setTransform(1, 0, 0, 1, 0, 0); gc.fillStyle = "#000"; gc.fillRect(0, 0, W, H);
		for (const q of necessarios(t)) desenharClipe(q.c, q.fid, t, fonte, q.alfa, W, H);
		// efeitos (camada de ajuste) sobre V1+V2
		const fx = P.clipes.filter((c) => c.faixa === "FX" && !c.off && t >= c.ini && t < c.ini + c.dur);
		let sx = 1, rot = 0, dx = 0, dy = 0, filtro = [], pos = [];
		for (const f of fx) {
			const p = f.p || {}, lt = t - f.ini, u = lt / f.dur;
			if (f.tipo === "shake") { const a = (p.forca || 24) * (1 - u) * (W / 1920); dx += a * (Math.sin(lt * 71) * 0.6 + Math.sin(lt * 43 + 1) * 0.4); dy += a * (Math.sin(lt * 59 + 2) * 0.6 + Math.sin(lt * 37) * 0.4); }
			else if (f.tipo === "tilt") { const q = easeOut(lt / (p.anim || 2)); sx *= 1 - 0.29 * q; rot += (-3.2 * Math.PI / 180) * q; filtro.push("saturate(" + (1 - 0.73 * q).toFixed(3) + ")"); }
			else if (f.tipo === "brilho") { sx *= 1 + 0.22 * easeOut(lt / 1.2); pos.push(f); }
			else if (f.tipo === "flashback") { sx *= 1 + 0.06 * u; filtro.push("sepia(0.5) saturate(0.7) contrast(0.92) brightness(1.06)"); pos.push(f); }
			else if (f.tipo === "pb") filtro.push("grayscale(1)");
			else if (f.tipo === "cor") { const fc = filtroCor(p); if (fc !== "none") filtro.push(fc); }
			else pos.push(f);
		}
		ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.fillStyle = "#000"; ctx.fillRect(0, 0, W, H);
		ctx.translate(W / 2 + dx, H / 2 + dy); ctx.rotate(rot); ctx.scale(sx, sx); ctx.translate(-W / 2, -H / 2);
		if (filtro.length) ctx.filter = filtro.join(" ");
		ctx.drawImage(camada, 0, 0); ctx.filter = "none";
		ctx.restore();
		for (const f of pos) {
			const p = f.p || {}, lt = t - f.ini, u = clamp(lt / f.dur, 0, 1);
			if (f.tipo === "preto") { ctx.globalAlpha = Math.sin(Math.PI * u); ctx.fillStyle = "#000"; ctx.fillRect(0, 0, W, H); ctx.globalAlpha = 1; }
			else if (f.tipo === "flash") { ctx.globalAlpha = (p.forca == null ? 0.7 : p.forca) * Math.pow(1 - u, 1.6); ctx.fillStyle = p.cor || "#fff"; ctx.fillRect(0, 0, W, H); ctx.globalAlpha = 1; }
			else if (f.tipo === "vhs") {
				ctx.save(); ctx.globalCompositeOperation = "screen"; ctx.globalAlpha = 0.35; ctx.filter = "hue-rotate(160deg) saturate(2)"; ctx.drawImage(ctx.canvas, 0, 0, W, H, (W / 1920) * 7, 0, W, H); ctx.restore(); ctx.filter = "none";
				ctx.fillStyle = "rgba(0,0,0,.16)"; for (let y = 0; y < H; y += 4 * (H / 1080)) ctx.fillRect(0, y, W, 1.5 * (H / 1080));
				const by = ((lt * 0.35) % 1) * H; ctx.fillStyle = "rgba(255,255,255,.07)"; ctx.fillRect(0, by, W, H * 0.06);
			} else if (f.tipo === "vinheta" || f.tipo === "flashback") {
				const gr = ctx.createRadialGradient(W / 2, H / 2, H * 0.35, W / 2, H / 2, H * 0.95); gr.addColorStop(0, "rgba(0,0,0,0)"); gr.addColorStop(1, "rgba(0,0,0," + (f.tipo === "flashback" ? 0.55 : p.forca || 0.6) + ")"); ctx.fillStyle = gr; ctx.fillRect(0, 0, W, H);
			} else if (f.tipo === "brilho") {
				const cx = (p.fx == null ? 0.5 : p.fx) * W, cy = (p.fy == null ? 0.5 : p.fy) * H, k = W / 1920;
				for (let i = 0; i < 7; i++) {
					const ang = i * 2.4 + lt * 0.6, r = (60 + i * 34) * k * (0.6 + 0.6 * easeOut(lt / 1.2)), x = cx + Math.cos(ang) * r, y = cy + Math.sin(ang) * r * 0.7;
					const tw = 0.55 + 0.45 * Math.sin(lt * 5 + i * 1.7), sz = (24 + (i % 3) * 14) * k * tw * (1 - u * 0.5);
					ctx.fillStyle = "rgba(255,255,230," + (0.85 * tw).toFixed(2) + ")"; ctx.beginPath();
					ctx.moveTo(x, y - sz * 2); ctx.lineTo(x + sz * 0.35, y - sz * 0.35); ctx.lineTo(x + sz * 2, y); ctx.lineTo(x + sz * 0.35, y + sz * 0.35); ctx.lineTo(x, y + sz * 2); ctx.lineTo(x - sz * 0.35, y + sz * 0.35); ctx.lineTo(x - sz * 2, y); ctx.lineTo(x - sz * 0.35, y - sz * 0.35); ctx.closePath(); ctx.fill();
				}
			}
		}
		// textos
		for (const c of P.clipes) {
			if (c.faixa !== "T" || c.off || t < c.ini || t >= c.ini + c.dur || fstate("T").oculto) continue;
			const x = c.txt || {}, lt = t - c.ini, k = H / 1080;
			const an = x.anim || "pop", rest = c.ini + c.dur - t;
			let sc = 1, dy = 0, al = 1, txt = x.texto || "";
			if (an === "pop") sc = lt < 0.12 ? 0.4 + 0.75 * (lt / 0.12) : lt < 0.22 ? 1.15 - 0.15 * ((lt - 0.12) / 0.1) : 1;
			else if (an === "deslizar") { const q = easeOut(lt / 0.3); dy = (1 - q) * 0.12 * H; al = q; }
			else if (an === "aparecer") al = clamp(Math.min(lt, rest) / 0.25, 0, 1);
			else if (an === "digitar") txt = txt.slice(0, Math.max(1, Math.floor(lt * 22)));
			const FON = { lilita: '"Lilita One","Rubik",sans-serif', rubik: '700 "Rubik",sans-serif', mono: '700 "JetBrains Mono",monospace' }, ff = FON[x.fonte || "lilita"];
			const tam = Math.round((x.tam || 96) * k);
			ctx.save(); ctx.globalAlpha = al; ctx.translate((x.x == null ? 0.5 : x.x) * W, (x.y == null ? 0.2 : x.y) * H + dy); ctx.scale(sc, sc);
			ctx.font = (/^\d/.test(ff) ? ff.replace(/^(\d+) /, "$1 " + tam + "px ") : tam + "px " + ff); ctx.textAlign = "center"; ctx.textBaseline = "middle"; ctx.lineJoin = "round";
			const linhas = txt.split("\n"), lh = tam * 1.08;
			if (x.caixa) { const w = Math.max(...linhas.map((l) => ctx.measureText(l).width)) + tam * 0.6, h = lh * linhas.length + tam * 0.3; ctx.fillStyle = x.caixa === true ? "rgba(0,0,0,.6)" : x.caixa; ctx.beginPath(); (ctx.roundRect ? ctx.roundRect(-w / 2, -h / 2, w, h, tam * 0.2) : ctx.rect(-w / 2, -h / 2, w, h)); ctx.fill(); }
			linhas.forEach((l, i) => { const yy = (i - (linhas.length - 1) / 2) * lh; if (x.contorno !== "nenhum") { ctx.lineWidth = Math.max(3, tam * 0.16); ctx.strokeStyle = x.contorno || "#0a0a0a"; ctx.strokeText(l, 0, yy); } ctx.fillStyle = x.cor || "#ffffff"; ctx.fillText(l, 0, yy); });
			ctx.restore();
		}
	}
	window.ED_QUADRO = desenharQuadro;
	/* keyframes: c.kf = { s|x|y|r|op: [[tempo dentro do clipe, valor], …] }, com curva suave entre eles */
	function valKf(c, prop, lt, base) {
		const k = c.kf && c.kf[prop]; if (!k || !k.length) return base;
		if (lt <= k[0][0]) return k[0][1];
		for (let i = 1; i < k.length; i++) if (lt <= k[i][0]) { const [t0, v0] = k[i - 1], [t1, v1] = k[i], q = (lt - t0) / ((t1 - t0) || 1), e = q * q * (3 - 2 * q); return v0 + (v1 - v0) * e; }
		return k[k.length - 1][1];
	}
	function trEm(c, t) { const tr = c.tr || {}, lt = t - c.ini; return { s: valKf(c, "s", lt, tr.s == null ? 1 : tr.s), x: valKf(c, "x", lt, tr.x || 0), y: valKf(c, "y", lt, tr.y || 0), r: valKf(c, "r", lt, tr.r || 0), op: valKf(c, "op", lt, tr.op == null ? 1 : tr.op) }; }
	/* o que aparece no instante t: V1 (com a dissolução entre dois clipes, quando tem) e V2 */
	function necessarios(t) {
		const out = [];
		if (!fstate("V1").oculto) {
			const c = clipeEm("V1", t);
			if (c) {
				out.push({ c, fid: "V1", alfa: 1, papel: "a" });
				// dissolução centrada no corte: entrando (c.trans) ou saindo (o próximo tem trans)
				const ant = c.trans && P.clipes.find((p) => p.faixa === "V1" && !p.off && Math.abs(p.ini + p.dur - c.ini) < 1e-3);
				if (ant && t < c.ini + c.trans.dur / 2) { out[0] = { c: ant, fid: "V1", alfa: 1, papel: "b" }; out.push({ c, fid: "V1", alfa: clamp((t - (c.ini - c.trans.dur / 2)) / c.trans.dur, 0, 1), papel: "a" }); }
				else { const nx = P.clipes.find((p) => p.faixa === "V1" && !p.off && p.trans && Math.abs(c.ini + c.dur - p.ini) < 1e-3); if (nx && t >= nx.ini - nx.trans.dur / 2) out.push({ c: nx, fid: "V1", alfa: clamp((t - (nx.ini - nx.trans.dur / 2)) / nx.trans.dur, 0, 1), papel: "b" }); }
			}
		}
		if (!fstate("V2").oculto) { const c = clipeEm("V2", t); if (c) out.push({ c, fid: "V2", alfa: 1, papel: "a" }); }
		return out;
	}
	window.ED_NECESSARIOS = necessarios;
	function desenharClipe(c, fid, t, fonte, alfa, W, H) {
		const src = fonte(c, t); if (!src) return;
		const sw = src.displayWidth || src.videoWidth || src.naturalWidth || src.width, sh = src.displayHeight || src.videoHeight || src.naturalHeight || src.height;
		if (!sw || !sh) return;
		const e = enqDe(c, sw, sh);
		gc.save(); gc.globalAlpha = alfa;
		if (fid === "V1") { const z = zoomEm(t); if (z) { gc.translate(z.fx * W, z.fy * H); gc.scale(z.s, z.sy); gc.translate(-z.fx * W, -z.fy * H); } }
		if (c.tr || c.kf) {
			const T = trEm(c, t), lt = t - c.ini, rest = c.ini + c.dur - t; let k = 1, al = 1;
			if (c.anim === "pop") { k = lt < 0.12 ? 0.3 + 0.85 * (lt / 0.12) : lt < 0.22 ? 1.15 - 0.15 * ((lt - 0.12) / 0.1) : rest < 0.12 ? Math.max(0.01, rest / 0.12) : 1; }
			else if (c.anim === "aparecer") al = clamp(Math.min(lt, rest) / 0.25, 0, 1);
			gc.globalAlpha = alfa * clamp(T.op, 0, 1) * al; gc.translate(W / 2 + T.x * W, H / 2 + T.y * H); if (T.r) gc.rotate((T.r * Math.PI) / 180); gc.scale(T.s * k, T.s * k); gc.translate(-W / 2, -H / 2);
		}
		if (c.cor) gc.filter = filtroCor(c.cor);
		// cobre o quadro mantendo a proporção; o recorte (crop) tira as bordas sem esticar
		const rw = e.w * sw, rh = e.h * sh, kk = Math.max(W / rw, H / rh), dw = rw * kk, dh = rh * kk, dx = (W - dw) / 2, dy = (H - dh) / 2;
		const cr = (c.tr && c.tr.crop) || {}, l = cr.l || 0, rr = cr.r || 0, tp = cr.t || 0, bt = cr.b || 0;
		try { gc.drawImage(src, (e.x + e.w * l) * sw, (e.y + e.h * tp) * sh, rw * (1 - l - rr), rh * (1 - tp - bt), dx + dw * l, dy + dh * tp, dw * (1 - l - rr), dh * (1 - tp - bt)); } catch (_) {}
		gc.filter = "none"; gc.restore();
	}
	/* correção de cor: brilho/contraste/saturação em %, temperatura de −100 (frio) a 100 (quente) */
	function filtroCor(k) { const f = []; if (k.brilho) f.push("brightness(" + (1 + k.brilho / 100) + ")"); if (k.contraste) f.push("contrast(" + (1 + k.contraste / 100) + ")"); if (k.saturacao) f.push("saturate(" + (1 + k.saturacao / 100) + ")"); if (k.temperatura) f.push(k.temperatura > 0 ? "sepia(" + (k.temperatura / 250) + ")" : "hue-rotate(" + (k.temperatura / 8) + "deg) saturate(" + (1 + k.temperatura / 400) + ")"); return f.join(" ") || "none"; }
	function fontePrevia(c, t) {
		const rt = RT[c.midia]; if (!rt) return null;
		if (rt.img) return rt.img;
		const vs = vidsDe(c.midia); if (!vs) return null;
		const v = vs.find((x) => x.dataset.clip === c.id) || elementoPara(c, t, ED.tocando);
		return v && v.readyState >= 2 ? v : null;
	}

	/* ---------- laço da prévia ---------- */
	let ultimoT = -1;
	function laco() {
		const t = tempoAgora();
		if (ED.tocando) { ED.t = t; if (t >= total()) { pausar(); ED.t = total(); } prepararVideos(true); }
		if (t !== ultimoT || ED.tocando || ED.sujo) {
			ultimoT = t; ED.sujo = false;
			if (tela.width !== P.w || tela.height !== P.h) { tela.width = P.w; tela.height = P.h; }
			desenharQuadro(g, P.w, P.h, t, fontePrevia);
			if (ED.alvoFoco) { const z = ED.alvoFoco, x = (z.p.fx == null ? 0.5 : z.p.fx) * P.w, y = (z.p.fy == null ? 0.5 : z.p.fy) * P.h; g.strokeStyle = "#3d9bff"; g.lineWidth = 4; g.beginPath(); g.arc(x, y, 22, 0, 7); g.moveTo(x - 34, y); g.lineTo(x + 34, y); g.moveTo(x, y - 34); g.lineTo(x, y + 34); g.stroke(); }
			$("#tc").innerHTML = tcode(t, P.fps) + " <small>/ " + tcode(total(), P.fps) + "</small>";
			medidor();
			desenharTL();
		}
		requestAnimationFrame(laco);
	}

	/* medidor de volume (pico do que está tocando, em dB) */
	const med = $("#medidor"), mg = med.getContext("2d"), mbuf = new Float32Array(1024); let mpico = -60;
	function medidor() {
		let p = -60; if (ED.tocando && ED.medidor) { ED.medidor.getFloatTimeDomainData(mbuf); let m = 0; for (const v of mbuf) m = Math.max(m, Math.abs(v)); p = Math.max(-60, 20 * Math.log10(m + 1e-9)); }
		mpico = Math.max(p, mpico - 1.2);
		const W = med.width, H = med.height; mg.clearRect(0, 0, W, H); mg.fillStyle = "rgba(255,255,255,.08)"; mg.fillRect(0, 0, W, H);
		const w = ((mpico + 60) / 60) * W; mg.fillStyle = mpico > -1 ? "#ff6b6b" : mpico > -9 ? "#ffcf4a" : "#7bd88f"; mg.fillRect(0, 0, w, H);
		med.title = ED.tocando ? Math.round(mpico) + " dB" : "Volume (toca para medir)";
	}
	/* ---------- linha do tempo (canvas) ---------- */
	const area = $("#tlArea"), tl = $("#tlCanvas"), tg = tl.getContext("2d"), RUL = 24;
	function alturas() { const disp = Math.max(100, (area.clientHeight || 300) - RUL), soma = FAIXAS.reduce((a, f) => a + f.h, 0), k = Math.min(1.6, Math.max(0.55, disp / soma)); return FAIXAS.map((f) => Math.floor(f.h * k)); }
	function layout() { const hs = alturas(); let y = RUL; return FAIXAS.map((f, i) => { const r = { f, y, h: hs[i] }; y += hs[i]; return r; }); }
	function xDe(t) { return (t - ED.scroll) * ED.pps; }
	function tDe(x) { return x / ED.pps + ED.scroll; }
	function cabecalhos() {
		const hs = $("#heads"); hs.innerHTML = '<div class="rg"></div>';
		const alt = alturas();
		for (const [i, f] of FAIXAS.entries()) {
			const d = document.createElement("div"); d.className = "th"; d.style.height = alt[i] + "px"; d.style.borderLeft = "3px solid " + COR[f.id];
			const st = fstate(f.id), ehAudio = f.tipo === "audio";
			const trv = `<button type="button" class="trava" aria-pressed="${!!st.trava}" title="${st.trava ? "Destrancar a faixa" : "Trancar a faixa (não mexe sem querer)"}">${st.trava ? "🔒" : "🔓"}</button>`;
			d.innerHTML = trv + `<span class="tnome" title="${f.voz ? "Clique para escolher o personagem, o volume ou tirar a faixa" : f.nome}" style="${f.voz ? "cursor:pointer" : ""}"></span>` + (ehAudio ? `<button type="button" class="solo" aria-pressed="${!!st.solo}" title="Ouvir só esta faixa">S</button>` : "") + `<button type="button" class="vis" aria-pressed="${ehAudio ? st.mudo : st.oculto}" title="${ehAudio ? "Silenciar a faixa" : "Esconder a faixa"}">${ehAudio ? (st.mudo ? "🔇" : "🔊") : (st.oculto ? "🙈" : "👁")}</button>`;
			d.querySelector(".tnome").textContent = (f.voz ? (f.papel === "jogo" ? "🎮 " : "🎙 ") : "") + f.nome + (st.vol ? " " + (st.vol > 0 ? "+" : "") + st.vol + "dB" : "");
			d.querySelector(".trava").onclick = () => { st.trava = !st.trava; if (st.trava) P.clipes.forEach((c) => { if (c.faixa === f.id) ED.sel.delete(c.id); }); cabecalhos(); salvarLogo(); ED.sujo = true; };
			d.querySelector(".vis").onclick = () => { if (ehAudio) st.mudo = !st.mudo; else st.oculto = !st.oculto; cabecalhos(); ED.sujo = true; salvarLogo(); reprogramarAudio(); };
			if (ehAudio) d.querySelector(".solo").onclick = () => { st.solo = !st.solo; cabecalhos(); salvarLogo(); reprogramarAudio(); };
			if (f.voz) d.querySelector(".tnome").onclick = (e) => menuVoz(f.id, e.currentTarget);
			else if (ehAudio) d.querySelector(".tnome").onclick = (e) => menuVoz(f.id, e.currentTarget);
			hs.appendChild(d);
		}
		const add = document.createElement("button"); add.type = "button"; add.className = "btn small"; add.style.margin = "4px 6px"; add.textContent = "＋ Voz"; add.title = "Adicionar a voz de um personagem (arquivo separado)";
		add.onclick = () => $("#addVoz").click(); hs.appendChild(add);
	}
	/* menu da faixa: personagem, voz/jogo, volume da faixa, tirar a faixa */
	function menuVoz(id, alvo) {
		const v = P.vozes.find((q) => q.id === id), st = fstate(id);
		let m = $("#menuVoz"); if (m) m.remove();
		m = document.createElement("div"); m.id = "menuVoz"; m.className = "card"; m.style.cssText = "position:fixed;z-index:20;width:230px;box-shadow:0 10px 30px rgba(0,0,0,.45)";
		const R = alvo.getBoundingClientRect(); m.style.left = R.left + "px"; m.style.top = Math.max(8, R.top - 10) + "px";
		if (v) {
			m.innerHTML = `<p class="lbl">Personagem</p><div class="chips">${PERSONAGENS.concat(["Call", "Jogo"]).map((n) => `<button type="button" class="chip" aria-pressed="${n === v.nome}">${n}</button>`).join("")}</div>
				<input type="text" placeholder="Outro nome" value=""><label class="linha"><input type="checkbox" style="flex:none" ${v.papel === "jogo" ? "checked" : ""}> <span>Som do jogo (não é fala)</span></label>`;
			m.querySelectorAll(".chip").forEach((b) => b.onclick = () => { v.nome = b.textContent; lembrarQuem(v.arquivo, v.nome); v.papel = b.textContent === "Jogo" ? "jogo" : v.papel === "jogo" && b.textContent !== "Jogo" ? "voz" : v.papel; feito(); });
			const inp = m.querySelector("input[type=text]"); inp.onchange = () => { if (inp.value.trim()) { v.nome = inp.value.trim(); lembrarQuem(v.arquivo, v.nome); feito(); } };
			m.querySelector("input[type=checkbox]").onchange = (e) => { v.papel = e.target.checked ? "jogo" : "voz"; feito(); };
		}
		if (v && v.papel !== "jogo" && P.clipes.some((c) => c.faixa === id)) {
			const sep = document.createElement("div"); sep.className = "campo";
			sep.innerHTML = '<span>Todos numa faixa só? Separe por personagem</span><div class="linha"><select style="flex:none;width:118px" title="Quantas pessoas falam nesta faixa"><option value="2">2 pessoas</option><option value="3" selected>3 pessoas</option><option value="4">4 pessoas</option><option value="5">5 pessoas</option><option value="6">6 pessoas</option><option value="0">Não sei</option></select><button type="button" class="btn small primary">🧩 Separar</button></div><p class="status"></p>';
			const [se, bt, msg] = [sep.querySelector("select"), sep.querySelector("button"), sep.querySelector(".status")];
			bt.onclick = async () => { bt.disabled = true; msg.textContent = "Ouvindo as vozes…"; try { const r = await window.ED_SEPARAR(id, +se.value, (f) => { msg.textContent = "Ouvindo as vozes… " + Math.round(f * 100) + "%"; }); status(`Separei em ${r.vozes} vozes (${r.segundos.join(" s, ")} s de fala). Clique no nome de cada faixa para dar o personagem; o S toca só ela.`, "ok"); m.remove(); salvarLogo(); } catch (e) { msg.textContent = "Não deu: " + (e.message || e); bt.disabled = false; } };
			m.appendChild(sep);
		}
		const outras = P.vozes.filter((q) => q.id !== id && q.papel !== "jogo");
		if (v && outras.length && P.clipes.some((c) => c.faixa === id)) {
			const j = document.createElement("div"); j.className = "linha";
			j.innerHTML = `<select title="É a mesma pessoa de outra faixa?">${outras.map((q) => `<option value="${q.id}">É o mesmo que: ${q.nome}</option>`).join("")}</select>`;
			j.appendChild(botao("Juntar", () => { const alvoId = j.querySelector("select").value; mexer(() => { P.clipes.forEach((c) => { if (c.faixa === id) c.faixa = alvoId; }); P.vozes = P.vozes.filter((q) => q !== v); }); feito(); }));
			m.appendChild(j);
		}
		m.appendChild(campoNum("Volume da faixa", st.vol || 0, -30, 15, 0.5, (x) => { st.vol = x || 0; cabecalhos(); reprogramarAudio(); }, "dB"));
		const linha = document.createElement("div"); linha.className = "linha";
		if (v) linha.appendChild(botao("Tirar a faixa", () => { if (P.clipes.some((c) => c.faixa === id) && !confirm("A faixa tem clipes. Tirar mesmo assim (os clipes somem)?")) return; mexer(() => { P.clipes = P.clipes.filter((c) => c.faixa !== id); P.vozes = P.vozes.filter((q) => q !== v); }); feito(); }));
		linha.appendChild(botao("Fechar", () => m.remove(), "primary")); m.appendChild(linha);
		document.body.appendChild(m);
		const r2 = m.getBoundingClientRect(); if (r2.bottom > innerHeight - 8) m.style.top = Math.max(8, innerHeight - r2.height - 8) + "px";
		function feito() { montarFaixas(); cabecalhos(); salvarLogo(); ED.sujo = true; m.remove(); }
		setTimeout(() => document.addEventListener("pointerdown", function fora(e) { if (!m.contains(e.target)) { m.remove(); document.removeEventListener("pointerdown", fora); } }), 0);
	}
	/* volume e solo das faixas (prévia e exportação usam o mesmo) */
	function ganhoFaixa(id) { const st = fstate(id); if (st.mudo) return 0; const solo = FAIXAS.some((f) => f.tipo === "audio" && fstate(f.id).solo); if (solo && !st.solo) return 0; return dbLin(st.vol || 0); }
	function ondaDe(c) {
		const rt = RT[c.midia]; if (!rt) return null;
		if (rt.buf) return rt.rms ? { rms: rt.rms } : null;
		return rt.aud && rt.aud[c.trilha || 0];
	}
	function desenharTL() {
		const W = area.clientWidth, H = area.clientHeight, dpr = window.devicePixelRatio || 1;
		if (tl.width !== Math.round(W * dpr) || tl.height !== Math.round(H * dpr)) { tl.width = Math.round(W * dpr); tl.height = Math.round(H * dpr); }
		const c2 = tg; c2.setTransform(dpr, 0, 0, dpr, 0, 0);
		const css = getComputedStyle(document.documentElement), bg = css.getPropertyValue("--bg"), line = css.getPropertyValue("--line"), muted = css.getPropertyValue("--muted"), fg = css.getPropertyValue("--fg");
		c2.fillStyle = bg; c2.fillRect(0, 0, W, H);
		const L = layout();
		for (const r of L) { c2.fillStyle = r.f.id === "V1" || r.f.id === (P.vozes[0] || {}).id ? "rgba(255,255,255,.025)" : "transparent"; c2.fillRect(0, r.y, W, r.h); c2.fillStyle = line; c2.fillRect(0, r.y + r.h - 1, W, 1); }
		// régua
		c2.fillStyle = css.getPropertyValue("--panel-2"); c2.fillRect(0, 0, W, RUL); c2.fillStyle = line; c2.fillRect(0, RUL - 1, W, 1);
		const passos = [0.1, 0.25, 0.5, 1, 2, 5, 10, 15, 30, 60, 120, 300, 600], passo = passos.find((p) => p * ED.pps >= 70) || 600;
		c2.fillStyle = muted; c2.font = "10px JetBrains Mono, monospace"; c2.textBaseline = "top";
		for (let t = Math.floor(ED.scroll / passo) * passo; t < tDe(W); t += passo) { const x = Math.round(xDe(t)) + 0.5; c2.fillRect(x, RUL - 8, 1, 8); c2.fillText(curto(t), x + 3, 4); }
		// trecho de exportação (I/O)
		if (P.entrada != null || P.saida != null) { const a = xDe(P.entrada || 0), b = xDe(P.saida != null ? P.saida : total()); c2.fillStyle = "rgba(61,155,255,.35)"; c2.fillRect(a, RUL - 6, b - a, 6); }
		// clipes
		const t0v = ED.scroll, t1v = tDe(W);
		for (const c of P.clipes) {
			if (c.ini + c.dur < t0v || c.ini > t1v) continue;
			const r = L.find((q) => q.f.id === c.faixa); if (!r) continue;
			const x = xDe(c.ini), w = Math.max(2, c.dur * ED.pps), y = r.y + 2, h = r.h - 4, sel = ED.sel.has(c.id);
			c2.globalAlpha = c.off ? 0.35 : 1;
			c2.fillStyle = COR[c.faixa]; c2.fillRect(x, y, w, h);
			c2.fillStyle = "rgba(0,0,0,.28)"; c2.fillRect(x, y + h - 1, w, 1);
			// onda
			const o = faixa(c.faixa).tipo === "audio" && ondaDe(c);
			if (o && o.rms && w > 6) {
				c2.fillStyle = "rgba(0,0,0,.38)"; const vol = c.vol || 0, x0 = Math.max(x, 0), x1 = Math.min(x + w, W);
				for (let px = x0; px < x1; px += 2) { const st = c.fonte + ((px - x) / ED.pps) * (c.vel || 1), i = Math.floor(st * 100); const db = (o.rms[i] == null ? -90 : o.rms[i]) + vol; const a = clamp((db + 60) / 60, 0, 1) * (h - 4) * 0.5; c2.fillRect(px, y + h / 2 - a, 1.5, Math.max(1, a * 2)); }
			}
			if (w > 30) {
				c2.save(); c2.beginPath(); c2.rect(x, y, w, h); c2.clip();
				c2.fillStyle = "#06121f"; c2.font = "600 10.5px Rubik, sans-serif"; c2.textBaseline = "top";
				let nome = c.faixa === "T" ? "🅣 " + ((c.txt && c.txt.texto) || "") : c.faixa === "FX" ? (FX_NOMES[c.tipo] || c.tipo) : c.faixa === "Z" ? "🔍 " + Math.round(((c.p && c.p.para) || 1) * 100) + "%" + (c.p && c.p.anim > 0 ? " ↗" : "") : (P.midias[c.midia] || {}).nome || "";
				if (faixa(c.faixa).tipo === "audio" && c.vol) nome += "  " + (c.vol > 0 ? "+" : "") + c.vol.toFixed(1) + " dB";
				c2.fillText((c.off ? "⦸ " : "") + nome, x + 4, y + 3); c2.restore();
			}
			if (c.kf) { c2.fillStyle = "#fff"; for (const L of Object.values(c.kf)) for (const [kt] of L) { const kx = x + kt * ED.pps; c2.beginPath(); c2.moveTo(kx, y + h - 9); c2.lineTo(kx + 4, y + h - 5); c2.lineTo(kx, y + h - 1); c2.lineTo(kx - 4, y + h - 5); c2.fill(); } }
			if (c.trans) { c2.fillStyle = "rgba(255,255,255,.55)"; const tw = c.trans.dur / 2 * ED.pps; c2.beginPath(); c2.moveTo(x - tw, y + h); c2.lineTo(x + tw, y); c2.lineTo(x + tw, y + h); c2.fill(); }
			if (sel) { c2.strokeStyle = "#fff"; c2.lineWidth = 2; c2.strokeRect(x + 1, y + 1, w - 2, h - 2); }
			c2.globalAlpha = 1;
		}
		// marcadores
		for (const m of P.marcadores) { const x = xDe(m.t); if (x < -5 || x > W + 5) continue; c2.fillStyle = m.cor || "#ffcf4a"; c2.beginPath(); c2.moveTo(x - 5, 0); c2.lineTo(x + 5, 0); c2.lineTo(x, 9); c2.fill(); c2.fillRect(x, 9, 1, H); }
		// seleção por caixa
		if (ED.caixa) { const b = ED.caixa; c2.strokeStyle = "#3d9bff"; c2.setLineDash([4, 3]); c2.strokeRect(Math.min(b.x0, b.x1), Math.min(b.y0, b.y1), Math.abs(b.x1 - b.x0), Math.abs(b.y1 - b.y0)); c2.setLineDash([]); }
		// cursor
		const px = xDe(ED.tocando ? tempoAgora() : ED.t);
		c2.fillStyle = "#ff4d4d"; c2.fillRect(Math.round(px), 0, 1.5, H); c2.beginPath(); c2.moveTo(px - 6, 0); c2.lineTo(px + 7, 0); c2.lineTo(px + 0.5, 8); c2.fill();
		if (ED.tocando) { const W2 = W * 0.85; if (px > W2) { ED.scroll += (px - W * 0.3) / ED.pps; } else if (px < 0) ED.scroll = Math.max(0, tDe(px) - 1); }
		c2.fillStyle = fg;
	}
	function zoomTL(v) { ED.pps = 0.5 * Math.pow(800, v / 100); }
	$("#tZoom").oninput = (e) => { const tc = ED.t; zoomTL(+e.target.value); ED.scroll = Math.max(0, tc - area.clientWidth * 0.4 / ED.pps); ED.sujo = true; };
	function caber() { const tt = Math.max(5, total()); ED.pps = (area.clientWidth - 30) / tt; ED.scroll = 0; $("#tZoom").value = clamp((Math.log(ED.pps / 0.5) / Math.log(800)) * 100, 0, 100); ED.sujo = true; }
	$("#tCaber").onclick = caber;

	/* ---------- interação na linha do tempo ---------- */
	function acertar(x, y) {
		const L = layout(), r = L.find((q) => y >= q.y && y < q.y + q.h); if (!r) return null;
		const t = tDe(x), tol = 6 / ED.pps;
		if (fstate(r.f.id).trava) return { faixa: r.f.id, t };
		let melhor = null;
		for (const c of P.clipes) { if (c.faixa !== r.f.id) continue; if (t >= c.ini - tol && t <= c.ini + c.dur + tol) { if (!melhor || (t >= c.ini && t <= c.ini + c.dur)) melhor = c; } }
		if (!melhor) return { faixa: r.f.id, t };
		const borda = Math.abs(t - melhor.ini) * ED.pps < 7 ? "ini" : Math.abs(t - (melhor.ini + melhor.dur)) * ED.pps < 7 ? "fim" : null;
		return { faixa: r.f.id, t, clipe: melhor, borda };
	}
	const ligados = (c, sem) => sem || !c.link ? [c] : P.clipes.filter((o) => o.link === c.link && Math.abs(o.ini - c.ini) < 1e-6 && Math.abs(o.dur - c.dur) < 1e-6);
	function pontosIma(excl) { const s = [ED.t, 0]; for (const c of P.clipes) if (!excl.has(c.id)) s.push(c.ini, c.ini + c.dur); for (const m of P.marcadores) s.push(m.t); return s; }
	function grudar(t, pts) { if (!ED.ima) return t; const tol = 8 / ED.pps; let b = t, d = tol; for (const p of pts) { const k = Math.abs(p - t); if (k < d) { d = k; b = p; } } return b; }
	let arr = null;
	tl.addEventListener("pointerdown", (e) => {
		const R = tl.getBoundingClientRect(), x = e.clientX - R.left, y = e.clientY - R.top;
		tl.setPointerCapture(e.pointerId);
		if (y < RUL) { arr = { modo: "cursor" }; irPara(grudar(tDe(x), pontosIma(new Set()))); return; }
		const h = acertar(x, y);
		if (!h || !h.clipe) { if (!e.shiftKey) ED.sel.clear(); arr = { modo: "caixa", x0: x, y0: y }; ED.caixa = { x0: x, y0: y, x1: x, y1: y }; irPara(tDe(x)); mostrarInspetor(); return; }
		const c = h.clipe, grupo = ligados(c, e.altKey);
		if (e.shiftKey || e.ctrlKey || e.metaKey) { grupo.forEach((q) => ED.sel.has(q.id) ? ED.sel.delete(q.id) : ED.sel.add(q.id)); }
		else if (!ED.sel.has(c.id)) { ED.sel.clear(); grupo.forEach((q) => ED.sel.add(q.id)); }
		mostrarInspetor();
		const alvo = P.clipes.filter((q) => ED.sel.has(q.id));
		ED.desfazer.push(foto()); ED.refazer = [];
		arr = { modo: h.borda ? "aparar" : "mover", borda: h.borda, x0: x, base: alvo.map((q) => ({ c: q, ini: q.ini, dur: q.dur, fonte: q.fonte, faixa: q.faixa })), alt: e.altKey, mudou: false, faixa0: c.faixa, ref: c };
		if (h.borda) arr.base = ligados(c, e.altKey).map((q) => ({ c: q, ini: q.ini, dur: q.dur, fonte: q.fonte }));
		ED.sujo = true;
	});
	tl.addEventListener("pointermove", (e) => {
		const R = tl.getBoundingClientRect(), x = e.clientX - R.left, y = e.clientY - R.top;
		if (!arr) { const h = y > RUL && acertar(x, y); tl.style.cursor = h && h.borda ? "ew-resize" : h && h.clipe ? "grab" : "default"; return; }
		if (arr.modo === "cursor") { irPara(tDe(x)); return; }
		if (arr.modo === "caixa") { ED.caixa.x1 = x; ED.caixa.y1 = y; const ta = tDe(Math.min(arr.x0, x)), tb = tDe(Math.max(arr.x0, x)), ya = Math.min(arr.y0, y), yb = Math.max(arr.y0, y), L = layout(); for (const c of P.clipes) { const r = L.find((q) => q.f.id === c.faixa); const dentro = r && r.y + r.h > ya && r.y < yb && c.ini + c.dur > ta && c.ini < tb; if (dentro) ED.sel.add(c.id); } ED.sujo = true; return; }
		const dt = (x - arr.x0) / ED.pps; if (Math.abs(x - arr.x0) > 2) arr.mudou = true;
		const excl = new Set(arr.base.map((b) => b.c.id));
		if (arr.modo === "mover") {
			const ref = arr.base.find((b) => b.c === arr.ref) || arr.base[0];
			let novo = Math.max(0, ref.ini + dt); const fimN = grudar(novo + ref.dur, pontosIma(excl)); novo = grudar(novo, pontosIma(excl)) !== novo ? grudar(novo, pontosIma(excl)) : fimN - ref.dur;
			const d = novo - ref.ini;
			// trocar de faixa (mesmo tipo) arrastando na vertical, só um clipe por vez
			const L = layout(), r = L.find((q) => y >= q.y && y < q.y + q.h);
			for (const b of arr.base) { b.c.ini = Math.max(0, b.ini + d); if (arr.base.length === 1 && r && faixa(r.f.id).tipo === faixa(b.faixa).tipo && (b.c.faixa === "V1" || b.c.faixa === "V2" || faixa(r.f.id).tipo === "audio")) b.c.faixa = r.f.id; }
		} else {
			for (const b of arr.base) {
				const lim = RT[b.c.midia] && RT[b.c.midia].dur ? RT[b.c.midia].dur : Infinity;
				const vel = b.c.vel || 1;
				if (arr.borda === "ini") { let ni = grudar(b.ini + dt, pontosIma(excl)); ni = Math.min(ni, b.ini + b.dur - 0.05); if (b.c.midia) ni = Math.max(ni, b.ini - b.fonte / vel); const k = ni - b.ini; b.c.ini = Math.max(0, ni); b.c.dur = b.dur - k; b.c.fonte = (b.fonte || 0) + (b.c.midia ? k * vel : 0); }
				else { let nf = grudar(b.ini + b.dur + dt, pontosIma(excl)); nf = Math.max(b.ini + 0.05, nf); if (b.c.midia && lim < Infinity) nf = Math.min(nf, b.ini + (lim - b.fonte) / vel); b.c.dur = nf - b.ini; }
			}
		}
		ED.sujo = true; if (ED.tocando) reprogramarAudio();
	});
	tl.addEventListener("pointerup", () => {
		if (arr && (arr.modo === "mover" || arr.modo === "aparar")) { if (!arr.mudou) ED.desfazer.pop(); else depoisDeMexer(); }
		arr = null; ED.caixa = null; mostrarInspetor(); ED.sujo = true;
	});
	area.addEventListener("wheel", (e) => {
		e.preventDefault();
		if (e.ctrlKey || e.metaKey) { const R = tl.getBoundingClientRect(), tc = tDe(e.clientX - R.left); const v = clamp(+$("#tZoom").value - Math.sign(e.deltaY) * 4, 0, 100); $("#tZoom").value = v; zoomTL(v); ED.scroll = Math.max(0, tc - (e.clientX - R.left) / ED.pps); }
		else ED.scroll = Math.max(0, ED.scroll + (e.deltaX || e.deltaY) / ED.pps);
		ED.sujo = true;
	}, { passive: false });
	new ResizeObserver(() => { ED.sujo = true; cabecalhos(); }).observe(area);
	// altura da linha do tempo
	(() => { const r = $("#redim"); let y0 = 0, h0 = 0; r.addEventListener("pointerdown", (e) => { r.setPointerCapture(e.pointerId); y0 = e.clientY; h0 = $("#tlPane").getBoundingClientRect().height; r.onpointermove = (ev) => { const h = clamp(h0 - (ev.clientY - y0), 160, innerHeight * 0.75); $("#ed").style.setProperty("--tl-h", h + "px"); ED.sujo = true; }; }); r.addEventListener("pointerup", () => { r.onpointermove = null; }); })();

	/* ---------- operações ---------- */
	const sels = () => P.clipes.filter((c) => ED.sel.has(c.id));
	function dividir() {
		const t = ED.t; let alvo = sels().filter((c) => t > c.ini + 1e-3 && t < c.ini + c.dur - 1e-3);
		if (!alvo.length) alvo = P.clipes.filter((c) => t > c.ini + 1e-3 && t < c.ini + c.dur - 1e-3 && !fstate(c.faixa).oculto && !fstate(c.faixa).trava);
		if (!alvo.length) return;
		mexer(() => { const nl = {}; for (const c of alvo) { const k = t - c.ini; const n = JSON.parse(JSON.stringify(c)); n.id = rid(); n.ini = t; n.dur = c.dur - k; n.fonte = (c.fonte || 0) + (c.midia ? k * (c.vel || 1) : 0); if (c.link) n.link = nl[c.link] || (nl[c.link] = rid()); c.dur = k; P.clipes.push(n); } });
		status("Dividido em " + tcode(t, P.fps));
	}
	function fecharBuraco() {
		const t = ED.t, v = P.clipes.filter((c) => c.faixa === "V1" && !c.off);
		if (v.some((c) => t >= c.ini && t < c.ini + c.dur)) return false;
		const a = Math.max(0, ...v.filter((c) => c.ini + c.dur <= t + 1e-6).map((c) => c.ini + c.dur)), dep = v.filter((c) => c.ini >= t - 1e-6);
		if (!dep.length) return false;
		const b = Math.min(...dep.map((c) => c.ini)), d = b - a; if (d < 0.01) return false;
		if (P.clipes.some((c) => c.ini < b - 1e-6 && c.ini + c.dur > a + 1e-6 && !fstate(c.faixa).trava && c.faixa !== "MUS")) { status("Tem coisa em outra faixa dentro do buraco; apague antes ou mova", "err"); return true; }
		mexer(() => { for (const c of P.clipes) if (c.ini >= b - 1e-6 && !fstate(c.faixa).trava) c.ini -= d; for (const m of P.marcadores) if (m.t >= b) m.t -= d; });
		irPara(a); status("Buraco de " + d.toFixed(2) + " s fechado", "ok"); return true;
	}
	function apagar(puxar) {
		const al = sels().filter((c) => !fstate(c.faixa).trava); if (!al.length) { fecharBuraco(); return; }
		mexer(() => {
			P.clipes = P.clipes.filter((c) => !ED.sel.has(c.id));
			if (puxar) {
				// junta os intervalos apagados e puxa tudo que vem depois (em todas as faixas)
				const iv = al.map((c) => [c.ini, c.ini + c.dur]).sort((a, b) => a[0] - b[0]), m = [];
				for (const v of iv) { if (m.length && v[0] <= m[m.length - 1][1] + 1e-6) m[m.length - 1][1] = Math.max(m[m.length - 1][1], v[1]); else m.push(v.slice()); }
				for (let i = m.length - 1; i >= 0; i--) {
					const [a, b] = m[i], d = b - a;
					// só puxa se nada ficou dentro do buraco em V1/A1 (senão viraria sobreposição)
					for (const c of P.clipes) { if (c.ini >= b - 1e-6) c.ini -= d; }
					for (const mk of P.marcadores) if (mk.t >= b) mk.t -= d;
				}
			}
			ED.sel.clear();
		});
	}
	function marcador() { mexer(() => P.marcadores.push({ id: rid(), t: ED.t, txt: "" })); listaMarcas(); }
	function copiar() { const s = sels(); if (s.length) ED.copia = JSON.stringify(s); }
	function colar() {
		if (!ED.copia) return; const s = JSON.parse(ED.copia), base = Math.min(...s.map((c) => c.ini)), nl = {};
		mexer(() => { ED.sel.clear(); for (const c of s) { c.id = rid(); c.ini = ED.t + (c.ini - base); if (c.link) c.link = nl[c.link] || (nl[c.link] = rid()); P.clipes.push(c); ED.sel.add(c.id); } });
	}
	$("#tDividir").onclick = dividir; $("#tApagar").onclick = () => apagar(false); $("#tPuxar").onclick = () => apagar(true);
	$("#tDesfazer").onclick = desfazer; $("#tRefazer").onclick = refazer; $("#tMarca").onclick = marcador;
	$("#tIma").onclick = (e) => { ED.ima = !ED.ima; e.currentTarget.setAttribute("aria-pressed", ED.ima); };
	$("#bPlay").onclick = tocar; $("#bInicio").onclick = () => irPara(0);
	$("#bVolta").onclick = () => irPara(ED.t - 1 / P.fps); $("#bFrente").onclick = () => irPara(ED.t + 1 / P.fps);
	document.addEventListener("keydown", (e) => {
		if (e.target.closest("input,textarea,select,[contenteditable]")) return;
		const k = e.key, ctrl = e.ctrlKey || e.metaKey;
		if (k === " ") { e.preventDefault(); tocar(); }
		else if (ctrl && (k === "z" || k === "Z") && !e.shiftKey) { e.preventDefault(); desfazer(); }
		else if (ctrl && (k === "y" || ((k === "z" || k === "Z") && e.shiftKey))) { e.preventDefault(); refazer(); }
		else if (ctrl && (k === "c" || k === "C")) copiar();
		else if (ctrl && (k === "v" || k === "V")) colar();
		else if (ctrl && (k === "a" || k === "A")) { e.preventDefault(); P.clipes.forEach((c) => ED.sel.add(c.id)); ED.sujo = true; }
		else if (k === "s" || k === "S") { if (!ctrl) dividir(); else { e.preventDefault(); salvarJa(); status("Salvo neste navegador", "ok"); } }
		else if (k === "Delete" || k === "Backspace") { e.preventDefault(); apagar(e.shiftKey); }
		else if (k === "ArrowLeft") { e.preventDefault(); irPara(ED.t - (e.shiftKey ? 1 : 1 / P.fps)); }
		else if (k === "ArrowRight") { e.preventDefault(); irPara(ED.t + (e.shiftKey ? 1 : 1 / P.fps)); }
		else if (k === "Home") irPara(0); else if (k === "End") irPara(total());
		else if (k === "ArrowUp" || k === "ArrowDown") { e.preventDefault(); const pts = [...new Set(P.clipes.filter((c) => c.faixa === "V1" || ehVoz(c.faixa)).flatMap((c) => [c.ini, c.ini + c.dur]).map((x) => +x.toFixed(3)))].sort((a, b) => a - b); const t = ED.t; const p = k === "ArrowUp" ? pts.filter((x) => x < t - 1e-3).pop() : pts.find((x) => x > t + 1e-3); if (p != null) irPara(p); }
		else if (k === "l" || k === "L") { if (!ED.tocando) tocar(); }
		else if (k === "k" || k === "K") pausar();
		else if (k === "j" || k === "J") irPara(ED.t - 2);
		else if (k === "i" || k === "I") { P.entrada = ED.t; if (P.saida != null && P.saida <= P.entrada) P.saida = null; ED.sujo = true; salvarLogo(); status("Entrada em " + tcode(ED.t, P.fps) + " (a exportação usa só o trecho; X limpa)"); }
		else if (k === "o" || k === "O") { P.saida = ED.t; if (P.entrada != null && P.entrada >= P.saida) P.entrada = null; ED.sujo = true; salvarLogo(); status("Saída em " + tcode(ED.t, P.fps) + " (a exportação usa só o trecho; X limpa)"); }
		else if (k === "x" || k === "X") { P.entrada = P.saida = null; ED.sujo = true; salvarLogo(); status("Trecho limpo: a exportação usa o vídeo inteiro"); }
		else if (k === "m" || k === "M") marcador();
		else if (k === "f" || k === "F") telaCheia();
		else if (k === "+" || k === "=") { $("#tZoom").value = +$("#tZoom").value + 6; $("#tZoom").oninput({ target: $("#tZoom") }); }
		else if (k === "-") { $("#tZoom").value = +$("#tZoom").value - 6; $("#tZoom").oninput({ target: $("#tZoom") }); }
		else if (k === "Escape") { ED.sel.clear(); ED.alvoFoco = null; mostrarInspetor(); ED.sujo = true; }
	});

	/* ---------- mídia ---------- */
	async function decodificarArquivoAudio(file) {
		ac();
		const b = await AC.decodeAudioData(await file.arrayBuffer());
		const m = b.getChannelData(0), sr = b.sampleRate, hop = Math.round(sr * 0.01), n = Math.floor(m.length / hop), rms = new Float32Array(n);
		for (let i = 0; i < n; i++) { let s = 0; for (let k = 0; k < hop; k++) { const v = m[i * hop + k]; s += v * v; } rms[i] = 10 * Math.log10(s / hop + 1e-12); }
		return { buf: b, rms, dur: b.duration };
	}
	function durVideo(url) { return new Promise((ok) => { const v = document.createElement("video"); v.preload = "metadata"; v.onloadedmetadata = () => ok({ dur: v.duration, w: v.videoWidth, h: v.videoHeight }); v.onerror = () => ok(null); v.src = url; }); }
	async function carregarMidia(mid, file, onp) {
		const m = P.midias[mid], rt = RT[mid] = RT[mid] || {};
		rt.file = file;
		if (m.tipo === "imagem") { rt.img = await createImageBitmap(file); rt.dur = Infinity; return; }
		if (m.tipo === "audio") { const a = await decodificarArquivoAudio(file); Object.assign(rt, a); m.dur = a.dur; return; }
		rt.url = URL.createObjectURL(file);
		let mp = null;
		try { mp = await MP4.abrir(file); } catch (e) { mp = null; if (m.bruto) throw e; }
		rt.mp4 = mp;
		const meta = await durVideo(rt.url);
		m.dur = (mp && mp.duracao) || (meta && meta.dur) || m.dur || 0; rt.dur = m.dur;
		if (mp && mp.video) { m.w = mp.video.width; m.h = mp.video.height; } else if (meta) { m.w = meta.w; m.h = meta.h; }
		rt.aud = [];
		if (mp) {
			m.nAud = mp.audios.length;
			for (let i = 0; i < mp.audios.length; i++) {
				const k = i, tr = mp.audios[i];
				rt.aud[i] = await MP4.audioMono(mp, tr, (f) => onp && onp(`Lendo o áudio ${k + 1} de ${mp.audios.length}: ${Math.round(f * 100)}%`));
			}
		}
	}
	function itemMidia(mid) {
		const m = P.midias[mid], li = document.createElement("li");
		li.draggable = true; li.dataset.mid = mid;
		li.innerHTML = `<span class="ic">${m.tipo === "video" ? (m.bruto ? "🎬" : "🎞") : m.tipo === "audio" ? (m.papel === "MUS" ? "🎵" : "🔊") : "🖼"}</span><span class="nm"></span><small>${m.dur && isFinite(m.dur) ? curto(m.dur) : ""}</small>`;
		li.querySelector(".nm").textContent = m.nome; li.title = "Arraste para a linha do tempo, ou clique duas vezes para pôr no cursor";
		if (!RT[mid]) li.classList.add("carregando");
		li.addEventListener("dragstart", (e) => { e.dataTransfer.setData("text/ep-midia", mid); e.dataTransfer.effectAllowed = "copy"; });
		li.addEventListener("dblclick", () => inserir(mid, null, ED.t));
		return li;
	}
	function listaMidias() { const ul = $("#midias"); ul.replaceChildren(...Object.keys(P.midias).map(itemMidia)); }
	function faixaPadrao(m) { return m.tipo === "audio" ? (m.papel === "VOZ" ? (P.vozes[0] || {}).id || "SFX" : m.papel || "SFX") : m.bruto ? "V1" : "V2"; }
	function inserir(mid, fid, t) {
		const m = P.midias[mid]; if (!m) return;
		fid = fid || faixaPadrao(m);
		const ft = faixa(fid).tipo;
		if (m.tipo === "audio" && ft !== "audio") fid = faixaPadrao(m);
		if (m.tipo !== "audio" && ft === "audio") fid = m.bruto ? "V1" : "V2";
		const dur = m.tipo === "imagem" ? 3 : m.dur || 3;
		mexer(() => {
			ED.sel.clear();
			if (m.tipo === "video" && (fid === "V1" || m.bruto) && m.nAud) {
				const link = rid();
				const v = { id: rid(), faixa: "V1", midia: mid, ini: t, dur, fonte: 0, link }; P.clipes.push(v); ED.sel.add(v.id);
				for (let i = 0; i < m.nAud; i++) {
					const nomes = ["Problems", "Call", "Jogo"];
					// continuação da mesma gravação (outro arquivo do OBS): a faixa i cai na mesma voz da faixa i do primeiro bruto
					let v = P.vozes.find((q) => q.trilha && q.trilha.m === m.nome && q.trilha.i === i) || P.vozes.find((q) => q.trilha && q.trilha.i === i && !q.daCall && Object.values(P.midias).some((o) => o.bruto && o.nome === q.trilha.m)) || P.vozes.find((q) => !q.trilha && !P.clipes.some((c) => c.faixa === q.id));
					if (!v) v = novaVoz(nomes[i] || "Faixa " + (i + 1), i === 2 ? "jogo" : "voz");
					if (!v.trilha) v.trilha = { m: m.nome, i };
					const a = { id: rid(), faixa: v.id, midia: mid, trilha: i, ini: t, dur, fonte: 0, link, vol: 0 }; P.clipes.push(a); ED.sel.add(a.id);
				}
				montarFaixas(); cabecalhos();
			} else {
				const c = { id: rid(), faixa: fid, midia: mid, ini: t, dur, fonte: 0, vol: m.tipo === "audio" ? ganhoPadrao(m) : 0 };
				if (fid === "V2") c.tr = { s: 1, x: 0, y: 0, op: 1 };
				P.clipes.push(c); ED.sel.add(c.id);
			}
		});
		mostrarInspetor();
	}
	/* ganho FIXO dos SFX: tabela que o editor calibrou (sfx_levels.py GAIN_DB); música: cama de −26 dB */
	const GANHO = [["anime-shine-sound-2", -6.9], ["anime-shine-sound-effect_QP4", -7.3], ["anime-wow", -10.4], ["bamboo-hit", -10.7], ["record-scratch", -17], ["sudden-suspense", -22.3], ["nintendo-switch", -3.2], ["spongebob-fail", -17.5], ["mc-random-drink", -5.5], ["cartoon-boing", -2.3], ["clown-horn", -19.8], ["anvil", -10.8], ["wrong_5", -8.1], ["bruh", -18], ["perfect-fart", -10.5], ["vine-boom", -7.1], ["mc-random-burp", 0.8], ["mc-xp-orb", 7], ["Whoosh 39", 0], ["bass-impact", 0], ["impact_water", -10.5], ["minecraft-drinking", -4.6], ["minecraft_click", 10]];
	function ganhoPadrao(m) {
		if (m.papel === "MUS") return -26;
		const g0 = GANHO.find(([k]) => m.nome.toLowerCase().includes(k.toLowerCase()));
		if (g0) return g0[1];
		// arquivo novo: RMS ativo −25 dBFS (curto) / −31 (longo), pico ≤ −5
		const rt = RT[m.id]; if (!rt || !rt.rms) return -8;
		let pk = -90, s = 0, n = 0; for (const v of rt.rms) { if (v > pk) pk = v; if (v > -45) { s += Math.pow(10, v / 10); n++; } }
		const ativo = n ? 10 * Math.log10(s / n) : -30;
		return +Math.min((m.dur <= 0.9 ? -25 : -31) - ativo, -5 - pk).toFixed(1);
	}
	window.ED_GANHO = ganhoPadrao;
	async function adicionarArquivos(files, papel, bruto) {
		for (const file of files) {
			const tipo = /^video\//.test(file.type) || /\.(mp4|mov|m4v|webm)$/i.test(file.name) ? "video" : /^audio\//.test(file.type) || /\.(mp3|wav|ogg|m4a|aac|flac|opus)$/i.test(file.name) ? "audio" : /^image\//.test(file.type) ? "imagem" : null;
			if (!tipo) continue;
			const mid = rid(), m = { id: mid, nome: file.name, tipo, dur: 0, bruto: !!bruto, papel: tipo === "audio" ? papel || (file.size > 3e6 ? "MUS" : "SFX") : undefined, tam: file.size };
			P.midias[mid] = m; listaMidias();
			status("Abrindo " + file.name + "…");
			try {
				await carregarMidia(mid, file, (s) => status(s));
				// guarda o arquivo: pequeno vai inteiro para o banco do navegador; grande fica no PC (só a alça)
				if (file.size < 60e6) await DB.set("arq:" + mid, file);
				else if (file.handle) await DB.set("alca:" + mid, file.handle);
				status(file.name + " pronto", "ok");
			} catch (e) {
				console.error(e); delete P.midias[mid]; delete RT[mid];
				aviso("Não consegui abrir " + file.name, String(e && e.message || e)); status("", "");
			}
			listaMidias(); salvarLogo();
			if (bruto && P.midias[mid]) { if (!P.clipes.some((c) => c.faixa === "V1")) { inserir(mid, "V1", 0); caber(); } else inserir(mid, "V1", total()); $("#vazio").hidden = true; }
		}
	}
	/* alguns navegadores (o do app do Claude, por exemplo) abrem o seletor moderno mas não deixam ler o arquivo:
	   aí usamos o seletor clássico (o bruto não fica lembrado entre aberturas, mas funciona) */
	const semAlca = () => { try { return /\bClaude\//.test(navigator.userAgent) || localStorage.getItem("ep:semFSA") === "1"; } catch (_) { return false; } };
	async function escolher(input, multi, tipos) {
		if (window.showOpenFilePicker && !semAlca()) {
			let hs;
			try { hs = await showOpenFilePicker({ multiple: multi, types: tipos }); } catch (e) { if (e.name === "AbortError") return []; }
			if (hs) {
				try { return await Promise.all(hs.map(async (h) => { const f = await h.getFile(); f.handle = h; return f; })); }
				catch (e) { try { localStorage.setItem("ep:semFSA", "1"); } catch (_) {} aviso("Clique de novo para escolher o arquivo", "Este navegador não deixou ler o arquivo pelo seletor novo. Na próxima vez o editor usa o seletor clássico."); return []; }
			}
		}
		return new Promise((ok) => { input.onchange = () => { ok(Array.from(input.files)); input.value = ""; }; input.click(); });
	}
	/* voz de um personagem gravada à parte (Craig, cada um gravando o seu): vira uma faixa com o nome do personagem, no começo do bruto */
	const chaveArq = (nome) => nome.toLowerCase().replace(/\.[^.]+$/, "").replace(/^\d+[-_ ]+/, "").replace(/[_-]\d+$/, "").trim();
	const lerQuem = () => { try { return JSON.parse(localStorage.getItem("ep:edicao:quem") || "{}"); } catch (_) { return {}; } };
	function lembrarQuem(arq, nome) { if (!arq) return; const m = lerQuem(); m[chaveArq(arq)] = nome; try { localStorage.setItem("ep:edicao:quem", JSON.stringify(m)); } catch (_) {} }
	async function adicionarVozes(files) {
		/* 1) abre todos os arquivos */
		const novos = [];
		for (const file of files) {
			const nomeArq = file.name.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, ""), pers = PERSONAGENS.find((n) => nomeArq.includes(n.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "")));
			const mid = rid(), m = { id: mid, nome: file.name, tipo: "audio", papel: "VOZ", dur: 0, tam: file.size };
			P.midias[mid] = m; listaMidias(); status("Abrindo " + file.name + "…");
			try { await carregarMidia(mid, file); if (file.size < 60e6) await DB.set("arq:" + mid, file); else if (file.handle) await DB.set("alca:" + mid, file.handle); }
			catch (e) { delete P.midias[mid]; aviso("Não consegui abrir " + file.name, String(e.message || e)); continue; }
			novos.push({ mid, m, pers: lerQuem()[chaveArq(file.name)] || pers, file });
		}
		if (!novos.length) return;
		/* 2) encaixe automático: compara com as faixas de voz do bruto (a pessoa aparece na call ou vaza no microfone) */
		const v1s = P.clipes.filter((c) => c.faixa === "V1" && c.midia && RT[c.midia] && RT[c.midia].aud).sort((a, b) => a.ini - b.ini);
		if (v1s.length && window.ED_SINC) {
			const bm = v1s[0].midia, refs = [];
			for (const q of P.vozes) { if (q.papel === "jogo" || !q.trilha || !RT[bm].aud[q.trilha.i]) continue; refs.push({ nome: q.id, rms: RT[bm].aud[q.trilha.i].rms }); }
			if (!refs.length) RT[bm].aud.forEach((a, i) => refs.push({ nome: "A" + (i + 1), rms: a.rms }));
			for (const n of novos) { status("Encaixando " + n.file.name + " no bruto…"); await new Promise((r) => setTimeout(r, 0)); try { n.sinc = RT[n.mid].rms ? window.ED_SINC(RT[n.mid].rms, refs) : null; } catch (e) { n.sinc = null; } }
			// arquivos do mesmo gravador começam juntos: a maioria concordando vale para todos
			const cons = novos.length >= 2 && window.ED_SINC_CONSENSO(novos.map((n) => n.sinc));
			for (const n of novos) { if (cons) n.off = cons.off, n.ref = cons.ref; else if (n.sinc && n.sinc.certo) n.off = n.sinc.off, n.ref = n.sinc.ref; }
		}
		/* 3) põe cada voz na sua faixa: um pedaço para cada pedaço do bruto (funciona antes ou depois dos cortes) */
		const encaixados = [];
		mexer(() => {
			for (const n of novos) {
				const v = novaVoz(n.pers || n.file.name.replace(/\.[^.]+$/, "").slice(0, 18), "voz"); v.arquivo = n.file.name;
				if (n.off != null) {
					for (const c of v1s.filter((q) => q.midia === v1s[0].midia)) {
						const vel = c.vel || 1; let ini = c.ini, dur = c.dur, fonte = c.fonte - n.off;
						if (fonte < 0) { ini += -fonte / vel; dur -= -fonte / vel; fonte = 0; }
						if (fonte + dur * vel > n.m.dur) dur = (n.m.dur - fonte) / vel;
						if (dur > 0.02) P.clipes.push({ id: rid(), faixa: v.id, midia: n.mid, ini, dur, fonte, vel: c.vel, vol: 0, link: c.link });
					}
					v.sinc = { off: +n.off.toFixed(3), ref: n.ref }; encaixados.push(n);
				} else P.clipes.push({ id: rid(), faixa: v.id, midia: n.mid, ini: 0, dur: n.m.dur, fonte: 0, vol: 0 });
			}
			// chegou o pacote (2+ vozes encaixadas): a call misturada fica silenciada (some sem apagar)
			if (encaixados.length >= 2) { const ref = encaixados[0].ref; if (ref && ref !== (P.vozes[0] || {}).id) fstate(ref).mudo = true; }
		});
		listaMidias(); cabecalhos(); salvarLogo();
		const falhou = novos.filter((n) => n.off == null);
		if (!falhou.length) status(`${encaixados.length} ${encaixados.length > 1 ? "vozes encaixadas" : "voz encaixada"} sozinha${encaixados.length > 1 ? "s" : ""} (${encaixados[0].off >= 0 ? "+" : ""}${encaixados[0].off.toFixed(2)} s)` + (encaixados.length >= 2 ? "; a call misturada ficou silenciada" : ""), "ok");
		else status(`${falhou.map((n) => n.file.name).join(", ")}: não achei o encaixe com certeza; ficou no começo (arraste para acertar)`, "err");
	}
	$("#addVoz").onclick = async () => adicionarVozes(await escolher($("#fVoz"), true, [{ description: "Voz (áudio)", accept: { "audio/*": [".wav", ".mp3", ".flac", ".ogg", ".m4a", ".opus"] } }]));
	$("#abrirBruto").onclick = async () => {
		if (P.clipes.some((c) => c.faixa === "V1")) {
			const r = await perguntar("Este projeto já tem um bruto", "O arquivo novo é a continuação da mesma gravação, ou é outro vídeo?", [["novo", "Outro vídeo (projeto novo)"], ["junta", "Continuação (junta no fim)"]]);
			if (!r) return;
			if (r === "novo") projetoNovo();
		}
		adicionarArquivos(await escolher($("#fBruto"), false, [{ description: "Bruto (MP4)", accept: { "video/mp4": [".mp4", ".m4v"], "video/quicktime": [".mov"] } }]), null, true);
	};
	$("#addArq").onclick = async () => adicionarArquivos(await escolher($("#fArq"), true, [{ description: "Vídeo, áudio ou imagem", accept: { "video/*": [".mp4", ".mov", ".webm"], "audio/*": [".mp3", ".wav", ".ogg", ".m4a"], "image/*": [".png", ".jpg", ".webp", ".gif"] } }]));
	// soltar arquivos na prévia (vira bruto se for o primeiro vídeo) ou na linha do tempo
	for (const alvo of [$("#prev"), area]) {
		alvo.addEventListener("dragover", (e) => { e.preventDefault(); alvo.classList.add("solta"); });
		alvo.addEventListener("dragleave", () => alvo.classList.remove("solta"));
		alvo.addEventListener("drop", async (e) => {
			e.preventDefault(); alvo.classList.remove("solta");
			const mid = e.dataTransfer.getData("text/ep-midia"), bib = e.dataTransfer.getData("text/ep-bib");
			const R = tl.getBoundingClientRect(), h = alvo === area ? acertar(e.clientX - R.left, e.clientY - R.top) : null;
			if (mid) { inserir(mid, h && h.faixa, h ? Math.max(0, grudar(h.t, pontosIma(new Set()))) : ED.t); return; }
			if (bib) { const nm = await BIB.importar(bib); if (nm) inserir(nm, h && h.faixa, h ? Math.max(0, h.t) : ED.t); return; }
			const fs = [];
			if (e.dataTransfer.items) for (const it of e.dataTransfer.items) { if (it.kind !== "file") continue; const f = it.getAsFile(); try { if (it.getAsFileSystemHandle) f.handle = await it.getAsFileSystemHandle(); } catch (_) {} fs.push(f); }
			const temV1 = P.clipes.some((c) => c.faixa === "V1");
			const vids = fs.filter((f) => /\.(mp4|mov|m4v)$/i.test(f.name)), resto = fs.filter((f) => !vids.includes(f));
			if (vids.length) await adicionarArquivos(vids, null, !temV1 || (h && h.faixa === "V1"));
			if (resto.length) await adicionarArquivos(resto, h && (h.faixa === "MUS" || h.faixa === "SFX") ? h.faixa : null, false);
		});
	}

	/* ---------- biblioteca local (pastas de SFX e de músicas do PC) ---------- */
	const BIB = {
		itens: [],
		async pasta(papel) {
			if (!window.showDirectoryPicker || semAlca()) {
				/* seletor clássico de pasta: vale só enquanto a página estiver aberta */
				const inp = document.createElement("input"); inp.type = "file"; inp.webkitdirectory = true; inp.multiple = true;
				inp.onchange = () => {
					const out = Array.from(inp.files).filter((f) => /\.(mp3|wav|ogg|m4a|flac)$/i.test(f.name)).map((f) => { const cam = (f.webkitRelativePath || f.name).split("/"); return { papel, nome: f.name, pasta: cam.slice(1, -1).join("/") + (cam.length > 2 ? "/" : ""), h: { getFile: async () => f } }; });
					this.itens = this.itens.filter((x) => x.papel !== papel).concat(out); status(out.length + (papel === "MUS" ? " músicas" : " sons") + " na biblioteca", "ok"); this.mostrar();
				};
				inp.click(); return;
			}
			let dir; try { dir = await showDirectoryPicker({ id: "ep-" + papel, mode: "read" }); } catch (e) { return; }
			await DB.set("pasta:" + papel, dir); await this.ler(papel, dir); this.mostrar();
		},
		async ler(papel, dir) {
			const out = [];
			const andar = async (d, pre) => { for await (const [n, h] of d.entries()) { if (h.kind === "directory") { if (pre.split("/").length < 4) await andar(h, pre + n + "/"); } else if (/\.(mp3|wav|ogg|m4a|flac)$/i.test(n)) out.push({ papel, nome: n, pasta: pre, h }); } };
			await andar(dir, ""); this.itens = this.itens.filter((x) => x.papel !== papel).concat(out);
			status(out.length + (papel === "MUS" ? " músicas" : " sons") + " na biblioteca", "ok");
		},
		async restaurar() { for (const papel of ["SFX", "MUS"]) { try { const d = await DB.get("pasta:" + papel); if (d && (await d.queryPermission({ mode: "read" })) === "granted") await this.ler(papel, d); else if (d) this.pendente = true; } catch (_) {} } this.mostrar(); },
		mostrar() {
			const q = ($("#bibBusca").value || "").toLowerCase(), ul = $("#bib");
			const l = this.itens.filter((x) => !q || (x.pasta + x.nome).toLowerCase().includes(q)).slice(0, 200);
			ul.replaceChildren(...l.map((x) => { const li = document.createElement("li"); li.draggable = true; li.innerHTML = `<span class="ic">${x.papel === "MUS" ? "🎵" : "🔊"}</span><span class="nm"></span><small></small>`; li.querySelector(".nm").textContent = x.nome; li.querySelector("small").textContent = x.pasta.replace(/\/$/, "").split("/").pop() || ""; li.title = x.pasta + x.nome + "\nClique para ouvir · arraste para a linha do tempo"; const key = x.papel + "|" + x.pasta + x.nome; li.addEventListener("dragstart", (e) => e.dataTransfer.setData("text/ep-bib", key)); li.addEventListener("click", () => this.ouvir(x)); li.addEventListener("dblclick", async () => { const mid = await this.importar(key); if (mid) inserir(mid, null, ED.t); }); return li; }));
		},
		async ouvir(x) { try { if (this.aud) this.aud.pause(); const f = await x.h.getFile(); this.aud = new Audio(URL.createObjectURL(f)); this.aud.volume = 0.6; this.aud.play(); } catch (_) {} },
		achar(key) { return this.itens.find((x) => x.papel + "|" + x.pasta + x.nome === key); },
		async importar(key) {
			const x = this.achar(key); if (!x) return null;
			const ja = Object.values(P.midias).find((m) => m.bib === key); if (ja && RT[ja.id]) return ja.id;
			const f = await x.h.getFile(), mid = rid();
			P.midias[mid] = { id: mid, nome: x.nome, tipo: "audio", papel: x.papel, bib: key, dur: 0, pasta: x.pasta };
			try { await carregarMidia(mid, f); if (f.size < 60e6) await DB.set("arq:" + mid, f); } catch (e) { delete P.midias[mid]; aviso("Não consegui abrir " + x.nome, String(e.message || e)); return null; }
			listaMidias(); salvarLogo(); return mid;
		},
	};
	window.ED_BIB = BIB;
	$("#pastaSfx").onclick = () => BIB.pasta("SFX"); $("#pastaMus").onclick = () => BIB.pasta("MUS");
	$("#bibBusca").oninput = () => BIB.mostrar();

	/* ---------- efeitos, zoom e texto ---------- */
	function addItem(faixaId, base) { const c = Object.assign({ id: rid(), faixa: faixaId, ini: ED.t, dur: 1 }, base); mexer(() => { ED.sel.clear(); P.clipes.push(c); ED.sel.add(c.id); }); mostrarInspetor(); return c; }
	const RECEITAS = {
		zoomSeco: () => addItem("Z", { dur: 2, p: { de: 1.25, para: 1.25, anim: 0, fx: 0.5, fy: 0.5 } }),
		zoomAnim: () => addItem("Z", { dur: 2.5, p: { de: 1, para: 1.38, anim: 0.8, fx: 0.5, fy: 0.5 } }),
		zoomFala: () => addItem("Z", { dur: 1.6, p: { de: 2.5, para: 2.5, anim: 0, fx: 0.5, fy: 0.45 } }),
		esticar: () => { const c = addItem("Z", { dur: 1.2, p: { de: 1, para: 3.9, paraY: 2.58, anim: 0.15, fx: 0.5, fy: 0.5 } }); addItem("FX", { tipo: "vhs", ini: c.ini, dur: 1.2, p: {} }); },
		flash: () => addItem("FX", { tipo: "flash", dur: 0.9, p: { cor: "#ffffff", forca: 0.7 } }),
		flashV: () => addItem("FX", { tipo: "flash", dur: 0.6, p: { cor: "#ff2a2a", forca: 0.55 } }),
		shake: () => addItem("FX", { tipo: "shake", dur: 0.6, p: { forca: 26 } }),
		vhs: () => addItem("FX", { tipo: "vhs", dur: 1.4, p: {} }),
		flashback: () => addItem("FX", { tipo: "flashback", dur: 5, p: {} }),
		tilt: () => addItem("FX", { tipo: "tilt", dur: 2.4, p: { anim: 2 } }),
		brilho: () => addItem("FX", { tipo: "brilho", dur: 1.8, p: { fx: 0.5, fy: 0.5 } }),
		pb: () => addItem("FX", { tipo: "pb", dur: 2, p: {} }),
		vinheta: () => addItem("FX", { tipo: "vinheta", dur: 3, p: { forca: 0.6 } }),
		preto: () => addItem("FX", { tipo: "preto", ini: Math.max(0, ED.t - 0.6), dur: 1.2, p: {} }),
		cor: () => addItem("FX", { tipo: "cor", dur: 5, p: { brilho: 0, contraste: 10, saturacao: 15, temperatura: 0 } }),
		dissolver: () => {
			const cs = P.clipes.filter((c) => c.faixa === "V1" && !c.off && P.clipes.some((p) => p.faixa === "V1" && p !== c && !p.off && Math.abs(p.ini + p.dur - c.ini) < 1e-3));
			const c = cs.sort((a, b) => Math.abs(a.ini - ED.t) - Math.abs(b.ini - ED.t))[0];
			if (!c) { status("Não tem corte no bruto perto do cursor", "err"); return; }
			mexer(() => { c.trans = { tipo: "dissolver", dur: 0.5 }; ED.sel.clear(); ED.sel.add(c.id); }); irPara(c.ini); mostrarInspetor(); status("Dissolver no corte de " + tcode(c.ini, P.fps), "ok");
		},
		congelar: async () => {
			const c = clipeEm("V1", ED.t); const src = c && fontePrevia(c, ED.t); if (!src) { status("Ponha o cursor em cima do bruto para congelar", "err"); return; }
			const sw = src.videoWidth || src.width, sh = src.videoHeight || src.height, e = enqDe(c, sw, sh), cv = document.createElement("canvas"); cv.width = Math.round(e.w * sw); cv.height = Math.round(e.h * sh);
			cv.getContext("2d").drawImage(src, e.x * sw, e.y * sh, cv.width, cv.height, 0, 0, cv.width, cv.height);
			const blob = await new Promise((ok) => cv.toBlob(ok, "image/png")), mid = rid(), nome = "Quadro " + tcode(ED.t, P.fps) + ".png";
			P.midias[mid] = { id: mid, nome, tipo: "imagem", dur: 0 }; RT[mid] = { img: await createImageBitmap(blob), dur: Infinity }; await DB.set("arq:" + mid, new File([blob], nome, { type: "image/png" }));
			listaMidias(); addItem("V2", { midia: mid, dur: 2, fonte: 0, tr: { s: 1, x: 0, y: 0, op: 1 } });
		},
		texto: () => addItem("T", { dur: 2, txt: { texto: "TEXTO", cor: "#ffffff", tam: 110, x: 0.5, y: 0.2, anim: "pop" } }),
	};
	$$("[data-fx]").forEach((b) => b.addEventListener("click", () => RECEITAS[b.dataset.fx]()));
	window.ED_RECEITAS = RECEITAS;

	/* ---------- propriedades (painel da direita) ---------- */
	function campoNum(rot, val, min, max, passo, set, unid) {
		const d = document.createElement("label"); d.className = "campo";
		d.innerHTML = `<span>${rot}</span><div class="linha"><input type="range" min="${min}" max="${max}" step="${passo}"><input type="number" min="${min}" max="${max}" step="${passo}" style="max-width:76px"></div>`;
		const [r, n] = d.querySelectorAll("input"); r.value = n.value = val;
		let iniciou = false;
		const ap = (v) => { v = clamp(+v, min, max); if (!isFinite(v)) return; if (!iniciou) { ED.desfazer.push(foto()); ED.refazer = []; iniciou = true; } set(v); r.value = n.value = v; ED.sujo = true; salvarLogo(); };
		r.oninput = () => ap(r.value); n.onchange = () => ap(n.value); r.onchange = () => { iniciou = false; if (ED.tocando) reprogramarAudio(); };
		if (unid) d.querySelector("span").textContent += " (" + unid + ")";
		return d;
	}
	function campoKf(c, grupo, prop, rot, min, max, passo, unid) {
		const base = { s: 1, x: 0, y: 0, r: 0, op: 1 }[prop], lt = () => clamp(ED.t - c.ini, 0, c.dur);
		const temKf = () => c.kf && c.kf[prop] && c.kf[prop].length;
		const valor = () => +(temKf() ? valKf(c, prop, lt(), base) : (c.tr && c.tr[prop] != null ? c.tr[prop] : base)).toFixed(3);
		const d = campoNum(rot + (temKf() ? " ◆" + c.kf[prop].length : ""), valor(), min, max, passo, (v) => grupo.forEach((q) => {
			if (q.kf && q.kf[prop] && q.kf[prop].length) { const L = q.kf[prop], x = clamp(ED.t - q.ini, 0, q.dur), e = L.find((k) => Math.abs(k[0] - x) < 0.02); if (e) e[1] = v; else { L.push([x, v]); L.sort((a, b) => a[0] - b[0]); } }
			else (q.tr = q.tr || {})[prop] = v;
		}), unid);
		const b = document.createElement("button"); b.type = "button"; b.className = "btn small"; b.style.flex = "none";
		const aqui = temKf() && c.kf[prop].some((k) => Math.abs(k[0] - lt()) < 0.02);
		b.textContent = aqui ? "◆✕" : "◆"; b.title = aqui ? "Tirar o keyframe deste ponto" : "Marcar um keyframe neste ponto (com o valor atual)";
		b.onclick = () => { mexer(() => grupo.forEach((q) => { q.kf = q.kf || {}; const L = q.kf[prop] = q.kf[prop] || [], x = clamp(ED.t - q.ini, 0, q.dur), i = L.findIndex((k) => Math.abs(k[0] - x) < 0.02); if (i >= 0) L.splice(i, 1); else { L.push([x, valKf(q, prop, x, q.tr && q.tr[prop] != null ? q.tr[prop] : base)]); L.sort((a, b2) => a[0] - b2[0]); } if (!L.length) delete q.kf[prop]; })); mostrarInspetor(); };
		d.querySelector(".linha").appendChild(b);
		return d;
	}
	function botao(txt, fn, cls) { const b = document.createElement("button"); b.type = "button"; b.className = "btn small " + (cls || ""); b.textContent = txt; b.onclick = fn; return b; }
	function mostrarInspetor() {
		const ins = $("#ins"), s = sels(); ins.innerHTML = ""; ED.alvoFoco = null; $("#prev").classList.remove("alvo");
		const idSel = s.map((q) => q.id).join(","); if (idSel !== ED._insId) { ED.alvoPan = false; ED._insId = idSel; }
		if (!s.length) { $("#insTtl").textContent = "Propriedades"; ins.innerHTML = '<p class="hint">Selecione um clipe na linha do tempo.</p>'; return; }
		const c = s.find((q) => q.faixa === "V1") || s[0];
		$("#insTtl").textContent = s.length > 1 ? s.length + " clipes" : faixa(c.faixa).nome;
		const info = document.createElement("p"); info.className = "hint";
		info.textContent = `Início ${tcode(c.ini, P.fps)} · duração ${c.dur.toFixed(2)} s` + (c.midia ? " · " + ((P.midias[c.midia] || {}).nome || "") : "");
		ins.appendChild(info);
		const lig = document.createElement("label"); lig.className = "linha"; lig.innerHTML = `<input type="checkbox" style="flex:none"> <span>Desligado (some sem apagar)</span>`;
		const cb = lig.querySelector("input"); cb.checked = s.every((q) => q.off); cb.onchange = () => mexer(() => s.forEach((q) => { q.off = cb.checked; })); ins.appendChild(lig);
		const audios = s.filter((q) => faixa(q.faixa).tipo === "audio");
		if (audios.length) ins.appendChild(campoNum("Volume" + (audios.length > 1 ? " (" + audios.length + " clipes)" : ""), audios[0].vol || 0, -40, 15, 0.1, (v) => audios.forEach((q) => { q.vol = v; }), "dB"));
		const mus = audios.filter((q) => q.faixa !== "SFX");
		if (mus.length) { ins.appendChild(campoNum("Entrada suave", mus[0].fadeIn || 0, 0, 5, 0.1, (v) => mus.forEach((q) => { q.fadeIn = v || undefined; }), "s")); ins.appendChild(campoNum("Saída suave", mus[0].fadeOut || 0, 0, 5, 0.1, (v) => mus.forEach((q) => { q.fadeOut = v || undefined; }), "s")); }
		if (audios.some((q) => q.faixa === "SFX")) { const h = document.createElement("p"); h.className = "hint"; h.textContent = "SFX com ganho fixo, sem curva de volume (padrão do editor)."; ins.appendChild(h); }
		const comMidia = s.filter((q) => q.midia && (faixa(q.faixa).tipo === "audio" || q.faixa === "V1" || q.faixa === "V2"));
		if (comMidia.length) {
			const vel = comMidia[0].vel || 1;
			/* muda a velocidade e puxa (ou empurra) o que vem depois, sem deixar buraco */
			const comVel = (v, extra) => mexer(() => {
				const fimAntes = Math.max(...comMidia.map((q) => q.ini + q.dur));
				comMidia.forEach((q) => { const old = q.vel || 1; q.dur = q.dur * old / v; q.vel = v === 1 ? undefined : v; if (extra) extra(q); });
				const d = Math.max(...comMidia.map((q) => q.ini + q.dur)) - fimAntes, ids = new Set(comMidia.map((q) => q.id));
				if (Math.abs(d) > 1e-4) { for (const o of P.clipes) if (!ids.has(o.id) && o.ini >= fimAntes - 1e-3) o.ini = Math.max(0, o.ini + d); for (const m of P.marcadores) if (m.t >= fimAntes) m.t += d; }
			});
			const mudarVel = (v) => comVel(v);
			const d = document.createElement("div"); d.className = "campo"; d.innerHTML = `<span>Velocidade (${vel}×)</span>`;
			const ch = document.createElement("div"); ch.className = "chips";
			for (const v of [0.5, 1, 1.5, 2, 4, 8]) { const b = document.createElement("button"); b.type = "button"; b.className = "chip"; b.setAttribute("aria-pressed", v === vel); b.textContent = v + "×"; b.onclick = () => { mudarVel(v); mostrarInspetor(); }; ch.appendChild(b); }
			d.appendChild(ch); ins.appendChild(d);
			if (comMidia.some((q) => q.faixa === "V1")) ins.appendChild(botao("⏩ Time lapse (4×, sem voz)", () => { comVel(4, (q) => { if (faixa(q.faixa).tipo === "audio") q.off = true; }); mostrarInspetor(); }));
		}
		const ligaveis = s.filter((q) => q.midia);
		if (ligaveis.some((q) => q.link)) ins.appendChild(botao("⛓ Separar áudio do vídeo", () => { mexer(() => ligaveis.forEach((q) => { delete q.link; })); mostrarInspetor(); }));
		else if (ligaveis.length > 1 && ligaveis.every((q) => Math.abs(q.ini - ligaveis[0].ini) < 1e-3 && Math.abs(q.dur - ligaveis[0].dur) < 1e-3)) ins.appendChild(botao("🔗 Ligar (andam juntos)", () => { const l = rid(); mexer(() => ligaveis.forEach((q) => { q.link = l; })); mostrarInspetor(); }));
		const vids = s.filter((q) => q.faixa === "V1" || q.faixa === "V2");
		if (vids.length) {
			const m = P.midias[vids[0].midia] || {};
			const sel = document.createElement("label"); sel.className = "campo"; sel.innerHTML = '<span>Enquadramento</span><select><option value="auto">Automático (jogo na metade direita quando o bruto é largo)</option><option value="dir">Metade direita</option><option value="esq">Metade esquerda</option><option value="tudo">Imagem inteira</option></select>';
			const se = sel.querySelector("select"); const e = vids[0].enq; se.value = !e ? "auto" : e.x === 0.5 && e.w === 0.5 ? "dir" : e.x === 0 && e.w === 0.5 ? "esq" : "tudo";
			se.onchange = () => mexer(() => vids.forEach((q) => { q.enq = se.value === "auto" ? undefined : se.value === "dir" ? { x: 0.5, y: 0, w: 0.5, h: 1 } : se.value === "esq" ? { x: 0, y: 0, w: 0.5, h: 1 } : { x: 0, y: 0, w: 1, h: 1 }; }));
			ins.appendChild(sel);
			if (m.w) { const h = document.createElement("p"); h.className = "hint"; h.textContent = `Fonte ${m.w}×${m.h}`; ins.appendChild(h); }
			const v1 = vids.filter((q) => q.faixa === "V1");
			if (v1.length === 1 || (v1.length && v1.every((q) => q.link === v1[0].link))) {
				const c1 = v1[0], ant = P.clipes.find((p) => p.faixa === "V1" && !p.off && p !== c1 && Math.abs(p.ini + p.dur - c1.ini) < 1e-3);
				if (ant) {
					const tl = document.createElement("label"); tl.className = "campo"; tl.innerHTML = '<span>Entrada deste clipe</span><select><option value="">Corte seco</option><option value="dissolver">Dissolver</option></select>';
					const st = tl.querySelector("select"); st.value = c1.trans ? "dissolver" : ""; st.onchange = () => { mexer(() => { c1.trans = st.value ? { tipo: "dissolver", dur: 0.5 } : undefined; }); mostrarInspetor(); }; ins.appendChild(tl);
					if (c1.trans) ins.appendChild(campoNum("Tempo da dissolução", c1.trans.dur, 0.1, 3, 0.05, (v) => { c1.trans.dur = v; }, "s"));
				}
			}
			const dcor = document.createElement("details"); dcor.className = "det"; dcor.innerHTML = "<summary>Cor do clipe</summary>";
			const k0 = vids[0].cor || {};
			for (const [k, n] of [["brilho", "Brilho"], ["contraste", "Contraste"], ["saturacao", "Saturação"], ["temperatura", "Temperatura (frio ↔ quente)"]]) dcor.appendChild(campoNum(n, k0[k] || 0, -100, 100, 1, (v) => vids.forEach((q) => { (q.cor = q.cor || {})[k] = v; }), k === "temperatura" ? "" : "%"));
			ins.appendChild(dcor);
			const v2 = vids.filter((q) => q.faixa === "V2");
			if (v2.length) {
				const an = document.createElement("label"); an.className = "campo"; an.innerHTML = '<span>Entrada e saída</span><select><option value="">Corte seco</option><option value="pop">Pop (cresce e some)</option><option value="aparecer">Aparecer e sumir</option></select>';
				const sa = an.querySelector("select"); sa.value = v2[0].anim || ""; sa.onchange = () => mexer(() => v2.forEach((q) => { q.anim = sa.value || undefined; })); ins.appendChild(an);
				const c0 = v2[0], tr = c0.tr || (c0.tr = { s: 1, x: 0, y: 0, op: 1 });
				const h = document.createElement("p"); h.className = "hint"; h.textContent = "◆ marca um keyframe no cursor: com dois ou mais, o valor anda de um para o outro."; ins.appendChild(h);
				ins.appendChild(campoKf(c0, v2, "s", "Escala", 0.05, 6, 0.01, ""));
				ins.appendChild(campoKf(c0, v2, "x", "Posição X", -1.5, 1.5, 0.005, ""));
				ins.appendChild(campoKf(c0, v2, "y", "Posição Y", -1.5, 1.5, 0.005, ""));
				ins.appendChild(campoKf(c0, v2, "r", "Rotação", -180, 180, 0.5, "°"));
				ins.appendChild(campoKf(c0, v2, "op", "Opacidade", 0, 1, 0.01, ""));
				const crop = tr.crop || {};
				const dc = document.createElement("details"); dc.className = "det"; dc.innerHTML = "<summary>Recortar bordas</summary>";
				for (const [k, n] of [["l", "Esquerda"], ["r", "Direita"], ["t", "Topo"], ["b", "Baixo"]]) dc.appendChild(campoNum(n, Math.round((crop[k] || 0) * 100), 0, 90, 1, (v) => v2.forEach((q) => { const t2 = q.tr = q.tr || {}; (t2.crop = t2.crop || {})[k] = v / 100; }), "%"));
				ins.appendChild(dc);
			}
		}
		if (c.faixa === "Z") {
			const p = c.p || (c.p = {});
			ins.appendChild(campoNum("Zoom inicial", Math.round((p.de || 1) * 100), 50, 800, 1, (v) => { p.de = v / 100; }, "%"));
			ins.appendChild(campoNum("Zoom final", Math.round((p.para || 1) * 100), 50, 800, 1, (v) => { p.para = v / 100; }, "%"));
			if (p.paraY) ins.appendChild(campoNum("Altura final (esticar)", Math.round(p.paraY * 100), 50, 800, 1, (v) => { p.paraY = v / 100; }, "%"));
			ins.appendChild(campoNum("Tempo da animação (0 = seco)", p.anim || 0, 0, 6, 0.05, (v) => { p.anim = v; }, "s"));
			const h = document.createElement("p"); h.className = "hint"; h.textContent = "Clique na prévia para escolher o ponto do zoom. O zoom fica até o fim do clipe (sem voltar) e desacelera no fim."; ins.appendChild(h);
			const pan = document.createElement("div"); pan.className = "linha";
			const bPan = botao(ED.alvoPan ? "🎯 Clique no ponto final…" : p.fx2 != null ? "🎯 Mudar o ponto final do pan" : "🎯 Pan: escolher ponto final", () => { ED.alvoPan = !ED.alvoPan; mostrarInspetor(); });
			pan.appendChild(bPan); if (p.fx2 != null) pan.appendChild(botao("Sem pan", () => { mexer(() => { delete p.fx2; delete p.fy2; }); mostrarInspetor(); }));
			ins.appendChild(pan);
			ED.alvoFoco = ED.alvoPan ? { p: { get fx() { return p.fx2 == null ? p.fx : p.fx2; }, set fx(v) { p.fx2 = v; }, get fy() { return p.fy2 == null ? p.fy : p.fy2; }, set fy(v) { p.fy2 = v; ED.alvoPan = false; setTimeout(mostrarInspetor, 0); } } } : c; $("#prev").classList.add("alvo");
		}
		if (c.faixa === "FX") {
			const p = c.p || (c.p = {});
			const tipo = document.createElement("label"); tipo.className = "campo"; tipo.innerHTML = '<span>Efeito</span><select>' + Object.entries(FX_NOMES).map(([k, v]) => `<option value="${k}">${v}</option>`).join("") + "</select>";
			const st = tipo.querySelector("select"); st.value = c.tipo; st.onchange = () => mexer(() => { c.tipo = st.value; }); ins.appendChild(tipo);
			if (c.tipo === "flash") { const cor = document.createElement("label"); cor.className = "campo"; cor.innerHTML = '<span>Cor</span><input type="color">'; const ci = cor.querySelector("input"); ci.value = p.cor || "#ffffff"; ci.oninput = () => { p.cor = ci.value; ED.sujo = true; salvarLogo(); }; ins.appendChild(cor); ins.appendChild(campoNum("Força", p.forca == null ? 0.7 : p.forca, 0.1, 1, 0.01, (v) => { p.forca = v; })); }
			if (c.tipo === "shake") ins.appendChild(campoNum("Força", p.forca || 24, 2, 80, 1, (v) => { p.forca = v; }, "px"));
			if (c.tipo === "cor") for (const [k, n] of [["brilho", "Brilho"], ["contraste", "Contraste"], ["saturacao", "Saturação"], ["temperatura", "Temperatura (frio ↔ quente)"]]) ins.appendChild(campoNum(n, p[k] || 0, -100, 100, 1, (v) => { p[k] = v; }, k === "temperatura" ? "" : "%"));
			if (c.tipo === "vinheta") ins.appendChild(campoNum("Força", p.forca || 0.6, 0.1, 1, 0.01, (v) => { p.forca = v; }));
			if (c.tipo === "tilt") ins.appendChild(campoNum("Tempo para murchar", p.anim || 2, 0.3, 5, 0.1, (v) => { p.anim = v; }, "s"));
			if (c.tipo === "brilho") { const h = document.createElement("p"); h.className = "hint"; h.textContent = "Clique na prévia para pôr o brilho no lugar certo."; ins.appendChild(h); ED.alvoFoco = c; $("#prev").classList.add("alvo"); }
		}
		if (c.faixa === "T") {
			const x = c.txt || (c.txt = {});
			const ta = document.createElement("label"); ta.className = "campo"; ta.innerHTML = '<span>Texto</span><textarea rows="2"></textarea>'; const tx = ta.querySelector("textarea"); tx.value = x.texto || ""; tx.oninput = () => { x.texto = tx.value; ED.sujo = true; salvarLogo(); }; ins.appendChild(ta);
			const cor = document.createElement("label"); cor.className = "campo"; cor.innerHTML = '<span>Cor</span><input type="color">'; const ci = cor.querySelector("input"); ci.value = x.cor || "#ffffff"; ci.oninput = () => { x.cor = ci.value; ED.sujo = true; salvarLogo(); }; ins.appendChild(cor);
			ins.appendChild(campoNum("Tamanho", x.tam || 96, 20, 400, 1, (v) => { x.tam = v; }, "px"));
			const sel = (rot, chave, ops, padrao) => { const l = document.createElement("label"); l.className = "campo"; l.innerHTML = `<span>${rot}</span><select>${ops.map(([v, n]) => `<option value="${v}">${n}</option>`).join("")}</select>`; const se = l.querySelector("select"); se.value = x[chave] == null ? padrao : String(x[chave]); se.onchange = () => mexer(() => { x[chave] = se.value === "true" ? true : se.value === "false" ? false : se.value; }); return l; };
			const lin = document.createElement("div"); lin.className = "linha";
			lin.append(sel("Fonte", "fonte", [["lilita", "Lilita (canal)"], ["rubik", "Rubik"], ["mono", "Mono"]], "lilita"), sel("Animação", "anim", [["pop", "Pop"], ["deslizar", "Deslizar"], ["digitar", "Digitar"], ["aparecer", "Aparecer"], ["nenhum", "Nenhuma"]], "pop"));
			ins.appendChild(lin);
			const lin2 = document.createElement("div"); lin2.className = "linha";
			lin2.append(sel("Contorno", "contorno", [["#0a0a0a", "Preto"], ["#ffffff", "Branco"], ["nenhum", "Sem contorno"]], "#0a0a0a"), sel("Fundo", "caixa", [["false", "Sem fundo"], ["true", "Caixa escura"]], "false"));
			ins.appendChild(lin2);
			const pos = document.createElement("div"); pos.className = "chips";
			for (const [n, y] of [["Topo", 0.14], ["Meio", 0.5], ["Baixo", 0.84]]) { const b = document.createElement("button"); b.type = "button"; b.className = "chip"; b.textContent = n; b.onclick = () => mexer(() => { x.x = 0.5; x.y = y; }); pos.appendChild(b); }
			ins.appendChild(pos);
			const h = document.createElement("p"); h.className = "hint"; h.textContent = "Clique na prévia para posicionar o texto."; ins.appendChild(h); ED.alvoFoco = { p: { get fx() { return x.x; }, set fx(v) { x.x = v; }, get fy() { return x.y; }, set fy(v) { x.y = v; } } }; $("#prev").classList.add("alvo");
		}
		const acoes = document.createElement("div"); acoes.className = "linha"; acoes.append(botao("✂ Dividir", dividir), botao("🗑 Apagar", () => apagar(false))); ins.appendChild(acoes);
	}
	// clicar na prévia escolhe o ponto do zoom / brilho / texto
	tela.addEventListener("click", (e) => {
		if (!ED.alvoFoco) return; const R = tela.getBoundingClientRect(); const p = ED.alvoFoco.p;
		ED.desfazer.push(foto()); p.fx = clamp((e.clientX - R.left) / R.width, 0, 1); p.fy = clamp((e.clientY - R.top) / R.height, 0, 1); ED.sujo = true; salvarLogo();
	});

	/* ---------- marcadores ---------- */
	function listaMarcas() {
		const d = $("#marcas"); d.replaceChildren(...P.marcadores.slice().sort((a, b) => a.t - b.t).map((m) => { const r = document.createElement("div"); r.className = "marca"; r.innerHTML = `<button class="btn small" type="button" style="flex:none">${curto(m.t)}</button><input type="text" placeholder="nota"><button class="btn small" type="button" title="Apagar">✕</button>`; const [ir, ap] = r.querySelectorAll("button"); const inp = r.querySelector("input"); inp.value = m.txt || ""; inp.oninput = () => { m.txt = inp.value; salvarLogo(); }; ir.onclick = () => irPara(m.t); ap.onclick = () => { mexer(() => { P.marcadores = P.marcadores.filter((x) => x !== m); }); listaMarcas(); }; return r; }));
		if (!P.marcadores.length) d.innerHTML = '<p class="hint">Aperte M para marcar o ponto do cursor.</p>';
	}

	/* ---------- projeto ---------- */
	function aplicarProjeto() {
		montarFaixas();
		$("#pNome").value = P.nome; $("#pFps").value = P.fps; $("#pRes").value = P.w + "x" + P.h; $("#pQual").value = String(P.qualidade || 1); $("#nomeProj").textContent = "Estúdio Problems · " + P.nome;
		listaMidias(); listaMarcas(); cabecalhos(); mostrarInspetor(); $("#vazio").hidden = P.clipes.length > 0; ED.sujo = true;
	}
	$("#pNome").oninput = (e) => { P.nome = e.target.value || "Sem nome"; $("#nomeProj").textContent = "Estúdio Problems · " + P.nome; salvarLogo(); };
	$("#pFps").onchange = (e) => { P.fps = +e.target.value; salvarLogo(); };
	$("#pQual").onchange = (e) => { P.qualidade = +e.target.value; ED.sujo = true; salvarLogo(); };
	function telaCheia() { const el = $("#tela").parentElement; if (document.fullscreenElement) document.exitFullscreen(); else if (el.requestFullscreen) el.requestFullscreen().catch(() => {}); }
	$("#bTela").onclick = telaCheia;
	$("#pRes").onchange = (e) => { const [w, h] = e.target.value.split("x").map(Number); P.w = w; P.h = h; ED.sujo = true; salvarLogo(); };
	$("#pSalvar").onclick = () => { const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([JSON.stringify(P, null, 1)], { type: "application/json" })); a.download = (P.nome || "projeto").replace(/[^\w\- ]+/g, "") + ".editor"; a.click(); }; // arquivo do Editor (antes .edicao.json; os dois abrem)
	$("#pAbrir").onclick = () => { const i = $("#fProj"); i.onchange = async () => { const f = i.files[0]; i.value = ""; if (!f) return; try { const n = JSON.parse(await f.text()); if (!n.clipes) throw new Error("não é um projeto da Edição"); pausar(); await salvarJa(); for (const k in RT) delete RT[k]; P = Object.assign(novoProjeto(), n); if (!n.id) P.id = rid(); ED.desfazer = []; ED.refazer = []; ED.sel.clear(); aplicarProjeto(); fechaInicio(); await reabrir(false); salvarLogo(); } catch (e) { aviso("Projeto inválido", e.message); } }; i.click(); };
	function projetoNovo() { pausar(); P = novoProjeto(); ED.desfazer = []; ED.refazer = []; ED.sel.clear(); for (const k in RT) delete RT[k]; aplicarProjeto(); salvarLogo(); }
	$("#pNovo").onclick = async () => { await salvarJa(); projetoNovo(); fechaInicio(); }; // o atual continua na tela inicial
	/* reabre os arquivos do projeto: pequenos vêm do banco; grandes pela alça (pode pedir permissão uma vez) */
	async function reabrir(comGesto) {
		let falta = 0;
		for (const mid in P.midias) {
			if (RT[mid]) continue; const m = P.midias[mid];
			let f = await DB.get("arq:" + mid).catch(() => null);
			if (!f) { const h = await DB.get("alca:" + mid).catch(() => null); if (h) { let ok = (await h.queryPermission({ mode: "read" })) === "granted"; if (!ok && comGesto) ok = (await h.requestPermission({ mode: "read" })) === "granted"; if (ok) { f = await h.getFile(); f.handle = h; } } }
			if (!f) { falta++; continue; }
			try { status("Reabrindo " + m.nome + "…"); await carregarMidia(mid, f, (s) => status(s)); } catch (e) { falta++; }
		}
		$("#pReabrir").hidden = !falta; listaMidias(); ED.sujo = true;
		status(falta ? "Clique em Projeto › 🔓 Reabrir os arquivos (o navegador pede permissão uma vez)" : P.clipes.length ? "Projeto aberto" : "", falta ? "err" : "ok");
		if (falta) $$('[data-aba="proj"]')[0].click();
	}
	$("#pReabrir").onclick = () => reabrir(true);

	/* ---------- abas ---------- */
	$$(".aba").forEach((b) => b.addEventListener("click", () => { $$(".aba").forEach((x) => x.setAttribute("aria-selected", x === b)); $$("[data-painel]").forEach((p) => { p.hidden = p.dataset.painel !== b.dataset.aba; }); }));

	/* ---------- API para exportar.js e auto.js ---------- */
	window.ED = {
		get P() { return P; }, set P(v) { P = v; }, RT, ED, get FAIXAS() { return FAIXAS; }, ganhoFaixa, ehVoz, novaVoz, montarFaixas, cabecalhos, status, aviso, mexer, total, clipeEm, fstate, faixa, rid, dbLin, XF, colado, ganhoPadrao, inserir, adicionarArquivos, BIB, tcode, pausar, irPara, caber, salvarLogo,
		redesenhar: () => { listaMidias(); listaMarcas(); mostrarInspetor(); ED.sujo = true; },
	};
	function redesenharTudo() { listaMarcas(); mostrarInspetor(); ED.sujo = true; $("#vazio").hidden = P.clipes.length > 0; }

	/* ---------- tela inicial: projetos recentes (como a do Animador) ---------- */
	const dataTxt = (t) => { const d = new Date(t), h = new Date(); return d.toDateString() === h.toDateString() ? "hoje, " + d.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }) : d.toLocaleDateString("pt-BR", { day: "2-digit", month: "short", year: d.getFullYear() === h.getFullYear() ? undefined : "numeric" }); };
	const durTxt = (s) => { s = Math.round(s || 0); const m = Math.floor(s / 60); return m >= 60 ? Math.floor(m / 60) + "h" + String(m % 60).padStart(2, "0") : m + ":" + String(s % 60).padStart(2, "0"); };
	const escH = (t) => String(t == null ? "" : t).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
	(() => { const st = document.createElement("style"); st.textContent = `
#inicio{flex:1;overflow:auto;padding:18px 16px 60px}
.ini{max-width:1180px;margin:0 auto}
.ini-novo{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:12px;margin-bottom:26px}
.ini-novo button{display:flex;align-items:center;gap:14px;text-align:left;padding:16px 18px;border-radius:14px;border:1px solid var(--line);background:var(--panel);cursor:pointer;color:var(--fg)}
.ini-novo button:hover{border-color:var(--accent);background:var(--panel-2)}
.ini-novo button.pri{background:linear-gradient(140deg,color-mix(in srgb,var(--accent) 26%,var(--panel)),var(--panel) 70%);border-color:color-mix(in srgb,var(--accent) 50%,var(--line))}
.ini-novo .ic{width:46px;height:46px;flex:none;border-radius:13px;display:grid;place-items:center;color:#fff;background:linear-gradient(135deg,color-mix(in srgb,var(--accent) 28%,transparent),rgba(25,211,240,.14));border:1px solid color-mix(in srgb,var(--accent) 45%,transparent)}.ini-novo .ic svg{width:24px;height:24px}.ini-novo button:hover .ic{background:linear-gradient(135deg,var(--accent),#19d3f0);border-color:transparent}.ini-novo b{display:block;font-size:15px}.ini-novo small{color:var(--muted);font-size:12px}
.ini-sec{display:flex;align-items:center;gap:10px;margin:0 0 12px;font-size:12.5px;text-transform:uppercase;letter-spacing:1px;color:var(--muted);font-weight:600}
.ini-sec .grow{flex:1}.ini-sec input{text-transform:none;letter-spacing:0;height:32px;width:240px;max-width:50vw;background:var(--panel-2);border:1px solid var(--line);border-radius:8px;padding:0 10px;outline:none}
.ini-sec input:focus{border-color:var(--accent)}
.ini-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:14px}
.ini-card{position:relative;background:var(--panel);border:1px solid var(--line);border-radius:12px;overflow:hidden;cursor:pointer;transition:transform .15s,border-color .15s;text-align:left;padding:0;color:var(--fg)}
.ini-card:hover,.ini-card:focus-visible{border-color:var(--accent);transform:translateY(-2px);outline:none}
.ini-card .th{aspect-ratio:16/9;background:#000 center/cover no-repeat;display:grid;place-items:center;color:var(--muted);border-bottom:1px solid var(--line)}
.ini-card .in{padding:10px 12px}.ini-card b{display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:13.5px}.ini-card small{color:var(--muted);font-size:11.5px}
.ini-card .mn{position:absolute;top:6px;right:6px;width:28px;height:28px;border-radius:7px;border:0;background:rgba(0,0,0,.55);color:#fff;cursor:pointer;opacity:0;font-size:16px;line-height:1}
.ini-card:hover .mn,.ini-card:focus-within .mn{opacity:1}
.ini-pop{position:absolute;top:38px;right:6px;z-index:5;background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:4px;box-shadow:0 12px 30px rgba(0,0,0,.4);min-width:150px}
.ini-card .th svg{width:34px;height:34px;opacity:.6}.ini-pop button svg{width:15px;height:15px;flex:none}
.ini-pop button{display:flex;align-items:center;gap:9px;width:100%;text-align:left;background:none;border:0;padding:7px 10px;border-radius:7px;cursor:pointer;color:var(--fg)}.ini-pop button:hover{background:var(--panel-2)}
.ini-vazio{padding:28px;text-align:center;color:var(--muted);border:1px dashed var(--line);border-radius:12px}
.brand{cursor:pointer}`; document.head.appendChild(st); })();
	// ícones iguais aos do menu do Estúdio Problems (linha, sem emoji)
	const ICO = {"editar": "<svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.9\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><rect x=\"2.5\" y=\"4.5\" width=\"19\" height=\"13\" rx=\"2\"/><path d=\"M2.5 8.5h19M7 4.5v4M12 4.5v4M17 4.5v4\"/><path d=\"M5 21h4M11 21h8M9 19.5v3\"/></svg>", "pasta": "<svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.9\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M3 7a2 2 0 0 1 2-2h4l2 2.5h8a2 2 0 0 1 2 2V18a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z\"/></svg>", "copiar": "<svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.9\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><rect x=\"8.5\" y=\"8.5\" width=\"12\" height=\"12\" rx=\"2\"/><path d=\"M15.5 8.5V5.5a2 2 0 0 0-2-2h-8a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h3\"/></svg>", "lixo": "<svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.9\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M4 6.5h16M9.5 6.5V4.5h5v2M6.5 6.5l1 13.5a1.5 1.5 0 0 0 1.5 1.5h6a1.5 1.5 0 0 0 1.5-1.5l1-13.5M10 11v6M14 11v6\"/></svg>", "lapis": "<svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.9\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><path d=\"M4 20h4L19.5 8.5a2.1 2.1 0 0 0-4-4L4 16z\"/><path d=\"m13.5 6.5 4 4\"/></svg>"};
	const INI = { q: "" };
	const ini = document.createElement("section"); ini.id = "inicio"; ini.hidden = true; ini.setAttribute("aria-label", "Projetos"); $("#ed").before(ini);
	async function desenhaInicio() {
		const l = await LISTA.ler(), q = INI.q.trim().toLowerCase(), L = l.filter((x) => !q || x.nome.toLowerCase().includes(q));
		ini.innerHTML = `<div class="ini">
			<div class="ini-novo">
				<button class="pri" data-a="novo"><span class="ic">${ICO.editar}</span><span><b>Novo vídeo longo</b><small>começa do zero: abra ou solte o bruto</small></span></button>
				<button data-a="arquivo"><span class="ic">${ICO.pasta}</span><span><b>Abrir projeto</b><small>arquivo .editor</small></span></button>
			</div>
			<div class="ini-sec">Projetos <small>${l.length || ""}</small><span class="grow"></span>${l.length ? `<input type="search" placeholder="Buscar projeto" value="${escH(INI.q)}" aria-label="Buscar projeto">` : ""}</div>
			<div class="ini-grid">${L.map((x) => `<div class="ini-card" role="button" tabindex="0" data-id="${escH(x.id)}"><div class="th" style="${x.thumb ? `background-image:url('${x.thumb}')` : ""}">${x.thumb ? "" : ICO.editar}</div>
				<div class="in"><b>${escH(x.nome)}</b><small>${dataTxt(x.mod)}${x.dur ? " · " + durTxt(x.dur) : ""}</small></div><button class="mn" data-m="${escH(x.id)}" title="Opções" aria-label="Opções">⋯</button></div>`).join("")
				|| `<div class="ini-vazio" style="grid-column:1/-1">${l.length ? "Nenhum projeto com esse nome." : "Nenhum projeto ainda. Comece um vídeo longo novo aqui em cima."}</div>`}</div></div>`;
		$("[data-a=novo]", ini).onclick = () => { projetoNovo(); fechaInicio(); };
		$("[data-a=arquivo]", ini).onclick = () => { $("#pAbrir").click(); };
		const qi = $("input[type=search]", ini); if (qi) qi.oninput = () => { INI.q = qi.value; const pos = qi.selectionStart; desenhaInicio().then(() => { const n = $("input[type=search]", ini); if (n) { n.focus(); n.setSelectionRange(pos, pos); } }); };
		$$(".ini-card", ini).forEach((c) => { const abre = () => abrirProjeto(c.dataset.id); c.onclick = (e) => { if (!e.target.closest(".mn,.ini-pop")) abre(); }; c.onkeydown = (e) => { if (e.key === "Enter" && e.target === c) abre(); }; });
		$$(".mn", ini).forEach((b) => b.onclick = (e) => { e.stopPropagation(); $$(".ini-pop", ini).forEach((x) => x.remove()); const id = b.dataset.m;
			b.insertAdjacentHTML("afterend", `<div class="ini-pop"><button data-o="ren">${ICO.lapis}Renomear</button><button data-o="dup">${ICO.copiar}Duplicar</button><button data-o="del">${ICO.lixo}Apagar</button></div>`);
			const pop = b.nextElementSibling; pop.onclick = async (ev) => { ev.stopPropagation(); const o = ev.target.closest("[data-o]")?.dataset.o; if (!o) return; pop.remove(); await opcaoProjeto(id, o); }; });
	}
	async function opcaoProjeto(id, o) {
		const l = await LISTA.ler(), m = l.find((x) => x.id === id); if (!m) return;
		const s = await DB.get("proj:" + id).catch(() => null);
		if (o === "ren") { const n = (prompt("Nome do projeto:", m.nome) || "").trim(); if (!n) return; m.nome = n; if (s) { const p = JSON.parse(s); p.nome = n; await DB.set("proj:" + id, JSON.stringify(p)); } await LISTA.gravar(l); }
		if (o === "dup" && s) { const p = JSON.parse(s), nid = rid(); p.id = nid; p.nome = m.nome + " (cópia)"; await DB.set("proj:" + nid, JSON.stringify(p)); l.unshift({ ...m, id: nid, nome: p.nome, mod: Date.now() }); await LISTA.gravar(l); }
		if (o === "del") { if (!confirm(`Apagar o projeto "${m.nome}" deste navegador? Os arquivos de vídeo no seu computador não são apagados.`)) return;
			await DB.del("proj:" + id); await LISTA.gravar(l.filter((x) => x.id !== id)); limparArquivos(); }
		desenhaInicio();
	}
	// tira do banco os arquivos que nenhum projeto usa mais (os grandes ficam no seu computador; aqui só a "alça" ou cópias pequenas)
	async function limparArquivos() {
		try { const ks = await DB.chaves(), usados = new Set();
			for (const k of ks) if (String(k).startsWith("proj:")) { try { Object.keys(JSON.parse(await DB.get(k)).midias || {}).forEach((m) => usados.add(m)); } catch (_) {} }
			for (const k of ks) { const m = String(k).match(/^(arq|alca):(.+)$/); if (m && !usados.has(m[2])) await DB.del(k); } } catch (_) {}
	}
	async function abrirProjeto(id) {
		const s = await DB.get("proj:" + id).catch(() => null); if (!s) { aviso("Projeto não encontrado", "Ele pode ter sido apagado."); return desenhaInicio(); }
		pausar(); for (const k in RT) delete RT[k]; P = Object.assign(novoProjeto(), JSON.parse(s)); P.id = id; ED.desfazer = []; ED.refazer = []; ED.sel.clear();
		aplicarProjeto(); await DB.set("atual", id); fechaInicio(); await reabrir(false);
	}
	async function abreInicio() { pausar(); await salvarJa(); status(""); $("#ed").hidden = true; ini.hidden = false; $("#nomeProj").textContent = "Estúdio Problems · seus projetos"; await desenhaInicio(); }
	function fechaInicio() { ini.hidden = true; $("#ed").hidden = false; $("#nomeProj").textContent = "Estúdio Problems · " + P.nome; ED.sujo = true; }
	document.querySelector(".bar .brand").title = "Voltar à tela inicial (seus projetos)";
	document.querySelector(".bar .brand").onclick = abreInicio;
	document.addEventListener("click", (e) => { if (!e.target.closest(".ini-pop,.mn")) $$(".ini-pop", ini).forEach((x) => x.remove()); });

	/* círculo de espaço (padrão de todos os projetos): os projetos do Editor guardados neste navegador, com "Baixar .editor" */
	addEventListener("DOMContentLoaded", () => window.EstudioConta?.espaco.registrar({
		programa: "Editor",
		async listar() {
			await salvarJa();
			const l = await LISTA.ler(), out = [];
			for (const x of l) {
				let s = null; try { s = await DB.get("proj:" + x.id); } catch (_) {}
				let b = (s ? s.length : 0) + (x.thumb ? x.thumb.length : 0);
				try { for (const mid of Object.keys(JSON.parse(s || "{}").midias || {})) { const f = await DB.get("arq:" + mid).catch(() => null); if (f && f.size) b += f.size; } } catch (_) {}
				out.push({ nome: x.nome, bytes: b, data: x.mod, thumb: x.thumb, info: x.dur ? durTxt(x.dur) : "", rotuloBaixar: "Baixar .editor", confirma: false,
					baixar: async () => { const t = await DB.get("proj:" + x.id); const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([t || "{}"], { type: "application/json" })); a.download = (x.nome || "projeto").replace(/[^\w\- ]+/g, "") + ".editor"; a.click(); },
					apagar: () => opcaoProjeto(x.id, "del") });
			}
			return out;
		},
	}));

	/* ---------- início ---------- */
	// o botão "Menu" e a conta vêm do componente padrão de todos os projetos (/estudio-conta.js), ao lado do tema
	zoomTL(40);
	(async () => {
		// o projeto que existia antes (um só, "projeto:atual") entra no histórico
		try { const velho = await DB.get("projeto:atual"); if (velho) { const p = Object.assign(novoProjeto(), JSON.parse(velho)); P = p; await DB.set("proj:" + p.id, JSON.stringify(p)); await guardaNaLista(); await DB.del("projeto:atual"); P = novoProjeto(); } } catch (_) {}
		aplicarProjeto(); requestAnimationFrame(laco); BIB.restaurar();
		const pedido = new URLSearchParams(location.search).get("p"); // ?p=<id> abre direto um projeto
		if (pedido) await abrirProjeto(pedido); else abreInicio();
		if (typeof VideoDecoder === "undefined" || typeof AudioDecoder === "undefined") aviso("Use o Chrome ou o Edge", "Este navegador não tem as ferramentas de vídeo (WebCodecs) que o editor usa.");
	})();
})();
