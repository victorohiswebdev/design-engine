# Quickstart

Clone, install, build, render, QA, ship. ~10 minutes to your first asset.

## 1. Install

```bash
git clone https://github.com/victorohiswebdev/design-engine && cd design-engine
python3 -m venv venv && source venv/bin/activate
pip install 'pyppeteer>=2.0.0'
```

Pyppeteer downloads its own Chromium on first use — no system Chrome needed.

## 2. Pick your output type

| Output | Canvas | Copy from |
|--------|--------|-----------|
| Slides / deck | 1920×1080 | `templates/deck/` |
| A4 document | 210×297 mm | `templates/a4/` |
| Flyer / one-pager | 1080×1350 | `templates/flyer/` |
| Brand carousel | 1080×1080 | `templates/carousel/` |

## 3. Author your HTML

Copy a scaffold from the matching `templates/` dir into your working folder, then
edit the slides/sections. Read `docs/formatting-standards.md` first — it sets
the rules every well-made asset follows (action titles, hierarchy, color, QA).

Then apply a brand token set (`docs/brands.md`) or keep it neutral.

## 4. Render

```bash
source venv/bin/activate
python3 scripts/generate.py deck my-deck.html     # → my-deck.pdf
python3 scripts/generate.py flyer flyer.html --format png   # → flyer.png
```

## 5. QA before shipping

```bash
python3 scripts/qa.py my-deck.html
# exit 0 = every element stays inside its slide. exit 1 = overflow.
```

## 6. Ship

Deliver the PDF/PNG. Keep the source HTML versioned in your own repo.

## Full docs

- `docs/formatting-standards.md` — the rulebook (read first)
- `docs/output-types.md` — the four canvases
- `docs/brands.md` — LiveFree / FYP / neutral token systems
- `docs/layout-patterns.md` — reusable layout recipes
- `docs/qa.md` — the QA methodology
- `docs/pdf-pipeline.md` — rendering internals + pitfalls