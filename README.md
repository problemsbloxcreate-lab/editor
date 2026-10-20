# Editor Problems (vídeo longo)

O editor de vídeo longo do canal Problems: carrega o bruto de Minecraft POV com o roteiro falado, sincroniza, separa as falas, monta a linha do tempo com o preset do editor do canal (ritmo, zooms, efeitos, SFX, música por clima) e exporta. O botão **🤖 Editar com o Claude** manda o pedido para a Action `edicao.yml`, que segue a skill `.claude/skills/editar-longo`.

Separado do Estúdio Problems (Shorts, repositório `estudio-problems`) em 20/10/2026: mexer em um não afeta o outro.

- O que vai para o ar é só a pasta `site/` (página principal: `site/index.html`), publicada pela Action **Publicar o editor (Cloudflare)** no Worker `editor-problems` (`worker/site`), na conta "problemsraiz". Ele só abre para quem entrou com o Google pelo menu do Estúdio Problems: o endereço é https://estudio.problemsraiz.workers.dev/editor/ (quem abre o endereço do Worker direto é mandado para lá).
- `site/comum/`: estilo, tema e roteiros (cópia própria; não depende do estúdio).
- `site/whisper/`: o reconhecedor de fala servido pelo próprio site.
- `site/dados/sons-url.json`: o servidor da equipe (Worker `sons-problems`), onde ficam os pedidos e os planos da edição automática.
- Sons e texturas da Mojang nunca entram aqui.

## Segredos do repositório (Settings → Secrets and variables → Actions)
- `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`: publicar o site (conta "problemsraiz", a mesma do porteiro).
- `SENHA_SONS`: a senha da equipe (servidor sons-problems).
- `CLAUDE_CODE_OAUTH_TOKEN`: o Claude da edição automática.
