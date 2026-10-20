/* Separar a call (todos numa faixa só) por personagem.
   Não é separação de fonte: cada trecho de fala (janelas de ~1 s) é medido pelo timbre (coeficientes cepstrais da voz)
   e pela altura (tom), os trechos parecidos são agrupados (k-means) e cada grupo vira uma faixa de voz própria.
   Funciona bem quando as vozes são diferentes; quando dois falam AO MESMO TEMPO, o trecho vai para quem estiver mais forte.
   Depois o dono dá o nome de cada faixa (clique no nome da faixa) e pode ouvir cada uma com o S. */
(function () {
	"use strict";
	const SR = 16000, NFFT = 512, HOPF = 256, NMEL = 26, NCEP = 13, JAN = 1.0;

	/* FFT radix-2 (in place) */
	function fft(re, im) {
		const n = re.length;
		for (let i = 1, j = 0; i < n; i++) { let b = n >> 1; for (; j & b; b >>= 1) j ^= b; j ^= b; if (i < j) { [re[i], re[j]] = [re[j], re[i]]; [im[i], im[j]] = [im[j], im[i]]; } }
		for (let len = 2; len <= n; len <<= 1) {
			const a = (-2 * Math.PI) / len, wr = Math.cos(a), wi = Math.sin(a);
			for (let i = 0; i < n; i += len) { let cr = 1, ci = 0; for (let k = 0; k < len / 2; k++) { const ur = re[i + k], ui = im[i + k], vr = re[i + k + len / 2] * cr - im[i + k + len / 2] * ci, vi = re[i + k + len / 2] * ci + im[i + k + len / 2] * cr; re[i + k] = ur + vr; im[i + k] = ui + vi; re[i + k + len / 2] = ur - vr; im[i + k + len / 2] = ui - vi; const t = cr * wr - ci * wi; ci = cr * wi + ci * wr; cr = t; } }
		}
	}
	const hz2mel = (h) => 2595 * Math.log10(1 + h / 700), mel2hz = (m) => 700 * (Math.pow(10, m / 2595) - 1);
	const FILT = (() => { const lo = hz2mel(80), hi = hz2mel(7600), pts = []; for (let i = 0; i < NMEL + 2; i++) pts.push(Math.floor(((NFFT + 1) * mel2hz(lo + ((hi - lo) * i) / (NMEL + 1))) / SR)); const f = []; for (let m = 1; m <= NMEL; m++) { const w = new Float32Array(NFFT / 2 + 1); for (let k = pts[m - 1]; k < pts[m]; k++) w[k] = (k - pts[m - 1]) / Math.max(1, pts[m] - pts[m - 1]); for (let k = pts[m]; k <= pts[m + 1]; k++) w[k] = (pts[m + 1] - k) / Math.max(1, pts[m + 1] - pts[m]); f.push(w); } return f; })();
	const HANN = Float32Array.from({ length: NFFT }, (_, i) => 0.5 - 0.5 * Math.cos((2 * Math.PI * i) / (NFFT - 1)));

	/* características de uma janela de fala: média e desvio dos cepstrais + tom mediano */
	function medir(x) {
		const re = new Float32Array(NFFT), im = new Float32Array(NFFT), ceps = [], tons = [];
		for (let p = 0, q = 0; p + NFFT <= x.length; p += HOPF, q++) {
			let e = 0; for (let i = 0; i < NFFT; i++) { const v = x[p + i]; e += v * v; re[i] = v * HANN[i]; im[i] = 0; }
			if (e / NFFT < 1e-6) continue; // quadro quase mudo
			fft(re, im);
			const mel = new Float32Array(NMEL);
			for (let m = 0; m < NMEL; m++) { let s = 0; const w = FILT[m]; for (let k = 0; k <= NFFT / 2; k++) if (w[k]) s += w[k] * (re[k] * re[k] + im[k] * im[k]); mel[m] = Math.log(s + 1e-9); }
			const c = new Float32Array(NCEP);
			for (let k = 0; k < NCEP; k++) { let s = 0; for (let m = 0; m < NMEL; m++) s += mel[m] * Math.cos((Math.PI * k * (m + 0.5)) / NMEL); c[k] = s; }
			ceps.push(c);
			if (q % 3 === 0) { // tom por autocorrelação (70–400 Hz), 1 a cada 3 quadros
				let best = 0, lag = 0; const a0 = 40, a1 = 228;
				for (let L = a0; L <= a1; L++) { let s = 0; for (let i = 0; i + L < NFFT; i += 2) s += x[p + i] * x[p + i + L]; if (s > best) { best = s; lag = L; } }
				if (lag && best > 0.3 * e / 2) tons.push(Math.log(SR / lag));
			}
		}
		if (ceps.length < 8) return null;
		const f = [];
		for (let k = 1; k < NCEP; k++) { let s = 0; for (const c of ceps) s += c[k]; const m = s / ceps.length; let v = 0; for (const c of ceps) v += (c[k] - m) * (c[k] - m); f.push(m, Math.sqrt(v / ceps.length)); }
		tons.sort((a, b) => a - b); f.push(tons.length ? tons[tons.length >> 1] * 6 : 0); // tom pesa mais (separa grave/agudo)
		return f;
	}

	/* k-means++ com várias tentativas; devolve rótulos e a "nota" (silhueta simplificada) */
	let semente = 1;
	const aleat = () => { semente = (semente + 0x6d2b79f5) | 0; let t = Math.imul(semente ^ (semente >>> 15), 1 | semente); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
	function kmeans(X, K, tent) {
		let melhor = null; semente = 12345 + K;
		for (let t = 0; t < (tent || 6); t++) {
			const C = [X[Math.floor(aleat() * X.length)].slice()];
			while (C.length < K) { const d = X.map((x) => Math.min(...C.map((c) => dist(x, c)))), s = d.reduce((a, b) => a + b, 0); let r = aleat() * s, i = 0; while (r > d[i] && i < X.length - 1) { r -= d[i]; i++; } C.push(X[i].slice()); }
			let lab = new Int32Array(X.length);
			for (let it = 0; it < 40; it++) {
				let mudou = false;
				for (let i = 0; i < X.length; i++) { let b = 0, bd = Infinity; for (let k = 0; k < K; k++) { const d = dist(X[i], C[k]); if (d < bd) { bd = d; b = k; } } if (lab[i] !== b) { lab[i] = b; mudou = true; } }
				for (let k = 0; k < K; k++) { const m = X.filter((_, i) => lab[i] === k); if (!m.length) continue; C[k] = m[0].map((_, j) => m.reduce((a, x) => a + x[j], 0) / m.length); }
				if (!mudou) break;
			}
			const inercia = X.reduce((a, x, i) => a + dist(x, C[lab[i]]), 0);
			if (!melhor || inercia < melhor.inercia) melhor = { lab, C, inercia };
		}
		// silhueta (amostrada) para escolher quantas pessoas
		const idx = X.map((_, i) => i).filter((_, i) => X.length < 400 || i % Math.ceil(X.length / 400) === 0);
		let sil = 0;
		for (const i of idx) {
			const dm = new Array(K).fill(0), n = new Array(K).fill(0);
			for (const j of idx) { if (i === j) continue; dm[melhor.lab[j]] += Math.sqrt(dist(X[i], X[j])); n[melhor.lab[j]]++; }
			const a = n[melhor.lab[i]] ? dm[melhor.lab[i]] / n[melhor.lab[i]] : 0, b = Math.min(...dm.map((v, k) => (k === melhor.lab[i] || !n[k] ? Infinity : v / n[k])));
			sil += isFinite(b) ? (b - a) / Math.max(a, b, 1e-9) : 0;
		}
		melhor.sil = sil / idx.length;
		return melhor;
	}
	function dist(a, b) { let s = 0; for (let i = 0; i < a.length; i++) { const d = a[i] - b[i]; s += d * d; } return s; }

	/* separa a faixa de voz `vid` em K faixas (K = 0 → descobre sozinho, de 2 a 6) */
	async function separar(vid, K, onp) {
		const P = ED.P, A = window.ED_CORTE;
		const clipes = P.clipes.filter((c) => c.faixa === vid && !c.off && c.midia);
		if (!clipes.length) throw new Error("a faixa está vazia");
		// janelas de fala de ~1 s no tempo da FONTE de cada clipe
		const jan = [];
		for (const c of clipes) {
			const rt = ED.RT[c.midia], aud = rt && !rt.buf && rt.aud && rt.aud[c.trilha || 0], buf = rt && rt.buf;
			const rms = aud ? aud.rms : rt && rt.rms; if (!rms) continue;
			const m = A.mascara(rms), vel = c.vel || 1, s0 = c.fonte, s1 = c.fonte + c.dur * vel;
			for (let i = Math.floor(s0 * 100); i < Math.ceil(s1 * 100);) {
				if (!m[i]) { i++; continue; } let j = i; while (j < Math.ceil(s1 * 100) && m[j]) j++;
				const a = i / 100, b = j / 100, n = Math.max(1, Math.round((b - a) / JAN));
				for (let k = 0; k < n; k++) jan.push({ c, a: a + ((b - a) * k) / n, b: a + ((b - a) * (k + 1)) / n, aud, buf });
				i = j;
			}
		}
		if (jan.length < 6) throw new Error("tem pouca fala nessa faixa para separar");
		// mede cada janela (16 kHz mono)
		const X = [], ok = [];
		for (let w = 0; w < jan.length; w++) {
			const J = jan[w], n = Math.floor((J.b - J.a) * SR), x = new Float32Array(n);
			if (J.aud) { const r = J.aud.sr / SR; for (let i = 0; i < n; i++) { const k = Math.floor((J.a + i / SR) * J.aud.sr); let s = 0, q = 0; for (let z = 0; z < r; z++) { s += J.aud.pcm[k + z] || 0; q++; } x[i] = s / q / 32768; } }
			else { const ch = J.buf.getChannelData(0), sr = J.buf.sampleRate; for (let i = 0; i < n; i++) x[i] = ch[Math.floor((J.a + i / SR) * sr)] || 0; }
			const f = medir(x); if (f) { X.push(f); ok.push(J); }
			if (onp && w % 50 === 0) { onp(w / jan.length); await new Promise((r) => setTimeout(r, 0)); }
		}
		if (X.length < 6) throw new Error("não deu para medir as vozes (fala muito curta)");
		// padroniza cada característica
		const D = X[0].length;
		for (let j = 0; j < D; j++) { let m = 0; for (const x of X) m += x[j]; m /= X.length; let v = 0; for (const x of X) v += (x[j] - m) ** 2; const sd = Math.sqrt(v / X.length) || 1; for (const x of X) x[j] = (x[j] - m) / sd; }
		let res = null;
		if (K >= 2) res = kmeans(X, Math.min(K, X.length), 24);
		else {
			// mais uma pessoa só entra se melhorar bem a separação, e nunca se dois grupos ficarem parecidos demais
			for (let k = 2; k <= Math.min(6, Math.floor(X.length / 4)); k++) {
				const r = kmeans(X, k, 20); r.k = k;
				let perto = Infinity; for (let i = 0; i < r.C.length; i++) for (let j = i + 1; j < r.C.length; j++) perto = Math.min(perto, Math.sqrt(dist(r.C[i], r.C[j])));
				const espalho = Math.sqrt(r.inercia / X.length);
				if (k > 2 && perto < 1.6 * espalho) break;
				if (!res || r.sil > res.sil + 0.06) res = r;
			}
		}
		// suaviza: rótulo isolado entre dois iguais do mesmo trecho vira o dos vizinhos
		const lab = Array.from(res.lab);
		for (let i = 1; i + 1 < lab.length; i++) if (lab[i - 1] === lab[i + 1] && lab[i] !== lab[i - 1] && ok[i - 1].c === ok[i].c && Math.abs(ok[i].a - ok[i - 1].b) < 0.05 && Math.abs(ok[i + 1].a - ok[i].b) < 0.05) lab[i] = lab[i - 1];
		const nK = res.C.length;
		// cria as faixas e põe cada pedaço de fala na faixa da sua voz (tempo da linha do tempo)
		const vOrig = P.vozes.find((v) => v.id === vid), contagem = new Array(nK).fill(0);
		lab.forEach((l, i) => { contagem[l] += ok[i].b - ok[i].a; });
		const ordem = contagem.map((s, k) => [s, k]).sort((a, b) => b[0] - a[0]).map((x) => x[1]); // quem fala mais vem primeiro
		ED.mexer(() => {
			const novas = {};
			ordem.forEach((k, i) => { const v = ED.novaVoz((vOrig ? vOrig.nome : "Call") + " · voz " + (i + 1), "voz"); v.daCall = vid; novas[k] = v.id; });
			// junta janelas seguidas da mesma voz
			const pedacos = [];
			ok.forEach((J, i) => { const l = lab[i], u = pedacos[pedacos.length - 1]; if (u && u.l === l && u.c === J.c && J.a - u.b < 0.35) u.b = J.b; else pedacos.push({ l, c: J.c, a: J.a, b: J.b }); });
			for (const p of pedacos) {
				const c = p.c, vel = c.vel || 1, a = Math.max(c.fonte, p.a - 0.06), b = Math.min(c.fonte + c.dur * vel, p.b + 0.08);
				P.clipes.push({ id: ED.rid(), faixa: novas[p.l], midia: c.midia, trilha: c.trilha, ini: c.ini + (a - c.fonte) / vel, dur: (b - a) / vel, fonte: a, vel: c.vel, vol: c.vol || 0 });
			}
			// a call inteira fica guardada, silenciada (some sem apagar)
			ED.fstate(vid).mudo = true;
		});
		ED.montarFaixas(); ED.cabecalhos();
		return { vozes: nK, janelas: X.length, segundos: contagem.map((s) => Math.round(s)) };
	}
	window.ED_SEPARAR = separar;
})();
