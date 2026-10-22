"""Acha as NOTAS DE EDIÇÃO sussurradas/faladas pelo criador no bruto ("takes futuros, editor", "time lapse editor", "corta aí"...).
Elas são pedidos diretos ao editor: NÃO vão pro vídeo (cortar) e disparam um efeito (ver SKILL: regra 9).
O ASR normal costuma ignorar sussurro (a nota fica ~-25..-40 dBFS, bem abaixo da fala ~-15), então:
  1) lê o ASR (palavras) e procura palavras-chave (editor, takes, time lapse, timelapse, corta);
  2) varre a faixa s1 por trechos de baixa energia (sussurro) entre fala forte, e re-transcreve só esses trechos com +14 dB de ganho.
Uso: python find_notes.py <s1.wav (16k mono)> <t1.json> [--from 0 --to 480] [--offset 0] [--max 40]
   --offset: soma ao tempo dos candidatos (p/ wav que começa em t0 do bruto)
Saída: lista "t_ini-t_fim  rms  texto". LIMITE (testado): o Whisper devolve VAZIO p/ a nota de "takes futuros" mesmo com +14 dB e há ~70 candidatos/6 min -> a detecção é só uma lista;
O TIMECODE VEM DO MATHEUS (ele aponta: "no 00;02;23;14 ele fala takes futuros editor") ou da escuta do trecho (energia baixa colada na fala, ~0.9 s). Confirme antes de cortar.
"""
import sys, os, re, json, wave, tempfile, subprocess
import numpy as np

KEY = re.compile(r"editor|takes?\b|time ?lapse|timelapse|corta|futuros?", re.I)


def load(wav):
    w = wave.open(wav); sr = w.getframerate()
    d = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768.0
    if w.getnchannels() > 1: d = d.reshape(-1, w.getnchannels()).mean(1)
    return d, sr


def candidates(d, sr, t0, t1, lo=-42.0, hi=-23.0, loud=-19.0, minlen=0.5, maxlen=4.0):
    hop = int(0.05 * sr); n = (len(d) - hop) // hop
    rms = np.array([20 * np.log10(np.sqrt((d[i * hop:(i + 1) * hop] ** 2).mean()) + 1e-9) for i in range(n)])
    out, i = [], int(t0 / 0.05)
    end = min(n, int(t1 / 0.05))
    while i < end:
        if lo <= rms[i] <= hi:
            j = i
            while j < end and (lo - 6 <= rms[j] <= hi + 3): j += 1
            ln = (j - i) * 0.05
            before = rms[max(0, i - 8):i].max() if i > 0 else -99
            after = rms[j:j + 8].max() if j + 8 < n else -99
            if minlen <= ln <= maxlen and (before > loud or after > loud):
                out.append((i * 0.05, j * 0.05, float(np.median(rms[i:j]))))
            i = j + 1
        else:
            i += 1
    return out


def transcribe(wav_path, a, b, d, sr):
    seg = d[int(max(0, a - 0.15) * sr): int((b + 0.15) * sr)] * (10 ** (14 / 20.0))
    seg = np.clip(seg, -1, 1)
    tmp = os.path.join(tempfile.gettempdir(), "note_%d.wav" % int(a * 100))
    w = wave.open(tmp, "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((seg * 32767).astype(np.int16).tobytes()); w.close()
    outj = tmp.replace(".wav", ".json")
    try:                         # 21/10: no MESMO processo (o modelo carrega 1 vez para todos os candidatos; antes 1 processo por candidato)
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import transcribe_tracks as _tt
        t = _tt.transcribe(tmp)["text"].strip()
    except Exception:
        t = ""
    for f in (tmp, outj):
        try: os.remove(f)
        except OSError: pass
    return t


def main():
    wav, tj = sys.argv[1], sys.argv[2]
    g = lambda k, dflt: float(sys.argv[sys.argv.index(k) + 1]) if k in sys.argv else dflt
    t0, t1, off, mx = g("--from", 0.0), g("--to", 1e9), g("--offset", 0.0), int(g("--max", 40))
    words = json.load(open(tj, encoding="utf8"))["words"]
    print("== palavras-chave no ASR ==")
    for i, w in enumerate(words):
        if KEY.search(w["w"]) and t0 <= w["s"] + off <= t1:
            print("%8.1f  %s" % (w["s"] + off, " ".join(x["w"].strip() for x in words[max(0, i - 6): i + 7])))
    d, sr = load(wav)
    cands = candidates(d, sr, max(0.0, t0 - off), min(len(d) / sr, t1 - off))
    print("== trechos sussurrados candidatos: %d (transcrevendo até %d com +14 dB) ==" % (len(cands), mx))
    for a, b, r in cands[:mx]:
        t = transcribe(wav, a, b, d, sr)
        flag = "  <<< NOTA?" if KEY.search(t) else ("  <<< vazio+baixo: sussurro/resmungo? ouvir" if (not t and r < -30) else "")
        print("%8.2f-%8.2f  rms %5.1f dB  %s%s" % (a + off, b + off, r, t, flag))


main()
