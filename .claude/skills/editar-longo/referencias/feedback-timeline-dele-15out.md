# Feedback 15/10/2026 — o Matheus EDITOU a v14 e eu li a timeline dele (padrões e decisões)

Mensagem dele: *"olha a timeline aí, fiz umas melhorias muito melhores, primeiro que você fica colocando keyframe nos efeitos sonoros, para com essa merda. Vê minhas melhorias aí, só diminuí o tempo porque tô com preguiça de corrigir suas merdas no bagulho todo; alguns sfx que você tinha colocado tavam em excesso, som de villager toda hora, uns tavam nada a ver. Reveja com atenção minhas mudanças, entenda os padrões e as decisões e atualiza a skill, melhora aí."*

**Como li:** ele editou a PRÓPRIA sequência "v14 - TESTE 5min takes futuros" no lugar (300,7 s → **137,8 s**: ele só apagou o final por preguiça, então a 2ª metade — vila/loja — NÃO foi revista por ele; as regras abaixo valem para ela também, mas não foram validadas ali). Fiz um **clone** dela ("(ref) v14 editada pelo Matheus 15-out", id `41c1f242-e5bb-4d7e-89d6-2f095fabf5ca`, salvo no projeto) e exportei `D:\Pobrs\v15\his_v14.mp4` (−18,0 LUFS, true peak −1,8 dBTP). Dados estruturados: [`timeline-dele-15out.json`](timeline-dele-15out.json). O diff automatizado é `scripts/timeline_diff.py` (use sempre que ele mexer numa sequência).

## 1. Keyframes: NUNCA em SFX
- Meus SFX tinham envelope (−51 dB → ganho em 10 ms → ... → −51 dB). Os que ele não tocou ainda estão assim (vine-boom, bonk@36.9, burp, huh, orbs). **Todos os que ele mexeu/colocou têm ganho FIXO no clipe, sem keyframe e sem fade** (e os clipes novos de música dele também: estáticos, sem fade).
- Builder agora: `setTimeVarying(false)` + `setValue(g)`; **sem fade**. O orb do XP (clique de 1 ms) ganhou o fade-in de 10 ms **dentro do mp3** (`mc_sounds_extract.py --ladder`), então não precisa de keyframe. Música: ele manteve meus fades de música onde não mexeu; os trechos de música dele são estáticos — preferir estático também.

## 2. Volumes: eu tinha passado do ponto (v14b ficou ALTA, não só "audível")
Ganho de clipe (dB do Premiere) que ele deixou, vs. o que o meu builder tinha aplicado:

| SFX | meu v14 | dele | | SFX | meu v14 | dele |
|---|---|---|---|---|---|---|
| anime-shine-2 (abertura) | +0,9 | **−6,9** | | cartoon-boing | +1,3 | **−2,3** |
| anime-wow (1) | +2,0 | **−10,4** | | clown-horn | −4,9 | **−19,8** |
| bamboo-hit (bonk) | −1,5 | **−10,7** (deixou um a −1,5) | | anvil | −0,3 | **−10,8** |
| record-scratch | −2,2 | **−17,0** | | wrong_5 | −2,2 | **−8,1** |
| sudden-suspense | −8,2 | **−22,3** | | bruh | −4,6 | **−18,0** |
| nintendo-error | −2,3 | **−3,2** | | spongebob-fail | −2,2 | **−15,3** / **−20,0** |
| mc-drink | +0,5 | **−5,5** | | fart | — | **−8,6** / **−12,3** |
| vine-boom | −7,1 | −7,1 (manteve) | | burp | +0,8 | +0,8 (manteve) |
| orbs XP | +7 | +7 (manteve) | | anime-shine QP4 | — | **−7,3** |

- Descida média de **~10 dB** nos longos/brickwalled (fail, buzina, bruh, scratch, suspense, wow/shine); impactos curtos (vine-boom, burp, orbs, bipe de erro, boing) ficaram.
- No render dele: **pico do SFX = pico da fala +0…+3 dB (mediana +2,5)**, impactos +3…+6 dB (vine-boom +4,9, bonk +6, boing +5,8, orbs +6); RMS final do SFX −21…−36 dBFS (fala ≈ −20). Integrado −18,0 LUFS.
- A "faixa dos −22 dB é a média" do feedback anterior era o **valor do clipe no Premiere** (v13). A média dele agora é **≈ −10 dB** (−2…−22 conforme o arquivo). Meu erro foi o oposto na rodada seguinte: normalizar por RMS (−15…−24 dBFS) deixou os SFX por cima da voz.
- Tabela por arquivo agora em `scripts/sfx_levels.py` (`GAIN_DB`); arquivo novo: RMS ativo −25 dBFS (≤0,9 s) / −31 (>0,9 s), teto de pico −5. `sfx_audit.py` alvo ajustado: delta de pico mediano ≈ +2…+3 dB (não +5).

## 3. Quais SFX ele tirou / quais manteve (padrão de curadoria)
Densidade: mantive 35 SFX no mesmo trecho; ele ficou com **25 (20 + 5 orbs)** → ~**1 SFX a cada 7 s** fora os orbs (gancho dos 12 s iniciais continua denso: shine, vine boom, wow, bonk, scratch, suspense).
- **Tirou/silenciou (excesso / "nada a ver")**: TODOS os Villager (hmm em "olha o tamanho da pan", hurr em "na vila", hmm em "villagers vão ajudar"), os 2 "huh" (cat huh e ceeday: **desabilitou** o clipe em vez de apagar), o wow de "é verdade" (volume −68,8 dB = mudo), a pilha de erros do obstáculo (windows-xp-error + wrong_5 + oof + nintendo; mantém só 1 bipe), bonk em "Isso, bebe água", 2 dos 3 goles, "oof".
- **Manteve (reforça estrutura/punchline)**: sting + vine boom na tese ("toda a água do mundo") · wow no item citado ("canudinho") · bonk + record scratch + suspense na virada "canudinho aqui?"→"Exatamente" · **fail na pergunta/punchline** (spongebob em "por que a gente não consegue beber nada?" e em "0,1% de toda a água do mundo") · **bigorna + wrong_5 em "apenas 0,1%"** · boing/burp/buzina nas piadas de barriga · bruh no "Furada" · orbs nos takes futuros · 1 gole.
- **Regra**: SFX só onde acontece algo (tese, item citado, virada de clima, fail/punchline, número que pesa, piada física). Nada de "SFX de pergunta" genérico, e **Villager só quando um villager aparece/fala de verdade, no máx. 1×/vídeo** (antes: "toda hora"). Não repetir o mesmo som perto (no mesmo bloco de ~30 s só 1 gole, 1 huh...).
- **Adicionou**: **peido** ×2 (`perfect-fart-sound-effect-hd_128k`, em "Eu não consigo beber" e logo após "você tá ficando grávido") e **anime-shine QP4** (revelação, §5). Humor físico/de barriga é bem-vindo.

## 4. Onde o SFX cai: NO CORTE (pré-roll 0–0,1 s), não no meio da palavra
Posição relativa ao corte do vídeo mais próximo: shine 0,00 · bonk +0,00 · scratch +0,15 · bipe −0,07 · spongebob +0,00 · bonk(36.9) −0,06 · burp +0,00 · anvil +0,00 · bruh −0,10 · orbs nos cortes dos takes · buzina −0,28 (antecipa o corte). Eu ancorava na palavra (+0,5…+3 s depois); ele **arrastou cada um p/ o início do segmento** (boing −3,0 s, drink −2,2 s, burp −1,3 s, buzina −0,9 s, bruh −1,6 s, spongebob −1,2 s). Builder: `sfx[{cut:true, pre:0.06}]` encosta no corte mais próximo (±1,5 s). Sem corte por perto = na palavra.

## 5. Efeitos NOVOS que ele criou (receitas implementadas em `build_edit3.py`)
- **Revelação/"sparkle"** (tl 62,0–63,2, entre "tô esvaziando a poça" e "Patão, eu acho que você só não reparou uma coisa"; ele **reaproveitou 1,2 s mudos de bruto que eu tinha cortado** — fonte 100,47–101,67, o plano da poça — como a batida da revelação): push-in lento **100→122 % em 1,2 s** + efeito **Brilho cintilante** (`AE.Impact_Glint_FX`: Intensidade 49,3 · Apenas destaques 41 · Especular 7 · Posição 0,50/0,46 · Difusão 128 · Brilho 100 · Área do brilho **6→19,2** · Ângulo 372,5 · Forma 11 · Colorir 93 · Variação de cor 13 · Aberração 37) + SFX **anime-shine QP4** + **troca de música** na mesma batida (Mitch the Snitch). Plano: `fx` (push-in) + `reveals[{kind:'sparkle'}]` + `sfx` + `music`.
- **"Tilt/murchar"** (tl 78,3, em "vocês são tão barrigudos…", 2,1 s): o quadro **encolhe 100→71 %, gira 0→−3,2° e dessatura 100→27 %** (fundo preto aparece), pivô no centro (âncora 0,75/0,5). Plano: `reveals[{kind:'tilt'}]`. A música cômica (Happy Shortcut) entra ~2 s depois.
- **VHS (Lava's VHS) vai na falha**: tirou da frase cortada e pôs em "por que a gente não consegue beber nada?" junto do spongebob-fail (o VHS 11,04 + bonk + scratch ficou). Zoom lento daquela frase foi removido (o VHS é o efeito).
- Ele usou o nested sequence só como ferramenta de aplicar escala/rotação/brilho; **não precisa de nested**: o builder faz direto no clipe (testado: frames idênticos em feel).

## 6. Mutes: DESABILITA clipes das faixas de call/jogo que atrapalham a piada
12 clipes (**desabilitados, não apagados**): **A2 (call)** em 31,0–33,3 · 33,4–37,0 ("Calma aí") · 37,2–38,4 ("Calma aí, não bebe ainda não") · 46,7–48,5 ("Aqui também") · 78,3–80,5 ("olha vocês") · 93,5–96,5 ("oi") · 96,5–99,0 · 99,0–100,8; **A3 (jogo)** em 63,2–68,2 · 68,2–68,3 · 70,5–72,7 · 72,7–73,1 (zona do boing/peido/burp sob a música suspeita). **A1 (voz principal) nunca**. Regra: onde a voz principal faz a piada/frase de efeito e a call/jogo fala por cima (interjeições curtas, "oi", "calma aí") ou o jogo suja o gag, desabilita o clipe inteiro daquele segmento. Builder: `mutes:[{track:1|2,a,b,why}]` (índice 0-based: 1 = call, 2 = jogo).

## 7. Música: trocou as minhas apostas (CLAP) por escolhas dele, mais baixas e sem automação
| tl | faixa (pasta Epidemic) | clima | nível |
|---|---|---|---|
| 0–1,8 / 1,8–11,0 / 12,6–25,7 | Brighter than the Sky · Lifecrash (MUY ANIMADAS) · Sleepy Sneaky Sway (2K25) | (já dele) | meus keyframes |
| 28,4–37,0 | Festive Riot (TROLL) | caça às poças, cômico | meus keyframes (−15,9→−19,4) |
| 37,0–62,2 | **When the Cats Away** (NUEVAS 2K24, src 5,0) | corrida de beber | meus keyframes (−20,6→−23,6) |
| 61,7–78,3 | **Mitch the Snitch** (MISTERIO, **src 44,4**) | desconfiança/barriga — entra na revelação (sparkle) | **estático −26,9** |
| 80,3–107,9 | **Happy Shortcut** (TROLL) | piadas de barriga/contagem | **estático −26,5** |
| 107,6–121,0 | **The Olive Branch** (TROLL) | decepção→esperança (pós "apenas 0,1%") | **estático −24,9** |
| 118,9–137,8 | **Your Gain** (VLOGS, src 10) | esperança/"Furada"+takes futuros+vila | meus keyframes (−19,9→−23,4) |
- Pastas que ele usa por clima: **TROLL** (cômico/gag/decepção), **MISTERIO** (desconfiança/revelação), **VLOGS** (esperança/exploração), **MUY ANIMADAS** (intro enérgica), **NUEVAS 2K24** (corrida/ritmo). Escolher DENTRO dessas pastas (índice CLAP cobre; as faixas dele não eram minhas top-1).
- Música entra no corte (−0,3…+0,0 s) e **muda junto com o efeito** (sparkle→suspeita; tilt→gag; "Furada"→esperança). Cama dele **−25…−27 dB** de clipe (≈ 4–7 dB abaixo do que eu punha); trechos de 15–25 s; ele escolhe a seção da faixa (Mitch a partir de 44,4 s).

## 8. Cortes que ele fez (afinou ~16,6 s a mais que o meu plano; falas repetidas, não ritmo)
Tirou: coaching repetido ("Isso, bebe água… bebe água de canudinho, vai. Isso.", 4,9 s) · 2ª/3ª tentativa de beber ("Por que que eu tô tomando? bebe água", "Eu não consigo", "nível procura 6", "falei esse ah véi", 6 s no total) · "maneiro" + vazio (0,6 s) · "tá bebendo água?/É, eu estou." (1,3 s) · restos de 0,2–0,6 s. ("olha ele tá barrigudo também" ficou: é o clipe do tilt, só com a call desabilitada.) Mantém **uma** tentativa de cada ideia (o fail + a reação), não a repetição. Isso é o "tighten por conteúdo" que o motor ainda não faz: repetições da MESMA ideia/frase (≥2 ocorrências de "bebe água", "por que a gente não consegue...") → manter só a melhor.

## 9. O que ele NÃO mexeu (aprovado implicitamente)
Cortes e hand-offs da 1ª parte, zooms (650 % no canudinho + spotlight, punch-ins 239–254 %, contadores 230–250 % com ease-out), VHS 11,04, White Flash na abertura, **takes futuros + flashback sépia/Lumetri + orbs** (5 takes em V2, tudo igual), Red Flash + Impact Shake no "0,1%", sting da abertura, intro Brighter→Lifecrash.

## 10. Lições de processo
- Ele edita no lugar → **clonar antes de ler/exportar**; markers rippam com as exclusões (marcadores depois do fim ficam).
- Eu não ouço: a verdade está nos **valores que ele deixou**. Depois de cada rodada dele: `python scripts/timeline_diff.py <SEQ_ID> <plan3.json>` e atualizar `GAIN_DB`/regras.
- A 2ª metade (loja/vila, 137–300 s) continua do meu plano antigo: regerar com as regras novas antes de mostrar (menos SFX, Villager ≤1, ganhos da tabela, SFX no corte, mutes onde call/jogo atropelam).
