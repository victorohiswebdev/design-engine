# Design Engine

A multi-output HTML + Tailwind CSS engine that renders **presentation slides, A4
documents, one-page flyers, brand carousels, and social feed posts** through headless Chromium
(Pyppeteer). Build each asset once as HTML, render it to a pixel-perfect PDF or
PNG, and ship.

The successor to the pioneering [`slide-engine`](https://github.com/victorohiswebdev/slide-engine).

## What it produces

| Output | Canvas | Usage |
|--------|--------|-------|
| **Slides / decks** | 1920×1080 per slide | Talks, defenses, masterclasses |
| **A4 documents** | 210×297 mm | Proposals, cover letters, forms, certificates |
| **Flyers / one-pagers** | 1080×1350 or 1920×1080 | Group drops on WhatsApp / Telegram |
| **Social feed** | 1080×1080 or 1080×1350 | Instagram / LinkedIn / X — wins in 1.7s |
| **Stories** | 1080×1920 | Stories / Reel covers |
| **Brand carousels** | 1080×1080 | Multi-slide brand series (legacy) |

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

# 2. Install — Pyppeteer>=2.0.0 downloads its own Chromium, no system Chrome needed
python3 -m venv venv && source venv/bin/activate
pip install 'pyppeteer>=2.0.0' Pillow numpy

# 3. Optimize any images you'll use (photos → JPEG/WebP, long edge 1600px, q82)
python3 scripts/image.py your-photo.jpg --out images/your-photo.jpg

# 4. Author a template (copy a scaffold from templates/) → my-slide.html
#    Decks: templates/deck/ · A4: templates/a4/ · Flyer: templates/flyer/ · Social: templates/social/ · Charts: templates/charts/

# 5. Render it (deck, a4, flyer, carousel, social, social-portrait, story)
python3 scripts/generate.py deck my-slide.html          # → my-slide.pdf
python3 scripts/generate.py social my-post.html --format png  # → my-post.png (1080x1080)
python3 scripts/generate.py story my-story.html --format png  # → my-story.png (1080x1920)

# 6. Geometric QA — no element escapes, no image 404s, no empty slides
python3 scripts/qa.py my-slide.html --strict
# exit 0 = clean

# 7. Perceptual QA — muddy gradients, brand drift, blur, crowding (no API needed)
python3 scripts/vision_qa.py my-slide.html --brand livefree --strict

# 8. With an API key, add an LLM second pair of eyes (Gemini/Claude/OpenAI/any OpenAI-compatible)
GEMINI_API_KEY=... python3 scripts/vision_qa.py my-slide.html --brand livefree --vision
```

## Repository layout

```
design-engine/
├── docs/          # The rulebook — read this first (esp. formatting-standards.md, social.md)
├── templates/     # Scaffolds: deck / a4 / flyer / social / carousel + charts/ snippets
├── scripts/       # generate.py + image.py + qa.py + vision_qa.py
├── examples/      # Curated sample outputs (no client data)
└── venv/          # Local Python env (gitignored)
```

## Docs index

- **`docs/formatting-standards.md`** — the 2026 formatting system: action titles,
  4-layer hierarchy, modular type tokens, WCAG color rules, CVD-safe charts,
  data-ink principle, depth-without-clutter. **Read this before building anything.**
- `docs/social.md` — the social feed system: 60-30-10 color, 3-level hierarchy, feed-scale type (64–120px), whitespace 30%, safe zones. **Read before any Instagram/Story.**
- `docs/output-types.md` — when to use deck vs a4 vs flyer vs social vs story, and each canvas.
- `docs/brands.md` — brand token systems (LiveFree, FYP, neutral) and their fonts.
- `docs/layout-patterns.md` — reusable layout recipes the generated HTML builds on.
- `docs/image-system.md` — the image pipeline: optimize assets, the treatment
  library (scrims, duotone, tints, masks), which effects survive into a PDF.
- `docs/charts.md` — dataviz kit: Okabe-Ito, direct labels, data-ink — bar, line, donut, table-as-visual (Phase 5).
- `docs/qa.md` — geometric QA: overflow, clip, missing images, empty slides.
- `docs/vision-qa.md` — perceptual QA: muddy gradients, brand drift, blur, crowding (Phase 4, heuristics + optional vision LLM).
- `docs/pdf-pipeline.md` — how rendering works, font loading, pitfalls, troubleshooting.

## Scripts

```bash
# Render any HTML template to PDF (or PNG via --format png)
python3 scripts/generate.py <deck|a4|flyer|carousel> <your.html>

# Automated layout + design QA: 0 = clean, 1 = fail.
# Flags overflow, broken/missing images, empty slides; warns on clip, missing
# alt, and white text over a plain photo. --strict makes warnings fail too.
python3 scripts/qa.py <your.html>
python3 scripts/qa.py <your.html> --strict

# Perceptual vision QA (Phase 4): muddy gradients, brand drift, blur, crowding.
# Heuristics run with no API key; --vision adds an LLM second pair of eyes.
python3 scripts/vision_qa.py <your.html> --brand livefree
python3 scripts/vision_qa.py <your.html> --brand livefree --vision --out report.json
```

See `python3 scripts/generate.py --help`.

## License

[MIT](LICENSE) © 2026 Victor Ohis