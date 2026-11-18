"""Cenas (cinemáticas) do 'Transformei TUDO em ÁGUA'.  Cada função devolve uma Cena; python run.py draft|final ids
yaw do Minecraft: 0 = sul (+z), 90 = oeste (-x), -90 = leste (+x), 180 = norte.
Zona livre e plana conferida no mapa: x -861..-823, z -286..-277 (y 94/95).  Faixa da onda: z -292, x -850..-828."""
from agua import *

V3 = lambda *a: np.array(a, float)


def mid(c, T, up=0.9, w=(0.5, 0.5)):
    """mira no meio dos dois primeiros atores (peito + up)."""
    return lambda tau: chest(c.built[0], tau * T) * w[0] + chest(c.built[1], tau * T) * w[1] + [0, up, 0]


def boca(a, *ts, v=0.85):
    for t in ts:
        a.key(t, mouth=0.0); a.key(t + 0.12, mouth=v); a.key(t + 0.5, mouth=v * 0.8); a.key(t + 0.7, mouth=0.0)


def chao(x, z, r=1):
    """chão mais alto em volta (para a câmera nunca entrar em bloco)."""
    return max(gy(x + dx, z + dz) for dx in range(-r, r + 1) for dz in range(-r, r + 1))


def rasante(p0, p1, alt0, alt1, n=6):
    """pontos de câmera de p0 a p1 (x, z) seguindo o relevo, altura alt0→alt1 acima do chão."""
    out = []
    for i in range(n + 1):
        u = i / n
        x, z = p0[0] + (p1[0] - p0[0]) * u, p0[1] + (p1[1] - p0[1]) * u
        out.append(V3(x, chao(x, z) + alt0 + (alt1 - alt0) * u, z))
    ys = np.array([p[1] for p in out]); k = np.convolve(np.pad(ys, 1, mode="edge"), [0.25, 0.5, 0.25], mode="valid")
    for p, y in zip(out, np.maximum(ys - 0.15, k)): p[1] = y
    return out


def capina(c, x0, z0, x1, z1, y):
    """tira o mato do corredor da câmera (capim na lente vira parede verde)."""
    a = "fill %d %d %d %d %d %d air replace " % (min(x0, x1), y, min(z0, z1), max(x0, x1), y + 3, max(z0, z1))
    c.cmd(a + "minecraft:grass", a + "minecraft:tall_grass", a + "minecraft:fern", a + "minecraft:large_fern", a + "#minecraft:flowers")


def inunda(c, centro=(-858, 95, -282), raio=70, limpa=None):
    """mundo já tomado pela água: contágio rápido centrado num marcador (os comandos rodam como o jogador: sem marcador, o centro vira onde ele olha)."""
    if limpa: capina(c, *limpa)
    c.cmd(aim("inu", (centro[0] + 0.5, centro[1], centro[2] + 0.5), 5.0), mirando("inu", "agua contagio %d 1" % raio))
    c.scene.settleTicks = 240


# ------------------------------------------------------------------ GANCHO
def marca_parede(c, x, z, yaw=90):
    """`agua parede marcar` com a origem 4 blocos abaixo do chão (poço 1x1 aberto e fechado): o alagamento atrás da onda não põe água
    acima do chão, então a malha da crista não pisca (WallFx amostra o heightmap na linha da frente; coluna alagada = +3 por 1 tick)."""
    g = int(gy(x + 0.5, z + 0.5))
    c.cmd("fill %d %d %d %d %d %d air" % (x, g - 4, z, x, g - 1, z), em((x, g + 6, z), yaw, "agua parede marcar"),
          "fill %d %d %d %d %d %d dirt" % (x, g - 4, z, x, g - 2, z), "setblock %d %d %d grass_block" % (x, g - 1, z))


def h1(draft):
    """0,00–3,80 'e se o minecraft todo virasse somente de água?': a gota cai, o contágio se espalha, a câmera sobe revelando."""
    T = 3.9
    gx, gz = -846.5, -281.5; g = gy(gx, gz)
    c = Cena("h1", T, draft, anchor=(-846, 100, -281))
    capina(c, -854, -287, -838, -276, int(g))
    c.cmd(aim("g", (gx, g, gz), 4.0))
    c.ev(0.0, mirando("g", "agua gota"))
    c.ev(1.3, mirando("g", "agua contagio 46 3"))
    m = c.ator("matteeoo", MAT, -848.9, -280.3, yaw=-78)
    p = c.ator("pedro", PED, -849.2, -282.9, yaw=-100)
    for a, d in ((m, 0.0), (p, 0.12)):
        a.look(0.0, (gx, g + 9, gz)); a.look(0.55 + d, (gx, g + 4.5, gz)); a.look(1.0 + d, (gx, g, gz))
        a.pose(1.3 + d, "susto"); a.jump(1.36 + d, 0.5, 0.36)
    boca(m, 1.35, 2.4); boca(p, 1.5, 2.6)
    m.turn(2.0, 90, 0.3); corre(m, 2.25, T + 0.5, (-860.6, -279.4)); m.look(2.9, (gx, g, gz), 0.7)
    p.turn(2.1, 90, 0.3); corre(p, 2.35, T + 0.5, (-860.4, -284.4))
    p0 = V3(-844.9, g + 0.8, -281.0); p1 = V3(-844.2, g + 1.0, -280.6); p2 = V3(-829.5, g + 15.0, -272.5)
    a0, a1, a2 = V3(gx - 1.6, g + 2.6, gz), V3(gx - 1.3, g + 0.95, gz), V3(gx - 5.0, g + 0.5, gz + 0.5)

    def cam():
        c.rig.add(track([p0, p1], lerp_point(a0, a1, "in_out"), 1.3, ease="linear", fov=(58, 60)).with_handheld("subtle"))
        c.rig.add(crane(p1, p2, lerp_point(a1, a2, "out"), T - 1.3, arc=2.0, ease="out", fov=(60, 74)).with_handheld("subtle"))
    c.shot_cam = cam
    return c


def h2(draft):
    """5,70–8,20 'porque hoje eu e o meu amigo vamos ter que': os dois correndo PARA a câmera com a parede de água atrás, chegando."""
    T = 2.6
    c = Cena("h2", T, draft, anchor=(-838, 100, -292))
    capina(c, -850, -295, -826, -289, 94)
    marca_parede(c, -809, -292)
    c.cmd("agua parede iniciar 15 0.5 90 300", "agua parede velocidade 0")
    c.ev(0.0, "agua parede velocidade 8.6")
    v = 5.8
    m = c.ator("matteeoo", MAT, -830.0, -293.4, yaw=90)
    p = c.ator("pedro", PED, -829.6, -290.7, yaw=90)
    corre(m, 0.0, T + 0.4, (-830.0 - v * (T + 0.4), -293.4))
    corre(p, 0.0, T + 0.4, (-829.6 - v * (T + 0.4), -290.7))
    back = V3(-800, 108, -292)
    p.look(0.1, back, 0.85); p.look(0.7, None); m.look(1.0, back, 0.85); m.look(1.65, None)
    boca(m, 0.1, 1.7); boca(p, 0.75, 1.9)
    x0 = -834.3; x1 = x0 - (v - 0.06) * T

    def cam():
        c.rig.add(track(rasante((x0, -292.1), (x1, -292.0), 1.0, 1.12), mid(c, T, 0.8), T, ease="linear", fov=(60, 66)).with_handheld("handheld"))
    c.shot_cam = cam
    return c


def h3(draft):
    """13,67–16,42 'recuperar o mundo todo é juntando três': giro de 135° — do rosto deles para o que eles veem: os 3 feixes."""
    T = 2.85
    ex, ey, ez = ESP1
    c = Cena("h3", T, draft, anchor=(-892, 112, -286), visao=16)
    m = c.ator("matteeoo", MAT, -899.7, -287.3, yaw=-55)
    p = c.ator("pedro", PED, -900.3, -290.3, yaw=-62)
    far3, far2 = V3(*ESP3) + [0, 30, 0], V3(ESP2[0], 150, ESP2[2])
    m.look(0.0, (ex + 0.5, ey + 0.6, ez + 0.5)); m.pose(0.05, "mostra"); m.look(1.1, far2)
    p.look(0.0, far2); p.point_at(0.25, far3); p.look(0.3, far3)
    boca(m, 0.1, 1.2); boca(p, 0.3)
    ctr = V3(-899.4, ey + 1.25, -288.9)

    def cam():
        c.rig.add(orbit(ctr, (3.6, 9.5), 78, -60, (0.25, 4.6), T, ease="in_out", look_offset=(0, 0.3, 0), fov=(56, 72)).with_handheld("subtle"))
    c.shot_cam = cam
    return c


def h4(draft):
    """22,78–24,93 'ficar todo inundado não vai sobrar nada': o Creeper de água GIGANTE cresce atrás dos dois no último bloco."""
    T = 2.3
    c = Cena("h4", T, draft, anchor=(-858, 100, -282), visao=12)
    inunda(c, limpa=(-872, -290, -850, -274, 94))
    c.cmd("execute rotated -90 0 run agua creeper 2.5 -845.5 95 -282.5", "agua creeper seguir false")
    c.ev(0.0, "agua creeper tamanho 21")
    m = c.ator("matteeoo", MAT, -857.6, -283.1, yaw=84)
    p = c.ator("pedro", PED, -858.2, -280.6, yaw=98)
    cr = V3(-845.5, 104, -282.5)
    m.pose(0.0, "talk"); m.look(0.4, cr, 0.9); m.pose(0.75, "susto"); m.look(1.3, None)
    p.look(0.2, cr, 0.9); p.pose(0.55, "susto"); p.look(1.15, None)
    boca(m, 0.8, 1.5); boca(p, 0.6, 1.4)
    corre(p, 1.2, T + 0.5, (-864.6, -280.2)); corre(m, 1.35, T + 0.5, (-864.2, -283.6))

    def cam():
        def aimf(tau):
            w = (0.55 * np.clip(tau * 1.7, 0, 1))[:, None]
            return mid(c, T, 0.6)(tau) * (1 - w) + (cr + [0, 4, 0])[None, :] * w
        c.rig.add(track(rasante((-860.9, -282.2), (-865.3, -281.8), 0.8, 0.62, n=4), aimf, T, ease="in_out", fov=(58, 84)).with_handheld("handheld"))
    c.shot_cam = cam
    return c


# ------------------------------------------------------------------ MIOLO
def c1(draft):
    """82,25–85,29 'Gabriel Medina': o Pedro surfando a crista da onda numa prancha (câmera de drone, 3/4 de frente).
    A onda nasce em t=0 (evento) e os primeiros 0,6 s são descartados na timeline (c.pre).  RODAR PRIMEIRO NO LOTE: a ondulação da
    crista (WallFx.wobble) usa um contador de ticks do cliente que só zera ao abrir o jogo — assim a altura da crista é calculável."""
    PRE = 0.6; T = 3.1 + PRE
    c = Cena("c1", T, draft, anchor=(-822, 112, -292), visao=14)
    c.pre = PRE
    x0 = -798.0; v = 5.5; H = 20.0; base = 94.5
    marca_parede(c, int(x0), -292)
    c.ev(0.0, "agua parede iniciar %d %.1f 90 300" % (H, v))
    wob = lambda l, tk: 1 + 0.05 * np.sin(l * 0.23 + tk * 0.17) + 0.04 * np.sin(l * 0.61 - tk * 0.29)
    sway = lambda t: 0.5 * np.sin(t * 1.7)
    z0 = -291.0
    px = lambda t: x0 + 1.5 - v * t                                          # 1,5 atrás da frente = no pico (perfil: pico em -0,08·H)
    crista = lambda t: base + H * wob(-292.0 - (z0 + sway(t)), 20.0 * t)
    p = c.ator("pedro", PED, px(0), z0, yaw=108, y=crista(0) + 0.1)
    board = Prop("prancha", "minecraft:smooth_quartz_slab", (px(0), crista(0) - 0.04, z0))
    for i in range(0, 78):
        t = i * 0.05
        rl = 6 * np.sin(t * 1.7 + 0.6)
        p.key(t, ease="linear", x=px(t), y=crista(t) + 0.1, z=z0 + sway(t), roll=rl)
        board.key(t, x=px(t), y=crista(t) - 0.04, z=z0 + sway(t), sx=2.3, sy=0.28, sz=0.62, yaw=0, pitch=0, roll=rl)
    p.pose(0.0, "agacha"); p.pose(PRE + 0.5, "joinha"); p.pose(PRE + 1.9, "acena"); boca(p, PRE + 0.5, PRE + 1.4, PRE + 2.2)
    c.props.append(board)
    top = base + H * 1.09

    def cam():
        f = lambda tau: np.stack([px(tau * T), crista(tau * T) + 0.9, z0 + sway(tau * T)], axis=1)
        k0 = V3(px(0) - 9.8, top + 4.2, z0 + 4.4); k1 = V3(px(T) - 8.6, top + 5.0, z0 - 3.2)
        c.rig.add(track([k0, (k0 + k1) / 2 + [-0.8, 0.1, 0], k1], f, T, ease="linear", fov=(45, 49), roll=(-4, 3)).with_handheld("handheld"))
    c.shot_cam = cam
    return c


def c5(draft):
    """345,5–348,8 'o que que você fez?': AGORA VIROU ÁGUA: PEDRA — a montanha atrás dos dois vira água."""
    T = 3.3
    c = Cena("c5", T, draft, anchor=(-748, 105, -302), visao=14)
    alvo = (-722.0, gy(-722, -306), -306.0)
    capina(c, -760, -308, -748, -296, int(gy(-755, -302)) - 1)
    c.cmd(aim("pd", alvo, 6.0))
    c.ev(0.0, mirando("pd", "agua agora pedra 30"))
    c.ev(0.05, "agua letreiro limpar")
    m = c.ator("matteeoo", MAT, -752.2, -300.6, yaw=126)
    p = c.ator("pedro", PED, -751.4, -303.4, yaw=64)
    mt = V3(alvo[0], alvo[1] + 8, alvo[2])
    p.look(0.0, mt, 0.9); p.look(1.3, None); p.pose(1.45, "ombros"); p.look(2.5, mt, 0.7)
    m.look(0.0, mt, 0.9); m.pose(0.7, "susto"); m.look(1.1, (-751.4, gy(-751.4, -303.4) + 1.6, -303.4))
    m.point_at(1.25, mt, left=True); boca(m, 1.2, 2.1); boca(p, 2.75)

    def cam():
        aimf = lambda tau: mid(c, T, 1.35)(tau) + np.outer(np.clip(tau, 0, 1), [2.0, 0.9, 0])
        c.rig.add(track(rasante((-755.0, -300.0), (-755.7, -304.2), 1.35, 1.5, n=4), aimf, T, ease="in_out", fov=(60, 64)).with_handheld("subtle"))
    c.shot_cam = cam
    return c


def c6(draft):
    """445,1–449,1 'Meu Deus, explodiu… de novo aquela onda': o Creeper de água explode e a onda vem atrás do Pedro."""
    T = 3.6
    c = Cena("c6", T, draft, anchor=(-845, 100, -281), visao=12)
    capina(c, -861, -286, -826, -277, 94)
    c.cmd("execute rotated -90 0 run agua creeper 2 -828.5 %d -281.5" % gy(-828.5, -281.5), "agua creeper seguir false")
    c.ev(0.0, "agua creeper explodir")
    v = 5.6
    p = c.ator("pedro", PED, -831.6, -280.4, yaw=90)
    m = c.ator("matteeoo", MAT, -836.2, -283.0, yaw=90)
    cr = V3(-828.5, gy(-828.5, -281.5) + 2, -281.5)
    p.look(0.0, cr, 0.9); p.pose(0.0, "susto"); p.look(0.5, None); corre(p, 0.3, T + 0.4, (-831.6 - v * (T + 0.1), -280.4))
    m.look(0.0, cr, 0.9); m.look(0.55, None); corre(m, 0.2, T + 0.4, (-836.2 - v * (T + 0.2), -283.0)); m.look(2.0, cr, 0.8); m.look(2.6, None)
    boca(p, 0.05, 1.6, 2.6); boca(m, 0.9, 2.1)
    x0 = -839.9; x1 = x0 - (v - 0.25) * T

    def cam():
        c.rig.add(track(rasante((x0, -280.6), (x1, -281.6), 0.95, 1.15), mid(c, T, 0.9, (0.55, 0.45)), T, ease="linear", fov=(62, 68)).with_handheld("handheld"))
    c.shot_cam = cam
    return c


def c9(draft):
    """670,3–673,0 'Oh, Avatar das Águas': o Pedro vira água — amassa, espirra e volta azul."""
    T = 2.8
    c = Cena("c9", T, draft, anchor=(-844, 100, -280), visao=12)
    px, pz = -842.5, -279.5
    g = gy(px, pz)
    capina(c, -849, -283, -840, -276, int(g))
    p = c.ator("pedro", PED, px, pz, yaw=100)
    mx, mz = -843.5, -277.3
    m = c.ator("matteeoo", MAT, mx, mz, yaw=140)
    pa = c.ator("pedro_agua", PEDA, px, pz, yaw=100)
    ts = 0.95
    p.pose(0.0, "mostra"); p.look(0.0, (px - 0.6, g + 0.9, pz))
    p.key(0.0, sx=1, sy=1, sz=1, y=g); p.key(ts - 0.22, sx=1, sy=1, sz=1); p.key(ts - 0.04, ease="in", sx=1.5, sy=0.28, sz=1.5)
    p.key(ts - 0.012, ease="linear", y=g); p.key(ts - 0.008, ease="linear", y=g - 40)          # troca: o normal some (vai p/ baixo do chão)
    pa.key(0.0, y=g - 40, sx=1.5, sy=0.28, sz=1.5); pa.key(ts - 0.004, ease="linear", y=g - 40); pa.key(ts, ease="linear", y=g, sx=1.5, sy=0.28, sz=1.5)
    pa.key(ts + 0.16, ease="out", sx=0.82, sy=1.3, sz=0.82); pa.key(ts + 0.32, sx=1.08, sy=0.92, sz=1.08); pa.key(ts + 0.48, sx=1, sy=1, sz=1)
    pa.pose(0.0, "mostra"); pa.look(0.0, (px - 0.6, g + 0.9, pz)); pa.pose(ts + 0.55, "susto"); pa.look(ts + 1.0, (mx, gy(mx, mz) + 1.6, mz)); pa.pose(ts + 1.25, "ombros")
    boca(pa, ts + 0.6, ts + 1.3)
    m.look(0.0, (px, g + 1.5, pz)); m.pose(0.0, "talk"); m.pose(ts + 0.15, "susto"); m.jump(ts + 0.18, 0.45, 0.34); m.point_at(ts + 0.85, (px, g + 1.3, pz)); boca(m, ts + 0.2, ts + 0.9)
    for dt, n in ((0.0, 260), (0.05, 200), (0.12, 120)):
        c.ev(ts + dt, "particle minecraft:splash %.2f %.2f %.2f 0.45 0.7 0.45 0.3 %d force" % (px, g + 1.0, pz, n))
    c.ev(ts, "particle minecraft:bubble_pop %.2f %.2f %.2f 0.4 0.8 0.4 0.05 80 force" % (px, g + 1.0, pz))
    c.ev(ts + 0.02, "particle minecraft:falling_water %.2f %.2f %.2f 0.5 0.6 0.5 0 140 force" % (px, g + 1.6, pz))
    k0 = V3(-847.3, chao(-847, -280) + 1.3, -280.3); k1 = V3(-845.9, chao(-846, -280) + 1.35, -279.9)

    def cam():
        a0 = V3(px - 0.5, g + 1.2, pz + 1.1); a1 = V3(px - 0.3, g + 1.25, pz + 0.75)
        c.rig.add(push_in(k0, k1, lerp_point(a0, a1, "in_out"), T, ease="in_out", fov=(58, 52)).with_handheld("subtle"))
    c.shot_cam = cam
    return c


def c11(draft):
    """828,1–832,0 'a gente tem um gigantesco problema': por cima do ombro, o Creeper cresce até o céu; eles viram e correm."""
    T = 3.9
    c = Cena("c11", T, draft, anchor=(-858, 105, -290), visao=12)
    inunda(c, limpa=(-866, -312, -849, -290, 94))
    c.cmd("execute rotated 0 0 run agua creeper 3 -857.5 95 -281.5", "agua creeper seguir false")
    c.ev(0.25, "agua creeper tamanho 21")
    m = c.ator("matteeoo", MAT, -858.6, -297.0, yaw=8)
    p = c.ator("pedro", PED, -855.6, -296.4, yaw=-6)
    cr = V3(-857.5, 112, -281.5)
    for a, d in ((m, 0.0), (p, 0.15)):
        a.look(0.0, (-857.5, 99, -281.5)); a.look(0.7 + d, cr); a.pose(0.9 + d, "susto")
        a.turn(2.2 + d, 180, 0.32)
    corre(m, 2.5, T + 0.6, (-859.4, -305.5)); corre(p, 2.62, T + 0.6, (-854.8, -305.0))
    boca(m, 1.0, 2.6, 3.3); boca(p, 1.2, 2.8)
    g = gy(-857, -297)

    def cam():
        a0 = V3(-857.2, g + 1.5, -294.5); a1 = V3(-857.5, g + 12.0, -286.0)
        c.rig.add(track(rasante((-856.5, -300.6), (-857.4, -308.2), 1.7, 0.75, n=5), lerp_point(a0, a1, "in_out"), T, ease="in_out", fov=(62, 86)).with_handheld("handheld"))
    c.shot_cam = cam
    return c


def c14(draft):
    """1007,7–1011,2 'Ó, a vila está reaparecendo': a grua sobe e o mundo volta em onda verde a partir do último bloco."""
    T = 3.5
    c = Cena("c14", T, draft, anchor=(-856, 105, -282), visao=14)
    inunda(c, raio=80, limpa=(-864, -290, -846, -274, 94))
    c.ev(1.6, "agua volta 3")
    m = c.ator("matteeoo", MAT, -856.4, -283.3, yaw=-70)
    p = c.ator("pedro", PED, -856.8, -280.4, yaw=-105)
    vila = V3(-893, 100, -300)
    m.look(0.0, (-857.5, 95.5, -281.5), 0.8); m.pose(0.0, "mostra"); m.look(1.7, vila, 0.7); m.point_at(1.85, vila, left=True); m.pose(2.5, "comemora"); m.jump(2.65, 0.7)
    p.look(0.0, (-857.5, 95.5, -281.5), 0.8); p.pose(1.85, "comemora"); p.jump(2.0, 0.75); p.jump(2.75, 0.75)
    boca(m, 1.8, 2.6); boca(p, 1.9, 2.8)
    g = gy(-853, -282)
    k0 = V3(-853.2, g + 1.2, -283.3); k1 = V3(-842.5, g + 11.5, -273.5)

    def cam():
        a0 = V3(-856.6, g + 1.25, -281.9); a1 = V3(-861.0, g + 0.8, -284.0)
        c.rig.add(crane(k0, k1, lerp_point(a0, a1, "in_out"), T, arc=1.0, ease="in_out", fov=(56, 72)).with_handheld("subtle"))
    c.shot_cam = cam
    return c


CENAS = {k: v for k, v in list(globals().items()) if callable(v) and getattr(v, "__doc__", None) and k[0] in "hc" and k[1:].isdigit()}
