"""Folha de FOCO para zooms (regra 2, 20/10/2026): um frame por zoom com grade rotulada em coordenadas do quadro 1920x1080.

Por quê: na v2 do "Bebi toda a água" 96 zooms usaram só 3 focos (65× centro 960,560; 18× HUD 960,0; 13× 900,1010) —
"seus zooms vão sempre pra mesma direção, e não vão na direção do objeto ou do que é mencionado" (Matheus).
Fluxo: gerar a folha -> OLHAR cada frame (Read) -> anotar fx,fy do objeto/personagem citado no plano -> só então montar.
Zoom sem foco conferido não entra.

uso: python zoom_focus_sheet.py <video> <saida_dir> t1[:rotulo] t2[:rotulo] ...
     (video = render/preview da timeline OU a fonte; t em segundos desse vídeo)
     python zoom_focus_sheet.py <video> <saida_dir> --plan plan.json   (usa plan['zooms'][i]['t'] e 'why'; precisa ser o render da MESMA timeline)
"""
import json, os, subprocess, sys

GRID_X, GRID_Y = 160, 120
FONT = r"fontfile='C\:/Windows/Fonts/arial.ttf':"   # sem fontfile o drawtext falha no Windows (Fontconfig)


def grid_filter(crop=""):
    f = ([crop] if crop else []) + ["scale=1920:1080", "drawgrid=w=%d:h=%d:t=2:c=yellow@0.45" % (GRID_X, GRID_Y),
         "drawbox=x=955:y=535:w=10:h=10:c=red@0.9:t=fill"]
    for x in range(0, 1920, GRID_X):
        f.append("drawtext=" + FONT + "text='%d':x=%d:y=4:fontsize=26:fontcolor=yellow:box=1:boxcolor=black@0.6" % (x, x + 4))
    for y in range(GRID_Y, 1080, GRID_Y):
        f.append("drawtext=" + FONT + "text='%d':x=4:y=%d:fontsize=26:fontcolor=yellow:box=1:boxcolor=black@0.6" % (y, y + 4))
    return ",".join(f)


def _crop_for(video):
    """Bruto 3840x1080 (POV + call lado a lado): a sequência mostra a METADE DIREITA (Movimento posição 0,540) -> recortar,
    senão a grade fica espremida e as coordenadas não batem com a tela (achado na revisão de 21/10)."""
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0", video],
                       capture_output=True, text=True)
    try:
        w, h = (int(x) for x in r.stdout.strip().split(",")[:2])
    except ValueError:
        return ""
    return "crop=%d:%d:%d:0" % (w // 2, h, w // 2) if w >= 3.4 * h else ""


def sheet(video, out_dir, items):
    os.makedirs(out_dir, exist_ok=True)
    vf = grid_filter(_crop_for(video))
    outs, jobs = [], []
    for i, (t, label) in enumerate(items):
        safe = "".join(ch if ch.isalnum() else "_" for ch in label)[:40]
        o = os.path.join(out_dir, "z%03d_%07.2f_%s.jpg" % (i, t, safe))
        jobs.append(["ffmpeg", "-v", "error", "-y", "-ss", "%.3f" % (t + 0.05), "-i", video, "-frames:v", "1", "-vf",
                     vf + ",drawtext=" + FONT + "text='%s':x=(w-tw)/2:y=h-50:fontsize=34:fontcolor=white:box=1:boxcolor=black@0.7" % label.replace("'", "").replace(":", " ")[:70],
                     "-q:v", "4", o])
        outs.append(o)
    from concurrent.futures import ThreadPoolExecutor          # 21/10: 4 em paralelo (~100 zooms: ~2 min -> ~25 s)
    with ThreadPoolExecutor(4) as ex:
        list(ex.map(lambda c: subprocess.run(c, check=False), jobs))
    return outs


def main():
    video, out_dir = sys.argv[1], sys.argv[2]
    if "--plan" in sys.argv:
        P = json.load(open(sys.argv[sys.argv.index("--plan") + 1], encoding="utf8"))
        items = [(z["t"], "%s %s%%" % (z.get("why", ""), z.get("s", ""))) for z in P["zooms"] if z.get("s", 100) > 100.5]
    else:
        items = []
        for a in sys.argv[3:]:
            t, _, lab = a.partition(":")
            items.append((float(t), lab or a))
    for o in sheet(video, out_dir, items): print(o)


if __name__ == "__main__":
    main()
