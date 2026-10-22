# Rodada 3 (20/10/2026) — o Matheus editou a MINHA edição completa do "Bebi toda a água do mundo"

Pedido dele: *"você editou e entregou uma versão [...] eu fiz uma leva de alterações manuais em que eu mesmo editei e melhorei muito o vídeo, compare a sua versão anterior com as minhas, com escolhas de músicas diferentes, nivelamento de vozes, cortes, zooms, movimentos, etc. Se não entender o porquê de alguma decisão, questione, analise as melhorias e melhore a skill."*

**Como li (reproduzível):** ele editou NO LUGAR a sequência "Sequencia 01 - EDICAO Claude 19-out v2" (`e6ab9379-…`, projeto `Downloads\10 - Bebi toda a agua do mundo ( Pronto pra finalizar )_1.prproj`; 1182,7 s → 1178,4 s). Minha versão = `plan.json` + `sfx_placed.json` (`examples/agua_reedit_19out/`), em tempo da "Sequência 01" (intocada, base do clone). Ponte entre as duas: tempo da FONTE (inPoint do nest "VIDEO ORIGINAL" no V1) → `examples/agua_reedit_19out/diff20/mapping.py`. Dump completo (clipes + componentes + keyframes + marcadores) com `scripts/fulldump.py <SEQ_ID> out.json` (29 s para 1.900 clipes). Diffs: `diff20/music_diff.py`, `sfx_diff.py`, `video_diff.py`, `ctx.py` (fala em volta de cada mudança), `music_lufs.py`. Saídas em `references/timeline-dele-20out/` (+ `his_v2_dump.json.gz` = a timeline dele congelada). Mix dele exportado: `D:\Pobrs\agua\his_v2_20out.wav`.

Números gerais: SFX 169 → 152 ativos (81 intactos, 36 removidos, 5 desabilitados, 25 com ganho mudado, 34 movidos, 24 novos) · zooms em V1: 96 + 8 stretch → 127 clipes com escala ≠ 100 · música: 42 faixas → 40 mantidas nos mesmos pontos, 1 nova, 2 removidas (Sadness, Cheer Up), Love Dust reduzida a 1,6 s, ~16 com ganho mudado · cortes: −23,4 s de conteúdo em 50 pontos · inserções: promo de evento (7,2 s) e tela final (10,7 s).

---

## 1. Nivelamento das VOZES (o que ele mais mexeu no áudio)
| faixa | antes (Sequência 01/minha) | dele |
|---|---|---|
| **A1 dublagem (Problems)** | 0 dB + Limitador pesado (amp 0,970 / entrada 0,747) | **−3,5 dB** + **2º Limitador pesado** (amp **0,948** / entrada **0,667**, look-ahead 0,133, liberação 0,375) — 588 clipes; trecho 11:08–11:32 a **−4,6 dB** (dublagem mais alta ali) |
| **A2 call (amigos = personagens)** | 0 dB, sem limitador | **+6 dB** + Limitador pesado (0,948 / 0,667) — 395 clipes. A namorada ("amorzinho/xoxozinho", 09:50–10:46) ficou em **−2,6 / 0 / +1,2 dB** (voz que já vem alta) |
| A3 jogo | 0 dB | 0 dB (igual) |
- Regra: **a call vinha ~6 dB abaixo da dublagem** → sobe a call e passa as duas pelo MESMO limitador (0,948/0,667) para nivelar; a dublagem desce 3,5 dB porque o 2º limitador empurra. Personagem que já grita/está alta = ajuste por clipe (−2…−9 dB em relação à call).
- **Reverberação de estúdio** num clipe da call (12:26, "fica boi, boi… só bolinha") junto de **Preto e branco + zoom 369 %** = beat de ironia antes da punchline "só 2,5% do mundo" (mesmo padrão do MineRing: ironia = P&B/reverb/zoom).
- Transições de áudio "Potência constante" 0,3 s nos cortes novos dele (A1–A3, mesmos pontos nas 3 faixas).
- Mix final dele: **−14,5 LUFS integrado, LRA 4,1, true peak +0,4 dBFS** (o meu render: −13,9 LUFS). O alvo "−18 LUFS" do teste de 15/10 não vale para o vídeo final; ver dúvida no fim sobre o pico.

## 2. MÚSICA — manteve quase todas as minhas escolhas; o que mudou foi o NÍVEL (e 2 trocas)
**O padrão escondido: ele nivela pela loudness do TRECHO da faixa, não por um dB fixo.** Eu pus −25/−26 em tudo; faixas que já são baixas na origem sumiam. Ele subiu exatamente essas:
| faixa (pasta) | LUFS do trecho | meu ganho | dele | efetivo dele |
|---|---|---|---|---|
| Expedition 13 (EPICAS) | −16…−18 | −26 | **−16,6** | −33…−35 |
| Weapon of Choice (TENSAS) | −17,3 | −26 | **−15,7** | −33 |
| That Thing Behind Us (2K25, vilão 2ª vez) | −13…−20 | −26 | **−20,6 / −14,6** | −34…−35 |
| Sneaky Town (MISTERIO) | −17,7 | −27 | **−18,1** | −36 |
| Last Level Pt. 1 (2K25) | −12,7 | −26 | −18,4 | −31 |
| Sneaky Grandma (TROLL) | −10,4 | −26 | −19,0 | −29 |
| Make No Mistakes (TENSAS) | −12…−13 | −26 | −20,2 | −32…−33 |
| Dine-o-Matic / Megapixel | −9,8 / −12,3 | −26 | −21,5 | −31…−34 |
| Lifecrash + Brighter (intro) | −9,8 | −25/−24 | −22,2 | −32 |
| faixas altas (When the Cats Away −8,8, Heroes of Speed −8, Surfer −7,7…) | | −26 | −26/−27,3 (iguais) | −34…−35 |
- **Efetivo = ganho do clipe + LUFS do trecho: mediana −35,6 LUFS (p10 −40, p90 −31).** Implementado em `scripts/music_level.py` (testado: Weapon of Choice → −15,7 dB, igual ao dele).
- **Respiro sem fala sobe +6…+9**: Speed Devil −18,9 só nos 3,4 s do time-lapse da piscina; Detective Gang −17 nos 3,8 s do time-lapse da cachoeira; Having Fun −22,8 sob o promo. Volta ao nível de cama quando a fala volta (corte no clipe, sem keyframe).
- **Clímax final (The Triumph, LEGENDARIAS)**: único com keyframe — abre a **−9 dB** (trecho de −23 LUFS = intro baixa da faixa) e desce até −20/−23 dB conforme a faixa cresce. Keyframe em música = só para acompanhar a dinâmica da própria faixa.
- **Trocas**: (a) **Your Gain (VLOGS)** ficou só 6 s (sob os takes futuros, a "esperança"); dali em diante (villagers 70 % de água, "beber água da plantação") entrou **In the Outskirts of Buenos Aires (TROLL, src 19,9 s, −24,6 dB, em A7)** por 36 s → esperança é um BEAT; quando a conversa volta a ser bobeira, volta o cômico. (b) **Love Dust (AMOR)** na cena da namorada caiu para 1,6 s e **Make No Mistakes (TENSAS)** foi antecipada para 09:51 (eu tinha posto no "parque do Brucutu", 40 s depois) e subiu para −20,2 → ver dúvida 1.
- **Sadness (TRISTE)** no "Brucutu desiste" saiu: **That Thing Behind Us** (tema do vilão) continua, subindo para −14,6, até a punchline "ele morreu" → drama de mentira do vilão não ganha música triste; o tema dele segue até a piada.
- **Speed Devil** antecipada 4 s (11:54, "tá sugando muito rápido") junto de vine boom + zoom 177 % (o meu Fullscreen Shake saiu).
- Os "cortes" internos das faixas (mesma música em vários clipes com saltos de 0,1–1,5 s na origem) são só o efeito dos cortes dele com ripple em todas as faixas — não é edição de música intencional.
- Silêncios de 1,5 s (música cala na punchline/falha) **mantidos**. Música do final (Cheer Up) saiu; o vídeo termina na tela final.

## 3. SFX — curadoria (o que saiu, o que entrou, níveis)
**Saíram (36) — padrões:**
- **TODOS os 6 "dun-dun-dun"** de entrada/retorno do Brucutu → trocados por **among-us-role-reveal** (07:14, 09:06, 13:21, 0…−6,8 dB), **danger-alarm** (18:05, −17,6), **suspense-1** (07:02), e na 1ª aparição um pacote **cinematic-boom (−5,6) + cartoon poke (0) + deep impact (−1,6)** com o nest de eco. Vilão = "impostor revelado", não fanfarra de metais.
- **original-sheesh** 4 de 5 (ficou só no "115 mil litros"), **deg-deg-sussy** ×2, **tadaa** ×3, **clown-horn** ×2, splash ×3 (robô, funil, sugando), **oof**, **sadtrombone** do "desisto", **loud-dramatic-stinger**, **vine-boom** em punchline de fala ("músculo", "Canudão!" — trocado por **guitar-riff-meme** −17), **anime-wow** do "canudo gigante" da loja, **baú** (chestopen), **levelup** "sai do time-lapse".
- **O ÚNICO Villager** também saiu (mesmo com os personagens falando de villagers) → **Villager = nunca**.
- **Pares redundantes**: toast + levelup juntos na conquista final (saíram os dois), 2 toasts seguidos (saiu um), boing + burp em "virou uma bola" (desabilitou os dois: a piada já tinha boing/peido 30 s antes).
- **Entraram (24)**: alert-sound ×2 (01:25 "até esvaziar toda essa poça", 04:54 "tô gigante"), whoosh longo ×2 (entrada/saída do promo), bonk ×2 (punch-ins novos), **one-piece-corneta + toing** ("quer que eu te carregue no colo?" — deboche romântico), levelup ×2 (sair da loja/"sugamos toda a piscina"), vine boom (Speed Devil), **zoom-impacto + impacto.wav** no "precisa de 150 mil litros" (zoom 359 % no requisito), cartoon poke na morte do Brucutu (antes do WASTED).
- **Níveis** (agora em `GAIN_DB`): toast de compra **−11…−14** (eu −6) · splash **−12** · **bruh −10,6** e **sudden-suspense −11** (ele SUBIU: os −18/−22 de 15/10 sumiam) · metal-gear −7,8 · wrong_5 −8 (−14,8 quando o zoom de 601 % já carrega o peso) · bonk −3…−9 · record scratch −12…−17 · anime-wow −15…−19.
- **Posição**: os que ele moveu foram para o **início do segmento/corte** (−0,3…−1,7 s: spongebob, shine, peido, record scratch, bruh) — confirma "SFX nasce no corte" de 15/10. Spongebob-fail esticado (2,5 → 3,3 s: deixa o fail terminar).

## 4. Zooms e movimentos
- **Abertura**: zoom-OUT **300 → 100 % em 1,5 s** (Bézier) + White Flash (Tonalidade 70→0 em 0,9 s). Eu deixava 100 %.
- **Curva**: os zooms que ele refez têm só **2 keyframes Bézier**: saída rápida (velocidade ~124, influência 14 %) e chegada com influência **100 %** = o mesmo ease-out "rápido que decai" (meus 7 keyframes aproximavam isso; ele manteve vários). Alguns ele fez mais longos e maiores: item **100→300 % em 1,0 s** com Âncora animada para centralizar o item (chapéu de líquidos), 100→278 % em 1,8 s (boia), 100→241 % em 0,78 s (capacete), 100→207 % em 1,7 s (draga), tensão **100→220 % em 0,6 s indo para o HUD** ("a nossa água tá abaixando?"; eu: 130 % em 1,2 s).
- **Push-in lento de cena**: 100→267 % em 4,8 s depois dos takes futuros; 109→125 % em 6,6 s sob o "só 2,5% do mundo" (junto de Red Flash + Impact Shake).
- **Número que pesa**: "apenas 0,1%" virou **zoom 601 % no contador**, Âncora tremendo (5 keys) + Impact Shake + Red Flash; "precisa de 150 mil" = **359 % no lugar do texto** + zoom-impacto + impacto. "foram mais de 20 litros" (fala da dublagem) **cortada**: no lugar, o HUD em V2 (zoom 230 % + flash) com o orb → **mostrar o número em vez de falar o número**.
- **Punch-ins novos (~30) — em REAÇÕES e falas de personagem**: "Que palhaçada é essa?" (183 % + Impact Shake), "quer que eu te carregue no colo?" (209 %), "Imenso. É, imenso pra você, né?" (267 % no outro personagem, à direita), "Aquele deve ser muito melhor… Brucutu" (**626 % no objeto distante citado**), "Droga, não aguento mais encher piscina" (335 %), "Bora buscar uma água nova" (270 %), "Fica quieto, Naniaco" (234 %), "Isso, Brucutu. Suga água do mundo" (321 %), "ele morreu" (246 %) etc. Faixa 158–369 %.
- **Zooms meus que ele tirou**: item da loja quando o item NÃO está enquadrado/ainda não apareceu ("copo d'água nível 1" 300 %, "funil gigante" 280 %, "robô mergulhador" 280 %, "de verdade" 125 %), "custa 1.500" (230 %), "beber a água da plantação" (240 % → 158 % no clipe seguinte). Ver dúvida 2.
- **Efeitos**: Red Flash saiu de "Por que a gente não consegue beber nada?" e de "Os mentirosos da piscina!" (ficou nos números/perdas: 0,1 %, 2,5 %, 100 % de novo, rio bloqueado, Brucutu chega). **Fullscreen Shake (meu) → zoom 177 %** (regra "sem shakes de tela cheia" confirmada). Impact Shake (Transformar) só em punch-in de reação/impacto. VHS + stretch 391×258 nos deboches (iguais). Stretch novo **354×272** no "é devagar" (falha do copo). **WASTED.png saiu** (ficou o som + VHS + zoom 294 %) → **nada de sticker PNG**.
- **Revelação do vilão (04:00)**: ele aninhou 1,47 s ("olha aquilo ali") numa sequência com **eco** (cópia em cima, opacidade 48→0, escala 100→1122 %, mesclagem) a 261 % + cinematic boom + cartoon poke + deep impact. Variante do "eco em V4" da rodada 2.

## 5. B-roll e inserções
- Mantidos: os 3 B-rolls de abertura/revelação, os 5 takes futuros com flashback, os 2 time-lapses (a hipótese das vagas estava certa).
- **Novos (CineCam, pedidos por ele hoje)**: closes da barriga d'água (Patão em V4 01:04,75, Problems em V3 01:06,88: "olha o tamanho da pança") e **poça seca com o peixe** (V2 01:26, "até esvaziar toda essa poça d'água"). Gag físico/consequência citada = mostrar com B-roll (plano aberto da situação).
- **Promo de evento no meio (03:03, 7,2 s)**: `Downloads\até dia 31.mp4` ("Próximo encontro — Curitiba-PR, 31/10, 14h, Livrarias Curitiba"), no fim do 1º ato (depois da 1ª compra, antes de testar o copo). Transição: **Impact Shake de saída** (Transformar posição 0,43 s + 4× Espelho + escalas 125/80 % = bordas espelhadas) no último clipe antes e no 1º depois, **whoosh longo** −8,5 dB nas duas pontas, música sobe para −22,8 sob o promo, White Flash na volta. Ver dúvida 3.
- **Tela final (10,7 s)**: últimos 10,7 s de `Downloads\Me Tornei o MESTRE do BALL VS BALL no Minecraft.mp4` ("VEJA MAIS VÍDEOS NO CANAL", arte da turma) logo depois do "Então é isso, tchau". Ver dúvida 4.

## 6. Cortes
- −23,4 s em 50 pontos, mesmo sobre a decupagem DELE: pausas residuais 0,03–0,6 s (a do "canudinho aqui?" → "Você é maluco?", 0,28 s), **interjeições da call** ("Bora.", "Tu achou", "Eu coloquei 1.500", "É,", "Tá"), **palavras repetidas** ("Olha o tamanho", "Olha só o", "É isso aí, Chico, é isso aí"), a fala da dublagem que só lê o HUD ("foram mais de 20 litros" — trocada pelo zoom no HUD), "Imagina", "Chique" solto, um "hein / isso / Não".
- **Palavrão da call ("se fudindo") foi CORTADO**, não bipado (meu bipe em A9 saiu) → canal infantil: cortar a palavra/frase; bipe só se não der para cortar sem quebrar a fala.
- Acrescentou de volta 3,8 s de fonte em 13:03 (cachoeira) e 0,5–0,6 s em 3 lugares (respiro de imagem).

## 7. O que ele NÃO mexeu (aprovado)
Estrutura de música por cena (40 de 42 faixas nos mesmos pontos), silêncios de 1,5 s, B-rolls de abertura, takes futuros + flashback + orbs, time-lapses, VHS/stretch nos deboches, Red/Green/White Flash na maioria, 52 de 95 zooms meus iguais (punch-ins 230–250 %, contadores 230 % com posição y 1,15), sparkle/tilt, mutes de A2/A3 sob B-roll.

## 8. Dúvidas enviadas a ele (20/10) — RESPOSTAS no fim
1. **Cena da namorada (09:50–10:46)**: trocou Love Dust (romance) por Make No Mistakes (TENSAS) mais alta. É porque a namorada leva eles pro parque do Brucutu (armadilha), ou o romântico ficou brega?
2. **Zoom no item da loja**: tirou "copo d'água nível 1", "funil gigante", "robô mergulhador". Regra = só dar zoom quando o item está enquadrado na tela (senão o zoom mostra o nada)?
3. **Promo "até dia 31"**: vai ter promo em todo vídeo? Sempre ~3 min / fim do 1º ato? Onde pego o arquivo da vez?
4. **Tela final**: são sempre os últimos ~10,7 s do vídeo anterior (BALL VS BALL)? Existe um arquivo fixo de end card?
5. **Pico +0,4 dBTP no mix**: é proposital (o YouTube abaixa) ou falta um limitador no master?
6. **Música por loudness**: confirma que subiu Expedition 13 / Weapon of Choice / That Thing Behind Us porque essas faixas são baixas na origem?

### Respostas dele (20/10/2026)
1. **Namorada**: "o romântico ficou brega; se fosse uma que encaixasse melhor eu teria mantido" → música romântica é permitida, mas a faixa tem que ser boa (Love Dust não serve); na dúvida, um tema leve/suspeito (Make No Mistakes) em vez de romance meloso.
2. **Zooms**: "estava atrasado e não fiz mesmo, mas tirei porque os seus zooms estão TODOS indo sempre pra mesma direção, e não vão na direção do objeto ou do que é mencionado". Medido: dos meus 96 zooms, **65 no foco fixo 960,560, 18 no HUD 960,0, 13 em 900,1010** — só 3 direções. Os dele vão até o objeto (0,64/0,60; 0,87/0,57; −0,05/1,18; Âncora animada até o item). → **REGRA: todo zoom tem foco conferido por FRAME** (`scripts/zoom_focus_sheet.py` gera o frame com grade 1920×1080; eu olho e anoto fx,fy do objeto/personagem citado). Sem foco conferido, sem zoom. Ele não refez todos os que tirou (faltou tempo): a intenção era ter zoom ali, mas no lugar certo.
3. **Promo**: sempre o arquivo `C:\Users\mathe\Downloads\até dia 31.mp4`, **por volta dos 3 min, onde houver uma pausa/respiro** (fim de cena, antes de uma nova ação).
4. **Tela final**: usar esse mesmo arquivo cortado (`Me Tornei o MESTRE do BALL VS BALL no Minecraft.mp4`, in 1234,116 s, 10,7 s).
5. **Pico +0,4 dBTP**: "faltou de leve" → conferir true peak ≤ −1 dBTP no render e corrigir (limitador no master/saída) antes de entregar.
6. **Música por loudness**: confirmado ("sim") → regra 5b + `music_level.py` valem.
