# Receitas de plano (código pronto)

Legenda de status: ✅ **renderizado e conferido no jogo** · 🧮 só validado numericamente (analisador/preview) — conferir com `stills()` antes de prometer.
Setup comum:
```python
import sys; sys.path.insert(0, r"C:\Users\mathe\.claude\skills\minecraft-cinematic\scripts")
from cinecam import *
```
`S` = ponto do herói (centro do que a câmera deve valorizar), `g` = altura do chão (`Terrain.ground_at`).

## 1. Revelação por oclusor + DoF (ref R-A, floresta) ✅
Parede de folhas a 1–3 blocos da lente, desfocada; a câmera desliza e revela o herói nítido.
```python
cmds = [f"fill {cx-7} {g+1} {cz-4} {cx-6} {g+3} {cz+4} minecraft:spruce_leaves[persistent=true]",   # oclusor (persistent: não apodrece)
        f"fill {cx-7} {g+4} {cz-2} {cx-6} {g+4} {cz+3} minecraft:spruce_leaves[persistent=true]"]
rig = Rig(fps=30, subframes=8)
reveal = track([(cx-10.5, g+1.5, cz+2.5), (cx-10.2, g+1.7, cz-3), (cx-9.0, g+2.0, cz-11)], S, 3.4,
               ease="soft_in_out", fov=(64, 60), name="leaf_reveal")
rig.add(reveal.with_handheld("subtle").with_roll((-3, 0)).with_dof(S, aperture=0.85))
rig.add(from_pose(rig.last_pose(), [(cx-5.0, g+2.3, cz-7.0)], S, 2.0, ease="smooth", fov=(60, 52), name="push")
        .with_handheld("subtle").with_dof(S, aperture=(0.85, 0.55)))
render(rig, "reveal", scene=Scene(time=12100, anchor=S, commands=cmds), world=World(seed=4242),
       settings=Settings(renderDistance=10), size=(1920,1080), supersample=2, grade="cinematic")
```
Resultado visto: folhas borradas ocupam o quadro → deslizam → santuário nítido, fundo desfocado, vinheta. Custo medido: 162 quadros 4K SS, 8 subframes ≈ 2 min de jogo + 40 s de DoF. Use `ease="smooth"` na emenda (com `"out"` o analisador acusa jerk em t≈3,4 s).

## 2. Aerial swoop → órbita (ref R-C, abertura de Hide&Seek) ✅
```python
rig = Rig(fps=30, subframes=8)
rig.add(crane((S[0]+48, S[1]+40, S[2]-48), (S[0]+15, S[1]+3, S[2]-15), S, 2.4, arc=7, ease="launch", fov=(82, 66), name="swoop"))
rig.add(orbit_from(rig.last_pose(), S, sweep_deg=85, T=3.2, radius_end=6, height_end=0.5, look_offset=(0,0.5,0), name="orbit")
        .with_handheld("subtle").with_roll((0, -8)))
```
Visto: borrão forte no 1º frame (chegada com velocidade), órbita suave. **Armadilhas medidas:** com `radius_end=9` o herói ficou pequeno demais; termine a órbita a 5–7 blocos para herói de 4–5 blocos de altura. O bloom do preset antigo estourava neve; presets atuais já mais suaves. Confira `Terrain.clearance(rig)`: a órbita final entrou numa árvore (surface) em um teste.

## 3. Whip de transição em duas pontas (R-C, 3,8 s) 🧮
Plano A termina em whip; corte; plano B começa já em whip no mesmo sentido e assenta.
```python
A_end = rig.last_pose()
rig.add(whip((A_end["x"],A_end["y"],A_end["z"]), (A_end["yaw"], A_end["pitch"]), (A_end["yaw"]-110, A_end["pitch"]), 0.2, name="whipA"))
# plano B (outra cena/ângulo): começa girando no MESMO sentido e desacelera até o enquadramento final
rig.add(pan(B_pos, (B_yaw+110, B_pitch), (B_yaw, B_pitch), 0.2, ease="out", name="whipB"), cut=True)
rig.add(<movimento B normal começando em (B_yaw,B_pitch)>)
```
Use `subframes=12`. O corte cai no pico do borrão; sem blur atravessando o corte (o Rig recorta). Teste visual pendente.

## 4. Plano-sequência de escala (ref R-B, skyblock) 🧮
Baixo olhando para cima → sobe e recua girando com roll → tilt até top-down.
```python
rig.add(orbit(S, radius=(5,26), start_deg=200, end_deg=330, height=(-1.5,14), T=4.0, ease="smooth", look_offset=(0,2,0),
              fov=(58,78)).with_roll((0,-14)).with_handheld("subtle"))
rig.add(from_pose(rig.last_pose(), [(S[0]+8, S[1]+55, S[2]+8)], (S[0], S[1]-20, S[2]), 2.5, ease="soft_in_out", fov=(78,85)).with_roll((-14,0)))
```
Vale pôr 2–3 oclusores no caminho (blocos grandes, ilhas) e speed lines no pós (fora desta skill hoje).

## 5. Vertigem (dolly-zoom) para dar peso a uma revelação 🧮
```python
rig.add(dolly_zoom(far_pos, near_pos, S, 2.6, fov0=40, ease="smooth"))
```
Escolha o sujeito no meio de um cenário com profundidade (fundo esticando é o efeito).

## 6. Voo por corredor (drone, perseguição) 🧮
```python
rig.add(through([p0, p1, p2, p3], 4.0, fov=88, bank=0.4, lag=0.25))
```
Verifique `Terrain.clearance` (0,5+). Combine `with_shake([(1.2, 1.0, 0.25)])` em impactos.

## 7. Herói low-angle com punch (ref heroica) 🧮
```python
rig.add(hold((S[0]+4, g+0.5, S[2]-4), (S[0], g+4, S[2]), 0.6, fov=58).with_handheld("breath"))
rig.add(push_in((S[0]+4, g+0.5, S[2]-4), (S[0]+2.2, g+0.7, S[2]-2.2), (S[0], g+3.5, S[2]), 0.9, ease="out_back", fov=(58, 50)))
```

## Calibração de sinais (conferir 1× por sessão com `stills`)
- Yaw/pitch/aim: **validado** (torre centrada em todos os quadros da órbita).
- Roll: `with_roll((0,-8))` inclina o horizonte no sentido horário visto da câmera? **Conferir num still** antes de depender do sentido (qualquer dutch ± serve visualmente, mas se a história pede "tombar para a direita", teste).
- Distância de segurança: oclusor tem de estar ≥ 0,4 bloco da lente (near plane 0,05) — folhas colando na lente viram parede escura.

## Checklist rápido de qualidade (antes de entregar)
☐ preview sem avisos (ou avisos explicados) ☐ clearance ≥ 0,5 ☐ stills início/meio/fim com herói nos terços ☐ ao menos 2 camadas de profundidade (oclusor/herói/fundo) ☐ roll e fov com ease ☐ DoF coerente (foco no herói) ☐ `report.warnings` vazio ☐ contact sheet olhado.
