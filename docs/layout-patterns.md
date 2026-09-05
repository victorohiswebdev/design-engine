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