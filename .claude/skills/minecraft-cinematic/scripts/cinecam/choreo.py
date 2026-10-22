"""choreo: peças de coreografia p/ cinemáticas que recriam o CONTEXTO da cena (aprendido no 'Chico BRoyale', 22/10/2026).
Use dentro de uma ficha com "python": def build(st, sb, card): ... (veja references/cinematicas-contexto.md).
- explosões por Prop (TNT pisca -> bola de fogo -> fumaça -> destroços em arco) no instante e do LADO certos (TNT real não tem hora marcada)
- quem corre já entra correndo e sai correndo (sem acelerar/frear dentro do take)
- quem fala gesticula o take inteiro (talk com energia), quem ouve reage (look/nod/laugh) — ninguém parado
Skin do criador = o PNG DELE (who=caminho, name=apelido), nunca um alias parecido da turma."""
import math
import numpy as np
from cinecam.actors import Prop
from cinecam.moves import track, lerp_point
from cinecam.camlib import Rig
from cinecam.acts import yaw_to

RNG = np.random.default_rng(11)
FIRE = ["minecraft:orange_concrete", "minecraft:yellow_concrete", "minecraft:white_concrete", "minecraft:orange_wool", "minecraft:yellow_wool"]
SMOKE = ["minecraft:gray_wool", "minecraft:light_gray_wool", "minecraft:gray_concrete_powder", "minecraft:light_gray_concrete"]
DEBRIS = ["minecraft:dirt", "minecraft:grass_block", "minecraft:stone", "minecraft:dirt", "minecraft:sand"]


def _prop(st, block, p, fn=None):
    pr = Prop("p%d" % len(st.props), block, p, fn=fn)
    st.props.append(pr)
    return pr


def tnt(st, sb, dx, dz, dy=0.0, fall=None, boom=None, size=1.0, debris=8):
    """TNT em (dx, dy, dz).  fall=(t0, t1, h): cai de h blocos e pousa em t1.  boom=t: pisca 0,6 s e explode em t."""
    base = sb.point(dx, dy, dz) - [0, 0, 0]
    p = _prop(st, "minecraft:tnt", base)
    if fall:
        t0, t1, h = fall
        p.key(0.0, y=base[1] + h).key(t0, y=base[1] + h).key(t1, ease="in", y=base[1])
        p.key(0.0, yaw=0).key(t1, ease="linear", yaw=200 * (t1 - t0))
        p.key(t1 + 0.12, ease="out", sy=0.8, sx=1.12, sz=1.12).key(t1 + 0.3, ease="out_back", sy=1, sx=1, sz=1)
    if boom is not None:
        t = boom
        for q in np.arange(max(0.0, t - 0.6), t, 0.15):          # pisca/estufa antes de estourar
            p.key(q, ease="out", sx=1.1, sy=1.1, sz=1.1).key(q + 0.07, ease="in", sx=1, sy=1, sz=1)
        p.key(t, ease="hold", sx=0, sy=0, sz=0)
        explosion(st, base + [0, 0.5, 0], t, size, debris)
    return p


def explosion(st, c, t, size=1.0, debris=8):
    c = np.asarray(c, float)
    for i in range(6):                                            # bola de fogo: incha rápido e some
        off = RNG.normal(0, 0.45 * size, 3); off[1] = abs(off[1]) * 0.6
        s1 = size * RNG.uniform(1.1, 2.0)
        p0 = c + off
        pr = _prop(st, FIRE[i % len(FIRE)], p0 - [0, 0.0, 0])
        pr.key(0.0, sx=0, sy=0, sz=0).key(t - 0.001, sx=0, sy=0, sz=0)
        pr.key(t + 0.02 * i, ease="hold", sx=0.2, sy=0.2, sz=0.2, y=p0[1])
        pr.key(t + 0.14 + 0.02 * i, ease="out", sx=s1, sy=s1, sz=s1, y=p0[1] - s1 / 2)
        pr.key(t + 0.5 + 0.03 * i, ease="in", sx=0, sy=0, sz=0, y=p0[1] + 0.6)
        pr.key(t, yaw=RNG.uniform(0, 90)).key(t + 0.5, yaw=RNG.uniform(90, 200))
    for i in range(7):                                            # fumaça: sobe, cresce e se desfaz
        off = RNG.normal(0, 0.6 * size, 3); off[1] = 0.2
        p0 = c + off
        s1 = size * RNG.uniform(0.9, 1.6)
        pr = _prop(st, SMOKE[i % len(SMOKE)], p0)
        pr.key(0.0, sx=0, sy=0, sz=0).key(t + 0.08, sx=0, sy=0, sz=0)
        pr.key(t + 0.25, ease="out", sx=s1 * 0.7, sy=s1 * 0.7, sz=s1 * 0.7)
        pr.key(t + 1.4, ease="in_out", sx=0, sy=0, sz=0, y=p0[1] + 2.8 * size)
        pr.key(t + 0.08, yaw=0, roll=0).key(t + 1.4, yaw=RNG.uniform(-80, 80), roll=RNG.uniform(-40, 40))
    for i in range(debris):                                       # destroços em arco com gravidade e giro
        ang = RNG.uniform(0, 2 * math.pi); sp = RNG.uniform(3.0, 6.5) * size; up = RNG.uniform(5.0, 8.5)
        v = np.array([math.cos(ang) * sp, up, math.sin(ang) * sp]); spin = RNG.uniform(-720, 720, 3); sc = RNG.uniform(0.25, 0.45)

        def fn(times, v=v, spin=spin, sc=sc):
            out = np.zeros((len(times), 9))
            tt = times - t
            vis = tt >= 0
            tt = np.clip(tt, 0, None)
            out[:, 0] = c[0] + v[0] * tt
            out[:, 1] = c[1] + v[1] * tt - 0.5 * 22.0 * tt ** 2
            out[:, 2] = c[2] + v[2] * tt
            out[:, 3:6] = np.where(vis, sc, 0.0)[:, None]
            out[:, 6] = spin[0] * tt; out[:, 7] = spin[1] * tt; out[:, 8] = spin[2] * tt
            return out
        _prop(st, DEBRIS[i % len(DEBRIS)], c, fn=fn)


def pop_block(st, sb, block, dx, dy, dz, t):
    p = sb.point(dx, dy, dz)
    pr = _prop(st, "minecraft:" + block, p)
    pr.key(0.0, sx=0, sy=0, sz=0).key(t, sx=0, sy=0, sz=0).key(t + 0.18, ease="out_back", sx=1, sy=1, sz=1)
    return pr


def mob_walk(st, mtype, a, b, t0, t1, T, age_rate=20.0, swing=0.35, dy=0.0):
    """mob andando de a=(dx,dz) a b, já em movimento (entra andando, sai andando)."""
    m = st.mob(mtype, a[0], a[1], dy=dy)
    pa, pb = st.sb.feet(a[0], a[1], dy) + [0, 0.5, 0], st.sb.feet(b[0], b[1], dy) + [0, 0.5, 0]
    y = yaw_to(pa, pb)
    m.key(0.0, x=pa[0], z=pa[2], yaw=y, swing=swing, age=0).key(t0, x=pa[0], z=pa[2])
    m.key(t1, ease="linear", x=pb[0], z=pb[2]).key(T + 0.5, ease="linear", age=age_rate * (T + 0.5))
    return m


def run_lin(st, n, to, t0, t1, run=True, face=None):
    """corre/anda em velocidade CONSTANTE (sem ease), membros balançando desde o 1º quadro."""
    a = st.actors[n]
    p0 = st.pos(n, t0); p1 = st.sb.feet(*to)
    y = face if face is not None else yaw_to(p0, p1)
    a.key(t0, yaw=y, x=p0[0], z=p0[2]).key(t1, ease="linear", x=p1[0], z=p1[2])
    st.yaw[n] = y
    d = float(np.linalg.norm((p1 - p0)[[0, 2]])); v = d / max(t1 - t0, 1e-3)
    amp, cyc = (62.0, 1.7) if run else (42.0, 1.25)
    f = max(1.4, v / cyc)
    a.wobble("rleg_x", t0, t1, amp, f, ramp=0.02).wobble("lleg_x", t0, t1, amp, f, phase=math.pi, ramp=0.02)
    a.wobble("rarm_x", t0, t1, amp * 1.1, f, phase=math.pi, ramp=0.02).wobble("larm_x", t0, t1, amp * 1.1, f, ramp=0.02)
    a.wobble("hop", t0, t1, 0.06, 2 * f, phase=-math.pi / 2, ramp=0.02).wobble("roll", t0, t1, 3.0, f, ramp=0.02)
    a.key(t0, lean=-12 if run else -4)
    return st


def fly(st, n, path, T, tumble=0.0):
    """posição por chaves suaves (voo/queda): path = [(t, dx, dy, dz), ...]"""
    a = st.actors[n]
    for k, (t, dx, dy, dz) in enumerate(path):
        p = st.sb.point(dx, dy, dz)
        a.key(t, ease="linear" if 0 < k < len(path) - 1 else "smooth", x=p[0], y=p[1], z=p[2])
    if tumble:
        a.key(0.0, roll=0).key(T, ease="linear", roll=tumble)
    return st


def follow_cam(st, names, T, off, fov=(62, 56), look_dy=1.0, fps=60):
    """câmera que acompanha o centro de `names` com um deslocamento fixo (queda/voo), suave."""
    ts = np.linspace(0, T, 7)
    C = [np.mean([st.pos(n, t) for n in names], axis=0) for t in ts]
    pts = [c + np.asarray(off, float) for c in C]

    def aim(tau):
        out = []
        for u in np.atleast_1d(tau):
            t = float(u) * T
            out.append(np.mean([st.pos(n, t) for n in names], axis=0) + [0, look_dy, 0])
        return np.array(out)
    mv = track(pts, aim, T, ease="linear", fov=fov, name="follow").with_handheld("subtle")
    return Rig(fps=fps, subframes=8, shutter=0.5).add(mv)


