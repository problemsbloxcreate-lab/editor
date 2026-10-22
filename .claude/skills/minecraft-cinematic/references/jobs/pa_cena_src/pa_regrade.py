import sys; sys.path.insert(0, r"C:\Users\mathe\.claude\skills\minecraft-cinematic\scripts")
from cinecam import post
import inspect; print(inspect.signature(post.finish))
m = r"D:\cinecam-out\pa_rasante_plongee\pa_rasante_plongee_master.mkv"
post.finish(m, r"D:\cinecam-out\pa_rasante_plongee\pa_rasante_plongee_clean.mp4", preset="clean", letterbox=None, crf=14, width=1920, height=1080, scale="1920:1080", audio=None, fps=60)
print("done")
