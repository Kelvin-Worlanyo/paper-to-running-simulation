"""
Round 1 sizing: two-stage Miller op-amp (NMOS input pair, PMOS mirror load,
PMOS common-source second stage, NMOS current-sink load), Sky130 1.8 V devices.

ROUND-0 DIAGNOSIS (numbers from the calibration table)
  Gain: re-evaluating round 0 with the calibrated table,
    A1 = gm_NM1/(Id*(lam_NM1+lam_PM1)) = 280.3u/(23u*(0.6304+0.0457)) = 18.0
    A2 = gm_PM0/(I6*(lam_PM0+lam_NM4)) = 15.56m/(2.37m*(0.0772+0.0411)) = 55.5
    -> 20log10(999) = 60.0 dB = measured 59.94 dB.  The whole 9.58 dB error is
    lam_NM1 = 0.63 / lam_NM0 = 0.335: the input pair sat only 41 / 76 mV above
    VDsat (Vds 191/225 mV, Vov 150 mV).  Calibrated NMOS lambda vs saturation
    margin m = Vds - Vov:  m=0.041->0.63, 0.076->0.335, 0.125->0.173,
    0.562->0.062, 0.889->0.041, i.e. lam ~= 0.012 + 0.026/m.  So the fix is
    HEADROOM for the pair, not a +9.58 dB gain overdesign (with lam_NM1 = 0.63
    left in place, 79.6 dB would need Vov1 = 21 mV: infeasible).  The gain
    margin applied is therefore the residual after calibration (60.00 - 59.94
    = +0.06 dB): design gain = 70.06 dB.
  GBW: over-predicted 11.6 % -> design for 1.116 * 28.159 MHz = 31.43 MHz
    (a_gm = 0.9 in gm = 2*a_gm*Id/Vov explains it; still inside +25 %).
  PM: over-predicted 1.0 deg -> design for 83.12 deg.

(1) DEVICE ROLES
  I0   reference current into diode NM3 (sets node vbias)
  NM3  diode bias reference                       INDEPENDENT (I0, Vov_t)
  NM2  tail sink                                  MIRROR of NM3 (L = 1.5 um)
  NM4  second-stage sink load                     MIRROR of NM3 (L = 1.5 um)
  NM0  input device, gate vin1 (inverting)        INDEPENDENT (Id1, Vov1)
  NM1  input device, gate vin2                    MATCHED to NM0
  PM2  diode side of active load (node A)         INDEPENDENT (Id1, Vov_p)
  PM1  load output side (node B)                  MATCHED to PM2
  PM0  second-stage CS driver (gate B)            MIRROR of PM2 (L = 0.6 um, x I6/Id1)
  C0   Miller capacitor B -> vout

(2) DEVICE CONSTRAINTS
  L: pair 2 um, NMOS mirrors 1.5 um, PMOS 0.6 um (unchanged from round 0 so the
  calibrated muCox / lambda / Vth stay valid).
  Vov_p = 0.25 V (round-0 actual 0.248: keeps PM0 fT and calibrated lambdas).
  Vov_t 0.20 -> 0.17 V and VC target 0.27 V (NM2 margin 0.10 V) to free 0.06 V
  for the pair.  Vov1 is SOLVED so that the gain meets 70.06 dB (0.126 V).
  Widths > 100 um split into m fingers.

(3) SIGNAL PATH
  vin1 -> NM0 -> A -> PM2/PM1 mirror -> B (non-inverting), B -> PM0 -> vout
  (inverting): vin1 is inverting, as decided.  C0 Miller B->vout, CL at vout.

(4) DESIGN EQUATIONS (symbolic; gm = 2*a_gm*Id/Vov, gds = lam*Id)
  lam_NM1(m) = lam_cal_NM1 * (0.012 + 0.026/m)/(0.012 + 0.026/0.041)
  A1 = 2 a_n/(Vov1*(lam_NM1(m1) + lam_PM1)),  A2 = 2 a_p/(Vov_p*(lam_PM0+lam_NM4))
  Gain = A1*A2
  GBW = gm1/(2 pi Cc_eff), Cc_eff = C0 + Cgd,PM0
  p2 = gm6 Cc/(C1 CLe + C1 Cc + Cc CLe), C1 = Cgs,PM0+Cgd,PM0+Cdb(PM1,NM1)+Cgd,NM1
  CLe = CL + Cdb(PM0,NM4);  z = gm6/Cc;  p3 = gm_PM2/C_A (zero at 2 p3)
  PM = 90 - atan(wu/p2) - atan(wu/z) - atan(wu/p3) + atan(wu/2p3)
  Power = VDD*(I0 + 2 Id1 + I6)
  Procedure: fix Vov_p, Vov_t, VC; solve Vov1 for gain; gm1 from GBW with
  C0 = 3.0 pF; sweep I6 up until PM >= 83.12 deg.  (C0 raised from 1.5 pF:
  with calibrated a_gm the 1.5 pF design could not reach 83.12 deg below 5 mA;
  3 pF lifts p2 ~ wT*Cc/(Cc+CL) and needs I6 = 3.87 mA, Id1 = 44.9 uA.)

(5) DC BIAS VERIFICATION (calibrated: Vthp 0.998, Vthn pair 0.623 at VSB 0.329,
    gamma 0.4, phi 0.8)
  VA = VDD - |Vthp| - Vov_p = 1.8 - 0.998 - 0.25 = 0.552 V
  VB = VA - 0.034 = 0.518 V (round-0 measured PM0/PM2 VSG offset)
  VC = 0.27 V:  Vthn(0.27) = 0.623 + 0.4*(sqrt(1.07) - sqrt(1.129))
                         = 0.623 + 0.4*(1.0344 - 1.0625) = 0.612 V
  NM3: VDS = VGS = 0.562 + 0.17 = 0.732 >= 0.17  ok
  NM2: VDS = 0.27 >= 0.17  ok (margin 0.10)
  NM0: VDS = 0.552 - 0.27 = 0.282 >= Vov1 0.126  ok (margin 0.156)
  NM1: VDS = 0.518 - 0.27 = 0.248 >= 0.126  ok (margin 0.122, lam 0.22 vs 0.63)
  PM2: VSD = VSG = 1.248 >= 0.25 ok;  PM1: VSD = 1.8 - 0.518 = 1.28 >= 0.25 ok
  vcm = VC + Vthn + Vov1 = 0.27 + 0.612 + 0.126 = 1.008 V
  PM0: VSD = 1.8 - 1.008 = 0.792 >= 0.25 ok;  NM4: VDS = 1.008 >= 0.17 ok

(6) DC OPERATING-POINT CONSISTENCY
  Stage 1 produces VB ~= VA = 1.8 - 0.998 - 0.25 = 0.552 V (PM1 matched to PM2
  at equal Id1).  Stage 2 needs VSG,PM0 = |Vthp| + sqrt(2 I6 L/(muCox W0));
  with W0 = W_PM2*I6/Id1 at the same L this is 0.998 + 0.25 = 1.248 V, i.e.
  VB = 1.8 - 1.248 = 0.552 V: equal to what stage 1 produces (round 0 measured
  a 34 mV difference, included above as NM1's VDS loss).
  I6 = I0*W4/W3 at VGS,NM4 = 0.732 V = VGS,NM3; 2 Id1 = I0*W2/W3 likewise.
  Unity-gain loop sets vout = vcm = 1.008 V, inside [Vov_t, VDD - Vov_p]
  = [0.17, 1.55] V.
  Input stage: VC = vcm - Vthn(VC) - Vov1 = 1.008 - 0.612 - 0.126 = 0.27 V, the
  tail's required 0.27 V.  (Exact numbers are computed by the code.)
"""
import math

COX = 8.3e-3        # F/m^2
CJ_W = 0.45e-9      # drain junction cap per metre of width
CGD_W = 0.30e-9     # gate-drain overlap cap per metre of width
WMAX = 100e-6

# round-0 calibration context (margins at which lam was extracted)
M_CAL_NM1 = 0.191 - 0.150
VC_CAL = 0.329
VB_OFFSET = 0.034


def initial_params():
    n2 = {"type": "NMOS", "muCox": 265e-6, "a_gm": 0.90, "lam": 0.63, "vth": 0.623}
    n15 = {"type": "NMOS", "muCox": 258e-6, "a_gm": 0.97, "lam": 0.05, "vth": 0.555}
    p06 = {"type": "PMOS", "muCox": 84e-6, "a_gm": 0.875, "lam": 0.05, "vth": -1.0}
    return {
        "NM0": dict(n2), "NM1": dict(n2),
        "NM2": dict(n15), "NM3": dict(n15), "NM4": dict(n15),
        "PM0": dict(p06), "PM1": dict(p06), "PM2": dict(p06),
    }


def _split(W, L):
    m = max(1, int(math.ceil(W / WMAX - 1e-9)))
    w = max(0.42e-6, W / m)
    return {"w": w, "l": L, "m": m}


def _lam_margin(m):
    return 0.012 + 0.026 / max(m, 0.02)


def compute_sizing(spec, params):
    vdd = spec["conditions"]["vdd"]
    cl = spec["conditions"]["cl"]
    tg = spec["targets"]

    # margin rules
    gain_t = tg["gain_dB"] + (60.0007 - 59.9415)      # residual after calibration
    gbw_t = tg["gbw_Hz"] * 1.116
    pm_t = tg["pm_deg"] + 1.0
    wu = 2 * math.pi * gbw_t

    pn0, pn1 = params["NM0"], params["NM1"]
    pn3, pn4 = params["NM3"], params["NM4"]
    pp0, pp1, pp2 = params["PM0"], params["PM1"], params["PM2"]

    L_pair, L_nm, L_p = 2e-6, 1.5e-6, 0.6e-6
    vovp, vovt = 0.25, 0.17
    vc = 0.27
    gamma, phi2 = 0.4, 0.8
    C0 = 3.0e-12
    I0 = 20e-6

    vthp = abs(pp2["vth"])
    va = vdd - vthp - vovp
    vb = va - VB_OFFSET
    vthn_pair = abs(pn0["vth"]) + gamma * (math.sqrt(phi2 + vc) - math.sqrt(phi2 + VC_CAL))

    lam_ref = _lam_margin(M_CAL_NM1)
    A2 = 2 * pp0["a_gm"] / (vovp * (pp0["lam"] + pn4["lam"]))

    def gain_db(vov1):
        m1 = vb - vc - vov1
        lam1 = pn1["lam"] * _lam_margin(m1) / lam_ref
        A1 = 2 * pn1["a_gm"] / (vov1 * (lam1 + pp1["lam"]))
        return 20 * math.log10(A1 * A2), lam1

    # gain decreases monotonically with Vov1: bisect
    lo, hi = 0.07, vb - vc - 0.03
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if gain_db(mid)[0] > gain_t:
            lo = mid
        else:
            hi = mid
    vov1 = 0.5 * (lo + hi)
    gain_pred, lam1 = gain_db(vov1)
    vcm = vc + vthn_pair + vov1

    mun, mup = pn0["muCox"], pp2["muCox"]
    best = None
    I6 = 100e-6
    while I6 <= 5e-3:
        W0 = 2 * I6 * L_p / (pp0["muCox"] * vovp ** 2)
        Cce = C0 + CGD_W * W0
        gm1 = wu * Cce
        Id1 = gm1 * vov1 / (2 * pn0["a_gm"])
        Wn1 = 2 * Id1 * L_pair / (mun * vov1 ** 2)
        Wp1 = 2 * Id1 * L_p / (mup * vovp ** 2)
        W4 = 2 * I6 * L_nm / (pn4["muCox"] * vovt ** 2)
        gm6 = 2 * pp0["a_gm"] * I6 / vovp
        C1 = (2.0 / 3.0) * W0 * L_p * COX + CJ_W * (Wp1 + Wn1) + CGD_W * Wn1
        CLe = cl + CJ_W * (W0 + W4)
        p2 = gm6 * Cce / (C1 * CLe + C1 * Cce + Cce * CLe)
        z = gm6 / Cce
        gmp2 = 2 * pp2["a_gm"] * Id1 / vovp
        CA = 2 * ((2.0 / 3.0) * Wp1 * L_p * COX + CGD_W * Wp1) + CJ_W * (Wp1 + Wn1)
        p3 = gmp2 / CA
        pm = 90 - math.degrees(math.atan(wu / p2) + math.atan(wu / z)
                               + math.atan(wu / p3) - math.atan(wu / (2 * p3)))
        best = dict(I6=I6, W0=W0, Cce=Cce, gm1=gm1, Id1=Id1, Wn1=Wn1, Wp1=Wp1,
                    W4=W4, pm=pm)
        if pm >= pm_t:
            break
        I6 += 10e-6

    I6, Id1, gm1 = best["I6"], best["Id1"], best["gm1"]

    W3 = 2 * I0 * L_nm / (pn3["muCox"] * vovt ** 2)
    W2 = W3 * (2 * Id1) / I0
    W4 = W3 * I6 / I0
    Wn = best["Wn1"]
    Wp2 = best["Wp1"]
    W0 = Wp2 * I6 / Id1

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
        "predicted": {"gain_dB": gain_pred, "gbw_Hz": gbw, "pm_deg": best["pm"],
                      "power_W": power},
        "debug": {"vov1": vov1, "lam_NM1": lam1, "Id1": Id1, "I6": I6,
                  "vcm": vcm, "va": va, "vthn_pair": vthn_pair},
    }


def _cal_params():
    def d(t, mu, a, lam, vth):
        return {"type": t, "muCox": mu * 1e-6, "a_gm": a, "lam": lam, "vth": vth}
    return {
        "NM0": d("NMOS", 267.1, 0.908, 0.3351, 0.623),
        "NM1": d("NMOS", 262.4, 0.896, 0.6304, 0.623),
        "NM2": d("NMOS", 251.6, 0.967, 0.1729, 0.554),
        "NM3": d("NMOS", 260.5, 0.963, 0.06205, 0.562),
        "NM4": d("NMOS", 262.0, 0.977, 0.04114, 0.546),
        "PM0": d("PMOS", 81.4, 0.879, 0.0772, 1.012),
        "PM1": d("PMOS", 84.9, 0.871, 0.04567, 0.998),
        "PM2": d("PMOS", 84.81, 0.871, 0.0466, 0.998),
    }


if __name__ == "__main__":
    import json
    spec = {"targets": {"gain_dB": 70.0, "gbw_Hz": 28159000.0, "pm_deg": 82.116},
            "conditions": {"vdd": 1.8, "cl": 2e-12, "vcm": None}}
    print(json.dumps(compute_sizing(spec, _cal_params()), indent=1))
