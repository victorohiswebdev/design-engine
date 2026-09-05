# Formatting Standards (2026 system)

This is the rulebook every asset follows. It is the research-backed formatting
system that replaced the "decorate and hope it looks right" approach: **action
titles, strict hierarchy ratios, modular type tokens, WCAG color rules,
CVD-safe charts, and the data-ink principle.**

> Read this before building anything. These rules are the engine's value.

## 1. Titles are full-sentence conclusions

Titles state the takeaway, never the topic.

- **Good:** "Predictive irrigation cut water use 32%"
- **Bad:** "Results" / "Methodology" / "Water Usage"

Rules:
- ≤ 15 words.
- A complete sentence a reader can understand in isolation.
- Reserve topic labels for the small eyebrow/segment marker above the title.

## 2. Four-layer hierarchy

Every slide expresses exactly four layers, in descending priority. Adjacent
layers must differ in size by **≥ 1.5:1** so the eye lands on the right layer instantly.

| Layer | Example | Size |
|-------|---------|------|
| **Title** | The headline conclusion | largest (50–66px) |
| **Supporting** | The argument under the title | large (32–42px) |
| **Detail** | The specifics, bullets | ≥ 24px body |
| **Counter / sources** | Footer notes, citations | micro (16px), muted |

The last layer is small and **muted** on purpose: it is context, not content. If a
layer runs long, **cut content — never shrink the font** below its floor.

## 3. Body text floor and type tokens

- Body text **≥ 24px**. If it doesn't fit at 24px, the slide has too much content.
- Modular type tokens (adjust per output type, keep the ratios):

| Token | Slide (1920×1080) | A4 / flyer |
|-------|-------------------|------------|
| Display | 76–150px | per canvas |
| H1 | 50–66px | 22–28pt |
| H2 | 32–36px | 16–18pt |
| Body bullet | 30px | 12pt |
| Caption | 20–24px | 9–10pt |
| Counter / source | 16px, muted | 8pt |

## 4. WCAG-compliant color

- **#D4AF37 (gold) is decorative only.** It fails the contrast ratio (≈2.3:1)
  on white. Never set body text in gold.
- **#2E8B57 (green) only ≥ 36px or in graphics.** Below that it fails contrast
  on white. Body text should be navy/ink.
- Muted text opacities floor at **~65–75%**. `navy/40–45` and `white/40–50`
  read washed out on projection — Victor flags them as missing contrast.
- When in doubt, check the actual contrast ratio of any text/background pair
  against WCAG AA (4.5:1) before shipping.

## 5. CVD-safe charts

Color-vision-deficiency-safe by default, using the Okabe-Ito palette, not
rainbow defaults:

- **Okabe-Ito** (accessible, distinguishable): `#0072B2`, `#E69F00`, `#009E73`,
  `#56B4E9`, `#D55E00`, `#CC79A7`, `#F0E442`, `#000000`.
- **Direct labels** on data (no reliance on a legend that forces color lookup).
- **Zero chartjunk:** no 3D, no superfluous gridlines, no gradient fills that
  obscure data. Ink = data.

## 6. Data-ink principle

The graphic should communicate the data with the minimum ink required. Remove
anything that doesn't carry information: drop shadows, decorative borders,
fake depth, redundant axes. When a number can be stated, state it — a clean
metric card beats a decorated chart.

## 7. Depth without clutter

Depth supports the message, never competes with it. Prefer **subtle layered
soft shadows**, two-tone panels, and one deliberate oversized element (a hero
metric, a single number, a pull quote) for variety. Avoid heavy gradients,
drop-shadow spam, and effects that don't carry information. **`backdrop-filter`
glass is not PDF-safe** (dropped in the print path — see image-system); if you
want the frosted look, use a translucent panel with a border and shadow. Apply
one primary depth treatment per deck and keep it consistent, exactly like the
image-treatment consistency rule. Deep displays need generous leading
(`leading-[1.2]`–`[1.3]` on 180–240px numerals) to render cleanly.

## 8. LiveFree palette & brand fonts

See **`docs/brands.md`** for the token systems. The headline rule that matters
most: **brand decks use that brand's font for body AND headings.** A "default"
body font (e.g. Open Sans in a LiveFree deck) reads as off-brand and gets
flagged immediately. Check the target brand's DESIGN.md before choosing type.

## Pre-export checklist

Running `scripts/qa.py <your.html>` is required before shipping any asset.
It verifies:
1. **Overflow** — no element's bounding box escapes its slide/container.
2. **Clip** — no text box clips its glyphs (with the display-type false-positive
   caveat handled by the bounds check, not naive scrollHeight).

See `docs/qa.md` for the methodology and what each result means.