#!/usr/bin/env python3
"""Generate the default WebApp Launcher icons (32 / 128 / 256 px PNG).

Design: rounded-square indigo->sky gradient tile with a white "browser window +
launch arrow" glyph.  Pure Pillow, no other dependencies.

Usage: python3 tools/gen-icons.py [out-dir]   (default: src-tauri/icons)
"""

import os
import sys

from PIL import Image, ImageDraw

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    os.path.dirname(__file__), "..", "src-tauri", "icons"
)

BASE = 512
SIZES = {32: "32x32.png", 128: "128x128.png", 256: "icon.png"}


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def tile_gradient(size):
    """Diagonal indigo (-> #6366f1-ish) to sky (#38bdf8) background with rounded corners."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    px = img.load()
    tl, br = (79, 70, 229), (56, 189, 248)  # indigo-600 -> sky-400
    for y in range(size):
        for x in range(size):
            t = (x + y) / (2 * (size - 1))
            px[x, y] = lerp(tl, br, t) + (255,)
    mask = Image.new("L", (size, size), 0)
    md = ImageDraw.Draw(mask)
    r = int(size * 0.225)
    md.rounded_rectangle([0, 0, size - 1, size - 1], radius=r, fill=255)
    img.putalpha(mask)
    return img


def draw_glyph(base):
    d = ImageDraw.Draw(base)
    s = base.size[0]
    u = s / 512.0  # unit scale

    # --- browser window outline (stroked) ---
    w0 = 118 * u
    w1 = 394 * u
    y0 = 128 * u
    y1 = 372 * u
    stroke = int(26 * u)
    radius = int(22 * u)
    d.rounded_rectangle(
        [w0, y0, w1, y1],
        radius=radius,
        outline=(255, 255, 255, 255),
        width=stroke,
    )
    # tab strip dots
    dot_r = int(9 * u)
    dots = ((134, 156, 232, 255), (252, 211, 77, 255), (110, 231, 183, 255))
    for i, col in enumerate(dots):
        cx = (w0 + 24 * u) + i * (34 * u)
        cy = y0 + 28 * u
        d.ellipse(
            [cx - dot_r, cy - dot_r, cx + dot_r, cy + dot_r], fill=col
        )
    # address pill
    d.rounded_rectangle(
        [w0 + 34 * u, y0 + 16 * u, w1 - 20 * u, y0 + 40 * u],
        radius=int(12 * u),
        outline=(255, 255, 255, 210),
        width=int(7 * u),
    )

    # --- launch arrow ↗ rising out of the window ---
    ax0, ay0 = 236 * u, 216 * u  # arrow start (inside window)
    ax1, ay1 = 340 * u, 112 * u  # arrow head (outside, top-right)
    ah = int(30 * u)  # head size
    d.line([ax0, ay0, ax1, ay1], fill=(255, 255, 255, 255), width=int(26 * u))
    d.line(
        [ax1 - ah * 0.707, ay1 + ah * 0.707, ax1, ay1],
        fill=(255, 255, 255, 255),
        width=int(24 * u),
    )
    d.line(
        [ax1 - ah * 0.707, ay1 - ah * 0.707, ax1, ay1],
        fill=(255, 255, 255, 255),
        width=int(24 * u),
    )


def render(size):
    base = tile_gradient(size)
    draw_glyph(base)
    return base


def main():
    os.makedirs(OUT, exist_ok=True)
    master = render(BASE)
    for size, name in SIZES.items():
        if size == BASE:
            img = master
        else:
            img = master.resize((size, size), Image.LANCZOS)
        path = os.path.join(OUT, name)
        img.save(path, "PNG")
        print("wrote", os.path.abspath(path), img.size)


if __name__ == "__main__":
    main()
