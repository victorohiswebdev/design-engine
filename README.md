# Design Engine

A multi-output HTML + Tailwind CSS engine that renders **presentation slides, A4
documents, one-page flyers, and brand carousels** through headless Chromium
(Pyppeteer). Build each asset once as HTML, render it to a pixel-perfect PDF or
PNG, and ship.

The successor to the pioneering [`slide-engine`](https://github.com/victorohiswebdev/slide-engine).

## What it produces

| Output | Canvas | Usage |
|--------|--------|-------|
| **Slides / decks** | 1920×1080 per slide | Talks, defenses, masterclasses |
| **A4 documents** | 210×297 mm | Proposals, cover letters, forms, certificates |
| **Flyers / one-pagers** | 1080×1350 or 1920×1080 | Group drops on WhatsApp / Telegram |
| **Brand carousels** | 1080×1080 | Instagram / social content series |

Every output is authored in HTML, styled with Tailwind, and exported to PDF or
PNG. No design tool, no vector software, no slides app. Just code you can review,
version, and reuse.

## Why it exists

Design work that "looks right" is unreliable and unrepeatable, and it depends on a
designer's eye. Design Engine makes the *rules* explicit: a documented formatting
system, a guaranteed-render pipeline, and an automated QA pass that catches
overflowed or clipped layouts before anything ships. Build once, reuse across an
entire brand.

## Quickstart

```bash
# 1. Clone and enter
git clone https://github.com/victorohiswebdev/design-engine && cd design-engine

# 2. Install Pyppeteer>=2.0.0 (downloads its own Chromium — no system Chrome needed)
python3 -m venv venv && source venv/bin/activate
pip install 'pyppeteer>=2.0.0'

# 3. Optimize any images you'll use (photos → JPEG/WebP, long edge 1600px, q82)
pip install Pillow
python3 scripts/image.py your-photo.jpg --out images/your-photo.jpg

# 4. Author a template (copy a scaffold from templates/) → my-slide.html

# 5. Render it (deck, flyer, a4, or carousel)
python3 scripts/generate.py deck my-slide.html
# → my-slide.pdf

# 6. QA it before shipping
python3 scripts/qa.py my-slide.html
# exit 0 = every element stays inside its slide bounds
```

## Repository layout

```
design-engine/
├── docs/          # The rulebook — read this first (esp. formatting-standards.md, image-system.md)
├── templates/     # Reusable scaffolds: deck / a4 / flyer / carousel (+ image treatment library)
├── scripts/       # generate.py (CLI) + qa.py (overflow/clip) + image.py (asset optimizer)
├── examples/      # Curated sample outputs (no client data)
└── venv/          # Local Python env (gitignored)
```

## Docs index

- **`docs/formatting-standards.md`** — the 2026 formatting system: action titles,
  4-layer hierarchy, modular type tokens, WCAG color rules, CVD-safe charts,
  data-ink principle. **Read this before building anything.**
- `docs/image-system.md` — the image pipeline: optimize assets, the treatment
  library (scrims, duotone, tints, masks), which effects survive into a PDF.
- `docs/output-types.md` — when to use deck vs a4 vs flyer vs carousel, and each canvas.
- `docs/brands.md` — brand token systems (LiveFree, FYP, neutral) and their fonts.
- `docs/layout-patterns.md` — reusable layout recipes the generated HTML builds on.
- `docs/qa.md` — the automated QA methodology (overflow + clip checks).
- `docs/pdf-pipeline.md` — how rendering works, font loading, pitfalls, troubleshooting.

## Scripts

```bash
# Render any HTML template to PDF (or PNG via --format png)
python3 scripts/generate.py <deck|a4|flyer|carousel> <your.html>

# Automated layout QA: exit 0 = clean, exit 1 = elements escape their slide
python3 scripts/qa.py <your.html>
```

See `python3 scripts/generate.py --help`.

## License

[MIT](LICENSE) © 2026 Victor Ohis