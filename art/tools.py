"""The tools I work with, as a patch bay: one small pixel logo for each.

Every logo is drawn by hand on the same 17 x 17 grid, in the rack's colour
ramps, and lit from the top left like the rest of the rack. Languages sit in
the first row, then the web, the stack and the tools.

    python art/tools.py   ->  assets/tools.png and assets/tools-compact.png
"""
from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import px  # noqa: E402
import rack  # noqa: E402
from fonts import SMALL, TITLE  # noqa: E402
from px import Canvas  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
PANEL = rack.FINISH["black"]
N = 17  # every logo fits this square

# Colour ramps: (light, mid, dark). Six come straight from the rack's cables
# and panels; the rest are matched to them in strength.
RAMP = {
    "blue": ("#9cbcff", "#3f72d9", "#22428c"),
    "steel": ("#c9d6ea", "#8ea3c8", "#5d7096"),
    "violet": ("#c9a6f2", "#8b55d6", "#56308f"),
    "blurple": ("#a9b0ff", "#5a64e6", "#363c9e"),
    "amber": ("#ffd88a", "#f2a224", "#a9620c"),
    "yellow": ("#fff0a3", "#f0cf38", "#b09018"),
    "orange": ("#ffa27a", "#e8572d", "#9e3216"),
    "crimson": ("#ff7385", "#d9283f", "#8f1428"),
    "green": ("#93e3a6", "#3daa5c", "#21703a"),
    "cyan": ("#a6e4ff", "#2fa6e6", "#1a6a99"),
    "coral": ("#ffb0a6", "#f26b5c", "#a8392d"),
    "bone": ("#ffffff", "#e8e2d4", "#b0a792"),
    "alu": ("#f1f2f4", "#c4c7cc", "#8a8e96"),
}
WHITE = "#f7f0e5"
HOLE = PANEL["base"]


# -----------------------------------------------------------------------------
# Shapes: each returns a set of (x, y) inside the 17 x 17 square.
# -----------------------------------------------------------------------------

def rows_mask(spans):
    """spans: {y: (x0, x1)} inclusive, or {y: [(x0, x1), ...]}."""
    out = set()
    for y, s in spans.items():
        for x0, x1 in (s if isinstance(s, list) else [s]):
            out.update((x, y) for x in range(x0, x1 + 1))
    return out


def centred(half_widths, top=0, cx=8):
    return rows_mask({top + j: (cx - hw, cx + hw) for j, hw in enumerate(half_widths) if hw >= 0})


def hexagon():
    """Pointy-top hexagon, 15 wide and 17 tall: close to regular."""
    return centred([1, 3, 5, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 5, 3, 1])


def shield():
    return centred([6] * 12 + [5, 4, 2], top=1)


def square():
    return rows_mask({y: (1, 15) for y in range(1, 16)})


def diamond():
    pts = {(x, y) for y in range(N) for x in range(N) if abs(x - 8) + abs(y - 8) <= 7}
    return pts - {(8, 1), (8, 15), (1, 8), (15, 8)}


def disc(cx, cy, r):
    return {(x, y) for y in range(N) for x in range(N) if (x - cx) ** 2 + (y - cy) ** 2 <= r * r + r * 0.6}


def glyph(font, ch, x, y):
    return {(x + i, y + j) for j, row in enumerate(font[ch]) for i, b in enumerate(row) if b == "#"}


def word(font, s, x, y):
    out, cx = set(), x
    for ch in s:
        out |= glyph(font, ch, cx, y)
        cx += len(font[ch][0]) + 1
    return out


def sprite(rows, ch="#"):
    return {(i, j) for j, row in enumerate(rows) for i, c in enumerate(row) if c == ch}


# -----------------------------------------------------------------------------
# The logos: a list of parts (mask, ramp) plus marks drawn flat on top.
# -----------------------------------------------------------------------------

def c_family(suffix, ramp):
    body = hexagon()
    c = glyph(TITLE, "C", 0, 0)
    if suffix == "":
        marks = {(x + 6, y + 5) for x, y in c}
    elif suffix == "++":
        marks = {(x + 2, y + 5) for x, y in c}
        marks |= glyph(SMALL, "+", 8, 7) | glyph(SMALL, "+", 12, 7)
    else:
        marks = {(x + 3, y + 5) for x, y in c} | glyph(SHARP, "#", 9, 6)
    return [(body, ramp)], [(marks, WHITE)]


SHARP = {"#": [".#.#.", "#####", ".#.#.", "#####", ".#.#."]}


def rust():
    """A gear with eight square teeth and the R cut through it."""
    gear = set()
    for y in range(N):
        for x in range(N):
            d = math.hypot(x - 8, y - 8)
            a = math.degrees(math.atan2(y - 8, x - 8)) % 45
            if d <= 6.3 or (d <= 8.4 and min(a, 45 - a) <= 11):
                gear.add((x, y))
    r_letter = {(x + 6, y + 5) for x, y in glyph(TITLE, "R", 0, 0)}
    return [(gear, "bone")], [(r_letter, HOLE)]


PY_BLUE = [
    ".................",
    "......#####......",
    ".....######......",
    ".....######......",
    "........###......",
    "..#########......",
    ".##########......",
    ".#########.......",
    ".####............",
    ".####............",
    "..###............",
]


def python():
    blue = sprite(PY_BLUE)
    yellow = {(16 - x, 16 - y) for x, y in blue}
    eyes = {(6, 2), (10, 14)}
    return [(blue, "blue"), (yellow, "yellow")], [(eyes, WHITE)]


def js():
    return [(square(), "yellow")], [(word(SMALL, "JS", 5, 9), "#1d1c22")]


def ts():
    return [(square(), "blue")], [(word(SMALL, "TS", 6, 9), WHITE)]


def html():
    return [(shield(), "orange")], [(glyph(TITLE, "5", 6, 3), WHITE)]


def css():
    return [(shield(), "blue")], [(glyph(TITLE, "3", 6, 3), WHITE)]


def node():
    """The hexagon from the Node.js mark, with JS inside it."""
    outer = hexagon()
    inner = centred([-1, -1, 1, 3, 5, 5, 5, 5, 5, 5, 5, 5, 5, 3, 1, -1, -1])
    return [(outer - inner, "green")], [(word(SMALL, "JS", 4, 6), "#93e3a6")]


CLYDE = [
    ".................",
    ".................",
    "...###.....###...",
    "..#############..",
    ".###############.",
    ".###############.",
    "#################",
    "####..#####..####",
    "####..#####..####",
    "####..#####..####",
    "#################",
    "#################",
    ".#####.....#####.",
    "..###.......###..",
]


def discord_js():
    body = sprite(CLYDE)
    eyes = {(x, y) for x in (4, 5, 11, 12) for y in (7, 8, 9)}
    return [(body - eyes, "blurple")], []


def sql():
    body = rows_mask({2: (5, 11), 3: (3, 13), **{y: (3, 13) for y in range(4, 15)}, 15: (5, 11)})
    rims = set()
    for y0 in (4, 8, 12):
        rims |= {(3, y0), (13, y0)} | {(x, y0 + 1) for x in range(4, 13)}
    return [(body, "alu")], [(rims, "#8a8e96")]


def git():
    body = diamond()
    w = set()
    w |= {(7, y) for y in range(5, 12)}
    w |= {(x, y) for x in (6, 7, 8) for y in (11, 12, 13)} - {(6, 11), (8, 11), (6, 13), (8, 13)}
    w |= {(x, y) for x in (6, 7, 8) for y in (3, 4, 5)} - {(6, 3), (8, 3), (6, 5), (8, 5)}
    w |= {(8, 6), (9, 7), (10, 8)}
    w |= {(x, y) for x in (10, 11, 12) for y in (8, 9, 10)} - {(10, 8), (12, 8), (10, 10), (12, 10)}
    w |= {(5, 2), (4, 1)} & body
    return [(body, "orange")], [(w, WHITE)]


def figma():
    def cell(x0, y0, cut):
        pts = {(x, y) for x in range(x0, x0 + 5) for y in range(y0, y0 + 5)}
        return pts - cut
    tl = cell(4, 1, {(4, 1), (4, 5)})
    tr = cell(9, 1, {(13, 1), (13, 5)})
    ml = cell(4, 6, {(4, 6), (4, 10)})
    mr = cell(9, 6, {(9, 6), (13, 6), (9, 10), (13, 10)})
    bl = cell(4, 11, {(4, 11), (4, 15), (8, 15)})
    return [(tl, "crimson"), (tr, "coral"), (ml, "violet"), (mr, "cyan"), (bl, "green")], []


TOOLS = [
    # (label, logo) in reading order: languages first, then web, stack and tools
    [("C", lambda: c_family("", "steel")),
     ("C++", lambda: c_family("++", "blue")),
     ("C#", lambda: c_family("#", "violet")),
     ("RUST", rust),
     ("PYTHON", python),
     ("JAVASCRIPT", js),
     ("TYPESCRIPT", ts)],
    [("HTML", html),
     ("CSS", css),
     ("NODE.JS", node),
     ("DISCORD.JS", discord_js),
     ("SQL", sql),
     ("GIT", git),
     ("FIGMA", figma)],
]

LABEL_FONT = dict(SMALL, **SHARP)


def draw_logo(cv, x, y, logo):
    """Lit from the top left: an edge facing up or left is light, one facing
    down or right is dark, the inside is the middle tone."""
    parts, marks = logo()
    for mask, ramp in parts:
        light, mid, dark = RAMP[ramp]
        for (i, j) in mask:
            if (i - 1, j) not in mask or (i, j - 1) not in mask:
                c = light
            elif (i + 1, j) not in mask or (i, j + 1) not in mask:
                c = dark
            else:
                c = mid
            cv.put(x + i, y + j, c)
    for mask, colour in marks:
        for (i, j) in mask:
            cv.put(x + i, y + j, colour)


def panel(w, h):
    cv = Canvas(w, h, PANEL["base"])
    cv.hline(0, 0, w, PANEL["light"])
    cv.vline(0, 0, h, PANEL["light"])
    cv.hline(0, h - 1, w, PANEL["dark"])
    cv.vline(w - 1, 0, h, PANEL["dark"])
    for k, (sx, sy) in enumerate([(4, 3), (w - 9, 3), (4, h - 8), (w - 9, h - 8)]):
        px.screw(cv, sx, sy, ["d", "h", "v", "d"][k])
    return cv


def wide():
    """Two rows of seven, each logo over its name. 420 wide, like the rack."""
    w, margin, top = rack.W, 14, 9
    cell = (w - 2 * margin) // 7
    row_h = N + 4 + 5
    gap = 10
    h = top + 2 * row_h + gap + top - 1
    cv = panel(w, h)
    for r, row in enumerate(TOOLS):
        y = top + r * (row_h + gap)
        for c, (name, logo) in enumerate(row):
            cx = margin + c * cell + cell // 2
            draw_logo(cv, cx - N // 2, y, logo)
            cv.text(cx, y + N + 4, name, PANEL["print"], font=LABEL_FONT, align="center")
    return cv


def compact():
    """For phones: the two rows become two columns, each logo beside its name."""
    w, margin, top = 176, 8, 9
    col = (w - 2 * margin) // 2
    pitch = N + 6
    h = top + 7 * pitch - 6 + top
    cv = panel(w, h)
    for c, row in enumerate(TOOLS):
        x = margin + c * col + 4
        for r, (name, logo) in enumerate(row):
            y = top + r * pitch
            draw_logo(cv, x, y, logo)
            cv.text(x + N + 5, y + 6, name, PANEL["print"], font=LABEL_FONT)
    return cv


if __name__ == "__main__":
    os.makedirs(ASSETS, exist_ok=True)
    wide().scaled(4).save(os.path.join(ASSETS, "tools.png"), optimize=True)
    compact().scaled(4).save(os.path.join(ASSETS, "tools-compact.png"), optimize=True)
    print("wrote tools.png and tools-compact.png")
