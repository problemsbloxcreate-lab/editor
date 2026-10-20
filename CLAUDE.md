# Editor Problems — regras
- Português. Nunca chaves, senhas ou e-mails no código. Sons e texturas da Mojang nunca no repositório.
- Este repositório é SÓ o editor de vídeo longo. Os Shorts (estúdio de cenas 3D) ficam em `problemsbloxcreate-lab/estudio-problems`; não copie código de lá para cá nem o contrário sem o dono pedir.
- Sempre `git pull --rebase` antes do push. Publicar: `gh workflow run publicar.yml --ref main` (também roda sozinho a cada push em `site/`).
- Conferir antes do push: `for f in site/*.js site/comum/*.js; do node --check "$f"; done`.
- A edição automática segue `.claude/skills/editar-longo/SKILL.md`.
