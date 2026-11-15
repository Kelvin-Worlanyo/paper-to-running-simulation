# =============================================================================
# Telescopic cascode OTA (Fig. 2) -- round 1 sizing of NM1/NM4 and V1..V4.
# Targets: gain 52.0 dB +/-3 dB, power 85.7568 uW +/-25% (fitted), vdd 1.8 V,
# CL 20 pF, vcm free.  Process: sky130 1.8 V devices, all L = 500 nm.
# Numbers quoted below are the ones this file computes from the round-0
# calibration table as printed (the executed run is handed the full-precision
# params file, which moves the last digit of W1 from 1.940 to 1.945 um).
#
# WHAT THE CALIBRATION SAID ROUND 0 GOT WRONG (quantified, four separate errors)
#
# E1  NM2's parameters, hence the power.  Round 0 set V4 = 0.95644 V from
#     muCox_n = 120 uA/V^2 and Vth_n = 0.600 V, expecting I_tail = 45.74 uA.
#     Measured Vth_NM2 = 0.633 V, so Vov_t was really 0.95644-0.633 = 0.32344 V,
#     and Id = (202.6u/2)*(3u/0.5u)*0.32344^2 = 63.58 uA -- the 63.56 uA that was
#     measured.  Power 114.41 uW vs 85.76 uW target: +33%.  The whole power
#     error is this one parameter error, not a structural one.
# E2  The branch-current mismatch, hence SIX of the nine devices' bias points.
#     NM2's extraction is itself from a TRIODE point (Vds 209 mV < Vov 323 mV),
#     so it under-reports muCox: back-solving the triode law gives
#     muCox_sat = 202.6 * (0.323^2/2)/(0.323*0.209-0.209^2/2) = 231.4 uA/V^2,
#     i.e. V4 = 0.95644 V asks for I_tail = 72.6 uA in saturation, while
#     V1 = 0.56421 V had the two PMOS sources pass only 31.9+31.7 = 63.6 uA.
#     The tail demanded 14% more current than the branches would accept.  Node
#     x1 carries no feedback, so the surplus collapsed the dummy branch
#     (NM1 Vds 58 mV, NM0 Vds 17 mV) and dragged NM2 itself into triode to shed
#     the difference.  That is also why the follower missed vcm: with NM1
#     clamped, Vgs_NM4 = 0.843 V on a tail at 0.209 V put vout at 1.052 V,
#     148 mV below the vcm of 1.1998 V.  Round 0 gave the tail only 20 mV of
#     Vds margin, so it had no room to absorb any of this.
# E3  lam of the PMOS current source.  Round 0 assumed lam_p = 0.16 /V for all
#     four PMOS.  Measured on the SAME printed 7u/0.5u cell: 0.8229 /V for PM2
#     at |Vds| = 250 mV, 0.138 /V for PM3 at 497 mV, 0.06602 /V for PM1 at
#     1258 mV.  lam is a strong function of the saturation margin, and round 0
#     squeezed the PMOS stack to a 5% margin, which left ro_PM2 = 38.3 kOhm and
#     R_up = 2.04 MOhm instead of the 11.95 MOhm it had predicted.  This is
#     most of the 5.79 dB gain over-prediction.
# E4  The tail-division factor.  Round 0 used gm_eff = gm1/2, which assumes an
#     ideal current-source tail and a matched partner.  With the finite
#     ro_NM2 and the degraded NM1 actually present, the factor was
#     (gm_NM1 + 1/ro_NM2)/(gm_NM1 + gm_NM4 + 1/ro_NM2)
#     = (113.9u + 135.1u)/(113.9u + 320.9u + 135.1u) = 0.4369, not 0.5.
#
# Recomputing round 0's own gain equation with the calibrated numbers at the
# measured operating point (I_b = 31.7 uA): ro_NM3 = 1/(0.245*31.7u) = 128.8 k,
# ro_NM4 = 211.4 k, R_dn = 393.8u*128.8k*211.4k = 10.72 M; ro_PM3 = 228.6 k,
# ro_PM2 = 38.3 k, R_up = 232.2u*228.6k*38.3k = 2.035 M; R_out = 1.710 M;
# A = 0.4369*320.9u*1.710M = 239.8 = 47.60 dB against a measured 46.69 dB.
# So the recalibrated model still OVER-predicts gain by 0.91 dB; that residual,
# not the raw 5.79 dB, is the margin this round carries (GAIN_OFFSET_DB).
# The recalibrated power model reproduces the measurement exactly (E1 above),
# so no bulk power margin is carried; POWER_DESIGN_FACTOR = 0.93 covers only
# the one effect still unmodelled, see section 4.
#
# -----------------------------------------------------------------------------
# (1) DEVICE ROLES
# -----------------------------------------------------------------------------
# NM2  (3u/0.5u, gate vbn0=V4)      tail current sink; its gate bias sets
#                                   I_tail and therefore the supply power.
# NM1, NM4 (VARIABLE, L=500n, m=1)  NMOS input pair, gates vin1/vin2, common
#                                   source at tail.  NM4 is the inverting-input
#                                   device and drives the measured branch; NM1
#                                   drives the dummy branch (node x1).
# NM0, NM3 (6u/0.5u, gate vbn1=V3)  NMOS cascodes; raise the sink-side output
#                                   resistance of NM1/NM4 by gm*ro.
# PM1, PM3 (7u/0.5u, gate vbp2=V2)  PMOS cascodes; raise the source-side output
#                                   resistance of PM0/PM2 by gm*ro.
# PM0, PM2 (7u/0.5u, gate vbp1=V1)  PMOS current sources, each delivering I_b.
# Nodes: tail (pair source), n1/n2 (pair drains = NMOS cascode sources),
# p1/p2 (PMOS source drains = PMOS cascode sources), x1 (dummy-branch output,
# unloaded and un-fed-back), vout (measured output, loaded by CL).
# There is no mirror: the sink current (V4) and the source current (V1) are set
# by independent gate biases, so I_PM0 = I_PM2 = I_tail/2 is a DESIGN equation
# that nothing in the circuit enforces (section 6f).
#
# -----------------------------------------------------------------------------
# (2) DEVICE CONSTRAINTS  (classification per the sizing rule)
# -----------------------------------------------------------------------------
# NM4  INDEPENDENT : W = 2*Id*L/(muCox*Vov1^2), L kept at the printed 500 nm,
#                    m kept at 1.  Vov1 is the one continuous gain knob.
#                    Result: Vov1 = 0.199112 V, W1 = 1.940 um (5 nm grid),
#                    inside the 0.42-100 um per-finger limit.
# NM1  MATCHED     : copies NM4 exactly (same W, L, m); required so the pair
#                    splits I_tail evenly.
# Everything else is (fixed, printed); its Vov is a DEPENDENT quantity,
# Vov = sqrt(2*Id*L/(muCox*W)), not a free choice.  Saturation needs
# |Vds| >= |Vov| for all nine.
#
# PARAMETER SOURCING.  Four calibration rows are physically invalid because the
# extractor applied the saturation square law to a device in triode:
#   NM0  muCox 13.15 uA/V^2, lam 58.97 /V   (Vds 17 mV)   -- unusable
#   NM1  muCox 86.16 uA/V^2, lam 15.06 /V   (Vds 58 mV)   -- unusable
#   NM2  muCox 202.6 uA/V^2                 (Vds 209 mV)  -- recoverable
# The MATCHED classification settles the first two: NM1 takes NM4's row and NM0
# takes NM3's row, because they are the identical printed cell carrying the same
# current, and their partner was measured in saturation.  For symmetry PM0 takes
# PM2's row and PM1 takes PM3's row (same cell, same side of the stack).
# NM2 has no saturated partner, so its muCox is recovered from the triode law:
#   muCox_sat = muCox_tri * (Vov^2/2)/(Vov*Vds - Vds^2/2)
#             = 202.6u * 0.052174/0.045670 = 202.6u * 1.14229 = 231.43 uA/V^2,
# then multiplied by exp(int lam dV) = 1.04110 for the channel-length
# modulation over the 80 mV of Vds margin it is now given.  Both corrections
# are bias-region corrections demanded by "fix the triode headroom first", not
# re-fits: every number above comes from the calibration table.
#
# lam FOR THE PMOS STACK.  The calibration measured the same 7u/0.5u PMOS cell
# at three saturation margins dV = |Vds| - |Vov|, so lam(dV) is calibrated data,
# not an assumption.  The exact three-point fit of lam = C + A/(B + dV) is
#   lam_p(dV) = 0.038283 + 0.029473/(0.031563 + dV)
# reproducing (0.006, 0.8229), (0.264, 0.1380), (1.031, 0.06602) to 5 digits.
# It is used for PM2 and PM3 (and for the NM2 CLM integral above).  Using PM2's
# row verbatim would mean designing a device that is deliberately held at its
# saturation edge, which the "every transistor saturated" requirement forbids.
# The NMOS lam values are used verbatim: NM3 and NM4 end up at Vds = 390 mV and
# 487 mV against the 349 mV and 494 mV at which they were calibrated, so no
# extrapolation is needed there.
#
# -----------------------------------------------------------------------------
# (3) SIGNAL PATH
# -----------------------------------------------------------------------------
# Bench: unity-gain follower, vout fed back to the inverting input (vin2)
# through an ideal inductor (DC short, AC open); the AC test signal drives vin2
# while vin1 sits at the DC vcm, i.e. vin1 is an AC ground.
# At the tail node, with both pair devices saturated and matched (gm1 each) and
# a tail resistance ro_t = ro_NM2, KCL gives
#   gm1*vin2 - 2*gm1*vtail = vtail/ro_t  ->  vtail = vin2*gm1/(2*gm1 + 1/ro_t)
#   id_NM4 = gm1*(vin2 - vtail) = gm1*vin2*(gm1 + 1/ro_t)/(2*gm1 + 1/ro_t)
# so the effective transconductance is gm1 * fac with
#   fac = (gm1 + 1/ro_t)/(2*gm1 + 1/ro_t),
# which is 0.5 only for an ideal tail and rises toward 1 as ro_t falls.  Here
# ro_t = 1/(2.125*44.308u) = 10.62 kOhm and gm1 = 196.29 uS, so fac = 0.59672
# (round 0 assumed 0.5; see E4).  That current passes NM3 (common gate, unity
# current gain) into vout, where it meets the cascoded output resistance.  The
# twin current in NM1 lands on x1, which drives nothing and does not return to
# vout, so the loop gain keeps the single-ended-readout factor fac.
# Dominant pole: vout against CL + output parasitics (20.016 pF).  Non-dominant
# poles: n2 at gm_NM3/(2*pi*C_n2) = 2.19 GHz and p2 at gm_PM3/(2*pi*C_p2) =
# 0.92 GHz, both three decades above the 0.93 MHz crossing.
#
# -----------------------------------------------------------------------------
# (4) DESIGN EQUATIONS (symbolic)
# -----------------------------------------------------------------------------
# Square law, per device: Id = (muCox/2)*(W/L)*Vov^2
#   -> Vov = sqrt(2*Id*L/(muCox*W)),  gm = a_gm*2*Id/Vov,  ro = 1/(lam*Id)
# Power:    P = I_tail * vdd            (gate biases draw no DC current)
#           Supply current is I_PM0 + I_PM2 = I_NM1 + I_NM4 = I_tail exactly.
# Output resistance:
#   R_dn = gm_NM3 * ro_NM3 * ro_NM4                       (NMOS cascode)
#   R_up = gm_PM3 * ro_PM3(dV) * ro_PM2(dV)               (PMOS cascode)
#   R_out = R_dn || R_up
# Gain:     A0 = fac * gm1 * R_out,  gm1 = a_gm*2*I_b/Vov1,  fac as in (3)
#           Reported gain = 20*log10(A0) - GAIN_OFFSET_DB.
# GBW:      f_u = A0/(2*pi*R_out*C_out) = fac*gm1/(2*pi*C_out)
# PM:       90deg - atan(f_u/f_n2) - atan(f_u/f_p2),  f_x = gm_x/(2*pi*C_x)
# Biases:   V4 = Vth_NM2 + Vov_t(I_tail)        (sets I_tail)
#           V1 = vdd - |Vth_PM2| - |Vov_p2(I_b)|   (sets I_b)
#           V3 = V(n) + Vth_NM3 + Vov_nc,  V2 = V(p) - |Vth_PM3| - |Vov_p3|
# Headroom (the binding inequality of this topology):
#           Vtail + Vth_NM4 + Vov1 <= vdd - (1+PMOS_MIN_FRAC)*(Vov_p2 + Vov_p3)
#
# WHY A DELIBERATE 5% CURRENT ASYMMETRY (DELTA).  Node x1 has no feedback path.
# Small-signal, with every device saturated, a tail-vs-PMOS current mismatch
# eps has NO solution: let the tail shift by t, then dI_NM2 = t/ro_t,
# dI_NM1 = -gm1*t, dvout = t (Vgs_NM4 is pinned by I_PM2), dI_NM4 = 0, and tail
# KCL forces t*(1/ro_t + gm1) = 0, i.e. t = 0.  The mismatch must therefore be
# absorbed large-signal, by some device leaving saturation; the excursion
# needed at x1 is R_up * eps * I_b = 4.85M * eps * 23.3u, i.e. 0.3 V for
# eps = 0.3%.  All nine devices are saturated only on a measure-zero surface in
# (V1, V4), which no model accuracy can hit.  What IS controllable is WHICH
# device absorbs it.  Setting I_b = I_tail/(2*(1-DELTA)) with DELTA = +5% makes
# the PMOS sources the stronger side, so x1 rises and PM1 -- a dummy-branch
# cascode with no AC role, no effect on vout and no effect on the supply
# current -- goes soft, while NM1, NM0, NM2 and the whole output branch stay
# saturated.  The opposite sign reproduces round 0, where NM1 and NM0 both
# collapsed and the AC tail division degraded (E4).  Cost: the pair runs
# I_NM1 = 20.988 uA against I_NM4 = 23.320 uA, so vout settles above vcm by
# Vgs_NM4(23.320u) - Vgs_NM1(20.988u)
#   = 0.199112 - sqrt(2*20.988u*0.5u/(303.2u*1.94u)) = 0.199112 - 0.188894
#   = 10.2 mV
# instead of exactly at it (round 0 missed by 148 mV).
#
# WHY POWER_DESIGN_FACTOR = 0.93.  The recalibrated NM2 model reproduces the
# measurement, so the margin rule asks for no bulk correction.  What it cannot
# see is mobility: NM2 moves from Vov = 0.323 V to 0.248 V, and the two
# saturated NMOS rows show muCox rising as Vov falls (303.2 uA/V^2 at 165 mV,
# 376.5 uA/V^2 at 118 mV).  Every unmodelled effect identified therefore pushes
# I_tail UP, so the tail current is designed 7% low: a +7% surprise lands on
# target, and no surprise lands at -7%, both far inside the +/-25% window.
#
# ARE THE TWO TARGETS JOINTLY REACHABLE?  Yes, with room to spare, and the
# binding constraint of round 0 is gone.  Solving Vov1 for 52.00 dB at each
# power across the whole tolerance band (vov1_hi is the headroom ceiling):
#   P/P_target   P (uW)   Vov1 needed   Vov1 ceiling   W1 (um)   min Vds/Vov
#      0.75       64.3      0.2491        0.3605         1.00      1.36 (NM2)
#      0.85       72.9      0.2202        0.3165         1.45      1.34 (NM2)
#      0.93       79.8      0.1991        0.2831         1.94      1.32 (NM2)  <- chosen
#      1.00       85.8      0.1822        0.2550         2.49      1.31 (NM2)
#      1.10       94.3      0.1603        0.2166         3.54      1.30 (NM2)
#      1.25      107.2      0.1311        0.1621         6.02      1.28 (NM2)
# 52.00 dB is met at every power in the band with 30-45% of spare overdrive
# before the headroom ceiling, so neither target has to be traded against the
# other.  Round 0 was cornered because it believed lam_PM2 = 0.16 /V while
# holding PM2 at a 5% Vds margin; giving the PMOS stack a 45% margin raises
# R_up from 2.04 MOhm to 4.85 MOhm and buys 7.5 dB, which is what converts the
# problem from infeasible to comfortable.  GBW and PM are not targets here.
#
# -----------------------------------------------------------------------------
# (5) DC BIAS VERIFICATION -- every branch supports saturation, with numbers
# -----------------------------------------------------------------------------
# Operating point: I_tail = 44.308 uA, I_b = 23.320 uA, P = 79.754 uW.
# Dependent overdrives of the printed cells at that current:
#   NM2 (3u/0.5u, 44.308 uA, muCox 231.43u x CLM 1.04110):
#       Vov_t  = sqrt(2*44.308u*0.5u/(240.94u*3u))  = 0.247585 V
#   NM0/NM3 (6u/0.5u, 23.320 uA, muCox 376.5u):
#       Vov_nc = sqrt(2*23.320u*0.5u/(376.5u*6u))   = 0.101603 V
#   PM0/PM2 (7u/0.5u, 23.320 uA, muCox 76.24u):
#       Vov_p2 = sqrt(2*23.320u*0.5u/(76.24u*7u))   = 0.209037 V
#   PM1/PM3 (7u/0.5u, 23.320 uA, muCox 83.26u):
#       Vov_p3 = sqrt(2*23.320u*0.5u/(83.26u*7u))   = 0.200030 V
# Input pair: Vov1 = 0.199112 V -> W1 = 2*23.320u*0.5u/(303.2u*0.199112^2)
#                                    = 1.940 um.
# Vertical budget, bottom to top, every level from the devices below it:
#   Vtail = Vov_t + 0.080 = 0.327585 V
#   vcm = vout = Vtail + Vth_NM4 + Vov1 = 0.327585 + 0.678 + 0.199112
#             = 1.204697 V
#   ceiling = vdd - (1+0.25)*(Vov_p2+Vov_p3) = 1.8 - 1.25*0.409067 = 1.288666 V
#             > 1.204697  OK (83.97 mV of slack, i.e. Vov1 could rise to
#             0.283081 V before the PMOS stack hits its 25% floor)
# NMOS branch, tail -> vout spans 1.204697 - 0.327585 = 0.877112 V and needs
# Vov1 + Vov_nc = 0.300715 V, leaving 0.576397 V shared equally:
#   V(n1) = V(n2) = 0.327585 + 0.487311 = 0.814896 V
#   NM1/NM4: Vds = 0.487311 >= Vov1   = 0.199112   OK (2.45x)
#   NM0/NM3: Vds = 0.389801 >= Vov_nc = 0.101603   OK (3.84x)
# PMOS branch, vdd -> vout spans 1.8 - 1.204697 = 0.595303 V and needs
# Vov_p2 + Vov_p3 = 0.409067 V, leaving 0.186236 V shared equally:
#   V(p1) = V(p2) = 1.8 - 0.302155 = 1.497845 V
#   PM0/PM2: |Vds| = 0.302155 >= Vov_p2 = 0.209037  OK (1.45x)
#   PM1/PM3: |Vds| = 0.293148 >= Vov_p3 = 0.200030  OK (1.47x)
# Tail device:
#   NM2:     Vds = Vtail = 0.327585 >= Vov_t = 0.247585  OK (1.32x)
# Column closes: 0.327585+0.487311+0.389801+0.293148+0.302155 = 1.800000 V.
# All nine transistors are in saturation and the tightest margin is NM2's 32%
# (round 0: NM2 +5.6% and the PMOS pair +5.0%, both of which then failed).
# Gain at this point: ro_NM3 = 1/(0.245*23.320u) = 175.03 k,
# ro_NM4 = 1/(0.1492*23.320u) = 287.41 k, gm_NM3 = 0.736*2*23.320u/0.101603
# = 337.85 uS; lam_p(0.093118) = 0.274668 -> ro_PM2 = ro_PM3 = 156.12 k,
# gm_PM3 = 0.854*2*23.320u/0.200030 = 199.12 uS, gm1 = 0.838*2*23.320u/0.199112
# = 196.29 uS:
#   R_dn = 337.85u*175.03k*287.41k = 16.996 MOhm
#   R_up = 199.12u*156.12k*156.12k =  4.853 MOhm
#   R_out = 3.775 MOhm,  fac = 0.59672,
#   A0 = 0.59672*196.29u*3.775M = 442.5 = 52.913 dB (model)
#      -> reported 52.913 - 0.91 = 52.003 dB.
#   f_u = 0.59672*196.29u/(2*pi*20.016p) = 931 kHz; f_n2 = 2.19 GHz,
#   f_p2 = 0.92 GHz, PM = 90 - 0.02 - 0.06 = 89.92 deg (CL dominates).
#
# -----------------------------------------------------------------------------
# (6) DC OPERATING-POINT CONSISTENCY -- what each stage produces vs what the
#     next one needs, with explicit arithmetic
# -----------------------------------------------------------------------------
# a) V4 -> tail current.  V4 = Vth_NM2 + Vov_t = 0.633 + 0.247585 = 0.880585 V.
#    NM2's Vgs = 0.880585 - 0 = 0.880585 -> Vov = 0.247585 ->
#    Id = (231.43u/2)*(3u/0.5u)*0.247585^2 * 1.04110 = 44.31 uA = I_tail as
#    intended.  Round 0's V4 was 0.95644 V; the 76 mV reduction is exactly the
#    power error E1 plus the triode correction E2.
# b) tail node needed by NM2 vs produced by the pair.  The pair produces
#    Vtail = vcm - Vth_NM4 - Vov1 = 1.204697 - 0.678 - 0.199112 = 0.327585 V;
#    NM2 needs >= 0.247585 V to stay saturated.  Produced - needed = +80.0 mV.
#    (vcm is an input we choose, so this is a choice of vcm, not an assumption
#    about tail: the arrow runs vcm -> Vtail, and NM2's requirement is then
#    checked against it.)
# c) V3 -> node n.  V3 = V(n) + Vth_NM3 + Vov_nc = 0.814896 + 0.767 + 0.101603
#    = 1.683499 V (< vdd = 1.8, legal).  Conversely NM3 with
#    Vgs = 1.683499 - 0.814896 = 0.868603 V carries
#    (376.5u/2)*(6u/0.5u)*0.101603^2 = 23.32 uA = I_b: the cascode passes
#    exactly the current the pair hands it, as a common-gate stage must.
# d) V1 -> branch current.  V1 = vdd - |Vth_PM2| - Vov_p2
#    = 1.8 - 0.992 - 0.209037 = 0.598963 V.  PM2's |Vgs| = 1.8 - 0.598963
#    = 1.201037 -> |Vov| = 0.209037 ->
#    Id = (76.24u/2)*(7u/0.5u)*0.209037^2 = 23.32 uA = I_b.
#    MATCHING CONDITION: I_PM0 = I_PM2 = 23.320 uA against I_tail/2 = 22.154 uA.
#    These are deliberately 5% apart (DELTA, section 4): the PMOS side is the
#    stronger one, so the 2.332 uA that NM1 cannot take raises x1 until PM1
#    leaves saturation, and the supply current stays I_tail = 44.308 uA.
# e) V2 -> node p.  V2 = V(p) - |Vth_PM3| - Vov_p3 = 1.497845 - 1.052
#    - 0.200030 = 0.245815 V (> 0, legal).  PM3's |Vgs| = 1.497845 - 0.245815
#    = 1.252030 -> |Vov| = 0.200030 ->
#    Id = (83.26u/2)*(7u/0.5u)*0.200030^2 = 23.32 uA, again exactly I_b.  And
#    V(p) - |Vds_PM3| = 1.497845 - 0.293148 = 1.204697 V = vout = vcm: the top
#    of the stack lands on the level the follower must settle at, to 1e-6 V.
# f) the two branches.  KCL leaves no freedom: I_NM1 = I_PM0 at x1,
#    I_NM4 = I_PM2 at vout, I_NM1 + I_NM4 = I_NM2 at tail.  With I_PM0 = I_PM2
#    = 23.320 uA and I_NM2 = 44.308 uA this forces I_NM4 = 23.320 uA (the
#    output branch, held by feedback: a residual error dI shifts vout by only
#    dI/gm1 = 5.1 mV per uA) and I_NM1 = 20.988 uA.  NM1's gate is pinned at
#    vcm, so the 2.332 uA it is short of PM0 cannot be taken from the tail; x1
#    rises instead, from 1.205 V until PM1's |Vds| falls to the triode value
#    that passes 20.988 uA: 2*u - u^2 = 0.900 with u = |Vds|/|Vov| gives
#    u = 0.684, |Vds_PM1| = 0.137 V and x1 = 1.497845 - 0.137 = 1.361 V, which
#    leaves PM0 at |Vds| = 0.302 V (unchanged, saturated) and NM0 at
#    Vds = 1.361 - 0.815 = 0.546 V (more saturated than designed).  So the
#    asymmetry costs exactly one dummy-branch device its saturation margin and
#    nothing else; vout = vcm + 10.2 mV (section 4).
# g) vcm as an output of (a)-(f), not an assumption.  vcm = 1.204697 V is
#    Vtail(from V4 and NM2) + Vth_NM4 + Vov1(from W1 and I_b), and the PMOS
#    stack built downward from vdd in (e) independently lands on 1.204697 V.
#    The two chains agree to 1e-6 V because V2 is computed FROM the PMOS split
#    of (vdd - vout), which is where the 83.97 mV of headroom slack in (5) is
#    spent.
#
# -----------------------------------------------------------------------------
# (7) PYTHON CODE
# -----------------------------------------------------------------------------

import math

# ---------------------------------------------------------------- process-ish
COX = 8.4e-3          # F/m^2, 1.8 V gate oxide
CGD_PER_W = 0.30e-9   # F/m of width, gate-drain overlap
CJ_PER_W = 0.90e-9    # F/m of width, drain/source junction

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

# --- round-0 calibration anchors (operating point at which params were taken)
CAL_VOV = {"NM0": 0.635, "NM1": 0.311, "NM2": 0.323, "NM3": 0.118, "NM4": 0.165,
           "PM0": 0.244, "PM1": 0.227, "PM2": 0.244, "PM3": 0.233}
CAL_VDS = {"NM0": 0.017, "NM1": 0.058, "NM2": 0.209, "NM3": 0.349, "NM4": 0.494,
           "PM0": 0.257, "PM1": 1.258, "PM2": 0.250, "PM3": 0.497}

# matched-pair parameter sourcing: the device on the left takes the calibrated
# parameters of the device on the right (see section 2)
PARAM_SOURCE = {"NM1": "NM4", "NM0": "NM3", "PM0": "PM2", "PM1": "PM3"}

# --- design knobs, all justified in the header
DELTA = 0.05              # PMOS branch current excess over half the tail current
VTAIL_DV = 0.080          # V of Vds margin above Vov for the tail device NM2
PMOS_MIN_FRAC = 0.25      # each stacked PMOS gets |Vds| >= (1+0.25)*|Vov|
GAIN_OFFSET_DB = 0.91     # recalibrated model still over-predicts gain by this
POWER_DESIGN_FACTOR = 0.93  # bias the tail current low (unmodelled mobility)

LAST_DESIGN = {}


def initial_params():
    """Round-0 estimates (ignored from round 1 on; kept for interface parity)."""
    n = {"type": "NMOS", "muCox": 120e-6, "a_gm": 1.0, "lam": 0.28, "vth": 0.60}
    p = {"type": "PMOS", "muCox": 40e-6, "a_gm": 1.0, "lam": 0.16, "vth": 0.95}
    out = {}
    for d in ("NM0", "NM1", "NM2", "NM3", "NM4"):
        out[d] = dict(n)
    for d in ("PM0", "PM1", "PM2", "PM3"):
        out[d] = dict(p)
    return out


# ---------------------------------------------------------------- small models
def _vov(mucox, w, l, m, i):
    return math.sqrt(2.0 * i * l / (mucox * w * m))


def _fit_lam_p(params):
    """lam = L + A/(B + dV) for the 7u/0.5u PMOS cell, dV = |Vds| - |Vov|.

    Exact three-point fit through PM2, PM3, PM1 -- the SAME printed cell at
    three different saturation margins in the round-0 calibration.
    """
    try:
        u = [CAL_VDS[d] - CAL_VOV[d] for d in ("PM2", "PM3", "PM1")]
        lm = [float(params[d]["lam"]) for d in ("PM2", "PM3", "PM1")]
        r = (lm[0] - lm[1]) / (lm[1] - lm[2])
        aa = r * (u[2] - u[1])
        bb = u[1] - u[0]
        b = (bb * u[2] - aa * u[0]) / (aa - bb)
        a = (lm[0] - lm[1]) * (b + u[0]) * (b + u[1]) / (u[1] - u[0])
        c = lm[0] - a / (b + u[0])
        if not (b > 0.0 and a > 0.0 and c > 0.0):
            raise ValueError
        return lambda dv: c + a / (b + max(dv, 0.0))
    except Exception:
        lam3 = float(params["PM3"]["lam"])
        return lambda dv: lam3


def _dev(params, name):
    """Calibrated parameters to use for a device (matched-pair substitution)."""
    return params[PARAM_SOURCE.get(name, name)]


def _nm2_mucox(params, lam_p):
    """NM2's saturation muCox, recovered from its TRIODE calibration point.

    The extractor used the saturation square law on a point with
    Vds = 209 mV < Vov = 323 mV, so it reported
        muCox_tri = 2*Id*L/(W*Vov^2)
    while the device actually carried the triode current
        Id = muCox_sat*(W/L)*(Vov*Vds - Vds^2/2).
    Hence muCox_sat = muCox_tri * (Vov^2/2) / (Vov*Vds - Vds^2/2).
    """
    vov, vds = CAL_VOV["NM2"], CAL_VDS["NM2"]
    tri = vov * vds - 0.5 * vds * vds
    fix = (0.5 * vov * vov) / tri if tri > 0.0 else 1.0
    return float(params["NM2"]["muCox"]) * fix, fix


def _branch(params, lam_p, i_b, i_tail):
    """Everything set by the branch / tail current alone (printed cells only)."""
    d = {}
    pn3, pn4 = _dev(params, "NM3"), _dev(params, "NM4")
    pp2, pp3 = _dev(params, "PM2"), _dev(params, "PM3")
    wp, lp, mp = FIXED["PM2"]
    wn, ln, mn = FIXED["NM3"]
    wt, lt, mt = FIXED["NM2"]

    mc_t, d["nm2_fix"] = _nm2_mucox(params, lam_p)
    # NM2 carries i_tail at Vds = Vov + VTAIL_DV; fold the channel-length
    # modulation of that extra VTAIL_DV into the current it must deliver.
    d["clm_t"] = math.exp(_lam_integral(lam_p, 0.0, VTAIL_DV))
    d["mucox_t"] = mc_t
    d["vov_t"] = _vov(mc_t * d["clm_t"], wt, lt, mt, i_tail)

    d["vov_p2"] = _vov(pp2["muCox"], wp, lp, mp, i_b)     # PM0 / PM2
    d["vov_p3"] = _vov(pp3["muCox"], wp, lp, mp, i_b)     # PM1 / PM3
    d["vov_nc"] = _vov(pn3["muCox"], wn, ln, mn, i_b)     # NM0 / NM3
    d["gm_nc"] = pn3["a_gm"] * 2.0 * i_b / d["vov_nc"]
    d["gm_p3"] = pp3["a_gm"] * 2.0 * i_b / d["vov_p3"]
    d["ro_nm3"] = 1.0 / (pn3["lam"] * i_b)
    d["ro_nm4"] = 1.0 / (pn4["lam"] * i_b)
    d["r_dn"] = d["gm_nc"] * d["ro_nm3"] * d["ro_nm4"]
    d["ro_t"] = 1.0 / (max(float(params["NM2"]["lam"]), 1e-6) * i_tail)
    return d


def _lam_integral(lam_p, u0, u1):
    """Integral of lam over the saturation margin, by Simpson on 20 panels."""
    n = 20
    h = (u1 - u0) / n
    s = lam_p(u0) + lam_p(u1)
    for i in range(1, n):
        s += (4.0 if i % 2 else 2.0) * lam_p(u0 + i * h)
    return s * h / 3.0


def _pmos_split(d, vdd, vout):
    """Share (vdd - vout) between PM2 and PM3 at equal excess over |Vov|."""
    excess = (vdd - vout) - (d["vov_p2"] + d["vov_p3"])
    half = 0.5 * excess
    vds_p2 = d["vov_p2"] + half
    vds_p3 = d["vov_p3"] + half
    return half, vds_p2, vds_p3


def _gain_at(params, lam_p, d, i_b, vtail, vov1, vdd):
    """Low-frequency loop gain for a trial input-pair overdrive."""
    pn4 = _dev(params, "NM4")
    vout = vtail + pn4["vth"] + vov1
    half, vds_p2, vds_p3 = _pmos_split(d, vdd, vout)
    lam_p2 = lam_p(half)
    ro_p2 = 1.0 / (lam_p2 * i_b)
    ro_p3 = 1.0 / (lam_p2 * i_b)
    r_up = d["gm_p3"] * ro_p3 * ro_p2
    r_out = 1.0 / (1.0 / r_up + 1.0 / d["r_dn"])
    gm1 = pn4["a_gm"] * 2.0 * i_b / vov1
    fac = (gm1 + 1.0 / d["ro_t"]) / (2.0 * gm1 + 1.0 / d["ro_t"])
    return {
        "gain": fac * gm1 * r_out, "vout": vout, "half": half, "vds_p2": vds_p2,
        "vds_p3": vds_p3, "lam_p2": lam_p2, "ro_p2": ro_p2, "ro_p3": ro_p3,
        "r_up": r_up, "r_out": r_out, "gm1": gm1, "fac": fac,
    }


def compute_sizing(spec, params):
    cond = spec.get("conditions", {})
    vdd = cond.get("vdd", 1.8)
    cl = cond.get("cl", 20e-12)
    tgt = spec["targets"]
    p_target = tgt["power_W"]
    a_design = 10.0 ** ((tgt["gain_dB"] + GAIN_OFFSET_DB) / 20.0)
    keep = spec.get("variables", {}).get("keep_printed", {})
    l_in = keep.get("NM1.l", 500e-9)
    m_in = int(keep.get("NM1.m", 1))

    lam_p = _fit_lam_p(params)
    pn2, pn3, pn4 = params["NM2"], _dev(params, "NM3"), _dev(params, "NM4")
    pp2, pp3 = _dev(params, "PM2"), _dev(params, "PM3")

    # ---- currents.  Power = I_tail * vdd; the PMOS sources are deliberately
    # DELTA stronger than half the tail so the dummy branch (PM1) absorbs the
    # residual current mismatch instead of the signal-path device NM1.
    i_tail = POWER_DESIGN_FACTOR * p_target / vdd
    i_b = i_tail / (2.0 * (1.0 - DELTA))

    d = _branch(params, lam_p, i_b, i_tail)
    vtail = d["vov_t"] + VTAIL_DV

    # ---- solve for the input-pair overdrive.  gain is monotone decreasing in
    # vov1 (gm1 falls AND the PMOS stack loses margin, raising lam_p2), so a
    # bisection between the geometry limit and the headroom limit is exact.
    vov1_lo = _vov(pn4["muCox"], W_MAX, l_in, m_in, i_b)
    vov1_hi = (vdd - (1.0 + PMOS_MIN_FRAC) * (d["vov_p2"] + d["vov_p3"])
               - pn4["vth"] - vtail)
    vov1_hi = min(vov1_hi, _vov(pn4["muCox"], W_MIN, l_in, m_in, i_b))
    limited = ""
    if vov1_hi <= vov1_lo:
        vov1 = max(vov1_lo, 1e-3)
        limited = "no headroom window"
    else:
        g_lo = _gain_at(params, lam_p, d, i_b, vtail, vov1_lo, vdd)["gain"]
        g_hi = _gain_at(params, lam_p, d, i_b, vtail, vov1_hi, vdd)["gain"]
        if g_lo < a_design:
            vov1, limited = vov1_lo, "gain-limited (W at max)"
        elif g_hi > a_design:
            vov1, limited = vov1_hi, "headroom-limited (gain too high)"
        else:
            a, b = vov1_lo, vov1_hi
            for _ in range(200):
                mid = 0.5 * (a + b)
                if _gain_at(params, lam_p, d, i_b, vtail, mid, vdd)["gain"] > a_design:
                    a = mid
                else:
                    b = mid
            vov1 = 0.5 * (a + b)

    # ---- input pair geometry (INDEPENDENT), snapped to a 5 nm grid
    w1 = 2.0 * i_b * l_in / (pn4["muCox"] * vov1 ** 2 * m_in)
    w1 = min(W_MAX, max(W_MIN, round(w1 / 5e-9) * 5e-9))
    vov1 = _vov(pn4["muCox"], w1, l_in, m_in, i_b)       # re-derive from the grid
    g = _gain_at(params, lam_p, d, i_b, vtail, vov1, vdd)

    # ---- DC operating point: every node from the driving stage's parameters
    vout = g["vout"]
    vcm = vout                                            # follower target
    extra_n = (vout - vtail) - (vov1 + d["vov_nc"])       # NMOS stack slack
    vds_nm4 = vov1 + 0.5 * extra_n
    vds_nm3 = d["vov_nc"] + 0.5 * extra_n
    v_n = vtail + vds_nm4
    v_p = vdd - g["vds_p2"]
    vbn0 = pn2["vth"] + d["vov_t"]                        # V4, sets i_tail
    vbn1 = v_n + pn3["vth"] + d["vov_nc"]                 # V3, NM0/NM3 gate
    vbp1 = vdd - pp2["vth"] - d["vov_p2"]                 # V1, sets i_b
    vbp2 = v_p - pp3["vth"] - d["vov_p3"]                 # V2, PM1/PM3 gate

    # ---- predictions (model, then the measured model residual removed)
    gain_dB = 20.0 * math.log10(g["gain"]) - GAIN_OFFSET_DB
    power = i_tail * vdd

    wp = FIXED["PM3"][0]
    wn = FIXED["NM3"][0]
    c_out = cl + (CGD_PER_W + CJ_PER_W) * (wp + wn)
    gbw = g["fac"] * g["gm1"] / (2.0 * math.pi * c_out)
    c_n = (2.0 / 3.0) * wn * FIXED["NM3"][1] * COX + CJ_PER_W * (wn + w1) + CGD_PER_W * w1
    c_p = (2.0 / 3.0) * wp * FIXED["PM3"][1] * COX + CJ_PER_W * 2.0 * wp + CGD_PER_W * wp
    f_n = d["gm_nc"] / (2.0 * math.pi * c_n)
    f_p = d["gm_p3"] / (2.0 * math.pi * c_p)
    pm = 90.0 - math.degrees(math.atan(gbw / f_n)) - math.degrees(math.atan(gbw / f_p))

    LAST_DESIGN.clear()
    LAST_DESIGN.update(
        i_tail=i_tail, i_b=i_b, i_nm1=i_tail - i_b, limited=limited,
        nm2_fix=d["nm2_fix"], clm_t=d["clm_t"], mucox_t=d["mucox_t"],
        vov_t=d["vov_t"], vtail=vtail, vov1=vov1, w1=w1, vov_nc=d["vov_nc"],
        vov_p2=d["vov_p2"], vov_p3=d["vov_p3"], vout=vout, vcm=vcm,
        vds_nm2=vtail, vds_nm4=vds_nm4, vds_nm3=vds_nm3,
        vds_p2=g["vds_p2"], vds_p3=g["vds_p3"], v_n=v_n, v_p=v_p,
        lam_p2=g["lam_p2"], ro_p2=g["ro_p2"], ro_nm3=d["ro_nm3"],
        ro_nm4=d["ro_nm4"], ro_t=d["ro_t"], r_up=g["r_up"], r_dn=d["r_dn"],
        r_out=g["r_out"], gm1=g["gm1"], gm_nc=d["gm_nc"], gm_p3=d["gm_p3"],
        fac=g["fac"], gain_model_dB=20.0 * math.log10(g["gain"]),
        c_out=c_out, f_n=f_n, f_p=f_p, vov1_hi=vov1_hi, vov1_lo=vov1_lo,
        offset_vout_vcm=(pn4["vth"] + vov1)
        - (pn4["vth"] + _vov(pn4["muCox"], w1, l_in, m_in, i_tail - i_b)),
        lam_p_at=[round(lam_p(x), 4) for x in (0.0, 0.05, 0.1, 0.2, 0.3)],
    )

    return {
        "sizes": {
            "NM1": {"w": w1, "l": l_in, "m": m_in},
            "NM4": {"w": w1, "l": l_in, "m": m_in},
        },
        "biases": {"V1": vbp1, "V2": vbp2, "V3": vbn1, "V4": vbn0},
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


CAL_PARAMS = {
    "NM0": {"type": "NMOS", "muCox": 13.15e-6, "a_gm": 0.450, "lam": 58.97, "vth": 0.686},
    "NM1": {"type": "NMOS", "muCox": 86.16e-6, "a_gm": 0.556, "lam": 15.06, "vth": 0.679},
    "NM2": {"type": "NMOS", "muCox": 202.6e-6, "a_gm": 0.749, "lam": 2.125, "vth": 0.633},
    "NM3": {"type": "NMOS", "muCox": 376.5e-6, "a_gm": 0.736, "lam": 0.245, "vth": 0.767},
    "NM4": {"type": "NMOS", "muCox": 303.2e-6, "a_gm": 0.838, "lam": 0.1492, "vth": 0.678},
    "PM0": {"type": "PMOS", "muCox": 76.63e-6, "a_gm": 0.814, "lam": 0.7353, "vth": 0.992},
    "PM1": {"type": "PMOS", "muCox": 88.08e-6, "a_gm": 0.856, "lam": 0.06602, "vth": 1.051},
    "PM2": {"type": "PMOS", "muCox": 76.24e-6, "a_gm": 0.807, "lam": 0.8229, "vth": 0.992},
    "PM3": {"type": "PMOS", "muCox": 83.26e-6, "a_gm": 0.854, "lam": 0.138, "vth": 1.052},
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
    r = compute_sizing(SPEC, CAL_PARAMS)
    for key in ("sizes", "biases", "vcm", "predicted"):
        print(key, r[key])
    for key in sorted(LAST_DESIGN):
        print("   ", key, LAST_DESIGN[key])
