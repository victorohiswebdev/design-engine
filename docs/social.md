# Social — feed & story system (Phase 6)

Design Engine's **social route** is for feed posts that must win in 1.7 seconds.
Built from the 2025-26 research that fixed the Madonna series — not a shrunken
deck, a true feed system.

> A slide is read. A social graphic is *scanned*. Different canvas, different rules.

## Canvases

| File | Canvas | Render | Use |
|------|--------|--------|-----|
| `templates/social/square.html` | **1080×1080** (1:1) | `generate.py social` | Feed — default, scales everywhere |
| `templates/social/portrait.html` | **1080×1350** (4:5) | `generate.py social-portrait` | Feed — max real estate |
| `templates/social/story.html` | **1080×1920** (9:16) | `generate.py story` | Stories / Reels cover |

Scaffolds are copy-paste: duplicate, replace copy/colors, render to PNG.

```bash
python3 scripts/generate.py social templates/social/square.html --format png
python3 scripts/generate.py social-portrait templates/social/portrait.html --format png
python3 scripts/generate.py story templates/social/story.html --format png
```

QA: `python3 scripts/qa.py templates/social/square.html` (bounds + image checks still apply).
Vision: `vision_qa.py` with `--brand` still catches muddy gradients / brand drift.

## Feed rules (the fix that un-drabbed Madonna)

Borrowed from TryMyPost / Lucky Graphics / TypographyMaster 2026 — these are
enforced in the scaffolds, not suggestions.

**1. Type at feed scale**
- Headline **64–120px** on 1080 canvas (ideal 90–110px). Subhead **20–29px**.
  Eyebrow **15–18px**, body/CTA **17–20px**. Anything under 48px headline or
  15px body disappears at 33% zoom (thumbnail test).
- Ratio **1:2.5 minimum** between body and headline. If body is 20px, headline
  must be ≥50px.
- Two fonts max: one display serif (Playfair 800/900) + one grotesque sans
  (Montserrat 600-800). No third font — we removed Caveat/Cormorant after they
  diluted hierarchy.

**2. Hierarchy is 3 levels, not 7**
- **Hook** (the one line they remember — `others miss.`) → **Credential**
  (sub in 20px) → **CTA** (single black bar + red pill). Everything else
  (ghost numbers, glows, 3 tiny pillars) was cut because it stole size.

**3. Whitespace is ~30%, not ~55%**
- Outer padding **24–32px** (not 52–72px). Hero fills the **center 60%**.
  Vertical gaps **8–12px** between hook lines, not 52px.

**4. Color is 60-30-10**
- **60% neutral** (cream `#FFFBF0`), **30% secondary** (charcoal `#141410`),
  **10% pop** (red `#C1272D` for `miss.` / Day pill / CTA). Gold `#C9A86A`
  is hairline only — on cream it fails 4.5:1, so it reads as drab beige if
  used as fill.

**5. Safe zones**
- Story/portrait: keep critical text out of **top 12%** (profile UI) and
  **bottom 20%** (reply/CTA bar). Scaffolds enforce this with top spacers and
  `mb-[220px]` footers.

## What we learned (so you don't repeat it)

| Mistake (Madonna v1-3) | Fix (Madonna huge) |
|------------------------|--------------------|
| `See what` 32px, eyebrow 9px → tiny at thumb | Eyebrow 18px, hook 190px, sub 29px |
| `px-[72px]` + `gap-52` → donut of air | `px-[24px]`, hero centered, 30% white |
| Ghost 02 + 3 pillars + glow + double border → 7 levels | Hook + sub + CTA only |
| Gold fill on cream → mud | Gold = 1px hairline, Red = 10% pop |

## When NOT to use social

Use `deck` for talks, `a4` for printable, `flyer` for group-drop one-pagers.
`social/*` is only for feed posts that compete in the scroll.

See `docs/formatting-standards.md` for the full type/color system and
`docs/output-types.md` for canvas picker.