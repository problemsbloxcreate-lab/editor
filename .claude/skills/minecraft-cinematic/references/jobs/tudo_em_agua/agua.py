"""Ferramentas das cinemáticas do 'Tudo em Água': mundo limpo da gravação + mod tudoagua no relógio do filme (serverSync)."""
from base import *
import numpy as np
from cinecam.atua import Ator
from cinecam.actors import POSE, Mob, Prop, Anim
from cinecam.terrain import Terrain
from cinecam import turma

MAT = turma.skin("matteeoo")
PED = os.path.join(H, "skins", "pedro.png").replace("\\", "/")
PEDA = os.path.join(H, "skins", "pedro_agua.png").replace("\\", "/")
LIMPO = r"D:\Pobrs\tudoagua\cine\world_limpo"
WORLD = World(mode="copy", copyFrom=LIMPO)
_T = None


def ter():
    global _T
    if _T is None:
        _T = Terrain.load(os.path.join(H, "terreno.json"))
    return _T


def gy(x, z):
    """y dos pés no chão da coluna do bloco (x, z) (folhas ignoradas)."""
    T = ter()
    ix = int(np.clip(np.floor(x) - T.x0, 0, T.w - 1)); iz = int(np.clip(np.floor(z) - T.z0, 0, T.h - 1))
    return float(T.ground[iz, ix])


def feet(x, z, dy=0.0):
    return np.array([x, gy(x, z) + dy, z], float)


RESET = ["function gravar:limpar_cena", "agua desfazer", "kill @e[tag=cine]", "agua mundo set 0"]


def aim(tag, alvo, alto=3.0):
    """Mira para os comandos do mod que usam 'onde o diretor olha': um armor stand marcador acima do alvo, olhando para baixo."""
    x, y, z = alvo
    return "summon armor_stand %.2f %.2f %.2f {Marker:1b,Invisible:1b,NoGravity:1b,Rotation:[0f,90f],Tags:[\"cine\",\"%s\"]}" % (x, y + alto, z, tag)


def mirando(tag, cmd):
    return "execute as @e[tag=%s,limit=1] run %s" % (tag, cmd)


def em(pos, yaw, cmd):
    """comando do mod que usa a posição/rotação de quem executa (parede marcar, subsolo, peixes, creeper)."""
    return "execute positioned %.2f %.2f %.2f rotated %.1f 0 run %s" % (pos[0], pos[1], pos[2], yaw, cmd)


def corre(a, t0, t1, to, passo=0.5):
    """corrida em velocidade constante seguindo o relevo real (y por chaves a cada meio bloco)."""
    p0 = a.pos_at(t0); p1 = np.array([to[0], 0, to[1]])
    a.walk(t0, t1, to, gait="run")
    n = max(2, int(np.hypot(p1[0] - p0[0], p1[2] - p0[2]) / passo))
    for i in range(n + 1):
        u = i / n
        x, z = p0[0] + (p1[0] - p0[0]) * u, p0[2] + (p1[2] - p0[2]) * u
        a.key(t0 + (t1 - t0) * u, ease="smooth", y=gy(x, z))
    return a


def chest(actor, t, up=1.3):
    p = actor.at(np.atleast_1d(np.asarray(t, float)))
    return np.stack([p[:, 0], p[:, 1] + up + p[:, POSE["hop"]] * 0.6, p[:, 2]], axis=1)


class Cena:
    """Uma cinemática: rig + cena + anim, em rascunho (960x540, 30 fps, sem blur) ou final (1920x1080, 60 fps)."""

    def __init__(self, nome, T, draft, anchor, hora=6000, fps=None, sub=None, visao=14):
        self.nome, self.T, self.draft = nome, T, draft
        self.fps = fps or (30 if draft else 60)
        self.rig = Rig(fps=self.fps, subframes=sub or (1 if draft else 6), shutter=0.5)
        self.scene = Scene(time=hora, anchor=anchor, commands=list(RESET), settleTicks=160, serverSync=True)
        self.settings = Settings(renderDistance=visao, simulationDistance=8, worldTicks=True)
        self.atores, self.props, self.mobs = [], [], []
        self.dof = None

    def cmd(self, *c): self.scene.commands += list(c); return self
    def ev(self, t, c): self.scene.events.append([float(t), c]); return self
    def bloco(self, t, x, y, z, estado): self.scene.blocks.append([float(t), int(x), int(y), int(z), estado]); return self

    def ator(self, nome, skin, x, z, yaw=0.0, item=None, y=None, **kw):
        a = Ator(nome, skin, (x, gy(x, z) if y is None else y, z), yaw=yaw, item=item, **kw)
        self.atores.append(a)
        return a

    def shot(self):
        built = [a.build(self.T) if isinstance(a, Ator) else a for a in self.atores]
        self.built = built
        anim = Anim(built, props=self.props, mobs=self.mobs)
        return Shot(name="agua_" + self.nome + ("_d" if self.draft else ""), rig=self.rig, scene=self.scene, settings=self.settings, anim=anim,
                    size=(960, 540) if self.draft else (1920, 1080), grade="insert", dof=(False if self.draft else self.dof), blur=not self.draft)
