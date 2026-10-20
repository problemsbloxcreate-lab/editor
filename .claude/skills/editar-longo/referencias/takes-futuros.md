# "Takes futuros" — nota do roteiro que vira teaser com flashback (feedback 15/10/2026)

## O que é
O criador sussurra **notas de edição** no meio da gravação. Uma recorrente: **"takes futuros, editor"** = pedido DIRETO ao editor:
**ilustrar a frase seguinte com cenas impactantes do FUTURO do vídeo** (teaser), em cortes rápidos.
Exemplo (bruto 2026-10-08): fonte **177.25–178.15** (timeline 00;02;23;14 da v13) → "takes futuros, editor" e logo depois (178.78–183.5): "Porque a gente ainda vai desbloquear muitas maneiras iradas de beber água inteira do mundo".
Outras notas do mesmo tipo no bruto: "Time Lapse editor" (fonte ~1107; time-lapse = acelerar o trecho) e "vou voltar aqui, tá, editor?" (~1159).

## Regras
1. **A nota NÃO vai pro vídeo**: cortar do fim da frase anterior até o início da frase seguinte (usar `NOTE_A/NOTE_B` do plan_v14: fala anterior termina 176.95 → corta em 177.05; a frase seguinte começa 178.78 → entra em 178.68). Fica pausa ~0,2 s e o corte leva Potência constante.
2. **A frase seguinte é ilustrada com 4–6 takes** (0,7–1,25 s cada) de cenas impactantes que ainda VÃO acontecer; a voz continua por baixo (A1–A3 intactas), só o vídeo é coberto. Cortes alinhados às palavras (um take por bloco de palavras).
3. **Ordem de impacto crescente** (do "funil/canudo" ao clímax "planeta-bola"); sem texto.
4. **Filtro flashback** nos takes (lavado/quente/vinheta) — ref (analise_r2 §6.4): "grade lavada, contraste baixo, preto levantado, dessaturado".
5. **SFX de XP do Minecraft a cada corte** (`mc-xp-orb-p0..p4`: o orb com tom subindo +0,+2,+4,+5,+7 semitons; `rms_db −17`, teto de pico −2,0 → ganho ≈ +7 dB: o orb é um clique de 1 ms + plink curto de RMS −24, fica inaudível se normalizado por pico). Flash branco entra no 1º take (White Flash B) e sai no último (White Flash A) — presets BERSERKER, encurtados (`flash_scale` 0.45).
6. Se a nota não for achada pelo ASR (o Whisper devolve VAZIO no sussurro), o timecode vem do Matheus ou da escuta; `scripts/find_notes.py` só lista candidatos.

## Como escolher as cenas do futuro
- Transcrever o resto do bruto (Groq, `transcribe_tracks.py` em pedaços) e ler a história; contact sheets a cada 15 s (`ffmpeg -vf fps=1/15,crop=1920:1080:1920:0,scale=384:216,tile=5x4`) → achar o clímax visual; depois sheets densas (0,5–1,25 s) na janela escolhida.
- 15/10: funil sugando o lago (src 1626), canudo gigante listrado (1939.4), redemoinho (2136), dois personagens-bola sobre o globo (2138.6), planeta-bola no céu (2142). Critério: lê-se em <1 s, muda de escala/forma, sem HUD ilegível.

## Técnica (Premiere)
- **Takes = arquivos de VÍDEO SÓ** (`ffmpeg -ss <t-1> -t 3.2 -i bruto -an -vf crop=1920:1080:1920:0 -c:v libx264 -crf 14 -pix_fmt yuv420p`) importados no projeto e postos em **V2** (`stage b6c_futuros`, plano `futuros:[{file,tl,dur,off,zoom,preset_in,preset_out}]`; `off`=1.0 é o início "quente" dentro do arquivo de 3,2 s → dá folga p/ ele deslizar). **NUNCA sobrescrever com o próprio bruto**: `overwriteClip` leva o áudio ligado junto e destrói a voz em A1–A3.
- Disco: **C: estava 100 % cheio** (87 MB livres): takes/renders grandes em `D:\Pobrs\...`; apagar renders intermediários antes de exportar.
- **Flashback** (stage `b6d_flashback`; `plan['flashback_lumetri']` + `plan['flashback_tint']`): **Cor de Lumetri** — props PT-BR: 14 Temperatura +25, 16 Saturação 62, 19 Exposição +0,5, 20 Contraste −8, 22 Sombras +15, 23 Brancos −8, 24 Pretos +25 (preto levantado), 40 Filme desb. 35, 110 Vinheta −2,0, 111 ponto médio 40, 113 difusão 75 — **+ Tonalidade sépia** (preto→(64,38,14), branco→(255,240,205), 48 %) + zoom lento 100→106 % (108 % no clímax) por take. **Só Lumetri (v14a) dava cinza-azulado frio, que não lê "flashback"; o sépia é o que resolve** (conferido por frame exportado). Ordem na pilha: flash > sépia > Lumetri (efeito novo entra no topo). Valores a calibrar com o olho dele.
- QE: itens vazios (gap) contam em `track.getItemAt(i)` → mapear com `qidx()` (já em `berserker.APPLY_JS`) e `type == "Empty"`. Presets em V2: `var TRK = 1; var tr = s.videoTracks[1];` antes do `APPLY_JS`.

## Atualização 15/10 (depois da edição dele)
- **Aprovado por omissão**: na v14 que ele editou, os 5 takes (V2), o flashback (sépia + Lumetri), os flashes e os 5 orbs ficaram **exatamente como estavam** — padrão mantido.
- Os orbs agora entram com **ganho fixo +7 dB e SEM keyframe** (o fade-in de 10 ms está dentro do `mc-xp-orb-p*.mp3`; `mc_sounds_extract.py --ladder` regera). Cada orb nasce no corte do take (pré-roll ≤0,08 s).
- A música da frase dos takes = **Your Gain (VLOGS)**, que ele fez começar no "Furada" (1 s antes dos takes) junto do bruh.

