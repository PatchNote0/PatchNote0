"""The hero: a modular synth whose modules are PatchNote's projects.

The Dastyar Moshaver module is a step sequencer laid out like a Persian study
week: Saturday at the top and time running right to left. Each lit block is a
note. The notes travel down the cables from left to right: the PatchNote voice
draws them on its scope, Budget Flow meters them on its faders, and Shora
Archive records them. The A4 output, the printed plan, is filed in the archive.

Run:  python art/rack.py   ->  assets/rack.gif and assets/rack.png
"""
from __future__ import annotations

import math
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import px  # noqa: E402
from fonts import WORDMARK  # noqa: E402
from px import Canvas, mix  # noqa: E402

W, H = 420, 160
SCALE = 4
STEPS = 8
FRAMES_PER_STEP = 4
FRAME_MS = 90

FINISH = {
    "ink": dict(base="#22325a", light="#30467a", dark="#17223f", print="#ebe5d6", dim="#9eacca"),
    "alu": dict(base="#c4c7cc", light="#e3e5e8", dark="#9a9ea5", print="#1f2126", dim="#585c63"),
    "crimson": dict(base="#b11f39", light="#cf3a52", dark="#82162a", print="#f7f0e5", dim="#f3c2c9"),
    "bone": dict(base="#e3dbca", light="#f3ede1", dark="#c3b9a3", print="#2a2520", dim="#6f665a"),
    "black": dict(base="#1d1c22", light="#2b2a32", dark="#121116", print="#ebe5d6", dim="#6c6a76"),
}

CABLE = {
    "crimson": ("#ff7385", "#d9283f", "#8f1428", "#3f0812"),
    "amber": ("#ffd88a", "#f2a224", "#a9620c", "#432604"),
    "black": ("#64636c", "#2c2b31", "#141317", "#050506"),
    "bone": ("#ffffff", "#e8e2d4", "#b0a792", "#45403a"),
    "blue": ("#9cbcff", "#3f72d9", "#22428c", "#0c1934"),
}

KNOB_BLACK = ("#5d5c66", "#3b3a42", "#2a2930", "#1b1a20", "#0b0b0e")
KNOB_ALU = ("#ffffff", "#e6e8eb", "#c2c5ca", "#8f939a", "#2c2d32")
KNOB_BONE = ("#fffaf0", "#efe7d6", "#d7cdb7", "#a89d85", "#3a342c")

# Saturday .. Friday, top to bottom. Columns are study blocks in time order;
# block 0 is drawn at the right because the week is read right to left.
PATTERN = [
    "11011010",
    "10110110",
    "01101101",
    "11010110",
    "10111001",
    "01101000",
    "00000000",
]
# relative pitch of each day, as cycles across the scope screen
CYCLES = [1.5, 2.0, 2.5, 3.0, 3.5, 4.5, 5.5]
DRIFT = [1, 2, 1, 3, 2, 1, 2]

# module placement: (left edge, width) --------------------------------------
LEFT_FILLER = (-6, 28)
DASTYAR = (23, 112)
VOICE = (136, 112)
GAP = (248, 6)
BUDGET = (254, 76)
SHORA = (331, 72)
RIGHT_FILLER = (404, 24)

JACK_Y = 127       # top of every jack
JACK_LABEL_Y = 120  # labels sit above jacks so hanging cables never hide them

JACKS = {}
makers_mark_later = []


def panel(cv, x, w, finish, screws="four"):
    f = FINISH[finish]
    cv.rect(x, 0, w, H, f["base"])
    cv.vline(x, 0, H, f["light"])
    cv.hline(x, 0, w, f["light"])
    cv.vline(x + w - 1, 0, H, f["dark"])
    cv.hline(x, H - 1, w, f["dark"])
    slots = ["d", "h", "v", "d"]
    if screws == "four":
        spots = [(x + 4, 3), (x + w - 9, 3), (x + 4, H - 8), (x + w - 9, H - 8)]
    else:
        spots = []
    for k, (sx, sy) in enumerate(spots):
        px.screw(cv, sx, sy, slots[k % 4])
    return f


def makers_mark(cv, x, w, finish):
    """The same small P/N mark at the foot of every module, like a maker's signature."""
    f = FINISH[finish]
    cv.text(x + w // 2, H - 8, "P/N", f["dim"], align="center")


def seam(cv, x):
    cv.vline(x, 0, H, "#09090b")


def rails(cv, x, w):
    cv.rect(x, 0, w, H, "#0b0a0e")
    for y0 in (0, H - 11):
        cv.rect(x, y0, w, 11, "#34333b")
        cv.hline(x, y0 + 1, w, "#5a5963")
        cv.hline(x, y0 + 9, w, "#1f1e24")
        for hx in range(x, x + w, 5):
            cv.rect(hx + 1, y0 + 4, 2, 2, "#141318")


def label(cv, cx, y, s, c):
    cv.text(cx, y, s, c, align="center")


def jack_at(cv, name, cx, text, colour):
    label(cv, cx, JACK_LABEL_Y, text, colour)
    px.jack(cv, cx - 4, JACK_Y)
    JACKS[name] = (cx, JACK_Y + 4)


# -----------------------------------------------------------------------------
# modules
# -----------------------------------------------------------------------------

PAD_W, PAD_H, PITCH_X, PITCH_Y = 7, 6, 9, 9


def grid_origin():
    x0, w = DASTYAR
    return x0 + 8, 40


def pad_xy(step, row):
    gx, gy = grid_origin()
    col = STEPS - 1 - step  # the week reads right to left
    return gx + col * PITCH_X, gy + row * PITCH_Y


def dastyar_static(cv):
    x0, w = DASTYAR
    makers_mark_later.append((x0, w, "ink"))
    f = panel(cv, x0, w, "ink")
    cx = x0 + w // 2
    label(cv, cx, 10, "DASTYAR MOSHAVER", f["print"])
    cv.fa_text(cx, 18, "دستیار مشاور", f["print"], size=11, weight=600)
    gx, gy = grid_origin()
    # the week's two ends, Saturday by the top row and Friday by the bottom one
    for r, word in ((0, "شنبه"), (6, "جمعه")):
        mask, _ = px.fa_mask(word, 11, 600)
        cv.fa_text(x0 + w - 6, gy + r * PITCH_Y + 3 - mask.height // 2, word, f["dim"],
                   size=11, weight=600, align="right")
    for i, name in enumerate(["BLOCK", "BREAK", "DAYS"]):
        kx = x0 + 22 + i * 34
        px.knob(cv, kx, 103, 4, [-120, 30, 95][i], KNOB_BONE, pointer="#1b1a20")
        label(cv, kx, 110, name, f["dim"])
    for i, name in enumerate(["CLOCK", "GATE", "A4"]):
        jack_at(cv, "dastyar." + name.lower(), x0 + 22 + i * 34, name, f["print"])


def dastyar_dynamic(cv, step, sub):
    f = FINISH["ink"]
    gx, gy = grid_origin()
    for s in range(STEPS):
        lx, _ = pad_xy(s, 0)
        px.led(cv, lx + 3, gy - 6, s == step, "#ff4655", "#3a1b2a", glow=mix(f["base"], "#ff4655", 0.35))
    for r in range(7):
        for s in range(STEPS):
            x, y = pad_xy(s, r)
            on = PATTERN[r][s] == "1"
            here = s == step
            if on and here and sub < 2:
                face, top, edge = "#ffffff", "#ffffff", "#f2c79c"
            elif on:
                face, top, edge = "#e6dfcd", "#f9f5ec", "#b5ad9a"
            elif here:
                face, top, edge = "#2f4373", "#3d5390", "#1a2647"
            else:
                face, top, edge = "#1a2747", "#2a3a64", "#121b33"
            cv.rect(x, y, PAD_W, PAD_H, face)
            cv.hline(x, y, PAD_W, top)
            cv.hline(x, y + PAD_H - 1, PAD_W, edge)
            cv.put(x, y, mix(top, f["base"], 0.5))
            cv.put(x + PAD_W - 1, y, mix(top, f["base"], 0.5))


def scope_rect():
    x0, w = VOICE
    return x0 + 11, 22, 90, 48


def voice_static(cv):
    x0, w = VOICE
    makers_mark_later.append((x0, w, "crimson"))
    f = panel(cv, x0, w, "crimson")
    cx = x0 + w // 2
    cv.text(cx, 7, "PATCHNOTE", f["print"], font=WORDMARK, align="center")
    sx, sy, sw, sh = scope_rect()
    sy += 2
    cv.rect(sx - 2, sy - 2, sw + 4, sh + 4, f["dark"])
    cv.hline(sx - 2, sy + sh + 1, sw + 4, f["light"])
    cv.vline(sx + sw + 1, sy - 1, sh + 2, f["light"])
    label(cv, cx, sy + sh + 5, "MADE WITH INTENTION", f["dim"])
    px.knob(cv, x0 + 28, 96, 7, -35, KNOB_BLACK)
    label(cv, x0 + 28, 107, "NOTE", f["print"])
    px.knob(cv, x0 + 64, 94, 4, 60, KNOB_BLACK)
    label(cv, x0 + 64, 101, "PATCH", f["dim"])
    px.knob(cv, x0 + 90, 94, 4, -80, KNOB_BLACK)
    label(cv, x0 + 90, 101, "DECAY", f["dim"])
    for name, jx in (("GATE", x0 + 22), ("V/OCT", x0 + 56), ("OUT", x0 + 90)):
        jack_at(cv, "voice." + name.lower().replace("/", ""), jx, name, f["print"])


def voice_dynamic(cv, frame, gate):
    sx, sy, sw, sh = scope_rect()
    sy += 2
    bg, grid, centre = "#170d08", "#3a2414", "#5a3a1c"
    cv.rect(sx, sy, sw, sh, bg)
    for gx in range(sx + 5, sx + sw, 10):
        for gy in range(sy + 4, sy + sh, 10):
            cv.put(gx, gy, grid)
    for gx in range(sx + 1, sx + sw, 2):
        cv.put(gx, sy + sh // 2, centre if (gx - sx) % 10 else grid)
    t = frame / FRAMES_PER_STEP
    env = envelopes(t)
    amp = sh // 2 - 4
    ys = []
    for i in range(sw):
        v = 0.0
        for r, e in enumerate(env):
            if e < 0.01:
                continue
            ph = 2 * math.pi * DRIFT[r] * frame / (STEPS * FRAMES_PER_STEP)
            v += e * math.sin(2 * math.pi * CYCLES[r] * i / sw + ph + r)
        ys.append(sy + sh // 2 - round(amp * math.tanh(v / 1.9)))
    trace, glow = "#ffc565", "#8f5219"
    pts = set()
    for i in range(sw):
        y0 = ys[i]
        y1 = ys[i + 1] if i + 1 < sw else y0
        for y in range(min(y0, y1), max(y0, y1) + 1):
            pts.add((sx + i, y))
    for (x, y) in pts:
        for (dx, dy) in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            q = (x + dx, y + dy)
            if q not in pts and sx <= q[0] < sx + sw and sy <= q[1] < sy + sh:
                cv.put(q[0], q[1], glow)
    for (x, y) in pts:
        if sy <= y < sy + sh:
            cv.put(x, y, trace)
    gx, gy = JACKS["voice.gate"]
    px.led(cv, gx + 11, JACK_LABEL_Y + 1, gate, "#ffd166", "#5e1222",
           glow=mix(FINISH["crimson"]["base"], "#ffd166", 0.4))


FADERS = [("PLAN", 0.84), ("ALLOC", 0.58), ("LEFT", 0.26)]


def fader_x(i):
    x0, w = BUDGET
    return x0 + 13 + i * 24


def budget_static(cv):
    x0, w = BUDGET
    makers_mark_later.append((x0, w, "alu"))
    f = panel(cv, x0, w, "alu")
    cx = x0 + w // 2
    label(cv, cx, 10, "BUDGET FLOW", f["print"])
    for i, (name, v) in enumerate(FADERS):
        sx = fader_x(i)
        cv.rect(sx - 1, 24, 3, 76, "#111215")
        cv.vline(sx + 2, 24, 76, f["light"])
        cv.hline(sx - 1, 100, 3, f["light"])
        label(cv, sx, 104, name, f["print"])
    jack_at(cv, "budget.in", x0 + 15, "IN", f["print"])
    jack_at(cv, "budget.out", x0 + 61, "OUT", f["print"])
    px.knob(cv, x0 + 38, JACK_Y + 4, 4, 40, KNOB_ALU, pointer="#1f2126")
    label(cv, x0 + 38, JACK_LABEL_Y, "MIX", f["dim"])


def budget_dynamic(cv, level):
    f = FINISH["alu"]
    for i, (name, v) in enumerate(FADERS):
        sx = fader_x(i)
        lit = round(min(1.0, level * v * 1.35) * 10)
        for k in range(10):
            y = 94 - k * 7
            px.led(cv, sx + 5, y, k < lit, "#ff3d4f", "#8d9096", glow=None, size=2)
        cy = 98 - round(v * 72)
        cv.hline(sx - 4, cy + 3, 9, mix(f["base"], "#000000", 0.35))
        cv.rect(sx - 4, cy - 2, 9, 5, "#ece6d8")
        cv.hline(sx - 4, cy - 2, 9, "#ffffff")
        cv.hline(sx - 4, cy + 2, 9, "#a99f89")
        cv.hline(sx - 3, cy, 7, "#2a2722")


def shora_static(cv):
    x0, w = SHORA
    makers_mark_later.append((x0, w, "bone"))
    f = panel(cv, x0, w, "bone")
    cx = x0 + w // 2
    label(cv, cx, 10, "SHORA ARCHIVE", f["print"])
    cv.fa_text(cx, 18, "شورا", f["print"], size=11, weight=600)
    wx, wy, ww, wh = x0 + 12, 34, 48, 17
    cv.rect(wx - 1, wy - 1, ww + 2, wh + 2, f["dark"])
    cv.rect(wx, wy, ww, wh, "#1d0b0d")
    cv.hline(wx - 1, wy + wh, ww + 2, f["light"])
    digits_x = wx + (ww - (4 * 5 + 3 * 4)) // 2
    for k, ch in enumerate("1405"):
        px.segment_digit(cv, digits_x + k * 9, wy + 4, ch, "#ff4b4b", "#3d1518")
    label(cv, cx, 55, "YEAR", f["dim"])
    for j in range(4):
        for i in range(3):
            bx, by = x0 + 22 + i * 10, 65 + j * 8
            cv.rect(bx, by, 8, 5, "#cfc5ad")
            cv.hline(bx, by, 8, "#f6f1e7")
            cv.hline(bx, by + 4, 8, "#a59a83")
    label(cv, cx, 99, "INDEX", f["dim"])
    jack_at(cv, "shora.file", x0 + 14, "FILE", f["print"])
    jack_at(cv, "shora.rec", x0 + 36, "REC", f["print"])
    jack_at(cv, "shora.out", x0 + 58, "OUT", f["print"])


def shora_dynamic(cv, rec):
    x0, w = SHORA
    f = FINISH["bone"]
    px.led(cv, x0 + 27, 109, rec, "#ff3d4f", "#b8ad96", glow=mix(f["base"], "#ff3d4f", 0.35))
    cv.text(x0 + 32, 108, "REC", f["print"])


def fillers(cv):
    x, w = LEFT_FILLER
    panel(cv, x, w, "black", screws="none")
    px.screw(cv, x + w - 12, 3, "v")
    px.screw(cv, x + w - 12, H - 8, "d")
    x, w = RIGHT_FILLER
    panel(cv, x, w, "black", screws="none")
    px.screw(cv, x + 5, 3, "d")
    px.screw(cv, x + 5, H - 8, "h")


# -----------------------------------------------------------------------------
# signal
# -----------------------------------------------------------------------------

def envelopes(t):
    """Loudness of each day's note at time t (in steps), seamless across the loop."""
    out = []
    for r in range(7):
        e = 0.0
        for s in range(STEPS):
            if PATTERN[r][s] != "1":
                continue
            for wrap in (0, STEPS, 2 * STEPS):
                dt = t - (s - wrap)
                if dt >= 0:
                    e += math.exp(-dt * 2.6)
        out.append(e)
    return out


def triggers(step):
    return [r for r in range(7) if PATTERN[r][step] == "1"]


# -----------------------------------------------------------------------------
# cables: from, to, colour, sag
# -----------------------------------------------------------------------------

PATCHES = [
    ((-14, 154), "dastyar.clock", "bone", 6),
    ("dastyar.gate", "voice.gate", "crimson", 13),
    ("voice.out", "budget.in", "amber", 9),
    ("budget.out", "shora.rec", "black", 8),
    ("dastyar.a4", "shora.file", "bone", 21),
    ("shora.out", (446, 150), "blue", 6),
]


def where(p):
    return JACKS[p] if isinstance(p, str) else p


def draw_cables(cv):
    for a, b, colour, sag in PATCHES:
        pts = px.cable_path(where(a), where(b), sag)
        px.draw_cable(cv, pts, CABLE[colour])
    for a, b, colour, sag in PATCHES:
        for p in (a, b):
            if isinstance(p, str):
                cx, cy = JACKS[p]
                px.plug(cv, cx - 4, cy - 4, CABLE[colour])


# -----------------------------------------------------------------------------
# render
# -----------------------------------------------------------------------------

def static_layer():
    cv = Canvas(W, H, "#0b0a0e")
    fillers(cv)
    dastyar_static(cv)
    seam(cv, DASTYAR[0] - 1)
    voice_static(cv)
    seam(cv, VOICE[0] - 1)
    rails(cv, *GAP)
    budget_static(cv)
    shora_static(cv)
    seam(cv, SHORA[0] - 1)
    seam(cv, RIGHT_FILLER[0] - 1)
    for x0, w, fin in makers_mark_later:
        makers_mark(cv, x0, w, fin)
    makers_mark_later.clear()
    return cv


def frame_image(base, frame):
    cv = Canvas(W, H)
    cv.img.paste(base.img)
    step, sub = divmod(frame, FRAMES_PER_STEP)
    t = frame / FRAMES_PER_STEP
    hits = triggers(step)
    gate = bool(hits) and sub < 2
    level = min(1.0, sum(envelopes(t)) / 2.2)
    rec = bool(hits) and 1 <= sub < 3
    dastyar_dynamic(cv, step, sub)
    budget_dynamic(cv, level)
    voice_dynamic(cv, frame, gate)
    shora_dynamic(cv, rec)
    draw_cables(cv)
    return cv.img


def to_palette(frames):
    colours = {}
    for im in frames:
        for count, c in im.getcolors(1 << 20):
            colours.setdefault(c, len(colours))
    assert len(colours) <= 256, f"{len(colours)} colours, a GIF holds 256"
    flat = []
    for c in sorted(colours, key=colours.get):
        flat.extend(c)
    flat.extend([0] * (768 - len(flat)))
    out = []
    for im in frames:
        p = Image.new("P", im.size)
        p.putpalette(flat)
        p.putdata([colours[c] for c in im.get_flattened_data()] if hasattr(im, "get_flattened_data") else [colours[c] for c in im.getdata()])
        out.append(p)
    return out


STILL_FRAME = 4 * FRAMES_PER_STEP + 1  # a busy step, caught as it sounds


def render_frames_for_still():
    base = static_layer()
    return {STILL_FRAME: frame_image(base, STILL_FRAME)}


def render(out_dir, still_frame=STILL_FRAME):
    base = static_layer()
    total = STEPS * FRAMES_PER_STEP
    frames = [frame_image(base, k) for k in range(total)]
    pal = to_palette(frames)
    big = [p.resize((W * SCALE, H * SCALE), Image.NEAREST) for p in pal]
    os.makedirs(out_dir, exist_ok=True)
    big[0].save(
        os.path.join(out_dir, "rack.gif"), save_all=True, append_images=big[1:],
        duration=FRAME_MS, loop=0, optimize=False, disposal=1,
    )
    frames[still_frame].resize((W * SCALE, H * SCALE), Image.NEAREST).save(
        os.path.join(out_dir, "rack.png"), optimize=True)
    return frames


if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    render(os.path.join(root, "assets"))
    print("wrote assets/rack.gif and assets/rack.png")
