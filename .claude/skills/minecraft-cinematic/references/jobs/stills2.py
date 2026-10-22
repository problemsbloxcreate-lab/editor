from common import *
R = 6.1
bp = belly_center(PAT_POS, R, R - 2.0, 7.0)
acts = []
cands = [(-34, -22), (-45, -30), (-40, -40), (-55, -35)]
for i, (ax, az) in enumerate(cands):
    pos = (PAT_POS[0] + 3 * i, FY, PAT_POS[2])
    acts.append(Actor(f"p{i}", PRO, pos, yaw=0).key(0, head_x=16, rarm_x=ax, rarm_z=az, larm_z=-14, vbelly=R, vbelly_out=R - 2, vbelly_y=7, vbelly_shine=0.85))
anim = Anim(acts)
def look(cam, tgt, fov):
    d = np.array(tgt) - np.array(cam); return dict(x=cam[0], y=cam[1], z=cam[2], yaw=math.degrees(math.atan2(-d[0], d[2])), pitch=-math.degrees(math.atan2(d[1], math.hypot(d[0], d[2]))), fov=fov, t=0)
poses = []
for i in range(4):
    b = bp + [3 * i, 0, 0]
    poses.append(look(b + [0.9, 0.45, 1.25], b + [0, 0.1, 0], 48))
print(stills(poses, "barriga_st2", scene=SCENE, world=WORLD, settings=settings(True), size=(960, 540), anim=anim))
