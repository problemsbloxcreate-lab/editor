"""Presets BERSERKER ("Lava's ...") do Matheus, reconstruídos a partir do .prfpset (library/berserker_presets.json, 192 presets).
O QE do Premiere NÃO aplica preset por nome; então lemos efeito + parâmetros + keyframes do XML e recriamos no clipe (addVideoEffect + setValue/addKey).

    import berserker as bz
    spec = bz.spec("White Flash B", ci=3, clip_in=media_in, clip_len=L)            # efeito no INÍCIO do clipe (anchor 'start')
    spec = bz.spec("Red Flash A", ci=3, clip_in=media_in, clip_len=L, anchor="end")  # no FIM do clipe
    jsx  = bz.APPLY_JS % json.dumps([spec, ...])   # dentro de um script com s, q (QE seq) e tr (s.videoTracks[0]); p/ outra faixa de vídeo: var TRK = 1; var tr = s.videoTracks[1]; antes

Âncora: presets "B"/shakes/zooms = relativos ao início do clipe; presets "A" (flash que sobe) = relativos ao fim. Tempos dos keyframes de
componente = tempo da MÍDIA (inPoint + offset).
Lumetri (VHS): só setamos Intensidade(11)/Saturação(16) — o resto fica no padrão.
"""
import json, os, re

LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "library", "berserker_presets.json")
_cat = None


def catalog():
    global _cat
    if _cat is None: _cat = json.load(open(LIB, encoding="utf8"))
    return _cat


def find(name):
    nm = name.lower().replace("lava's ", "")
    hits = [p for p in catalog() if p["path"][-1].lower().replace("lava's ", "").strip() == nm]
    if not hits: hits = [p for p in catalog() if nm in p["path"][-1].lower()]
    if not hits: raise KeyError("preset não encontrado: " + name)
    return hits[0]


def _val(s):
    if s is None: return None
    s = str(s).strip()
    if s in ("true", "false"): return s == "true"
    if ":" in s: return [float(x) for x in s.split(":")]
    try: return float(s)
    except ValueError: return None


LUMETRI_ONLY = {11, 16}


def spec(name, ci, clip_in, clip_len, anchor=None, t_start=0.0, tscale=1.0):
    """t_start: deslocamento (s) a partir do início do clipe onde o efeito começa (anchor start). tscale<1 encurta o preset (ex.: flash de 0,9 s -> 0,4 s). Retorna dict p/ APPLY_JS."""
    p = find(name)
    out = {"ci": ci, "fx": [], "preset": p["path"][-1]}
    for f in p["filters"]:
        cp = f.get("comp")
        if not cp: continue
        lim = float(f["out"]) / 254016000000.0 if f.get("out") else 5.0
        params = []
        for i, pa in enumerate(cp["params"]):
            if cp["match"] == "AE.ADBE Lumetri" and i not in LUMETRI_ONLY:
                if pa.get("keys") is None: continue
            if pa.get("keys"):
                ks = []
                tmax = max(k["t"] for k in pa["keys"] if "t" in k)
                a = anchor or ("end" if tmax > lim / 2 else "start")
                for k in pa["keys"]:
                    if "t" not in k: continue
                    v = _val(k["v"])
                    if v is None: continue
                    t = (clip_len - (lim - k["t"]) * tscale) if a == "end" else (t_start + k["t"] * tscale)
                    if t < -1e-6 or t > clip_len + 1e-6: continue
                    ks.append([round(clip_in + max(0.0, min(t, clip_len)), 5), v])
                if ks: params.append({"i": i, "keys": ks})
            else:
                st = str(pa.get("start") or "").strip()
                if re.fullmatch(r"\d+", st) and int(st) > 2 ** 40:      # cor: 4 canais de 16 bits (A,R,G,B)
                    n = int(st)
                    params.append({"i": i, "color": [((n >> sh) & 0xFFFF) // 256 for sh in (48, 32, 16, 0)]})
                    continue
                v = _val(pa.get("start"))
                if v is None or isinstance(v, bool): continue
                params.append({"i": i, "v": v})
        out["fx"].append({"name": cp["display"], "match": cp["match"], "params": params})
    return out


APPLY_JS = '''function qidx(trk, ci) { var kk = -1; for (var i = 0; i < trk.numItems; i++) { if (String(trk.getItemAt(i).type) != "Empty") kk++; if (kk == ci) return i; } return ci; }
var SP = %s;
for (var n = 0; n < SP.length; n++) { var ci = SP[n].ci; var cl = tr.clips[ci];
  for (var f = 0; f < SP[n].fx.length; f++) { var F = SP[n].fx[f]; var FXO = qe.project.getVideoEffectByName(F.name);
    if (!FXO) { r.err = (r.err || "") + "sem efeito " + F.name + "; "; continue; }
    var n0 = cl.components.numItems, B0 = []; for (var u = 0; u < n0; u++) B0.push(cl.components[u].matchName); q.getVideoTrackAt(typeof TRK == "undefined" ? 0 : TRK).getItemAt(qidx(q.getVideoTrackAt(typeof TRK == "undefined" ? 0 : TRK), ci)).addVideoEffect(FXO);
    if (cl.components.numItems <= n0) { r.err = (r.err || "") + "não aplicou " + F.name + "; "; continue; }
    var ix = cl.components.numItems - 1; for (var u = 0; u < n0; u++) if (cl.components[u].matchName != B0[u]) { ix = u; break; }   // onde o Premiere inseriu
    var comp = cl.components[ix];
    for (var k = 0; k < F.params.length; k++) { var P = F.params[k]; var pr = comp.properties[P.i];
      try { if (P.keys) { pr.setTimeVarying(true); for (var j = 0; j < P.keys.length; j++) { pr.addKey(P.keys[j][0]); pr.setValueAtKey(P.keys[j][0], P.keys[j][1]); } }
        else if (P.color) pr.setColorValue(P.color[0], P.color[1], P.color[2], P.color[3], true); else pr.setValue(P.v, true); } catch (e) { r.err = (r.err || "") + F.name + "#" + P.i + ":" + e + " "; } } } }
'''
