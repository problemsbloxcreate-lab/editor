"""Extrai os pedaços A/C usados como capa de POV (1920x1080, NVENC alta qualidade, sem áudio, 0,5 s de folga)."""
import json, os, subprocess
P = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'plan.json'), encoding='utf8'))
for c in P['pov']:
    if c['src'] == 'B' or os.path.exists(c['file']): continue
    a = max(0.0, c['src_in'] - 0.5)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', '%.4f' % a, '-i', P['raw'][c['src']], '-t', '%.4f' % (c['dur'] + 1.0), '-an', '-vf', 'scale=1920:1080:flags=lanczos',
                    '-c:v', 'h264_nvenc', '-preset', 'p6', '-rc', 'vbr', '-cq', '15', '-b:v', '0', '-pix_fmt', 'yuv420p', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', c['file']], check=True)
    print('ok', c['file'])
