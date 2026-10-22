"""Ganho fixo dos SFX: tabela GAIN_DB do Matheus (sfx_levels.gain_for) ou regra por RMS ativo/pico p/ arquivo novo."""
import os, sys, subprocess, tempfile, wave
import numpy as np
sys.path.insert(0, os.path.expanduser("~/.claude/skills/minecraft-video-editor/scripts"))
from sfx_levels import gain_for
_c = {}


def levels(path, off, dur):
    k = (path, round(off, 3), round(dur, 3))
    if k in _c: return _c[k]
    tmp = os.path.join(tempfile.gettempdir(), "sfxlv_agua.wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(off), "-t", str(dur), "-i", path, "-vn", "-ac", "1", "-ar", "44100", tmp], check=True)
    w = wave.open(tmp); d = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768.0; w.close()
    if len(d) < 441: _c[k] = (-6.0, -20.0); return _c[k]
    pk = 20 * np.log10(np.abs(d).max() + 1e-9)
    hop = 882; n = max(len(d) // hop, 1)
    fr = np.array([np.sqrt((d[i * hop:(i + 1) * hop] ** 2).mean()) for i in range(n)])
    act = fr > fr.max() * 10 ** (-35 / 20.0)
    rms = 20 * np.log10(np.sqrt((fr[act] ** 2).mean()) + 1e-9)
    _c[k] = (float(pk), float(rms)); return _c[k]


def gain(path, off, dur, name):
    pk, rm = levels(path, off, dur)
    g, _ = gain_for(name, pk, rm, dur, {})
    return round(float(g), 2)
