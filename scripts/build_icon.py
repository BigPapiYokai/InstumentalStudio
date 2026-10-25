"""Generate SonicLoom Studio application icon (.ico) using Pillow.

Design: dark navy rounded-square background, an S-waveform ribbon band (cyan->indigo
gradient) suggesting sound waves, plus two small stem-marker dots.
"""
import os
import math
from PIL import Image, ImageDraw

SIZES = [16, 32, 48, 64, 128, 256]

BG_TOP = (15, 23, 42)          # deep navy
BG_BOTTOM = (30, 41, 59)       # slate
BAND_TOP = (56, 189, 248)      # sky cyan
BAND_BOTTOM = (56, 189, 248)   # cyan (monochrome band)
STROKE = (226, 232, 240)       # off-white
DOT = (56, 189, 248)


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def smooth_gradient(size):
    img = Image.new("RGB", (size, size), BG_TOP)
    px = img.load()
    for y in range(size):
        t = y / max(1, size - 1)
        c = lerp(BG_TOP, BG_BOTTOM, t)
        for x in range(size):
            px[x, y] = c
    return img


def build():
    main = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    d = ImageDraw.Draw(main)

    # Background: subtle rounded square
    bg = smooth_gradient(256)
    mask = Image.new("L", (256, 256), 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle([0, 0, 255, 255], radius=52, fill=255)
    main.paste(bg, (0, 0), mask)

    margin = 18
    width = 256 - 2 * margin
    cy = 128
    amp = 72
    n = 64

    upper, lower = [], []
    for i in range(n + 1):
        t = i / n
        u = t - 0.5
        x = margin + t * width
        y_up = cy - amp * math.sin(math.pi * u)
        y_low = cy - amp * math.sin(math.pi * u + math.pi)
        upper.append((x, y_up))
        lower.append((x, y_low))

    # Ribbon band fill between upper and lower curves (cyan band)
    band = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    ImageDraw.Draw(band).polygon(
        [upper[0]] + lower[::-1] + [upper[-1]],
        fill=(BAND_TOP[0], BAND_TOP[1], BAND_TOP[2], 230),
    )
    main.alpha_composite(band)

    # Stroke the two curve caps
    d.line(upper, fill=STROKE, width=4, joint="curve")
    d.line(lower, fill=STROKE, width=4, joint="curve")

    # Stem marker dots
    d.ellipse([70 - 3, 128 - 3, 70 + 3, 128 + 3], fill=DOT)
    d.ellipse([186 - 3, 128 - 3, 186 + 3, 128 + 3], fill=DOT)

    os.makedirs("resources", exist_ok=True)
    out = "resources/icon.ico"
    main.convert("RGBA").save(out, format="ICO", sizes=[(sz, sz) for sz in SIZES])
    print("Saved", out, main.size)


if __name__ == "__main__":
    build()