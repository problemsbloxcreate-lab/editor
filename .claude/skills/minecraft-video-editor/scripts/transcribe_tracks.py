"""Transcreve uma faixa de áudio com o MESMO motor do Estúdio Problems (js/transcribe.js + servidor-ia/worker.js),
só que rodando LOCAL (faster-whisper na placa de vídeo; sem login, sem chave, sem internet depois do 1º download do modelo).

Motor (igual ao do Estúdio):
  - áudio 16 kHz mono, cortado em pedaços de até 25 s, cada corte no trecho mais quieto dos últimos 4 s (janela de 50 ms);
    pedaço com pico < 0.004 (silêncio) é pulado;
  - whisper-large-v3-turbo, task=transcribe, language=pt, vad_filter=True, condition_on_previous_text=False,
    initial_prompt = texto dos 3 últimos trechos (últimos 200 caracteres), palavras com tempo;
  - tempos devolvidos no tempo do arquivo (início do pedaço + tempo dentro dele, fim limitado à duração do pedaço);
  - "frases": a quebra em frases curtas do Estúdio (pontuação, vírgula com 3+ palavras, pausa > 0,35 s ou 8 palavras).

Uso: python transcribe_tracks.py <audio/vídeo> <saida.json> [<audio2> <saida2.json> ...] [--lang pt] [--model large-v3-turbo] [--device auto|cuda|cpu]
     (vários pares no mesmo comando = o modelo carrega uma vez só)
Saída (formato que o resto da skill já usa): {"text", "segments":[{s,e,t,nsp}], "words":[{w,s,e}], "frases":[{s,e,t,w}], "motor":{...}}
"""
import glob, json, os, subprocess, sys, time
import numpy as np

SR = 16000


def _cuda_dlls():
    """cuBLAS/cuDNN vindos do pip (nvidia-cublas-cu12 / nvidia-cudnn-cu12) entram no caminho de DLL do Windows"""
    try:
        import nvidia
        for base in getattr(nvidia, "__path__", []):
            for d in glob.glob(os.path.join(base, "*", "bin")):
                os.add_dll_directory(d); os.environ["PATH"] = d + os.pathsep + os.environ.get("PATH", "")
    except Exception:
        pass


def load_audio(path):
    raw = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def chunks(mono):
    """igual ao Transcribe.chunks do Estúdio"""
    out, MAX, SEARCH, win = [], 25 * SR, 4 * SR, round(SR * .05)
    e2 = mono.astype(np.float64) ** 2
    cs = np.concatenate([[0.0], np.cumsum(e2)])
    pos, n = 0, len(mono)
    while pos < n:
        end = min(n, pos + MAX)
        if end < n:
            best, bestE = end, float("inf")
            for i in range(end - SEARCH, end - win, win):
                e = cs[i + win] - cs[i]
                if e < bestE: bestE, best = e, i + (win >> 1)
            end = best
        peak = float(np.abs(mono[pos:end:64]).max()) if end > pos else 0.0
        if peak > .004: out.append((pos / SR, mono[pos:end]))
        pos = end
    return out


def fine(segs):
    """igual ao Transcribe.fine: frases curtas com o segundo de cada uma"""
    import re
    out = []
    for sg in segs:
        w = sg.get("w") or []
        if len(w) <= 7: out.append(sg); continue
        cur = []

        def push():
            if cur: out.append({"s": cur[0][0], "e": cur[-1][1], "t": re.sub(r"\s+([,.!?;:])", r"\1", " ".join(x[2] for x in cur)), "w": list(cur)})
            cur.clear()
        for i, x in enumerate(w):
            nx = w[i + 1] if i + 1 < len(w) else None
            cur.append(x)
            pause = nx[0] - x[1] if nx else 0
            if not nx or re.search(r"[.!?…]$", x[2]) or (re.search(r"[,;:]$", x[2]) and len(cur) >= 3) or pause > .35 or len(cur) >= 8: push()
        push()
    return out


_MODELS = {}


def load_model(name, device):
    """Carrega UMA vez por processo (21/10: várias faixas / notas no mesmo processo não recarregam ~1,6 GB nem refazem o aquecimento da placa)."""
    if (name, device) not in _MODELS:
        _MODELS[(name, device)] = _load_model(name, device)
    return _MODELS[(name, device)]


def _load_model(name, device):
    from faster_whisper import WhisperModel
    if device in ("auto", "cuda"):
        _cuda_dlls()
        try:
            m = WhisperModel(name, device="cuda", compute_type="float16")
            m.transcribe(np.zeros(SR, np.float32), language="pt")  # força carregar cuBLAS/cuDNN agora
            return m, "cuda/float16"
        except Exception as e:
            if device == "cuda": raise
            print("placa indisponível (%s) — usando o processador" % str(e)[:120], flush=True)
    return WhisperModel(name, device="cpu", compute_type="int8"), "cpu/int8"


def transcribe(path, lang="pt", model_name="large-v3-turbo", device="auto"):
    t0 = time.time()
    mono = load_audio(path)
    model, dev = load_model(model_name, device)
    segs = []
    parts = chunks(mono)
    for k, (base, data) in enumerate(parts):
        dur = len(data) / SR
        prompt = " ".join(s["t"] for s in segs[-3:])[-200:] or None
        it, _ = model.transcribe(data, language=lang, task="transcribe", vad_filter=True, condition_on_previous_text=False,
                                 initial_prompt=prompt, word_timestamps=True)
        for s in it:
            tx = (s.text or "").strip()
            if not tx: continue
            w = [[round(base + (x.start or 0), 2), round(base + min(dur, x.end or 0), 2), (x.word or "").strip()] for x in (s.words or [])]
            w = [x for x in w if x[2]]
            segs.append({"s": round(base + (s.start or 0), 2), "e": round(base + min(dur, s.end or dur), 2), "t": tx, "nsp": round(s.no_speech_prob, 3), "w": w})
        print("  pedaço %d/%d (%.0f s)" % (k + 1, len(parts), base + dur), flush=True)
    words = [{"w": x[2], "s": x[0], "e": x[1]} for s in segs for x in s["w"]]
    out = {"text": " ".join(s["t"] for s in segs),
           "segments": [{"s": s["s"], "e": s["e"], "t": s["t"], "nsp": s["nsp"]} for s in segs],
           "words": words, "frases": fine(segs),
           "motor": {"modelo": model_name, "dispositivo": dev, "pedacos": len(parts), "segundos_audio": round(len(mono) / SR, 1),
                     "segundos_gastos": round(time.time() - t0, 1), "params": "25s/silêncio, vad, sem contexto anterior, prompt=3 últimos trechos"}}
    return out


def main():
    a = sys.argv[1:]
    if len(a) < 2: sys.exit(__doc__)
    opt = lambda n, d: a[a.index(n) + 1] if n in a else d
    pos, i = [], 0
    while i < len(a):
        if a[i].startswith("--"):
            i += 2
            continue
        pos.append(a[i]); i += 1
    for src, dst in zip(pos[0::2], pos[1::2]):
        out = transcribe(src, opt("--lang", "pt"), opt("--model", "large-v3-turbo"), opt("--device", "auto"))
        json.dump(out, open(dst, "w", encoding="utf8"), ensure_ascii=False)
        m = out["motor"]
        print(dst, len(out["segments"]), "segmentos", len(out["words"]), "palavras |", m["dispositivo"], "| %.0f s de áudio em %.0f s" % (m["segundos_audio"], m["segundos_gastos"]))


if __name__ == "__main__":
    main()
