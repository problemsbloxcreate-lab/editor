"""turma: the Problems channel cast -> skin PNGs, plus a labelled front-view sheet to recognise who is on screen.

    from cinecam.turma import skin, cast_sheet, TURMA
    Actor("stick", skin("stick"), pos)            # aliases: "chico", "o stick"...
    cast_sheet("D:/x/turma.png")                  # front views of every skin of 0.Turma (+ helpers) with names

Skins root (first that exists): env CINECAM_SKINS -> the Modrinth profile the Matheus keeps up to date
("Template Forge 09.26/config/bbs/assets/models/skins") -> the copy shipped in the skill (assets/skins).
Main cast lives in <root>/0.Turma (Windows: case-insensitive "0.turma").
"""
from __future__ import annotations

import os
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional

_SKILL = Path(__file__).resolve().parents[2]
_CANDIDATES = [os.environ.get("CINECAM_SKINS") or "",
               str(Path.home() / "AppData/Roaming/ModrinthApp/profiles/Template Forge 09.26/config/bbs/assets/models/skins"),
               str(_SKILL / "assets" / "skins")]


def skins_root() -> Path:
    for c in _CANDIDATES:
        if c and (Path(c) / "0.Turma").is_dir():
            return Path(c)
    raise FileNotFoundError("skins folder not found (set CINECAM_SKINS); tried: " + "; ".join(c for c in _CANDIDATES if c))


# key -> (file relative to 0.Turma, display name, aliases, what to look for on screen)
TURMA: Dict[str, tuple] = {
    "problems": ("Problems0.png", "Problems", ["problems", "prob", "bob", "eu"], "boneco todo CIANO (azul-piscina), rosto simples"),
    "stick": ("O_Stick.png", "Stick", ["stick", "o stick", "chico", "chique", "xico"], "cabeça VERDE com faixa branca, jaqueta marrom, mãos/pés verdes"),
    "patao": ("ajudantes/cariocapato.png", "Patão", ["patao", "patão", "pato", "carioca"], "pato: cabeça azul com bico laranja, camisa listrada vermelho/preto, braços azuis"),
    "brucutu": ("brucutu.png", "Brucutu", ["brucutu"], "careca musculoso SEM camisa, shorts azul, faixas verdes nos pulsos"),
    "mamae": ("Mamae_Problems.png", "Mamãe Problems", ["mamae", "mamãe", "mae", "mãe"], "ciano como o Problems, com cabelo comprido azul-claro"),
    "mel": ("Mel_player.png", "Mel", ["mel"], "cabeça amarela com óculos, camisa laranja florida"),
    "melzinha": ("Melzinha.png", "Melzinha", ["melzinha"], "toda MAGENTA/rosa lisa"),
    "melxicano": ("Melxicano.png", "Melxicano", ["melxicano"], "amarelo com sombreiro e poncho colorido"),
    "zoom": ("ZOOM.png", "Zoom", ["zoom"], "robô de armadura LARANJA com visor cinza e luzes no peito"),
    "zoom_rosto": ("ZoomRosto.png", "Zoom (rosto)", ["zoom rosto"], "igual ao Zoom (armadura laranja)"),
    "zoom_sem_armadura": ("zoomsemarmadura.png", "Zoom sem armadura", ["zoom sem armadura"], "todo PRETO com olhos/boca brancos"),
    "kadu": ("kadu2.png", "Kadu", ["kadu"], "cabeça VERMELHA, terno escuro, gravata vermelha"),
    "eugene": ("eugene.png", "Eugene", ["eugene"], "cabeça de monitor/TV cinza, moletom laranja"),
    "propolis": ("propolis.png", "Própolis", ["propolis", "própolis"], "todo AMARELO liso"),
    "zegalo": ("zegalo.png", "Zé Galo", ["ze galo", "zé galo", "zegalo", "galo"], "galo (cabeça de galo) com jaleco claro"),
    "matteeoo": ("ajudantes/matteoo HD.png", "Matteeoo", ["matteeoo", "matteoo", "mateo"], "marrom com chapéu (skin HD)"),
    "miauzinha": ("ajudantes/Miauzinha.png", "Miauzinha", ["miauzinha", "gata"], "Miauzinha"),
    "carlao": ("ajudantes/carlao-figueiredo.png", "Carlão Figueiredo", ["carlao", "carlão"], "Carlão"),
    "jujuba": ("ajudantes/jujuba.png", "Jujuba", ["jujuba"], "Jujuba"),
    "nissan": ("ajudantes/nissan.png", "Nissan", ["nissan"], "Nissan"),
    "noobzinho": ("ajudantes/noobzinho.png", "Noobzinho", ["noob", "noobzinho"], "noob"),
    "ovelhex": ("ajudantes/ovelhex.png", "Ovelhex", ["ovelhex", "ovelha"], "todo preto"),
    "sad": ("ajudantes/sadhd.png", "Sad", ["sad"], "azul-escuro com detalhes lilás"),
}


def _norm(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s.lower().strip()) if unicodedata.category(c) != "Mn")


def skin(who: str) -> str:
    """Path of a cast member's skin by key/alias, or any PNG path/name under the skins root (e.g. 'Kadu Luigi')."""
    if os.path.isfile(who):
        return who
    n = _norm(who)
    root = skins_root()
    for k, (f, name, aliases, _) in TURMA.items():
        if n == k or n == _norm(name) or n in (_norm(a) for a in aliases):
            p = root / "0.Turma" / f
            if p.exists():
                return str(p).replace("\\", "/")
    hits = [p for p in root.rglob("*.png") if _norm(p.stem) == n]
    if hits:
        return str(hits[0]).replace("\\", "/")
    raise KeyError(f"skin '{who}' not found under {root}")


def front_view(png: str, scale: int = 8):
    """Flat front view (16x32 px * scale) of a 64x64 or legacy 64x32 skin, overlays applied."""
    from PIL import Image
    im = Image.open(png).convert("RGBA")
    if im.width > 64:                                                         # HD skins (128 px): same layout, scaled
        im = im.resize((64, im.height * 64 // im.width), Image.NEAREST)
    legacy = im.height == 32
    out = Image.new("RGBA", (16, 32), (0, 0, 0, 0))

    def put(box, at, ovl=None, flip=False):
        part = im.crop(box)
        if ovl and not legacy:
            o = im.crop(ovl)
            part = Image.alpha_composite(part, o)
        if flip:
            part = part.transpose(Image.FLIP_LEFT_RIGHT)
        out.alpha_composite(part, at)

    put((8, 8, 16, 16), (4, 0))
    out.alpha_composite(im.crop((40, 8, 48, 16)), (4, 0))                   # hat layer exists in both formats
    put((20, 20, 28, 32), (4, 8), (20, 36, 28, 48))
    put((44, 20, 48, 32), (0, 8), (44, 36, 48, 48))                          # right arm (viewer's left)
    if legacy:
        put((44, 20, 48, 32), (12, 8), flip=True); put((4, 20, 8, 32), (8, 20), flip=True)
    else:
        put((36, 52, 40, 64), (12, 8), (52, 52, 56, 64))
        put((20, 52, 24, 64), (8, 20), (4, 52, 8, 64))
    put((4, 20, 8, 32), (4, 20), (4, 36, 8, 48))
    return out.resize((16 * scale, 32 * scale), Image.NEAREST)


def cast_sheet(out_png: str, keys: Optional[List[str]] = None, scale: int = 6) -> str:
    """Labelled sheet of front views (default: the whole TURMA) — open it next to a gameplay frame to tell who is who."""
    from PIL import Image, ImageDraw, ImageFont
    keys = keys or list(TURMA)
    root = skins_root()
    cells = []
    for k in keys:
        p = root / "0.Turma" / TURMA[k][0]
        if p.exists():
            cells.append((k, front_view(str(p), scale)))
    cw, ch, cols = 16 * scale + 40, 32 * scale + 34, 8
    rows = (len(cells) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cw, rows * ch), (40, 44, 52))
    d = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("arial.ttf", 15)
    except OSError:
        font = ImageFont.load_default()
    for i, (k, im) in enumerate(cells):
        x, y = (i % cols) * cw, (i // cols) * ch
        sheet.paste(im, (x + 20, y + 4), im)
        d.text((x + 6, y + 32 * scale + 10), k, fill=(255, 255, 255), font=font)
    Path(out_png).parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_png)
    return out_png
