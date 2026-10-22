# Síntese das 5 referências (Problems) — 12/10/2026

Fontes: analise_r1..r5.md (mesma pasta). Medição por ffmpeg (cortes, LUFS) + frames; áudio NÃO foi ouvido — "sem música/SFX" = não detectado.

| Ref | Vídeo | Dur | Cortes de cena | Mediana | Voz LUFS | Música |
|---|---|---|---|---|---|---|
| r1 | EqUbhDBjv0A | 21:10 | 283 | 2.8s | -21.5 | só end card |
| r2 | HtRwJkTY9_0 | 21:05 | 148 | 3.7s | -21.5 | só end card (pad) |
| r3 | 8LYjpPi3694 | 21:11 | 218 | 3.0s | -18.6 | nenhuma |
| r4 | LSVCoB_iLis | 19:20 | 344 | 1.1s | -11.9 | nenhuma |
| r5 | P5-y81v7ph0 | 19:00 | 268 | 2.2s | -22.3 | só end card |

## Padrão comum (confirmado em 5/5)
1. 0:00–2.5s cartão "MEU NOVO LIVRO / LINK NA DESCRIÇÃO" (voz já falando), corte seco p/ gameplay.
2. Selo "classificação indicativa L" canto sup. esquerdo ~2.5–6.5s (slide-in/out).
3. Cortes = quase todos câmera do próprio jogo (replay/3ª pessoa fisheye). Sem jump cut de respiração nem punch-in de edição.
4. Capítulos: tela preta ~1.0–1.4s + SILÊNCIO digital a cada ~3 min (≈3:00, 6:10, 9:10, 12:00, 15:05, 18:00).
5. Fim: fala "Problemzinho, esquininha azul…" + end card estático ~10.8s "VEJA MAIS VÍDEOS NO CANAL" (áudio -10 dB, música/pad).
6. Mix plano, LRA 1.7–2.7 LU, sem ducking (não há música p/ duckar).
## Elementos raros
Flash vermelho/dano, speed lines (r1 20:07), sticker "?" (r2), contador de dias pixel (r5), "DIA SEGUINTE" (r3 4:48), stings de sub-grave (r3 ~25x), zoom no HUD + flash branco (r3 18:08).
## CORREÇÃO (12/10, Matheus): TODOS os vídeos têm música; há SFX de meme; inserções raras (ícones de dinheiro etc.)
Prioridades dele: timing de corte, ritmo, música+SFX, zooms em momentos específicos (mostrar algo), dimensões distorcidas p/ piada.
Demucs (htdemucs, CPU) nos 5: stems não-vocais ficam ~15 dB abaixo da voz o vídeo inteiro (v3 voz -22/mús -37; v4 -15/-30; v5 -25/-38; bateria+baixo contínuos) = cama de música sob a fala. Detector automático de trocas de faixa ficou ruidoso (20–30 pontos/vídeo, mistura som do jogo): NÃO confiável sem ouvido. Zoom: HUD nem sempre visível, detecção automática inviável.

## (obsoleto) DIVERGÊNCIA com o briefing
Briefing diz: muita música/trocas, SFX de meme, PNGs/animações. As 5 refs, por medição, mostram o oposto (edição mínima). Pendente: confirmar com Matheus (refs certas? música baixa não detectada?).
