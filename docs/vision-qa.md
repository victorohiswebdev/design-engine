# Vision QA — perceptual gate (Phase 4)

The layer geometry cannot catch. A slide can pass every `qa.py` check and still look cheap — a muddy beige gradient where a crisp panel should be, a random purple that is not the brand purple, white text 1.8:1 on a pale photo, a hero image that is visibly soft. Those are the failures an audience *feels* in the room, and they are invisible to `boundingRect` math. Vision QA closes that gap.

> `qa.py` proves the slide is built correctly. `vision_qa.py` proves it *looks* correct.

## What it checks (heuristics — no API key needed)

All heuristics run on the rendered PNG via Pillow + NumPy. No API, no cost, deterministic.

| Check | Level | What it means |
|-------|-------|---------------|
| `BRAND_DRIFT` | warn | Dominant saturated color is >120 distance from the declared palette — a one-off teal that is not the brand teal. Photo-forward slides are automatically excluded (photos are hue-diverse by nature). |
| `LOW_CONTRAST` | warn | Luminance range <95 and σ <28 — the whole slide sits in a narrow flat band, washed out. |
| `MUDDY_GRADIENT` | warn | >38% of pixels are desaturated midtone (S <0.12, V 0.32–0.88) and the slide is not a photo — a beige/gray wash that reads as stock gradient mud. |
| `CROWDING` | warn | <3% near-white whitespace on a non-photo, non-dark slide — no air, gutters collapsed. |
| `SPARSE` | warn | >88% near-white with σ <22 and not a photo — reads blank / forgotten slide. |
| `BLUR` | warn | Laplacian variance <18 on a 480×270 downsample — hero image is soft / low-res. |

Heuristics are **warn-only** by design — they flag taste, not function. With `--strict` they become failures.

Photo slides are excluded from palette / whitespace / muddy checks because a full-bleed photo naturally dominates color and whitespace. Detection is hue-diversity (`unique hues >60 and mean saturation >40`), validated against the three deck templates.

## Optional vision LLM — second pair of eyes

With `--vision` and an API key, each slide is also sent to a vision LLM for a second pass against the 2026 formatting standards:

- Action-title discipline (full sentence ≤15w), 4-layer hierarchy ≥1.5:1, body ≥24px
- WCAG contrast, brand coherence, depth-without-clutter, image-treatment consistency

Provider-agnostic — auto-detects from env, or pin with `--vision-provider`:

```bash
export GEMINI_API_KEY=...        # Google Gemini native API
python3 scripts/vision_qa.py deck.html --brand livefree --vision

export ANTHROPIC_API_KEY=sk-ant-...  # Anthropic Claude
export OPENAI_API_KEY=sk-...         # OpenAI
python3 scripts/vision_qa.py deck.html --brand livefree --vision

# Explicit provider / model
python3 scripts/vision_qa.py deck.html --vision --vision-provider gemini --vision-model gemini-2.0-flash
python3 scripts/vision_qa.py deck.html --vision --vision-provider openai --vision-model gpt-4o
python3 scripts/vision_qa.py deck.html --vision --vision-provider anthropic --vision-model claude-3-5-sonnet-latest

# Any OpenAI-compatible endpoint (OpenRouter, Ollama, local vLLM, Gemini OpenAI-compat)
VISION_BASE_URL=https://openrouter.ai/api/v1 VISION_API_KEY=... \
  python3 scripts/vision_qa.py deck.html --vision --vision-model google/gemini-2.0-flash
GEMINI_API_KEY=... VISION_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai \
  python3 scripts/vision_qa.py deck.html --vision --vision-provider openai --vision-model gemini-2.0-flash
```

Env resolution: `VISION_PROVIDER` / `VISION_MODEL` / `VISION_API_KEY` / `VISION_BASE_URL` take precedence, with fallbacks `GEMINI_API_KEY` / `GOOGLE_API_KEY`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `OPENAI_BASE_URL`. Gemini tries the `google-genai` SDK first, then falls back to raw REST (no extra dependency).

If no key is present, `--vision` degrades gracefully to heuristics-only. LLM findings are always `warn` — they advise, they do not fail a build alone. Rate: one request per slide.

Prompt and JSON contract are documented at the top of `scripts/vision_qa.py` (`VISION_PROMPT`).

## Usage

```bash
source venv/bin/activate              # Pillow + numpy + pyppeteer
pip install numpy                     # if not already

# heuristics only (fast, free)
python3 scripts/vision_qa.py templates/deck/deck.html
python3 scripts/vision_qa.py templates/deck/deck.html --brand livefree
python3 scripts/vision_qa.py templates/deck/deck.html --brand "#0b1120,#F97316,#0a6b8a"

# heuristics + LLM (when key is set — any provider)
GEMINI_API_KEY=... python3 scripts/vision_qa.py templates/deck/deck.html --vision
ANTHROPIC_API_KEY=... python3 scripts/vision_qa.py deck.html --vision --vision-model claude-3-5-sonnet-latest
OPENAI_API_KEY=... python3 scripts/vision_qa.py deck.html --vision --vision-model gpt-4o-mini
VISION_BASE_URL=https://openrouter.ai/api/v1 VISION_API_KEY=... python3 scripts/vision_qa.py deck.html --vision --vision-model google/gemini-2.0-flash

# strict: warns become failures (CI gate)
python3 scripts/vision_qa.py templates/deck/deck.html --strict

# JSON report for CI or for feeding into generate
python3 scripts/vision_qa.py deck.html --brand livefree --out report.json
```

## How it renders

Same pipeline as `generate.py`: local HTTP server → headless Chromium (Pyppeteer) → `networkidle0` → `document.fonts.ready` → element screenshots of each `<section>` at native 1920×1080. No `clip` coordinate math — each section is screenshotted as an element, which is robust across the four canvas types (deck, A4, flyer, carousel).

Screenshots land in `/tmp/vision-qa-XXXX/slide-01.png` … and are kept for inspection. Pass `--out` to keep the report; the PNGs are never auto-deleted so a failing CI run can archive them.

## Brand flag

`--brand` selects the palette to compare against:

- `neutral` — `#1E2A38 / #2E8B57 / #F5F7FA` (default, scaffolds)
- `livefree` — `#0b1120 / #F97316 / #0a6b8a / #00e5ff`
- `fyp` — FYP navy/green/gold
- custom hex list — `--brand "#123456,#abcdef,#ffffff"`

When the deck mixes brand and photos, pass the brand anyway — photo slides are auto-excluded from palette checks.

## Exit codes

- `0` PASS — no fails (warnings may still be printed)
- `1` FAIL — any heuristic `fail` or (with `--strict`) any `warn`; LLM never fails alone unless strict
- `2` error — file not found, missing deps, render error

## Verified behavior (Sep 2026)

- `templates/deck/deck.html`, `deck-layouts.html`, `flyer-portrait.html`, `carousel.html` → `0 warn` on neutral (vision clean)
- `templates/deck/deck-image.html` → `0 warn` on `--brand livefree`, `1 warn` on neutral (expected — photo palette dominates)
- `templates/a4/proposal.html` → `0 warn` (vision clean, captures each A4 section)
- Synthetic off-brand purple (`#8B5CF6` on neutral) → `BRAND_DRIFT` warn
- Heuristic + LLM path tested with no key → degrades to heuristics-only with a clear message

## When to run which gate

| Goal | Command |
|------|---------|
| Fast local check while drafting | `qa.py deck.html` |
| Pre-delivery / client review | `qa.py deck.html --strict && vision_qa.py deck.html --brand <brand> --strict` |
| Full editorial audit (with a second pair of eyes) | `vision_qa.py deck.html --brand <brand> --vision --out report.json` |

For a one-command pipeline on multiple decks, see `docs/pdf-pipeline.md#batch`.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `Need Pillow + numpy` | `pip install Pillow numpy` inside the venv |
| Screenshots are white | Tailwind/browser@4 needs `networkidle0` + font ready — the script already does this; check network and that `pyppeteer>=2.0.0` |
| Too many `BRAND_DRIFT` on photo decks | Pass the correct `--brand` and ensure the slide is photo-forward; if still noisy, the palette is too narrow — pass a custom hex list |
| `[vision] no API key` | Set `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` in the env, then re-run with `--vision` |
