# Cinemáticas automáticas (regra 20, 21/10/2026)

> **v2 (21/10/2026, feedback do Matheus nas 14 do vídeo completo): "ângulos não tão bons — NUNCA de lado, sempre de frente ou 45°;
> costas evitar; animar MAIS (braços/corpo); NUNCA item mal encaixado (canudo atravessando a cabeça = abominável)".**
> LER ANTES de escrever fichas: `minecraft-cinematic/references/enquadramento.md` (pesquisa do agente sênior de enquadramento:
> zonas de ângulo, cheat de blocking, tamanhos de plano, posição na tela, movimentos, checklist, atuação por emoção).
> Toda ficha passa por `cinematicas.py check` (valida SEM renderizar) — ficha recusada não vai para render.

**Pedido do Matheus:** em TODO vídeo editado, gerar e inserir animações do CineCam (skill `minecraft-cinematic`) **recriando o lugar onde o vídeo está** e fazendo a cutscene "como se fosse ali dentro". Continuidade e imersão são o mais importante. **Densidade:** o 1º minuto é onde mais tem (3–5); depois, uma a cada 1–2 min (média ~90 s). Skins: `ModrinthApp/profiles/Template Forge 09.26/config/bbs/assets/models/skins`, principalmente `0.Turma`.

## A referência: as cenas do "Bebi toda a água do mundo"
| take | fala que ilustra | por que funcionou |
|---|---|---|
| `takes_futuros_oceano` (4 s) | "vamos beber toda a água do mundo" | a turma certa (Problems ciano, Stick, Patão) com as skins do jogo, água drenando, câmera em movimento |
| `universo_canudo` (3 s) | "toda a água do mundo com esse canudinho" | exagero literal da frase (Patão gigante no espaço com o canudo listrado) |
| `pa_rasante_plongee` (7 s) | "só o tanto de poça d'água" | o MESMO deserto (areia em degraus, poças) visto de outro ângulo |
| `barriga_a/b` (3 s) | barriga cheia | o look do mod do vídeo (barriga voxel), a lagoa e as canas do lugar, close com DoF |
| `peixe_seco_v2` (2 s) | poça seca | o mesmo lugar depois da ação; **plano aberto mostra a situação** (close só se pedirem) |

O comum entre elas: **mesmo bioma, chão, água, plantas, hora do dia e personagens** da gameplay em volta; ação = o que a frase diz; câmera de cinema (movimento, motion blur, DoF); 2–4 s; a voz continua por baixo.

## Fluxo (pasta do job; tempos de TIMELINE do plan3)
Depois que o plan3 está montado (keeps finais, promo e end card já posicionados):
1. `python scripts/cinematicas.py slots plan3.json work/t1.json work/t2.json` → `cine/slots.json`: frases com mais "imagem" (ação, lugar, coisa, exagero, número), na densidade da regra, fora de takes futuros, promo (±8 s), end card e B-rolls existentes. O arquivo traz também os 60 melhores candidatos: **troque o slot** se outra frase ilustrar melhor (ex.: a punchline, não a frase de transição).
2. `python scripts/cinematicas.py context cine/slots.json <bruto> plan3.json` → `cine/ctx_<id>.jpg` (4 quadros da gameplay: 1,5 s antes, início, meio, fim) + pistas objetivas (frações areia/grama/água/neve/pedra, hora pela cor do céu, bioma sugerido) + `cine/turma.png` (frente de cada skin da turma com o nome). **Abrir cada ctx e a turma** e anotar: bioma e chão, água (lagoa/rio/mar), plantas, estruturas (casa de vila, pirâmide), mobs, hora, QUEM está na cena (pela skin) e o que estão fazendo.
3. **Escrever `cine/cards.json`** (uma ficha por slot; formato abaixo). Regra de ouro: **recriar o lugar** (site do mesmo bioma + kit + o que aparece no ctx) e **mostrar a frase** com a turma certa.
3b. `python scripts/cinematicas.py check cine/cards.json` → reprova ficha com personagem de PERFIL (60–120°), sujeito com rosto a mais de 50° da lente, de costas sem motivo, cortado na lateral do quadro, sujeito < 15 % da altura no fim, ou item que atravessa o corpo / mão fora do item / água atrás de quem bebe. A câmera tenta sozinha o lado espelhado e azimutes menores antes de recusar.
4. `python scripts/cinematicas.py render cine/cards.json stills` → `cine/st_<id>.jpg` (início/meio/fim, ~1,5 min para todas). **Olhar todas**: personagem certo, de frente/perfil (nunca de costas sem motivo), nada tapando (cana/árvore na frente), canudo/objeto visível, chão sem buraco, sem bloco flutuando. Corrigir a ficha e repetir só as que mudaram (`--only c02,c05`).
5. `python scripts/cinematicas.py render cine/cards.json final` → `cine/<id>.mp4` + folha de 6 quadros `cine/<id>_final.jpg` (1080p60, subframes adaptativos 4–12 com anti-aliasing, DoF na GPU, grade `insert`). Conferir as folhas.
6. `python scripts/cinematicas.py insert plan3.json cine/cards.json` → `brolls` (V3, flash branco só nas do 1º minuto), `mutes` de A2/A3 sob cada uma (A1 nunca), whoosh `19--Whoosh 39.wav` 0,25 s antes, SFX da ficha, marcador `CINE cNN: por quê`. Idempotente (refaz as CINE sem duplicar; backup `plan3.json.antes_cine.bak`). Depois o build normal (Premiere ou FilmCraft).

Tempos medidos (21/10, RTX 5070 laptop com o Premiere e outro Java abertos): 3 fichas = stills ~1,5 min, final ~2,5–3,5 min (uma sessão do jogo para todas). Vídeo de 20 min ≈ 13–17 cinemáticas ≈ 12–20 min de render final.

## A ficha (cards.json)
```json
{"id": "c03", "tl": 21.18, "dur": 2.11, "intro": true, "site": "desert", "time": 5000, "close": true,
 "why": "'de canudinho, vai': Problems bebe da lagoa, a barriga d'água cresce",
 "set":   [["pond", {"dx": 0, "dz": -4, "rx": 6, "rz": 2.6, "name": "lagoa"}], ["mob", {"mtype": "camel", "dx": -12, "dz": -14}]],
 "cast":  [{"who": "problems", "dx": 0, "dz": -0.2, "face": "camera"}],
 "beats": [["drink", {"who": "problems", "src": "lagoa", "t0": 0.0, "t1": 2.11, "gulps": 4}]],
 "camera": {"kind": "close", "focus": [0, 0.95, 0.15]},
 "sfx": [["mc-random-drink", 0.15]]}
```
- `tl`/`dur` vêm do slot (pode ajustar ±0,5 s para casar com a frase); `intro` = flash na entrada.
- **Local**: `site` = bioma do catálogo `minecraft-cinematic/references/sites_4242.json` (desert = o deserto dos takes da água; plains, forest, birch_forest, flower_forest, meadow, sunflower_plains, snowy_plains, snowy_taiga, jungle, bamboo_jungle, savanna, badlands, ice_spikes, stony_shore, windswept_hills, ocean_island, end_void = "universo"; taiga/dark_forest/cherry/swamp/beach caem no mais parecido). `biome` troca o kit sem trocar o lugar; `time` 5000 dia / 12300 pôr do sol / 18000 noite (o `context` sugere); `weather`.
- **Cenário** (`set`, na ordem; métodos de `cinecam/sets.py`): `pond` (lagoa orgânica, cana só na beira de trás, alga dentro; `water:false` = seca), `tree` (feature vanilla), `template` (peça de estrutura, ex. `minecraft:village/desert/houses/desert_small_house_1`), `structure` (vila inteira, longe), `mob` (parado, NoAI), `block`/`box`/`raw` (qualquer comando), `mark` (ponto nomeado). O kit do bioma põe chão + espalhados + árvores DEPOIS do elenco (desvia deles). Em volta do set o terreno é suavizado em degraus (menos no deserto, cujas dunas já combinam).
- **Plateia** (`audience`, graus, padrão 0): o lado das câmeras. Todo personagem fica ABERTO para ela; `face:"<outro>"` vira "cheat": o corpo gira só 45 % do ângulo (máx. 35°) e a cabeça completa até o rosto ficar a ≤ 50° da lente. Alvo a mais de 110° do eixo da lente não é olhado: use `present_to`.
- **Sujeito** (`subject`): quem o take é sobre (padrão: o 1º do elenco) — valida com regras mais duras (rosto ≤ 50°, ≥ 15 % da altura no fim).
- **Elenco** (`cast`): `who` = chave/apelido da turma (`problems`, `stick`/chico/chique, `patao`, `brucutu`, `mel`, `zoom`, `kadu`, `eugene`, `zegalo`, `matteeoo`… ver `turma.png`) ou nome de qualquer PNG da pasta de skins; `dx,dz` no set (+z = lado da câmera); `face` camera|<ator>|<marca>; `scale` (gigante); `item` (item vanilla na mão).
- **Ações** (`beats`, `cinecam/acts.py` v2 — amplitudes da tabela §4.2 do enquadramento.md, com antecipação, overshoot, assimetria e squash): `talk` (quem fala! braço principal abre e bate ~1,8 Hz, troca de braço a cada 1,2 s, cabeça acentua; `emphatic:true` = discussão), `present` (braços abertos para a lente — a pose mais usada nas refs), `present_to` (apresentador: mostra algo ATRÁS/ao lado sem virar as costas), `point` (IK: o braço aponta de verdade; não apontar para a lente), `wave`, `hands_together`, `facepalm`, `think` (mão no queixo por IK), `shrug`, `celebrate` (V assimétrico + pulos), `excited` (soquinhos + pulinhos), `laugh`, `angry`, `shock` (tranco + tremor), `nod`, `headshake`, `lean_in`, `walk` (to, t0, t1, run), `look`, `turn`, `hop`, `fall`, `drink`. Todo personagem tem respiração/micro-movimento automático e ninguém deve ficar > 0,6 s sem gesto: encadeie 2–3 ações por take.
- **Itens SEMPRE encaixados**: item na mão = `cast[...]["item"]` (item vanilla, o jogo desenha preso à mão direita); qualquer outro (canudo, corda) é calculado pela cinemática exata do modelo (`cinecam/kin.py`) a cada quadro e checado contra cabeça/tronco/braços/barriga. `drink`: a água tem de estar À FRENTE de quem bebe (lagoa entre o personagem e a câmera, um pouco de lado); o canudo sai reto da frente da boca até a água e passa pela mão (braço por IK). Água atrás = ficha recusada.
- **Câmera** (`camera.kind`) — TODAS posicionadas pela frente real do(s) personagem(ns) (`az` 0 = de frente, 30–45 = 3/4, `side:-1` espelha), distância mínima calculada para o grupo caber inteiro: `hero_low` (grupo/abertura/tese: baixa, push-in, olhos no terço), `establish` (lugar novo: grua do alto até a turma, pela frente), `orbit_push` (arco de 3/4 para a frente), `reveal` (sobe e afasta DE FRENTE revelando o `target` que está ATRÁS do elenco), `truck` (arco à frente; `follow` = câmera À FRENTE de quem anda, a 35° da direção), `close` (`who` = rosto+peito com headroom certo; `focus` = objeto/barriga), `plongee` (situação inteira, de frente e do alto), `dolly_shock` (susto: vertigo de frente), `ots` (por cima do ombro em diálogo: o do ombro pode estar de costas). Parâmetros extras na própria chave (`az`, `d0`, `d1`, `fov`, `ap`, `side`…).
- Ficha que precisa de algo fora disso: `"python": "cine/c07.py"` com `def build(st, sb, card): ... return rig` (usa o mesmo Stage/SetBuilder; exemplos em `minecraft-cinematic/references/` e `references/jobs/`).

## Regras de direção (v2: ver também as 10 regras de ouro do enquadramento.md)
0. **Nunca de perfil; sujeito de frente/3/4 (15–40°); costas só com motivo (OTS, saindo de cena).** Para mostrar o que eles olham, a câmera fica do lado do que é olhado, ou o objeto vai ATRÁS deles e o personagem apresenta (`present_to`) de frente.
1. **Continuidade primeiro**: mesmo bioma/chão/água/plantas/hora/personagens da gameplay em volta. Se a cena tem lagoa com cana, a cinemática tem lagoa com cana. Se a gameplay está na vila, `template`/`structure` da vila do mesmo tipo.
2. **A frase manda**: ilustrar o que é DITO (ação, exagero literal, situação). Exagero ("toda a água do mundo", "imagina se…") pode sair do lugar (End/universo, ilha, gigante) mas mantém a turma e os objetos do vídeo.
3. **Quem fala aparece** (ou reage): `talk` em quem fala; deboche/pergunta → `shock`/`dolly_shock` no personagem certo.
4. Personagem **de frente ou de perfil**, nunca de costas para a câmera sem motivo; nada tapando (cana/árvore/bloco entre câmera e ator).
5. Plano **aberto** para situação/lugar; **close** só para objeto/barriga/rosto (lição do peixe seco: "era pra ser plano mais aberto").
6. 1,6–3,4 s; sem duas cinemáticas coladas (≥ 2 s de gameplay entre elas); nada sobre takes futuros, promo, end card.
7. Fidelidade impossível (item/mob/HUD do mod sem modelo no CineCam) → escolher outra frase do `candidates` ou ilustrar a consequência; nunca uma cena genérica sem relação com o lugar.
8. Status honesto no RESUMO: quais cinemáticas, por quê, o que é aposta.

## Limites atuais (honestos)
- Personagens = modelo de player com qualquer skin (sem cotovelo/joelho); mobs vanilla (parados via `set` ou animados via `Stage.mob`); itens vanilla na mão; a barriga voxel do vídeo da água existe (`drink`); itens/blocos de mods de vídeo só com modelo copiado para o CineCam.
- O mundo é o seed 4242 (não o save do vídeo): o lugar é RECRIADO, não o mesmo bloco a bloco. Se o Matheus passar o save do vídeo, `World(mode="copy", copyFrom=...)` + coordenadas dá o lugar exato (ficha com `site: [x, y, z]`).
- RAM: o jogo pede ~3 GB; com Premiere + outros projetos abertos a máquina chega a 0,5 GB livres. O lote tem retry automático das que falharem; se falhar de novo, fechar algo pesado e rodar `--only` nas que faltaram.
