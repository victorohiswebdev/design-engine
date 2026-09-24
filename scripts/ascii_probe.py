#!/usr/bin/env python3
"""Read a region of a rendered image as text: a classified character map, or a
residual brightness profile.

Replaces the throwaway script you would otherwise hand-write every time a
colour threshold fails to separate overlapping elements, or a faint overlay is
lost in a photograph. See references/pixel-inspection.md for when to reach for
which mode.

Modes
  map  (default) classify every cell and print a grid. Use when a threshold
       cannot separate two overlapping elements -- a white icon on a coloured
       slab on a cream background -- and you need the icon's exact position,
       size and shading. Read the grid instead of guessing again.
  row  brightness per row minus a slow-moving baseline. Surfaces a low-contrast
       HORIZONTAL element (faint watermark letter bands, a hairline rule) that
       the image's own vertical gradient swamps.
  col  the same, down the columns.

Residual modes caveat: with a baseline window comparable to the element's own
size, the element sits inside its own baseline, so only edge transitions
survive and band heights badly under-report size. Read the PITCH between bands;
get size from somewhere else.

Usage
  ascii_probe.py IMG --box x0,y0,x1,y1 [--step 2]
  ascii_probe.py IMG --box 640,140,1080,1010 --mode row --thresh 2.5
  ascii_probe.py IMG --box 560,160,1080,1000 --mode col
"""
import argparse
import sys

from PIL import Image

DARK = 28     # below this on every channel: black
LIGHT = 228   # above this on every channel: brighter than a cream veil
MID = 110     # mean below this: dark type or a black button

LEGEND = ". black   Y saturated colour   W near-white   # dark type   - mid-tone"


def classify(p):
    r, g, b = p[:3]
    if r < DARK and g < DARK and b < DARK:
        return "."
    if g > 110 and g - r > 45 and g - b > 45:
        return "Y"                      # saturated colour (green by default)
    if min(r, g, b) > LIGHT:
        return "W"                      # near-white
    if (r + g + b) / 3 < MID:
        return "#"                      # dark type / black button
    return "-"                          # mid-tone: veil, photograph, other colour


# A cell takes the most informative class it contains, so foreground wins over
# background when several classes share one cell.
PRIORITY = ("#", "Y", "W", "-", ".")


def parse_box(s):
    try:
        parts = [int(v) for v in s.split(",")]
    except ValueError:
        raise argparse.ArgumentTypeError("box must be four integers: x0,y0,x1,y1")
    if len(parts) != 4:
        raise argparse.ArgumentTypeError("box must be four integers: x0,y0,x1,y1")
    return parts


def residual(profile, window):
    out, half = [], max(1, window // 2)
    for i, (pos, val) in enumerate(profile):
        lo, hi = max(0, i - half), min(len(profile), i + half + 1)
        base = sum(v for _, v in profile[lo:hi]) / (hi - lo)
        out.append((pos, val - base))
    return out


def do_map(px, box, step):
    x0, y0, x1, y1 = box
    print(LEGEND)
    for y in range(y0, y1, step):
        row = ""
        for x in range(x0, x1, step):
            classes = [classify(px[xx, yy])
                       for yy in range(y, min(y + step, y1))
                       for xx in range(x, min(x + step, x1))]
            row += next((c for c in PRIORITY if c in classes), "-")
        print(f"{y:5d} {row}")


def do_residual(px, box, mode, window, thresh):
    x0, y0, x1, y1 = box
    horizontal = mode == "row"
    span0, span1 = (y0, y1) if horizontal else (x0, x1)
    cross0, cross1 = (x0, x1) if horizontal else (y0, y1)
    axis, cross = ("y", "x") if horizontal else ("x", "y")

    profile = []
    for pos in range(span0, span1):
        total = 0
        for c in range(cross0, cross1):
            p = px[c, pos] if horizontal else px[pos, c]
            total += sum(p) / 3
        profile.append((pos, total / (cross1 - cross0)))

    res = residual(profile, window)
    print(f"{mode}-residual across {cross}{cross0}-{cross1}, baseline window {window}")
    print("positive = brighter than baseline = candidate element")

    bands, start = [], None
    for pos, r in res:
        if r > thresh and start is None:
            start = pos
        elif r <= thresh and start is not None:
            if pos - start > 1:
                bands.append((start, pos - 1))
            start = None
    if start is not None:
        bands.append((start, span1 - 1))

    stride = max(1, (span1 - span0) // 60)
    for pos, r in res:
        if (pos - span0) % stride == 0:
            print(f"  {axis}{pos:5d} {r:+6.1f} {'#' * min(60, max(0, int(r * 3)))}")

    print(f"\n{len(bands)} band(s) above +{thresh}: {bands}")
    if len(bands) > 1:
        print("pitches between band starts: "
              f"{[b[0] - a[0] for a, b in zip(bands, bands[1:])]}")
    if bands:
        print("read the PITCH, not the heights: with a window near the element's own "
              "size only edge transitions survive, so heights under-report size.")


def main():
    ap = argparse.ArgumentParser(
        description="Read a rendered region as text (character map or residual profile).",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("image")
    ap.add_argument("--box", type=parse_box, required=True,
                    help="x0,y0,x1,y1 region to probe, in source pixels")
    ap.add_argument("--mode", choices=("map", "row", "col"), default="map")
    ap.add_argument("--step", type=int, default=2, help="map cell size in px (default 2)")
    ap.add_argument("--window", type=int, default=61,
                    help="baseline window for residual modes (default 61)")
    ap.add_argument("--thresh", type=float, default=2.5,
                    help="residual level counted as the element being present")
    args = ap.parse_args()

    try:
        im = Image.open(args.image).convert("RGB")
    except FileNotFoundError as e:
        print(f"File not found: {e.filename}")
        return 2
    except Exception as e:
        print(f"Could not read image: {e}")
        return 2

    x0, y0, x1, y1 = args.box
    w, h = im.size
    if not (0 <= x0 < x1 <= w and 0 <= y0 < y1 <= h):
        print(f"box {args.box} is outside the image bounds {w}x{h}")
        return 2

    px = im.load()
    print(f"{args.image}  region x{x0}-{x1} y{y0}-{y1}")
    if args.mode == "map":
        do_map(px, args.box, max(1, args.step))
    else:
        do_residual(px, args.box, args.mode, max(3, args.window), args.thresh)
    return 0


if __name__ == "__main__":
    sys.exit(main())
