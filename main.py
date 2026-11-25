#!/usr/bin/env python3
"""news-image-20261125 v1 — "One Day, One World".

A one-page newspaper, 1024x1024, summing up Wednesday 25 November
2026: 30 stories, 7 regions. Three lead stories carry real Wikimedia
photographs (file photos); the ten mid stories and the world map are
flat illustrations drawn in code. Python 3.13 stdlib only, no network
at grading time: main.py reads atlas.bin.gz and photo_*.rgb.gz from
its own directory and writes $MAKEFUN_OUTPUT_DIR/entry.png
(or ./output/entry.png when the variable is unset).

Deterministic: fixed zlib level, no timestamps, no randomness, no
iteration over unordered data. Two runs write byte-identical PNGs.
"""
import gzip
import os
import struct
import sys
import zlib

W, H = 1024, 1024
HERE = os.path.dirname(os.path.abspath(__file__))

# Palette — newsprint paper, ink, one red accent, muted blues/greys.
PAPER = (247, 243, 234)
INK = (22, 22, 22)
RED = (176, 30, 36)
NAVY = (31, 58, 95)
GREY = (96, 96, 96)
FAINT = (216, 210, 196)
PALE = (238, 233, 220)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SKY = (186, 210, 228)
SEA = (172, 202, 226)
LAND = (233, 226, 206)
STEEL = (74, 82, 92)
SMOKE = (120, 120, 118)
GOLD = (214, 164, 32)
GREEN = (46, 125, 60)
TEAL = (32, 110, 110)


# ---------------------------------------------------------------- PNG out
def _chunk(ctype, data):
    out = struct.pack(">I", len(data)) + ctype + data
    out += struct.pack(">I", zlib.crc32(ctype + data) & 0xFFFFFFFF)
    return out


def write_png(path, w, h, rgb):
    """Write RGB bytes (row-major, 3 bytes/px) as a deterministic PNG."""
    raw = bytearray()
    stride = w * 3
    for y in range(h):
        raw.append(0)
        raw += rgb[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 6)
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    png += _chunk(b"IDAT", comp)
    png += _chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


# ---------------------------------------------------------------- assets
def load_atlas(path):
    """Parse atlas.bin.gz into {name: (px, ascent, {cp: glyph})}.

    Glyph tuple: (advance, xoff, yoff, w, h, packed_rows).
    Format written by build_assets.py: magic b"ATL3", u32 font count;
    per font: u8 name length, name, u16 px, u16 ascent, u16 descent,
    u16 glyph count; per glyph: u32 cp, u16 advance, i16 xoff,
    i16 yoff, u16 w, u16 h, then the packed rows.
    """
    raw = gzip.open(path, "rb").read()
    assert raw[:4] == b"ATL3", "bad atlas magic"
    pos = 4
    nfonts = struct.unpack_from(">I", raw, pos)[0]
    pos += 4
    fonts = {}
    for _ in range(nfonts):
        nlen = raw[pos]
        pos += 1
        name = raw[pos:pos + nlen].decode("ascii")
        pos += nlen
        px, ascent, descent, ng = struct.unpack_from(">HHHH", raw, pos)
        pos += 8
        glyphs = {}
        for _ in range(ng):
            cp, adv, xoff, yoff, gw, gh = struct.unpack_from(">IHhhHH", raw, pos)
            pos += 14
            stride = (gw + 7) // 8
            packed = raw[pos:pos + stride * gh]
            pos += stride * gh
            glyphs[cp] = (adv, xoff, yoff, gw, gh, packed)
        fonts[name] = (px, ascent, glyphs)
    return fonts


def load_photo(name):
    """Load photo_<name>.rgb.gz (raw RGB bytes, size known by caller)."""
    path = os.path.join(HERE, f"photo_{name}.rgb.gz")
    return gzip.open(path, "rb").read()


# ---------------------------------------------------------------- canvas
class Page:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(color)

    def rect(self, x0, y0, x1, y1, color):
        x0 = max(0, x0)
        y0 = max(0, y0)
        x1 = min(self.w, x1)
        y1 = min(self.h, y1)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(color) * (x1 - x0)
        for y in range(y0, y1):
            i = (y * self.w + x0) * 3
            self.px[i:i + (x1 - x0) * 3] = row

    def hline(self, x0, x1, y, color, thick=1):
        for t in range(thick):
            self.rect(x0, y + t, x1, y + t + 1, color)

    def vline(self, x, y0, y1, color, thick=1):
        for t in range(thick):
            self.rect(x + t, y0, x + t + 1, y1, color)

    def disc(self, cx, cy, r, color):
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r, cx + r + 1):
                if (x - cx) * (x - cx) + (y - cy) * (y - cy) <= r * r:
                    self.set(x, y, color)

    def line(self, x0, y0, x1, y1, color, thick=1):
        """Bresenham line with square thickness."""
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        x, y = x0, y0
        half = thick // 2
        while True:
            self.rect(x - half, y - half, x - half + thick, y - half + thick,
                      color)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy

    def poly(self, pts, color):
        """Scanline fill of a simple polygon (even-odd rule)."""
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        for y in range(max(0, min(ys)), min(self.h, max(ys) + 1)):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    t = (y - y0) / (y1 - y0)
                    xs.append(x0 + t * (x1 - x0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self.rect(int(xs[i]), y, int(xs[i + 1]) + 1, y + 1, color)

    def blit(self, x0, y0, w, h, rgb):
        """Copy raw RGB rows onto the page, clipped."""
        for y in range(h):
            yy = y0 + y
            if yy < 0 or yy >= self.h:
                continue
            row = rgb[y * w * 3:(y + 1) * w * 3]
            sx0 = max(0, -x0)
            sx1 = min(w, self.w - x0)
            if sx1 <= sx0:
                continue
            i = (yy * self.w + x0 + sx0) * 3
            self.px[i:i + (sx1 - sx0) * 3] = row[sx0 * 3:sx1 * 3]


# ---------------------------------------------------------------- text
class Typer:
    def __init__(self, fonts):
        self.fonts = fonts

    def width(self, font_name, text):
        _, _, glyphs = self.fonts[font_name]
        total = 0
        for ch in text:
            g = glyphs.get(ord(ch))
            if g is None:
                g = glyphs.get(32)
            total += g[0]
        return total

    def draw(self, page, font_name, x, baseline, text, color):
        _, _, glyphs = self.fonts[font_name]
        pen = x
        for ch in text:
            g = glyphs.get(ord(ch))
            if g is None:
                g = glyphs.get(32)
            adv, xoff, yoff, gw, gh, packed = g
            if gw and gh:
                stride = (gw + 7) // 8
                for gy in range(gh):
                    for gx in range(gw):
                        if packed[gy * stride + gx // 8] & (0x80 >> (gx % 8)):
                            page.set(pen + xoff + gx, baseline + yoff + gy,
                                     color)
            pen += adv
        return pen

    def draw_centred(self, page, font_name, cx, baseline, text, color):
        w = self.width(font_name, text)
        return self.draw(page, font_name, cx - w // 2, baseline, text, color)

    def wrap(self, font_name, text, max_w):
        """Greedy word wrap; returns lines that fit max_w."""
        words = text.split(" ")
        lines = []
        cur = ""
        for word in words:
            trial = word if not cur else cur + " " + word
            if self.width(font_name, trial) <= max_w:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        return lines

    def draw_wrapped(self, page, font_name, x, baseline, text, color,
                     max_w, line_h, max_lines=None):
        lines = self.wrap(font_name, text, max_w)
        if max_lines is not None:
            lines = lines[:max_lines]
        y = baseline
        for line in lines:
            self.draw(page, font_name, x, y, line, color)
            y += line_h
        return y


# ---------------------------------------------------------------- stories
# Every number below appears in exactly one version on the page.
# Wires read to 07:00 UTC, Wednesday 25 November 2026.
# Sources: Reuters, AP, BBC, WSJ, The Hindu, ICJ, UEFA.

MASTHEAD = "ONE DAY, ONE WORLD"
DATE_LINE = "WEDNESDAY, 25 NOVEMBER 2026"
SUBHEAD = ("30 STORIES \u00b7 7 REGIONS \u00b7 EVERY ONE DATED "
           "WEDNESDAY 25 NOVEMBER 2026")

STATS = [
    ("11", "WOUNDED"),
    ("227", "METRES"),
    ("25", "VIOLATIONS"),
    ("25", "HOSTAGES"),
    ("5.6", "QUAKE"),
    ("$41B", "SANOFI"),
]

STRIP = ("RIYADH \u2014 11 HURT, HOUTHIS HIT PIF TOWER \u00b7 KERCH SPAN DOWN "
         "\u00b7 ABU DHABI TALKS FAIL \u00b7 NATO AWACS TO POLAND \u00b7 "
         "25 HOSTAGES IN CARTAGENA")

REGIONS = [
    ("NORTH AMERICA", 4, (31, 58, 95)),
    ("EUROPE", 6, (176, 30, 36)),
    ("MIDDLE EAST", 5, (214, 164, 32)),
    ("ASIA-PACIFIC", 7, (46, 125, 60)),
    ("AFRICA", 3, (120, 82, 40)),
    ("LATAM", 2, (32, 110, 110)),
    ("SPORT", 3, (74, 82, 92)),
]

LEAD = {
    "kicker": "MIDDLE EAST \u2014 CONFIRMED \u00b7 REUTERS",
    "headline": "HOUTHIS HIT RIYADH'S TALLEST TOWER, 11 HURT",
    "deck": ("Yemen's Houthis strike the PIF Tower in Riyadh for the "
             "second time in under a week; Saudi Civil Defense says 11 "
             "wounded \u2014 2 Saudis, 2 Indians, 3 Nepalis, 4 Egyptians. "
             "The first strike on 19 Nov damaged floors, no injuries."),
    "photo": "riyadh",
    "caption": "King Abdullah Financial District, Riyadh (file photo)",
}

CARDS = [
    {
        "kicker": "UKRAINE WAR \u2014 CONFIRMED \u00b7 REUTERS",
        "headline": "KERCH SPAN DOWN AS ABU DHABI TALKS FAIL",
        "deck": ("Ukraine hits the Kerch Bridge a third time this week \u2014 "
                 "a 227-metre road arch span falls; US-mediated talks in "
                 "Abu Dhabi end with no breakthrough."),
        "photo": "kerch",
        "caption": "The Kerch Bridge road arch span (file photo)",
    },
    {
        "kicker": "NATO \u2014 CONFIRMED \u00b7 REUTERS",
        "headline": "NATO SENDS EARLY-WARNING JETS TO POLAND",
        "deck": ("NATO sends early-warning aircraft to Poland after Russian "
                 "drones breach Polish airspace; 25 violations against "
                 "NATO members counted in 2026."),
        "photo": "awacs",
        "caption": "A NATO E-3 Sentry (file photo)",
    },
]

# Ten mid stories, 4-13. Each tile: a flat illustration drawn in code
# (key = the scene function in SCENES below), a kicker with its
# certainty tag, and a headline. No deck — the tile is 188px wide.
MIDS = [
    {"n": 4, "scene": "globe", "bg": (222, 236, 244),
     "kicker": "CLIMATE \u2014 REPORTED",
     "headline": "EU SEEKS POST-COP31 CLIMATE OVERHAUL"},
    {"n": 5, "scene": "chart", "bg": (244, 228, 228),
     "kicker": "MARKETS \u2014 REPORTED",
     "headline": "ANTHROPIC FALLS BELOW ITS IPO PRICE"},
    {"n": 6, "scene": "store", "bg": (238, 233, 220),
     "kicker": "COLOMBIA \u2014 REPORTED",
     "headline": "25 HOSTAGES SEIZED IN CARTAGENA SUPERMARKET"},
    {"n": 7, "scene": "quake", "bg": (228, 228, 232),
     "kicker": "QUAKE \u2014 CONFIRMED",
     "headline": "5.6 QUAKE SHAKES NEPAL NEAR CHINA BORDER"},
    {"n": 8, "scene": "scales", "bg": (222, 236, 244),
     "kicker": "JUSTICE \u2014 CONFIRMED",
     "headline": "14 NATIONS BACK MYANMAR RULING"},
    {"n": 9, "scene": "capsule", "bg": (232, 240, 232),
     "kicker": "PHARMA \u2014 CONFIRMED",
     "headline": "SANOFI TO BUY INSMED FOR $41BN"},
    {"n": 10, "scene": "bat", "bg": (238, 233, 220),
     "kicker": "CRICKET \u2014 CONFIRMED",
     "headline": "ENGLAND LEVEL T20 SERIES IN SYDNEY"},
    {"n": 11, "scene": "stumps", "bg": (222, 236, 244),
     "kicker": "CRICKET \u2014 CONFIRMED",
     "headline": "NEW ZEALAND HOLD INDIA TO A DRAW"},
    {"n": 12, "scene": "tanker", "bg": (228, 228, 232),
     "kicker": "HORMUZ \u2014 CLAIM",
     "headline": "IRAN CLAIMS 3 TANKERS HIT BY MINES"},
    {"n": 13, "scene": "office", "bg": (244, 228, 228),
     "kicker": "KOREA \u2014 REPORTED",
     "headline": "PYONGYANG THREATENS TO SHUT SWISS OFFICE"},
]

ALSO = [
    "GAZA \u2014 EISENKOT CALLS ARSON \u2018TERRORISM\u2019",
    "UKRAINE AID \u2014 NORWAY PLEDGES $7BN FOR 2027",
    "UKRAINE \u2014 ZELENSKY: NEEDS \u20ac115BN IN 2027",
    "RUSSIA \u2014 432,519 CASUALTIES, KYIV CLAIMS",
    "NATO \u2014 VOWS SPACE DEFENCE",
    "MANCHESTER \u2014 12,000 EVACUATED AT CONCERT",
    "GIULIANI \u2014 TRUMP AWARDS MEDAL OF FREEDOM",
    "TARIFFS \u2014 TRUMP SET TO UNVEIL NEW WAVE",
    "DENMARK \u2014 COURT UPHOLDS \u2018GHETTO\u2019 EVICTIONS",
    "ISRAEL \u2014 ARMY SUICIDES HIT 16-YEAR HIGH",
    "MEXICO \u2014 \u2018EL CHAPO ISIDRO\u2019 TRIED AT HOME",
    "TRIPOLI \u2014 DEMANDS ANSWERS FROM KYIV",
    "ZAPORIZHZHIA \u2014 STRIKES KILL 2, WOUND 30+",
    "INDIA \u2014 MODI, MERZ HOLD GERMANY TALKS",
    "SENSEX \u2014 DROPS 1,484 POINTS",
    "FOOTBALL \u2014 REAL MADRID HIT PSV FOR FIVE",
    "SPACE \u2014 ASTEROID ECLIPSE IMAGED",
]

DATE_CHECK = ("DATE CHECK \u2014 Wires to 07:00 UTC, 25 Nov 2026. Left out: "
              "COP31 collapse (22 Nov) \u00b7 Nvidia +31% (23 Nov) \u00b7 "
              "ICJ ruling (19 Nov) \u00b7 Korea minister (22 Nov). "
              "Sources: Reuters, AP, BBC, WSJ.")

# World map pins: (story no., longitude, latitude, nudge dx, nudge dy).
# Pins 1-3 are the leads, 4-13 the mids.
PINS = [
    (1, 46.7, 24.7, 0, 0),      # Riyadh
    (2, 36.5, 45.3, 0, 0),      # Kerch
    (3, 21.0, 52.2, 0, 0),      # Warsaw
    (4, 30.7, 36.9, -6, 6),     # Antalya (COP31)
    (5, -122.4, 37.8, 0, 0),    # San Francisco (Anthropic)
    (6, -75.5, 10.4, 0, 0),     # Cartagena
    (7, 85.0, 28.0, 0, 0),      # Nepal
    (8, 96.2, 16.8, 0, 0),      # Yangon
    (9, 2.35, 48.85, 0, 0),     # Paris (Sanofi)
    (10, 151.2, -33.9, 0, 0),   # Sydney
    (11, 72.8, 19.1, 0, 0),     # Mumbai
    (12, 56.5, 26.6, 6, -5),    # Strait of Hormuz
    (13, 125.75, 39.0, 0, 0),   # Pyongyang
]

# Simplified continent outlines (lon, lat), drawn as flat landmasses.
CONTINENTS = [
    # North America
    [(-168, 66), (-158, 58), (-152, 60), (-140, 60), (-130, 54),
     (-125, 49), (-124, 42), (-120, 34), (-114, 29), (-110, 24),
     (-105, 20), (-97, 16), (-94, 17), (-90, 14), (-86, 12),
     (-83, 9), (-79, 9), (-81, 13), (-84, 16), (-87, 21),
     (-90, 21), (-91, 19), (-97, 26), (-93, 30), (-89, 30),
     (-84, 30), (-81, 25), (-80, 32), (-76, 35), (-74, 40),
     (-70, 42), (-68, 45), (-65, 44), (-60, 47), (-55, 47),
     (-60, 52), (-64, 58), (-68, 58), (-72, 62), (-78, 62),
     (-85, 66), (-92, 66), (-95, 69), (-110, 68), (-125, 70),
     (-140, 70), (-155, 71), (-165, 68)],
    # South America
    [(-79, 9), (-77, 4), (-80, -3), (-81, -6), (-77, -12),
     (-72, -18), (-70, -23), (-70, -30), (-72, -37), (-73, -44),
     (-74, -50), (-69, -52), (-66, -55), (-68, -50), (-65, -45),
     (-62, -41), (-58, -35), (-52, -32), (-48, -28), (-41, -23),
     (-39, -17), (-35, -9), (-35, -6), (-40, -3), (-44, -2),
     (-50, 0), (-53, 4), (-58, 6), (-62, 9), (-68, 11),
     (-72, 12), (-76, 10)],
    # Eurasia
    [(-10, 36), (-9, 43), (-2, 44), (-4, 48), (0, 51), (3, 53),
     (8, 57), (10, 59), (5, 62), (12, 65), (18, 69), (30, 70),
     (45, 68), (60, 69), (68, 70), (70, 68), (75, 72), (90, 75),
     (105, 73), (120, 70), (135, 62), (142, 59), (142, 54),
     (141, 50), (138, 46), (132, 43), (127, 40), (122, 38),
     (120, 35), (122, 31), (118, 25), (110, 21), (106, 20),
     (108, 18), (105, 9), (103, 1), (100, 8), (95, 16),
     (91, 22), (88, 22), (85, 19), (80, 13), (80, 7),
     (76, 10), (72, 20), (66, 25), (60, 25), (57, 26),
     (54, 27), (50, 29), (48, 30), (44, 30), (43, 29),
     (40, 31), (36, 33), (36, 36), (30, 36), (26, 38),
     (23, 36), (19, 40), (15, 44), (12, 44), (8, 44),
     (3, 42), (0, 40), (-2, 37), (-6, 36)],
    # Africa
    [(-6, 35), (-10, 31), (-15, 27), (-17, 21), (-17, 15),
     (-15, 11), (-13, 8), (-8, 5), (-4, 5), (2, 6), (6, 4),
     (9, 4), (9, 0), (12, -4), (13, -8), (12, -12), (13, -17),
     (12, -22), (14, -27), (16, -29), (19, -34), (20, -35),
     (25, -34), (28, -33), (32, -29), (35, -24), (36, -20),
     (40, -15), (40, -10), (42, -5), (46, -1), (51, 2),
     (51, 11), (48, 11), (44, 11), (40, 15), (39, 18),
     (37, 22), (35, 28), (33, 31), (30, 31), (25, 32),
     (20, 32), (15, 32), (11, 34), (10, 37), (5, 37),
     (0, 36)],
    # Australia
    [(113, -22), (114, -30), (115, -34), (118, -35), (124, -33),
     (129, -32), (132, -32), (135, -35), (138, -35), (140, -38),
     (142, -39), (145, -38), (147, -39), (150, -37), (153, -32),
     (153, -27), (150, -23), (146, -19), (142, -11), (142, -15),
     (137, -12), (135, -12), (132, -12), (130, -13), (126, -14),
     (122, -17), (118, -20), (114, -22)],
    # United Kingdom
    [(-5, 50), (-3, 53), (-5, 56), (-3, 58), (-1, 57), (0, 53),
     (1, 51), (-3, 50)],
    # Japan
    [(130, 31), (132, 33), (134, 34), (136, 35), (138, 35),
     (140, 37), (141, 39), (141, 41), (140, 43), (142, 44),
     (144, 44), (143, 42), (141, 40), (139, 38), (137, 36),
     (135, 34), (133, 34), (131, 32)],
    # New Zealand
    [(167, -45), (168, -47), (170, -43), (174, -41), (176, -38),
     (178, -38), (175, -40), (172, -43), (168, -46)],
]


# ---------------------------------------------------------------- scenes
# Flat illustrations for the ten mid tiles. Each draws inside the box
# (x, y, w, h) — the caller paints the tile background first.

def _scene_globe(page, x, y, w, h):
    page.disc(x + 158, y + 12, 8, GOLD)
    page.disc(x + 46, y + 27, 19, (58, 124, 188))
    page.disc(x + 40, y + 20, 5, GREEN)
    page.disc(x + 54, y + 30, 6, GREEN)
    page.disc(x + 38, y + 34, 4, GREEN)
    page.disc(x + 52, y + 16, 3, GREEN)
    page.hline(x + 8, x + w - 8, y + 48, GREEN, 2)


def _scene_chart(page, x, y, w, h):
    page.hline(x + 10, x + w - 10, y + 16, FAINT, 1)
    page.hline(x + 10, x + w - 10, y + 30, FAINT, 1)
    page.hline(x + 10, x + w - 10, y + 44, FAINT, 1)
    page.line(x + 12, y + 10, x + 12, y + 46, STEEL, 1)
    page.line(x + 12, y + 46, x + w - 12, y + 46, STEEL, 1)
    page.line(x + 16, y + 12, x + 60, y + 20, RED, 2)
    page.line(x + 60, y + 20, x + 110, y + 28, RED, 2)
    page.line(x + 110, y + 28, x + 164, y + 42, RED, 2)
    page.poly([(x + 164, y + 42), (x + 154, y + 38), (x + 158, y + 48)],
              RED)


def _scene_store(page, x, y, w, h):
    for i in range(8):
        col = RED if i % 2 == 0 else WHITE
        page.rect(x + 8 + i * 22, y + 6, x + 8 + (i + 1) * 22, y + 18, col)
    page.rect(x + 8, y + 18, x + w - 8, y + 48, (214, 204, 184))
    page.rect(x + 80, y + 30, x + 108, y + 48, STEEL)
    page.rect(x + 22, y + 26, x + 62, y + 40, (150, 190, 220))
    page.rect(x + 126, y + 26, x + 166, y + 40, (150, 190, 220))


def _scene_quake(page, x, y, w, h):
    page.poly([(x + 8, y + 48), (x + 58, y + 8), (x + 108, y + 48)],
              (120, 140, 160))
    page.poly([(x + 44, y + 20), (x + 58, y + 8), (x + 72, y + 20)],
              WHITE)
    page.poly([(x + 88, y + 48), (x + 138, y + 14), (x + 180, y + 48)],
              (90, 108, 132))
    page.poly([(x + 128, y + 22), (x + 138, y + 14), (x + 148, y + 22)],
              WHITE)
    page.line(x + 96, y + 48, x + 104, y + 44, INK, 2)
    page.line(x + 104, y + 44, x + 98, y + 40, INK, 2)
    page.line(x + 98, y + 40, x + 106, y + 36, INK, 2)
    page.disc(x + 140, y + 30, 3, RED)


def _scene_scales(page, x, y, w, h):
    page.rect(x + 92, y + 8, x + 96, y + 46, STEEL)
    page.rect(x + 78, y + 46, x + 110, y + 49, STEEL)
    page.line(x + 40, y + 14, x + 148, y + 14, STEEL, 2)
    page.poly([(x + 30, y + 30), (x + 50, y + 30), (x + 40, y + 16)],
              GOLD)
    page.poly([(x + 138, y + 30), (x + 158, y + 30), (x + 148, y + 16)],
              GOLD)
    page.line(x + 40, y + 14, x + 40, y + 18, STEEL, 1)
    page.line(x + 148, y + 14, x + 148, y + 18, STEEL, 1)


def _scene_capsule(page, x, y, w, h):
    page.rect(x + 46, y + 20, x + 142, y + 34, WHITE)
    page.disc(x + 46, y + 27, 7, WHITE)
    page.disc(x + 142, y + 27, 7, WHITE)
    page.rect(x + 46, y + 20, x + 94, y + 34, RED)
    page.disc(x + 46, y + 27, 7, RED)
    page.line(x + 94, y + 20, x + 94, y + 34, RED, 1)
    page.rect(x + 158, y + 22, x + 162, y + 32, GREEN)
    page.rect(x + 153, y + 25, x + 167, y + 29, GREEN)


def _scene_bat(page, x, y, w, h):
    page.rect(x + 82, y + 6, x + 90, y + 20, (140, 100, 60))
    page.rect(x + 70, y + 20, x + 102, y + 48, (216, 188, 140))
    page.rect(x + 70, y + 20, x + 74, y + 48, (180, 150, 100))
    page.disc(x + 148, y + 38, 8, RED)
    page.line(x + 142, y + 34, x + 154, y + 42, WHITE, 1)


def _scene_stumps(page, x, y, w, h):
    for i in range(3):
        page.rect(x + 66 + i * 12, y + 12, x + 66 + i * 12 + 6, y + 44,
                  GOLD)
    page.rect(x + 68, y + 8, x + 80, y + 12, GOLD)
    page.rect(x + 84, y + 8, x + 96, y + 12, GOLD)
    page.disc(x + 142, y + 36, 8, RED)
    page.line(x + 136, y + 32, x + 148, y + 40, WHITE, 1)


def _scene_tanker(page, x, y, w, h):
    page.rect(x + 20, y + 26, x + 148, y + 40, (40, 48, 60))
    page.poly([(x + 148, y + 26), (x + 168, y + 33), (x + 148, y + 40)],
              (40, 48, 60))
    page.rect(x + 56, y + 16, x + 72, y + 26, RED)
    page.rect(x + 84, y + 20, x + 128, y + 26, WHITE)
    page.hline(x + 8, x + 60, y + 46, (58, 124, 188), 2)
    page.hline(x + 90, x + 170, y + 46, (58, 124, 188), 2)
    page.hline(x + 30, x + 140, y + 50, (58, 124, 188), 2)
    page.disc(x + 168, y + 12, 5, BLACK)
    page.line(x + 168, y + 4, x + 168, y + 20, BLACK, 1)
    page.line(x + 160, y + 12, x + 176, y + 12, BLACK, 1)


def _scene_office(page, x, y, w, h):
    page.rect(x + 62, y + 10, x + 122, y + 50, (120, 128, 140))
    for r in range(4):
        for c in range(3):
            page.rect(x + 70 + c * 16, y + 16 + r * 9,
                      x + 78 + c * 16, y + 22 + r * 9, (220, 228, 235))
    page.line(x + 92, y + 2, x + 92, y + 10, STEEL, 1)
    page.rect(x + 92, y + 2, x + 104, y + 7, RED)
    page.line(x + 62, y + 10, x + 122, y + 50, RED, 2)
    page.line(x + 122, y + 10, x + 62, y + 50, RED, 2)


SCENES = {
    "globe": _scene_globe,
    "chart": _scene_chart,
    "store": _scene_store,
    "quake": _scene_quake,
    "scales": _scene_scales,
    "capsule": _scene_capsule,
    "bat": _scene_bat,
    "stumps": _scene_stumps,
    "tanker": _scene_tanker,
    "office": _scene_office,
}

PHOTO_SIZE = {"riyadh": (440, 210), "kerch": (476, 126), "awacs": (476, 126)}


# ---------------------------------------------------------------- map
def draw_map(page, t, x0, y0, w, h):
    page.rect(x0, y0, x0 + w, y0 + h, SEA)

    def px(lon):
        return x0 + (lon + 170.0) / 360.0 * w

    def py(lat):
        return y0 + (78.0 - lat) / 136.0 * h

    for cont in CONTINENTS:
        pts = [(int(px(lon)), int(py(lat))) for lon, lat in cont]
        page.poly(pts, LAND)
    t.draw(page, "map9", x0 + 4, y0 + 10, "WORLD \u2014 PINS 1\u201313", NAVY)
    for n, lon, lat, dx, dy in PINS:
        cx = int(px(lon)) + dx
        cy = int(py(lat)) + dy
        page.disc(cx, cy, 6, WHITE)
        page.disc(cx, cy, 5, RED)
        t.draw_centred(page, "map9", cx, cy + 3, str(n), WHITE)
    page.hline(x0, x0 + w, y0, STEEL, 1)
    page.hline(x0, x0 + w, y0 + h - 1, STEEL, 1)
    page.vline(x0, y0, y0 + h, STEEL, 1)
    page.vline(x0 + w - 1, y0, y0 + h, STEEL, 1)


# ---------------------------------------------------------------- render
def render(fonts, photos):
    page = Page(W, H, PAPER)
    t = Typer(fonts)

    # Masthead.
    t.draw_centred(page, "mast", 512, 48, MASTHEAD, INK)
    page.hline(28, 996, 58, RED, 3)
    t.draw_centred(page, "date", 512, 86, DATE_LINE, RED)
    t.draw_centred(page, "sub", 512, 104, SUBHEAD, NAVY)

    # Stat bar: six big numbers, one consistent version each.
    for i, (num, lab) in enumerate(STATS):
        x = 28 + i * 162
        page.rect(x, 110, x + 158, 150, PALE)
        page.hline(x, x + 158, 110, RED, 2)
        t.draw_centred(page, "stat20", x + 79, 135, num, RED)
        t.draw_centred(page, "stat10", x + 79, 147, lab, INK)

    # Day strip.
    t.draw_centred(page, "strip11", 512, 168, STRIP, INK)

    # Region bar: segment widths proportional to story counts.
    x = 28
    cum = 0
    for name, cnt, col in REGIONS:
        cum += cnt
        x_end = 28 + round(cum / 30.0 * 968)
        page.rect(x, 174, x_end, 190, col)
        t.draw_centred(page, "sub", (x + x_end) // 2, 186,
                       f"{name} {cnt}", WHITE)
        x = x_end

    # Lead story 1, photo left, text right.
    pw, ph = PHOTO_SIZE["riyadh"]
    page.blit(28, 196, pw, ph, photos["riyadh"])
    page.rect(28, 196, 52, 220, RED)
    t.draw_centred(page, "kick12", 40, 213, "1", WHITE)
    page.rect(28, 390, 468, 406, BLACK)
    t.draw(page, "check10", 36, 402, LEAD["caption"], WHITE)
    t.draw(page, "kick12", 484, 212, LEAD["kicker"], RED)
    hlines = t.wrap("head28", LEAD["headline"], 512)
    t.draw_wrapped(page, "head28", 484, 248, LEAD["headline"], INK,
                   512, 33, 3)
    deck_y = 248 + (len(hlines) - 1) * 33 + 27
    t.draw_wrapped(page, "deck14", 484, deck_y, LEAD["deck"], INK,
                   512, 19, 4)

    # Lead stories 2 and 3, side by side.
    for i, card in enumerate(CARDS):
        cx = 28 + i * 492
        pw, ph = PHOTO_SIZE[card["photo"]]
        page.blit(cx, 414, pw, ph, photos[card["photo"]])
        page.rect(cx, 414, cx + 24, 438, RED)
        t.draw_centred(page, "kick12", cx + 12, 431, str(i + 2), WHITE)
        page.rect(cx, 524, cx + 476, 540, BLACK)
        t.draw(page, "check10", cx + 8, 536, card["caption"], WHITE)
        t.draw(page, "kick12", cx, 554, card["kicker"], RED)
        hlines = t.wrap("head21", card["headline"], 476)
        t.draw_wrapped(page, "head21", cx, 580, card["headline"],
                       INK, 476, 25, 2)
        deck_y = 580 + (len(hlines) - 1) * 25 + 19
        t.draw_wrapped(page, "deck12", cx, deck_y, card["deck"], INK,
                       476, 15, 2)

    # Mid stories 4-13, two rows of five illustrated tiles.
    for row in range(2):
        for col in range(5):
            mid = MIDS[row * 5 + col]
            tx = 28 + col * 195
            ty = 646 + row * 102
            page.rect(tx, ty, tx + 188, ty + 54, mid["bg"])
            SCENES[mid["scene"]](page, tx, ty, 188, 54)
            t.draw(page, "kick12", tx, ty + 66,
                   f"{mid['n']} \u00b7 {mid['kicker']}", RED)
            t.draw_wrapped(page, "kick12", tx, ty + 82, mid["headline"],
                           INK, 188, 14, 2)

    # World map + ALSO ON list.
    t.draw(page, "kick12", 28, 870, "ALSO ON \u2014 17 MORE STORIES", RED)
    page.hline(28, 996, 876, RED, 2)
    draw_map(page, t, 28, 882, 340, 112)
    for i, item in enumerate(ALSO):
        col = i // 9
        row = i % 9
        ax = 384 + col * 300
        ay = 894 + row * 12
        num = f"{14 + i}. "
        t.draw(page, "also10", ax, ay, num, RED)
        t.draw(page, "also10", ax + t.width("also10", num), ay, item, INK)

    # Date check + sources.
    page.rect(28, 1000, 32, 1014, RED)
    t.draw(page, "check10", 38, 1012, DATE_CHECK, INK)
    return page


def main():
    fonts = load_atlas(os.path.join(HERE, "atlas.bin.gz"))
    photos = {name: load_photo(name) for name in PHOTO_SIZE}
    page = render(fonts, photos)
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR") or os.path.join(HERE, "output")
    os.makedirs(outdir, exist_ok=True)
    write_png(os.path.join(outdir, "entry.png"), W, H, bytes(page.px))
    print("wrote entry.png")


if __name__ == "__main__":
    sys.exit(main())
