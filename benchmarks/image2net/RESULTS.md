# Image2Net benchmark: Claude Opus 5 as the reader (zero-shot)

Benchmark: `ci2n_datasets/validation` (github.com/LAD021/ci2n_datasets). The repo
now holds **122** image/netlist pairs; the paper reports on **104**. Which 104 is
not recorded, so everything here is on all 122.

Reader: Claude Code subagents (Opus 5), one image at a time, with `PROMPT.md`,
image zoom/grid tools and a schema check. No access to the answer key.
Scorer: `score.py`, a dgl-free port of the benchmark's own graph construction and
GED code (checked: golden vs itself 122/122 exact; any single moved port caught).

## Headline

| run | exact (GED 0) | mean NED |
|---|---|---|
| Image2Net (paper, 104 pairs) | 80.77% | 0.116 |
| Opus 5, run 1 (`PROMPT_v1.md`) | 90/122 = 73.8% | 0.029 |
| Opus 5, run 2 (`PROMPT.md`, PMOS/NMOS arrow rule corrected) | 91/122 = 74.6% | 0.026 |

By size (run 2): ≤10 devices 37/43, 11–20 devices 43/63, >20 devices 11/16.

**NED caveat.** The paper runs the GED search for 2 h per circuit. Their search
cut short returns a loose path: with only 30 s, run 2's NED would read 0.213.
Our NED takes the minimum with a mapping-based upper bound (still a true upper
bound; `test_bounds.py` checks it against exact GED), so 0.026 can only be
above the true value, never below.

## Consistency

Runs 1 and 2 agree with each other on 120/122 circuits; 30 of run 2's 31
misses are the same mistake made in run 1. The errors are systematic, so
self-consistency is useless as a failure detector here.

## What the 31 misses are (run 2)

Error types (`diff.py`): no device is ever missed; misses are wiring, above
all gate connections, plus a few device types and body pins.

Blind adjudication (`blind.py`): each miss shown to a judge as readings A/B in
random order with neutral net names; the judge decides from the image.
Unblinded with `results/blind_key.json`, spot-checked by hand (036, 037, 108).

| cause | circuits | who the image supports |
|---|---|---|
| Same-label nets: model joins terminals carrying the same label (V_B1, VSS, CK…); the answer key keeps them separate | 21 | convention (see below) |
| Dashed test/optional elements included (V'fb loop break, VDD/2 battery, C_L) | 3 | either |
| Answer key misreads the drawing (gate bus drawn through a symbol read as body; a "4.2 µA" source typed as a voltage source) | 3 | model |
| Figure drawn wrong (PMOS arrow on an NMOS position, mirror wired to body side); model followed the evident intent, key follows the literal symbol | 4 | answer key |

The label rule is documented: Image2Net deletes text as noise and connects only
what drawn wires connect ("all ports that intersect the same connected domain in
wire graph"). `PROMPT.md` told the model the opposite (same label = same net,
which is standard schematic practice and what a simulator needs). So the
official score penalises the electrically correct reading of 21 circuits.

Caveat: the judges are the same model as the reader. Blinding removes
favouritism, not shared blind spots.

## Files

- `pred/opus5_agent/`, `pred/opus5_agent_v2/`: predictions + per-image notes
- `results/*.json`: per-circuit scores; `judge*.json`: verdicts; `blind_key.json`
- `score.py`, `test_score.py`, `test_bounds.py`, `diff.py`, `explain.py`, `agree.py`, `blind.py`, `tools.py`
