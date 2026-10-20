/* Tema claro/escuro, o mesmo nas três etapas (Roteiro, Gravação, Vídeo).
   A escolha fica neste navegador (ep:tema). Sem escolha, cada página usa o seu padrão (<html data-padrao="claro|escuro">).
   Carregue no <head>; o botão ☀/🌙 entra sozinho no cabeçalho (elemento [data-tema-aqui], ou o primeiro <header>). */
(function () {
  var CHAVE = "ep:tema", raiz = document.documentElement;
  function ler() { try { return localStorage.getItem(CHAVE); } catch (e) { return null; } }
  function atual() { return ler() || raiz.getAttribute("data-padrao") || "escuro"; }
  function aplicar(t) { raiz.setAttribute("data-theme", t === "claro" ? "light" : "dark"); raiz.style.colorScheme = t === "claro" ? "light" : "dark"; }
  aplicar(atual());
  function botao() {
    var lugar = document.querySelector("[data-tema-aqui]") || document.querySelector("header");
    if (!lugar || document.getElementById("temaBtn")) return;
    var b = document.createElement("button");
    b.type = "button"; b.id = "temaBtn"; b.className = "tema-btn";
    function rotulo() { var c = atual() === "claro"; b.textContent = c ? "🌙" : "☀️"; b.title = c ? "Mudar para o tema escuro" : "Mudar para o tema claro"; b.setAttribute("aria-label", b.title); }
    rotulo();
    b.addEventListener("click", function () {
      var novo = atual() === "claro" ? "escuro" : "claro";
      try { localStorage.setItem(CHAVE, novo); } catch (e) {}
      aplicar(novo); rotulo();
      window.dispatchEvent(new CustomEvent("ep:tema", { detail: novo }));
    });
    lugar.appendChild(b);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", botao); else botao();
  /* outra aba do site mudou o tema: acompanha */
  window.addEventListener("storage", function (e) { if (e.key === CHAVE) { aplicar(atual()); var b = document.getElementById("temaBtn"); if (b) b.textContent = atual() === "claro" ? "🌙" : "☀️"; } });
})();
