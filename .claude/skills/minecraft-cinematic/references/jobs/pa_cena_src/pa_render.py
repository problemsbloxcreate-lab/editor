import sys; sys.path.insert(0,'.')
from pa_shot import *
from waitlib import when_free
make_skin()
rig = build(fps=60, subframes=8)
anim = Anim([build_actor()])
ss = int(sys.argv[1]) if len(sys.argv) > 1 else 2
info = when_free(lambda: render(rig, "pa_rasante_plongee", scene=scene(), world=WORLD, settings=SETTINGS,
                                size=(1920,1080), grade="cinematic", supersample=ss, xmx="4G", anim=anim))
print("FINAL", info["final"], info["report"].get("warnings"), info["report"].get("maxWait"), info["game_seconds"])
