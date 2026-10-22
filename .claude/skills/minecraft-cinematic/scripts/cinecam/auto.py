"""auto: a JSON "shot card" -> rendered cutaway.  Used by the video editor (minecraft-video-editor, stage "cinemáticas") so a
whole video's cinematics are described as data, checked as stills/drafts and rendered in ONE game session (render_batch).

Card (all keys optional except id/dur):
{
 "id": "c01", "dur": 3.0, "fps": 60,
 "site": "desert" | [x, y_top_ground, z],  "r": 18,            # catalogued flat site of that biome (references/sites_4242.json)
 "time": 5000, "weather": "clear", "biome": "desert",          # kit = floor + scatter + trees of the biome (sets.KITS)
 "density": 1.0, "trees": true,
 "set":   [["pond", {"dx": 5, "dz": -3, "rx": 4.5, "rz": 3}],   # SetBuilder methods + kwargs, in order (pond, tree, template,
           ["mob", {"mtype": "camel", "dx": -9, "dz": -14, "yaw": 30}], ...],   #  structure, mob, block, box, raw, mark)
 "cast":  [{"who": "problems", "dx": 0, "dz": 0, "face": "camera"}, {"who": "stick", "dx": -1.6, "dz": 0.4, "face": "problems"}],
 "beats": [["walk", {"who": "problems", "to": [3, -2], "t0": 0.3, "t1": 1.6}], ["celebrate", {"who": "*", "t": 2.0}], ...],
 "camera": {"kind": "hero_low", ...kwargs of acts.cam_<kind>},
 "grade": "insert",
 "python": "path/to/custom.py"     # optional: def build(st, sb, card) -> Rig | None  (st = acts.Stage; free-form choreography)
}
Qualities: "stills" (3 frames: start/middle/end, 960x540, frozen), "draft" (960x540, 2 subframes, no DoF) and "final"
(1920x1080, adaptive subframes 4-12 with sub-pixel AA, DoF when the camera asks for it).
"""
from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path
from typing import Dict, List, Sequence

import numpy as np

from . import acts as _acts
from . import framing as _fr
from .render import Shot, Settings, World, render_batch
from .sets import SetBuilder, site as _site


def auto_subframes(rig, height: int = 1080, lo: int = 4, hi: int = 12) -> int:
    """Motion-blur samples from the camera's real motion: ~1 sample per 1.5 px of blur (p95 over the shot)."""
    d = rig.sample_frames()
    if len(d["t"]) < 3:
        return lo
    deg_px = np.maximum(d["fov"], 1.0) / height
    ang = np.hypot(np.diff(d["yaw"]), np.diff(d["pitch"])) / deg_px[1:]
    pos = np.linalg.norm(np.diff(np.stack([d["x"], d["y"], d["z"]], 1), axis=0), axis=1)
    trans = np.degrees(pos / 3.0) / deg_px[1:]                     # subject ~3 blocks away (cutaways are mostly medium/close)
    blur = (ang + trans) * rig.shutter
    return int(np.clip(math.ceil(np.percentile(blur, 95) / 1.5), lo, hi))


def _solve_camera(st, T, fps, kind, cam, card):
    """Build the requested camera and check it (enquadramento.md §3g).  If it fails and the card did not pin `side`/`az`, try the
    mirrored side and tighter azimuths before giving up (the card must then be re-blocked)."""
    tries = [dict(cam)]
    if "side" not in cam:
        tries.append(dict(cam, side=-1))
    if "az" not in cam and kind in ("hero_low", "orbit_push", "close", "establish"):
        for sd in (1, -1):
            for scale in (0.5, 0.0):
                base = {"hero_low": (18, 6), "orbit_push": (40, 12), "close": (24, 6), "establish": (28, 14)}[kind]
                tries.append(dict(cam, side=sd, az=(base[0] * scale + 4, base[1] * scale + 2)))
    import inspect
    allowed = set(inspect.signature(_acts.CAMS[kind]).parameters)
    drop = [k for k in cam if k not in allowed]
    if drop:
        print(f"[cinecam] {card.get('id')}: parâmetros ignorados na câmera '{kind}': {drop}")
        tries = [{k: v for k, v in kw.items() if k in allowed} for kw in tries]
    last = None
    for kw in tries:
        rig = _acts.CAMS[kind](st, T, fps=fps, sub=2, **kw)
        ok, why = _fr.verdict(_fr.check_shot(rig, st, subject=card.get("subject")), allow_back=st.allow_back)
        if ok:
            if kw != cam:
                print(f"[cinecam] {card.get('id')}: câmera ajustada para passar no enquadramento: {kw}")
            return rig
        last = why
    raise ValueError("enquadramento reprovado (refaça o blocking/câmera): " + "; ".join(last or []))


def check_card(card: dict) -> List[str]:
    """Problems of a card without rendering ([] = ok): props glued + framing (after the automatic camera search)."""
    try:
        shot_from_card(card, "draft")
        return []
    except ValueError as e:
        return [str(e)]


def stage_from_card(card: dict):
    T = float(card["dur"])
    where = card.get("site", "desert")
    sb = SetBuilder(_site(where) if isinstance(where, str) else where, r=int(card.get("r", 18)), seed=int(card.get("seed", 7)))
    biome = card.get("biome") or (where if isinstance(where, str) else "plains")
    if card.get("kit", True):
        sb.ground(biome)
    for op, kw in card.get("set", []):
        getattr(sb, op)(**kw) if isinstance(kw, dict) else getattr(sb, op)(*kw)
    aud = float(card.get("audience", 0.0))
    st = _acts.Stage(sb, T, audience=aud)
    for c in card.get("cast", []):
        st.add(**c)
        # corredor da câmera (as câmeras ficam do lado da plateia): sem grama/flor/árvore entre a lente e o personagem
        # (21/10, job do vídeo inteiro: câmera baixa atravessando grama alta tapava a cena)
        fx, fz = -math.sin(math.radians(aud)), math.cos(math.radians(aud))
        for f in np.arange(0.5, 10.5, 0.5):
            for l in np.arange(-5.0, 5.5, 0.5):
                sb.keep_free_rect(c.get("dx", 0) + fx * f + fz * l, c.get("dz", 0) + fz * f - fx * l,
                                  c.get("dx", 0) + fx * f + fz * l, c.get("dz", 0) + fz * f - fx * l)
    if card.get("kit", True):
        sb.dress(biome, density=float(card.get("density", 1.0)), trees=bool(card.get("trees", True)))
    for name, kw in card.get("beats", []):
        getattr(st, name)(**kw)
    return st, sb


def shot_from_card(card: dict, quality: str = "final", prefix: str = "") -> Shot:
    st, sb = stage_from_card(card)
    T = float(card["dur"])
    fps = int(card.get("fps", 60))
    cam = dict(card.get("camera", {"kind": "hero_low"}))
    kind = cam.pop("kind", "hero_low")
    rig = None
    if card.get("python"):
        spec = importlib.util.spec_from_file_location("card_" + card["id"], card["python"])
        mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        rig = mod.build(st, sb, card)
    problems = st.run_checks()                       # props glued to limbs: non-negotiable
    if problems:
        raise ValueError("item mal encaixado: " + "; ".join(problems[:4]))
    if rig is None:
        rig = _solve_camera(st, T, fps, kind, cam, card)
    else:
        ok, why = _fr.verdict(_fr.check_shot(rig, st, subject=card.get("subject")), allow_back=st.allow_back)
        if not ok:
            raise ValueError("enquadramento: " + "; ".join(why))
    final = quality == "final"
    sub = int(card.get("sub") or (auto_subframes(rig) if final else 2))
    rig.subframes = sub
    name = f"{prefix}{card['id']}" + ("" if final else "_" + quality)
    settings = Settings(renderDistance=int(card.get("render_distance", 8 if card.get("close") else 10)), simulationDistance=6,
                        worldTicks=True, clouds=bool(card.get("clouds", True)))
    scene = sb.scene(time=int(card.get("time", 6000)), weather=card.get("weather", "clear"),
                     anchor=tuple(np.round(st.center() + [0, 4, 0], 2)) if st.actors else None,
                     dimension=card.get("dimension", sb.dimension))
    if quality == "stills":
        rows = rig.sample_frames()
        n = len(rows["t"])
        idx = [0, n // 2, n - 1]
        poses = [dict(x=rows["x"][i], y=rows["y"][i], z=rows["z"][i], yaw=rows["yaw"][i], pitch=rows["pitch"][i], roll=rows["roll"][i],
                      fov=rows["fov"][i], t=float(rows["t"][i])) for i in idx]
        return Shot(name, poses=poses, scene=scene, settings=settings, anim=st.anim(), size=(960, 540))
    return Shot(name, rig=rig, scene=scene, settings=settings, anim=st.anim(), size=(1920, 1080) if final else (960, 540),
                grade=card.get("grade", "insert"), dof=None if final else False)


def render_cards(cards: Sequence[dict], quality: str = "final", prefix: str = "", seed: int = 4242, log=print) -> List[Dict]:
    """All cards in ONE Minecraft session.  Returns render_batch infos (+ 'id')."""
    shots, ok_cards, refused = [], [], []
    for c in cards:
        try:
            shots.append(shot_from_card(c, quality, prefix)); ok_cards.append(c)
        except ValueError as e:                       # a refused card does not stop the others
            refused.append({"id": c["id"], "ok": False, "error": str(e)})
            log(f"[cinecam] {c['id']} RECUSADO: {e}")
    infos = render_batch(shots, world=World(seed=seed), log=log) if shots else []
    for c, i in zip(ok_cards, infos):
        i["id"] = c["id"]
    order = {c["id"]: k for k, c in enumerate(cards)}
    return sorted(infos + refused, key=lambda i: order[i["id"]])


if __name__ == "__main__":
    import sys
    cards = json.load(open(sys.argv[1], encoding="utf-8"))
    q = sys.argv[2] if len(sys.argv) > 2 else "draft"
    res = render_cards(cards if isinstance(cards, list) else cards["cards"], q)
    print(json.dumps([{k: v for k, v in r.items() if k != "report"} for r in res], indent=1, ensure_ascii=False))
