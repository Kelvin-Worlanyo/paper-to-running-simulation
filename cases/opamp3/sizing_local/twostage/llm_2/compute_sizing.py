"""
Round 2 sizing: two-stage Miller op-amp (NMOS input pair, PMOS mirror load,
PMOS common-source second stage, NMOS current-sink load), Sky130 1.8 V devices.

What changed vs round 1 and why
  Round 1 measured: gain -3.9 dB vs prediction, GBW +23 % vs prediction,
  PM -10.6 deg vs prediction.
  (a) Gain: round 1 rescaled lam by L_round0/L_new although the parameters it
      receives are fitted on the round-1 geometry. That double-counted the
      length increase (x2/3 on lam -> ~+3.5 dB optimistic). lam is now taken
      as fitted at the round-1 lengths (L_FIT) and rescaled only for a length
      that actually changes.
  (b) PM: the model omitted the input-pair gate capacitance that loads vout in
      the unity-gain bench (vout drives vin1: Cin = Cgs,NM0/2 + Cgd,NM0; with
      NM0 at 3 um x ~30 um that is ~0.3 pF, +15 % on CL). NM0/NM1 go back to
      L = 2 um (gate area /2.2); stage-1 gds is dominated by the PMOS mirror
      anyway. Cc is no longer fixed: it is swept with I6, the mirror
      length/overdrive and PM0 overdrive, and the analytic model picks the
      lowest-power point that meets gain >= target+2 dB and PM >= target-1 deg
      (now that Cin and the lower crossing are modelled). Chasing +3 deg in the
      model cost 2x power (5.5 vs 3.1 mW with nominal params) and an 11-finger
      PM0 whose own parasitics would eat the gain.
  (c) GBW: measured/predicted = 1.23 with the same gm equations; gm1 is sized
      for 0.85 x target so the measured value lands near 1.05 x target if the
      bias persists, and still inside 25 % (0.85x) if it does not. The lower
      crossing also recovers PM.

(1) DEVICE ROLES
  I0   reference current into diode NM3 (sets vbias)
  NM3  diode bias reference                      INDEPENDENT (I0, Vov_t)
  NM2  tail sink                                 MIRROR of NM3 (same L)
  NM4  2nd-stage sink load                       MIRROR of NM3 (same L)
  NM0  input device, gate vin1 (inverting)       INDEPENDENT (Id1, Vov1, L=2u)
  NM1  input device, gate vin2                   MATCHED to NM0
  PM2  diode side of active load (node A)        INDEPENDENT (Id1, Vov_m, Lm)
  PM1  mirror output (node B)                    MATCHED to PM2
  PM0  2nd-stage CS driver, gate B               INDEPENDENT (I6, Vov_0, L0)
       (current set by NM4; its VSG is imposed on node B by the loop)
  C0   Miller cap B -> vout

(2) DEVICE CONSTRAINTS
  Vov1 = 0.12 V, Vov_t = 0.18 V, Vov_m in {0.22..0.30}, Vov_0 in {0.25..0.35}
  subject to headroom (section 5). W per finger <= 100 um (m > 1 beyond).
  NM2/NM4 use NM3's L (2 um). lam(L) = lam_fit * L_FIT / L.

(3) SIGNAL PATH
  vin1/vin2 -> NM0/NM1 (gm1) -> B (PM2/PM1 fold NM0's current) -> PM0 (gm6) -> vout.
  vin1 -> A -> mirror -> B non-inverting; B -> vout inverting: vin1 inverting.

(4) DESIGN EQUATIONS
  gm = a_gm Id / Vov, gds = lam Id, W = 2 Id L / (muCox Vov^2)
  A1 = gm1 / (Id1 (lam_n0 + lam_p1)),  A2 = gm6 / (I6 (lam_p0 + lam_n4))
  Gain = A1 A2
  GBW = gm1 / (2 pi Cce), Cce = C0 + Cgd,PM0;  gm1 = 0.85 * 2 pi GBW_t * Cce
  C1  = Cgs0 + Cdb(PM1) + Cdb(NM1) + Cgd(NM1) + Cgd(PM1)          (node B)
  CLe = CL + Cdb(PM0) + Cdb(NM4) + Cgd(NM4) + Cgs(NM0)/2 + Cgd(NM0) (vout)
  p2  = gm6 Cce / (C1 CLe + C1 Cce + Cce CLe)
  z   = gm6 / Cce (RHP)
  p3  = gm_PM2 / C_A, C_A = Cgs(PM2)+Cgs(PM1)+Cdb(PM2)+Cdb(NM0)+Cgd(NM0);
        mirror zero at 2 p3
  PM  = 90 - atan(wc/p2) - atan(wc/z) - atan(wc/p3) + atan(wc/2p3)
  Power = VDD (I0 + 2 Id1 + I6). Search keeps Gain >= 72 dB, maximises
  model PM up to target-1 deg, then minimises power. If that is unreachable (PM saturates as p2 -> wT,p0-limited)
  the highest-PM point is taken.

(5) DC BIAS VERIFICATION (nominal Vthn 0.60, |Vthp| 0.95, gamma 0.4; the code
    re-evaluates this with the fitted Vth and rejects infeasible points)
  VA = 1.8 - 0.95 - Vov_m;  Vov_m = 0.25 -> VA = 0.60 V
  VB = 1.8 - 0.95 - Vov_0 (loop imposes PM0's VSG); Vov_0 = 0.30 -> VB = 0.55 V
  NM2 needs VC >= 0.18 + 0.10 = 0.28 V
  NM0/NM1 need VC <= min(VA, VB) - 0.12 - 0.10 = 0.55 - 0.22 = 0.33 V
  choose VC = midpoint 0.305 V
    NM2 VDS = 0.305 (Vdsat 0.18, margin 0.125)
    NM1 VDS = 0.55 - 0.305 = 0.245 (Vdsat 0.12, margin 0.125)
    NM0 VDS = 0.60 - 0.305 = 0.295 (margin 0.175)
  Vthn(VSB=0.305) = 0.60 + 0.4 (sqrt(1.105) - sqrt(0.8)) = 0.60 + 0.4 (1.051 - 0.894)
                  = 0.663 V -> vcm = 0.305 + 0.663 + 0.12 = 1.088 V
  NM3: VDS = VGS = 0.78 >= 0.18 ok
  PM2: VSD = VSG = 1.20 >= 0.25 ok; PM1: VSD = 1.8 - 0.55 = 1.25 ok
  PM0: VSD = 1.8 - 1.088 = 0.712 >= 0.30 ok (margin 0.41)
  NM4: VDS = 1.088 >= 0.18 ok

(6) DC OPERATING-POINT CONSISTENCY
  Stage-1 output node B must sit at VSG of PM0: VB = 1.8 - |Vthp0| - Vov_0.
  With Vov_0 = 0.30 and Vov_m = 0.25, VB = 0.55 V vs VA = 0.60 V: PM1 has
  VSD 1.25 V vs PM2 1.20 V; with lam_p ~0.1/V that is a 0.5 % current
  mismatch -> offset 0.005 * Id1 / gm1 = 0.005 * 0.12/2 = 0.3 mV, harmless;
  the loop absorbs it. NM1 VDS = 0.245 V > 0.12 V (checked above).
  vout = vcm = 1.088 V lies in [Vov_t, VDD - Vov_0] = [0.18, 1.50] V.
  Tail: NM2 at VGS = 0.78 V (same as NM3) gives 2 Id1 = I0 W2/W3;
  NM4 gives I6 = I0 W4/W3, and PM0 is sized for that I6 at Vov_0.
"""
import math

COX = 8.3e-3
CJ_W = 0.45e-9
CGD_W = 0.30e-9
WMAX = 100e-6

# lengths of the round-1 design, on which the received parameters were fitted
L_FIT = {"NM0": 3e-6, "NM1": 3e-6, "NM2": 2e-6, "NM3": 2e-6, "NM4": 2e-6,
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


def compute_sizing(spec, params):
    vdd = spec["conditions"]["vdd"]
    cl = spec["conditions"]["cl"]
    tg = spec["targets"]
    gbw_t = tg["gbw_Hz"]
    pm_t = tg["pm_deg"]
    gain_t = tg["gain_dB"]
    wu_t = 2 * math.pi * gbw_t
    gbw_k = 0.85
    wc = gbw_k * wu_t
    gain_req = gain_t + 2.0
    pm_req = pm_t - 1.0

    pn0, pn3, pn4 = params["NM0"], params["NM3"], params["NM4"]
    pp0, pp2 = params["PM0"], params["PM2"]

    Ln0 = 2e-6
    Lt = 2e-6          # NM3 and its mirrors NM2, NM4
    vov1, vovt = 0.12, 0.18
    gamma, phi2 = 0.4, 0.8
    marg = 0.10
    I0 = 20e-6

    vthn = abs(pn0["vth"])
    vthp_m = abs(pp2["vth"])
    vthp_0 = abs(pp0["vth"])
    lam_n0 = _lam(params, "NM0", Ln0)
    lam_n4 = _lam(params, "NM4", Lt)

    best = None
    for Lm in (0.6e-6, 0.8e-6, 1.0e-6, 1.2e-6):
        lam_p1 = _lam(params, "PM1", Lm)
        for vovm in (0.22, 0.25, 0.28, 0.30):
            va = vdd - vthp_m - vovm
            for L0 in (0.5e-6, 0.6e-6, 0.8e-6, 1.0e-6):
                lam_p0 = _lam(params, "PM0", L0)
                for vov0 in (0.25, 0.28, 0.30, 0.33, 0.35):
                    vb = vdd - vthp_0 - vov0
                    vc_min = vovt + marg
                    vc_max = min(va, vb) - vov1 - marg
                    if vc_max < vc_min:
                        continue
                    vc = 0.5 * (vc_min + vc_max)
                    vthb = vthn + gamma * (math.sqrt(phi2 + vc) - math.sqrt(phi2))
                    vcm = vc + vthb + vov1
                    if vdd - vcm < vov0 + marg:
                        continue
                    for C0 in (0.6e-12, 0.8e-12, 1.0e-12, 1.2e-12, 1.5e-12, 2.0e-12):
                        I6 = 40e-6
                        while I6 <= 3e-3:
                            W0 = 2 * I6 * L0 / (pp0["muCox"] * vov0 ** 2)
                            Cce = C0 + CGD_W * W0
                            gm1 = wc * Cce
                            Id1 = gm1 * vov1 / pn0["a_gm"]
                            Wn1 = 2 * Id1 * Ln0 / (pn0["muCox"] * vov1 ** 2)
                            Wp1 = 2 * Id1 * Lm / (pp2["muCox"] * vovm ** 2)
                            W4 = 2 * I6 * Lt / (pn4["muCox"] * vovt ** 2)
                            gm6 = pp0["a_gm"] * I6 / vov0
                            A1 = gm1 / (Id1 * (lam_n0 + lam_p1))
                            A2 = gm6 / (I6 * (lam_p0 + lam_n4))
                            gain_dB = 20 * math.log10(A1 * A2)
                            if gain_dB < gain_req:
                                break  # more I6 does not raise gain
                            C1 = ((2.0 / 3.0) * W0 * L0 * COX
                                  + CJ_W * (Wp1 + Wn1) + CGD_W * (Wn1 + Wp1))
                            Cin = 0.5 * (2.0 / 3.0) * Wn1 * Ln0 * COX + CGD_W * Wn1
                            CLe = cl + CJ_W * (W0 + W4) + CGD_W * W4 + Cin
                            p2 = gm6 * Cce / (C1 * CLe + C1 * Cce + Cce * CLe)
                            z = gm6 / Cce
                            gmp2 = pp2["a_gm"] * Id1 / vovm
                            CA = (2 * (2.0 / 3.0) * Wp1 * Lm * COX
                                  + CJ_W * (Wp1 + Wn1) + CGD_W * (Wn1 + Wp1))
                            p3 = gmp2 / CA
                            pm = 90 - math.degrees(
                                math.atan(wc / p2) + math.atan(wc / z)
                                + math.atan(wc / p3) - math.atan(wc / (2 * p3)))
                            power = vdd * (I0 + 2 * Id1 + I6)
                            # score: PM up to the requirement first, then power
                            key = (round(min(pm, pm_req), 2), -power)
                            if best is None or key > best["key"]:
                                best = dict(key=key, power=power, I6=I6, W0=W0,
                                            Cce=Cce, gm1=gm1, Id1=Id1, Wn1=Wn1,
                                            Wp1=Wp1, gm6=gm6, pm=pm,
                                            gain_dB=gain_dB, Lm=Lm, L0=L0,
                                            vovm=vovm, vov0=vov0, C0=C0, vcm=vcm)
                            if pm >= pm_req:
                                break
                            I6 += 10e-6

    if best is None:
        # fallback: round-1-like point
        best = dict(I6=500e-6, Lm=0.8e-6, L0=0.6e-6, vovm=0.25, vov0=0.25,
                    C0=1.5e-12, vcm=1.1)
        best["W0"] = 2 * best["I6"] * best["L0"] / (pp0["muCox"] * 0.0625)
        best["Cce"] = best["C0"] + CGD_W * best["W0"]
        best["gm1"] = wc * best["Cce"]
        best["Id1"] = best["gm1"] * vov1 / pn0["a_gm"]
        best["Wn1"] = 2 * best["Id1"] * Ln0 / (pn0["muCox"] * vov1 ** 2)
        best["Wp1"] = 2 * best["Id1"] * best["Lm"] / (pp2["muCox"] * 0.0625)
        best["gm6"] = pp0["a_gm"] * best["I6"] / 0.25
        best["gain_dB"] = 0.0
        best["pm"] = 0.0

    I6, Id1 = best["I6"], best["Id1"]
    W3 = 2 * I0 * Lt / (pn3["muCox"] * vovt ** 2)
    W2 = W3 * (2 * Id1) / I0
    W4 = W3 * I6 / I0
    gbw = best["gm1"] / (2 * math.pi * best["Cce"])
    power = vdd * (I0 + 2 * Id1 + I6)

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
                      "pm_deg": best["pm"], "power_W": power},
    }


if __name__ == "__main__":
    import json
    spec = {"targets": {"gain_dB": 70.0, "gbw_Hz": 28159000.0, "pm_deg": 82.116},
            "conditions": {"vdd": 1.8, "cl": 2e-12, "vcm": None}}
    print(json.dumps(compute_sizing(spec, initial_params()), indent=1))
