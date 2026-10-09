# Reported results → claims record

You extract what a paper REPORTS about each circuit it presents, with a
verbatim quote for every value, so the reproduction can be compared against
it. You do not judge whether the numbers are right.

## Rules

- Use only the paper, through the query tool, run from
  `<repo root>`:
  `.venv/bin/python ingest/doc.py PDF outline | read "SECTION" | find PATTERN | captions | render "CAPTION" OUT.png`
  (a table can be read from its rendered image). No other files, no internet,
  no directory listing.
- Every claim needs `quote`: text copied EXACTLY from the paper (it is checked
  by string match against the PDF text layer; for a value read only from a
  table image, set `quote` to the table caption and `from_table_image` true).

## Output (path given in your task)

```json
{
 "process": {"value": "180 nm", "quote": "..."},
 "supply_V": {"value": 1.8, "quote": "..."},
 "tool": {"value": "Cadence Virtuoso", "quote": "..."},
 "circuits": {
  "<circuit key given in your task>": {
    "figure": "Fig. 2",
    "claims": [
      {"metric": "gain_dB", "value": 52, "quote": "...", "page": 3,
       "qualifier": "measured"},
      {"metric": "gbw_Hz", "value": 193.36e6, "quote": "...", "page": 4}
    ]
  }
 },
 "conflicts": [{"what": "...", "values": ["...", "..."], "quotes": ["...", "..."]}]
}
```

`metric` is one of gain_dB, gbw_Hz, pm_deg, power_W, slew_V_per_us, cl_F, vcm_V,
ugf_Hz, bandwidth_Hz, cmrr_dB, psrr_dB, swing_V, offset_V; values in SI base
units (Hz, W, F, V). `qualifier`: measured (a simulated or measured result),
target, max, min, typical. If the same quantity is reported with two different
values (prose vs table), include both claims and add a `conflicts` entry.

Reply with a one-line summary per circuit.
