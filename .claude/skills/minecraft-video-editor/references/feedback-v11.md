# Feedback do Matheus ao teste v11 (15/10/2026) — nota 4/10

Timestamps na timeline v11 (59,94 fps); mapa p/ tempo de fonte em `examples/feedback_v11_mapa.json`.

| TC v11 | Problema | Regra extraída |
|---|---|---|
| 0:00–0:00;31 | ruído morto no início | começar ~0.09 s antes da 1ª palavra |
| 2;07–2;57, 8;27–9;31, 18;40–19;16, 27;27–28;20, 31;29–32;03, 32;53–33;37, 34;10–35;05 | pausas longas | toda lacuna >= 0.22 s vira ~0.19 s |
| 6;53–8;33 | citou o item (canudinho) sem destaque | mostrar item: sticker pop + spotlight + SFX item |
| 14;58 (SFX) | SFX certo mas tarde; devia ser 14;03 (deboche) | SFX no gatilho da palavra |
| 15;12 | música devia ter trocado (fim do clima da intro) | trocar por clima, no tempo da fala |
| 27;50 | corte mal feito: palavra do 2º personagem cortada no início | folga antes do ataque; validar RMS |
| 27;51 | 1ª tentativa de cumprir objetivo: música tensão/ação/intriga + zooms leves e sutis | cena de tentativa = tensão |
| 29;41 | "?" digitado + pop = péssimo | pergunta retórica = distorção OU SFX meme OU P&B (ref: cacho de "?" gigantes) |
| 37;13 | obstáculo ("não consigo beber") sem tratamento | obstáculo = mostrar/brincar (zoom no HUD/mensagem + SFX erro) |
| geral | escolha e trocas de música = pior; faltou SFX | música por clima; mais SFX |

Pedido: reeditar os 3 primeiros minutos + melhorar momentos futuros nesse trecho. Resultado: sequência "v12 - TESTE 3min reeditado" (plan em `examples/plan2_v12_teste3min.json`, builder `examples/plan_v12_builder.py`).

## O que a ref BBKrwgbsp74 faz (medido nesta rodada)
- Pergunta curiosa/retórica (0:20 "E o que vem nesse kit, Cadu?"): cacho de 6–8 "?" brancos gigantes com contorno preto, pop + wobble + SFX.
- Piada (0:23 patada): zoom grande/distorcido na cara + SFX; música cai.
- Problema ("meus itens são muito ruins", 0:34): zoom ~3x na hotbar + escurece o resto + SFX fail.
- Dano ("será que ela tá dando dano?", 4:30): tinta vermelha na tela.
- SFX/hits de edição por ~5–15 s no início; depois mais raros (~1 por 20–40 s na ref; o Matheus quer um pouco mais).
