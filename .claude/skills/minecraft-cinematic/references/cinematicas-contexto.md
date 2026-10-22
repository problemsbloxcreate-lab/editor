# Cinemáticas que recriam o CONTEXTO da cena (feedback do Matheus, 22/10/2026 — vídeo "Chico BRoyale")

**O que ele reprovou:** "suas animações estão todas iguais, é só os personagens gesticulando numa ilha; simule mais o contexto do que está acontecendo exatamente na cena; se o personagem estiver correndo, continue o movimento; se tiver uma explosão do lado direito, mantenha assim; nas cenas de conversa gesticula mais e com mais interpolação, suaviza mais os movimentos e deixa mais contínuos e fluidos, tem momentos que eles ficam literalmente parados." E: **"por que a skin do Chico virou o Stick?"**

## Regras
1. **Skin do criador = o PNG dele.** Nunca trocar por um personagem da turma com apelido parecido (o `stick` tem alias "chico", mas o Chico do vídeo tem skin própria). Peça/ache o PNG e use `{"who": "<caminho.png>", "name": "chico"}`; as ações referem-se ao `name`.
2. **Antes da ficha, leia a CENA, não só a frase**: abra `ctx_<id>.jpg` das duas POVs (1,5 s antes → fim) e anote: quem está fazendo o quê (correndo? caindo? voando em espectador? comendo?), de que LADO vem a ameaça/explosão, o que se mexe em volta (mobs, TNT caindo, blocos sendo colocados), dia/noite/lugar. A cinemática é esse momento visto por uma câmera de cinema — não "dois bonecos falando".
3. **Movimento contínuo**: quem corre entra correndo e sai correndo — `choreo.run_lin()` (velocidade constante, membros balançando desde o 1º quadro), nunca `walk` com ease que acelera e freia dentro do take. Queda/voo = `choreo.fly()` com chaves lineares + câmera que acompanha (`choreo.follow_cam()`).
4. **Ação do lado certo e no segundo certo**: TNT real não tem hora marcada (a gravação só começa depois do mundo assentar), então a explosão é feita com Prop: `choreo.tnt(st, sb, dx, dz, fall=(t0, t1, h), boom=t)` (cai, pisca, estoura em bola de fogo + fumaça + destroços em arco com gravidade) ou `choreo.explosion(st, ponto, t)`. Blocos sendo colocados = `choreo.pop_block()` (escala 0→1 out_back). Mobs andando = `choreo.mob_walk()` (já em movimento; `age` linear anima patas/cabeça).
5. **Ninguém parado**: quem fala tem `talk(energy≥1.3)` cobrindo o take INTEIRO (emphatic nas reclamações/sustos); quem ouve reage (`look` → `nod`/`laugh`/`shrug`); gestos extras (`point`, `present`, `present_to`) sobrepostos à fala. Nenhum trecho > ~0,5 s sem algo se mexendo no personagem principal.
6. **Varie o lugar/luz pela cena**: noite da gameplay = `time 13000` (crepúsculo arroxeado — 14300+ fica escuro demais e nada aparece); paredão de terracota, floresta, cratera, queda no vazio etc. conforme o ctx.

## Gotchas pagos nesta rodada
- **Lote com o MESMO lugar**: blocos de uma ficha ficam no mundo para a próxima (render_batch numa sessão só). Toda ficha que reaproveita coordenadas começa limpando o volume (`["box", [-20,-40,-24,22,24,20,"air"]]`) e reconstrói o cenário.
- **NBT 1.20.1**: TNT usa `Fuse` (maiúsculo); `fuse` é ignorado → explode em 4 s durante o assentamento e esburaca o cenário.
- **Mobs hostis**: o mundo vem em pacífico → `["raw", ["difficulty normal"]]` (NoAI não ataca). Zumbi/esqueleto queimam no sol do fim de tarde → `husk`, ou capacete via `ArmorItems`.
- **`wobble(ramp=0)` = divisão por zero** (NaN no canal) → use ramp ≥ 0,02.
- **plongee muito alto** achata o personagem (parece deitado) e esconde o que está dentro de buraco → `establish` terminando em ~4 blocos de altura ou plongee baixo (height ~4, back ~7).
- **RAM**: o jogo precisa de ~3 GB livres; com Premiere + outro Minecraft aberto a JVM morre ("insufficient memory"). Feche o Premiere para renderizar; render final em lotes de 8 fichas (≈7 min cada) em primeiro plano.

## Referência
Fichas e coreografia completas: `D:\Pobrs\chico_broyale\cine\make_cards.py` + `builds.py` (16 takes: queda no vazio com destroços, espectador sobre a ilha, parede subindo × TNT explodindo, mobs cercando, fuga de explosões, comendo, golem+lobo, chuva de TNT, emparedado por blocos, camelo deitado + zumbi, TNT caindo na frente, baú, creeper × TNT, explosão do lado do baú, lobo/bode, arremessado no ar).
