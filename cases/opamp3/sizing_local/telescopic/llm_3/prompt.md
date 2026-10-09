# Sizing, LLM round 3: telescopic cascode (Fig. 2): fill the sizes and biases the figure omits

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
# Telescopic cascode (Fig. 2), round 2.
# Round-1 feedback: gain +1.1 dB (in tolerance), follower settles, but PM0/PM1
# (left, x1 branch) in triode again.
#
# Diagnosis (strategy, not numbers). x1 has no feedback. Unity feedback fixes
# I4 = I(PM2); then I1 = I(NM2) - I(PM2) is forced into the left branch, and
# x1 moves by (I(PM0) - I1) * Rx with Rx ~ Rout ~ 14 MOhm. The x1 window is
# ~0.25-0.4 V, so the ratio I(NM2) : 2 I(PM0) must be right to ~0.3 %. PMOS
# too strong -> x1 rises -> PM1 then PM0 triode (what we saw, twice).
# Round 1 set the two currents with DIFFERENT lambda corrections:
#   NM2: Vov2/sqrt(1 + lam*Vtail), Vtail = 0.456 -> factor 1.182
#   PM2: Vovp/sqrt(1 + lam*Vsd),   Vsd   = 0.220 -> factor 1.088
# If the fitted (muCox, vth) already describe the current at the operating
# point (as the fitted vth already contains body effect), those corrections
# weaken NM2 by 18 % and PM2 by 8.8 %: PMOS 8.6 % too strong, exactly the
# observed direction. Fix: place the operating point so the two corrections
# are EQUAL, lam_n2*Vds(NM2) = lam_p2*Vsd(PM2). Then I(NM2)/2I(PM2) comes out
# the same whether or not the fit already includes (1+lam V): the balance no
# longer depends on that convention. That forces Vsd(PM2) = r*Vtail with
# r = lam_n2/lam_p2, which reallocates headroom: tail goes down (0.456 ->
# ~0.26 V), PM2 Vsd goes up, and the x1 up-room (PM1 slack) and down-room
# (NM0 slack) are set equal instead of leaving the tail with the most slack.
# PM0/PM1 fitted params (taken in triode) are not used; PM2/PM3 set their bias.
#
# Numbers below use initial_params(); local code re-evaluates with fitted ones.
# m = 0.10 V minimum margin on NM2, NM4, PM2.
#
# (1) Device roles
#   NM2 tail sink (vbn0), NM1/NM4 input pair (NM4 at vin2 drives vout), NM0/NM3
#   NMOS cascodes (vbn1), PM1/PM3 PMOS cascodes (vbp2), PM0/PM2 PMOS current
#   loads (vbp1). Output vout; x1 is the unloaded left drain (no signal to vout).
#
# (2) Device constraints / classification
#   NM1: INDEPENDENT, W = 2 Id L/(muCox Vov1^2), Vov1 = 2Id/gm1, gm1 from the
#   gain equation. NM4: MATCHED to NM1. L = 0.5u, m = 1 (printed).
#   Fixed: NM2 3u/0.5u, NM0/NM3 6u/0.5u, PMOS 7u/0.5u. Knob: branch current I.
#
# (3) Signal path
#   vin2 -> NM4 (Gm ~ gm/2: NM1 degenerates the tail, vin1 AC ground) -> n2
#   (1/gm3) -> NM3 -> vout (Rout || CL). Non-dominant poles at n2 (gm3/Cn2),
#   p2 (gmp3/Cp2); tail node gives a pole-zero doublet (ignored).
#
# (4) Design equations
#   Vov2 = sqrt(2*2I/(k_n*6)), Vov3 = sqrt(2I/(k_n*12)), Vovp = sqrt(2I/(k_p*14))
#   ro = 1/(lam I); Rn = ro3+ro4+gm3(1+eta_n)ro3 ro4; Rp = ro3p+ro2p+gmp(1+eta_p)ro3p ro2p
#   Rout = Rn||Rp; gt = lam2*2I; Gm = gm1(gm1+gt)/(2gm1+gt); A = Gm Rout
#   -> gm1^2 + gm1(gt - 2A/Rout) - (A/Rout) gt = 0
#   GBW = Gm/(2 pi CL); PM = 90 - atan(GBW/f_n2) - atan(GBW/f_p2); P = VDD*2I
#   Headroom (vout = x1 = vcm at balance), tail = t, Vsd(PM2) = r t:
#     vcm = t + Vth4 + Vov1; n2 = t + Vov1 + m; p2 = VDD - r t
#     up   (PM1/PM3 slack) = VDD - r t - vcm - Vovp = VDD-(1+r)t-Vth4-Vov1-Vovp
#     down (NM0/NM3 slack) = vcm - n2 - Vov3 = Vth4 - m - Vov3
#     t = (VDD - 2Vth4 - Vov1 - Vovp + m + Vov3)/(1+r)   (up = down)
#     t >= t_min = max(Vov2 + m, (Vovp + m)/r)
#   Current scan I = 3..100 uA: keep max of min(up, down, t-Vov2-m, rt-Vovp-m)
#   with 0.42u <= W1 <= 30u.
#   Result (initial params, r = 1): I = 6 uA, gm1 = 54.5 uS, Gm = 28.4 uS,
#   Vov1 = 0.220, W1 = 0.459 um, Rout = 14.0 M, A = 398 = 52.0 dB,
#   GBW = 0.23 MHz, PM ~ 90 deg, power = 21.6 uW.
#
# (5) DC bias verification (initial params, I = 6 uA)
#   Vov2 = 0.122, Vov3 = 0.061, Vovp = 0.120, Vth4 = 0.55, Vov1 = 0.220.
#   t = (1.8-1.10-0.220-0.120+0.10+0.061)/2 = 0.2605 >= t_min 0.222
#   NM2: Vds = 0.2605 >= 0.122 (slack 0.139)
#   vcm = 0.2605+0.55+0.220 = 1.0305
#   NM4: n2 = 0.2605+0.220+0.1 = 0.5805; Vds4 = 0.320 >= 0.220 (slack 0.10)
#   NM3: Vds3 = 1.0305-0.5805 = 0.450 >= 0.061 (slack 0.389 = x1 down room)
#   PM2: p2 = 1.8-0.2605 = 1.5395; Vsd = 0.2605 >= 0.120 (slack 0.1405)
#   PM3: Vsd3 = 1.5395-1.0305 = 0.509 >= 0.120 (slack 0.389 = x1 up room)
#   Left branch identical at balance.
#   lambda factors: NM2 1+0.4*0.2605 = 1.104, PM2 1+0.4*0.2605 = 1.104: equal.
#
# (6) DC operating-point consistency (each node from its driving device)
#   tail = vcm - Vth4 - Vov1 = 1.0305-0.55-0.220 = 0.2605 (input follower).
#   vbn0 = Vth2 + Vov2/sqrt(1.104) = 0.55+0.116 = 0.666: NM2 sinks 2I at 0.2605.
#   vbn1 = n2 + Vth3 + Vov3 = 0.5805+0.55+0.061 = 1.1915 -> NM3 source = n2.
#   vbp2 = p2 - |Vthp3| - Vovp = 1.5395-0.95-0.120 = 0.4695 -> PM3 source = p2.
#   vbp1 = VDD - |Vthp2| - Vovp/sqrt(1.104) = 1.8-0.95-0.114 = 0.736: PM2
#     sources I at Vsd 0.2605, half of NM2's 2I with the same (1+lam V) factor.
#   Feedback drives vin2 until I4 = I(PM2) -> vout = vin2 = vcm = 1.03 V.
#
# (7) Python code below.
# ============================================================================
import math

VDD_DEFAULT = 1.8
L0 = 0.5e-6
MARGIN = 0.10
ETA_N, ETA_P = 0.18, 0.17
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

    # headroom allocation with equal lambda factors on NM2 and PM2
    r = pn2["lam"] / pp2["lam"] if pp2["lam"] > 0 else 1.0
    r = min(max(r, 0.4), 2.5)
    t_min = max(vov2 + MARGIN, (vovp2 + MARGIN) / r)
    t_eq = (vdd - 2 * vth4 - vov1 - vovp3 + MARGIN + vov3) / (1 + r)
    t = max(t_min, t_eq)
    vcm = t + vth4 + vov1
    up = vdd - r * t - vcm - vovp3
    down = vth4 - MARGIN - vov3
    s_tail = t - vov2 - MARGIN
    s_p2 = r * t - vovp2 - MARGIN
    score = min(up, down, s_tail + MARGIN, s_p2 + MARGIN)
    return dict(I=I, vdd=vdd, vov2=vov2, vov3=vov3, vovp2=vovp2, vovp3=vovp3,
                gm1=gm1, Gm=Gm, wl1=wl1, vov1=vov1, Rn=Rn, Rp=Rp, Rout=Rout, A=A,
                gm3=gm3, gmp3=gmp3, vth4=vth4, r=r, t=t, vcm=vcm, up=up,
                down=down, score=score)


def compute_sizing(spec, params):
    gain_target = spec["targets"]["gain_dB"]
    cl = spec["conditions"].get("cl") or 20e-12

    best = None
    I = 3e-6
    while I <= 100e-6 + 1e-12:
        d = _design(I, spec, params, gain_target)
        w1 = d["wl1"] * L0
        if 0.42e-6 <= w1 <= W1_MAX:
            if best is None or d["score"] > best["score"]:
                best = d
        I += 0.5e-6
    d = best if best is not None else _design(10e-6, spec, params, gain_target)
    I, vdd = d["I"], d["vdd"]
    w1 = min(max(d["wl1"] * L0, 0.42e-6), 100e-6)

    vcm, tail = d["vcm"], d["t"]
    n2 = tail + d["vov1"] + MARGIN
    p2 = vdd - d["r"] * tail
    pn2, pp2 = params["NM2"], params["PM2"]
    vbn1 = n2 + abs(params["NM3"]["vth"]) + d["vov3"]
    vbn0 = abs(pn2["vth"]) + d["vov2"] / math.sqrt(1 + pn2["lam"] * tail)
    vbp2 = p2 - abs(params["PM3"]["vth"]) - d["vovp3"]
    vbp1 = vdd - abs(pp2["vth"]) - d["vovp2"] / math.sqrt(1 + pp2["lam"] * (vdd - p2))

    Gm = d["Gm"]
    gbw = Gm / (2 * math.pi * cl)
    cn2 = (2.0 / 3.0) * 6e-6 * L0 * 8.5e-3 + 2 * (6e-6 + w1) * 1e-9
    p_nd = d["gm3"] / (2 * math.pi * cn2)
    cp2 = (2.0 / 3.0) * 7e-6 * L0 * 8.5e-3 + 2 * 7e-6 * 1e-9
    p_pd = d["gmp3"] / (2 * math.pi * cp2)
    pm = 90.0 - math.degrees(math.atan(gbw / p_nd)) - math.degrees(math.atan(gbw / p_pd))

    compute_sizing.debug = dict(I=I, w1=w1, vcm=vcm, tail=tail, n2=n2, p2=p2,
                                r=d["r"], up=d["up"], down=d["down"],
                                vov1=d["vov1"], vov2=d["vov2"], vov3=d["vov3"],
                                vovp=d["vovp2"], gm1=d["gm1"], Gm=Gm,
                                Rout=d["Rout"], vbp1=vbp1, vbp2=vbp2,
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
parameters it receives from simulation and re-ran it 3 time(s).
Device parameters, currents and node voltages are confidential and are not shown;
only errors relative to your targets and predictions are.
Local outcome: stalled diverging. The best design of that
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

Write ONE Python file, `<repo root>/cases/opamp3/sizing_B/telescopic/llm_3/compute_sizing.py`, standard library only (math allowed), with:

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
`.venv/bin/python pipeline/sizing_local.py dry <repo root>/cases/opamp3/sizing_B/telescopic 3` must print OK. That command
does not simulate; do not run any simulation yourself.
