"""Round 0 sizing: two-stage Miller op-amp (Fig. 4), commercial 180 nm, 1.8 V core devices.

(1) DEVICE ROLES
  I0        reference current into diode NM3 (sets vbias).
  NM3       diode-connected NMOS reference (Iref = I0).
  NM2       tail current sink of the input pair, MIRROR of NM3 (same L).
  NM4       second-stage current sink, MIRROR of NM3 (same L).
  NM0/NM1   NMOS differential input pair (NM0 gate = vin1 = inverting input).
  PM2       diode-connected PMOS load (node A) of the first stage.
  PM1       PMOS mirror load (node B = first-stage output), MIRROR of PM2 (same L).
  PM0       PMOS common-source second stage (gate B, drain vout).
  C0        Miller compensation cap Cc between B and vout (no nulling resistor).

(2) DEVICE CONSTRAINTS / CLASSIFICATION
  NM3  INDEPENDENT: W = 2*I0*L/(muCox_n*Vov_t^2), Vov_t = 0.20 V, L_t = 1.0 um
  NM2  MIRROR of NM3: W = W3 * I5/I0 * L/L  (I5 = I0 -> W2 = W3)
  NM4  MIRROR of NM3: W = W3 * I6/I0
  NM0  INDEPENDENT: W = 2*I1*L/(muCox_n*Vov_in^2), Vov_in = 0.15 V, L = 0.6 um
  NM1  MATCHED to NM0
  PM2  INDEPENDENT: W = 2*I1*L/(muCox_p*Vov_p^2), Vov_p = 0.25 V, L_p = 0.5 um
  PM1  MIRROR of PM2 (I1/I1 -> W1 = W2, same L)
  PM0  INDEPENDENT with Vov = Vov_p and L = L_p, i.e. W0 = W2 * I6/I1; this equal
       current density makes Vsg(PM0) = Vsg(PM2) -> zero systematic offset,
       which requires I6/I1 = W4/W2(n-side ratio) -> I6 = I0*(W4/W3), satisfied.
  Cc   chosen 0.8 pF (large vs node-B parasitics, small vs CL = 2 pF).

(3) SIGNAL PATH
  vin1/vin2 -> NM0/NM1 gm1 -> mirror PM2/PM1 folds the NM0 current to B ->
  node B (Rout1 = 1/(gds_NM1+gds_PM1)) -> PM0 gate, gm6 -> vout (Rout2 =
  1/(gds_PM0+gds_NM4)) -> CL. Cc from B to vout splits poles (Miller).
  Inverting input vin1: +vin1 -> NM0 more current -> A falls -> PM1 more current
  -> B rises -> PM0 less current -> vout falls. Correct.

(4) DESIGN EQUATIONS (gm = a_gm * 2*Id/Vov, gds = lam*Id)
  A1 = gm1/(gds1+gdsP1) = gm1/(I1*(lam_n1+lam_p1))
  A2 = gm6/(gdsP0+gds4) = gm6/(I6*(lam_p0+lam_n4))
  Gain = 20log10(A1*A2)
  GBW  = gm1/(2*pi*Cc)          -> gm1 = 2*pi*GBW*Cc = 2*pi*28.159e6*0.8e-12 = 141.5 uS
  p2   = gm6*Cc/(C1*C2 + Cc*(C1+C2)), C1 = Cgs(PM0)+small, C2 = CL + Cdb
  z    = gm6/Cc (RHP)
  p3   = gmP2/(Cgs(PM2)+Cgs(PM1)+Cd) (mirror pole, zero at 2*p3)
  PM   = 90 - atan(wu/p2) - atan(wu/z) - atan(wu/p3) + atan(wu/(2 p3))
  Power = VDD*(I0 + I5 + I6)
  Numbers: Vov_in = 0.15 -> I1 = gm1*Vov/2 = 10.6 uA, I5 = I0 = 21.2 uA.
  gm6 target ~4.8 mS so p2 ~ 7-8 x GBW: I6 = gm6*Vov_p/2 = 600 uA.
  lam (per device at its L): n L0.6 = 0.083, n L1.0 = 0.05, p L0.5 = 0.12 /V
  A1 = (2/0.15)/(0.083+0.12) = 65.7 (36.3 dB); A2 = (2/0.25)/(0.12+0.05) = 47.1
  (33.5 dB) -> ~69.8 dB. C1 ~ 2/3*137um*0.5um*8.5fF/um^2 + ~40 fF = 0.43 pF,
  p2 = 4.8e-3*0.8e-12/(0.43*2 + 0.8*2.43)e-24 = 1.37e9 rad/s (218 MHz) ->
  7.4 deg; z = 6e9 rad/s (955 MHz) -> 1.7 deg; mirror doublet ~0.5 deg;
  PM ~ 80 deg (code, with Cdb/Cgd on vout included: 78.5 deg). Power = 1.8*(21.2+21.2+600) uA = 1.16 mW.

(5) DC BIAS VERIFICATION (Vtn = |Vtp| = 0.50 V, vcm = 1.05 V)
  NM3: VGS = 0.50+0.20 = 0.70 V = VDS -> saturated (diode). I0 sees 1.8-0.70 = 1.10 V.
  NM0/NM1: VGS = 0.50+0.15 = 0.65 V plus body effect (Vsb ~ 0.33 V -> dVth ~ +0.07)
           -> VGS ~ 0.72 V. Node C = vcm - VGS = 1.05 - 0.72 = 0.33 V.
  NM2: VDS = 0.33 V >= Vov_t = 0.20 V -> saturated (0.13 V margin).
  PM2: VSG = 0.50+0.25 = 0.75 V -> node A = 1.8-0.75 = 1.05 V; diode -> saturated.
  NM0: VDS = 1.05-0.33 = 0.72 V >= Vov_in = 0.15 V -> saturated.
  PM1: node B = A = 1.05 V (balanced mirror) -> VSD = 0.75 >= 0.25 -> saturated.
  NM1: VDS = 1.05-0.33 = 0.72 >= 0.15 -> saturated.
  PM0: VSG = 1.8-1.05 = 0.75 = Vth+0.25; vout = vcm = 1.05 V in the follower:
       VSD = 0.75 >= 0.25 -> saturated.
  NM4: VGS = 0.70 (vbias), VDS = 1.05 >= 0.20 -> saturated.
  vcm window: >= Vov_t + VGS1 = 0.20+0.72 = 0.92 V, <= A + Vtn(+body 0.07) = 1.62 V;
  output window [Vov4, VDD-|Vtp|... VDD-Vov_p] = [0.20, 1.55] V. vcm = 1.05 V fits both.

(6) DC OPERATING-POINT CONSISTENCY
  Stage 1 output B is set by the driving stage: B = VDD - |Vtp| - Vov_p
  = 1.8 - 0.50 - 0.25 = 1.05 V (mirror balance forces VSD(PM1) = VSG(PM2)).
  Stage 2 needs VSG(PM0) = 1.8 - B = 0.75 V; PM0 with (W/L)0 = (W/L)2*I6/I1 at
  Vov 0.25 draws exactly I1*(W0/W2) = 10.6uA*56.6 = 600 uA = NM4 current
  (W4/W3 = 600/21.2 = 28.3). Equal -> no systematic offset, vout sits where
  the feedback loop puts it (vcm = 1.05 V), inside [Vov4 = 0.20, 1.8-0.25 = 1.55].
  Tail: C = 1.05 - 0.72 = 0.33 V >= 0.20 V for NM2.

(7) PYTHON CODE below.
"""
import math

VDD = 1.8
COX = 8.5e-3        # F/m^2, ~4.1 nm oxide
L_IN = 0.6e-6
L_P = 0.5e-6
L_T = 1.0e-6
VOV_IN = 0.15
VOV_P = 0.25
VOV_T = 0.20
CC = 0.8e-12
I6 = 600e-6
VCM = 1.05
WF_MAX = 10e-6      # max width per finger


def initial_params():
    n_in = {"type": "NMOS", "muCox": 300e-6, "a_gm": 1.0, "lam": 0.083, "vth": 0.50}
    n_t = {"type": "NMOS", "muCox": 300e-6, "a_gm": 1.0, "lam": 0.05, "vth": 0.50}
    p = {"type": "PMOS", "muCox": 70e-6, "a_gm": 1.0, "lam": 0.12, "vth": 0.50}
    return {
        "NM0": dict(n_in), "NM1": dict(n_in),
        "NM2": dict(n_t), "NM3": dict(n_t), "NM4": dict(n_t),
        "PM0": dict(p), "PM1": dict(p), "PM2": dict(p),
    }


def _w_indep(i, l, mucox, vov):
    return 2.0 * i * l / (mucox * vov * vov)


def _fingers(w, l):
    m = max(1, int(math.ceil(w / WF_MAX)))
    wf = max(w / m, 0.22e-6)
    return {"w": wf, "l": l, "m": m}


def compute_sizing(spec, params):
    t = spec["targets"]
    cl = spec["conditions"]["cl"]
    vdd = spec["conditions"].get("vdd", VDD) or VDD
    gbw = t["gbw_Hz"]

    # first stage from GBW
    a_in = params["NM0"]["a_gm"]
    gm1 = 2 * math.pi * gbw * CC
    i1 = gm1 * VOV_IN / (2.0 * a_in)
    i5 = 2 * i1
    i0 = i5

    # sizes
    w3 = _w_indep(i0, L_T, params["NM3"]["muCox"], VOV_T)
    w2 = w3 * i5 / i0
    w4 = w3 * I6 / i0
    w0n = _w_indep(i1, L_IN, params["NM0"]["muCox"], VOV_IN)
    wp2 = _w_indep(i1, L_P, params["PM2"]["muCox"], VOV_P)
    wp1 = wp2
    wp0 = wp2 * I6 / i1

    sizes = {
        "NM0": _fingers(w0n, L_IN), "NM1": _fingers(w0n, L_IN),
        "NM2": _fingers(w2, L_T), "NM3": _fingers(w3, L_T), "NM4": _fingers(w4, L_T),
        "PM0": _fingers(wp0, L_P), "PM1": _fingers(wp1, L_P), "PM2": _fingers(wp2, L_P),
    }

    # predictions
    gm6 = params["PM0"]["a_gm"] * 2 * I6 / VOV_P
    gmp2 = params["PM2"]["a_gm"] * 2 * i1 / VOV_P
    a1 = gm1 / (i1 * (params["NM1"]["lam"] + params["PM1"]["lam"]))
    a2 = gm6 / (I6 * (params["PM0"]["lam"] + params["NM4"]["lam"]))
    gain_db = 20 * math.log10(a1 * a2)

    cgs = lambda w, l: (2.0 / 3.0) * w * l * COX
    c1 = cgs(wp0, L_P) + 0.1 * cgs(wp0, L_P) + 20e-15
    c2 = cl + 0.3 * cgs(wp0, L_P) + 0.3 * cgs(w4, L_T)
    p2 = gm6 * CC / (c1 * c2 + CC * (c1 + c2))
    z = gm6 / CC
    p3 = gmp2 / (2 * cgs(wp2, L_P) + 10e-15)
    wu = 2 * math.pi * gbw
    pm = 90 - math.degrees(math.atan(wu / p2) + math.atan(wu / z)
                           + math.atan(wu / p3) - math.atan(wu / (2 * p3)))
    power = vdd * (i0 + i5 + I6)

    return {
        "sizes": sizes,
        "biases": {},
        "currents": {"I0": i0},
        "caps": {"C0": CC},
        "vcm": VCM,
        "predicted": {"gain_dB": gain_db, "gbw_Hz": gm1 / (2 * math.pi * CC),
                      "pm_deg": pm, "power_W": power},
    }


if __name__ == "__main__":
    import json
    print(json.dumps(compute_sizing({"targets": {"gain_dB": 70, "gbw_Hz": 28159000.0, "pm_deg": 82.116},
                                     "conditions": {"vdd": 1.8, "cl": 2e-12}},
                                    initial_params()), indent=1))
