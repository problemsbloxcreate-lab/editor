from common import *
pat = Actor("patao", PAT, PAT_POS, yaw=0).key(0, vbelly=6, vbelly_out=4, vbelly_y=7, rarm_z=12, larm_z=-12)
pro = Actor("problems", PRO, PRO_POS, yaw=0).key(0, vbelly=5.5, vbelly_out=3.5, vbelly_y=7, rarm_z=12, larm_z=-12)
anim = Anim([pat, pro])
def look(cam, tgt, fov, t=0.0):
    d = np.array(tgt) - np.array(cam); yaw = math.degrees(math.atan2(-d[0], d[2])); pitch = -math.degrees(math.atan2(d[1], math.hypot(d[0], d[2])))
    return dict(x=cam[0], y=cam[1], z=cam[2], yaw=yaw, pitch=pitch, fov=fov, t=t)
bp = belly_center(PAT_POS, 6, 4); bq = belly_center(PRO_POS, 5.5, 3.5)
poses = [look(bp + [0, 0.05, 1.5], bp, 50), look(bp + [1.0, 0.25, 1.0], bp, 50), look(bp + [-0.6, -0.3, 0.9], bp, 55),
         look(bq + [0, 0.05, 1.5], bq, 50), look(bq + [-1.0, 0.25, 1.0], bq, 50), look(bp + [-1.5, 1.2, 5.0], (3049, 65, -357), 60)]
print(stills(poses, "barriga_st1", scene=SCENE, world=WORLD, settings=settings(True), size=(1280, 720), anim=anim))
