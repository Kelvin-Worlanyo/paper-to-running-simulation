# Sizing round 0: telescopic cascode (Fig. 2): fill the sizes and biases the figure omits

You derive analytical design equations for an analog circuit and encode them as a
Python sizing function. A script executes it unmodified, a simulator measures the
result, and calibration data comes back in the next round (to a fresh session).
Read only this prompt and the files it names. Do not open any other file.

## Circuit (from the paper's figure; ids are the printed designators)
```
pins: vdd=vdd gnd=gnd out=vout in=['vin1', 'vin2']
inverting input (decided by simulation): vin2
V1     Voltage  bias  Positive=vbp1 Negative=gnd                       VARIABLE
V2     Voltage  bias  Positive=vbp2 Negative=gnd                       VARIABLE
V3     Voltage  bias  Positive=vbn1 Negative=gnd                       VARIABLE
V4     Voltage  bias  Positive=vbn0 Negative=gnd                       VARIABLE
PM0    PMOS     core  Drain=p1 Gate=vbp1 Source=vdd                    w=7u l=500n m=1 (fixed, printed)
PM2    PMOS     core  Drain=p2 Gate=vbp1 Source=vdd                    w=7u l=500n m=1 (fixed, printed)
PM1    PMOS     core  Drain=x1 Gate=vbp2 Source=p1                     w=7u l=500n m=1 (fixed, printed)
PM3    PMOS     core  Drain=vout Gate=vbp2 Source=p2                   w=7u l=500n m=1 (fixed, printed)
NM0    NMOS     core  Drain=x1 Gate=vbn1 Source=n1                     w=6u l=500n m=1 (fixed, printed)
NM3    NMOS     core  Drain=vout Gate=vbn1 Source=n2                   w=6u l=500n m=1 (fixed, printed)
NM1    NMOS     core  Drain=n1 Gate=vin1 Source=tail                   VARIABLE
NM4    NMOS     core  Drain=n2 Gate=vin2 Source=tail                   VARIABLE
NM2    NMOS     core  Drain=tail Gate=vbn0 Source=gnd                  w=3u l=500n m=1 (fixed, printed)
```

## Specification
```json
{
 "targets": {
  "gain_dB": 52.0
 },
 "tolerance": {
  "gain_dB": [
   "abs",
   3.0
  ]
 },
 "conditions": {
  "vdd": 1.8,
  "cl": 2e-11,
  "vcm": null
 },
 "variables": {
  "devices": [
   "NM1",
   "NM4"
  ],
  "biases": [
   "V1",
   "V2",
   "V3",
   "V4"
  ],
  "vcm": true,
  "keep_printed": {
   "NM1.l": 5e-07,
   "NM4.l": 5e-07,
   "NM1.m": 1,
   "NM4.m": 1
  }
 },
 "also_required": "every transistor saturated; unity-gain follower settles at vcm"
}
```

Targets are to be MET WITHIN TOLERANCE (not exceeded by as much as possible).

## Rules (apply them; do not restate them)

1. Structure your reasoning in seven sections, in order, BEFORE writing code:
   (1) Device roles  (2) Device constraints  (3) Signal path  (4) Design
   equations (gain, GBW, phase margin, power; symbolic)  (5) DC bias
   verification: show that every branch supports saturation, with numbers
   (6) DC operating-point consistency: show the voltage each stage produces is
   what the next stage needs, with explicit arithmetic  (7) Python code.
   Write sections (1)-(6) at the top of the file as a comment block.
2. Classify every variable transistor as MIRROR (W = Wref * Itarget/Iref *
   L/Lref, same L as its reference), MATCHED (copies its partner exactly) or
   INDEPENDENT (W = 2 Id L / (muCox Vov^2)). A mirror must use its reference's L.
3. Anti-circularity: compute every inter-stage node voltage from the driving
   stage's device parameters (e.g. V = VDD - |Vth,p| - Vov). Never assume a
   node voltage and then use it to justify itself.
4. Parasitics: large widths add gate and junction capacitance that lower GBW
   and phase margin. Prefer raising overdrive over widening devices when phase
   margin or GBW falls short.
5. Never write "self-adjusts" or "consistent by construction" without numbers.
6. Process: SkyWater Sky130, 1.8 V devices (sky130_fd_pr__nfet_01v8 /
   pfet_01v8). Allowed W 0.42-100 um, L 0.15-8 um per finger; use m > 1 for
   more width. Typical |Vth| is about 0.5-0.7 V (NMOS) and 0.9-1.0 V (PMOS)
   at L = 0.5 um, but trust calibrated values when given.
7. Do not change anything marked (fixed, printed). Size only VARIABLE items.
8. Bench: unity-gain feedback, DC loop through an ideal inductor, AC injected at
   the inverting input; gain = loop gain at 0.01 Hz, GBW = 0 dB crossing,
   PM = unwrapped phase margin, power = supply current x VDD.

## Round 0
Estimate initial_params() for every MOS device from your process knowledge,
then write compute_sizing().

## Output contract

Write ONE Python file, `<repo root>/cases/opamp3/sizing/telescopic/round_0/compute_sizing.py`, standard library only (math allowed), with:

```python
def initial_params():          # required in round 0 only; ignored afterwards
    return {"<device id>": {"type": "NMOS"|"PMOS", "muCox": A_per_V2, "a_gm": float,
                              "lam": per_V, "vth": V}, ...}   # every MOS device

def compute_sizing(spec, params):
    # spec: the dict under "## Specification" below; params: per-device dict as above
    return {
      "sizes":    {"<device id>": {"w": metres, "l": metres, "m": int}, ...},   # VARIABLE MOS only
      "biases":   {"<source id>": volts, ...},     # VARIABLE voltage sources only
      "currents": {"<source id>": amps, ...},      # VARIABLE current sources only
      "caps":     {"<cap id>": farads, ...},       # VARIABLE capacitors only
      "vcm": volts,                                # input common mode (if variable)
      "predicted": {"gain_dB": .., "gbw_Hz": .., "pm_deg": .., "power_W": ..},
    }
```

Check that it executes before you finish:
`.venv/bin/python pipeline/sizing.py dry <repo root>/cases/opamp3/sizing/telescopic 0` must print OK. That command
does not simulate; do not run any simulation yourself.
