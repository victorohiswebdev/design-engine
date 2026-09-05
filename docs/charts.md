# Dataviz — Chart & diagram kit (Phase 5)

Inline SVG/Css charts that embody `docs/formatting-standards.md` §§4–6: **Okabe-Ito CVD-safe, direct labels, zero chartjunk, data-ink**.

> If a number can be stated, state it. A 96px insight beats a decorated chart. When you need a chart, use one of these.

## Palette

**Okabe-Ito** (print- and CVD-safe) — never the brand palette for data:

| Token | Hex | Use |
|-------|-----|-----|
| blue | `#0072B2` | primary accredited series |
| orange | `#E69F00` | secondary |
| green | `#009E73` | tertiary |
| sky | `#56B4E9` | |
| vermillion | `#D55E00` | |
| purple | `#CC79A7` | |

Brand ink (`#1E2A38`) is only for **text, axes, and the header band**. Data stays Okabe-Ito.

## Components

| Snippet | File | When to use |
|---------|------|-------------|
| **Bar · horizontal ranked** | `templates/charts/bar.html` | The 80% case — any comparison of 2–6 items. Ranked, direct-labeled, one accent bar. |
| **Line · trend, minimal axis** | `templates/charts/line.html` | Trend over time — one axis, no grid, area under the accredited line is 8% ink. Dashed gray for control. |
| **Donut · part-to-whole** | `templates/charts/donut.html` | Only when ≤3 slices and the *part* begs to be seen. More than 3 → use a ranked bar. |
| **Table · as visual** | `templates/charts/table.html` | When comparison *is* the point and the table must read as a chart: one header band, no vertical rules, zebra only where it helps tracking. |
| **Big-number insight** | no snippet — just a `text-[96px] font-black` card (see `deck-charts.html` S6) | When the insight fits in one number, don't build a chart. |

Demo deck: `templates/deck/deck-charts.html` (6 slides, 992KB PDF, 0 warns on `qa.py` + `vision_qa.py`).

## Copy-paste contract

```html
<div class="bg-white rounded-[2rem] shadow-soft ring-1 ring-ink/5 p-10">
  <!-- paste <svg ...> or table grid here -->
</div>
```

- Keep `role="img"` + `aria-label` on every `<svg>`.
- Fill bar `width` as `value / max * 420` (the card's track is 420px in `viewBox="0 0 1000 360"`).
- Replace `points="..."` on the polyline and the matching `path` area.
- For donuts: progress `stroke-dasharray="333 490"` is 68% — recompute as `percent/100 * 490`.

## Rules that matter

- **Direct-label every datum** — no legend that forces color lookup.
- **No pie** except 2-slice. No 3D, no gradient fills, no gridlines.
- **Gold `#D4AF37` is never a data color** (2.3:1 on white — fails WCAG).
- **Error bars / CI belong in the appendix**, noted in the footnote — never squeezed onto the slide if it hurts legibility.
- **One accent datum per slide** — the accredited best is `fill="#0072B2"` + `font-black`.

## Verifying

```bash
python3 scripts/qa.py templates/deck/deck-charts.html              # 0 warns
python3 scripts/vision_qa.py templates/deck/deck-charts.html --brand neutral  # vision clean
```
