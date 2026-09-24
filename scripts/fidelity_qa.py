#!/usr/bin/env python3
"""Fidelity gate — does a replica actually match the design it is copying?

`qa.py` proves a layout is built correctly. `vision_qa.py` proves it looks
correct. Neither can tell you whether you reproduced the *source*. This does,
the only way that is not guesswork: it reduces the reference and the candidate
to the same normalised signature and diffs them element by element, in
percentage points of canvas.

One image argument inspects a signature (how you reverse-engineer a reference).
Two image arguments gate a replica against it.

    python3 scripts/fidelity_qa.py reference.png                    # inspect
    python3 scripts/fidelity_qa.py reference.png my-replica.png     # gate
    python3 scripts/fidelity_qa.py ref.png mine.png --tol 0.5 --json report.json

Exit codes follow `qa.py`: 0 = PASS, 1 = FAIL, 2 = usage / IO / decode error.
Warnings do not fail the run unless `--strict` is given.

What it measures, and why each one earns its place
    content   outer bbox of all non-background ink — is the whole thing the right size
    block     the solid colour slab (e.g. a NO tile) — position and extent
    glyph     the knock-out glyphs INSIDE that slab
    bands     horizontal slices separated by fully empty rows, so a heading row is
              measured independently of the row beneath it
    runs      column runs WITHIN each band — what makes individual letters
              measurable instead of one undifferentiated smear

THREE TRAPS, each of which cost a debugging round. The code handles all three:
  1. A source screenshot often carries a full-width border row. That one row puts
     ink in every column, so whole-image column runs collapse to a single run and
     letter segmentation silently returns NOTHING. Such rows are dropped.
  2. Coloured display text is the same colour as a coloured slab, so detecting the
     slab by colour DENSITY merges the two. The slab is found by requiring one
     CONTIGUOUS run per row, which fragmented letterforms can never satisfy.
  3. Bands merge when two elements sit closer than about 3 normalised px apart, so
     a BAND-count mismatch is a real defect (two elements touching, or an outline
     that grew into a neighbour) and fails the gate. A RUN-count mismatch within a
     band is a warning, not a failure: small text in a low-resolution reference
     blurs together and legitimately segments into fewer runs than a crisp render.
     When run counts disagree the runs are not compared pairwise — that would
     report a meaningless 20pp+ delta between two different letters — and the
     band's overall ink envelope is compared instead.
"""
import argparse
import json
import sys

from PIL import Image

NORM = 1000        # both images are resampled to this square before measuring
DARK = 28          # RGB below this on every channel reads as background
MIN_BAND = 3       # ignore bands thinner than this
MIN_RUN = 2        # ignore column runs narrower than this
BLOCK_FRAC = 0.15  # a row belongs to the slab when its longest contiguous run exceeds this
DEFAULT_TOL = 1.0  # percentage points; the gate fails above this
ASPECT_WARN = 1.0  # flag an aspect-ratio mismatch above this percentage


def classify(p):
    """'.' background, 'Y' colour, 'W' everything else (light ink by default)."""
    r, g, b = p[:3]
    if r < DARK and g < DARK and b < DARK:
        return "."
    if r > 190 and g > 140 and b < 110:
        return "Y"
    return "W"


def runs_in(grid, lo, hi, want, w):
    """Column runs of `want` over rows lo..hi as (x0%, x1%, tallest stroke in that run)."""
    spans, s = [], None
    for x in range(w):
        n = sum(1 for y in range(lo, hi) if grid[y][x] == want)
        if n > 0 and s is None:
            s = x
        elif n == 0 and s is not None:
            if x - s >= MIN_RUN:
                spans.append((s, x - 1))
            s = None
    if s is not None:
        spans.append((s, w - 1))
    return [
        (a / w * 100, b / w * 100,
         max(sum(1 for y in range(lo, hi) if grid[y][x] == want) for x in range(a, b + 1)))
        for a, b in spans
    ]


def signature(path):
    src = Image.open(path)
    im = src.convert("RGB").resize((NORM, NORM), Image.LANCZOS)
    w = h = NORM
    px = im.load()
    grid = [[classify(px[x, y]) for x in range(w)] for y in range(h)]

    sig = {"path": path, "size": src.size, "aspect": src.size[0] / src.size[1]}

    rows = [sum(1 for x in range(w) if grid[y][x] != ".") for y in range(h)]
    edge = [rows[y] > 0.95 * w for y in range(h)]     # trap 1: screenshot border rows

    pts = [(x, y) for y in range(h) for x in range(w)
           if grid[y][x] != "." and not edge[y]]
    sig["content"] = (
        (min(p[0] for p in pts) / w * 100, max(p[0] for p in pts) / w * 100,
         min(p[1] for p in pts) / h * 100, max(p[1] for p in pts) / h * 100)
        if pts else None)

    bands, start = [], None
    for y in range(h):
        live = rows[y] > 0 and not edge[y]
        if live and start is None:
            start = y
        elif not live and start is not None:
            if y - start > MIN_BAND:
                bands.append((start, y - 1))
            start = None
    if start is not None:
        bands.append((start, h - 1))

    sig["bands"] = [
        {"y": (a / h * 100, b / h * 100),
         "white": runs_in(grid, a, b + 1, "W", w),
         "yellow": runs_in(grid, a, b + 1, "Y", w)}
        for a, b in bands
    ]

    # trap 2: the slab is the only thing with one CONTIGUOUS run per row
    slab_rows, slab_x = [], []
    for y in range(h):
        best = cur = 0
        bs = cur_s = None
        for x in range(w):
            if grid[y][x] == "Y":
                if cur == 0:
                    cur_s = x
                cur += 1
                if cur > best:
                    best, bs = cur, cur_s
            else:
                cur = 0
        if best > BLOCK_FRAC * w:
            slab_rows.append(y)
            slab_x.append((bs, bs + best - 1))

    if slab_rows:
        y0, y1 = min(slab_rows), max(slab_rows)
        x0 = min(a for a, _ in slab_x)
        x1 = max(b for _, b in slab_x)
        sig["block"] = (x0 / w * 100, x1 / w * 100, y0 / h * 100, y1 / h * 100)

        ix0, ix1 = x0 + int(0.02 * w), x1 - int(0.02 * w)
        iy0, iy1 = y0 + int(0.02 * h), y1 - int(0.02 * h)
        dark = [(x, y) for y in range(iy0, iy1) for x in range(ix0, ix1) if grid[y][x] == "."]
        sig["glyph"] = (
            (min(d[0] for d in dark) / w * 100, max(d[0] for d in dark) / w * 100,
             min(d[1] for d in dark) / h * 100, max(d[1] for d in dark) / h * 100)
            if dark else None)
    else:
        sig["block"] = sig["glyph"] = None
    return sig


def envelope(band, tag):
    """Outer ink extent of a band's runs: (x0, x1). Robust when run counts differ."""
    key = "white" if tag == "W" else "yellow"
    rs = band[key]
    return (rs[0][0], rs[-1][1]) if rs else None


def compare(ref, cand, tol):
    """Returns (rows, fails, warns). rows are (label, ref, cand, delta|None)."""
    rows, fails, warns = [], [], []

    def scalar(label, rv, cv):
        if rv is None or cv is None:
            rows.append((label, rv, cv, None))
            if (rv is None) != (cv is None):
                fails.append(f"{label}: present in one image, absent in the other")
            return
        d = abs(cv - rv)
        rows.append((label, rv, cv, d))
        if d > tol:
            fails.append(f"{label}: {d:.1f}pp off (tolerance {tol})")

    for key in ("content", "block", "glyph"):
        rb, cb = ref[key], cand[key]
        for i, nm in enumerate(("x0", "x1", "y0", "y1")):
            scalar(f"{key} {nm}",
                   rb[i] if rb else None, cb[i] if cb else None)

    if len(ref["bands"]) != len(cand["bands"]):
        fails.append(
            f"band count {len(cand['bands'])} != reference {len(ref['bands'])} — two "
            f"elements are touching or an outline grew into a neighbour "
            f"(ref starts {[round(b['y'][0], 1) for b in ref['bands']]}, "
            f"candidate {[round(b['y'][0], 1) for b in cand['bands']]})")
        return rows, fails, warns

    for i, (rb, cb) in enumerate(zip(ref["bands"], cand["bands"])):
        scalar(f"band {i} y0", rb["y"][0], cb["y"][0])
        scalar(f"band {i} y1", rb["y"][1], cb["y"][1])
        for tag in ("W", "Y"):
            re_, ce = envelope(rb, tag), envelope(cb, tag)
            if re_ and ce:
                scalar(f"band {i} {tag} ink x0", re_[0], ce[0])
                scalar(f"band {i} {tag} ink x1", re_[1], ce[1])
            rn = len(rb["white" if tag == "W" else "yellow"])
            cn = len(cb["white" if tag == "W" else "yellow"])
            if rn != cn:
                warns.append(
                    f"band {i} {tag}: {cn} runs vs reference {rn} — fine detail segments "
                    f"differently (usually source blur); envelope compared instead")
            elif rn:
                for j in range(rn):
                    src_ = rb["white" if tag == "W" else "yellow"][j]
                    cnd = cb["white" if tag == "W" else "yellow"][j]
                    scalar(f"band {i} {tag}{j} x0", src_[0], cnd[0])
                    scalar(f"band {i} {tag}{j} x1", src_[1], cnd[1])
    return rows, fails, warns


def show(sig, indent="  "):
    print(f"{indent}size {sig['size']}  aspect {sig['aspect']:.4f}")
    for key in ("content", "block", "glyph"):
        b = sig[key]
        print(f"{indent}{key:9}" + ("none" if not b else
              f"x {b[0]:5.1f}-{b[1]:5.1f}%  y {b[2]:5.1f}-{b[3]:5.1f}%"))
    for i, b in enumerate(sig["bands"]):
        print(f"{indent}band {i}: y {b['y'][0]:5.1f}-{b['y'][1]:5.1f}%   "
              f"(h {b['y'][1] - b['y'][0]:4.1f}pp)")
        for tag, key in (("W", "white"), ("Y", "yellow")):
            if b[key]:
                print(f"{indent}    {tag}: " + "  ".join(
                    f"{a:5.1f}->{c:5.1f}(h{d})" for a, c, d in b[key]))


def main():
    ap = argparse.ArgumentParser(description="Fidelity gate: diff a replica against its reference.")
    ap.add_argument("reference")
    ap.add_argument("candidate", nargs="?")
    ap.add_argument("--tol", type=float, default=DEFAULT_TOL,
                    help=f"max allowed delta in percentage points (default {DEFAULT_TOL})")
    ap.add_argument("--strict", action="store_true", help="warnings also fail the run")
    ap.add_argument("--json", metavar="PATH", help="write a machine-readable report")
    ap.add_argument("--quiet", action="store_true", help="only print the verdict")
    args = ap.parse_args()

    try:
        ref = signature(args.reference)
        cand = signature(args.candidate) if args.candidate else None
    except FileNotFoundError as e:
        print(f"File not found: {e.filename}")
        return 2
    except Exception as e:                                   # decode / IO
        print(f"Could not read image: {e}")
        return 2

    if not args.quiet or cand is None:
        print(f"REFERENCE {args.reference}")
        show(ref)
    if cand is None:
        return 0
    if not args.quiet:
        print(f"\nCANDIDATE {args.candidate}")
        show(cand)

    rows, fails, warns = compare(ref, cand, args.tol)
    deltas = [d for _, _, _, d in rows if d is not None]
    worst = max(deltas) if deltas else 0.0
    worst_lbl = max((r for r in rows if r[3] is not None), key=lambda r: r[3], default=("-",))[0]

    if not args.quiet:
        print(f"\nDELTAS (percentage points of canvas; tolerance {args.tol})")
        over = [r for r in rows if r[3] is not None and r[3] > args.tol]
        shown = sorted(rows, key=lambda r: -(r[3] or 0))[:16]
        print(f"  {'element':<22}{'reference':>10}{'replica':>10}{'delta':>9}")
        for label, rv, cv, d in shown:
            if d is None:
                continue
            print(f"  {label:<22}{rv:>10.1f}{cv:>10.1f}{d:>9.1f}"
                  + ("  <-- over" if d > args.tol else ""))
        if len(rows) > len(shown):
            print(f"  ... {len(rows)} elements compared, {len(over)} over tolerance; "
                  f"worst 16 shown")

        if ref["aspect"] and cand["aspect"]:
            drift = abs(cand["aspect"] - ref["aspect"]) / ref["aspect"] * 100
            if drift > ASPECT_WARN:
                print(f"\n  WARN aspect {cand['aspect']:.4f} vs reference "
                      f"{ref['aspect']:.4f} ({drift:.2f}% off) — a non-square canvas is "
                      f"being compared as a square")

    for w in warns:
        print(f"  WARN {w}")
    for f in fails:
        print(f"  FAIL {f}")

    if args.json:
        with open(args.json, "w") as fh:
            json.dump({"reference": args.reference, "candidate": args.candidate,
                       "tolerance": args.tol, "worst_delta": worst,
                       "worst_element": worst_lbl, "fails": fails, "warns": warns,
                       "pass": not fails and not (args.strict and warns),
                       "deltas": [{"element": l, "reference": r, "candidate": c, "delta": d}
                                  for l, r, c, d in rows if d is not None]}, fh, indent=2)

    print(f"\nfidelity: worst delta {worst:.1f}pp on '{worst_lbl}' "
          f"| {len(fails)} fail(s), {len(warns)} warn(s)")
    if fails:
        print("RESULT: FAIL — tighten the elements flagged above")
        return 1
    if warns and args.strict:
        print("RESULT: FAIL — warnings are failures under --strict")
        return 1
    if warns:
        print("RESULT: PASS (with warnings)")
        return 0
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
