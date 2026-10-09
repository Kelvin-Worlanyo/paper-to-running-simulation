# ============================================================================
# Telescopic cascode (Fig. 2), round 4.
#
# Round-3 post-mortem (why 40.1 dB and NM0/NM1 TRIODE).
#   The right branch was right: PM2 13.1 uA @ Vsd 267, PM3 Vsd 292, NM4 Vov 256
#   @ Vds 594, NM3 Vds 351, tail 295 mV, NM2 26.1 uA: all SAT.
#   The failure is the floating left node x1. KCL: I4 = I_P2 (vout), I1 =
#   I_tail - I_P2 must equal I_P0(x1). Any imbalance dI = I_tail - 2 I_P is
#   dumped into x1 through R_left (~= Rout ~ 11.6 M): dV(x1) = -dI * R_left.
#   Round 3 predicted Vgs4 = 0.975 V but NM4 measured Vth+Vov = 0.690+0.256 =
#   0.946 V, so at vcm 1.2663 the balanced tail would sit at 1.2663-0.946 =
#   0.320 V, i.e. 25 mV above the design 0.291: dI_tail = gds2*25mV =
#   8.50uS*25mV = +0.21 uA -> x1 fell until NM0/NM1 went triode; NM1 triode
#   needed +23 mV Vov, which pulled vout/vin2 to 1.241 and tail to 0.2953.
#   That triode state also broke the differential half-circuit (gain 40.1 dB).
#   The 11.9 dB "over-prediction" is a bias failure, not a model error, so the
#   gain margin rule is NOT applied as +11.9 dB; triode headroom is fixed first.
#
#   Residual imbalance in the measured state: I1 = I_P0 = I_P2 + gds_P0*(274-
#   267 mV) = I_P2 + 3.56uS*7mV = I_P2 + 24.9 nA, so I_tail(0.2953) = 2 I_P2 +
#   24.9 nA. Balanced tail = 0.2953 - 24.9nA/8.50uS = 0.2924 V.
#
# Strategy: keep V1, V2, V4 bit-identical to round 3 (currents known to the
# measured point, PMOS 13.1 uA, NM2 gm 247.9 uS / gds 8.50 uS) and keep
# W1 = W4 = 0.77 um (Vgs4 measured). Only vcm and V3 move:
#   - vcm is the precision trim of the tail current (dI_tail/dvcm =
#     gds2/(1+eta4) = 7.2 uS, well-known), placing x1 at the centre of its
#     saturation window with a deliberate small dI > 0.
#   - V3 is lowered so NM4/NM1 run at small slack: this (a) raises lambda4
#     and lowers Rn -> gain from ~55 to ~52 dB without touching any current,
#     and (b) moves the cascode slack to NM3/NM0, widening the downward x1
#     window from 0.29 V to ~0.55 V. Vgs4 shift from the lambda integral is
#     only ~9 mV and is fed into vcm.
#
# (1) Device roles
#   NM2 tail sink (V4, fixed 0.815). NM1/NM4 input pair (NM4 = vin2,
#   inverting, drives vout). NM0/NM3 NMOS cascodes (V3). PM1/PM3 PMOS
#   cascodes (V2). PM0/PM2 PMOS loads (V1). Left branch (x1) mirrors right.
#
# (2) Device constraints / classification
#   NM4: INDEPENDENT, W = 0.77 um, L 0.5 um, m 1 (W = 2 I L/(muCox Vov^2)
#        with the measured muCox 259.1u, Vov 0.256, I 13.1u -> 0.77 um).
#   NM1: MATCHED to NM4.
#   Branch currents set by V1 (PM0/PM2, 13.1 uA each) and V4 (NM2 26.1 uA).
#
# (3) Signal path
#   vin2 -> NM4 gm4 -> n2 (1/gm3n) -> NM3 -> vout (Rout || CL); PM3/PM2 load.
#   Tail node is a virtual ground only for the DM part; CM part is degenerated
#   by 1/gds2. Non-dominant poles at n2, p2 (~GHz).
#
# (4) Design equations (symbolic)
#   lambda(s) = c (a + b/s), s = Vds - Vov; c fitted to the measured lambda at
#     the measured slack (PMOS a,b = .037,.0345 validated: PM0 vs PM2 slope
#     -1.94/V measured vs -1.90/V model; NMOS a,b = .070,.0475).
#   dln I|Vgs = c (a dVds + b ln(s/s_m))  ->  dVov = -dlnI * I/gm
#   ro = 1/(lambda I); Rn = ro4+ro3n+(gm3n+gmb3n) ro3n ro4;
#   Rp = ro2+ro3p+(gm3p+gmb3p) ro3p ro2
#   A = (gm4/2)(Rn||Rp) [DM]  +  (gm4/2)/(1+2 gm4/gds2) Rp [CM]
#   GBW = A/(2 pi CL Rout_eff) ~ (gm4/2)(1+cm)/(2 pi CL)
#   PM = 90 - atan(GBW/f_n2) - atan(GBW/f_p2);  P = VDD I_tail
#   Balance: I_tail(t) = 2 I_P + dI;  x1 - vout = -dI R_left
#
#   Numbers (I = 13.1 uA, W = 0.77 um, NM4 slack 70 mV):
#     gm4 90.76u, gm3n 218.1u(+15% body), gm3p 138.2u(+23% body), gds2 8.50u
#     ro4 159 k (lambda .477 @ s .070), ro3n 488 k, ro2 274 k, ro3p 306 k
#     Rn 20.3 M, Rp 14.7 M, Rout 8.54 M
#     A_dm = 45.38u*8.54M = 387.7 ; A_cm = 45.38u/22.4*14.74M = 29.9
#     A = 417.6 = 52.42 dB model ; +0.75 dB (half the round-2 model bias)
#       -> predicted 53.17 dB (window 49..55)
#     GBW = 0.389 MHz ; f_n2 1.12 GHz, f_p2 0.65 GHz -> PM 89.9 deg
#     P = 1.8 * 26.10u = 47.0 uW
#
# (5) DC bias verification (vcm 1.2501, vout 1.2498)
#   NM2: Vds 0.2952 >= Vov 0.182  (slack 0.113, measured point, unchanged)
#   NM4: Vds 0.3346 >= Vov 0.2646 (slack 0.070); NM1 same, slack 0.0697
#   NM3: Vds 1.2498-0.6298 = 0.6200 >= Vov 0.0530 (slack 0.567)
#   PM3: Vsd 1.533-1.2498 = 0.2832 >= Vov 0.136 (slack 0.147)
#   PM2/PM0: Vsd 0.267 >= Vov 0.138 (slack 0.129, V1/V2 unchanged)
#   Left branch: dI = +24.1 nA put through Rout 8.54 M -> x1 = 1.2498 -
#     0.2057 = 1.044 V: NM0 Vds 1.044-0.630 = 0.414 >= 0.053 (slack 0.361),
#     PM1 Vsd 1.533-1.044 = 0.489 >= 0.136 (slack 0.353). x1 centred; it
#     tolerates +-0.36 V = +-42 nA of imbalance (= +-5 mV of tail error).
#
# (6) DC operating-point consistency (each node from its driving device)
#   tail: measured-state I_tail(0.2953) = 2 I_P2 + 3.56u*7mV = 2 I_P2 + 24.97nA
#     want 2 I_P2 + 24.08 nA -> t = 0.2953 + (24.08-24.97)nA/8.50uS = 0.2952
#   Vth4 = 0.690 + 0.39(sqrt(1.0952)-sqrt(1.0953)) = 0.6900
#   Vov4: Vds4 0.594 -> 0.3346, s .338 -> .070, lambda-integral
#     dlnI = 0.641(0.07(-0.259) + 0.0475 ln(.070/.338)) = -0.0596
#     -> Vov4 = 0.256 + 0.0596*13.1/90.76 = 0.2646
#   vout = t + Vth4 + Vov4 = 0.2952+0.6900+0.2646 = 1.2498;
#   vcm = vout + dI/gm4 = 1.2498 + 0.0003 = 1.2501
#   n2 = t + Vds4 = 0.2952 + 0.3346 = 0.6298
#   Vth3 = 0.798 + 0.39(sqrt(1.4298)-sqrt(1.6893)) = 0.7574;
#   Vov3: Vds3 .351 -> .620, dlnI = +0.050 -> 0.056 - 0.050*0.060 = 0.0530
#   V3 = 1.7429 + (0.6298+0.7574+0.0530) - (0.8893+0.798+0.056) = 1.4391 V
#     -> NM3 source = 1.4391 - 0.7574 - 0.0530 = 0.6287 (+1 mV from V3_r3
#        rounding offset) = n2.
#   p2 = 1.8 - 0.267 = 1.533 (V1 0.67062, V2 0.34046 unchanged).
#   Loop: vout = vin2 = 1.2498, I4 = I_P2 = 13.1 uA, I1 = 13.1u + 24 nA,
#     I_tail = 26.10 uA = I1 + I4.
#
# (7) Python code below.
# ============================================================================
import math

VDD_DEFAULT = 1.8
L0 = 0.5e-6
PHI2 = 0.8
GAMMA_N = 0.39
GAMMA_P = 0.467
SHAPE_P = (0.037, 0.0345)
SHAPE_N = (0.070, 0.0475)

# Round-3 inputs (exactly what produced the measured point)
VCM_R3 = 1.2663215657731286
V1_R3 = 0.6706177243903462
V2_R3 = 0.3404573706044404
V3_R3 = 1.7429069198884066
V4_R3 = 0.815
W_R3 = 0.77e-6

# Round-3 measured operating point (SAT devices)
M = {
    "NM2": dict(id=26.1e-6, vov=0.182, vds=0.295, gm=247.9e-6, lam=0.3256, vth=0.633),
    "NM4": dict(id=13.1e-6, vov=0.256, vds=0.594, gm=90.76e-6, lam=0.1349, vth=0.690),
    "NM3": dict(id=13.1e-6, vov=0.056, vds=0.351, gm=218.1e-6, lam=0.2352, vth=0.798),
    "PM2": dict(id=13.1e-6, vov=0.138, vds=0.267, gm=136.2e-6, lam=0.2791, vth=0.992),
    "PM3": dict(id=13.1e-6, vov=0.136, vds=0.292, gm=138.2e-6, lam=0.2377, vth=1.057),
    "PM0": dict(id=13.1e-6, vov=0.138, vds=0.274, gm=136.6e-6, lam=0.2655, vth=0.992),
}
T_M = VCM_R3 - (0.692 + 0.279)            # tail from NM1 (vin1 = vcm): 0.2953
VOUT_M = (T_M + 0.690 + 0.256 + T_M + 0.594 + 0.351 + 1.8 - 0.267 - 0.292) / 3.0


def initial_params():
    n = {"type": "NMOS", "muCox": 270e-6, "a_gm": 1.0, "lam": 0.20, "vth": 0.69}
    p = {"type": "PMOS", "muCox": 100e-6, "a_gm": 1.0, "lam": 0.25, "vth": 1.0}
    out = {}
    for d in ("NM0", "NM1", "NM2", "NM3", "NM4"):
        out[d] = dict(n)
    for d in ("PM0", "PM1", "PM2", "PM3"):
        out[d] = dict(p)
    return out


def _plaus(v, lo, hi, default):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return default
    return v if lo <= v <= hi else default


def _meas(params):
    m = {k: dict(v) for k, v in M.items()}
    for d in m:
        p = params.get(d, {}) if isinstance(params, dict) else {}
        m[d]["lam"] = _plaus(p.get("lam"), 0.02, 0.8, m[d]["lam"])
        m[d]["vth"] = _plaus(p.get("vth"), 0.3, 1.3, m[d]["vth"])
        shape = SHAPE_P if d.startswith("PM") else SHAPE_N
        a, b = shape
        s = m[d]["vds"] - m[d]["vov"]
        m[d]["shape"] = shape
        m[d]["c"] = m[d]["lam"] / (a + b / s)
    return m


def _lam(m, d, vds, vov):
    a, b = m[d]["shape"]
    return m[d]["c"] * (a + b / max(vds - vov, 0.01))


def _dlnI(m, d, vds, vov):
    a, b = m[d]["shape"]
    s = max(vds - vov, 0.01)
    sm = m[d]["vds"] - m[d]["vov"]
    return m[d]["c"] * (a * (vds - m[d]["vds"]) + b * math.log(s / sm))


def _design(m, s4, dI, vdd):
    I = M["NM4"]["id"]
    gm4 = m["NM4"]["gm"]
    # balanced tail from the measured imbalance
    gds_p = 0.5 * (m["PM0"]["lam"] + m["PM2"]["lam"]) * I
    dP = gds_p * (M["PM0"]["vds"] - M["PM2"]["vds"])          # 24.9 nA
    gds2 = m["NM2"]["lam"] * M["NM2"]["id"]
    t = T_M + (dI - dP) / gds2
    eta4 = GAMMA_N / (2 * math.sqrt(PHI2 + t))
    vth4 = m["NM4"]["vth"] + GAMMA_N * (math.sqrt(PHI2 + t) - math.sqrt(PHI2 + T_M))
    vov4 = M["NM4"]["vov"]
    for _ in range(60):
        vds4 = vov4 + s4
        vov4 = M["NM4"]["vov"] - _dlnI(m, "NM4", vds4, vov4) * I / gm4
    vds4 = vov4 + s4
    vov1 = vov4 + dI / gm4
    vcm = t + vth4 + vov1
    vout = t + vth4 + vov4
    n2 = t + vds4
    # NM3 cascode
    vov3 = M["NM3"]["vov"]
    for _ in range(60):
        vds3 = vout - n2
        vov3 = M["NM3"]["vov"] - _dlnI(m, "NM3", vds3, vov3) * I / m["NM3"]["gm"]
    vds3 = vout - n2
    n2_m = VOUT_M - M["NM3"]["vds"]
    vth3 = m["NM3"]["vth"] + GAMMA_N * (math.sqrt(PHI2 + n2) - math.sqrt(PHI2 + n2_m))
    V3 = V3_R3 + (n2 + vth3 + vov3) - (n2_m + m["NM3"]["vth"] + M["NM3"]["vov"])
    # PMOS side unchanged except PM3 Vsd follows vout
    vsd2 = M["PM2"]["vds"]
    p2 = vdd - vsd2
    vsd3 = p2 - vout
    vov2, vov3p = M["PM2"]["vov"], M["PM3"]["vov"]
    # small-signal
    gm3n = m["NM3"]["gm"] * (1 + 0.0 * vov3)
    gmb3n = gm3n * GAMMA_N / (2 * math.sqrt(PHI2 + n2))
    gm3p = m["PM3"]["gm"]
    gmb3p = gm3p * GAMMA_P / (2 * math.sqrt(PHI2 + vsd2))
    ro4 = 1 / (_lam(m, "NM4", vds4, vov4) * I)
    ro3n = 1 / (_lam(m, "NM3", vds3, vov3) * I)
    ro2 = 1 / (_lam(m, "PM2", vsd2, vov2) * I)
    ro3p = 1 / (_lam(m, "PM3", vsd3, vov3p) * I)
    Rn = ro4 + ro3n + (gm3n + gmb3n) * ro3n * ro4
    Rp = ro2 + ro3p + (gm3p + gmb3p) * ro3p * ro2
    Rout = Rn * Rp / (Rn + Rp)
    A_dm = 0.5 * gm4 * Rout
    A_cm = 0.5 * gm4 / (1 + 2 * gm4 / gds2) * Rp
    A = A_dm + A_cm
    # x1 window (NM0 mirrors NM3, PM1 mirrors PM3 when x1 = vout)
    win_dn = vds3 - vov3
    win_up = vsd3 - vov3p
    x1 = vout - dI * Rout
    slack = dict(NM2=t - M["NM2"]["vov"], NM4=vds4 - vov4, NM1=vds4 - vov1,
                 NM3=vds3 - vov3, NM0=(x1 - n2) - vov3,
                 PM3=vsd3 - vov3p, PM1=(p2 - x1) - vov3p, PM2=vsd2 - vov2,
                 PM0=vsd2 - vov2)
    I_tail = M["NM2"]["id"] + gds2 * (t - T_M)
    return dict(t=t, eta4=eta4, vth4=vth4, vov4=vov4, vds4=vds4, vcm=vcm, vout=vout,
                n2=n2, vov3=vov3, vds3=vds3, vth3=vth3, V3=V3, p2=p2, vsd3=vsd3,
                dP=dP, gds2=gds2, ro4=ro4, ro3n=ro3n, ro2=ro2, ro3p=ro3p, Rn=Rn,
                Rp=Rp, Rout=Rout, A_dm=A_dm, A_cm=A_cm, A=A,
                A_dB=20 * math.log10(A), win_dn=win_dn, win_up=win_up, x1=x1,
                slack=slack, I_tail=I_tail, gm3n=gm3n, gm3p=gm3p, gm4=gm4)


GAIN_OFFSET_DB = 0.75     # half of the round-2 measured-vs-model +1.52 dB


def compute_sizing(spec, params):
    target = spec["targets"]["gain_dB"]
    cond = spec.get("conditions", {})
    vdd = cond.get("vdd") or VDD_DEFAULT
    cl = cond.get("cl") or 20e-12
    m = _meas(params or {})
    goal = target - GAIN_OFFSET_DB
    best = None
    for k in range(0, 60):
        s4 = 0.07 + 0.005 * k            # NM4 slack 70 ... 365 mV (floor: NM1 sat margin)
        d = _design(m, s4, 0.0, vdd)
        # centre x1 in its window: x1 - vout = (win_up - win_dn)/2
        dI = (d["win_dn"] - d["win_up"]) / (2 * d["Rout"])
        d = _design(m, s4, dI, vdd)
        key = abs(d["A_dB"] - goal)
        if best is None or key < best[0]:
            best = (key, s4, dI, d)
    _, s4, dI, d = best

    gbw = d["A"] / (2 * math.pi * cl * d["Rout"])
    cox = 8.5e-3
    c_n2 = (2 / 3) * 6e-6 * L0 * cox + 1e-9 * (6e-6 + W_R3) * 2 + 0.5e-15 * W_R3 * 1e6
    c_p2 = (2 / 3) * 7e-6 * L0 * cox + 2e-9 * 7e-6
    f_n2 = d["gm3n"] / (2 * math.pi * c_n2)
    f_p2 = d["gm3p"] / (2 * math.pi * c_p2)
    pm = 90 - math.degrees(math.atan(gbw / f_n2)) - math.degrees(math.atan(gbw / f_p2))
    compute_sizing.debug = dict(s4=s4, dI=dI, f_n2=f_n2, f_p2=f_p2, **d)
    return {
        "sizes": {"NM1": {"w": W_R3, "l": L0, "m": 1},
                  "NM4": {"w": W_R3, "l": L0, "m": 1}},
        "biases": {"V1": V1_R3, "V2": V2_R3, "V3": d["V3"], "V4": V4_R3},
        "currents": {},
        "caps": {},
        "vcm": d["vcm"],
        "predicted": {"gain_dB": d["A_dB"] + GAIN_OFFSET_DB, "gbw_Hz": gbw,
                      "pm_deg": pm, "power_W": vdd * d["I_tail"]},
    }


if __name__ == "__main__":
    spec = {"targets": {"gain_dB": 52.0}, "conditions": {"vdd": 1.8, "cl": 2e-11}}
    cal = {
        "NM0": dict(type="NMOS", muCox=8.688e-6, a_gm=0.467, lam=117.1, vth=0.733),
        "NM1": dict(type="NMOS", muCox=217.4e-6, a_gm=0.769, lam=1.791, vth=0.692),
        "NM2": dict(type="NMOS", muCox=262.4e-6, a_gm=0.864, lam=0.3256, vth=0.633),
        "NM3": dict(type="NMOS", muCox=705e-6, a_gm=0.464, lam=0.2352, vth=0.798),
        "NM4": dict(type="NMOS", muCox=259.1e-6, a_gm=0.889, lam=0.1349, vth=0.690),
        "PM0": dict(type="PMOS", muCox=98.76e-6, a_gm=0.718, lam=0.2655, vth=0.992),
        "PM1": dict(type="PMOS", muCox=109.7e-6, a_gm=0.712, lam=0.08576, vth=1.056),
        "PM2": dict(type="PMOS", muCox=98.62e-6, a_gm=0.717, lam=0.2791, vth=0.992),
        "PM3": dict(type="PMOS", muCox=100.8e-6, a_gm=0.720, lam=0.2377, vth=1.057),
    }
    r = compute_sizing(spec, cal)
    print(r)
    for k, v in compute_sizing.debug.items():
        print(k, v)
