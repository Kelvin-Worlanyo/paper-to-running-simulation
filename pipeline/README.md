# Paper → verified simulation pipeline

Blocks (see `paper_repro/main.pdf`, Fig. 1):

| Block | Code | Who |
|---|---|---|
| A. Ingest, verified figure crops | `ingest/pagemap.py`, `ingest/crop.py`, `ingest/doc.py` | deterministic |
| B+C. Schematic → circuit record | `PROMPT_circuit.md` (agent), `validate.py`, `circuit.py` | Claude Code sub-agent |
| Claims with quotes | `PROMPT_claims.md` (agent), `compare.verify_quotes` | agent + deterministic |
| D. Static checks | `erc.py` | deterministic |
| D/E. Operating point, polarity, regions, bias search, AC bench | `sim.py`, `tospice.py` | ngspice + Sky130 |
| F. Compare, ladder | `compare.py` | deterministic |
| Driver | `run_case.py CASE_DIR` | |

## Reproducing the paper's numbers

```
# Image2Net (vision_eval/image2net): predictions are in pred/, prompts PROMPT_v1.md, PROMPT.md, PROMPT_wires.md
.venv/bin/python vision_eval/image2net/score.py vision_eval/image2net/pred/opus5_agent_wires --out vision_eval/image2net/results/opus5_agent_wires.json
.venv/bin/python vision_eval/image2net/test_score.py      # scorer sanity
.venv/bin/python vision_eval/image2net/test_bounds.py     # GED bounds bracket exact GED
# blind adjudication: blind.py (packets), results/judge*.json (verdicts), results/blind_key*.json (keys)

# AnalogGym: records in cases/analoggym/records (agent-written)
.venv/bin/python pipeline/exp_truth_validation.py
.venv/bin/python pipeline/exp_analoggym.py

# Case study: cases/opamp3/{paper.pdf, crops/, records/, reported.json}
.venv/bin/python pipeline/run_case.py cases/opamp3

# Paper
cd paper_repro && ../.venv/bin/python make_figs.py && ../.venv/bin/python gen_numbers.py && tectonic -X compile main.tex
```

## Rules the agents ran under

Agents were told to open only their assigned images/crops, the prompt, the
paper through `ingest/doc.py`, and their own outputs. Answer netlists
(`vision_eval/image2net/ci2n_datasets/validation/golden`, `AnalogGym/`) and
earlier hand transcriptions (`design/`) were off limits. Agents reported the
few directory listings they made (their own output folders, image-folder
names).
