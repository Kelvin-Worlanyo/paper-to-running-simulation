# Paper to Running Simulation — artifacts

Code, prompts and recorded runs for:

> K. Tamakloe, G. Bonsu, I. Sabiku and D. Chen, "Paper to Running Simulation:
> LLM Agents That Set Up Published Analog Circuits in Open and Foundry Flows,"
> submitted to *Microelectronics* (MDPI), 2026.

The pipeline takes a published paper as a PDF and produces a circuit that runs
in the reader's own process, a standard testbench, and a statement of how close
the result comes to what the paper reports. Four role-specialised LLM agents do
the reading, claim extraction, sizing-code generation and benchmark
adjudication; everything between them is deterministic code, and every agent
output is checked by something the model did not produce.

## Layout

    ingest/                 PDF parsing: layout, sections, captions, verified
                            figure crops, cell-wise OCR of image-only tables
      digitize_plot.py      curve and axis recovery from a printed plot
      check_figures.py      the papers' own figures checked against their
                            tables, their text and our simulations
    pipeline/               checks, bench, bias search, comparison, ladder
      PROMPT_circuit.md     the reading agent's prompt
      PROMPT_claims.md      the claims agent's prompt
      erc.py                static checks
      sim.py                bench, operating point, bias re-derivation
      compare.py            claim verification and the reproduction ladder
      sizing.py             published sizing loop
      sizing_local.py       local loop, with the outgoing-prompt screen
      step_response.py      closed-loop step response: overshoot, ringing,
                            settling, tracking (process-independent)
      run_step.py           rebuilds a recorded run and steps it in closed loop
      feasibility.py        one-sided bound on a published specification from
                            its own reported numbers
      exp_quote_control.py  negative control for the claim check: corrupted
                            quotes that it must reject
      cadence/              foundry-PDK back end (device map, model setup,
                            placement, simulation), configured by role
    design/                 the validated ngspice runner and the AC and
                            transient testbench templates the bench is built on
    cases/                  the three case-study papers' recorded runs
      <paper>/records/      circuit records written by the reading agent
      <paper>/reported*.json  claims with quotes and their verification
      <paper>/out/          Sky130 results
      <paper>/out_pdk/      commercial 180 nm PDK results
      <paper>/out*/step_*   closed-loop step responses of every run that
                            operates
      opamp3/sizing_*/      re-sizing runs: prompts, generated sizing code,
                            per-round calibration, trajectories, final results,
                            prompt-screen logs
      figure_checks_all.json  the figure check: each published claim against
                            the paper's own figure, table and text
      opamp3/figure_trace_fig7.json  our trace of one published curve
      quote_control.json    the claim check run against corrupted claims
      analoggym/            the controlled reading experiment's records and
                            scores
      pdk_placer/           what the placer drew from each record, and the
                            design environment's own check of it
    benchmarks/image2net/   scoring code, predictions, blind adjudication
                            packets, judges' verdicts, the terminal- and
                            net-level audit and the answer key
    benchmarks/analoggym/   our bench against AnalogGym's own testbench
    paper/                  the generators that turn the runs above into every
                            number, table and figure in the manuscript

Case-study papers: `opamp3` = paper A, `affc` = paper B, `subvt` = paper C.

## Reproducing

The open-PDK path is fully reproducible with ngspice and the SkyWater Sky130
models. Point the pipeline at a circuit record and run the case driver; the
checks, bench and bias search need no credentials.

The foundry path needs your own PDK, your own Cadence installation and a
configuration file naming four things *by role* — a reference schematic that
uses the PDK's transistors, a testbench that already simulates with it, an
empty library on the PDK technology, and a private directory. See
`pipeline/cadence/pdk_config.example.json`. Nothing about any particular PDK is
contained here.

## What is not included, and why

* **No process design kit content.** The 180 nm results were produced with a
  commercial PDK under licence. No model files, model names, device parameters,
  operating points, library or cell names, or paths appear anywhere in this
  repository, and the foundry is not named. PDK results appear only as
  circuit-level metrics, which is what the paper reports.
* **No PDFs or figure crops of the case-study papers.** They are the copyright
  of their publishers. The derived circuit records, the short verbatim quotes
  used to verify claims, and our own trace of one published curve are
  included; none of the published artwork is reproduced.
* **No Image2Net or AnalogGym datasets.** Both are public; fetch them from
  their own repositories. The predictions, scores and adjudication records of
  our runs are here.

## Notes for readers of the paper

* Every number, table and figure in the manuscript is generated from the files
  in `cases/`, `benchmarks/` and `design/`; none is typed by hand. Run
  `paper/gen_numbers.py` for the numbers and tables and `paper/make_figs.py`,
  `paper/mk_results_panels.py`, `paper/mk_figcheck.py`,
  `paper/mk_overview_panels.py` and `paper/mk_record_fig.py` for the figures.
  They need the two public datasets fetched first -- Image2Net's validation
  directory on `PYTHONPATH` and AnalogGym's amplifier models at
  `AnalogGym/AnalogGym/Amplifier` -- and nothing else; no PDK and none of the
  case-study PDFs.
* The sizing runs are named by loop rather than by process:
  `sizing_published` (the published loop), `sizing_local` (ours),
  `sizing_local_pdk` (ours, on the commercial PDK),
  `sizing_published_power` (the published loop fitting power in place of phase
  margin) and `sizing_published_power_pmfloor` (the same, with a 45$^\circ$
  phase-margin floor as a design constraint).
* `leak_audit.json` in the local-loop runs records the outgoing-prompt screen:
  how many renderings of simulation-derived values were searched for in each
  prompt, and how many were found.

## Licence

MIT (see `LICENSE`). Note that the exclusions above are not ours to license:
the commercial PDK's content remains under its own licence and is not present
here, and the case-study papers remain the copyright of their publishers.

## Citing

See `CITATION.cff`, or cite the paper directly.
