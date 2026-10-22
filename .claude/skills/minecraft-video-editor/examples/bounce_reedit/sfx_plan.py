import json, os, sys, wave, tempfile, subprocess
import numpy as np, soundfile as sf
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
SKILL = os.path.expanduser("~/.claude/skills/minecraft-video-editor/scripts"); sys.path.insert(0, SKILL)
import events as E
import sfx_timing as TM
from sfx_levels import GAIN_DB, table_gain
LIB = os.path.normpath(os.path.join(SKILL, "..", "library", "sfx"))
IDX = json.load(open(os.path.join(LIB, "index.json"), encoding="utf8"))
COMP_DB = 0.0
G_MAT, G_PED = -1.7, -5.4      # ganhos nominais (dB) dos clipes de voz já compensados
joins = sorted(set(json.load(open(os.path.join(HERE, "joins3.json")))))
MAT, _ = sf.read("D:/Pobrs/bounce/tl7_mat.wav"); PED, _ = sf.read("D:/Pobrs/bounce/tl7_ped.wav")
VOICE = (MAT * 10 ** (G_MAT / 20) + PED * 10 ** (G_PED / 20)).astype(np.float32)   # mistura nominal (pico aproximado; sem música)
_pk = {}


def file_levels(path, dur, off=0.0):
    key = (path, round(dur, 2), round(off, 3))
    if key in _pk: return _pk[key]
    tmp = os.path.join(tempfile.gettempdir(), "sfxlv_bounce.wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(off), "-t", str(dur), "-i", path, "-vn", "-ac", "1", "-ar", "48000", tmp], check=True)
    d, _ = sf.read(tmp)
    pk = 20 * np.log10(np.abs(d).max() + 1e-9)
    hop = 960; n = max(len(d) // hop, 1)
    fr = np.array([np.sqrt((d[i * hop:(i + 1) * hop] ** 2).mean()) for i in range(n)])
    act = fr > fr.max() * 10 ** (-35 / 20)
    _pk[key] = (float(pk), float(20 * np.log10(np.sqrt((fr[act] ** 2).mean()) + 1e-9)))
    return _pk[key]


def voice_peak(t0, t1):
    a, b = int(max(t0, 0) * 16000), int(t1 * 16000)
    seg = VOICE[a:b]
    return float(20 * np.log10(np.abs(seg).max() + 1e-6)) if len(seg) else -60.0


# mediana dos picos da voz por segundo (só onde há fala)
_sp = [voice_peak(s, s + 1) for s in range(0, 610)]
_sp = [x for x in _sp if x > -40]
MEDP = float(np.median(_sp))

# referência relativa da tabela dele: R_f = pico_arquivo + ganho_tabela (mediana M)
_R = []
for fn in sorted(os.listdir(LIB)):
    if not fn.endswith((".mp3", ".wav")): continue
    g = table_gain(fn)
    if g is None or "xp-orb" in fn or "click" in fn: continue
    dur = min(IDX.get(fn, {}).get("dur", 1.0), 2.5)
    _R.append(file_levels(os.path.join(LIB, fn), dur)[0] + g)
M_REF = float(np.median(_R))


def _mp(path):
    rem = sorted((a, b) for a, b, *_ in json.load(open(os.path.join(HERE, path), encoding="utf8")))
    def f(t):
        acc = 0
        for a, b in rem:
            if t >= b: acc += b - a
            elif t > a: acc += t - a; break
            else: break
        return t - acc
    return f, (lambda t: any(a < t < b for a, b in rem))
_n1, _i1 = _mp("remove.json"); _n2, _ = _mp("remove2_ok.json"); _n3, _ = _mp("remove3_ok.json")
def new(t): return _n3(_n2(_n1(t)))
def inside(t): return _i1(t)


def plan(verbose=False):
    ev, bad, vplan = E.resolve()
    DROP = {("pop", 198.9), ("pop", 363.7), ("bonk", 587.8), ("click", 307.4), ("orb1", 446.6), ("splash", 44.0), ("boing", 76.2), ("nerr", 371.7), ("vine", 368.3), ("pling", 466.4), ("bonk", 57.5), ("glass", 148.7), ("orb0", 405.4), ("orb2", 407.3), ("orb4", 408.5), ("pop", 346.5)}
    ev = [x for x in ev if (x["key"], x["hint"]) not in DROP]
    ev = [dict(x, t=round(new(x["t"]), 3)) for x in ev if not inside(x["t"])]
    for z in vplan["zooms"]: z["t"] = round(new(z["t"]), 3)
    for z in vplan["presets"]: z["t"] = round(new(z["t"]), 3)
    vplan["zooms"] = [z for z in vplan["zooms"] if True]
    ev.sort(key=lambda x: x["t"])
    F, busy = [], {4: -1.0, 5: -1.0, 6: -1.0}
    for x in ev:
        t = x["t"]
        def near_snap(tt): return any(-0.10 <= c - tt <= 0.35 for c in joins)
        if x["snap"]:
            near = [c for c in joins if -0.10 <= c - t <= 0.35]
            if near: t = max(0.0, min(near, key=lambda c: abs(c - t)) - 0.06)
        fn = x["file"]; path = os.path.join(LIB, fn); assert os.path.exists(path), path
        dur0 = IDX[fn]["dur"]; on = TM.file_onset(path)                  # silêncio inicial do arquivo -> in-point (o som começa NO clipe)
        d = min(x["opt"].get("dur", min(dur0 - on, 2.5)), dur0 - on)
        if x["q"] is not None and not (x["snap"] and near_snap(t)): t = TM.place_time(t)       # um fio ANTES do início real da fala
        tr = next((k for k in (5, 6, 7) if busy[k] <= t + 1e-6), None)
        if tr is None:
            print("sem faixa livre p/", x); continue
        busy[tr] = t + d
        pk, rms = file_levels(path, d, on)
        ref = min(max(voice_peak(t - 0.4, t + 1.2), MEDP - 4.0), MEDP + 1.0)
        tg = table_gain(fn)
        if tg is not None and "xp-orb" not in fn and "click" not in fn:
            delta = max(-4.0, min(2.0, (pk + tg - M_REF)))
        elif "xp-orb" in fn: delta = 0.5
        elif "click" in fn: delta = 0.0
        else: delta = 0.0 if d <= 0.9 else -2.0
        g_nom = ref + delta - pk                    # ganho nominal (pós-master) p/ o pico do SFX = pico local da voz + delta
        g_clip = g_nom + COMP_DB                    # + compensação do master -12 dB
        capped = g_clip > 15.0
        g_clip = min(g_clip, 15.0)
        F.append({"name": fn, "t": round(t, 4), "dur": round(d, 3), "tr": tr, "gdb": round(g_clip, 2), "g": 10 ** ((g_clip - 15) / 20.0), "key": x["key"], "why": x["why"], "ref": round(ref, 1), "delta": round(delta, 1), "pk": round(pk, 1), "capped": capped, "off": on, "path": path.replace("\\", "/")})
    return F, vplan


if __name__ == "__main__":
    F, vp = plan()
    print("MEDP %.1f  M_REF %.1f  | %d SFX" % (MEDP, M_REF, len(F)))
    for x in F: print("%8.2f dur %.2f A%d %-8s clip %+5.1f dB (ref %.0f δ%+.1f pk %.1f)%s %s" % (x["t"], x["dur"], x["tr"] + 1, x["key"], x["gdb"], x["ref"], x["delta"], x["pk"], " CAP" if x["capped"] else "", x["why"][:40]))
    json.dump(F, open(os.path.join(HERE, "plan_sfx.json"), "w", encoding="utf8"), ensure_ascii=False)
    json.dump(vp, open(os.path.join(HERE, "plan_v_raw.json"), "w", encoding="utf8"), ensure_ascii=False)
