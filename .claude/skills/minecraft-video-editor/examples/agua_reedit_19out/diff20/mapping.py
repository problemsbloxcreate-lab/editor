"""Mapeia tempo da timeline antiga (Sequência 01 = base da minha v2) <-> fonte (nest VIDEO ORIGINAL) <-> timeline nova (v2 editada por ele)."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
L = lambda f: json.load(open(os.path.join(HERE, f), encoding="utf8"))
ORIG = L("orig_seq01.json"); HIS = L("his_v2.json")


def segs(d, tr=0, enabled_only=False):
    out = []
    for c in d["V"][tr]["clips"]:
        if enabled_only and c["d"]: continue
        out.append((c["s"], c["e"], c["i"], c["d"]))
    return out


OLD = segs(ORIG); NEW = segs(HIS)


def old2src(t):
    for s, e, i, d in OLD:
        if s - 1e-4 <= t < e + 1e-4: return i + (t - s)
    return None


def src2new(x, prefer=None):
    best = None
    for s, e, i, d in NEW:
        if i - 1e-3 <= x <= i + (e - s) + 1e-3:
            t = s + (x - i)
            if best is None or (prefer is not None and abs(t - prefer) < abs(best - prefer)): best = t
    return best


def old2new(t):
    x = old2src(t)
    return None if x is None else src2new(x, prefer=t)


def new2src(t):
    for s, e, i, d in NEW:
        if s - 1e-4 <= t < e + 1e-4: return i + (t - s)
    return None


def src2old(x):
    for s, e, i, d in OLD:
        if i - 1e-3 <= x <= i + (e - s) + 1e-3: return s + (x - i)
    return None


def new2old(t):
    x = new2src(t)
    return None if x is None else src2old(x)


def tc(t):
    if t is None: return "  --  "
    m, s = divmod(t, 60); return "%02d:%05.2f" % (m, s)
