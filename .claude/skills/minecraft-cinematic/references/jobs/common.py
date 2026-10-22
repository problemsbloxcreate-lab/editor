"""Barriga cheia d'água — closes de 3 s (Patão, Problems) p/ 'Bebi toda a água do mundo' (Premiere 01:01:26–01:08:45)."""
import sys, math
sys.path.insert(0, r"C:\Users\mathe\.claude\skills\minecraft-cinematic\scripts")
import numpy as np
from cinecam import *

SK = r"C:/Users/mathe/AppData/Roaming/ModrinthApp/profiles/Construir Pirâmide/config/bbs/assets/models/skins/0.Turma/"
PAT, PRO = SK + "ajudantes/cariocapato.png", SK + "Problems0.png"

FY = 64.0                               # feet y (sand top = 63)
PAT_POS = (3050.5, FY, -356.5)          # yaw 0 = faces +z (camera side)
PRO_POS = (3044.5, FY, -356.5)
POND = (3052, -363, 3058, -353)         # x0 z0 x1 z1 (on Patão's left / camera right)

SET = [
    "fill 3036 64 -372 3066 74 -340 minecraft:air",
    "fill 3036 60 -372 3066 63 -340 minecraft:sand",
    "fill 3036 59 -372 3066 59 -340 minecraft:sandstone",
    f"fill {POND[0]} 62 {POND[1]} {POND[2]} 63 {POND[3]} minecraft:water",
    "fill 3057 62 -357 3060 63 -350 minecraft:water",
    "setblock 3040 64 -362 minecraft:dead_bush", "setblock 3061 64 -366 minecraft:dead_bush",
    "setblock 3038 64 -349 minecraft:cactus", "setblock 3038 65 -349 minecraft:cactus",
]
SCENE = Scene(time=5000, weather="clear", anchor=(3050, 70, -356), commands=SET)
WORLD = World(seed=4242)


def settings(frozen=False):
    return Settings(renderDistance=12, simulationDistance=6, worldTicks=not frozen, clouds=True)


def belly_center(pos, R, out, cy=7.0, yaw=0.0):
    """World point of the voxel ball's centre (model z = -2-out+R; model front -z -> world forward)."""
    f = (2.0 + out - R) / 16.0
    y = pos[1] + 1.5 - cy / 16.0
    yr = math.radians(yaw)
    return np.array([pos[0] - math.sin(yr) * f, y, pos[2] + math.cos(yr) * f])
