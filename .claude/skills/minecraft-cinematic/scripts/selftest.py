"""Fast offline self-test of camlib (no game).  python selftest.py  -> prints PASS/FAIL lines, exit code 1 on failure."""
import os
import sys
import tempfile

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from cinecam import *  # noqa: E402

fails = []


def check(ok, msg):
    print(("PASS " if ok else "FAIL ") + msg)
    if not ok:
        fails.append(msg)


# easing: monotonic, endpoints
u = np.linspace(0, 1, 501)
for k in ("smooth", "launch", "whip", "out", "in_out", "soft_in_out", "out_expo", "launch_soft"):
    y = EASES[k](u)
    check(abs(y[0]) < 1e-6 and abs(y[-1] - 1) < 1e-3 and np.all(np.diff(y) >= -1e-9), f"ease '{k}' monotonic 0->1")

# look_at convention: camera south of a subject looks north (yaw 180); east of subject looks west (yaw 90)
yaw, pit = look_at(np.array([0, 0, 10.0]), np.array([0, 0, 0.0]))
check(abs(abs(float(yaw)) - 180) < 1e-6 and abs(float(pit)) < 1e-6, "look_at: camera south of subject -> yaw 180")
yaw, pit = look_at(np.array([10.0, 0, 0]), np.array([0, 0, 0.0]))
check(abs(float(yaw) - 90) < 1e-6, "look_at: camera east of subject -> yaw 90")
yaw, pit = look_at(np.array([0, 10.0, 0]), np.array([0, 0, 1.0]))
check(float(pit) > 80, "look_at: camera above looking down -> pitch ~ +84")

# orbit bearing convention: a=0 camera north of subject (z smaller), yaw 0
m = orbit((0, 0, 0), 10, 0, 90, 0, 1.0)
p0 = m.start_pose(); p1 = m.end_pose()
check(abs(p0["z"] + 10) < 1e-6 and abs(p0["yaw"]) < 1e-6, "orbit a=0: camera at z=-r looking south (yaw 0)")
check(abs(p1["x"] - 10) < 1e-6 and abs(p1["yaw"] - 90) < 1e-3, "orbit a=90: camera at x=+r looking west (yaw 90)")

# continuity helper
rig = Rig(fps=30, subframes=4)
rig.add(crane((30, 20, -30), (12, 4, -12), (0, 2, 0), 1.5, arc=3, ease="smooth"))
rig.add(orbit_from(rig.last_pose(), (0, 2, 0), 60, 2.0))
rep = rig.analyze()
check(not [w for w in rep["warnings"] if "not continuous" in w], "orbit_from joins seamlessly")

# a cut must not let blur straddle: rows of the frame before the cut stay inside segment 1
rig = Rig(fps=30, subframes=8)
rig.add(hold((0, 0, 0), (0, 0, 10), 0.5))
rig.add(hold((100, 0, 0), (100, 0, 10), 0.5), cut=True)
d = rig.sample_rows()
last_a = d["x"][14 * 8:15 * 8]
check(np.all(last_a < 1.0), "no ghosting across a hard cut")
check(np.all(np.diff(d["t"]) >= 0), "film clock monotonic")

# csv columns
f = os.path.join(tempfile.gettempdir(), "cinecam_selftest.csv")
n = rig.write_csv(f)
hdr = open(f).readline().strip()
check(hdr == "t,x,y,z,yaw,pitch,roll,fov,focus,aperture" and n == 30 * 8, "csv header + row count")

# dof modifier
rig = Rig(fps=30, subframes=2)
rig.add(hold((0, 0, 0), (0, 0, 10), 1.0).with_dof((0, 0, 10), aperture=0.6))
d = rig.sample_frames()
check(abs(d["focus"][0] - 10) < 0.2 and abs(d["aperture"][0] - 0.6) < 1e-9, "with_dof focuses on a point along the view axis")

print("\nALL PASS" if not fails else f"\n{len(fails)} FAILED")
sys.exit(1 if fails else 0)
