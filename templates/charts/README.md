# Charts — snippet library

Copy the `<svg>` (or the div grid for tables) from one file, paste into a slide's white card, replace the numbers. No JS. Every snippet is Okabe-Ito, direct-labeled, and `qa.py` + `vision_qa.py` clean.

- `bar.html` — horizontal ranked bar (the 80% case)
- `line.html` — trend with area, minimal axis
- `donut.html` — part-to-whole ≤3 slices only (more → use bar)
- `table.html` — table-as-visual

Demo deck: `templates/deck/deck-charts.html` (6 slides, all pass at 0 warns).
See `docs/charts.md` for the data-ink rules.
