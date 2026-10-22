"""Extrai as faixas de voz do bruto numa passada só (21/10/2026): antes eram 3 ffmpeg lendo o arquivo de vários GB 3 vezes.

uso: python extract_audio.py <bruto.mp4> <pasta> [--s3]
  -> <pasta>/s1.wav (POV/dublagem, faixa 0:a:0), s2.wav (call, 0:a:1) [, s3.wav (jogo, 0:a:2) só com --s3]
Formato = o de sempre: 48 kHz, MONO (média dos canais = o que o cutengine calcula), PCM 16 bits.
s3/t3 não são usados pelo corte nem pelo plano (só contexto opcional do timeline_diff): pular economiza 1 passada de GPU no Whisper.
"""
import os, subprocess, sys


def main():
    a = sys.argv[1:]
    if len(a) < 2:
        sys.exit(__doc__)
    bruto, out = a[0], a[1]
    os.makedirs(out, exist_ok=True)
    n = 3 if "--s3" in a else 2
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", bruto]
    for k in range(n):
        cmd += ["-map", "0:a:%d" % k, "-vn", "-ac", "1", "-ar", "48000", "-c:a", "pcm_s16le", os.path.join(out, "s%d.wav" % (k + 1))]
    subprocess.run(cmd, check=True)
    print("ok:", ", ".join(os.path.join(out, "s%d.wav" % (k + 1)) for k in range(n)))


if __name__ == "__main__":
    main()
