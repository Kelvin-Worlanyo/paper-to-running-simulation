"""Round-0 sizing for the two-stage Miller op-amp of Fig. 4, ported to Sky130 1.8 V.

================================================================================
(1) DEVICE ROLES
================================================================================
I0   : bias reference current pushed into the diode-connected NMOS NM3.
NM3  : diode-connected NMOS (Drain=Gate=vbias). It is the gate-voltage reference
       for every NMOS current source.  INDEPENDENT (it sets Vov_b).
NM2  : tail current source of the input pair (Drain=C, Gate=vbias).  MIRROR of
       NM3, same L, W scaled by Itail/I0.
NM0  : input device, gate = vin1 (the inverting input), drain = A. INDEPENDENT.
NM1  : input device, gate = vin2, drain = B.  MATCHED to NM0 (identical W/L/m);
       the pair must be identical or the first stage has systematic offset.
PM2  : diode-connected PMOS load of the NM0 branch (Drain=Gate=A). INDEPENDENT;
       it sets the PMOS gate-source voltage of the whole p-side, hence V(A).
PM1  : PMOS mirror load of the NM1 branch (Gate=A, Drain=B).  MATCHED to PM2 so
       that it carries exactly Itail/2 and node B sits at the same DC level as A.
PM0  : second-stage driver, PMOS common source, Gate=B, Drain=vout.  Because its
       gate hangs on B and B sits at the same DC potential as A, PM0 sees exactly
       the same Vgs as PM2: PM0 is a MIRROR of PM2 (same L, W scaled by I2/Id1).
NM4  : second-stage current-source load (Gate=vbias, Drain=vout).  MIRROR of NM3,
       same L, W scaled by I2/I0.
C0   : Miller compensation capacitor from B (stage-1 output) to vout.
No variable voltage sources exist in this circuit, so "biases" is empty; the only
free DC voltage is the input common mode vcm.

================================================================================
(2) DEVICE CONSTRAINTS
================================================================================
Square-law strong/moderate inversion, consistent with the calibration formulas
that come back in later rounds:
    Id  = (muCox/2) (m W / L) Vov^2         ->  W = 2 Id L / (muCox m Vov^2)
    gm  = a_gm * 2 Id / Vov
    gds = lam * Id,  ro = 1/(lam Id)
Saturation requires Vds > Vov for every device (Vdsat ~ Vov here).
Process window: W in [0.42, 100] um per finger, L in [0.15, 8] um.  Any device
needing more than 20 um of width is split into m fingers of W = Wtot/m, which
keeps the mirror ratio exact because only the product m*W enters Id.
L = 2 um is used for EVERY variable transistor.  Reason: the gain target needs
output resistance, lam ~ 1/(VA' L), and L = 2 um gives lam ~ 0.07 /V for both
flavours (VA ~ 14 V) instead of ~0.28 /V at L = 0.5 um -- a 70 dB two-stage
amplifier is not reachable at minimum length with these currents.  Mirrors
inherit their reference's L (NM2, NM4 from NM3; PM0 from PM2), which is the same
2 um, so rule 2 and the gain requirement agree.

Three overdrives are the only free "shape" variables:
    Vov_b  = 0.20 V  : NMOS bias-mirror overdrive (NM3, and therefore NM2, NM4).
                       Small enough to leave the tail and the output branch
                       headroom (Vds,sat = 0.20 V on a 1.8 V rail), large enough
                       to keep the mirror devices out of weak inversion.
    Vov_p  = 0.26 V  : shared PMOS overdrive of PM2/PM1/PM0 (one number, because
                       they share Vgs).  Chosen for second-stage gm: see (4).
    Vov_n            : input-pair overdrive, SOLVED from the gain target in (4).

================================================================================
(3) SIGNAL PATH
================================================================================
vin1 (inverting) -> NM0 gate.  Differential current +-gm_n*vid/2 splits in the
pair; the NM0 half goes into the diode-connected PM2 and is mirrored by PM1 into
node B, so the single-ended first-stage transconductance is the full gm_n of one
input device (the classic mirror-load stage):
    stage 1:  vB   = -gm_NM0 * (ro_NM1 || ro_PM1) * vid
    stage 2:  vout = -gm_PM0 * (ro_PM0 || ro_NM4) * vB
C0 bridges B and vout: it splits the two poles (Miller) and makes B the dominant
pole node, so the loop gain rolls off at -20 dB/dec through unity gain.
Feedback path on the bench: vout back to vin1 through the DC inductor, AC injected
at vin1; the measured gain is therefore this two-stage loop gain.

================================================================================
(4) DESIGN EQUATIONS (symbolic)
================================================================================
Currents / power.  Three branches draw from vdd: the reference I0, the tail Itail
(NM2), and the output branch I2 (PM0/NM4).
    P = vdd * (I0 + Itail + I2)                                           (P)
Power is a FITTED target here (+-25 % relative), so (P) is solved for the output
branch:  I2 = P_target/vdd - I0 - Itail.

Gain.
    A1 = gm_NM0 * ro1,  ro1 = 1/((lam_NM0 + lam_PM1) Id1),  Id1 = Itail/2
       = 2 a_gm_n / (Vov_n (lam_NM0 + lam_PM1))                           (A1)
    A2 = gm_PM0 * ro2,  ro2 = 1/((lam_PM0 + lam_NM4) I2)
       = 2 a_gm_p / (Vov_p (lam_PM0 + lam_NM4))                           (A2)
    A  = A1 * A2 ,  gain_dB = 20 log10 A
Both stage gains are current-INDEPENDENT (intrinsic gain): the gain target cannot
be bought with current, only with overdrive and channel length.  With L = 2 um and
Vov_p = 0.26 V fixed, (A2) is pinned at ~54.9, so the 70 dB (3162 V/V) target is
met by solving (A1) for the input-pair overdrive:
    Vov_n = 2 a_gm_n / (A_req/A2 * (lam_NM0 + lam_PM1))                   (Vn)

GBW.  With Miller compensation the dominant pole is at node B and
    GBW = gm_NM0 / (2 pi Cc_eff),   Cc_eff = C0 + Cgd_PM0                 (G)
Itail and Vov_n are already spent on gain, so gm_NM0 = a_gm_n Itail/Vov_n is
fixed and (G) is solved for the compensation capacitor:
    C0 = gm_NM0/(2 pi GBW_target) - Cgd_PM0.
That is the decoupling that makes the three targets simultaneously solvable:
power -> currents, overdrive/length -> gain, C0 -> GBW.

Phase margin (NOT a target this round; computed and reported only).
    p2 = gm_PM0 / (2 pi Cl_eff),  Cl_eff = CL + Cdb_PM0 + Cdb_NM4
    z  = gm_PM0 / (2 pi Cc_eff)                (RHP zero, no nulling resistor)
    PM = 90 - atan(GBW/p2) - atan(GBW/z)
The 60-degree rule of thumb needs gm_PM0 >~ 2.2 gm_NM0 Cl_eff/Cc_eff.  With the
numbers below that is 2.2*80.6u*4.75 = 842 uS, and the power budget delivers
gm_PM0 = 2 I2/Vov_p = 848 uS at Vov_p = 0.26 V: the targets are compatible, with
~1 % of margin.  This is what sets Vov_p -- larger Vov_p would raise the gain but
starve the second pole; smaller Vov_p would widen PM0 (rule 4) for no gain.

Parasitics (rule 4).  PM0 ends up ~130 um wide and NM4 ~74 um, so
    Cgd_PM0 ~ CGDO_P * Wtot_PM0 ~ 0.2 fF/um * 130 um = 26 fF  adds to C0 and is
      pre-subtracted from C0 so that GBW lands on target instead of 5 % low;
    Cdb ~ 0.8 fF/um on each output-node drain adds ~163 fF to the 2 pF load,
      which is already included in Cl_eff above (it costs ~2 deg of PM).
Cgs_PM0 (~2.3 pF) sits on node B but is NOT Miller-multiplied, so it appears in
the dominant pole next to Cc*A2 ~ 25 pF: a ~1 % effect on GBW, ignored.

================================================================================
(5) DC BIAS VERIFICATION (numbers, vdd = 1.8 V)
================================================================================
Currents:  I_tot = 248.8 uW / 1.8 V = 138.2 uA; I0 = 8 uA, Itail = 20 uA
           => I2 = 138.2 - 8 - 20 = 110.2 uA.  Id1 = Itail/2 = 10 uA.
Overdrives: Vov_b = 0.20 V, Vov_p = 0.26 V, Vov_n = 2/(57.6*0.14) = 0.248 V
           (A2 = 2/(0.26*0.14) = 54.9, A_req = 3162, A1_req = 57.6).
Thresholds: |Vth_n| = 0.60 V, |Vth_p| = 0.90 V (Sky130 01v8 at L = 2 um).

Node voltages, each computed from the DEVICE that drives it (rule 3):
  vbias = Vth_n + Vov_b                      = 0.60 + 0.20 = 0.80 V   (NM3 diode)
  V(A)  = vdd - |Vth_p| - Vov_p              = 1.80 - 0.90 - 0.26 = 0.64 V (PM2 diode)
  V(B)  = V(A)   (PM1 matched to PM2 and carrying the same 10 uA)      = 0.64 V
  Vgs_NM0 = Vth_n + Vov_n                    = 0.60 + 0.248 = 0.848 V
  V(C)  = chosen inside its legal window, then vcm follows from it:
          lower bound  V(C) >= Vov_b = 0.20 V          (NM2 tail saturated)
          upper bound  V(C) <= V(A) - Vov_n = 0.392 V  (NM0 saturated)
          V(C) = midpoint = 0.296 V  =>  vcm = 0.296 + 0.848 = 1.144 V
  vout  = vcm = 1.144 V on the unity-gain bench.

Saturation check, branch by branch:
  NM3  Vds = vbias = 0.800 V  > Vov_b = 0.200 V      margin +0.600 V  SAT
  NM2  Vds = V(C)  = 0.296 V  > Vov_b = 0.200 V      margin +0.096 V  SAT
  NM0  Vds = V(A) - V(C) = 0.640 - 0.296 = 0.344 V > Vov_n = 0.248 V  SAT (+0.096)
  NM1  Vds = V(B) - V(C) = 0.344 V              > 0.248 V             SAT (+0.096)
  PM2  |Vds| = vdd - V(A) = 1.160 V             > Vov_p = 0.260 V     SAT (+0.900)
  PM1  |Vds| = vdd - V(B) = 1.160 V             > 0.260 V             SAT (+0.900)
  PM0  |Vds| = vdd - vout = 1.800 - 1.144 = 0.656 V > 0.260 V         SAT (+0.396)
  NM4  Vds = vout = 1.144 V                     > Vov_b = 0.200 V     SAT (+0.944)
Every branch has >= 96 mV of saturation margin; the two tightest (NM2 and the
input pair) are tight by construction because V(C) was placed at the midpoint of
its own window, i.e. the headroom is split evenly between tail and pair.
Input-CM window width = 0.392 - 0.200 = 0.192 V, so vcm may drift +-96 mV.

================================================================================
(6) DC OPERATING-POINT CONSISTENCY (what each stage produces vs. what the next needs)
================================================================================
a) Bias branch -> tail and output source.  NM3 produces vbias = 0.80 V from I0 =
   8 uA.  NM2 and NM4 need exactly that gate voltage; they have the same L = 2 um
   and the same Vgs, so their currents are set by width ratio alone:
     NM2: Itail = I0 * W_NM2/W_NM3 = 8 uA * 13.33/5.33 = 20.0 uA   (wanted 20.0)
     NM4: I2    = I0 * W_NM4/W_NM3 = 8 uA * 73.5/5.33  = 110.2 uA  (wanted 110.2)
b) First stage -> second-stage gate.  The pair splits Itail into 10 uA per side.
   PM2 must sink 10 uA; with W/L = 11.83/2 and muCox_p = 50 uA/V^2 it does so at
   Vov_p = sqrt(2*10u*2u/(50u*11.83u)) = 0.260 V, so it PRODUCES
   V(A) = 1.8 - 0.9 - 0.260 = 0.640 V.  PM1 is its twin and carries the other
   10 uA at the same Vgs, so V(B) = 0.640 V as well.  PM0 NEEDS a gate voltage
   that makes it carry I2 = 110.2 uA; at W_tot/L = 130.4/2 (11.02x PM2) its
   required overdrive is sqrt(2*110.2u*2u/(50u*130.4u)) = 0.260 V, i.e. gate at
   1.8 - 0.9 - 0.260 = 0.640 V.  Produced 0.640 V, needed 0.640 V: the ratio
   11.02 = I2/Id1 is exactly what makes these two numbers equal.
c) Second stage -> output node / feedback.  PM0 at V(B) = 0.640 V delivers
   110.2 uA; NM4 at vbias = 0.80 V sinks 110.2 uA.  Difference 0.0 uA by (a)+(b),
   so the output node is in balance at the vout the feedback sets.  Residual
   mismatch dI is absorbed by the DC loop (vout = vcm forced through the
   inductor) moving V(B) by dI/(gm_PM0) = dI/848 uS; a 10 % current mismatch
   (11 uA) moves V(B) by 13 mV, which is 13 % of NM0's 96 mV margin -- the first
   stage stays saturated, so the bias point tolerates realistic mirror error.
d) Input side.  The pair needs Vgs = 0.848 V; the bench holds vin = vcm = 1.144 V
   and the follower holds vout = 1.144 V, so V(C) = 1.144 - 0.848 = 0.296 V,
   which is the value used in (5): produced by NM0/NM1, needed by NM2 (>=0.20 V).

(7) code below.
"""
import math

# Sky130 01v8 estimates used for round 0 (everything here is replaced by
# measured values from round 1 onward).
MUCOX_N = 150e-6      # A/V^2, effective muCox, nfet_01v8, moderate inversion
MUCOX_P = 50e-6       # A/V^2, pfet_01v8 (mobility ratio ~1/3)
VTH_N = 0.60          # V
VTH_P = -0.90         # V (simulator sign convention for PMOS)
LAM_L2 = 0.07         # 1/V at L = 2 um  (VA ~ 14 V)

L_ALL = 2.0e-6        # channel length of every variable device
VOV_B = 0.20          # NMOS bias-mirror overdrive (NM3/NM2/NM4)
VOV_P = 0.26          # shared PMOS overdrive (PM2/PM1/PM0)
I_REF = 8.0e-6        # reference branch current I0
I_TAIL = 20.0e-6      # input-pair tail current

CGDO_P = 0.20e-9      # F/m of gate width, PMOS gate-drain overlap
CJ_DRAIN = 0.80e-9    # F/m of gate width, drain junction + overlap at vout

W_MIN, W_MAX = 0.42e-6, 100e-6
W_FINGER = 20e-6      # split anything wider than this into fingers


def initial_params():
    """Per-device process estimates (round 0 only)."""
    n = dict(type="NMOS", muCox=MUCOX_N, a_gm=1.0, lam=LAM_L2, vth=VTH_N)
    p = dict(type="PMOS", muCox=MUCOX_P, a_gm=1.0, lam=LAM_L2, vth=VTH_P)
    out = {}
    for d in ("NM0", "NM1", "NM2", "NM3", "NM4"):
        out[d] = dict(n)
    for d in ("PM0", "PM1", "PM2"):
        out[d] = dict(p)
    return out


def _g(params, dev, key, default):
    v = params.get(dev, {}).get(key)
    return default if v is None else v


def _fingers(w_tot):
    """Split a total width into m fingers, keeping m*W = w_tot exactly."""
    m = max(1, int(math.ceil(w_tot / W_FINGER)))
    w = w_tot / m
    if w < W_MIN:                      # too narrow: use one minimum finger
        m, w = 1, W_MIN
    if w > W_MAX:                      # cannot happen with W_FINGER = 20 um
        m, w = int(math.ceil(w_tot / W_MAX)), w_tot / int(math.ceil(w_tot / W_MAX))
    return {"w": w, "l": L_ALL, "m": int(m)}


def compute_sizing(spec, params):
    t = spec["targets"]
    c = spec["conditions"]
    vdd = c["vdd"]
    cl = c["cl"]
    gain_req_dB = t["gain_dB"]
    gbw_req = t["gbw_Hz"]
    p_req = t.get("power_W")

    # --- device parameters -------------------------------------------------
    mucox_n = _g(params, "NM0", "muCox", MUCOX_N)
    mucox_n3 = _g(params, "NM3", "muCox", MUCOX_N)
    mucox_p = _g(params, "PM2", "muCox", MUCOX_P)
    agm_n = _g(params, "NM0", "a_gm", 1.0)
    agm_p = _g(params, "PM0", "a_gm", 1.0)
    lam_n0 = _g(params, "NM0", "lam", LAM_L2)
    lam_p1 = _g(params, "PM1", "lam", LAM_L2)
    lam_p0 = _g(params, "PM0", "lam", LAM_L2)
    lam_n4 = _g(params, "NM4", "lam", LAM_L2)
    vth_n = abs(_g(params, "NM0", "vth", VTH_N))
    vth_p = abs(_g(params, "PM2", "vth", VTH_P))

    # --- (P) power target -> branch currents -------------------------------
    i0 = I_REF
    i_tail = I_TAIL
    if p_req:
        i_tot = p_req / vdd
        i2 = i_tot - i0 - i_tail
    else:
        i2 = 110.0e-6
    i2 = max(i2, 10.0e-6)
    id1 = i_tail / 2.0

    # --- (A2),(Vn) gain target -> input-pair overdrive ---------------------
    a_req = 10.0 ** (gain_req_dB / 20.0)
    vov_p = VOV_P
    a2 = 2.0 * agm_p / (vov_p * (lam_p0 + lam_n4))
    a1_req = a_req / a2
    vov_n = 2.0 * agm_n / (a1_req * (lam_n0 + lam_p1))
    vov_n = min(max(vov_n, 0.08), 0.40)

    # --- transconductances -------------------------------------------------
    gm1 = agm_n * 2.0 * id1 / vov_n          # input device
    gm2 = agm_p * 2.0 * i2 / vov_p           # PM0

    # --- widths: INDEPENDENT devices ---------------------------------------
    w_n = 2.0 * id1 * L_ALL / (mucox_n * vov_n ** 2)          # NM0 (NM1 matched)
    w_p = 2.0 * id1 * L_ALL / (mucox_p * vov_p ** 2)          # PM2 (PM1 matched)
    w_nm3 = 2.0 * i0 * L_ALL / (mucox_n3 * VOV_B ** 2)        # NM3 reference
    # --- widths: MIRRORS (same L as the reference, W scaled by current) ----
    w_nm2 = w_nm3 * (i_tail / i0)
    w_nm4 = w_nm3 * (i2 / i0)
    w_pm0 = w_p * (i2 / id1)

    sizes = {
        "NM0": _fingers(w_n), "NM1": _fingers(w_n),
        "NM2": _fingers(w_nm2), "NM3": _fingers(w_nm3), "NM4": _fingers(w_nm4),
        "PM2": _fingers(w_p), "PM1": _fingers(w_p), "PM0": _fingers(w_pm0),
    }

    # --- (G) GBW target -> compensation capacitor (parasitics removed) -----
    cgd_pm0 = CGDO_P * w_pm0
    cc_tot = gm1 / (2.0 * math.pi * gbw_req)
    c0 = max(cc_tot - cgd_pm0, 50e-15)
    cc_eff = c0 + cgd_pm0

    # --- DC operating point ------------------------------------------------
    v_a = vdd - vth_p - vov_p                  # PM2 diode drop sets A (and B)
    vgs_n = vth_n + vov_n
    vc_lo, vc_hi = VOV_B, v_a - vov_n
    v_c = 0.5 * (vc_lo + vc_hi) if vc_hi > vc_lo else vc_lo
    vcm = min(max(vgs_n + v_c, 0.3), vdd - 0.2)

    # --- predictions -------------------------------------------------------
    a1 = gm1 / ((lam_n0 + lam_p1) * id1)
    a2v = gm2 / ((lam_p0 + lam_n4) * i2)
    gain_db = 20.0 * math.log10(a1 * a2v)
    gbw = gm1 / (2.0 * math.pi * cc_eff)
    cl_eff = cl + CJ_DRAIN * (w_pm0 + w_nm4)
    f_p2 = gm2 / (2.0 * math.pi * cl_eff)
    f_z = gm2 / (2.0 * math.pi * cc_eff)
    pm = 90.0 - math.degrees(math.atan(gbw / f_p2)) - math.degrees(math.atan(gbw / f_z))
    power = vdd * (i0 + i_tail + i2)

    return {
        "sizes": sizes,
        "biases": {},
        "currents": {"I0": i0},
        "caps": {"C0": c0},
        "vcm": vcm,
        "predicted": {"gain_dB": gain_db, "gbw_Hz": gbw, "pm_deg": pm, "power_W": power},
    }
