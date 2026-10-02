#!/usr/bin/env python3
"""Generate one wallpaper per Tidepool theme (1920x1200 PNG).

    python3 tools/gen_wallpapers.py            # all themes
    python3 tools/gen_wallpapers.py creeper    # one theme

Needs Pillow and numpy. Reads colors from themes/<id>/palette.sh.
Drop your own image at wallpapers/<id>.png to replace any of these.
"""
import math
import os
import random
import re
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
W, H = 1920, 1200


def palette(theme):
    out = {}
    with open(os.path.join(ROOT, "themes", theme, "palette.sh")) as f:
        for line in f:
            m = re.match(r'^([A-Z0-9_]+)="(#[0-9a-fA-F]{6})"', line.strip())
            if m:
                out[m.group(1)] = m.group(2)
    return out


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mixc(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def vgradient(stops, w=W, h=H):
    """stops: list of (position 0..1, (r,g,b))."""
    ys = np.linspace(0, 1, h)
    arr = np.zeros((h, w, 3), dtype=np.float32)
    pos = [s[0] for s in stops]
    for c in range(3):
        arr[:, :, c] = np.interp(ys, pos, [s[1][c] for s in stops])[:, None]
    return arr


def to_image(arr, grain=1.0, seed=1):
    if grain:
        rng = np.random.default_rng(seed)
        arr = arr + rng.normal(0, grain, arr.shape[:2])[:, :, None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")


def glow(img, cx, cy, radius, color, strength):
    """Add a soft radial glow."""
    ys, xs = np.mgrid[0:img.size[1], 0:img.size[0]]
    d = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2) / radius
    a = np.clip(1 - d, 0, 1) ** 2 * strength
    base = np.asarray(img).astype(np.float32)
    col = np.array(color, dtype=np.float32)
    base = base * (1 - a[:, :, None]) + col * a[:, :, None]
    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8), "RGB")


# ---------------------------------------------------------------- tidepool
def tidepool():
    p = palette("tidepool")
    base, mantle, accent, accent2 = rgb(p["BASE"]), rgb(p["MANTLE"]), rgb(p["ACCENT"]), rgb(p["ACCENT2"])
    img = to_image(vgradient([(0, mixc(base, accent2, 0.10)), (0.55, base), (1, mixc(base, accent, 0.22))]))
    img = glow(img, W * 0.78, H * 0.18, 620, accent, 0.30)
    rnd = random.Random(3)
    for k in range(7):
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        y0 = 560 + k * 105
        a1, a2 = rnd.uniform(18, 40), rnd.uniform(8, 20)
        f1, f2 = rnd.uniform(0.0016, 0.0030), rnd.uniform(0.004, 0.008)
        ph1, ph2 = rnd.uniform(0, 6.28), rnd.uniform(0, 6.28)
        pts = [(x, y0 + a1 * math.sin(x * f1 + ph1) + a2 * math.sin(x * f2 + ph2)) for x in range(0, W + 8, 8)]
        d.polygon(pts + [(W, H), (0, H)], fill=mixc(accent2, accent, k / 6) + (int(22 + k * 9),))
        layer = layer.filter(ImageFilter.GaussianBlur(1.2))
        img.paste(layer, (0, 0), layer)
        # thin crest line
        line = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(line).line(pts, fill=mixc(accent, (255, 255, 255), 0.4) + (46,), width=2)
        img.paste(line, (0, 0), line)
    return img


# --------------------------------------------------------------- nightshift
def nightshift():
    p = palette("nightshift")
    base, overlay, accent, accent2 = rgb(p["BASE"]), rgb(p["OVERLAY"]), rgb(p["ACCENT"]), rgb(p["ACCENT2"])
    img = to_image(vgradient([(0, mixc(base, (0, 0, 0), 0.4)), (0.6, base), (1, mixc(overlay, accent2, 0.25))]))
    img = glow(img, W * 0.3, H * 0.82, 760, accent2, 0.30)
    d = ImageDraw.Draw(img)
    rnd = random.Random(11)
    for _ in range(420):
        x, y = rnd.randint(0, W), rnd.randint(0, int(H * 0.65))
        b = rnd.randint(70, 200)
        s = 1 if rnd.random() < 0.85 else 2
        d.rectangle([x, y, x + s, y + s], fill=(b, b, min(255, b + 40)))
    for k, (yy, amp) in enumerate([(840, 90), (930, 70), (1020, 50)]):
        pts = [(x, yy - amp * (0.6 * math.sin(x * 0.004 + k * 2) + 0.4 * math.sin(x * 0.011 + k))) for x in range(0, W + 10, 10)]
        d.polygon(pts + [(W, H), (0, H)], fill=mixc(base, accent, 0.05 + k * 0.03))
    # dotted grid, like an editor gutter
    for gx in range(80, W, 80):
        for gy in range(80, 700, 80):
            d.ellipse([gx, gy, gx + 2, gy + 2], fill=mixc(base, accent, 0.30))
    return img


# ------------------------------------------------------------------- arcade
def arcade():
    p = palette("arcade")
    base, accent, accent2, yellow = rgb(p["BASE"]), rgb(p["ACCENT"]), rgb(p["ACCENT2"]), rgb(p["YELLOW"])
    horizon = int(H * 0.60)
    sky = vgradient([(0, base), (0.45, mixc(base, accent, 0.30)), (0.60, mixc(accent, yellow, 0.35))], h=horizon + 1)
    floor = vgradient([(0, mixc(base, accent, 0.18)), (1, base)], h=H - horizon)
    arr = np.concatenate([sky[:horizon], floor], axis=0)
    img = to_image(arr, grain=0.8)
    d = ImageDraw.Draw(img)
    # sun with stripe cutouts
    sun_r, cx, cy = 250, W // 2, horizon - 40
    sun = Image.new("RGB", (W, H), (0, 0, 0))
    sd = ImageDraw.Draw(sun)
    for i in range(sun_r * 2):
        t = i / (sun_r * 2)
        sd.line([(cx - sun_r, cy - sun_r + i), (cx + sun_r, cy - sun_r + i)], fill=mixc(yellow, accent, t))
    mask = Image.new("L", (W, H), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse([cx - sun_r, cy - sun_r, cx + sun_r, cy + sun_r], fill=255)
    for k in range(7):
        y = cy - 40 + k * 18
        md.rectangle([0, y, W, y + 2 + k * 2], fill=0)
    mask = mask.crop((0, 0, W, horizon))
    img.paste(sun.crop((0, 0, W, horizon)), (0, 0), mask)
    img = glow(img, cx, horizon, 700, accent, 0.22)
    d = ImageDraw.Draw(img)
    # perspective grid
    vx = W / 2
    for i in range(-24, 25):
        x_bottom = vx + i * 150
        d.line([(vx + i * 6, horizon), (x_bottom, H)], fill=accent2, width=2)
    y, step = horizon, 6
    while y < H:
        d.line([(0, y), (W, y)], fill=mixc(accent2, base, 0.35 + (y - horizon) / (H - horizon) * -0.25), width=2)
        step *= 1.22
        y += step
    d.line([(0, horizon), (W, horizon)], fill=mixc(accent, (255, 255, 255), 0.5), width=3)
    return img


# --------------------------------------------------------- blocky wallpapers
PX = 5  # each pixel-art pixel becomes 5x5 real pixels at 1920 wide? 1920/384 = 5
GW, GH = W // PX, H // PX   # 384 x 240 art pixels; one "block" is 8x8 art pixels


def jitter(color, amount, rnd):
    f = 1 + rnd.uniform(-amount, amount)
    return tuple(max(0, min(255, int(c * f))) for c in color)


def block_scale(art):
    return art.resize((W, H), Image.NEAREST)


def creeper():
    p = palette("creeper")
    rnd = random.Random(21)
    grass, dirt, stone = rgb(p["ACCENT"]), (124, 84, 48), (96, 100, 92)
    sky_top, sky_bot = (10, 16, 30), (30, 52, 52)
    art = Image.new("RGB", (GW, GH))
    px = art.load()
    for y in range(GH):
        c = mixc(sky_top, sky_bot, y / GH)
        c = tuple((v // 6) * 6 for v in c)  # banded sky
        for x in range(GW):
            px[x, y] = c
    # stars and a square moon
    for _ in range(70):
        x, y = rnd.randint(0, GW - 1), rnd.randint(0, int(GH * 0.5))
        px[x, y] = (200, 210, 220)
    for dy in range(14):
        for dx in range(14):
            px[300 + dx, 30 + dy] = jitter((226, 232, 214), 0.04, rnd)
    # blocky clouds
    for cx, cy in [(40, 50), (150, 30), (230, 70)]:
        for dx in range(rnd.randint(30, 44)):
            for dy in range(8):
                if 0 <= cx + dx < GW:
                    px[cx + dx, cy + dy] = jitter((52, 70, 76), 0.05, rnd)
    # terrain in 8px blocks
    cols = GW // 8
    heights = [int(GH * 0.58 + 26 * math.sin(i * 0.23) + 14 * math.sin(i * 0.61 + 1.3)) // 8 * 8 for i in range(cols)]
    for i, top in enumerate(heights):
        for y in range(top, GH):
            depth = (y - top) // 8
            if depth == 0:
                base = grass
            elif depth < 4:
                base = dirt
            else:
                base = stone
            for x in range(i * 8, i * 8 + 8):
                c = jitter(base, 0.10, rnd)
                if depth >= 4 and rnd.random() < 0.012:
                    c = rnd.choice([(30, 30, 30), (80, 220, 230), (230, 190, 60)])  # coal, diamond, gold
                px[x, y] = c
    # trees
    for i in range(3, cols - 3, 9):
        top = heights[i]
        for y in range(top - 40, top):
            for x in range(i * 8 + 2, i * 8 + 6):
                px[x, y] = jitter((96, 66, 36), 0.10, rnd)
        for ly in range(top - 64, top - 32):
            for lx in range(i * 8 - 14, i * 8 + 22):
                if 0 <= lx < GW and (abs(lx - (i * 8 + 4)) < 14 - max(0, (ly - (top - 48)) // 6)):
                    px[lx, ly] = jitter((46, 120, 44), 0.14, rnd)
    return block_scale(art)


def nether():
    p = palette("nether")
    rnd = random.Random(33)
    rack, lava = (104, 40, 40), rgb(p["ACCENT"])
    art = Image.new("RGB", (GW, GH))
    px = art.load()
    for y in range(GH):
        c = mixc((20, 8, 8), (58, 18, 14), y / GH)
        for x in range(GW):
            px[x, y] = c
    cols = GW // 8
    ceil = [int(34 + 26 * math.sin(i * 0.31) + 18 * math.sin(i * 0.77 + 2)) // 8 * 8 for i in range(cols)]
    floor = [int(GH * 0.70 + 16 * math.sin(i * 0.19 + 1) + 10 * math.sin(i * 0.5)) // 8 * 8 for i in range(cols)]
    lava_top = int(GH * 0.80) // 8 * 8
    for i in range(cols):
        for y in range(0, ceil[i]):
            for x in range(i * 8, i * 8 + 8):
                px[x, y] = jitter(rack, 0.16, rnd)
        for y in range(floor[i], GH):
            for x in range(i * 8, i * 8 + 8):
                if y >= lava_top:
                    t = rnd.random()
                    px[x, y] = jitter(mixc(lava, (255, 200, 60), t * 0.7), 0.06, rnd)
                else:
                    px[x, y] = jitter(rack, 0.16, rnd)
    # glowstone clusters hanging from the ceiling
    for i in rnd.sample(range(4, cols - 4), 5):
        for dy in range(rnd.randint(10, 24)):
            for dx in range(rnd.randint(6, 14)):
                x, y = i * 8 + dx - 4, ceil[i] + dy
                if 0 <= x < GW:
                    px[x, y] = jitter((255, 190, 90), 0.10, rnd)
    # embers
    for _ in range(80):
        x, y = rnd.randint(0, GW - 1), rnd.randint(40, int(GH * 0.8))
        px[x, y] = (255, rnd.randint(120, 190), 40)
    return block_scale(art)


# -------------------------------------------------------------------- frost
def frost():
    p = palette("frost")
    accent, accent2 = rgb(p["ACCENT"]), rgb(p["ACCENT2"])
    img = to_image(vgradient([(0, (226, 240, 250)), (0.5, (190, 214, 236)), (1, (206, 224, 244))]), grain=0.7)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    rnd = random.Random(5)
    palette_cols = [accent, accent2, (255, 255, 255), (140, 190, 240), (180, 150, 240)]
    for _ in range(16):
        r = rnd.randint(110, 330)
        x, y = rnd.randint(-100, W + 100), rnd.randint(-100, H + 100)
        c = rnd.choice(palette_cols)
        d.ellipse([x - r, y - r, x + r, y + r], fill=c + (rnd.randint(50, 120),))
    layer = layer.filter(ImageFilter.GaussianBlur(70))
    img.paste(layer, (0, 0), layer)
    # frosted panes
    panes = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(panes)
    for pts in ([(260, 120), (980, 60), (1100, 640), (340, 760)],
                [(1180, 360), (1760, 300), (1820, 980), (1260, 1060)]):
        pd.polygon(pts, fill=(255, 255, 255, 46), outline=(255, 255, 255, 150))
        pd.line(pts + [pts[0]], fill=(255, 255, 255, 170), width=2)
    panes = panes.filter(ImageFilter.GaussianBlur(1.2))
    img.paste(panes, (0, 0), panes)
    return img


MAKERS = {
    "tidepool": tidepool, "nightshift": nightshift, "arcade": arcade,
    "creeper": creeper, "nether": nether, "frost": frost,
}

if __name__ == "__main__":
    names = sys.argv[1:] or list(MAKERS)
    out_dir = os.path.join(ROOT, "wallpapers")
    os.makedirs(out_dir, exist_ok=True)
    for n in names:
        img = MAKERS[n]()
        path = os.path.join(out_dir, n + ".png")
        img.save(path, optimize=True)
        print(f"{n}.png  {os.path.getsize(path) // 1024} KB")
