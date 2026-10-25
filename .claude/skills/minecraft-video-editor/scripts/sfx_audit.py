"""Audita os SFX do plano NO RENDER (v13: inaudíveis; v14b: por cima da voz; v4 = calibrado pelo que o Matheus deixou: pico do SFX = pico da fala +0...+3 dB, mediana +2,5; impactos +3...+6).
Uso: python sfx_audit.py <plan3.json> <render.mp4>
Para cada SFX: pico no render durante o SFX (local) vs. pico "base" (fala+música) em janelas de 0.4 s antes/depois (sem o SFX).
 delta = local - base. Alvo dele: mediana +2...+3 dB; sons longos/brickwalled (fail, buzina, bruh, scratch, shine) 0...+2 é o desejado (ficam "atrás" da voz);
 impactos curtos (vine boom, boing, bonk, orbs) +3...+6. delta < -1 e rmsD < 0 = enterrado (só então revisar o ganho). NÃO subir tudo até +5 (foi o erro da v14b).
 Para auditar a timeline DELE: montar um plano-fantasma {"sfx":[{file,tl,dur}]} a partir do dump (timeline_diff.py --out) e rodar contra o render do clone.
Também imprime: pico máximo do render (alvo <= -1 dBFS; sobreposição SFX+voz pode estourar), pico/RMS médio dos SFX no plano.
"""
import sys, os, json, subprocess, tempfile, wave
import numpy as np

plan = json.load(open(sys.argv[1], encoding="utf8")); render = sys.argv[2]
sr = 44100        # 21/10: PCM float32 pelo pipe (sem WAV temporário fixo no C:, sem cópia float64 de ~600 MB)
d = np.frombuffer(subprocess.run(["ffmpeg", "-loglevel", "error", "-i", render, "-vn", "-ac", "2", "-ar", str(sr), "-f", "f32le", "-"],
                                 check=True, capture_output=True).stdout, dtype=np.float32)
d = np.abs(d.reshape(-1, 2)).max(axis=1)      # 25/10: maior canal (o "-ac 1" do ffmpeg SOMA L+R e inventava pico acima de 0 dBFS)
db = lambda x: 20 * np.log10(x + 1e-9)
END = len(d) / sr


def pk(a, b):       # pico em [a,b]; janela fora do áudio (SFX perto do fim) = -99 em vez de quebrar
    seg = d[int(max(0, a) * sr): int(min(END, max(a + 0.01, b)) * sr)]
    return db(np.abs(seg).max()) if b > a and len(seg) else -99.0
def rms(a, b):      # RMS máx em janelas de 100 ms dentro de [a,b]
    seg = d[int(max(0, a) * sr): int(min(END, max(a + 0.1, b)) * sr)]; h = int(0.1 * sr)
    return max(db(np.sqrt((seg[i:i + h] ** 2).mean())) for i in range(0, max(1, len(seg) - h), h // 2)) if len(seg) >= h else -99.0
# 25/10: pico do render = TRUE PEAK do ebur128 nos canais originais (o pico do mono convertido não bate com a medida do check_final)
_eb = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", render, "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True, errors="replace").stderr
_tp = [float(x.split(":")[1].split()[0]) for x in _eb.splitlines() if x.strip().startswith("Peak:")]
print("pico máximo do render: true peak %s dBTP (alvo <= -1)" % ("%.1f" % _tp[-1] if _tp else "?"))
rows = []
for s in plan["sfx"]:
    a = s["tl"]; ln = min(s.get("dur", 1.0), 0.8); local = pk(a, a + ln)
    base = [x for x in [pk(t, t + 0.4) for t in np.arange(a - 3.0, a - 0.3, 0.4)] + [pk(t, t + 0.4) for t in np.arange(a + s.get("dur", 1.0) + 0.3, a + s.get("dur", 1.0) + 3.0, 0.4)] if x > -98]
    b = float(np.median(base)) if base else -99.0
    rl = rms(a, a + ln); rb = float(np.median([rms(t, t + 0.4) for t in np.arange(a - 3.0, a - 0.3, 0.4)])) if a > 3.5 else -20.0
    rows.append((a, os.path.basename(s["file"])[:36], s.get("rms_db", s.get("peak_db")), local, b, local - b, rl - rb))
for a, n, p, l, b, dl, rd in rows:
    print("%7.2f  %-36s alvo %5s  pico %6.1f (base %6.1f, delta %+5.1f)  rmsD %+5.1f %s" % (a, n, p if p is not None else "-", l, b, dl, rd, "" if (dl >= -1 or rd >= 0) else "  <-- enterrado?"))
dl = [r[5] for r in rows]; rd = [r[6] for r in rows]
print("SFX audíveis (delta >= -1 dB ou rmsD >= 0): %d/%d | delta de pico mediano %+.1f dB (alvo dele +2...+3) | rmsD mediano %+.1f dB | acima de +6 dB: %d (revisar: competem com a voz)" % (sum(1 for r in rows if r[5] >= -1 or r[6] >= 0), len(rows), float(np.median(dl)), float(np.median(rd)), sum(1 for r in rows if r[5] > 6)))
