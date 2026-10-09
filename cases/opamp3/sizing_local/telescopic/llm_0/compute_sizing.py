# ============================================================================
# Telescopic cascode (Fig. 2), round 0. Params: NMOS muCox=270u, Vth=0.55,
# lam=0.40; PMOS muCox=60u, |Vth|=0.95, lam=0.40; gamma_n=0.45, gamma_p=0.35,
# 2phiF=0.8. Saturation margin m=0.08 V.
#
# (1) Device roles
#   NM2 tail current sink (gate vbn0). NM1/NM4 input pair (NM4 at vin2 drives
#   vout side). NM0/NM3 NMOS cascodes (vbn1). PM1/PM3 PMOS cascodes (vbp2).
#   PM0/PM2 PMOS current-source loads (vbp1). Output is single-ended at vout;
#   x1 is the unused (symmetric) branch.
#
# (2) Device constraints / classification
#   NM1: INDEPENDENT, W = 2 Id L / (muCox Vov1^2) with Vov1 set by the gain
#   target. NM4: MATCHED to NM1. L = 0.5u, m = 1 (kept printed).
#   Everything else fixed: NM2 3u/0.5u, NM0/NM3 6u/0.5u, PMOS 7u/0.5u.
#   Branch current I is the free design knob (Id each side, 2I in NM2).
#
# (3) Signal path
#   vin2 -> gm4 -> n2 (low-Z, 1/gm3) -> NM3 -> vout (high-Z, Rout || CL).
#   Non-dominant poles at n2 (gm3/C_n2) and p2 (gmp3/C_p2).
#
# (4) Design equations
#   Vov2 = sqrt(2*2I/(k_n*6)), Vov3 = sqrt(2I/(k_n*12)), Vovp = sqrt(2I/(k_p*14))
#   ro = 1/(lam I);  Rn = ro3 + ro4 + gm3 ro3 ro4;  Rp = ro3p + ro2p + gmp ro3p ro2p
#   Rout = Rn || Rp;  A = gm4 Rout  (loop gain, beta = 1)  -> gm4 = A_target/Rout
#   GBW = gm4/(2 pi CL);  PM = 90 - atan(GBW/f_n2) - atan(GBW/f_p2)
#   Power = VDD * 2I
#   Headroom window (vout = vcm in unity feedback):
#     vcm_min = (Vov2+m) + Vth4(body) + Vov1,  vcm_max = VDD - 2 Vovp - 2m
#   I is scanned; the I with the widest window that gives a legal W1 is kept.
#   Result: I = 10 uA, gm4 = 70.5 uS, Vov1 = 0.284 V, W/L1 = 0.92 -> W1 = 0.461u
#   Rn = 16.4 M, Rp = 8.60 M, Rout = 5.64 M, A = 70.5u*5.64M = 398 = 52.0 dB.
#   GBW = 70.5u/(2 pi 20p) = 0.56 MHz; f_n2 ~ 1.35 GHz, f_p2 ~ 0.61 GHz -> PM ~ 90.
#   Power = 1.8 * 20u = 36 uW.
#
# (5) DC bias verification (I = 10 uA, vcm = vout = 1.229 V)
#   Window: vcm_min = 0.237 + 0.607 + 0.284 = 1.126; vcm_max = 1.8 - 0.309 - 0.16
#   = 1.331; vcm = midpoint 1.229.
#   NM2: Vds = tail = 0.321 >= Vov2 0.157   (slack 0.164)
#   NM4: Vds = n2 - tail = 0.878 - 0.321 = 0.556 >= Vov1 0.284 (slack 0.272)
#   NM3: Vds = vout - n2 = 1.229 - 0.878 = 0.351 >= Vov3 0.079 (slack 0.272)
#   PM3: Vsd = p2 - vout = 1.514 - 1.229 = 0.285 >= Vovp 0.154 (slack 0.131)
#   PM2: Vsd = 1.8 - p2 = 0.286 >= Vovp 0.154 (slack 0.132)
#   Left branch (NM1, NM0, PM1, PM0) is identical: vin1 = vcm, x1 nominal = vout.
#
# (6) DC operating-point consistency (each node from its driving device)
#   vbn0 = Vth2 + Vov2/sqrt(1+lam*tail) = 0.55 + 0.157/sqrt(1.129) = 0.698 V
#   tail = vcm - Vth4(Vsb=tail) - Vov1: Vth4 = 0.55 + 0.45(sqrt(1.121)-sqrt(0.8))
#        = 0.624 -> tail = 1.229 - 0.624 - 0.284 = 0.321 V (>= Vov2 + m = 0.237)
#   n2 chosen mid of [tail+Vov1+m = 0.685, vout-Vov3-m = 1.070] = 0.878 V;
#   vbn1 = n2 + Vth3(Vsb=0.878) + Vov3 = 0.878 + 0.730 + 0.079 = 1.687 V
#     -> NM3 source sits at 1.687 - 0.730 - 0.079 = 0.878 V (what NM4 needs).
#   p2 chosen mid of [vout+Vovp+m = 1.463, VDD-Vovp-m = 1.566] = 1.514 V;
#   vbp2 = p2 - |Vthp3|(Vsb=0.286) - Vovp = 1.514 - 1.002 - 0.154 = 0.359 V
#     -> PM3 source sits at 0.359 + 1.002 + 0.154 = 1.514 V.
#   vbp1 = VDD - |Vthp| - Vovp/sqrt(1+lam*0.286) = 1.8 - 0.95 - 0.146 = 0.704 V
#     -> PM2 sources I = 10 uA, matching NM2's 2I = 20 uA split in half.
#   Unity feedback: loop drives vin2 until I4 = I_PM2, i.e. vout = vin2 = vcm =
#   1.229 V, inside the window [1.126, 1.331].
#
# (7) Python code below.
# ============================================================================
import math

VDD_DEFAULT = 1.8
L0 = 0.5e-6
MARGIN = 0.08          # V, saturation margin on every Vds
GAMMA_N, GAMMA_P, PHI2 = 0.45, 0.35, 0.8   # body-effect constants (round-0 guesses)

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


def _vth_body(pr, vsb, gamma):
    vsb = max(vsb, 0.0)
    return abs(pr["vth"]) + gamma * (math.sqrt(PHI2 + vsb) - math.sqrt(PHI2))


def _design(I, spec, params, gain_target):
    vdd = spec["conditions"].get("vdd") or VDD_DEFAULT
    pn2, pn3, pn1 = params["NM2"], params["NM3"], params["NM1"]
    pp0, pp3 = params["PM2"], params["PM3"]
    wl_n2 = FIXED["NM2"][0] / FIXED["NM2"][1]
    wl_n3 = FIXED["NM3"][0] / FIXED["NM3"][1]
    wl_p = FIXED["PM2"][0] / FIXED["PM2"][1]

    vov2 = _vov(2 * I, pn2["muCox"], wl_n2)
    vov3 = _vov(I, pn3["muCox"], wl_n3)
    vovp0 = _vov(I, pp0["muCox"], wl_p)
    vovp3 = _vov(I, pp3["muCox"], wl_p)

    # small-signal
    ro = lambda pr: 1.0 / (pr["lam"] * I)
    gm3 = _gm(I, pn3, wl_n3)
    gmp3 = _gm(I, pp3, wl_p)
    Rn = ro(pn3) + ro(pn1) + gm3 * ro(pn3) * ro(pn1)
    Rp = ro(pp3) + ro(pp0) + gmp3 * ro(pp3) * ro(pp0)
    Rout = Rn * Rp / (Rn + Rp)
    A = 10 ** (gain_target / 20.0)
    gm1 = A / Rout
    wl1 = (gm1 / pn1["a_gm"]) ** 2 / (2 * pn1["muCox"] * I)
    vov1 = _vov(I, pn1["muCox"], wl1)

    # headroom window for vcm (= vout in unity feedback)
    tail_min = vov2 + MARGIN
    vth1_min = _vth_body(pn1, tail_min, GAMMA_N)
    vcm_min = tail_min + vth1_min + vov1
    vcm_max = vdd - vovp0 - vovp3 - 2 * MARGIN
    return dict(I=I, vdd=vdd, vov2=vov2, vov3=vov3, vovp0=vovp0, vovp3=vovp3,
                gm1=gm1, wl1=wl1, vov1=vov1, Rn=Rn, Rp=Rp, Rout=Rout, A=A,
                vcm_min=vcm_min, vcm_max=vcm_max, gm3=gm3, gmp3=gmp3)


def compute_sizing(spec, params):
    gain_target = spec["targets"]["gain_dB"]
    cl = spec["conditions"].get("cl") or 20e-12
    pn1, pn3, pp1, pp0 = params["NM1"], params["NM3"], params["PM3"], params["PM2"]

    # scan branch current; keep the design with the largest vcm window
    best = None
    I = 5e-6
    while I <= 150e-6:
        d = _design(I, spec, params, gain_target)
        w1 = d["wl1"] * L0
        if 0.42e-6 <= w1 <= 100e-6:
            slack = d["vcm_max"] - d["vcm_min"]
            if best is None or slack > best[0]:
                best = (slack, d)
        I += 1e-6
    d = best[1]
    I, vdd = d["I"], d["vdd"]

    w1 = d["wl1"] * L0
    vcm = 0.5 * (d["vcm_min"] + d["vcm_max"])

    # tail node: from input pair Vgs (fixed-point over body effect only)
    tail = vcm - pn1["vth"] - d["vov1"]
    for _ in range(30):
        tail = vcm - _vth_body(pn1, tail, GAMMA_N) - d["vov1"]
    # n2 between input-pair sat edge and cascode sat edge
    n_lo = vcm - _vth_body(pn1, tail, GAMMA_N) + MARGIN   # = tail + vov1 + margin
    n_hi = vcm - d["vov3"] - MARGIN
    n2 = 0.5 * (n_lo + n_hi)
    vbn1 = n2 + _vth_body(pn3, n2, GAMMA_N) + d["vov3"]
    # channel-length-modulation correction so NM2 sinks exactly 2I at Vds = tail
    vbn0 = params["NM2"]["vth"] + d["vov2"] / math.sqrt(1 + params["NM2"]["lam"] * tail)
    # PMOS side
    p_lo = vcm + d["vovp3"] + MARGIN
    p_hi = vdd - d["vovp0"] - MARGIN
    p2 = 0.5 * (p_lo + p_hi)
    vbp2 = p2 - _vth_body(pp1, vdd - p2, GAMMA_P) - d["vovp3"]
    # PM0/PM2 source exactly I at Vsd = vdd - p2 (lambda-corrected)
    vbp1 = vdd - abs(pp0["vth"]) - d["vovp0"] / math.sqrt(1 + pp0["lam"] * (vdd - p2))

    gbw = d["gm1"] / (2 * math.pi * cl)
    # non-dominant pole at n2: gm3 / C(n2); C ~ Cgs3 + junctions, ~ 2fF/um * W
    cn2 = (2.0 / 3.0) * 6e-6 * L0 * 8.5e-3 + 2 * (6e-6 + w1) * 1e-9
    p_nd = d["gm3"] / (2 * math.pi * cn2)
    cp2 = (2.0 / 3.0) * 7e-6 * L0 * 8.5e-3 + 2 * 7e-6 * 1e-9
    p_pd = d["gmp3"] / (2 * math.pi * cp2)
    pm = 90.0 - math.degrees(math.atan(gbw / p_nd)) - math.degrees(math.atan(gbw / p_pd))

    _dbg = dict(I=I, tail=tail, n2=n2, p2=p2, vcm=vcm, vov1=d["vov1"], vov2=d["vov2"],
                vov3=d["vov3"], vovp=d["vovp0"], gm1=d["gm1"], Rn=d["Rn"], Rp=d["Rp"],
                vcm_min=d["vcm_min"], vcm_max=d["vcm_max"], vth1=_vth_body(pn1, tail, GAMMA_N),
                vth3=_vth_body(pn3, n2, GAMMA_N), vthp3=_vth_body(pp1, vdd - p2, GAMMA_P),
                p_nd=p_nd, p_pd=p_pd)
    compute_sizing.debug = _dbg
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
            "gain_dB": 20 * math.log10(d["gm1"] * d["Rout"]),
            "gbw_Hz": gbw,
            "pm_deg": pm,
            "power_W": vdd * 2 * I,
        },
    }


if __name__ == "__main__":
    spec = {"targets": {"gain_dB": 52.0}, "conditions": {"vdd": 1.8, "cl": 2e-11}}
    p = initial_params()
    r = compute_sizing(spec, p)
    print(r)
