#!/usr/bin/env python3
"""Render a desktop preview per Tidepool theme for the README (1280x800 PNG).

    python3 tools/gen_previews.py            # all themes
    python3 tools/gen_previews.py frost      # one theme

Needs Pillow and JetBrainsMono Nerd Font. Reads themes/<id>/palette.sh and
wallpapers/<id>.png, and draws the bar, windows and a notification with the
theme's own colors, rounding, borders, gaps and opacity. It is a mockup drawn
from the palette, not a screenshot.
"""
import os
import re
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
W, H = 1280, 800
S = 2  # draw at 2x, then downscale for smooth edges

# Same defaults as load_palette() in bin/tp-theme
DEFAULTS = {
    "ROUNDING": 12, "BORDER": 2, "GAPS_IN": 5, "GAPS_OUT": 12,
    "BAR_ALPHA": 0.8, "BAR_RADIUS": 12, "WIN_ALPHA": 0.9, "THEME_KIND": "dark",
}


def palette(theme):
    out = dict(DEFAULTS)
    with open(os.path.join(ROOT, "themes", theme, "palette.sh")) as f:
        for line in f:
            m = re.match(r'^([A-Z0-9_]+)=(?:"([^"]*)"|([^\s#]+))', line.strip())
            if not m:
                continue
            val = m.group(2) if m.group(2) is not None else m.group(3)
            try:
                val = float(val) if "." in val else int(val)
            except ValueError:
                pass
            out[m.group(1)] = val
    return out


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgba(h, a):
    return rgb(h) + (int(a * 255),)


def font(bold=False, size=13):
    name = "JetBrainsMono Nerd Font" + (":bold" if bold else "")
    path = subprocess.run(["fc-match", "-f", "%{file}", name],
                          capture_output=True, text=True).stdout.strip()
    return ImageFont.truetype(path, size * S)


def box(x0, y0, x1, y1):
    return [int(x0 * S), int(y0 * S), int(x1 * S), int(y1 * S)]


def mask_round(size, radius):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], radius=radius, fill=255)
    return m


def gradient(size, c1, c2):
    """Diagonal 45deg gradient, like the Hyprland active border."""
    g = Image.new("RGB", (2, 2))
    g.putpixel((0, 1), c1)
    g.putpixel((1, 0), c2)
    g.putpixel((0, 0), tuple((a + b) // 2 for a, b in zip(c1, c2)))
    g.putpixel((1, 1), tuple((a + b) // 2 for a, b in zip(c1, c2)))
    return g.resize(size, Image.BILINEAR)


def glass(canvas, wall, rect, radius, fill):
    """Blurred wallpaper behind a translucent panel, like Hyprland's blur."""
    x0, y0, x1, y1 = rect
    size = (x1 - x0, y1 - y0)
    behind = wall.crop(rect).filter(ImageFilter.GaussianBlur(14 * S))
    panel = Image.new("RGBA", size, fill)
    behind = Image.alpha_composite(behind.convert("RGBA"), panel)
    canvas.paste(behind, (x0, y0), mask_round(size, radius))


def border(canvas, rect, radius, width, color):
    """color is an (r,g,b,a) tuple or a (c1, c2) gradient pair."""
    x0, y0, x1, y1 = rect
    size = (x1 - x0, y1 - y0)
    ring = mask_round(size, radius)
    inner = Image.new("L", size, 0)
    ImageDraw.Draw(inner).rounded_rectangle(
        [width, width, size[0] - 1 - width, size[1] - 1 - width],
        radius=max(radius - width, 0), fill=255)
    ring.paste(0, (0, 0), inner)
    if len(color) == 2:
        src = gradient(size, color[0], color[1]).convert("RGBA")
    else:
        src = Image.new("RGBA", size, color)
        ring = ring.point(lambda v: v * color[3] // 255)
    canvas.paste(src, (x0, y0), ring)


def text_runs(d, x, y, runs, f):
    """Draw [(text, color), ...] left to right; returns the end x (in 2x px)."""
    for t, c in runs:
        d.text((x, y), t, font=f, fill=c)
        x += d.textlength(t, font=f)
    return x


def render(theme):
    p = palette(theme)
    c = {k: rgb(p[k]) for k in ("BASE", "MANTLE", "SURFACE", "OVERLAY", "TEXT", "SUBTEXT",
                                "ACCENT", "ACCENT2", "ON_ACCENT", "GREEN", "YELLOW", "RED",
                                "BLUE", "MAUVE")}
    rnd, bw = p["ROUNDING"] * S, max(1, p["BORDER"]) * S
    gin, gout = p["GAPS_IN"], p["GAPS_OUT"]
    reg, bold, small = font(size=13), font(True, 13), font(size=12)

    wall = Image.open(os.path.join(ROOT, "wallpapers", theme + ".png")).convert("RGB")
    wall = wall.resize((W * S, H * S), Image.LANCZOS).convert("RGBA")
    img = wall.copy()
    d = ImageDraw.Draw(img)

    # ---- Waybar: three floating islands (margin 8/12, height 38, see config.jsonc)
    bar_y0, bar_y1 = 8, 46
    bar_fill = rgba(p["BASE"], p["BAR_ALPHA"])
    edge = c["TEXT"] + (26,)
    islands = {"left": (12, 470), "center": (W / 2 - 110, W / 2 + 110), "right": (W - 520, W - 12)}
    for x0, x1 in islands.values():
        r = box(x0, bar_y0, x1, bar_y1)
        glass(img, wall, r, p["BAR_RADIUS"] * S, bar_fill)
        border(img, r, p["BAR_RADIUS"] * S, S, edge)
    d = ImageDraw.Draw(img)
    pill_r = p["ROUNDING"] * 2 // 3 * S
    ty = (bar_y0 + 11) * S

    x = 15
    d.rounded_rectangle(box(x, 11, x + 36, 43), radius=pill_r, fill=c["ACCENT"])
    d.text((int((x + 12) * S), ty), "\uf303", font=bold, fill=c["ON_ACCENT"])
    x += 44
    for n in range(1, 6):
        w = 40 if n == 1 else 26
        if n == 1:
            d.rounded_rectangle(box(x, 11, x + w, 43), radius=pill_r, fill=c["ACCENT"])
        d.text((int((x + (w / 2 - 4)) * S), ty), str(n), font=bold if n == 1 else reg,
               fill=c["ON_ACCENT"] if n == 1 else c["SUBTEXT"])
        x += w + 4
    d.text((int((x + 10) * S), ty), "kitty  ~/tidepool", font=reg, fill=c["SUBTEXT"])

    clock = "\uf017  Fri 02 Oct   21:48"
    cx = W / 2 * S - d.textlength(clock, font=bold) / 2
    d.text((cx, ty), clock, font=bold, fill=c["TEXT"])

    x = (W - 508) * S
    for t, col in (("\uf028  62%", c["MAUVE"]), ("\uf1eb  87%", c["ACCENT2"]),
                   ("\uf2db  12%", c["BLUE"]), ("\U000f035b  41%", c["GREEN"]),
                   ("\uf240  93%", c["GREEN"]), ("\U000f03d8  " + p["THEME_NAME"], c["ACCENT"]),
                   ("\uf011", c["RED"])):
        d.text((x, ty), t, font=reg, fill=col)
        x += d.textlength(t, font=reg) + 22 * S

    # ---- Windows: dwindle layout, terminal left, editor and visualizer right
    top, bottom, left, right = bar_y1 + gout, H - gout, gout, W - gout
    mid = left + (right - left) * 0.52
    split = top + (bottom - top) * 0.58
    wins = {
        "term": box(left, top, mid - gin, bottom),
        "code": box(mid + gin, top, right, split - gin),
        "cava": box(mid + gin, split + gin, right, bottom),
    }
    win_fill = rgba(p["BASE"], p["WIN_ALPHA"])
    for name, r in wins.items():
        glass(img, wall, r, rnd, win_fill)
        if name == "term":
            border(img, r, rnd, bw, (c["ACCENT"], c["ACCENT2"]))
        else:
            border(img, r, rnd, bw, c["OVERLAY"] + (204,))
    d = ImageDraw.Draw(img)

    # Terminal: starship prompt colored by the theme
    x0, y0 = wins["term"][0] + 22 * S, wins["term"][1] + 20 * S
    lh = 24 * S
    seg_h = 22 * S
    xx = x0
    for label, bg, fg in ((" \uf303 cachewraith ", c["ACCENT"], c["ON_ACCENT"]),
                          (" ~/tidepool ", c["SURFACE"], c["TEXT"])):
        tw = d.textlength(label, font=bold)
        d.rectangle([xx, y0 - 2 * S, xx + tw, y0 - 2 * S + seg_h], fill=bg)
        d.text((xx, y0), label, font=bold, fill=fg)
        xx += tw
    text_runs(d, xx, y0, [("  \ue0a0 main", c["ACCENT2"]), (" !1", c["YELLOW"])], reg)
    y = y0 + lh * 1.3
    text_runs(d, x0, y, [("❯ ", c["ACCENT"]), ("tp-theme ", c["GREEN"]), ("list", c["TEXT"])], reg)
    y += lh
    for t in sorted(os.listdir(os.path.join(ROOT, "themes"))):
        mark = "● " if t == theme else "  "
        d.text((x0, y), mark + t, font=reg, fill=c["ACCENT"] if t == theme else c["SUBTEXT"])
        y += lh
    y += lh * 0.4
    text_runs(d, x0, y, [("❯ ", c["ACCENT"]), ("tp-theme ", c["GREEN"]),
                         ("set ", c["TEXT"]), (theme, c["YELLOW"])], reg)
    y += lh
    d.text((x0, y), "Theme: " + p["THEME_NAME"], font=reg, fill=c["TEXT"])
    y += lh * 1.4
    d.text((x0, y), "❯ ", font=reg, fill=c["ACCENT"])
    cur_x = x0 + d.textlength("❯ ", font=reg)
    d.rectangle([cur_x, y + 2 * S, cur_x + 2 * S, y + 17 * S], fill=c["ACCENT"])

    # Editor: a slice of hyprland.lua with this theme's values
    x0, y = wins["code"][0] + 22 * S, wins["code"][1] + 20 * S
    kw, st, nu, fn, cm, tx = c["MAUVE"], c["GREEN"], c["YELLOW"], c["BLUE"], c["SUBTEXT"], c["TEXT"]
    code = [
        [("-- hyprland.lua", cm)],
        [("hl", tx), (".", tx), ("config", fn), ("({", tx)],
        [("  general ", tx), ("= {", tx)],
        [("    gaps_in     ", tx), ("= ", tx), (str(gin), nu), (",", tx)],
        [("    gaps_out    ", tx), ("= ", tx), (str(gout), nu), (",", tx)],
        [("    border_size ", tx), ("= ", tx), (str(p["BORDER"]), nu), (",", tx)],
        [("  },", tx)],
        [("  decoration ", tx), ("= { ", tx), ("rounding ", tx), ("= ", tx),
         (str(p["ROUNDING"]), nu), (" },", tx)],
        [("})", tx)],
        [("local ", kw), ("mod ", tx), ("= ", tx), ('"SUPER"', st)],
        [("hl", tx), (".", tx), ("bind", fn), ("(mod .. ", tx), ('" + T"', st), (", ", tx)],
        [("  hl.dsp.", tx), ("exec_cmd", fn), ("(", tx), ('"tp-theme pick"', st), ("))", tx)],
    ]
    for i, line in enumerate(code):
        d.text((x0, y), f"{i + 1:>2}  ", font=small, fill=c["OVERLAY"] if p["THEME_KIND"] == "dark" else c["SUBTEXT"])
        text_runs(d, x0 + d.textlength("00  ", font=small), y, line, small)
        y += 21 * S

    # Visualizer: cava bars with the theme gradient (ACCENT2 -> ACCENT -> MAUVE)
    x0, y0, x1, y1 = wins["cava"]
    pad = 18 * S
    n = 36
    bar_w = (x1 - x0 - 2 * pad) / n
    grad = Image.new("RGB", (1, 3))
    for i, k in enumerate(("MAUVE", "ACCENT", "ACCENT2")):
        grad.putpixel((0, i), c[k])
    grad = grad.resize((int(bar_w), y1 - y0 - 2 * pad), Image.BILINEAR).convert("RGBA")
    for i in range(n):
        h = 0.18 + 0.78 * abs(((i * 37) % 23) / 23 - 0.5) * 2 * (0.6 + 0.4 * ((i * 7) % 5) / 4)
        bh = int((y1 - y0 - 2 * pad) * min(h, 0.96))
        bx = int(x0 + pad + i * bar_w)
        piece = grad.crop((0, grad.height - bh, int(bar_w) - 3 * S, grad.height))
        img.paste(piece, (bx, y1 - pad - bh))

    # ---- Notification (swaync), top right over the windows
    nr = box(W - 12 - 360, bar_y1 + 10, W - 12 - 12, bar_y1 + 10 + 74)
    glass(img, wall, nr, rnd, rgba(p["BASE"], min(1.0, p["BAR_ALPHA"] + 0.1)))
    border(img, nr, rnd, bw, c["OVERLAY"] + (255,))
    d = ImageDraw.Draw(img)
    ix, iy = nr[0] + 16 * S, nr[1] + 16 * S
    d.rounded_rectangle([ix, iy, ix + 42 * S, iy + 42 * S], radius=pill_r, fill=c["ACCENT"])
    d.text((ix + 13 * S, iy + 11 * S), "\U000f03d8", font=bold, fill=c["ON_ACCENT"])
    d.text((ix + 58 * S, iy + 2 * S), "Theme", font=bold, fill=c["TEXT"])
    d.text((ix + 58 * S, iy + 22 * S), p["THEME_NAME"] + " is now active", font=reg, fill=c["SUBTEXT"])

    return img.convert("RGB").resize((W, H), Image.LANCZOS)


if __name__ == "__main__":
    names = sys.argv[1:] or sorted(os.listdir(os.path.join(ROOT, "themes")))
    out_dir = os.path.join(ROOT, "docs", "previews")
    os.makedirs(out_dir, exist_ok=True)
    for n in names:
        path = os.path.join(out_dir, n + ".png")
        render(n).save(path, optimize=True)
        print(f"{n}.png  {os.path.getsize(path) // 1024} KB")
