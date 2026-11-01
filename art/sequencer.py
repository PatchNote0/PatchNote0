"""The live piece: a year of GitHub contributions played as a step sequencer.

Each column is a week and each row a day, exactly like GitHub's own calendar.
A lit pad is a day with contributions, brighter for busier days (GitHub's four
levels). The playhead walks through the year once per loop.

A GitHub Action runs this every day (.github/workflows/sequencer.yml).

    python art/sequencer.py                 # fetch, then draw
    python art/sequencer.py --offline       # draw from assets/sequencer.json
    python art/sequencer.py --demo          # draw made-up data, for testing only

Data comes from the public calendar at github.com/users/<login>/contributions,
with the GraphQL API as a fallback when a token is present. If both fail the
last good data is kept, and with no data at all the panel says it is waiting.
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import random
import re
import sys
import urllib.request

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import px  # noqa: E402
from px import Canvas, mix  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
CACHE = os.path.join(ASSETS, "sequencer.json")

H = 100
SCALE = 4
FRAME_MS = 80

PANEL = dict(base="#1d1c22", light="#2b2a32", dark="#121116", print="#ebe5d6", dim="#8a8794")
# GitHub's levels 0-4 as one amber ramp, dark to bright
PAD = {
    0: ("#25242b", "#2f2e36", "#17161b"),
    1: ("#5a3a14", "#6f4919", "#3e280d"),
    2: ("#a8661a", "#c27a22", "#7a4a12"),
    3: ("#eda02c", "#ffb84d", "#b97716"),
    4: ("#ffd889", "#fff0c9", "#e0a548"),
}
FLASH = ("#ffffff", "#ffffff", "#ffe2b0")
PITCH, PAD_SIZE = 7, 6
GRID_Y = 30


# -----------------------------------------------------------------------------
# data
# -----------------------------------------------------------------------------

def fetch_html(login):
    url = f"https://github.com/users/{login}/contributions"
    req = urllib.request.Request(url, headers={"User-Agent": "patchnote-profile-sequencer"})
    with urllib.request.urlopen(req, timeout=30) as r:
        page = r.read().decode("utf-8", "replace")
    return parse_calendar(page)


def parse_calendar(page):
    """Read days, levels and counts out of GitHub's calendar markup."""
    days = {}
    for m in re.finditer(r'<td[^>]*?data-date="(\d{4}-\d{2}-\d{2})"[^>]*?id="([^"]+)"[^>]*?data-level="(\d)"', page):
        days[m.group(2)] = {"date": m.group(1), "level": int(m.group(3)), "count": None}
    if not days:  # attribute order differs between page versions
        for td in re.finditer(r"<td[^>]*ContributionCalendar-day[^>]*>", page):
            tag = td.group(0)
            d = re.search(r'data-date="([^"]+)"', tag)
            lv = re.search(r'data-level="(\d)"', tag)
            i = re.search(r'id="([^"]+)"', tag)
            if d and lv and i:
                days[i.group(1)] = {"date": d.group(1), "level": int(lv.group(1)), "count": None}
    for m in re.finditer(r'<tool-tip[^>]*for="([^"]+)"[^>]*>([^<]*)</tool-tip>', page):
        tip = html.unescape(m.group(2))
        n = re.match(r"\s*([\d,]+) contribution", tip)
        if m.group(1) in days:
            if n:
                days[m.group(1)]["count"] = int(n.group(1).replace(",", ""))
            elif tip.strip().startswith("No contribution"):
                days[m.group(1)]["count"] = 0
    total = None
    t = re.search(r"([\d,]+)\s+contributions?\s+in the last year", page)
    if t:
        total = int(t.group(1).replace(",", ""))
    out = sorted(days.values(), key=lambda d: d["date"])
    if len(out) < 300:
        raise RuntimeError(f"calendar looked wrong: {len(out)} days")
    return {"days": out, "total": total, "source": "html"}


def fetch_graphql(login, token):
    query = """query($login:String!){user(login:$login){contributionsCollection{contributionCalendar{
      totalContributions weeks{contributionDays{date contributionCount contributionLevel}}}}}}"""
    body = json.dumps({"query": query, "variables": {"login": login}}).encode()
    req = urllib.request.Request("https://api.github.com/graphql", data=body, headers={
        "Authorization": f"bearer {token}", "User-Agent": "patchnote-profile-sequencer",
        "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read())
    cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    levels = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}
    days = [{"date": d["date"], "count": d["contributionCount"], "level": levels[d["contributionLevel"]]}
            for wk in cal["weeks"] for d in wk["contributionDays"]]
    return {"days": days, "total": cal["totalContributions"], "source": "graphql"}


def demo_data():
    rng = random.Random(7)
    end = dt.date(2026, 11, 1)
    start = end - dt.timedelta(days=364 + (end.weekday() + 1) % 7)
    days = []
    d = start
    while d <= end:
        busy = 0.35 + 0.3 * (d.weekday() < 5)
        lv = 0 if rng.random() > busy else rng.choice([1, 1, 2, 2, 3, 4])
        days.append({"date": d.isoformat(), "level": lv, "count": [0, 1, 3, 6, 10][lv]})
        d += dt.timedelta(days=1)
    return {"days": days, "total": sum(x["count"] for x in days), "source": "demo"}


def load(mode, login):
    if mode == "demo":
        return demo_data()
    if mode == "fetch":
        errors = []
        try:
            data = fetch_html(login)
        except Exception as e:  # network, markup change
            errors.append(f"html: {e}")
            data = None
        if data is None and os.environ.get("GITHUB_TOKEN"):
            try:
                data = fetch_graphql(login, os.environ["GITHUB_TOKEN"])
            except Exception as e:
                errors.append(f"graphql: {e}")
        if data is not None:
            data["login"] = login
            data["fetched"] = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
            with open(CACHE, "w") as fh:
                json.dump(data, fh, indent=1)
            return data
        print("could not fetch the calendar; keeping the last good drawing", *errors, sep="\n  ")
    if os.path.exists(CACHE):
        with open(CACHE) as fh:
            return json.load(fh)
    return None


# -----------------------------------------------------------------------------
# drawing
# -----------------------------------------------------------------------------

def weeks_of(days, weeks):
    """Group days into GitHub's columns: weeks that start on Sunday."""
    cols = []
    for d in days:
        date = dt.date.fromisoformat(d["date"])
        row = (date.weekday() + 1) % 7  # Sunday = 0
        if not cols or row == 0:
            cols.append([None] * 7)
        cols[-1][row] = dict(d, row=row, date_obj=date)
    return cols[-weeks:]


class Sheet:
    """One layout of the panel: the whole year, or the last weeks for a phone."""

    def __init__(self, name, weeks, w, subtitle, legend):
        self.name, self.weeks, self.w, self.subtitle, self.legend = name, weeks, w, subtitle, legend
        self.h = H
        grid_w = weeks * PITCH - 1
        self.gx = (w - grid_w) // 2 + 3  # a little room on the left for M, W, F
        self.gy = GRID_Y
        self.right = self.gx + grid_w


SHEETS = [
    Sheet("sequencer", 53, 420, "ONE YEAR OF GITHUB CONTRIBUTIONS", legend=True),
    Sheet("sequencer-compact", 20, 176, "LAST 20 WEEKS", legend=False),
]


def panel(cv, sh):
    w = sh.w
    cv.rect(0, 0, w, H, PANEL["base"])
    cv.hline(0, 0, w, PANEL["light"])
    cv.vline(0, 0, H, PANEL["light"])
    cv.hline(0, H - 1, w, PANEL["dark"])
    cv.vline(w - 1, 0, H, PANEL["dark"])
    for (x, y, s) in ((4, 3, "d"), (w - 9, 3, "h"), (4, H - 8, "v"), (w - 9, H - 8, "d")):
        px.screw(cv, x, y, s)


def draw_static(cv, sh, data):
    panel(cv, sh)
    _, w = cv.text(sh.gx, 9, "P/N CLOCK", PANEL["print"])
    cv.text(sh.gx + w + 8, 9, sh.subtitle, PANEL["dim"])
    if not data:
        for c in range(sh.weeks):
            for r in range(7):
                pad(cv, sh, c, r, 0)
        msg = "WAITING FOR THE FIRST DAILY RUN"
        tw = px.text_width(msg)
        mid = (sh.gx + sh.right) // 2
        cv.rect(mid - tw // 2 - 8, sh.gy + 3 * PITCH - 4, tw + 16, PITCH + 6, PANEL["base"])
        cv.text(mid, sh.gy + 3 * PITCH, msg, PANEL["print"], align="center")
        return []
    cols = weeks_of(data["days"], sh.weeks)
    lit = sum(1 for col in cols for d in col if d and d["level"] > 0)
    count = sum(1 for col in cols for d in col if d)
    ly = sh.gy + 7 * PITCH + 6
    if sh.legend:
        cv.text(sh.right, 9, f"{lit} OF {count} DAYS LIT", PANEL["print"], align="right")
    else:  # the narrow sheet has room for the count only
        cv.text(sh.gx, ly + 1, f"{lit} DAYS LIT", PANEL["print"])
    # month names above the first full week of each month
    last = None
    for c, col in enumerate(cols):
        first = next((d for d in col if d), None)
        if not first:
            continue
        m = first["date_obj"].month
        if m != last and first["date_obj"].day <= 7:
            name = first["date_obj"].strftime("%b").upper()
            x = sh.gx + c * PITCH
            if x + px.text_width(name) <= sh.right:
                cv.text(x, sh.gy - 8, name, PANEL["dim"])
        last = m
    for r, name in ((1, "M"), (3, "W"), (5, "F")):
        cv.text(sh.gx - 6, sh.gy + r * PITCH, name, PANEL["dim"])
    for c, col in enumerate(cols):
        for r in range(7):
            if col[r] is not None:
                pad(cv, sh, c, r, col[r]["level"])
    if sh.legend:  # each swatch is the pad itself
        cv.text(sh.gx, ly + 1, "LESS", PANEL["dim"])
        for i in range(5):
            pad_at(cv, sh.gx + 18 + i * PITCH, ly, i)
        cv.text(sh.gx + 18 + 5 * PITCH + 2, ly + 1, "MORE", PANEL["dim"])
    stamp = f"UPDATED {data.get('fetched', data['days'][-1]['date'])}"
    cv.text(sh.right, ly + 1, stamp, PANEL["dim"], align="right")
    return cols


def pad_at(cv, x, y, level, flash=False):
    face, top, edge = FLASH if flash else PAD[level]
    cv.rect(x, y, PAD_SIZE, PAD_SIZE, face)
    cv.hline(x, y, PAD_SIZE, top)
    cv.hline(x, y + PAD_SIZE - 1, PAD_SIZE, edge)


def pad(cv, sh, c, r, level, flash=False):
    pad_at(cv, sh.gx + c * PITCH, sh.gy + r * PITCH, level, flash)


def draw_frame(base, sh, cols, c):
    cv = Canvas(sh.w, sh.h)
    cv.img.paste(base.img)
    x = sh.gx + c * PITCH
    # the playhead: a red LED over the column, and the column's pads lit up
    px.led(cv, x + 2, sh.gy - 2, True, "#ff4655", "#3a1b2a", glow=None)
    for r in range(7):
        d = cols[c][r]
        if d is None:
            continue
        if d["level"] > 0:
            pad(cv, sh, c, r, d["level"], flash=True)
        else:
            cv.hline(x, sh.gy + r * PITCH, PAD_SIZE, "#45444e")
    return cv.img


def mark_today(cv, sh, cols):
    if not cols:
        return
    c = len(cols) - 1
    r = max(i for i in range(7) if cols[c][i] is not None)
    x, y = sh.gx + c * PITCH, sh.gy + r * PITCH
    cv.outline(x - 1, y - 1, PAD_SIZE + 2, PAD_SIZE + 2, "#ff4655")


def render(data):
    os.makedirs(ASSETS, exist_ok=True)
    for sh in SHEETS:
        base = Canvas(sh.w, sh.h)
        cols = draw_static(base, sh, data)
        mark_today(base, sh, cols)
        still = base.img.resize((sh.w * SCALE, sh.h * SCALE), Image.NEAREST)
        still.save(os.path.join(ASSETS, f"{sh.name}.png"), optimize=True)
        if not cols:
            still.save(os.path.join(ASSETS, f"{sh.name}.gif"))
            continue
        frames = [draw_frame(base, sh, cols, c) for c in range(len(cols))]
        big = [p.resize((sh.w * SCALE, sh.h * SCALE), Image.NEAREST) for p in to_palette(frames)]
        big[0].save(os.path.join(ASSETS, f"{sh.name}.gif"), save_all=True, append_images=big[1:],
                    duration=FRAME_MS, loop=0, optimize=False, disposal=1)


def to_palette(frames):
    colours = {}
    for im in frames:
        for _, c in im.getcolors(1 << 20):
            colours.setdefault(c, len(colours))
    flat = [v for c in sorted(colours, key=colours.get) for v in c]
    flat += [0] * (768 - len(flat))
    out = []
    for im in frames:
        p = Image.new("P", im.size)
        p.putpalette(flat)
        get = im.get_flattened_data if hasattr(im, "get_flattened_data") else im.getdata
        p.putdata([colours[c] for c in get()])
        out.append(p)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--login", default=os.environ.get("GH_LOGIN", "PatchNote0"))
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--offline", action="store_true")
    g.add_argument("--demo", action="store_true")
    ap.add_argument("--out", default=None, help="write somewhere other than assets/ (testing)")
    a = ap.parse_args()
    global ASSETS
    if a.out:
        ASSETS = a.out
    mode = "demo" if a.demo else "offline" if a.offline else "fetch"
    data = load(mode, a.login)
    render(data)
    lit = "no data" if not data else f"{data.get('source')} data, {len(data['days'])} days"
    print(f"drew the sequencer from {lit}")


if __name__ == "__main__":
    main()
