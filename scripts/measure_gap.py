#!/usr/bin/env python3
"""Measure the largest empty band inside a rendered design.

The eye says "there's a gap there"; this says how big it is, in pixels and in
percent of canvas height. Never tune spacing by guess — measure it, move it, and
re-measure.

The background colour and the scan band are detected from the image, so this
works on any canvas rather than only the cream one it was first written for.

    python3 scripts/measure_gap.py my-post.png
    python3 scripts/measure_gap.py my-post.png --json report.json

Exit codes: 0 = measured, 2 = usage / IO error.
"""
import argparse
import json
import sys
from collections import Counter

from PIL import Image

TOL = 12       # per-channel distance from the background that still counts as background
INSET = 0.02   # ignore this fraction of the content width at each side (edge antialiasing)


def dominant(im):
    """The most common colour, quantised so near-identical background pixels agree."""
    counts = im.getcolors(1 << 24) or []
    c = Counter((p[0] // 8 * 8, p[1] // 8 * 8, p[2] // 8 * 8) for _n, p in counts
                for _ in range(min(_n, 64)))
    return c.most_common(1)[0][0]


def is_bg(p, bg):
    return (abs(p[0] - bg[0]) <= TOL and abs(p[1] - bg[1]) <= TOL and abs(p[2] - bg[2]) <= TOL)


def main():
    ap = argparse.ArgumentParser(description="Find the largest ink-free band in a render.")
    ap.add_argument("image")
    ap.add_argument("--margin", type=int, default=0,
                    help="expand the scan band beyond the content bbox; 0 (default) keeps "
                         "the search INSIDE the content, which is where a dead zone matters")
    ap.add_argument("--json", metavar="PATH")
    args = ap.parse_args()

    try:
        im = Image.open(args.image).convert("RGB")
    except FileNotFoundError as e:
        print(f"File not found: {e.filename}")
        return 2
    except Exception as e:
        print(f"Could not read image: {e}")
        return 2

    w, h = im.size
    px = im.load()
    bg = dominant(im)

    pts = [(x, y) for y in range(h) for x in range(w) if not is_bg(px[x, y], bg)]
    print(f"canvas        : {w}x{h}")
    print(f"background    : #{bg[0]:02X}{bg[1]:02X}{bg[2]:02X} (auto-detected)")
    if not pts:
        print("content       : none — the canvas is a flat fill")
        return 0

    cx0, cx1 = min(p[0] for p in pts), max(p[0] for p in pts)
    cy0, cy1 = min(p[1] for p in pts), max(p[1] for p in pts)
    print(f"content bbox  : x {cx0}-{cx1}, y {cy0}-{cy1}")

    # scan the content column, inset to dodge edge antialiasing
    x0 = min(cx0 + int((cx1 - cx0) * INSET), w - 1)
    x1 = max(cx1 - int((cx1 - cx0) * INSET), x0 + 1)
    y0 = max(0, cy0 - args.margin)
    y1 = min(h, cy1 + args.margin)
    print(f"scan band     : x {x0}-{x1}, y {y0}-{y1}")

    best_len, best_start, cur_start = 0, None, None
    for y in range(y0, y1):
        if any(not is_bg(px[x, y], bg) for x in range(x0, x1)):
            cur_start = None
        else:
            if cur_start is None:
                cur_start = y
            run = y - cur_start + 1
            if run > best_len:
                best_len, best_start = run, cur_start

    if best_start is None:
        print("largest gap   : none — content fills the scanned column")
        return 0

    pct = best_len / h * 100
    print(f"largest gap   : {best_len}px  ({pct:.1f}% of canvas height)")
    print(f"gap rows      : y {best_start} -> {best_start + best_len - 1}")
    if args.json:
        with open(args.json, "w") as fh:
            json.dump({"image": args.image, "canvas": [w, h],
                       "background": list(bg), "content_bbox": [cx0, cy0, cx1, cy1],
                       "gap_px": best_len, "gap_pct": pct,
                       "gap_rows": [best_start, best_start + best_len - 1]}, fh, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
