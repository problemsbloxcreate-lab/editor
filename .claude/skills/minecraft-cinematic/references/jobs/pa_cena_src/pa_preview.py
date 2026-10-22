import sys; sys.path.insert(0,'.')
from pa_shot import *
make_skin()
rig = build()
import os; os.makedirs(r"D:\cinecam-out\pa_cena", exist_ok=True)
print(plot_rig(rig, r"D:\cinecam-out\pa_cena\path.png"))
d = rig.sample_frames()
import numpy as np
# clearance contra a malha de blocos desenhada
clr = []
for i in range(len(d["t"])):
    dx, dz = d["x"][i]-S.CX, d["z"][i]-S.CZ
    clr.append(d["y"][i] - gmax(dx, dz, 0.0))
clr = np.array(clr); i = int(clr.argmin())
print("clearance min %.2f at t=%.2f (x=%.1f y=%.1f z=%.1f)" % (clr.min(), d["t"][i], d["x"][i], d["y"][i], d["z"][i]))
print("cmd count", len(S.commands()))
