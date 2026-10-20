# Padrão de edição — canal Problems (Minecraft POV)

Fonte: briefing do Matheus (12/10/2026) + vídeo-referência BBKrwgbsp74 (primeiros 60 s, medido com demucs) + 5 refs em `sintese-referencias.md`.
Prioridades dele, em ordem: **timing de corte e ritmo → música + SFX → zooms pontuais → distorção para piada**. Inserções (ícones de dinheiro etc.) são raras.

## 0. Mapa roteiro -> efeito (v1, 15/10/2026) — o que a edição DEVE fazer quando...
| Gatilho na fala/cena | Tratamento | Receita (build_edit2 `fx`/`stickers`/`sfx`) |
|---|---|---|
| personagem cita um ITEM ("esse canudinho") | mostrar o item | sticker do item (pop+rot) + spotlight PNG fade + SFX item (zeldaitem) na palavra |
| pergunta RETÓRICA / dúvida debochada | distorção OU SFX meme OU P&B | pop de zoom 125–140% + curvatura -40..-55 + SFX (huh-cat/como-assim/hm); variar entre as perguntas; cacho de "?" gigantes (cluster) nas mais fortes; P&B = Tonalidade 100 + push |
| deboche/ideia duvidosa do outro personagem | SFX no gatilho (palavra do deboche), não depois | record-scratch; micro-punch 112% |
| OBSTÁCULO ("não consigo beber") | mostrar e brincar | zoom 230–250% no HUD/mensagem do jogo (ver quando a mensagem está visível!) + SFX erro/fail (windows-xp-error, wah-wah) |
| número do HUD citado ("mais de 100 litros") | zoom no contador | hud zoom fx=960,fy=0 s=230 hold ~1.5 s (+ ding) |
| 1ª tentativa de cumprir o objetivo | música de tensão/intriga + dolly lento (100->105–109%) em pedaços | cena de tentativa = tensão; stinger no 1º frame da música |
| piada com o corpo (barriga) | zoom abaulado no avatar (foco ~(960,600)) | pop 160% curv -55 + taco-bell-bong |
| revelação de frustração (0,1% da água) | zoom no contador + dun-dun-dun; depois sad trombone | |
| novo objetivo / virada de ato | whoosh + troca de música | |
Regras: eventos de `fx` não podem se sobrepor (builder acusa); distorção/P&B só em pergunta/piada (1 por ~15–30 s), dolly de tensão pode ser contínuo.

## 0b. Ritmo (regra dura)
- Lacuna de fala máxima na entrega: 0.23 s (PAD 0.10 após cauda + 0.09 antes do ataque). `check_final.py` falha se > 0.32 s.
- Comece ~0.09 s antes da 1ª palavra (cortar ruído morto).
- Corte só onde as DUAS vozes estão em silêncio (RMS); nunca dentro de palavra; pad antes do ataque.

## 1. Anatomia dos primeiros 35 s (ref BBKrwgbsp74) — o "molde" do gancho
| t | O que acontece | Técnica |
|---|---|---|
| 0.0–2.5 | cartão "MEU NOVO LIVRO / LINK NA DESCRIÇÃO" (arte do cliente) | whoosh em 0.0 e ~0.75 (texto entrando) |
| 2.0–2.5 | cartão → gameplay desfocado que foca (0.25 s) | **SFX anime shine** abrindo o vídeo |
| 2.7–6.5 | selo "classificação indicativa L" (canto sup. esq.) | slide-in/out |
| 6.0–7.0 | fala "desastres naturais" | **SFX Among Us role reveal** + glitch/aberração cromática + flash branco (~6.5) = ideia de perigo |
| 16.0–17.5 | chat mostra "X received the GOOD KIT" | **dolly-in** (zoom lento 100→~160%) em direção ao chat para mostrar a informação |
| ~20.0 | sticker "?" (vários, contorno preto, pop) quando voz sobe | scale-pop, ~0.5 s |
| ~22–24.5 | personagem leva patada do amigo; ~1 s depois: **SFX cômico** + **zoom grande e DISTORCIDO** na cara | música cai a silêncio ~1.5 s (23.75–25.25) = beat de piada |
| 34.0–35.0 | fala sobre os itens ruins | zoom na **hotbar** (~3x) + **escurecer tudo que não é item** (spotlight) + **SFX comic fail** na palavra "ruins" |

Densidade: ~5 efeitos em 34 s. **Depois do 1º minuto, bem menos agitado** (1 efeito a cada ~20–40 s, só quando a fala/cena pede).

## 2. Regras de efeito (cada um amarrado a uma causa na fala/cena)
- **Dolly-in / zoom de informação**: quando algo na tela precisa ser lido (chat, HUD, placa, itens). Ease-out, 0.5–1.5 s, volta com corte ou zoom-out suave.
- **Zoom de piada**: 1 s depois do gatilho (patada, falha, susto), 150–250 %, pode distorcer (fisheye/bulge/esticar). Sempre com SFX cômico. Duração 0.5–1 s.
- **Spotlight**: escurecer o resto (≈ -70 % brilho) + zoom no objeto citado; sai quando a fala acaba.
- **Glitch/aberração + flash**: só em palavra de impacto/perigo (no máx. 1–2 por vídeo no gancho).
- **Sticker/PNG**: raro, <1 s, pop com overshoot; ícone de dinheiro etc. quando o personagem cita.
- Nunca efeito sem motivo; nunca 2 efeitos grandes em <3 s (exceto gancho).

## 3. Ritmo de corte
- Cortes das refs são em grande parte câmera do jogo; a edição real corta: falas erradas/repetidas, pausas mortas, silêncios do bruto. Respiração natural não se corta.
- Mediana entre cortes nas refs: 1.1–3.7 s; takes longos (25–85 s) quando a ação é contínua e a fala sustenta.
- Telas pretas + silêncio ~1.0–1.4 s a cada ~3 min marcam passagem de tempo/ato (r1–r5). Usar ao mudar de ato.

## 4. Música (Epidemic Sound)
- **Sempre há cama de música** o vídeo todo (confirmado por Matheus e por stems: ~15 dB abaixo da voz).
- Cada faixa dura **30 s a 1:30 no máximo**.
- Trocar a faixa quando o clima muda: mudança de cenário, narrativa, passagem de tempo, plot twist, batalha, fuga, tensão, cena engraçada, triste. A música acompanha o clima.
- Transição de faixa: corte seco no momento da mudança, ou stinger/riser curto; música pode cair a silêncio num gag (ver 22–25 s).
- Escolher por emoção (tensão, épico, cômico, triste, suspense, aventura), não repetir a mesma faixa no vídeo.

## 5. Mixagem (medido na ref, 0–60 s)
- Voz ≈ -14 a -18 dBFS (RMS 250 ms); cama de música ≈ -30 a -35 dBFS → **~15 dB abaixo da voz**.
- SFX de edição ≈ -22 a -26 dBFS → **~7 dB abaixo da voz** (mais altos que a música, mais baixos que a voz).
- Vozes niveladas entre si; alvo geral do episódio -14 a -16 LUFS integrado (refs variam -12 a -22; não copiar os baixos).
- Música: duck extra sob falas de gag; pode abrir ~5–8 dB em trechos sem fala (ação, paisagem).

## 6. Faixas de áudio (regra dura)
- Nunca mesclar. Cada fonte numa faixa própria: POV, call(s), jogo, música, SFX. Tudo editável/restaurável (mute/cortes, não delete de clip nem render de mix).
- Remover voz de terceiros/ruído (clique de mouse/teclado, tosse) **só** quando atrapalhar fala do personagem principal ou for ruído puro. Discussões/gritos simultâneos do roteiro ficam.
- Tudo que não é fala do roteiro sai (por corte/mute na faixa, não destruição).
- Cortes de erro: identificar fala errada/repetida, remover a errada, **encaixar a certa** (take posterior ou anterior).

## 7. Pontos de atenção para os brutos (sinalizar sempre no projeto e no chat)
- (CORRIGIDO 15/10) Brutos NÃO vêm sem pausas: no teste havia ~29 s de lacunas em 210 s. Sempre rodar cutengine.
- Várias faixas de áudio no bruto (POV, call, jogo).
- Anotar no projeto (marker/nota) e no chat qualquer coisa fora do padrão.

## 8. Lacunas conhecidas
- Detecção automática de trocas de música e zooms nas refs é ruidosa → calibrar com timestamps do Matheus.
- Fonte de música Epidemic: precisa do acesso/biblioteca dele (definir).

---
## v2 (16/10/2026) — SUPERA os trechos de zoom/pop/música/SFX acima
Ver [`feedback-teste-corrigido.md`](feedback-teste-corrigido.md): zoom que fica (ease-out, nunca volta), seco × animado, presets BERSERKER, SFX atuais com níveis baixos, música por clima (cala no record scratch, entrada mais alta, sem duck), hand-off ~0 + Potência constante. Pop "sobe e volta" e cacho de "?" foram DESCARTADOS pelo Matheus.
