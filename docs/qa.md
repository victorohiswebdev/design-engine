# QA methodology

Every asset must pass an automated gate before it ships. The gate checks the
**real** rendered layout and the **design health** of a deck in a headless
browser — not guesses, not screenshots. `scripts/qa.py` is the gate.

## Why not a naive text-clip check

`scrollHeight > clientHeight` is a trap on display headings. Montserrat Black's
font metrics exceed the line box even on single-line headings, so the naive
check reports a "clip" when nothing is clipped. The definitive check is
**boundingClientRect vs the container**, which tests actual visible geometry.

## The checks

| Check | Severity | What it catches |
|-------|----------|-----------------|
| **OVERFLOW** | fail | An element escapes its section/container bounds (the real bleed). `position:absolute` decorations are excluded by design. |
| **IMG-MISSING** | fail | An `<img>` failed to load (`naturalWidth===0` / 404). Slides render blank and nobody notices until delivery. |
| **EMPTY-SLIDE** | fail | A section with almost no content and no image: a dropped/forgotten slide. Sparse "anchor" slides (one big number, a bold statement) are excluded via a big-text check. |
| **CLIP** | warn | A text box may clip its glyphs. Ignore display headings (line-box artifact — use `leading-[1.25]`+ if really flagged). |
| **NO-ALT** | warn | An `<img>` is missing the `alt` attribute (a11y rule from formatting-standards). Decorative `alt=""` is fine; only total absence is flagged. |
| **SCRIM-RISK** | warn | White/near-white text sits over a **plain** full-bleed photo with no scrim/tint/duotone overlay, so contrast is not guaranteed. |

## Exit codes & `--strict`

```bash
python3 scripts/qa.py my-deck.html                # 0 = PASS, 1 = FAIL
python3 scripts/qa.py my-deck.html --strict       # warnings also become failures
python3 scripts/qa.py my-deck.html --dump-text    # print rendered DOM innerText
```

- **0 = PASS.** No fail-level issues. Warnings may still be printed.
- **1 = FAIL.** Any OVERFLOW, IMG-MISSING, or EMPTY-SLIDE (or any warning when
  `--strict`). Deal with what's named, don't guess.
- **2 = usage / file-not-found / render error.**

Use `--strict` for a client deliverable or a public deck; use the relaxed run
during drafting.

## How the gate runs

1. Serves the asset from the **common parent** of the working directory and the
   asset, so repo-relative (`../../images/...`) and standalone fixtures both
   resolve.
2. Loads in Pyppeteer (headless Chromium) at 1920×1080, waits for
   `networkidle0` + fonts.
3. Evaluates the checks against the real layout.

## Verified behavior

- The 5 bundled templates (`templates/`) pass with **0 fails, 0 warns**.
- A fixture with a broken image, an empty slide, and white-text-on-plain-photo
  fails as expected (IMG-MISSING + EMPTY-SLIDE fail; NO-ALT + SCRIM-RISK warn).
- `--strict` elevates the warning-only case (NO-ALT + SCRIM-RISK) from exit 0
  to exit 1.

## Documented fix guidance

| Check | Fix |
|-------|-----|
| OVERFLOW past container | Reduce row padding/gaps, never shrink fonts. |
| IMG-MISSING | Confirm the `images/` path exists and run `scripts/image.py` on the asset. |
| EMPTY-SLIDE | Fill the slide or delete it — a blank page ships silently. |
| CLIP on large display | Add `leading-[1.25]`+ line-height, not smaller fonts. |
| NO-ALT | Add an alt attribute (empty `alt=""` for decorative images). |
| SCRIM-RISK | Add a scrim, brand tint, or duotone overlay (see `templates/deck/_image-treatments.html`). |

## Display-type leading rule

Large display type (76–150px) needs generous leading: cover titles and 88–110px
headings use `leading-[1.25]`; 64px h2s use `leading-[1.3]`. At these sizes
`leading-none` clips visibly and `leading-[1.06]`–`[1.15]` still trips the
bounds check.

## Verifying content & colors

- **Content:** `--dump-text` prints the DOM `innerText`. Verify against the DOM,
  never pypdf (custom fonts, letter-spacing, and `<br>`-splits make PDF text
  extraction unreliable).
- **Broken images:** surfaced by the IMG-MISSING check in the browser.
- **Dark sections:** verify via `getComputedStyle` that dark sections report the
  dark token and light sections stay transparent (inheriting `body` white) —
  catches the cascade-layers bug that renders dark slides white-on-white
  (see `docs/pdf-pipeline.md`).
- **Flyers:** assert the content block height ≤ container with
  `getBoundingClientRect()` so the CTA isn't pushed off-canvas.