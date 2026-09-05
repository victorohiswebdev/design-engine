# Examples

Curated sample renders live here to demonstrate the engine's four output types.
Rendered artifacts are gitignored (regenerable from source) — only this explainer
is tracked.

To regenerate any sample, render the matching template:

```bash
source venv/bin/activate

# Deck (1920×1080 slides → PDF)
python3 scripts/generate.py deck templates/deck/deck.html --out examples/deck.pdf

# A4 document (210×297mm → PDF)
python3 scripts/generate.py a4 templates/a4/proposal.html --out examples/proposal.pdf

# Portrait flyer (1080×1350 → PNG)
python3 scripts/generate.py flyer templates/flyer/flyer-portrait.html --format png --out examples/flyer.png

# Brand carousel (1080×1080 → PNG)
python3 scripts/generate.py carousel templates/carousel/carousel.html --format png --out examples/carousel.png
```

Every sample passes the QA gate before it ships:

```bash
python3 scripts/qa.py templates/deck/deck.html
# → RESULT: PASS
```

> **No client data here.** These are neutral scaffold renders. Keep business
> proposals, certificates with real names, and any branded/private deliverables
> out of this public repo — version them in your own working directory instead.