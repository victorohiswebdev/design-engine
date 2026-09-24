# Canvas sizes, margins, and what survives downscaling

## Master at 2x DPR

Always render at 2x the logical canvas. Platforms downsample anyway, and the 2x file is the archive copy. A 1080x1080 logical post renders to 2160x2160; verify with the real pixel count rather than asserting it.

## Common canvases

| Placement | Logical size | Ratio | Notes |
|---|---|---|---|
| Feed square | 1080x1080 | 1:1 | Safest cross-platform; works everywhere |
| Feed portrait | 1080x1350 | 4:5 | Maximum feed real estate; needs its own layout tuning |
| Story / reel cover | 1080x1920 | 9:16 | Platform UI eats top and bottom |
| Wide / video thumbnail | 1920x1080 | 16:9 | Also fine for LinkedIn and X |
| Link / OG card | 1200x630 | 1.91:1 | What renders in a chat or social preview |
| Print | A4 via `page.pdf` | - | Vector text, embedded fonts, zero margins |

## Safe margins

- Feed formats: roughly 74-80px on a 1080 canvas (about 7%). Keep every element inside the same side margins so the eye finds one column.
- Story format: hold roughly 250px clear at top and bottom; the platform chrome covers that band.
- Bottom breathing room slightly larger than the gap above the footer is fine and normal. Deliberate asymmetry reads as intentional; a *slack* gap mid-composition reads as unfinished.

## Contrast floor on dark canvases

Secondary text, mono micro-labels, and captions on a near-black canvas need roughly `#ADA7A0` or lighter. A muted `#847E78` is the tempting, elegant-looking choice and it disappears as soon as the image is scaled into a feed. Treat the contrast floor as a gate, not a taste call: lift the value, then confirm at thumbnail size.

## What survives thumbnail scale

Checked at roughly 270px wide, simulating a real feed. Still legible:

- Headline-scale display type.
- Large numerals (a metric figure can read while its label does not).
- High-contrast accent color blocks and marks.
- The silhouette of a CTA button.

Effectively gone: brand lockups, eyebrows, browser-chrome details, metric labels, footer text, chart labels, buttons' own text, and all fine grid or texture work.

The design rule this implies: **one idea per post at headline scale**, with micro-detail as a reward for tapping through rather than as the message. If the post's meaning depends on text that vanishes at 270px, the composition is wrong, not just the font size.

## Placeholder content

Any figure invented purely to make the composition balance (a load time, a multiplier, a percentage) is a placeholder. Say so in the handoff and offer the real numbers, or reframe the figure as a generic benchmark. Composed-but-fabricated metrics presented as the user's results is the one failure mode that turns a good artifact into real damage.

## Print settings

`render-pdf.js` sets `printBackground: true` (full-bleed dark art depends on it) and zero margins (the art owns its own margins). Text stays vector and webfonts are subset-embedded. Confirm what actually embedded by inspecting the PDF rather than assuming.
