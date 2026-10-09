# ============================================================================
# Telescopic cascode (Fig. 2), round 2.
#
# Round-1 post-mortem (calibration table). NM2 sank 26.2 uA (Vov 182, Vds 310,
# SAT) but V1 made each PMOS load source 15.7 uA (PM2 SAT, Vov 157, Vsd 229).
# 2 x 15.7 = 31.4 > 26.2, so the output branch took 15.7 uA (loop forces it)
# and the left branch got only 10.5 uA: x1 rose until PM0/PM1 went TRIODE
# (Vsd 85/32 mV). The pair needed Vov4 - Vov1 = 424 - 338 = 86 mV of offset,
# so vout = 0.310 + 0.639 + 0.466 = 1.415 V instead of vcm 1.330 V, which put
# PM3 in TRIODE (Vsd 155 < Vov 166). 26.8 dB is a dead-bias number, so the
# "design for target + Y dB" rule (Y = 33 dB) is NOT applied; the fixes are
# (a) current balance 2*I_P = I_tail and (b) PM3 headroom. The gain model
# is re-derived with the calibrated lambda_p = 0.495 (was an assumed 0.15),
# which alone drops the round-1 prediction by ~10 dB, and then W1 is widened.
#
# Balance sensitivity: x1 has no feedback, so the left branch saturates only
# if |I_P - I_tail/2| < (x1 window/2)/Rout ~ 0.35 V / 3.9 M = 90 nA (0.7 %).
# To get that precision every biased device is placed AT, or scaled by
# current ratio from, an operating point the simulator measured:
#   NM2 kept at Vov 182 mV, Vds 310 mV -> 26.2 uA (V4 = 0.633 + 0.182 = 0.815)
#   PM2/PM0 kept at Vsd 229 mV, only the current scaled 15.7 -> 13.1 uA.
# Model: EKV Id = 0.5 k W/L veff^2, veff = 2nUt ln(1+exp(Vov/2nUt)),
# 2nUt = 69.8 mV; gm/Id = 2 sigmoid(Vov/2nUt)/veff x (measured correction).
#   NMOS moderate inversion anchored to NM3 (Vov 65 mV, 15.7 uA, W/L 12):
#     k_n = 336 uA/V2; EKV gm/Id 16.27 vs measured 0.52*2/0.065 = 16.0 -> x0.984
#   PMOS gm/Id anchored to PM2: measured 9.53 vs EKV 11.03 -> x0.864
#   lambda: NM2 0.293, NM3 0.182, NM4 0.169, PMOS 0.495 (PM2, only SAT PMOS).
#   Vth: NM2 0.633 (Vsb 0), NM4 0.681 (Vsb 0.310), NM3 0.807 (Vsb 0.949),
#        PM2 0.992, PM3 1.048 (Vsb 0.229); gamma_n 0.39.
#
# (1) Device roles
#   NM2 tail sink (V4 = vbn0). NM1/NM4 input pair, NM4 (vin2, inverting)
#   drives the output branch. NM0/NM3 NMOS cascodes (V3 = vbn1). PM1/PM3
#   PMOS cascodes (V2 = vbp2). PM0/PM2 PMOS current-source loads (V1 = vbp1).
#   Left branch x1 is not in the signal path but must stay saturated.
#
# (2) Device constraints / classification
#   NM1: INDEPENDENT, L = 0.5 um, m = 1 (kept printed); W1 from the gain
#        equation: moderate inversion, W/L = 2 I/(k_n veff4^2).
#   NM4: MATCHED to NM1.
#   Fixed: NM2 W/L 6, NM0/NM3 W/L 12, PMOS W/L 14.
#   Currents: I_tail = 26.2 uA, I per side = 13.1 uA (both branches), set by
#   V4 (tail) and V1 (loads) with 2*I_P = I_tail.
#
# (3) Signal path
#   vin2 -> NM4 (gm4/2: vin1 held, tail follows vin2/2 since ro2 = 1/(0.293
#   *26.2u) = 130 k >> 1/gm = 5 k) -> n2 (low Z, 1/gm3) -> NM3 -> vout
#   (Rout || CL). Non-dominant poles at n2 (gm3/C_n2) and p2 (gmp3/C_p2).
#
# (4) Design equations (symbolic)
#   veff_P2 = veff(0.157) sqrt(I/15.7u)         (Vsd 0.229 unchanged)
#   veff_N2 = veff(0.182) sqrt(2I/26.2u)        (Vds 0.310 unchanged)
#   veff_4  = sqrt(2I/(k_n W1/L)),  gm4 = 0.984 * gm/Id(Vov4) * I
#   ro_x = 1/(lambda_x I)
#   Rn = ro4 + ro3 + gm3 (1+eta_n) ro3 ro4 ;  Rp = 2 rop + gmp3 (1+eta_p) rop^2
#   A = (gm4/2)(Rn || Rp) ; GBW = (gm4/2)/(2 pi CL)
#   PM = 90 - atan(GBW/f_n2) - atan(GBW/f_p2) ; P = VDD * I_tail
#   Numbers (I = 13.1 uA, W1 = 4.31 um):
#     Vov4 = 74.4 mV, gm4 = 201.6 uS (gm/Id 15.4)
#     gm3 = 219 uS, gmp3 = 136 uS, ro4 = 451 k, ro3 = 419 k, rop = 154 k
#     Rn = 0.87 M + 219u*1.161*419k*451k = 49.0 M
#     Rp = 0.31 M + 136u*1.23*154k^2    = 4.29 M
#     Rout = 3.95 M ; A = 100.8u * 3.95 M = 398 = 52.0 dB
#     GBW = 100.8u/(2 pi 20p) = 0.80 MHz ; f_n2 = 0.88 GHz, f_p2 = 0.64 GHz
#     -> PM = 89.9 deg ; P = 1.8 * 26.2u = 47.2 uW
#
# (5) DC bias verification (vcm = vout = x1 nominal = 1.065 V)
#   NM2: Vds = tail = 0.310          >= Vov 0.182 (slack 0.128)
#   NM4: Vds = n2 - tail = 0.695 - 0.310 = 0.385 >= Vov 0.074 (slack 0.311)
#   NM3: Vds = vout - n2 = 1.065 - 0.695 = 0.370 >= Vov 0.054 (slack 0.316)
#   PM3: Vsd = p2 - vout = 1.571 - 1.065 = 0.506 >= Vov 0.136 (slack 0.370)
#   PM2: Vsd = 1.8 - p2 = 0.229       >= Vov 0.141 (slack 0.088)
#   Left branch (same gates, vin1 = vcm, same 13.1 uA): n1 = 0.695, p1 = 1.571,
#   x1 saturated anywhere in [0.695+0.054, 1.571-0.136] = [0.749, 1.435] V.
#
# (6) DC operating-point consistency (each node from its driving device)
#   tail (NM4 source): vcm = tail + Vth4 + Vov4 with tail chosen = 0.310
#     (NM2 anchor) -> vcm = 0.310 + 0.681 + 0.0744 = 1.065 V;
#     conversely tail = 1.065 - 0.681 - 0.074 = 0.310 V.
#   V4: NM2 sinks 2I = 26.2 uA at Vds 0.310 = measured point
#     -> V4 = 0.633 + 0.182 = 0.815 V -> I_tail 26.2 uA.
#   V1: PM2 sources 13.1 uA at Vsd 0.229:
#     veff = 0.1640*sqrt(13.1/15.7) = 0.1498 -> Vov 0.1411
#     V1 = 1.8 - 0.992 - 0.141 = 0.667 V. 2 x 13.1 = 26.2 = I_tail (balance).
#   V2: p2 = 1.8 - 0.229 = 1.571. PM3 at Vsd 0.506 (lambda 0.495 from its
#     triode-edge anchor, sat-equivalent 15.9 uA x (1+0.495*0.506)/(1+0.495
#     *0.155) = 18.4 uA at Vov 166) -> Vov3 = 0.136 at 13.1 uA
#     V2 = 1.571 - 1.048 - 0.136 = 0.387 V -> PM3 source = 0.387+1.048+0.136
#     = 1.571 V = the p2 that gives PM2 its 0.229 V.
#   V3: n2 window [tail + veff4 + m = 0.455, vout - veff3 - m = 0.935]
#     -> n2 = 0.695. Vth3 = 0.807 + 0.39(sqrt(1.495) - sqrt(1.749)) = 0.768,
#     Vov3 = 0.054 (NM3 anchor scaled to 13.1 uA)
#     V3 = 0.695 + 0.768 + 0.054 = 1.517 V -> NM3 source = 0.695 V.
#   Loop: vout = vin2 = vcm = 1.065 with I4 = I1 = 13.1 uA, no offset needed.
#
# (7) Python code below.
# ============================================================================
import math

VDD_DEFAULT = 1.8
L0 = 0.5e-6
TWO_N_UT = 0.0698          # 2 n Ut, n = 1.35
UT = 0.02585
PHI2 = 0.8
MARGIN = 0.05

FIXED_WL = {"PM0": 14.0, "PM2": 14.0, "PM1": 14.0, "PM3": 14.0,
            "NM0": 12.0, "NM3": 12.0, "NM2": 6.0}

# Round-1 measured SAT operating points used as anchors (ratio scaling keeps
# every re-biased device close to a point the simulator actually produced).
A_NM2 = dict(id=26.2e-6, vov=0.182, vds=0.310)            # SAT
A_PM2 = dict(id=15.7e-6, vov=0.157, vds=0.229)            # SAT
A_PM3 = dict(id=15.7e-6, vov=0.166, vds=0.155)            # edge of TRIODE
A_NM3 = dict(id=15.7e-6, vov=0.065, vds=0.466, wl=12.0)   # SAT, moderate inversion
A_NM4 = dict(vsb=0.310)                                   # Vth 681 mV measured here


def initial_params():
    n = {"type": "NMOS", "muCox": 270e-6, "a_gm": 1.0, "lam": 0.40, "vth": 0.55}
    p = {"type": "PMOS", "muCox": 60e-6, "a_gm": 1.0, "lam": 0.40, "vth": 0.95}
    out = {}
    for d in ("NM0", "NM1", "NM2", "NM3", "NM4"):
        out[d] = dict(n)
    for d in ("PM0", "PM1", "PM2", "PM3"):
        out[d] = dict(p)
    return out


# ---------------------------------------------------------------- EKV helpers
def _veff(vov):
    x = vov / TWO_N_UT
    return vov if x > 40 else TWO_N_UT * math.log1p(math.exp(x))


def _vov_from_veff(ve):
    y = ve / TWO_N_UT
    return ve if y > 40 else TWO_N_UT * math.log(math.expm1(y))


def _gm_over_id(vov):
    x = vov / TWO_N_UT
    sig = 1.0 if x > 40 else 1.0 / (1.0 + math.exp(-x))
    return 2.0 * sig / _veff(vov)


def _plaus(v, lo, hi, default):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return default
    return v if lo <= v <= hi else default


def _get(params, dev, key, lo, hi, default):
    return _plaus(params.get(dev, {}).get(key), lo, hi, default)


def _model(params):
    M = {}
    M["vth_nm2"] = _get(params, "NM2", "vth", 0.3, 0.9, 0.633)
    M["vth_nm3"] = _get(params, "NM3", "vth", 0.3, 1.1, 0.807)
    M["vth_nm4"] = _get(params, "NM4", "vth", 0.3, 1.0, 0.681)
    M["vth_pm2"] = _get(params, "PM2", "vth", 0.5, 1.3, 0.992)
    M["vth_pm3"] = _get(params, "PM3", "vth", 0.5, 1.3, 1.048)
    M["lam_nm2"] = _get(params, "NM2", "lam", 0.02, 0.6, 0.2933)
    M["lam_nm3"] = _get(params, "NM3", "lam", 0.02, 0.6, 0.182)
    M["lam_nm4"] = _get(params, "NM4", "lam", 0.02, 0.6, 0.1691)
    M["lam_p"] = _get(params, "PM2", "lam", 0.02, 0.8, 0.4952)   # only SAT PMOS row
    # moderate-inversion NMOS k and gm/Id correction from NM3 (Vov 65 mV)
    M["k_n"] = 2 * A_NM3["id"] / (A_NM3["wl"] * _veff(A_NM3["vov"]) ** 2)
    a3 = _get(params, "NM3", "a_gm", 0.1, 1.5, 0.520)
    M["gmc_n"] = (a3 * 2 / A_NM3["vov"]) / _gm_over_id(A_NM3["vov"])
    a2 = _get(params, "PM2", "a_gm", 0.1, 1.5, 0.748)
    M["gmc_p"] = (a2 * 2 / A_PM2["vov"]) / _gm_over_id(A_PM2["vov"])
    M["gamma_n"] = 0.39
    M["gamma_p"] = 0.467   # PM3 1048 vs PM2 992 mV at Vsb 0.229
    return M


def _scale_vov(anchor_vov, ratio):
    """vov that carries ratio x the anchor current at the anchor Vds (EKV)."""
    return _vov_from_veff(_veff(anchor_vov) * math.sqrt(ratio))


# ---------------------------------------------------------------- design
def _design(I, w1, M, vdd):
    wl1 = w1 / L0
    # PMOS loads at the anchor Vsd (0.229 V): only the current changes
    vsd_p2 = A_PM2["vds"]
    p2 = vdd - vsd_p2
    vov_p2 = _scale_vov(A_PM2["vov"], I / A_PM2["id"])
    # tail at the anchor Vds (0.310 V), 2I
    tail = A_NM2["vds"]
    vov_n2 = _scale_vov(A_NM2["vov"], 2 * I / A_NM2["id"])
    # input device (moderate inversion, NM3-anchored k)
    ve4 = math.sqrt(2 * I / (M["k_n"] * wl1))
    vov4 = _vov_from_veff(ve4)
    gm4 = M["gmc_n"] * _gm_over_id(vov4) * I
    vth4 = M["vth_nm4"] + M["gamma_n"] * (math.sqrt(PHI2 + tail) - math.sqrt(PHI2 + A_NM4["vsb"]))
    vcm = tail + vth4 + vov4
    # PMOS cascode PM3: current I at Vsd3 = p2 - vcm (lambda-corrected from
    # its triode-edge anchor)
    vsd3 = p2 - vcm
    ve_a = _veff(A_PM3["vov"])
    vd_a = A_PM3["vds"]
    tri = (2 * ve_a * vd_a - vd_a ** 2) / ve_a ** 2 if vd_a < ve_a else 1.0
    i3_sat_anchor = A_PM3["id"] / tri
    lam = M["lam_p"]
    ratio3 = I / (i3_sat_anchor * (1 + lam * max(vsd3, 0)) / (1 + lam * vd_a))
    vov_p3 = _scale_vov(A_PM3["vov"], ratio3)
    vbp2 = p2 - M["vth_pm3"] - vov_p3
    vbp1 = vdd - M["vth_pm2"] - vov_p2
    vbn0 = M["vth_nm2"] + vov_n2
    # NMOS cascode NM3 at I
    vov_n3 = _scale_vov(A_NM3["vov"], I / A_NM3["id"])
    ve_n3 = _veff(vov_n3)
    ve_4 = _veff(vov4)
    n_lo = tail + max(vov4, ve_4) + MARGIN
    n_hi = vcm - max(vov_n3, ve_n3) - MARGIN
    n2 = 0.5 * (n_lo + n_hi)
    vth3 = M["vth_nm3"] + M["gamma_n"] * (math.sqrt(PHI2 + n2) - math.sqrt(PHI2 + A_NM4["vsb"] + 0.639))
    vbn1 = n2 + vth3 + vov_n3
    # small-signal
    gm_n3 = M["gmc_n"] * _gm_over_id(vov_n3) * I
    gm_p3 = M["gmc_p"] * _gm_over_id(vov_p3) * I
    eta_n = M["gamma_n"] / (2 * math.sqrt(PHI2 + n2))
    eta_p = M["gamma_p"] / (2 * math.sqrt(PHI2 + vsd_p2))
    ro4 = 1 / (M["lam_nm4"] * I)
    ro3 = 1 / (M["lam_nm3"] * I)
    rop = 1 / (lam * I)
    Rn = ro4 + ro3 + gm_n3 * (1 + eta_n) * ro3 * ro4
    Rp = 2 * rop + gm_p3 * (1 + eta_p) * rop * rop
    Rout = Rn * Rp / (Rn + Rp)
    A = 0.5 * gm4 * Rout
    return dict(I=I, w1=w1, p2=p2, tail=tail, vcm=vcm, n2=n2, vsd3=vsd3,
                vov_p2=vov_p2, vov_p3=vov_p3, vov_n2=vov_n2, vov4=vov4, vov_n3=vov_n3,
                vth4=vth4, vth3=vth3, gm4=gm4, gm_n3=gm_n3, gm_p3=gm_p3,
                ro4=ro4, ro3=ro3, rop=rop, Rn=Rn, Rp=Rp, Rout=Rout, A=A,
                A_dB=20 * math.log10(A), n_lo=n_lo, n_hi=n_hi,
                V1=vbp1, V2=vbp2, V3=vbn1, V4=vbn0)


def compute_sizing(spec, params):
    target = spec["targets"]["gain_dB"]
    cond = spec.get("conditions", {})
    vdd = cond.get("vdd") or VDD_DEFAULT
    cl = cond.get("cl") or 20e-12
    M = _model(params)
    I = A_NM2["id"] / 2          # tail kept at its measured 26.2 uA
    best = None
    for j in range(0, 400):
        w1 = 0.42e-6 * (1.01 ** j)
        if w1 > 100e-6:
            break
        d = _design(I, w1, M, vdd)
        if d["n_hi"] - d["n_lo"] < 0.1 or d["vsd3"] < d["vov_p3"] + MARGIN:
            continue
        key = abs(d["A_dB"] - target)
        if best is None or key < best[0]:
            best = (key, d)
    d = best[1]
    w1 = round(d["w1"] * 1e8) / 1e8   # 0.01 um grid
    d = _design(I, w1, M, vdd)

    gbw = 0.5 * d["gm4"] / (2 * math.pi * cl)
    cox = 8.5e-3
    c_n2 = (2 / 3) * 6e-6 * L0 * cox + 1e-9 * (6e-6 + w1) * 2 + 0.5e-15 * w1 * 1e6
    c_p2 = (2 / 3) * 7e-6 * L0 * cox + 2e-9 * 7e-6
    f_n2 = d["gm_n3"] / (2 * math.pi * c_n2)
    f_p2 = d["gm_p3"] / (2 * math.pi * c_p2)
    pm = 90 - math.degrees(math.atan(gbw / f_n2)) - math.degrees(math.atan(gbw / f_p2))
    compute_sizing.debug = dict(M=M, f_n2=f_n2, f_p2=f_p2, **d)
    return {
        "sizes": {"NM1": {"w": w1, "l": L0, "m": 1},
                  "NM4": {"w": w1, "l": L0, "m": 1}},
        "biases": {"V1": d["V1"], "V2": d["V2"], "V3": d["V3"], "V4": d["V4"]},
        "currents": {},
        "caps": {},
        "vcm": d["vcm"],
        "predicted": {"gain_dB": d["A_dB"], "gbw_Hz": gbw, "pm_deg": pm,
                      "power_W": vdd * 2 * I},
    }


if __name__ == "__main__":
    spec = {"targets": {"gain_dB": 52.0}, "conditions": {"vdd": 1.8, "cl": 2e-11}}
    cal = {
        "NM0": dict(type="NMOS", muCox=1137e-6, a_gm=0.349, lam=0.1464, vth=0.810),
        "NM1": dict(type="NMOS", muCox=218.5e-6, a_gm=0.901, lam=0.1487, vth=0.681),
        "NM2": dict(type="NMOS", muCox=263.6e-6, a_gm=0.866, lam=0.2933, vth=0.633),
        "NM3": dict(type="NMOS", muCox=617.9e-6, a_gm=0.520, lam=0.182, vth=0.807),
        "NM4": dict(type="NMOS", muCox=207.3e-6, a_gm=0.880, lam=0.1691, vth=0.681),
        "PM0": dict(type="PMOS", muCox=61.18e-6, a_gm=0.562, lam=8.101, vth=0.993),
        "PM1": dict(type="PMOS", muCox=12.7e-6, a_gm=0.511, lam=29.96, vth=1.014),
        "PM2": dict(type="PMOS", muCox=90.71e-6, a_gm=0.748, lam=0.4952, vth=0.992),
        "PM3": dict(type="PMOS", muCox=81.65e-6, a_gm=0.682, lam=2.378, vth=1.048),
    }
    r = compute_sizing(spec, cal)
    print(r)
    for k, v in compute_sizing.debug.items():
        print(k, v)
