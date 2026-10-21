# Editor Problems — regras
- Português. Nunca chaves, senhas ou e-mails no código. Sons e texturas da Mojang nunca no repositório.
- Este repositório é SÓ o editor de vídeo longo. Os Shorts (estúdio de cenas 3D) ficam em `problemsbloxcreate-lab/estudio-problems`; não copie código de lá para cá nem o contrário sem o dono pedir.
- Sempre `git pull --rebase` antes do push. Publicar: `gh workflow run publicar.yml --ref main` (também roda sozinho a cada push em `site/`).
- Conferir antes do push: `for f in site/*.js site/comum/*.js; do node --check "$f"; done`.
- A edição automática segue `.claude/skills/editar-longo/SKILL.md`.

## Login e ligação com o menu (NÃO QUEBRAR) — decisão do dono, 20/10/2026
- Todos os projetos do Estúdio Problems entram SÓ pelo login do Google do menu. Endereço único: https://estudio.problemsraiz.workers.dev
  (menu em `/`, ADM em `/adm`, `/shorts/`, `/editor/`, `/modelador/`, `/animador/`). Nenhum projeto tem senha própria.
- Quem libera é o **porteiro** (Worker `estudio`, conta Cloudflare "problemsraiz", código em `porteiro/` do repo
  `problemsbloxcreate-lab.github.io`): confere o e-mail no servidor `turma-ia` (EMAILS_PERMITIDOS) e guarda um cookie de sessão.
  Os projetos com portão próprio (Shorts, Editor) só aceitam o **passe assinado** do porteiro (cabeçalho `x-porteiro-passe`,
  conferido com `PORTEIRO_URL/chave-publica`). Sem passe → redireciona para o menu. Não crie bypass, senha nem "modo teste".
- Projeto novo: precisa de uma entrada em `PROJETOS` (porteiro/wrangler.toml). Página que precisa de login no navegador usa
  `<script src="/estudio-login.js"></script>`; o botão da conta (foto, nome, e-mail, Minha conta, Voltar ao menu, Sair) é
  `<script src="/estudio-conta.js" defer></script>` (+ opcional `<span data-estudio-conta></span>` no cabeçalho).
- Links internos para o menu usam `/` (raiz do endereço único). Nada de endereços antigos (`*.problemsbloxcreate.workers.dev`
  do Shorts/Editor, `github.io`): o GitHub Pages só serve de origem para o porteiro e redireciona para o endereço único.
- Servidor de sons (`sons-problems`) fica na conta Cloudflare antiga "problemsbloxcreate" (espaço só para os sons). As páginas
  falam com ele pelo `/nuvem/` do porteiro (passe, sem senha); só os robôs do GitHub usam a senha da equipe (SENHA_SONS).
- Conta da pessoa (nome, foto, fundo do menu): `GET/POST /conta` no porteiro (KV PERFIS). Fundo próprio de imagem/vídeo fica só
  no navegador (IndexedDB).
- Depois de qualquer mudança: conferir o diagnóstico da Action "Publicar o porteiro" (todos os projetos com passe aceito).

## Padrão visual de todos os projetos (decisão do dono, 20/10/2026)
- Cabeçalho: nome do projeto em MAIÚSCULAS (ANIMADOR, EDITOR, MODELADOR, SHORTS…) com "Estúdio Problems" embaixo; título da aba `NOME · Estúdio Problems`.
- À direita, sempre o componente `/estudio-conta.js` (`<span data-estudio-conta></span>`): **círculo de espaço no navegador**, **Menu** e **foto da conta**
  (Minha conta, Voltar ao menu, Atualizar todos os sites, itens do projeto, Sair). Não crie botões próprios de voltar ao menu nem de conta.
- Ícones de linha iguais aos do menu (SVG, `stroke="currentColor"`, 1.9), sem emoji nas telas novas.
- Tela inicial com atalhos e projetos/abertos recentemente.
- O que o projeto guarda no navegador aparece no círculo de espaço: banco em `BANCOS` (estudio-conta.js) + `EstudioConta.espaco.registrar(...)` com "Baixar" o arquivo do projeto (.animador, .editor…). Quem passar a guardar algo novo, registra junto.
- Arquivo de projeto de cada programa tem o nome dele como extensão: `.animador`, `.editor`… (os antigos `.toon`/`.edicao.json` continuam abrindo). Formatos de fora (ex.: `.bbmodel` do Blockbench) ficam como são.
- Projeto novo: comece do `modelo-projeto/` do repositório `problemsbloxcreate-lab.github.io` (login do Google/Firebase pelo menu, porteiro, cabeçalho e ícones prontos).
