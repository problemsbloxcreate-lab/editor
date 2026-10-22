# v12 (minha) × "teste corrigido" (Matheus) — notas de análise (15/10/2026)

Fonte dos dados: dump ExtendScript das duas sequências (clipes, componentes, keyframes), export da sequência dele (`user_teste_corrigido.mp4`, 39,0 s), prfpset do Premiere (BERSERKER), áudio dos brutos (s1/s2) para medir cortes.
Sequência dele = clone da minha v12 editada (mesmos números de zoom/keys em vários pontos) cobrindo fonte 0,517–58,592 s.

## 1. Cortes (fonte)
- Dele: 15 keeps; minha: 12 keeps no mesmo trecho. Lacunas sem fala somadas: 2,1 s (dele) × 3,9 s (minha); maiores 0,20 × 0,22; lacunas >=0,2 s: 1 × 4.
- Transição entre falantes (hand-off) = lacuna ~0: J01 0,004 s (canudinho.→Ô), J03 0,02 (aqui?→Exatamente), J05 0,0 (patão!→Eu já vou), J09 0,0, J13 0,0. Mesma pessoa pausando = 0,18–0,21 s (J07, J08, J10–J12), igual ao meu pad. J00/J04 = 0,09.
- Entrada do corte cai em cima da 1ª fração do ataque (15–40 ms já audíveis em 9 de 14 cortes; 85 ms em J13). Saída: 12 de 14 em silêncio limpo. Eu deixava ~0,10 s antes do ataque e ~0,09 s depois da cauda.
- Início: 0,517 s (o "No" começa em 0,44) → começa ~70 ms dentro dele; minha v12 começava em 0,317.
- Cortes extras dele: 13,197–13,363 (micro-pausa antes de "canudinho aqui?", cai no corte p/ VHS), 14,898–15,148, 20,988–21,171 (corta 55 ms da cauda de "patão!"), 56,056–56,823 ("Por que a" some; começa em "gente").
- Mantém clipe de 0,58 s sem fala (41,141–41,725) = o instante em que entra a música de tensão (24,291 tl): música entra ANTES da fala (~0,6 s).
- Áudio com L-cut: A1 (voz POV) estende até 37,437 sob o corte de vídeo em 37,237 e some em 37,437–37,554 (silencia "gente não..." sobreposto ao "falei" da A2).
- Estrutura: 20 clipes em V1; vários são só razor p/ reiniciar keyframes.

## 2. Zoom / movimento (tl)
| tl | o que | focus |
|---|---|---|
| 0–0,43 | 182%→100% (zoom-out de abertura) + White Flash B (Tonalidade 70→0 em 0,90 s) + anime-shine | centro |
| 3,55–4,42 | pop 100→138% em 0,12 s, hold 0,25 s, volta em 0,5 s; vine-boom em 3,537 ("toda") | centro |
| 5,82–6,57 | 100→650% em 0,75 s, hold até 7,374 (corte); spot_dark fade 5,49→5,67; anime-wow 5,689 | no canudinho em mãos do personagem (fx 940, fy 684) |
| 9,83–11,04 | push lento 100→~132% | centro |
| 11,04–12,58 | clipe esticado 391%×258% (não uniforme) + Lava's VHS + bonk 11,044 + record scratch 11,195; MÚSICA CALA 11,05–12,55 | centro |
| 14,03–14,95 | 239% estático (hard cut-in) no personagem com canudo | fx≈932, fy≈578 |
| 16,25–17,97 | 254% com pan manual (5 keys) seguindo o Chique | rastreado |
| 24,88–27,46 | 138% estático 2,6 s (era meu pop 100→138→100) | centro |
| 27,55–28,42 | pulso 100→118% | centro |
| 28,46–29,08 | 119,8% + Red Flash B (Tonalidade 70→0) + Impact Shake High (22 keys) | centro |
| 29,10–31,57 | push lento 101,9→108% | centro |
| 31,75–33,67 | 136→250% em 0,27 s na mensagem do jogo (fx 962, fy 944 — meus números), hold, sai em 0,35 s | mensagem |
| 36,0–37,43 | push lento 103→108% | centro |
Largos (100%) respiram: 12,6–14,0; 14,95–16,25; 17,97–24,29 (6,3 s); 33,7–36,0.

## 3. Efeitos = presets BERSERKER ("Lava's …") — confirmados por comparação de valores
- Início: Lava's White Flash B (Tonalidade, 70→0 em 0,901 s).
- 11,044: Lava's VHS (Entalhe de cor, Ruído herdado, Cor de Lumetri, Distorção ondulada ×2) + Motion 391×258 não uniforme.
- 28,462: Lava's Red Flash B + Lava's Impact Shake High (Transformar, posição 22 keys iguais).
- Não achei nenhum "glow" (Brilho para VR) na sequência dele.
- prfpset: `Documents\Adobe\Premiere Pro\26.0\Profile-mathe\Effect Presets and Custom Items.prfpset`; 192 presets parseados em `presets_catalog.json`.
- QE não enxerga presets pelo nome (getVideoEffectByName devolve objeto sem nome). Aplicar = reconstruir a partir do XML (efeito+params+keys) ou automação de UI.

## 4. SFX (tl, dB exibido)
Dele: anime-shine 0,00 (−0,8), vine-boom 3,537 (−11,1), anime-wow 5,689 (−15,7), bamboo-bonk 11,044 (−6,9), record-scratch 11,195 (−18,5), sudden-suspense 12,279 (−22,3), bonk 19,586 (−5,4), huh-cat 25,859 (−14,5; corta 0,5 s do começo), windows-xp-error 27,327 (−4,6), wrong_5 28,395 (−14,1), nintendo-switch-error 29,012 (0), spongebob-fail 36,169 (−14,7).
Minha v12 tinha a mais: zeldaitem 5,87 (−1), 2º suspense 26,14, whoosh 34,12 (+0,8), erro.mp3 35,34, wah-wah-fail 39,49, ding 42,0, + cluster de "?" (27,5). Ele removeu todos.
Níveis: record-scratch −9 dB e suspense −6 dB mais baixos que os meus.

## 5. Música
- 0–1,8: Brighter than the Sky (só 1,8 s, −14,8 dB, em A7); 1,802–11,044: **Lifecrash – Rascal Genius** (pasta MUY ANIMADAS; −16,2 dB; começa do início da faixa na 1ª palavra do roteiro "Patão").
- 11,05–12,55: SEM música (record scratch/VHS).
- 12,579: Sleepy Sneaky Sway (igual à minha, −15 dB, fade-in 0,08 s) até 24,29.
- 24,291: That Thing Behind Us (igual à minha), −10,3 dB nos 4,2 s de entrada, −13,9 dB sob o diálogo (minha: −16,1 e −23,1 com duck). Sem ducks. Termina em 36,37 (antes do corte 37,237).
- Mix: o render dele ficou −18,2 LUFS/−3,9 dBFS; o meu −14,6/−1,7 (SFX dele mais baixos; mesmo limitador 0,92).

## 6. Descobertas de ambiente
- Biblioteca de músicas LOCAL: `D:\Users\PREDATOR\Documents\Epidemic 2K23 (Pasta de músicas)\` com ~400 faixas por clima (PROBLEMAS, TENSAS, SUSPENSE, TROLL, INTROS, MISTERIO, MUY ANIMADAS, DUDOSAS…). Não era preciso Drive.
- SFX novos em Downloads (copiados p/ library/sfx): bamboo-hit-anime-bonk-sound, nintendo-switch-error, spongebob-fail, anime-wow-sound-effect (1), wrong_5.
