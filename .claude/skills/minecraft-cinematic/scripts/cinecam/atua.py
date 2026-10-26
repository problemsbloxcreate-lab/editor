"""atua: atuação v1.0 (25/10/2026) — personagens que se mexem como animação de verdade, sem keyframe à mão.

O corpo do mod agora dobra (cotovelo, joelho, tronco no quadril; boca e piscar). Este módulo dirige esse corpo:
  • POSES: as poses de atuação do Shorts web (site/index.html poseAlvo + corpoVivo, calibradas pelo dono em 19–20/10) com as mesmas
    convenções; `Ator.pose(t, "point")` troca de pose e o resto acontece sozinho.
  • MOLAS por parte do corpo (dinâmica de 2ª ordem, f/ζ/r): o tronco puxa, a cabeça vem logo, o braço antecipa (r<0) e passa do
    ponto, o antebraço chega por último e balança (follow-through) — os princípios de animação saem da física, não de chave.
  • CAMADAS que não passam pela mola (ciclos): fala pela voz (gesto + cabeça + boca), andar/correr com fase pela DISTÂNCIA
    (pé não escorrega), comemorar, rir, tremer...
  • VIDA: respiração e troca de peso parado, piscar (sozinho e nas trocas de pose), pé no chão (o corpo desce quando o joelho dobra).

    from cinecam import *
    from cinecam.atua import Ator
    k = Ator("kadu", skin("kadu"), (x, y, z), yaw=0)
    k.pose(0.0, "idle").talk(0.2, 2.4, text="Você é IDOSO e não sabia!").pose(1.1, "point").pose(2.6, "comemora")
    k.walk(3.2, 4.6, to=(x, z + 3)).look(4.8, (x + 2, y + 1.6, z))
    actor = k.build()          # um Actor normal (Anim([actor]), render, stills) com todos os canais assados a 120 Hz

Convenção interna = a do Shorts web (radianos; braço x<0 vai para a frente; cotovelo <0 dobra para a frente; joelho >0 para trás;
tronco sp=[frente+, torção, lado]); a conversão para os canais do mod (graus; y/z dos braços com sinal trocado) fica em `_to_channels`.
"""
from __future__ import annotations

import math
import zlib
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np

from .actors import Actor, POSE, PN

D = 180.0 / math.pi
HZ = 120                       # assar a 120 Hz (molas estáveis; o render interpola para os subframes)


# --------------------------------------------------------------------------------------------------------------------------- pose buffer
class P:
    """Pose no formato do Shorts web.  h/aR/aL/lR/lL = (x,y,z) rad | sp = tronco | jb = [cotovelo D, cotovelo E, joelho D, joelho E]
    | dy = descida do corpo (blocos) | crouch = agachar 0..1 (vira perna+joelho+tronco)."""
    __slots__ = ("h", "aR", "aL", "lR", "lL", "sp", "jb", "dy", "crouch", "hop", "sq")

    def __init__(self):
        self.h = np.zeros(3); self.aR = np.zeros(3); self.aL = np.zeros(3); self.lR = np.zeros(3); self.lL = np.zeros(3)
        self.sp = np.zeros(3); self.jb = np.zeros(4); self.dy = 0.0; self.crouch = 0.0; self.hop = 0.0; self.sq = 0.0

    def vec(self) -> np.ndarray:
        return np.concatenate([self.h, self.aR, self.aL, self.lR, self.lL, self.sp, self.jb, [self.dy, self.crouch, self.hop, self.sq]])

    @staticmethod
    def from_vec(v: np.ndarray) -> "P":
        p = P()
        p.h, p.aR, p.aL, p.lR, p.lL, p.sp, p.jb = v[0:3], v[3:6], v[6:9], v[9:12], v[12:15], v[15:18], v[18:22]
        p.dy, p.crouch, p.hop, p.sq = v[22], v[23], v[24], v[25]
        return p


NV = 26
# mola por componente do vetor: (f Hz, ζ, r).  r<0 = antecipa; ζ<1 = passa do ponto.
# r = 0 em tudo (25/10, "rollback"): r != 0 soma a derivada da entrada e, numa troca de pose, dá um tranco de 1 quadro
# (o braço "volta" e depois vai).  A antecipação agora é desenhada na curva de transição (_prof); a mola só dá o atraso
# entre as partes e o passar do ponto (follow-through).
_G = {"h": (4.0, 0.7, 0.0), "aR": (3.3, 0.55, 0.0), "aL": (3.2, 0.55, 0.0), "lR": (4.0, 0.85, 0.0), "lL": (4.0, 0.85, 0.0),
      "sp": (3.0, 0.8, 0.0), "jbA": (2.6, 0.48, 0.0), "jbL": (4.0, 0.85, 0.0), "misc": (4.5, 0.9, 0.0)}
SPRING = np.array([_G["h"]] * 3 + [_G["aR"]] * 3 + [_G["aL"]] * 3 + [_G["lR"]] * 3 + [_G["lL"]] * 3 + [_G["sp"]] * 3
                  + [_G["jbA"]] * 2 + [_G["jbL"]] * 2 + [_G["misc"]] * 4)


def mirror(p: P) -> P:
    """Mesma pose com o outro braço (apontar com a esquerda etc.)."""
    q = P()
    q.h = p.h * [1, -1, -1]; q.sp = p.sp * [1, -1, -1]
    q.aR, q.aL = p.aL * [1, -1, -1], p.aR * [1, -1, -1]
    q.lR, q.lL = p.lL * [1, -1, -1], p.lR * [1, -1, -1]
    q.jb = p.jb[[1, 0, 3, 2]]
    q.dy, q.crouch, q.hop, q.sq = p.dy, p.crouch, p.hop, p.sq
    return q


# ------------------------------------------------------------------------------------------------------------------------------- poses
# Estáticas (alvo da mola).  Valores = poseAlvo + corpoVivo do Shorts web (quando o corpoVivo usa .set, ele vence).
def _cross(p: P):
    p.aR[:] = (-0.38, 0.95, 0.16); p.aL[:] = (-0.46, -0.95, -0.16); p.jb[0] = -1.62; p.jb[1] = -1.55


def _s(**kw) -> Callable[[P], None]:
    def f(p: P):
        for k, v in kw.items():
            if k == "jbR": p.jb[0] = v
            elif k == "jbL": p.jb[1] = v
            elif k == "kR": p.jb[2] = v
            elif k == "kL": p.jb[3] = v
            elif k in ("dy", "crouch"): setattr(p, k, v)
            elif k == "cross":
                _cross(p)
            else: getattr(p, k)[:] = v
    return f


STATIC: Dict[str, Callable[[P], None]] = {
    "idle": _s(), "talk": _s(), "calm": _s(),
    "point": _s(aR=(-1.52, 0, 0), jbR=-0.05, sp=(0.07, 0.16, 0), h=(0, -0.1, 0)),
    "stop": _s(aR=(-1.62, 0, 0.15), jbR=-0.35, sp=(0.07, 0.16, 0), h=(0, -0.1, 0)),
    "finger": _s(aR=(-1.35, 0.15, 0.18), jbR=-1.35, sp=(0.04, 0, 0)),
    "cross": _s(cross=1, sp=(-0.05, 0, 0)),
    "sus": _s(cross=1, sp=(-0.03, 0, -0.06), h=(0, -0.16, 0.14)),
    "smug": _s(cross=1, sp=(-0.1, 0, 0), h=(-0.19, 0, 0.1)),
    "tilt": _s(h=(0, -0.1, 0.3), sp=(0, 0, 0.07)),
    "hold": _s(aR=(-0.95, 0.18, 0.1), jbR=-0.65, sp=(0.05, 0.1, 0)),
    "mostra": _s(aR=(-0.95, 0.18, 0.1), jbR=-0.65, sp=(0.05, 0.1, 0), h=(0.08, 0, 0)),
    "entrega": _s(aR=(-0.95, 0.18, 0.1), jbR=-0.65, sp=(0.05, 0.1, 0)),
    "facepalm": _s(aR=(-1.05, 0.55, 0.25), jbR=-2.05, sp=(0.16, 0, 0), h=(0.3, 0, 0)),
    "pensando": _s(aR=(-0.75, 0.6, 0.22), jbR=-2.1, aL=(-0.4, -1.0, -0.12), jbL=-1.5, sp=(0.04, 0, 0), h=(-0.18, 0, 0.12)),
    "abraca": _s(aR=(-1.3, 0.55, 0.3), aL=(-1.3, -0.55, -0.3), jbR=-0.9, jbL=-0.9, sp=(0.1, 0, 0), h=(0.1, 0, 0)),
    "chora": _s(aR=(-1.15, 0.5, 0.22), aL=(-1.15, -0.5, -0.22), jbR=-1.95, jbL=-1.95, sp=(0.22, 0, 0), h=(0.26, 0, 0)),
    "vergonha": _s(aR=(-1.15, 0.5, 0.22), aL=(-1.15, -0.5, -0.22), jbR=-1.95, jbL=-1.95, sp=(0.22, 0, 0), h=(0.33, 0, 0)),
    "bravo": _s(aR=(0.15, 0, -0.32), aL=(0.15, 0, 0.32), jbR=-0.45, jbL=-0.45, sp=(0.12, 0, 0), h=(0.18, 0, 0)),
    "ombros": _s(aR=(-0.1, -0.55, -0.3), aL=(-0.1, 0.55, 0.3), jbR=-1.35, jbL=-1.35, sp=(0, 0, 0.05), h=(-0.05, 0, 0.18)),
    "grita": _s(aR=(0.25, 0, -0.45), aL=(0.25, 0, 0.45), jbR=-0.35, jbL=-0.35, sp=(0.2, 0, 0), h=(-0.42, 0, 0), crouch=0.27),
    "medo": _s(aR=(-1.15, 0.35, 0.1), aL=(-1.15, -0.35, -0.1), jbR=-1.25, jbL=-1.25, sp=(-0.32, 0, 0), h=(0.12, 0, 0), crouch=0.7),
    "susto": _s(aR=(-2.25, 0, -0.95), aL=(-2.25, 0, 0.95), jbR=-0.85, jbL=-0.85, sp=(-0.28, 0, 0), h=(-0.22, 0, 0), crouch=0.25),
    "sad": _s(h=(0.24, 0, 0), aR=(0.04, 0, 0.04), aL=(0.04, 0, -0.04), jbR=-0.08, jbL=-0.08, sp=(0.22, 0, 0)),
    "joinha": _s(aR=(-0.9, 0.1, 0.1), jbR=-1.0, sp=(0, 0.1, 0), h=(-0.05, 0, 0.1)),
    "apaixonado": _s(aR=(-0.6, 0.8, 0.15), aL=(-0.6, -0.8, -0.15), jbR=-1.5, jbL=-1.5, h=(-0.1, 0, 0)),
    "cochicha": _s(aR=(-1.0, 0.6, 0.25), jbR=-1.9, aL=(-0.2, 0, -0.1), sp=(0.12, 0, 0.12), h=(0.15, 0, -0.15)),
    "coca": _s(aR=(-2.0, 0.3, 0.55), jbR=-1.6, sp=(0, 0, 0.05), h=(0.05, 0, 0.15)),
    "bocejo": _s(aR=(-2.0, 0, 0.5), jbR=-0.4, sp=(-0.15, 0, 0), h=(-0.35, 0, 0)),
    "empurra": _s(aR=(-1.55, 0, 0.08), aL=(-1.55, 0, -0.08), jbR=-0.1, jbL=-0.1, sp=(0.28, 0, 0), lR=(0.38, 0, 0), lL=(-0.32, 0, 0),
                  kL=0.35, h=(0.12, 0, 0)),
    "sorrateiro": _s(aR=(-0.45, 0, 0.12), aL=(-0.45, 0, -0.12), jbR=-0.8, jbL=-0.8, h=(0.22, 0, 0), crouch=0.67),
    "boca": _s(h=(-0.28, 0, 0), aR=(-0.25, 0, -0.38), aL=(-0.25, 0, 0.38)),
    "sit": _s(lR=(-1.45, 0, 0.12), lL=(-1.45, 0, -0.12), kR=0.3, kL=0.3, aR=(-0.55, 0.1, 0.08), aL=(-0.55, -0.1, -0.08),
              jbR=-0.75, jbL=-0.75, sp=(0.06, 0, 0)),
    "comemora": _s(aR=(-2.7, 0, -0.62), aL=(-2.7, 0, 0.62), jbR=-0.3, jbL=-0.3, sp=(-0.14, 0, 0), h=(-0.22, 0, 0)),   # braços em V
    "rindo": _s(aR=(-0.45, 0.75, 0.18), aL=(-0.45, -0.75, -0.18), jbR=-1.2, jbL=-1.2, sp=(-0.17, 0, 0), h=(-0.23, 0, 0)),
    "palmas": _s(aR=(-0.95, 0.65, 0.1), aL=(-0.95, -0.65, -0.1), jbR=-1.1, jbL=-1.1, h=(-0.05, 0, 0)),
    "acena": _s(aR=(-2.55, 0, -0.25), jbR=-0.52, sp=(0, 0, -0.06)),
    "nervoso": _s(aR=(-0.6, 0.75, 0.15), aL=(-0.6, -0.75, -0.15), jbR=-1.45, jbL=-1.45, sp=(0.06, 0, 0), h=(0.08, 0, 0)),
    "procura": _s(aR=(-0.15, 0, 0.1), aL=(-0.15, 0, -0.1), h=(0.05, 0, 0)),
    "mine": _s(aR=(-1.5, 0, 0.1), jbR=-0.35, sp=(0.1, 0, 0), h=(0.25, 0, 0)),
    "agacha": _s(crouch=1.0, jbR=-0.5, jbL=-0.5, aR=(-0.35, 0, 0.1), aL=(-0.35, 0, -0.1)),
    "braco_frente": _s(aR=(-1.45, 0, 0.12), aL=(-1.45, 0, -0.12), jbR=-0.3, jbL=-0.3, sp=(0.08, 0, 0)),
}

# Oscilações (camada sem mola).  f(p, T, s) com s = semente do ator.
OSC: Dict[str, Callable[[P, float, float], None]] = {
    "comemora": lambda p, T, s: (p.aR.__setitem__(0, 0.25 * math.sin(T * 10)), p.aL.__setitem__(0, -0.25 * math.sin(T * 10)),
                                 p.jb.__setitem__(slice(0, 2), -0.35 * (math.sin(T * 10) ** 2 - 0.5)),
                                 setattr(p, "crouch", 0.3 * (1 - math.sin(T * 10) ** 2)), setattr(p, "hop", 0.18 * math.sin(T * 10) ** 2)),
    "rindo": lambda p, T, s: (setattr(p, "sp", np.array([-0.1 * math.sin(T * 14) ** 2, 0, 0])), p.h.__setitem__(0, -0.12 * math.sin(T * 14) ** 2)),
    "palmas": lambda p, T, s: (p.aR.__setitem__(1, 0.28 * math.sin(T * 9) ** 2 - 0.14), p.aL.__setitem__(1, -0.28 * math.sin(T * 9) ** 2 + 0.14)),
    "acena": lambda p, T, s: (p.aR.__setitem__(2, 0.35 * math.sin(T * 10)), p.jb.__setitem__(0, -0.22 * math.sin(T * 10))),
    "nervoso": lambda p, T, s: (p.h.__setitem__(1, 0.28 * math.sin(T * 9)), p.aR.__setitem__(0, 0.06 * math.sin(T * 21)),
                                p.aL.__setitem__(0, -0.06 * math.sin(T * 21))),
    "medo": lambda p, T, s: p.h.__setitem__(1, 0.05 * math.sin(T * 30)),
    "grita": lambda p, T, s: p.h.__setitem__(0, 0.03 * math.sin(T * 28)),
    "susto": lambda p, T, s: (p.aR.__setitem__(2, 0.05 * math.sin(T * 26)), p.aL.__setitem__(2, -0.05 * math.sin(T * 26 + 1))),
    "bravo": lambda p, T, s: p.lR.__setitem__(0, -0.45 * math.sin(T * 11) ** 2),
    "procura": lambda p, T, s: (p.h.__setitem__(1, 0.6 * math.sin(T * 1.6)), p.sp.__setitem__(1, 0.25 * math.sin(T * 1.6))),
    "sorrateiro": lambda p, T, s: p.h.__setitem__(1, 0.45 * math.sin(T * 2.2)),
    "apaixonado": lambda p, T, s: (p.h.__setitem__(2, 0.2 * math.sin(T * 3)), p.sp.__setitem__(2, 0.08 * math.sin(T * 3))),
    "shake": lambda p, T, s: p.h.__setitem__(1, 0.38 * math.sin(T * 10)),
    "nod": lambda p, T, s: p.h.__setitem__(0, 0.28 * math.sin(T * 6.5) ** 2),
    "mine": lambda p, T, s: (p.aR.__setitem__(0, -0.9 * math.sin(T * 12) ** 2 + 0.45), p.sp.__setitem__(1, 0.12 * math.sin(T * 12))),
}
# poses que não ganham a "viveza" (já se mexem) nem o gesto de fala por cima
_MOVE = {"comemora", "rindo", "palmas", "acena", "nervoso", "medo", "procura", "shake", "nod", "mine", "sit"}
_GOLPE = {"grita", "medo", "susto"}


# --------------------------------------------------------------------------------------------------------------------------- dinâmica
def springs(x: np.ndarray, dt: float, params: np.ndarray, boost: Optional[np.ndarray] = None) -> np.ndarray:
    """Dinâmica de 2ª ordem (t3ssel8r) por coluna: y'' tal que y + k1 y' + k2 y'' = x + k3 x'.
    params[:,0]=f (Hz), [:,1]=ζ, [:,2]=r.  boost (n,) multiplica f (troca de pose rápida, golpe)."""
    n, m = x.shape
    f, z, r = params[:, 0], params[:, 1], params[:, 2]
    y = x[0].copy(); yd = np.zeros(m); xp = x[0].copy()
    out = np.empty_like(x)
    for i in range(n):
        fi = f * (boost[i] if boost is not None else 1.0)
        k1 = z / (np.pi * fi); k2 = 1.0 / ((2 * np.pi * fi) ** 2); k3 = r * z / (2 * np.pi * fi)
        xd = (x[i] - xp) / dt; xp = x[i]
        k2s = np.maximum(k2, np.maximum(dt * dt / 2 + dt * k1 / 2, dt * k1))     # estável em qualquer f
        y = y + dt * yd
        yd = yd + dt * (x[i] + k3 * xd - y - k1 * yd) / k2s
        out[i] = y
    return out


def _pos(x: float, e: float = 0.12) -> float:
    """max(0, x) sem quina (a quina dava tranco no joelho a cada passo)."""
    return 0.5 * (x + math.sqrt(x * x + e * e)) - 0.5 * e


def _abs(x: float, e: float = 0.12) -> float:
    return math.sqrt(x * x + e * e) - e


def _prof(u: float, antic: float) -> float:
    """Transição 0→1 com antecipação: recua `antic` no começo (sin², velocidade zero nas pontas) e chega com smoothstep."""
    if u <= 0:
        return 0.0
    if u >= 1:
        return 1.0
    a = -antic * math.sin(math.pi * min(u / 0.35, 1.0)) ** 2 if u < 0.35 else 0.0
    v = min(max((u - 0.12) / 0.88, 0.0), 1.0)
    return a + v * v * (3 - 2 * v)


def _sm(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


# ------------------------------------------------------------------------------------------------------------------------------- voz
def voice_from_wav(path: str, t_offset: float = 0.0, fps: int = 100) -> Dict[str, np.ndarray]:
    """Envelope da fala (port do _vozProc do Shorts web): e (rápido), es (lento), acc (acento) a `fps` Hz, tempo 0 = t_offset."""
    import wave
    with wave.open(path, "rb") as w:
        sr, nch, sw = w.getframerate(), w.getnchannels(), w.getsampwidth()
        raw = w.readframes(w.getnframes())
    dt = {1: np.uint8, 2: np.int16, 4: np.int32}[sw]
    a = np.frombuffer(raw, dt).astype(np.float32)
    if sw == 1:
        a = a - 128
    a = a.reshape(-1, nch).mean(1) / float(np.iinfo(dt).max if sw > 1 else 128)
    hop = max(1, sr // fps)
    n = len(a) // hop
    rms = np.sqrt((a[:n * hop].reshape(n, hop) ** 2).mean(1))
    nz = np.sort(rms[rms > 1e-4])
    ref = max(1e-3, nz[int(len(nz) * 0.95)]) if len(nz) else 1.0
    return _voz_proc(rms, ref, fps, t_offset)


def voice_from_text(text: str, dur: float, t_offset: float = 0.0, fps: int = 50) -> Dict[str, np.ndarray]:
    """Sem gravação: envelope de sílabas pelo texto (port do _vozSint): tônica forte, número/maiúscula com acento, vírgula pausa."""
    import re
    n = int(math.ceil(dur * fps)) + 2
    raw = np.zeros(n); on = []
    pal = [w for w in str(text or "").split() if w]
    sil = lambda w: max(1, len(re.findall(r"[aeiouáéíóúâêôãõàyü]+", w.lower())))
    tot = sum(sil(w) for w in pal) or 1
    pausas = sum(1 for w in pal if re.search(r"[,;:]$", w))
    fala = float(np.clip(len(text or "") / 14.0, 0.3, max(0.3, dur - 0.12)))
    sd = max(0.06, (fala - pausas * 0.14) / tot)
    t0 = 0.06
    for wi, w in enumerate(pal):
        ns = sil(w)
        forte = bool(re.search(r"\d", w)) or (len(w) > 2 and w == w.upper() and re.search(r"[A-ZÀ-Ú]", w) is not None)
        ton = ns - 2 if ns >= 2 else 0
        for j in range(ns):
            st = (j == ton and (len(w) >= 4 or forte)) or (wi == 0 and j == 0)
            amp = 1.0 if st else 0.62
            for i in range(int(t0 * fps), min(n, int(math.ceil((t0 + sd) * fps)) + 1)):
                q = (i / fps - t0) / sd
                if 0 <= q <= 1:
                    raw[i] = max(raw[i], amp * math.sin(math.pi * q))
            if st and (not on or t0 - on[-1] > 0.2):
                on.append(t0 + sd * 0.15)
            t0 += sd
        if re.search(r"[,;:]$", w):
            t0 += 0.14
    V = _voz_proc(raw, 1.0, fps, t_offset)
    acc = np.zeros(n); p = 0.0; oi = 0; dec = math.exp(-7 / fps)
    for i in range(n):
        p *= dec
        while oi < len(on) and on[oi] <= i / fps:
            p = 1.0; oi += 1
        acc[i] = p
    V["acc"] = _attack(acc, fps)
    V["on"] = np.array(on) + t_offset
    return V


def _voz_proc(raw: np.ndarray, ref: float, fps: int, t_offset: float) -> Dict[str, np.ndarray]:
    n = len(raw)
    e, es, acc = np.zeros(n), np.zeros(n), np.zeros(n)
    k = lambda s: 1 - math.exp(-1 / (fps * s))
    atk, rel, atkS, relS, dec = k(0.025), k(0.09), k(0.15), k(0.45), math.exp(-7 / fps)
    a = b = p = 0.0; last = -1e9; on = []
    for i in range(n):
        v = min(1.0, raw[i] / ref); a0 = a
        a += (v - a) * (atk if v > a else rel); e[i] = a
        b += (v - b) * (atkS if v > b else relS); es[i] = b
        p *= dec
        if a - a0 > 0.6 / fps * 2.5 and a > 0.4 and i - last > fps * 0.2:
            p = max(p, min(1.0, a * 1.1)); last = i; on.append(i / fps)
        acc[i] = p
    return {"t": np.arange(n) / fps + t_offset, "e": e, "es": es, "acc": _attack(acc, fps), "on": np.array(on) + t_offset}


def _attack(x: np.ndarray, fps: float, tau: float = 0.04) -> np.ndarray:
    """Sobe com constante tau (sem degrau: o acento da fala dava tranco de 1 quadro) e desce como veio."""
    out = np.zeros_like(x); y = 0.0; k = 1 - math.exp(-1 / (fps * tau))
    for i, v in enumerate(x):
        y = y + (v - y) * k if v > y else v
        out[i] = y
    return out


# ------------------------------------------------------------------------------------------------------------------------------- ator
@dataclass
class _Ev:
    t: float
    kind: str
    data: dict = field(default_factory=dict)


class Ator:
    """Um personagem dirigido por intenção (pose, fala, andar, olhar, pular) → `build()` devolve um Actor assado."""

    def __init__(self, name: str, skin: str, pos: Sequence[float], yaw: float = 0.0, slim: bool = False, item: Optional[str] = None,
                 hat: bool = False, face="auto", seed: Optional[int] = None, left: bool = False, energy: float = 1.0):
        self.name, self.skin, self.slim, self.item, self.hat, self.face = name, skin, slim, item, hat, face
        self.p0 = np.array(pos, float); self.yaw0 = float(yaw)
        self.seed = (zlib.crc32(name.encode()) % 997) / 997.0 * 6.28 if seed is None else seed
        self.left, self.energy = left, energy
        self.ground_y: Optional[float] = None          # y do chão para a sombra (padrão: o y dos pés)
        self.poses: List[_Ev] = [_Ev(0.0, "idle")]
        self.talks: List[Tuple[float, float, Dict]] = []
        self.walks: List[Tuple[float, float, np.ndarray, str]] = []
        self.turns: List[Tuple[float, float, float]] = []
        self.looks: List[Tuple[float, Optional[np.ndarray], float]] = []
        self.jumps: List[Tuple[float, float, float]] = []
        self.items: List[Tuple[float, float]] = []
        self.extra: List[Tuple[float, Dict[str, float], str]] = []

    # --- direção ---
    def pose(self, t: float, kind: str, left: Optional[bool] = None, snap: float = 1.0):
        """Troca de pose em t (STATIC/OSC).  left=True usa o braço esquerdo.  snap>1 = troca mais rápida (golpe)."""
        if kind not in STATIC and kind not in OSC:
            raise KeyError(f"pose {kind!r}; tem: {sorted(set(STATIC) | set(OSC))}")
        self.poses.append(_Ev(float(t), kind, {"left": self.left if left is None else left, "snap": snap}))
        self.poses.sort(key=lambda e: e.t)
        return self

    def point_at(self, t: float, target: Sequence[float], left: Optional[bool] = None, elbow: float = -0.08):
        """Aponta para um ponto do mundo (x, y, z) com o braço esticado (resolve ombro→alvo no corpo do personagem)."""
        self.poses.append(_Ev(float(t), "point", {"left": self.left if left is None else left, "snap": 1.0,
                                                  "target": np.array(target, float), "elbow": elbow}))
        self.poses.sort(key=lambda e: e.t)
        return self

    def _arm_to(self, t: float, target: np.ndarray, left: bool) -> np.ndarray:
        """Ângulos (convenção web: x, y, z rad) do braço apontando do ombro para target."""
        yaw = self.yaw0
        for (tt, y, d) in self.turns:
            if tt <= t:
                yaw = y
        ps = math.radians(yaw)
        fwd = np.array([-math.sin(ps), 0, math.cos(ps)]); right = np.array([-math.cos(ps), 0, -math.sin(ps)]); up = np.array([0, 1.0, 0])
        sh = self.pos_at(t) + up * 1.375 + right * (5 / 16) * (-1 if left else 1)
        d = target - sh
        d = d / (np.linalg.norm(d) + 1e-9)
        dm = np.array([-d @ right, -d @ up, -d @ fwd])          # espaço do modelo: direita = -x, baixo = +y, frente = -z
        # convenção web (ordem XYZ do three.js): braço caído u=(0,1,0) → Rx(x)·Rz(-z)·u = (sin z, cos z·cos x, cos z·sin x)
        return np.array([math.atan2(dm[2], dm[1]), 0.0, math.asin(float(np.clip(dm[0], -1, 1)))])

    def talk(self, t0: float, t1: float, text: str = "", wav: Optional[str] = None, wav_offset: float = 0.0, calm: bool = False):
        """Fala entre t0 e t1: gesto e cabeça pelo volume da voz e boca abrindo.  wav = trecho gravado (wav_offset = onde a fala
        começa dentro do arquivo); sem wav, envelope sintético do texto."""
        V = voice_from_wav(wav, t_offset=t0 - wav_offset) if wav else voice_from_text(text, t1 - t0, t_offset=t0)
        self.talks.append((float(t0), float(t1), {"V": V, "calm": calm}))
        return self

    def walk(self, t0: float, t1: float, to: Sequence[float], gait: str = "auto"):
        """Anda/corre do ponto onde está até `to` (x,z) entre t0 e t1; gait walk|run|runFast|auto (pela velocidade)."""
        self.walks.append((float(t0), float(t1), np.array(to, float), gait))
        self.walks.sort(key=lambda w: w[0])
        return self

    def turn(self, t: float, yaw: float, dur: float = 0.45):
        self.turns.append((float(t), float(yaw), dur))
        return self

    def face_to(self, t: float, target: Sequence[float], dur: float = 0.45):
        """Vira o corpo para um ponto (x, z) ou (x, y, z)."""
        tg = np.array(target, float)
        tx, tz = (tg[0], tg[1]) if len(tg) == 2 else (tg[0], tg[2])
        x, z = self.pos_at(t)[[0, 2]]
        return self.turn(t, math.degrees(math.atan2(-(tx - x), tz - z)), dur)

    def look(self, t: float, target: Optional[Sequence[float]], weight: float = 1.0):
        """A cabeça olha para um ponto (None = volta para a frente)."""
        self.looks.append((float(t), None if target is None else np.array(target, float), weight))
        self.looks.sort(key=lambda l: l[0])
        return self

    def jump(self, t: float, h: float = 0.9, air: float = 0.42):
        """Pulo com antecipação (agacha antes), corpo esticado subindo, pernas encolhidas no ar e amortecimento na queda."""
        self.jumps.append((float(t), float(h), float(air)))
        return self

    def hold_item(self, t0: float, t1: float = 1e9):
        self.items.append((float(t0), float(t1)))
        return self

    def key(self, t: float, ease: str = "smooth", **vals):
        """Canal cru do mod por cima de tudo (ex.: belly, vbelly...)."""
        self.extra.append((float(t), vals, ease))
        return self

    # --- caminho / yaw ---
    def pos_at(self, t: float) -> np.ndarray:
        p = self.p0.copy()
        for (t0, t1, to, g) in self.walks:
            if t <= t0:
                break
            a = p.copy()
            b = np.array([to[0], p[1], to[1]])
            u = 1.0 if t >= t1 else float(_walk_u((t - t0) / (t1 - t0)))
            p = a + (b - a) * u
        return p

    # --- assar ---
    def build(self, T: Optional[float] = None) -> Actor:
        self.__dict__.pop("_dist", None)
        T = T or max([e.t for e in self.poses] + [t1 for _, t1, _ in self.talks] + [w[1] for w in self.walks]
                     + [j[0] + j[2] + 0.6 for j in self.jumps] + [l[0] for l in self.looks] + [3.0]) + 0.5
        n = int(math.ceil(T * HZ)) + 1
        tg = np.arange(n) / HZ
        dt = 1.0 / HZ
        base = np.zeros((n, NV)); osc = np.zeros((n, NV)); boost = np.ones(n)
        s = self.seed

        # 1) pose atual: curva suave da pose velha para a nova (antecipação desenhada, sem degrau) → mola; oscilação em crossfade
        evs = self.poses
        tgt = []
        for ev in evs:
            p = P(); STATIC.get(ev.kind, STATIC["idle"])(p)
            if ev.data.get("left"):
                p = mirror(p)
            if "target" in ev.data:
                arm = self._arm_to(ev.t, ev.data["target"], bool(ev.data.get("left")))
                if ev.data.get("left"):
                    p.aL[:] = arm; p.jb[1] = ev.data["elbow"]
                else:
                    p.aR[:] = arm; p.jb[0] = ev.data["elbow"]
            tgt.append(p.vec())
        seg_k, A = 0, tgt[0].copy()
        for i, t in enumerate(tg):
            k = seg_k
            while k + 1 < len(evs) and evs[k + 1].t <= t:
                k += 1
            if k != seg_k:
                A = base[i - 1].copy() if i > 0 else tgt[k].copy()          # parte de onde a curva estava (troca no meio de outra)
                seg_k = k
            ev = evs[k]
            age = t - ev.t
            fast = ev.kind in _GOLPE or ev.data.get("snap", 1) > 1
            base[i] = A + (tgt[k] - A) * (_prof(age / (0.18 if fast else 0.38), 0.0 if fast else 0.12) if k > 0 else 1.0)
            if ev.kind in _GOLPE or ev.data.get("snap", 1) > 1:
                boost[i] = 1.0 + (max(2.2, ev.data.get("snap", 1)) - 1.0) * float(np.exp(-age / 0.25))
            w_in = float(_sm(age / 0.2)) if k > 0 else 1.0
            if ev.kind in OSC:
                q = P(); OSC[ev.kind](q, t, s)
                if ev.data.get("left"):
                    q = mirror(q)
                osc[i] += w_in * q.vec()
            if k > 0 and evs[k - 1].kind in OSC and w_in < 1:
                q = P(); OSC[evs[k - 1].kind](q, t, s)
                if evs[k - 1].data.get("left"):
                    q = mirror(q)
                osc[i] += (1 - w_in) * q.vec()

        # 2) olhar (base: cabeça relativa ao corpo, com mola)
        yaw = self._yaw_track(tg)
        pos = np.array([self.pos_at(t) for t in tg])
        prev_rel = 0.0
        look_add = np.zeros_like(base)
        for i, t in enumerate(tg):
            L = None
            for (lt, tgt, wgt) in self.looks:
                if lt <= t:
                    L = (tgt, wgt)
            if L and L[0] is not None:
                hp = pos[i] + [0, 1.62, 0]
                d = L[0] - hp
                tyaw = math.degrees(math.atan2(-d[0], d[2]))
                rel = (tyaw - yaw[i] + 180) % 360 - 180
                rel = prev_rel + ((rel - prev_rel + 180) % 360 - 180)        # contínuo: alvo atrás não vira de +180 para -180
                prev_rel = rel
                pit = -math.atan2(d[1], math.hypot(d[0], d[2]))
                look_add[i, 1] += L[1] * np.clip(math.radians(rel), -1.25, 1.25) * -1.0
                look_add[i, 0] += L[1] * np.clip(pit, -0.8, 0.8)
                look_add[i, 16] += L[1] * np.clip(math.radians(rel), -1.25, 1.25) * -0.25      # o tronco acompanha um pouco
        # troca de olhar vira rampa (~0,25 s) em vez de degrau
        win = int(0.12 * HZ)
        for _ in range(2):
            pad = np.concatenate([np.repeat(look_add[:1], win, 0), look_add, np.repeat(look_add[-1:], win, 0)])
            cs = np.cumsum(pad, 0)
            look_add = (cs[2 * win:] - cs[:-2 * win])[:len(tg)] / (2 * win)
        base += look_add

        # 2b) pulo e gesto da fala também entram ANTES da mola (o acento da sílaba virava tranco de 1 quadro);
        #     a fala é lida 50 ms adiantada para compensar o atraso da mola
        for i, t in enumerate(tg):
            q = P()
            if self.jumps:
                self._jump_layer(q, t, pose=True)
            if self.talks:
                ev = self._ev_at(t + 0.05)
                self._talk_layer(q, t + 0.05, ev.kind if ev else "idle", bool(ev and ev.data.get("left")))
            base[i] += q.vec()

        # 3) molas
        out = springs(base, dt, SPRING, boost) + osc

        # 4) viveza parado + fala + andar + pulo (camadas aditivas)
        walk_w = self._walk_weight(tg)
        for i, t in enumerate(tg):
            p = P.from_vec(out[i].copy())
            ev = self._ev_at(t)
            moving = walk_w[i]
            # viveza (parado): respira, troca o peso, cotovelo solto; poses seguradas não congelam
            still = 1.0 - moving
            if still > 0:
                br, w = math.sin(t * 1.9 + s), math.sin(t * 0.55 + s)
                rel = 0.5 + 0.5 * w
                p.sp += still * np.array([0.02 * br, 0.04 * math.sin(t * 1.1 + s * 1.7), 0.03 * w])
                p.dy += still * -0.006 * (1 + br)
                p.jb[2] += still * 0.07 * rel; p.jb[3] += still * 0.07 * (1 - rel)
                p.lR[0] -= still * 0.03 * rel; p.lL[0] -= still * 0.03 * (1 - rel)
                p.lR[2] += still * 0.02 * w; p.lL[2] += still * 0.02 * w
                p.jb[0] -= still * (0.05 + 0.02 * br); p.jb[1] -= still * (0.05 + 0.02 * br)
                ag = t * 20 + s * 40
                bx, bz = math.sin(ag * 0.067) * 0.05, math.cos(ag * 0.09) * 0.05 + 0.05
                p.aR += still * np.array([bx, 0, bz]); p.aL += still * np.array([-bx, 0, -bz])
                sd = s * 5.3
                p.h += still * np.array([0.035 * math.sin(t * 2.1 + sd), 0.08 * math.sin(t * 1.5 + sd * 2) + 0.03 * math.sin(t * 3.1 + sd), 0])
            # andar/correr
            if moving > 0:
                self._walk_layer(p, t, i, tg, pos, moving)
            # pulo (só a altura: a pose já passou pela mola)
            self._jump_layer(p, t, pose=False)
            out[i] = p.vec()

        # 5) agachar → perna/joelho/tronco; pé no chão; cabeça compensa o tronco
        ch = self._to_channels(out, tg, pos, yaw)
        a = _Baked(self.name, self.skin, self.p0, self.yaw0, self.slim, self.item, self.hat, self.face)
        a.set_grid(tg, ch)
        for (t, vals, ease) in self.extra:
            a.key(t, ease=ease, **vals)
        return a

    # --- camadas ---
    def _ev_at(self, t: float) -> Optional[_Ev]:
        e = None
        for ev in self.poses:
            if ev.t <= t:
                e = ev
        return e

    def _talk_layer(self, p: P, t: float, kind: str, left: bool):
        for (t0, t1, d) in self.talks:
            if not (t0 - 0.05 <= t <= t1 + 0.4):
                continue
            V = d["V"]
            j = int(np.clip(np.searchsorted(V["t"], t), 0, len(V["t"]) - 1))
            e, es, acc = float(V["e"][j]), float(V["es"][j]), float(V["acc"][j])
            fade = float(_sm((t1 + 0.4 - t) / 0.4))
            e, es, acc = e * fade, es * fade, acc * fade
            # braço que puxa o gesto troca a cada 2 acentos
            on = V["on"]; nacc = int(np.sum((on >= t0) & (on <= t)))
            lado = (nacc // 2) % 2
            Lw = float(lado); Rw = 1 - Lw
            cm = 0.4 if d["calm"] or kind == "calm" else 1.0
            cm *= self.energy
            s = self.seed
            p.h += np.array([0.13 * acc * cm - 0.05 * es + 0.04 * math.sin(t * 9.3 + s) * e,
                             math.sin(t * 0.9 + s * 2) * 0.16 * es * cm, math.sin(t * 1.7 + s) * 0.07 * es * cm])
            if kind in ("idle", "talk", "calm"):
                g = lambda w: (0.12 + 0.6 * es + 0.45 * acc) * w * cm
                p.aR += [-0.1 - g(Rw) - 0.1 * es * Lw * cm, -0.3 * es * Rw * cm, -0.16 * es * Rw * cm]
                p.aL += [-0.1 - g(Lw) - 0.1 * es * Rw * cm, 0.3 * es * Lw * cm, 0.16 * es * Lw * cm]
                sobeR = float(np.clip(-p.aR[0] / 0.9, 0, 1)); sobeL = float(np.clip(-p.aL[0] / 0.9, 0, 1))
                p.jb[0] -= 1.05 * sobeR; p.aR[1] += 0.4 * sobeR; p.aR[2] -= 0.12 * sobeR
                p.jb[1] -= 1.05 * sobeL; p.aL[1] -= 0.4 * sobeL; p.aL[2] += 0.12 * sobeL
                p.sp += [0.12 * acc + 0.04 * es, 0.2 * es * (1 - 2 * Lw), 0.05 * es * math.sin(t * 1.7 + s)]
            elif kind not in _GOLPE and kind not in _MOVE:
                p.h += [0.1 * acc, math.sin(t * 3.7 + s) * 0.11 * e, 0]
                if kind in ("point", "stop", "finger"):
                    (p.aL if left else p.aR)[0] -= 0.22 * acc
                elif kind in ("cross", "sus", "smug"):
                    p.aR[0] += 0.08 * acc; p.aL[0] += 0.08 * acc
                elif kind in ("ombros", "bravo"):
                    p.aR[2] -= 0.12 * acc; p.aL[2] += 0.12 * acc
                p.sp[0] += 0.08 * acc

    def _mouth(self, tg: np.ndarray) -> np.ndarray:
        m = np.zeros(len(tg))
        for (t0, t1, d) in self.talks:
            V = d["V"]
            sel = (tg >= t0) & (tg <= t1 + 0.1)
            e = np.interp(tg[sel], V["t"], V["e"], left=0, right=0)
            m[sel] = np.maximum(m[sel], e)
        # boca de Minecraft: aberta/fechada (com histerese e no mínimo 2 quadros a 30 fps)
        out = np.zeros(len(tg)); state = 0; hold = 0
        for i, v in enumerate(m):
            hold -= 1
            if hold <= 0:
                ns = 1 if (v > 0.42 if state == 0 else v > 0.24) else 0
                if ns != state:
                    state, hold = ns, int(0.066 * HZ)
            out[i] = state
        return out

    def _blink(self, tg: np.ndarray) -> np.ndarray:
        rng = np.random.default_rng(zlib.crc32(("blink:" + self.name).encode()))
        times = []
        t = float(rng.uniform(0.4, 1.6))
        while t < tg[-1]:
            times.append(t); t += float(rng.uniform(2.2, 4.6))
        for ev in self.poses[1:]:                                   # piscar na troca de pose (o olho "recarrega")
            if rng.random() < 0.55:
                times.append(ev.t + 0.03)
        b = np.zeros(len(tg))
        for t0 in times:
            u = (tg - t0)
            b = np.maximum(b, np.where((u >= 0) & (u < 0.05), u / 0.05, 0))
            b = np.maximum(b, np.where((u >= 0.05) & (u < 0.09), 1.0, 0))
            b = np.maximum(b, np.where((u >= 0.09) & (u < 0.17), 1 - (u - 0.09) / 0.08, 0))
        return b

    def _yaw_track(self, tg: np.ndarray) -> np.ndarray:
        """Yaw do corpo: virar (turn), olhar a direção da caminhada; com mola (o giro leva 0,35–0,6 s e assenta)."""
        tgt = np.full(len(tg), self.yaw0)
        cur = self.yaw0
        evs = sorted([(t, "turn", y) for (t, y, d) in self.turns] + [(w[0], "walk", w) for w in self.walks], key=lambda e: e[0])
        for (t, kind, v) in evs:
            if kind == "turn":
                cur = v
                tgt[tg >= t] = cur
            else:
                t0, t1, to, g = v
                a = self.pos_at(t0)
                dx, dz = to[0] - a[0], to[1] - a[2]
                if math.hypot(dx, dz) > 0.3:
                    wy = math.degrees(math.atan2(-dx, dz))
                    sel = (tg >= t0 - 0.15) & (tg < t1)
                    tgt[sel] = wy
                    tgt[tg >= t1] = cur                         # volta a olhar para onde estava (para a câmera)
        un = np.degrees(np.unwrap(np.radians(tgt)))
        return springs(un[:, None], 1.0 / HZ, np.array([[2.0, 0.85, 0.0]]))[:, 0]

    def _walk_weight(self, tg: np.ndarray) -> np.ndarray:
        w = np.zeros(len(tg))
        for (t0, t1, to, g) in self.walks:
            w = np.maximum(w, _sm((tg - t0 + 0.12) / 0.2) * _sm((t1 + 0.18 - tg) / 0.22))
        return w

    def _walk_layer(self, p: P, t: float, i: int, tg, pos, weight: float):
        # fase pela distância andada (passada do jogo: andar 2,36 blocos por ciclo; correr 2,65)
        if i == 0:
            return
        if not hasattr(self, "_dist"):
            seg = np.linalg.norm(np.diff(pos[:, [0, 2]], axis=0), axis=1)
            self._dist = np.concatenate([[0], np.cumsum(seg)])
            self._spd = np.concatenate([[0], seg * HZ])
            self._spd = np.convolve(self._spd, np.ones(9) / 9, mode="same")
        v = float(self._spd[i])
        if v < 0.05:
            return
        g = "walk" if v < 4.9 else ("run" if v < 7 else "runFast")
        for (t0, t1, to, gg) in self.walks:
            if t0 - 0.2 <= t <= t1 + 0.3 and gg != "auto":
                g = gg
        corre = g != "walk"
        cyc = 2.36 if not corre else 3.2          # corrida de desenho: passada mais longa, perna menos frenética
        ph = self._dist[i] / cyc * 2 * math.pi + self.seed
        s, sn = math.cos(ph), math.sin(ph)
        lim = min(1.0, v / (4.3 if not corre else 5.6)) * weight
        inc = 0.42 if g == "runFast" else 0.28 if corre else 0.06
        if not corre:
            p.lR[0] += 0.5 * s * lim; p.lL[0] -= 0.5 * s * lim
            p.aR[0] += (-0.05 - 0.55 * s) * lim; p.aL[0] += (-0.05 + 0.55 * s) * lim
            p.aR[2] -= 0.06 * lim; p.aL[2] += 0.06 * lim                   # braços soltos um pouco para fora
            p.jb[0] += (-0.32 - 0.2 * _pos(s)) * lim; p.jb[1] += (-0.32 - 0.2 * _pos(-s)) * lim
        else:
            p.lR[0] += (-0.28 + 0.9 * s) * lim; p.lL[0] += (-0.28 - 0.9 * s) * lim
            k = 1.1 if g == "runFast" else 0.95
            p.aR += np.array([-0.15 - k * s, 0, 0.12]) * lim; p.aL += np.array([-0.15 + k * s, 0, -0.12]) * lim
            p.jb[0] += (-1.5 + 0.25 * s) * lim; p.jb[1] += (-1.5 - 0.25 * s) * lim
            p.hop += 0.05 * sn * sn * lim
        # joelho: curva lisa (sem quina) que dobra quando a perna passa por baixo vindo para a frente
        p.jb[2] += ((1.35 if corre else 0.55) * ((1 + sn) / 2) ** 2 + 0.04) * lim
        p.jb[3] += ((1.35 if corre else 0.55) * ((1 - sn) / 2) ** 2 + 0.04) * lim
        # quadril/ombro: torção contra a perna que avança, balanço de lado sobre a perna de apoio, quique na passada
        p.sp += np.array([inc, (0.16 if corre else 0.1) * s, (0.03 if corre else 0.05) * s]) * lim
        p.h[0] -= inc * 0.85 * lim
        p.h[2] -= (0.02 if corre else 0.035) * s * lim
        p.dy += -(0.035 if corre else 0.025) * sn * sn * lim

    def _jump_layer(self, p: P, t: float, pose: bool = True):
        """pose=True: agachar/braços/pernas/estica (vai antes da mola); pose=False: só a altura (parábola real)."""
        for (tj, h, air) in self.jumps:
            u = t - tj
            if not pose:
                if 0 <= u < air:
                    x = u / air
                    p.hop += 4 * h * x * (1 - x)
                continue
            pre = float(_sm((u + 0.22) / 0.22)) * (1 - float(_sm(u / 0.06)))          # antecipação: agacha e recolhe os braços
            fly = float(_sm(u / 0.06)) * (1 - float(_sm((u - air + 0.08) / 0.1)))     # no ar
            x = min(max(u / air, 0.0), 1.0)
            land = float(_sm((u - air + 0.02) / 0.06)) * math.exp(-max(0.0, u - air - 0.04) / 0.14)   # amortece na queda
            p.crouch += 0.75 * pre + 0.65 * land
            p.aR[0] += 0.5 * pre + fly * (-1.56 * (1 - x) - 0.4); p.aL[0] += 0.5 * pre + fly * (-1.56 * (1 - x) - 0.4)
            p.aR[2] -= 0.25 * fly; p.aL[2] += 0.25 * fly
            p.sp[0] += 0.15 * pre + 0.18 * land
            p.sq += -0.06 * pre + fly * (0.08 * math.exp(-max(u, 0) / 0.1) - 0.03) - 0.08 * land
            tuck = fly * (1 - math.exp(-max(u, 0) / 0.08))
            p.lR[0] -= 0.35 * tuck; p.lL[0] -= 0.15 * tuck; p.jb[2] += 0.75 * tuck; p.jb[3] += 0.45 * tuck
            p.h[0] -= 0.15 * fly

    def _to_channels(self, out: np.ndarray, tg, pos, yaw) -> np.ndarray:
        n = len(tg)
        ch = np.zeros((n, PN))
        ch[:, POSE["sx"]] = ch[:, POSE["sy"]] = ch[:, POSE["sz"]] = 1
        for nm in ("belly", "belly_y", "head", "rarm_len", "larm_len", "rleg_len", "lleg_len"):
            ch[:, POSE[nm]] = 1
        ch[:, POSE["vbelly_y"]], ch[:, POSE["vbelly_out"]], ch[:, POSE["vbelly_vox"]] = 7, 3, 1
        mouth, blink = self._mouth(tg), self._blink(tg)
        items = np.zeros(n)
        for (a, b) in self.items:
            items = np.maximum(items, _sm((tg - a) / 0.12) * _sm((b - tg) / 0.12))
        if self.item and not self.items:
            items[:] = 1
        for i in range(n):
            p = P.from_vec(out[i])
            # agachar: coxa para a frente, joelho dobra o dobro, tronco inclina
            q = 0.45 * p.crouch
            p.lR[0] -= q; p.lL[0] -= q; p.jb[2] += 2 * q; p.jb[3] += 2 * q; p.sp[0] += q * 0.7
            p.jb[2] = max(p.jb[2], 0.0); p.jb[3] = max(p.jb[3], 0.0)          # joelho não dobra para a frente
            p.jb[0] = min(p.jb[0], 0.15); p.jb[1] = min(p.jb[1], 0.15)
            p.aR[0] = min(max(p.aR[0], -3.1), 1.3); p.aL[0] = min(max(p.aL[0], -3.1), 1.3)   # camadas somadas não passam do limite do ombro
            # pé no chão: o corpo desce até o pé mais baixo encostar (perna 0,75 = coxa+canela em blocos)
            ext = lambda th, kn: 0.375 * (math.cos(th) + math.cos(th + kn))
            ea, eb = ext(p.lR[0], p.jb[2]), ext(p.lL[0], p.jb[3])
            ground = 0.5 * (ea + eb + math.sqrt((ea - eb) ** 2 + 0.0004)) - 0.75     # max suave (troca de perna sem degrau)
            # cabeça compensa o tronco (continua olhando para quem está na frente)
            h = p.h - np.array([p.sp[0] * 0.55, p.sp[1] * 0.5, p.sp[2] * 0.6])
            r = ch[i]
            r[POSE["x"]], r[POSE["y"]], r[POSE["z"]] = pos[i]
            r[POSE["yaw"]] = yaw[i]
            r[POSE["head_x"]], r[POSE["head_y"]], r[POSE["head_z"]] = web_to_mc(h)
            r[POSE["rarm_x"]], r[POSE["rarm_y"]], r[POSE["rarm_z"]] = web_to_mc(p.aR)
            r[POSE["larm_x"]], r[POSE["larm_y"]], r[POSE["larm_z"]] = web_to_mc(p.aL)
            r[POSE["rleg_x"]], r[POSE["rleg_y"]], r[POSE["rleg_z"]] = web_to_mc(p.lR)
            r[POSE["lleg_x"]], r[POSE["lleg_y"]], r[POSE["lleg_z"]] = web_to_mc(p.lL)
            r[POSE["rarm_bend"]], r[POSE["larm_bend"]] = p.jb[0] * D, p.jb[1] * D
            r[POSE["rleg_bend"]], r[POSE["lleg_bend"]] = p.jb[2] * D, p.jb[3] * D
            r[POSE["torso_x"]], r[POSE["torso_y"]], r[POSE["torso_z"]] = p.sp[0] * D, -p.sp[1] * D, -p.sp[2] * D
            r[POSE["hop"]] = p.hop + ground + p.dy
            r[POSE["sy"]] = 1 + p.sq; r[POSE["sx"]] = r[POSE["sz"]] = 1 - 0.5 * p.sq
            r[POSE["mouth"]] = mouth[i]; r[POSE["blink"]] = blink[i]
            r[POSE["shadow_y"]] = self.ground_y if self.ground_y is not None else self.p0[1]     # sombra de contato no chão
            r[POSE["item"]] = items[i]
        # ângulos contínuos no tempo: a decomposição em Euler pode pular ±360 (braço passando de 180°) → girava o braço inteiro
        for nm in ("head_x", "head_y", "head_z", "rarm_x", "rarm_y", "rarm_z", "larm_x", "larm_y", "larm_z",
                   "rleg_x", "rleg_y", "rleg_z", "lleg_x", "lleg_y", "lleg_z", "yaw"):
            c = POSE[nm]
            ch[:, c] = np.degrees(np.unwrap(np.radians(ch[:, c])))
        return ch


def web_to_mc(e) -> Tuple[float, float, float]:
    """Euler do Shorts web (three.js, ordem XYZ, y para cima/frente +z) → ModelPart do Minecraft (rotationZYX, y para baixo/frente -z),
    em graus.  Os referenciais diferem por 180° em X (y e z trocam de sinal); a ORDEM também difere — com o braço levantado,
    copiar o ângulo z direto inverte "abrir" e "fechar" (comemorar virava mãos cruzadas na cabeça)."""
    x, y, z = float(e[0]), -float(e[1]), -float(e[2])
    cx, sx, cy, sy, cz, sz = math.cos(x), math.sin(x), math.cos(y), math.sin(y), math.cos(z), math.sin(z)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]]); Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    R = Rx @ Ry @ Rz
    b = -math.asin(float(np.clip(R[2, 0], -1, 1)))
    a = math.atan2(R[2, 1], R[2, 2])
    c = math.atan2(R[1, 0], R[0, 0])
    return a * D, b * D, c * D


def _walk_u(x):
    """Posição ao longo da caminhada: arranca (aceleração ~0,25 s), velocidade constante, freia."""
    x = float(np.clip(x, 0, 1))
    a = 0.18
    if x < a:
        return 0.5 * x * x / a / (1 - a)
    if x > 1 - a:
        y = 1 - x
        return 1 - 0.5 * y * y / a / (1 - a)
    return (x - a / 2) / (1 - a)


class _Baked(Actor):
    """Actor com todos os canais já calculados numa grade (120 Hz); keys extras somam por cima."""

    def __init__(self, name, skin, pos, yaw, slim, item, hat, face):
        super().__init__(name, skin, pos, yaw=yaw, slim=slim, item=item, hat=hat, face=face)
        self.keys = {f: [] for f in self.FIELDS}

    def set_grid(self, tg: np.ndarray, ch: np.ndarray):
        self._tg, self._ch = tg, ch

    def at(self, times: np.ndarray) -> np.ndarray:
        times = np.asarray(times, float)
        out = np.empty((len(times), self.WIDTH))
        for c in range(self.WIDTH):
            out[:, c] = np.interp(times, self._tg, self._ch[:, c])
        if any(self.keys[f] for f in self.FIELDS):
            extra = Actor.at(self, times)
            for f, idx in self.FIELDS.items():
                if self.keys[f]:
                    out[:, idx] = extra[:, idx]
        return out


def snaps(actor: Actor, T: float, fps: int = 30, deg: float = 4.0, blocks: float = 0.03) -> List[Tuple[float, str, float]]:
    """Trancos de 1 quadro (25/10, "rollback"): a aceleração troca de sinal em quadros seguidos (zigue-zague: vai, volta, vai)
    com amplitude acima do limite (graus nos ângulos, blocos em x/y/z/hop).  Movimento rápido mas contínuo (corrida, aceno)
    não conta.  Lista vazia = movimento limpo; rode antes de renderizar."""
    t = np.arange(0, T, 1.0 / fps)
    a = actor.at(t)
    out = []
    ang = [n for n in POSE if n.endswith(("_x", "_y", "_z", "_bend")) and n not in ("x", "y", "z")] + ["yaw"]
    for n in ang + ["x", "y", "z", "hop"]:
        j = np.diff(a[:, POSE[n]], 2)
        lim = blocks if n in ("x", "y", "z", "hop") else deg
        zz = (j[:-1] * j[1:] < 0) & (np.abs(j[:-1]) > lim) & (np.abs(j[1:]) > lim)
        for i in np.nonzero(zz)[0]:
            out.append((round(float(t[i + 1]), 3), n, round(float(min(abs(j[i]), abs(j[i + 1]))), 2)))
    return sorted(out)
