# job.json e camera.csv (contrato Python ↔ mod CineCam)

Normalmente você NÃO escreve isso à mão: `cinecam.render()/stills()/scout()` geram tudo. Documentado aqui para depurar.

## camera.csv
Cabeçalho: `t,x,y,z,yaw,pitch,roll,fov`. Uma linha por **render pass** (= frames × subframes).
- `t` segundos (relógio do filme, monótono). A diferença entre linhas vira o avanço do relógio do jogo (nuvens, água, mobs).
- `x,y,z` posição da lente em blocos (mundo). `yaw/pitch/roll/fov` em graus (convenção Minecraft; fov vertical).
- As linhas de um mesmo frame são amostras dentro do obturador (motion blur): o mod faz média **em luz linear**.

## job.json
```json
{
 "name": "intro", "out": "D:/cinecam-out/intro",
 "width": 1920, "height": 1080, "fps": 30, "subframes": 8,
 "ffmpeg": "ffmpeg", "codec": "lossless",
 "world":   {"mode": "fresh|copy", "seed": 123, "preset": "normal|flat", "structures": true, "copyFrom": "C:/…/saves/Meu Mundo"},
 "settings":{"renderDistance": 16, "simulationDistance": 8, "worldTicks": true, "gamma": 0.5, "mipmap": 4,
             "biomeBlend": 7, "clouds": true, "particles": true},
 "scene":   {"time": 6000, "weather": "clear|rain|thunder", "anchor": [x,y,z], "settleTicks": 100,
             "preloadTimeoutSec": 300, "commands": ["fill …", "place structure …"]},
 "scout":   {"maps": [{"name":"a","x0":-128,"z0":-128,"x1":128,"z1":128,"step":2,"generate":false}],
             "queries": ["locate structure #minecraft:village"]},
 "camera": "camera.csv"
}
```
- **world.mode=fresh** cria `saves/cinecam-<name>`. **mode=copy** copia o save indicado (o original nunca é aberto).
- **anchor**: onde o espectador invisível fica; os chunks carregam ao redor dele (raio ≈ renderDistance×16 − 16). O mod avisa se o caminho da câmera sai desse raio.
- **commands**: executados como op (permissão 4) após os chunks carregarem. Útil: `place structure minecraft:village_plains ~ ~ ~`, `fill`, `setblock`, `summon`, `data merge`, `gamerule`. O jogo roda com `doDaylightCycle/doWeatherCycle/doMobSpawning/randomTickSpeed=0` e o relógio sob controle do mod.
- **worldTicks=false**: mundo congelado (stills, arquitetura). **true**: o relógio avança com o filme (nuvens, água, partículas, entidades do cliente).
- **scout**: sem filmar (`-Pmode=scout`) grava `<name>_scout_<mapa>.json` (alturas surface/ground/floor, cor do bloco, bioma) e `<name>_queries.json` (saída de `/locate`). `generate:true` força gerar chunks não carregados (lento, síncrono).

## Saídas
- `out/<name>_master.mkv` — master **lossless RGB** (libx264rgb qp0). Pós-processo (cinecam.post) gera `out/<name>.mp4`.
- `out/<name>_report.json` — `ok`, `rows/rowsRendered`, `passes/retries/maxWait` (esperas por chunks), `filmSeconds`, `warnings`.
- `stills`: `out/stills/frame_0000.png …` (uma por linha do CSV).
- Log do jogo: `D:/cinecam-run/jobs/<name>/game.log` (linhas `[cinecam]`).

## Fluxo interno do mod (fases)
TITLE → WORLD → SETUP (gamerules, spectator, teleporta ao anchor) → PRELOAD (espera chunks) → COMMANDS (commands + scout) → SETTLE (espera malha de chunks) → FILM → FINISH.
FILM: cada iteração do loop do jogo = 1 pass: pose da linha *i* aplicada via `ViewportEvent`, relógio `FixedTimer`, espera até a fila de chunks esvaziar (2 passes estáveis na 1ª subamostra), lê o framebuffer, acumula em linear, manda para o ffmpeg.

## Gotchas conhecidos
- RAM: Minecraft + gradle pedem ~4–5 GB livres. Feche apps pesados; o `render()` avisa se há < 2,5 GB.
- C: está sem espaço: tudo pesado vai em D: (`CINECAM_RUN`, `CINECAM_OUT`).
- Só uma execução por vez (lock em `D:/cinecam-run/render.lock`; apague se ficou órfão).
- Janela: o framebuffer pode ser menor que o pedido (SO limita). O mod avisa em `warnings` e usa o tamanho real.

## v0.8 (21/10/2026) — lote numa sessão
- `"next": ["D:/cinecam-run/jobs/b/job.json", ...]` no job.json da 1ª cena: depois do FINISH o mod devolve o relógio vanilla, restaura a água drenada, carrega a próxima e volta à fase SETUP (teleporta ao anchor, hora/tempo, PRELOAD, COMMANDS, SETTLE, FILM). O mundo (seed/copy) é o da 1ª cena; cada cena tem seu relatório. Cena que falha não para as outras. Python: `render_batch([...])`.
- `"mode": "film"|"stills"|"scout"` por cena (sobrepõe o `-Pmode`).
- Lançamento: `D:/cinecam-run/launch.json` guarda o comando java do runClient (capturado do `gradle --info`); `run_game` troca `-Dcinecam.job/-Dcinecam.mode/-Xmx` e lança direto. Fonte do mod mudou → `gradlew classes` antes (carimbo em `stamp`).
