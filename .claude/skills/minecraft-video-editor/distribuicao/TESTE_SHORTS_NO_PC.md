# Teste do Shorts no PC

As cenas dos Shorts agora podem ser desenhadas no Minecraft de verdade, no PC de quem produz. O estúdio continua igual: luz, cor, filtros, troca de skin, câmera, legendas e inserts. Só a imagem da cena passa a vir do Minecraft. Este guia é para testar isso num PC que ainda não tem nada instalado.

**Windows 10 ou 11 · instalação: 20 a 60 min (uma vez só) · teste: ~15 min por vídeo**

## Antes de começar

- Login no [Estúdio Problems](https://estudio.problemsraiz.workers.dev) com a sua conta da equipe.
- Chrome ou Edge atualizado.
- Uns **10 GB livres** no disco e internet boa (a instalação baixa o Minecraft 1.20.1 com Forge, cerca de 2 GB).
- **8 GB de RAM** no mínimo (16 GB é o ideal: o Minecraft e o estúdio ficam abertos juntos).
- Não precisa comprar o Minecraft nem ter o Premiere para este teste. O instalador traz um Minecraft próprio só para desenhar as cenas.

## Passo a passo

### 1. Instale o Estúdio Problems Local

Abra o menu Iniciar, digite **PowerShell**, abra e cole este comando (depois aperte Enter):

```powershell
irm https://raw.githubusercontent.com/problemsbloxcreate-lab/editor/main/.claude/skills/minecraft-video-editor/distribuicao/EstudioProblemsLocal.ps1 -OutFile $env:TEMP\EstudioProblemsLocal.ps1; powershell -NoProfile -ExecutionPolicy Bypass -File $env:TEMP\EstudioProblemsLocal.ps1
```

Ele instala tudo sozinho, em 6 etapas: ferramentas, código, Claude Code, mídia, CineCam (o Minecraft que desenha as cenas) e o serviço que fica rodando em segundo plano. Não precisa ser administrador. Quando terminar, aparece:

`Pronto. Página local: http://127.0.0.1:4790`

- Se aparecer "winget não encontrado", instale o **Instalador de Aplicativo** (App Installer) pela Microsoft Store e rode o comando de novo. Pode rodar quantas vezes precisar: ele só completa o que falta.
- Na etapa do Claude Code, não precisa entrar com conta para este teste: o login só é usado para editar vídeos longos.

### 2. Confira se o serviço está rodando

Abra http://127.0.0.1:4790 no navegador. Se abrir a página do **Editor Problems**, está tudo certo. O serviço liga sozinho com o Windows a partir de agora.

### 3. Abra o Shorts no estúdio

Entre no [Estúdio Problems](https://estudio.problemsraiz.workers.dev), vá na aba **Shorts** e aperte **Ctrl+F5** para carregar a versão nova.

Deixe **só uma aba** do Shorts aberta durante o teste.

### 4. Mande gerar as cenas

Na lista de vídeos, ache **Rápido Demais: Hack ou Gênio?** e clique em **🖥 No meu PC**.

Abre uma aba nova do serviço local. Confira as opções e clique em **Gerar as cenas**:

- **Motion blur**: vem ligado.
- **Desfoque de lente**: vem desligado. Pode testar dos dois jeitos em outra rodada.

Quando aparecer "Pronto: as cenas vão aparecendo na linha do tempo do Shorts", pode fechar essa aba. Na primeira vez o PC se pareia com o estúdio sozinho.

Se o navegador bloquear a aba nova, o botão vira "Permita pop-ups e clique de novo": libere os pop-ups do estúdio e clique outra vez. O pedido vale 2 minutos.

### 5. Espere o Minecraft desenhar

- Uma janela do Minecraft abre sozinha. **Não feche e não minimize**; pode deixar outra janela na frente.
- A primeira cena leva 1 a 2 minutos (abre o jogo e monta o mundo do vídeo). As outras levam uns 10 a 20 segundos cada.
- A aba do Shorts precisa ficar aberta (pode ficar em segundo plano).
- Na lista de vídeos aparece o andamento: `🖥 NOME-DO-PC: 12/39 cenas · gerando`.
- O Minecraft fecha sozinho 15 minutos depois da última cena.

Algumas cenas continuam no 3D do estúdio porque têm algo que o Minecraft ainda não desenha (martelo do juiz, passagem secreta, raio-x, iceberg) ou porque uma trava de qualidade segurou. É esperado: no Rápido Demais, umas 33 das 39 cenas vêm do Minecraft.

### 6. Confira o resultado

Quando o andamento parar de mudar, aperte **Ctrl+F5** de novo e assista ao vídeo. Marque o que estiver certo:

- [ ] **0:01** · Cena 2: a porta da base abre quando o Problems sai.
- [ ] **0:04** · Cena 4 (vista de cima): mar à esquerda, vila em cima, base embaixo. Tem chão; nada de céu ou vazio no lugar do chão.
- [ ] **0:21** · Cenas 15 a 18: os corações aparecem em cima da cabeça, alinhados com o personagem.
- [ ] **0:32** · Cena 22: o barco aparece ao lado do Problems.
- [ ] **0:35** · Cena 24: o Problems rema o barco na água, com os remos mexendo.
- [ ] **0:45** · Cena 30: o barco corre no túnel de gelo azul, e o túnel está aberto (não tem terra por dentro).
- [ ] **todas** · Nenhum braço ou perna "vai e volta" (rollback), ninguém desliza pelo chão e nada atravessa parede ou corpo.
- [ ] **todas** · Luz, filtros, legendas e inserts do estúdio continuam aparecendo por cima das cenas do Minecraft.
- [ ] **todas** · O vídeo toca liso no preview, sem pulos para trás.

## Regras do teste

> **Um PC por vídeo.** Se duas pessoas mandarem o mesmo vídeo ao mesmo tempo, os dois PCs fazem o mesmo trabalho e um apaga o do outro.
>
> **Não fique mandando de novo.** A nuvem antiga da equipe grava no máximo 1000 arquivos por dia, e ela também guarda a reserva, as cópias de segurança e as imagens de revisão. Um vídeo inteiro gasta umas 80 gravações. Mande uma vez e espere terminar.
>
> **Se aparecer "nuvem no limite"**, pare o teste: a cota volta às 21h (horário de Brasília).

## Se algo der errado

| O que aparece | O que fazer |
|---|---|
| 127.0.0.1 não abre | O serviço não está rodando. Rode o comando de instalação de novo: ele reabre o serviço sozinho. Não precisa reiniciar o PC nem mexer no Gerenciador de Tarefas. |
| Alguém pediu para "atualizar" ou "reiniciar o serviço" | Rode o comando de instalação de novo. O serviço também se atualiza sozinho em até 15 minutos, e ao clicar em 🖥 No meu PC ele confere se há versão nova antes de começar. |
| "Permita pop-ups" | Libere pop-ups para o site do estúdio e clique em 🖥 No meu PC outra vez. |
| "pedido vencido" | O pedido vale 2 minutos. Volte ao Shorts e clique de novo. |
| "entre pelo menu" | O login do estúdio expirou. Entre de novo pelo menu do Estúdio e repita. |
| 0 cenas por muito tempo | Confira que só há uma aba do Shorts aberta, aperte Ctrl+F5 nela e deixe aberta. Se o Minecraft não abriu, rode o comando de instalação de novo. |
| "com erro" no andamento | Anote o número da cena e mande no retorno. A cena com erro continua no 3D, o resto do vídeo segue. |
| "nuvem no limite" | Pare e tente depois das 21h. |

## Como mandar o retorno

Para cada problema, mande: **o vídeo**, **o número da cena** (aparece na linha do tempo, como #04), **o tempo** e um **print ou gravação de tela** do preview. Diga também o que a lista mostrou no andamento (por exemplo `🖥 PC-SALA: 31/39 cenas · 2 com erro`) e quantos GB de RAM o PC tem.
