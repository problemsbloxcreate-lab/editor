# Skill `minecraft-video-editor` v6 (canal Problems) — instalar em outro computador

Exportado da máquina do Matheus. Estado: **v6 (20/10/2026)**, rodada 3 do Matheus incorporada (vozes, música por loudness, SFX do vilão, zoom com foco no objeto, promo + tela final).

## São 2 zips — extraia os DOIS na MESMA pasta
| zip | conteúdo |
|---|---|
| `minecraft-video-editor_v6_INSTALAR.zip` | skill inteira (regras, scripts, SFX, ~50 músicas, presets BERSERKER, índice CLAP, promo e tela final), skills de apoio (`watch`, `minecraft-cinematic`, regras da ponte do Premiere), agente `producao-problems`, extensão **MCP Bridge** do Premiere + presets `.prfpset`, memórias do Claude, research em texto, instalador |
| `minecraft-video-editor_v6_MUSICAS.zip` | biblioteca **Epidemic** local inteira (pastas por clima: TROLL, MISTERIO, TENSAS, VLOGS, EPICAS, 2K25, NUEVAS 2K24…), ~2 GB. Depois de extrair fica a pasta `MUSICAS\` ao lado do `INSTALAR.bat` |

## Transcrição: local, sem chave
O editor transcreve as falas com o **mesmo motor do Estúdio Problems** (whisper-large-v3-turbo, pedaços de 25 s cortados no silêncio, filtro de voz), rodando no próprio PC: na placa NVIDIA leva ~30 s para 8 min de áudio; sem placa, vai pelo processador (mais lento). Não precisa de Groq nem de login.

## Antes de instalar (na máquina nova)
1. **Python 3.11+** (python.org, marcar *Add python.exe to PATH*).
2. **Adobe Premiere Pro** 2024 ou mais novo, **fechado** durante a instalação.
3. **Claude Code** instalado e logado.

## Instalar
Dê dois cliques em **`INSTALAR.bat`** (instala o ffmpeg pelo winget se faltar e roda `instalar.py`). Ele pergunta 3 pastas (Enter aceita o padrão):
- **pasta de trabalho do Claude** (onde você abre o Claude Code, padrão `C:\Users\<você>\Skills`) — as memórias vão para a chave de projeto dessa pasta;
- **pasta das músicas Epidemic** (padrão `Documents\Epidemic 2K23 (Pasta de músicas)`);
- **pasta de mídia de trabalho** (renders, takes, time-lapses; na máquina original era `D:\Pobrs`).

O instalador copia tudo para `~/.claude`, **troca os caminhos da máquina original** (`C:\Users\mathe`, `D:\Pobrs`, `D:\Users\PREDATOR\...Epidemic...`) pelos seus em todos os arquivos, instala a extensão do Premiere e grava `PlayerDebugMode=1` (HKCU\Software\Adobe\CSXS.9–14), roda `pip install -r requirements.txt`, baixa o modelo CLAP (1,2 GB) e o de transcrição (1,6 GB) e no fim roda a **checagem** (`doctor.py`).

Sem perguntas: `python instalar.py --sim --skills "C:\Users\voce\Skills" --epidemic "E:\Epidemic 2K23 (Pasta de músicas)" --work "E:\Pobrs"`.

## Depois de instalar
1. Abra o Premiere → **Janela › Extensões › MCP Bridge** (o painel precisa ficar aberto enquanto o Claude edita).
2. Presets BERSERKER no painel (opcional — o builder recria os efeitos pelo JSON): Efeitos › Presets › botão direito › *Importar presets* → `dependencias\premiere\Effect Presets and Custom Items.prfpset`.
3. Teste a ponte: `python "%USERPROFILE%\.claude\skills\minecraft-video-editor\scripts\doctor.py" --bridge` → tudo **OK**.
4. Abra o Claude Code na pasta de trabalho e peça, por exemplo: *"edita esse bruto do Problems: <caminho>"*.

## Interface "Editor Problems" (arrastar o bruto)
Atalho **Editor Problems** na Área de Trabalho (ou `skill\minecraft-video-editor\app\ABRIR_EDITOR.bat`) → abre http://localhost:4790 no navegador. Arraste o bruto (ou cole o caminho), escolha **Automático / Premiere / FilmCraft**, escreva notas e clique **Editar**. O Claude Code roda a skill em segundo plano (usa a sua assinatura do Claude) e a tela mostra o andamento. No fim:
- **Premiere** (se estiver instalado, aberto e com o painel MCP Bridge aberto): a edição fica num **projeto novo** na pasta do job — o projeto que você estava usando não é tocado;
- **FilmCraft** (sem Premiere, ou se você escolher): o FilmCraft (editor open source) é baixado sozinho na 1ª vez (70 MB, release oficial, SHA256 conferido) e abre com a edição pronta.

## CineCam (B-roll cinemático) — mod criado pelo Claude
Vem completo na skill `minecraft-cinematic`: código atual do mod (v0.7), `.jar` compilado em `assets/cinecam-mod/dist/`, skins da turma em `assets/skins/` e scripts das cenas já feitas. O instalador pergunta se quer preparar agora: instala o **JDK 17** (winget) e faz o 1º build **com internet** (baixa Minecraft 1.20.1 + Forge, ~1–2 GB). Depois o Claude renderiza sozinho. Para fazer depois: `python "%USERPROFILE%\.claude\skills\minecraft-cinematic\scripts\setup_cinecam.py"`.

## O que NÃO vem (e quando faz falta)
- **Brutos, projetos `.prproj` e renders** dos vídeos anteriores: só servem para reabrir edições antigas.
- **Instâncias do Modrinth/Minecraft** (só para extrair SFX novos do jogo; os SFX de Minecraft já vêm prontos em `library/sfx`). Os mundos de render do CineCam não vêm: ele gera de novo pela seed de cada cena.

## Se der FALTA na checagem
| item | correção |
|---|---|
| ffmpeg | `winget install Gyan.FFmpeg` e **reabrir** o terminal |
| pacote X | `python -m pip install -r requirements.txt` |
| ponte MCP | Premiere aberto + painel MCP Bridge aberto; se o painel não aparece no menu, rodar o instalador de novo (registro) e reiniciar o Premiere |
| biblioteca Epidemic | extrair o zip de músicas ao lado do instalador e rodar de novo |
| transcrição local | `python -m pip install faster-whisper nvidia-cublas-cu12 nvidia-cudnn-cu12` |

Por onde o Claude começa: `skill/minecraft-video-editor/SKILL.md` → `references/feedback-timeline-dele-20out.md` (rodada mais recente) → decupagem e rodadas anteriores.
