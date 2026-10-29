"""SHORTS no PC (v1.1, 26/10/2026): o serviço local renderiza no Minecraft deste PC (CineCam) as cenas de um vídeo do Shorts
EXATAMENTE como estão no estúdio, e manda cada uma para a linha do tempo assim que fica pronta.

Regra do dono (26/10): o Shorts continua sendo o sistema — fluxo, revisão e TODOS os controles (luz, hora, cor, filtros, skins por
cena, câmera, inserts…). O estúdio exporta o estado final de cada cena (CINE_EXPORT, site/index.html); aqui só se desenha.
Cor/filtros/brilho/legendas/inserts continuam no estúdio, por cima do vídeo.

Nuvem da equipe (servidor de sons, pelo porteiro com o TOKEN DE DISPOSITIVO deste PC — rota /nuvem/rev/img):
  <id>-cinexp          índice {n: assinatura, "mundo": assinatura}             ← o estúdio grava (navegador de quem edita)
  <id>-cinexp  & n     a cena n exportada (câmera, gente, skins, mobs, hora…)   ← o estúdio grava
  <id>-cinemundo       blocos do vídeo (mapa do vídeo ou o mundo da base perto da ação)
  <id>-mine    & n     MP4 cru 9:16 da cena n (≤ 5,6 MB, sem áudio)             → este PC grava
  <id>-mine            índice {n: versão}: a linha do tempo troca o 3D pelo vídeo (MINE_LINHA)
  <id>-cinest          estado deste PC {pc, ativo, ate, cenas: {n: {estado, erro|falta, s}}}  → o site mostra
A conta antiga dos sons grava no máximo 1000 chaves por dia: 3 gravações por cena pronta (MP4, índice, estado).
Uma sessão por vez; o jogo fica aberto entre as cenas (cinecam Sessao) e fecha 15 min depois da última mudança.

    python curtas.py <id>            # sessão manual (sem o site), para testar
"""
import json, os, socket, subprocess, sys, threading, time, urllib.error, urllib.parse, urllib.request

APP = os.path.dirname(os.path.abspath(__file__))
SK = os.path.dirname(APP)
sys.path.insert(0, os.path.join(SK, "scripts"))
import paths as P
import midia_sync as M

CINE_SCRIPTS = os.path.join(os.path.dirname(SK), "minecraft-cinematic", "scripts")
LIMITE_MP4 = int(5.6 * 2 ** 20)
OCIOSO_S = 15 * 60
_EST = {"id": None, "ativo": False, "cenas": {}, "log": [], "inicio": 0}
_LOCK = threading.Lock()
_PARAR = threading.Event()


# ------------------------------------------------------------------------------------------------------------ nuvem
def _nuvem(metodo, id_, n=None, corpo=None, tipo="application/json", timeout=60):
    q = "id=" + urllib.parse.quote(id_) + (f"&n={int(n)}" if n is not None else "") + f"&q={int(time.time() * 1000)}"
    h = {"user-agent": "EstudioProblemsLocal", "content-type": tipo}
    if M.token():
        h["authorization"] = "Bearer " + M.token()
    if isinstance(corpo, (dict, list)):
        corpo = json.dumps(corpo, ensure_ascii=False).encode("utf8")
    r = urllib.request.urlopen(urllib.request.Request(M.PORTEIRO + "/nuvem/rev/img?" + q, data=corpo, method=metodo, headers=h),
                               timeout=timeout)
    return r.read()


def _json(id_, n=None):
    try:
        return json.loads(_nuvem("GET", id_, n) or b"null")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def _log(m):
    print("[shorts]", m, flush=True)
    _EST["log"] = (_EST["log"] + [time.strftime("%H:%M:%S ") + m])[-80:]


def estado():
    with _LOCK:
        return {k: (dict(v) if isinstance(v, dict) else v) for k, v in _EST.items()}


def parar():
    _PARAR.set()


def _marca(n, **kw):
    with _LOCK:
        _EST["cenas"][n] = dict(kw, quando=int(time.time()))


# ------------------------------------------------------------------------------------------------------------ vídeo
def _cabe(src, dst):
    """MP4 da cena que cabe na nuvem (≤ 5,6 MB): H.264, sem áudio, faststart; CRF sobe até caber."""
    for crf in (18, 21, 24, 27, 30):
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", src, "-an", "-c:v", "libx264", "-preset", "medium", "-crf", str(crf),
                        "-pix_fmt", "yuv420p", "-movflags", "+faststart", dst], check=True)
        if os.path.getsize(dst) <= LIMITE_MP4:
            return True
    return False


class NuvemNoLimite(RuntimeError):
    """A conta antiga da nuvem (KV SONS) grava no máximo 1000 chaves por dia — a mesma da reserva da equipe, das cópias de
    segurança e das imagens de revisão.  Bateu no limite: a sessão para na hora (não insiste) e só volta depois das 21h."""


_PEND = {"mine": {}, "feito": {}, "mundo": None, "quando": 0.0}          # índice do vídeo esperando para subir (agrupado)


def _put(*a, **kw):
    try:
        return _nuvem("PUT", *a, **kw)
    except urllib.error.HTTPError as e:
        corpo = e.read()[:300].decode("utf8", "replace") if e.code == 500 else ""
        if "limit exceeded" in corpo:
            raise NuvemNoLimite("nuvem no limite de gravações do dia (volta às 21h)") from e
        raise


def _enviar(vid, n, mp4):
    tmp = mp4.replace(".mp4", "_nuvem.mp4")
    if not _cabe(mp4, tmp):
        raise RuntimeError("cena grande demais para a nuvem mesmo comprimida")
    _put(vid + "-mine", n, open(tmp, "rb").read(), "video/mp4", timeout=180)
    with _LOCK:
        _PEND["mine"][str(n)] = int(time.time() * 1000)


def _subir_indice(vid, ja=False):
    """Índice do vídeo (a linha do tempo troca o 3D pelo vídeo) + estado: juntos, no máximo a cada 45 s — 2 gravações por
    leva em vez de 2 por cena."""
    with _LOCK:
        if not ja and time.time() - _PEND["quando"] < 45:
            return
        novos = dict(_PEND["mine"]); _PEND["mine"].clear(); _PEND["quando"] = time.time()
        feito = dict(_PEND["feito"]); _PEND["feito"].clear(); mundo_h = _PEND["mundo"]
    if novos:
        ix = _json(vid + "-mine") or {}
        ix.update(novos)
        _put(vid + "-mine", None, ix)
    if feito and mundo_h:                             # 29/10: o que já foi feito (assinatura de cada cena), para a próxima vez
        fz = _json(vid + "-cinefeito") or {}
        if fz.get("mundo") != mundo_h:
            fz = {"mundo": mundo_h, "cenas": {}}
        fz.setdefault("cenas", {}).update(feito)
        _put(vid + "-cinefeito", None, fz)
    _publicar_estado(vid)


def _publicar_estado(vid):
    with _LOCK:
        st = {"pc": socket.gethostname(), "ate": int((time.time() + OCIOSO_S) * 1000), "ativo": _EST["ativo"],
              "cenas": {str(k): v for k, v in _EST["cenas"].items()}}
    try:
        _put(vid + "-cinest", None, st)
    except NuvemNoLimite:
        raise
    except Exception as e:
        _log(f"estado não subiu: {e}")


# ------------------------------------------------------------------------------------------------------------ sessão
def sessao(vid, efeitos=None, qualidade="final"):
    """Segue o índice das cenas exportadas pelo estúdio e renderiza as que mudaram, até 15 min sem nada novo."""
    if CINE_SCRIPTS not in sys.path:
        sys.path.insert(0, CINE_SCRIPTS)
    from cinecam.estudio import shot_da_cena
    from cinecam.render import Sessao, World
    from concurrent.futures import ThreadPoolExecutor
    ef = {"blur": True, "dof": False, **(efeitos or {})}
    with _LOCK:
        if _EST["ativo"]:
            raise RuntimeError(f"já tem uma sessão de Shorts rodando ({_EST['id']})")
        _EST.update(id=vid, ativo=True, cenas={}, inicio=time.time())
    _PARAR.clear()
    pasta = os.path.join(P.cache_dir(), "shorts", vid)
    os.makedirs(pasta, exist_ok=True)
    feitos, mundo, mundo_h = {}, None, None
    ultimo = time.time()
    s = Sessao(World(seed=4242, preset="flat", groundY=64), log=_log)   # chão em todo lugar, na altura do estúdio
    try:
        while not _PARAR.is_set():
            ix = _json(vid + "-cinexp") or {}
            if ix.get("mundo") and ix["mundo"] != mundo_h:
                mundo = _json(vid + "-cinemundo")
                mundo_h = ix["mundo"]
                _PEND["mundo"] = mundo_h
                # 29/10 (dono: "pra que regerar tudo se 35 das 39 estão certas?"): começa do que já foi feito numa vez anterior
                # com o MESMO mundo — só entra na fila cena cuja assinatura mudou no estúdio (ou que deu erro / nunca foi feita)
                fz = _json(vid + "-cinefeito") or {}
                feitos = {int(k): v for k, v in (fz.get("cenas") or {}).items()} if fz.get("mundo") == mundo_h else {}
                _log(f"mundo do vídeo: {(mundo or {}).get('fonte')} ({len((mundo or {}).get('blocos') or [])} blocos)")
            pend = sorted(int(n) for n, h in ix.items() if n.isdigit() and feitos.get(int(n)) != h)
            if not pend:
                if time.time() - ultimo > OCIOSO_S:
                    _log(f"{OCIOSO_S // 60} min sem cena nova: fechando")
                    break
                _PARAR.wait(4)
                continue
            with ThreadPoolExecutor(2) as ex:
                futs = []
                for n in pend:
                    if _PARAR.is_set():
                        break
                    ix2 = _json(vid + "-cinexp") or {}            # mundo trocou no meio da leva: volta e recomeça com o novo
                    if ix2.get("mundo") and ix2["mundo"] != mundo_h:
                        break
                    h = ix[str(n)]
                    X = _json(vid + "-cinexp", n)
                    feitos[n] = h
                    if not X:
                        continue
                    try:
                        sh, falta = shot_da_cena(X, mundo, ef, os.path.join(pasta, "skins"), qualidade, nome=f"est_{vid}_{n:02d}")
                    except Exception as e:
                        _marca(n, estado="erro", erro=f"conversão: {e}"[:500]); continue
                    if falta:                                 # o Minecraft ainda não desenha algo desta cena: fica no 3D do estúdio
                        _marca(n, estado="3d", falta=falta[:6]); _log(f"cena {n} fica no 3D: {falta[:3]}")
                        with _LOCK: _PEND["feito"][str(n)] = h
                        continue
                    _marca(n, estado="renderizando")
                    t0 = time.time()
                    try:
                        info = s.render(sh, post=False)
                    except Exception as e:
                        info = {"ok": False, "error": str(e)}
                    futs.append(ex.submit(_terminar, vid, n, sh, info, t0, h))
                for f in futs:
                    f.result()
            _subir_indice(vid, ja=True)
            ultimo = time.time()
    except NuvemNoLimite as e:
        _log(str(e))
    finally:
        s.close()
        with _LOCK:
            _EST["ativo"] = False
        try:
            _subir_indice(vid, ja=True)
        except NuvemNoLimite:
            pass
        _log("sessão encerrada")


def _terminar(vid, n, sh, info, t0, h=None):
    from cinecam.render import Sessao
    info = Sessao.pos(sh, info)
    if info.get("ok"):
        try:
            _enviar(vid, n, info["final"])
            _marca(n, estado="pronto", s=round(time.time() - t0, 1))
            if h:
                with _LOCK: _PEND["feito"][str(n)] = h
            _log(f"cena {n} pronta em {time.time() - t0:.0f} s")
        except NuvemNoLimite:
            _PARAR.set()
            raise
        except Exception as e:
            _marca(n, estado="erro", erro=f"envio: {e}"[:500]); _log(f"cena {n}: envio falhou: {e}")
    else:
        err = str(info.get("error"))
        _marca(n, estado="3d" if err.startswith("colisão") else "erro", erro=err[:500])
        if h and err.startswith("colisão"):         # recusa de qualidade é sempre a mesma: não refaz à toa (erro de verdade refaz)
            with _LOCK: _PEND["feito"][str(n)] = h
        _log(f"cena {n}: {err[:200]}")
    _subir_indice(vid)


def iniciar(vid, efeitos=None):
    """Começa a sessão numa thread (o servidor responde na hora)."""
    if not M.token():
        raise RuntimeError("este PC ainda não está pareado com o Estúdio (abra o serviço pelo site uma vez)")
    t = threading.Thread(target=sessao, args=(vid, efeitos), daemon=True)
    t.start()
    return t


if __name__ == "__main__":
    sessao(sys.argv[1])
