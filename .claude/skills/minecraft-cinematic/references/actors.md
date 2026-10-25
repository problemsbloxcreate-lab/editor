# Atores, água e feixes (CineCam v0.3)

Tudo é desenhado pelo mod no render level (AFTER_ENTITIES), 1 pose por passe de render => motion blur correto nos personagens.
Nada existe no mundo (sem entidade/IA/servidor). Fonte: `Actors.java`, `Anim.java`, `WaterDrain.java`; Python: `scripts/cinecam/actors.py`.

```python
a = Actor("problems", r"C:/.../Problems0.png", pos=(810, 65, -194), yaw=0)       # skin 64x64 (64x32 legado fica errado)
a.key(0.5, ease="out_back", head_x=-48, lean=12, rarm_z=-150)                      # canais seguram o valor entre keys; ease: smooth|out_back|out|in|in_out|linear|hold
a.wobble("belly", 1.5, 3.3, amp=0.1, freq=7.5)                                     # senoide aditiva
anim = Anim([a, ...], water=WaterRegion((x0, z0, x1, z1), y_min, y_max), water_level=lambda t: ..., beams=[f(t)->[x1,y1,z1,x2,y2,z2,r1,r2,alpha,lift,push_z] | None])
render(rig, nome, scene=..., anim=anim)            # 60 fps: Rig(fps=60). Tempo de animação por linha = row_times(rig)
```
Canais: x y z yaw | sx sy sz | head_x/y/z | rarm_x/y/z larm_x/y/z | rleg_* lleg_* | belly belly_y head lean item hop roll.
Sinais (calibrados; **z RECALIBRADO 17/10 com stills de frente**): head_x<0 olha p/ CIMA; rarm_x=-90 braço p/ frente; **rarm_z=+90 / larm_z=-90 = T-pose (braço PRA FORA)** — o sinal antigo (-90/+90) cruza os braços na frente do peito/rosto (bug visto pelo Matheus); rleg_z>0 abre a perna direita; lean>0 inclina p/ TRÁS; yaw 0 olha +z (sul). Modelo = 2,0 blocos de altura.
`mouth_position(actor, t)` dá a boca no mundo (para mirar feixes).

## Água
`water_level(t)` = altura da superfície (fracionária); só células de água dentro da caixa mudam, no CLIENTE (zero conflito com fluidos). Água por frame (constante entre subframes). Kelp/seagrass viram ar; waterlogged perde a água. Caixa grande (240x240x40) escaneia em segundos; drenar ~1 camada/frame custa ~0,5–1 s de remesh por frame.
Pegadinha: o fundo do mar perto da ilha estava a y≈49, mas o oceano tem trincheiras até y≈22; cure `water_level` em 2 fases (superfície→fundo visível lento, trincheiras rápido).

## Receita da ilha (ator no meio do oceano)
`fill x0 44 z0 x1 64 z1 sandstone` + topo `sand` no nível do mar+2: o oceano ao redor seca e a ilha vira pilar. Seed 4242, ilha em (810, -194): oceano frio profundidade ~14, penhasco ao norte.
Coreografia usada: intro (cada um faz pose enquanto a câmera passa) → bebem (cabeça p/ trás, barriga ∝ água sumida, feixes em arco descendo na boca com `push_z`) → câmera sobe revelando o fundo seco → arrota/pula/squash → plano baixo nas barrigas.
Cuidado: `ease="out_back"` na câmera faz overshoot de POSIÇÃO (desceu até o nível da areia) — use `out`.
Grade `toon` (post.py) = saturada, sem névoa; `punchy` lava céu/areia por causa do bloom.

## v0.3.1 — dimensão End, funil, canudo, ator gigante (exemplo `example_universo_canudo.py`)
- `Scene(dimension="minecraft:the_end")`: céu escuro de "universo" sem chão; construir tudo com `commands` (fills ≤32768 blocos; em fatias). Longe da ilha principal (z≈700) é void. Iluminação: o End não tem skylight -> grade de `minecraft:light[level=15]` sobre a fatia; estrelas = `end_rod` espalhados ao fundo; gamma=1.0. Ator gigante: `bright=1` (fullbright) e `sx=sy=sz=50`.
- `Anim(funnel=f(t))` + `WaterRegion(..., center=(x,z))`: superfície por célula = nível + funnel*distância ao centro -> buraco seco que se expande como ralo.
- `tube(p0,p2,r1,r2,alpha,lift,push_z,style,color,segments)` style 1 = canudo listrado vermelho/branco, 0 = água cintilante; `bent_straw(tip, mouth)` dá (lift, push_z) para um canudo que sobe reto e dobra na boca. Duas camadas (canudo translúcido + água por dentro) vendem o canudinho.
- `mouth_position` boca em up=0.12/forward=0.27 (a boca fica abaixo do nariz no skin).
- Armadilha: outra sessão do Matheus também usa o CineCam (lock `D:/cinecam-run/render.lock`) -> não apagar; reexecutar até liberar (`retry.sh` no scratchpad faz isso).

## v0.4 — mundo de BORRACHA (adereços de bloco, membros elásticos, chapéu, sombra) — exemplo `example_borracha_gear5.py`
- `Prop(name, "minecraft:grass_block", pos)` = modelo de bloco desenhado pelo mod (sem colisão, nada no mundo), pivô no **centro da base**.
  Canais `x y z sx sy sz yaw pitch roll` (`sx=0` esconde). `Prop(..., fn=lambda times: (n,9))` = procedural (árvore que enverga, grade de chão).
  Tinta de bioma real (grama/folhas casam com o mundo). Iluminação = luz do bloco/céu na posição. `Anim([...], props=[...])`.
  Para "chão de borracha": `fill ... air` na camada do topo + grade de props de grama no lugar; altura h(x,z,t) → `sy=1+h`, `sx=sz=1/sqrt(sy)`.
  **Zona morta** (|h|<0,025 → 0) senão a grade mostra costuras escuras em repouso. Afundamento com raio largo (~2,3) senão parece BURACO.
  Árvore-mola: tronco+copa como props, compressão + flexão (offset ∝ y², roll −φ = topo p/ +x, pitch +φ = topo p/ +z) — verificado em still.
- Actor: `rarm_len larm_len rleg_len lleg_len` (escala y a partir do ombro/quadril: braço de borracha Gear 5; perna <1 finge joelho no impacto).
  `shadow_y` = sombra redonda (textura vanilla) nesse y — use a altura REAL do chão sob ele (chão amassado), senão a sombra flutua.
  `Actor(hat=True)` = copa + aba 3D texturizadas com o topo da cabeça da skin (feito p/ Matteeoo; chapéu acompanha cabeça/escala).
- Flip em torno do centro do corpo: `lean` gira nos pés; compense `feet = centro − c·(cos a·up − sin a·fwd)`, fwd=(−sin yaw,0,cos yaw), lean<0 = frente.
- 1 take contínuo seguindo o personagem: `Move(DUR, fn)` próprio com `CubicSpline` por tempo + mira com lag 0,12 s + `focus` = distância ao longo do eixo até ele (DoF segue). Distância 4–5,5 blocos (7+ fica pequeno demais em 16:9).
- Custo: ~360 props × 1440 linhas ⇒ anim.json ~28 MB, gera em ~5 s. Mod: `src.bak-v031` em D:\cinecam-forge-1.20.1 é o backup pré-v0.4.
- Braços: NUNCA componha xRot+zRot crus com o braço acima do ombro — monte a direção (abertura β do corpo, giro θ) e converta (`arm_euler` no exemplo); mantenha β 18–140 e giro |θ|≲25° p/ a silhueta ler. Personagem com o peito virado p/ câmera (yaw = direção da câmera) senão braços no plano lateral somem no corpo. Toco do braço: o cubo começa 2 px acima do ombro — o mod (v0.4) desliza o pivô ao esticar (`stretchArm`), senão o toco atravessa o tronco.
- QA de braços antes do render: stills com a câmera do filme nos instantes de pose + 1 still de calibração de frente quando mexer em sinais.

## v0.5 — SILHUETA CONTRA O SOL (Cena 2 Gear 5) — `example_sol_silhueta.py` + `example_sol_silhueta_fx.py` + `scripts/cinecam/sunfx.py`
- `Actor` canal `silhouette` 0..1: escurece modelo+chapéu (contraluz). 0,35 correndo pro sol → 0,95 dentro do sol.
- `Scene(sunScale=2.7, sunTexture="…png")`: o mod redesenha o sol N× maior NA posição exata do sol vanilla (Ry(-90)·Rx(timeOfDay·360)), depois do céu (terreno/entidades/nuvens por cima). Textura vanilla aditiva estoura branco/rosa sobre céu claro → use `sunTexture` RGBA própria (miolo 16×16 pixel-art quente + halo dourado com alpha) desenhada com alpha reto. Direção do sol: `sun_dir(time)` no exemplo (verificado: centro bate em 0,03°). Sol vanilla visível ≈ 4–6°: sem sunScale o personagem teria de estar a ~70 blocos.
- Alinhamento: câmera = CENTRO do corpo (pés+1,05) − sol·D (alinhar os pés deixa ele 3° acima). D≈17 com fov 44→33 = silhueta ~1/3 do miolo.
- **Perfil, nunca de costas (feedback do Matheus):** na silhueta o corpo fica de LADO pra câmera (yaw ⊥ eixo câmera–sol), braços/pernas no plano sagital (β≈25, θ ±105..150), entrando no sol pela diagonal baixo-esquerda→centro mantendo a direção de tela do plano anterior. Plano colado também de lado.
- Nuvens desligadas (`Settings(clouds=False)`) — cruzam o sol e sujam a silhueta.
- Pós `sunfx.sun_fx`: céu aprofundado só nos pixels azuis (`sky`), raios radiais SÓ do miolo quente (halo inteiro inunda o quadro), flash branco ponderado por luminância (silhueta fica preta), starburst de feixes, halo. Valores bons: rays 0,3 (pico 0,8), halo ≤0,18, gamma 1,35, sky 0,9 no plano do sol. Render com `grade="clean"` e grade final depois dos FX.

## v0.6 — MOBS + ITEM DE MOD NA MÃO (Cena 3 Gear 5) — `example_luva_porco.py`
- `Mob(name, "minecraft:pig", centro, fn=…)`: mob vanilla desenhado pelo mod (instância só no cliente, sem IA). Canais: x y z (CENTRO do corpo) yaw pitch roll sx sy sz (squash em eixos do MUNDO, antes da rotação — bom p/ impacto) shadow_y swing (passo de perna por linha). `Anim(..., mobs=[...])`. yaw 0 = olha +z, igual ao Actor.
- Item de outro mod sem carregar o mod: copie o JSON do modelo p/ `src/main/resources/assets/cinecam/models/item/` (só funciona se as texturas forem vanilla ou estiverem no cinecam), adicione em `CineCam.EXTRA_MODELS` e use `Actor(item="model:cinecam:item/<nome>")`. Ex.: Luva Elástica do mod rubberflux (`bounce-forge-1.20.1-1.0.2.jar`, instâncias "Base Desempenho"/"Trolajes").
- Canal `item` do Actor agora é ESCALA do item (0 some, 1 normal): anime p/ "tirar do bolso" com pop. O item fica na ponta do braço esticado sem esticar junto.
- Braço mirando um alvo: `arm_aim(feet, yaw, alvo)` no exemplo devolve (xRot, zRot, len) — braço de borracha alcançando um mob; `hand_pos` dá a posição da mão p/ o mob grudar nela.
- Ricochete: `pig_state` (trechos balísticos entre contatos + 0,07 s grudado amassando pela normal), árvores-mola com o tronco amassando no ponto do impacto, parede de props que afunda e ondula.
- GOTCHA framebuffer: o SO pode encolher a janela (veio 2560×1600 16:10 → vídeo achatado). Agora o mod reforça o tamanho no início do filme e a cada passe; confira `report.warnings` sempre.

## v0.7 — BARRIGA VOXEL "cheia d'água" (look do mod do jogo) — job `D:/cinecam-run/barriga_agua/takes.py` (20/10/2026)
- O mod do vídeo "Bebi toda a água do mundo" desenha a barriga como **bola de cubos de 1 px** saindo do peito, pintada com o pixel da frente do torso (skin + camada jacket). O canal antigo `belly` (escala do torso) NÃO parece com isso → use os canais novos:
  `vbelly` raio em px (0 = off) | `vbelly_y` centro em px abaixo do pescoço (7) | `vbelly_out` px que sai além da frente do torso (≈ R−2) | `vbelly_wave` ondulação (px; 0,15–0,2 em repouso, ≤0,6 no impacto — acima disso solta cubos soltos na borda) | `vbelly_jig` squash/stretch (+ = mais alta; −0,2 na aterrissagem) | `vbelly_vox` tamanho do cubo (1) | `vbelly_shine` 0..1 faixas de brilho azul-água deslizando (vende "líquido").
- Sombreamento por face estilo bloco (topo 1,0 / frente 0,64 / lados 0,78 / baixo 0,45): skin de cor chapada (Problems ciano) só lê volume com a câmera **um pouco acima** (aros claros dos degraus sobre frente teal escura, igual ao jogo). Skin listrada (Patão) lê de qualquer ângulo.
- Close de barriga: distância 1,3–1,6 bloco, fov 44–52, DoF no centro da bola (aperture 0,45). Mais perto que ~1,0 a bola enche o quadro e vira ruído. Grade `clean` para casar com gameplay vanilla (`cinematic` estoura céu/areia).
- Gole = bola cresce um degrau com out_back + jig −0,1 + wobble 6,5 Hz decaindo. Pulinho = hop 0,2 e na aterrissagem jig −0,2 → out_back +0,07 + wobble 7 Hz. Tapinha com a mão NÃO lê (braço é um bloco comprido que tapa a barriga).
- ~~Canudo: ponta na água ATRÁS do personagem~~ **ERRADO (21/10/2026): gerou canudo atravessando a cabeça. Regra atual: água À FRENTE de quem bebe, canudo reto saindo da frente da boca e passando pela mão — `Stage.drink` (acts v2) faz e checa; ver enquadramento.md §3h.** alpha 0,6 deixa o feixe de água aparecer dentro.
- Mob canal `age` (v0.7, índice 11): tickCount do mob → anima rabo/barbatana/asa que leem ageInTicks (o mob não tica). Peixe desesperado: `age = 1 + 70·t` (~3,5× o vanilla). Exemplo `D:/cinecam-run/barriga_agua/peixe.py` (bacalhau se debatendo na poça seca, `D:/cinecam-out/peixe_seco/`).
- Bacalhau fora d'água: o renderer vanilla já deita de lado → `roll=0` = de lado, `roll=90` = EM PÉ (errado), flips de ±180 trocam de lado. Conferido em still de calibração.
- **GOTCHA água fantasma:** `setblock ... dead_*_coral` (planta/leque) nasce `waterlogged=true` = FONTE de água; na fase de settle ela inunda o buraco. Use `[waterlogged=false]`. Diagnóstico: `execute if block X Y Z minecraft:water run say ...` nos commands e ler game.log. Lembrete: `fill` > 32768 blocos falha calado ("-> 0") — divida.

## v1.0 (25/10/2026) — corpo que dobra + `Ator` (atuação por molas)
Canais novos do `Actor` (PN 52): `rarm_bend larm_bend` (cotovelo, graus, NEGATIVO = antebraço para a frente), `rleg_bend lleg_bend`
(joelho, POSITIVO = canela para trás), `torso_x torso_y torso_z` (tronco em volta do quadril; x + = inclina para a frente), `mouth`
(0/1 boca aberta), `blink` (0..1). `Actor(face="auto")` usa `cinecam.face.detect(skin)`; passe `face={...}` (retângulos em pixels
da cara 8×8: `mouth [x0,y0,x1,y1]`, `eyes [[...],[...]]`, `lid [r,g,b]`, `mouthColor`, `z`) para skins diferentes, `face=None` desliga.

Prefira `cinecam.atua.Ator` a chaves à mão:
```python
from cinecam.atua import Ator
k = Ator("kadu", skin("kadu"), (x, y, z), yaw=0)
k.talk(0.15, 2.2, text="Você sabia que o Minecraft tem um SEGREDO?")   # ou wav=r"...\fala.wav", wav_offset=0.0
k.point_at(0.9, (x - 3, y + 1.9, z + 1.2))      # plano frontal: aponte para o lado (lê na tela), não para a lente
k.pose(2.2, "ombros"); k.jump(3.0, h=0.8); k.pose(3.05, "comemora"); k.pose(4.5, "idle")
k.walk(4.6, 6.0, to=(x, z + 2.4)); k.pose(6.2, "joinha"); k.talk(6.25, 7.2, text="Bora descobrir!")
actor = k.build(7.6)        # Actor assado a 120 Hz → Anim([actor]); actor.at(t) dá a posição para a câmera seguir
```
Molas (`atua.SPRING`, f Hz / ζ / r): cabeça 3,2/0,6/+0,25, braço 2,7/0,5/−0,45 (antecipa e passa), antebraço 2,1/0,42/0 (chega por
último), tronco 2,3/0,75, pernas 3,6/0,8. `pose(..., snap=3)` = troca rápida (susto, golpe). Ciclos (`OSC`) não passam pela mola.
