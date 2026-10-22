# Enquadramento, planos, ângulos, movimento e blocking — cutscenes de Minecraft (canal Problems)

Escopo: cutscenes de **1,6–3,4 s** inseridas no meio de gameplay POV em primeira pessoa, público **6–11 anos**, 16:9.
Personagem = modelo de player: **2,0 blocos**, cabeça cúbica de 0,5 (de y=1,5 a y=2,0), olhos **visuais** em y≈1,72 (a altura
de olho do jogo, 1,62, é a câmera do player, não o desenho), boca em y≈1,60, ombro 1,5, quadril 0,75, braço de 0,75 bloco
(12 px), tronco 0,5 de largura × 0,25 de profundidade. Sem cotovelo e sem joelho. Não há rig de rosto: **toda a emoção vem de
corpo, braços e cabeça**.

Convenções do código (acts.py/camlib.py): x leste, y cima, z sul; yaw do ator 0 = olha +z; frente do ator =
`(-sin(yaw), 0, cos(yaw))`; `yaw_to(a,b) = atan2(-dx, dz)`; head_y soma ao yaw do corpo (HEAD_Y_SIGN = +1); head_x<0 olha p/
CIMA; rarm_x=-90 braço p/ frente, -180 p/ cima, positivo = p/ trás; **rarm_z=+A / larm_z=-A = braço abrindo p/ fora**; lean>0 =
inclina p/ TRÁS; câmera = posição + mira, fov **vertical** em graus, pitch positivo olha p/ baixo.

Este arquivo **substitui** duas orientações antigas que causaram erro: (1) actors.md v0.7 "canudo: ponta na água ATRÁS do
personagem" — errado, ver §3.h; (2) camera-language.md regra 4 "paralaxe sempre: primeiro plano de folhas" — vale só com os
limites de oclusão da §3.g.

---

## 1. Fundamentos (o que as escolas dizem, traduzido para um boneco cúbico de 2 blocos)

### 1.1 Fontes usadas
| Fonte | O que tiramos dela |
|---|---|
| Joseph V. Mascelli, *The Five C's of Cinematography* (1965) | ângulo de câmera = ponto de vista; altura da câmera relativa ao olho do personagem; "cheat" de posição para a câmera; continuidade de direção de tela. |
| Daniel Arijon, *Grammar of the Film Language* (1976) | linha de interesse (eixo de 180°) e o **triângulo de câmeras** do diálogo (posições externas/internas/paralelas). |
| Roy Thompson & Christopher Bowen, *Grammar of the Shot* / *Grammar of the Edit* | tamanhos de plano por "onde cortar o corpo", headroom, lead room / noseroom, regra dos 30°, cortar fora das articulações. |
| Blain Brown, *Cinematography: Theory and Practice* | 180°, 30°, eyeline match, motivação de movimento, regra dos terços como ponto de partida. |
| Steven D. Katz, *Film Directing Shot by Shot* (1991) | staging em profundidade, blocking em triângulo/arco, movimento de câmera ligado a movimento de ator. |
| Walter Murch, *In the Blink of an Eye* (1995/2001) | "regra dos seis" (emoção > história > ritmo > **eye-trace** > plano 2D > espaço 3D) e eye-trace: o olho do espectador deve achar o sujeito no 1º quadro onde já estava olhando. |
| Bruce Block, *The Visual Story* | contraste/afinidade, movimento de câmera × intensidade, profundidade com planos sobrepostos. |
| Marcos Mateu-Mestre, *Framed Ink* (2010) | composição para animação/storyboard: leitura clara em silhueta, direção do olhar, profundidade por camadas. |
| Gustavo Mercado, *The Filmmaker's Eye* (2010) | quando cada tamanho de plano funciona e como quebrar a regra com motivo. |
| Alexander Dean & Lawrence Carra, *Fundamentals of Play Directing* (direção teatral) | **posições de corpo no palco**: frente plena, um-quarto (45°), perfil (90°), três-quartos (135°), costas plenas; "abrir" o ator para a plateia (*cheating out*). |
| Frank Thomas & Ollie Johnston, *The Illusion of Life* (1981) | os 12 princípios: **staging**, antecipação, exagero, follow-through/overlap, slow in/out, arcos, timing, appeal. |
| Richard Williams, *The Animator's Survival Kit* (2001) | antecipação, overshoot, *moving hold*, assimetria (evitar "twinning"), timing de pose a pose. |
| Pixar/DreamWorks (pipeline de **layout**: rough layout → final layout; material didático *Pixar in a Box*) | layout = decidir câmera e staging ANTES de animar; a câmera é escolhida pela leitura do personagem, não pelo cenário. |
| Animadores de Minecraft no YouTube (Alan Becker — *Animation vs. Minecraft*; Black Plasma Studios; animações em Mine-imator/Blockbench; Bionic para câmera) | personagens quase sempre de frente/3/4, poses grandes e legíveis em silhueta, braços muito exagerados, cabeça inclinando o tempo todo; quando há rig de rosto ele carrega metade da emoção — **nós não temos, então o corpo tem de exagerar ainda mais**. |

### 1.2 Tamanhos de plano (onde cortar o corpo)
Regra clássica: corte **entre** articulações, nunca nelas (Thompson/Bowen). No player: nunca cortar exatamente no pescoço
(y 1,5), na costura cintura (0,75) ou nos pés (0,0). Corte no meio do tronco, meio da coxa ou deixe pé com respiro.
- **Close de rosto (PP/big close)**: cabeça ocupa ~55 % da altura; só reação/punchline.
- **Close (plano próximo)**: cabeça + ombros + peito, cabeça ~40 %.
- **Plano médio**: da cintura para cima (corte ~0,7).
- **Americano**: do meio da coxa para cima (corte ~0,2–0,4). Ótimo para gesto de braço — o braço inteiro cabe.
- **Inteiro**: corpo todo com respiro em cima e embaixo.
- **Conjunto**: 2–4 personagens inteiros + um pouco de lugar.
- **Geral / grande geral**: lugar manda, personagem ≤ 25 % (geral) ou ≤ 12 % (grande geral).
Para crianças e cutscene de 2–3 s, o **americano e o inteiro 3/4** são o pão com manteiga: corpo inteiro lê a ação,
o rosto ainda é legível. Geral só como 1º meio segundo de um movimento que termina em conjunto.

### 1.3 Ângulos verticais
- **Altura do olho** = neutro, empatia, "estou ali com eles".
- **Contra-plongée (câmera baixa olhando p/ cima)** = poder, heroísmo, ameaça, gigantismo. Exagerado = caricatura.
- **Plongée (câmera alta olhando p/ baixo)** = vulnerável, pequeno, fofo/cômico (leve), derrota (forte), mapa/geografia.
- **Top-down (90°)** = mapa, padrão gráfico; personagem vira o topo de um cubo: **zero expressão**.

### 1.4 Ângulos horizontais — "3/4 é o ângulo mais expressivo"
Retrato, ilustração e animação concordam: o **3/4** (rosto girado ~30–45° da lente) mostra dois planos do volume
(frente + lateral), dá profundidade e mantém os olhos legíveis. Para uma cabeça **cúbica** isso é literal:
- de frente pura (0°) o cubo vira um **quadrado chapado** (adesivo 2D) — o rosto lê, o volume some;
- a 20–40° aparecem **duas faces do cubo**: lê como bloco 3D e o rosto ainda está quase inteiro;
- a 60° a face lateral já é maior que a frontal (largura projetada da face = 0,5·cos θ; da lateral = 0,5·sin θ; empatam em 45°,
  a lateral domina acima disso);
- de **perfil (90°)** o tronco vira uma tira de 0,25 bloco (contra 1,0 bloco de frente, com braços): o corpo perde **75 % da
  largura**, os olhos somem, os braços ficam um atrás do outro. É exatamente a "tira fina sem expressão" que o Matheus rejeitou.
No teatro (Dean/Carra) a hierarquia de força das posições é a mesma: frente plena e um-quarto são fortes; perfil serve para
dois atores se encarando e é fraco; três-quartos (135°) e costas são fracas, usadas só como efeito. Atenção ao vocabulário:
"três-quartos" do teatro = 135° (quase de costas); "3/4" do cinema/animação = ~45° de frente. Aqui **3/4 = 25–50° de frente**.

### 1.5 Eixo de 180°, eyeline e regra dos 30°
- **Linha de interesse**: a reta entre os dois personagens que interagem (ou a direção do movimento). Câmeras de uma mesma
  cena ficam do **mesmo lado**; assim A fica sempre à esquerda olhando para a direita e B à direita olhando para a esquerda.
- **Eyeline match**: se A olha para fora de quadro à direita, o próximo plano mostra o alvo olhando de volta para a esquerda.
- **30°**: dois planos seguidos do mesmo sujeito precisam mudar ≥ 30° de azimute **ou** um tamanho de plano (≥ 1,5× na
  altura do sujeito na tela). Menos que isso = jump cut involuntário.

### 1.6 Triângulo de câmeras e over-the-shoulder (Arijon)
Diálogo de dois: base do triângulo paralela à linha de interesse, do lado da câmera. Vértice = **master** (2-shot).
Ângulos **externos (OTS)**: atrás do ombro de A, mirando B a 3/4; o ombro de A ocupa 20–33 % da largura na borda,
desfocado. **Internos**: entre os dois, cada um a 3/4. Note: no OTS o personagem de primeiro plano está **de costas** —
isso é permitido porque ele não é o sujeito; o sujeito (quem fala) aparece a 3/4 de frente.

### 1.7 Cheat-to-camera / blocking teatral aberto
No palco, dois atores conversando não ficam de perfil um para o outro: cada um "abre" o corpo ~45° para a plateia e só
vira a cabeça para o parceiro. No cinema chama-se *cheating*: o ator se posiciona num ângulo que seria estranho na vida
real, mas que **na lente** parece natural. Grupos ficam em **arco/ferradura aberto para a câmera**, nunca em fila
paralela à lente nem em roda fechada. É a regra mais importante deste documento para o nosso sistema (ver §3.a).

### 1.8 Headroom, lead room, noseroom e terços
- **Headroom**: espaço acima da cabeça; diminui com o plano mais fechado (close quase zero; inteiro 8–15 %). Excesso de
  headroom "afunda" o personagem; headroom negativo em plano médio "decapita".
- **Linha dos olhos** no terço superior (~33 % do topo) em close e médio.
- **Lead room / noseroom**: espaço na direção do olhar ou do movimento = 60–67 % da largura à frente.
- **Terços**: um personagem que olha para o lado vai para o terço oposto; dois personagens nos dois terços; centro só
  quando ele fala para a lente ou a gag é simétrica.

### 1.9 Motivação de movimento e movimento × emoção
Câmera só se move com motivo (Katz, Brown): **seguir** (o ator anda), **revelar** (informação nova entra), **intensificar**
(push-in em realização/medo), **distanciar** (pull-out em isolamento ou na revelação cômica), **dar peso** (contra-plongée
subindo). Comédia física lê melhor em plano aberto e câmera estável — vale a máxima de Chaplin: tragédia em close,
"comedy in long-shot". Energia de desenho animado moderno vem de **snap zoom e whip pan** (Edgar Wright, Looney Tunes) — em
pulsos curtos, não em deriva contínua.

### 1.10 Como layout de animação 3D trabalha (Pixar/DreamWorks) e o que copiar
1. A câmera é escolhida **para o personagem**: primeiro decide-se que lado do rosto e que pose precisam ler; depois o
   cenário é "trapaceado" (objetos movidos, paredes "wild") para caber.
2. **Staging = uma ideia por plano**, inequívoca em silhueta (Thomas & Johnston). Se a pose não lê preenchida de preto, ela
   não lê.
3. Personagens são **reposicionados entre planos** (cheat de continuidade) para manter o 3/4 — ninguém percebe.
4. Os Minecraft animators do YouTube fazem o mesmo: quase todo plano é frente/3/4, o personagem "atua para a câmera",
   gestos são duas a três vezes maiores que os humanos, a cabeça inclina constantemente.
Consequência para nós: **o cenário e os personagens se adaptam à câmera; a câmera não "descobre" o que o cenário deu.**

### 1.11 Eye-trace no corte vindo de gameplay (Murch)
O gameplay é POV com a mira no centro: o olho do espectador está no **centro** da tela no instante do corte. No 1º quadro
da cutscene o sujeito deve estar na zona central (x 0,30–0,70; y 0,25–0,60). Ele pode migrar para o terço durante o
movimento. Sujeito numa borda no quadro 1 = criança "procura" e perde meio segundo de um plano de 2 s.

---

## 2. Auditoria take a take (job 20261021_054217 — "Bebi toda a água do mundo")

Medido nos stills stA–stE, finA/finB, cNN_final e cine_check/sheet.jpg + geometria do cards.json.
θ = ângulo horizontal entre a frente do personagem e a direção personagem→câmera (0 = olha a lente). Câmera sempre veio do
lado +z.

**Causa-raiz sistêmica** (vale para quase todos):
1. `face="<ator ou marca>"`, `turn()` e `point()` giram o **corpo inteiro** para o alvo por pura geometria, sem saber onde
   está a câmera. Como as câmeras assumem "elenco olhando +z", todo personagem que olha para outro ou para um lugar no
   fundo acaba de perfil ou de costas. `point()` é o pior: chama `turn()` e o personagem dá as costas para apontar algo
   que está atrás dele.
2. `look()` aceita até ±65° de cabeça — com o corpo já de frente, o rosto vai para perfil.
3. Câmeras (`hero_low`, `orbit_push`, `plongee`) são posicionadas em **coordenadas de mundo** (+z do set) e miram o
   centro do grupo; não leem o yaw de quem é o sujeito.
4. Nenhuma checagem de "fatia na borda", headroom, oclusão do rosto ou encaixe de item antes do render final.
5. A cena "beber" foi montada com a **água atrás** do personagem (ele olha a câmera, de costas para a lagoa) — o canudo
   tem de vir por trás e entra pela nuca.

| Take | Fala / intenção | O que estava errado | Como deveria ter sido |
|---|---|---|---|
| **c01** trio "vamos beber toda a água" (hero_low 6,2→3,8) | Tese do vídeo, energia | Trio em **fila reta paralela à lente**, espaçamento igual, todos fazendo a mesma comemoração (twinning, offset de só 0,06 s). Stick vira a cabeça 65° para o Problems e Patão 65° para a lagoa **atrás** → rostos de perfil. Na comemoração, braços a −170° com z=18 vistos de baixo **passam na frente da cara** (Patão some atrás dos próprios braços). Problems a 0° = cubo chapado. | Arco aberto (raio ~2,5): Problems ao centro 0,6 bloco mais ao fundo, corpo 15–20°; Stick e Patão abertos 30° para a câmera, cabeça +15–20° para o Problems (rosto ≤ 50°). Lagoa à frente-lado, não atrás. Comemoração com três poses diferentes (V assimétrico, soco no ar com um braço, pulinho duplo) e offsets 0,12–0,2 s. Braços para cima no máx. −155° com abertura ≥ 30°. Câmera a 0,7 de altura, fov 50, conjunto (H≈4,2). |
| **c02** Patão "você é maluco?" (dolly_shock) | Susto, vertigem | Frontal 0° perfeito + **pose T simétrica** e parada por 2,2 s = boneco de teste. Fatia ciano do Problems na borda esquerda no início. Fundo de deserto plano perto → dolly zoom quase não lê (precisa de camadas a 10–40 blocos). | Corpo 20°, susto assimétrico (braço direito −60/+80, esquerdo −20/−50), hop 0,2 + passo para trás 0,3, cabeça para trás e inclinada 10°, tremor 8 Hz decaindo, depois *moving hold*. Fundo com duna/lagoa/cacto em profundidades diferentes. Problems totalmente fora ou inteiro no terço oposto. |
| **c03** close bebendo (close d 1,8→1,45) | Barriga cresce | **Topo da cabeça cortado**, olhos a ~3 % do topo. Personagem **de costas para a lagoa**: o canudo sobe por trás do ombro e **entra pela nuca** (o erro citado pelo Matheus). Barriga vista de frente vira um **disco chapado**. DoF focado no peito borra o rosto. | Personagem na margem **olhando a água**, corpo a 35–40° da lente; canudo sai da boca para a frente-baixo e mergulha na água no espaço de lead room. Plano médio (H≈1,55, fov 45, d≈1,9) com olhos no terço superior; câmera 0,3 acima do centro da barriga (y≈1,35), pitch +8°. A 3/4 a barriga **sai do corpo** e lê como volume. |
| **c04** villagers 70 % água (orbit_push) | Apontar o villager | Problems e Stick com corpo virado para o villager → **costas/3/4-costas (~150°)**, Problems enorme em primeiro plano de costas, braço apontando para dentro do quadro (some). Villager, o assunto da fala, a ~5 % da altura do quadro. | "Apresentador": Problems no terço esquerdo a 3/4 (30°) virado para a lente, braço aberto em diagonal (x −70, z +60) indicando o villager, que está no terço direito a 3–4 blocos atrás, **de frente**. Stick reage a 3/4. Câmera altura do olho (1,5), fov 45, d≈4. Alternativa: OTS por trás do villager no rosto do Problems. |
| **c05** Brucutu discursa (hero_low) | Ironia: ele secou a poça | Galho seco **cobrindo 1/3 do quadro** no começo. Problems cortado na borda esquerda (só o braço aparece). Brucutu **aponta para a lente** → braço encurtado, vira um toco. Stick a ~63° (perfil). Câmera baixa **esconde a poça seca** — a ironia some. | Brucutu 20–25°, gestos abertos (z ±40–70) em vez de apontar para a lente; câmera a 2,2 com pitch +10° para mostrar o buraco seco atrás dele. Problems e Stick no fundo, inteiros, a 3/4, reagindo — ou fora de quadro. Sem oclusor no rosto. |
| **c06** bebendo a piscina (hero_low) | Barriga + piscina | De novo **de costas para a piscina**: canudo escondido atrás do corpo, ação ilógica. Barriga frontal = disco. Patão como fatia na borda direita, de perfil (~84°). | Problems na borda da piscina olhando a água a 35–40° da lente, canudo à frente; Patão inteiro no terço oposto, corpo aberto 30°, cabeça para o Problems. |
| **c07** Brucutu enche a piscina de balde | Indignação | Problems **de perfil (~110°)** e cortado na borda esquerda, enorme; Brucutu **de 3/4-costas (~133°)** a ~12 % da altura, ação do balde ilegível. | 2-shot em profundidade: Brucutu no terço direito, a 3/4 de frente (a piscina entre ele e a lateral da câmera), balde erguido acima da água; Problems no terço esquerdo a 3/4, apontando **atravessando a tela** (braço lê na horizontal). Câmera 1,0, fov 45. |
| **c08** desculpa da dengue (4 personagens) | Grupo cínico × desconfiado | Câmera atravessa **capim alto**: lâminas planas gigantes cobrem metade do quadro. Problems **de perfil puro (90°)** no centro; Brucutu a ~70°; Patão cortado na borda; Stick escondido atrás do Problems. | Arco de 4 aberto para a câmera: trio à esquerda sorrindo/acenando a 20–35°, Brucutu à direita a 30° com lean para trás e cabeça inclinada (desconfiança). Câmera na altura do olho, conjunto H≈4, fov 50; capim limpo num cone de 2 blocos na frente da lente. |
| **c09** parque de fachada (plongee) | Piscina vazia | Plongée **por trás**: os três olham a piscina = **todos de costas (180°)** e pequenos (~8 % da altura). | Câmera **do outro lado da piscina**, alta (4–5) olhando para baixo 30°: piscina vazia em primeiro plano, o trio atrás dela **de frente** (eles olham a piscina, que olha a câmera), ~18 % da altura. Regra: para mostrar "o que eles olham" com rosto, a câmera fica **atrás do objeto olhado**. |
| **c10** "olha o tamanho dessa cachoeira" (establish) | Revelação | 1ª versão começava na **nuca enorme** do Problems; a final termina com os personagens a ~6 % da altura e o Problems vira de costas para apontar (o `point` faz `turn`). | *Pull-back reveal*: começa em americano dos dois a 3/4 (Problems apresentando com o braço aberto para trás-lado), câmera recua e sobe (crane 1,5 bloco/s, ease soft) revelando a cachoeira; termina com a dupla no terço inferior a ≥ 15 % da altura e a cachoeira nos 2/3 de cima. |
| **c11** bebendo na cachoeira (hero_low) | Barriga | Enquadramento razoável, mas **de costas para a lagoa**, canudo por cima do ombro vindo de trás; barriga frontal chapada. | Igual a c03/c06: de frente para a água a 35–40°, canudo à frente, câmera levemente acima da barriga. |
| **c12** Problems gigante (hero_low d 12→9,5) | Escala absurda | Problems a ~30° ok; **Patão 3/4-costas (~142°)**, pequeno e parcialmente atrás da vegetação → o susto dele não aparece. Distância 12 achata a escala. Folhas cobrindo o quadro no início. | Câmera **baixa perto do Patão** (y 0,5, d 2,5, fov 60, pitch −22°): Patão no terço inferior esquerdo a 30–40°, olhando para cima (head_x −30); o gigante no terço direito ao fundo, cortado no peito para parecer maior que o quadro. Tilt-up de 15° durante o take. |
| **c13** Stick bebendo o lago | Barriga + choque | Canudo de trás (entra no ombro/nuca). Problems como **fatia na borda direita**, de perfil (~106°): o choque é invisível. | Stick no terço esquerdo a 35° olhando a água; Problems inteiro no terço direito a 30°, choque assimétrico grande. |
| **c14** Brucutu vira uma bola | Barriga máxima | Frontal, canudo por trás; Problems **fatia na borda esquerda** de perfil (~110°) apontando — gesto invisível. | Brucutu a 35–40° com câmera levemente alta (vende a bola); Problems no terço oposto a 3/4 apontando atravessando a tela, ou fora do quadro. |

Placar: 11 dos 14 takes têm pelo menos um personagem relevante de perfil ou de costas; 7 têm fatia de personagem na borda;
5 têm o canudo vindo de trás; 3 têm oclusor no começo cobrindo o sujeito; 2 cortam a cabeça ou deixam o sujeito < 10 % da
altura no fim.

---

## 3. Regras executáveis

### (a) Ângulo horizontal câmera × frente do personagem

Definições (por quadro, por personagem):
```
fwd_body = (-sin(yaw), 0, cos(yaw))
fwd_face = (-sin(yaw + head_y), 0, cos(yaw + head_y))
to_cam   = normalize_xz(C - head_center)
θ_body = acos(fwd_body · to_cam)   θ_face = acos(fwd_face · to_cam)        (graus, 0..180)
```

| Zona | θ | Uso |
|---|---|---|
| Frontal pleno | 0–10° | só fala para a lente ("take to camera") e gag simétrica; ≤ 40 % do take — o cubo fica chapado |
| **Frente** | 10–25° | ótimo: falas, reações |
| **3/4** | 25–50° | ótimo e **preferido**: diálogo, gesto de braço, barriga, apontar |
| Tolerável | 50–60° | secundários; o sujeito só de passagem (≤ 0,4 s) |
| **PROIBIDO — perfil** | **60–120°** | nenhum personagem com altura na tela ≥ 10 % por mais de 0,25 s. Exceções: silhueta contra o sol (aprovada antes, v0.5) e travessia rápida (≤ 0,3 s) |
| Costas-3/4 | 120–150° | só como **OTS** em primeiro plano (não é o sujeito), ou personagem saindo de cena |
| Costas | 150–180° | só com motivo: OTS de revelação, *turn reveal* (começa de costas e vira em ≤ 0,5 s), saída de cena |

Limites por papel (aplicar a θ_face; θ_body pode ser até 10° maior):
- **sujeito**: alvo 15–40°, máximo 50° em ≥ 90 % dos quadros e 100 % no quadro do beat principal;
- **secundário** (≥ 10 % da altura): máximo 60°;
- **figurante** (< 10 % da altura): máximo 70°, nunca de costas se estiver olhando para o sujeito.
Compatibilidade com `framing.py` (zonas 30/55/65/115): manter 65–115 como **reprovação dura** para qualquer um; para o
**sujeito**, apertar para 50/60/120.

**Cheat de corpo para 1 personagem olhando um alvo** (parceiro, objeto, lugar):
```
def cheat(pos, cam, target, body_k=0.45, body_max=35, face_max=50, head_max=40):
    yc = yaw_to(pos, cam)                     # olharia a lente
    d  = wrap(yaw_to(pos, target) - yc)       # quanto o alvo está fora do eixo da lente
    if abs(d) > 110:   -> NÃO olhar: usar pose de apresentador (§4) ou mudar câmera/alvo de lugar
    body   = yc + clamp(body_k * d, -body_max, body_max)
    face   = yc + clamp(d, -face_max, face_max)
    head_y = clamp(wrap(face - body), -head_max, head_max)
    return body, head_y
```
Ex.: parceiro a 90° do eixo da lente → corpo 35°, rosto 50°, head_y 15°. Lê como "olhando o amigo" porque na tela eles
estão em lados opostos e um aponta o rosto para o outro (eyeline por composição, não por geometria real).

**2 personagens**: distância entre eles 1,6–2,4 blocos (perto o bastante para caber num americano/inteiro, longe o bastante
para braço de 0,75 não atravessar o outro). Corpos abertos 25–35° para a lente, cabeça +15–20° para o parceiro → rostos
40–55°. No beat de fala, quem fala pode trazer o rosto para 15–25° (atuar para a câmera); quem escuta mantém o olhar no
parceiro.

**3 personagens**: arco côncavo para a câmera (raio 2–3 blocos). Defina um **ponto focal** 3–5 blocos à frente do centro do
arco, do lado da câmera; cada corpo mira esse ponto (resultado: todos 15–35° da lente). O dominante vai ou ao centro um
pouco atrás (0,5–1,0, "upstage") ou no terço mais perto da lente (0,5–1,0 à frente). Ninguém alinhado com outro na direção
da lente (sobreposição de silhuetas ≤ 15 %). Cabeças em alturas de tela diferentes (triângulo), nunca três na mesma linha.

**Personagem + objeto atrás dele** (cachoeira, villager, poça seca): o objeto fica **atrás e deslocado lateralmente** ≥ 1/3
da largura (staging em profundidade). O personagem fica de frente/3/4 e indica com o braço aberto para trás-lado (pose de
apresentador) — **nunca** gira o corpo para o objeto. Se a fala exige que ele OLHE o objeto: OTS com o objeto como sujeito
(personagem ≤ 30 % do quadro, na borda, ≤ 1,5 s) ou câmera atrás do objeto olhando o personagem (regra c09).

**Escolha automática de azimute da câmera** (depois do cheat):
```
pen(θ, papel): θ≤25: 0 | 25–50: 0,2·(θ−25)/25 | 50–60: 1 (sujeito) / 0,3 (outros) | 60–120: 50 (duro)
               | 120–150: 8 (0,5 se papel=='ots') | >150: 15 (0,5 se 'ots' ou 'turn_reveal')
para az em passos de 5° numa janela ±70° em torno da frente do sujeito:
   C = foco + dist·(sin az, 0, cos az) + altura
   custo = Σ_quadros Σ_atores peso·pen(θ_face) + 20·fatias_na_borda + 30·rosto_ocluído + 10·lado_errado_do_eixo
escolher o menor; empate → o mais perto de 25–35° do sujeito.
pesos: sujeito 1,0 | secundário 0,5 | figurante 0,15
```
Orbitas/arcos são definidos **relativos ao yaw do sujeito**, não ao +z do mundo: começar em ±30–40° e terminar em
±5–20° (ou cruzar o 0 até ∓15°); **o arco inteiro fica dentro de |θ| ≤ 45°**.

### (b) Altura e inclinação da câmera por intenção (personagem de 2 blocos; olho visual 1,72)

| Intenção | Altura da câmera (y acima do chão) | Pitch (+ = p/ baixo) | Distância / fov | Notas |
|---|---|---|---|---|
| **Neutro** | 1,4–1,8 | −3…+5 | conforme plano | padrão de fala/diálogo |
| **Heroico** | 0,4–0,9 | −10…−20 | d 2,5–4,5, fov 45–60 | céu atrás; acima de −25° vira caricatura |
| **Poder/vilão/gigante** | 0,2–0,5 | −20…−35 | fov 60–75, perto | distorção de grande angular ajuda; Brucutu vilão |
| **Cômico (fofo)** | 2,3–3,0 | +8…+15 | inteiro/conjunto, fov 45–55 | personagens "chibi", gag lê no corpo todo |
| **Cômico (absurdo)** | 0,3–0,6 | −15…−25 | fov 70–80 a 1,2–1,8 | grande angular colada, 0,5–1 s, punchline |
| **Vulnerável/derrota/pequeno** | 3,5–6,0 | +25…+45 | conjunto/geral | plongée; nunca o único ângulo de um sujeito que fala |
| **Close de barriga voxel** | 1,25–1,5 (≈0,2–0,45 acima do centro da barriga, y≈1,06) | +8…+15 | d 1,3–1,9, fov 44–50 | a 3/4: a bola sai do tronco |
| **Mapa / geografia** | 8+ | +60…+90 | — | ≤ 1,5 s; ninguém é sujeito |

Com pitch < −12° e braços acima de −140°, os braços passam na frente do rosto: nesses ângulos braço para cima exige
abertura |z| ≥ 30°.

### (c) Tamanho de plano → distância × fov

Altura de mundo coberta no plano do sujeito: `H = 2·d·tan(fov/2)` ⇒ `d = H / (2·tan(fov/2))`. Largura = H·16/9.

| Plano | H (blocos) | Altura do personagem na tela | fov recomendado | d (fov 40) | d (fov 45) | d (fov 50) | d (fov 55) | d (fov 60) | Headroom (topo da cabeça→topo do quadro) |
|---|---|---|---|---|---|---|---|---|---|
| Close de rosto | 0,9 | cabeça ~55 % | 35–45 | 1,24 | 1,09 | 0,97 | — | — | 0–5 % (pode cortar ≤ 10 % da cabeça, nunca os olhos) |
| Close | 1,25 | cabeça ~40 % | 38–48 | 1,72 | 1,51 | 1,34 | 1,20 | — | 4–10 % |
| Médio | 1,55 | da cintura p/ cima | 40–50 | 2,13 | 1,87 | 1,66 | 1,49 | — | 6–12 % |
| Americano | 2,0 | meio da coxa p/ cima | 45–55 | 2,75 | 2,41 | 2,14 | 1,92 | 1,73 | 8–14 % |
| Inteiro | 2,45 | ~82 % | 45–55 | 3,37 | 2,96 | 2,63 | 2,35 | 2,12 | 8–15 %, pés 4–10 % acima da base |
| Conjunto (2–3) | 3,4–4,2 | 48–60 % | 50–60 | 4,7–5,8 | 4,1–5,1 | 3,6–4,5 | 3,3–4,0 | 2,9–3,6 | 10–20 % |
| Geral | ≥ 8 | ≤ 25 % | 55–70 | — | 9,7 | 8,6 | 7,7 | 6,9 | — |
| Grande geral | 15–40 | 5–13 % | 60–75 | — | — | — | — | — | só abrindo um movimento; nunca o quadro final |

- **Linha dos olhos** (y de tela medido do topo): close/médio 0,28–0,40; americano/inteiro 0,18–0,30.
- **Mira**: para pôr os olhos no terço superior, mire abaixo dos olhos: `aim_y = 1,72 − d·tan(fov/6)` (ex.: médio d 1,87,
  fov 45 → aim_y ≈ 1,47). Inteiro/conjunto: mire y 1,0–1,1 (não 1,25 do `_subject` atual, que deixa headroom curto quando
  a câmera é baixa).
- Plano mais fechado = fov menor (35–45); grande angular (≥ 65) colada no rosto só para gag.
- Quadro **final** de qualquer take: sujeito ≥ 15 % da altura (crianças leem pessoas, não paisagem).
- Conjunto de 3 com espaçamento s entre vizinhos: precisa `W ≥ 2s / 0,56` (laterais em 0,22 e 0,78) → `H = W·9/16`.
  Ex.: s = 2,1 → W 7,5 → H 4,2 → fov 50, d 4,5.

### (d) Posição na tela (x, y normalizados 0..1 a partir do canto superior esquerdo)

| Caso | Cabeça do(s) personagem(ns) | Observações |
|---|---|---|
| 1 personagem falando para a lente (θ ≤ 15) | x 0,45–0,55 | simetria permitida |
| 1 personagem olhando/apontando para um lado | x 0,30–0,40 (olha p/ direita) ou 0,60–0,70 (olha p/ esquerda) | lead room = 60–67 % à frente do rosto |
| 1 personagem andando | começa em 0,33 do lado de trás; termina ≤ 0,45 | 2/3 do quadro à frente; nunca alcançar a borda de saída |
| 2 personagens | 0,33 ± 0,05 e 0,67 ± 0,05 | diferença de altura das cabeças ≤ 10 % da tela, salvo staging em profundidade |
| 2 em profundidade (um à frente) | frente em 0,30/0,70; fundo no terço oposto, 0,3–1,5 bloco atrás | sobreposição de silhueta ≤ 15 %, rosto do fundo 100 % livre |
| 3 personagens | 0,22–0,28 / 0,45–0,55 / 0,72–0,78 | triângulo: o do meio mais alto ou mais baixo na tela por ≥ 4 % |
| Personagem + objeto da fala | personagem num terço, objeto no outro | o objeto ocupa a lead room do personagem |
| Margem de segurança | todo personagem relevante ≥ 3 % da borda (cabeça ≥ 4 % do topo, salvo close de rosto) | legenda/UI de baixo: sujeito nos 2/3 superiores |
| Quadro 1 após o gameplay | sujeito em x 0,30–0,70, y 0,25–0,60 | eye-trace |

**Fatia na borda proibida**: para cada personagem, fração visível do bbox na tela `f_in` deve ser **≥ 0,92** (inteiro) ou
**0** (fora). Entre os dois só se for **OTS de primeiro plano**: bbox com altura ≥ 60 % da tela, largura visível ≥ 12 %,
desfocado e de costas/3/4-costas. Qualquer outro caso (o "pedaço ciano na borda" de c02/c05/c06/c08/c13/c14) reprova.

### (e) Movimento de câmera por intenção (shots de 2–3 s)

Medidas: velocidade de translação em blocos/s, rotação em °/s, variação de tamanho = quanto a altura do sujeito na tela
muda durante o take. **Um movimento por take.** O pico de ação do personagem cai entre 25 % e 65 % do take; nos últimos
0,3 s a câmera está ≥ 80 % assentada (o corte volta ao gameplay limpo).

| Intenção | Movimento | Números | Ease |
|---|---|---|---|
| Entrar na cena vindo do gameplay | push-in curto já em velocidade | tamanho +15–25 %; 0,4–1,2 b/s | `launch_soft` |
| Importância / realização / medo | push-in | +20–40 % em 2–3 s (ex. d 3,0→2,2) | `soft_in_out` |
| Punch cômico / punchline | snap zoom (fov) ou push rápido | fov −20–35 % em 0,12–0,20 s, depois hold | `out` (sem `out_back` em posição) |
| Revelação cômica / isolamento / escala | pull-back (+ crane up) | tamanho −35–55 %; 1,0–2,5 b/s; crane 0,8–1,5 b/s | `soft_in_out`; termina com sujeito ≥ 15 % |
| Herói / admiração | arco baixo | 10–18 °/s, total 25–40°, dentro de \|θ\| ≤ 45° | `soft_in_out` |
| Seguir quem anda | truck lateral à frente-3/4 | velocidade do ator ±10 %; câmera 1,5–2 blocos **à frente** do ator, 3/4 de frente | `linear` no miolo, lag 0,12 |
| Poder / gigante | tilt-up ou crane-down com contra-plongée | tilt 8–15 °/s; crane 0,3–0,8 b/s | `soft_in_out` |
| Chegar num lugar | crane de alto → conjunto | 2–4 b/s no início, termina < 0,3 b/s | `launch` |
| Susto | dolly zoom | fov 44→26 (≈ −40 %) em 1,2–2,0 s; fundo com camadas a 10–40 blocos; sujeito a 15–25° | `smooth` |
| Tensão / vilão | deriva lenta + handheld | ≤ 0,3 b/s; handheld 0,3–0,6°; roll ≤ 8° | `smooth` |
| Respiro / gag em plano aberto | quase parado | deriva ≤ 0,15 b/s; handheld `subtle` (0,2–0,4°) | — |

Limites gerais:
- Rotação de câmera (pan/tilt) ≤ 30 °/s fora de whip; whip 600–1500 °/s por ≤ 0,3 s só como transição.
- Sujeito não atravessa mais de 30 % da largura da tela por segundo, salvo seguindo ação rápida.
- fov varia ≤ 10° num take (exceto snap zoom e dolly zoom).
- Roll: 0 ± 3° no normal; 8–15° só vilão/caos; sempre volta com ease.

Evitar (todos apareceram no job auditado):
- arco/órbita que passa por perfil ou termina nas costas do sujeito;
- câmera atravessando **capim, flores e folhagem a menos de 1,5 bloco** (plantas em cruz viram lâminas planas gigantes);
- oclusor de primeiro plano sobre o **rosto** do sujeito em qualquer quadro; oclusor em geral: ≤ 25 % da área, só nas bordas
  ou nos primeiros 0,4 s;
- establishing que **termina** com o elenco < 12 % da altura ou escondido atrás de árvore;
- plongée/top-down quando o sujeito tem fala ou reação;
- mira fixa no centro do grupo quando o grupo ocupa > 60 % da largura (alguém sai pela borda no push-in);
- `out_back` em posição de câmera (overshoot atravessa o chão).

### (f) Eixo de 180° entre takes

1. Por **cena** (mesmo site + mesmo elenco num trecho do vídeo), fixar no card um `screen_map`: lado de tela de cada
   personagem e do objeto principal, ex. `{"problems": "L", "brucutu": "R", "piscina": "fundo"}`.
2. Linha de interesse = par principal (A, B) ou direção de movimento. Lado da câmera:
   `lado = sign(((B − A) × (C − A)).y)`. Takes consecutivos da mesma cena: **mesmo sinal**. Trocar de lado só com um take
   cuja câmera cruze a linha **em movimento contínuo** visível, ou com um plano neutro (frontal ao longo da linha) entre os dois.
3. Direção de movimento (quem anda da esquerda para a direita) se mantém entre takes da mesma ação.
4. Coerência com o gameplay: se no POV o objeto (lagoa, villager) estava à esquerda, a cutscene o põe à esquerda quando
   for possível sem violar (a).
5. Regra dos 30°: cutscenes do mesmo sujeito separadas por < 15 s de gameplay mudam ≥ 30° de azimute ou ≥ 1,5× de tamanho.
6. Dentro de um take, a câmera não cruza a linha entre dois personagens que interagem (eles trocariam de lado na tela).

### (g) Checklist de validação automática

Projeção de um ponto P (câmera C, yaw/pitch → f, r = normalize(f × ŷ), u = r × f; roll gira (x, y)):
```
v = P − C;  z = v·f;  x = v·r;  y = v·u
tv = tan(fov/2);  th = tv·16/9
sx = 0,5 + 0,5·x/(z·th);   sy = 0,5 − 0,5·y/(z·tv)        (z ≤ 0,05 ⇒ atrás da câmera)
```
Bbox de um ator = projeção dos 8 cantos de cabeça, tronco, braços e pernas via `KActor` (kin.py), mais o item.

**Por quadro** (amostrar a cada 2 quadros; reprovação dura em negrito):
1. **θ_face e θ_body de cada ator na tela** dentro dos limites do papel (§3.a); perfil 60–120 com altura ≥ 10 % → **falha**.
2. **Fatia na borda**: `f_in` ∈ [0,92, 1] ou 0, ou OTS válido.
3. **Rosto do sujeito 100 % visível**: nenhum bloco do cenário (raycast nos blocos do set, ou depth exportado pelo mod <
   profundidade da cabeça − 0,1) e nenhum outro ator sobre o bbox da cabeça.
4. Sobreposição entre bboxes de atores (IoU) ≤ 0,10, salvo OTS.
5. **Headroom ≥ 0** (cabeça inteira) exceto close de rosto; olhos na faixa da §3.c.
6. Altura do sujeito na tela dentro da faixa do plano pedido; no último quadro ≥ 15 %.
7. Posição do sujeito na faixa da §3.d com tolerância ±0,06; lead room ≥ 55 % na direção de θ_face.
8. Horizonte: roll ≤ 3° salvo intenção marcada.
9. Clearance: câmera ≥ 0,5 do chão, ≥ 1,5 de plantas em cruz, nunca dentro de bloco.
10. **Item encaixado** (canudo, balde, qualquer prop/feixe ligado a ator) — ver (h).
11. Braço para cima com pitch < −12°: abertura |z| ≥ 30° (senão cobre o rosto).

**Por take**:
12. ≥ 90 % dos quadros aprovados em 1–7 e 100 % no(s) quadro(s) de beat (gole, susto, punchline).
13. Quadro 1: sujeito em x 0,30–0,70, y 0,25–0,60, sem oclusor.
14. Velocidades da §3.e (translação, °/s, variação de tamanho, fov) e assentamento nos últimos 0,3 s.
15. Lado do eixo igual ao `screen_map` da cena; 30° em relação à cutscene anterior do mesmo sujeito.
16. Cada personagem relevante tem ≥ 1 mudança de silhueta grande (§4) e nunca fica > 0,6 s sem movimento visível
    além do idle.
17. Stills de QA antes do render final: t = 0,1 s, beat principal, fim − 0,1 s; reprovar o card se 1–11 falharem.

### (h) Itens e adereços (canudo, balde, objetos na mão)

Canudo / feixe até a boca:
- A **água fica à frente** do personagem: `dot(normalize_xz(fonte − pés), fwd_body) ≥ cos 70°`. O personagem **olha a água**
  (head_x +10…+25, cabeça para baixo-frente), nunca de costas para ela.
- O trecho do canudo nos 0,6 bloco finais chega pela **frente do rosto**: `dot(normalize(p_0,6 − boca), fwd_face) ≥ 0,5`
  (≤ 60° da normal da face). Ponto final a ≤ 0,08 da `mouth_position`.
- Amostrar o tubo em 24 pontos: nenhum dentro da caixa da cabeça (cubo de 0,5 + 0,03 de margem) nem do tronco, exceto o
  último ponto na boca.
- Na tela: o canudo não cruza a faixa dos olhos (retângulo de y 1,66–1,80 da cabeça projetado); comprimento visível
  ≥ 0,5 bloco projetado (senão some).
- Encenação padrão de "beber": personagem na margem, corpo 35–40° da lente, água à frente e um pouco para o lado oposto ao
  da câmera; o canudo sai da boca para a frente-baixo e mergulha **na lead room**; câmera 3/4 do lado aberto.
  (`_straw_tip` atual procura "ao lado e um pouco atrás" — inverter: `feet + fwd·1,6 + side_longe_da_câmera·0,6`.)
- `mouth_position` antiga tinha o sinal de yaw invertido (boca atrás da cabeça para yaw ≠ 0/180) — corrigida em kin.py
  em 21/10; mesmo assim a regra de encenação acima é obrigatória.

Item na mão (balde, picareta): fica na mão do **lado da câmera** ou erguido (rarm_x −60…−100) para sair da silhueta do
tronco; sobreposição do bbox do item com o tronco na tela ≤ 30 %.

---

## 4. Coreografia e atuação para um boneco sem cotovelo e sem joelho

### 4.1 O que torna o boneco expressivo
1. **Staging de silhueta**: a pose tem de ler preenchida de preto. Com o corpo a 0–25° da lente, o braço só sai da
   silhueta se **abrir** (eixo z); movimento puro para a frente (eixo x) encurta em direção à lente e some. Com o corpo a
   25–50°, o eixo x volta a ler. Portanto: de frente use z; a 3/4 use x + z. Mão sempre ≥ 0,15 bloco fora do contorno do
   tronco na tela.
2. **Antecipação**: movimento contrário antes da ação, 15–30 % da amplitude, 0,08–0,15 s (a 60 fps: 5–9 quadros).
   Pulo: agacha (lean −6, braços x +25 para trás, sy 0,92) → pula.
3. **Exagero**: para 6–11 anos e sem rosto animado, amplitudes 1,3–1,6× o "realista". Gesto de fala humano de 15° vira 25°.
4. **Overshoot e settle**: chegada em `out_back` com 10–20 % além da pose, assenta em 0,15–0,30 s.
5. **Follow-through / overlap**: o corpo lidera; cabeça chega 0,04–0,07 s depois; braços 0,08–0,12 s depois; o braço
   "de trás" (longe da câmera) mais 0,05 s. Nada começa e termina no mesmo quadro.
6. **Assimetria (anti-twinning)**: os dois braços nunca iguais: diferença de 20–40 % de amplitude e 0,05–0,12 s de
   defasagem; um braço faz o gesto principal, o outro um secundário menor. Entre personagens: offsets 0,12–0,25 s e poses
   diferentes para a mesma emoção.
7. **Linha de ação**: lean + inclinação da cabeça na mesma curva (lean −8 com head_x +8 = curva de raiva para a frente;
   lean +10 com head_x −12 = curva de susto para trás). **Contrapposto**: corpo girado 10–15° para um lado, cabeça 10–20°
   para o outro.
8. **Pulos e squash**: hop 0,2–0,5 bloco; na aterrissagem sy 0,88 / sx=sz 1,06 por 0,06–0,08 s, `out_back` para 1.
   Pulinhos de alegria a 1,8–2,2 Hz (gap 0,45–0,55 s).
9. **Cabeça é o rosto**: inclinação lateral (head_z ±10–18) comunica dúvida, deboche, fofura; aceno (head_x) comunica fala;
   nunca deixe a cabeça parada > 0,5 s. Limites legíveis: head_y ±40 (além disso vira perfil), head_x −35…+30.
10. **Moving hold**: em pose segurada, manter 1–3° de deriva + idle; hold parado = boneco travado. Hold mínimo de uma
    pose-chave: 0,25 s (criança precisa ler).
11. **Uma grande mudança de silhueta por take** no mínimo (área do contorno muda ≥ 30 %): a pose T parada do c02 não tem.
12. **Braço acima do ombro**: montar a direção (abertura β 18–140°, giro |θ| ≲ 25°) e converter com `arm_euler`
    (actors.md v0.4); nunca x −170 cru com z pequeno — de baixo cobre o rosto.
13. **Pose de apresentador** (substitui "virar para apontar"): corpo 15–30° para a lente, braço do lado do objeto
    x −40…−80, z +50…+80 (abre na diagonal para trás-lado), cabeça +15–25° para o objeto e volta à lente na punchline.
14. **Apontar atravessando a tela**: corpo a 30–45°, braço x −85…−95 com z +20…+35 para o alvo do lado oposto da tela;
    nunca apontar para a lente (encurta). Alinhar ao alvo com `arm_aim`.
15. **Tempo de fala real**: usar os timestamps da transcrição para pôr os acentos de gesto/aceno nas sílabas tônicas.

### 4.2 Tabela de amplitudes e ritmo por emoção

Sinais: lean > 0 = para trás; head_x < 0 = olha para cima; braços x < 0 = para a frente/cima; abertura = rarm_z +A /
larm_z −A. "Braço G" = gesto principal, "Braço S" = secundário.

| Emoção | Corpo (lean / yaw / hop) | Cabeça | Braço G (x / abertura) | Braço S | Ritmo | Timing |
|---|---|---|---|---|---|---|
| **Fala normal** | lean −2…−5 nas ênfases; yaw ±5–8 a 0,7 Hz | head_x ±6–9 a 2,5–3,5 Hz (tônicas); head_y ±6–10 a 0,8–1,2 Hz; head_z ±5 | x −30…−60, z +15…+30; batidas ±12–18 a 1,5–2,2 Hz | x −10…−20, z 8–12; troca de braço G a cada 1–1,5 s | 2–3 Hz | ataque 0,12–0,18 s |
| **Fala enfática / argumento** | lean −6…−10; passo à frente 0,2 | head_x ±10–14 | os dois braços: x −50…−80, z +25…+45, batidas ±20–25 a 2 Hz (defasados 0,08 s) | — | 2 Hz | `out` 0,1 s |
| **Alegria / comemoração** | antecipação lean −6 → hop 0,3–0,5 a 2 Hz; lean +6…+8 no topo; squash na queda | head_x −12…−20; head_z ±10 alternando | V assimétrico: x −150…−160, z +30…+40, sacode ±15–20 a 3–4 Hz | x −120…−140, z −25…−35, defasado 0,08–0,12 s | hops 2 Hz; braços 3–4 Hz | subida `out_back` 0,18 s |
| **Susto** | congela 0,05 s → tranco 0,10–0,14 s: lean +14…+18, hop 0,15–0,25, passo atrás 0,3 | head_x −12…−18, head_z ±8 | x −50…−70, z +70…+90 ("mãos para cima") | x −20…−35, z −45…−60 (menor) | tremor ±2–3° a 7–9 Hz, decay 4–6 em 0,6 s | `out_back`; hold 0,5–1,0 s com moving hold |
| **Raiva** | lean −8…−14; pisão (hop 0,1 com squash forte sy 0,85) | head_x +8…+12 (encara por baixo) | jabs apontando: x −85…−95 em 2–3 batidas ±12–15 a 2,5–3 Hz | rígido: x +15…+25 (para trás), z −10…−15 | tremor de corpo ±1,5–2,5° a 8–12 Hz | ataques secos `out` 0,08–0,12 s |
| **Deboche / zoeira** | lean +6…+10; yaw ±10 a 1,5–2 Hz (rebolado) | head_z ±12–18; riso head_x −5…−12 a 4–5 Hz | aponta a vítima: x −80…−90, z +15; ou "dancinha" x ±25 a 2 Hz | x +10…+20 (para trás), balança ±5 a 4–5 Hz | riso 4–5 Hz | solto, `smooth` |
| **Cansaço** | lean −10…−15 (curvado); balanço ±2–3° a 0,3–0,5 Hz; arfar lean ±2 a 1,8–2,2 Hz | head_x +15…+25 (cabeça baixa) | pendurado: x −5…−10, z ±3 | igual, defasado | 0,3–0,5 Hz (arfar 2 Hz) | tudo lento: `in_out` 0,4–0,6 s, arrasto |
| Bônus — **dúvida** | yaw 10° para um lado | head_z +12…+18 para o outro; head_x −5 | x −20, z +20 (mão "aberta") | parado | 0,5 Hz | hold 0,4 s |
| Bônus — **beber (barriga)** | lean +4…+8 a cada gole; hop 0,15 ao final | head_x +10…+20 (olha a água à frente); gole +5° a 1,5–2 Hz | x −15…−25, z +18…+25 (cotovelos imaginários "abrindo") | espelho menor, defasado | 1,5–2 Hz (goles) | gole `out` 0,12 s |

Calibração: os presets atuais de acts.py estão abaixo disso — `talk` (head_x 4°, braço ±9°), `walk` (braços ±25°),
`celebrate` (−170° cru, z 18°, offset 0,06 s) e `shock` (simétrico) devem subir para esta tabela. Andar: pernas ±35–45°,
braços ±40–50°, bob 0,04–0,06 a 2× a cadência, lean −4. Correr: pernas ±55–65°, braços ±60–75°, lean −10…−14.

---

## 5. Receita de layout para um card (ordem obrigatória)

1. **Ideia do take em uma frase** (quem é o sujeito, qual o beat, qual objeto precisa aparecer).
2. **Lado da câmera** pelo `screen_map` da cena e pela necessidade de mostrar o objeto (regra c09: para mostrar o que
   eles olham com rosto, câmera atrás do objeto).
3. **Blocking**: arco aberto, distâncias (§3.a), objeto atrás-lado ou na lead room; nada de `face=<ator>` cru — sempre
   `cheat()`; `point` vira apresentador ou apontar atravessando a tela.
4. **Plano e altura** pela intenção (§3.b, §3.c); mira pela fórmula do terço.
5. **Movimento** pela tabela (§3.e), definido relativo ao yaw do sujeito; azimute fino pelo solver.
6. **Atuação** pela tabela (§4.2), com antecipação, assimetria, beat entre 25 % e 65 % do take.
7. **Validação** (§3.g) + stills de QA → só então render final.

---

## 6. Dez regras de ouro

1. **Nunca de perfil**: θ entre 60° e 120° reprova qualquer personagem com ≥ 10 % da altura da tela; o sujeito vive em
   15–40° (3/4), máximo 50°.
2. **Costas só com motivo**: OTS de primeiro plano, *turn reveal* de até 0,5 s ou saída de cena — nunca no sujeito.
3. **O personagem se abre para a câmera, não para o alvo**: corpo gira no máximo 35° fora da lente, a cabeça faz o resto até
   50°; alvo a mais de 110° = pose de apresentador ou mudar a câmera de lugar.
4. **Para mostrar o que eles olham, a câmera fica atrás do que é olhado** (eles de frente, o objeto em primeiro plano ou ao lado).
5. **Grupo em arco aberto, nunca em fila**: 2 nos terços, 3 em triângulo, sem sobreposição de silhueta > 15 %.
6. **Nada de fatia na borda**: personagem inteiro (≥ 92 % visível) ou fora; meio corpo na borda só como OTS desfocado.
7. **Cabeça inteira e olhos no terço superior**; no último quadro o sujeito tem ≥ 15 % da altura; no primeiro está no
   centro (eye-trace do gameplay).
8. **Um movimento motivado por take**, relativo à frente do sujeito, com ease, assentado nos últimos 0,3 s; nenhum
   arco passa por perfil; nada de câmera atravessando capim ou folhagem sobre o rosto.
9. **Item perfeitamente encaixado**: água à frente, canudo entra pela frente do rosto, nenhum ponto dentro da cabeça ou do
   tronco, item da mão fora da silhueta do tronco — conferido em still antes do render.
10. **Atuação 1,5× maior que a vida, assimétrica e com antecipação**: pelo menos uma grande mudança de silhueta por take,
    braços abrindo (z) quando de frente, cabeça sempre viva, nunca dois braços nem dois personagens iguais.
