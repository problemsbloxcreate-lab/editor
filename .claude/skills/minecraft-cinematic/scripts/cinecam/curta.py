"""curta: cenas dos SHORTS (9:16) a partir de FICHAS JSON (v1.1, 26/10/2026).

O produtor (Claude, na produção do Shorts) só escreve dados — um MAPA por vídeo e uma FICHA por cena; o PC de quem produz renderiza
(serviço local, minecraft-video-editor/app/curtas.py).  As regras do canal saem daqui, não da ficha: câmera na altura do rosto e DE
FRENTE (contraplano fixo: a mesma câmera toda vez que o personagem fala no mesmo lugar), duração EXATA da cena, nada atravessa
nada (recusa), boca parada, piscar, sombra; motion blur e desfoque de lente opcionais.  Formato completo: references/ficha-curta.md.

    from cinecam.curta import shot_da_ficha, checar_ficha, render_fichas
    problemas = checar_ficha(mapa, ficha)                  # rápido, sem abrir o jogo (colisão, trancos, enquadramento)
    infos = render_fichas(mapa, [ficha1, ficha2], qualidade="final")   # uma sessão do jogo para todas
"""
from __future__ import annotations

import math
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

from .actors import Anim, Mob, POSE
from .atua import Ator, snaps
from .camlib import Rig
from .moves import track
from .render import Scene, Settings, Shot, World, checar_colisao
from .sets import SetBuilder, site as _site
from .turma import skin as _skin

FPS = 30
SIZE = {"final": (1080, 1920), "rascunho": (540, 960)}
VFOV = 58.0
HFOV = 2 * math.degrees(math.atan(math.tan(math.radians(VFOV / 2)) * 9 / 16))
EYE = 1.62          # altura da câmera "no rosto" (pés + 1,62; o rosto do modelo de 2 blocos fica em 1,5–2,0)

# 26/10/2026 (dono): as mesmas regras dos Shorts portadas para as cinemáticas do VÍDEO LONGO (16:9 1920×1080, 60 fps como a
# timeline do Premiere).  A ficha (ou o mapa) diz "formato": "16:9"; sem isso continua 9:16 (Shorts).  No 16:9 a lente é mais
# fechada (vfov 40 ≈ hfov 66) e as distâncias mudam para o personagem ficar do mesmo tamanho na tela.
FORMATOS = {
    "9:16": {"final": (1080, 1920), "rascunho": (540, 960), "fps": 30, "vfov": 58.0, "aspect": 9 / 16, "sub": 6, "ap": 0.3,
             "dist": {"fala": 2.6, "medio": 2.9, "reacao": 2.0, "close": 1.75}, "aberto": 6.4, "dois_min": 3.4, "palco": (-7, -6, 7, 9)},
    "16:9": {"final": (1920, 1080), "rascunho": (960, 540), "fps": 60, "vfov": 40.0, "aspect": 16 / 9, "sub": 4, "ap": 0.22,
             "dist": {"fala": 2.9, "medio": 3.6, "reacao": 2.3, "close": 1.8}, "aberto": 7.5, "dois_min": 3.0, "palco": (-10, -6, 10, 11)},
}


def formato(mapa: Dict, ficha: Dict) -> Dict:
    nome = ficha.get("formato") or mapa.get("formato") or "9:16"
    if nome not in FORMATOS:
        raise KeyError(f"formato {nome!r} (tem: {sorted(FORMATOS)})")
    F = dict(FORMATOS[nome]); F["nome"] = nome
    F["hfov"] = 2 * math.degrees(math.atan(math.tan(math.radians(F["vfov"] / 2)) * F["aspect"]))
    return F


# ------------------------------------------------------------------------------------------------------------------- lugar
def _lugar(mapa: Dict, nome: str) -> Dict:
    L = (mapa.get("lugares") or {}).get(nome)
    if L is None:
        raise KeyError(f"lugar {nome!r} não está no mapa (tem: {sorted((mapa.get('lugares') or {}))})")
    return L


def montar_lugar(mapa: Dict, nome: str, palco=(-7, -6, 7, 9)) -> SetBuilder:
    """Set do lugar — o MESMO para todas as cenas dele (mesmos comandos, mesma semente): continuidade entre cortes."""
    L = _lugar(mapa, nome)
    where = L.get("site") or _site(L.get("bioma", "plains"))
    sb = SetBuilder(where, r=int(L.get("raio", 20)), seed=int(L.get("seed", 5)))
    bioma = L.get("bioma") or (where.get("biome") if isinstance(where, dict) else "plains")
    sb.ground(bioma)
    for nome_m, m in (L.get("marcas") or {}).items():
        sb.keep_free(float(m[0]), float(m[1]), 2.0)
    sb.keep_free_rect(*palco)                          # palco + corredor da câmera (a câmera fica do lado +z)
    for b in L.get("blocos") or []:
        k = b[0]
        if k == "box":                                  # sets.box/block já põem "minecraft:" (aceita o id com ou sem)
            sb.box(*[int(v) for v in b[1:7]], b[7].replace("minecraft:", ""))
        elif k == "bloco":
            sb.block(int(b[1]), int(b[2]), int(b[3]), b[4].replace("minecraft:", ""))
        elif k == "arvore":
            sb.tree(float(b[1]), float(b[2]), b[3] if len(b) > 3 else "oak")
        elif k == "comando":
            sb.raw(b[1])
        elif k == "lagoa":                              # ["lagoa", dx, dz, rx, rz] (água com borda orgânica, plantas)
            sb.pond(float(b[1]), float(b[2]), float(b[3]), float(b[4]), plants=b[5] if len(b) > 5 else "sugar_cane")
    if L.get("enfeite", True):
        sb.dress(bioma, density=float(L.get("densidade", 0.8)))
    sb.raw("kill @e[type=item]")                      # tocha/planta do set anterior (mesma sessão) cai como item no chão
    return sb


def _pt(sb: SetBuilder, p) -> np.ndarray:
    """[dx, dz] ou [dx, dy, dz] do lugar → mundo (pés).  Meio bloco é respeitado (nada de arredondar)."""
    base = sb.feet(0, 0)
    if len(p) == 2:
        return base + np.array([float(p[0]), 0.0, float(p[1])])
    return base + np.array([float(p[0]), float(p[1]), float(p[2])])


# ------------------------------------------------------------------------------------------------------------------- elenco
def _elenco(mapa, ficha, sb) -> Dict[str, Ator]:
    L = _lugar(mapa, ficha["lugar"])
    marcas = L.get("marcas") or {}
    out: Dict[str, Ator] = {}
    for c in ficha.get("elenco", []):
        quem = c["quem"]
        em = c.get("em", quem)
        m = marcas.get(em) if isinstance(em, str) else None
        if isinstance(em, str) and m is None:
            raise KeyError(f"{quem}: marca {em!r} não existe no lugar {ficha['lugar']}")
        pos = _pt(sb, m[:2] if m else em)
        vira = float(c.get("vira", m[2] if m and len(m) > 2 else 0.0))
        out[quem] = Ator(quem, c.get("skin_png") or _skin(c.get("skin", quem)), pos, yaw=vira, item=c.get("item"),
                         slim=bool(c.get("slim", False)), energy=float(c.get("energia", 1.0)))
    return out


def _alvo(a: Dict[str, Ator], sb, alvo, t: float) -> Optional[np.ndarray]:
    if alvo is None:
        return None
    if isinstance(alvo, str):
        if alvo in a:
            return a[alvo].pos_at(t) + [0, 1.3, 0]
        if alvo == "camera":
            return None
        raise KeyError(f"alvo {alvo!r}: nem personagem nem ponto")
    return _pt(sb, alvo)


def _acoes(ficha, a: Dict[str, Ator], sb):
    for x in sorted(ficha.get("acoes", []), key=lambda x: float(x.get("t", 0))):
        quem, faz, t = x.get("quem"), x["faz"], float(x.get("t", 0))
        if quem not in a:
            raise KeyError(f"ação {faz} em {t}s: {quem!r} não está no elenco")
        A = a[quem]
        if faz == "fala":
            A.talk(t, float(x["ate"]), text=x.get("texto", ""), calm=bool(x.get("calmo", False)))
        elif faz == "pose":
            A.pose(t, x["pose"], snap=3.0 if x.get("rapido") else 1.0, left=x.get("esquerda"))
        elif faz == "aponta":
            alvo = x.get("alvo")
            if alvo in ("esquerda", "direita"):           # lado da TELA (câmera do lado +z olhando para -z: direita da tela = +x)
                p = A.pos_at(t) + [(-3.0 if alvo == "esquerda" else 3.0), 1.9, 1.0]
            else:
                p = _alvo(a, sb, alvo, t)
            A.point_at(t, p, left=x.get("esquerda"))
        elif faz == "entrega":                            # estende no espaço ENTRE os dois (nunca até o peito do outro)
            o = a[x["para"]]
            p = A.pos_at(t) + 0.55 * (o.pos_at(t) - A.pos_at(t)) + [0, 1.2, 0.35]
            A.point_at(t, p, elbow=-0.5)
            A.hold_item(t - 0.2, float(x.get("ate", t + 1.5)))
        elif faz == "segura":
            A.hold_item(t, float(x.get("ate", 1e9)))
        elif faz == "olha":
            A.look(t, _alvo(a, sb, x.get("alvo"), t), float(x.get("peso", 0.8)))
        elif faz == "vira":
            para = x.get("para", "camera")
            if para == "camera":
                A.turn(t, 0.0)
            elif isinstance(para, (int, float)):
                A.turn(t, float(para))
            else:
                A.face_to(t, _alvo(a, sb, para, t))
        elif faz == "pula":
            A.jump(t, float(x.get("altura", 0.9)), float(x.get("ar", 0.42)))
        elif faz == "anda":
            q = _pt(sb, x["para"])
            A.walk(t, float(x["ate"]), (q[0], q[2]), gait=x.get("modo", "auto"))
        else:
            raise KeyError(f"ação desconhecida {faz!r} (fala pose aponta entrega segura olha vira pula anda)")


def _mobs(ficha, sb) -> List[Mob]:
    out = []
    for i, m in enumerate(ficha.get("mobs", [])):
        tipo = "minecraft:" + m["tipo"].replace("minecraft:", "")
        p = _pt(sb, m["em"])
        mob = Mob.feet(f"mob{i}", tipo, p)
        h = Mob.height(tipo) / 2
        mob.key(0.0, yaw=float(m.get("vira", 0.0)))
        if m.get("aparece") is not None:                  # escondido (sx=0) até a hora de aparecer
            ta = float(m["aparece"])
            for ch in ("sx", "sy", "sz"):
                mob.keys[ch] = [(0.0, 0.0, "hold"), (ta, 1.0, "hold")]
        x0 = p
        for (t0, t1, *dst) in m.get("anda", []):
            q = _pt(sb, dst)
            yaw = math.degrees(math.atan2(-(q[0] - x0[0]), q[2] - x0[2]))
            mob.key(float(t0), x=x0[0], z=x0[2]).key(float(t0) + 0.01, yaw=yaw).key(float(t1), ease="linear", x=q[0], z=q[2])
            x0 = q
        out.append(mob)
    return out


# ------------------------------------------------------------------------------------------------------------------- câmera
def _fwd(yaw: float) -> np.ndarray:
    r = math.radians(yaw)
    return np.array([-math.sin(r), 0.0, math.cos(r)])


def _chest(A, t, up=1.45):
    p = A.at(np.atleast_1d(np.asarray(t, float)))
    return np.stack([p[:, 0], p[:, 1] + up + 0.6 * p[:, POSE["hop"]], p[:, 2]], axis=1)


def _plano(rig: Rig, pl: Dict, t0: float, T: float, at: Dict, sb, first: bool, efeitos: Dict, mobs: Sequence[Mob] = (),
           F: Optional[Dict] = None):
    """Um plano de frente, na altura do rosto (regras do dono 25–26/10), no formato F (9:16 ou 16:9).
    Ajustes opcionais do plano: dist (distância), lado (graus em volta do personagem, ≤ ~20 = continua de frente),
    altura (câmera acima dos pés; padrão EYE), mira (altura do ponto mirado), push (false ou blocos)."""
    F = F or FORMATOS["9:16"]
    kind = pl.get("plano", "fala")
    quem = pl.get("quem")
    A = at.get(quem) if quem else None
    pv = pl.get("push", True)
    push = (0.3 if pv is True else 0.0 if pv is False else float(pv))
    fov = float(pl.get("fov", F["vfov"]))
    hfov = 2 * math.degrees(math.atan(math.tan(math.radians(fov / 2)) * F["aspect"]))
    eye = float(pl.get("altura", EYE))
    lado = float(pl.get("lado", 0.0))
    ap = F["ap"] if efeitos.get("dof", True) else 0.0
    tm = t0 + T / 2
    if kind in ("fala", "medio", "reacao", "close"):
        if A is None:
            raise KeyError(f"plano {kind} precisa de 'quem' do elenco")
        yaw = float(A.at(np.array([t0]))[0, POSE["yaw"]]) + lado
        d = float(pl.get("dist", F["dist"][kind]))
        f = A.at(np.array([t0]))[0, :3]
        head = float(pl.get("mira", 1.55 if kind != "close" else 1.62))
        p0 = f + _fwd(yaw) * d + [0, eye, 0]
        p1 = f + _fwd(yaw) * (d - push * (0.6 if kind == "close" else 1.0)) + [0, eye, 0]
        aim = lambda t, A=A, head=head: _chest(A, t, head)
    elif kind == "dois":
        com = at.get(pl.get("com")) if pl.get("com") else next((x for k, x in at.items() if k != quem), None)
        if A is None or com is None:
            raise KeyError("plano dois precisa de 'quem' e 'com'")
        a0, b0 = A.at(np.array([t0]))[0, :3], com.at(np.array([t0]))[0, :3]
        c = (a0 + b0) / 2
        ya, yb = (float(x.at(np.array([t0]))[0, POSE["yaw"]]) for x in (A, com))
        dirv = _fwd(ya) + _fwd(yb)
        dirv = dirv / (np.linalg.norm(dirv) + 1e-9) if np.linalg.norm(dirv) > 0.3 else np.array([0, 0, 1.0])
        if lado:
            dirv = _fwd(math.degrees(math.atan2(-dirv[0], dirv[2])) + lado)
        sep = float(np.linalg.norm((a0 - b0)[[0, 2]]))
        d = float(pl.get("dist", max(F["dois_min"], (sep + 1.5) / (2 * math.tan(math.radians(hfov / 2))))))
        p0 = c + dirv * d + [0, eye - 0.05, 0]
        p1 = c + dirv * (d - push) + [0, eye - 0.05, 0]
        mh = float(pl.get("mira", 1.4))
        aim = lambda t, A=A, B=com, mh=mh: (_chest(A, t, mh) + _chest(B, t, mh)) / 2
    elif kind == "aberto":
        if pl.get("centro") is not None:
            c = _pt(sb, pl["centro"])
        else:
            c = np.mean([x.at(np.array([t0]))[0, :3] for x in at.values()], axis=0) if at else sb.feet(0, 0)
        d = float(pl.get("dist", F["aberto"]))
        dv = _fwd(lado)
        p0 = c + dv * d + np.array([0.3 * dv[2], pl.get("altura", 1.85), 0])
        p1 = c + dv * (d - push * 1.5) + np.array([0, pl.get("altura", 1.85), 0])
        mh = float(pl.get("mira", 1.2))
        aim = lambda t, c=c, mh=mh: np.repeat((c + [0, mh, 0])[None, :], np.size(t), 0)
    elif kind == "segue":
        if A is None:
            raise KeyError("plano segue precisa de 'quem'")
        def pos_at(t, A=A):
            q = A.at(np.atleast_1d(np.asarray(t, float)))
            fw = np.stack([_fwd(y) for y in q[:, POSE["yaw"]]])
            return q[:, :3] + fw * float(pl.get("dist", 3.0)) + [0, eye - 0.1, 0]
        n = 6
        pts = [tuple(pos_at(t0 + T * k / (n - 1))[0]) for k in range(n)]
        p0 = None
        aim = lambda t, A=A, mh=float(pl.get("mira", 1.4)): _chest(A, t, mh)
        mv = track(pts, lambda tau: aim(t0 + tau * T), T, ease="linear", fov=fov)
    elif kind == "insert" and "mob" in pl:                 # insert seguindo um mob (de frente para ele, na altura da cara dele)
        M = mobs[int(pl["mob"])]

        def mc(t, M=M):
            q = M.at(np.atleast_1d(np.asarray(t, float)))
            return q[:, :3] + [0, Mob.height(M.type) * 0.25, 0]
        dist = float(pl.get("dist", 2.6))
        n = 6
        pts = []
        for k in range(n):
            tk = t0 + T * k / (n - 1)
            q = M.at(np.array([tk]))[0]
            pts.append(tuple(mc(tk)[0] + _fwd(q[3]) * (dist - push * k / (n - 1))))
        p0, p1 = None, None
        aim = mc
        mv = track(pts, lambda tau: aim(t0 + tau * T), T, ease="linear", fov=fov)
        kind = "segue"
    elif kind == "insert":
        alvo = np.asarray(pl["alvo"], float)
        tgt = _pt(sb, alvo)
        dirv = _fwd(float(pl.get("de", 0.0)))
        up = np.array([0, float(pl.get("sobe", 0.0)), 0])
        p0 = tgt + dirv * float(pl.get("dist", 2.2)) + up
        p1 = tgt + dirv * (float(pl.get("dist", 2.2)) - push) + up
        aim = lambda t, tgt=tgt: np.repeat(tgt[None, :], np.size(t), 0)
    else:
        raise KeyError(f"plano desconhecido {kind!r} (fala medio reacao close dois aberto segue insert)")
    if kind != "segue":
        mv = track([tuple(p0), tuple(p1)], lambda tau, aim=aim: aim(t0 + tau * T), T, ease="smooth", fov=fov)
    if ap > 0:
        foc0 = float(np.linalg.norm(np.array(p0 if p0 is not None else pts[0]) - aim(t0)[0]))
        foc1 = float(np.linalg.norm(np.array(p1 if p0 is not None else pts[-1]) - aim(t0 + T)[0]))
        mv = mv.with_dof((max(foc0, 0.5), max(foc1, 0.5)), ap)
    rig.add(mv, cut=not first)


# ------------------------------------------------------------------------------------------------------------------- coreografia
class Cena:
    """O que a coreografia Python de uma ficha recebe (ficha["python"] = arquivo, ficha["coreografia"] = função, padrão
    "coreografia"): `def coreografia(c): ...` roda DEPOIS das ações da ficha e ANTES de assar os atores — dá para usar
    c.atores[nome] (Ator: pose/key/walk/jump...) e criar efeitos (c.prop, c.mob, choreo.explosion(c, ...), choreo.pop_block(c, c.sb, ...)).
    Depois de assar, c.built tem os Actors: funções de Prop podem chamar c.mao(nome, t) / c.cabeca(nome, t) (avaliadas na escrita)."""

    def __init__(self, sb, atores: Dict[str, Ator], T: float, ficha: Dict):
        self.sb, self.atores, self.T, self.ficha = sb, atores, T, ficha
        self.props: List = []
        self.mobs: List[Mob] = []
        self.built: Dict = {}
        self.scene_kw: Dict = {}            # ex.: {"blocks": [...]} (blocos que mudam no meio do plano)

    def pt(self, p) -> np.ndarray:
        return _pt(self.sb, p)

    def ponto(self, dx: float, dy: float, dz: float) -> np.ndarray:
        return _pt(self.sb, [dx, dy, dz])

    def prop(self, block: str, p, fn=None):
        from .actors import Prop
        pr = Prop("p%d" % len(self.props), block if ":" in block else "minecraft:" + block, np.asarray(p, float), fn=fn)
        self.props.append(pr)
        return pr

    def mob(self, tipo: str, dx: float, dz: float, dy: float = 0.0, vira: float = 0.0) -> Mob:
        tipo = "minecraft:" + tipo.replace("minecraft:", "")
        m = Mob.feet(f"mob{len(self.mobs)}c", tipo, _pt(self.sb, [dx, dy, dz]))
        m.key(0.0, yaw=float(vira))
        self.mobs.append(m)
        return m

    # compatível com cinecam.choreo (st.props / st.sb / st.mob / st.pos)
    def pos(self, nome: str, t: float) -> np.ndarray:
        if nome in self.built:
            return self.built[nome].at(np.array([float(t)]))[0, :3]
        return self.atores[nome].pos_at(float(t))

    def _parte(self, nome: str, t: float, parte: str, local) -> np.ndarray:
        from .colisao import boxes
        a = self.built[nome]
        row = a.at(np.array([float(t)]))[0]
        M = boxes(row, getattr(a, "slim", False), True)[parte][0]
        return (M @ np.array([*local, 1.0]))[:3]

    def mao(self, nome: str, t: float, esquerda: bool = False) -> np.ndarray:
        """Ponta da mão (mundo) no instante t — só depois de assar (dentro de fn de Prop)."""
        return self._parte(nome, t, "arm_loL" if esquerda else "arm_loR", ((0.5 if esquerda else -1.5), 10.0, 0.0))

    def cabeca(self, nome: str, t: float) -> np.ndarray:
        return self._parte(nome, t, "head", (0.0, -4.0, 0.0))


def _coreografia(ficha: Dict):
    if not ficha.get("python"):
        return None
    import importlib.util
    spec = importlib.util.spec_from_file_location("coreo_%s" % abs(hash(ficha["python"])), ficha["python"])
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return getattr(mod, ficha.get("coreografia", "coreografia"))


# ------------------------------------------------------------------------------------------------------------------- shot
def shot_da_ficha(mapa: Dict, ficha: Dict, qualidade: str = "final", nome: Optional[str] = None,
                  efeitos: Optional[Dict] = None) -> Tuple[Shot, Dict[str, Ator]]:
    """Ficha → Shot pronto para render/Sessao.  efeitos {"blur": bool, "dof": bool} (padrão: os da ficha, senão ligados)."""
    ef = {"blur": True, "dof": True, **(ficha.get("efeitos") or {}), **(efeitos or {})}
    F = formato(mapa, ficha)
    T = float(ficha["dur"])
    sb = montar_lugar(mapa, ficha["lugar"], F["palco"])
    elenco = _elenco(mapa, ficha, sb)
    _acoes(ficha, elenco, sb)
    cena = Cena(sb, elenco, T, ficha)
    fn = _coreografia(ficha)
    if fn:
        fn(cena)
    built = {k: v.build(T + 0.5) for k, v in elenco.items()}
    cena.built = built
    mobs = _mobs(ficha, sb) + cena.mobs
    rascunho = qualidade != "final"
    rig = Rig(fps=F["fps"], subframes=1 if rascunho else F["sub"], shutter=0.5)
    planos = ficha.get("camera") or [{"plano": "fala", "quem": next(iter(elenco))}]
    t = 0.0
    for i, pl in enumerate(planos):
        fim = min(T, float(pl.get("ate", T))) if i < len(planos) - 1 else T
        _plano(rig, pl, t, fim - t, built, sb, i == 0, ef if not rascunho else {**ef, "dof": False}, mobs, F)
        t = fim
    L = _lugar(mapa, ficha["lugar"])
    c = sb.feet(0, 0)
    scene = sb.scene(time=int(ficha.get("hora", L.get("hora", 4000))), weather=L.get("clima", "clear"), anchor=tuple(c + [0, 4, 2]),
                     **cena.scene_kw)
    nm = nome or f"curta_{ficha.get('video', 'x')}_{int(ficha.get('n', 0)):02d}"
    sh = Shot(nm, rig=rig, scene=scene, settings=Settings(renderDistance=int(L.get("visao", 10)), simulationDistance=6, worldTicks=True),
              anim=Anim(list(built.values()), mobs=mobs, props=cena.props), size=F["rascunho" if rascunho else "final"], grade="insert",
              blur=bool(ef["blur"]) and not rascunho, dof=(bool(ef["dof"]) and not rascunho))
    return sh, built


def stills_da_ficha(mapa: Dict, ficha: Dict, quando: Sequence[float] = (0.15, 0.5, 0.9), nome: Optional[str] = None) -> Shot:
    """Shot de stills (rascunho) nos instantes `quando` (fração da duração) — conferir o enquadramento antes do filme."""
    sh, _ = shot_da_ficha(mapa, ficha, "rascunho", nome=nome)
    rows = sh.rig.sample_frames()
    n = len(rows["t"])
    poses = []
    for u in quando:
        i = int(min(n - 1, round(u * (n - 1))))
        poses.append(dict(x=rows["x"][i], y=rows["y"][i], z=rows["z"][i], yaw=rows["yaw"][i], pitch=rows["pitch"][i],
                          roll=rows["roll"][i], fov=rows["fov"][i], t=float(rows["t"][i])))
    return Shot((nome or sh.name) + "_st", poses=poses, scene=sh.scene, settings=sh.settings, anim=sh.anim, size=sh.size)


def checar_ficha(mapa: Dict, ficha: Dict) -> List[str]:
    """Problemas da ficha SEM abrir o jogo: estrutura, colisão (corpo/personagem/bloco), trancos, rosto de frente.  Vazia = ok."""
    try:
        sh, built = shot_da_ficha(mapa, ficha, "rascunho")
    except Exception as e:
        return [f"ficha inválida: {e}"]
    out = list(checar_colisao(sh.anim, sh.rig, sh.scene))
    # câmera nunca dentro/colada em personagem ou mob (a lente atravessando o corpo aparece como uma faixa escura na borda)
    fr = sh.rig.sample_frames()
    for k in range(0, len(fr["t"]), 3):
        cam = np.array([fr["x"][k], fr["y"][k], fr["z"][k]]); tk = float(fr["t"][k])
        for nm, a in built.items():
            q = a.at(np.array([tk]))[0]
            dh = math.hypot(cam[0] - q[0], cam[2] - q[2])
            if dh < 0.75 and q[1] - 0.2 < cam[1] < q[1] + 2.2:
                out.append(f"{tk:.2f}s: câmera colada em {nm} ({dh:.2f} bl; mín. 0,75)")
                break
        for i, m in enumerate(sh.anim.mobs):
            q = m.at(np.array([tk]))[0]
            if q[6] > 0 and math.hypot(cam[0] - q[0], cam[2] - q[2]) < 0.9 and abs(cam[1] - q[1]) < 1.6:
                out.append(f"{tk:.2f}s: câmera colada no mob {i} ({m.type})")
    out = list(dict.fromkeys(out))
    for k, a in built.items():
        out += [f"{t:.2f}s: {k} tranco em {p} ({v} bl)" for (t, p, v) in snaps(a, float(ficha["dur"]))][:3]
    # de frente: em cada plano com 'quem', o corpo dele a ≤ 30° da lente no meio do plano
    rows = sh.rig.sample_frames()
    t = 0.0
    planos = ficha.get("camera") or []
    for i, pl in enumerate(planos):
        fim = min(float(ficha["dur"]), float(pl.get("ate", ficha["dur"]))) if i < len(planos) - 1 else float(ficha["dur"])
        q = pl.get("quem")
        if q in built and pl.get("plano") not in ("segue", "insert", "aberto"):
            tm = (t + fim) / 2
            k = int(min(len(rows["t"]) - 1, round(tm * formato(mapa, ficha)["fps"])))
            cam = np.array([rows["x"][k], rows["y"][k], rows["z"][k]])
            a = built[q].at(np.array([tm]))[0]
            v = cam - a[:3]
            ang = abs((math.degrees(math.atan2(-v[0], v[2])) - a[POSE["yaw"]] + 180) % 360 - 180)
            if ang > 30:
                out.append(f"plano {i + 1}: {q} a {ang:.0f}° da lente (máx. 30°: de frente)")
        t = fim
    return out


def render_fichas(mapa: Dict, fichas: Sequence[Dict], qualidade: str = "final", sessao=None, efeitos: Optional[Dict] = None,
                  log=print, ao_pronto=None) -> List[Dict]:
    """Renderiza as fichas numa sessão só do jogo (abre se não vier uma).  O pós de cada cena (DoF, encode) roda numa thread
    enquanto o jogo já faz a próxima.  ao_pronto(info) é chamado quando cada MP4 fica pronto (ex.: enviar para a nuvem)."""
    from concurrent.futures import ThreadPoolExecutor
    from .render import Sessao
    own = sessao is None
    s = sessao or Sessao(World(seed=int(mapa.get("seed_mundo", 4242))), log=log)
    res = {}

    def _fim(sh, info, f):
        info = Sessao.pos(sh, info)
        info["n"] = f.get("n")
        log(f"[curta] cena {f.get('n')}: {'ok' if info.get('ok') else info.get('error')}")
        if ao_pronto:
            try:
                ao_pronto(info)
            except Exception as e:
                log(f"[curta] ao_pronto falhou na cena {f.get('n')}: {e}")
        return info

    try:
        with ThreadPoolExecutor(2) as ex:
            futs = {}
            for f in fichas:
                try:
                    sh, _ = shot_da_ficha(mapa, f, qualidade, efeitos=efeitos)
                    info = s.render(sh, post=False)
                    futs[f.get("n")] = ex.submit(_fim, sh, info, f)
                except Exception as e:
                    res[f.get("n")] = {"name": f"cena {f.get('n')}", "ok": False, "error": str(e), "n": f.get("n")}
                    log(f"[curta] cena {f.get('n')}: {e}")
            for n, fu in futs.items():
                res[n] = fu.result()
    finally:
        if own:
            s.close()
    return [res.get(f.get("n")) for f in fichas]
