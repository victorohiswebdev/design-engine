# Brands

A brand identity in Design Engine is a **token system** — a named palette and a
font rule. Decks and A4 documents owned by a brand use that brand's tokens, not
the engine's generic defaults.

> **Never assume a brand.** When the copy doesn't make the ownership obvious,
> ask which brand an asset belongs to before choosing colors or type. The most
> common cleanups are off-brand fonts and off-brand palettes.

## Neutral (engine default)

The `templates/` scaffolds ship neutral and minimal. They are meant to be
re-ski-ned with a brand token set before shipping.

| Token | Value | Usage |
|-------|-------|-------|
| Ink / text | `#1E2A38` | Primary text |
| Panel | `#F5F7FA` | Neutral card background |
| Display font | Montserrat 700–900 | Headings |
| Body font | Open Sans 300–700 | Body |

## LiveFree — `#0b1120 / #F97316 / #0a6b8a / #00e5ff`

The LiveFree identity (source: the project's DESIGN.md). **Font: Montserrat for
body AND headings — never Open Sans.** Open Sans body reads as generic/default
in LiveFree material.

| Token | Value | Usage |
|-------|-------|-------|
| `--color-navy` | `#0b1120` | Dark slides, primary text |
| `--color-orange` | `#F97316` | Primary accent, CTAs, top bars |
| `--color-orange-deep` | `#ea580c` | Gradient end, hover state |
| `--color-teal` | `#0a6b8a` | Secondary accent |
| `--color-cyan` | `#00e5ff` | Eyebrows on dark, sparse highlights |
| `--color-panel` | `#f8fafc` | Light card background |
| Font | **Montserrat (all weights)** | Body AND headings |

Proven pattern: dark navy covers/dividers with dot-grid `radial-gradient`
(white dots at 0.07–0.08 opacity, 44–56px grid), orange gradient top bars,
`glow-orange` box-shadow on key cards, teal bottom bars. Section rhythm
dark → light → dark → light → dark.

## FYP — `#1E2A38 / #2E8B57 / #D4AF37`

The Final Year Project identity (navy/green/gold). Note: this is the FYP system,
not a universal brand.

| Token | Value | Usage |
|-------|-------|-------|
| `--color-navy` | `#1E2A38` | Primary text |
| `--color-green` | `#2E8B57` | Accents, banners |
| `--color-green-light` | `#DFF5E7` | Card backgrounds, callouts |
| `--color-panel` | `#F5F7FA` | Neutral card background |
| `--color-gold` | `#D4AF37` | Premium accents (sparingly, decorative only) |
| Font | Montserrat (headings) | Open Sans (body) |

## Concatenating a brand token set

Wires a token system into a scaffold so both light and dark slides resolve:

```css
:root {
  --color-orange: #F97316;
  --color-teal: #0a6b8a;
  --color-cyan: #00e5ff;
  --color-navy: #0b1120;
  --color-panel: #f8fafc;
}
```

Then Tailwind classes reference the tokens (e.g. `bg-navy`, `text-orange`) per the
template's `theme` extension.