# Schematic figure → sized circuit record (blocks B + C)

You read ONE schematic figure and write a circuit record that a simulator can
use. Every number you write must come from the source, with evidence. Never
invent a value: if the figure does not give it, record it as absent.

## Rules of the run

- Read only what your task names: the figure image(s), the paper PDF through
  the query tool below, and this file. Do not list or search directories or
  open other files. Do not use the internet.
- Python: `.venv/bin/python`,
  run from `<repo root>`.
- Image tools: `vision_eval/image2net/tools.py grid IMG OUT.png` and
  `vision_eval/image2net/tools.py zoom IMG X0 Y0 X1 Y1 OUT.png` (fractions 0..1).
  Put crops in the scratch directory your task names.
- Paper text (when your task gives a PDF): `ingest/doc.py PDF outline`,
  `ingest/doc.py PDF read "SECTION"`, `ingest/doc.py PDF find PATTERN`,
  `ingest/doc.py PDF captions`, `ingest/doc.py PDF render "CAPTION" OUT.png`.
  Use them to find sizes or values the figure omits (tables, prose).
- Validate: `.venv/bin/python pipeline/validate.py RECORD.json` must print OK.

## Output: one JSON file (path given in your task)

```json
{
 "ckt_type": "DISO-Amplifier",
 "source": "Fig. 4",
 "pins": {"vdd": "vdd", "gnd": "gnd", "out": "vout", "in": ["vin1", "vin2"]},
 "ckt_netlist": [
  {"id": "V1", "role": "supply", "component_type": "Voltage",
   "port_connection": {"Positive": "vdd", "Negative": "gnd"},
   "value": "1.8", "evidence": {"value": "figure: 'vdc=1.8' beside V1"}},
  {"id": "NM0", "role": "core", "component_type": "NMOS",
   "port_connection": {"Drain": "A", "Gate": "vin1", "Source": "C"},
   "size": {"w": "4u", "l": "500n", "m": "1"},
   "evidence": {"w": "figure: 'w=4u' beside NM0", "l": "figure: 'l=500n'", "m": "figure: 'm:1'"}}
 ],
 "absent": [{"item": "NM1.w", "why": "printed as the symbol 'wn1'; no value in figure or text"}],
 "notes": ["crossing left of PM1 read as not connected (no dot)"]
}
```

### Devices and ports (exact names)

| component_type | ports |
|---|---|
| PMOS, NMOS | Drain, Gate, Source, and Body only when a separate bulk wire is drawn |
| NPN, PNP | Collector, Base, Emitter |
| Res, Cap, Ind | Pos, Neg |
| Diode | In (anode), Out (cathode) |
| Current | In, Out: current flows through the source from In to Out (In = arrow tail) |
| Voltage | Positive, Negative |
| Diso_amp | InP, InN, Out; Dido_amp InP, InN, OutP, OutN; Siso_amp In, Out |

### Fields

- `id`: the designator printed on the figure. If none is printed, assign
  M1, M2, ... and say so in `notes`.
- `role`, one of:
  - `core`: part of the circuit (transistors, compensation caps, bias
    current references drawn as part of the circuit)
  - `bias`: a voltage source that sets a bias node of the circuit (for
    example a source on a cascode gate)
  - `supply`: the supply source; `input`: a stimulus source on an input;
    `load`: the load capacitor/resistor on the output
- `size` (transistors): `w`, `l`, `m` as printed, in SPICE form (`4u`, `500n`,
  `1`). A width printed as a symbol (`wn1`) is NOT a value: leave `w` out and
  add an `absent` entry.
- `value` (R, C, I, V): as printed (`600f`, `20u`, `1.8`, `1.2`). A symbolic
  value (`vb2`, `VCM`) is not a value: record it in `absent`, and put the symbol
  in `evidence`.
- `evidence`: for every number, where you read it, quoted as printed.
- `pins`: the nets that are the supply, ground, output and inputs of the
  circuit (not of the harness). Two inputs for a differential amplifier, in
  the order they are labelled (e.g. vin1, vin2). Do NOT decide which input
  is inverting; the pipeline tests that.

### Reading conventions

- Terminals with the same text label (vdd, gnd, vbias, VSS …) are the same
  net, even without a drawn wire. All ground symbols are one net.
- Wires that cross with a dot are connected; without a dot or with a hop,
  not connected; a T-junction is connected.
- PMOS vs NMOS: trust the printed model name (`pmos1`, `nmos1`, `pfet`) when
  shown; otherwise gate bubble → PMOS; arrow on the source pointing out → NMOS,
  pointing in → PMOS.
- A label that makes no electrical sense (for example a gate tied to VSS that
  would turn off a current source) is still recorded as drawn; add a note.

## Procedure

1. `grid` the figure; inventory every device with its designator and printed
   parameters (zoom until every character is certain: 0 vs 8, u vs n).
2. Trace every terminal to a net; cross-check each net's terminal list.
3. Look up anything missing in the paper text/tables (if a PDF is given).
4. Write the JSON, run the validator, fix until OK.
5. Reply with: device count, what is absent, and anything uncertain.
