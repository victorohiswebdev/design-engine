# QA methodology

Every asset must pass an automated QA pass before it ships. The engine's QA
script (`scripts/qa.py`) checks the **real** layout condition in a rendered
headless browser — not guesses, not screenshots.

## Why not a naive text-clip check

`scrollHeight > clientHeight` is a trap on display headings. Montserrat Black's
font metrics exceed the line box even on single-line headings, so the naive
check reports a "clip" when nothing is actually clipped. The definitive check is
**boundingClientRect vs the section bounds**, which tests the actual visible
geometry.

## The bounds check (definitive)

```python
# scripts/qa.py — logic
for each <section>:
    sRect = section.getBoundingClientRect()
    for each non-absolute h1,h2,h3,p,span,div into it:
        r = el.getBoundingClientRect()
        overflow if r.right > sRect.right + 1 or
                   r.bottom > sRect.bottom + 1 or
                   r.left < sRect.left - 1
```

- `position: absolute` children are excluded — ghost step-numbers and
  decorations bleed off-edge *by design* and are clipped by `overflow:hidden`.
- Exit code **0 = clean**, **1 = an element escapes its slide bounds**.

## CLI

```bash
python3 scripts/qa.py your-deck.html     # → exit 0 clean / 1 overflow
python3 scripts/qa.py --dump-text your-deck.html
```

`--dump-text` prints the rendered DOM `innerText` for content verification.
Verify content against the **DOM**, never pypdf text extraction: custom fonts,
letter-spacing, and `<br>`-split titles make PDF text extraction unreliable and
report genuinely-rendered text as "missing".

## What each result means

| Check result | Meaning | Fix |
|--------------|---------|-----|
| Overflow past slide **bottom/right** | Real layout bug — content is bleeding off-slide | Reduce row padding/gaps, never the font |
| `CLIP` on a large display heading | Usually a line-box artifact from `leading-none` | Use `leading-[1.25]`+ line-height, not smaller fonts |
| `OVERFLOW` past the container (flyer) | Content taller than the canvas — CTA pushed off-frame | Compress spacing, never text |

## Display-type leading rule

Large display type (76–150px) needs generous leading:

- Cover titles and 88–110px section headings: `leading-[1.25]`
- 64px h2s: `leading-[1.3]`

At these sizes, `leading-none` clips visibly and `leading-[1.06]`–`[1.15]`
still trips the bounds check on 88–110px headings.

## Verifying content, images, and colors

- **Content:** DOM `innerText` (see `--dump-text`), not PDF text extraction.
- **Images:** reference `/images/*` and confirm they exist in `images/` before
  render (404s are silent in PDFs). Extract report images from a source DOCX
  first if needed.
- **Dark sections:** verify via `getComputedStyle` that every dark section
  reports the dark token and light sections stay transparent (inheriting
  `body` white) — catches the cascade-layers bug that renders dark slides
  white-on-white. See `pdf-pipeline.md`.
- **Flyers:** assert the content block height ≤ container height with
  `getBoundingClientRect()` before screenshotting.