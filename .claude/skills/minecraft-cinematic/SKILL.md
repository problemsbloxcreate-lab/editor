---
name: minecraft-cinematic
description: Criar vídeos curtos de Minecraft de altíssima qualidade e muito cinemáticos, com movimentos de câmera dinâmicos (aerial swoop, órbita, travessia de folhagem com paralaxe, whip pan, dolly-zoom, dutch roll, push-in, voo com bank), motion blur de obturador, grade de cor, bloom, vinheta e grain — renderizados por mim no Minecraft REAL (mod CineCam, frame a frame, 16:9 por padrão), sem BBS/Blender. Use SEMPRE que o Matheus pedir animação/abertura/intro/cinematic/trailer/plano de câmera de Minecraft, "movimentação de câmera", "câmera cinematográfica", "tipo o vídeo do Bionic", mandar referência de vídeo/short de Minecraft para replicar o estilo, ou pedir um vídeo curto de Minecraft que eu mesmo renderize — mesmo sem dizer a palavra "skill".
---

# Minecraft Cinematic — câmera de cinema dentro do Minecraft real

Eu sou o diretor de fotografia **e** o operador de render: desenho a câmera em Python (curvas, não palpite), valido numericamente e visualmente, e o mod **CineCam** renderiza frame a frame no Minecraft real (sombras/texturas vanilla, shaders opcionais), com motion blur correto, entregando MP4.

Decisões do Matheus (15/10/2026): **Minecraft real renderizado por mim**, **16:9 prioritário** (vertical 9:16 sob pedido), **shaders opcionais** (nem sempre), personagens articulados e efeitos "quando necessário", **câmera é o foco**.

## Antes de tudo, ler
0. **[`references/enquadramento.md`](references/enquadramento.md) — REGRAS DE ENQUADRAMENTO E ATUAÇÃO (21/10/2026, pesquisa de um agente sênior de layout após o feedback do Matheus: NUNCA personagem de perfil — frente ou 3/4; costas só com motivo; blocking aberto para a câmera; tamanhos de plano; posição na tela; movimentos por intenção; checklist; tabela de atuação por emoção). Vale sobre qualquer nota antiga que contradiga. LER PRIMEIRO em qualquer take com personagem.**
0b. **[`references/cinematicas-contexto.md`](references/cinematicas-contexto.md) — CONTEXTO DA CENA (22/10/2026, feedback do Matheus no "Chico BRoyale"): a cinemática recria o que ACONTECE na gameplay (correndo continua correndo, explosão do lado certo, mobs andando, blocos sendo colocados, queda/voo com câmera junto), ninguém parado (fala com gesto o take inteiro, quem ouve reage), skin do criador = o PNG DELE (nunca um alias da turma), noite = time 13000. Peças prontas em `scripts/cinecam/choreo.py` (tnt/explosion/pop_block/mob_walk/run_lin/fly/follow_cam). Gotchas: limpar o set entre fichas do mesmo lote, NBT `Fuse` maiúsculo, difficulty normal p/ hostis, wobble ramp>0.**
1. [`references/camera-language.md`](references/camera-language.md) — a gramática aprendida das 5 referências (números, quando usar cada movimento, 12 regras). **LER antes de desenhar qualquer plano.**
2. [`references/job-schema.md`](references/job-schema.md) — contrato job.json/camera.csv, fases do mod, gotchas.
3. [`references/recipes.md`](references/recipes.md) — código pronto dos planos das refs (abertura aérea, revelação por folhagem, órbita atrás da árvore, plano-sequência de escala, whip de transição).

## GitHub (22/10/2026)
Esta skill também vive em github.com/problemsbloxcreate-lab/editor (`.claude/skills/minecraft-cinematic`, repo PÚBLICO, sem as skins). **Toda modificação termina com** `python ~/.claude/skills/minecraft-video-editor/scripts/sync_github.py -m "o que mudou"`.

## Ambiente (já montado)
- Mod: `D:\cinecam-forge-1.20.1` (Forge 1.20.1, fonte também em `assets/cinecam-mod/`). **v0.8: o jogo é lançado DIRETO com java** (o comando do `runClient` é capturado do `gradle --info` na 1ª vez para `D:\cinecam-run\launch.json`); quando o fonte do mod muda, só roda `gradlew classes` antes. Sem a JVM do gradle viva durante o render (−1–2 GB). `CINECAM_GRADLE=1` volta ao caminho antigo.
- **Fonte em `assets/cinecam-mod/` = cópia IDÊNTICA do mod atual (v0.8, sincronizada 21/10/2026)**; `.jar` compilado em `assets/cinecam-mod/dist/cinecam-forge-1.20.1-0.1.0.jar` (só para pôr numa instância Forge 1.20.1 comum — o render NÃO usa o .jar, compila do fonte via `runClient`). Ao mudar o mod em `D:\cinecam-forge-1.20.1`, recopiar `src/` para cá e recompilar (`gradlew build --offline`, JAVA_HOME = JDK 17 de `~/.gradle/jdks`).
- **Máquina NOVA**: `python scripts/setup_cinecam.py [--home …] [--run …] [--out …]` (copia o fonte, garante JDK 17, `gradlew build downloadAssets prepareRunClient` ONLINE uma vez — o render roda `--offline` — e grava CINECAM_HOME/RUN/OUT/JAVA_HOME com setx).
- **Skins da turma** (Problems, Patão, Stick, Brucutu, Matteeoo…): a pasta que o Matheus mantém é `ModrinthApp/profiles/Template Forge 09.26/config/bbs/assets/models/skins` (principal: `0.Turma`); `cinecam.turma.skin("stick")` acha por apelido (chico/chique, patao, mel, zoom…) ou por nome de PNG; `cast_sheet(png)` = folha com a frente de cada skin e o nome (para reconhecer quem está no vídeo). Cópia idêntica em `assets/skins/` (fallback em outra máquina). Scripts de cenas reais em `references/jobs/` (barriga, peixe seco, poças).
- **Locações catalogadas** (seed 4242, igual em qualquer máquina): `references/sites_4242.json` — um trecho plano por bioma (deserto do vídeo da água, planície, florestas, neve, selva, savana, badlands, campos, ilha no oceano, vazio do End); refazer com `scripts/sites_build.py`.
- Python: `scripts/cinecam/` → `import sys; sys.path.insert(0, "<skill>/scripts"); from cinecam import *`.
- **Tudo pesado em D:** (C: está cheio): jobs `D:\cinecam-run`, saídas `D:\cinecam-out\<nome>\`.
- RAM é o gargalo (Minecraft ~3 GB). Há outros pipelines do Matheus rodando (Premiere, outros mods em teste): em 21/10 a máquina chegou a 0,5 GB livres e o encoder morreu sem memória → o encoder do master usa 4 threads, o lote usa `-Xmx3G` e repete 1× as cenas que falharem. Um render por vez (lock). Mundos temporários (`D:\cinecam-run\saves\cinecam-*`) são apagados no fim de cada execução (`CINECAM_KEEP_SAVES=1` mantém).
- **Muitas cenas = UMA sessão do jogo**: `render_batch([Shot(...), ...])` (filme e/ou stills misturados; mesmo mundo; cada cena com seu anchor/hora/comandos/atores). Economiza ~40–55 s de boot por cena.
- Nunca abra/edite mundos dele: `World(mode="copy", copyFrom=...)` copia antes.

## Fluxo (cada etapa tem uma checagem objetiva)
1. **Briefing curto** (só o que muda o resultado): ideia/tema, duração (padrão 6–10 s), formato (padrão 16:9 1920×1080 30 fps), onde (seed/mundo/estrutura; se vago, eu escolho), clima/hora, referência de estilo. Não pergunte mais que isso: assuma e marque `// ASSUMPTION` no resumo.
2. **Cenário**: se não há mundo pronto, `scout()` — `locate structure/biome` + mapa de terreno. `Terrain.save_map()` → **abra o PNG** e escolha coordenadas reais. Construções extras via `Scene.commands` (`place structure`, `fill`, `setblock`, `summon`).
3. **Shot list**: 2–4 movimentos encadeados; para cada um: intenção, movimento (tabela §3 da linguagem), duração, ease, fov, roll. Gancho no 1º quadro (já em movimento).
4. **Código da câmera** (`Rig` + movimentos de `moves.py`; emende com `rig.last_pose()`/`orbit_from`/`from_pose`). Adicione `with_handheld("subtle")`, `with_roll`, `with_fov`, `with_lag`.
5. **Preview numérico**: `plot_rig(rig, "path.png")` → **ler o PNG**. Zero avisos de continuidade/jerk, velocidades plausíveis, roll/fov com ease. Com mapa: `Terrain.clearance(rig)` ≥ 0,5 bloco.
6. **Stills de enquadramento**: `stills(poses, ...)` nos instantes-chave (início, meio, fim de cada movimento) → **ler as imagens**: sujeito nos terços? oclusor de primeiro plano? horizonte? sem atravessar bloco? Corrija a câmera, não o mundo, quando possível.
7. **Render**: `render(rig, nome, scene=..., size=(1920,1080), grade="cinematic")`. `subframes=8` (whips/shakes 12–16; teste rápido `subframes=1`, 960×540). `supersample=2` para anti-aliasing (se a janela permitir).
8. **Verificar o MP4** (nunca entregar sem olhar): `report.json` (`ok`, `warnings`, `maxWait`), contact sheet com ffmpeg (`select` + `tile`) de ~12 quadros, conferir 3 transições/pontos de pico (blur, roll, fov). Itere 1–2 vezes e **entregue com status honesto** (o que é aposta, o que foi verificado).

## API essencial
```python
import sys; sys.path.insert(0, r"C:\Users\mathe\.claude\skills\minecraft-cinematic\scripts")
from cinecam import *
rig = Rig(fps=30, subframes=8, shutter=0.5)
rig.add(crane((60,95,-60), (18,72,-18), subject, 2.4, arc=8, ease="launch", fov=(78,66)))      # chegada
rig.add(orbit_from(rig.last_pose(), subject, sweep_deg=70, T=3.0, radius_end=9, height_end=2.0,
                   look_offset=(0,1.4,0)).with_handheld("subtle").with_roll((0,-9)))               # revela
plot_rig(rig, r"D:\cinecam-out\x\path.png")
render(rig, "x", scene=Scene(time=1000, weather="clear", anchor=(0,80,0)), world=World(seed=4242))
```
Movimentos: `track hold push_in truck crane orbit orbit_from pan whip dolly_zoom through chase parallax_pass from_pose`.
Modificadores: `.with_handheld(preset|tuple) .with_roll() .with_fov() .with_lag() .with_bank() .with_shake() .with_time_ease() .offset()`.
Easings: `launch launch_soft smooth soft_in_out in_out out out_expo whip out_back in out in_quart linear` ou `(x1,y1,x2,y2)` bezier.
Pós: `grade` = `insert` (inserção em gameplay; padrão do editor) `clean punchy cinematic moody golden horror`; `letterbox=2.39`. Detalhes: `scripts/cinecam/post.py`.

## Armadilhas (já pagas)
- Câmera a >(renderDistance×16−16) do `anchor` mostra vazio → ajuste `anchor`/`renderDistance` (o mod avisa em `warnings`).
- `ease="launch"` só no início de plano após corte; no meio de um movimento contínuo gera jerk (o analisador acusa).
- Mundo `worldTicks=True` deixa mobs/nuvens/água se mexerem; `False` congela (use para stills/arquitetura).
- Whip sem `subframes>=8` vira troca de quadro seca. Nunca blur atravessando corte (o `Rig` já recorta as amostras no corte).
- Roll: sinal/direção deve ser conferido num still (veja `references/recipes.md` § Calibração).
- Quem ficou preso: `D:\cinecam-run\render.lock` órfão → apagar; processos `java`/`ffmpeg` do render → `taskkill /F /T`.

## Estado e limites (honestos)
**v0.2 (15/10/2026)** — verificado no jogo: câmera por curvas, motion blur linear (8 subframes), DoF por profundidade com rack focus, supersampling 4K→1080p, grade/bloom/vinheta/grain, stills de enquadramento, scout de terreno/`/locate`, preview numérico. Referência renderizada: `D:/cinecam-out/test4/test4.mp4` (revelação por folhagem) e `test2` (swoop+órbita). `python scripts/selftest.py` valida a lib offline.

**v0.3 (16/10/2026) — ATORES + ÁGUA (verificado em render 1080p/60fps):** `Actor`(skin PNG qualquer, keyframes de cabeça/braços/pernas/barriga/escala/lean/hop/roll, `.wobble`), `Anim`(atores + `WaterRegion` drenada só no cliente + feixes de água `beams`), `render(..., anim=Anim(...))` e `stills(..., anim=...)` (cada pose leva `t`). Referência completa: [`references/actors.md`](references/actors.md). Exemplo renderizado: `D:/cinecam-out/takes_futuros_oceano/` (Problems/Stick/Patão bebendo o oceano, 4,017 s @60).

**v0.4 (17/10/2026) — MUNDO DE BORRACHA:** `Prop` (qualquer bloco como objeto squash&stretch, tinta de bioma, procedural por `fn`), membros elásticos (`rarm_len`…), `shadow_y` (sombra de contato), `Actor(hat=True)`. Exemplo: `references/example_borracha_gear5.py` (Matteeoo ricocheteando em chão-trampolim com ondas, árvore-mola e abóbora; `D:/cinecam-out/borracha_c1/`). Detalhes em `references/actors.md` § v0.4.

**v0.5 (17/10/2026) — SILHUETA CONTRA O SOL:** canal `silhouette`, `Scene(sunScale, sunTexture)` (sol gigante na posição real), pós `cinecam/sunfx.py` (raios ocluídos, flash, feixes, halo, céu profundo). Exemplo: `references/example_sol_silhueta*.py` → `D:/cinecam-out/borracha_c2/`. § v0.5 em actors.md.

**v0.6 (17/10/2026) — MOBS + ITEM DE MOD:** `Mob` (qualquer mob vanilla animado/amassado), item de mod via modelo JSON (`model:cinecam:item/…`, ex. Luva Elástica), canal `item` = escala. Exemplo `references/example_luva_porco.py` → `D:/cinecam-out/borracha_c3/`. § v0.6 em actors.md.

**v0.7 (20/10/2026) — BARRIGA VOXEL CHEIA D'ÁGUA:** canais `vbelly*` no Actor (bola de cubos de 1 px pintada com a frente do torso, igual ao mod do vídeo "Bebi toda a água do mundo"; squash, ondulação, brilho de água). Takes renderizados: `D:/cinecam-out/barriga_a/` (Patão + canudo) e `barriga_b/` (Problems pulando). § v0.7 em actors.md.

**v0.8 (21/10/2026) — CENAS AUTOMÁTICAS PARA O EDITOR + REVISÃO DE DESEMPENHO/QUALIDADE:**
- `cinecam/sets.py` `SetBuilder` (recria o LUGAR: chão do bioma sobre base sólida, lagoa orgânica com cana atrás e alga dentro ou seca, árvores por feature, peças de vila por `place template`, mobs parados, terreno em volta suavizado em degraus, árvores cortadas removidas), `cinecam/acts.py` `Stage` (elenco por apelido + `walk/look/turn/hop/celebrate/shock/point/talk/wave/fall/drink` + respiração `Actor.idle` automática) e 8 câmeras prontas `CAMS` (`hero_low establish orbit_push reveal truck close plongee dolly_shock`), `cinecam/auto.py` (ficha JSON → cena; `render_cards(cards, "stills"|"draft"|"final")`), `cinecam/turma.py`. Quem usa: `minecraft-video-editor/scripts/cinematicas.py` (regra 20 do editor; ficha documentada em `minecraft-video-editor/references/cinematicas.md`). Testado na abertura do "Bebi toda a água" (`D:\Pobrs\cine_test40\cine\c01-c03.mp4`).
- Mod: fila `next` no job.json (lote numa sessão; relógio vanilla devolvido entre cenas, água drenada restaurada, texturas de skin por cena), `mode` por cena, profundidade lida só no subframe do meio, encoder com 4 threads. Lançamento direto sem gradle (ver Ambiente).
- DoF ~6× mais rápido com a mesma imagem (PSNR 61 dB): leitura do pipe por `readinto` (o `.read(n)` com buffer grande era o gargalo: 10× mais lento no Windows), operações só cv2 → **GPU via OpenCL** (`cv2.UMat`), gamma por tabela, níveis largos em meia resolução. 3 s @60 fps: ~2,5 min → ~25 s.
- Qualidade: **vinheta corrigida** (o `mode=backward` CLAREAVA os cantos em todos os grades — agora escurece); saída marcada **BT.709** (mesma cor da gameplay do OBS no Premiere); grade novo **`insert`** (padrão das cinemáticas do editor: cores vanilla + curva que segura o estouro de céu/areia/água, bloom suave, vinheta leve, sem grain); **anti-aliasing por jitter de subpixel** entre os subframes do motion blur (≥4 subframes = 4–12× AA de graça, sem supersample); **subframes adaptativos** pela velocidade da câmera (`auto_subframes`, 4–12).

**v0.9 (21/10/2026) — ENQUADRAMENTO, ATUAÇÃO E ITENS ENCAIXADOS (feedback do Matheus nas 14 cinemáticas do vídeo completo):**
- `cinecam/kin.py`: cinemática EXATA do modelo (mesmas transformações do Actors.java): boca, mão, pegada, ombro, frente do rosto/corpo, caixas de colisão (+ bola da barriga) e IK de braço (`arm_aim`, erro 0,000°). A antiga `mouth_position` tinha o sinal do yaw INVERTIDO (boca atrás da cabeça para yaw ≠ 0) — causa do canudo atravessando a cabeça; agora usa kin.
- `cinecam/framing.py`: valida SEM renderizar, quadro a quadro — ângulo câmera×frente de cada personagem visível (perfil 60–120° proibido; sujeito com rosto ≤ 50°; costas só para quem está em `allow_back`), personagem cortado na lateral, sujeito ≥ 15 % da altura no fim.
- `cinecam/acts.py` v2: blocking aberto (`audience`; `face=` vira cheat: corpo ≤ 35°, rosto ≤ 50° da lente, cabeça completa), câmeras pela FRENTE real do personagem (`az`, `side`), distância mínima para o grupo caber, mira pela regra do terço; gestos expressivos (talk, present, present_to, point por IK, wave, hands_together, facepalm/think por IK, shrug, celebrate assimétrico, excited, laugh, angry, shock com tremor, nod, headshake, lean_in) com antecipação/overshoot/squash; `drink` com canudo reto da frente da boca à água À FRENTE, passando pela mão (IK a 30 Hz) e checado contra o corpo; item vanilla na mão aparece (canal item=1).
- `cinecam/auto.py`: toda ficha passa por checagem de itens (recusa) e de enquadramento (tenta lado espelhado/azimutes menores; senão recusa com o motivo); no lote, ficha recusada não derruba as outras. Auditoria das 14 entregues: 7 reprovariam (4 de costas, 3 de perfil) + 5 canudos errados.
- Calibração de sinais (still 21/10): braço direito y+ = abre para fora, y− = cruza o peito; esquerdo espelhado; head_y + = olha para a direita do personagem.

**Ainda NÃO existe** (não prometa; implementar sob demanda, nesta ordem de valor):
1. ~~Atores articulados~~ → feito (v0.3); faltam cotovelos/joelhos, itens animados além do item na mão direita, mobs não-player.
2. **Shader pack** (Complementary/Oculus) integrado ao render — hoje vanilla + pós.
3. Overlays de pós (speed lines, flash de corte, lettering) e áudio/SFX — usar Remotion/Premiere depois.
4. Render vertical 9:16 testado (a matemática suporta; falta validar framebuffer e fov).
5. Sinal do roll e whip de transição conferidos em vídeo (ver `references/recipes.md`).

Custos medidos (RTX 5070 Laptop, 15 GB RAM compartilhada): 1080p/8 subframes ≈ 20 s por 5 s de filme; 4K supersampled ≈ 2 min por 5,4 s + DoF 40 s; boot do jogo + mundo ≈ 40–60 s.
