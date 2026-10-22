"""Ganho de clipe da MÚSICA pelo loudness do TRECHO usado (regra 5b, 20/10/2026).

O Matheus não usa um dB fixo: no 'Bebi toda a água do mundo' ele subiu as faixas que são baixas na origem
(Expedition 13 −18 LUFS -> −16,6 dB; That Thing Behind Us −20 LUFS -> −14,6 dB) e deixou as altas em −26/−27.
O que fica constante é o EFETIVO = ganho do clipe (dB) + LUFS do trecho: mediana −35,6 LUFS (p10 −40, p90 −31).

uso:  python music_level.py <arquivo.mp3> <src_in_s> <dur_s> [cama|respiro|climax]
      from music_level import music_gain; g, lufs = music_gain(path, src_in, dur, kind="cama")
"""
import re, subprocess, sys

TARGET = {"cama": -35.6,      # sob fala (padrão)
          "respiro": -28.0,   # sem fala: time-lapse, inserção/promo, travessia (ele sobe +6…+9: −27,4 / −24,7 / −28,4)
          "climax": -33.0}    # tensão/vilão/épico com fala por cima (That Thing Behind Us, Weapon of Choice: −34…−36 efetivo; o clímax final ele abriu em ~−31 e desceu c/ keyframe)
CLAMP = (-30.0, -8.0)         # faixa de ganho de clipe que ele usou (−27,3 … −9,0)


def section_lufs(path, src_in, dur):
    out = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-ss", str(src_in), "-t", str(min(dur, 30.0)), "-i", path,
                          "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True, encoding="utf8", errors="ignore").stderr
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", out)
    return float(m[-1]) if m else None


def music_gain(path, src_in=0.0, dur=20.0, kind="cama"):
    L = section_lufs(path, src_in, dur)
    if L is None or L < -60: return -26.0, L
    g = TARGET.get(kind, TARGET["cama"]) - L
    return round(min(max(g, CLAMP[0]), CLAMP[1]), 1), L


if __name__ == "__main__":
    p, a, d = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
    k = sys.argv[4] if len(sys.argv) > 4 else "cama"
    g, L = music_gain(p, a, d, k)
    print("trecho %.1f LUFS -> ganho de clipe %+.1f dB (%s, efetivo %.1f)" % (L, g, k, g + L))
