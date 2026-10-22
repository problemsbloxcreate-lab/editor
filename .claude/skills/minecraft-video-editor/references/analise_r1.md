# Análise de edição — Referência R1 (Problems: "Agulha no Palheiro")

- Fonte: https://youtu.be/EqUbhDBjv0A — 21:10 (1269,6 s), 1280x720, 60 fps, AV1 + Opus estéreo.
- Formato: desafio competitivo com 3 jogadores (Problems vs Cadu/"Kadukos" vs Matheus), mapa de fazenda com pilha de palha, loja de upgrades (garfo, isqueiro, ímã, aspirador "VACUUM", dinamite, coelho, OVNI, bolsa) e "armadilhas" (trapaças) usadas entre os jogadores. Narração ao vivo (voz do Problems + amigos na mesma faixa; não há locução separada).
- Metodologia: 80 frames esparsos + 3 janelas densas a 2 fps (0:00-0:40, 10:00-10:40, 19:50-20:30) + janelas de 8-12 fps nos eventos + cortes de cena (limiar 0.3) + blackdetect + EBU R128/RMS/FFT no áudio. Não foi possível "ouvir" o áudio: SFX/música são inferidos por espectro/níveis; o que é suposição está marcado como (hipótese).

## 0. Conclusão curta (leia primeiro)
1. Edição **enxuta/limpa**: ~95% é gameplay contínuo gravado com **câmera cinematográfica do próprio jogo** (3ª pessoa/POV alternando, grande-angular com distorção). Quase todos os "cortes" detectados são trocas de ângulo de câmera do replay, não jump cuts de edição.
2. **Praticamente zero overlays de edição no corpo**: sem legendas, lettering, stickers, memes, setas ou contadores. Os textos na tela ($, capacidade da mochila, "Sold 115 straw for $1.15", placas "DYNAMITE RABBIT / UFO / EVOLUIR BOLSA") são do jogo/mod.
3. Elementos de edição identificados: (a) cartão de abertura "MEU NOVO LIVRO / LINK NA DESCRIÇÃO" (0:00-0:02,4); (b) selo "classificação indicativa L" (~2,5-7 s); (c) flash/tinta vermelha-laranja de ~0,7 s em ~13,3 s; (d) **6 telas pretas de ~1,0-1,4 s com silêncio digital** (separadores de ~3 min); (e) **speed lines + zoom radial** (~3 s em 20:07-20:10) na explosão final; (f) end card "VEJA MAIS VÍDEOS NO CANAL" (~1262-1269) com música.
4. Cortes: 283 detectados; mediana 2,78 s; média 4,46 s; ~13,4 cortes/min (faixa 6-21/min). O ritmo não acelera no clímax; segue a ação do jogo.
5. Voz: -21,5 LUFS integrado, LRA 2,2 LU, true peak -5,9 dBFS: **mix baixo e muito nivelado/comprimido** (não está em -14 LUFS).
6. Música: **sem faixa musical identificável no corpo**; só o end card tem música (-34,3 LUFS, ~13 LU abaixo da voz).
7. SFX de edição: raros. Transientes fortes só em 165,6 / 183,4 / 363,4 / 554,2 / 934,5 s (4 deles no retorno das telas pretas). Sons de meme (vine boom, bruh etc.) **não detectados**.
8. Gancho: 2 frases faladas sobre o cartão do livro (0:00-0:09), depois promessa do desafio; sem cold open de ação, sem título na tela.
9. Estrutura = loop de progressão (coletar, vender, comprar upgrade, trapaça, vingança) com escalada, e fecho moral ("quem mais trapaceou foi quem mais se ferrou"); Problems e Cadu acham a agulha (empate).
10. Para a skill: o padrão desta ref é **corte-por-câmera + fala contínua + pouquíssimo overlay**; o que o editor precisa montar: cartão de abertura, selo de classificação, separadores pretos, 1 efeito de clímax e end card.

## 1. Ritmo e tipos de corte

### 1.1 Números (cuts1.txt, limiar 0.3, 283 cortes)
- Mediana entre cortes **2,78 s**; média 4,46 s; mínimo ~0,02 s (artefato de flash duplicado); máximo 37,4 s (571,4 → 608,8 s, plano contínuo).
- Cortes por minuto (minuto 0 a 20): 14, 13, 21, 14, 15, 17, 9, 21, 16, 8, 14, 13, 9, 17, 10, 13, 19, 6, 8, 13, 13; último minuto parcial = end card, 0 cortes.
- Mais denso: min 2 e 7 (21/min: loja, compra de bolsa/coelhos, ida e volta), min 16 (19/min: batalha/gelo). Mais lento: min 17 (6/min), 18 e 9 (8/min): jogador farmando em ângulo fixo.
- O ritmo oscila entre 6 e 21/min acompanhando a ação (loja e explosões = mais ângulos; farm passivo = plano longo).
- Intervalos maiores que 8 s: 42 (ex.: 37,5 s [21,5 s], 90,3 s [17,6 s], 571 s [37,4 s], 849 s [32,8 s], 1038 s [26 s], 1097 s [27,2 s]).
- Intervalos menores que 0,7 s: ~40 (ex.: 15,7; 59,0; 74,2; 129,2; 134,1; 152,5; 168,1; 219,9; 249,4): pulos rápidos de câmera/duplicações do detector.

### 1.2 Tipos de corte observados
- **Troca de câmera do replay (dominante)**: mesmo cenário/HUD contínuo entre planos; ângulos: atrás do boneco ciano, POV com a mão (diamante ciano à direita), ângulo baixo na pilha, aéreo, close nos coelhos. Distorção grande-angular em todos os planos.
- **Continuidade de HUD**: ex. 10:00-10:25 saldo sobe $14,67, $15,07, $15,40, $15,51 em planos consecutivos com mochila 115 constante: prova de que NÃO há jump cuts temporais.
- **Corte na respiração**: não há. Fala contínua e sobreposta (3 pessoas); silêncio digital só nas telas pretas (silencedetect -40 dB/0,15 s só pegou os 5-6 pretos).
- **Zoom punch-in de edição**: não detectado; zooms são movimento de câmera do jogo (aproximação no boneco, close no Kadukos ~15:2x).
- **B-roll**: não há; tudo é o próprio gameplay.
- **Time-skip por preto**: ver 2.3.
- **Transição por efeito de cor**: ~13,3 s (ver 6.3). **Speed lines + zoom radial**: ver 6.4.

## 2. Estrutura do vídeo

### 2.1 Gancho / abertura (0:00-0:30)
- 0:00-0:02,4: **cartão promo do livro** "Problems — A COR ESCONDIDA": capa em 3D leve à esquerda + texto neon "MEU NOVO LIVRO" (branco/rosa/ciano, contorno branco) + faixa "LANÇAMENTO" no topo + "LINK NA DESCRIÇÃO" embaixo; fundo skyline azul/rosa com fumaça. Animação: texto sai de cinza metálico/fosco para neon em ~0,5 s; "LANÇAMENTO" e "LINK NA DESCRIÇÃO" entram em sequência (~1,0 e ~1,5 s); hold até corte seco. Fala sobreposta: "O livro do Problems chegou, link na descrição".
- 0:02,4: corte seco para gameplay (pilha em plano aberto, close, boneco em cima da pilha com garfo). Fala 0:02-0:09: "No vídeo de hoje eu vou encontrar uma agulha no palheiro, e eu, Cadu e Matheus vamos competir..." (promessa + regra).
- 0:09-0:30: explica a mecânica (coletar, vender, comprar melhorias) com planos de 2-6 s. Primeiro conflito com rivais em 0:31 ("Caraca, Problems / Você ainda tá na mão?").
- Sem título animado, sem cold open de clímax, sem pergunta-gancho em texto.

### 2.2 Corpo (0:30-20:30): ciclos de escalada (sem títulos na tela)
| Bloco | Tempo | Conteúdo |
|---|---|---|
| A | 0:30-3:02 | mecânica, garfo, 1ª dinamite (explode a pilha dos rivais), loja, 1º upgrade |
| B | 3:03-6:02 | bolsa +10, coelhos, isqueiro do Cadu, terra suja aparece |
| C | 6:03-9:13 | "marrom é a cor do Matheus", 6 upgrades de bolsa, espionagem do Cadu, alçapão de trapaças |
| D | 9:14-12:08 | trapaças (lama, gelo, nuvem preta, saco arco-íris), vingança 2x1 |
| E | 12:09-15:34 | aspirador do Cadu, OVNIs, saco colorido, Problems investiga Cadu |
| F | 15:35-18:00 | Cadu invisível, vácuo, congelamento, nuvens |
| G | 18:01-20:57 | clímax: 30 dinamites, speed lines, "achei a agulha", empate, moral |
Os blocos coincidem com as telas pretas (ver 2.3).

### 2.3 Telas pretas (separadores)
blackdetect: 181,98→183,37 s (1,38 s); 362,15→363,37 (1,22); 552,97→554,13 (1,17); 728,18→729,23 (1,05); 933,47→934,57 (1,10); 1079,87→1081,10 (1,23).
- **Áudio em silêncio digital** durante o preto (silencedetect -40 dB: 182,0 +1,35 s; 553,0 +1,13; 728,2 +1,02; 933,5 +1,04; 1079,9 +1,20; RMS cai a -54..-113 dB).
- Em 4 dos 6 retornos há **pico de transiente** logo depois (183,4; 363,4; 554,2; 934,5 s): possível hit/whoosh de edição (hipótese).
- Intervalo médio ~180 s (180, 191, 175, 206, 146 s): provável ponto de capítulo/mid-roll ou time-skip. Replicar: corte para preto 1,0-1,4 s com áudio zerado a cada ~3 min.
- Nenhum texto de capítulo sobre o preto.

### 2.4 Fechamento (20:30-21:10)
- 20:17-20:30 Problems acha a agulha; Cadu também (20:28 "A agulha tá na minha mão" / 20:38 "só que a minha agulha também"): empate. Moral 20:48-20:57: "o crime não compensa... não trapaceie. Então é isso. Tchau."
- ~1258-1262: gameplay residual; ~1262: **end card** "VEJA MAIS VÍDEOS NO CANAL" (ilustração dos 5 personagens do canal, fundo azul-roxo radial), ~7-8 s; título animado entra por volta de 1262-1263 e fica estático. Música no end card (-34 LUFS), sem voz.
- Sem CTA falado de inscrição; o CTA é só o end card.

## 3. Música
- **Trocas de música no corpo: nenhuma detectável.** Espectro dos trechos mais silenciosos de cada bloco de 2 min não correlaciona com a música do end card (correlação -0,12 a 0,52; o último bloco, 0,96, é o end card em si). O piso constante (~-34 dB RMS, p2 de -32 a -35 dB em todos os trechos) é compatível com ambiente do jogo/vazamento de mic; não é prova de música.
- Única música confirmada: **end card** (~1262-1269): -34,3 LUFS, true peak -23 dBFS. Estilo (hipótese): loop upbeat/jingle de canal. Entrada: de -120 dB a -34 dB em ~0,3 s (corte seco, sem riser).
- Música/voz ≈ -13 LU. Ducking: não aplicável (sem sobreposição com voz).
- Abertura (0-12 s): RMS igual ao resto (-22 dB); não dá para afirmar música sob o cartão do livro.
- **Atenção**: esta ref NÃO tem trilha contínua. Se a skill adicionar música, é decisão de projeto, não padrão R1. Padrão R1 = áudio do jogo + vozes + bumper no final.

## 4. Mixagem e nivelamento de voz
- Integrado: **-21,5 LUFS**; LRA **2,2 LU** (low -22,3 / high -20,1); True Peak **-5,9 dBFS**.
- Janelas de 20 s: 0 s -21,6 LUFS (pico -9,6 dBFS); 100 s -21,1 (-7,6); 400 s -20,2 (-6,3); 800 s -21,6 (-10,6); 1000 s -21,4 (-9,8); 1262 s (end card) -34,3 (-23,0).
- RMS por segundo: percentis 5/25/50/75/95 = -23,0 / -22,1 / -21,6 / -21,1 / -19,5 dB: dinâmica quase nula (compressão/limitação forte e constante). Médias de blocos de 60 s entre -20,9 e -23,1 dB.
- Bandas (10 s a cada 60 s): graves <150 Hz 58-66 dB, médios 150-3000 Hz ~77-79 dB (voz), >6 kHz 48-60 dB; sem variação de timbre: mesma cadeia o vídeo todo.
- Sem clipping; headroom ~6 dB. Para a skill: voz em ≈ -21..-20 LUFS integrado, LRA < 3 LU, TP ≈ -6 dBFS replica a ref (ou -14 LUFS se o cliente preferir loudness de YouTube).
- Vozes dos 3 jogadores em nível equivalente (sem dips quando outro fala).

## 5. SFX
- **SFX de edição (memes/hits/risers)**: não detectados. Transientes >13 dB sobre a mediana local e > -14 dBFS: 165,6; 183,4; 363,4; 554,2; 934,5 s (5 eventos em 21 min).
  - 183,4 / 363,4 / 554,2 / 934,5 = logo após telas pretas: impacto/whoosh curto de retorno (hipótese; confirmar de ouvido).
  - 165,6 s (~2:45, "Prontinho. Agora eu já tenho 25"): ding de compra/jogo (hipótese).
- SFX do jogo (visíveis nos frames): coleta de palha ("+1" flutuante), venda ("Sold 115 straw for $1.15", chuva de notas de dólar + partículas verdes), explosões de dinamite, "evoluir bolsa", balde de gelo/nuvem/lama. São do jogo, não de edição.
- Sem "bruh", "vine boom", "oof", Minecraft hurt, notificações, risers ou stingers de meme.
- Para a skill: SFX opcional/mínimo; manter áudio original do gameplay; "hit" nos retornos de preto.

## 6. Efeitos visuais, overlays e texto

### 6.1 Cartão de abertura "MEU NOVO LIVRO"
- Quadro cheio 16:9, 0:00-0:02,4. Esquerda (~0-40% da largura): capa "PROBLEMS - A COR ESCONDIDA" com perspectiva leve, personagens azul e rosa. Direita: "MEU" (branco), "NOVO" (magenta), "LIVRO" (ciano), tipografia grossa com contorno branco e glow; "LANÇAMENTO" pequeno no topo com linhas laterais; "LINK NA DESCRIÇÃO" no pé. Fundo: skyline de cidade, gradiente azul-rosa, fumaça.
- Animação: acende de cinza para neon em ~0,5 s; subtítulos entram em ~1,0 e ~1,5 s; sai por corte seco.
- É **asset pronto do canal**: na skill, template/placeholder fornecido pelo cliente.

### 6.2 Selo "classificação indicativa L"
- Canto superior esquerdo, ~2,5 s a ~7,0 s (~4,5 s). Texto branco "classificação indicativa" em 2 linhas (sans grossa com sombra) + quadrado verde com "L" branco. ~15% da largura, margem ~3-4% da borda. Entra no primeiro plano de gameplay; some sem animação marcada.

### 6.3 Flash/tinta vermelha-laranja (~13,3 s)
- Gradiente vermelho/laranja saturado sobre o plano (pilha, boneco correndo), ~0,7-0,8 s, **decaindo** de volta às cores naturais; a 12 fps: 5 frames normais, ~4 laranja intenso, ~4 de retorno, depois plano novo (POV com HUD).
- Pode ser efeito do jogo ou transição colorida de edição (incerto); coincide com troca de plano.

### 6.4 Speed lines + zoom radial (~1206,5-1210,5 s = 20:07-20:10)
- Fala: "Eu tenho 30 dinamites... usa um monte... explode tudo, vai agora, galera!".
- A 8 fps: do plano com enxame de coelhos entra **overlay de linhas de velocidade radiais (anime) douradas/laranja com pontas verdes** + zoom blur radial/punch-in (~150-250%) com o boneco ciano no centro; depois as explosões (partículas cinza/brancas/pretas do jogo) preenchem a tela e as linhas ficam brancas. ~3-4 s.
- É o **único efeito dinâmico forte** do vídeo; reservar para o clímax.

### 6.5 Telas pretas e fim
- Ver 2.3 e 2.4. Entrada/saída do preto por corte seco (sem fade longo perceptível).

### 6.6 HUD/Textos do jogo (não são edição)
- Canto inferior esquerdo: saldo verde ("$0.01", "$15.22", "$47.12") e ícone da mochila com contagem (115, 665, depois ícone dourado 1045).
- Corações vermelhos + hotbar centro inferior.
- Mensagens: "Sold 115 straw for $1.15", "Pouch capacity set to 415 straw", "You lost $0.70 - balance: $0.33", "Collected 100 straw from the blast".
- Placas: "DYNAMITE RABBIT UFO" ($0.7/$10/$20), "FORK $2 / LIGHTER $15 / MAGNET $50 / VACUUM $100", "EVOLUIR BOLSA $1".
- Partículas: notas de dólar caindo (~25,5 s), "+1" amarelo nas coletas, losangos verdes/amarelos ao comprar.
- Nametags: "Kadukos", "Pitchfork" sobre a ferramenta.

### 6.7 Cor / look
- Sem color grade perceptível; look vanilla vivo, contraste natural, leve distorção de lente da câmera do jogo. Sem vinheta, grão ou shake de edição.

## 7. Pontos de atenção para editar brutos no padrão R1
1. **Decupagem por câmera**: o bruto já deve ter ângulos trocados no jogo (replay/câmera cinemática); a edição escolhe e mantém continuidade. Evitar jump cuts temporais; HUD ($/mochila) contínuo entre planos.
2. **Sem pausas**: fala quase sem respiros; não cortar "ums" (voz sobreposta de 3 jogadores).
3. **Abertura**: cartão promo ~2,4 s, corte seco, gameplay; selo "L" nos primeiros ~4,5 s.
4. **Telas pretas** de ~1-1,4 s com **áudio zerado** a cada ~3 min (6 em 21 min); considerar hit no retorno.
5. **Um efeito dinâmico**: speed lines + zoom radial no clímax (~3 s). Flash vermelho-laranja ~0,7 s em ~13 s.
6. **Áudio**: voz ≈ -21 LUFS, LRA ~2 LU, TP ≈ -6 dBFS; sem música contínua; end card com música ~-34 LUFS.
7. **Fechamento**: moral falada, "Então é isso. Tchau.", ~4-5 s de gameplay e end card ~7-8 s.
8. Duração total 21:10; corpo útil ~20:57.
9. Manter áudio ao vivo (reações, risadas), não regravar locução.
10. Incertezas: não verificado de ouvido (música sob a fala, SFX de retorno do preto, estilo da música do end card).

## 8. Lista de ASSETS a obter/criar
| # | Asset | Tipo | Termo de busca / origem | Uso |
|---|---|---|---|---|
| 1 | Cartão promo do livro ("MEU NOVO LIVRO", "LINK NA DESCRIÇÃO") | vídeo/PNG do cliente | pedir ao cliente; fallback: montar em Remotion (capa, fundo cidade neon azul/rosa, tipografia neon) | 0:00-0:02,4 |
| 2 | Selo "classificação indicativa L" | PNG alpha | "classificação indicativa livre png transparente"; ou recriar: quadrado verde + "L" branco + texto | ~2,5-7 s |
| 3 | Speed lines radiais (dourado/laranja+branco) | overlay vídeo/PNG seq | "anime speed lines overlay green screen", "radial speed lines transparent" | clímax |
| 4 | Zoom blur radial/punch-in | efeito | nativo (Premiere Radial Blur / Remotion scale+blur) | clímax |
| 5 | Flash vermelho-laranja decaindo | ajuste de cor | camada sólida vermelha/laranja em blend, 0,7 s, ease-out | ~13,3 s |
| 6 | Tela preta 1-1,4 s com silêncio | edição | gerar | 6x, ~3/3 min |
| 7 | Hit/whoosh de retorno (hipótese) | SFX | myinstants.com: "bass drop short", "cinematic hit", "whoosh impact" | após cada preto |
| 8 | End card "VEJA MAIS VÍDEOS NO CANAL" (5 personagens) | imagem/vídeo | arte oficial do cliente; animar entrada do texto | ~1262-1269 |
| 9 | Música do end card (loop upbeat) | áudio | do cliente; fallback: YouTube Audio Library "upbeat game" ~10 s em -34 LUFS | end card |
| 10 | Cadeia de voz | preset | normalizar -21 LUFS, limiter -6 dBTP, compressão leve | todo vídeo |

SFX de meme NÃO são necessários para R1 (nenhum detectado). Se o cliente pedir (fora do padrão), myinstants.com: "vine boom", "bruh", "oof", "sad violin", "windows error".

## 9. Reproduzibilidade
- Frames: `ffmpeg -ss S -t 40 -i video.mp4 -vf fps=2,scale=512:-1`; sheets por `tile`.
- Pretos: `blackdetect=d=0.03:pix_th=0.12`; silêncio: `silencedetect=n=-40dB:d=0.15`; loudness: `ebur128=peak=true`.
- Apoio: `...\scratchpad\refs\r1\{dense_a,dense_b,dense_c,sheets,t1..t7}`.
