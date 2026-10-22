import sys; sys.path.insert(0,'.')
from pa_shot import *
from waitlib import when_free
make_skin()
rig = build(fps=30, subframes=1)
times = [4.6, 5.8, 6.99]
d = rig._eval_at(np.array(times))
poses = [{k: float(d[k][i]) for k in ("x","y","z","yaw","pitch","roll","fov")} | {"t": times[i]} for i in range(len(times))]
anim = Anim([build_actor()])
files = when_free(lambda: stills(poses, "pa_stills3", scene=scene(), world=WORLD, settings=SETTINGS, size=(1280,720), anim=anim, xmx="3G"))
print("\n".join(files))
