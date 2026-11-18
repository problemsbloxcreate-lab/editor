"""Varre um bruto a 4 qps: miniaturas 96x54 (scan/<src>_thumb.npy) + atributos por quadro (scan/<src>_feat.npy):
[yellow_top, yellow_all, mean_lum, std_lum, btn_gray, dark_frac, chatbox]"""
import subprocess, sys, numpy as np, cv2, os
src, path = sys.argv[1], sys.argv[2]
FPS = 4; W, H = 320, 180
cmd = ['ffmpeg', '-v', 'error', '-hwaccel', 'cuda', '-hwaccel_output_format', 'cuda', '-i', path, '-vf', 'fps=%d,scale_cuda=w=%d:h=%d:format=nv12,hwdownload,format=nv12,format=rgb24' % (FPS, W, H), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-']
p = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=10 ** 8)
fs, th = [], []
n = W * H * 3
while True:
    b = p.stdout.read(n)
    if len(b) < n: break
    f = np.frombuffer(b, np.uint8).reshape(H, W, 3).astype(np.int16)
    r, g, bl = f[..., 0], f[..., 1], f[..., 2]
    yel = (r > 200) & (g > 165) & (g < 235) & (bl < 110) & (r - bl > 120)
    lum = 0.299 * r + 0.587 * g + 0.114 * bl
    gray = (np.abs(r - g) < 8) & (np.abs(g - bl) < 8) & (lum > 95) & (lum < 130)      # face do botão vanilla
    chat = lum[int(H * 0.55):int(H * 0.93), :int(W * 0.5)]
    fs.append([yel[:int(H * 0.2)].mean(), yel.mean(), lum.mean(), lum.std(), gray.mean(), (lum < 40).mean(), (chat < 45).mean()])
    th.append(cv2.resize(f.astype(np.uint8), (96, 54), interpolation=cv2.INTER_AREA))
np.save('scan/%s_feat.npy' % src, np.array(fs, np.float32)); np.save('scan/%s_thumb.npy' % src, np.array(th, np.uint8))
print(src, len(fs))
