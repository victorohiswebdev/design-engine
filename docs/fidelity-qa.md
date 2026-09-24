# Fidelity QA — the replica gate

`qa.py` proves a layout is built correctly. `vision_qa.py` proves it *looks*
correct. Neither can tell you whether you reproduced the design you were asked
to copy. That is a different question, and it has a different gate.

`scripts/fidelity_qa.py` reduces the reference and the candidate to the same
normalised signature and diffs them element by element, in percentage points of
canvas. Anything you cannot measure, you are guessing about.

## Why measure instead of eyeball

Two images of "the same" design look identical side by side while being 20%
apart on half a dozen elements. The eye is bad at this and worse on a blurred
source. The gate turns the vague instruction "match the reference" into a list
of numbers with a tolerance, so iterating becomes: measure, correct the largest
deltas, re-measure. That loop converges; nudging values until it "looks right"
does not.

## What it measures

| Element | What it is | Why it earns its place |
|---|---|---|
| **content** | Outer bbox of all non-background ink | Is the whole composition the right size and position? |
| **block** | The solid colour slab (e.g. a `NO` tile) | Position and extent of the heaviest visual mass |
| **glyph** | The knock-out glyphs *inside* that slab | Catches a block that moved with its lettering left behind |
| **bands** | Horizontal slices separated by fully empty rows | Lets a heading row be measured independently of the row beneath it |
| **runs** | Column runs *within* each band | The thing that makes individual letters measurable instead of one smear |

Both images are resampled to a 1000×1000 grid, so a 626×630 reference and a
1080×1080 render are compared in the same units.

## Usage

```bash
# Inspect one signature — how you reverse-engineer a reference
python3 scripts/fidelity_qa.py reference.png

# Gate a replica against it
python3 scripts/fidelity_qa.py reference.png my-replica.png
python3 scripts/fidelity_qa.py reference.png my-replica.png --tol 0.5
python3 scripts/fidelity_qa.py reference.png my-replica.png --json report.json --strict
```

## Exit codes & `--strict`

- **0 = PASS.** No element is further off than `--tol` (default **1.0pp**).
- **1 = FAIL.** An element exceeded the tolerance, or the structure differs (see
  below), or any warning was raised under `--strict`.
- **2 = usage / file-not-found / decode error.**

Warnings do not fail a relaxed run, matching `qa.py`.

## Fails vs warnings — the important distinction

**A band-count mismatch is a failure.** Bands merge when two elements sit closer
than about 3 normalised pixels apart, so a different band count means two
elements are touching, or an outline has grown into its neighbour. Both are real
defects, and the message names the band positions in each image.

**A run-count mismatch is a warning.** Fine detail in a low-resolution reference
blurs together and legitimately segments into fewer runs than a crisp render of
the same design — a 626×630 source splits one label into 4 runs where a 1080px
render splits it into 6. When run counts disagree the runs are *not* compared
pairwise (that reports a meaningless 20pp+ delta between two different letters);
the band's overall ink envelope is compared instead.

## What this gate cannot do

- **Recover information a low-resolution source destroyed.** Stroke weights and
  letterform detail below the source's resolution are not measurable, only
  guessable. Supply the largest source you have.
- **Read your mind about fonts.** It compares geometry, not letterforms. If you
  substituted a face, the gate will confirm your substitute is the right *size
  and position* — not that it is the right *font*.
- **Judge whether the design is any good.** It compares against the reference;
  it has no opinion about the reference.
- It disables itself usefully: with no candidate it just prints the signature.

## Verified behaviour

- Identical images → `0.0pp` worst delta, 0 fails, 0 warns, exit 0.
- A fixture with an extra band → exit 1, band count named with both images'
  band starts.
- A 20px (2.0pp) vertical shift → exit 1 at `--tol 1.0`, exit 0 at `--tol 3.0`.
- An unrelated design → exit 1 with content-bbox deltas of ~20pp.
- A missing file → exit 2.
