/* Encaixe automático da voz de um personagem gravada à parte (Craig, cada um gravando o seu) no bruto.
   A voz da pessoa também está na call do bruto (ou vaza no microfone), então comparamos o "desenho" do volume
   dos dois (envelope de 50 ms, depois 10 ms) e achamos o deslocamento em que eles batem (correlação cruzada por FFT).
   Devolve off (segundos): tempo no bruto = tempo no arquivo da pessoa + off. */
(function () {
	"use strict";
	function fft(re, im, inv) {
		const n = re.length;
		for (let i = 1, j = 0; i < n; i++) { let b = n >> 1; for (; j & b; b >>= 1) j ^= b; j ^= b; if (i < j) { let t = re[i]; re[i] = re[j]; re[j] = t; t = im[i]; im[i] = im[j]; im[j] = t; } }
		for (let len = 2; len <= n; len <<= 1) {
			const a = ((inv ? 2 : -2) * Math.PI) / len, wr = Math.cos(a), wi = Math.sin(a), h = len >> 1;
			for (let i = 0; i < n; i += len) { let cr = 1, ci = 0; for (let k = 0; k < h; k++) { const p = i + k, q = p + h, vr = re[q] * cr - im[q] * ci, vi = re[q] * ci + im[q] * cr; re[q] = re[p] - vr; im[q] = im[p] - vi; re[p] += vr; im[p] += vi; const t = cr * wr - ci * wi; ci = cr * wi + ci * wr; cr = t; } }
		}
		if (inv) for (let i = 0; i < n; i++) { re[i] /= n; im[i] /= n; }
	}
	/* envelope: RMS 10 ms (dB) → passo de `k` quadros, log-energia padronizada; silêncio vira 0 */
	function envelope(rms, k) {
		const n = Math.floor(rms.length / k), e = new Float32Array(n);
		for (let i = 0; i < n; i++) { let s = 0; for (let j = 0; j < k; j++) s += Math.pow(10, (rms[i * k + j] || -100) / 10); e[i] = Math.max(-60, 10 * Math.log10(s / k + 1e-12)); }
		let m = 0; for (const v of e) m += v; m /= n || 1; let d = 0; for (const v of e) d += (v - m) ** 2; d = Math.sqrt(d / (n || 1)) || 1;
		for (let i = 0; i < n; i++) e[i] = Math.max(0, (e[i] - m) / d); // só os trechos acima da média (fala) contam
		return e;
	}
	function correlacao(p, r) {
		let N = 1; while (N < p.length + r.length) N <<= 1;
		const pr = new Float64Array(N), pi = new Float64Array(N), rr = new Float64Array(N), ri = new Float64Array(N);
		pr.set(p); rr.set(r); fft(pr, pi); fft(rr, ri);
		for (let i = 0; i < N; i++) { const a = pr[i], b = -pi[i], c = rr[i], d = ri[i]; pr[i] = a * c - b * d; pi[i] = a * d + b * c; }
		fft(pr, pi, true);
		return { c: pr, N }; // c[k] = Σ p[n]·r[n+k]  (k negativo fica em N+k)
	}
	function picos(c, N, maxPos, maxNeg) {
		let best = -Infinity, bk = 0;
		const val = (k) => c[k >= 0 ? k : N + k];
		for (let k = -maxNeg; k <= maxPos; k++) { const v = val(k); if (v > best) { best = v; bk = k; } }
		// segundo pico (longe do primeiro) para medir a confiança
		let seg = -Infinity, soma = 0, q = 0, n = 0;
		for (let k = -maxNeg; k <= maxPos; k++) { const v = val(k); soma += v; q += v * v; n++; if (Math.abs(k - bk) > 20 && v > seg) seg = v; }
		const media = soma / n, dp = Math.sqrt(Math.max(1e-12, q / n - media * media));
		return { k: bk, pico: best, seg, media, z: (best - media) / dp };
	}
	/* sincroniza o áudio `rmsP` (pessoa) contra cada faixa de referência; usa a que bater melhor */
	function sincronizar(rmsP, refs) {
		const K = 5; // 50 ms
		const p = envelope(rmsP, K);
		let melhor = null;
		for (const ref of refs) {
			const r = envelope(ref.rms, K);
			if (!p.length || !r.length) continue;
			const { c, N } = correlacao(p, r), pk = picos(c, N, r.length - 1, p.length - 1);
			const conf = pk.z, razao = (pk.pico - pk.media) / Math.max(1e-9, pk.seg - pk.media);
			// refina em 10 ms em volta do pico
			const p1 = envelope(rmsP, 1), r1 = envelope(ref.rms, 1);
			let bk = pk.k * K, bv = -Infinity;
			for (let k = pk.k * K - K * 2; k <= pk.k * K + K * 2; k++) { let s = 0; for (let i = 0; i < p1.length; i += 2) { const j = i + k; if (j >= 0 && j < r1.length) s += p1[i] * r1[j]; } if (s > bv) { bv = s; bk = k; } }
			const res = { off: bk * 0.01, conf, razao, ref: ref.nome };
			if (!melhor || res.conf > melhor.conf) { if (melhor) res.outra = Math.max(melhor.outra || 0, melhor.conf); melhor = res; } else melhor.outra = Math.max(melhor.outra || 0, res.conf);
		}
		if (melhor) melhor.certo = melhor.conf >= 3.5 && melhor.conf - (melhor.outra || 0) >= 0.6;
		return melhor;
	}
	/* vários arquivos do mesmo gravador (Craig) começam juntos: se a maioria concorda no deslocamento, vale para todos */
	function consenso(lista) {
		const ok = lista.filter((x) => x && x.off != null);
		let melhor = null;
		for (const a of ok) { const iguais = ok.filter((b) => Math.abs(b.off - a.off) < 0.12); if (!melhor || iguais.length > melhor.n) melhor = { n: iguais.length, off: iguais.reduce((s, b) => s + b.off, 0) / iguais.length, ref: a.ref }; }
		return melhor && melhor.n >= 2 && melhor.n >= Math.ceil(ok.length / 2) ? melhor : null;
	}
	window.ED_SINC = sincronizar;
	window.ED_SINC_CONSENSO = consenso;
})();
