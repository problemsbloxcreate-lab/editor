"""Acha os presets de exportação do Premiere/Media Encoder em QUALQUER versão instalada (2024, 2025, 2026…).
uso: from adobe_presets import h264_preset, wav_preset   (devolvem caminho com '/' ou None)"""
import glob, os

ROOTS = [os.environ.get("ProgramFiles", r"C:\Program Files") + r"\Adobe", r"C:\Program Files\Adobe"]


def _find(name):
    hits = []
    for r in ROOTS:
        hits += glob.glob(os.path.join(r, "*", "MediaIO", "systempresets", "*", name))
    # Media Encoder primeiro, depois Premiere; versão mais nova primeiro
    hits.sort(key=lambda p: ("Media Encoder" not in p, [-int(x) for x in p.split() if x.isdigit()][:1] or [0]))
    return hits[0].replace("\\", "/") if hits else None


def h264_preset():
    return _find("H264 Match Source - High bitrate.epr")


def wav_preset():
    return _find("Waveform Audio 48kHz 16-bit.epr")


if __name__ == "__main__":
    print("H264:", h264_preset()); print("WAV :", wav_preset())
