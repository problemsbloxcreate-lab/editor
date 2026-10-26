"""CineCam v1.0 — 3 exemplos 9:16 no estilo dos Shorts de referência (cortes na fala, atuação por molas).
A) diálogo Kadu × Stick (diamante)   B) ação: Problems corre, pula o muro, creeper   C) gancho: Kadu fala para a câmera
python showcase.py [--fast] [--check] [A B C]"""
import sys, math
sys.path.insert(0, r"C:\Users\mathe\.claude\skills\minecraft-cinematic\scripts")
import numpy as np
from cinecam import *
from cinecam.turma import skin
from cinecam.atua import Ator
from cinecam.actors import POSE, Mob
from cinecam.sets import SetBuilder, site
from cinecam.render import render_batch, Shot

FAST = "--fast" in sys.argv
NOBLUR = "--sem-blur" in sys.argv            # opção: sem motion blur e sem desfoque de lente
SUFFIX = ("_fast" if FAST else "") + ("_sem_blur" if NOBLUR else "")
CHECK = "--check" in sys.argv
WHICH = [a for a in sys.argv[1:] if a in ("A", "B", "C")] or ["A", "B", "C"]
FPS, SUB = 30, (1 if FAST else 6)
SIZE = (540, 960) if FAST else (1080, 1920)


def make_set(wall=False):
    sb = SetBuilder(site("plains"), r=20, seed=5)
    sb.ground("plains")
    sb.keep_free_rect(-8, -10, 8, 12)
    if wall:
        sb.box(-3, 0, -2, 3, 0, -2, "minecraft:mossy_cobblestone")
    sb.tree(-6, -9, "oak"); sb.tree(7, -11, "birch"); sb.tree(-10, -3, "oak")
    sb.dress("plains", density=0.8)
    return sb


def chest(actor, t, up=1.2):
    p = actor.at(np.atleast_1d(np.asarray(t, float)))
    return np.stack([p[:, 0], p[:, 1] + up + p[:, POSE["hop"]] * 0.6, p[:, 2]], axis=1)


def between(a, b, t, up=1.2):
    return (chest(a, t, up) + chest(b, t, up)) / 2


def shot(rig, p0, p1, aim, t0, T, fov=58, ap=0.3, focus=None, cut=True):
    """Plano de T s começando no tempo de filme t0; aim(t) -> ponto (n,3); câmera de p0 a p1 (drift/push-in lento)."""
    mv = track([p0, p1], lambda tau: aim(t0 + tau * T), T, ease="smooth", fov=fov)
    d = float(np.linalg.norm(np.array(p0) - aim(t0)[0]))
    mv = mv.with_dof(focus or (d, float(np.linalg.norm(np.array(p1) - aim(t0 + T)[0]))), ap)
    rig.add(mv, cut=cut)
    return rig


def front(f, yaw, dist, h, side=0.0):
    """Ponto a dist blocos na frente de f (pés) pelo yaw do personagem, deslocado side para o lado dele, altura h."""
    r = math.radians(yaw)
    fwd = np.array([-math.sin(r), 0, math.cos(r)]); right = np.array([-math.cos(r), 0, -math.sin(r)])
    return tuple(np.asarray(f, float) + fwd * dist + right * side + [0, h, 0])


# ------------------------------------------------------------------------------------------------ A) diálogo
def clip_A():
    sb = make_set()
    c0 = sb.feet(0, 0)
    K, S = c0 + [0.85, 0, 0], c0 + [-0.85, 0, 0]
    k = Ator("kadu", skin("kadu"), K, yaw=14, item="minecraft:diamond")
    s = Ator("stick", skin("stick"), S, yaw=-14)
    kh, sh_ = np.array(K) + [0, 1.62, 0], np.array(S) + [0, 1.62, 0]
    k.look(0.0, sh_, 0.6); s.look(0.0, kh, 0.6)
    k.talk(0.25, 1.85, text="Stick! Olha o que eu ACHEI!")
    k.hold_item(0.55, 9); k.pose(0.6, "mostra")
    s.pose(1.95, "medo", snap=3).talk(2.05, 3.3, text="UM DIAMANTE?!")
    s.pose(2.5, "grita")
    k.pose(2.2, "idle")
    s.jump(3.45, h=0.95); s.pose(3.92, "comemora"); s.pose(5.2, "idle")
    k.pose(3.6, "rindo"); k.point_at(5.1, np.array(K) + 0.55 * (np.array(S) - np.array(K)) + [0, 1.2, 0.35], elbow=-0.5); k.talk(5.15, 6.5, text="E esse aqui é seu, parceiro!")
    s.pose(6.55, "palmas"); s.talk(6.6, 7.7, text="Melhor amigo!"); s.pose(7.75, "joinha")
    k.pose(6.7, "joinha")
    T = 8.6
    ka, sa = k.build(T), s.build(T)
    rig = Rig(fps=FPS, subframes=SUB, shutter=0.5)
    two = lambda t: between(ka, sa, t, 1.45)
    c = np.array(sb.feet(0, 0))
    shot(rig, tuple(c + [0.25, 1.6, 4.6]), tuple(c + [0.2, 1.6, 4.2]), two, 0.0, 1.95, fov=58, cut=False)
    shot(rig, front(S, -14, 2.5, 1.65), front(S, -14, 2.2, 1.65), lambda t: chest(sa, t, 1.55), 1.95, 1.5, fov=56)
    shot(rig, tuple(c + [0.1, 1.25, 5.4]), tuple(c + [0.1, 1.25, 5.1]), lambda t: between(ka, sa, t, 1.5), 3.45, 1.7, fov=60, ap=0.2)
    shot(rig, front(K, 14, 2.6, 1.65), front(K, 14, 2.3, 1.65), lambda t: chest(ka, t, 1.55), 5.15, 1.45, fov=56)
    shot(rig, tuple(c + [0.2, 1.6, 4.4]), tuple(c + [0.15, 1.6, 3.9]), two, 6.6, T - 6.6, fov=58)
    return Shot("showcase_A" + SUFFIX, rig=rig, scene=sb.scene(time=4000, anchor=tuple(c + [0, 4, 2])),
                settings=Settings(renderDistance=10, simulationDistance=6, worldTicks=True), anim=Anim([ka, sa]), size=SIZE, blur=not NOBLUR, dof=(False if NOBLUR else None)), (ka, sa)


# ------------------------------------------------------------------------------------------------ B) ação
def clip_B():
    sb = make_set(wall=True)
    P0 = sb.feet(0, -9)
    p = Ator("problems", skin("problems"), P0, yaw=0, energy=1.2)
    p.walk(0.0, 2.15, to=(P0[0], P0[2] + 10.4), gait="run")
    p.jump(1.08, h=1.35, air=0.55)
    p.pose(2.4, "procura")
    end = np.array(sb.feet(0, 1.4))
    cre = sb.feet(1.6, -4.2)
    p.look(2.5, np.array(cre) + [0, 1.4, 0], 1.0)
    p.pose(3.55, "susto", snap=3); p.look(3.45, None)
    p.walk(4.4, 5.4, to=(end[0] - 5.5, end[2] + 2.5), gait="run")
    T = 5.0
    pa = p.build(T)
    # creeper: anda devagar até o muro (atrás dele) e para
    def cfn(times):
        out = np.zeros((len(times), 12))
        u = np.clip((times - 2.2) / 1.6, 0, 1)
        out[:, 0] = cre[0]; out[:, 1] = cre[1] + 0.85; out[:, 2] = cre[2] - 2.5 + 2.5 * (u * u * (3 - 2 * u))
        out[:, 3] = 0; out[:, 6:9] = (times >= 2.3)[:, None] * 1.0; out[:, 9] = cre[1]; out[:, 10] = np.where((u > 0) & (u < 1), 0.35, 0); out[:, 11] = 20 * times
        return out
    mob = Mob("creeper", "minecraft:creeper", (cre[0], cre[1] + 0.85, cre[2]), fn=cfn)
    rig = Rig(fps=FPS, subframes=SUB, shutter=0.5)
    # 1) foge para a câmera: travelling para trás na frente dele, baixo
    def lead(t):
        return chest(pa, t, 1.4)
    z0, z1 = pa.at(np.array([0.0]))[0, POSE["z"]], pa.at(np.array([1.08]))[0, POSE["z"]]
    shot(rig, (P0[0] + 0.5, P0[1] + 1.55, z0 + 3.4), (P0[0] + 0.4, P0[1] + 1.55, z1 + 3.0), lead, 0.0, 1.08, fov=60, cut=False)
    # 2) pulo do muro: aberto 3/4, baixo
    w = np.array(sb.feet(0, -2))
    shot(rig, tuple(w + [1.4, 1.35, 5.6]), tuple(w + [1.2, 1.35, 5.9]), lambda t: chest(pa, t, 1.2), 1.08, 1.27, fov=62, ap=0.2)
    # 3) para e procura (médio de frente)
    shot(rig, tuple(end + [0.3, 1.65, 2.8]), tuple(end + [0.25, 1.65, 2.5]), lambda t: chest(pa, t, 1.5), 2.35, 0.95, fov=56)
    # 4) insert do creeper surgindo atrás do muro (contra-plongée)
    shot(rig, tuple(np.array(cre) + [-1.2, 1.35, 3.4]), tuple(np.array(cre) + [-1.1, 1.35, 3.0]),
         lambda t: np.stack([np.full(np.size(t), cre[0]), np.full(np.size(t), cre[1] + 1.2), mob.at(np.atleast_1d(t))[:, 2]], axis=1), 3.3, 0.6, fov=50, ap=0.35)
    # 5) susto (médio, de frente)
    shot(rig, tuple(end + [0.25, 1.65, 2.9]), tuple(end + [0.2, 1.65, 2.7]), lambda t: chest(pa, t, 1.5), 3.9, 0.55, fov=58, ap=0.2)
    # 6) fuga: aberto com os dois
    shot(rig, tuple(end + [1.8, 1.6, 4.8]), tuple(end + [1.2, 1.6, 5.0]), lambda t: (chest(pa, t, 1.1) * 0.6 + np.array([[cre[0], cre[1] + 1.1, cre[2]]]) * 0.4),
         4.45, T - 4.45, fov=62, ap=0.15)
    return Shot("showcase_B" + SUFFIX, rig=rig, scene=sb.scene(time=4000, anchor=tuple(end + [0, 4, -2])),
                settings=Settings(renderDistance=10, simulationDistance=6, worldTicks=True), anim=Anim([pa], mobs=[mob]), size=SIZE, blur=not NOBLUR, dof=(False if NOBLUR else None)), (pa,)


# ------------------------------------------------------------------------------------------------ C) gancho
def clip_C():
    sb = make_set()
    K = sb.feet(0, 0)
    k = Ator("kadu", skin("kadu"), K, yaw=0, energy=1.15)
    k.talk(0.1, 1.95, text="Você é IDOSO e não SABIA!")
    k.point_at(0.45, np.array(K) + [-3.2, 2.0, 1.0])
    k.pose(2.0, "ombros"); k.talk(2.05, 3.55, text="Sabe aquele bloco que todo mundo usa?")
    k.pose(3.65, "pensando")
    k.pose(4.65, "grita", snap=3); k.talk(4.7, 5.6, text="Ele tem SETE anos!")
    k.pose(5.7, "rindo")
    k.pose(6.9, "joinha"); k.talk(6.95, 7.8, text="Se inscreve!")
    T = 8.2
    ka = k.build(T)
    rig = Rig(fps=FPS, subframes=SUB, shutter=0.5)
    c = lambda up: (lambda t: chest(ka, t, up))
    shot(rig, front(K, 0, 3.3, 1.65, 0.2), front(K, 0, 2.9, 1.65, 0.15), c(1.45), 0.0, 2.0, fov=58, cut=False)
    shot(rig, front(K, 0, 2.3, 1.68, 0.12), front(K, 0, 2.15, 1.68, 0.1), c(1.58), 2.0, 1.65, fov=56)
    shot(rig, front(K, 12, 2.6, 1.68), front(K, 10, 2.45, 1.68), c(1.55), 3.65, 1.0, fov=56)
    shot(rig, front(K, 0, 1.75, 1.72), front(K, 0, 1.6, 1.72), c(1.65), 4.65, 1.0, fov=54, ap=0.18)
    shot(rig, front(K, 0, 3.0, 1.6, 0.2), front(K, 0, 2.7, 1.6, 0.15), c(1.4), 5.65, T - 5.65, fov=58)
    return Shot("showcase_C" + SUFFIX, rig=rig, scene=sb.scene(time=4000, anchor=tuple(np.array(K) + [0, 4, 2])),
                settings=Settings(renderDistance=10, simulationDistance=6, worldTicks=True), anim=Anim([ka]), size=SIZE, blur=not NOBLUR, dof=(False if NOBLUR else None)), (ka,)


if __name__ == "__main__":
    shots = []
    for w in WHICH:
        sh, actors = {"A": clip_A, "B": clip_B, "C": clip_C}[w]()
        if CHECK:
            a = actors[0]
            for t in np.arange(0, 2.6, 0.2):
                q = a.at(np.array([t]))[0]
                print(w, f"t={t:.1f} z={q[POSE['z']]:.2f} hop={q[POSE['hop']]:.2f} yaw={q[POSE['yaw']]:.0f}")
            print(w, "rig", sh.rig.duration)
            continue
        shots.append(sh)
    if shots:
        for r in render_batch(shots, world=World(seed=4242)):
            print(r.get("ok"), r.get("final"), r.get("error"))
