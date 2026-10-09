"""
Round 1 sizing: two-stage Miller op-amp (NMOS input pair, PMOS mirror load,
PMOS common-source second stage, NMOS current-sink load), Sky130 1.8 V devices.

What changed vs round 0 and why
  Round 0 measured gain was ~10 dB below both target and prediction while GBW/PM
  were fine. Two structural weaknesses: (a) headroom: NM0/NM1 had only 0.10 V and
  NM2 only 0.10 V of VDS above Vdsat (0.05 V design margin), so their real output
  conductance was far above lam*Id (near the saturation edge gds rises steeply);
  (b) every gain-setting device used a short L (PMOS 0.6 um, lam ~0.125/V).
  Fixes: re-allocate headroom (Vov_p 0.30->0.25, Vov1 0.15->0.12, Vov_t
  0.20->0.18) so both NM2 and NM0 get ~0.14 V of margin; lengthen the devices
  whose drain nodes are NOT the critical parasitic node (NM0/NM1 2->3 um,
  PM1/PM2 0.6->0.8 um, NM2/3/4 1.5->2 um) while PM0, whose gate cap loads node B
  (second pole), stays at 0.6 um. lam is rescaled ~1/L from the fitted values.
  GBW was 10 % low: gm1 is now sized for 1.10x the target to cover node-B
  current diverted into C1 and overlap caps not in Cc_eff.

(1) DEVICE ROLES
  I0   reference current into diode NM3 (sets vbias)
  NM3  diode bias reference                      INDEPENDENT (I0, Vov_t, L=2u)
  NM2  tail sink                                 MIRROR of NM3 (L=2u)
  NM4  2nd-stage sink load                       MIRROR of NM3 (L=2u)
  NM0  input device, gate vin1 (inverting)       INDEPENDENT (Id1, Vov1, L=3u)
  NM1  input device, gate vin2                   MATCHED to NM0
  PM2  diode side of active load (node A)        INDEPENDENT (Id1, Vov_p, L=0.8u)
  PM1  mirror output (node B)                    MATCHED to PM2
  PM0  2nd-stage CS driver, gate B               INDEPENDENT (I6, Vov_p, L=0.6u)
       (not a mirror: its current is set by NM4; its VSG is set by the loop)
  C0   Miller cap B -> vout

(2) DEVICE CONSTRAINTS
  Vov1 = 0.12 V, Vov_p = 0.25 V, Vov_t = 0.18 V; W per finger <= 100 um (m>1).
  L as above; mirrors NM2/NM4 share NM3's L.

(3) SIGNAL PATH
  vin1/vin2 -> NM0/NM1 (gm1) -> B (PM2/PM1 fold NM0's current) -> PM0 (gm6) -> vout.
  vin1 -> A -> mirror -> B non-inverting, B -> vout inverting: vin1 inverting.

(4) DESIGN EQUATIONS
  gm = a_gm Id/Vov, gds = lam(L) Id, lam(L) = lam_fit * L_prev/L,
  W = 2 Id L/(muCox Vov^2)
  A1 = gm1/(Id1 (lam_n0 + lam_p1)),  A2 = gm6/(I6 (lam_p0 + lam_n4)), Gain = A1 A2
  GBW = gm1/(2 pi Cc_eff), Cc_eff = C0 + Cgd,PM0 ; gm1 sized for 1.10*GBW_target
  p2 = gm6 Cc/(C1 CLe + C1 Cc + Cc CLe), C1 = Cgs0+Cgd0+Cdb(PM1,NM1)+Cgd(NM1)
  z = gm6/Cc (RHP), p3 = gm_PM2/C_A (mirror doublet, zero at 2 p3)
  PM = 90 - atan(wu/p2) - atan(wu/z) - atan(wu/p3) + atan(wu/2p3)
  Power = VDD (I0 + 2 Id1 + I6). I6 swept upward until PM >= target - 3 deg (PM model saturates near
  the target because p2 -> wT,p Cc/(Cc+CL); chasing the last 3 deg cost ~2x power
  and a 2x wider PM0; tolerance is +-10 deg).

(5) DC BIAS VERIFICATION (nominal Vthn 0.60, |Vthp| 0.95, gamma 0.4)
  VA = 1.8 - 0.95 - 0.25 = 0.60 V
  NM2 needs VC >= 0.18 + 0.12 = 0.30 V; NM0 needs VC <= VA - 0.12 - 0.12 = 0.36 V
  choose VC = 0.33 V -> NM2 VDS = 0.33 (Vdsat 0.18, margin 0.15)
                        NM0 VDS = 0.60 - 0.33 = 0.27 (Vdsat 0.12, margin 0.15)
  Vthn(VSB=0.33) = 0.60 + 0.4 (sqrt(1.13) - sqrt(0.8)) = 0.60 + 0.4(1.063-0.894)
                 = 0.667 V -> vcm = 0.33 + 0.667 + 0.12 = 1.117 V
  NM3: VDS = VGS = 0.78 >= 0.18 ok
  PM2: VSD = VSG = 1.20 >= 0.25 ok; PM1: VSD = 1.8 - VB = 1.20 ok
  PM0: VSD = 1.8 - 1.117 = 0.683 >= 0.25 ok (margin 0.43)
  NM4: VDS = 1.117 >= 0.18 ok

(6) DC OPERATING-POINT CONSISTENCY
  Stage-1 output VB = VA = 1.8 - |Vthp| - Vov_p = 0.60 V (PM1/PM2 matched, equal Id1).
  PM0 must carry I6 = I0 W4/W3 (NM4 at same VGS as NM3). With
  W0 = 2 I6 L0/(muCox_p Vov_p^2), PM0 needs VSG = |Vthp,0.6u| + 0.25 V.
  If |Vthp| at 0.6 um equals that at 0.8 um, VB,req = 1.8-0.95-0.25 = 0.60 V = VA.
  A Vth difference dV between the two lengths (tens of mV) moves VB by dV; stage-1
  gain ~ 150 means input offset dV/150 < 0.5 mV and PM1 VSD changes 1.20 -> 1.20+-dV,
  still >> 0.25 V. vout is set by the follower loop to vcm = 1.117 V, inside
  [Vov_t, VDD - Vov_p] = [0.18, 1.55] V.
  Tail: NM2 at VGS 0.78 V gives 2 Id1 = I0 W2/W3.
"""
import math

COX = 8.3e-3
CJ_W = 0.45e-9
CGD_W = 0.30e-9
WMAX = 100e-6

# lengths the fitted params were characterised at (round-0 design)
L_PREV = {"NM0": 2e-6, "NM1": 2e-6, "NM2": 1.5e-6, "NM3": 1.5e-6, "NM4": 1.5e-6,
          "PM0": 0.6e-6, "PM1": 0.6e-6, "PM2": 0.6e-6}


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
    gbw_k = 1.10

    L = {"NM0": 3e-6, "NM1": 3e-6, "NM2": 2e-6, "NM3": 2e-6, "NM4": 2e-6,
         "PM0": 0.6e-6, "PM1": 0.8e-6, "PM2": 0.8e-6}

    def lam(dev):
        return params[dev]["lam"] * L_PREV[dev] / L[dev]

    pn0, pn3, pn4 = params["NM0"], params["NM3"], params["NM4"]
    pp0, pp2 = params["PM0"], params["PM2"]

    vov1, vovp, vovt = 0.12, 0.25, 0.18
    gamma, phi2 = 0.4, 0.8
    C0 = 1.5e-12
    I0 = 20e-6

    vthn = abs(pn0["vth"])
    vthp = max(abs(pp2["vth"]), abs(pp0["vth"]))

    # --- DC headroom (section 5) ---
    va = vdd - vthp - vovp
    vc_min = vovt + 0.12
    vc_max = va - vov1 - 0.12
    vc = 0.5 * (vc_min + vc_max) if vc_max > vc_min else vc_min
    vthb = vthn + gamma * (math.sqrt(phi2 + vc) - math.sqrt(phi2))
    vcm = vc + vthb + vov1

    Lp0, Lp2, Ln0 = L["PM0"], L["PM2"], L["NM0"]
    best = None
    I6 = 50e-6
    while I6 <= 3e-3:
        W0 = 2 * I6 * Lp0 / (pp0["muCox"] * vovp ** 2)
        Cce = C0 + CGD_W * W0
        gm1 = gbw_k * wu * Cce
        Id1 = gm1 * vov1 / pn0["a_gm"]
        Wn1 = 2 * Id1 * Ln0 / (pn0["muCox"] * vov1 ** 2)
        Wp1 = 2 * Id1 * Lp2 / (pp2["muCox"] * vovp ** 2)
        W4 = 2 * I6 * L["NM4"] / (pn4["muCox"] * vovt ** 2)
        gm6 = pp0["a_gm"] * I6 / vovp
        C1 = ((2.0 / 3.0) * W0 * Lp0 * COX + CJ_W * (Wp1 + Wn1) + CGD_W * (Wn1 + Wp1))
        CLe = cl + CJ_W * (W0 + W4)
        p2 = gm6 * Cce / (C1 * CLe + C1 * Cce + Cce * CLe)
        z = gm6 / Cce
        gmp2 = pp2["a_gm"] * Id1 / vovp
        CA = 2 * ((2.0 / 3.0) * Wp1 * Lp2 * COX + CGD_W * Wp1) + CJ_W * (Wp1 + Wn1) \
            + CGD_W * Wn1
        p3 = gmp2 / CA
        wc = wu  # crossing placed at target
        pm = 90 - math.degrees(math.atan(wc / p2) + math.atan(wc / z)
                               + math.atan(wc / p3) - math.atan(wc / (2 * p3)))
        best = dict(I6=I6, W0=W0, Cce=Cce, gm1=gm1, Id1=Id1, Wn1=Wn1, Wp1=Wp1,
                    W4=W4, gm6=gm6, pm=pm, p2=p2)
        if pm >= pm_t - 3.0:
            break
        I6 += 10e-6

    I6, Id1, gm1, gm6 = best["I6"], best["Id1"], best["gm1"], best["gm6"]

    W3 = 2 * I0 * L["NM3"] / (pn3["muCox"] * vovt ** 2)
    W2 = W3 * (2 * Id1) / I0
    W4 = W3 * I6 / I0
    Wn = best["Wn1"]
    Wp2 = best["Wp1"]
    W0 = best["W0"]

    A1 = gm1 / (Id1 * (lam("NM0") + lam("PM1")))
    A2 = gm6 / (I6 * (lam("PM0") + lam("NM4")))
    gain_dB = 20 * math.log10(A1 * A2)
    gbw = gm1 / (2 * math.pi * best["Cce"])
    power = vdd * (I0 + 2 * Id1 + I6)

    return {
        "sizes": {
            "NM0": _split(Wn, L["NM0"]),
            "NM1": _split(Wn, L["NM1"]),
            "NM2": _split(W2, L["NM2"]),
            "NM3": _split(W3, L["NM3"]),
            "NM4": _split(W4, L["NM4"]),
            "PM2": _split(Wp2, L["PM2"]),
            "PM1": _split(Wp2, L["PM1"]),
            "PM0": _split(W0, L["PM0"]),
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
