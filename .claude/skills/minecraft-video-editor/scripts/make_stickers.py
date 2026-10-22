"""Gera stickers PNG (estilo ref Problems: preenchimento branco + contorno preto grosso) em library/png.
 - interrogacao_cluster.png : cacho de "?" gigantes (pergunta retórica)
 - interrogacao_big.png      : 1 "?" gigante
 - canudinho.png             : canudo listrado vermelho/branco com cotovelo (item reveal)
Uso: python make_stickers.py
"""
import os, math, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "library", "png")
os.makedirs(OUT, exist_ok=True)
FONT = r"C:\Windows\Fonts\ariblk.ttf"


def qmark(size, rot=0, fill=(255, 255, 255, 255), stroke=int(0.11)):
    f = ImageFont.truetype(FONT, size)
    sw = max(6, int(size * 0.10))
    pad = sw * 2 + 10
    w, h = size + pad * 2, int(size * 1.35) + pad * 2
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # sombra
    sh = Image.new("RGBA", (w, h), (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
    sd.text((pad + sw * 0.5, pad + sw * 0.7), "?", font=f, fill=(0, 0, 0, 120), stroke_width=sw, stroke_fill=(0, 0, 0, 120))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(4)))
    d.text((pad, pad), "?", font=f, fill=fill, stroke_width=sw, stroke_fill=(0, 0, 0, 255))
    return im.rotate(rot, expand=True, resample=Image.BICUBIC)


def cluster(path, W=1500, H=760, seed=7):
    random.seed(seed)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    spots = [(0.10, 0.55, 330, -14), (0.27, 0.30, 420, 9), (0.47, 0.50, 470, -4), (0.66, 0.28, 400, 13), (0.82, 0.55, 340, -11), (0.38, 0.78, 230, 17), (0.60, 0.80, 250, -16)]
    for fx, fy, s, r in spots:
        q = qmark(s, r)
        im.alpha_composite(q, (int(fx * W - q.width / 2), int(fy * H - q.height / 2)))
    im.save(os.path.join(OUT, path))


def straw(path, S=1000):
    K = 2  # supersample
    W = S * K
    im = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    # caminho: base embaixo-esquerda -> cotovelo -> ponta em cima-direita (canudo flexível)
    pts = [(0.20, 0.84), (0.36, 0.60), (0.40, 0.42), (0.52, 0.26), (0.80, 0.16)]
    # amostra suave (Catmull-Rom simples)
    def cr(p0, p1, p2, p3, t):
        return tuple(0.5 * ((2 * p1[i]) + (-p0[i] + p2[i]) * t + (2 * p0[i] - 5 * p1[i] + 4 * p2[i] - p3[i]) * t * t + (-p0[i] + 3 * p1[i] - 3 * p2[i] + p3[i]) * t ** 3) for i in range(2))
    P = [pts[0]] + pts + [pts[-1]]
    path_pts = []
    for i in range(1, len(P) - 2):
        for k in range(40): path_pts.append(cr(P[i - 1], P[i], P[i + 1], P[i + 2], k / 40))
    path_pts.append(pts[-1])
    path_pts = [(x * W, y * W) for x, y in path_pts]
    width = 0.15 * W
    d = ImageDraw.Draw(im)
    # contorno preto + sombra
    sh = Image.new("RGBA", (W, W), (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
    for a, b in zip(path_pts, path_pts[1:]):
        sd.line([(a[0] + 14, a[1] + 18), (b[0] + 14, b[1] + 18)], fill=(0, 0, 0, 110), width=int(width + 40))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
    d = ImageDraw.Draw(im)
    for a, b in zip(path_pts, path_pts[1:]):
        d.line([a, b], fill=(0, 0, 0, 255), width=int(width + 64))
        d.ellipse([b[0] - (width + 64) / 2, b[1] - (width + 64) / 2, b[0] + (width + 64) / 2, b[1] + (width + 64) / 2], fill=(0, 0, 0, 255))
    # listras ao longo do caminho (distância acumulada)
    acc = 0.0; stripe = 0.10 * W
    for a, b in zip(path_pts, path_pts[1:]):
        seg = math.dist(a, b)
        if seg == 0: continue
        dx, dy = (b[0] - a[0]) / seg, (b[1] - a[1]) / seg
        nx, ny = -dy, dx
        pos = 0.0
        while pos < seg:
            step = min(seg - pos, stripe - (acc % stripe))
            c = (225, 24, 36, 255) if int(acc // stripe) % 2 == 0 else (255, 255, 255, 255)
            p0 = (a[0] + dx * pos, a[1] + dy * pos); p1 = (a[0] + dx * (pos + step + 1.5), a[1] + dy * (pos + step + 1.5))
            hw = width / 2
            d.polygon([(p0[0] + nx * hw, p0[1] + ny * hw), (p1[0] + nx * hw, p1[1] + ny * hw), (p1[0] - nx * hw, p1[1] - ny * hw), (p0[0] - nx * hw, p0[1] - ny * hw)], fill=c)
            pos += step; acc += step
    im = im.resize((S, S), Image.LANCZOS)
    im.save(os.path.join(OUT, path))


def spotlight(path, W=3840, H=2160, r=0.16, edge=0.55, dark=185):
    """overlay escuro com 'buraco' elíptico transparente no centro (spotlight). Mover pela Posição p/ mirar."""
    import numpy as np
    yy, xx = np.mgrid[0:H, 0:W].astype("float32")
    d = np.sqrt(((xx - W / 2) / (W * r)) ** 2 + ((yy - H / 2) / (W * r * 0.62)) ** 2)
    a = np.clip((d - 1.0) / edge, 0, 1) ** 1.2 * dark
    arr = np.zeros((H, W, 4), dtype="uint8"); arr[..., 3] = a.astype("uint8")
    Image.fromarray(arr, "RGBA").save(os.path.join(OUT, path))


if __name__ == "__main__":
    spotlight("spot_dark.png")
    cluster("interrogacao_cluster.png")
    q = qmark(700); q.save(os.path.join(OUT, "interrogacao_big.png"))
    straw("canudinho.png")
    print("ok", os.listdir(OUT))
