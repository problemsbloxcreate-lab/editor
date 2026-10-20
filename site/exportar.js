/* Exportação da aba Edição: monta cada quadro na ordem (decodificando o bruto com o WebCodecs, quadro exato), mistura o áudio
   (com a mesma regra da prévia: ganho fixo, transição de potência constante de 0,2 s nos cortes colados, limitador em −1 dBFS)
   e grava um MP4 (H.264 + AAC no Chrome/Edge do Windows; VP9/AV1 + Opus quando o navegador não tiver H.264). */
(function () {
	"use strict";
	const $ = (s) => document.querySelector(s), clamp = (v, a, b) => Math.max(a, Math.min(b, v));
	const SR = 48000;

	/* ---------- quadros do vídeo de origem ---------- */
	function Fonte(mid) {
		const rt = ED.RT[mid], tr = rt && rt.mp4 && rt.mp4.video;
		const st = { tr, dec: null, fila: [], prox: 0, fim: false, err: null, novo: null, pos: -1, ok: false, vid: null };
		async function preparar() {
			if (!tr || typeof VideoDecoder === "undefined") return false;
			/* decodifica pelo processador: o decodificador da placa de vídeo tem poucos quadros e trava se seguramos alguns
			   (aconteceu no fim do arquivo, no PC do Problems); se não der, usa o que o navegador tiver */
			const cfg = MP4.videoConfig(tr); cfg.hardwareAcceleration = "prefer-software";
			let s = await VideoDecoder.isConfigSupported(cfg).catch(() => ({ supported: false }));
			if (!s.supported) { delete cfg.hardwareAcceleration; s = await VideoDecoder.isConfigSupported(cfg).catch(() => ({ supported: false })); }
			if (!s.supported) return false;
			st.cfg = cfg; st.ok = true; return true;
		}
		function zerar(t) {
			for (const f of st.fila) f.close(); st.fila = [];
			if (st.dec && st.dec.state !== "closed") st.dec.close();
			st.dec = new VideoDecoder({ output: (f) => { st.fila.push(f); if (st.novo) { const r = st.novo; st.novo = null; r(); } }, error: (e) => { st.err = e; if (st.novo) { const r = st.novo; st.novo = null; r(); } } });
			st.dec.configure(st.cfg);
			st.prox = MP4.chaveAntes(tr, MP4.indicePorTempo(tr, t)); st.fim = false; st.esvaziou = false; st.pos = t;
		}
		const tsDe = (i) => Math.round(((tr.dts[i] + tr.cts[i]) / tr.timescale) * 1e6);
		async function alimentar(n) {
			let k = 0;
			while (k < n && st.prox < tr.n) {
				const i0 = st.prox, i1 = Math.min(tr.n, i0 + n - k);
				for await (const s of MP4.amostras(rt.file, tr, i0, i1)) {
					st.dec.decode(new EncodedVideoChunk({ type: tr.key[s.i] ? "key" : "delta", timestamp: tsDe(s.i), duration: Math.round((tr.dur[s.i] / tr.timescale) * 1e6), data: s.data }));
					k++;
				}
				st.prox = i1;
			}
			// fim do arquivo: pede os últimos quadros sem ficar esperando parado (o laço de quadro() continua olhando a fila)
			if (st.prox >= tr.n && !st.fim) { st.fim = true; st.esvaziou = false; const d = st.dec; d.flush().then(() => { if (st.dec === d) st.esvaziou = true; }, () => { if (st.dec === d) st.esvaziou = true; }); }
		}
		/* quadro que aparece no tempo de fonte t (segundos) */
		async function quadro(t) {
			if (!st.ok) return quadroPorSeek(t);
			if (!st.dec || t < st.pos - 1e-3 || t > st.pos + 3) zerar(t);
			st.pos = t;
			const alvo = t * 1e6 + 500; let ultimoNovo = performance.now(), nFila = -1;
			for (let tent = 0; tent < 4000; tent++) {
				if (st.err) throw st.err;
				if (st.fila.length !== nFila) { nFila = st.fila.length; ultimoNovo = performance.now(); }
				else if (performance.now() - ultimoNovo > 6000) { if (st.fila.length) break; throw new Error("o decodificador parou de entregar quadros em " + t.toFixed(2) + " s"); }
				// descarta os quadros que já passaram (mantém o último antes do alvo)
				while (st.fila.length > 1 && st.fila[1].timestamp <= alvo) st.fila.shift().close();
				const ult = st.fila[st.fila.length - 1];
				if ((ult && ult.timestamp > alvo) || (st.fim && st.esvaziou)) break;
				if (st.dec.decodeQueueSize < 6 && !st.fim) { await alimentar(8); continue; }
				await new Promise((r) => { st.novo = r; setTimeout(r, 200); });
			}
			return st.fila[0] && st.fila[0].timestamp <= alvo ? st.fila[0] : st.fila[0] || null;
		}
		/* sem WebCodecs para esse vídeo: busca no <video> (mais lento, mas funciona) */
		async function quadroPorSeek(t) {
			if (!st.vid) { st.vid = document.createElement("video"); st.vid.muted = true; st.vid.src = rt.url; await new Promise((r) => { st.vid.onloadeddata = r; st.vid.onerror = r; }); }
			if (Math.abs(st.vid.currentTime - t) > 0.001) { st.vid.currentTime = t; await new Promise((r) => { st.vid.onseeked = r; setTimeout(r, 2000); }); }
			return st.vid;
		}
		function fechar() { for (const f of st.fila) f.close(); st.fila = []; if (st.dec && st.dec.state !== "closed") st.dec.close(); }
		return { preparar, quadro, fechar };
	}

	/* ---------- mistura do áudio ---------- */
	function Mixer() {
		const P = ED.P, XF = ED.XF;
		const clipes = P.clipes.filter((c) => !c.off && ED.faixa(c.faixa).tipo === "audio" && ED.ganhoFaixa(c.faixa) > 0).map((c) => ({ c, xi: ED.colado(c, -1) ? XF : 0, xo: ED.colado(c, 1) ? XF : 0, g: ED.dbLin(c.vol || 0) * ED.ganhoFaixa(c.faixa), rt: ED.RT[c.midia] }));
		let env = 1; const ceil = Math.pow(10, -1 / 20), rel = 1 - Math.exp(-1 / (0.12 * SR));
		return function (t0, n) {
			const L = new Float32Array(n), R = new Float32Array(n), t1 = t0 + n / SR;
			for (const k of clipes) {
				const c = k.c, a = c.ini - k.xi, b = c.ini + c.dur + k.xo; if (b <= t0 || a >= t1 || !k.rt) continue;
				const i0 = Math.max(0, Math.floor((a - t0) * SR)), i1 = Math.min(n, Math.ceil((b - t0) * SR));
				const aud = k.rt.buf ? null : k.rt.aud && k.rt.aud[c.trilha || 0];
				const buf = k.rt.buf, ch0 = buf && buf.getChannelData(0), ch1 = buf && buf.numberOfChannels > 1 ? buf.getChannelData(1) : ch0;
				const ssr = buf ? buf.sampleRate : aud ? aud.sr : SR;
				const sfx = c.faixa === "SFX";
				for (let i = i0; i < i1; i++) {
					const tl = t0 + i / SR, s = c.fonte + (tl - c.ini) * (c.vel || 1);
					if (s < 0) continue;
					let gn = k.g;
					// entrada: potência constante 0,2 s centrada no corte colado; solta: 8 ms
					if (k.xi) { if (tl < c.ini + XF) gn *= Math.sin((Math.PI / 2) * clamp((tl - (c.ini - XF)) / (2 * XF), 0, 1)); }
					else if (tl < c.ini + 0.008) gn *= clamp((tl - c.ini) / 0.008, 0, 1);
					if (k.xo) { if (tl > c.ini + c.dur - XF) gn *= Math.cos((Math.PI / 2) * clamp((tl - (c.ini + c.dur - XF)) / (2 * XF), 0, 1)); }
					else if (!sfx && tl > c.ini + c.dur - 0.008) gn *= clamp((c.ini + c.dur - tl) / 0.008, 0, 1);
					if (c.faixa !== "SFX") { if (c.fadeIn && tl < c.ini + c.fadeIn) gn *= clamp((tl - c.ini) / c.fadeIn, 0, 1); if (c.fadeOut && tl > c.ini + c.dur - c.fadeOut) gn *= clamp((c.ini + c.dur - tl) / c.fadeOut, 0, 1); }
					const x = s * ssr, j = Math.floor(x), f = x - j;
					if (buf) { if (j + 1 >= buf.length) continue; L[i] += gn * (ch0[j] + (ch0[j + 1] - ch0[j]) * f); R[i] += gn * (ch1[j] + (ch1[j + 1] - ch1[j]) * f); }
					else if (aud) { if (j + 1 >= aud.pcm.length) continue; const v = (aud.pcm[j] + (aud.pcm[j + 1] - aud.pcm[j]) * f) / 32768 * gn; L[i] += v; R[i] += v; }
				}
			}
			// limitador simples: ataque imediato, soltura de 120 ms, teto −1 dBFS
			for (let i = 0; i < n; i++) { const p = Math.max(Math.abs(L[i]), Math.abs(R[i])), need = p > ceil ? ceil / p : 1; env = need < env ? need : env + (1 - env) * rel; L[i] *= env; R[i] *= env; }
			return [L, R];
		};
	}
	window.ED_MIXER = Mixer;

	/* ---------- exportar ---------- */
	let rodando = false;
	async function escolherCodecs(W, H, fps) {
		const br = Math.round((fps > 30 ? 18e6 : 12e6) * (W * H) / (1920 * 1080) * (+ED.P.qualidade || 1));
		const vids = [["avc", fps > 30 ? "avc1.64002a" : "avc1.640028"], ["avc", "avc1.640033"], ["vp9", "vp09.00.41.08"], ["av1", "av01.0.09M.08"]];
		let v = null;
		for (const [m, codec] of vids) { const cfg = { codec, width: W, height: H, bitrate: br, framerate: fps, latencyMode: "quality" }; if (m === "avc") cfg.avc = { format: "avc" }; const s = await VideoEncoder.isConfigSupported(cfg).catch(() => ({ supported: false })); if (s.supported) { v = { m, cfg }; break; } }
		let a = null;
		for (const [m, codec, bitrate] of [["aac", "mp4a.40.2", 192000], ["opus", "opus", 160000]]) { const cfg = { codec, sampleRate: SR, numberOfChannels: 2, bitrate }; const s = await AudioEncoder.isConfigSupported(cfg).catch(() => ({ supported: false })); if (s.supported) { a = { m, cfg }; break; } }
		return { v, a };
	}
	async function exportar(opc) {
		opc = opc || {};
		if (rodando) return; const P = ED.P, tt = ED.total();
		if (!tt) { ED.aviso("Nada para exportar", "Abra um bruto primeiro."); return; }
		if (typeof VideoEncoder === "undefined") { ED.aviso("Use o Chrome ou o Edge", "Este navegador não exporta vídeo (sem WebCodecs)."); return; }
		ED.pausar();
		const W = P.w, H = P.h, fps = P.fps, T0 = clamp(P.entrada || 0, 0, tt), T1 = clamp(P.saida != null ? P.saida : tt, T0 + 0.1, tt), N = Math.ceil((T1 - T0) * fps);
		const cod = await escolherCodecs(W, H, fps);
		if (!cod.v) { ED.aviso("Não deu para exportar", "O navegador não tem codificador de vídeo para " + W + "×" + H + "."); return; }
		// destino: arquivo no PC (sem limite de tamanho) ou memória
		let alvo, gravador = null, nome = (P.nome || "edicao").replace(/[^\w\- ]+/g, "") + ".mp4";
		const semAlca = (() => { try { return /\bClaude\//.test(navigator.userAgent) || localStorage.getItem("ep:semFSA") === "1"; } catch (_) { return false; } })(); // navegador que não deixa gravar pelo seletor novo: baixa pelo jeito clássico
		if (opc.memoria || !window.showSaveFilePicker || semAlca) alvo = new Mp4Muxer.ArrayBufferTarget();
		else {
			let h; try { h = await showSaveFilePicker({ suggestedName: nome, types: [{ description: "Vídeo MP4", accept: { "video/mp4": [".mp4"] } }] }); } catch (e) { return; }
			gravador = await h.createWritable(); alvo = new Mp4Muxer.FileSystemWritableFileStreamTarget(gravador);
		}
		const mux = new Mp4Muxer.Muxer({ target: alvo, video: { codec: cod.v.m, width: W, height: H, frameRate: fps }, audio: cod.a ? { codec: cod.a.m, numberOfChannels: 2, sampleRate: SR } : undefined, fastStart: alvo instanceof Mp4Muxer.ArrayBufferTarget ? "in-memory" : false, firstTimestampBehavior: "offset" });
		let erro = null;
		const venc = new VideoEncoder({ output: (ch, meta) => mux.addVideoChunk(ch, meta), error: (e) => { erro = e; } });
		venc.configure(cod.v.cfg);
		const aenc = cod.a ? new AudioEncoder({ output: (ch, meta) => mux.addAudioChunk(ch, meta), error: (e) => { erro = e; } }) : null;
		if (aenc) aenc.configure(cod.a.cfg);
		const fontes = {}, imgs = {};
		const cv = new OffscreenCanvas(W, H), ctx = cv.getContext("2d");
		const mix = Mixer();
		rodando = true; const prog = $("#expProg"), barra = prog.querySelector("i"); prog.hidden = false;
		const t0 = performance.now(); let aud = T0;
		ED.status("Exportando…");
		try {
			for (let n = 0; n < N; n++) {
				if (erro) throw erro;
				const t = T0 + n / fps;
				// quadros de origem que esse instante usa
				const usados = {};
				for (const q of window.ED_NECESSARIOS(t)) {
					const c = q.c, rt = ED.RT[c.midia]; if (!rt) continue;
					if (rt.img) { usados[c.id] = rt.img; continue; }
					const chave = c.midia + "@" + q.fid + "@" + q.papel; // um decodificador por uso: V1, V2 e a dissolução podem pedir o mesmo bruto em tempos diferentes
					if (!fontes[chave]) { fontes[chave] = Fonte(c.midia); await fontes[chave].preparar(); }
					usados[c.id] = await fontes[chave].quadro(Math.max(0, c.fonte + (t - c.ini) * (c.vel || 1)));
				}
				window.ED_QUADRO(ctx, W, H, t, (c) => usados[c.id] || null);
				const vf = new VideoFrame(cv, { timestamp: Math.round((n * 1e6) / fps), duration: Math.round(1e6 / fps) });
				venc.encode(vf, { keyFrame: n % (fps * 2) === 0 }); vf.close();
				while (venc.encodeQueueSize > 6) await new Promise((r) => setTimeout(r, 2));
				// áudio em blocos de 0,5 s, acompanhando o vídeo
				while (aenc && aud < Math.min(T1, t + 1)) {
					const nAm = Math.min(SR / 2, Math.ceil((T1 - aud) * SR)); if (nAm <= 0) break;
					const [Lc, Rc] = mix(aud, nAm), data = new Float32Array(nAm * 2); data.set(Lc, 0); data.set(Rc, nAm);
					const ad = new AudioData({ format: "f32-planar", sampleRate: SR, numberOfFrames: nAm, numberOfChannels: 2, timestamp: Math.round((aud - T0) * 1e6), data });
					aenc.encode(ad); ad.close(); aud += nAm / SR;
				}
				if (n % 15 === 0) { const f = (n + 1) / N, dt = (performance.now() - t0) / 1000, falta = f > 0.01 ? dt / f - dt : 0; barra.style.width = (f * 100).toFixed(1) + "%"; ED.status(`Exportando ${Math.round(f * 100)}% · faltam ~${Math.ceil(falta / 60)} min`); await new Promise((r) => setTimeout(r, 0)); }
			}
			await venc.flush(); if (aenc) await aenc.flush();
			mux.finalize();
			if (gravador) await gravador.close();
			else if (!opc.memoria) { const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([alvo.buffer], { type: "video/mp4" })); a.download = nome; a.click(); }
			const seg = (performance.now() - t0) / 1000;
			ED.status(`Exportado: ${nome} (${cod.v.cfg.codec}${cod.a ? " + " + cod.a.cfg.codec : ""}) em ${Math.round(seg)} s`, "ok");
			return opc.memoria ? { buffer: alvo.buffer, codec: cod } : true;
		} catch (e) {
			console.error(e); ED.aviso("A exportação parou", String(e && e.message || e)); ED.status("Exportação parou", "err");
			try { if (gravador) await gravador.abort(); } catch (_) {}
			return false;
		} finally {
			rodando = false; prog.hidden = true; barra.style.width = "0";
			for (const k in fontes) fontes[k].fechar();
			try { venc.close(); } catch (_) {} try { aenc && aenc.close(); } catch (_) {}
		}
	}
	$("#bExportar").onclick = () => exportar();
	window.ED_EXPORTAR = exportar;
})();
