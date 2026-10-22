# Padrão aprovado — sequência "teste corrigido" do Matheus (16/10/2026)

Origem: ele clonou minha v12 e refez os 40 s iniciais (fonte 0.517–58.592). Comparação medida (dump ExtendScript + áudio dos brutos + export) + áudio-feedback dele (`feeds.mp3`, transcrito).
Tudo abaixo é **medido** a menos que marcado (hipótese).

## 1. Cortes (voz)
- **Troca de falante (hand-off) = lacuna 0–0,09 s**; **mesma pessoa pausando = ~0,2 s**. Resultado: 2,1 s de pausa em 39 s (v12 tinha 3,9 s; 4 lacunas >=0,2 s → 1).
- **Corte de entrada no 1º quadro do ataque** da palavra (15–40 ms já "dentro" em 9/14 cortes); corte de saída em silêncio limpo.
- **Transição de áudio "Potência constante" (0,2–0,3 s, centrada no corte) nas 3 faixas do bruto** nos cortes apertados (hand-off/zero-gap): é o que permite cortar tão colado sem estalo. Música também: fade in/out com a mesma transição.
- Música/voz: **L-cut** — áudio da voz POV estendido 0,2 s por baixo do corte de vídeo; fala sobreposta/atrapalhando é **silenciada na própria faixa** (clipe da A1 removido), nunca mesclar.
- Mantém um clipe curto sem fala (~0,6 s) quando **a música nova entra** (a música chega antes da fala).
- Evitar fragmentos: ping-pong rápido não pode picotar (trecho < 0,5 s com palavra → desfaz o corte; sem palavra no ASR = ruído → some).

## 2. Zoom — critério (áudio dele) + medido
- **Corte seco** (punch-in estático) = momento mais bruto, engraçado, escrachado. **Zoom animado** = quando o personagem está demonstrando/enfatizando algo, fala arrastada, entonação específica, ou muda o ritmo/tensão da cena.
- **A velocidade da animação acompanha a velocidade da fala** (fala rápida → zoom rápido; devagar → zoom lento; mudança de ritmo/tensão da cena também).
- **NUNCA "zoom e volta"** ("muito ruim"): o zoom **fica** um tempo, com **gráfico de velocidade decrescente** (começa rápido e decai suave = ease-out) e termina num corte seco para o plano aberto.
- Medido: zooms em 112–138 % (ênfase), 239–254 % (personagem que fala, hard cut; 254 % com pan manual seguindo o personagem), **650 % no item citado dentro do mundo** (não sticker PNG) + spotlight escuro, 250 % na mensagem do jogo (foco 962,944), 391×258 % **não uniforme** (esticado) = distorção da pergunta debochada. Entre zooms ficam planos abertos longos (respiro).
- Tensão: dolly mínimo (100→103 %) na entrada da música; depois 138 % fixo.

## 3. Efeitos = presets BERSERKER ("Lava's …") — ver `scripts/berserker.py`
- Abertura: **White Flash B** (Tonalidade 70→0 em 0,9 s) + zoom-out 182→100 % + anime-shine. Deboche/pergunta retórica: **Lava's VHS** (+ escala esticada) + bonk + record scratch + **a música CALA** (11,05–12,55 s) e a faixa seguinte entra na fala seguinte. Obstáculo: **Red Flash B + Impact Shake High** + 3 erros (xp-error, wrong, switch-error).
- Matheus: "90 % do que você precisa tem pronto lá" — flashes, shakes, zooms, VHS, glows, outlines (traçado), pop in/out, flips 3D, light sweeps, pans, vinheta. Usar preset em vez de criar. (Glow = os flashes; não há "Brilho para VR" na sequência.)

## 4. SFX
- Do áudio: alguns eram **ultrapassados/não combinavam/altos demais**; faltavam memes **atuais da bolha do nicho** → ver mais referências (repertório). Removidos por ele: zeldaitem, whoosh, erro.mp3, wah-wah-fail, ding, 2º suspense, cacho de "?". Entraram: bamboo-hit bonk, anime-wow, wrong_5, nintendo-switch-error, spongebob-fail (+ os mantidos: vine boom, anime-shine, bonk, record scratch, suspense, huh-cat, windows-xp-error).
- Níveis (exibidos): stingers baixos (record scratch −18,5; suspense −22,3), impactos/erros mais altos (−0,8…−7), fail/wow −14…−16. Mix final dele −18,2 LUFS / −3,9 dBFS (o meu −14,6: SFX altos demais).
- Repertório atual baixado (library/sfx): faaah, emotional-damage, sheesh, metal-gear-alert, tuco-get-out, hitmarker, clown-horn, why-are-you-running, cartoon-boing, gta wasted, mario oof, deg-deg-sussy, tadaa, bruh, steve hurt, huh (ceeday), what-the-dog-doing.

## 5. Música
- Biblioteca **local** Epidemic: `D:\Users\PREDATOR\Documents\Epidemic 2K23 (Pasta de músicas)\` (pastas por clima: PROBLEMAS, TENSAS, SUSPENSE, TROLL, INTROS, MISTERIO, MUY ANIMADAS…). Busca por clima com CLAP: `scripts/clap_index.py` + `clap_query.py`.
- Áudio dele: manteve 2 das minhas faixas (Sleepy Sneaky Sway, That Thing Behind Us), **trocou o corte/timing da 1ª** (intro: sting Brighter 1,8 s → Lifecrash a partir da 1ª fala do roteiro) e tirou a que não combinava. **Do minuto 1 em diante ele trocaria muito mais músicas**: as minhas não combinavam com o clima do momento → música é por CLIMA da cena, cada mudança de clima = nova faixa.
- Níveis (exibidos): intro −16,2, plano −15,0, **tensão entra mais alta (−10,3 nos 4 s de entrada) e fica −13,9**; **sem ducking**. Em efeito de record scratch a música some.

## 6. Premiere (técnico)
- QE: `addTransition(getAudioTransitionByName("Potência constante"), true, "00:00:00:12")` no item i+1 = transição 0,2 s centrada no corte.
- Novos efeitos entram em `components[2]` (logo após Opacidade/Movimento); cor de parâmetro via `setColorValue(a,r,g,b)` (setValue com inteiro grande dá cor errada); presets não aplicáveis por nome (QE) → reconstruir do `.prfpset`.

## 7. Ajustes finais (feedback 15/10/2026, sobre a entrega v13)
- **SFX inaudíveis**: "ficaram muito baixos, a maioria inaudível, a faixa dos −22 dB é a média". Causa (medida): o builder normalizava cada SFX para ~−27 LUFS → pico no mix −22…−35 dBFS; auditoria do render v13: metade dos SFX com delta <+1 dB sobre fala+música (base ≈ −10,5 dBFS de pico/400 ms). Correção em 2 passos: `peak_db` por tier melhorou (mediana de delta +1,0 → +3,5 dB) mas o orb do XP seguiu inaudível (pico = clique de 1 ms, RMS −24); versão final = `rms_db` (RMS ativo final: impacto −15, fail −16, gag −17, wow/stinger −18…−19, orb −17, gole −21) + teto de pico −2,5 (`sfx_levels.py`) + auditoria `sfx_audit.py` (v14: 56/62 com delta, pico mediano +4,7 dB).
- **"Takes futuros"**: nota sussurrada pelo criador (fonte 177.25–178.15; timecode 00;02;23;14 da v13) = pedido direto p/ ilustrar a frase seguinte com cenas impactantes do futuro; "como se fosse com um filtro de flashback e um SFX de XP do Minecraft a cada corte" → ver `takes-futuros.md`.
- **SFX de Minecraft** devem ser usados "pra fazer graça e dar dinâmica" (XP, level up, Villager, burp, bigorna, creeper, oof...) → extraídos do jogo (`mc_sounds_extract.py`).
- Pedido de sempre: atualizar a skill com tudo e entregar a edição final de 5 min.

## 8. Rodada 15/10 — ele editou a v14 (SFX sem keyframe, volumes, curadoria, mutes, efeitos)
Ver [`feedback-timeline-dele-15out.md`](feedback-timeline-dele-15out.md) (+ `timeline-dele-15out.json`): ganhos fixos por SFX (a tabela de tiers da seção 7 acima foi SUPERADA — v14b ficou alta), ~1 SFX/7 s, SFX no corte, Villager ≤1×, mutes de call/jogo, Brilho cintilante e tilt, músicas dele por pasta, cortes de repetição.

