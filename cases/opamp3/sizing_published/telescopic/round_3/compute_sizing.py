# ============================================================================
# Telescopic cascode (Fig. 2), round 3.
#
# Round-2 post-mortem. Output branch all SAT; measured 63.02 dB vs 52.0
# predicted (under-predicted by 11 dB). Main cause: round 2 used the PM2
# lambda (0.495) for PM3 too; PM3 actually measured 0.1316 at Vsd 0.501, so
# Rp was 4.3 M in the model but ~18 M in silicon. Left branch: PM2 sourced
# 13.4 uA (Vsd 230) while the tail sank 26.0 uA (Vds 291), so NM1 got 12.6 and
# x1 rose until PM0/PM1 went TRIODE (imbalance 0.8 uA, 3 %).
# Model re-check on the round-2 point using the measured gm/lambda of every
# output-branch device gives 61.50 dB -> Y = 61.50 - 63.02 = -1.52 dB, so the
# design goal in the model is 52 - 1.52 = 50.48 dB.
# Lambda depends strongly on slack s = Vds - Vov, measured:
#   PMOS: s .365 -> .1316, s .089 -> .4244, s .072 -> .495, s .020 -> 1.61
#     fit lambda = 0.037 + 0.0345/s (reproduces all four within 10 %)
#   NMOS: s .822 -> .1278, s .318 -> .2194 : lambda = 0.070 + 0.0475/s,
#     scaled per device to its own measured row (NM4 x0.863, NM2 x0.664).
#   Current vs Vds is the integral: I ~ exp(c(a Vds + b ln s)).
# NMOS strong-inversion k from NM4 (EKV k 297u at veff .102) and NM2 (248u at
# veff .187): k = k0/(1+theta veff), k0 = 390 uA/V2, theta = 3.07 /V.
#
# (1) Device roles
#   NM2 tail sink (V4). NM1/NM4 input pair (NM4 = vin2, inverting, drives
#   vout). NM0/NM3 NMOS cascodes (V3). PM1/PM3 PMOS cascodes (V2). PM0/PM2
#   PMOS loads (V1). Left branch x1 mirrors the output branch.
#
# (2) Device constraints / classification
#   NM1: INDEPENDENT, L 0.5 um, m 1; W from the gain equation with the
#        theta-EKV model: W/L = 2 I (1+theta veff)/(k0 veff^2).
#   NM4: MATCHED to NM1.
#   Currents: V4 kept at 0.815 V with the tail kept at Vds 0.291 -> I_tail =
#   26.0 uA exactly as measured; I per side = 13.0 uA; V1 re-trimmed so the
#   PMOS load sources 13.0 (not 13.4) uA -> 2 I_P = I_tail (fixes PM0/PM1).
#
# (3) Signal path
#   vin2 -> NM4 (gm4/2) -> n2 (1/gm3n) -> NM3 -> vout (Rout || CL);
#   PM3/PM2 cascode load. Non-dominant poles at n2 and p2 (~GHz).
#
# (4) Design equations (symbolic)
#   gm = gm_meas * (gm/Id_EKV(Vov)/gm/Id_EKV(Vov_meas)) * I/I_meas
#   ro = 1/(lambda(s) I)
#   Rn = ro4 + ro3n + gm3n (1+eta_n) ro3n ro4 ; Rp = ro2 + ro3p + gm3p (1+eta_p) ro3p ro2
#   A = (gm4/2)(Rn||Rp) ; GBW = (gm4/2)/(2 pi CL)
#   PM = 90 - atan(GBW/f_n2) - atan(GBW/f_p2) ; P = VDD I_tail
#   Gain is lowered 11 dB two ways: (a) W1 4.31 -> 0.77 um puts NM4 in strong
#   inversion (Vov 84 -> 281 mV, gm/Id 14.7 -> 5.9) and (b) the higher vcm
#   this needs squeezes the PMOS stack to equal slack 0.130 V, raising PM3
#   lambda .13 -> .30 and PM2 .42 -> .30 (Rp 18 M -> 11.4 M).
#   Numbers (I = 13.0 uA, W1 = 0.77 um):
#     gm4 = 77.3 uS, gm3n = 216.6 uS, gm3p = 137.8 uS
#     ro4 = 407 k, ro3n = 351 k, ro2 = 254 k, ro3p = 253 k
#     Rn = 36.4 M, Rp = 11.4 M, Rout = 8.67 M
#     A = 38.7u * 8.67 M = 335 = 50.51 dB (model) -> expected 50.51+1.52 = 52.03 dB
#     GBW = 38.7u/(2 pi 20p) = 0.308 MHz ; f_n2 1.11 GHz, f_p2 0.65 GHz
#     PM = 89.96 deg ; P = 1.8 * 26.0u = 46.8 uW
#
# (5) DC bias verification (vcm = vout = 1.266 V)
#   NM2: Vds = 0.291        >= Vov 0.182 (slack 0.109)
#   NM4: Vds = 0.891 - 0.291 = 0.600 >= Vov 0.281 (slack 0.319)
#   NM3: Vds = 1.266 - 0.891 = 0.375 >= Vov 0.056 (slack 0.319)
#   PM3: Vsd = 1.533 - 1.266 = 0.267 >= Vov 0.137 (slack 0.130)
#   PM2: Vsd = 1.800 - 1.533 = 0.267 >= Vov 0.137 (slack 0.130)
#   Left branch: same gates, vin1 = vcm, I1 = 26.0 - 13.0 = 13.0 uA = PM0
#   current, so x1 sits at the vout point: NM0 Vds .375, PM1 Vsd .267.
#
# (6) DC operating-point consistency (each node from its driving device)
#   tail: vcm - Vth4 - Vov4 = 1.2663 - 0.694 - 0.2813 = 0.291 V (NM4 Vsb is
#     the anchor's 0.291, so Vth4 = 0.694 unchanged). NM2 at V4 0.815,
#     Vds 0.291 = measured point -> 26.0 uA.
#   n2: NMOS slack split equal: vcm - tail = 0.975 = Vds4 + Vds3n
#     -> Vds4 = 0.281 + 0.319 = 0.600 -> n2 = 0.291 + 0.600 = 0.891
#     Vth3n = 0.765 + 0.39(sqrt(1.691) - sqrt(1.494)) = 0.795
#     V3 = 0.891 + 0.795 + 0.056 = 1.743 V -> NM3 source = 1.743-0.795-0.056 = 0.891.
#   p2: PMOS slack split equal: 1.8 - 1.266 = 0.534 = 2*0.130 + 0.137 + 0.137
#     -> Vsd2 = 0.267, p2 = 1.533.
#   V1: PM2 at 13.0 uA, Vsd 0.267: from anchor (13.4 uA, Vov .1411, Vsd .230)
#     lambda-integral factor +1.4 %, current ratio 0.970 -> Vov2 = 0.1374
#     V1 = 1.8 - 0.992 - 0.1374 = 0.6706 V.
#   V2: Vth3p = 1.047 + 0.467(sqrt(1.067) - sqrt(1.030)) = 1.0554,
#     Vov3 at 13.0 uA, Vsd 0.267 = 0.1372
#     V2 = 1.533 - 1.0554 - 0.1372 = 0.3405 V -> PM3 source 1.533 V.
#   Loop: vout = vin2 = vcm = 1.266; I4 = I_P = 13.0 = I_tail/2 = I1.
#
# (7) Python code below.
# ============================================================================
import math

VDD_DEFAULT = 1.8
L0 = 0.5e-6
TWO_N_UT = 0.0698
PHI2 = 0.8
GAMMA_N = 0.39
GAMMA_P = 0.467
MEASURED_GAIN_R2 = 63.020474

# lambda(s) = c * (a + b/s), s = Vds - Vov (fitted to the measured rows)
SHAPE_P = (0.037, 0.0345)   # PM3 s=.365 -> .1316, PM2 s=.089 -> .4244, PM0 s=.020 -> 1.61
SHAPE_N = (0.070, 0.0475)   # NM0 s=.822 -> .1278, NM3 s=.318 -> .2194

# Round-2 measured SAT operating points (anchors)
A = {
    "NM2": dict(id=26.0e-6, vov=0.182, vds=0.291, vth=0.633, gm=247.1e-6, wl=6.0),
    "NM4": dict(id=13.4e-6, vov=0.084, vds=0.403, vth=0.694, gm=197.6e-6, wl=4.31 / 0.5, vsb=0.291),
    "NM3": dict(id=13.4e-6, vov=0.058, vds=0.376, vth=0.765, gm=221.7e-6, vsb=0.694),
    "PM2": dict(id=13.4e-6, vov=0.14114, vds=0.230, vth=0.992, gm=136.6e-6),
    "PM3": dict(id=13.4e-6, vov=0.136, vds=0.501, vth=1.047, gm=142.7e-6, vsb=0.230),
}
V4_R2 = 0.815          # produced 26.0 uA at tail Vds 0.291
TAIL = 0.291


def initial_params():
    n = {"type": "NMOS", "muCox": 270e-6, "a_gm": 1.0, "lam": 0.40, "vth": 0.55}
    p = {"type": "PMOS", "muCox": 60e-6, "a_gm": 1.0, "lam": 0.40, "vth": 0.95}
    out = {}
    for d in ("NM0", "NM1", "NM2", "NM3", "NM4"):
        out[d] = dict(n)
    for d in ("PM0", "PM1", "PM2", "PM3"):
        out[d] = dict(p)
    return out


def _veff(vov):
    x = vov / TWO_N_UT
    return vov if x > 40 else TWO_N_UT * math.log1p(math.exp(x))


def _vov_from_veff(ve):
    y = ve / TWO_N_UT
    return ve if y > 40 else TWO_N_UT * math.log(math.expm1(y))


def _sig(vov):
    x = vov / TWO_N_UT
    return 1.0 if x > 40 else 1.0 / (1.0 + math.exp(-x))


def _plaus(v, lo, hi, default):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return default
    return v if lo <= v <= hi else default


def _anchors(params):
    """Refresh anchor lambda/vth from the calibrated params when plausible."""
    an = {k: dict(v) for k, v in A.items()}
    for d in an:
        p = params.get(d, {}) if isinstance(params, dict) else {}
        an[d]["lam"] = _plaus(p.get("lam"), 0.02, 0.8, {"NM2": 0.3359, "NM4": 0.189, "NM3": 0.2194,
                                                          "PM2": 0.4244, "PM3": 0.1316}[d])
        an[d]["vth"] = _plaus(p.get("vth"), 0.3, 1.3, an[d]["vth"])
    for d, shape in (("NM2", SHAPE_N), ("NM4", SHAPE_N), ("NM3", SHAPE_N),
                     ("PM2", SHAPE_P), ("PM3", SHAPE_P)):
        a, b = shape
        s = an[d]["vds"] - an[d]["vov"]
        an[d]["c"] = an[d]["lam"] / (a + b / s)
        an[d]["shape"] = shape
    # NMOS mobility degradation: k(veff) = k0/(1+theta veff) from NM4 and NM2
    k4 = 2 * an["NM4"]["id"] / (an["NM4"]["wl"] * _veff(an["NM4"]["vov"]) ** 2)
    k2 = 2 * an["NM2"]["id"] / (an["NM2"]["wl"] * _veff(an["NM2"]["vov"]) ** 2)
    v4, v2 = _veff(an["NM4"]["vov"]), _veff(an["NM2"]["vov"])
    theta = (k4 / k2 - 1) / (v2 - (k4 / k2) * v4)
    theta = min(max(theta, 0.0), 5.0)
    an["theta"] = theta
    an["k0"] = k4 * (1 + theta * v4)
    return an


def _lam(an, d, vds, vov):
    a, b = an[d]["shape"]
    s = max(vds - vov, 0.005)
    return an[d]["c"] * (a + b / s)


def _ifac(an, d, vds, vov):
    """current factor vs anchor from integrated lambda(s) at fixed Vov."""
    a, b = an[d]["shape"]
    s = max(vds - vov, 0.005)
    sa = an[d]["vds"] - an[d]["vov"]
    return math.exp(an[d]["c"] * (a * (vds - an[d]["vds"]) + b * math.log(s / sa)))


def _gmid_ekv(vov, theta=0.0):
    ve = _veff(vov)
    return _sig(vov) * (2 / ve - theta / (1 + theta * ve))


def _vov_for(an, d, I, vds):
    """Vov carrying I at vds, scaled from anchor (EKV + lambda integral)."""
    vov = an[d]["vov"]
    for _ in range(40):
        f = _ifac(an, d, vds, vov)
        ve = _veff(an[d]["vov"]) * math.sqrt(I / (an[d]["id"] * f))
        vov = 0.5 * vov + 0.5 * _vov_from_veff(ve)
    return vov


def _gm(an, d, I, vov, theta=0.0):
    ga = an[d]["gm"] / an[d]["id"]
    return ga * _gmid_ekv(vov, theta) / _gmid_ekv(an[d]["vov"], theta) * I


def _vov4(an, I, wl, vds):
    th, k0 = an["theta"], an["k0"]
    vov = 0.1
    for _ in range(60):
        f = _ifac(an, "NM4", vds, vov)
        # I = 0.5 k0/(1+th ve) wl ve^2 f  -> solve for ve
        target = 2 * I / (k0 * wl * f)
        ve = math.sqrt(target)
        for _ in range(30):
            ve = math.sqrt(target * (1 + th * ve))
        vov = 0.5 * vov + 0.5 * _vov_from_veff(ve)
    return vov


def _gain(an, I, gm4, vov4, vds4, vov3n, vds3n, n2, vov2, vsd2, vov3, vsd3):
    gm3n = _gm(an, "NM3", I, vov3n)
    gm3p = _gm(an, "PM3", I, vov3)
    ro4 = 1 / (_lam(an, "NM4", vds4, vov4) * I)
    ro3n = 1 / (_lam(an, "NM3", vds3n, vov3n) * I)
    ro2 = 1 / (_lam(an, "PM2", vsd2, vov2) * I)
    ro3p = 1 / (_lam(an, "PM3", vsd3, vov3) * I)
    eta_n = GAMMA_N / (2 * math.sqrt(PHI2 + n2))
    eta_p = GAMMA_P / (2 * math.sqrt(PHI2 + vsd2))
    Rn = ro4 + ro3n + gm3n * (1 + eta_n) * ro3n * ro4
    Rp = ro2 + ro3p + gm3p * (1 + eta_p) * ro3p * ro2
    Rout = Rn * Rp / (Rn + Rp)
    Av = 0.5 * gm4 * Rout
    return dict(gm3n=gm3n, gm3p=gm3p, ro4=ro4, ro3n=ro3n, ro2=ro2, ro3p=ro3p,
                Rn=Rn, Rp=Rp, Rout=Rout, A=Av, A_dB=20 * math.log10(Av))


def _anchor_gain(an):
    a4, a3, p2, p3 = an["NM4"], an["NM3"], an["PM2"], an["PM3"]
    return _gain(an, a4["id"], a4["gm"], a4["vov"], a4["vds"], a3["vov"], a3["vds"],
                 a3["vsb"], p2["vov"], p2["vds"], p3["vov"], p3["vds"])["A_dB"]


def _design(an, I, w1, vdd):
    wl = w1 / L0
    th = an["theta"]
    # NMOS side: tail fixed at the anchor; iterate NM4 Vds
    vds4 = 0.4
    for _ in range(20):
        vov4 = _vov4(an, I, wl, vds4)
        vcm = TAIL + an["NM4"]["vth"] + vov4
        vds3n = 0.4
        for _ in range(20):
            vov3n = _vov_for(an, "NM3", I, vds3n)
            ssum = vcm - TAIL - vov4 - vov3n
            vds4_new = vov4 + ssum / 2
            vds3n = vov3n + ssum / 2
        vds4 = vds4_new
    n2 = TAIL + vds4
    vth3n = an["NM3"]["vth"] + GAMMA_N * (math.sqrt(PHI2 + n2) - math.sqrt(PHI2 + an["NM3"]["vsb"]))
    V3 = n2 + vth3n + vov3n
    # PMOS side: equal slack on PM2 / PM3
    vsd2, vsd3 = 0.23, vdd - 0.23 - vcm
    for _ in range(40):
        vov2 = _vov_for(an, "PM2", I, vsd2)
        vov3 = _vov_for(an, "PM3", I, vsd3)
        ssum = vdd - vcm - vov2 - vov3
        vsd2 = vov2 + ssum / 2
        vsd3 = vov3 + ssum / 2
    p2 = vdd - vsd2
    vth3p = an["PM3"]["vth"] + GAMMA_P * (math.sqrt(PHI2 + vsd2) - math.sqrt(PHI2 + an["PM3"]["vsb"]))
    V2 = p2 - vth3p - vov3
    V1 = vdd - an["PM2"]["vth"] - vov2
    # tail: V4 unchanged (26.0 uA measured at Vds 0.291); I = tail/2
    gm4 = _gm(an, "NM4", I, vov4, th)
    g = _gain(an, I, gm4, vov4, vds4, vov3n, vds3n, n2, vov2, vsd2, vov3, vsd3)
    slack = dict(NM2=TAIL - an["NM2"]["vov"], NM4=vds4 - vov4, NM3=vds3n - vov3n,
                 PM3=vsd3 - vov3, PM2=vsd2 - vov2)
    return dict(I=I, w1=w1, vov4=vov4, vcm=vcm, vds4=vds4, n2=n2, vov3n=vov3n, vds3n=vds3n,
                vth3n=vth3n, vov2=vov2, vsd2=vsd2, p2=p2, vov3=vov3, vsd3=vsd3, vth3p=vth3p,
                gm4=gm4, slack=slack, min_slack=min(slack.values()),
                V1=V1, V2=V2, V3=V3, V4=V4_R2, **g)


def compute_sizing(spec, params):
    target = spec["targets"]["gain_dB"]
    cond = spec.get("conditions", {})
    vdd = cond.get("vdd") or VDD_DEFAULT
    cl = cond.get("cl") or 20e-12
    an = _anchors(params or {})
    Y = _anchor_gain(an) - MEASURED_GAIN_R2      # over-prediction (negative: under)
    goal = target + Y
    I = A["NM2"]["id"] / 2
    best = None
    for j in range(0, 300):
        w1 = 0.42e-6 * (1.01 ** j)
        if w1 > 4.31e-6:
            break
        d = _design(an, I, w1, vdd)
        if d["min_slack"] < 0.07:
            continue
        key = abs(d["A_dB"] - goal)
        if best is None or key < best[0]:
            best = (key, d)
    if best is None:
        d = _design(an, I, 1.0e-6, vdd)
    else:
        d = best[1]
    w1 = round(d["w1"] * 1e8) / 1e8
    d = _design(an, I, w1, vdd)

    gbw = 0.5 * d["gm4"] / (2 * math.pi * cl)
    cox = 8.5e-3
    c_n2 = (2 / 3) * 6e-6 * L0 * cox + 1e-9 * (6e-6 + w1) * 2 + 0.5e-15 * w1 * 1e6
    c_p2 = (2 / 3) * 7e-6 * L0 * cox + 2e-9 * 7e-6
    f_n2 = d["gm3n"] / (2 * math.pi * c_n2)
    f_p2 = d["gm3p"] / (2 * math.pi * c_p2)
    pm = 90 - math.degrees(math.atan(gbw / f_n2)) - math.degrees(math.atan(gbw / f_p2))
    pred_gain = d["A_dB"] - Y                     # expected measured value
    compute_sizing.debug = dict(Y=Y, goal=goal, theta=an["theta"], k0=an["k0"],
                                f_n2=f_n2, f_p2=f_p2, **d)
    return {
        "sizes": {"NM1": {"w": w1, "l": L0, "m": 1},
                  "NM4": {"w": w1, "l": L0, "m": 1}},
        "biases": {"V1": d["V1"], "V2": d["V2"], "V3": d["V3"], "V4": d["V4"]},
        "currents": {},
        "caps": {},
        "vcm": d["vcm"],
        "predicted": {"gain_dB": pred_gain, "gbw_Hz": gbw, "pm_deg": pm,
                      "power_W": vdd * 2 * I},
    }


if __name__ == "__main__":
    spec = {"targets": {"gain_dB": 52.0}, "conditions": {"vdd": 1.8, "cl": 2e-11}}
    cal = {
        "NM0": dict(type="NMOS", muCox=808.4e-6, a_gm=0.433, lam=0.1278, vth=0.765),
        "NM1": dict(type="NMOS", muCox=456.1e-6, a_gm=0.602, lam=0.1864, vth=0.694),
        "NM2": dict(type="NMOS", muCox=262.2e-6, a_gm=0.864, lam=0.3359, vth=0.633),
        "NM3": dict(type="NMOS", muCox=652.5e-6, a_gm=0.484, lam=0.2194, vth=0.765),
        "NM4": dict(type="NMOS", muCox=438.7e-6, a_gm=0.621, lam=0.189, vth=0.694),
        "PM0": dict(type="PMOS", muCox=90.94e-6, a_gm=0.673, lam=1.613, vth=0.992),
        "PM1": dict(type="PMOS", muCox=37.32e-6, a_gm=0.551, lam=12.63, vth=1.033),
        "PM2": dict(type="PMOS", muCox=96.09e-6, a_gm=0.719, lam=0.4244, vth=0.992),
        "PM3": dict(type="PMOS", muCox=103.5e-6, a_gm=0.724, lam=0.1316, vth=1.047),
    }
    r = compute_sizing(spec, cal)
    print(r)
    for k, v in compute_sizing.debug.items():
        print(k, v)
