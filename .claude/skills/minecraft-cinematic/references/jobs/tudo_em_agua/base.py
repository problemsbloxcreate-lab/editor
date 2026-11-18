"""Base das cinemáticas do 'Tudo em Água': CineCam (cliente dev) + mod tudoagua carregado + CÓPIA do mundo da gravação."""
import sys, os, importlib, json, math
sys.path.insert(0, os.path.expanduser(r"~/.claude/skills/minecraft-cinematic/scripts"))
from cinecam import *
R = importlib.import_module("cinecam.render")
MOD = r"C:\Users\mathe\Skills\tudo-em-agua-forge-1.20.1"
if not any(m["id"] == "tudoagua" for m in R.EXTRA_MODS):
    R.EXTRA_MODS.append({"id": "tudoagua", "root": MOD, "mixin": "tudoagua.mixins.json"})
SAVES = os.path.expandvars(r"%APPDATA%\ModrinthApp\profiles\Template Forge 09.26 (1)\saves")
WORLD = World(mode="copy", copyFrom=os.path.join(SAVES, "Tudo em Agua - BACKUP"))   # save onde a gravação de 16/11 foi feita (termina com o mundo de volta)
H = os.path.dirname(os.path.abspath(__file__))
# lugares do mundo real (memória do mod, 09/11)
ULTIMO = (-858, 94, -282)     # bloco do balde / spawn
ESP1 = (-898, 110, -289); ESP2 = (-800, 34, -240); ESP3 = (-770, 163, -160)
LAGO = (-888, 64, -320); ONDA0 = (-740, 0, -292); MONT_L = (-665, 0, -300)


def pose(pos, alvo, fov=60, roll=0, t=0.0):
    yaw, pitch = look_at(pos, alvo)
    return dict(t=t, x=pos[0], y=pos[1], z=pos[2], yaw=float(yaw), pitch=float(pitch), roll=roll, fov=fov)
