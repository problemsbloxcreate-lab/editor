# Linguagem de câmera — o que as referências ensinam

Fonte: 5 referências do Matheus analisadas quadro a quadro + fluxo óptico (translação/rotação/zoom por frame @60fps).
Tudo em convenção Minecraft: x leste, y cima, z sul; yaw 0 olha +z; pitch positivo olha para baixo.

## 1. As referências, shot a shot

### R-A · Bionic "My World is Secretly Alive" (0–10 s) — terror cinematográfico, plano contínuo
| t | O que acontece | Técnica |
|---|---|---|
| 0–2 s | Câmera **baixa, quase no chão, atrás de folhagem** (folhas desfocadas em primeiro plano). Steve fica pequeno atrás de uma árvore, fora do centro (terços). Deriva lenta e viva (handheld sutil, ~0,3°). | Oclusor de primeiro plano + DoF raso + composição assimétrica. Cor fria/desaturada, névoa azulada, vinheta. |
| 2–3 s | A câmera **atravessa as folhas** (cortina de folhas passa rápido = paralaxe forte) e revela uma **entidade escura** (blocos pretos, olhos vermelhos) já grande no quadro. | "Parallax reveal": a câmera passa a 1–2 blocos do oclusor; o sujeito aparece por trás. Roll ~10–15° (dutch) começa no mesmo movimento. |
| 3–6 s | Movimento lento e contínuo ao longo do corpo da entidade (órbita parcial + tilt para cima), folhas ainda cruzando o quadro. Em fluxo óptico: dy ≈ −3 %/frame constante (≈ 180 %/s de quadro) durante a travessia. | Velocidade quase constante (não eased no meio) = sensação de "caminhando por entre". |
| ~6,5 s | Corte seco para preto; texto vermelho "ALIVE" piscando; fade para gameplay. | Preto como respiro antes da virada. |

### R-B · Bionic skyblock (0–10 s) — um único plano que revela escala
1. Início **ultra-baixo olhando para cima**: herói sobre 1 bloco contra céu/nuvens (silhueta forte).
2. A câmera **sobe e recua girando** ao redor dele (órbita + dolly-out + crane). Roll varia de ~0° a ~−15° e volta: a horizontal "respira".
3. Revela **100 jogadores em ilhas flutuantes** em fila curva. Objetos próximos passam grandes (paralaxe) → senso de profundidade.
4. A câmera faz **tilt até olhar para baixo** (top-down) sobre a grade de ilhas e continua avançando; entram **speed lines** (faixas de luz diagonais) por cima.
5. Fluxo óptico: deriva lateral contínua −1…−2 %/frame, zoom pulsando (+4 %/frame num pico em 1,8 s).
Lição: **um plano, três mudanças de ângulo (baixo → alto → vertical)** vendem épico sem cortar.

### R-C · Bionic "Hide & Seek c/ armas" (0–10 s) — **a referência de câmera principal**
- **0–1,1 s — aerial swoop**: câmera alta sobre a costa/vila, mergulha e vira para o jogador. Fluxo: zoom **+4 %/frame logo em 0,15 s**, decai exponencialmente em ~0,9 s. É um **ease "launch"**: ataque quase instantâneo + desaceleração longa. Pousa num médio-aberto com o herói no terço inferior.
- **1,9 s — whip/tilt** (pico de 2 frames, dy −4 %/frame + blur) levanta para um **top-down** sobre árvore onde um amigo está.
- **2–3,8 s — top-down quase parado**: deriva de zoom −2 %/frame decelerando (câmera sobe lentamente), grade escura, **vinheta forte e brilho laranja no alvo** (destaque de luz).
- **3,8 s — whip-pan** forte (dx −6 %/frame) com motion blur = transição para o rosto do youtuber. **Toda troca de cena é um movimento rápido, não fade.**
- **6,0–9,9 s — órbita atrás de uma árvore** (câmera rente ao chão): tronco como **moldura fixa na borda direita** durante todo o plano; o herói rodando de costas → 3/4 → frente; **rack focus** (fundo borrado no início, nítido depois); **push-in** de plano aberto para médio; flare de sol no canto superior esquerdo; micro-roll.
- Legendas palavra-a-palavra, grossas, na base — nunca cobrem o sujeito (sujeito nos 2/3 superiores).

### R-D · Shorts do Problems (9:16, "Pokémon", "Bis 2000/2026/2050") — personagem articulado
- Câmera **colada nos personagens** (2-shot), deriva mínima, **punch-in** em punchline, **whip-blur** entre blocos com troca de cor/ano.
- Personagens têm **animação articulada**: braços erguem e balançam, cabeça inclina, squash/stretch, adereços flutuam com sombra de contato, reveal de morph com 2-3 frames de flash.
- Iluminação suave (shader), fundo limpo desfocado.
(Prioridade da skill é 16:9; use isto só quando o pedido for vertical.)

## 2. Números úteis (medidos)
- **Ease "launch"** (R-C): pico de velocidade em ~12–15 % da duração; ~80 % do deslocamento nos primeiros 25 % do tempo. `ease="launch"` reproduz.
- **Whip**: 2–5 frames @60fps (≈ 0,05–0,12 s) de pico + landing desacelerado de ~0,15 s. Total do movimento 0,2–0,3 s. Velocidade angular pico 600–1500 °/s (só aceitável por <0,3 s).
- **Deriva lenta** (R-A/R-B): 0,5–2 % do quadro por frame @60fps ≈ 30–120 % do quadro/s … traduza em blocos: câmera a 3–10 blocos/s num shot de 4–6 s.
- **Roll dutch**: 8–18° é a faixa "dinâmica"; >25° só em ação/terror. Sempre entra e sai com ease.
- **Duração de plano** (short-form): 1,0–2,5 s por movimento; abertura de vídeo 6–10 s no total, quase sempre 2–3 movimentos encadeados + 1 whip.
- **Gancho**: o 1º quadro já está **em movimento** (a câmera "chega" com velocidade). Plano parado nos 2 primeiros segundos = perde retenção.

## 3. Gramática — escolher o movimento pela intenção
| Intenção | Movimento (cinecam) | Detalhe |
|---|---|---|
| Chegar / estabelecer lugar | `crane(..., arc>0, ease="launch")` de alto → médio-aberto | termina com o herói nos terços, horizonte baixo |
| Mostrar escala / "olha o tamanho" | `orbit` em espiral para fora + `with_roll((0,-12))` + subida | revele pelo menos 2 camadas de profundidade |
| Revelar algo escondido | `parallax_pass` rente a oclusor (folhas/tronco/pilar) | oclusor a 1–3 blocos da lente, sujeito 8–20 atrás |
| Tensão / criatura | `track` baixo + `with_roll(±10)` + `with_handheld("handheld")` + fov 60–68 | névoa, ruído, vinheta; evite céu |
| Heroico / impacto | low-angle (câmera 0,3–0,6 bloco do chão, pitch −15…−30) + `push_in` curto com `out_back` | fov 55–65; sujeito contra o céu |
| Velocidade / perseguição | `chase` ou `through` fov 80–95, `bank=0.4`, speed lines no pós | blur 180° (subframes ≥ 8) |
| Transição entre cenas | **whip em duas pontas**: `whip` termina em blur → CUT → `whip` começa em blur continuando a mesma direção | o corte cai no pico do borrão |
| Dar importância ao rosto/objeto | `push_in` lento (3–6 s, `smooth`) + fov decrescente 70→55 | ou `dolly_zoom` para estranhamento |
| Respiro | `hold` + `with_handheld("breath")` 0,6–1,2 s | nunca `hold` perfeito: parece travado |

## 4. Regras de ouro (cada uma veio de erro ou acerto observado)
> 21/10/2026: com personagens, as regras de `enquadramento.md` têm prioridade (nunca perfil; câmera pela frente do personagem; câmera lateral sobre o personagem = perfil = proibido).
1. **Todo movimento tem motivo** (revelar, seguir, dar peso). Sem motivo, `hold`.
2. **Nunca linear.** Use `smooth`/`soft_in_out`; `launch` só quando o plano começa após um corte (já em velocidade).
3. **Continuidade**: emende com `rig.last_pose()` / `orbit_from` / `from_pose`. O analisador acusa saltos de posição/ângulo.
4. **Paralaxe sempre**: cena precisa de primeiro plano (folhas, tronco, bloco), plano médio (herói) e fundo (horizonte/ilhas). Câmera lateral sobre cenário vazio parece slideshow.
5. **FOV é personalidade**: 30–45 retrato/compressão; 60–70 padrão; 85–100 velocidade/épico (distorce bordas); dolly-zoom para vertigem. Varie o FOV ao longo do movimento (ex. 75→68 ao pousar).
6. **Roll respira**: entre ±(5–15)° com ease; volta a 0 no assentamento. Roll constante parece erro.
7. **Velocidade constante no meio é válida** (travessia de folhagem) — mas começo/fim suaves.
8. **Handheld sutil sempre** (`subtle`), forte só em perseguição/terror.
9. **Motion blur**: shutter 0,5, `subframes=8`; whips e shakes pedem 12–16. Hold longo: subframes 4 (rápido).
10. **Composição**: sujeito nos terços; deixe espaço na frente do olhar; legenda embaixo → sujeito no 2/3 superior.
11. **Luz** (time): dourado = 0–1500 ou 11000–12500; meio-dia 6000 é chapado (use nublado/ névoa/ grade); noite 14000+ com vinheta e bloom; chuva+trovão = clima de terror.
12. **Não atravesse o terreno**: use `Terrain.clearance(rig)`; mínimo 0,5 bloco acima do chão e 1 bloco de folhas, salvo reveal intencional.

## 5. Efeitos que fazem diferença (por custo)
- Barato (ffmpeg pós): vinheta, grade de cor, bloom, grain, aberração cromática leve, letterbox 2,39:1.
- Médio: speed lines (overlay), flash branco em corte, texto/lettering (fora desta skill: Remotion/Premiere).
- Pesado: DoF por profundidade (o mod exporta profundidade), shader pack (Complementary) para luz volumétrica.
