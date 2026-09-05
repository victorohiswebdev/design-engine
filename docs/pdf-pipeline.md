# PDF / PNG pipeline

How rendering works, why the pieces are where they are, and the pitfalls that
silently break output. The engine uses **Pyppeteer** — it downloads its own
Chromium, so no system Chrome is required (Playwright is unsupported on newer
Ubuntu; see pitfalls).

## Render path

```
author HTML → local HTTP server → headless Chromium (Pyppeteer)
           → networkidle0 + fonts loaded → PDF (printBackground, exact canvas) | PNG screenshot
```

`scripts/generate.py <type> <file>` encapsulates this. Details:

1. Starts a local HTTP server serving the project directory (Tailwind CDN +
   Google Fonts need a real origin, not `file://`).
2. Launches headless Chromium via Pyppeteer with `--no-sandbox`
   (`--disable-dev-shm-usage` on constrained hosts).
3. Loads at the target canvas (1920×1080 for decks).
4. Waits for `networkidle0`, then force-loads every font weight and waits for
   `document.fonts.ready`.
5. **PDF:** `page.pdf({printBackground: true, width, height, margins: 0})`.
   **PNG:** `page.screenshot({clip: {x,y,width,height}})`.

## Font loading (the #1 cause of "looks like a default font")

`networkidle0` alone is *not* enough. Google Fonts may not be applied before
export. **Force-load every weight**, then export:

```python
await page.evaluate("""async () => {
  await Promise.all(['400','500','600','700','800','900'].map(w => document.fonts.load(w + ' 16px Montserrat')));
  await document.fonts.ready;
}""")
```

Then wait for `document.fonts.ready`. Do not use `document.fonts.check()` as a
gate — it returns `false` for weights no element currently uses. Force-load
first, then export.

## The cascade-layers dark-slide bug

Tailwind v4 puts utilities in `@layer utilities`. Unlayered author CSS beats
layered CSS regardless of specificity. So:

```css
/* WRONG — overrides bg-navy on <section>, dark slides render WHITE */
section { background-color: #ffffff; }
```

**Fix:** never set `background-color` on the bare `section` selector. Light
slides inherit `body { background-color: #ffffff }`. Verify after every render
via `getComputedStyle`: dark sections must report the dark token (e.g.
`rgb(11, 17, 32)`), light sections `rgba(0,0,0,0)`.

## Unicode symbols fall back to DejaVuSans

Montserrat has no `❌`, `✓`, `✕`, `✔` glyphs; Chromium renders them from
DejaVuSans and the style mismatch reads as off-brand. **Avoid these characters**
in copy — draw indicators with CSS or use Montserrat-covered punctuation
(`×`, `+`, `→`).

## Port binding on re-runs

`TCPServer(("", PORT))` fails with `Address already in use` when a previous run
left its server bound. Loop over ports (`PORT + attempt`, up to 20) before
binding. `scripts/generate.py` and `qa.py` both do this.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `Playwright does not support chromium on ubuntu26.04-x64` | Use Pyppeteer (downloads its own Chromium) |
| 404 for image assets | Copy them into `images/` before render |
| Tailwind not applying | Tailwind CDN needs network — use `networkidle0` wait |
| Blank PDF pages | Ensure `printBackground=True` and the `@page` size matches the canvas |
| "Looks like a default font" | Force-load every font weight, then `document.fonts.ready` |
| `Address already in use` | Port-loop until a free one binds |
| PDF text "missing" | Verify against the DOM (`qa.py --dump-text`), not pypdf |
| **Tailwind utilities not applying (everything collapses)** | Likely a too-old Chromium. `pip install 'pyppeteer>=2.0.0'` — pyppeteer 1.x bundles an old Chromium that throws `SyntaxError: Unexpected token .` parsing `@tailwindcss/browser@4`, leaving every utility unstyled. Slide-engine hit this with 1.0.2; 2.0.0 (Chromium ~136) fixed it |
| **Trailing blank page in a deck** | Default `body` margin (8px) pushes the last slide's bottom edge past the page boundary, spilling a phantom final page. Set `body { margin: 0 }` |

## Setup

```bash
python3 -m venv venv && source venv/bin/activate
pip install 'pyppeteer>=2.0.0'   # 1.x Chromium is too old for @tailwindcss/browser@4
```

Needs internet on the *first* load for the Tailwind CDN and Google Fonts.