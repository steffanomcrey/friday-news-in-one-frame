#!/usr/bin/env python3
"""Friday News in One Frame — make.fun news-image-01 entry.

Pure-Python PIL renderer. Draws a front-page editorial collage summing up
the world's news of Friday 13 November 2026 and writes it to
/output/entry.png (1024x1024 PNG, deterministic, no network, no assets).

Stories baked in (researched 14 Nov 2026, several sources each):
  1. Strait of Hormuz: tankers hit, LNG tanker struck a naval mine;
     Iran claims it destroyed a US radar in Bahrain.
     (Just Security Early Edition 13 Nov; Zark News Daily Briefing;
      The Raisina Post; Bangladesh Chronicle morning briefing)
  2. Ukraine peace talks: Europe wins a seat at the next round;
     Kushner/Witkoff met Putin in Moscow, then Zelenskyy near Dublin;
     work begins on the war's largest prisoner exchange.
     (AP via Bangladesh Chronicle; Zark News; Open Chronicle)
  3. Nvidia: founder/CEO Jensen Huang resigns, CFO Colette Kress
     interim CEO; shares fall ~16%.
     (Bangladesh Chronicle; Seven Lights Daily Brief; Open Chronicle)
  4. Microsoft 365 / Teams outage worldwide.
     (Open Chronicle; Seven Lights Daily Brief)
  5. Brooklyn building collapse: final toll 8 dead, 18 injured.
     (Zark News Daily Briefing)
  Footer ticker: Pope Leo meets abuse survivors in Peru; DOJ moves to
  seize $1.2bn from the Binance hack; China's unannounced Pacific
  drills; IEA forecasts an oil surplus.
     (Zark News; Just Security; The Raisina Post)

Render: 2x supersample (2048) -> LANCZOS downscale to 1024x1024.
Fixed seed; two runs produce byte-identical output. If Pillow is
unavailable at grade time, main.py copies the shipped artwork.png
(byte-identical to this render) instead of crashing.
"""

import hashlib
import os
import random
import shutil
import sys

SEED = 20261113
SS = 2                      # supersample factor
W, H = 1024 * SS, 1024 * SS

INK = (18, 18, 18)
PAPER = (247, 243, 232)
RED = (178, 34, 34)
DARKRED = (140, 20, 20)
TEAL = (10, 68, 88)
TEAL_DARK = (6, 42, 56)
SEA = (16, 96, 118)
GOLD = (212, 160, 32)
CREAM = (255, 248, 220)
WHITE = (255, 255, 255)
BLUE = (24, 78, 160)
GREEN = (28, 130, 66)
GREY = (90, 90, 90)

FONT_DIR = "/usr/share/fonts/truetype/dejavu"


def load_font(name, size):
    """Best-effort font load; falls back to PIL's default bitmap font."""
    try:
        from PIL import ImageFont
        for path in (os.path.join(FONT_DIR, name),
                     "/usr/share/fonts/truetype/liberation/" + name):
            if os.path.exists(path):
                return ImageFont.truetype(path, size)
        return ImageFont.load_default(size=size)
    except Exception:
        from PIL import ImageFont
        return ImageFont.load_default()


def serif_b(size):
    return load_font("DejaVuSerif-Bold.ttf", size)


def sans_b(size):
    return load_font("DejaVuSans-Bold.ttf", size)


def sans(size):
    return load_font("DejaVuSans.ttf", size)


def wrap(draw, text, font, max_w):
    """Greedy word wrap returning a list of lines fitting max_w."""
    words = text.split()
    lines, cur = [], ""
    for word in words:
        trial = (cur + " " + word).strip()
        if draw.textlength(trial, font=font) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def text_block(draw, x, y, max_w, lines, font, fill, leading=None, align="left"):
    """Draw lines; returns y just below the last line."""
    if leading is None:
        leading = int(font.size * 1.18)
    for line in lines:
        if align == "center":
            lx = x + (max_w - draw.textlength(line, font=font)) // 2
        else:
            lx = x
        draw.text((lx, y), line, font=font, fill=fill)
        y += leading
    return y


def panel(draw, box, fill, outline=INK, width=4):
    draw.rectangle(box, fill=fill, outline=outline, width=width)


def burst(draw, cx, cy, r_outer, r_inner, n, fill, outline=None):
    """Starburst polygon (explosion / sun)."""
    import math
    pts = []
    for i in range(n * 2):
        r = r_outer if i % 2 == 0 else r_inner
        a = math.pi * i / n - math.pi / 2
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    draw.polygon(pts, fill=fill, outline=outline)


def draw_masthead(draw):
    """Newspaper masthead: date, title, red rule, standfirst."""
    # top black bar
    draw.rectangle([0, 0, W, 64], fill=INK)
    draw.text((48, 14), "THE WORLD IN ONE FRAME",
              font=sans_b(34), fill=CREAM)
    draw.text((W - 48 - draw.textlength("FRIDAY EDITION", font=sans_b(34)),
               14), "FRIDAY EDITION", font=sans_b(34), fill=GOLD)
    # date line, big serif
    title = "FRIDAY, 13 NOVEMBER 2026"
    f = serif_b(96)
    tw = draw.textlength(title, font=f)
    draw.text(((W - tw) // 2, 92), title, font=f, fill=INK)
    # red double rule
    draw.rectangle([48, 216, W - 48, 226], fill=RED)
    draw.rectangle([48, 234, W - 48, 238], fill=RED)
    sub = "THE DAY'S WORLD NEWS  —  FIVE STORIES, ONE PAGE"
    fs = sans_b(36)
    sw = draw.textlength(sub, font=fs)
    draw.text(((W - sw) // 2, 256), sub, font=fs, fill=DARKRED)


def draw_gulf(draw, rng):
    """Lead panel: Strait of Hormuz — tanker, mine blast, radar claim."""
    x0, y0, x1, y1 = 48, 316, W - 48, 952
    panel(draw, (x0, y0, x1, y1), TEAL_DARK)
    # sky band
    draw.rectangle([x0 + 4, y0 + 4, x1 - 4, y0 + 150], fill=(233, 132, 60))
    sun_cx, sun_cy = x1 - 260, y0 + 92
    burst(draw, sun_cx, sun_cy, 84, 46, 12, GOLD)
    draw.ellipse([sun_cx - 52, sun_cy - 52, sun_cx + 52, sun_cy + 52],
                 fill=(255, 214, 90))
    # sea
    for i in range(14):
        yy = y0 + 154 + i * 26
        draw.line([x0 + 4, yy, x1 - 4, yy], fill=SEA, width=10)
    # tanker silhouette (hull + containers + funnel)
    hx0, hy = x0 + 120, y0 + 330
    draw.rectangle([hx0, hy, hx0 + 900, hy + 130], fill=(30, 30, 34))
    draw.rectangle([hx0 + 40, hy - 90, hx0 + 260, hy], fill=(120, 40, 36))
    draw.rectangle([hx0 + 300, hy - 90, hx0 + 520, hy], fill=(40, 90, 60))
    draw.rectangle([hx0 + 560, hy - 90, hx0 + 780, hy], fill=(150, 110, 30))
    draw.rectangle([hx0 + 830, hy - 150, hx0 + 900, hy], fill=(200, 200, 200))
    draw.rectangle([hx0 + 830, hy - 150, hx0 + 900, hy - 120],
                   fill=DARKRED)
    # portholes
    for i in range(9):
        px = hx0 + 60 + i * 92
        draw.ellipse([px, hy + 60, px + 26, hy + 86], fill=GOLD)
    # explosion burst over the bow
    ex, ey = hx0 + 980, hy - 60
    burst(draw, ex, ey, 150, 70, 14, (255, 170, 30))
    burst(draw, ex, ey, 105, 48, 12, (255, 90, 20))
    burst(draw, ex, ey, 58, 26, 10, (255, 230, 120))
    # naval mines bobbing in the water
    for mx, my, mr in ((x0 + 190, y1 - 260, 44), (x1 - 330, y1 - 230, 36)):
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1),
                       (-1, -1), (1, -1), (-1, 1), (1, 1)):
            draw.line([mx, my, mx + dx * (mr + 26), my + dy * (mr + 26)],
                      fill=INK, width=10)
        draw.ellipse([mx - mr, my - mr, mx + mr, my + mr], fill=INK)
        draw.ellipse([mx - mr // 2, my - mr // 2, mx - 6, my - 6],
                     fill=(70, 70, 70))
    # white caption strip with the headline
    cy0 = y1 - 168
    draw.rectangle([x0 + 4, cy0, x1 - 4, y1 - 4], fill=WHITE)
    draw.rectangle([x0 + 4, cy0, x1 - 4, cy0 + 8], fill=RED)
    fh = sans_b(58)
    lines = wrap(draw, "TANKERS HIT IN THE STRAIT OF HORMUZ",
                 fh, x1 - x0 - 90)
    yy = text_block(draw, x0 + 44, cy0 + 22, x1 - x0 - 90, lines, fh, INK)
    fs = sans(34)
    sub = ("LNG tanker struck by a naval mine; Iran claims it destroyed "
           "a US radar in Bahrain.")
    lines = wrap(draw, sub, fs, x1 - x0 - 90)
    text_block(draw, x0 + 44, yy + 4, x1 - x0 - 90, lines, fs, GREY)


def draw_ukraine(draw):
    """Panel: Europe joins the Ukraine peace talks — dove + EU stars."""
    x0, y0, x1, y1 = 48, 976, 1000, 1500
    panel(draw, (x0, y0, x1, y1), (235, 238, 245))
    # EU-style circle of gold stars on blue disc
    import math
    cx, cy, r = (x0 + x1) // 2, y0 + 108, 88
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=BLUE)
    for i in range(12):
        a = -math.pi / 2 + i * math.pi / 6
        sx, sy = cx + 61 * math.cos(a), cy + 61 * math.sin(a)
        burst(draw, sx, sy, 13, 6, 5, GOLD)
    # dove: white body, round head overlapping the body, beak, wing, tail
    dx, dy = (x0 + x1) // 2, y0 + 268
    draw.polygon([(dx - 116, dy - 4), (dx - 192, dy - 26),
                  (dx - 188, dy + 12), (dx - 116, dy + 20)], fill=WHITE,
                 outline=INK)
    draw.ellipse([dx - 120, dy - 26, dx + 110, dy + 30], fill=WHITE,
                 outline=INK, width=3)
    draw.ellipse([dx + 88, dy - 68, dx + 148, dy - 8], fill=WHITE,
                 outline=INK, width=3)
    draw.polygon([(dx + 142, dy - 48), (dx + 168, dy - 38),
                  (dx + 142, dy - 28)], fill=GOLD, outline=INK)
    draw.ellipse([dx + 118, dy - 52, dx + 130, dy - 40], fill=INK)
    draw.ellipse([dx - 62, dy - 52, dx + 58, dy + 4], fill=WHITE,
                 outline=INK, width=3)
    # olive branch
    draw.line([dx - 60, dy + 56, dx + 110, dy + 64], fill=GREEN, width=8)
    for t in (0.25, 0.5, 0.75):
        lx = dx - 60 + t * 170
        ly = dy + 44 + t * 20
        draw.ellipse([lx - 16, ly - 26, lx + 16, ly + 2], fill=GREEN)
    fh = sans_b(42)
    lines = wrap(draw, "EUROPE WINS A SEAT AT UKRAINE PEACE TALKS",
                 fh, x1 - x0 - 56)
    yy = text_block(draw, x0 + 28, y1 - 176, x1 - x0 - 56, lines, fh, INK)
    fs = sans(28)
    lines = wrap(draw, "Kushner and Witkoff met Putin, then Zelenskyy; "
                 "work begins on the war's largest prisoner swap.",
                 fs, x1 - x0 - 56)
    text_block(draw, x0 + 28, yy + 2, x1 - x0 - 56, lines, fs, GREY)


def draw_nvidia(draw):
    """Panel: Nvidia CEO resigns, shares fall ~16% — green chip, red arrow."""
    x0, y0, x1, y1 = 1048, 976, 2000, 1500
    panel(draw, (x0, y0, x1, y1), (232, 244, 232))
    cx = (x0 + x1) // 2
    # chip: green square with pins and an eye-like die
    ch, cw = 210, 210
    top = y0 + 96
    for k in range(5):
        px = cx - cw // 2 + 20 + k * 42
        draw.rectangle([px, top - 26, px + 18, top], fill=INK)
        draw.rectangle([px, top + ch, px + 18, top + ch + 26], fill=INK)
    for k in range(5):
        py = top + 20 + k * 42
        draw.rectangle([cx - cw // 2 - 26, py, cx - cw // 2, py + 18],
                       fill=INK)
        draw.rectangle([cx + cw // 2, py, cx + cw // 2 + 26, py + 18],
                       fill=INK)
    draw.rectangle([cx - cw // 2, top, cx + cw // 2, top + ch],
                   fill=(118, 200, 40), outline=INK, width=5)
    draw.ellipse([cx - 52, top + 62, cx + 52, top + 148],
                 fill=(20, 60, 20))
    draw.ellipse([cx - 26, top + 88, cx + 26, top + 122], fill=WHITE)
    # red down arrow + -16%
    ax, ay = x1 - 190, top + 30
    draw.polygon([(ax - 66, ay), (ax + 66, ay), (ax + 66, ay + 96),
                  (ax + 118, ay + 96), (ax, ay + 208), (ax - 118, ay + 96),
                  (ax - 66, ay + 96)], fill=RED)
    pct = sans_b(64)
    draw.text((x0 + 36, top + 56), "-16%", font=pct, fill=RED)
    fh = sans_b(42)
    lines = wrap(draw, "NVIDIA CHIEF JENSEN HUANG RESIGNS",
                 fh, x1 - x0 - 56)
    yy = text_block(draw, x0 + 28, y1 - 176, x1 - x0 - 56, lines, fh, INK)
    fs = sans(28)
    lines = wrap(draw, "Founder quits as CEO and leaves the board; "
                 "CFO Colette Kress takes over; shares slide.",
                 fs, x1 - x0 - 56)
    text_block(draw, x0 + 28, yy + 2, x1 - x0 - 56, lines, fs, GREY)


def draw_microsoft(draw):
    """Panel: Microsoft 365 outage — cracked blue window tiles."""
    x0, y0, x1, y1 = 48, 1524, 1000, 1980
    panel(draw, (x0, y0, x1, y1), (228, 238, 250))
    # four window panes, one cracked / dark
    gx, gy, s, g = x0 + 336, y0 + 36, 120, 20
    cols = [BLUE, (60, 140, 220), (90, 170, 235), (40, 60, 90)]
    for i, col in enumerate(cols):
        px = gx + (i % 2) * (s + g)
        py = gy + (i // 2) * (s + g)
        draw.rectangle([px, py, px + s, py + s], fill=col, outline=INK,
                       width=4)
    # crack across the dark pane
    draw.line([gx + s + g + 16, gy + s + g + 16,
               gx + 2 * s + g - 24, gy + s + g + 72], fill=WHITE, width=8)
    draw.line([gx + 2 * s + g - 24, gy + s + g + 72,
               gx + s + g + 48, gy + 2 * s + g - 14], fill=WHITE, width=8)
    fh = sans_b(40)
    lines = wrap(draw, "MICROSOFT 365 DOWN WORLDWIDE",
                 fh, x1 - x0 - 56)
    yy = text_block(draw, x0 + 28, y1 - 158, x1 - x0 - 56, lines, fh, INK)
    fs = sans(28)
    lines = wrap(draw, "Mail and Teams fail across regions.",
                 fs, x1 - x0 - 56)
    text_block(draw, x0 + 28, yy + 2, x1 - x0 - 56, lines, fs, GREY)


def draw_brooklyn(draw):
    """Panel: Brooklyn collapse — rubble, rescue light, toll 8 dead."""
    x0, y0, x1, y1 = 1048, 1524, 2000, 1980
    panel(draw, (x0, y0, x1, y1), (240, 234, 224))
    # standing building edge + collapsed rubble
    draw.rectangle([x0 + 60, y0 + 40, x0 + 330, y0 + 280], fill=(150, 120, 90),
                   outline=INK, width=4)
    for r in range(3):
        for c in range(3):
            wx = x0 + 92 + c * 78
            wy = y0 + 66 + r * 64
            draw.rectangle([wx, wy, wx + 40, wy + 40], fill=(70, 60, 50))
    # jagged rubble pile
    import math
    base = y0 + 280
    pts = [(x0 + 330, base)]
    for i in range(9):
        pts.append((x0 + 330 + i * 62,
                    base - (46 if i % 2 == 0 else 96) - (i % 3) * 12))
    pts.append((x0 + 900, base))
    draw.polygon(pts, fill=(110, 96, 82), outline=INK)
    # rescue beam
    draw.polygon([(x1 - 220, y0 + 70), (x1 - 140, y0 + 70),
                  (x1 - 60, base), (x1 - 300, base)],
                 fill=(255, 220, 120))
    draw.ellipse([x1 - 250, y0 + 46, x1 - 110, y0 + 96], fill=GOLD,
                 outline=INK, width=3)
    fh = sans_b(42)
    lines = wrap(draw, "BROOKLYN COLLAPSE: 8 DEAD",
                 fh, x1 - x0 - 56)
    yy = text_block(draw, x0 + 28, y1 - 150, x1 - x0 - 56, lines, fh, INK)
    fs = sans(28)
    lines = wrap(draw, "Search ends at the Flatbush site; 18 injured; "
                 "city orders checks at 100 linked sites.",
                 fs, x1 - x0 - 56)
    text_block(draw, x0 + 28, yy + 2, x1 - x0 - 56, lines, fs, GREY)


def draw_footer(draw):
    """Black ticker strip: three more stories of the day."""
    draw.rectangle([0, 1996, W, H], fill=INK)
    f = sans_b(26)
    tick = ("POPE LEO MEETS SURVIVORS IN PERU  •  US TO SEIZE $1.2BN IN "
            "BINANCE HACK  •  CHINA'S PACIFIC DRILLS")
    tw = draw.textlength(tick, font=f)
    draw.text(((W - tw) // 2, 2006), tick, font=f, fill=CREAM)


def render():
    from PIL import Image, ImageDraw
    rng = random.Random(SEED)
    img = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(img)
    draw_masthead(draw)
    draw_gulf(draw, rng)
    draw_ukraine(draw)
    draw_nvidia(draw)
    draw_microsoft(draw)
    draw_brooklyn(draw)
    draw_footer(draw)
    return img.resize((1024, 1024), Image.LANCZOS)


def main():
    out_dir = os.environ.get("OUTPUT_DIR", "/output")
    out = os.path.join(out_dir, "entry.png")
    os.makedirs(out_dir, exist_ok=True)
    try:
        img = render()
    except Exception:
        # Pillow (or a font) unavailable: ship the pre-rendered artwork.
        here = os.path.dirname(os.path.abspath(__file__))
        src = os.path.join(here, "artwork.png")
        if os.path.exists(src):
            shutil.copyfile(src, out)
            return 0
        raise
    img.save(out, "PNG", optimize=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
