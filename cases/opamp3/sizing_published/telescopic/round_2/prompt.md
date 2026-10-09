# Sizing round 2: telescopic cascode (Fig. 2): fill the sizes and biases the figure omits

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

## Previous sizing function (round 1)
```python
# ============================================================================
# Telescopic cascode (Fig. 2), round 1.
#
# Round-0 post-mortem (from the calibration table): the tail NM2 was biased at
# Vov = 66 mV (vth 0.632, not 0.55) and sank only 6.3 uA instead of 20 uA,
# while the PMOS loads (vbp1) were set for 10 uA each. Loads out-sourced the
# tail, so vout railed to 1.706 V, NM4 went triode (Vds 192 mV), NM1 turned
# off (Vgs 0.54 < 0.754) and both PMOS stacks collapsed (Vsd 0-76 mV). The
# -38 dB "gain" is a dead bias point, not a gain-model error, so the
# "gain over-predicted by Y dB" rule is NOT applied (Y = 90 dB is meaningless);
# the fix is the bias model.
#
# Model used this round (calibrated, sanitised in _model()):
#   EKV interpolation Id = 0.5 k W/L veff^2, veff = 2nUt ln(1+exp(Vov/2nUt)),
#   gm = k W/L veff sigmoid(Vov/2nUt), 2nUt = 69.8 mV. This fits weak and
#   strong inversion with one k, which the square-law row of NM2 cannot.
#   NMOS: vth0 = 0.632 (NM2, Vsb=0). k_n = 477.4u*(66mV/veff(66mV))^2 = 263u.
#         gamma_n = 0.39 (NM4: +123 mV at Vsb 0.687 -> 0.378; NM3: +163 mV at
#         Vsb 0.879 -> 0.406). lambda_n = mean(NM2 0.124, NM3 0.148) = 0.136.
#   PMOS: vth0 = 0.993 (PM2, Vsb=0). PM2 was TRIODE (Vov 104, Vsd 76 mV), its
#         muCox 84.17u uses the SAT formula; triode EKV gives
#         k_p = 84.17u*0.5*0.104^2/(veff*0.076 - 0.076^2/2) = 74.7u.
#         gamma_p = 0.45. lambda_p: every PMOS row is TRIODE/OFF (lambda 8.3,
#         53.7, 6.8e4 ... are garbage) -> assumed 0.15 (about lambda_n).
#   OFF/TRIODE rows (muCox 0, 7331u, lambda 2.3 ...) are ignored.
#
# (1) Device roles
#   NM2 tail sink (vbn0 = V4). NM1/NM4 input pair; NM4 (vin2, inverting) feeds
#   the output branch. NM0/NM3 NMOS cascodes (vbn1 = V3). PM1/PM3 PMOS
#   cascodes (vbp2 = V2). PM0/PM2 PMOS current-source loads (vbp1 = V1).
#   Single-ended output vout; x1 is the mirror-less left branch (not in the
#   signal path).
#
# (2) Device constraints / classification
#   NM1: INDEPENDENT. W1 chosen by a 2-D (I, W1) scan with W1 >= 0.42 um,
#        L = 0.5 um, m = 1 (kept printed). NM4: MATCHED to NM1.
#   Fixed: NM2 W/L 6, NM0/NM3 W/L 12, PMOS W/L 14.
#   Branch current I per side (2I in NM2) is set by V4; the PMOS loads are set
#   to exactly I by V1 so that 2*I_P = I_tail (otherwise x1 or vout rails).
#
# (3) Signal path
#   vin2 -> NM4 (gm4/2, because vin1 is held and the tail node follows half
#   of vin2) -> n2 (1/gm3, low Z) -> NM3 -> vout (Rout || CL). Non-dominant
#   poles at n2 (gm3/C_n2) and p2 (gmp3/C_p2).
#
# (4) Design equations
#   Vov2 = inv(2I, k_n, 6), Vov3 = inv(I, k_n, 12), Vovp = inv(I, k_p, 14),
#   Vov1 = inv(I, k_n, W1/L)   (inv = EKV inversion)
#   ro_n = 1/(lam_n I), ro_p = 1/(lam_p I)
#   Rn = 2 ro_n + (gm3+gmb3) ro_n^2 ; Rp = 2 ro_p + (gmp+gmbp) ro_p^2
#   Rout = Rn || Rp ; A = (gm4/2) Rout ; GBW = (gm4/2)/(2 pi CL)
#   PM = 90 - atan(GBW/f_n2) - atan(GBW/f_p2) ; P = VDD * 2I
#   Headroom (m = 0.05 V): vcm_min = (Vov2+m) + Vth4(Vsb=Vov2+m) + Vov1,
#                          vcm_max = VDD - 2 Vovp - 2m
#   Rule: saturation first. Admissible = window >= 0.10 V; among those, gain
#   closest to 52 dB. Gain falls as I rises (A ~ 1/I) but Vov1, Vov2, Vovp all
#   grow, so the window closes. Result: I = 14.5 uA, W1 = 0.42 um (minimum).
#     Vov1 = 0.362, Vov2 = 0.187, Vov3 = 0.075, Vovp = 0.160 V
#     gm4 = 79.6 uS, gm3 = 226 uS, gmp = 158 uS
#     Rn = 67.6 M, Rp = 41.7 M, Rout = 25.8 M
#     A = 39.8u * 25.8M = 1026 = 60.2 dB  (above the 55 dB upper limit: with
#       lambda_p = 0.15 no saturated design reaches 52 dB; the next point that
#       would, I = 20 uA, has a negative vcm window. If the real lambda_p is
#       ~0.25 the same sizing gives ~55 dB.)
#     GBW = 39.8u/(2 pi 20p) = 0.317 MHz; f_n2 ~ 1.2 GHz, f_p2 ~ 0.74 GHz -> PM ~ 90
#     Power = 1.8 * 29 uA = 52 uW
#
# (5) DC bias verification (I = 14.5 uA, vcm = vout = 1.330 V)
#   Window: vcm_min = 0.237 + 0.681 + 0.362 = 1.279;
#           vcm_max = 1.8 - 0.320 - 0.100 = 1.380; vcm = 1.330 (midpoint).
#   NM2: Vds = tail = 0.280           >= Vov2 0.187 (slack 0.093)
#   NM4: Vds = n2 - tail = 0.948 - 0.280 = 0.668 >= Vov1 0.362 (slack 0.306)
#   NM3: Vds = vout - n2 = 1.330 - 0.948 = 0.382 >= Vov3 0.075 (slack 0.307)
#   PM3: Vsd = p2 - vout = 1.565 - 1.330 = 0.235 >= Vovp 0.160 (slack 0.075)
#   PM2: Vsd = 1.8 - p2 = 0.235       >= Vovp 0.160 (slack 0.075)
#   Left branch NM1/NM0/PM1/PM0: same currents and gate voltages, vin1 = vcm,
#   so x1 nominal = 1.330 with the same slacks.
#
# (6) DC operating-point consistency (each node from its driving device)
#   tail (from NM4 gate): tail = vcm - Vth4(tail) - Vov1;
#     Vth4 = 0.632 + 0.39(sqrt(0.8+0.280) - sqrt(0.8)) = 0.688
#     tail = 1.330 - 0.688 - 0.362 = 0.280 V.
#   vbn0: NM2 must sink 2I = 29 uA at Vds 0.280: Id/(1+lam Vds) = 26.8 uA
#     -> Vov2c = 0.183, vbn0 = 0.632 + 0.183 = 0.815 V
#     (round 0 used 0.698 -> Vov 66 mV -> 6.3 uA, the root failure).
#   n2: window [tail+Vov1+m = 0.691, vout-Vov3-m = 1.204] -> 0.948 V.
#     vbn1 = n2 + Vth3(Vsb 0.948) + Vov3 = 0.948 + 0.799 + 0.075 = 1.822 V
#     -> NM3 source = 1.822 - 0.799 - 0.075 = 0.948 V = NM4 drain needed.
#   p2: window [vout+Vovp+m = 1.540, VDD-Vovp-m = 1.590] -> 1.565 V.
#     vbp2 = p2 - |Vthp3|(Vsb 0.235) - Vovp = 1.565 - 1.048 - 0.160 = 0.357 V
#     -> PM3 source = 0.357 + 1.048 + 0.160 = 1.565 V.
#   vbp1: PM2 sources I = 14.5 uA at Vsd 0.235: I/(1+lam 0.235) = 14.0 uA
#     -> Vovp0c = 0.157, vbp1 = 1.8 - 0.993 - 0.157 = 0.650 V.
#   Current balance: 2 * I_P = 2 * 14.5 = 29 uA = I_NM2 -> the loop sets
#   I4 = I_P2 = 14.5 uA with vin2 = vin1 = vcm, vout = 1.330 V inside
#   [1.279, 1.380].
#
# (7) Python code below.
# ============================================================================
import math

VDD_DEFAULT = 1.8
L0 = 0.5e-6
UT = 0.02585
N_SLOPE = 1.35
TWO_N_UT = 2 * N_SLOPE * UT          # 0.0698 V
PHI2 = 0.8
GAMMA_N = 0.39                        # from NM4 (Vsb 0.687 -> +123 mV) and NM3 (Vsb 0.879 -> +163 mV)
GAMMA_P = 0.45
MARGIN = 0.05                         # V, saturation margin on every Vds
WIN_MIN = 0.10                        # V, extra vcm window (spread over the stack)

FIXED = {  # printed, not changed: (W/L, m)
    "PM0": 14.0, "PM2": 14.0, "PM1": 14.0, "PM3": 14.0,
    "NM0": 12.0, "NM3": 12.0, "NM2": 6.0,
}

# round-0 calibration operating points used to convert the square-law fits to
# the EKV (weak-to-strong interpolating) form used here
CAL_NM2 = dict(vov=0.066)                 # SAT
CAL_PM2 = dict(vov=0.104, vds=0.076)      # TRIODE


def initial_params():
    n = {"type": "NMOS", "muCox": 270e-6, "a_gm": 1.0, "lam": 0.40, "vth": 0.55}
    p = {"type": "PMOS", "muCox": 60e-6, "a_gm": 1.0, "lam": 0.40, "vth": 0.95}
    out = {}
    for d in ("NM0", "NM1", "NM2", "NM3", "NM4"):
        out[d] = dict(n)
    for d in ("PM0", "PM1", "PM2", "PM3"):
        out[d] = dict(p)
    return out


# ---------------------------------------------------------------- device model
def _veff(vov):
    x = vov / TWO_N_UT
    if x > 40:
        return vov
    return TWO_N_UT * math.log1p(math.exp(x))


def _sig(vov):
    x = vov / TWO_N_UT
    if x > 40:
        return 1.0
    return 1.0 / (1.0 + math.exp(-x))


def _id(k, wl, vov):
    return 0.5 * k * wl * _veff(vov) ** 2


def _gm(k, wl, vov):
    return k * wl * _veff(vov) * _sig(vov)


def _vov_for(I, k, wl):
    """invert I = 0.5 k wl veff^2 for vov (Vgs - Vth)."""
    ve = math.sqrt(2.0 * I / (k * wl))
    y = ve / TWO_N_UT
    if y > 40:
        return ve
    return TWO_N_UT * math.log(math.expm1(y))


def _vth_body(vth0, vsb, gamma):
    vsb = max(vsb, 0.0)
    return vth0 + gamma * (math.sqrt(PHI2 + vsb) - math.sqrt(PHI2))


def _plaus(v, lo, hi, default):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return default
    return v if lo <= v <= hi else default


def _model(params):
    """Calibrated, sanitised per-type parameters.

    Rows from OFF/TRIODE devices give meaningless muCox/lambda (0, 7331u,
    lambda 8.3, 53.7 ...), so only the SAT tail NM2 and the shallow-triode PM2
    rows are converted; lambda comes from the two SAT NMOS rows.
    """
    n2, p2 = params.get("NM2", {}), params.get("PM2", {})
    vthn = _plaus(n2.get("vth"), 0.3, 0.9, 0.632)
    vthp = _plaus(p2.get("vth"), 0.5, 1.2, 0.993)
    # NMOS: square-law muCox at Vov=66 mV -> EKV k with the same current
    mun_sq = _plaus(n2.get("muCox"), 100e-6, 900e-6, 477.4e-6)
    vo = CAL_NM2["vov"]
    kn = mun_sq * vo ** 2 / _veff(vo) ** 2
    # PMOS: muCox reported with the SAT formula for a TRIODE point -> triode EKV k
    mup_sq = _plaus(p2.get("muCox"), 20e-6, 300e-6, 84.17e-6)
    vo, vd = CAL_PM2["vov"], CAL_PM2["vds"]
    kp = mup_sq * 0.5 * vo ** 2 / (_veff(vo) * vd - 0.5 * vd ** 2)
    lams = [_plaus(params.get(d, {}).get("lam"), 0.02, 0.5, None) for d in ("NM2", "NM3")]
    lams = [x for x in lams if x is not None]
    lamn = sum(lams) / len(lams) if lams else 0.136
    lamp = 0.15   # no SAT PMOS row yet; assume ~lamn
    return dict(vthn=vthn, vthp=vthp, kn=kn, kp=kp, lamn=lamn, lamp=lamp)


# ---------------------------------------------------------------- design
def _design(I, w1, M, vdd):
    kn, kp, lamn, lamp = M["kn"], M["kp"], M["lamn"], M["lamp"]
    wl1 = w1 / L0
    vov1 = _vov_for(I, kn, wl1)
    gm4 = _gm(kn, wl1, vov1)
    vov2 = _vov_for(2 * I, kn, FIXED["NM2"])
    vov3 = _vov_for(I, kn, FIXED["NM3"])
    vovp = _vov_for(I, kp, FIXED["PM2"])
    gm3 = _gm(kn, FIXED["NM3"], vov3)
    gmp = _gm(kp, FIXED["PM3"], vovp)
    ron, rop = 1.0 / (lamn * I), 1.0 / (lamp * I)
    # body transconductance of the cascodes (Vsb ~0.9 V NMOS, ~0.25 V PMOS)
    gmb3 = gm3 * GAMMA_N / (2 * math.sqrt(PHI2 + 0.9))
    gmbp = gmp * GAMMA_P / (2 * math.sqrt(PHI2 + 0.25))
    Rn = 2 * ron + (gm3 + gmb3) * ron * ron
    Rp = 2 * rop + (gmp + gmbp) * rop * rop
    Rout = Rn * Rp / (Rn + Rp)
    # single-ended drive of the pair (vin1 held at vcm): i4 = (gm4/2) * vin2
    A = 0.5 * gm4 * Rout
    # headroom window for vcm = vout
    tail_min = vov2 + MARGIN
    vcm_min = tail_min + _vth_body(M["vthn"], tail_min, GAMMA_N) + vov1
    vcm_max = vdd - 2 * vovp - 2 * MARGIN
    return dict(I=I, w1=w1, vov1=vov1, vov2=vov2, vov3=vov3, vovp=vovp, gm3=gm3,
                gmp=gmp, gm4=gm4, Rn=Rn, Rp=Rp, Rout=Rout, A=A,
                A_dB=20 * math.log10(A), vcm_min=vcm_min, vcm_max=vcm_max,
                window=vcm_max - vcm_min)


def compute_sizing(spec, params):
    A_dB = spec["targets"]["gain_dB"]
    cond = spec.get("conditions", {})
    vdd = cond.get("vdd") or VDD_DEFAULT
    cl = cond.get("cl") or 20e-12
    M = _model(params)

    # 2-D scan (I, W1). Saturation first: only designs whose vcm window is at
    # least WIN_MIN wide are admissible; among them take the gain closest to
    # target (tie-break: wider window).
    best = None
    for i in range(2, 81):
        I = i * 0.5e-6
        for j in range(0, 41):
            w1 = 0.42e-6 * (1.08 ** j)
            d = _design(I, w1, M, vdd)
            if d["window"] < WIN_MIN:
                continue
            key = (round(abs(d["A_dB"] - A_dB), 2), -d["window"])
            if best is None or key < best[0]:
                best = (key, d)
    if best is None:   # nothing admissible: widest window
        for i in range(2, 81):
            d = _design(i * 0.5e-6, 0.42e-6, M, vdd)
            if best is None or d["window"] > best[1]["window"]:
                best = (None, d)
    d = best[1]
    I, w1 = d["I"], d["w1"]
    vcm = 0.5 * (d["vcm_min"] + d["vcm_max"])

    # tail from the input device: tail = vcm - Vth4(Vsb=tail) - Vov1
    tail = vcm - M["vthn"] - d["vov1"]
    for _ in range(50):
        tail = vcm - _vth_body(M["vthn"], tail, GAMMA_N) - d["vov1"]
    vth4 = _vth_body(M["vthn"], tail, GAMMA_N)
    # n2 centred between NM4 sat edge and NM3 sat edge
    n_lo = tail + d["vov1"] + MARGIN
    n_hi = vcm - d["vov3"] - MARGIN
    n2 = 0.5 * (n_lo + n_hi)
    vth3 = _vth_body(M["vthn"], n2, GAMMA_N)
    vbn1 = n2 + vth3 + d["vov3"]
    # NM2 sinks 2I at Vds = tail (lambda-corrected)
    vov2c = _vov_for(2 * I / (1 + M["lamn"] * tail), M["kn"], FIXED["NM2"])
    vbn0 = M["vthn"] + vov2c
    # PMOS: p2 centred between PM3 sat edge and PM2 sat edge
    p_lo = vcm + d["vovp"] + MARGIN
    p_hi = vdd - d["vovp"] - MARGIN
    p2 = 0.5 * (p_lo + p_hi)
    vthp3 = _vth_body(M["vthp"], vdd - p2, GAMMA_P)
    vbp2 = p2 - vthp3 - d["vovp"]
    vovp0c = _vov_for(I / (1 + M["lamp"] * (vdd - p2)), M["kp"], FIXED["PM2"])
    vbp1 = vdd - M["vthp"] - vovp0c

    gm4 = d["gm4"]
    gbw = (gm4 / 2) / (2 * math.pi * cl)
    cn2 = (2.0 / 3.0) * 6e-6 * L0 * 8.5e-3 + 2 * (6e-6 + w1) * 1e-9
    p_nd = d["gm3"] / (2 * math.pi * cn2)
    cp2 = (2.0 / 3.0) * 7e-6 * L0 * 8.5e-3 + 2 * 7e-6 * 1e-9
    p_pd = d["gmp"] / (2 * math.pi * cp2)
    pm = 90.0 - math.degrees(math.atan(gbw / p_nd)) - math.degrees(math.atan(gbw / p_pd))

    compute_sizing.debug = dict(M=M, vcm=vcm, tail=tail, n2=n2, p2=p2,
                                vth4=vth4, vth3=vth3, vthp3=vthp3, vov2c=vov2c,
                                vovp0c=vovp0c, **d)
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
            "gain_dB": d["A_dB"],
            "gbw_Hz": gbw,
            "pm_deg": pm,
            "power_W": vdd * 2 * I,
        },
    }


if __name__ == "__main__":
    spec = {"targets": {"gain_dB": 52.0}, "conditions": {"vdd": 1.8, "cl": 2e-11}}
    cal = {
        "NM0": dict(type="NMOS", muCox=0.0, a_gm=1.0, lam=0.2335, vth=0.838),
        "NM1": dict(type="NMOS", muCox=0.0, a_gm=1.0, lam=0.2479, vth=0.754),
        "NM2": dict(type="NMOS", muCox=477.4e-6, a_gm=0.540, lam=0.1241, vth=0.632),
        "NM3": dict(type="NMOS", muCox=7331e-6, a_gm=0.118, lam=0.1483, vth=0.795),
        "NM4": dict(type="NMOS", muCox=196.9e-6, a_gm=0.741, lam=2.313, vth=0.755),
        "PM0": dict(type="PMOS", muCox=0.02262e-6, a_gm=0.385, lam=6.824e4, vth=0.993),
        "PM1": dict(type="PMOS", muCox=0.001199e-6, a_gm=0.480, lam=2.682e5, vth=0.993),
        "PM2": dict(type="PMOS", muCox=84.17e-6, a_gm=0.483, lam=8.309, vth=0.993),
        "PM3": dict(type="PMOS", muCox=7.219e-6, a_gm=0.500, lam=53.69, vth=1.012),
    }
    r = compute_sizing(spec, cal)
    print(r)
    for k, v in compute_sizing.debug.items():
        print(k, v)

```

## Calibration (one DC operating point, this round's sizing)

| Dev | Type | W/L (um) x m | Id (uA) | Vov (mV) | Vds (mV) | gm (uS) | Region | muCox (uA/V2) | a_gm | lambda (1/V) | Vth (mV) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| NM0 | NMOS | 6/0.5x1 | 10.5 | 39 | 712 | 187 | SAT | 1137 | 0.349 | 0.1464 | 810 |
| NM1 | NMOS | 0.42/0.5x1 | 10.5 | 338 | 662 | 55.95 | SAT | 218.5 | 0.901 | 0.1487 | 681 |
| NM2 | NMOS | 3/0.5x1 | 26.2 | 182 | 310 | 249.3 | SAT | 263.6 | 0.866 | 0.2933 | 633 |
| NM3 | NMOS | 6/0.5x1 | 15.7 | 65 | 466 | 250.8 | SAT | 617.9 | 0.520 | 0.182 | 807 |
| NM4 | NMOS | 0.42/0.5x1 | 15.7 | 424 | 639 | 65.04 | SAT | 207.3 | 0.880 | 0.1691 | 681 |
| PM0 | PMOS | 7/0.5x1 | 10.5 | 157 | 85 | 75.41 | TRIODE | 61.18 | 0.562 | 8.101 | 993 |
| PM1 | PMOS | 7/0.5x1 | 10.5 | 344 | 32 | 31.23 | TRIODE | 12.7 | 0.511 | 29.96 | 1014 |
| PM2 | PMOS | 7/0.5x1 | 15.7 | 157 | 229 | 149.2 | SAT | 90.71 | 0.748 | 0.4952 | 992 |
| PM3 | PMOS | 7/0.5x1 | 15.7 | 166 | 155 | 129.2 | TRIODE | 81.65 | 0.682 | 2.378 | 1048 |

WARNING: PM0 in TRIODE (Vds=85 mV, Vov=157 mV)
WARNING: PM1 in TRIODE (Vds=32 mV, Vov=344 mV)
WARNING: PM3 in TRIODE (Vds=155 mV, Vov=166 mV)

## Predicted vs measured (fitted targets)

| Metric | Target | Predicted | Measured | Prediction error |
|---|---|---|---|---|
| gain_dB | 52.0 | 60.22538866877405 | 26.8157731 | +33.41 dB |

Follower settles at vcm: False; saturated 6/9.

## History (all rounds so far)

| Round | gain_dB | saturated |
|---|---|---|
| 0 | -38.2663059 | 2/9 |
| 1 | 26.8157731 | 6/9 |

## This round
Do NOT re-estimate device parameters: compute_sizing() will be called with the
calibrated values above. Update compute_sizing() using the margin rules:
- linear metric (GBW, power) over-predicted by X%: design for (1 + X/100) x target
- gain over-predicted by Y dB: design for target + Y dB
- phase margin over-predicted by Z deg: design for target + Z deg
- if your predicted PM is catastrophically low but the measured PM passes, your PM
  equation is wrong: trust the measurement and do not distort sizing to fix it.
- any device flagged TRIODE is a bias-point failure: fix its headroom first.

## Output contract

Write ONE Python file, `<repo root>/cases/opamp3/sizing/telescopic/round_2/compute_sizing.py`, standard library only (math allowed), with:

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
`.venv/bin/python pipeline/sizing.py dry <repo root>/cases/opamp3/sizing/telescopic 2` must print OK. That command
does not simulate; do not run any simulation yourself.
