# Inspecting a rendered artifact precisely

Step 3 of the pipeline splits into critique and measurement. This file is the
measurement half: how to get a number you can act on, and which questions a
vision model must not be asked.

## Critique versus measurement

| Question | Tool |
|---|---|
| "Does this composition read?" | `vision_analyze` |
| "Is this element too large?" | measure it |
| "Where is the dead space?" | `vision_analyze` |
| "Is this element 4px off?" | measure it |

Vision is confident about magnitude and unreliable about it. Asked to judge
element sizes on a replica whose measured deltas were 0-4px on every edge, it
reported the headline mis-sized, the slab too large, the mark too small and the
buttons too big — all four wrong. It also returned pixel coordinates expressed
in the upscaled crop it was shown, which silently rescales every number by the
crop factor.

The failure is worse than a wrong number: a critique that *sounds* specific
("the letters are roughly half the visual height they should be") invites a
rewrite that makes a correct layout wrong. When a critique and a measurement
disagree, the measurement wins.

## Reading a region as text

When a colour threshold cannot separate overlapping elements — a white icon on
a coloured slab on a cream background — stop tuning thresholds and print the
region as classified characters:

```bash
python3 scripts/ascii_probe.py render.png --box 350,1066,445,1140 --step 2
```

```
legend: . black   Y saturated colour   W near-white   # dark type   - mid-tone
 1066 ----------WWWWWWWWWWWW---------
 1070 ---------WWWWWWWWWWWWW---------
 1074 -------WWWWWWWWWWWWWWWW--------
```

An element's exact position, size and internal shading become readable from
text. Two rounds of threshold tuning on an overlapping icon produced nothing;
one character map produced the exact extent immediately.

The same trick answers shape questions that vision gets wrong ("is this letter
upright or rotated?"): read the glyph directly rather than asking for an
impression of it.

## Faint overlays: residual profiles

A ~13% opacity watermark over a photograph is invisible to any absolute
threshold — the photo's own tones vary far more than the overlay does. Subtract
a slow-moving baseline and it appears as systematic positive deviation:

    residual(p) = brightness(p) - mean(brightness over p +/- K)

```bash
python3 scripts/ascii_probe.py render.png --box 640,140,1080,1010 --mode row --thresh 2.5
```

The bands it prints are the overlay's letter positions.

**Know what it does not measure.** With a window K comparable to the element's
own size, the element sits inside its own baseline, so only edge transitions
survive and band heights under-report size badly. The *pitch* between bands is
trustworthy; the *size* is not. Read spacing from the profile and get size
somewhere else.

## Measuring one element inside a busy render

A whole-canvas background/ink classification works only on a flat canvas. Over a
photograph there is no background — a cream veil and a cream garment both count
as light ink — so the content bbox becomes the entire canvas, every row has ink,
and all bands collapse into one. **Symptom: `content x 0.0-99.9%` with a single
enormous run.** Do not loosen thresholds when that appears; the model does not
apply.

Mask one element by its own colour and compare that mask's bbox between the two
images, restricted to the y-band the element occupies:

| Mask | Test | Catches |
|---|---|---|
| brand colour | saturated: `g>110 and g-r>45 and g-b>45` | coloured type, filled slabs, icons |
| dark | `sum(rgb) < 120` | black type, black buttons |
| near-white | `all(c > 228)` | a white pill, a white icon on a coloured slab |
| mid-tone | matches none of the above | the veil / photograph itself |

Deltas of 0-4px per edge are achievable and are the target.

**A mask can catch two elements at once.** A saturated-colour mask over a row
containing both a coloured slab and a coloured icon returns one bbox spanning
both, which reads as a ~50px error that is not real. Restrict the band, or print
the mask's column groups and confirm you have a single element before reading
the bbox.
