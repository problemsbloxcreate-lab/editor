# Análise da referência R2 — Problems (Minecraft, POV + roleplay falado)

Fonte: https://youtu.be/HtRwJkTY9_0 · 21:05 (1264,7 s) · 1280x720 · 60 fps · AV1 · áudio Opus estéreo 48 kHz.
Tema do vídeo: roleplay "dois ovos de águia" (Pobre e Patão) que precisam evoluir para salvar a mãe capturada por "Chico" (vilão que monta um zoológico). Mod/skin: personagens viram aves (macaw azul, "águia" ciano), câmera 3ª pessoa de fisheye largo, HUD com hotbar.

Legenda de honestidade: eu não ouço o áudio, só meço (LUFS, RMS, espectro, estéreo). O que é inferência está marcado como **(hipótese)**. Tempos em mm:ss ou segundos, medidos por ffmpeg (scene score 0,3, blackdetect, ebur128) e conferidos visualmente em frames densos (2 fps) e folhas de contato (1 fps, todos os 1265 s).

## 0. Conclusão em 10 linhas (leia isto se tiver pressa)

1. Este é o vídeo "menos editado" dos 5: é uma **gravação contínua de gameplay com dublagem ao vivo de dois personagens**, quase sem cortes de edição. Os 148 "cortes" detectados são, em sua imensa maioria, **movimento de câmera do próprio jogo** (câmera de 3ª pessoa girando, zoom do avatar, voo rápido, mudança de câmera próxima/distante), não cortes do editor.
2. Cortes de edição reais identificáveis: **~18 eventos** em 21 min (7 dips pretos, cartão de livro, selo, teaser, flash branco, "?"s, torcida, end card).
3. A **fala é contínua**: 4.925 palavras, ~234 palavras/min, só ~25% dos quadros de 50 ms abaixo de -27 dBFS e apenas 24 pausas >=0,25 s em 21 min. Não há "respiros" editados.
4. **Música: não detectada** durante o corpo do vídeo. Só o end card tem um colchão tonal (-35 dBFS, notas G em oitavas, estéreo mais aberto) (hipótese: pad/música de outro).
5. **Voz nivelada e achatada**: -21,5 LUFS integrado, LRA 2,6 LU, true peak -8,8 dBTP, RMS por segundo praticamente constante em -22 dBFS (±1 dB) em todos os 21 min. Muito baixo comparado a -14 LUFS do padrão YouTube.
6. **Marcador estrutural mais forte**: 7 "dips" para preto de ~1,1 s com **silêncio digital** (-180 dB) a cada ~3 min (183, 371, 547, 735, 930, 1117 s; mais um suave em 135,6 s). Servem como elipse/passagem de tempo ou de local.
7. Overlays gráficos são **raros e curtos**: cartão "MEU NOVO LIVRO" (0-2,5 s), selo "classificação indicativa L" (2,7-6,5 s), "?" sticker (4 ocorrências), torcida de silhuetas + confete (754-756 s), end card "VEJA MAIS VÍDEOS NO CANAL" (1253,9-1264,7 s).
8. Há um **teaser de 4,5 s** (209,5-214,1 s) logo na frase "no vídeo de hoje a gente vai fazer missões e evoluir...", em grade lavada/dessaturada. Esse é o único trecho com cortes rápidos reais (5 cortes em 4,6 s).
9. Zoom/shake/flash **em pós: praticamente nenhum** (HUD mantém o mesmo tamanho em todos os quadros densos, ou seja, sem punch-in). Flashes coloridos de tela são, em sua maioria, do jogo (vinheta vermelha de dano), com 2 flashes verdes e 1 flash branco ambíguos.
10. Para o nosso editor: o "padrão" deste vídeo é **não atrapalhar** o bruto: manter takes longos, voz limpa e nivelada, e usar overlays só em picos emocionais (~1 a cada 2-4 min).

---

## 1. Ritmo e tipos de corte

### 1.1 Números (cuts2.txt, limiar 0,3)

| Métrica | Valor |
|---|---|
| Total de cortes detectados | 148 em 1264,7 s (7,0/min) |
| Duração mediana do plano | 3,65 s |
| Média | 8,49 s |
| Maior plano contínuo | 80,0 s (444,4 -> 524,4 s) |
| Percentis 10/25/75/90 | 0,43 / 1,55 / 9,88 / 22,5 s |
| Planos <1 s | 27 |
| 1-3 s | 39 |
| 3-8 s | 39 |
| >8 s | 44 |
| Primeiros 3 min | 4+2+3 = 9 cortes = 3/min |

Cortes por minuto (min 0..21): `4, 2, 3, 14, 3, 11, 13, 4, 1, 9, 18, 10, 10, 12, 2, 5, 4, 9, 3, 1, 10, 0`.
Planos longos (>20 s): 2,5-52,9 · 59,8-83,0 · 97,3-135,6 · 150,6-178,9 · 214,1-277,5 · 281,5-302,1 · 302,1-328,2 · 444,4-524,4 · 524,4-550,1 · 831,8-863,4 · 863,4-891,2 · 891,2-915,9 · 921,1-984,4 · 1059,4-1084,6 · 1084,6-1106,9 · 1106,9-1138,4 · 1145,7-1201,4.

### 1.2 Por que é o mais lento dos 5 (investigado)

- O material é **uma câmera livre de 3ª pessoa seguindo o avatar** (modelo de ave) com lente fisheye. Não existe "plano/contraplano": a ação é a mesma cena durante dezenas de segundos. Os cortes que o detector acha são quando a câmera do jogo muda de distância/ângulo (close da ave -> câmera aberta), voo em alta velocidade (cena inteira muda de céu para chão) e fade de clima.
- A narrativa é **diálogo dublado ao vivo sobre o gameplay** (duas vozes caracterizadas, "Pobre" e "Patão", mais NPCs: mãe águia, raposa, Cadu, Chico). O ritmo vem da fala (~234 palavras/min), não de cortes. Não há jump cut na fala.
- Os agrupamentos de cortes (ex.: 189,2/189,4/189,5/189,8; 199,6/199,8; 652-671; 781-796; 1027-1052) são **cenas do jogo** com zoom/rotação rápidos (conferido em tiras de 0,15 s). Dos 27 cortes "duros" (score >0,5) que inspecionei em pares antes/depois, 23 são câmera do jogo ou clima, 1 é transição cartão->jogo, 1 é o flash do relâmpago (82,97 s), 1 é fim do teaser, 1 é início do end card.
- Estimativa de cortes de edição reais: ~18 em 21 min (ver 1.3). Os outros ~130 são do jogo **(hipótese, amostragem visual de ~50 deles)**.

### 1.3 Lista de cortes/transições que SÃO de edição (confirmados em frame)

| t (s) | Tipo | Detalhe |
|---|---|---|
| 0,0 -> 2,48 | Cartão promo | "MEU NOVO LIVRO" (ver 6.1), corte duro para jogo |
| 2,48 -> ~2,7 | Revelação com blur | 1º quadro do gameplay em **gaussian blur forte**, desfoca em ~0,25 s |
| 135,60-136,52 | Dip preto 0,92 s | áudio NÃO zera (-32 dB residual). Elipse suave (jaguar leva os ovos) |
| 182,73-183,93 | Dip preto 1,20 s | áudio -180 dB (silêncio digital) ~0,9 s |
| 209,5-214,1 | Teaser | 5 cortes em 4,6 s, ver 6.4 |
| 328,2-328,5 | Flash branco | fade-from-white ~0,3 s com mudança de local (floresta -> campo) (hipótese: flash do jogo/mod de evolução; não dá para provar que é pós) |
| 370,45-371,67 | Dip preto 1,22 s | áudio -40 a -46 dB (não é zero digital) |
| 547,17-548,22 | Dip preto 1,05 s | áudio -180 dB |
| 734,45-735,52 | Dip preto 1,07 s | áudio -180 dB |
| 753,7 | Corte duro + torcida | ver 6.6 |
| 929,67-930,85 | Dip preto 1,18 s | áudio -180 dB |
| 1116,22-1117,28 | Dip preto 1,07 s | áudio -180 dB |
| 1253,9 | Corte para end card | ver 6.7 |

### 1.4 Os dips pretos (padrão forte, replicável)

- Intervalos entre eles: 47 · 188 · 177 · 187 · 195 · 187 s. Os 6 últimos formam uma grade quase regular de **~3 min** (3:03, 6:10, 9:07, 12:15, 15:30, 18:37).
- Posição narrativa: sempre numa **elipse ou virada**:
  - 3:03 (183 s): "Corre, pato, corre" -> escapam da jaguatirica -> campo aberto.
  - 6:10 (370 s): Patão cai/morre ("agora é só eu") -> volta como "fantasma".
  - 9:07 (547 s): chegada ao acampamento dos caçadores.
  - 12:15 (735 s): Cadu leva os dois para a montanha sobre o lago (salto de local).
  - 15:30 (930 s): cheiro da pena -> voo até o zoológico.
  - 18:37 (1117 s): "É dois contra um" -> luta com o Chico -> captura (virada de ato).
- Duração 0,92 a 1,22 s (média 1,1 s). Em 5 dos 7 o áudio vai a **zero digital** durante ~1 s; no 135 s e 371 s o áudio cai a -32/-45 dB mas não a zero.
- **(hipótese)** A regularidade (~3 min) pode indicar ponto de emenda entre arquivos de gravação OU slot de mid-roll; mesmo assim funcionam como "capítulos". Para a skill: usar dip preto de ~1 s com silêncio como **marcador de elipse/virada de ato**, no máximo 1 a cada ~3 min.

---

## 2. Estrutura (gancho, capítulos, fechamento)

| Janela | Conteúdo | Observação |
|---|---|---|
| 0:00-0:02,5 | Promo do livro do Paulo ("link na descrição") | voz já em cima do cartão |
| 0:02,5-0:30 | Cold open: ovos no ninho, águia chega ("Ei, moça, me choca") | selo "L" 2,7-6,5 s |
| 0:30-0:59 | Mãe sai, volta, **Chico captura a mãe** ("mais uma pro meu zoológico") | flash vermelho em 0:45 |
| 1:00-1:30 | Tempestade de raios; relâmpago em 1:23 (flash branco+feixe+fogo) | clima do jogo |
| 1:30-2:15 | Jaguar encontra os ovos, leva-os ao covil | dip suave 2:15 |
| 2:15-3:09 | Covil (caveiras/sangue), chocam, fogem | dip 3:03 |
| 3:09-3:31 | Falham em voar | |
| **3:29-3:34** | **Frase-promessa**: "no vídeo de hoje a gente vai fazer missões e evoluir pra virar uma águia forte e salvar nossa mãe" + **teaser** | só aos 16,6% do vídeo |
| 3:34-6:10 | Cap. 1 "fome": minhoca, coelho, volta ao ninho (carne de coelho) | "?" verde 4:16 |
| 6:10-9:07 | Cap. 2 "voar": Patão cai, Pobre sozinho evolui; raposa pede ajuda | |
| 9:07-12:15 | Cap. 3 "acampamento dos caçadores": gaiolas, jaguatirica, Cadu (mentor) | "?" brancos 9:29 |
| 12:15-15:30 | Cap. 4 "treino do Cadu" (voo sobre o lago), evolução, devolver raposinha, matar jaguar | torcida 12:34 |
| 15:30-18:37 | Cap. 5 "zoológico": procura da mãe, vidro, mãe aparece | "?" 16:19 |
| 18:37-20:53 | Cap. 6 clímax: capturados, jaula de cobras, evolução final (gigante), vingança no Chico | "Eu virei mágica gigantesca" 20:04 |
| 20:53-21:04 | Fechamento: "Prontinho, mãe... Tchau" + easter egg falado "Esquinha azul / escondido no canal do Problas pra você achar" | |
| 21:03-21:05 | End card ~10,8 s | 1253,9 s em diante |

Observações:
- O vídeo funciona como "episódio de série": cold open longo (3:30) com perigo antes da promessa. Gancho = personagens fofos em perigo + vilão.
- O fechamento incorpora um **easter egg falado** ("esquinha azul escondido no canal") que incentiva rewatch. Em 1257-1264 o áudio cai para -35 dBFS; a transcrição do Whisper nesse trecho (repetindo "Esquinha azul") pode ser alucinação sobre o colchão do end card **(hipótese)**.
- Capítulos NÃO têm título na tela (nenhum lettering de capítulo em 21 min).

---

## 3. Música

Medições (a partir do M/S de todo o vídeo, 22,05 kHz):

- Nível por quadro de 50 ms (canal médio): P1 -39,5 · P5 -34,1 · P10 -30,8 · P50 -24,9 · P90 -22,1 · P99 -19,8 dBFS.
- Canal Side (L-R)/2: mediana -44 dBFS. Correlação L/R **0,97** ao longo do vídeo: o áudio é praticamente **mono**. Música estéreo típica daria correlação <0,85.
- Nas **pausas** (quadros <-31 dBFS, 2.216 quadros, 8,9% do tempo) o espectro médio é ruidoso, **sem picos tonais** (nenhum pico >6 dB acima da vizinhança). Piso de ~-35 dBFS (11 dB abaixo da fala em -24,5). Isso é compatível com ambiente do jogo/ruído, **não** com música contínua.
- **Conclusão: nenhuma música detectada no corpo do vídeo (0:00-20:53).** Se houver bed musical, ele está <= -35 dBFS e atrás de 11 dB de voz, o que não tem função audível. Ressalva: eu não ouço; música muito baixa mascarada pela fala não é mensurável.
- Trocas de música: **nenhuma**. Momentos de música: **nenhum**. Ducking: **não aplicável / não mensurável**.
- **End card (1254-1264,7 s):** nível -35,5 dBFS (σ 1,9 dB), correlação L/R **0,77** (mais aberto), picos tonais em 66, 198, 392, 786 Hz (G2/G3/G4/G5, oitavas) e 1109/1662 Hz. É conteúdo musical sustentado (pad/drone em G) **(hipótese: música de outro, de baixíssimo volume)**. Transição: entra no mesmo instante do corte para o end card (1253,9 s); a voz cai de -25 para -35 dBFS ~1,5 s antes.
- Implicação para a skill: **não colocar trilha** neste estilo. Se o cliente quiser, a referência dá piso de -35 dBFS (= -11 dB sob a voz), mas não evidencia nenhuma trilha real. Marque como "opcional/não aprovado pela ref".

---

## 4. Nivelamento da voz

- EBU R128 (ffmpeg ebur128): **Integrado -21,5 LUFS** · Threshold -31,6 · **LRA 2,6 LU** (LRA low -22,6 / high -20,0) · **True peak -8,8 dBTP** (pico de amostra -9,0 dBFS; P99,9 de |amostra| = -13,4 dBFS).
- RMS por segundo (canal médio) em janelas de 60 s: média entre **-21,8 e -22,8 dBFS** em todos os 20 blocos (variação <1 dB entre blocos). Percentis 1 s: P1 -29,7 · P5 -24,1 · P10 -23,7 · P25 -23,0 · P50 -22,3 · P75 -21,6 · P95 -20,1 · P99 -19,1.
- Leitura: voz **fortemente comprimida/limitada** ("flat"), todas as falas no mesmo nível, sem diferença audível mensurável entre início e fim. Sobra 8,8 dB de headroom: o vídeo é **muito mais baixo** que o alvo de streaming (-14 LUFS), ~7,5 dB abaixo.
- Quedas internas: só nos dips pretos (-29 a -180 dB) e no end card (-35).
- Para nosso uso: manter a ideia de **voz uniformemente nivelada (LRA <=3 LU)**, mas recomendo normalizar para ~-16 a -14 LUFS (o ref está baixo demais, não imitar o nível absoluto). Isso é decisão, não está no ref.
- Duas vozes do roleplay (Pobre/Patão) têm o mesmo nível aparente: sem diferença de ganho por personagem em 1 s de resolução.

---

## 5. SFX

Detecção por canal Side (estéreo) acima da mediana local (+5 dB, > -42 dBFS), janelas de 0,5 s. 26 grupos em 21 min (~1,2/min), todos **-31 a -38 dBFS no Side** (muito abaixo da voz) — são sons do jogo/mixagem ou SFX discretos:

| Janela | Evento visual correspondente |
|---|---|
| 2,0-3,5 s | cartão -> jogo (hipótese: whoosh/impacto de transição) |
| 47-49,5 s | Chico captura a mãe (flash vermelho) |
| 71-75 s e 81-86 s | tempestade, relâmpago em 82,97 s |
| 136-138 s | dip suave, jaguar |
| 177-179 s, 213-215 s | cave / fim do teaser |
| 507-511 s | lago/raposa |
| 753,5-755,5 s | **torcida + confete** (hipótese: aplauso estéreo) |
| 894-900 s | cena de pássaros/montanha |
| 1110-1112 s | luta com o Chico |
| 1229-1240 s | evolução final / jaula de cobra |
| 1253 s | corte para end card |

- Não encontrei **stingers de edição** nos dips pretos: o áudio volta com a voz no mesmo nível (-24) logo após o preto. O pico na volta (ex.: 183,9 s) é só pico de fala.
- Picos de amostra: nenhum transiente isolado acima de -9 dBFS fora da voz. **Não há SFX de meme** detectável (sem vine boom, bruh, etc.) — o vídeo é "audio-light" em SFX de edição.
- Itens que eu esperaria e **não** vi: whoosh em cada overlay, "pop" em sticker, riser. Se existirem, estão abaixo do ruído de medição (hipótese). Para a skill: SFX só diegéticos + 1 aplauso/celebração + eventual whoosh no cartão.

---

## 6. Efeitos visuais, overlays, textos

### 6.1 Cartão promo do livro (0,0-2,48 s)
- Arte full-screen: capa "PROBLEMS - A COR ESCONDIDA" à esquerda + título "MEU NOVO LIVRO" à direita (tipografia 3 linhas, MEU branco/azul, NOVO magenta, LIVRO ciano), fundo skyline roxo/rosa/azul neon.
- Animação: 0,00 s só capa e fundo -> 0,25 s título entra em cinza/translúcido -> 0,50 s cores cheias -> ~1,00 s surge "LANÇAMENTO" (topo) e "LINK NA DESCRIÇÃO" (base). Hold até 2,48 s.
- Voz em cima: "O livro do Paulo chegou, link na descrição" (nível normal de fala).

### 6.2 Transição cartão -> jogo (2,48-2,75 s)
- Hard cut para o 1º quadro do gameplay **desfocado (gaussian blur forte)** que foca em ~0,25 s, junto do selo entrando.

### 6.3 Selo "classificação indicativa" (L)
- Texto branco em duas linhas "classificação indicativa" + quadrado verde com "L", canto superior esquerdo.
- Entra por **slide horizontal vindo da esquerda** (2,75-3,0 s) e sai por slide para a esquerda (6,2-6,6 s). Fica ~3,7 s totais. (Prática comum no YouTube BR.)

### 6.4 Teaser rápido (209,5-214,1 s)
- Dura ~4,6 s, 5 cortes (210,1 · 210,4 · 212,4 · 213,3 · 214,1), mostrando **cenas futuras** do vídeo: coruja/ave branca na floresta noturna (209,5), montanha com crystal (210,2), topo de montanha, jaulas do acampamento (~211), rio visto de cima, trilha do zoológico, cúpula de vidro (~213,5).
- **Grade lavada**: céu quase branco, contraste baixo, preto levantado (desbotado/dessaturado) em contraste com o verde saturado do resto. Dispara na fala "no vídeo de hoje a gente vai fazer missões e evoluir...".
- Sem texto, sem marcador visível. É o único trecho "montado" do vídeo.

### 6.5 "?" stickers (reação de dúvida/suspense)
| t aprox. | Aparência | Duração |
|---|---|---|
| 3:42 (222 s) | 2 grupos de 3 "?" brancos com contorno preto grosso, esquerda e direita do personagem | ~1 s |
| 4:16-4:17 (256-257,5 s) | **1 "?" grande verde** brilhante com contorno preto, entra com **scale pop** (pequeno -> grande) ao lado do avatar | ~1,5 s |
| 9:29-9:31 (569,5-571,5 s) | **cacho de 6-8 "?" brancos** no rodapé, cresce e some (pop com wobble) | ~2 s |
| 16:19 (979 s) | **4 "?" brancos grandes** nos cantos (2 esquerda, 2 direita) | ~1 s |
- Casam com falas de confusão ("Cadê ela?", "Não tá vazia nada", "Nova atração zoológico?"). São PNG/vídeo de sticker com contorno preto grosso e **cor muda por ocorrência** (verde no 4:16).

### 6.6 Torcida + confete (celebração, ~754-756 s)
- Logo após um corte duro (753,7 s) com quadro desfocado/fade, entra **overlay de silhuetas de torcida (plateia com braços levantados) sobre confete/fogos brilhantes** vindos de baixo: aparece 754,0 -> pico 754,75-755,0 -> some 755,5-756 s (~1,8 s).
- Fala: "Eu tô voando em cima do crocodilo... eu evoluí" (12:34-12:36).
- Áudio: salto estéreo +8 dB no Side em 753,5-755,5 s (hipótese: SFX de aplauso/comemoração).

### 6.7 End card (1253,9-1264,7 s, ~10,8 s)
- Fundo azul-royal com **sunburst radial** (raios) e texto "VEJA MAIS VÍDEOS" em cima; **"NO CANAL"** aparece em segundo momento (1254,5 s mostra "No..." digitando/entrando). Cinco personagens do elenco (laranja de lupa, vermelho de cartola, ciano, verde de óculos, amarelo) abraçados, em PNG, centralizados na base.
- Entra por corte duro com 1 quadro só do sunburst vazio (1254,0), depois texto, depois personagens.

### 6.8 Dips pretos
- Ver 1.4. Corte seco para preto sem fade medido (1-2 quadros de transição não resolvíveis a 2 fps), ~1,1 s, com silêncio.

### 6.9 Flashes e tints de tela
| Tipo | Instantes (s) | Interpretação |
|---|---|---|
| Verde | 35, 97 | flash de ~0,5 s, o HUD (hotbar) também fica esverdeado/esmaecido. (hipótese: efeito do mod/jogo ou overlay verde; ambíguo) |
| Vermelho vinheta | 45, 115, 298, 488, 620, 922, 1107 (+ outros) | **dano do jogo** (vinheta vermelha com barra de vida piscando); coincide com ataques (Chico, jaguar) |
| Branco (flash) | 82,9-83,3 (relâmpago + feixe amarelo + fogo), 328,3 (fade-from-white com troca de local) | relâmpago é do jogo; o 328 ambíguo |
| Preto | 7 dips (1.4) | edição |
- **Nenhum flash de impacto/estrobo** tipo "dopamina". Nenhum "glitch", "RGB split", "shake".

### 6.10 Zoom, shake, câmera
- HUD (hotbar + vida) tem **o mesmo tamanho em todos os quadros** das 4 janelas densas (0-42 s, ~540-582 s, 1086-1128 s, 1170-1212 s) -> **sem punch-in/zoom em pós**. Variação de enquadramento é do jogo (câmera dolly/orbita, FOV largo).
- Sem screen shake de edição. Qualquer tremor é dano/impacto do jogo.
- Sem legendas/closed captions queimadas. Texto na tela só: selo L, "LINK NA DESCRIÇÃO", end card, textos do jogo (nametags "Feather", "Unlocked identity: minecraft:chicken", placa "NEW ZOO ATTRACTION", "Press Left Shift to Dismount").

### 6.11 Contadores / UI
- Nenhum contador, barra de progresso, ícone de missão ou emoji sobreposto em pós. Os ícones de habilidade na hotbar (ícones pequenos) são do mod.
- Mudança de HUD: de 1 slot vazio (0-480 s) para hotbar com 3-4 ícones (a partir de ~500 s) -> reflete a progressão do jogo.

---

## 7. Padrões reutilizáveis para a skill (derivados)

1. **Take longo**: deixar o gameplay rodar; se cortar, cortar na fala, não na ação. Mediana de plano ~4 s só por causa do jogo; planos editados de 20-80 s são normais.
2. **Dip preto de ~1,1 s com silêncio** nas elipses (no máximo 1 a cada ~3 min, 6 por 21 min). 5 de 7 com áudio zerado.
3. **Abertura**: cartão promo de 2,5 s (sobre fala) -> hard cut -> blur-to-sharp 0,25 s + selo "L" por 3,7 s (slide in/out pela esquerda).
4. **Gancho em 2 etapas**: cold open de ~3,5 min de narrativa -> frase-promessa -> teaser de ~4,5 s (5 cortes, grade lavada).
5. **Overlays emotivos**: "?" para dúvida (4x), torcida+confete para vitória (1x). Máx. ~1 overlay a cada 3-4 min.
6. **Áudio**: voz nivelada, LRA <= 3, sem música (ou ~-35 dBFS no end card), SFX esparsos e baixos.
7. **Fechamento**: tchau dito + convite/easter egg falado, depois end card de ~10,8 s com sunburst azul, "VEJA MAIS VÍDEOS NO CANAL" e elenco.

---

## 8. Pontos de atenção ao editar brutos (para o editor/IA)

- **Não crie cortes de ritmo**: este estilo funciona porque a dublagem ao vivo sobre gameplay contínuo é a edição. Cortar a cada 2-3 s quebraria a atuação (ritmo ~234 palavras/min).
- **Não corte pausas da fala** (só 24 pausas >=0,25 s em 21 min). Se remover silêncio, preservar a cadência de diálogo e as pausas dramáticas ("Pera aí... barulho?").
- Preservar os **ruídos/gritos** do jogo (dano, trovão) — são parte do SFX; a mix é quase mono.
- Quando o jogo faz **flash vermelho (dano)** ou **relâmpago**, deixar como está; não duplicar com flash de edição.
- Dips pretos: posicionar **na virada** (morte de personagem, troca de local, mudança de ato). Verificar que o áudio zera ~1 s (usar ganho -inf ou silêncio digital) e que a voz retoma limpa.
- Teaser: usar 4-6 clipes de ~1 s das cenas futuras com grade dessaturada/lavada; cortes secos; sem texto.
- Selo "L": exportar como PNG com animação slide (2 linhas de texto + quadrado verde com "L"). Manter 3,5-4 s.
- Stickers "?": contorno preto grosso, preenchimento branco (verde na variante "pop"), scale pop 0->110%->100% em ~0,25 s, hold ~1 s, sair rápido. Cantos ou rodapé, nunca cobrindo o personagem.
- Torcida+confete: usar só em marco de vitória/evolução. Duração ~1,8 s. Corte duro + desfoque no 1º quadro.
- Normalizar a voz (-16 a -14 LUFS, true peak <= -1 dBTP) em vez de copiar -21,5 LUFS.
- Garantir **todas as faixas de áudio no remux** (voz de dois personagens + jogo); o vídeo ref tem 1 mix, mas o bruto do cliente pode ter faixas separadas.
- Não colocar legenda queimada (ref não tem).
- O easter egg falado do fim ("esquinha azul escondido no canal") deve ser preservado, se vier no bruto.

---

## 9. Assets a achar na web

| Asset | Termo de busca | Observação |
|---|---|---|
| Selo classificação indicativa L (BR) | "classificação indicativa livre L png verde", "age rating Brazil L green icon png" | usar PNG com transparência + versão animada slide |
| "?" sticker branco com contorno preto | "question mark sticker png black outline white", "confused question marks png transparent", "comic question mark outline" | variante verde brilhante, versão em cacho (3 a 8) |
| Torcida silhueta + confete | "crowd silhouette cheering green screen", "audience silhouette overlay confetti fireworks green screen", "celebration overlay confetti sparkles transparent" | 2 s |
| Aplauso / comemoração (SFX) | myinstants: "applause", "crowd cheer", "aplausos", "torcida" | só para a torcida |
| Trovão / relâmpago (SFX) | myinstants: "thunder", "relampago", "trovao" | só se o jogo não tiver |
| Whoosh de cartão (hipótese) | myinstants: "whoosh", "swoosh transition" | opcional |
| Sunburst azul | "blue sunburst background radial rays png/loop", "end screen background blue rays" | para end card |
| Cartão promo (livro/neon skyline) | "neon city skyline background purple pink", "book mockup 3d transparent" | o cartão é do cliente; fornecer arte própria |
| End card elenco | usar PNGs do elenco do próprio canal (5 personagens abraçados) | pedir ao cliente |
| Fonte "MEU NOVO LIVRO" | tipografia sans pesada com contorno, ex.: "Bangers", "Lilita One", "Anton" | estimado visualmente |
| Grade lavada de teaser | LUT "faded matte low contrast", "washed out film emulation LUT" | só para o teaser |
| Pad/drone G (end card) | "ambient pad G major royalty free loop", Pixabay/Uppbeat | opcional (hipótese) |

---

## 10. Limitações desta análise

- Não ouço áudio: "sem música" e "sem SFX de edição" significam **não detectados por medição** (nível, espectro, estéreo), não prova de ausência.
- O mix é quase mono (corr 0,97), por isso não consegui separar voz de jogo; o piso de -35 dBFS pode ser ambiente do jogo.
- A taxa de 2 fps nas janelas densas e 1 fps no resto não resolve fades de 1-2 quadros (dips pretos podem ter fade de 2-5 quadros).
- A classificação "corte de jogo x corte de edição" foi feita por inspeção visual de amostra (27 cortes duros + clusters), não dos 148.
- Janelas densas (2 fps, 512 px) analisadas: 0-42 s (abertura), ~540-582 s (lago/acampamento, dip 547), 1086-1128 s (zoológico, dip 1117) e 1170-1212 s (jaula de cobras, evolução final). Mais folhas de contato de 1 fps de todo o vídeo.
- Arquivos de apoio: `r2/dense_A..D`, `r2/dm_*.jpg` (montagens), `r2/full/sheet_*.jpg`, `r2/cutv/*.jpg`.
