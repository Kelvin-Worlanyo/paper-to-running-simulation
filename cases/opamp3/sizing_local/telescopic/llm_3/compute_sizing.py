# ============================================================================
# Telescopic cascode (Fig. 2), round 3.
# Round-2 feedback: gain +1.1 dB (in tolerance), follower settles, PM0/PM1 in
# triode for the third time (x1 driven high: PMOS loads out-source I(NM2)-I4).
#
# Diagnosis (strategy). x1 has no feedback: x1 - vcm = dI * Rx, with
# dI = I(PM0) + I(PM2) - I(NM2) and Rx ~ Rout. A bias error dV on vbp1 gives
# dI = 2 gmp dV, so the tolerable bias error is window / (2 gmp Rx). Round 2
# ran at I = 6 uA, where Vovp = 0.12 V: 1 mV of Vth error = 1.7 % of current,
# and the x1 window allowed only ~0.6 mV. That is below any fit accuracy, so
# re-deriving lambda conventions (rounds 1-2) cannot fix it.
# Structural change:
#  (a) choose the branch current I to MAXIMISE the tolerable bias error
#      window / (Rx * max(2 gmp, gm2)), not the headroom. Rx ~ I^-1.5 while gm
#      ~ I^0.5, so the tolerance grows ~ window * I until the Vov stack eats the
#      window; near-optimum at ~20 uA (2.3x more tolerant than 6 uA).
#      The gain target is kept by a wider input pair (lower Vov1, higher Gm/I).
#  (b) the x1 window is [lo, hi] with lo = NM0 edge, hi = PM1 edge. Three rounds
#      all erred in the same direction (PMOS strong). Place the nominal x1 at
#      lo + 0.30 * window by weakening vbp1 by dV = (vcm - x1_t)/(2 gmp Rx),
#      giving 70 % of the window to the observed error direction.
#  (c) lambda factors on NM2 and PM2 kept equal (lam_n*Vtail = lam_p*Vsd2)
#      when feasible, so the NM2 : 2*PM2 ratio does not depend on whether the
#      fit already includes (1 + lam V).
# Numbers below use initial_params(); local code re-evaluates with fitted ones.
# m = 0.10 V margin on NM2, NM1/NM4 and PM2.
#
# (1) Device roles
#   NM2 tail sink (vbn0), NM1/NM4 input pair (NM4 at vin2 drives vout), NM0/NM3
#   NMOS cascodes (vbn1), PM1/PM3 PMOS cascodes (vbp2), PM0/PM2 PMOS current
#   loads (vbp1). Output vout; x1 = unloaded left drain, set only by the
#   current balance I(PM0)+I(PM2) = I(NM2).
#
# (2) Device constraints / classification
#   NM1: INDEPENDENT, W = 2 Id L/(muCox Vov1^2) (via gm1 from the gain
#   equation, W = gm1^2 L/(2 muCox Id a_gm^2)). NM4: MATCHED to NM1.
#   L = 0.5u, m = 1 (printed). Fixed: NM2 3u, NM0/NM3 6u, PMOS 7u, all 0.5u.
#   Knob: branch current I (sets all fixed-device overdrives).
#
# (3) Signal path
#   vin2 -> NM4 (Gm ~ gm1/2, NM1 degenerates tail, vin1 AC ground) -> n2
#   (1/gm3) -> NM3 -> vout (Rout || CL). Non-dominant poles at n2 (gm3/Cn2)
#   and p2 (gmp3/Cp2); tail pole-zero doublet ignored.
#
# (4) Design equations
#   Vov2 = sqrt(2*2I/(k_n*6)), Vov3 = sqrt(2I/(k_n*12)), Vovp = sqrt(2I/(k_p*14))
#   ro = 1/(lam I); Rn = ro3+ro4+gm3(1+eta_n)ro3 ro4; Rp = ro3p+ro2p+gmp(1+eta_p)ro3p ro2p
#   Rout = Rn||Rp; gt = lam2*2I; Gm = gm1(gm1+gt)/(2gm1+gt); A = Gm Rout
#   -> gm1^2 + gm1(gt - 2A/Rout) - (A/Rout) gt = 0
#   GBW = Gm/(2 pi CL); PM = 90 - atan(GBW/f_n2) - atan(GBW/f_p2); P = VDD*2I
#   Headroom: t = max(Vov2+m, (Vovp+m)/r), r = lam_n/lam_p; Vsd2 = max(r t, Vovp+m)
#     vcm = t + Vth4 + Vov1;  n1 = n2 = t + Vov1 + m;  p1 = p2 = VDD - Vsd2
#     lo = n2 + Vov3 (NM0 edge), hi = p2 - Vovp (PM1 edge), window = hi - lo
#   Robustness: tol(I) = window / (Rx * max(2 gmp, gm2)), Rx = Rout.
#   Scan I = 3..60 uA with up, down >= 0.05 V, 0.42u <= W1 <= 60u; tol is
#   flat near its peak (0.77 mV at 30 uA), so take the LOWEST I with
#   tol >= 0.9*peak (keeps up-room and Vov1 out of weak inversion).
#   Skew: x1_t = lo + 0.30*window, dVbp1 = +(vcm - x1_t)/(2 gmp Rx).
#   Result (initial params): I = 20 uA, W1 = 5.01 um, Vov1 = 0.122,
#   gm1 = 329 uS, Gm = 168 uS, Rout = 2.36 MOhm, A = 52.0 dB, GBW = 1.34 MHz,
#   f_n2 = 1.47 GHz, f_p2 = 0.86 GHz -> PM ~ 89.9 deg, power = 72 uW;
#   tol = 0.70 mV vs 0.30 mV for the round-2 design at 6 uA (2.3x).
#
# (5) DC bias verification (initial params, I = 20 uA)
#   Vov2 = 0.222, Vov3 = 0.111, Vovp = 0.218, Vth = 0.55, Vov1 = 0.122.
#   t = max(0.222+0.1, (0.218+0.1)/1) = 0.322.  NM2: Vds 0.322 >= 0.222.
#   vcm = 0.322+0.55+0.122 = 0.994.
#   n2 = 0.322+0.122+0.1 = 0.544; NM4 Vds = 0.222 >= 0.122 (slack 0.10).
#   NM3: Vds = 0.994-0.544 = 0.450 >= 0.111.
#   Vsd2 = max(0.322, 0.318) = 0.322; p2 = 1.478; PM2 slack 0.104.
#   PM3: Vsd = 1.478-0.994 = 0.484 >= 0.218 (slack 0.266).
#   x1 window: lo = 0.544+0.111 = 0.655, hi = 1.478-0.218 = 1.260 (0.605 V).
#   x1 target = 0.655+0.3*0.605 = 0.836 -> 0.424 V room up, 0.181 V down.
#   lambda factors: NM2 1+0.4*0.322 = PM2 1+0.4*0.322 = 1.129 (equal).
#
# (6) DC operating-point consistency (each node from its driving device)
#   tail = vcm - Vth4 - Vov1 = 0.994-0.55-0.122 = 0.322 (input follower).
#   vbn0 = Vth2 + Vov2/sqrt(1.129) = 0.55+0.222/1.0625 = 0.759.
#   vbn1 = n2 + Vth3 + Vov3 = 0.544+0.55+0.111 = 1.205 -> NM3 source = n2.
#   vbp2 = p2 - |Vthp3| - Vovp = 1.478-0.95-0.218 = 0.310 -> PM3 source = p2.
#   vbp1 = VDD - |Vthp| - Vovp/sqrt(1.129) + dV = 1.8-0.95-0.2054+0.00018
#        = 0.6448; dV = (0.994-0.836)/(2*183u*2.365M) = 0.18 mV weakens
#        PM0/PM2 by 2*0.18/218 = 0.17 % so nominal x1 sits at 0.836 V.
#   Feedback drives vin2 until I4 = I(PM2) -> vout = vin2 = vcm = 0.994 V.
#
# (7) Python code below.
# ============================================================================
import math

VDD_DEFAULT = 1.8
L0 = 0.5e-6
MARGIN = 0.10
ETA_N, ETA_P = 0.18, 0.17
W1_MAX = 60e-6
X1_FRAC = 0.30  # nominal x1 position inside its window (0 = NM0 edge)

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
    gmp2 = _gm(I, pp2, wl_p)
    gm2 = _gm(2 * I, pn2, wl_n2)
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

    r = pn2["lam"] / pp2["lam"] if pp2["lam"] > 0 else 1.0
    r = min(max(r, 0.4), 2.5)
    t = max(vov2 + MARGIN, (vovp2 + MARGIN) / r)
    vsd2 = max(r * t, vovp2 + MARGIN)
    vcm = t + vth4 + vov1
    n2 = t + vov1 + MARGIN
    p2 = vdd - vsd2
    lo = n2 + vov3
    hi = p2 - vovp3
    up, down = hi - vcm, vcm - lo
    window = hi - lo
    tol = window / (Rout * max(2 * gmp2, gm2))
    return dict(I=I, vdd=vdd, vov2=vov2, vov3=vov3, vovp2=vovp2, vovp3=vovp3,
                gm1=gm1, Gm=Gm, wl1=wl1, vov1=vov1, Rn=Rn, Rp=Rp, Rout=Rout, A=A,
                gm3=gm3, gmp3=gmp3, gmp2=gmp2, gm2=gm2, vth4=vth4, r=r, t=t,
                vsd2=vsd2, vcm=vcm, n2=n2, p2=p2, lo=lo, hi=hi, up=up,
                down=down, window=window, tol=tol)


def compute_sizing(spec, params):
    gain_target = spec["targets"]["gain_dB"]
    cl = spec["conditions"].get("cl") or 20e-12

    fallback = None
    ok = []
    I = 3e-6
    while I <= 60e-6 + 1e-12:
        d = _design(I, spec, params, gain_target)
        w1 = d["wl1"] * L0
        if 0.42e-6 <= w1 <= W1_MAX:
            if fallback is None or min(d["up"], d["down"]) > min(fallback["up"], fallback["down"]):
                fallback = d
            if d["up"] >= 0.05 and d["down"] >= 0.05:
                ok.append(d)
        I += 0.5e-6
    best = None
    if ok:
        # tol is flat near its peak: take the LOWEST current within 90 % of
        # the peak (more up-room, less moderate-inversion error on gm1)
        tmax = max(x["tol"] for x in ok)
        best = min((x for x in ok if x["tol"] >= 0.9 * tmax), key=lambda x: x["I"])
    d = best or fallback or _design(10e-6, spec, params, gain_target)
    I, vdd = d["I"], d["vdd"]
    w1 = min(max(d["wl1"] * L0, 0.42e-6), 100e-6)

    vcm, tail, n2, p2 = d["vcm"], d["t"], d["n2"], d["p2"]
    pn2, pp2 = params["NM2"], params["PM2"]
    vbn1 = n2 + abs(params["NM3"]["vth"]) + d["vov3"]
    vbn0 = abs(pn2["vth"]) + d["vov2"] / math.sqrt(1 + pn2["lam"] * tail)
    vbp2 = p2 - abs(params["PM3"]["vth"]) - d["vovp3"]
    # skew: place nominal x1 at lo + X1_FRAC*window (PMOS slightly weaker)
    x1_t = d["lo"] + X1_FRAC * d["window"]
    dv = (vcm - x1_t) / (2 * d["gmp2"] * d["Rout"])
    dv = max(min(dv, 0.2 * d["vovp2"]), -0.2 * d["vovp2"])
    vbp1 = (vdd - abs(pp2["vth"])
            - d["vovp2"] / math.sqrt(1 + pp2["lam"] * d["vsd2"]) + dv)

    Gm = d["Gm"]
    gbw = Gm / (2 * math.pi * cl)
    cn2 = (2.0 / 3.0) * 6e-6 * L0 * 8.5e-3 + 2 * (6e-6 + w1) * 1e-9
    p_nd = d["gm3"] / (2 * math.pi * cn2)
    cp2 = (2.0 / 3.0) * 7e-6 * L0 * 8.5e-3 + 2 * 7e-6 * 1e-9
    p_pd = d["gmp3"] / (2 * math.pi * cp2)
    pm = 90.0 - math.degrees(math.atan(gbw / p_nd)) - math.degrees(math.atan(gbw / p_pd))

    compute_sizing.debug = dict(I=I, w1=w1, vcm=vcm, tail=tail, n2=n2, p2=p2,
                                lo=d["lo"], hi=d["hi"], x1_t=x1_t, dv=dv,
                                tol_mV=1e3 * d["tol"], r=d["r"],
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
