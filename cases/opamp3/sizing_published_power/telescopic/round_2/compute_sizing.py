# =============================================================================
# Telescopic cascode OTA (Fig. 2) -- round 2 sizing of NM1/NM4 and V1..V4.
# Targets: gain 52.0 dB +/-3 dB, power 85.7568 uW +/-25% (fitted), vdd 1.8 V,
# CL 20 pF, vcm free.  Process: sky130 1.8 V devices, all L = 500 nm.
# Every number quoted below is produced by this file from the round-1
# calibration table as printed; run it as a script to reproduce them.  The
# executed run is handed the same rows at full precision, which moves W1 from
# 2.845 um to 2.855 um, the four biases by at most 0.3 mV and the predicted
# gain from 52.294 dB to 52.305 dB.  Nothing else changes.
#
# WHAT THE ROUND-1 CALIBRATION SAID ROUND 1 GOT WRONG (quantified)
#
# Round 1 predicted 52.007 dB / 79.754 uW and measured 48.704 dB / 81.133 uW:
# gain over-predicted by 3.30 dB, power under-predicted by 1.7%, 7 of 9 devices
# saturated (PM0 and PM1, both in the dummy branch, flagged TRIODE).  Five
# separate errors, all now closed by the new table:
#
# E1  lam OF THE PMOS STACK AT THE REALIZED MARGIN -- most of the gain error.
#     Round 1 fitted lam_p(dV) = 0.038283 + 0.029473/(0.031563 + dV) to three
#     round-0 points of the same printed 7u/0.5u cell and designed the stack at
#     dV = |Vds| - |Vov| = 93 mV, expecting lam = 0.2747.  Measured: PM2 at
#     dV = 286-209 = 77 mV gives lam = 0.3606 and PM3 at 282-208 = 74 mV gives
#     0.3880, mean 0.3743 at dV = 75.5 mV, where that fit says 0.3136 -- the
#     fit under-states lam by 19% in this region, and the realized margin was
#     75 mV not 93.  Together: ro_PM = 106.4 k instead of 156.1 k, so
#     R_up = 2.234 MOhm instead of the 4.853 MOhm predicted (-6.74 dB on R_up,
#     -5.53 dB on R_out).  The round-0 shape is kept below but RESCALED by
#     0.3743/0.3136 = 1.1937 so it passes through this round's measurement.
# E2  THE BRANCH CURRENT, hence the realized asymmetry and the two TRIODE
#     flags.  Round 1 sized V1 with muCox_PM2 = 76.24 uA/V^2 (round 0) for
#     I_b = 23.320 uA; the new table gives muCox_PM2 = 82.08 uA/V^2 (+7.7%) at
#     the same |Vov| = 209 mV, and I_b came out 25.1 uA (+7.6%), while the tail
#     came out 45.1 uA (+1.8%).  So the designed +5% PMOS-over-NMOS asymmetry
#     was realized as 25.1/22.55 = +11.3%, and the dummy branch had to shed
#     1 - 19.9/25.1 = 21% of PM0's saturation current.  That is why BOTH dummy
#     PMOS went triode, not just PM1 as round 1 predicted (section 6f).
# E3  NM2's muCox -- the whole power error, and it is small.  Round 1 recovered
#     muCox_sat = 231.43 uA/V^2 from NM2's round-0 TRIODE point and multiplied
#     it by a 1.0411 CLM factor, i.e. designed with 240.94 uA/V^2.  NM2 is now
#     SAT and measures 244.50 uA/V^2 at Vov = 248 mV, 1.48% higher; the power
#     came in 1.73% high.  The triode recovery was therefore right to within
#     0.25%, and the power model needs no bulk correction, only that 0.3%
#     (POWER_DESIGN_FACTOR = 0.997).
# E4  THE TAIL DIVISION FACTOR.  Round 1 took ro_t from the round-0
#     lam_NM2 = 2.125 /V, itself extracted at a triode point, giving
#     ro_t = 10.62 k and fac = 0.5967.  With NM2 now saturated,
#     lam_NM2 = 0.3893 /V, ro_t = 1/(0.3893*45.1u) = 56.96 k, and with the
#     measured gm_NM4 = 202.66 uS, gm_NM1 = 180.89 uS,
#     fac = (gm_NM1 + 1/ro_t)/(gm_NM4 + gm_NM1 + 1/ro_t) = 0.49475.
#     Round 1 over-stated fac by 21% (+1.63 dB).
# E5  THE RESIDUAL AFTER E1+E4, WHICH NOW HAS THE OPPOSITE SIGN.  Replaying
#     round 1's own gain equation at the MEASURED operating point with the new
#     table (I_b = 25.1 uA, I_tail = 45.1 uA, measured Vov's, so every gm
#     reproduces the measured gm to 0.1%):
#       gm_nc  = 0.674*2*25.1u/0.099 = 341.8 uS
#       ro_NM3 = 1/(0.1903*25.1u) = 209.36 k, ro_NM4 = 1/(0.1521*25.1u)
#              = 261.94 k  ->  R_dn = 18.742 MOhm
#       gm_PM3 = 0.817*2*25.1u/0.208 = 197.2 uS, ro_PM = 1/(0.3743*25.1u)
#              = 106.44 k ->  R_up = 2.234 MOhm,  R_out = 1.9960 MOhm
#       A0 = 0.49475*202.66u*1.9960M = 200.1 = 46.026 dB
#     against a measured 48.704 dB: the recalibrated model now UNDER-predicts
#     by 2.678 dB.  That residual is carried as a multiplicative correction on
#     the output resistance, K_OUT = 10^(2.678/20) = 1.3611, not as a dB offset
#     on the reported number, because the quantity in error is R_out.
#     PHYSICAL READING: the square-law model omits the cascode body effect.
#     Both cascodes have Vsb != 0 (NM3's source sits at 0.81 V above its body;
#     PM3's source sits 0.30 V below vdd), and a cascode's resistance boost is
#     (gm+gmb)*ro, not gm*ro.  With gmb/gm = gamma/(2*sqrt(2*phi_F+Vsb)) and
#     gamma ~ 0.5 V^0.5, 2*phi_F ~ 0.7 V, that is +20% on R_dn and +25% on
#     R_up, i.e. ~1.24x on R_out = 1.90 dB of the 2.678 dB.  The remaining
#     0.78 dB is not explained; K_OUT carries both, and it is applied
#     multiplicatively so it tracks the operating point instead of being
#     frozen in dB.  ROBUSTNESS: the design below is solved for 52.3 dB WITH
#     K_OUT, so if K_OUT turned out to be entirely spurious (K = 1) the circuit
#     would still land at 52.3 - 2.678 = 49.62 dB, inside the 49-55 dB window.
#     That is why 52.3 dB is used as the design point rather than 52.0 dB.
#
# -----------------------------------------------------------------------------
# (1) DEVICE ROLES
# -----------------------------------------------------------------------------
# NM2  (3u/0.5u, gate vbn0=V4)      tail current sink; its gate bias sets
#                                   I_tail and therefore the supply power, which
#                                   is I_tail*vdd exactly (both branches return
#                                   through it).
# NM1, NM4 (VARIABLE, L=500n, m=1)  NMOS input pair, gates vin1/vin2, common
#                                   source at tail.  NM4 is the inverting-input
#                                   device, carries the AC signal and drives the
#                                   measured output; NM1 drives the dummy branch
#                                   (node x1) and is a DC-only device.
# NM0, NM3 (6u/0.5u, gate vbn1=V3)  NMOS cascodes; multiply the sink-side output
#                                   resistance of NM1/NM4 by (gm+gmb)*ro.
# PM1, PM3 (7u/0.5u, gate vbp2=V2)  PMOS cascodes; same for the source side.
# PM0, PM2 (7u/0.5u, gate vbp1=V1)  PMOS current sources, each sized by V1 to
#                                   deliver I_b.
# Nodes: tail (pair source), n1/n2 (pair drains = NMOS cascode sources), p1/p2
# (PMOS source drains = PMOS cascode sources), x1 (dummy-branch output: no load,
# no feedback, no path to vout), vout (loaded by CL and fed back to vin2).
# There is NO mirror in this circuit: the sink current (V4) and the source
# current (V1) are set by two independent gate biases, so I_PM0 = I_PM2 =
# I_tail/2 is a DESIGN equation that nothing in the circuit enforces.  PM0 and
# PM2 share one gate and are the identical printed cell, so I_PM0,sat =
# I_PM2,sat is enforced; this is the root of section 6f.
#
# -----------------------------------------------------------------------------
# (2) DEVICE CONSTRAINTS  (classification per the sizing rule)
# -----------------------------------------------------------------------------
# NM4  INDEPENDENT : W = 2*Id*L/(muCox*Vov1^2), L kept at the printed 500 nm,
#                    m kept at 1.  Vov1 is the one continuous gain knob.
#                    Result: Vov1 = 0.172165 V, W1 = 2.845 um (5 nm grid),
#                    inside the 0.42-100 um per-finger limit.
# NM1  MATCHED     : copies NM4 exactly (same W, L, m).  It does NOT carry the
#                    same current (section 6f), so its Vov is computed at its
#                    own current from the same W.
# The other seven devices are (fixed, printed); their Vov is DEPENDENT,
# Vov = sqrt(2*Id*L/(muCox*W)), not a free choice.  Saturation needs
# |Vds| >= |Vov| for all nine.
#
# PARAMETER SOURCING.  Seven of the nine calibration rows are from saturated
# devices and are used verbatim.  Two are physically invalid because the
# extractor applied the saturation square law to a device in triode:
#   PM0  muCox 65.43 uA/V^2, lam 4.153 /V  (|Vds| 135 mV < |Vov| 209 mV)
#   PM1  muCox 18.51 uA/V^2, lam 16.91 /V  (|Vds|  54 mV < |Vov| 392 mV)
# The MATCHED classification settles both: PM0 takes PM2's row and PM1 takes
# PM3's row -- the identical printed cell at the same position in the stack,
# measured in saturation in the other branch.  NM0 also takes NM3's row for the
# same reason; NM0's own row (SAT, 531.9 uA/V^2 at Vov = 79 mV) is kept out of
# the signal-path model but used as the independent confirmation of the
# mobility trend below.
#
# MOBILITY IS A FUNCTION OF Vov IN THIS TABLE, and the input pair is the one
# device whose Vov this round changes.  Same 6u/0.5u cell: 531.9 uA/V^2 at
# Vov = 79 mV, 431.7 at 99 mV.  Same 1.95u/0.5u cell (the pair itself):
#   NM1  muCox 286.7 uA/V^2, a_gm 0.859  at Vov = 189 mV
#   NM4  muCox 276.0 uA/V^2, a_gm 0.872  at Vov = 216 mV
# so for the pair cell muCox(Vov) = 276.0 - 396.3*(Vov - 0.216) uA/V^2 and
# a_gm(Vov) = 0.872 + 0.481*(Vov - 0.216), both two-point fits of the same cell,
# clamped to [250, 330] uA/V^2 and [0.820, 0.900].  Cross-check against round 0,
# which measured this geometry at Vov = 165 mV and got 303.2 uA/V^2: the fit
# extrapolates 296.2, 2.3% low -- good enough over the 13 mV this round moves.
# At the chosen Vov1 = 172.2 mV the fit gives 293.4 uA/V^2 and a_gm = 0.851.
# Round 1's W1 is the proof that the square law itself is exact once muCox is
# right: W = 1.95 um at I_b = 25.1 uA with muCox = 276 predicts
# Vov = sqrt(2*25.1u*0.5u/(276u*1.95u)) = 0.21596 V, and 216 mV was measured.
#
# lam FOR THE PMOS STACK.  Four same-cell measurements now exist for the
# 7u/0.5u PMOS, as a function of the saturation margin dV = |Vds| - |Vov|:
#   round 0: (0.006, 0.8229), (0.264, 0.1380), (1.031, 0.06602)
#   round 1: (0.077, 0.3606), (0.074, 0.3880)   <- closest to the design point
# The round-0 three-point fit lam = C + A/(B+dV) is kept for its SHAPE and
# rescaled by 1.1937 so it reproduces the round-1 mean (0.3743 at 75.5 mV)
# exactly.  This round's design margin is 88.3 mV, so the shape is only trusted
# over the 13 mV between the anchor and the design point (0.3743 -> 0.3393, a
# 9% move); nothing is extrapolated beyond the measured span.
# The NMOS lam values are used verbatim and need no extrapolation either: this
# design puts NM4 at Vds = 475 mV and NM3 at 401 mV against the 490 mV and
# 431 mV at which they were calibrated, and NM2 at a Vds margin of 80 mV
# against the 63 mV at which lam_NM2 = 0.3893 was taken.
#
# -----------------------------------------------------------------------------
# (3) SIGNAL PATH
# -----------------------------------------------------------------------------
# Bench: unity-gain follower, vout fed back to the inverting input (vin2)
# through an ideal inductor (DC short, AC open); the AC test signal drives vin2
# while vin1 sits at the DC vcm, i.e. vin1 is an AC ground.
# At the tail node, with the two pair devices carrying DIFFERENT currents (gm4
# and gm1n) and a tail resistance ro_t = ro_NM2, KCL gives
#   gm4*(vin2 - vtail) - gm1n*vtail = vtail/ro_t
#   -> vtail = vin2*gm4/(gm4 + gm1n + 1/ro_t)
#   -> id_NM4 = gm4*(vin2 - vtail) = gm4*vin2*fac,
#      fac = (gm1n + 1/ro_t)/(gm4 + gm1n + 1/ro_t)
# which is 0.5 only for an ideal tail and a matched partner.  Validated on the
# round-1 measurement: fac = (180.89u + 17.557u)/(202.66u + 180.89u + 17.557u)
# = 0.49475, and this design gives 0.50874.  Round 1's 0.5967 was wrong through
# a triode-extracted ro_t (E4).
# That current passes NM3 (common gate, unity current gain) into vout, where it
# meets the cascoded output resistance.  The twin current in NM1 lands on x1,
# which drives nothing and does not return to vout, so the loop gain keeps the
# single-ended-readout factor fac.  x1's two PMOS being soft (section 6f)
# therefore does not enter the AC path at all.
# Dominant pole: vout against CL + output parasitics (20.024 pF).  Non-dominant
# poles: n2 at gm_NM3/(2*pi*C_n2) = 2.12 GHz and p2 at gm_PM3/(2*pi*C_p2)
# = 0.91 GHz, both three decades above the 0.99 MHz crossing.
#
# -----------------------------------------------------------------------------
# (4) DESIGN EQUATIONS (symbolic)
# -----------------------------------------------------------------------------
# Square law, per device: Id = (muCox/2)*(W/L)*Vov^2
#   -> Vov = sqrt(2*Id*L/(muCox*W)),  gm = a_gm*2*Id/Vov,  ro = 1/(lam*Id)
# Power:    P = I_tail*vdd  (gate biases draw no DC current, and the supply
#           current is I_PM0 + I_PM2 = I_NM1 + I_NM4 = I_NM2 = I_tail exactly,
#           whatever the branch asymmetry does).
# Output resistance:
#   R_dn  = gm_NM3*ro_NM3*ro_NM4                      (NMOS cascode)
#   R_up  = gm_PM3*ro_PM3(dV)*ro_PM2(dV)              (PMOS cascode)
#   R_out = K_OUT*(R_dn || R_up),  K_OUT from E5 (cascode body effect)
# Gain:     A0 = fac*gm1*R_out,  gm1 = a_gm(Vov1)*2*I_b/Vov1,  fac as in (3)
# GBW:      f_u = A0/(2*pi*R_out*C_out) = fac*gm1/(2*pi*C_out)
# PM:       90deg - atan(f_u/f_n2) - atan(f_u/f_p2),  f_x = gm_x/(2*pi*C_x)
# Biases:   V4 = Vth_NM2 + Vov_t(I_tail)              (sets I_tail)
#           V1 = vdd - |Vth_PM2| - |Vov_p2(I_b)|      (sets I_b)
#           V3 = V(n2) + Vth_NM3 + Vov_nc
#           V2 = V(p2) - |Vth_PM3| - |Vov_p3|
# Headroom (the binding inequality of this topology):
#           Vtail + Vth_NM4 + Vov1 <= vdd - (1+PMOS_MIN_FRAC)*(Vov_p2 + Vov_p3)
# Monotonicity that makes the solve exact: raising Vov1 lowers gm1 AND raises
# vout, which shrinks the PMOS saturation margin and raises lam_p, so the gain
# is strictly decreasing in Vov1 and a bisection between the W_MAX end and the
# headroom end is unique.
#
# WHY A DELIBERATE 4% CURRENT ASYMMETRY (DELTA), AND WHY ONLY 4%.  Node x1 has
# no feedback path.  Small-signal, with every device saturated, a tail-vs-PMOS
# current mismatch has no solution: let the tail shift by t, then
# dI_NM2 = t/ro_t, dI_NM1 = -gm1n*t, dI_NM4 = 0 (Vgs_NM4 is pinned by I_PM2),
# and tail KCL forces t*(1/ro_t + gm1n) = 0, i.e. t = 0.  The mismatch must be
# absorbed large-signal, by a device leaving saturation, and the only choice
# available to the designer is WHICH one.  I_b = I_tail/(2*(1-DELTA)) with
# DELTA = +4% makes the PMOS sources the stronger side, so x1 rises and the
# dummy branch's PM0/PM1 go soft (section 6f) while NM1, NM0, NM2 and the whole
# output branch stay saturated.  The opposite sign reproduces round 0, where
# NM0 and NM1 both collapsed, NM2 was dragged into triode and the follower
# missed vcm by 148 mV.  DELTA is cut from round 1's 5% to 4% because the two
# currents are now set from saturated rows measured at this round's own
# operating point (I_b from muCox_PM2 = 82.08 at |Vov| = 209 mV, designed at
# 207.5 mV; I_tail from muCox_NM2 = 244.5 at Vov = 248 mV, designed at
# 253.6 mV), so the residual uncertainty in the match is ~2-3% rather than the
# 8% round 1 carried, and a smaller DELTA shrinks the follower offset:
#   vout - vcm = Vov1 - Vov_NM1 = 0.172165 - 0.164260 = 7.9 mV
# against the 27 mV measured in round 1 (which still passed).
#
# ARE THE TWO TARGETS JOINTLY REACHABLE?  Yes, everywhere in the power band.
# This file's own solve, run at seven values of POWER_DESIGN_FACTOR (vov1_ceil
# is the headroom ceiling above, half is the resulting PMOS saturation margin,
# min ratio is the tightest |Vds|/|Vov| among the seven devices that can be
# saturated at all -- it is always NM2, the tail):
#   P/P_target   P (uW)     Vov1     Vov1 ceiling  W1 (um)  half (mV)  gain(dB)  min ratio
#      0.750      64.32   0.237910    0.347543      1.230     99.7     52.3181    1.364
#      0.850      72.89   0.208794    0.304374      1.735     95.5     52.3145    1.342
#      0.950      81.47   0.183216    0.263677      2.430     90.7     52.2989    1.323
#      0.997      85.50   0.172165    0.245291      2.845     88.3     52.2937    1.315  <- chosen
#      1.050      90.04   0.160213    0.225071      3.405     85.5     52.3051    1.307
#      1.150      98.62   0.139694    0.188265      4.775     79.8     52.2989    1.294
#      1.250     107.20   0.121141    0.153026      6.740     73.8     52.2986    1.282
# 52.3 dB is met at every power in the band with 26-46% of spare overdrive
# before the headroom ceiling, so neither target has to be traded against the
# other and the NOMINAL power is chosen: the power model is now accurate to
# 0.3% (E3), so there is no reason to sit off-centre in the power window.  The
# chosen point also keeps every lam in the table within a few mV of the Vds at
# which it was measured (section 2), which is the real reason to prefer it over
# the low-power end: at P/P_target = 0.75 the PMOS margin would be 99.7 mV,
# 24 mV away from the lam anchor.
#
# -----------------------------------------------------------------------------
# (5) DC BIAS VERIFICATION -- every branch supports saturation, with numbers
# -----------------------------------------------------------------------------
# Operating point: I_tail = 47.4997 uA, I_b = I_NM4 = 24.7394 uA,
# I_NM1 = 22.7603 uA, P = 85.4995 uW (0.997 x target).
# Dependent overdrives of the printed cells at those currents:
#   NM2 (3u/0.5u, 47.4997 uA, muCox 244.5u x CLM 1.00662):
#       Vov_t  = sqrt(2*47.4997u*0.5u/(246.12u*3u)) = 0.253637 V
#   NM0/NM3 (6u/0.5u, 24.7394 uA, muCox 431.7u):
#       Vov_nc = sqrt(2*24.7394u*0.5u/(431.7u*6u))  = 0.097730 V
#   PM0/PM2 (7u/0.5u, 24.7394 uA, muCox 82.08u):
#       Vov_p2 = sqrt(2*24.7394u*0.5u/(82.08u*7u))  = 0.207504 V
#   PM1/PM3 (7u/0.5u, 24.7394 uA, muCox 83.16u):
#       Vov_p3 = sqrt(2*24.7394u*0.5u/(83.16u*7u))  = 0.206153 V
# Input pair: Vov1 = 0.172165 V at W1 = 2.845 um (muCox 293.37u at that Vov),
#   and the same W at I_NM1 gives Vov_NM1 = 0.164260 V.
# Vertical budget, bottom to top, every level built from the devices below it:
#   Vtail = Vov_t + 0.080 = 0.333637 V
#   vout  = Vtail + Vth_NM4 + Vov1    = 0.333637 + 0.704 + 0.172165 = 1.209802 V
#   vcm   = Vtail + Vth_NM4 + Vov_NM1 = 0.333637 + 0.704 + 0.164260 = 1.201898 V
#   ceiling = vdd - 1.25*(Vov_p2+Vov_p3) = 1.8 - 1.25*0.413657 = 1.282929 V
#             > 1.209802  OK (73.1 mV of slack; Vov1 could rise to 0.245291 V
#             before the PMOS stack hits its 25% floor)
# NMOS branch, tail -> vout spans 1.209802 - 0.333637 = 0.876165 V and needs
# Vov1 + Vov_nc = 0.269895 V, leaving 0.606270 V shared equally:
#   V(n2) = 0.333637 + 0.475300 = 0.808937 V
#   NM4: Vds = 0.475300 >= Vov1   = 0.172165  OK (2.76x, and 475 mV is 15 mV
#        from the 490 mV at which lam_NM4 was measured)
#   NM3: Vds = 0.400865 >= Vov_nc = 0.097730  OK (4.10x, 30 mV from its 431 mV)
# PMOS branch, vdd -> vout spans 1.8 - 1.209802 = 0.590198 V and needs
# Vov_p2 + Vov_p3 = 0.413657 V, leaving 0.176541 V shared equally (88.3 mV
# each, which is the lam_p anchor region):
#   V(p2) = 1.8 - 0.295775 = 1.504225 V
#   PM2: |Vds| = 0.295775 >= Vov_p2 = 0.207504  OK (1.43x)
#   PM3: |Vds| = 0.294423 >= Vov_p3 = 0.206153  OK (1.43x)
# Tail device:
#   NM2: Vds = Vtail = 0.333637 >= Vov_t = 0.253637  OK (1.32x, +80.0 mV)
# Column closes: 0.333637+0.475300+0.400865+0.294423+0.295775 = 1.800000 V.
# Dummy branch (NM1, NM0, PM1, PM0 at 22.7603 uA) -- section 6f shows PM0 and
# PM1 cannot be saturated at the same time as the rest, and gives their numbers;
# NM1 keeps Vds = 0.479 V >= 0.164 V and NM0 Vds = 0.778 V >= 0.094 V.
# Gain at this point: ro_NM3 = 1/(0.1903*24.7394u) = 212.44 k,
# ro_NM4 = 1/(0.1521*24.7394u) = 265.78 k, gm_nc = 0.674*2*24.7394u/0.097730
# = 341.23 uS; lam_p(0.088270) = 0.33928 -> ro_PM2 = ro_PM3 = 119.14 k,
# gm_PM3 = 0.817*2*24.7394u/0.206153 = 196.09 uS,
# gm1 = 0.8509*2*24.7394u/0.172165 = 244.54 uS:
#   R_dn  = 341.23u*212.44k*265.78k = 19.262 MOhm
#   R_up  = 196.09u*119.14k*119.14k =  2.783 MOhm
#   R_dn||R_up = 2.4319 MOhm,  x K_OUT (1.3611) -> R_out = 3.3101 MOhm
#   fac = (234.75u + 18.49u)/(244.54u + 234.75u + 18.49u) = 0.50874
#   A0 = 0.50874*244.54u*3.3101M = 411.8 = 52.2937 dB  (predicted gain)
#   f_u = 0.50874*244.54u/(2*pi*20.024p) = 988.8 kHz; f_n2 = 2.12 GHz,
#   f_p2 = 0.91 GHz, PM = 90 - 0.03 - 0.06 = 89.91 deg (CL dominates).
# Power: 47.4997u*1.8 = 85.4995 uW, i.e. -0.3% on target, which is exactly the
# unexplained part of round 1's power residual (E3).
#
# -----------------------------------------------------------------------------
# (6) DC OPERATING-POINT CONSISTENCY -- what each stage produces vs what the
#     next one needs, with explicit arithmetic
# -----------------------------------------------------------------------------
# a) V4 -> tail current.  V4 = Vth_NM2 + Vov_t = 0.633 + 0.253637 = 0.886637 V.
#    NM2's Vgs = 0.886637 - 0 = 0.886637 -> Vov = 0.253637 ->
#    Id = (244.5u/2)*(3u/0.5u)*0.253637^2*1.00662 = 47.50 uA = I_tail as
#    intended.  Round 1's V4 was 0.880585 V for 44.308 uA and delivered
#    45.1 uA; the 6.1 mV increase buys the 2.4 uA that centres the power.
# b) tail node needed by NM2 vs produced by the pair.  The pair produces
#    Vtail = vcm - Vth_NM4 - Vov_NM1 = 1.201898 - 0.704 - 0.164260 = 0.333637 V
#    (vcm is an input we choose, so the arrow runs vcm -> Vtail, and NM2's
#    requirement is then checked against it).  NM2 needs Vds >= 0.253637 V.
#    Produced - needed = +80.0 mV.  Round 1 is the proof that this arithmetic
#    is the right way round: it reported vcm = vout = 1.2047 V, which put
#    Vtail = 1.2047 - 0.704 - 0.189 = 0.3117 V, and 311 mV was measured.
# c) V3 -> node n2.  V3 = V(n2) + Vth_NM3 + Vov_nc = 0.808937 + 0.783
#    + 0.097730 = 1.689667 V (< vdd = 1.8, legal).  Conversely NM3 with
#    Vgs = 1.689667 - 0.808937 = 0.880730 V carries
#    (431.7u/2)*(6u/0.5u)*0.097730^2 = 24.74 uA = I_b: the cascode passes
#    exactly the current the pair hands it, as a common-gate stage must.
# d) V1 -> branch current.  V1 = vdd - |Vth_PM2| - Vov_p2 = 1.8 - 0.992
#    - 0.207504 = 0.600496 V.  PM2's |Vgs| = 1.8 - 0.600496 = 1.199504 ->
#    |Vov| = 0.207504 -> Id = (82.08u/2)*(7u/0.5u)*0.207504^2 = 24.74 uA = I_b.
#    MATCHING CONDITION: I_PM0 = I_PM2 = 24.7394 uA against I_tail/2
#    = 23.7499 uA.  These are deliberately 4% apart (DELTA, section 4).
# e) V2 -> node p2.  V2 = V(p2) - |Vth_PM3| - Vov_p3 = 1.504225 - 1.061
#    - 0.206153 = 0.237073 V (> 0, legal).  PM3's |Vgs| = 1.504225 - 0.237073
#    = 1.267152 -> |Vov| = 0.206153 ->
#    Id = (83.16u/2)*(7u/0.5u)*0.206153^2 = 24.74 uA, again exactly I_b.  And
#    V(p2) - |Vds_PM3| = 1.504225 - 0.294423 = 1.209802 V = vout: the top of
#    the stack lands on the level the follower settles at, to 1e-6 V.
# f) THE TWO BRANCHES, AND WHY 9/9 IS NOT AVAILABLE.  KCL leaves no freedom:
#    I_NM1 = I_PM0 at x1, I_NM4 = I_PM2 at vout, I_NM1 + I_NM4 = I_NM2 at tail.
#    PM0 and PM2 share gate V1 and are the same printed cell, so their
#    saturation currents are equal; the output branch is held by feedback, so
#    I_NM4 = I_PM2,sat = 24.7394 uA, and the tail then forces
#    I_NM1 = 47.4997 - 24.7394 = 22.7603 uA.  PM0 must therefore pass 8.0% LESS
#    than its own saturation current, and a saturated device cannot do that:
#    PM0 is pushed into triode by construction, at
#      2*u - u^2 = I_NM1/I_PM0,sat = 0.9200 with u = |Vds_PM0|/Vov_p2
#      -> u = 1 - sqrt(1-0.9200) = 0.71716, |Vds_PM0| = 148.81 mV,
#         p1 = 1.8 - 0.148813 = 1.651187 V.
#    This is scale-invariant: u depends only on the current RATIO, so no amount
#    of headroom, overdrive or current rescaling removes the flag -- only
#    I_PM2 = I_tail/2 EXACTLY would, which is a codimension-1 condition in
#    (V1, V4) that no model of a few-percent accuracy can target, and which
#    nothing in the circuit restores if it drifts (the small-signal argument in
#    section 4).  PM1 follows PM0 down: with p1 = 1.651 V its |Vov| =
#    1.651187 - 0.237073 - 1.061 = 0.353114 V, whose saturation current would
#    be (83.16u/2)*14*0.353114^2 = 72.59 uA, so it too must throttle,
#      u = 1 - sqrt(1 - 22.7603/72.59) = 0.17149, |Vds_PM1| = 60.6 mV,
#      x1 = 1.651187 - 0.060555 = 1.590631 V.
#    The NMOS half of the dummy branch stays comfortably saturated:
#      Vov_NM0(22.7603 uA) = sqrt(2*22.7603u*0.5u/(431.7u*6u)) = 0.093739 V,
#      V(n1) = V3 - Vth_NM3 - Vov_NM0 = 1.689667 - 0.783 - 0.093739
#            = 0.812928 V,
#      NM0: Vds = 1.590631 - 0.812928 = 0.777703 >= 0.093739  OK (8.30x)
#      NM1: Vds = 0.812928 - 0.333637 = 0.479291 >= 0.164260  OK (2.92x)
#    So the asymmetry costs exactly the two dummy-branch PMOS their saturation
#    margin and nothing else: x1 has no AC path to vout (section 3), the supply
#    current is I_tail whatever x1 does, and the follower offset is set by the
#    pair, not by x1.  Round 1 measured precisely this pattern (PM0 at 135 mV,
#    PM1 at 54 mV, x1 = 1.611 V, NM0 and NM1 saturated) at a 21% deficit; this
#    round's deficit is 8.0%, which is as small as the parameter accuracy
#    allows while keeping the sign of the mismatch safe.
# g) vcm as an output of (a)-(f), not an assumption.  vcm = 1.201898 V is
#    Vtail(from V4 and NM2's row) + Vth_NM4 + Vov_NM1(from W1 and I_NM1), and
#    the PMOS stack built downward from vdd in (e) independently lands on
#    vout = 1.209803 V, which is vcm + (Vov1 - Vov_NM1) = 1.201898 + 0.007905.
#    The two chains agree to 1e-6 V because V2 is computed FROM the PMOS split
#    of (vdd - vout), which is where the 73.1 mV of headroom slack in (5) goes.
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
W_GRID = 5e-9

# --- round-1 calibration anchors: the operating point at which the parameters
# this function is handed were extracted (section 2).
CAL_VOV = {"NM0": 0.079, "NM1": 0.189, "NM2": 0.248, "NM3": 0.099, "NM4": 0.216,
           "PM0": 0.209, "PM1": 0.392, "PM2": 0.209, "PM3": 0.208}
CAL_VDS = {"NM0": 0.792, "NM1": 0.507, "NM2": 0.311, "NM3": 0.431, "NM4": 0.490,
           "PM0": 0.135, "PM1": 0.054, "PM2": 0.286, "PM3": 0.282}
CAL_ID = {"NM0": 19.9e-6, "NM1": 19.9e-6, "NM2": 45.1e-6, "NM3": 25.1e-6,
          "NM4": 25.1e-6, "PM0": 19.9e-6, "PM1": 19.9e-6, "PM2": 25.1e-6,
          "PM3": 25.1e-6}
CAL_GAIN_DB = 48.7044186      # measured loop gain of the round-1 sizing

# matched-pair parameter sourcing: the device on the left takes the calibrated
# parameters of the device on the right (section 2).  PM0/PM1 were measured in
# TRIODE, so their own rows are unusable.
PARAM_SOURCE = {"NM1": "NM4", "NM0": "NM3", "PM0": "PM2", "PM1": "PM3"}

# the 7u/0.5u PMOS lam(dV) shape, exact three-point fit of the round-0
# calibration of the same cell: lam = C + A/(B + dV), dV = |Vds| - |Vov|.
# It is rescaled at run time to pass through the round-1 measurement (E1).
LAM_P_SHAPE = (0.038283, 0.029473, 0.031563)

# The input-pair cell (1.95u/0.5u) was measured at two overdrives, section 2:
# NM1 at Vov = 189 mV and NM4 at 216 mV, both SAT.  These are the printed
# values; compute_sizing() refits IN_FIT from the full-precision rows it is
# handed, and these serve only as the fallback.
IN_MU = ((0.189, 286.7e-6), (0.216, 276.0e-6))
IN_AG = ((0.189, 0.859), (0.216, 0.872))
MU_IN_CLAMP = (250e-6, 330e-6)
AG_IN_CLAMP = (0.820, 0.900)
IN_FIT = {"mu": IN_MU, "ag": IN_AG}

# --- design knobs, all justified in the header
DELTA = 0.04              # PMOS branch current excess over half the tail current
VTAIL_DV = 0.080          # V of Vds margin above Vov for the tail device NM2
PMOS_MIN_FRAC = 0.25      # each stacked PMOS gets |Vds| >= (1+0.25)*|Vov|
GAIN_DESIGN_DB = 52.3     # design point: 52.0 target + 0.3 dB, see E5
POWER_DESIGN_FACTOR = 0.997  # the one unexplained part of round 1's power error

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


def _interp2(pts, x, clamp):
    """Straight line through two measured (Vov, value) points, clamped."""
    (x0, y0), (x1, y1) = pts
    y = y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return min(clamp[1], max(clamp[0], y))


def _mucox_in(vov):
    return _interp2(IN_FIT["mu"], vov, MU_IN_CLAMP)


def _agm_in(vov):
    return _interp2(IN_FIT["ag"], vov, AG_IN_CLAMP)


def _set_in_fit(params):
    """Refit the pair cell's muCox(Vov) and a_gm(Vov) from the handed rows.

    NM1 and NM4 are the same printed cell measured at two different overdrives
    (189 mV and 216 mV, both saturated), which is what makes the two-point fit
    of section 2 calibration data rather than an assumption.
    """
    try:
        mu = ((CAL_VOV["NM1"], float(params["NM1"]["muCox"])),
              (CAL_VOV["NM4"], float(params["NM4"]["muCox"])))
        ag = ((CAL_VOV["NM1"], float(params["NM1"]["a_gm"])),
              (CAL_VOV["NM4"], float(params["NM4"]["a_gm"])))
        for pts in (mu, ag):
            if pts[0][1] <= 0.0 or pts[1][1] <= 0.0:
                raise ValueError
        IN_FIT["mu"], IN_FIT["ag"] = mu, ag
    except Exception:
        IN_FIT["mu"], IN_FIT["ag"] = IN_MU, IN_AG


def _vov_in(i, w, l, m):
    """Overdrive of the input-pair cell at current i, with muCox(Vov).

    Fixed point of Vov = sqrt(2*i*L/(muCox(Vov)*W*m)); muCox is weakly and
    monotonically decreasing in Vov, so the iteration contracts.
    """
    v = 0.2
    for _ in range(80):
        vn = _vov(_mucox_in(v), w, l, m, i)
        if abs(vn - v) < 1e-12:
            v = vn
            break
        v = vn
    return v


def _dev(params, name):
    """Calibrated parameters to use for a device (matched-pair substitution)."""
    return params[PARAM_SOURCE.get(name, name)]


def _fit_lam_p(params):
    """lam_p(dV) for the 7u/0.5u PMOS cell, dV = |Vds| - |Vov| (section 2).

    Shape: the exact round-0 three-point fit of this same printed cell.
    Scale: rescaled so the curve passes through the MEAN of this round's two
    saturated PMOS rows (PM2 at dV = 77 mV, PM3 at 74 mV), which sit 13 mV from
    this design's margin.  The round-0 curve alone under-states lam there by
    19%, which was most of round 1's gain error (E1).
    """
    c, a, b = LAM_P_SHAPE
    shape = lambda dv: c + a / (b + max(dv, 0.0))
    try:
        dv2 = CAL_VDS["PM2"] - CAL_VOV["PM2"]
        dv3 = CAL_VDS["PM3"] - CAL_VOV["PM3"]
        lm = 0.5 * (float(params["PM2"]["lam"]) + float(params["PM3"]["lam"]))
        k = lm / shape(0.5 * (dv2 + dv3))
        if not (0.2 < k < 5.0):
            raise ValueError
    except Exception:
        k = 1.0
    return (lambda dv: k * shape(dv)), k


def _r_out(params, lam_p, i_b, half, k_out):
    """Cascoded output resistance at branch current i_b and PMOS margin half."""
    pn3, pn4 = _dev(params, "NM3"), _dev(params, "NM4")
    pp3 = _dev(params, "PM3")
    wn, ln, mn = FIXED["NM3"]
    wp, lp, mp = FIXED["PM3"]
    vov_nc = _vov(pn3["muCox"], wn, ln, mn, i_b)
    vov_p3 = _vov(pp3["muCox"], wp, lp, mp, i_b)
    gm_nc = pn3["a_gm"] * 2.0 * i_b / vov_nc
    gm_p3 = pp3["a_gm"] * 2.0 * i_b / vov_p3
    r_dn = gm_nc / (pn3["lam"] * i_b) / (pn4["lam"] * i_b)
    ro_p = 1.0 / (lam_p(half) * i_b)
    r_up = gm_p3 * ro_p * ro_p
    return k_out / (1.0 / r_up + 1.0 / r_dn), r_dn, r_up, gm_nc, gm_p3, ro_p


def _k_out(params, lam_p):
    """Model residual on R_out, calibrated on the one measured gain (E5).

    Replays the gain equation at the round-1 MEASURED operating point, using
    the measured overdrives so that every gm reproduces the measured gm, and
    returns the factor by which the modelled R_out must be multiplied for the
    equation to reproduce the measured 48.704 dB.  Physically this is the
    cascode body effect, (gm+gmb)*ro instead of gm*ro, which the square-law
    model omits.
    """
    try:
        i_b, i_t, i_1 = CAL_ID["NM4"], CAL_ID["NM2"], CAL_ID["NM1"]
        pn2, pn3, pn4 = params["NM2"], _dev(params, "NM3"), _dev(params, "NM4")
        pp3 = _dev(params, "PM3")
        gm_nc = pn3["a_gm"] * 2.0 * i_b / CAL_VOV["NM3"]
        r_dn = gm_nc / (pn3["lam"] * i_b) / (pn4["lam"] * i_b)
        half = 0.5 * ((CAL_VDS["PM2"] - CAL_VOV["PM2"])
                      + (CAL_VDS["PM3"] - CAL_VOV["PM3"]))
        ro_p = 1.0 / (lam_p(half) * i_b)
        r_up = pp3["a_gm"] * 2.0 * i_b / CAL_VOV["PM3"] * ro_p * ro_p
        r_out = 1.0 / (1.0 / r_up + 1.0 / r_dn)
        # the pair's gm comes from the same a_gm(Vov) fit the design path uses,
        # so the residual below is a residual of the model, not of a function
        # swap; at the calibrated overdrives the fit returns the measured a_gm.
        gm4 = _agm_in(CAL_VOV["NM4"]) * 2.0 * i_b / CAL_VOV["NM4"]
        gm1 = _agm_in(CAL_VOV["NM1"]) * 2.0 * i_1 / CAL_VOV["NM1"]
        g_t = pn2["lam"] * i_t
        fac = (gm1 + g_t) / (gm4 + gm1 + g_t)
        a_model = fac * gm4 * r_out
        k = 10.0 ** (CAL_GAIN_DB / 20.0) / a_model
        if not (0.5 <= k <= 3.0):
            raise ValueError
        return k, 20.0 * math.log10(a_model)
    except Exception:
        return 1.0, float("nan")


def _branch(params, i_b, i_tail):
    """Everything set by the branch / tail current alone (printed cells only)."""
    d = {}
    pn2, pn3 = params["NM2"], _dev(params, "NM3")
    pp2, pp3 = _dev(params, "PM2"), _dev(params, "PM3")
    wp, lp, mp = FIXED["PM2"]
    wn, ln, mn = FIXED["NM3"]
    wt, lt, mt = FIXED["NM2"]

    # NM2's muCox was extracted at a Vds margin of CAL_VDS-CAL_VOV = 63 mV and
    # is used at VTAIL_DV = 80 mV; fold the channel-length modulation of the
    # extra 17 mV into the current it delivers (1 + lam*dVds = 1.0066).
    d["clm_t"] = 1.0 + pn2["lam"] * (VTAIL_DV - (CAL_VDS["NM2"] - CAL_VOV["NM2"]))
    d["mucox_t"] = pn2["muCox"] * d["clm_t"]
    d["vov_t"] = _vov(d["mucox_t"], wt, lt, mt, i_tail)

    d["vov_p2"] = _vov(pp2["muCox"], wp, lp, mp, i_b)     # PM0 / PM2
    d["vov_p3"] = _vov(pp3["muCox"], wp, lp, mp, i_b)     # PM1 / PM3
    d["vov_nc"] = _vov(pn3["muCox"], wn, ln, mn, i_b)     # NM0 / NM3
    d["g_t"] = pn2["lam"] * i_tail                        # 1 / ro_NM2
    return d


def _gain_at(params, lam_p, d, i_b, i_nm1, vtail, vov1, w1, l_in, m_in, vdd,
             k_out):
    """Low-frequency loop gain for a trial input-pair overdrive."""
    pn4 = _dev(params, "NM4")
    vout = vtail + pn4["vth"] + vov1
    half = 0.5 * ((vdd - vout) - (d["vov_p2"] + d["vov_p3"]))
    r_out, r_dn, r_up, gm_nc, gm_p3, ro_p = _r_out(params, lam_p, i_b, half,
                                                   k_out)
    gm1 = _agm_in(vov1) * 2.0 * i_b / vov1
    vov_nm1 = _vov_in(i_nm1, w1, l_in, m_in)
    gm_nm1 = _agm_in(vov_nm1) * 2.0 * i_nm1 / vov_nm1
    fac = (gm_nm1 + d["g_t"]) / (gm1 + gm_nm1 + d["g_t"])
    return {
        "gain": fac * gm1 * r_out, "vout": vout, "half": half,
        "vds_p2": d["vov_p2"] + half, "vds_p3": d["vov_p3"] + half,
        "lam_p2": lam_p(half), "ro_p2": ro_p, "r_up": r_up, "r_dn": r_dn,
        "r_out": r_out, "gm1": gm1, "gm_nm1": gm_nm1, "vov_nm1": vov_nm1,
        "gm_nc": gm_nc, "gm_p3": gm_p3, "fac": fac,
    }


def _w_for(params, i_b, vov1, l_in, m_in):
    """Width of the input pair for a trial overdrive, with muCox(Vov)."""
    return 2.0 * i_b * l_in / (_mucox_in(vov1) * vov1 ** 2 * m_in)


def compute_sizing(spec, params):
    cond = spec.get("conditions", {})
    vdd = cond.get("vdd", 1.8)
    cl = cond.get("cl", 20e-12)
    tgt = spec["targets"]
    p_target = tgt["power_W"]
    a_design = 10.0 ** ((tgt["gain_dB"] + (GAIN_DESIGN_DB - 52.0)) / 20.0)
    keep = spec.get("variables", {}).get("keep_printed", {})
    l_in = keep.get("NM1.l", 500e-9)
    m_in = int(keep.get("NM1.m", 1))

    _set_in_fit(params)
    lam_p, lam_k = _fit_lam_p(params)
    k_out, gain_replay_dB = _k_out(params, lam_p)
    pn2, pn3, pn4 = params["NM2"], _dev(params, "NM3"), _dev(params, "NM4")
    pp2, pp3 = _dev(params, "PM2"), _dev(params, "PM3")

    # ---- currents.  Power = I_tail*vdd; the PMOS sources are deliberately
    # DELTA stronger than half the tail current so the dummy branch (PM0/PM1)
    # absorbs the residual current mismatch instead of the signal-path NMOS.
    i_tail = POWER_DESIGN_FACTOR * p_target / vdd
    i_b = i_tail / (2.0 * (1.0 - DELTA))
    i_nm1 = i_tail - i_b

    d = _branch(params, i_b, i_tail)
    vtail = d["vov_t"] + VTAIL_DV

    def gain_of(v):
        return _gain_at(params, lam_p, d, i_b, i_nm1, vtail, v,
                        _w_for(params, i_b, v, l_in, m_in), l_in, m_in, vdd,
                        k_out)["gain"]

    # ---- solve for the input-pair overdrive.  The gain is strictly decreasing
    # in vov1 (gm1 falls AND the PMOS stack loses margin, raising lam_p), so a
    # bisection between the geometry limit and the headroom limit is exact.
    vov1_lo = _vov_in(i_b, W_MAX, l_in, m_in)
    vov1_hi = (vdd - (1.0 + PMOS_MIN_FRAC) * (d["vov_p2"] + d["vov_p3"])
               - pn4["vth"] - vtail)
    vov1_hi = min(vov1_hi, _vov_in(i_b, W_MIN, l_in, m_in))
    limited = ""
    if vov1_hi <= vov1_lo:
        vov1 = max(vov1_lo, 1e-3)
        limited = "no headroom window"
    else:
        if gain_of(vov1_lo) < a_design:
            vov1, limited = vov1_lo, "gain-limited (W at max)"
        elif gain_of(vov1_hi) > a_design:
            vov1, limited = vov1_hi, "headroom-limited (gain too high)"
        else:
            a, b = vov1_lo, vov1_hi
            for _ in range(200):
                mid = 0.5 * (a + b)
                if gain_of(mid) > a_design:
                    a = mid
                else:
                    b = mid
            vov1 = 0.5 * (a + b)

    # ---- input pair geometry (INDEPENDENT), snapped to the 5 nm grid, then
    # the overdrive re-derived from the gridded width.
    w1 = _w_for(params, i_b, vov1, l_in, m_in)
    w1 = min(W_MAX, max(W_MIN, round(w1 / W_GRID) * W_GRID))
    vov1 = _vov_in(i_b, w1, l_in, m_in)
    g = _gain_at(params, lam_p, d, i_b, i_nm1, vtail, vov1, w1, l_in, m_in,
                 vdd, k_out)

    # ---- DC operating point: every node from the driving stage's parameters
    vout = g["vout"]                                      # settles here
    vcm = vtail + pn4["vth"] + g["vov_nm1"]               # what we must apply
    extra_n = (vout - vtail) - (vov1 + d["vov_nc"])       # NMOS stack slack
    vds_nm4 = vov1 + 0.5 * extra_n
    vds_nm3 = d["vov_nc"] + 0.5 * extra_n
    v_n2 = vtail + vds_nm4
    v_p2 = vdd - g["vds_p2"]
    vbn0 = pn2["vth"] + d["vov_t"]                        # V4, sets i_tail
    vbn1 = v_n2 + pn3["vth"] + d["vov_nc"]                # V3, NM0/NM3 gate
    vbp1 = vdd - pp2["vth"] - d["vov_p2"]                 # V1, sets i_b
    vbp2 = v_p2 - pp3["vth"] - d["vov_p3"]                # V2, PM1/PM3 gate

    # ---- the dummy branch, large signal (section 6f).  PM0 must pass
    # I_NM1/I_b = 1-2*DELTA of its own saturation current, which a saturated
    # device cannot do, so it sits in triode at |Vds| = u*Vov_p2 with u the
    # root of the triode law 2u - u^2 = I_NM1/I_b.  PM1 then follows.
    ratio = i_nm1 / i_b
    u0 = 1.0 - math.sqrt(max(0.0, 1.0 - ratio))
    vds_pm0 = u0 * d["vov_p2"]
    v_p1 = vdd - vds_pm0
    vov_pm1 = max(1e-6, v_p1 - vbp2 - pp3["vth"])
    i_pm1_sat = 0.5 * pp3["muCox"] * (FIXED["PM1"][0] / FIXED["PM1"][1]) \
        * vov_pm1 ** 2
    u1 = 1.0 - math.sqrt(max(0.0, 1.0 - min(1.0, i_nm1 / i_pm1_sat)))
    vds_pm1 = u1 * vov_pm1
    v_x1 = v_p1 - vds_pm1
    vov_nm0 = _vov(pn3["muCox"], FIXED["NM0"][0], FIXED["NM0"][1], 1, i_nm1)
    v_n1 = vbn1 - pn3["vth"] - vov_nm0
    vds_nm0 = v_x1 - v_n1
    vds_nm1 = v_n1 - vtail

    # ---- predictions
    gain_dB = 20.0 * math.log10(g["gain"])
    power = i_tail * vdd

    wp = FIXED["PM3"][0]
    wn = FIXED["NM3"][0]
    # vout carries CL, the two output drain junctions/overlaps, and -- through
    # the unity-gain feedback -- the gate of NM4 (7 fF, included for honesty).
    c_out = (cl + (CGD_PER_W + CJ_PER_W) * (wp + wn)
             + (2.0 / 3.0) * w1 * l_in * COX + CGD_PER_W * w1)
    gbw = g["fac"] * g["gm1"] / (2.0 * math.pi * c_out)
    c_n = ((2.0 / 3.0) * wn * FIXED["NM3"][1] * COX + CJ_PER_W * (wn + w1)
           + CGD_PER_W * w1)
    c_p = ((2.0 / 3.0) * wp * FIXED["PM3"][1] * COX + CJ_PER_W * 2.0 * wp
           + CGD_PER_W * wp)
    f_n = g["gm_nc"] / (2.0 * math.pi * c_n)
    f_p = g["gm_p3"] / (2.0 * math.pi * c_p)
    pm = 90.0 - math.degrees(math.atan(gbw / f_n)) \
        - math.degrees(math.atan(gbw / f_p))

    LAST_DESIGN.clear()
    LAST_DESIGN.update(
        i_tail=i_tail, i_b=i_b, i_nm1=i_nm1, limited=limited,
        lam_k=lam_k, k_out=k_out, gain_replay_dB=gain_replay_dB,
        clm_t=d["clm_t"], mucox_t=d["mucox_t"], vov_t=d["vov_t"], vtail=vtail,
        vov1=vov1, w1=w1, mucox_in=_mucox_in(vov1), agm_in=_agm_in(vov1),
        vov_nm1=g["vov_nm1"], vov_nc=d["vov_nc"], vov_p2=d["vov_p2"],
        vov_p3=d["vov_p3"], vout=vout, vcm=vcm, offset_vout_vcm=vout - vcm,
        vds_nm2=vtail, vds_nm4=vds_nm4, vds_nm3=vds_nm3,
        vds_p2=g["vds_p2"], vds_p3=g["vds_p3"], v_n2=v_n2, v_p2=v_p2,
        half=g["half"], lam_p2=g["lam_p2"], ro_p2=g["ro_p2"],
        r_up=g["r_up"], r_dn=g["r_dn"], r_out=g["r_out"], gm1=g["gm1"],
        gm_nm1=g["gm_nm1"], gm_nc=g["gm_nc"], gm_p3=g["gm_p3"], fac=g["fac"],
        vov1_lo=vov1_lo, vov1_hi=vov1_hi, c_out=c_out, f_n=f_n, f_p=f_p,
        dummy_ratio=ratio, vds_pm0=vds_pm0, v_p1=v_p1, vov_pm1=vov_pm1,
        vds_pm1=vds_pm1, v_x1=v_x1, vov_nm0=vov_nm0, v_n1=v_n1,
        vds_nm0=vds_nm0, vds_nm1=vds_nm1,
        sat_ratios={
            "NM2": vtail / d["vov_t"], "NM4": vds_nm4 / vov1,
            "NM3": vds_nm3 / d["vov_nc"], "PM2": g["vds_p2"] / d["vov_p2"],
            "PM3": g["vds_p3"] / d["vov_p3"], "NM1": vds_nm1 / g["vov_nm1"],
            "NM0": vds_nm0 / vov_nm0, "PM0": vds_pm0 / d["vov_p2"],
            "PM1": vds_pm1 / vov_pm1},
        column_closes=(vtail + vds_nm4 + vds_nm3 + g["vds_p3"] + g["vds_p2"]),
        lam_p_at=[round(lam_p(x), 4) for x in (0.05, 0.075, 0.0883, 0.1, 0.15)],
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
    "NM0": {"type": "NMOS", "muCox": 531.9e-6, "a_gm": 0.592, "lam": 0.124, "vth": 0.785},
    "NM1": {"type": "NMOS", "muCox": 286.7e-6, "a_gm": 0.859, "lam": 0.1422, "vth": 0.704},
    "NM2": {"type": "NMOS", "muCox": 244.5e-6, "a_gm": 0.881, "lam": 0.3893, "vth": 0.633},
    "NM3": {"type": "NMOS", "muCox": 431.7e-6, "a_gm": 0.674, "lam": 0.1903, "vth": 0.783},
    "NM4": {"type": "NMOS", "muCox": 276.0e-6, "a_gm": 0.872, "lam": 0.1521, "vth": 0.704},
    "PM0": {"type": "PMOS", "muCox": 65.43e-6, "a_gm": 0.652, "lam": 4.153, "vth": 0.992},
    "PM1": {"type": "PMOS", "muCox": 18.51e-6, "a_gm": 0.519, "lam": 16.91, "vth": 1.027},
    "PM2": {"type": "PMOS", "muCox": 82.08e-6, "a_gm": 0.820, "lam": 0.3606, "vth": 0.992},
    "PM3": {"type": "PMOS", "muCox": 83.16e-6, "a_gm": 0.817, "lam": 0.388, "vth": 1.061},
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
