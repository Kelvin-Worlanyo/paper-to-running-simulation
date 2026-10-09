"""
Round 3 sizing: two-stage Miller op-amp (NMOS input pair, PMOS mirror load,
PMOS common-source second stage, NMOS current-sink load), Sky130 1.8 V devices.

What round 2 told us (and what changes)
  Round 2 predicted gain 0 dB / PM 0 deg: that is the FALLBACK branch. With the
  fitted lam values no grid point reached the hard gain requirement (72 dB), and
  because model gain does not depend on I6 every point was rejected, so the
  hard-coded fallback (I6 500 uA, Cc 1.5 pF, L0 0.6 u, Lm 0.8 u, Lt 2 u,
  NM0 2 u @ Vov 0.12) was simulated: 64.7 dB, 35.8 MHz, 65.9 deg.
  Structural fixes:
  (a) No hard rejection on gain/PM any more. Every headroom-feasible point is
      scored by normalised shortfall (gain in units of 3 dB, PM in units of
      10 deg) and then by power, so the function always returns a designed
      point with an honest prediction.
  (b) Gain was short because both stages are dominated by short-L devices.
      New free lengths: NM3/NM2/NM4 mirror length Lt in {2,3,4} um (NM4 lam
      halves at 4 um), PMOS mirror Lm in {0.8..1.2} um, L0 in {0.5..0.8} um.
      lam(L) = lam_fit * L_FIT / L with L_FIT = the fallback geometry the
      parameters were fitted on. NM4's junction + Cgd at vout (W4 ~ I6 Lt/Vovt^2)
      is now in CLe, so long Lt is not free.
  (c) GBW came out 1.49x the gm1/Cc model at fixed NM0 geometry and current
      density (Vov 0.12 V, L 2 um): the pair sits in moderate inversion where
      gm/Id exceeds a_gm/Vov. NM0 keeps exactly that density, and the model
      uses gm1 = KGM a_gm Id1/Vov1 with KGM = 1.45 in GBW, PM and gain.
      GBW is aimed at 27.5 MHz (-2 %) instead of 0.85 x target.
  (d) PM: the p2 expression is kept (C1 = Cgs0 dominates), and I6 (<= 2.5 mA),
      Vov0 and Cc (<= 3.5 pF) are searched. Physical limit: p2 -> wT0 Cc/(Cc+CLe)
      as gm6 -> inf, with wT0 = 1.5 mu_p Vov0/L0^2, so L0 stays short.
      Score: shortfall below gain_t+1 dB (per 3 dB) plus shortfall below
      pm_t-4 deg (per 10 deg), i.e. normalised by the tolerances; then power.

(1) DEVICE ROLES
  I0   reference current into diode NM3 (sets vbias)
  NM3  diode bias reference                      INDEPENDENT (I0, Vovt, Lt)
  NM2  tail sink                                 MIRROR of NM3 (same Lt)
  NM4  2nd-stage sink load                       MIRROR of NM3 (same Lt)
  NM0  input device, gate vin1 (inverting)       INDEPENDENT (Id1, Vov1 0.12, L 2u)
  NM1  input device, gate vin2                   MATCHED to NM0
  PM2  diode side of active load (node A)        INDEPENDENT (Id1, Vovm, Lm)
  PM1  mirror output (node B)                    MATCHED to PM2
  PM0  2nd-stage CS driver, gate B               INDEPENDENT (I6, Vov0, L0)
  C0   Miller cap B -> vout

(2) DEVICE CONSTRAINTS
  Vov1 = 0.12 V (kept: calibrated KGM applies only at this density), Vovt in
  {0.18..0.30} (smaller NM4 junction at vout), Vovm in {0.22..0.32},
  Vov0 in {0.22..0.35}; headroom checks of section 5 are evaluated with the fitted Vth and infeasible points dropped.
  W per finger <= 100 um (m > 1 beyond). NM2/NM4 share NM3's L.

(3) SIGNAL PATH
  vin1 -> NM0 -> A -> PM2/PM1 mirror -> B (non-inverting from vin1 to B... with
  the NM1 path inverting: B falls when vin2 rises) -> PM0 (inverting) -> vout.
  Net: vout inverting w.r.t. vin1, as the simulation decided.

(4) DESIGN EQUATIONS
  gm1 = KGM a_gm Id1/Vov1, gm6 = a_gm I6/Vov0, gds = lam(L) Id
  A1 = gm1/(Id1 (lam_n0 + lam_p1)), A2 = gm6/(I6 (lam_p0 + lam_n4)), Gain = A1 A2
  Cce = C0 + Cgd0;  GBW = gm1/(2 pi Cce)  -> Id1 = 2 pi GBW Cce Vov1/(KGM a_gm)
  C1  = Cgs0 + (Cdb + Cgd)(PM1, NM1)
  CLe = CL + Cdb0 + (Cdb + Cgd)(NM4) + Cgs(NM0)/2 + Cgd(NM0)
  p2  = gm6 Cce/(C1 CLe + C1 Cce + Cce CLe);  z = gm6/Cce (RHP)
  p3  = gm_PM2/C_A (mirror), zero at 2 p3
  PM  = 90 - atan(wc/p2) - atan(wc/z) - atan(wc/p3) + atan(wc/2p3)
  Power = VDD (I0 + 2 Id1 + I6)

(5) DC BIAS VERIFICATION (nominal Vthn 0.60, |Vthp| 0.95, gamma 0.4, example
    point Vovm 0.25, Vov0 0.25, Vovt 0.18; code repeats with fitted Vth)
  VA = 1.8 - 0.95 - 0.25 = 0.60 V;  VB = 1.8 - 0.95 - 0.25 = 0.60 V
  VC window: >= Vovt + 0.08 = 0.26 V; <= min(VA,VB) - 0.12 - 0.08 = 0.40 V
  VC = midpoint 0.33 V:  NM2 VDS 0.33 (Vdsat 0.18, margin 0.15)
    NM0/NM1 VDS = 0.60 - 0.33 = 0.27 (Vdsat 0.12, margin 0.15)
  Vthn(VSB 0.33) = 0.60 + 0.4 (sqrt(1.13) - sqrt(0.8)) = 0.60 + 0.4 (1.063 - 0.894)
                 = 0.668 V -> vcm = 0.33 + 0.668 + 0.12 = 1.118 V
  PM0 VSD = 1.8 - 1.118 = 0.682 >= 0.25 + 0.08 ok; NM4 VDS = 1.118 >= 0.18 ok
  PM2 VSD = VSG = 1.20 ok; PM1 VSD = 1.8 - 0.60 = 1.20 ok; NM3 VDS = VGS ~0.78 ok

(6) DC OPERATING-POINT CONSISTENCY
  Node B is set by PM0's VSG carrying I6 (imposed by NM4):
  VB = 1.8 - |Vthp0| - Vov0 = 0.60 V; mirror diode VA = 1.8 - |Vthp2| - Vovm = 0.60 V.
  With Vov0 = Vovm the two PMOS VSDs are equal (1.20 V) -> no systematic offset;
  when the search picks Vov0 != Vovm, e.g. 0.30 vs 0.25, VSD differs by 0.05 V,
  lam_p ~0.1 -> 0.5 % mismatch -> 0.005 * Vov1/2 = 0.3 mV offset, harmless.
  vout = vcm = 1.118 V lies inside [Vovt, VDD - Vov0] = [0.18, 1.55] V.
  Tail: NM2 at VGS(NM3) with W2 = W3 (2 Id1)/I0; NM4: W4 = W3 I6/I0; same Lt.
"""
import math

COX = 8.3e-3
CJ_W = 0.45e-9
CGD_W = 0.30e-9
WMAX = 100e-6
KGM = 1.45           # measured gm1 / (a_gm Id/Vov) at Vov1 0.12, L 2u (round 2)
GBW_AIM = 27.5e6

# geometry the received parameters were fitted on (round-2 simulated design)
L_FIT = {"NM0": 2e-6, "NM1": 2e-6, "NM2": 2e-6, "NM3": 2e-6, "NM4": 2e-6,
         "PM0": 0.6e-6, "PM1": 0.8e-6, "PM2": 0.8e-6}


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


def _lam(params, dev, L):
    return params[dev]["lam"] * L_FIT[dev] / L


def _grid(a, b, n):
    return [a + (b - a) * i / (n - 1) for i in range(n)]


def compute_sizing(spec, params):
    vdd = spec["conditions"]["vdd"]
    cl = spec["conditions"]["cl"]
    tg = spec["targets"]
    pm_t = tg["pm_deg"]
    gain_t = tg["gain_dB"]
    wc = 2 * math.pi * min(GBW_AIM, tg["gbw_Hz"])
    gain_req = gain_t + 1.0
    pm_req = pm_t - 4.0

    pn0, pn3, pn4 = params["NM0"], params["NM3"], params["NM4"]
    pp0, pp2 = params["PM0"], params["PM2"]

    Ln0 = 2e-6
    vov1 = 0.12
    gamma, phi2 = 0.4, 0.8
    marg = 0.08
    I0 = 20e-6
    gm1_gain = KGM * pn0["a_gm"]

    vthn = abs(pn0["vth"])
    vthp_m = abs(pp2["vth"])
    vthp_0 = abs(pp0["vth"])
    lam_n0 = _lam(params, "NM0", Ln0)

    best = None
    for Lt in (2e-6, 3e-6, 4e-6):
        lam_n4 = _lam(params, "NM4", Lt)
        for vovt in (0.18, 0.22, 0.26, 0.30):
            for Lm in (0.8e-6, 1.0e-6, 1.2e-6):
                lam_p1 = _lam(params, "PM1", Lm)
                for vovm in (0.22, 0.25, 0.28, 0.32):
                    va = vdd - vthp_m - vovm
                    for L0 in (0.5e-6, 0.6e-6, 0.7e-6, 0.8e-6):
                        lam_p0 = _lam(params, "PM0", L0)
                        for vov0 in (0.22, 0.25, 0.28, 0.31, 0.35):
                            vb = vdd - vthp_0 - vov0
                            vc_min = vovt + marg
                            vc_max = min(va, vb) - vov1 - marg
                            if vc_max < vc_min:
                                continue
                            vc = 0.5 * (vc_min + vc_max)
                            vthb = vthn + gamma * (math.sqrt(phi2 + vc) - math.sqrt(phi2))
                            vcm = vc + vthb + vov1
                            if vdd - vcm < vov0 + marg or vcm < vovt + marg:
                                continue
                            A1 = gm1_gain / (vov1 * (lam_n0 + lam_p1))
                            A2 = pp0["a_gm"] / (vov0 * (lam_p0 + lam_n4))
                            gain_dB = 20 * math.log10(A1 * A2)
                            for C0 in (1.0e-12, 1.5e-12, 2.0e-12, 2.5e-12,
                                       3.0e-12, 3.5e-12):
                                for I6 in _grid(200e-6, 2.5e-3, 24):
                                    W0 = 2 * I6 * L0 / (pp0["muCox"] * vov0 ** 2)
                                    Cce = C0 + CGD_W * W0
                                    gm1 = wc * Cce
                                    Id1 = gm1 * vov1 / gm1_gain
                                    Wn1 = 2 * Id1 * Ln0 / (pn0["muCox"] * vov1 ** 2)
                                    Wp1 = 2 * Id1 * Lm / (pp2["muCox"] * vovm ** 2)
                                    W4 = 2 * I6 * Lt / (pn4["muCox"] * vovt ** 2)
                                    gm6 = pp0["a_gm"] * I6 / vov0
                                    C1 = ((2.0 / 3.0) * W0 * L0 * COX
                                          + (CJ_W + CGD_W) * (Wp1 + Wn1))
                                    Cin = (0.5 * (2.0 / 3.0) * Wn1 * Ln0 * COX
                                           + CGD_W * Wn1)
                                    CLe = cl + CJ_W * (W0 + W4) + CGD_W * W4 + Cin
                                    p2 = gm6 * Cce / (C1 * CLe + C1 * Cce + Cce * CLe)
                                    z = gm6 / Cce
                                    gmp2 = pp2["a_gm"] * Id1 / vovm
                                    CA = (2 * (2.0 / 3.0) * Wp1 * Lm * COX
                                          + (CJ_W + CGD_W) * (Wp1 + Wn1))
                                    p3 = gmp2 / CA
                                    pm = 90 - math.degrees(
                                        math.atan(wc / p2) + math.atan(wc / z)
                                        + math.atan(wc / p3)
                                        - math.atan(wc / (2 * p3)))
                                    power = vdd * (I0 + 2 * Id1 + I6)
                                    short = (max(0.0, gain_req - gain_dB) / 3.0
                                             + max(0.0, pm_req - pm) / 10.0)
                                    key = (-round(short, 3), -power)
                                    if best is None or key > best["key"]:
                                        best = dict(key=key, I6=I6, W0=W0, Cce=Cce,
                                                    gm1=gm1, Id1=Id1, Wn1=Wn1,
                                                    Wp1=Wp1, pm=pm, gain_dB=gain_dB,
                                                    Lm=Lm, L0=L0, Lt=Lt, vovt=vovt,
                                                    vovm=vovm, vov0=vov0, C0=C0,
                                                    vcm=vcm, power=power)

    if best is None:
        raise RuntimeError("no headroom-feasible point with the fitted Vth")

    I6, Id1, Lt, vovt = best["I6"], best["Id1"], best["Lt"], best["vovt"]
    W3 = 2 * I0 * Lt / (pn3["muCox"] * vovt ** 2)
    W2 = W3 * (2 * Id1) / I0
    W4 = W3 * I6 / I0
    gbw = best["gm1"] / (2 * math.pi * best["Cce"])

    return {
        "sizes": {
            "NM0": _split(best["Wn1"], Ln0),
            "NM1": _split(best["Wn1"], Ln0),
            "NM2": _split(W2, Lt),
            "NM3": _split(W3, Lt),
            "NM4": _split(W4, Lt),
            "PM2": _split(best["Wp1"], best["Lm"]),
            "PM1": _split(best["Wp1"], best["Lm"]),
            "PM0": _split(best["W0"], best["L0"]),
        },
        "biases": {},
        "currents": {"I0": I0},
        "caps": {"C0": best["C0"]},
        "vcm": best["vcm"],
        "predicted": {"gain_dB": best["gain_dB"], "gbw_Hz": gbw,
                      "pm_deg": best["pm"], "power_W": best["power"]},
    }


if __name__ == "__main__":
    import json
    spec = {"targets": {"gain_dB": 70.0, "gbw_Hz": 28159000.0, "pm_deg": 82.116},
            "conditions": {"vdd": 1.8, "cl": 2e-12, "vcm": None}}
    print(json.dumps(compute_sizing(spec, initial_params()), indent=1))
