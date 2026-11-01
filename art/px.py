"""A small pixel-art toolkit: a canvas, hand-drawn parts and text.

Everything is drawn at 1 art pixel = 1 image pixel and scaled up with
nearest-neighbour at the end, so every edge stays a hard pixel edge.
"""
from __future__ import annotations

import math
import os

from PIL import Image, ImageDraw, ImageFont

from fonts import SMALL, TITLE, WORDMARK

HERE = os.path.dirname(os.path.abspath(__file__))
FA_FONT = os.path.join(HERE, "fonts", "Vazirmatn.ttf")


def rgb(c):
    if isinstance(c, tuple):
        return c[:3]
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def mix(a, b, t):
    a, b = rgb(a), rgb(b)
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def scale_color(c, k):
    c = rgb(c)
    return tuple(max(0, min(255, round(v * k))) for v in c)


class Canvas:
    def __init__(self, w, h, bg="#000000"):
        self.w, self.h = w, h
        self.img = Image.new("RGB", (w, h), rgb(bg))
        self.draw = ImageDraw.Draw(self.img)
        self.px = self.img.load()

    # basic pixels ----------------------------------------------------------
    def put(self, x, y, c):
        x, y = int(x), int(y)
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[x, y] = rgb(c)

    def get(self, x, y):
        return self.px[int(x), int(y)]

    def rect(self, x, y, w, h, c):
        if w <= 0 or h <= 0:
            return
        self.draw.rectangle([x, y, x + w - 1, y + h - 1], fill=rgb(c))

    def hline(self, x, y, w, c):
        self.rect(x, y, w, 1, c)

    def vline(self, x, y, h, c):
        self.rect(x, y, 1, h, c)

    def outline(self, x, y, w, h, c):
        self.hline(x, y, w, c)
        self.hline(x, y + h - 1, w, c)
        self.vline(x, y, h, c)
        self.vline(x + w - 1, y, h, c)

    def darken(self, x, y, k):
        x, y = int(x), int(y)
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[x, y] = scale_color(self.px[x, y], k)

    def sprite(self, x, y, rows, palette):
        """Stamp a hand-drawn sprite. Characters missing from palette are see-through."""
        for j, row in enumerate(rows):
            for i, ch in enumerate(row):
                if ch in palette:
                    self.put(x + i, y + j, palette[ch])

    def paste(self, other, x, y):
        self.img.paste(other.img, (x, y))

    # text ------------------------------------------------------------------
    def text(self, x, y, s, c, font=SMALL, spacing=1, align="left"):
        w = text_width(s, font, spacing)
        if align == "center":
            x = x - w // 2
        elif align == "right":
            x = x - w
        cx = x
        for ch in s.upper():
            g = font.get(ch, font["?"] if "?" in font else font[" "])
            for j, row in enumerate(g):
                for i, b in enumerate(row):
                    if b == "#":
                        self.put(cx + i, y + j, c)
            cx += len(g[0]) + spacing
        return x, w

    def fa_text(self, x, y, s, c, size=11, weight=600, align="center", baseline=False):
        """Persian text, shaped by HarfBuzz/Raqm, drawn without anti-aliasing.

        With baseline=True, y is the baseline and letters keep their true
        heights, so a column of single letters lines up like set type.
        """
        if baseline:
            mask, top = fa_line(s, size, weight)
            y = y - top
        else:
            mask, (left, top) = fa_mask(s, size, weight)
        w = mask.width
        if align == "center":
            x0 = x - w // 2
        elif align == "right":
            x0 = x - w
        else:
            x0 = x
        m = mask.load()
        for j in range(mask.height):
            for i in range(mask.width):
                if m[i, j]:
                    self.put(x0 + i, y + j, c)
        return x0, w, mask.height

    # export ------------------------------------------------------------------
    def scaled(self, k):
        return self.img.resize((self.w * k, self.h * k), Image.NEAREST)


def text_width(s, font=SMALL, spacing=1):
    total = 0
    for ch in s.upper():
        g = font.get(ch, font[" "])
        total += len(g[0]) + spacing
    return max(0, total - spacing)


_fa_cache = {}
_fa_line_cache = {}


def _persian_font(size, weight):
    from PIL import features
    if not features.check("raqm"):
        raise RuntimeError(
            "Persian text needs Pillow built with Raqm, or the letters will not join. "
            "On macOS: brew install fribidi, then reinstall Pillow.")
    font = ImageFont.truetype(FA_FONT, size, layout_engine=ImageFont.Layout.RAQM)
    try:
        font.set_variation_by_axes([weight])
    except OSError:
        pass
    return font


def to_pixels(gray, threshold=100):
    """Turn anti-aliased text into hard pixels. Pure 1-bit rendering drops the
    small dots Persian letters depend on (ن becomes ں); a low threshold keeps them."""
    return gray.point(lambda v: 255 if v >= threshold else 0).convert("1")


def fa_line(s, size=11, weight=600):
    """Render s on a fixed line box. Returns the ink-trimmed mask and how far the
    top of the ink sits above the baseline."""
    key = (s, size, weight)
    if key in _fa_line_cache:
        return _fa_line_cache[key]
    font = _persian_font(size, weight)
    pad = size * 2
    img = Image.new("L", (pad * 4 + size * len(s), pad * 3), 0)
    d = ImageDraw.Draw(img)
    base_y = pad * 2
    d.text((pad, base_y), s, font=font, fill=255, anchor="ls", direction="rtl", language="fa")
    img = to_pixels(img)
    bbox = img.getbbox()
    mask = img.crop(bbox)
    _fa_line_cache[key] = (mask, base_y - bbox[1])
    return _fa_line_cache[key]


def fa_mask(s, size=11, weight=600):
    key = (s, size, weight)
    if key in _fa_cache:
        return _fa_cache[key]
    font = _persian_font(size, weight)
    probe = Image.new("L", (1, 1), 0)
    d = ImageDraw.Draw(probe)
    l, t, r, b = d.textbbox((0, 0), s, font=font, direction="rtl", language="fa")
    img = Image.new("L", (r - l + 4, b - t + 4), 0)
    d = ImageDraw.Draw(img)
    d.text((-l + 2, -t + 2), s, font=font, fill=255, direction="rtl", language="fa")
    img = to_pixels(img)
    # trim to ink
    bbox = img.getbbox()
    img = img.crop(bbox)
    _fa_cache[key] = (img, (l, t))
    return _fa_cache[key]


# -----------------------------------------------------------------------------
# Hand-drawn parts. Each takes the canvas, a top-left corner and colours.
# Light falls from the top left everywhere.
# -----------------------------------------------------------------------------

def screw(cv, x, y, slot="h"):
    o, h, m, s, k = "#26252b", "#d6d7dc", "#a2a4ab", "#6f7178", "#3a3b42"
    rows = [
        ".ooo.",
        "ohmmo",
        "ommso",
        "omsso",
        ".ooo.",
    ]
    cv.sprite(x, y, rows, {"o": o, "h": h, "m": m, "s": s})
    if slot == "h":
        cv.hline(x + 1, y + 2, 3, k)
    elif slot == "v":
        cv.vline(x + 2, y + 1, 3, k)
    else:  # diagonal
        cv.put(x + 1, y + 3, k)
        cv.put(x + 2, y + 2, k)
        cv.put(x + 3, y + 1, k)


def jack(cv, x, y):
    """A 3.5 mm jack seen from the front: hex nut and a round dark hole. 9 x 9."""
    rows = [
        "..ooooo..",
        ".ohhhhho.",
        "ohhmmmmso",
        "ohmrkrmso",
        "ohmkkkmso",
        "ohmrkrmso",
        "omsmmmsso",
        ".ossssso.",
        "..ooooo..",
    ]
    cv.sprite(x, y, rows, {
        "o": "#17171b", "h": "#e2e3e7", "m": "#aeb0b6", "s": "#74767d",
        "r": "#2a2b30", "k": "#060608",
    })


def plug(cv, x, y, ramp):
    """The round boot of a patch cable plugged into a jack. 9 x 9, sits over the jack."""
    hi, mid, lo, out = ramp
    rows = [
        "..ooooo..",
        ".ohhhmmo.",
        "ohhhmmmlo",
        "ohhmmmmlo",
        "ohmmkmmlo",
        "ommmmmllo",
        "ommmmlllo",
        ".olllllo.",
        "..ooooo..",
    ]
    cv.sprite(x, y, rows, {"o": out, "h": hi, "m": mid, "l": lo, "k": mix(mid, out, 0.6)})


def led(cv, x, y, on, hue_on, hue_off, glow=None, size=2):
    """A small LED. When it is on, a one pixel halo spills onto the panel."""
    if on and glow:
        for (dx, dy) in [(-1, 0), (size, 0), (0, -1), (0, size), (size - 1, -1), (size - 1, size),
                         (-1, size - 1), (size, size - 1)]:
            cv.put(x + dx, y + dy, glow)
    cv.rect(x, y, size, size, hue_on if on else hue_off)
    if on:
        cv.put(x, y, mix(hue_on, "#ffffff", 0.55))


def knob(cv, cx, cy, r, angle_deg, body, pointer="#f4f0e8", skirt=None):
    """A round knob, shaded from the top left, with a pointer line.

    body is a ramp: (highlight, light, mid, dark, outline).
    """
    hl, light, mid, dark, outline = body
    if skirt:
        sr = r + 2
        for j in range(-sr, sr + 1):
            for i in range(-sr, sr + 1):
                d = math.hypot(i, j)
                if d <= sr + 0.35 and d > r + 0.35:
                    edge = d > sr - 0.65
                    c = skirt[2] if edge else (skirt[0] if (i + j) < -1 else skirt[1])
                    cv.put(cx + i, cy + j, c)
    for j in range(-r - 1, r + 2):
        for i in range(-r - 1, r + 2):
            d = math.hypot(i, j)
            if d > r + 0.35:
                continue
            if d > r - 0.65:
                c = outline
            else:
                # lambert-ish shading towards the top left
                nx, ny = i / max(r, 1), j / max(r, 1)
                lit = -(nx * 0.7071 + ny * 0.7071)
                if lit > 0.55:
                    c = hl
                elif lit > 0.1:
                    c = light
                elif lit > -0.45:
                    c = mid
                else:
                    c = dark
            cv.put(cx + i, cy + j, c)
    # flat top face
    top = max(1, r - 2)
    for j in range(-top, top + 1):
        for i in range(-top, top + 1):
            if math.hypot(i, j) <= top - 0.2:
                c = light if (i + j) < 0 else mid
                cv.put(cx + i, cy + j, c)
    # pointer
    a = math.radians(angle_deg)
    for t in range(1, r):
        px_ = cx + round(math.sin(a) * t)
        py_ = cy - round(math.cos(a) * t)
        cv.put(px_, py_, pointer)


def segment_digit(cv, x, y, ch, on, off):
    """A seven-segment digit, 5 wide and 9 tall."""
    segs = {
        "0": "abcdef", "1": "bc", "2": "abged", "3": "abgcd", "4": "fgbc",
        "5": "afgcd", "6": "afgedc", "7": "abc", "8": "abcdefg", "9": "abcdfg",
        "-": "g", " ": "",
    }[ch]
    geo = {
        "a": [(1, 0), (2, 0), (3, 0)],
        "b": [(4, 1), (4, 2), (4, 3)],
        "c": [(4, 5), (4, 6), (4, 7)],
        "d": [(1, 8), (2, 8), (3, 8)],
        "e": [(0, 5), (0, 6), (0, 7)],
        "f": [(0, 1), (0, 2), (0, 3)],
        "g": [(1, 4), (2, 4), (3, 4)],
    }
    for name, pts in geo.items():
        c = on if name in segs else off
        for (i, j) in pts:
            cv.put(x + i, y + j, c)


# -----------------------------------------------------------------------------
# Cables
# -----------------------------------------------------------------------------

def bezier(p0, p1, p2, p3, n):
    pts = []
    for k in range(n + 1):
        t = k / n
        u = 1 - t
        x = u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0]
        y = u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1]
        pts.append((x, y))
    return pts


def cable_path(a, b, sag):
    """A hanging cable from jack a to jack b. Both ends leave the plug downwards."""
    (x0, y0), (x1, y1) = a, b
    low = max(y0, y1) + sag
    c0 = (x0 + (x1 - x0) * 0.12, low + sag * 0.15)
    c1 = (x1 - (x1 - x0) * 0.12, low + sag * 0.15)
    n = int(abs(x1 - x0) + abs(y1 - y0) + 2 * sag) * 3
    return bezier((x0, y0), c0, c1, (x1, y1), max(n, 40))


def stamp_disc(cv, cx, cy, r, color):
    for j in range(-r, r + 1):
        for i in range(-r, r + 1):
            if i * i + j * j <= r * r + r * 0.6:
                cv.put(cx + i, cy + j, color)


def draw_cable(cv, pts, ramp, shadow_k=0.5):
    """A three pixel cable with a lit upper edge and a shadow cast on the panel.

    Where the cable runs flatter than 45 degrees its thickness is stacked
    vertically (light on top); where it is steep, horizontally (light on the left).
    """
    hi, mid, lo, out = ramp
    centers = []
    for (x, y) in pts:
        p = (round(x), round(y))
        if not centers or centers[-1] != p:
            centers.append(p)
    body = {}
    for k, (x, y) in enumerate(centers):
        a = centers[max(0, k - 2)]
        b = centers[min(len(centers) - 1, k + 2)]
        steep = abs(b[1] - a[1]) > abs(b[0] - a[0])
        if steep:
            body[(x - 1, y)] = hi
            body.setdefault((x, y), mid)
            body.setdefault((x + 1, y), lo)
        else:
            body[(x, y - 1)] = hi
            body.setdefault((x, y), mid)
            body.setdefault((x, y + 1), lo)
    # the brightest value wins where samples overlap
    order = {hi: 3, mid: 2, lo: 1}
    final = {}
    for p, c in body.items():
        if p not in final or order[c] > order[final[p]]:
            final[p] = c
    shadow = set()
    for (x, y) in centers:
        for dy in (2, 3):
            shadow.add((x + 1, y + dy))
    for p in shadow:
        if p not in final:
            cv.darken(p[0], p[1], shadow_k)
    for p, c in final.items():
        cv.put(p[0], p[1], c)
    return set(final)
