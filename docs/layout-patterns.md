# Layout Patterns

Reusable recipes the generated HTML is built on. Every pattern assumes the
largest hierarchy layer (title) at top, per `formatting-standards.md`.

## 55/45 split

- Text left (55%), visuals/charts right (45%).
- CSS: `.w-[55%]` + `.w-[45%]`.
- Use: explaining something with a supporting visual.

## Two side-by-side cards

- CSS: `.flex-1 .rounded-[2.5rem]`.
- Use: comparison, aim + objectives, wrong-vs-right.

## 3-column flow

- Cards joined by `→` arrows in a horizontal row.
- Use: system architecture, pipeline, process steps.

## 5-card grid

- CSS: `.grid-cols-5 .gap-7`.
- Use: impact metrics, five quick takes.

## 3×2 icon grid

- CSS: `.grid-cols-2 .gap-7`.
- Use: feature showcase, closing argument.

## Large hero image

- CSS: `.max-h-[620px]` with `object-contain`.
- Use: prototype photos, results, full-bleed emotional shots.

> **object-contain, never object-cover**, for dashboard/screenshots with an
> explicit height. `object-cover` crops edges and hides information.
> Add `bg-white p-4` padding.

## Metric cards

- CSS: `.rounded-[2rem]` with a colored icon circle.
- Use: performance numbers you want to land fast.

## Card grids (3/4 col)

- CSS: `.grid-cols-3 .gap-8` or `.grid-cols-4 .gap-8`.
- Use: feature cards, impact metrics, pricing tables.

## Full-bleed image

- An `<img>` at `absolute inset-0` with an overlay gradient for legibility.
- Use: emotional/wow slides, hero shots.

## Bullet list

- One icon + text per bullet, stacked vertically.
- Use: key points, agenda items.

## Slide counter & section label

Every slide carries a slide counter top-right (`XX / YY`) and a section label:
green dot + uppercased tracked eyebrow above the title.

```html
<span class="w-3 h-3 rounded-full bg-green"></span>
<span class="text-2xl font-bold text-green uppercase tracking-[0.22em] font-title">Section</span>
```

## Corner radius system

- Cards: `rounded-[2rem]` / `rounded-[2.5rem]`
- Inner panels: `rounded-2xl` / `rounded-3xl`
- Buttons / badges: `rounded-xl`
- Pill badges: `rounded-full`

## Color-correctness

These rules carry across every pattern:
- **No Unicode symbol glyphs** (`❌`, `✓`, `✕`, `✔`) — the brand font lacks
  them and Chromium falls back to DejaVuSans, which mismatches the type.
  Draw indicators with CSS (colored border, circle, `::before` check shape) or
  use Montserrat-covered punctuation (×, +, →).
- Dark slides: never set `background-color` on the bare `section` selector
  (an unlayered `section { background:#fff }` would override `bg-navy` — see
  `pdf-pipeline.md`). Light slides inherit `body { background:#fff }`.

## 2026 depth & variety patterns (Phase 3)

Adds variety and depth without breaking the formatting rules. The complete
showcase is `templates/deck/deck-layouts.html` — all six slides pass the QA
gate at 0 fails / 0 warns (verified).

**Bento grid** — modular cells of mixed sizes read as one system. One large
hero cell (a metric) with supporting cells. CSS:
`grid grid-cols-4 grid-rows-2 gap-6`, hero = `col-span-2 row-span-2`, rounded
`[2rem]`. Use an accent-filled hero + panel/white cells + one teal cell, all
with `shadow-soft`.

**Editorial / asymmetric** — one dominant headline column (≤58% width) + a
quiet second zone (metric or panel) on the far side, wide margins, a thin
accent rule. Reads as print/magazine, not a report form.

**Anchor / divider (dark)** — a navy pacing slide that stops the room between
sections: full-screen dark, dot-grid `radial-gradient` at ~7% white opacity,
centered statement, a `NN` number between two rules, cyan eyebrow, white text.
Set the dark background on an inner element or inline style, NEVER on the bare
`section` selector (cascade-layers pitfall).

**Single-number pacing** — one massive numeral as the hero (180–240px), a small
label, one context line, generous white space. Isolation = impact.

**Pull quote** — a vertical accent bar on the left, a large opening quote glyph,
a big quote line, and an attribution with a horizontal rule.

**Depth utilities (PDF-safe)** — subtle, layered soft shadows only:
```css
.shadow-soft { box-shadow: 0 1px 2px rgba(11,17,32,.06), 0 8px 24px rgba(11,17,32,.08); }
.shadow-lift { box-shadow: 0 2px 4px rgba(11,17,32,.06), 0 14px 34px rgba(11,17,32,.13); }
```
Depth-without-clutter rules: soft shadows and two-tone panels only; no heavy
gradients; `backdrop-filter` glass drops in the PDF (see image-system); one
primary depth treatment per deck. Big display numerals use generous leading
(`leading-[1.2]`–`[1.3]`) so the QA clip check stays clean.