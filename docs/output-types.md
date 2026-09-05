# Output Types

Design Engine produces seven kinds of output. Each has a fixed canvas, a specific
rendering path, and its own QA rules. Pick the type first, then build the HTML.

## Slides / decks — 1920×1080

**Canvas:** 1920×1080 per slide. Each slide is a `<section class="relative w-screen h-screen">`
(or a fixed 1920×1080 block). The PDF is exported at exactly `1920px × 1080px`
per page.

**Use for:** talks, defenses, masterclasses, workshops, pitches that run
full-screen or in a slides app.

**Structure rhythm (for decks with sections):** alternate
dark → light → dark → light → dark. Section variety keeps a long deck from
going flat. Covers and dividers carry the dark theme; content slides run light.

**Rendering:** `python3 scripts/generate.py deck your-deck.html`

**QA:** every element's bounding rect must stay inside its `<section>`.
Run `python3 scripts/qa.py your-deck.html`.

## A4 documents — 210×297 mm

**Canvas:** A4 (210×297mm), continuous flow (no forced page breaks). When a
section can't finish on a page the remainder continues on the next. Inter-section
gap is 6mm (calibrated). Covers must be vertically centered.

**Use for:** proposals, cover letters, forms, certificates, program outlines —
anything printable and formal.

**Rendering:** `python3 scripts/generate.py a4 your-doc.html`

**QA:** per-page text extraction (blocks sorted by y,x — PyMuPDF block order is
*not* visual order), and a vision check of the cover for optical centering.

## Flyers / one-pagers — 1080×1350 or 1920×1080

**Canvas (portrait):** 1080×1350 (4:5) — the format that displays fully in
WhatsApp/Telegram group drops.
**Canvas (landscape):** 1920×1080 — slide-like single pages.

**Use for:** group-drop marketing flyers, promo cards, one-page shareables.

**Rendering to PNG** (not PDF):
```python
page.screenshot({'path': 'flyer.png', 'clip': {'x':0,'y':0,'width':1080,'height':1350}})
```

**QA:** the content block height must equal the container height. Measure
`container.getBoundingClientRect().height` — if content is taller than the
canvas, the CTA gets pushed off-frame (silent in screenshots). Compress
**spacing** (paddings/gaps/fonts), never the text, to fix overflow.

## Social — 1080×1080 / 1080×1350 / 1080×1920

**Canvas:** `social` 1080×1080 (1:1 feed), `social-portrait` 1080×1350 (4:5, max real estate), `story` 1080×1920 (9:16).
Feed posts compete in the scroll — different rules from decks. Full system in `docs/social.md`.

**Use for:** Instagram feed, LinkedIn, X — anywhere the post must win in 1.7s.

**Scaffolds:** `templates/social/square.html`, `portrait.html`, `story.html` — copy, replace copy/colors, render:

```bash
python3 scripts/generate.py social templates/social/square.html --format png
python3 scripts/generate.py social-portrait templates/social/portrait.html --format png
python3 scripts/generate.py story templates/social/story.html --format png
```

**QA:** same bounds check as flyer/carousel. Design rules (from the Madonna fix): headline 64–120px, body ≥18px, 1:2.5 ratio, outer padding 24–32px, center 60% owns the hook, 60-30-10 color (60 neutral / 30 charcoal / 10 red pop; gold is hairline only on cream), 3-level hierarchy (Hook → sub → CTA), safe zones top 12% / bottom 20%.

## Brand carousels — 1080×1080 (legacy)

**Canvas:** 1080×1080 square.

**Use for:** multi-slide brand series (legacy). Prefer `templates/social/` for new work; `carousel` remains for backward compat.

**Rendering:** PNG screenshot at 1080×1080, one page per carousel frame.

**QA:** same bounds check as flyers — each frame's content must fit the square.

## Choosing the right type

| Need | Output | Canvas |
|------|--------|--------|
| Present to an audience | **deck** | 1920×1080 |
| Formal / printable | **a4** | 210×297 mm |
| Drop a promo in a group | **flyer** | 1080×1350 |
| Feed post (default) | **social** | 1080×1080 |
| Feed post (max height) | **social-portrait** | 1080×1350 |
| Story / Reel cover | **story** | 1080×1920 |
| Social series (legacy) | **carousel** | 1080×1080 |

Start from `scripts/generate.py --help` to see each render path.
