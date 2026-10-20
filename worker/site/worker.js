/* Portão do Editor Problems (vídeo longo): serve a pasta site/ inteira, mas só para quem sabe a senha do estúdio.
   A senha é o segredo SENHA_SITE do Worker (nunca no código). Quem acerta ganha um cookie de 1 ano;
   trocar a senha derruba todos os cookies antigos. Sem a senha configurada, o site fica FECHADO. */

const COOKIE = "ep_site";
const ANO = 365 * 24 * 3600;

async function ficha(senha) { // valor do cookie: HMAC da senha (não dá para descobrir a senha a partir dele)
	const k = await crypto.subtle.importKey("raw", new TextEncoder().encode(senha), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
	const s = await crypto.subtle.sign("HMAC", k, new TextEncoder().encode("editor-problems/v1"));
	return [...new Uint8Array(s)].map((b) => b.toString(16).padStart(2, "0")).join("");
}
function igual(a, b) {
	const ea = new TextEncoder().encode(a || ""), eb = new TextEncoder().encode(b || "");
	let d = ea.length ^ eb.length;
	for (let i = 0; i < Math.max(ea.length, eb.length); i++) d |= (ea[i] || 0) ^ (eb[i] || 0);
	return d === 0;
}
function cookieDe(req) {
	const m = (req.headers.get("Cookie") || "").match(new RegExp("(?:^|;\\s*)" + COOKIE + "=([a-f0-9]{64})"));
	return m ? m[1] : "";
}
/* Passe do porteiro (endereço único do Estúdio Problems, Worker "estudio"): quem entrou com o Google no menu chega aqui
   pelo porteiro com um passe assinado (cabeçalho x-porteiro-passe). Conferimos a assinatura com a chave PÚBLICA do
   porteiro (PORTEIRO_URL/chave-publica). O passe vale 2 minutos e só para este endereço. Sem passe válido, vale a senha. */
let chavePorteiro = null, chaveEm = 0;
const deB64u = (s) => Uint8Array.from(atob(s.replace(/-/g, "+").replace(/_/g, "/") + "===".slice((s.length + 3) % 4)), (c) => c.charCodeAt(0));
async function passeValido(req, env, url) {
	const ps = req.headers.get("x-porteiro-passe");
	if (!ps || !env.PORTEIRO_URL) return false;
	try {
		if (!chavePorteiro || Date.now() - chaveEm > 3600e3) {
			const jwk = await (await fetch(env.PORTEIRO_URL.replace(/\/+$/, "") + "/chave-publica")).json();
			chavePorteiro = await crypto.subtle.importKey("jwk", { kty: jwk.kty, crv: jwk.crv, x: jwk.x, y: jwk.y }, { name: "ECDSA", namedCurve: "P-256" }, false, ["verify"]);
			chaveEm = Date.now();
		}
		const [dados, ass] = ps.split(".");
		if (!(await crypto.subtle.verify({ name: "ECDSA", hash: "SHA-256" }, chavePorteiro, deB64u(ass), new TextEncoder().encode(dados)))) return false;
		const p = JSON.parse(new TextDecoder().decode(deB64u(dados)));
		return !!p.e && p.h === url.host && p.x > Date.now() / 1000;
	} catch { return false; }
}
const voltarPara = (u) => { const v = u.searchParams.get("v") || "/"; return v.startsWith("/") && !v.startsWith("//") ? v : "/"; };

function telaSenha(erro, volta) {
	const h = `<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>Editor Problems</title>
<style>
:root{--bg:#f9fbfd;--fg:#202124;--muted:#5f6368;--line:#dadce0;--card:#fff;--ciano:#00b8c4}
@media (prefers-color-scheme:dark){:root{--bg:#141518;--fg:#e8eaed;--muted:#9aa0ab;--line:#33363e;--card:#1c1d21;--ciano:#19f0f0}}
*{box-sizing:border-box}html,body{height:100%;margin:0}
body{background:var(--bg);color:var(--fg);font:15px/1.4 system-ui,-apple-system,"Segoe UI",Arial,sans-serif;display:grid;place-items:center;padding:16px}
form{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:28px 26px;width:100%;max-width:340px;display:flex;flex-direction:column;gap:14px;box-shadow:0 10px 30px rgba(0,0,0,.08);animation:sobe .35s ease-out}
@keyframes sobe{from{opacity:0;transform:translateY(8px)}}
.logo{width:44px;height:44px;border-radius:8px;background:var(--ciano);box-shadow:inset 0 0 0 4px rgba(0,0,0,.18);align-self:center}
h1{margin:0;font-size:20px;text-align:center}
input{font:inherit;color:inherit;background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:11px 12px;width:100%}
input:focus{outline:2px solid var(--ciano);outline-offset:1px}
button{font:600 15px inherit;border:0;border-radius:8px;padding:11px;background:var(--ciano);color:#062022;cursor:pointer}
.erro{color:#d93025;font-size:13px;text-align:center;margin:0;min-height:1em}
${erro ? "form{animation:treme .35s}@keyframes treme{25%{transform:translateX(-6px)}75%{transform:translateX(6px)}}" : ""}
@media (prefers-reduced-motion:reduce){form{animation:none}}
</style></head><body>
<form method="post" action="/entrar?v=${encodeURIComponent(volta)}"><span class="logo" aria-hidden="true"></span><h1>Editor Problems</h1>
<input type="password" name="senha" placeholder="Senha" autocomplete="current-password" autofocus required aria-label="Senha">
<button type="submit">Entrar</button><p class="erro" role="alert">${erro ? "Senha errada." : ""}</p></form></body></html>`;
	return new Response(h, { status: erro ? 401 : 200, headers: { "content-type": "text/html; charset=utf-8", "cache-control": "no-store", "x-robots-tag": "noindex" } });
}

export default {
	async fetch(req, env) {
		const url = new URL(req.url);
		if (!env.SENHA_SITE) return new Response("O site está fechado: falta configurar a senha.", { status: 503, headers: { "content-type": "text/plain; charset=utf-8" } });
		if (url.pathname === "/robots.txt") return new Response("User-agent: *\nDisallow: /\n", { headers: { "content-type": "text/plain" } });
		const certo = await ficha(env.SENHA_SITE);

		if (url.pathname === "/entrar" && req.method === "POST") {
			const f = await req.formData().catch(() => null), senha = f ? String(f.get("senha") || "") : "";
			if (!igual(senha, env.SENHA_SITE)) { await new Promise((r) => setTimeout(r, 600)); return telaSenha(true, voltarPara(url)); }
			return new Response(null, { status: 303, headers: { Location: voltarPara(url), "Set-Cookie": `${COOKIE}=${certo}; Path=/; Max-Age=${ANO}; HttpOnly; Secure; SameSite=Lax` } });
		}
		if (url.pathname === "/sair") return new Response(null, { status: 303, headers: { Location: "/", "Set-Cookie": `${COOKIE}=; Path=/; Max-Age=0; HttpOnly; Secure; SameSite=Lax` } });

		const porPorteiro = await passeValido(req, env, url);
		if (!porPorteiro && !igual(cookieDe(req), certo)) {
			const pagina = req.method === "GET" && (req.headers.get("Accept") || "").includes("text/html");
			if (pagina) return telaSenha(false, url.pathname + url.search);
			return new Response("precisa da senha do estúdio", { status: 401, headers: { "content-type": "text/plain; charset=utf-8", "cache-control": "no-store" } });
		}
		const r = await env.ASSETS.fetch(req);
		/* vídeo apagado (ou link velho): em vez de "página não encontrada", volta para o estúdio com a lista dos vídeos */
		if (r.status === 404 && req.method === "GET" && /^\/videos\/[a-z0-9][a-z0-9-]*\/?(index\.html)?$/.test(url.pathname) && (req.headers.get("Accept") || "").includes("text/html"))
			return new Response(null, { status: 302, headers: { Location: "/?app=shorts&apagado=" + encodeURIComponent(url.pathname.split("/")[2] || ""), "cache-control": "no-store" } });
		const h = new Headers(r.headers);
		h.set("x-robots-tag", "noindex"); h.set("cache-control", "private, no-cache"); // nada fica guardado em cache público
		return new Response(r.body, { status: r.status, statusText: r.statusText, headers: h });
	},
};
