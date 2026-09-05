#!/usr/bin/env python3
"""Design Engine — image optimization pipeline.

Headless Chrome inflates heavy JPEGs significantly when embedding them in a PDF
(measured ~8x: a 548KB JPEG produced a 4.4MB PDF). The right fix is to size the
image at the source: downscale to the largest on-slide size you actually need,
re-encode efficiently, and strip metadata. This script does exactly that as a
thin wrapper around Pillow.

Usage:
    source venv/bin/activate              # needs: pip install Pillow
    python3 scripts/image.py photo.jpg --out images/sample.jpg
    python3 scripts/image.py photo.png --format webp --out images/sample.webp
    python3 scripts/image.py about-face.png --keep-alpha --out images/face.png

Options:
    --max <px>        long-edge limit (default 1600). Deck canvas is 1920 wide,
                      so 1600 is plenty for a full-bleed on most slides.
    --quality <1-100> JPEG/WebP quality (default 82)
    --format <fmt>    jpg | webp | png. default: match source (jpg for photos).
                      Prefer webp/jpg for photos. PNG only when you need alpha.
    --keep-alpha      preserve transparency (png/webp). No-op for jpg.
    --out <path>      destination (required)
    --max-bytes <n>   warn if result exceeds n bytes (~kB*something) — not enforced.

Recommended convention (docs/image-system.md):
    - Photos → JPEG or WebP, long edge ~1600px, q82. This keeps PDFs small.
    - Transparent logos / cut-outs → PNG or WebP with --keep-alpha.
    - Never embed full-resolution originals; the PDF bloat penalty is steep.
"""
import argparse
import os
import sys

try:
    from PIL import Image, ImageOps
except ImportError:
    print("Pillow is required. Run: source venv/bin/activate && pip install Pillow")
    sys.exit(2)

PHOTO_FORMATS = {"jpg", "jpeg", "webp"}


def strip_exif(im):
    """Remove EXIF/ICC metadata so nothing bleeds into the render or leaks data."""
    try:
        exif = im.getexif()
        exif.clear()
        im.info.pop("exif", None)
    except Exception:
        pass
    return im


def main():
    p = argparse.ArgumentParser(description="Design Engine image optimizer")
    p.add_argument("src", help="source image path")
    p.add_argument("--out", required=True, help="destination path")
    p.add_argument("--max", type=int, default=1600, help="long-edge limit (default 1600)")
    p.add_argument("--quality", type=int, default=82, help="JPEG/WebP quality (default 82)")
    p.add_argument("--format", dest="fmt", choices=["jpg", "webp", "png"], default=None)
    p.add_argument("--keep-alpha", action="store_true", help="preserve transparency (png/webp)")
    args = p.parse_args()

    if not os.path.exists(args.src):
        print(f"Source not found: {args.src}")
        sys.exit(2)

    in_bytes = os.path.getsize(args.src)
    im = Image.open(args.src)
    im.load()

    # Honor EXIF orientation so the re-encode doesn't lose rotation.
    im = ImageOps.exif_transpose(im)
    im = strip_exif(im)

    # Downscale to the long-edge limit, preserving aspect (LANCZOS = high quality).
    if max(im.size) > args.max:
        im.thumbnail((args.max, args.max), Image.LANCZOS)

    fmt = (args.fmt or ("png" if (im.format or "").lower() == "png" else "jpg")).lower()
    if fmt == "jpg":
        # JPEG has no alpha — flatten transparency onto white unless kept as png.
        if im.mode in ("RGBA", "LA", "P"):
            rgba = im.convert("RGBA")
            bg = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
            rgba = Image.alpha_composite(bg, rgba).convert("RGB")
            im = rgba
    elif not args.keep_alpha:
        im = im.convert("RGB")

    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    pil_fmt = "JPEG" if fmt == "jpg" else fmt.upper()
    save_kw = {"format": pil_fmt, "quality": args.quality, "optimize": True}
    if fmt == "png":
        save_kw = {"format": "PNG", "optimize": True}

    im.save(args.out, **save_kw)
    out_bytes = os.path.getsize(args.out)
    ratio = out_bytes / in_bytes * 100 if in_bytes else 0
    print(f"{args.src} ({in_bytes/1024:.0f} KB) -> {args.out} ({out_bytes/1024:.0f} KB, {ratio:.0f}%)")
    print(f"  size {im.size[0]}x{im.size[1]}, long edge {max(im.size)}, format {fmt.upper()}, q{args.quality}")
    if out_bytes > 300_000:
        print(f"  WARN: {out_bytes/1024:.0f} KB is large for a slide image — consider --max smaller.")


if __name__ == "__main__":
    main()