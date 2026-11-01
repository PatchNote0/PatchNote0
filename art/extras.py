"""The smaller pieces: nameplates, a pixel avatar, the footer wordmark and a share board.

    python art/extras.py   ->  assets/plate-*.png, pixel-avatar.png, wordmark.png, share-board.png
"""
from __future__ import annotations

import math
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import px  # noqa: E402
import rack  # noqa: E402
from fonts import WORDMARK  # noqa: E402
from px import Canvas  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
CRIMSON = rack.FINISH["crimson"]


def big_text(cv, x, y, s, colour, font, k):
    """Draw bitmap text with every font pixel as a k x k block."""
    cx = x
    for ch in s:
        g = font[ch]
        for j, row in enumerate(g):
            for i, b in enumerate(row):
                if b == "#":
                    cv.rect(cx + i * k, y + j * k, k, k, colour)
        cx += (len(g[0]) + 1) * k
    return cx - x - k


def text_w(s, font, k):
    return (sum(len(font[c][0]) + 1 for c in s) - 1) * k


def avatar():
    """P/N on the crimson panel, with the voice module's amber trace beneath it."""
    n = 56
    cv = Canvas(n, n, CRIMSON["base"])
    k = 2
    w = text_w("P/N", WORDMARK, k)
    x = (n - w) // 2
    y = 12
    # a one pixel shadow under the letters, as if printed on the panel
    big_text(cv, x + 1, y + 1, "P/N", CRIMSON["dark"], WORDMARK, k)
    big_text(cv, x, y, "P/N", CRIMSON["print"], WORDMARK, k)
    # one cycle and a half of the scope trace
    prev = None
    for i in range(8, n - 8):
        t = (i - 8) / (n - 16)
        yy = 42 - round(4 * math.sin(t * 3 * math.pi))
        if prev is not None:
            for v in range(min(prev, yy), max(prev, yy) + 1):
                cv.put(i, v, "#ffc565")
        cv.put(i, yy, "#ffc565")
        prev = yy
    out = cv.scaled(9)
    out.save(os.path.join(ASSETS, "pixel-avatar.png"), optimize=True)


def wordmark():
    """PATCHNOTE in the wordmark face, crimson on transparent, for the footer."""
    k = 1
    w = text_w("PATCHNOTE", WORDMARK, k)
    img = Image.new("RGBA", (w, 9), (0, 0, 0, 0))
    cx = 0
    for ch in "PATCHNOTE":
        g = WORDMARK[ch]
        for j, row in enumerate(g):
            for i, b in enumerate(row):
                if b == "#":
                    img.putpixel((cx + i, j), (208, 40, 63, 255))
        cx += len(g[0]) + 1
    img.resize((w * 8, 9 * 8), Image.NEAREST).save(os.path.join(ASSETS, "wordmark.png"), optimize=True)


def share_board():
    """1280 x 640: the whole rack as the lead tile and three calm type tiles under it."""
    s = 3
    cw, ch = 1280 // s, 640 // s  # 426 x 213 art pixels
    cv = Canvas(cw, ch, "#0b0a0e")
    frames = rack.render_frames_for_still()
    hero = frames[rack.STILL_FRAME]
    gx = (cw - rack.W) // 2
    cv.img.paste(hero, (gx, 3))
    top = 3 + rack.H + 3
    tile_h = ch - top - 3
    gap = 3
    tile_w = (rack.W - 2 * gap) // 3
    tiles = [
        ("crimson", "SOFTWARE, INTERFACES", "AND VISUAL SYSTEMS"),
        ("ink", None, None),
        ("bone", "PATCHNOTE.TOP", "GITHUB.COM/PATCHNOTE0"),
    ]
    for i, (fin, a, b) in enumerate(tiles):
        f = rack.FINISH[fin]
        x = gx + i * (tile_w + gap)
        cv.rect(x, top, tile_w, tile_h, f["base"])
        cv.hline(x, top, tile_w, f["light"])
        cv.hline(x, top + tile_h - 1, tile_w, f["dark"])
        if fin == "ink":
            line1 = "نرم‌افزار، رابط کاربری"
            line2 = "و سیستم‌های بصری"
            cv.fa_text(x + tile_w - 8, top + 8, line1, f["print"], size=12, weight=600, align="right")
            cv.fa_text(x + tile_w - 8, top + 25, line2, f["print"], size=12, weight=600, align="right")
        elif fin == "crimson":
            cv.text(x + 8, top + 11, a, f["print"], font=px.TITLE)
            cv.text(x + 8, top + 23, b, f["print"], font=px.TITLE)
        else:
            cv.text(x + 8, top + 11, a, f["print"], font=px.TITLE)
            cv.text(x + 8, top + 25, b, f["dim"], font=px.SMALL)
    out = Image.new("RGB", (1280, 640), (11, 10, 14))
    out.paste(cv.scaled(s), (1, 0))
    out.save(os.path.join(ASSETS, "share-board.png"), optimize=True)


PLATES = [
    # file, finish, English name, Persian name, use the wordmark face
    ("dastyar", "ink", "DASTYAR MOSHAVER", "دستیار مشاور", False),
    ("budget", "alu", "BUDGET FLOW", None, False),
    ("shora", "bone", "SHORA ARCHIVE", "شورا", False),
    ("patchnote", "crimson", "PATCHNOTE", None, True),
]
PLATE_H = 17


def nameplate(slug, finish, name, name_fa, wordmark_face):
    """A strip cut from the module's own panel: its finish, two screws and its name
    in the same lettering it carries in the rack."""
    f = rack.FINISH[finish]
    pad = 13
    tw = px.text_width(name, WORDMARK if wordmark_face else px.SMALL)
    fa_w = px.fa_mask(name_fa, 11, 600)[0].width if name_fa else 0
    inner = tw + (10 + fa_w if name_fa else 0)
    w = inner + 2 * pad
    cv = Canvas(w, PLATE_H, f["base"])
    cv.hline(0, 0, w, f["light"])
    cv.vline(0, 0, PLATE_H, f["light"])
    cv.hline(0, PLATE_H - 1, w, f["dark"])
    cv.vline(w - 1, 0, PLATE_H, f["dark"])
    px.screw(cv, 3, (PLATE_H - 5) // 2, "d")
    px.screw(cv, w - 8, (PLATE_H - 5) // 2, "h")
    if wordmark_face:
        cv.text(pad, 4, name, f["print"], font=WORDMARK)
    else:
        cv.text(pad, 6, name, f["print"])
    if name_fa:
        mask, _ = px.fa_mask(name_fa, 11, 600)
        cv.fa_text(w - pad, (PLATE_H - mask.height) // 2, name_fa, f["print"], size=11, weight=600, align="right")
    cv.scaled(4).save(os.path.join(ASSETS, f"plate-{slug}.png"), optimize=True)
    return w


if __name__ == "__main__":
    os.makedirs(ASSETS, exist_ok=True)
    for plate in PLATES:
        nameplate(*plate)
    avatar()
    wordmark()
    share_board()
    print("wrote the nameplates, pixel-avatar.png, wordmark.png and share-board.png")
