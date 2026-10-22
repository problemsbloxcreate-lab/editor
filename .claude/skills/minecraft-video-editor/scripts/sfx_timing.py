"""Timing dos SFX — corrige o ATRASO de SFX ancorados em palavra do ASR (achado em 16/10/2026, vídeo Bounce).

CAUSA (medida): o `start` de palavra do Whisper/Groq (whisper-large-v3) CHEGA DEPOIS do início real da fala — nas palavras que vêm depois de uma pausa,
o início de energia do mic é, na mediana, 0,19 s ANTES do `start` do ASR (p25 0,42 s; p75 0,03 s). Somado ao silêncio inicial do próprio arquivo do SFX
(0,03–0,18 s: wow 0,18, vine 0,09, sheep 0,05, boing 0,03), o som audível chegava 0,25–0,45 s depois da fala. O `end` da palavra tem o erro oposto
(estica a última palavra: "aqui." 2,88→3,88 s com a fala terminando em 3,4 s).

REGRAS:
  1. NUNCA ancorar SFX no `start`/`end` cru do ASR: passar por `refine_start()` / `refine_end()` (usam a energia RMS de 10 ms do mic da voz).
  2. Aparar o silêncio inicial do arquivo: `file_onset()` -> usar como in-point (src_off) e colocar o clipe em (onset_da_fala - PRE).
  3. PRE padrão 0,06 s (o SFX começa um fio ANTES da fala, como o Matheus faz; no corte: 0–0,1 s).
  4. Depois de qualquer ripple/edição: conferir `clip.start` de cada SFX contra o plano; `clip.start = t` NÃO move o clipe (apara a cabeça): remover e recolocar (overwriteClip).

API:  rms = np.load(...)  # RMS dB, 1 quadro = 10 ms, tempo da MESMA linha do tempo do ASR
      t_real = refine_start(rms, t_asr)    ;    t_fim = refine_end(rms, t_asr_end)    ;    off = file_onset(path)
CLI:  python sfx_timing.py <arquivo_sfx>      -> imprime o início audível
"""
import os, subprocess, sys, tempfile
import numpy as np

PRE = 0.06
BIAS_FALLBACK = 0.12      # sem dip de energia achado (fala contínua): adianta só um pouco


def _smooth(R, n=3):
    return np.convolve(R, np.ones(n) / n, mode="same")


def refine_start(R, t, back=0.45, fwd=0.08, rise_db=10.0, abs_thr=-38.0):
    """Início REAL da palavra que o ASR marcou em t: o primeiro quadro de energia depois do ÚLTIMO silêncio/dip antes de t+fwd.
    Fala contínua (sem dip na janela) -> t - BIAS_FALLBACK."""
    S = _smooth(np.asarray(R, dtype=float))
    i1 = min(int((t + fwd) * 100), len(S) - 1); i0 = max(int((t - back) * 100), 1)
    floor = float(np.percentile(S[max(i0 - 60, 0):i1 + 1], 15))
    thr = max(abs_thr, floor + rise_db)
    # último quadro "quieto" (< thr - 4) na janela
    quiet = np.where(S[i0:i1 + 1] < thr - 4.0)[0]
    if len(quiet) == 0: return round(max(t - BIAS_FALLBACK, 0.0), 3)
    last_quiet = i0 + quiet[-1]
    for i in range(last_quiet, i1 + 1):
        if S[i] >= thr and (i + 4 > len(S) or S[i:i + 4].min() >= thr - 6.0):     # sobe e SUSTENTA (40 ms)
            return round(i / 100.0, 3)
    return round(t, 3)


def refine_end(R, t, back=0.6, fwd=0.05, end_thr=-40.0):
    """Fim REAL da fala que o ASR marcou terminando em t (o Whisper estica a última palavra): último quadro com energia > end_thr em [t-back, t+fwd]."""
    S = _smooth(np.asarray(R, dtype=float))
    i0 = max(int((t - back) * 100), 0); i1 = min(int((t + fwd) * 100), len(S) - 1)
    idx = np.where(S[i0:i1 + 1] > end_thr)[0]
    return round((i0 + idx[-1]) / 100.0, 3) if len(idx) else round(t, 3)


_on = {}


def file_onset(path, max_dur=1.5):
    """segundos de silêncio inicial do arquivo de SFX (primeiro amostra > max(-45 dBFS, pico-30 dB))"""
    if path in _on: return _on[path]
    import soundfile as sf
    tmp = os.path.join(tempfile.gettempdir(), "sfx_onset_%d.wav" % os.getpid())
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-t", str(max_dur), "-i", path, "-vn", "-ac", "1", "-ar", "48000", tmp], check=True)
    x, sr = sf.read(tmp); a = np.abs(x)
    thr = max(10 ** (-45 / 20.0), a.max() * 10 ** (-30 / 20.0)) if len(a) else 1.0
    idx = np.where(a > thr)[0]
    _on[path] = round(float(idx[0]) / sr, 3) if len(idx) else 0.0
    return _on[path]


def place_time(t_speech_onset, pre=PRE):
    """onde colocar o clipe (já com in-point = file_onset): um fio antes do início da fala"""
    return round(max(t_speech_onset - pre, 0.0), 4)


if __name__ == "__main__":
    for p in sys.argv[1:]: print(p, "início audível: %.3f s" % file_onset(p))
