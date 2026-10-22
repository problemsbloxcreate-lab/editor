# Decupagem do Matheus — "Bebi toda a água do mundo" (vídeo inteiro, 19/10/2026)

**Fonte:** `C:\Users\mathe\Downloads\10 - Bebi toda a agua do mundo ( Pronto pra finalizar )_1.prproj`, "Sequência 01" (`e4e82caa`), 59,94 fps, 1182,7 s. Ele decupou o bruto inteiro `2026-10-08 08-16-27.mp4` (2170 s) de forma profissional. **Lido só-leitura** (dump ExtendScript, nada editado). Dados e scripts em `C:\Users\mathe\Skills\_research\mc-decup\` (`dump.json`, `cuts.json`, `edges.json`, `context_log.txt`, `compare_v14.txt`, `analyze_cuts.py`, `timeline_stems.py`, `dub_cuts.py`, `compare_v14.py`).

**Estrutura da sequência:** V1 = nest "VIDEO ORIGINAL" (o bruto em tempo real, offset 0) com 381 clipes; A2 (call) e A3 (jogo) = o bruto, cortados JUNTO com o V1 (381/381 alinhados). **A1 = dublagem**: a voz do teste era provisória (outra pessoa); o Problems dublou depois (`2026-10-14 08-40-46.mp4`, 1952 s, voz no stream 1) e o Matheus encaixou a dublagem **frase a frase** (460 trechos; o deslocamento dub↔bruto varia o tempo todo, de −127 a +224 s → não há sincronia fixa). A voz provisória do bruto ficou na A1 **desabilitada** (86 clipes), com 48 trechos ainda ativos. Sem transições de áudio, sem marcadores.

## 1. Números da decupagem
| medida | dele | nossa v14 (mesma fonte 0,5–364,8 s) |
|---|---|---|
| bruto → vídeo | 2165 s → **1183 s (54,6 %)** | — |
| mesmo trecho de fonte mantido | **250,1 s** (69 %) | 300,5 s (82 %) |
| clipes no trecho | 79 (média 3,2 s) | 133 (média 2,3 s) |
| duração do clipe (vídeo todo) | p5 0,83 · **mediana 2,6 s** · p95 7,4 · mín. 0,42 | p5 0,41 · mediana 1,87 · p95 5,3 |
| ritmo | 1 corte a cada **3,1 s** | 1 a cada 2,3 s |
| pausa entre falas no resultado (voz < −50 dBFS, ≥ 50 ms) | **mediana 0,07 s**, p75 0,10, p95 0,33–0,38 | mediana 0,10 s, p95 0,18 |
| silêncio total no trecho | 6,7 s | 11,4 s |

Pausas na timeline final dele (dub ∪ call): 197 de 278 abaixo de 0,1 s; só 7 acima de 0,5 s em 20 min, e todas com motivo (2 slots de inserção com A2/A3 mudos, 1 beat visual de 2,9 s em 82,8 s, 4 de 0,5–1 s).

**Leitura:** ele corta **menos vezes e mais fundo**. Tira ideias inteiras e deixa blocos contínuos mais longos. Nós picotamos mais (micro-cortes de 0,06–0,3 s) e mesmo assim mantivemos 50 s a mais de conteúdo.

## 2. Precisão do corte (attack / margem)
Medido em faixas LIMPAS (call A2 e dublagem têm gate: piso −88 / −120 dBFS → limiar **−50 dBFS** em janelas de 10 ms).
| borda | mediana | p75 | p95 |
|---|---|---|---|
| **entrada** (corte → 1º quadro com som), call falando no corte (n=182) | **0,010 s** | 0,050 | 0,197 |
| **saída** (último quadro com som → corte), call (n=145) | **0,020 s** | 0,050 | 0,177 |
| entrada, dublagem (n=460) | **0,000** (≤ 1 quadro de 10 ms) | 0,010 | 0,030 |
| saída, dublagem (n=460) | **0,000** | 0,030 | 0,080 |
| junta inteira (cauda + cabeça), todas as 376 juntas, voz −45 dBFS | 0,022 s | — | 0,092 (p90) |

- **Entrada = no ataque**: o corte cai no 1º quadro do som (o ataque/respiro de entrada FICA; nada de silêncio antes). 
- **Saída = no fim do som**: a cauda da palavra fica até ela morrer e o corte vem logo depois, a 0–50 ms.
- **Troca de falante × mesmo falante quase não muda**: lacuna mediana 0,012 s × 0,026 s. A diferença de 0,2 s que o nosso `tighten2` usa para o mesmo falante NÃO existe na decupagem dele.
- Comparado às bordas da v14 (casadas a menos de 0,6 s): a entrada dele vem **+67 ms mais tarde** (p90 +0,27 s) e a saída **−83 ms mais cedo** (p10 −0,38 s). Nós deixávamos ~0,07–0,08 s de folga a mais em cada lado → isso aparece como 80+ "lascas" de 0,06–0,3 s que ele tira e nós não.

## 3. Contexto: o que ele tira (log completo em `context_log.txt`)
Das 376 juntas: 126 só aparam (sem palavra, < 0,6 s), 104 tiram trecho MUDO (andar/esperar, mediana ~0,9 s) e 146 tiram FALA.
1. **Bastidor de gravação, sempre fora**, e são os maiores cortes (12–26 s): contagem "3, 2, 1", "pode falar agora / depois que o patrão falar", "corta aí, corta aí", "pode gravar", "calma, deixa eu falar de novo", "é porque reiniciou", "buguei", a call combinando quem fala ("acho que era tu que ia falar"), "como é que tá o bruto aí?".
2. **Retake: fica o ÚLTIMO take completo** e a largada falsa sai inteira, inclusive as palavras soltas: "Bom, galera, todo mundo sabe… / Calma, deixa eu falar de novo / Bom, galera, todo mundo sabe…" → só o 2º; "Aqui galera eu acho que / Aqui eu acho que o Brucutu…" → o 2º; "E olha só, galera, o Brucutu tá… / E olha só, galera, o Brucutu tá bem ali" → o 2º. Na dublagem é igual: "Parece que é uma loja… (lido 2×)" → o 2º; "Bora buscar uma nova / Bora buscar uma água nova" → o 2º.
3. **Gaguejo e conectivo hesitante**: "e… e vamos", "O… O problema", "Eu… eu também", "Agora… / vamos embora" → fica um, e a pausa vai junto.
4. **Repetição da mesma informação**: coaching "bebe água, vai, isso" ×N → 1 vez; números ditos 2× ("Já bebi mais de 100 litros / já bebi quase 100 litros") → 1; "vai, vai, vai" longo → curto; eco da call ("É verdade" depois de "é verdade, Chico"); "Bora galera continuar bebendo" que repete a frase anterior.
5. **Muleta de início/fim de frase sai** quando a frase anda sem ela: "É,", "É, mas", "Quer", "Olha", "O", "mano", "galera", "aí", "Agora", "Aqui", "deixa eu ver", "meu" (dezenas de cortes de 0,3–0,9 s com UMA palavra).
6. **Jogo morto**: andar, esperar a máquina sugar, abrir menu sem fala → sai (mediana 0,9 s por corte). Esperas longas saem inteiras: 252 s de "sugando a cachoeira" (fonte 1438→1690) viraram um corte só.
7. **Fica**: piada/reação da call mesmo atravessando a voz principal ("Isso aqui é músculo", "Vocês são tão barrigudos"); mutes da call só onde ela atropela (14 clipes A2 desabilitados, nunca apagados).
8. **Notas ao editor viram vaga**: na frase dos "takes futuros" (fonte 178,8–182,7) o clipe de V1 está **desabilitado** (tl 117,07–120,90) = espaço reservado para os takes. Nas notas de time-lapse (fonte ~1104→1161 e 1438→1690) ele pôs **5,5–6 s de outro trecho do bruto** (fonte 125–131 e 31–37) com A2/A3 mudos sob a dublagem = provavelmente vaga provisória (hipótese, não perguntada).

## 4. Quando há DUBLAGEM (este vídeo)
- O vídeo foi cortado pelo conteúdo e pelo jogo; a dublagem corre por cima, **contínua através dos cortes de vídeo** (os cortes de V1 tiram jogo morto enquanto a frase dublada segue → J/L-cut o tempo todo).
- Cada trecho da dublagem: entrada e saída no quadro do som (tabela acima), trechos encostados (lacuna 0 na timeline em > 75 % dos casos), mediana de 1,7 s por trecho; 893 s usados de 1953 s gravados (só 43 s de fala sobraram: retakes e frases cortadas).
- Do roteiro dublado ele ainda tirou frases inteiras que não faziam falta ("Acredita em mim, não é não, Chique?", "Se bebendo 160 litros de água a gente tá desse jeito?").

## 5. O que eu deveria ter feito no nosso teste (v12–v14)
1. **Margens**: entrada no 1º quadro do ataque (≤ 10–20 ms antes) e saída 20–50 ms depois do fim do som, para QUALQUER falante. O `cutengine` deixa PAD_BEFORE 0,09 + PAD_AFTER 0,10 (~0,19 s) no mesmo falante → é o dobro do que ele deixa (alvo de lacuna na junta: **0,03–0,07 s**, teto ~0,2 s só quando a imagem pede respiro). Limiar −50 dBFS em faixa com gate (call/dub); o ON −38 / OFF −46 pode cortar o começo de ataque fraco.
2. **Conteúdo antes de ritmo**: deixei 57,8 s que ele tiraria em 6 min (19 %): coaching repetido, números repetidos, largada falsa ("Aqui galera eu acho que"), muletas ("É,", "mas", "meu", "deixa eu ver"), eco da call, bastidor. O motor só olha silêncio; precisa de uma passada de **texto** antes (retake/repetição/bastidor/muleta).
3. **Menos micro-cortes, mais cortes decisivos**: mediana de clipe 2,6 s (nós 1,9). Lascas < 0,3 s sem palavra são sinal de margem errada, não de decisão.
4. **Notas do editor**: reservar a vaga (desabilitar o V1 / clipe provisório com A2/A3 mudos) em vez de deixar a fala crua rodando.
5. Fica igual ao que já fazíamos: nunca cortar dentro da palavra; fragmento < 0,5 s só se for palavra inteira (o mínimo dele é 0,42 s).

## 6. Checklist de decupagem (aplicar em todo bruto do Problems)
1. Transcrever s1/s2 (palavras) e calcular RMS de 10 ms das 3 faixas.
2. **Passada de TEXTO** (antes de qualquer silêncio): marcar (a) bastidor ("3, 2, 1", "pode falar", "corta", "de novo", "reiniciou", "buguei", combinação de falas); (b) retakes = frase/n-grama repetido em ≤ 20 s → manter o ÚLTIMO completo; (c) gaguejo/conectivo repetido; (d) a mesma informação dita 2× (números, coaching) → a melhor; (e) muletas de borda que a frase dispensa. Tudo vira `remove`.
3. **Passada de jogo morto**: trechos sem fala nas duas vozes e sem ação que a fala comenta → fora (mediana 0,9 s); esperas longas inteiras.
4. **Aparar**: entrada no 1º quadro ≥ −50 dBFS da fala que entra (folga 0–20 ms); saída no último quadro ≥ −50 dBFS + 20–50 ms. Lacuna resultante 0,03–0,07 s; até ~0,3 s só como beat intencional (gag/visual).
5. Call que atropela a piada → desabilitar o clipe da A2 (nunca A1).
6. Notas ao editor → vaga marcada (V1 desabilitado ou clipe provisório) + marcador.
7. Conferir: pausas da timeline (mediana alvo ≤ 0,08 s, p95 ≤ 0,35 s), nenhuma borda com fala cortada, duração de clipe ~2,6 s de mediana.

## 7. Recalibração do motor (19/10) — `tighten3` + `textpass` medidos contra a Sequência 01
Ferramentas: `scripts/textpass.py` (passada de texto) + `cutengine.tighten3` (margens). Avaliação reprodutível em `Skills/_research/mc-decup/run_eval.py` (`eval_decup.py` compara keeps em tempo de fonte com a máscara dele; `tune_text.py` mostra cada remoção com a % que ele também tirou). Calibrado em 0,5–740 s; **validado em trechos não usados** (1161–1438 e 1750–2100). Depois de ver a validação fiz 3 correções GERAIS (bastidor por sentença, recomeço interno só no POV, duração máx. de 1 s por palavra do ASR); os números abaixo são os finais.

| trecho | motor | mantido (ele) | IoU | palavras que ele tirou → nós também | palavras que ele manteve → nós também | |Δ| entrada / saída | pausa mediana / p95 |
|---|---|---|---|---|---|---|---|
| CALIB-A 0,5–365 | antigo `tighten2` | 312 s (248) | 0,785 | 10 % | 100 % | 81 / 78 ms | 0,09 / 0,18 |
| | **novo** | 290 s | **0,814** | **37 %** | 99,2 % | **35 / 57 ms** | 0,06 / 0,08 |
| CALIB-B 365–740 | antigo | 321 s (243) | 0,745 | 9 % | 99,9 % | 72 / 79 ms | 0,11 / 0,19 |
| | **novo** | 288 s | **0,803** | **35 %** | 99,0 % | **32 / 50 ms** | 0,07 / 0,29 |
| VALID-1 1161–1438 | antigo | 229 s (157) | 0,675 | 8 % | 99,8 % | 88 / 70 ms | 0,11 / 0,19 |
| | **novo** | 204 s | **0,736** | **34 %** | 99,5 % | **33 / 48 ms** | 0,07 / 0,41 |
| VALID-2 1750–2100 | antigo | 281 s (200) | 0,692 | 9 % | 99,9 % | 83 / 99 ms | 0,11 / 0,18 |
| | **novo** | 259 s | **0,712** | **19 %** | 97,7 % | **32 / 57 ms** | 0,06 / 0,28 |

- **Margens**: vencedor da varredura (ON −38/−34 × OFF −50/−46/−42 × LEAD 0/15/30 ms × TAIL 0/20/35 ms) = **ON −38, OFF −46, LEAD 15 ms, TAIL 20 ms**: viés ~0 e erro mediano ~33 ms na entrada / ~50 ms na saída em todos os trechos (antes 70–100 ms). OFF −50 vale para faixa com gate (call/dub); no mic cru do POV ele alonga a cauda.
- **Passada de texto**: precisão por trecho 86 / 96 / 100 / 77 % (s que ela tira e ele também tirou). O caso de 77 % é um retake de verdade do POV ("só chegar aqui, a gente já conseguiu… / aqui a gente já conseguiu beber mais de 20 %") que ele manteve em parte por causa da dublagem.
- **Segurança**: bordas caindo em fala alta (> −30 dBFS no quadro do corte): novo 1 em ~780; antigo 0. As dele: ~28 %, porque cortou o vídeo por baixo da dublagem e ignorou a voz provisória.
- **Teto do que dá para aprender só do bruto**: o que ainda sobra a mais (46–68 s por trecho) é quase tudo FALA. Uma parte grande é efeito da dublagem: o roteiro foi relido, e ele cortou o vídeo por baixo da frase dublada, tirando pedaços da voz provisória (das palavras do POV que ele tirou, 52–58 % estão na dublagem). Nas falas da **call** (voz crua, decisão pura de conteúdo) o motor novo acerta 52 / 35 / 82 / 9 % do que ele tirou.
- **Ainda manual**: repetição de informação e coaching ("bebe água" ×N, número dito 2×), frase de transição que a cena dispensa, cortar a cauda da frase quando a imagem já mostrou ("tá tudo vazio"), e tudo que depende da dublagem. Ler a transcrição e completar o `remove` antes do build.
