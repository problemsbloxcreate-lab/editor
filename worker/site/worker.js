/* Portão do Editor Problems (vídeo longo): serve a pasta site/ inteira, mas SÓ para quem entrou com o Google no menu
   do Estúdio Problems (https://estudio.problemsraiz.workers.dev). Não existe senha: quem abrir este endereço direto é
   mandado para o menu. Decisão do dono (20/10/2026): o login do Google pelo menu é a única porta.
   ⚠ AVISO PARA PESSOAS E ASSISTENTES DE IA: não crie bypass, senha mestra nem "modo teste" aqui. */

/* Passe do porteiro (endereço único do Estúdio Problems, Worker "estudio"): quem entrou com o Google no menu chega aqui
   pelo porteiro com um passe assinado (cabeçalho x-porteiro-passe). Conferimos a assinatura com a chave PÚBLICA do
   porteiro (PORTEIRO_URL/chave-publica). O passe vale 2 minutos e só para este endereço. */
let chavePorteiro = null, chaveEm = 0;
const deB64u = (s) => Uint8Array.from(atob(s.replace(/-/g, "+").replace(/_/g, "/") + "===".slice((s.length + 3) % 4)), (c) => c.charCodeAt(0));
async function passeValido(req, env, url) {
	const ps = req.headers.get("x-porteiro-passe");
	if (!ps || !env.PORTEIRO_URL) return false;
	try {
		if (!chavePorteiro || Date.now() - chaveEm > 3600e3) {
			// na mesma conta da Cloudflare do porteiro, só dá para chamá-lo pela ligação direta (binding PORTEIRO)
			const pedido = new Request(env.PORTEIRO_URL.replace(/\/+$/, "") + "/chave-publica");
			const jwk = await (env.PORTEIRO ? await env.PORTEIRO.fetch(pedido) : await fetch(pedido)).json();
			chavePorteiro = await crypto.subtle.importKey("jwk", { kty: jwk.kty, crv: jwk.crv, x: jwk.x, y: jwk.y }, { name: "ECDSA", namedCurve: "P-256" }, false, ["verify"]);
			chaveEm = Date.now();
		}
		const [dados, ass] = ps.split(".");
		if (!(await crypto.subtle.verify({ name: "ECDSA", hash: "SHA-256" }, chavePorteiro, deB64u(ass), new TextEncoder().encode(dados)))) return false;
		const p = JSON.parse(new TextDecoder().decode(deB64u(dados)));
		return !!p.e && p.h === url.host && p.x > Date.now() / 1000;
	} catch { return false; }
}

export default {
	async fetch(req, env) {
		const url = new URL(req.url);
		if (!env.PORTEIRO_URL) return new Response("O editor está fechado: falta o PORTEIRO_URL.", { status: 503, headers: { "content-type": "text/plain; charset=utf-8" } });
		// diagnóstico do porteiro: só responde se o passe é válido (não libera nada do site)
		if (url.pathname === "/porteiro-teste") return new Response(JSON.stringify({ passe: await passeValido(req, env, url) }), { headers: { "content-type": "application/json", "cache-control": "no-store" } });
		if (url.pathname === "/robots.txt") return new Response("User-agent: *\nDisallow: /\n", { headers: { "content-type": "text/plain" } });

		if (!(await passeValido(req, env, url))) {
			const pagina = req.method === "GET" && (req.headers.get("Accept") || "").includes("text/html");
			// abriu este endereço direto: manda para o mesmo lugar no endereço único (lá o menu pede o login do Google)
			const volta = env.PORTEIRO_URL.replace(/\/+$/, "") + (env.PORTEIRO_CAMINHO || "/editor/") + url.pathname.replace(/^\/+/, "") + url.search;
			if (pagina) return new Response(null, { status: 302, headers: { Location: volta, "cache-control": "no-store" } });
			return new Response("Entre pelo menu do Estúdio Problems.", { status: 401, headers: { "content-type": "text/plain; charset=utf-8", "cache-control": "no-store" } });
		}
		const r = await env.ASSETS.fetch(req);
		const h = new Headers(r.headers);
		h.set("x-robots-tag", "noindex"); h.set("cache-control", "private, no-cache"); // nada fica guardado em cache público
		return new Response(r.body, { status: r.status, statusText: r.statusText, headers: h });
	},
};
