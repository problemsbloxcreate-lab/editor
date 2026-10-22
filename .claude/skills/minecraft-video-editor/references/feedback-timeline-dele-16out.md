# Feedback 16/10/2026 (rodada 2) — o Matheus editou DE NOVO a v14 e eu li a diferença

**O que comparei:** a sequência viva "v14 - TESTE 5min takes futuros" (id `b081148b`, agora 137,487 s) × o clone da rodada 1 "(ref) v14 editada pelo Matheus 15-out" (`41c1f242`, 137,771 s). Snapshot desta rodada: clone **"(ref2) v14 editada pelo Matheus 16-out"** (`2bea56b2-fd56-40f2-9235-7c2ea7320533`, no `Teste Problems.prproj`). Dados: `timeline-dele-16out.json`. Método: dump completo (componentes + keyframes) das duas, diff por TEMPO DA FONTE; frames exportados do clone (nunca da sequência dele — `setInPoint` mexe na work area).

**Escopo:** TUDO o que mudou está em **0–36 s** (a intro e o momento da poça). Dos 36 s ao fim está idêntico à rodada 1 (zooms, presets, SFX, música, mutes). A 2ª metade do vídeo continua sem revisão dele.

## 1. A grande novidade: B-ROLL CINEMÁTICO por cima do jogo (V3/V4)
Os 3 vídeos novos são **renders do CineCam** (skill `minecraft-cinematic`: `D:\cinecam-out\…`, 1920×1080 60 fps, **vídeo-só**). Ele os importou e pôs em V3 ilustrando a frase:

| tl (s) | clipe (trecho usado) | frase que ilustra | tratamento |
|---|---|---|---|
| 1,235–5,239 (4,0 s, partido em 2 no 3,837) | `takes_futuros_oceano` 0–4,0 | "(eu,) Patão e Chique, vamos beber toda a água do mundo" | V3 puro; na 2ª metade, **eco em V4** (abaixo) |
| 9,409–10,761 (1,35 s) | `universo_canudo` 0,83–2,19 | "Beber toda a água do mundo com esse…" (corta pro rosto/"canudinho aqui?" com a distorção que já existia) | V3 puro |
| 32,733–35,719 (3,0 s) | `pa_rasante_plongee` 3,59–6,57 | "só o tanto de poça d'água que tem aqui na frente" | V3, **reenquadre** posição `[0.5, 0.266]` + escala **150,8** (motivo não dito por ele), **Tonalidade branco→branco 70→0 em 0,9 s** (lavagem branca que some = revelação) |

- **O B-roll termina exatamente onde o zoom do item começa** (5,239 = fonte 6,38 = "usando"); ele cobre a tese e entrega pro item.
- **Eco (V4)** na 2ª metade do oceano: cópia do mesmo trecho, opacidade **42,3→0 em 0,27 s**, escala **100→462 em 0,95 s**, modo de mesclagem **14** (clareia, tipo Tela/Adição — o 14 é o valor interno do Premiere; no builder `echo.blend`). Dá o "soco de luz" no meio do plano.
- **Mutes sob o B-roll de abertura:** A2 (call) 1,80–5,82 e A3 (jogo) 0–5,82 DESABILITADOS (o B-roll não tem som de jogo e a fala do Matheus não existe nesse trecho); A1 (voz principal) intacta. Mesmo padrão da rodada 1 (mute do que disputa), agora também para "o som do jogo que não bate com a imagem".
- Builder: stage `b6h_brolls` + `b6i_flash` (`plan['brolls']`) — testado em clone descartável (V3/V4, keyframes de opacidade/escala, Tonalidade com as MESMAS cores dele `0xFF00FF00FF00FF50`).

## 2. Pacote de SFX do B-roll (arquivos que ELE trouxe — já em `library/sfx/` e na tabela `GAIN_DB`)
| tl | arquivo | ganho | nota |
|---|---|---|---|
| 0,85 (dur 1,89) | `19--Whoosh 39.wav` | 0 dB | **0,385 s antes** do B-roll (1,235) |
| 1,42 e 2,00 (0,8 s cada) | `minecraft_click.mp3` ×2 | **+10 dB** | cliques de UI na abertura (hipótese: marcam o HUD/legenda "100% de água no mundo" que aparece; não confirmado) |
| 1,67 (dur 3,82) | `fortnite-shield-potion…mp3` | −4,4 | "poção/beber" sustentado sob o B-roll de abertura |
| 9,29 (dur 1,84) | `minecraft-drinking-sound-effect.mp3` | −4,6 | gole **0,12 s antes** do B-roll do canudo (9,409) |
| 9,38 (0,26 s) | `nintendo-switch-error.mp3` | −3,3 | NOVO dele: bipe de erro junto da dúvida ("toda a água do mundo com esse canudinho?"); mesmo ganho de antes |
| **32,733** (todos no 1º quadro do B-roll) | `bass-impact.mp3` 0 dB (3,1 s) + `impact_water.mp3` −10,5 (2,3 s, som do Roblox) + `19--Whoosh 39.wav` 0 dB (1,9 s) | | revelação das poças = **3 camadas juntas** |
- `anime-wow (1)` do item ("canudinho", 5,24): **−10,4 → −17,0**. Com whoosh/clique/poção/boom por perto, o wow tem que ficar mais baixo. `vine-boom` (3,77) só trocou de trilha (A5→A6) — provavelmente para não sobrepor o `anime-shine`/novos na mesma trilha (hipótese).
- Janela 0–6 s agora tem **~7 camadas** de SFX (shine, whoosh, 2 cliques, poção, vine-boom, wow): a abertura é DENSA; a regra "1 SFX a cada 7 s" vale para o corpo do vídeo, não para o gancho.

## 3. Cortes finos (−0,284 s no total)
- **Zoom do item (canudinho 100→650 %)**: o clipe do item agora começa na fonte **6,22** (era 6,96) — **0,16 s antes de "usando"** (6,38), a palavra que apresenta o item, e não em "canudinho" (7,30). Regra: **o corte para o item cai ANTES da frase que o apresenta**; a animação (1,5 s) acompanha "usando esse canudinho".
- Aparou **0,28 s** (fonte 11,68–11,96) antes de "Beber toda a água do mundo": respiro/pausa curta antes de frase-chave sai. (Reforça "silêncio zero"; o meu `tighten2` deixou passar 0,28 s ali.)
- Música: a Lifecrash foi cortada junto com o vídeo em 9,54 (o pedaço de 1,22 s que sobrou com o fade antigo é artefato do ripple, não intenção).

## 4. O que NÃO mudou (confirma a rodada 1)
Zooms de 100→230/250 % com ease-out e hold, presets, "Distorção ondulada + Lumetri + Ruído + Entalhe de cor" nos clipes de incredulidade, stickers, mutes de 30–38 s, música por clima: iguais. SFX continuam com **ganho fixo, sem keyframe** (os novos dele também).

## 5. Como aplicar (checklist para uma próxima edição)
1. Antes de montar: para cada **tese/frase-promessa** ("vamos beber toda a água do mundo") e cada **revelação visual** ("só o tanto de poça"), perguntar se vale um **B-roll do CineCam** (skill `minecraft-cinematic`; 1,3–4 s; render de 3–7 s, usar `off`). Sem render pronto, propor o plano de câmera e pedir o OK dele — não inventar sem o mod/mundo.
2. `plan['brolls']`: entrada na hora da frase (ou ~0,3 s antes), saída onde o próximo efeito assume (zoom do item/corte); 2 pedaços se passar de ~3 s, com `echo` no 2º.
3. `plan['mutes']` sob o B-roll (A2/A3); voz A1 nunca.
4. SFX de pacote: whoosh 0,1–0,4 s ANTES do B-roll; na revelação, impacto grave + splash + whoosh NO 1º quadro; gole/ambiente sustentado quando o B-roll mostra beber; `flash` (Tonalidade 70→0 em 0,9 s) só em revelação.
5. Item citado: corte p/ o item **antes** da frase que o apresenta.
6. Verificar: exportar do CLONE e olhar frames dos 3 pontos; `sfx_audit.py`.

## 6. Limites do que li
- Eu NÃO ouço: nível/música/SFX seguem sendo apostas; o que vale é o que ele deixou.
- Os motivos do reenquadre 150,8 % da plongée e dos cliques +10 dB são hipóteses.
- Os 3 B-rolls vieram de renders meus anteriores (`D:\cinecam-out`); não sei se ele pediria outros planos (ex.: B-roll na 2ª metade).
