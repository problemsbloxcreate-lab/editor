/* Leitor de MP4 da aba Edição: lê só o índice do arquivo (moov, ou moof dos MP4 fragmentados/híbridos do OBS) e devolve
   cada faixa com a lista de amostras (onde está cada pedaço no arquivo). Assim o bruto de vários GB nunca é carregado inteiro:
   o áudio de cada faixa é lido pedaço por pedaço e decodificado com o WebCodecs, e o vídeo é decodificado só na exportação. */
(function () {
	"use strict";
	const td = new TextDecoder("latin1");
	const typ = (u8, o) => td.decode(u8.subarray(o, o + 4));
	const hex2 = (n) => n.toString(16).padStart(2, "0");

	async function lerFaixa(file, a, b) { return new Uint8Array(await file.slice(a, b).arrayBuffer()); }

	/* caixas de primeiro nível: só os cabeçalhos (rápido mesmo em arquivo de 10 GB) */
	async function topo(file) {
		const out = [];
		let p = 0;
		while (p + 8 <= file.size) {
			const h = await lerFaixa(file, p, Math.min(file.size, p + 16));
			const dv = new DataView(h.buffer);
			let size = dv.getUint32(0), hdr = 8;
			const t = typ(h, 4);
			if (size === 1) { size = Number(dv.getBigUint64(8)); hdr = 16; }
			else if (size === 0) size = file.size - p;
			if (size < hdr) break;
			out.push({ type: t, start: p, size, hdr });
			p += size;
		}
		return out;
	}

	/* percorre as caixas filhas de um trecho já na memória */
	function filhos(u8, a, b) {
		const dv = new DataView(u8.buffer, u8.byteOffset, u8.byteLength), out = [];
		let p = a;
		while (p + 8 <= b) {
			let size = dv.getUint32(p), hdr = 8;
			const t = typ(u8, p + 4);
			if (size === 1) { size = Number(dv.getBigUint64(p + 8)); hdr = 16; } else if (size === 0) size = b - p;
			if (size < hdr || p + size > b) break;
			out.push({ type: t, a: p + hdr, b: p + size, start: p });
			p += size;
		}
		return out;
	}
	const um = (u8, box, t) => filhos(u8, box.a, box.b).find((x) => x.type === t);
	const todos = (u8, box, t) => filhos(u8, box.a, box.b).filter((x) => x.type === t);

	function lerStsd(u8, dv, box, tr) {
		/* full box: 4 bytes versão/flags + 4 bytes contagem; depois a 1ª entrada */
		const e = box.a + 8, esz = dv.getUint32(e), fmt = typ(u8, e + 4), ea = e + 8, eb = e + esz;
		tr.fmt = fmt;
		if (tr.kind === "video") {
			tr.width = dv.getUint16(ea + 24); tr.height = dv.getUint16(ea + 26);
			const kids = filhos(u8, ea + 78, eb);
			const cfg = (t) => kids.find((k) => k.type === t);
			if (fmt === "avc1" || fmt === "avc3") {
				const c = cfg("avcC"); if (c) { tr.desc = u8.slice(c.a, c.b); tr.codec = "avc1." + hex2(u8[c.a + 1]) + hex2(u8[c.a + 2]) + hex2(u8[c.a + 3]); }
			} else if (fmt === "hvc1" || fmt === "hev1") {
				const c = cfg("hvcC");
				if (c) {
					const d = u8.slice(c.a, c.b); tr.desc = d;
					const sp = d[1] >> 6, tier = (d[1] >> 5) & 1, pid = d[1] & 31;
					let compat = ((d[2] << 24) | (d[3] << 16) | (d[4] << 8) | d[5]) >>> 0, rev = 0;
					for (let i = 0; i < 32; i++) { rev = (rev << 1) | (compat & 1); compat >>>= 1; }
					const cons = Array.from(d.subarray(6, 12)); while (cons.length && !cons[cons.length - 1]) cons.pop();
					tr.codec = fmt + "." + (["", "A", "B", "C"][sp]) + pid + "." + (rev >>> 0).toString(16) + "." + (tier ? "H" : "L") + d[12] + (cons.length ? "." + cons.map((x) => x.toString(16)).join(".") : "");
				}
			} else if (fmt === "av01") {
				const c = cfg("av1C");
				if (c) {
					const d = u8.slice(c.a, c.b); tr.desc = d;
					const prof = d[1] >> 5, lvl = d[1] & 31, tier = d[2] >> 7, hb = (d[2] >> 6) & 1, tw = (d[2] >> 5) & 1;
					tr.codec = "av01." + prof + "." + String(lvl).padStart(2, "0") + (tier ? "H" : "M") + "." + (hb ? (tw ? "12" : "10") : "08");
				}
			} else if (fmt === "vp09") {
				const c = cfg("vpcC");
				if (c) { const d = u8.subarray(c.a, c.b); tr.codec = "vp09." + String(d[4]).padStart(2, "0") + "." + String(d[5]).padStart(2, "0") + "." + String(d[6] >> 4).padStart(2, "0"); }
			}
		} else if (tr.kind === "audio") {
			tr.channels = dv.getUint16(ea + 16); tr.sampleRate = dv.getUint32(ea + 24) >>> 16;
			const kids = filhos(u8, ea + 28, eb);
			if (fmt === "mp4a") {
				const es = kids.find((k) => k.type === "esds");
				if (es) {
					/* descritores MPEG-4: 3 (ES) → 4 (DecoderConfig) → 5 (DecoderSpecificInfo = AudioSpecificConfig) */
					let p = es.a + 4, obj = 0x40;
					const len = () => { let n = 0; for (let i = 0; i < 4; i++) { const b = u8[p++]; n = (n << 7) | (b & 127); if (!(b & 128)) break; } return n; };
					while (p < es.b) {
						const tag = u8[p++], n = len();
						if (tag === 3) { const fl = u8[p + 2]; p += 3; if (fl & 128) p += 2; if (fl & 64) p += 1 + u8[p]; if (fl & 32) p += 2; continue; }
						if (tag === 4) { obj = u8[p]; p += 13; continue; }
						if (tag === 5) { tr.desc = u8.slice(p, p + n); break; }
						p += n;
					}
					const aot = tr.desc && tr.desc.length ? tr.desc[0] >> 3 : 2;
					tr.codec = obj === 0x40 ? "mp4a.40." + aot : "mp4a." + hex2(obj);
					if (tr.desc && tr.desc.length >= 2) {
						const sfi = ((tr.desc[0] & 7) << 1) | (tr.desc[1] >> 7), ch = (tr.desc[1] >> 3) & 15;
						const SR = [96000, 88200, 64000, 48000, 44100, 32000, 24000, 22050, 16000, 12000, 11025, 8000, 7350];
						if (SR[sfi]) tr.sampleRate = SR[sfi]; if (ch) tr.channels = ch;
					}
				}
			} else if (fmt === "Opus") {
				const d = kids.find((k) => k.type === "dOps");
				tr.codec = "opus";
				if (d) {
					/* dOps (big endian) → OpusHead (little endian), que é o que o WebCodecs espera */
					const s = new DataView(u8.buffer, u8.byteOffset + d.a, d.b - d.a), ch = s.getUint8(1);
					const h = new Uint8Array(19), hv = new DataView(h.buffer);
					h.set([79, 112, 117, 115, 72, 101, 97, 100]); h[8] = 1; h[9] = ch;
					hv.setUint16(10, s.getUint16(2), true); hv.setUint32(12, s.getUint32(4), true); hv.setInt16(16, s.getInt16(8), true); h[18] = s.getUint8(10);
					tr.desc = h; tr.channels = ch;
				}
			}
		}
	}

	function tabelaAmostras(u8, dv, stbl, tr) {
		const g = (t) => um(u8, stbl, t);
		const stsz = g("stsz") || g("stz2"), stco = g("stco"), co64 = g("co64"), stsc = g("stsc"), stts = g("stts"), ctts = g("ctts"), stss = g("stss");
		if (!stsz || !(stco || co64) || !stsc || !stts) return 0;
		const fixo = dv.getUint32(stsz.a + 4), n = dv.getUint32(stsz.a + 8);
		if (!n) return 0;
		const size = new Uint32Array(n);
		for (let i = 0; i < n; i++) size[i] = fixo || dv.getUint32(stsz.a + 12 + i * 4);
		const nch = dv.getUint32((stco || co64).a + 4), choff = new Float64Array(nch);
		for (let i = 0; i < nch; i++) choff[i] = stco ? dv.getUint32(stco.a + 8 + i * 4) : Number(dv.getBigUint64(co64.a + 8 + i * 8));
		const off = new Float64Array(n);
		const nsc = dv.getUint32(stsc.a + 4);
		let s = 0;
		for (let e = 0; e < nsc; e++) {
			const first = dv.getUint32(stsc.a + 8 + e * 12) - 1, per = dv.getUint32(stsc.a + 12 + e * 12);
			const next = e + 1 < nsc ? dv.getUint32(stsc.a + 8 + (e + 1) * 12) - 1 : nch;
			for (let c = first; c < next && s < n; c++) { let o = choff[c]; for (let k = 0; k < per && s < n; k++) { off[s] = o; o += size[s]; s++; } }
		}
		const dts = new Float64Array(n), dur = new Float64Array(n);
		let t = 0; s = 0;
		const nts = dv.getUint32(stts.a + 4);
		for (let e = 0; e < nts; e++) { const c = dv.getUint32(stts.a + 8 + e * 8), d = dv.getUint32(stts.a + 12 + e * 8); for (let k = 0; k < c && s < n; k++) { dts[s] = t; dur[s] = d; t += d; s++; } }
		const cts = new Float64Array(n);
		if (ctts) { const v = u8[ctts.a], nc = dv.getUint32(ctts.a + 4); s = 0; for (let e = 0; e < nc; e++) { const c = dv.getUint32(ctts.a + 8 + e * 8), o = v ? dv.getInt32(ctts.a + 12 + e * 8) : dv.getUint32(ctts.a + 12 + e * 8); for (let k = 0; k < c && s < n; k++) cts[s++] = o; } }
		const key = new Uint8Array(n);
		if (stss) { const ns = dv.getUint32(stss.a + 4); for (let i = 0; i < ns; i++) key[dv.getUint32(stss.a + 8 + i * 4) - 1] = 1; } else key.fill(1);
		Object.assign(tr, { n, off, size, dts, dur, cts, key });
		return n;
	}

	async function abrir(file, onp) {
		const caixas = await topo(file);
		const mv = caixas.find((c) => c.type === "moov");
		if (!mv) throw new Error("este arquivo não parece um MP4/MOV (sem índice). Se for .mkv, remuxe para MP4 no OBS (Arquivo › Remuxar gravações).");
		const u8 = await lerFaixa(file, mv.start, mv.start + mv.size), dv = new DataView(u8.buffer);
		const moov = { a: mv.hdr, b: mv.size };
		const tracks = [], porId = {};
		const mvhd = um(u8, moov, "mvhd");
		let duracao = 0;
		if (mvhd) { const v = u8[mvhd.a]; const ts = dv.getUint32(mvhd.a + (v ? 20 : 12)); const d = v ? Number(dv.getBigUint64(mvhd.a + 24)) : dv.getUint32(mvhd.a + 16); duracao = ts ? d / ts : 0; }
		for (const trak of todos(u8, moov, "trak")) {
			const tkhd = um(u8, trak, "tkhd"), mdia = um(u8, trak, "mdia");
			if (!tkhd || !mdia) continue;
			const id = dv.getUint32(tkhd.a + (u8[tkhd.a] ? 20 : 12));
			const mdhd = um(u8, mdia, "mdhd"), hdlr = um(u8, mdia, "hdlr");
			const v = u8[mdhd.a], ts = dv.getUint32(mdhd.a + (v ? 20 : 12));
			const h = typ(u8, hdlr.a + 8), kind = h === "vide" ? "video" : h === "soun" ? "audio" : "outro";
			const tr = { id, kind, timescale: ts, n: 0 };
			const minf = um(u8, mdia, "minf"), stbl = minf && um(u8, minf, "stbl");
			if (stbl) { const sd = um(u8, stbl, "stsd"); if (sd) lerStsd(u8, dv, sd, tr); tabelaAmostras(u8, dv, stbl, tr); }
			tracks.push(tr); porId[id] = tr;
		}
		/* MP4 fragmentado (OBS "MP4 híbrido"/fMP4): as amostras ficam nos moof */
		const moofs = caixas.filter((c) => c.type === "moof");
		if (moofs.length && tracks.some((t) => !t.n)) {
			const trex = {};
			const mvex = um(u8, moov, "mvex");
			if (mvex) for (const x of todos(u8, mvex, "trex")) { const tid = dv.getUint32(x.a + 4); trex[tid] = { dur: dv.getUint32(x.a + 12), size: dv.getUint32(x.a + 16), flags: dv.getUint32(x.a + 20) }; }
			const acc = {};
			for (let mi = 0; mi < moofs.length; mi++) {
				const m = moofs[mi];
				if (onp && mi % 50 === 0) onp(mi / moofs.length);
				const b = await lerFaixa(file, m.start, m.start + m.size), bv = new DataView(b.buffer), box = { a: m.hdr, b: m.size };
				for (const traf of todos(b, box, "traf")) {
					const tf = um(b, traf, "tfhd"); if (!tf) continue;
					const fl = bv.getUint32(tf.a) & 0xffffff, tid = bv.getUint32(tf.a + 4);
					const tr = porId[tid]; if (!tr || tr.n) continue;
					let p = tf.a + 8, base = m.start;
					const df = Object.assign({ dur: 0, size: 0, flags: 0 }, trex[tid] || {});
					if (fl & 1) { base = Number(bv.getBigUint64(p)); p += 8; }
					if (fl & 2) p += 4;
					if (fl & 8) { df.dur = bv.getUint32(p); p += 4; }
					if (fl & 16) { df.size = bv.getUint32(p); p += 4; }
					if (fl & 32) { df.flags = bv.getUint32(p); p += 4; }
					const a = acc[tid] || (acc[tid] = { off: [], size: [], dts: [], dur: [], cts: [], key: [], t: 0 });
					const tfdt = um(b, traf, "tfdt");
					if (tfdt) a.t = b[tfdt.a] ? Number(bv.getBigUint64(tfdt.a + 4)) : bv.getUint32(tfdt.a + 4);
					for (const tn of todos(b, traf, "trun")) {
						const f2 = bv.getUint32(tn.a) & 0xffffff, v2 = b[tn.a], cnt = bv.getUint32(tn.a + 4);
						let q = tn.a + 8, dofs = 0, ffl = null;
						if (f2 & 1) { dofs = bv.getInt32(q); q += 4; }
						if (f2 & 4) { ffl = bv.getUint32(q); q += 4; }
						let o = base + dofs;
						for (let i = 0; i < cnt; i++) {
							let d = df.dur, s = df.size, sf = i === 0 && ffl != null ? ffl : df.flags, c = 0;
							if (f2 & 0x100) { d = bv.getUint32(q); q += 4; }
							if (f2 & 0x200) { s = bv.getUint32(q); q += 4; }
							if (f2 & 0x400) { sf = bv.getUint32(q); q += 4; }
							if (f2 & 0x800) { c = v2 ? bv.getInt32(q) : bv.getUint32(q); q += 4; }
							a.off.push(o); a.size.push(s); a.dts.push(a.t); a.dur.push(d); a.cts.push(c); a.key.push((sf >> 16) & 1 ? 0 : 1);
							o += s; a.t += d;
						}
					}
				}
			}
			for (const tid in acc) {
				const tr = porId[tid], a = acc[tid];
				Object.assign(tr, { n: a.off.length, off: Float64Array.from(a.off), size: Uint32Array.from(a.size), dts: Float64Array.from(a.dts), dur: Float64Array.from(a.dur), cts: Float64Array.from(a.cts), key: Uint8Array.from(a.key) });
			}
		}
		for (const t of tracks) if (t.n) { const fim = (t.dts[t.n - 1] + t.dur[t.n - 1]) / t.timescale; if (fim > duracao) duracao = fim; }
		return { file, tracks: tracks.filter((t) => t.n), video: tracks.find((t) => t.kind === "video" && t.n), audios: tracks.filter((t) => t.kind === "audio" && t.n), duracao };
	}

	/* lê as amostras [i0,i1) agrupando as que estão coladas no arquivo (poucas leituras) */
	async function* amostras(file, tr, i0, i1, maxGrupo) {
		maxGrupo = maxGrupo || 4 << 20;
		let i = i0;
		while (i < i1) {
			let j = i + 1, fim = tr.off[i] + tr.size[i];
			while (j < i1 && tr.off[j] === fim && fim - tr.off[i] < maxGrupo) { fim += tr.size[j]; j++; }
			const buf = await lerFaixa(file, tr.off[i], fim);
			for (let k = i; k < j; k++) yield { i: k, data: buf.subarray(tr.off[k] - tr.off[i], tr.off[k] - tr.off[i] + tr.size[k]) };
			i = j;
		}
	}

	/* decodifica uma faixa de áudio inteira para mono Int16 (taxa da própria faixa) + RMS de 10 ms em dB */
	async function audioMono(media, tr, onp) {
		if (typeof AudioDecoder === "undefined") throw new Error("este navegador não tem WebCodecs (use o Chrome ou o Edge atualizados)");
		const cfg = { codec: tr.codec, sampleRate: tr.sampleRate, numberOfChannels: tr.channels || 2 };
		if (tr.desc) cfg.description = tr.desc;
		const ok = await AudioDecoder.isConfigSupported(cfg).catch(() => ({ supported: false }));
		if (!ok.supported) throw new Error("o navegador não decodifica o áudio " + tr.codec);
		const sr = tr.sampleRate, total = Math.ceil(media.duracao * sr) + sr, pcm = new Int16Array(total);
		let erro = null, feitos = 0;
		const dec = new AudioDecoder({
			output: (ad) => {
				try {
					const n = ad.numberOfFrames, ch = ad.numberOfChannels, base = Math.round((ad.timestamp / 1e6) * sr), tmp = new Float32Array(n), soma = new Float32Array(n);
					for (let c = 0; c < ch; c++) { ad.copyTo(tmp, { planeIndex: c, format: "f32-planar" }); for (let k = 0; k < n; k++) soma[k] += tmp[k]; }
					for (let k = 0; k < n; k++) { const idx = base + k; if (idx >= 0 && idx < total) { const v = soma[k] / ch; pcm[idx] = v >= 1 ? 32767 : v <= -1 ? -32768 : Math.round(v * 32767); } }
				} finally { ad.close(); }
			},
			error: (e) => { erro = e; },
		});
		dec.configure(cfg);
		for await (const s of amostras(media.file, tr, 0, tr.n)) {
			if (erro) throw erro;
			dec.decode(new EncodedAudioChunk({ type: "key", timestamp: Math.round(((tr.dts[s.i] + tr.cts[s.i]) / tr.timescale) * 1e6), duration: Math.round((tr.dur[s.i] / tr.timescale) * 1e6), data: s.data }));
			feitos++;
			if (dec.decodeQueueSize > 64) await new Promise((r) => dec.addEventListener("dequeue", r, { once: true }));
			if (onp && feitos % 400 === 0) onp(feitos / tr.n);
		}
		await dec.flush(); dec.close();
		if (erro) throw erro;
		return { sr, pcm, rms: rmsDb(pcm, sr) };
	}

	function rmsDb(pcm, sr) {
		const hop = Math.round(sr * 0.01), m = Math.floor(pcm.length / hop), out = new Float32Array(m);
		for (let i = 0; i < m; i++) { let s = 0; const a = i * hop; for (let k = 0; k < hop; k++) { const v = pcm[a + k] / 32768; s += v * v; } out[i] = 10 * Math.log10(s / hop + 1e-12); }
		return out;
	}

	/* decodificador de vídeo para a exportação: entrega os quadros de [t0,t1) em ordem (começa no quadro-chave anterior) */
	function videoConfig(tr) {
		const c = { codec: tr.codec, codedWidth: tr.width, codedHeight: tr.height, hardwareAcceleration: "prefer-hardware" };
		if (tr.desc && tr.fmt !== "vp09") c.description = tr.desc;
		return c;
	}
	function indicePorTempo(tr, t) {
		/* amostra com cts <= t (busca binária pelo dts; cts ≈ dts + atraso) */
		const x = t * tr.timescale;
		let lo = 0, hi = tr.n - 1;
		while (lo < hi) { const mid = (lo + hi + 1) >> 1; if (tr.dts[mid] <= x) lo = mid; else hi = mid - 1; }
		return lo;
	}
	function chaveAntes(tr, i) { while (i > 0 && !tr.key[i]) i--; return i; }

	window.MP4 = { abrir, amostras, audioMono, rmsDb, videoConfig, indicePorTempo, chaveAntes };
})();
