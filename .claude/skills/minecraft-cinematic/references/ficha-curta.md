# Ficha de cena dos SHORTS (CineCam 9:16) — `cinecam/curta.py`

O produtor escreve **dados**, o PC renderiza. Um **mapa** por vídeo e uma **ficha** por cena (`n` = número da cena na linha do
tempo do Shorts; `dur` = duração EXATA da cena em segundos). As regras do canal estão no código, não na ficha:

- câmera **na altura do rosto** e **de frente** (corpo ≤ ~15° da lente; nunca 45–60°); contraplano fixo (o mesmo plano do mesmo
  personagem no mesmo lugar sai sempre igual);
- boca **parada** (sem abrir e fechar na fala), piscar sozinho, sombra de contato;
- **nada atravessa nada** (membro/item no próprio corpo é corrigido sozinho; em outro personagem, mob ou bloco a ficha é recusada);
- câmera nunca colada em personagem/mob; trancos ("rollback") recusados;
- motion blur e desfoque de lente **opcionais** (`efeitos`).

## Mapa (`<id>-cinemapa`)

```json
{"seed_mundo": 4242,
 "lugares": {
   "campo": {"bioma": "plains", "hora": 4000, "clima": "clear", "seed": 5, "raio": 20,
             "marcas": {"kadu": [0.85, 0, 14], "stick": [-0.85, 0, -14]},
             "blocos": [["arvore", -6, -9, "oak"], ["box", -3, 0, -2, 3, 0, -2, "minecraft:mossy_cobblestone"],
                        ["bloco", 2, 0, -4, "minecraft:crafting_table"], ["comando", "setblock ..."]],
             "enfeite": true, "densidade": 0.8}}}
```
- `bioma`: um dos locais catalogados (`references/sites_4242.json`: plains, desert, forest, snowy_plains, jungle, meadow…) ou
  `"site": {"x","y","z","biome"}`.
- Coordenadas do lugar: `dx, dz` em blocos a partir do centro; **a câmera fica do lado +z** (o "público"). Direita da TELA = −x
  do personagem que olha para a câmera… para simplificar: `x` positivo aparece à DIREITA da tela.
- `marcas`: onde cada um fica naquele lugar `[dx, dz, vira]`; `vira` = graus (0 = de frente para a câmera; + = vira para a esquerda
  da tela). Duas pessoas conversando: ±10–15° uma para a outra, ~1,7 bloco de distância.

## Ficha (`<id>-cine`, n)

```json
{"n": 4, "dur": 2.3, "lugar": "campo",
 "elenco": [{"quem": "kadu", "item": "minecraft:diamond"}, {"quem": "stick", "em": [-0.85, 0], "vira": -14}],
 "acoes": [
   {"t": 0.2, "quem": "kadu", "faz": "entrega", "para": "stick", "ate": 2.3},
   {"t": 0.25, "quem": "kadu", "faz": "fala", "ate": 1.8, "texto": "É seu, parceiro!"}],
 "mobs": [{"tipo": "creeper", "em": [3.5, -5], "aparece": 0.8, "anda": [[0.8, 2.0, 1.5, -2.6]]}],
 "camera": [{"plano": "fala", "quem": "kadu", "ate": 1.2}, {"plano": "reacao", "quem": "stick"}],
 "efeitos": {"blur": true, "dof": true}}
```

**elenco**: `quem` = apelido da turma (`skin` opcional se o PNG tiver outro apelido; `skin_png` = caminho), `em` = marca ou `[dx, dz]`,
`vira`, `item` (na mão direita, aparece com `segura`/`entrega`), `energia` (gesto da fala, 1 = normal).

**acoes** (`t` em segundos dentro da cena):
| faz | campos | o que faz |
|---|---|---|
| `fala` | `ate`, `texto`, `calmo` | gesto e cabeça pelo ritmo das sílabas (boca parada) |
| `pose` | `pose`, `rapido`, `esquerda` | troca de pose com antecipação (lista em `atua.STATIC`/`OSC`: point stop finger cross sus smug tilt mostra facepalm pensando abraca chora vergonha bravo ombros grita medo susto sad joinha apaixonado cochicha coca bocejo empurra sorrateiro comemora rindo palmas acena nervoso procura mine sit agacha shake nod idle) |
| `aponta` | `alvo` = personagem, `[dx,dy,dz]`, `"esquerda"`/`"direita"` (da tela) | braço esticado até o alvo (em plano de frente, aponte para o lado) |
| `entrega` | `para`, `ate` | estende o item no espaço ENTRE os dois |
| `segura` | `ate` | item na mão |
| `olha` | `alvo` (null = volta), `peso` | cabeça e um pouco do tronco |
| `vira` | `para` = `"camera"`, personagem ou graus | gira o corpo (0,45 s, com mola) |
| `pula` | `altura`, `ar` | antecipação, voo, amortece |
| `anda` | `para` `[dx,dz]`, `ate`, `modo` walk/run/auto | passada pela distância (pé não escorrega) |

**mobs**: `tipo` vanilla (creeper, zombie, pig, cow, sheep, chicken, spider, villager…), `em`, `vira`, `aparece` (s; escondido antes),
`anda` = lista `[t0, t1, dx, dz]` (passada vanilla pela distância, cada mob com o próprio modelo).

**camera** (lista de planos; `ate` = fim do plano, o último vai até `dur`):
| plano | quadro |
|---|---|
| `fala` | quem fala, médio (cintura para cima), de frente, push-in lento |
| `medio` | um pouco mais aberto |
| `reacao` / `close` | close de quem ouve / close forte (susto, punch) |
| `dois` | `quem` + `com` juntos (distância calculada para caber no 9:16) |
| `aberto` | o lugar inteiro (abre o lugar novo) |
| `segue` | acompanha quem anda/corre, na frente dele |
| `insert` | `mob` (índice, acompanha o mob) ou `alvo` `[dx,dy,dz]` + `de` (graus) + `dist` |
Opções: `push` (false = parado), `fov`.

## Uso
```python
from cinecam.curta import checar_ficha, render_fichas
checar_ficha(mapa, ficha)                     # < 1 s, sem jogo: [] = ok; senão a lista do que corrigir
render_fichas(mapa, fichas, "final" | "rascunho", ao_pronto=lambda info: ...)   # UMA sessão do jogo; pós em paralelo
```
Desempenho medido (26/10, RTX 5070 Laptop): 1ª cena ~50 s (abre o jogo), cada próxima ~14 s de jogo + ~15 s de pós em paralelo;
5 cenas (11 s de filme) = 135 s. Rascunho (540×960, sem blur/DoF) para conferir rápido.

## 16:9 — cinemáticas do vídeo longo (v1.2, 26/10/2026)
`"formato": "16:9"` na ficha ou no mapa → 1920×1080 a 60 fps, vfov 40, mesmas regras (rosto, de frente, boca parada, nada
atravessa). Campos extras no plano: `dist`, `lado`, `altura`, `mira`, `push` (blocos), `centro` (aberto), `sobe` (insert).
Efeitos: `"python": "coreo.py", "coreografia": "c06"` → `def c06(c)` com `curta.Cena` (ver SKILL.md § v1.2). Para o editor, a
ficha também leva `id`, `tl`, `dur`, `why`, `intro`, `whoosh`, `flash` (o `cinematicas.py insert` usa). Exemplo completo:
`D:\Pobrs\trolagem\cine3\make_fichas.py`.
