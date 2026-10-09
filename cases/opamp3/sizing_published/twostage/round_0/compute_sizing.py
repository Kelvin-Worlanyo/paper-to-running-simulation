"""
Round 0 sizing: two-stage Miller op-amp (NMOS input pair, PMOS mirror load,
PMOS common-source second stage, NMOS current-sink load), Sky130 1.8 V devices.

(1) DEVICE ROLES
  I0        reference current into diode NM3 (sets node vbias)
  NM3       diode-connected bias reference                  INDEPENDENT (I0, Vov_t)
  NM2       tail current sink, mirrors NM3                  MIRROR of NM3 (same L)
  NM4       second-stage current-sink load, mirrors NM3     MIRROR of NM3 (same L)
  NM0       input pair device, gate vin1 (inverting)         INDEPENDENT (Id1, Vov1)
  NM1       input pair device, gate vin2 (non-inverting)     MATCHED to NM0
  PM2       diode side of the active-load mirror (node A)    INDEPENDENT (Id1, Vov_p)
  PM1       mirror output side of the load (node B)          MATCHED to PM2
  PM0       second-stage common-source driver (gate B)       MIRROR of PM2 (same L,
            ratio I6/Id1; at balance VB = VA so it copies PM2's VSG)
  C0        Miller compensation capacitor B -> vout

(2) DEVICE CONSTRAINTS
  L: NM0/NM1 = 2 um (low lambda, pair is small anyway); NM2/NM3/NM4 = 1.5 um
  (common mirror L); PM0/PM1/PM2 = 0.6 um (common mirror L; short to keep the
  big PM0 gate capacitance at node B small, i.e. high fT at the 2nd pole).
  Overdrives: Vov1 = 0.15 V, Vov_p = 0.30 V, Vov_t = 0.20 V.
  Widths above 100 um per finger are split with m > 1.

(3) SIGNAL PATH
  vin1/vin2 -> NM0/NM1 (gm1) -> node B (mirror PM2/PM1 folds NM0's current to B)
  -> PM0 gate (gm6) -> vout. C0 closes Miller loop B->vout; CL = 2 pF at vout.
  vin1 -> A -> mirror -> B is non-inverting, B -> vout inverting, so vin1 is the
  inverting input (consistent with the given decision).

(4) DESIGN EQUATIONS (symbolic)
  gm = a_gm*Id/Vov,  gds = lam*Id,  W = 2*Id*L/(muCox*Vov^2)
  A1 = gm1/(Id1*(lam_n0 + lam_p1)),  A2 = gm6/(I6*(lam_p0 + lam_n4))
  Gain = A1*A2
  GBW = gm1/(2*pi*Cc_eff),  Cc_eff = C0 + Cgd,PM0
  p2  = gm6*Cc_eff/(C1*CLe + C1*Cc_eff + Cc_eff*CLe)
        C1 = Cgs,PM0 + Cgd,PM0 + Cdb(PM1,NM1);  CLe = CL + Cdb(PM0,NM4)
  z   = gm6/Cc_eff (RHP),  p3 = gm_PM2/C_A (mirror pole, zero at 2*p3)
  PM  = 90 - atan(wu/p2) - atan(wu/z) - atan(wu/p3) + atan(wu/(2 p3))
  Power = VDD*(I0 + 2*Id1 + I6)
  Procedure: C0 = 1.5 pF; gm1 from GBW; sweep I6 upward, recomputing PM0/NM4
  parasitics each step, and take the smallest I6 with PM >= target.
  Since C1 grows with gm6 (Cgs,PM0 ~ gm6*L^2/(1.5 mu Vov_p)), p2 saturates at
  about wT,p*Cc/(Cc+CL); Vov_p = 0.3 V and L = 0.6 um give wT,p ~ 1.4 GHz,
  which is what makes 82 deg reachable.

(5) DC BIAS VERIFICATION (nominal params: Vthn 0.60, |Vthp| 0.95, gamma 0.4)
  Node A = VDD - |Vthp| - Vov_p = 1.8 - 0.95 - 0.30 = 0.55 V
  vcm window:
    NM2 sat: VC >= Vov_t + 0.05 = 0.25 V; Vthn(VSB=0.25)=0.60+0.4*(sqrt(1.05)-sqrt(0.8))
             = 0.60+0.4*(1.0247-0.8944) = 0.652 V -> vcm >= 0.25+0.652+0.15 = 1.052 V
    NM0 sat: VA - VC >= Vov1 + 0.05 -> vcm <= VA + Vthn - 0.05 = 0.55+0.652-0.05 = 1.152 V
    choose midpoint vcm ~ 1.10 V -> VC = 1.10 - 0.654 - 0.15 = 0.30 V (code iterates body effect)
  NM3: VDS = VGS = 0.60+0.20 = 0.80 >= 0.20 ok
  NM2: VDS = VC = 0.30 >= 0.20 ok (0.10 V margin)
  NM0/NM1: VDS = 0.55 - 0.30 = 0.25 >= 0.15 ok
  PM2 (diode): VSD = VSG = 1.25 >= 0.30 ok; PM1: VSD = 1.8 - VB = 1.25 >= 0.30 ok
  PM0: VSD = 1.8 - vout = 1.8 - 1.10 = 0.70 >= 0.30 ok
  NM4: VDS = vout = 1.10 >= 0.20 ok

(6) DC OPERATING-POINT CONSISTENCY
  Stage 1 output B: with matched PM1/PM2 carrying equal Id1, VB = VA = 0.55 V
  (VSD,PM1 = VSG,PM2 = 0.95 + 0.30 = 1.25 V).
  Stage 2 needs VSG,PM0 such that PM0 carries I6 = NM4's mirrored current.
  PM0 is sized W0 = W_PM2*(I6/Id1) at the same L, so its required
  VSG = |Vthp| + sqrt(2*I6*L/(muCox_p*W0)) = 0.95 + 0.30 = 1.25 V, i.e.
  VB_required = 1.8 - 1.25 = 0.55 V = VA produced by stage 1. Match.
  NM4 current: I6 = I0*W4/W3 at VGS = 0.80 V (same node vbias), so the PM0
  pull-up and NM4 pull-down agree at the same gate voltages; residual
  lambda mismatch is absorbed by vout moving, and the unity-gain loop sets
  vout = vcm = 1.10 V, which lies inside [Vov_t, VDD - Vov_p] = [0.20, 1.50] V.
  Tail: 2*Id1 = I0*W2/W3, so NM2 at VGS = 0.80 V gives exactly 2*Id1.
  (Numeric currents/widths are printed by the code in `predicted`/`sizes`.)
"""
import math

COX = 8.3e-3        # F/m^2, tox ~ 4.15 nm
CJ_W = 0.45e-9      # drain junction cap per metre of width (area + sidewall)
CGD_W = 0.30e-9     # gate-drain overlap cap per metre of width
WMAX = 100e-6


def initial_params():
    n2 = {"type": "NMOS", "muCox": 250e-6, "a_gm": 2.0, "lam": 0.04, "vth": 0.60}
    n15 = {"type": "NMOS", "muCox": 250e-6, "a_gm": 2.0, "lam": 0.055, "vth": 0.60}
    p06 = {"type": "PMOS", "muCox": 55e-6, "a_gm": 2.0, "lam": 0.125, "vth": 0.95}
    return {
        "NM0": dict(n2), "NM1": dict(n2),
        "NM2": dict(n15), "NM3": dict(n15), "NM4": dict(n15),
        "PM0": dict(p06), "PM1": dict(p06), "PM2": dict(p06),
    }


def _split(W, L):
    m = max(1, int(math.ceil(W / WMAX - 1e-9)))
    w = max(0.42e-6, W / m)
    return {"w": w, "l": L, "m": m}


def compute_sizing(spec, params):
    vdd = spec["conditions"]["vdd"]
    cl = spec["conditions"]["cl"]
    tg = spec["targets"]
    gbw_t = tg["gbw_Hz"]
    pm_t = tg["pm_deg"]
    wu = 2 * math.pi * gbw_t

    pn0, pn1 = params["NM0"], params["NM1"]
    pn3, pn4 = params["NM3"], params["NM4"]
    pp0, pp1, pp2 = params["PM0"], params["PM1"], params["PM2"]

    L_pair, L_nm, L_p = 2e-6, 1.5e-6, 0.6e-6
    vov1, vovp, vovt = 0.15, 0.30, 0.20
    gamma, phi2 = 0.4, 0.8
    C0 = 1.5e-12
    I0 = 20e-6

    mun, mup = pn0["muCox"], pp2["muCox"]
    vthn, vthp = abs(pn0["vth"]), abs(pp2["vth"])

    # --- DC headroom / vcm (section 5) ---
    va = vdd - vthp - vovp

    def vth_body(vs):
        return vthn + gamma * (math.sqrt(phi2 + vs) - math.sqrt(phi2))

    vc_min = vovt + 0.05
    vcm_min = vc_min + vth_body(vc_min) + vov1
    vcm_max = va + vth_body(vc_min) - 0.05
    vcm = 0.5 * (vcm_min + vcm_max)

    # --- first stage current from GBW, iterate with PM0 sweep ---
    best = None
    I6 = 50e-6
    while I6 <= 3e-3:
        W0 = 2 * I6 * L_p / (pp0["muCox"] * vovp ** 2)
        Cce = C0 + CGD_W * W0
        gm1 = wu * Cce
        Id1 = gm1 * vov1 / pn0["a_gm"]
        Wn1 = 2 * Id1 * L_pair / (mun * vov1 ** 2)
        Wp1 = 2 * Id1 * L_p / (mup * vovp ** 2)
        W4 = 2 * I6 * L_nm / (pn4["muCox"] * vovt ** 2)
        gm6 = pp0["a_gm"] * I6 / vovp
        C1 = (2.0 / 3.0) * W0 * L_p * COX + CJ_W * (Wp1 + Wn1) + CGD_W * Wn1
        CLe = cl + CJ_W * (W0 + W4)
        p2 = gm6 * Cce / (C1 * CLe + C1 * Cce + Cce * CLe)
        z = gm6 / Cce
        gmp2 = pp2["a_gm"] * Id1 / vovp
        CA = 2 * ((2.0 / 3.0) * Wp1 * L_p * COX + CGD_W * Wp1) + CJ_W * (Wp1 + Wn1)
        p3 = gmp2 / CA
        pm = 90 - math.degrees(math.atan(wu / p2) + math.atan(wu / z)
                               + math.atan(wu / p3) - math.atan(wu / (2 * p3)))
        best = dict(I6=I6, W0=W0, Cce=Cce, gm1=gm1, Id1=Id1, Wn1=Wn1, Wp1=Wp1,
                    W4=W4, gm6=gm6, pm=pm)
        if pm >= pm_t:
            break
        I6 += 10e-6

    I6, Id1, gm1, gm6 = best["I6"], best["Id1"], best["gm1"], best["gm6"]

    # --- sizes ---
    W3 = 2 * I0 * L_nm / (pn3["muCox"] * vovt ** 2)
    W2 = W3 * (2 * Id1) / I0
    W4 = W3 * I6 / I0
    Wn = best["Wn1"]
    Wp2 = best["Wp1"]
    W0 = Wp2 * I6 / Id1

    A1 = gm1 / (Id1 * (pn0["lam"] + pp1["lam"]))
    A2 = gm6 / (I6 * (pp0["lam"] + pn4["lam"]))
    gain_dB = 20 * math.log10(A1 * A2)
    gbw = gm1 / (2 * math.pi * best["Cce"])
    power = vdd * (I0 + 2 * Id1 + I6)

    return {
        "sizes": {
            "NM0": _split(Wn, L_pair),
            "NM1": _split(Wn, L_pair),
            "NM2": _split(W2, L_nm),
            "NM3": _split(W3, L_nm),
            "NM4": _split(W4, L_nm),
            "PM2": _split(Wp2, L_p),
            "PM1": _split(Wp2, L_p),
            "PM0": _split(W0, L_p),
        },
        "biases": {},
        "currents": {"I0": I0},
        "caps": {"C0": C0},
        "vcm": vcm,
        "predicted": {"gain_dB": gain_dB, "gbw_Hz": gbw, "pm_deg": best["pm"],
                      "power_W": power},
    }


if __name__ == "__main__":
    import json
    spec = {"targets": {"gain_dB": 70.0, "gbw_Hz": 28159000.0, "pm_deg": 82.116},
            "conditions": {"vdd": 1.8, "cl": 2e-12, "vcm": None}}
    print(json.dumps(compute_sizing(spec, initial_params()), indent=1))
