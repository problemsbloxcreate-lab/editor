# Análise de edição — Referência r4 (Problems, "Fim do The End / 54 bilhões de blocos")

- Fonte: https://youtu.be/LSVCoB_iLis — duração 19:20 (1160 s), 1280x720, AV1, áudio Opus 48 kHz estéreo (dual-mono, ver seção 4).
- Tipo: aventura/exploração POV em Minecraft (modpack "backrooms do End"), dois jogadores (Problems0 + AstroooZ_) conversando em voz, narrativa com plot twist final (o "Zero" some da memória do parceiro).
- Método: transcrição Whisper, 80 frames esparsos + 240 frames densos a 2 fps (0:00-0:40, 9:00-9:40, 16:40-17:20) em contact sheets, 344 cortes de cena (limiar 0.3), EBU R128 / volumedetect / silencedetect / análise espectral do áudio.
- CONFIANÇA: o áudio é um mix único já "master" (mono duplicado em L/R, -11.3 LUFS). Não é possível separar faixas; afirmações sobre música/SFX marcam o que foi medido e o que é inferido.

> TL;DR do padrão: edição MUITO enxuta — gameplay quase contínuo, narrado ao vivo, sem legendas, sem música detectável, sem SFX de meme. Os únicos "efeitos de edição" são: (1) cartão de abertura "MEU NOVO LIVRO", (2) badge "classificação indicativa L" (gag), (3) inserts de referência (print Reddit + clipe TikTok) com vinheta, (4) transições de time-skip: dip to black + silêncio de ~1 s (uma com flash rosa no retorno), (5) end screen "VEJA MAIS VÍDEOS NO CANAL". O trabalho do editor está em escolher/encurtar o gameplay, manter o áudio nivelado/alto e pontuar os saltos de tempo.

---

## 1. Estrutura (gancho, capítulos, fechamento)

Os "atos" são separados exatamente pelos 6 dips de preto+silêncio (seção 6). Timestamps medidos:

| Ato | Intervalo | Conteúdo | Fala-chave |
|---|---|---|---|
| Gancho | 0:00-0:24 | cartão do livro (0-2.5 s) + máquina voadora sobre ilha do End; promessa: "descobrir o que tem no final do The End", "30 dias ligado" | "O livro do Paulo chegou, link na descrição" |
| 1 | 0:24-3:09 | tese (anéis do End removidos; 2 bi / 10 bi / 54 bi de blocos), inserts Reddit + TikTok (0:23-0:36), dias passam (4 -> 28 dias), primeiras anomalias (Enderman roxo, backrooms gigantes) | "o fim está nos 54 bilhões" |
| 2 | 3:10-6:09 | (dip em 3:09) casa de cabeça pra baixo, aparece o NPC/jogador "Zero", conversa em chat, Creeper no End | "Quem é você e o que é isso?" |
| 3 | 6:09-9:24 | (dip 6:09) foguetes + elytra, Zero entrega recursos, viagem, Farland | "Eu deixei aqui todo esse pacote de recursos" |
| 4 | 9:24-12:08 | (dip 9:24) mobs corrompidos, casa pro Zero, Enderman branco, End Ships | "estamos corrompendo a memória do jogo" |
| 5 | 12:08-15:07 | (dip 12:08) navios infinitos pra cima, End City bugada, aranha, metrópole | "camada 1000, infinito pra cima" |
| 6 | 15:07-18:42 | (dip 15:07) chegada aos 54 bi, Ender Dragon gigante crescendo, luta | "Ele é colossal" |
| Twist | 18:42-19:09 | silêncio de 1.1 s em 18:42 -> Zero morre/sai do jogo; Zoom não lembra dele | "Quem é Zero?" |
| Jingle + end screen | 19:09-19:20 | "Problemzinho, esquininha azul, escondido no canal do Problems, pra você achar" + arte "VEJA MAIS VÍDEOS NO CANAL" (10 s estática) | — |

Observações: o gancho é rápido e sem rodeios — a 1ª frase já fala do livro e a 2ª (0:02) do objetivo. Não há capítulos com título na tela; capítulos são marcados APENAS por "dias passam" na fala + dip to black.

## 2. Ritmo e tipos de corte

Dados brutos: 344 timestamps do detector de cena; deduplicando rajadas <0.6 s (flashes/fades geram vários hits) restam 230 eventos, mediana entre cortes 2.4 s, média 5.0 s.

| Intervalo | cortes | cortes/min |
|---|---|---|
| 0:00-3:10 | 42 | 13.3 |
| 3:10-6:10 | 36 | 12.0 |
| 6:10-9:24 | 26 | 8.0 |
| 9:24-12:08 | 25 | 9.1 |
| 12:08-15:07 | 41 | 13.7 |
| 15:07-18:42 | 53 | 14.7 |
| 18:42-19:20 | 7 | 11.4 |

- Primeiros 5 min: 15 cortes/min; resto: 10.8/min. O vídeo NÃO acelera por decisão editorial; o que muda é o gameplay (câmera alternando entre POV de Problems0 e AstroooZ_, teleportes, GUI abrindo).
- IMPORTANTE: boa parte desses "cortes" é troca de câmera DENTRO do gameplay, não efeito de edição. Cortes de edição identificáveis: 0:02.5 (cartão -> ilha), 0:20.1 (flash), 0:23.9 (-> print Reddit), 0:27.5 (-> clipe TikTok), 0:29.4 (-> Reddit "rendered with math"), 0:35.9 (volta ao jogo), os 6 dips pretos e o end screen.
- Takes longos sem corte: 0:50-1:26 (36 s), 2:57-3:23 (26 s), 4:58-5:39 (41 s), 6:42-7:26 (44 s). Regra: takes de 25-45 s intactos quando há conversa/ação contínua.
- NÃO há jump cut de respiração: a conversa dos dois é gravada junta; não há silêncio <0.3 s cortado. O único silêncio digital do vídeo são os 6 dips. Falas sobrepostas, risadas e "hãã" ficam. Não é o padrão "talking head com jump cut".
- NÃO há zoom punch-in digital nos frames densos (0-40 s, 9:00-9:40, 16:40-17:20): o enquadramento é 100% do jogo. Nenhum shake de edição. O único movimento "extra" é o blur/zoom do flash vermelho (seção 5).
- B-roll: só os inserts Reddit/TikTok no ato 1. Nenhum depois.

## 3. Música

- Medido: sem faixa musical sustentada em nenhum trecho. O espectrograma não mostra bandas tonais contínuas (assinatura de bed musical); só voz (300-3k Hz), ambiente de jogo e transientes graves (SFX do jogo: explosões, redstone, dragão).
- Piso: o 5º percentil do RMS (janelas de 50 ms) fica só ~10 dB abaixo da mediana (-21 vs -11.6 dBFS) em todos os atos: sempre há voz ou som do jogo.
- Trocas de música: 0. Nenhum riser/hit/crossfade identificável.
- Única parte "musical": jingle falado/cantado 19:09-19:17 ("Problemzinho / Esquininha azul / ..."). O nível cai ~2 dB na janela final (mean -13.8 dB vs -11.8 dB antes; momentary 1140-1160 = -17.8 LUFS, fade de saída).
- Ducking: não aplicável.
- Decisão sugerida: para este formato (aventura POV com conversa) NÃO colocar música por padrão. Se o brief pedir, só em trechos de viagem longos SEM fala, com ducking >= 18 dB. (Hipótese: a ref não prova nada sobre música.)

## 4. Mixagem / voz

- Loudness integrado -11.3 LUFS (muito alto; YouTube normaliza -14), LRA 1.8 LU (extremamente comprimido), true peak +0.9 dBFS (limiter agressivo; 5704 amostras >0.98).
- Momentary médio por janela de 20 s: -11.3 a -13.5 LUFS em todo o vídeo (desvio ~0.5 dB): mix constante.
- Estéreo: L = R (side = -180 dB): dual-mono, voz centrada e duplicada.
- Voz e game audio vêm no mesmo mix; os 2 jogadores têm nível parecido (call). Sem diferença de timbre detectável.
- Skill: normalizar para ~-12/-11 LUFS integrado, limiter true-peak ~ -0.5 a 0 dBFS, compressor forte (LRA < 3 LU).

## 5. SFX, efeitos visuais, overlays, textos

### 5.1 SFX
- Medido: nenhum pico isolado de SFX acima do mix. O detector de transientes só achou os 6 retornos pós-silêncio (190.2, 369.9, 564.9, 728.8, 907.9, 1123.5 s). Não há whoosh, vine boom, bruh, notification ou memes sonoros destacados.
- Frequência de SFX de edição: ~0 em 19 min. Os SFX audíveis são do jogo (elytra, redstone, explosão, hit do dragão, totem, chat).
- Nos dips, a transição é a AUSÊNCIA de áudio (não é riser/whoosh); o áudio retorna com corte seco.
- Diferença para refs de humor: este vídeo (r4) é estilo aventura, SFX de meme não são o padrão aqui.

### 5.2 Overlays / gráficos (cada um)
1. Cartão de abertura "MEU NOVO LIVRO" — 0:00-0:02.5: fundo gradiente azul/rosa neon com skyline em silhueta; capa do livro ("PROBLEMS — A COR ESCONDIDA") à esquerda (~28% da largura, ~85% da altura); à direita texto em 3 linhas "MEU / NOVO / LIVRO" (branco / magenta / ciano, bold condensada com glow neon). Entrada: texto com fade-in nos primeiros ~0.3 s; selo "LANÇAMENTO" (azul, no topo do bloco) e "LINK NA DESCRIÇÃO" (branco, sombra, embaixo) aparecem por volta de 0.5-1.0 s. 2.5 s no total, corte seco para o gameplay.
2. Badge "classificação indicativa — L" — ~0:02.5 a ~0:06.5 (4 s): canto superior esquerdo, ~18% da largura, texto branco bold "classificação indicativa" em 2 linhas + quadrado verde com "L". Entrada/saída secas.
3. Insert Reddit — 0:23.9-0:27.4 e 0:29.4-0:35.8: print de r/Minecraft ("End rings have been removed in the latest snapshot" / "I rendered the End rings with math"), tela cheia, fundo branco/cinza desfocado com vinheta escura nas bordas; zoom lento (Ken Burns). Sem seta/círculo/destaque.
4. Insert TikTok — 0:27.5-0:29.4: clipe vertical 9:16 ("INVESTIGATING MINECRAFT'S END RINGS", "this way.", "PART 2") centralizado, ~30% da largura, barras pretas laterais, vinheta.
5. Flash vermelho — 0:20.0-0:20.4 (~0.4 s): tela vira vermelho saturado com blur radial/zoom sobre o barco, volta ao normal em ~0.3 s. Parece efeito de teleporte do jogo ou do bruto (não confirmado). Tratar como "color flash + zoom blur" de 0.3-0.5 s. Mesmo tipo de flash rosa/magenta no retorno do dip de 12:08.
6. Chat do Minecraft (nativo, não overlay) — canto inferior esquerdo ~4:50-7:05.
7. Mapa do mod (setas rosas em grade) — dados do jogo, ~10:00 e ~13:15.
8. End screen — ~19:10-19:20: arte estática "VEJA MAIS VÍDEOS NO CANAL" (5 personagens abraçados, fundo azul com raios, texto ciano com borda branca); 10 s; sem animação de entrada perceptível.
- NÃO há: legendas, lower thirds, contadores, setas/círculos, PNGs de meme, stickers, emojis, punch-in, shake, flash branco, LUT.
- Grading: nenhum; a cor vem do shader do jogo (End roxo/magenta). 16:9 puro, sem moldura.

## 6. Transições "dias passam" (peça-chave)

Seis transições idênticas, nos saltos de tempo (dia 4 -> 28 -> 50...):

| # | tempo | evento |
|---|---|---|
| 1 | 189.3-190.2 s (3:09) | fade-out -> ~0.9 s preto + silêncio -> fade-in (ilha -> casa invertida) |
| 2 | 369.1-369.8 s (6:09) | idem (casa -> viagem de foguete) |
| 3 | 564.0-564.8 s (9:24) | idem (cut extra ~568.1) |
| 4 | 727.9-728.7 s (12:08) | idem + flash rosa/magenta saturado no retorno |
| 5 | 906.9-907.8 s (15:07) | idem, fade-out e fade-in mais lentos (~0.5 s), cena de End City |
| 6 | 1122.7-1123.5 s (18:42) | silêncio de 1.14 s (silencedetect -40 dB) + preto; marca o twist |

- Padrão: fade-out ~0.2-0.5 s -> preto ~0.8 s COM silêncio absoluto -> fade-in ~0.2-0.5 s; áudio volta com corte seco.
- Componente "TIME-SKIP" da skill: 1 s de preto + zero áudio entre atos (equivale ao "capítulo" neste canal).

## 7. Cadência dos inserts (ato 1)

Prova externa aparece só em 0:23.9-0:35.9 (12 s) e é narrada pela voz dos jogadores (áudio do insert não é usado). Ordem: Reddit 3.5 s -> TikTok 1.9 s -> Reddit math 6.4 s -> volta ao gameplay por corte seco. Não reaparece. Regra: inserir prova externa uma vez, no começo, para validar a tese.

## 8. Pontos de atenção para editar brutos

1. A edição é de "poda", não de efeitos: o bruto vem de uma call com 2 POVs; o editor escolhe a câmera a cada 2-5 s na ação e deixa 25-45 s inteiros em conversa.
2. Manter o áudio simultâneo: não cortar respirações nem sobreposição de falas. Auto-editor com limiar alto destrói esse padrão.
3. Preto + silêncio total entre atos; sem música/whoosh nessas transições.
4. Loudness: exportar a -11/-12 LUFS, true-peak ~0 dBFS (medido +0.9).
5. Cartão de abertura 2.5 s com CTA do livro, mas a voz já fala desde 0:00 por cima do cartão.
6. Badge "classificação indicativa" é um gag de abertura; pode ser trocado por outro selo.
7. Inserts Reddit: screenshot com Ken Burns + vinheta, nunca captura de navegador ao vivo.
8. End screen: reservar os 10 s finais; o jingle corre por cima.
9. Twist: manter 1.1 s de silêncio em 18:42 antes de "Cadê o Zero?".
10. Sem legendas automáticas (incoerente com o padrão).

## 9. LISTA DE ASSETS

Visuais
| Asset | Nome provável | Onde achar / termo de busca |
|---|---|---|
| Capa do livro | "PROBLEMS — A Cor Escondida" | arquivo oficial do canal (pedir ao Matheus/cliente) |
| Fundo do cartão | gradiente neon azul/rosa + skyline | criar em Remotion; busca "neon city skyline silhouette png" |
| Badge classificação indicativa L | "Classificação Indicativa Livre" | busca "classificação indicativa livre png transparente" |
| Print Reddit | posts "End rings have been removed in the latest snapshot" / "I rendered the End rings with math" | reddit r/Minecraft; screenshot 1920x1080 |
| Clipe TikTok | "Investigating Minecraft's End Rings (Part 2)" | busca TikTok; insert vertical |
| End screen | "VEJA MAIS VÍDEOS NO CANAL" | arte do canal; fallback: recriar |
| Jingle de encerramento | "Problemzinho / esquininha azul" | áudio original do canal |

Sonoros (a ref não usa SFX de meme; abaixo só opcionais)
| SFX | Termo myinstants.com | Uso |
|---|---|---|
| Silêncio de 1 s | (sem asset) | time-skip |
| Riser curto | "cinematic riser short" | opcional |
| Whoosh | "whoosh transition" | não usado na ref |
| Hit grave | "bass drop boom" | não usado na ref |

## 10. Resumo executável do "padrão r4"

1. Cartão de livro 2.5 s com voz já falando; badge "L" 4 s no canto superior esquerdo no 1º corte.
2. Gameplay contínuo; troca de POV a cada 2-5 s na ação, 25-45 s em conversa.
3. Insert de prova externa uma vez no ato 1 (Reddit/TikTok com vinheta + Ken Burns).
4. A cada salto de tempo: fade-out 0.25 s, 0.8-1 s de preto SEM áudio, fade-in 0.3 s (opcional flash magenta).
5. Sem legenda, sem SFX de meme, sem música; mix a -11.5 LUFS, compressão pesada, true-peak ~0 dBTP, dual-mono.
6. 1.1 s de silêncio antes do twist final.
7. Encerrar com jingle falado + end screen 10 s.

## 11. Limitações

- Música/SFX embutidos em nível < -35 dB não seriam detectáveis no mix. Recomendo ouvir 0:00-0:25, 5:00-5:30 e 19:00-19:20 para confirmar.
- Zoom digital sutil (<5%) pode existir e não ser visível a 2 fps.
- Não há bumper/intro de canal após o cartão: o vídeo vai direto ao jogo.
