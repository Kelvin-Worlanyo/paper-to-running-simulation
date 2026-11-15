# =============================================================================
# Telescopic cascode OTA (Fig. 2) -- round 0 sizing of NM1/NM4 and V1..V4.
# Targets: gain 52.0 dB +/-3 dB, power 85.7568 uW +/-25% (fitted), vdd 1.8 V,
# CL 20 pF, vcm free.  Process: sky130 1.8 V devices, all L = 500 nm.
# Numbers below are the ones this file computes (printed by running it).
#
# -----------------------------------------------------------------------------
# (1) DEVICE ROLES
# -----------------------------------------------------------------------------
# NM2  (3u/0.5u, gate vbn0=V4)      tail current sink, sets I_tail = 2*I_b.
# NM1, NM4 (VARIABLE, L=500n, m=1)  NMOS input pair, gates vin1/vin2, common
#                                   source at tail.  NM4 is the inverting-input
#                                   device and drives the measured branch.
# NM0, NM3 (6u/0.5u, gate vbn1=V3)  NMOS cascodes, boost the sink-side output
#                                   resistance of NM1/NM4 by gm*ro.
# PM1, PM3 (7u/0.5u, gate vbp2=V2)  PMOS cascodes, boost the source-side output
#                                   resistance of PM0/PM2 by gm*ro.
# PM0, PM2 (7u/0.5u, gate vbp1=V1)  PMOS current sources, each must deliver I_b.
# Nodes: tail (pair source), n1/n2 (pair drains = cascode sources), p1/p2 (PMOS
# current-source drains = PMOS cascode sources), x1 (dummy branch output, not
# connected onward), vout (measured output, loaded by CL).
# There is no mirror anywhere: both the sink current (V4) and the source current
# (V1) are set by gate biases, so I_PM0 = I_PM2 = I_tail/2 is a DESIGN equation,
# not something the circuit arranges for itself (see section 6).
#
# -----------------------------------------------------------------------------
# (2) DEVICE CONSTRAINTS  (classification per the sizing rule)
# -----------------------------------------------------------------------------
# NM4  INDEPENDENT : W = 2*Id*L / (muCox * Vov1^2), L kept at the printed 500 nm,
#                    m kept at 1.  Vov1 is the single gain knob of the circuit.
# NM1  MATCHED     : copies NM4 exactly (same W, L, m).  Required for the
#                    differential pair to split I_tail evenly.
# Everything else is (fixed, printed) and is not touched; its Vov is therefore
# a dependent quantity, Vov = sqrt(2*Id*L/(muCox*W)), not a free choice.
# Geometry limits: 0.42 um <= W <= 100 um per finger -> W1 = 3.820 um is legal.
# Saturation requirement for every device: |Vds| >= |Vov|.
#
# -----------------------------------------------------------------------------
# (3) SIGNAL PATH
# -----------------------------------------------------------------------------
# Bench: unity-gain follower, vout fed back to the inverting input (vin2) through
# an ideal inductor (DC short, AC open); the AC test signal drives vin2 while
# vin1 sits at the DC vcm, i.e. vin1 is an AC ground.
# vin2 -> NM4 gate.  The tail node is not a hard virtual ground: with vin1 AC
# grounded and Rtail = ro_NM2 >> 1/gm1, vtail = vin2 * gm1/(2*gm1 + 1/Rtail)
# ~= vin2/2, so the signal current delivered to node n2 is
#       id_NM4 = gm1*(vin2 - vtail) = (gm1/2)*vin2.
# That current passes NM3 (common gate, unity current gain) into vout, where it
# meets the cascoded output resistance.  The twin current id_NM1 = -(gm1/2)*vin2
# lands on x1, which drives nothing, so it does not return to vout: the loop
# gain carries the factor 1/2 of a single-ended readout of a non-mirrored pair.
# Dominant pole: vout against CL + output parasitics.  Non-dominant poles: n2
# (1/gm_NM3 against its own capacitance) and p2 (1/gm_PM3 against its own), both
# in the 0.7-1.5 GHz decade and therefore irrelevant here.
#
# -----------------------------------------------------------------------------
# (4) DESIGN EQUATIONS (symbolic)
# -----------------------------------------------------------------------------
# Square law, per device: Id = (muCox/2)*(W/L)*Vov^2  ->  Vov = sqrt(2*Id*L/(muCox*W))
#                         gm = a_gm * 2*Id/Vov,   ro = 1/(lam*Id)
# Power:   P = I_tail * vdd = 2*I_b*vdd                      (gate biases draw no DC)
# Output resistance:
#   R_dn = gm_NM3 * ro_NM3 * ro_NM4      (NMOS cascode over the input device)
#   R_up = gm_PM3 * ro_PM3 * ro_PM2      (PMOS cascode over the current source)
#   R_out = R_dn || R_up
# Gain:    A0 = (gm1/2) * R_out,  gm1 = a_gm*2*I_b/Vov1
#          => Vov1 required for a target A0:  Vov1 = a_gm*I_b*R_out / A0
# GBW:     f_u = A0 * 1/(2*pi*R_out*C_out) = gm1 / (4*pi*C_out)
# PM:      90deg - atan(f_u/f_n2) - atan(f_u/f_p2),  f_x = gm_x/(2*pi*C_x)
# Headroom (the binding equation of this topology, derived in section 5):
#          Vtail + Vov1 <= vdd - Vth_n - (1+m_p)*(|Vov_PM2| + |Vov_PM3|)
# Biases:  V4 = Vth_n + Vov_NM2(I_tail)          (sets I_tail)
#          V1 = vdd - |Vth_p| - |Vov_PM0(I_b)|   (sets I_b)
#          V3 = V(n) + Vth_n + Vov_NM3,  V2 = V(p) - |Vth_p| - |Vov_PM3|
#
# Round-0 parameters (initial_params): muCox_n 120 uA/V^2, muCox_p 40 uA/V^2,
# lam_n 0.28/V, lam_p 0.16/V, Vth_n 0.60 V, |Vth_p| 0.95 V, a_gm 1.0.
#
# GAIN vs POWER ARE IN TENSION HERE, and the tension is quantified, not asserted.
# Vov1 is the only gain knob; raising it lowers gain but also raises
# vcm = Vtail + Vth_n + Vov1, and vcm IS the output DC level in a follower, so it
# eats the PMOS cascode stack's headroom.  Sweeping I_tail over the allowed power
# band (Vov1 needed for 52.0 dB vs Vov1 allowed by headroom, 5% PMOS Vds margin):
#   I_tail/I_nom   P (uW)   Vov1_req   Vov1_max   best gain (dB)
#      0.75         64.3     0.267      0.334        52.0
#      0.85         72.9     0.251      0.280        52.0
#      0.96         82.3     0.236      0.223        52.48   <- chosen
#      1.00         85.8     0.231      0.204        53.10
#      1.10         94.3     0.221      0.156        55.00
#      1.25        107.2     0.207      0.089        59.38   (out of tolerance)
# So at the fitted power the circuit is ~1.1 dB too strong, and the gain target
# alone would prefer ~0.85x power.  Both targets are reachable at once over
# 0.75-1.00x; they cannot both be centred.  The current is therefore chosen to
# minimise the worse of the two normalised errors: at 0.96x, gain error
# +0.48 dB = 0.16 of the 3 dB tolerance and power error -4.0% = 0.16 of the 25%
# tolerance.  Above ~1.13x the gain leaves its +/-3 dB window altogether.
#
# -----------------------------------------------------------------------------
# (5) DC BIAS VERIFICATION -- every branch supports saturation, with numbers
# -----------------------------------------------------------------------------
# Chosen operating point: I_tail = 45.737 uA, I_b = 22.868 uA (P = 82.33 uW).
# Dependent overdrives of the printed cells at that current:
#   NM2 (3u/0.5u, 45.737 uA):  Vov_t  = sqrt(2*45.737u*0.5u/(120u*3u))  = 0.35644 V
#   NM0/NM3 (6u/0.5u, 22.868 uA): Vov_nc = sqrt(2*22.868u*0.5u/(120u*6u)) = 0.17822 V
#   PM0..PM3 (7u/0.5u, 22.868 uA): Vov_p = sqrt(2*22.868u*0.5u/(40u*7u))  = 0.28579 V
# Input pair: Vov1 = 0.22336 V -> W1 = 2*22.868u*0.5u/(120u*0.22336^2) = 3.820 um.
# Vertical budget, bottom to top, all from the devices above:
#   Vtail      = Vov_t + 0.020 = 0.37644 V   -> Vds_NM2 = 0.37644 >= 0.35644  OK (+5.6%)
#   vcm = vout = Vtail + Vth_n + Vov1 = 0.37644 + 0.600 + 0.22336 = 1.19979 V
#   output ceiling = vdd - 2*Vov_p = 1.8 - 0.57157 = 1.22843 V > 1.19979  OK
# NMOS branch (tail -> vout spans 1.19979 - 0.37644 = 0.82335 V, needs
# Vov1 + Vov_nc = 0.40158 V, so 0.42178 V of slack to share):
#   V(n1)=V(n2) = 0.37644 + 0.43425 = 0.81068 V
#   NM1/NM4: Vds = 0.81068 - 0.37644 = 0.43425 >= Vov1 = 0.22336   OK (1.94x)
#   NM0/NM3: Vds = 1.19979 - 0.81068 = 0.38911 >= Vov_nc = 0.17822 OK (2.18x)
# PMOS branch (vdd -> vout spans 1.8 - 1.19979 = 0.60021 V, needs 2*Vov_p =
# 0.57157 V, so only 0.02864 V of slack -- this is the binding side):
#   V(p1)=V(p2) = 1.8 - 0.30010 = 1.49990 V
#   PM0/PM2: |Vds| = 1.8 - 1.49990 = 0.30010 >= Vov_p = 0.28579  OK (+5.0%)
#   PM1/PM3: |Vds| = 1.49990 - 1.19979 = 0.30010 >= 0.28579      OK (+5.0%)
# All nine transistors are in saturation; the PMOS cascode pair has the least
# margin (5%), which is why the current was backed off from 1.25x power.
# Gain check at this point: ro_n = 1/(0.28*22.868u) = 156.2 kOhm,
# ro_p = 1/(0.16*22.868u) = 273.4 kOhm, gm_nc = 2*22.868u/0.17822 = 256.6 uS,
# gm_p = 2*22.868u/0.28579 = 160.0 uS, gm1 = 2*22.868u/0.22336 = 204.8 uS:
#   R_dn = 256.6u*156.2k*156.2k = 6.259 MOhm
#   R_up = 160.0u*273.4k*273.4k = 11.954 MOhm
#   R_out = 4.108 MOhm,  A0 = 0.5*204.8u*4.108M = 420.6 = 52.48 dB.
#   f_u = 204.8u/(4*pi*20.016p) = 814 kHz; f_n2 = 1.52 GHz, f_p2 = 0.74 GHz,
#   PM = 90 - 0.03 - 0.06 = 89.9 deg (single-pole response, CL dominates).
#
# -----------------------------------------------------------------------------
# (6) DC OPERATING-POINT CONSISTENCY -- what each stage produces vs what the
#     next one needs, with explicit arithmetic
# -----------------------------------------------------------------------------
# a) V4 -> tail current.  V4 = Vth_n + Vov_t = 0.600 + 0.35644 = 0.95644 V.
#    NM2 gate-source = 0.95644 - 0 = 0.95644 -> Vov = 0.35644 ->
#    Id = (120u/2)*(3u/0.5u)*0.35644^2 = 45.74 uA = I_tail as intended.
# b) tail node needed by NM2 vs produced by the pair.  The pair produces
#    Vtail = vcm - Vth_n - Vov1 = 1.19979 - 0.600 - 0.22336 = 0.37643 V;
#    NM2 needs >= 0.35644 V. Produced - needed = +0.020 V.  (vcm is an input we
#    choose, so this is a choice of vcm, not an assumption about tail.)
# c) V3 -> node n.  V3 = V(n) + Vth_n + Vov_nc = 0.81068 + 0.600 + 0.17822
#    = 1.58890 V (< vdd, legal).  Conversely NM3 with Vgs = 1.58890 - 0.81068
#    = 0.77822 V carries (120u/2)*(6u/0.5u)*(0.17822)^2 = 22.87 uA = I_b: the
#    cascode passes exactly the current the pair hands it, as a common-gate
#    stage must.
# d) V1 -> branch current.  V1 = vdd - |Vth_p| - Vov_p = 1.8 - 0.95 - 0.28579
#    = 0.56421 V.  PM2 |Vgs| = 1.8 - 0.56421 = 1.23579 -> |Vov| = 0.28579 ->
#    Id = (40u/2)*(7u/0.5u)*0.28579^2 = 22.87 uA = I_b.  MATCHING CONDITION:
#    I_PM0 = I_PM2 = 22.87 uA must equal I_tail/2 = 22.87 uA.  It does, by
#    construction of V1 and V4 from the same I_b -- this is the one place where
#    model error cannot be absorbed by feedback, because node x1 has no
#    feedback path (see f).
# e) V2 -> node p.  V2 = V(p) - |Vth_p| - Vov_p = 1.49990 - 0.95 - 0.28579
#    = 0.26411 V (> 0, legal).  PM3 |Vgs| = 1.49990 - 0.26411 = 1.23579 ->
#    |Vov| = 0.28579 -> 22.87 uA, again exactly I_b.  And V(p) - |Vds_PM3|
#    = 1.49990 - 0.30010 = 1.19980 V = vout = vcm: the top of the stack lands on
#    the output level the follower has to settle at, to within 1e-5 V.
# f) the two branches.  In the follower, vin1 = vcm and vin2 = vout ~= vcm, so
#    the pair is balanced and NM1 and NM4 each carry I_tail/2 = 22.87 uA; with
#    PM0 and PM2 sharing gate V1 and matched geometry, both branches sit at the
#    same node voltages, x1 = vout = 1.19979 V and p1 = p2 = 1.49990 V.  The
#    vout branch is held there by the feedback loop (a residual current error
#    dI shifts vout by only dI/gm1 = 4.9 mV per uA).  The x1 branch is NOT:
#    x1 is a high-impedance unloaded node, so any error in (d) drives it to a
#    rail and pushes PM1 or NM0 out of saturation.  Round 0 has no calibration,
#    so V1 vs V4 accuracy rests entirely on the muCox/Vth estimates above; that
#    is the first thing the next round's measurements should fix.
#
# -----------------------------------------------------------------------------
# (7) PYTHON CODE
# -----------------------------------------------------------------------------

import math

# ---------------------------------------------------------------- process-ish
COX = 8.4e-3          # F/m^2, 1.8 V gate oxide (tox ~ 4.1 nm): 8.4 fF/um^2
CGD_PER_W = 0.30e-9   # F/m of width, gate-drain overlap (0.30 fF/um)
CJ_PER_W = 0.90e-9    # F/m of width, drain/source junction (0.90 fF/um)

# ---------------------------------------------------------------- fixed cells
# (fixed, printed) geometry from the figure: w, l, m
FIXED = {
    "PM0": (7.0e-6, 500e-9, 1),
    "PM1": (7.0e-6, 500e-9, 1),
    "PM2": (7.0e-6, 500e-9, 1),
    "PM3": (7.0e-6, 500e-9, 1),
    "NM0": (6.0e-6, 500e-9, 1),
    "NM3": (6.0e-6, 500e-9, 1),
    "NM2": (3.0e-6, 500e-9, 1),
}
W_MIN, W_MAX = 0.42e-6, 100e-6

# headroom bookkeeping
VTAIL_MARGIN = 0.020      # V of Vds above Vov for the tail device
PMOS_MARGIN = 0.05        # fractional Vds margin above |Vov| for PM2/PM3

LAST_DESIGN = {}          # intermediate quantities of the last call, for inspection


def initial_params():
    """Round-0 estimates for sky130_fd_pr__{nfet,pfet}_01v8 at L = 0.5 um.

    muCox : effective mu*Cox in the square law Id = muCox/2 * (W/L) * Vov^2
            (already derated for vertical-field mobility degradation).
    a_gm  : multiplier on the square-law gm = 2*Id/Vov.  Kept at 1.0 in round 0;
            it is the handle calibration will move in later rounds.
    lam   : channel-length modulation, ro = 1/(lam*Id); 0.28 /V (n) and 0.16 /V
            (p) correspond to intrinsic gains gm*ro of ~40 (n) and ~45 (p) at
            the overdrives this circuit uses.
    vth   : threshold MAGNITUDE (PMOS stored positive).
    """
    n = {"type": "NMOS", "muCox": 120e-6, "a_gm": 1.0, "lam": 0.28, "vth": 0.60}
    p = {"type": "PMOS", "muCox": 40e-6, "a_gm": 1.0, "lam": 0.16, "vth": 0.95}
    out = {}
    for d in ("NM0", "NM1", "NM2", "NM3", "NM4"):
        out[d] = dict(n)
    for d in ("PM0", "PM1", "PM2", "PM3"):
        out[d] = dict(p)
    return out


# ---------------------------------------------------------------- small models
def _vov(p, w, l, m, i):
    """Square-law overdrive needed to carry i through (w, l, m)."""
    return math.sqrt(2.0 * i * l / (p["muCox"] * w * m))


def _gm_of_vov(p, i, vov):
    return p["a_gm"] * 2.0 * i / vov


def _ro(p, i):
    return 1.0 / (p["lam"] * i)


def _branch(params, i_b, i_tail):
    """Everything that depends only on the branch current (fixed cells)."""
    wp, lp, mp = FIXED["PM0"]
    wn, ln, mn = FIXED["NM0"]
    wt, lt, mt = FIXED["NM2"]
    pp, pn = params["PM0"], params["NM0"]
    d = {}
    d["vov_p"] = _vov(pp, wp, lp, mp, i_b)                 # PM0/PM1/PM2/PM3
    d["vov_nc"] = _vov(pn, wn, ln, mn, i_b)                # NM0/NM3 cascodes
    d["vov_t"] = _vov(params["NM2"], wt, lt, mt, i_tail)   # NM2 tail
    d["gm_p"] = _gm_of_vov(pp, i_b, d["vov_p"])
    d["gm_nc"] = _gm_of_vov(pn, i_b, d["vov_nc"])
    d["ro_p"] = _ro(pp, i_b)
    d["ro_n"] = _ro(pn, i_b)
    d["r_up"] = d["gm_p"] * d["ro_p"] * d["ro_p"]          # gm3*ro3*ro2
    d["r_dn"] = d["gm_nc"] * d["ro_n"] * d["ro_n"]         # gm_NM3*ro_NM3*ro_NM4
    d["r_out"] = 1.0 / (1.0 / d["r_up"] + 1.0 / d["r_dn"])
    return d


def compute_sizing(spec, params):
    cond = spec.get("conditions", {})
    vdd = cond.get("vdd", 1.8)
    cl = cond.get("cl", 20e-12)
    tgt = spec["targets"]
    a_target = 10.0 ** (tgt["gain_dB"] / 20.0)
    p_target = tgt["power_W"]
    keep = spec.get("variables", {}).get("keep_printed", {})
    l_in = keep.get("NM1.l", 500e-9)
    m_in = int(keep.get("NM1.m", 1))
    # tolerances as published in the specification (absolute dB / relative)
    tol = spec.get("tolerance", {})
    tol_g = tol.get("gain_dB", ("abs", 3.0))[1]
    tol_p = tol.get("power_W", ("rel", 0.25))[1]

    pn, pp = params["NM1"], params["PM0"]
    vth_n, vth_p = pn["vth"], abs(pp["vth"])

    i_tail_nom = p_target / vdd

    # ---- pick the branch current.  Vov1 is the only gain knob and the headroom
    # inequality caps it at vov1_max, so for each candidate current the best
    # achievable gain is the one at Vov1 = min(vov1_req, vov1_max).  Score each
    # candidate by its worst target error in units of that target's tolerance
    # and keep the minimax point: both targets inside tolerance, neither
    # favoured over the other.
    best = None
    k = 0.75
    while k <= 1.2501:
        i_tail = k * i_tail_nom
        i_b = 0.5 * i_tail
        d = _branch(params, i_b, i_tail)
        gm1_req = 2.0 * a_target / d["r_out"]              # A = (gm1/2)*Rout
        vov1_req = pn["a_gm"] * 2.0 * i_b / gm1_req
        vtail = d["vov_t"] + VTAIL_MARGIN
        vout_max = vdd - (1.0 + PMOS_MARGIN) * 2.0 * d["vov_p"]
        vov1_max = vout_max - vth_n - vtail
        vov1 = min(vov1_req, vov1_max)
        w1 = 2.0 * i_b * l_in / (pn["muCox"] * vov1 ** 2 * m_in)
        if vov1 > 0.0 and W_MIN <= w1 <= W_MAX:
            err_g = abs(20.0 * math.log10(vov1_req / vov1)) / tol_g
            err_p = abs(k - 1.0) / tol_p
            score = max(err_g, err_p)
            if best is None or score < best[0]:
                best = (score, k, i_tail, i_b, d, vov1_req, vov1, vtail,
                        vov1_max - vov1_req)
        k += 0.0025

    if best is None:                 # no headroom anywhere: take nominal power
        k = 1.0                      # and the smallest legal input pair
        i_tail = i_tail_nom
        i_b = 0.5 * i_tail
        d = _branch(params, i_b, i_tail)
        vov1_req = pn["a_gm"] * i_b * d["r_out"] / a_target
        vtail = d["vov_t"] + VTAIL_MARGIN
        vov1 = _vov(pn, W_MAX, l_in, m_in, i_b)
        slack = 0.0
    else:
        _, k, i_tail, i_b, d, vov1_req, vov1, vtail, slack = best

    # ---- input pair geometry (INDEPENDENT: W = 2*Id*L/(muCox*Vov^2)), on a 5 nm grid
    w1 = 2.0 * i_b * l_in / (pn["muCox"] * vov1 ** 2 * m_in)
    w1 = min(W_MAX, max(W_MIN, round(w1 / 5e-9) * 5e-9))
    vov1 = _vov(pn, w1, l_in, m_in, i_b)                   # re-derive from the grid value
    gm1 = _gm_of_vov(pn, i_b, vov1)

    # ---- DC operating point, every node from the driving stage's parameters
    vcm = vtail + vth_n + vov1                             # NM1/NM4 gate = source + Vgs
    vout = vcm                                             # unity-gain follower
    # NMOS stack: share (vout - vtail) between NM4 and NM3 above their own Vov
    extra_n = (vout - vtail) - (vov1 + d["vov_nc"])
    vds_nm4 = vov1 + 0.5 * extra_n
    vds_nm3 = d["vov_nc"] + 0.5 * extra_n
    v_n = vtail + vds_nm4                                  # nodes n1 / n2
    vbn1 = v_n + vth_n + d["vov_nc"]                       # NM0/NM3 gate
    vbn0 = vth_n + d["vov_t"]                              # NM2 gate sets i_tail
    # PMOS stack: share (vdd - vout) between PM2 and PM3
    vds_p = 0.5 * (vdd - vout)
    v_p = vdd - vds_p                                      # nodes p1 / p2
    vbp1 = vdd - vth_p - d["vov_p"]                        # PM0/PM2 gate sets i_b
    vbp2 = v_p - vth_p - d["vov_p"]                        # PM1/PM3 gate

    # ---- predictions
    gain = 0.5 * gm1 * d["r_out"]
    gain_dB = 20.0 * math.log10(gain)
    power = i_tail * vdd

    wp = FIXED["PM3"][0]
    wn = FIXED["NM3"][0]
    c_out = cl + (CGD_PER_W + CJ_PER_W) * (wp + wn)
    gbw = gm1 / (2.0 * math.pi * 2.0 * c_out)              # A*f_p1 = gm1/(4*pi*Cout)
    c_n = (2.0 / 3.0) * wn * FIXED["NM3"][1] * COX + CJ_PER_W * (wn + w1) + CGD_PER_W * w1
    c_p = (2.0 / 3.0) * wp * FIXED["PM3"][1] * COX + CJ_PER_W * 2.0 * wp + CGD_PER_W * wp
    f_n = d["gm_nc"] / (2.0 * math.pi * c_n)
    f_p = d["gm_p"] / (2.0 * math.pi * c_p)
    pm = 90.0 - math.degrees(math.atan(gbw / f_n)) - math.degrees(math.atan(gbw / f_p))

    LAST_DESIGN.clear()
    LAST_DESIGN.update(
        i_tail=i_tail, i_branch=i_b, k_power=k, vov1_req=vov1_req, vov1=vov1,
        w1=w1, gm1=gm1, r_up=d["r_up"], r_dn=d["r_dn"], r_out=d["r_out"],
        vov_p=d["vov_p"], vov_nc=d["vov_nc"], vov_t=d["vov_t"], vtail=vtail,
        v_n=v_n, v_p=v_p, vds_nm4=vds_nm4, vds_nm3=vds_nm3, vds_p=vds_p,
        headroom_slack=slack, c_out=c_out, f_n=f_n, f_p=f_p,
    )

    return {
        "sizes": {
            "NM1": {"w": w1, "l": l_in, "m": m_in},
            "NM4": {"w": w1, "l": l_in, "m": m_in},
        },
        "biases": {
            "V1": vbp1,
            "V2": vbp2,
            "V3": vbn1,
            "V4": vbn0,
        },
        "currents": {},
        "caps": {},
        "vcm": vcm,
        "predicted": {
            "gain_dB": gain_dB,
            "gbw_Hz": gbw,
            "pm_deg": pm,
            "power_W": power,
        },
    }


if __name__ == "__main__":
    SPEC = {
        "targets": {"gain_dB": 52.0, "power_W": 8.57568e-05},
        "tolerance": {"gain_dB": ["abs", 3.0], "power_W": ["rel", 0.25]},
        "conditions": {"vdd": 1.8, "cl": 2e-11, "vcm": None},
        "variables": {
            "devices": ["NM1", "NM4"],
            "biases": ["V1", "V2", "V3", "V4"],
            "vcm": True,
            "keep_printed": {"NM1.l": 5e-07, "NM4.l": 5e-07, "NM1.m": 1, "NM4.m": 1},
        },
    }
    r = compute_sizing(SPEC, initial_params())
    for key in ("sizes", "biases", "vcm", "predicted"):
        print(key, r[key])
    for key in sorted(LAST_DESIGN):
        print("   ", key, LAST_DESIGN[key])
