# Circuit diagram → netlist (Image2Net benchmark, zero-shot)

You convert analog circuit diagrams into topology netlists. You get only the
image. No reference netlists exist anywhere you may look.

## Rules of the run

- Read only: your assigned images, crops you make of them, and this file.
  Do not list, search or open any other part of the filesystem. Do not use the
  internet. (The benchmark's answers sit on this machine; seeing them would
  void the run.)
- Work each image independently; don't carry assumptions between images.
- Python: `.venv/bin/python`
  Tools: `vision_eval/image2net/tools.py` (run from the project root,
  `<repo root>`):
  - `tools.py grid IMG OUT.png` — image upscaled with a labelled 0.1 grid
  - `tools.py zoom IMG X0 Y0 X1 Y1 OUT.png` — crop by fractions (0..1), upscaled
  - `tools.py check PRED.json` — schema check (types, port names); must print OK
  Put crops in the scratch directory named in your task, not in the project.

## Output

One file per image: `vision_eval/image2net/pred/opus5_agent_wires/<id>.json`

```json
{"ckt_type": "DISO-Amplifier",
 "ckt_netlist": [
   {"component_type": "NMOS", "port_connection": {"Drain": "n3", "Gate": "vin", "Source": "tail"}},
   {"component_type": "Res",  "port_connection": {"Pos": "VDD", "Neg": "n3"}}
 ]}
```

`ckt_type`: one of DISO-Amplifier, DIDO-Amplifier, SISO-Amplifier, Bandgap,
LDO, Comparator, Other (not scored).

Also write `<id>.notes.txt` next to it: one line per spot you were unsure
about (e.g. "crossing at M5 gate: read as not connected"). Empty file if none.

## Device types and ports (use these names exactly)

| component_type | ports |
|---|---|
| PMOS, NMOS | Drain, Gate, Source, and Body only when drawn (see below) |
| NPN, PNP | Collector, Base, Emitter |
| Res, Cap, Ind | Pos, Neg |
| Diode | In (anode), Out (cathode) |
| Current | In, Out — current flows through the source from In to Out: In is the terminal at the arrow's tail, Out at its head |
| Voltage | Positive (+ terminal), Negative |
| Diso_amp | InP (+ input), InN (− input), Out — op-amp/comparator/OTA triangle with two inputs, one output |
| Dido_amp | InP, InN, OutP, OutN — two inputs, two outputs (fully differential) |
| Siso_amp | In, Out — one input, one output (buffer/inverter/gain triangle) |

Anything that fits none of these (switches, logic gates, blocks): leave it
out, and say so in the notes.

## Conventions

- **Nets**: name them freely; names are not scored, connectivity is.
- **Ground**: every ground symbol is one net, `GND`.
- **Only drawn wires connect (benchmark rule).** Apart from ground symbols,
  two terminals are on the same net only if a drawn wire joins them. Text
  labels do not connect anything: two stubs both labelled VB1, two separate
  VDD arrows or bars, or a gate labelled Vout with no wire to the output are
  DIFFERENT nets. (This is the convention of the benchmark's answer key, whose
  pipeline removes all text before tracing wires.)
- **Pins/labels are not devices**: Vin, Vout, Vb, bias labels are just net
  names. Only draw a Voltage or Current device for an actual source symbol.
- **Crossings**: wires that cross with a dot are connected. Wires that cross
  with no dot, or with a hop/bridge, are not connected. A T-junction is
  connected.
- **MOS body**: add `Body` only when the symbol draws a bulk terminal as a
  separate wire going to a net. A 3-terminal symbol (or bulk shown only as an
  arrow on the source) gets no Body.
- **MOS drain vs source**: the arrow side is the source for 4-terminal/arrow
  symbols; for symmetric symbols pick the terminal nearer the supply for PMOS
  source and nearer ground for NMOS source (the scorer treats drain/source as
  interchangeable in most cases anyway).
- **PMOS vs NMOS**: a bubble on the gate → PMOS. Arrow on the source (like a
  BJT emitter): pointing out, away from the channel → NMOS; pointing in,
  toward the channel → PMOS. Arrow on the middle (bulk) terminal: pointing in
  → NMOS; pointing out → PMOS. Drawing styles are inconsistent: when the
  symbol reading conflicts with the circuit (a device whose source sits on
  the positive rail is almost always PMOS), prefer the circuit and note it.
- Include every drawn device: bias networks, start-up circuits, compensation
  caps, loads.

## Procedure (per image)

1. `grid` the image and look at it whole. Note the drawing style (how
   crossings, bodies and PMOS are drawn).
2. Inventory: list every device with a grid location and an ID you assign.
   Count them. Zoom into dense regions until you are sure of each symbol.
3. Trace: for each device terminal, follow the wire to its net. Zoom along
   long wires and at every crossing. Name the nets.
4. Cross-check net by net: for each net, list all terminals on it and look
   at the image again to confirm that set. A net with a single terminal is
   either a pin (label/port) or a mistake — check which.
5. Recount devices against the inventory. Write the JSON, run `check`, fix
   until OK. Write the notes file.

Accuracy matters more than speed: a single wrong connection makes the
netlist wrong.
