# Image System

How images get into Design Engine the *right* way: an optimization pipeline, a
CSS treatment library, and the hard facts about what survives into a PDF.

## The core problem

Two things make naive image use painful in this pipeline:

1. **Headless Chrome inflates images in PDFs.** A 548KB JPEG embedded by Chrome
   produced a ~4.4MB PDF. Images re-use the same asset 4-5 times and a deck can
   hit 10MB fast. Chrome encodes each embed largely independently, so bytes
   multiply with usage.
2. **Some CSS image effects silently drop in the PDF print path.**

Both are solved at the source (optimize before render) and by knowing your
treatments (see below).

## 1. Optimize every asset first — `scripts/image.py`

Dependency: `pip install Pillow`. Run it on anything before it goes in a deck:

```bash
source venv/bin/activate
# photos → JPEG or WebP, long edge 1600px, q82
python3 scripts/image.py hero.jpg --out images/hero.jpg

# transparent logos / cut-outs → PNG (needs alpha)
python3 scripts/image.py face.png --keep-alpha --out images/face.png

# control size
python3 scripts/image.py wide.png --max 1280 --out images/wide.jpg
```

What it does: honors EXIF orientation, downscales to the long-edge limit
(LANCZOS), strips all EXIF/ICC metadata, flattens JPEG transparency onto white,
and re-encodes (JPEG/WebP/PnG) at your quality. It prints the before/after size
and warns if the result is still heavy.

**Asset contract (defaults):**
- Photos: JPEG or WebP, long edge **1600px**, q**82**. Enough for a full-bleed
  on a 1920-wide slide.
- Transparent cut-outs / logos: PNG or WebP with `--keep-alpha`.
- Never embed full-resolution originals. The PDF penalty is steep.
- A slide image should be a few hundred KB at most.

## 2. Image treatments — `templates/deck/_image-treatments.html`

A documented, copy-from reference file with the CSS + markup for the standard
treatments. A deck commits to **one** primary treatment and applies it
everywhere; mixed treatments read as assembled, not designed.

| # | Treatment | PDF-safe? |
|---|-----------|-----------|
| S1 | Full-bleed + gradient **scrim** (guaranteed text contrast) | ✅ |
| S2 | **Duotone** (CSS `filter` grayscale+sepia + `mix-blend-mode: color`) | ✅ |
| S3 | **Duotone** (pseudo-element blend, brand split shadows/highlights) | ✅ |
| S4 | **Brand tint** (`mix-blend-mode: multiply` — rich, dark colorize) | ✅ |
| S5 | **CSS mask-image** (vignette / arch / shaped crop) | ✅ |
| S6 | **Glassmorphism** (`backdrop-filter: blur()`) | ❌ **dropped in PDF** |
| S7 | **Framed image card** (image inside padded, shadowed card) | ✅ |
| S8 | **Image grid / collage** | ✅ |

### The glassmorphism trap (verified)

`backdrop-filter: blur()` renders on screen and in PNG screenshots but is
**dropped in the PDF print path** — the "frosted" blur disappears and the card
turns sharp/transparent. Do not rely on it for a delivered deck. Fake the look
with a translucent panel + border + shadow (`S6 .no-blur` variant), which is
PDF-safe.

### The rest are safe

Scrims, both duotone techniques, CSS masks, and all `mix-blend-mode` values
(multiply, screen, lighten, darken, color) survived a real headless-Chromium →
PDF test with pyppeteer 2.0.0 (Sep 2026).

### Legibility rule

Text over any photo goes through a **scrim** (S1) so contrast is guaranteed
regardless of the photo's brightness — never place text directly on a raw
image and hope the light is kind. Use the scrim ratio from the library
(strong at bottom/under text).

## 3. Referencing images in a deck

- Give every image explicit dimensions or an `object-fit: cover/contain` in a
  sized box so layout doesn't reflow mid-render.
- Reference relative to the repo (`images/...`; the render server serves from
  the repo root).
- Do **not** use `loading="lazy"` on any image a PDF needs — lazy images below
  the fold never load in the print pipeline. Let loading stay eager (default).
- Add `alt` text; it is part of the accessibility standard in
  `docs/formatting-standards.md`.
- For screenshots/dashboards use `object-contain`, never `object-cover` (cover
  crops edges and hides information). Add a light padded panel behind them.

## 4. Keeping deck size sane

- Optimize each unique image with `image.py` (Section 1).
- Repeating the **same** image many times multiplies the PDF bytes. Use each
  image a few times at most, or accept a larger PDF for image-heavy decks.
- For web/social delivery where a file must be small, export **per-slide PNGs**
  (`generate.py deck --format png` captures the first slide; screenshot each
  slide individually) instead of one big PDF.
- A 6-slide full-bleed image deck from one optimized 338KB asset rendered to a
  ~10MB PDF in testing. Budget accordingly for client deliverables.

## 5. Example

`templates/deck/deck-image.html` is a working image-forward deck that exercises
S1 (cover scrim), S2 (duotone), S4 (brand tint), S7 (framed), S8 (grid) on a
single optimized asset. Render it with:

```bash
python3 scripts/generate.py deck templates/deck/deck-image.html
```
