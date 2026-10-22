"""Premiere em QUALQUER idioma (Estúdio Problems Local, 22/10/2026): a skill escreve os efeitos pelo nome em PORTUGUÊS
("Cor de Lumetri", "Limitador pesado", "Potência constante"...) e este módulo troca, dentro do JSX, pelo nome que existe NO Premiere
desta máquina (inglês, português ou outro).

    import pr_names
    jsx = pr_names.wrap(jsx)          # em todo run() dos builders: injeta o prelúdio e troca as chamadas QE por EP_*
    pr_names.ensure(runner)           # 1x por job, já DENTRO do projeto do job: confere/descobre os nomes (cache por versão+idioma)
    python pr_names.py check          # com o Premiere aberto: mostra o que resolve e o que falta (só leitura)

No JSX (depois do wrap):
    EP_vfx("Cor de Lumetri")  EP_afx("Limitador pesado")  EP_atr("Potência constante")    -> objeto QE do efeito/transição
    EP_comp(clip, "Brilho cintilante")                                                       -> componente pelo matchName (não pelo nome exibido)
    EP_pt(comp, i)                                                                           -> nome PT do parâmetro i (para receitas por nome)
Como resolve: nome descoberto nesta máquina (cache) > nome PT > nomes EN conhecidos > índice na lista (transições).  Se nada existir,
EP_vfx devolve null e o builder registra a falha (ex.: preset que usa plugin BCC não instalado) sem derrubar o resto.
A descoberta (discover) roda numa CÓPIA da sequência do job, aplica efeitos e lê o matchName, e apaga a cópia — nunca em projeto do usuário.
"""
import json, os, re, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SK = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import paths as P

# nome PT (como a skill escreve) -> (tipo, matchName, nomes em inglês conhecidos)
FX = {
    "Cor de Lumetri": ("v", "AE.ADBE Lumetri", ["Lumetri Color"]),
    "Tonalidade": ("v", "AE.ADBE Tint", ["Tint"]),
    "Brilho cintilante": ("v", "AE.Impact_Glint_FX", ["Glint"]),
    "Distorção de lente": ("v", "PR.ADBE Lens Distortion", ["Lens Distortion"]),
    "Transformar": ("v", "AE.ADBE Geometry2", ["Transform"]),
    "3D básico": ("v", "AE.ADBE Basic 3D", ["Basic 3D"]),
    "Entalhe de cor": ("v", "AE.ADBE Color Emboss", ["Color Emboss"]),
    "Sombra projetada": ("v", "AE.ADBE Drop Shadow", ["Drop Shadow"]),
    "Desfoque rápido": ("v", "AE.ADBE Fast Blur", ["Fast Blur", "Fast Blur (Legacy)"]),
    "Grade": ("v", "AE.ADBE Grid", ["Grid"]),
    "Efeitos de iluminação": ("v", "AE.ADBE LightingEffect", ["Lighting Effects"]),
    "Espelho": ("v", "AE.ADBE Mirror", ["Mirror"]),
    "Mosaico (herdado)": ("v", "AE.ADBE Mosaic", ["Mosaic (Legacy)", "Mosaic"]),
    "Ruído (herdado)": ("v", "AE.ADBE Noise", ["Noise (Legacy)", "Noise"]),
    "Tornar bordas ásperas": ("v", "AE.ADBE Roughen Edges", ["Roughen Edges"]),
    "Deslocamento com turbulência": ("v", "AE.ADBE Turbulent Displace", ["Turbulent Displace"]),
    "Ultra Key": ("v", "AE.ADBE Ultra Key", ["Ultra Key"]),
    "Distorção ondulada": ("v", "AE.ADBE Wave Warp", ["Wave Warp"]),
    "Preto e branco": ("v", "AE.ADBE Black & White", ["Black & White"]),
    "Brilho para VR": ("v", "AE.Mettle SkyBox Glow", ["VR Glow"]),
    "BCC Cube": ("v", "AE.BCC3Cube", ["BCC Cube"]),
    "BCC Extruded EPS": ("v", "AE.ScriptEP", ["BCC Extruded EPS"]),
    "Limitador pesado": ("a", "e0b23f05-f1a7-4ef7-9b50-7ec3e3002058", ["Hard Limiter"]),
    "Reverberação de estúdio": ("a", "7ea99d31-ca8f-454f-acd7-81a258efb336", ["Studio Reverb"]),
    "Potência constante": ("at", None, ["Constant Power", "#0"]),          # transição: sem matchName legível; #0 = 1ª da lista
    "Ganho constante": ("at", None, ["Constant Gain", "#1"]),
    "Atenuação exponencial": ("at", None, ["Exponential Fade", "#2"]),
}
CORE = {"Cor de Lumetri", "Tonalidade", "Brilho cintilante", "Distorção de lente", "Limitador pesado"}   # usados pelos builders (o resto: presets)
PROPS = {k: v for k, v in json.load(open(os.path.join(SK, "library", "pr_props_pt.json"), encoding="utf8")).items() if not k.startswith("_")}


def cache_path(version, locale):
    return P.writable("pr_names_%s_%s.json" % (re.sub(r"[^\w.]", "_", version or "x"), locale or "x"))


def _latest_cache():
    d = P.cache_dir()
    fs = sorted((f for f in os.listdir(d) if f.startswith("pr_names_")), key=lambda f: os.path.getmtime(os.path.join(d, f)))
    return json.load(open(os.path.join(d, fs[-1]), encoding="utf8")) if fs else {}


def prelude(found=None):
    found = found if found is not None else _latest_cache().get("names", {})
    cand = {pt: ([found[pt]] if found.get(pt) else []) + [pt] + en for pt, (k, m, en) in FX.items()}
    kind = {pt: k for pt, (k, m, en) in FX.items()}
    match = {pt: m for pt, (k, m, en) in FX.items() if m}
    props = {m: v["props"] for m, v in PROPS.items()}
    return ('''var EP_CAND = %s, EP_KIND = %s, EP_MATCH = %s, EP_PROPS = %s, __EPL = {};
function EP_list(k) { if (!__EPL[k]) { app.enableQE(); var l;      // sem ternário encadeado: o ExtendScript avalia errado
    if (k == "v") l = qe.project.getVideoEffectList(); else if (k == "a") l = qe.project.getAudioEffectList();
    else if (k == "at") l = qe.project.getAudioTransitionList(); else l = qe.project.getVideoTransitionList(); var o = {arr: l, has: {}}; for (var i = 0; i < l.length; i++) o.has[l[i]] = 1; __EPL[k] = o; } return __EPL[k]; }
function EP_name(pt, k) { k = k || EP_KIND[pt] || "v"; var L = EP_list(k); var c = EP_CAND[pt] || [pt];
  for (var i = 0; i < c.length; i++) { var n = String(c[i]); if (n.charAt(0) == "#") { var ix = parseInt(n.substr(1), 10); if (ix < L.arr.length) return L.arr[ix]; } else if (L.has[n]) return n; }
  return null; }
function EP_vfx(pt) { var n = EP_name(pt, "v"); return n ? qe.project.getVideoEffectByName(n) : null; }
function EP_afx(pt) { var n = EP_name(pt, "a"); return n ? qe.project.getAudioEffectByName(n) : null; }
function EP_atr(pt) { var n = EP_name(pt, "at"); return n ? qe.project.getAudioTransitionByName(n) : null; }
function EP_vtr(pt) { var n = EP_name(pt, "vt"); return n ? qe.project.getVideoTransitionByName(n) : null; }
function EP_comp(c, pt) { var m = EP_MATCH[pt]; for (var u = c.components.numItems - 1; u >= 0; u--) { var x = c.components[u]; if ((m && x.matchName == m) || x.displayName == pt) return x; } return null; }
function EP_pt(comp, i) { var L = EP_PROPS[comp.matchName]; return (L && i < L.length) ? L[i] : comp.properties[i].displayName; }
''' % (json.dumps(cand, ensure_ascii=True), json.dumps(kind), json.dumps(match), json.dumps(props, ensure_ascii=True)))


_SUBS = [(re.compile(r"qe\.project\.getVideoEffectByName\("), "EP_vfx("), (re.compile(r"qe\.project\.getAudioEffectByName\("), "EP_afx("),
         (re.compile(r"qe\.project\.getAudioTransitionByName\("), "EP_atr("), (re.compile(r"qe\.project\.getVideoTransitionByName\("), "EP_vtr(")]


def wrap(jsx):
    """prelúdio + chamadas QE por nome trocadas pelas EP_* (idempotente)."""
    if "var EP_CAND" in jsx:
        return jsx
    for rx, rep in _SUBS:
        jsx = rx.sub(rep, jsx)
    return prelude() + jsx


CHECK_JS = '''app.enableQE(); var miss = [], ok = {};
for (var pt in EP_CAND) { var n = EP_name(pt); if (n) ok[pt] = n; else miss.push(pt); }
return __result({version: app.version, locale: $.locale, ok: ok, miss: miss});'''

# descoberta: numa CÓPIA da sequência ativa (a do job), aplica efeitos candidatos no 1º clipe de V1/A1 e lê o matchName do componente novo
DISCOVER_JS = '''app.enableQE(); var WANT = %s; var AWANT = %s; var res = {names: {}, props: {}, tried: 0};
var src = app.project.activeSequence; if (!src) throw new Error("sem sequência ativa");
var before = app.project.sequences.numSequences; src.clone(); var seq = app.project.sequences[app.project.sequences.numSequences - 1];
if (app.project.sequences.numSequences == before) throw new Error("clone falhou");
try {
  app.project.activeSequence = seq; var q = qe.project.getActiveSequence();
  function scan(list, want, isA) { var trk = isA ? seq.audioTracks[0] : seq.videoTracks[0]; var qt = isA ? q.getAudioTrackAt(0) : q.getVideoTrackAt(0);
    var qi = null; for (var i = 0; i < qt.numItems; i++) if (String(qt.getItemAt(i).type) != "Empty") { qi = qt.getItemAt(i); break; }
    if (!qi || !trk.clips.numItems) return; var c = trk.clips[0]; var left = 0; for (var w in want) left++;
    for (var i = 0; i < list.length && left > 0; i++) { var n0 = c.components.numItems;
      try { if (isA) qi.addAudioEffect(qe.project.getAudioEffectByName(list[i])); else qi.addVideoEffect(qe.project.getVideoEffectByName(list[i])); } catch (e) { continue; }
      res.tried++; if (c.components.numItems <= n0) continue; var x = c.components[c.components.numItems - 1];
      if (want.hasOwnProperty(x.matchName)) { res.names[want[x.matchName]] = list[i]; var pr = []; for (var k = 0; k < x.properties.numItems; k++) pr.push(x.properties[k].displayName);
        res.props[x.matchName] = pr; delete want[x.matchName]; left--; } } }
  scan(qe.project.getVideoEffectList(), WANT, false); scan(qe.project.getAudioEffectList(), AWANT, true);
} finally { app.project.activeSequence = src; app.project.deleteSequence(seq); }
res.version = app.version; res.locale = $.locale; return __result(res);'''


def _bridge(js, timeout=600):
    fd, path = tempfile.mkstemp(suffix=".jsx"); os.close(fd)
    open(path, "w", encoding="utf8").write(js)
    try:
        out = subprocess.run([sys.executable, os.path.join(HERE, "run_bridge.py"), path, str(timeout)], capture_output=True, text=True, encoding="utf8")
        if out.returncode:
            raise RuntimeError((out.stderr or out.stdout)[-600:])
        return json.load(open(path[:-4] + ".result.json", encoding="utf8"))
    finally:
        for p in (path, path[:-4] + ".result.json"):
            try: os.remove(p)
            except OSError: pass


def check():
    return _bridge(prelude() + CHECK_JS, 60)


def ensure(log=print):
    """chamar com o PROJETO DO JOB ativo (sequência de trabalho aberta). Confere; se faltar efeito, descobre na cópia e grava o cache."""
    r = check()
    cp = cache_path(r["version"], r["locale"])
    cached = json.load(open(cp, encoding="utf8")) if os.path.exists(cp) else {"names": {}, "props": {}}
    pt_locale = str(r["locale"]).lower().startswith("pt")
    absent = set(cached.get("absent", []))
    miss = [pt for pt in r["miss"] if FX[pt][1] and pt not in cached["names"] and pt not in absent and (pt in CORE or not pt_locale)]
    if miss:
        want = {FX[pt][1]: pt for pt in miss if FX[pt][0] == "v"}
        awant = {FX[pt][1]: pt for pt in miss if FX[pt][0] == "a"}
        log("pr_names: Premiere %s (%s) sem nome para %s — descobrindo numa cópia da sequência" % (r["version"], r["locale"], ", ".join(miss)))
        d = _bridge(prelude(cached["names"]) + DISCOVER_JS % (json.dumps(want), json.dumps(awant)), 900)
        cached["names"].update(d["names"]); cached["props"].update(d["props"])
        cached["absent"] = sorted(absent | {pt for pt in miss if pt not in d["names"]})      # não procurar de novo a cada job
    for pt, n in r["ok"].items():
        cached["names"].setdefault(pt, n)
    cached.update(version=r["version"], locale=r["locale"])
    json.dump(cached, open(cp, "w", encoding="utf8"), ensure_ascii=False, indent=1)
    still = [pt for pt in FX if FX[pt][1] and pt not in cached["names"]]
    if still:
        log("pr_names: AVISO — este Premiere não tem: %s (presets que usam ficam sem esse efeito; plugins BCC/Mettle são de terceiros)" % ", ".join(still))
    if not pt_locale:
        log("pr_names: Premiere em %s — efeitos resolvidos por nome traduzido/matchName; parâmetros pelo índice da referência PT" % r["locale"])
    return cached


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf8")
    a = sys.argv[1:]
    if not a or a[0] == "check":
        r = check()
        print("Premiere %s, idioma %s" % (r["version"], r["locale"]))
        for pt, n in sorted(r["ok"].items()):
            print("  OK    %-30s -> %s" % (pt, n))
        for pt in r["miss"]:
            print("  FALTA %-30s (%s)" % (pt, FX[pt][1]))
    elif a[0] == "discover":
        print(json.dumps(ensure(), ensure_ascii=False, indent=1)[:3000])
