# Sizing, LLM round 2: telescopic cascode (Fig. 2): fill the sizes and biases the figure omits

You derive analytical design equations for an analog circuit and encode them as a
Python sizing function. Local code runs it with device parameters it measures itself
and never shows you; you see only how far the results are from the targets.
Read only this prompt and the files it names. Do not open any other file.

## Circuit
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

## Your previous function
```python
# ============================================================================
# Telescopic cascode (Fig. 2), round 1.
# Round-0 feedback: gain 3.9 dB below prediction; PM0/PM1 (left, x1 branch)
# in triode. Structural fixes in this round:
#  (a) GAIN EXPRESSION. AC is injected at vin2 only; vin1 is AC ground, so the
#      tail node moves by ~vin/2 and NM1 acts as a 1/gm source degeneration for
#      NM4. The current into vout is i4 = gm*vin*(gm+gt)/(2gm+gt) ~ gm/2 * vin
#      (gt = 1/ro of NM2). Round 0 used gm*Rout: a 6 dB overestimate.
#      Cascode output resistance now also includes body transconductance of
#      the cascodes (gm+gmb) ro ro, gmb = eta*gm.
#  (b) BODY EFFECT. Fitted per-device vth is measured at each device's own
#      operating point, so it already contains the body effect; round 0 added
#      it a second time. Now params["..."]["vth"] is used directly.
#  (c) HEADROOM. x1 has no feedback: it lands where the left PMOS current
#      equals the left NMOS current, and it moves opposite to any vout error.
#      Its room to move up is the PM1 Vsd slack, down is the NM0 Vds slack.
#      PM2 and NM4 are given only a fixed margin (m), and vcm is placed to
#      equalise the NM2 (tail) slack and the x1/vout upward slack (PM1/PM3),
#      which was the side that failed. Downward room (NM0/NM3) is ~Vth4-Vov3-m.
#  Bias currents: NM2 sinks 2I with its (1+lam Vds) term at the predicted tail
#  voltage, PM0/PM2 source I with (1+lam Vsd) at the predicted Vsd, so the two
#  sides are balanced with the same current model.
#
# Numbers below use initial_params() (the local code replaces them with fitted
# values; the same equations are then re-evaluated). m = 0.10 V.
#
# (1) Device roles
#   NM2 tail sink (vbn0), NM1/NM4 input pair (NM4 at vin2 drives the vout
#   side), NM0/NM3 NMOS cascodes (vbn1), PM1/PM3 PMOS cascodes (vbp2), PM0/PM2
#   PMOS current-source loads (vbp1). Single-ended output at vout; x1 is the
#   unloaded left branch drain (no mirror, so it carries no signal to vout).
#
# (2) Device constraints / classification
#   NM1: INDEPENDENT, W = 2 Id L / (muCox Vov1^2), Vov1 = 2 Id / gm1 with gm1
#   from the gain equation. NM4: MATCHED to NM1. L = 0.5u, m = 1 (printed).
#   Fixed: NM2 3u/0.5u, NM0/NM3 6u/0.5u, PMOS 7u/0.5u. Knob: branch current I.
#
# (3) Signal path
#   vin2 -> NM4 (Gm = gm/2, NM1 degenerates the tail) -> n2 (low Z, 1/gm3) ->
#   NM3 -> vout (Rout || CL). Non-dominant poles at n2 (gm3/Cn2), p2
#   (gmp3/Cp2) and the tail node ((2gm1)/Ctail, gives a pole-zero doublet).
#
# (4) Design equations
#   Vov2 = sqrt(2*2I/(k_n*6)), Vov3 = sqrt(2I/(k_n*12)), Vovp = sqrt(2I/(k_p*14))
#   ro = 1/(lam I); eta_n = 0.18, eta_p = 0.17 (gmb/gm at the cascode Vsb)
#   Rn = ro3 + ro4 + gm3(1+eta_n) ro3 ro4;  Rp = ro3p + ro2p + gmp(1+eta_p) ro3p ro2p
#   Rout = Rn || Rp;  gt = lam2 * 2I
#   A = Gm Rout, Gm = gm1 (gm1+gt)/(2 gm1+gt)  -> gm1 from the quadratic
#       gm1^2 + gm1 (gt - 2 A/Rout) - (A/Rout) gt = 0
#   GBW = Gm/(2 pi CL); PM = 90 - atan(GBW/f_n2) - atan(GBW/f_p2)
#   Power = VDD * 2I
#   Window (vout = vcm):  vcm_lo = Vov2 + m + Vth4 + Vov1  (tail at NM2 edge+m)
#                         vcm_hi = VDD - (Vovp+m) - Vovp    (PM2 at edge+m, PM3 at edge)
#   vcm = (vcm_lo + vcm_hi)/2 -> NM2 slack = PM3/PM1 slack = (vcm_hi-vcm_lo)/2.
#   I scanned 3..100 uA; keep the largest window with 0.42u <= W1 <= 30u.
#   Result (initial params): I = 6 uA, gm1 = 54.5 uS, Gm = 28.4 uS,
#   Vov1 = 0.220 V, W1 = 0.459 um, Rn = 41.2 M, Rp = 21.2 M, Rout = 14.0 M,
#   A = 28.4u * 14.0M = 398 = 52.0 dB, GBW = 28.4u/(2 pi 20p) = 0.23 MHz,
#   f_n2 ~ 1.05 GHz, f_p2 ~ 0.47 GHz -> PM ~ 90 deg, power = 1.8*12u = 21.6 uW.
#
# (5) DC bias verification (initial params, I = 6 uA)
#   Vov2 = sqrt(24u/(270u*6)) = 0.122; Vov3 = sqrt(6u/(270u*12)) = 0.061;
#   Vovp = sqrt(6u/(60u*14)) = 0.120; Vth4 = 0.55; Vov1 = 0.220.
#   vcm_lo = 0.122+0.1+0.55+0.220 = 0.992;  vcm_hi = 1.8-0.220-0.120 = 1.461
#   vcm = 1.226; tail = 1.226-0.55-0.220 = 0.456 >= Vov2 0.122 (slack 0.334)
#   NM4: n2 = 0.456+0.220+0.1 = 0.776; Vds4 = 0.320 >= 0.220 (slack 0.10)
#   NM3: Vds3 = 1.226-0.776 = 0.450 >= 0.061 (slack 0.389: x1 down room)
#   PM2: p2 = 1.8-0.220 = 1.580; Vsd2 = 0.220 >= 0.120 (slack 0.10)
#   PM3: Vsd3 = 1.580-1.226 = 0.354 >= 0.120 (slack 0.234: x1 up room)
#   Left branch identical at balance (vin1 = vcm, x1 = vout).
#   Biases: vbn0 = 0.55+0.122/sqrt(1.182) = 0.662; vbn1 = 0.776+0.55+0.061
#   = 1.387; vbp2 = 1.580-0.95-0.120 = 0.511; vbp1 = 1.8-0.95-0.120/
#   sqrt(1.088) = 0.735.
#
# (6) DC operating-point consistency (each node from its driving device)
#   tail = vcm - Vth4 - Vov1 (source follower from the input, not assumed).
#   vbn0 = Vth2 + Vov2/sqrt(1+lam2*tail): NM2 then sinks exactly 2I at that tail.
#   vbn1 = n2 + Vth3 + Vov3: NM3's source sits at vbn1 - Vth3 - Vov3 = n2,
#     which is the value that gives NM4 Vds = Vov1 + m.
#   vbp2 = p2 - |Vthp3| - Vovp: PM3's source sits at vbp2 + |Vthp3| + Vovp = p2.
#   vbp1 = VDD - |Vthp| - Vovp/sqrt(1+lamp*(VDD-p2)): PM2 sources exactly I at
#     Vsd = VDD - p2, equal to half of NM2's 2I (both lambda-corrected).
#   Unity feedback: loop drives vin2 until I4 = I_PM2, so vout = vin2 = vcm,
#   inside [vcm_lo, vcm_hi].
#
# (7) Python code below.
# ============================================================================
import math

VDD_DEFAULT = 1.8
L0 = 0.5e-6
MARGIN = 0.10          # V, minimum saturation margin on PM2 / NM4 / NM2
ETA_N, ETA_P = 0.18, 0.17   # gmb/gm of the cascodes at their source voltages
W1_MAX = 30e-6

FIXED = {  # printed, not changed
    "PM0": (7e-6, L0), "PM2": (7e-6, L0), "PM1": (7e-6, L0), "PM3": (7e-6, L0),
    "NM0": (6e-6, L0), "NM3": (6e-6, L0), "NM2": (3e-6, L0),
}


def initial_params():
    n = {"type": "NMOS", "muCox": 270e-6, "a_gm": 1.0, "lam": 0.40, "vth": 0.55}
    p = {"type": "PMOS", "muCox": 60e-6, "a_gm": 1.0, "lam": 0.40, "vth": 0.95}
    out = {}
    for d in ("NM0", "NM1", "NM2", "NM3", "NM4"):
        out[d] = dict(n)
    for d in ("PM0", "PM1", "PM2", "PM3"):
        out[d] = dict(p)
    return out


def _vov(I, mucox, wl):
    return math.sqrt(2.0 * I / (mucox * wl))


def _gm(I, pr, wl):
    return pr["a_gm"] * math.sqrt(2.0 * pr["muCox"] * wl * I)


def _design(I, spec, params, gain_target):
    vdd = spec["conditions"].get("vdd") or VDD_DEFAULT
    pn2, pn3, pn4 = params["NM2"], params["NM3"], params["NM4"]
    pp2, pp3 = params["PM2"], params["PM3"]
    wl_n2 = FIXED["NM2"][0] / FIXED["NM2"][1]
    wl_n3 = FIXED["NM3"][0] / FIXED["NM3"][1]
    wl_p = FIXED["PM2"][0] / FIXED["PM2"][1]

    vov2 = _vov(2 * I, pn2["muCox"], wl_n2)
    vov3 = _vov(I, pn3["muCox"], wl_n3)
    vovp2 = _vov(I, pp2["muCox"], wl_p)
    vovp3 = _vov(I, pp3["muCox"], wl_p)

    ro = lambda pr: 1.0 / (pr["lam"] * I)
    gm3 = _gm(I, pn3, wl_n3)
    gmp3 = _gm(I, pp3, wl_p)
    Rn = ro(pn3) + ro(pn4) + gm3 * (1 + ETA_N) * ro(pn3) * ro(pn4)
    Rp = ro(pp3) + ro(pp2) + gmp3 * (1 + ETA_P) * ro(pp3) * ro(pp2)
    Rout = Rn * Rp / (Rn + Rp)
    A = 10 ** (gain_target / 20.0)
    gt = pn2["lam"] * 2 * I
    ar = A / Rout
    b = gt - 2 * ar
    gm1 = (-b + math.sqrt(b * b + 4 * ar * gt)) / 2.0
    Gm = gm1 * (gm1 + gt) / (2 * gm1 + gt)
    wl1 = (gm1 / pn4["a_gm"]) ** 2 / (2 * pn4["muCox"] * I)
    vov1 = _vov(I, pn4["muCox"], wl1)

    vth4 = abs(pn4["vth"])
    vcm_lo = vov2 + MARGIN + vth4 + vov1
    vcm_hi = vdd - (vovp2 + MARGIN) - vovp3
    return dict(I=I, vdd=vdd, vov2=vov2, vov3=vov3, vovp2=vovp2, vovp3=vovp3,
                gm1=gm1, Gm=Gm, wl1=wl1, vov1=vov1, Rn=Rn, Rp=Rp, Rout=Rout, A=A,
                vcm_lo=vcm_lo, vcm_hi=vcm_hi, gm3=gm3, gmp3=gmp3, vth4=vth4)


def compute_sizing(spec, params):
    gain_target = spec["targets"]["gain_dB"]
    cl = spec["conditions"].get("cl") or 20e-12

    best = None
    I = 3e-6
    while I <= 100e-6 + 1e-12:
        d = _design(I, spec, params, gain_target)
        w1 = d["wl1"] * L0
        if 0.42e-6 <= w1 <= W1_MAX:
            slack = d["vcm_hi"] - d["vcm_lo"]
            if best is None or slack > best[0]:
                best = (slack, d)
        I += 0.5e-6
    if best is None:   # fall back: legal width closest to range
        d = _design(10e-6, spec, params, gain_target)
    else:
        d = best[1]
    I, vdd = d["I"], d["vdd"]
    w1 = min(max(d["wl1"] * L0, 0.42e-6), 100e-6)

    vcm = 0.5 * (d["vcm_lo"] + d["vcm_hi"])
    tail = vcm - d["vth4"] - d["vov1"]
    n2 = tail + d["vov1"] + MARGIN
    vbn1 = n2 + abs(params["NM3"]["vth"]) + d["vov3"]
    vbn0 = abs(params["NM2"]["vth"]) + d["vov2"] / math.sqrt(1 + params["NM2"]["lam"] * tail)
    p2 = vdd - d["vovp2"] - MARGIN
    vbp2 = p2 - abs(params["PM3"]["vth"]) - d["vovp3"]
    pp2 = params["PM2"]
    vbp1 = vdd - abs(pp2["vth"]) - d["vovp2"] / math.sqrt(1 + pp2["lam"] * (vdd - p2))

    Gm = d["Gm"]
    gbw = Gm / (2 * math.pi * cl)
    cn2 = (2.0 / 3.0) * 6e-6 * L0 * 8.5e-3 + 2 * (6e-6 + w1) * 1e-9
    p_nd = d["gm3"] / (2 * math.pi * cn2)
    cp2 = (2.0 / 3.0) * 7e-6 * L0 * 8.5e-3 + 2 * 7e-6 * 1e-9
    p_pd = d["gmp3"] / (2 * math.pi * cp2)
    pm = 90.0 - math.degrees(math.atan(gbw / p_nd)) - math.degrees(math.atan(gbw / p_pd))

    compute_sizing.debug = dict(I=I, w1=w1, vcm=vcm, tail=tail, n2=n2, p2=p2,
                                vov1=d["vov1"], vov2=d["vov2"], vov3=d["vov3"],
                                vovp=d["vovp2"], gm1=d["gm1"], Gm=Gm, Rn=d["Rn"],
                                Rp=d["Rp"], Rout=d["Rout"], vcm_lo=d["vcm_lo"],
                                vcm_hi=d["vcm_hi"], vbp1=vbp1, vbp2=vbp2,
                                vbn1=vbn1, vbn0=vbn0, p_nd=p_nd, p_pd=p_pd)
    return {
        "sizes": {
            "NM1": {"w": w1, "l": L0, "m": 1},
            "NM4": {"w": w1, "l": L0, "m": 1},
        },
        "biases": {"V1": vbp1, "V2": vbp2, "V3": vbn1, "V4": vbn0},
        "currents": {},
        "caps": {},
        "vcm": vcm,
        "predicted": {
            "gain_dB": 20 * math.log10(Gm * d["Rout"]),
            "gbw_Hz": gbw,
            "pm_deg": pm,
            "power_W": vdd * 2 * I,
        },
    }


if __name__ == "__main__":
    spec = {"targets": {"gain_dB": 52.0}, "conditions": {"vdd": 1.8, "cl": 2e-11}}
    r = compute_sizing(spec, initial_params())
    print(r)
    print(compute_sizing.debug)

```

## Result of your previous function (relative feedback only)

Your function was run by local code, which also re-fitted the device
parameters it receives from simulation and re-ran it 5 time(s).
Device parameters, currents and node voltages are confidential and are not shown;
only errors relative to your targets and predictions are.
Local outcome: stalled settled. The best design of that
local run is reported below.

| Metric | vs target | vs your prediction |
|---|---|---|
| gain_dB | +1.1 dB (within tolerance) | +1.1 dB |

Follower settles at the input common mode: True.
Transistors not saturated: PM0 (triode), PM1 (triode).

Rows are measured minus target / measured minus predicted.

## This round
The parameters your function receives are already fitted to simulation, so a
remaining error comes from the EQUATIONS or the DESIGN STRATEGY, not from numbers.
Revise the structure: missing poles or zeros, wrong gain expression, headroom
allocation, which device sets which current. Keep initial_params() (it is only
used if local fitting has no data for a device).

## Output contract

Write ONE Python file, `<repo root>/cases/opamp3/sizing_B/telescopic/llm_2/compute_sizing.py`, standard library only (math allowed), with:

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
`.venv/bin/python pipeline/sizing_local.py dry <repo root>/cases/opamp3/sizing_B/telescopic 2` must print OK. That command
does not simulate; do not run any simulation yourself.
