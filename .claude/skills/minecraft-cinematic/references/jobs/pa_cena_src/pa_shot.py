import sys; sys.path.insert(0, r"C:\Users\mathe\.claude\skills\minecraft-cinematic\scripts")

import numpy as np

from scipy.interpolate import PchipInterpolator as P

from PIL import Image

from cinecam import *

from cinecam.camlib import Move, look_at, unwrap_deg

import pa_scene as S



T = 7.0

FPS = 60

SKIN = r"D:/cinecam-run/pa_cyan_skin.png"



def make_skin():

    cy, dk, md = (36, 224, 222, 255), (0, 120, 130, 255), (22, 190, 190, 255)

    im = Image.new("RGBA", (64, 64), cy)

    px = im.load()

    for y in range(64):                      # sombreado leve nas faces inferiores/laterais para ler volume

        for x in range(64):

            if (y % 16) > 11 and y < 52: px[x, y] = md

    for (x, y) in [(9, 12), (10, 12), (13, 12), (14, 12), (11, 14), (12, 14)]:

        px[x, y] = dk                        # olhos + boca (frente da cabeÃ§a)

    im.save(SKIN)



def gmax(dx, dz, rad=1.6):

    m = -99

    for a in (-rad, 0, rad):

        for b in (-rad, 0, rad):

            m = max(m, S.h_rel(int(round(dx+a)), int(round(dz+b))))

    return S.G + m + 1.0



# ---- keyframes da cÃ¢mera (coords relativas ao centro da bacia)

KT = [0, 1.0, 2.0, 2.8, 3.6, 4.6, 5.6, 6.5, 7.0]

CXk = [2.3, 2.6, 2.8, 2.2, 1.0, 0.0, -1.0, -1.5, -1.6]

CZk = [40, 34.8, 28.4, 20.5, 8.5, -5, -13.5, -16.5, -17.5]

fx, fz = P(KT, CXk), P(KT, CZk)

# rasante: segue o terreno com média CAUSAL (só olha o passado) -> sempre acima do degrau, sem quina

_fine = np.arange(-0.8, 2.41, 0.02)

_raw = np.array([gmax(fx(max(t, 0)), fz(max(t, 0))) + 0.5 for t in _fine])

_w = int(0.5/0.02)

_sm = np.array([_raw[max(0, i-_w):i+1].mean() for i in range(len(_fine))])

low_t = np.arange(0, 2.41, 0.2)

Yk_t = list(low_t) + [3.0, 3.8, 4.8, 5.8, 6.5, 7.0]

Yk = [float(np.interp(t, _fine, _sm)) for t in low_t] + [S.G + 2.5, S.G + 9, S.G + 17, S.G + 22, S.G + 22, S.G + 21]

fy = P(Yk_t, Yk)

froll = P([0, 1.0, 2.0, 3.0, 4.0, 5.5, 7.0], [0, 3.5, -2.0, -7.0, -4.0, 0, 0])

ffov = P([0, 1.5, 2.8, 3.6, 4.8, 7.0], [62, 64, 76, 86, 70, 60])

PITCH_END, YAW_END = 52.0, 0.0



def smooth(u):

    u = np.clip(u, 0, 1); return u*u*(3 - 2*u)



def cam_fn(tau):

    t = tau*T

    x, y, z = fx(t), fy(t), fz(t)

    pos = np.stack([S.CX + x, y, S.CZ + z], -1)

    rw = np.array([S.runner_world(float(tt)) for tt in t])

    aim = rw + np.array([0, 1.25, 0])

    yaw_r, pit_r = look_at(pos, aim)

    s = smooth((t - 2.3)/(5.0 - 2.3))

    yaw = unwrap_deg((1 - s)*yaw_r + s*YAW_END) if False else (1 - s)*np.asarray(yaw_r) + s*YAW_END

    pit = (1 - s)*np.asarray(pit_r) + s*PITCH_END

    return {"x": pos[:, 0], "y": pos[:, 1], "z": pos[:, 2], "yaw": yaw, "pitch": pit, "roll": froll(t), "fov": ffov(t)}



def build(fps=FPS, subframes=8):

    rig = Rig(fps=fps, subframes=subframes, shutter=0.5)

    rig.add(Move(T, cam_fn, "rasante_plongee").with_handheld("subtle"))

    return rig



def build_actor():

    a = S.runner_world

    ts = np.arange(0, S.T_STOP + 0.001, 0.1)

    x0, y0, z0 = a(0)

    A = Actor("runner", SKIN, pos=(x0, y0, z0), yaw=180)

    for t in ts[1:]:

        x, y, z = a(float(t)); A.key(float(t), ease="linear", x=x, y=y, z=z)

    A.key(0.0, ease="linear", lean=-9, hop=0.05, head_x=0)

    A.key(S.T_STOP, ease="smooth", lean=-9)

    A.key(S.T_STOP + 0.25, ease="smooth", lean=0, head_x=24, rarm_x=0, larm_x=0, rleg_x=0, lleg_x=0, rarm_z=-22, larm_z=22)

    A.key(S.T_STOP + 0.0, ease="linear", hop=0.05)

    A.key(S.T_STOP + 0.4, ease="smooth", hop=0.0)

    A.key(S.T_STOP + 0.3, ease="smooth", head_x=24)
    A.key(S.T_STOP + 0.9, ease="out_back", rarm_z=-155, larm_z=155, head_x=-18)   # "vou beber tudo!": bracos pro alto
    A.wobble("rleg_x", 0.0, S.T_STOP, amp=44, freq=2.65, phase=0)

    A.wobble("lleg_x", 0.0, S.T_STOP, amp=44, freq=2.65, phase=np.pi)

    A.wobble("rarm_x", 0.0, S.T_STOP, amp=40, freq=2.65, phase=np.pi)

    A.wobble("larm_x", 0.0, S.T_STOP, amp=40, freq=2.65, phase=0)

    A.wobble("hop", 0.0, S.T_STOP, amp=0.05, freq=5.3)

    return A



def scene():

    return Scene(time=3500, weather="clear", anchor=(S.CX, S.G + 12, S.CZ + 8), commands=S.commands(), settleTicks=140, preloadTimeoutSec=420)



WORLD = World(seed=4242)

SETTINGS = Settings(renderDistance=12, simulationDistance=6, worldTicks=True)

