"""Round-1 sizing for the two-stage Miller op-amp of Fig. 4, Sky130.

WHAT ROUND 0 GOT WRONG (the whole of this round follows from it).  Round 0 was
not wrong about the topology or the small-signal form; it was wrong about the
process constants, and in one place about the mirror law.  The calibration
table says:

  quantity          round-0 guess        calibrated            consequence
  muCox, nfet       130 uA/V^2           317.3 @ Vov =  95 mV  W too wide
  muCox, pfet        40 uA/V^2           160.8 @ Vov =  77 mV  W far too wide
                                         176.4 @ Vov =  72 mV
  gm/Id, input pair 2*0.85/0.1474 = 11.5  166.7/10.4 = 16.0    gm1 +39 %
  gm/Id, PM0        2*0.85/0.150  = 11.3  1489/113   = 13.2    gm2 +16 %
  lam, node B       0.0333+0.1700=0.2033  0.0786+0.0912=0.1698 ro1 +20 %
  lam, node vout    0.0333+0.1700=0.2033  0.1110+0.0312=0.1422 ro2 +43 %
  Vth, nfet         0.600 V (all five)    0.625 / 0.536 / 0.538 / 0.534
  Vth, pfet         0.950 V (all three)   0.997 / 0.992 / 0.992

Every one of the three misses follows from that list, and all three go the same
way (the circuit was BETTER than predicted):
  * gain  +8.85 dB.  Av1 = 2*a_gm/(Vov1*s1) and Av2 = 2*a_gm/(Vov2*s2) were
    each ~4.5 dB optimistic because gm/Id was underestimated AND the lambda
    sums were overestimated -- the pfet lambda most of all (0.170 guessed
    against 0.091-0.111 measured).  35.08+34.92 dB predicted, 39.55+39.39 dB
    delivered.
  * GBW   +42.6 %.  gm1 = a_gm*2*Id1/Vov1 at the DESIGNED 10.26 uA came out
    166.7 uS instead of 118.4 uS, so w_c = gm1/Cc_eff rose by the same 1.41x.
  * power +5.0 %.  Here the model form, not just a constant, was wrong: rule
    2's plain mirror law W4 = W3*Id2/Ibias assumes the reference and the mirror
    share muCox and Vth.  NM3 and NM4 do not (252.1/538 mV against 254.8/534
    mV), so at the common vbias NM4's overdrive is 184 mV where NM3's is 180,
    and the branch delivered 113 uA where 105.7 was planned (+6.9 %); NM2 came
    in +1.4 % the same way.  Section (1) corrects the mirror law for exactly
    this and section (6) shows the residual is then 7 nA.

HOW THIS ROUND IS BUILT.  The same small-signal model, fed the calibrated
parameters and round 0's as-laid-out geometry, predicts 78.944 dB / 38.4544 MHz
/ 259.68 uW against measurements of 78.8492 dB / 40.1460 MHz / 261.92 uW.  So
once the parameters are right the model is right: +0.095 dB, -4.21 %, -0.86 %.
Those three residuals -- not round 0's raw errors, which were parameter errors
and are now gone -- are what the margin rules are applied to, and they are the
three constants GAIN_MARGIN_DB / GBW_MARGIN / POWER_MARGIN below.

================================================================================
(1) DEVICE ROLES
================================================================================
I0   -- bias reference current, vdd into vbias.  Sets the whole DC plan.
NM3  -- diode-connected nfet (Drain=Gate=vbias).  MIRROR REFERENCE:
        vbias = Vth,NM3 + Vovb, and every other nfet current source copies it.
NM2  -- tail current source of the input pair (Drain=C, Gate=vbias).
NM0 / NM1 -- NMOS differential input pair, sources at the tail node C, drains at
        A and B.  NM0's gate is vin1, the inverting input, so NM0 is the device
        the AC test signal drives.
PM2  -- diode-connected pfet load on node A (Drain=Gate=A).  pfet mirror
        reference; it is what PRODUCES the first stage's output voltage.
PM1  -- pfet load on node B, gate tied to A.  MATCHED to PM2, so the pair is a
        1:1 active load and the first stage is single-ended at node B.
PM0  -- second-stage common-source pfet, gate = B, drain = vout.
NM4  -- second-stage current-source load (Drain=vout, Gate=vbias).  It sets the
        stage-2 current; PM0 is sized so its gate drive carries exactly that.
C0   -- Miller compensation capacitor from B to vout.  There is no nulling
        resistor in this topology, so the RHP zero at +gm2/Cc_eff cannot be
        cancelled and is a permanent phase-margin cost.

Classification required by rule 2 (a mirror keeps its reference's L):
  NM3 INDEPENDENT    W3  = 2*Ibias*Ln/(muCox3*Vovb^2)              =  8.815 um
  NM2 MIRROR of NM3  W2  = W3 * (Itail/Ibias) * k2 ,   L = Ln      = 16.260 um
  NM4 MIRROR of NM3  W4  = W3 * (Id2/Ibias)   * k4 ,   L = Ln      = 71.500 um
  NM0 INDEPENDENT    W0  = 2*Id1*Ln/(muCox0*Vov1^2)                =  4.680 um
  NM1 MATCHED to NM0 W1  = W0 , L = Ln                             =  4.680 um
  PM2 INDEPENDENT    Wp2 = 2*Id1*Lp/(muCoxP2*VovP2^2)              =  6.305 um
  PM1 MATCHED to PM2 Wp1 = Wp2 , L = Lp                            =  6.305 um
  PM0 MIRROR of PM2  Wp0 = Wp2 * (Id2/Id1) * kp ,      L = Lp      = 70.840 um

THE MIRROR CORRECTION FACTORS k.  A mirror copies its reference's GATE voltage,
not its width-per-ampere; the plain ratio W = Wref*I/Iref is the special case
muCox = muCox,ref and Vth = Vth,ref.  Equating Id = muCox*(W/L)*Vov^2/2 on both
sides at the shared gate node gives
      k = (muCox,ref/muCox) * (Vov,ref/Vov)^2 ,   Vov = Vgate - Vth  (nfets)
                                                  Vov = VDD - Vgate - |Vth|
with the calibrated numbers:
      k2 (NM2) = (252.1/247.7)*(0.1800/0.1820)^2 = 0.99552   (-0.4 %)
      k4 (NM4) = (252.1/254.8)*(0.1800/0.1840)^2 = 0.94685   (-5.3 %)
      kp (PM0) = (176.4/160.8)*(0.1000/0.0950)^2 = 1.21553   (+21.6 %)
k4 = 0.947 is precisely round 0's +6.9 % NM4 current error, with the sign
reversed; kp = 1.216 is the same effect in the output pfet mirror.  Writing the
widths straight from each device's own muCox and Vth (what _widths() does) is
algebraically identical to the corrected mirror law above -- the report in
section (6) prints both and they agree to the 5 nm layout grid.

================================================================================
(2) DEVICE CONSTRAINTS
================================================================================
Process: Sky130 1.8 V.  compute_sizing() is called with the calibrated table;
nothing here is re-estimated.  Square law throughout:
      Id = muCox*(W/L)*Vov^2/2 ,  gm = a_gm*2*Id/Vov ,  gds = lam*Id
and every parameter is used for the device it was measured on -- which matters,
because the calibration shows they are NOT common to a polarity: lam spans
0.0312 (NM4) to 0.0786 (NM1) at the same L = 3 um, because gds/Id depends on
Vds as well as on L.  Hence the two different lambda sums
      s1 = lam_NM1 + lam_PM1 = 0.07855 + 0.09123 = 0.169780 /V   (node B)
      s2 = lam_PM0 + lam_NM4 = 0.11100 + 0.03124 = 0.142240 /V   (node vout)
rather than round 0's single s = 0.2033 at both nodes.

THE LENGTHS ARE DELIBERATELY UNCHANGED, Ln = 3.0 um and Lp = 0.5 um.  Round 0
chose them by trading lam = K/L against phase margin.  That trade is no longer
available: the calibrated lam values BELONG to those two lengths, and the
spread above shows a 1/L law cannot be reconstructed from them (NM3 and NM4 are
the same device at the same L and differ by 1.45x).  Changing a length would
mean inventing lam, i.e. re-estimating the one parameter this round is supposed
to trust.  Both lengths therefore stay, and the gain is set by the overdrives
alone.

WHAT THAT COSTS, AND WHERE IT IS SPENT.  With the lambdas fixed,
      Av = (2*a_NM0/(Vov1*s1)) * (2*a_PM0/(VovP0*s2)) = 64.371/(Vov1*VovP0)
so the only way to shed round 0's 8.85 dB of excess gain is to raise the
PRODUCT of the two overdrives by 10^(8.85/20) = 2.77x, from the measured
0.095*0.077 = 0.00732 V^2 to 0.02036 V^2.  There is no other knob, and this is
the one real extrapolation in the round: a_gm and muCox are square-law FITS
taken at the round-0 overdrives, and both drift with Vov.  The calibration
table shows the drift directly, for the nfet, because it contains the same
device family at two overdrives:
      nfet_01v8, L = 3 um:   Vov =  95 mV (NM0)       a_gm = 0.762, muCox 317.3
                             Vov = 182 mV (NM2/3/4)   a_gm = 0.967, muCox 251.5
a_gm rises and the fitted muCox falls as the overdrive grows (both are the same
moderate- to strong-inversion transition).  For the pfets there is only ONE
overdrive in the data (72-77 mV), so their drift is unmeasured.

THAT ASYMMETRY DECIDES THE SPLIT.  The excursion is put on the nfet input pair,
whose Vov-dependence is measured, and kept off the pfets, whose is not:
      VOVP0 = 0.095 V  (1.23x the measured 77 mV)
      Vov1  = 0.2119 V (E1) (1.16x the measured 182 mV top of the nfet range)
Sweeping the split, with gain/GBW/power held exactly on target and C0
re-optimised at every point (stressed columns = the drift model of section 4):
   VovP0   Vov1    PM    | stressed: gain    gbw     PM
   0.080  0.2517  56.96  |          70.96  29.02  55.38   Vov1 1.38x the range
   0.090  0.2237  56.90  |          71.33  28.82  57.43
   0.095  0.2119  56.76  |          71.48  28.70  58.21   <== chosen
   0.100  0.2013  56.55  |          71.98  29.59  57.86
   0.110  0.1830  55.99  |          72.64  30.60  57.62
   0.128  0.1575  54.65  |          73.23  31.12  57.59   equal-ratio split
   0.150  0.1342  52.62  |          73.47  30.95  57.23
The equal-ratio split (1.66x on each stage, VovP0 = 0.128) is the intuitive
choice and it is the WORST of these: it puts a 1.66x excursion on the pfet,
whose a_gm = 0.510 is the least trustworthy number in the table, and the drift
model then pushes the gain to 73.2 dB, outside the +/-3 dB window.  VOVP0 =
0.095 keeps both pfet overdrives within 1.3x of where they were measured, has
the best stressed phase margin, and leaves the stressed gain 1.5 dB inside the
window.  Below 0.090 the input pair's overdrive leaves the measured nfet range
altogether and the stressed phase margin starts falling.
  Validity band enforced in code: VOV1_MIN = 0.100 (below it the input pair
drops into the moderate inversion where a_gm = 0.762 was fitted and the square
law is weakest), VOV1_MAX = 0.260 (1.43x the top of the measured nfet range).

THE nfet MIRROR FAMILY IS HELD AT ITS CALIBRATION POINT ON PURPOSE.  VOVB =
0.180 V and IBIAS = 12.0 uA are round 0's own operating point for NM2/NM3/NM4
(measured 180/182/184 mV at 12.0/20.8/113 uA), so their muCox, Vth and lam are
used exactly where they were extracted -- and those three devices are what set
the power.  Raising VOVB to 0.30 V buys +0.4 deg of phase margin (it shrinks
NM4 and so node vout) and would put the only devices that fix the supply
current 1.7x outside their measured range; it was declined.  W3 = 8.815 um
against round 0's 8.862 um: NM3 is deliberately the same transistor.
Geometry: 0.42 um <= W <= 100 um per finger, 0.15 um <= L <= 8 um, no finger
above 60 um (m = 2 for NM4 and PM0), widths on a 5 nm grid.

================================================================================
(3) SIGNAL PATH
================================================================================
AC injection at vin1 (gate of NM0, the inverting input):
  vin1 -> gm,NM0 steers tail current into node A; the PM2/PM1 mirror folds that
  half into node B, so the transconductance to the single-ended output B is
  Gm1 = gm,NM0 = 79.94 uS (full gm, not gm/2).
  Node B impedance:    Ro1 = 1/(Id1*s1) = 529.80 kOhm.
  B -> gate of PM0 -> common-source inversion into vout, Gm2 = gm,PM0 = 1103.76 uS.
  Node vout impedance: Ro2 = 1/(Id2*s2) = 68.391 kOhm.
  C0 bridges B and vout: pole splitting plus a feed-forward RHP zero.
Two gain stages, two split poles, one RHP zero, and the mirror doublet: half
the differential signal reaches node B through PM2 -> PM1, so node A adds
      p3 = gm,PM2/C_A = 107.42 uS / 44.26 fF = 386.27 MHz, with a zero at 2*p3,
14.3x the crossover and worth a net 3.99 - 2.00 = 1.99 deg (round 0 paid 3.85
deg here; PM2 is 1.8x narrower now, so C_A fell from 89.4 to 44.3 fF).  It is
carried in (E4) regardless.
The tail node C is a common-mode node the differential half-circuit does not
see, and PM0's source is vdd, so no other pole is in the signal path.

================================================================================
(4) DESIGN EQUATIONS (symbolic)
================================================================================
Vov1 = overdrive of NM0/NM1, VovP0 = overdrive of PM0, VovP2 = overdrive of
PM2/PM1, Id1 = per-input-device current, Id2 = second-stage current,
Itail = 2*Id1, Ibias = I0.  Note VovP2 != VovP0: the topology forces equal
NODE VOLTAGES (V(A) = V(B)), and PM0/PM2 have different Vth, so
      VovP2 = VovP0 + |Vth,PM0| - |Vth,PM2| = 0.095 + 0.005 = 0.100 V.    (E0)

  gm1 = a_NM0*2*Id1/Vov1         gm2 = a_PM0*2*Id2/VovP0
  Ro1 = 1/(Id1*s1)               Ro2 = 1/(Id2*s2)

  GAIN   Av = gm1*Ro1*gm2*Ro2 = (2*a_NM0/(Vov1*s1)) * (2*a_PM0/(VovP0*s2))
         The currents cancel, so the DC gain depends ONLY on the overdrives and
         the lambdas.  With VovP0 chosen (section 2),
            Av2  = 2*a_PM0/(VovP0*s2)                = 75.4840 (37.557 dB)
            Vov1 = 2*a_NM0/(s1 * Av_target/Av2)      = 0.211935 V          (E1)
         and the current split is then free for the phase margin.

  POWER  P = VDD*(Ibias + 2*Id1 + Id2)  =>  Id2 = Itot - Ibias - 2*Id1    (E2)
         with Itot = P_target*(1+POWER_MARGIN)/VDD = 137.0404 uA.

  GBW    the loop response is
            A(s) = Av*(1 - s/z)*(1 + s/(2*p3)) / ((1+s/p1)(1+s/p2)(1+s/p3))
         and w_c solves |A(w_c)| = 1.  To first order w_c = gm1/Cc_eff;
         requiring w_c = 2*pi*GBW_target*(1+GBW_MARGIN) fixes gm1 and hence
         Id1 = gm1*Vov1/(2*a_NM0), once C0 is chosen.                    (E3)
         The first-order value is 12.8 % optimistic here (gm1/Cc_eff reads
         30.43 MHz against a true crossing of 26.97 MHz, because the p2 and p3
         terms have already eaten gain by then), so the code solves |A| = 1
         exactly and rescales gm1 until the true crossing equals the target.
         Cc_eff = C0 + Cgd,PM0 = 0.404 + 0.0142 = 0.41817 pF: PM0's overlap
         capacitance is electrically in parallel with the Miller cap.

  PHASE MARGIN (pole splitting, RHP zero, mirror doublet, both load nodes):
            p1 = 1/(gm2*Ro1*Ro2*Cc_eff)
            p2 = gm2*Cc_eff/(C1*C2 + Cc_eff*(C1 + C2))
            z  = +gm2/Cc_eff                        (right half plane)
            p3 = gm,PM2/C_A         with a zero at 2*p3   (mirror doublet)
            PM = 180 - atan(w_c/p1) - atan(w_c/p2) - atan(w_c/z)
                     - atan(w_c/p3) + atan(w_c/(2*p3))                  (E4)
         C1  = Cgs,PM0 + (Cov+Cjd)*(Wp1 + Wn1)       (node B)
         C2  = CL + Cjd*Wp0 + (Cjd+Cov)*W4           (node vout)
         C_A = 2*Cgs,PM2 + Cjd*Wp2 + (Cjd+Cov)*W0    (node A)
         with Cox = 8.4 fF/um^2, Cov = 0.20 fF/um, Cjd = 0.50 fF/um.
         p2 and z are both proportional to gm2, so both atan LOSSES shrink as
         gm2 grows: phase margin is bought with second-stage transconductance.

  MARGINS.  Applied to the margin-corrected targets, from the residuals at the
  head of this file: gain 70.0 + 0.095 dB, GBW 28.159 MHz * 0.9579 = 26.9735
  MHz, power 248.8 uW * 0.99145 = 246.66 uW.  The phase margin has no residual
  to correct: it was never measured (the bench reported only the three fitted
  targets), so it is designed to the 45 deg floor plus PM_GUARD = 5 deg and the
  guard is then stress-tested below.

  COUNTING THE DEGREES OF FREEDOM.  (E1), (E2), (E3) are three equations in
  Vov1, Id1, Id2 once VovP0, Ibias, Vovb, Ln, Lp are chosen, so the three
  toleranced targets are met identically and exactly ONE knob is left for the
  phase-margin constraint (E4): C0.  It is swept 0.10-1.60 pF in 1 fF steps and
  the feasible point of maximum PM is taken.  PM(C0) has an interior maximum:
  raising C0 raises gm1 = w_c*Cc_eff, which by (E3) raises Id1, which by (E2)
  steals current from the second stage and lowers gm2, dragging p2 and z down;
  lowering C0 makes p2 ~ gm2*Cc_eff/(C1*C2) fall in proportion to C0 while
  w_c = gm1/Cc_eff rises.
      C0 = 0.150 pF -> PM = 50.30   C0 = 0.450 pF -> PM = 56.66
      C0 = 0.250 pF -> PM = 55.09   C0 = 0.500 pF -> PM = 56.36
      C0 = 0.300 pF -> PM = 56.09   C0 = 0.600 pF -> PM = 55.29
      C0 = 0.350 pF -> PM = 56.60   C0 = 0.700 pF -> PM = 53.68
      C0 = 0.404 pF -> PM = 56.76 <= C0 = 1.000 pF -> PM = 45.96
  The maximum is flat: 0.35-0.50 pF all stay within 0.4 deg of it, so the 1 fF
  grid is not pretending to a precision the model does not have.

  WHAT PAYS FOR THE 45 deg FLOOR.  The current split: 102.80 uA of the 137.03
  uA budget goes to the second stage, so gm2/gm1 = 1103.8/79.9 = 13.81, which
  places p2 at 1.914*f_c (27.59 deg) and the RHP zero at 15.57*f_c (3.67 deg).
  The phase budget at crossover is
      89.98 (p1) + 27.59 (p2) + 3.67 (RHP zero) + 1.99 (mirror doublet)
      = 123.24 deg  ->  PM = 56.76 deg,  i.e. 11.8 deg above the floor.
  Round 0 could only reach 51.6 deg (and, re-evaluated with the calibrated
  parameters, 48.0 deg) because its pfet widths were 4x too large on a 40
  uA/V^2 guess: Cgs,PM0 was 352 fF where it is now 213 fF, and C_A 89 fF where
  it is now 44 fF.  Getting muCox right is what bought the margin.

  TWO STRESS TESTS OF THAT MARGIN.
  (a) Parasitic constants Cox/Cov/Cjd scaled, whole procedure re-run with C0
      re-optimised (C1 is 97 % Cgs,PM0, so this is the dominant cap risk):
        x0.50 -> 63.55    x1.00 -> 56.76    x1.50 -> 50.93
        x0.75 -> 59.98    x1.25 -> 53.76    x2.00 -> 45.63 (fails the guard)
      Round 0's design broke the 45 deg floor between 1.25x and 1.5x; this one
      still clears it at 2x (45.63 deg), failing only the 5 deg guard there.  Gain, GBW and power are untouched by the
      scaling (C0 re-centres between 0.31 and 0.46 pF).
  (b) gm/Id drift, the real exposure of section 2: geometry frozen, a_gm and
      muCox moved along the overdrive dependence the calibration table itself
      shows for the nfets (a_gm(V) = V/(2*(a+bV)) fitted to 0.762 @ 95 mV and
      0.967 @ 182 mV, b = 0.365; the pfet is given the same shape anchored on
      PM0, and muCox falls 2.38 relative per volt of Vov, which reproduces both
      measured nfet rows).  Then
        Vov1 0.212 -> 0.286, a_NM0 0.762 -> 1.08 (a_gm saturates near 1, so
            this is a deliberate over-estimate), gm1   79.9 ->   84.2 uS
        VovP0 0.095 -> 0.097, a_PM0 0.510 -> 0.582, gm2 1103.8 -> 1228.7 uS
        => gain 71.48 dB, GBW 28.69 MHz, PM 58.21 deg, power unchanged
      All four inside their windows (67.0-73.0 dB, 21.1-35.2 MHz, >= 45 deg),
      and the phase margin IMPROVES because gm2 drifts up harder than gm1.
      Power is immune by construction: the currents are set by the nfet mirror
      family, which section 2 pinned to its measured overdrive.

  RESULTING DESIGN POINT (all numbers produced by the equations above, then
  re-derived from the gridded widths by _reevaluate()):
    s1 = 0.169780 /V, s2 = 0.142240 /V, VovP0 = 0.09500 V (chosen),
    VovP2 = 0.10000 V (E0), Vov1 = 0.21194 V (E1)
    Ibias = 12.000 uA (chosen), Id1 = 11.117 uA, Itail = 22.235 uA,
    Id2 = 102.797 uA, total 137.032 uA
    gm1 = 79.94 uS (gm/Id 7.19), gm2 = 1103.8 uS (gm/Id 10.74),
    gm,PM2 = 107.42 uS
    Ro1 = 529.80 kOhm, Ro2 = 68.391 kOhm
    Av1 = 42.353 (32.538 dB), Av2 = 75.487 (37.557 dB), Av = 3197.1 (70.095 dB)
    C0 = 0.40400 pF, Cc_eff = 0.41817 pF, C1 = 220.21 fF (Cgs,PM0 = 212.52),
    C2 = 2085.47 fF, C_A = 44.26 fF
    p1 = 9.517 kHz, p2 = 51.608 MHz, z = 420.09 MHz, p3 = 386.27 MHz,
    f_c = 26.9713 MHz, PM = 56.76 deg, power = 246.66 uW
    W0 = W1 = 4.680 um, W2 = 16.260 um, W3 = 8.815 um,
    W4 = 71.500 um (m = 2), Wp1 = Wp2 = 6.305 um, Wp0 = 70.840 um (m = 2)
    vcm = 1.17597 V

================================================================================
(5) DC BIAS VERIFICATION -- every branch supports saturation, with numbers
================================================================================
Bias branch.  NM3 is diode connected and carries I0 = 12.000 uA, so
  W3 = 2*12.00u*3.0u/(252.1u*0.180^2) = 8.815 um and it PRODUCES
  vbias = Vth,NM3 + Vovb = 0.538 + 0.180 = 0.71800 V.
  Vds = Vgs always, so 0.71800 >= 0.18000: saturated, margin +538.0 mV.   [OK]
NM2 (tail).  Gate = vbias, and its own Vth is 0.536 V, so its overdrive is
  0.71800 - 0.536 = 0.18200 V (not 0.180 -- this is the k2 correction).
  W2 = 2*22.235u*3.0u/(247.7u*0.18200^2) = 16.260 um.
  Needs Vds,NM2 = V(C) >= 0.18200 V.
NM0/NM1.  Vgs = Vth,NM0 + Vov1 = 0.625 + 0.21194 = 0.83694 V, so
  V(C) = vcm - 0.83694 = 1.17597 - 0.83694 = 0.33903 V.
  NM2 check: 0.33903 >= 0.18200, margin +157.0 mV.                        [OK]
  W0 = W1 = 2*11.117u*3.0u/(317.3u*0.21194^2) = 4.680 um.
PM2/PM1.  PM2's drain and gate are node A and its source is vdd, so (rule 3:
  from the pfet's own parameters, never assumed)
  V(A) = VDD - |Vth,PM2| - VovP2 = 1.800 - 0.992 - 0.100 = 0.70800 V.
  |Vds,PM2| = |Vgs,PM2| = 1.09200 V >= 0.10000: saturated, margin +992.0 mV.
  PM1 has the same Vgs and the same 11.117 uA, and |Vds,PM1| = 1.800 - V(B) =
  1.09200 V >= 0.10000 V, margin +992.0 mV.                               [OK]
  Wp1 = Wp2 = 2*11.117u*0.5u/(176.4u*0.10000^2) = 6.305 um.
NM0/NM1 saturation.  Vds,NM0 = V(A) - V(C) = 0.70800 - 0.33903 = 0.36897 V
  against a required Vov1 = 0.21194 V -> margin +157.0 mV.  Node B is
  identical.                                                              [OK]
  (The two +157.0 mV margins are equal by construction, not by luck: vcm was
  put at the centre of the window below, and those are its two edges.)
PM0.  |Vgs,PM0| = VDD - V(B) = 1.800 - 0.70800 = 1.09200 V, overdrive
  1.09200 - 0.997 = 0.09500 V = VOVP0, as (E0) demands.
  Wp0 = 2*102.797u*0.5u/(160.8u*0.09500^2) = 70.840 um, m = 2 x 35.420 um.
  In the follower vout = vcm = 1.17597 V, so |Vds,PM0| = 0.62403 V >=
  0.09500 V, margin +529.0 mV.                                            [OK]
NM4.  Gate = vbias, own Vth 0.534 V -> overdrive 0.18400 V (the k4 correction).
  W4 = 2*102.797u*3.0u/(254.8u*0.18400^2) = 71.500 um, m = 2 x 35.750 um.
  Vds = vout = 1.17597 V >= 0.18400 V, margin +992.0 mV.                  [OK]
Input common-mode window.
  lower edge: V(C) >= Vov,NM2  -> vcm >= 0.625 + 0.21194 + 0.18200 = 1.01894 V
  upper edge: Vds,NM0 >= Vov1.  V(C) = vcm - Vth,NM0 - Vov1, so the Vov1 terms
              cancel and the edge is vcm <= V(A) + Vth,NM0
                                         = 0.70800 + 0.625 = 1.33300 V
  output side (vout = vcm in the follower) is looser:
              0.18400 V <= vout <= 1.800 - 0.09500 = 1.70500 V
  vcm = 1.17597 V is the exact centre of [1.01894, 1.33300], 157.0 mV from
  either edge.  It also lands V(C) = 0.33903 V within 41 mV of the 0.380 V at
  which NM0's Vth = 0.625 V was calibrated, so the body effect behind that
  number still applies (a 41 mV shift in Vsb moves Vth by about 10 mV, which
  moves V(C) by the same 10 mV and the two margins by 10 mV).              [OK]

================================================================================
(6) DC OPERATING-POINT CONSISTENCY -- what each stage produces versus what the
    next stage needs (explicit arithmetic; nothing is asserted to "self-adjust")
================================================================================
(a) Bias branch -> nfet current sources.  NM3 PRODUCES vbias = 0.71800 V.
    What NM2 NEEDS to deliver Itail at that gate voltage, with ITS parameters
    (muCox 247.7, Vth 0.536 -> Vov 0.18200), is W2/L = 16.260/3.0 = 5.4200:
      Id = 0.5*247.7u*5.4200*0.18200^2 = 22.235 uA = Itail.             match
    What NM4 NEEDS to deliver Id2 (muCox 254.8, Vth 0.534 -> Vov 0.18400) is
    W4/L = 71.500/3.0 = 23.8333:
      Id = 0.5*254.8u*23.8333*0.18400^2 = 102.797 uA = Id2.             match
    Against the plain mirror law the widths are 0.4 % and 5.3 % smaller
    (section 1, k2 and k4); using the plain law is what cost round 0 its 5 %.
(b) First stage -> its own load.  The tail delivers 22.235 uA, so NM0 and NM1
    each carry 11.117 uA and therefore PM2 and PM1 each carry 11.117 uA.  PM2
    is diode connected and reports that current back as a voltage:
      V(A) = VDD - |Vth,PM2| - sqrt(2*Id1*Lp/(muCoxP2*Wp2))
           = 1.800 - 0.992 - sqrt(2*11.117u*0.5u/(176.4u*6.305u))
           = 1.800 - 0.992 - 0.09998 = 0.70802 V.
    PM1 sees that same Vgs and is saturated, so it sources 11.117 uA into node
    B while NM1 sinks 11.117 uA out of it: the load is balanced at
    V(B) = V(A) with zero net current into node B.
(c) First stage -> second stage (the critical interface).  The voltage the
    first stage PRODUCES at B is 0.70802 V.  The voltage PM0 NEEDS at its gate
    to carry NM4's 102.797 uA is
      V(B),req = VDD - |Vth,PM0| - sqrt(2*Id2*Lp/(muCoxP0*Wp0))
               = 1.800 - 0.997 - sqrt(2*102.797u*0.5u/(160.8u*70.840u))
               = 1.800 - 0.997 - 0.09500 = 0.70800 V.
    Produced 0.70802 V, needed 0.70800 V: 18 uV apart.  This is not luck and
    it is not the plain mirror law either -- PM0 and PM2 have different Vth
    (0.997 against 0.992) and different muCox (160.8 against 176.4), so equal
    width-per-ampere would NOT give equal gate voltages.  What makes the two
    agree is (E0): VovP2 was set to VovP0 + 0.005 V precisely so that
      VDD - |Vth,PM2| - VovP2 = VDD - |Vth,PM0| - VovP0,
    and Wp0/Wp2 = 70.840/6.305 = 11.236 = (Id2/Id1)*kp = 9.2466*1.21553 =
    11.2395 (the 0.04 % difference is the 5 nm width grid).
    Checking the two output branch currents at that node voltage:
      Id,PM0 = 0.5*160.8u*(70.840/0.5)*0.09500^2 = 102.804 uA
      Id,NM4 = 0.5*254.8u*(71.500/3.0)*0.18400^2 = 102.797 uA
    -> net 7 nA into node vout, 6.8e-5 of the branch current.  The feedback
    absorbs it by moving node B by dV(B) = 0.5*VovP0*(dI/I)
    = 0.5*0.095*6.8e-5 = 3.2 uV.
(d) Second stage -> output and back through the feedback.  In the follower
    vout = vcm = 1.17597 V and both output devices are saturated there
    (section 5).  PM0's gate at 0.708 V is 0.468 V BELOW its drain, so PM0 is a
    saturated common-source amplifier, not a diode.  The feedback pins V(B) at
    the 0.70801 V of (c), because that is the only gate voltage at which PM0's
    current equals NM4's.  Quantitatively, a 10 % error in NM4's current would
    move node B by only
      dV(B) = 0.5*VovP0*(dI/I) = 0.5*0.095*0.10 = 4.75 mV
    and the resulting output offset, divided by the loop gain, is
      4.75 mV * Av2/Av = 4.75 mV * 75.49/3197.1 = 112 uV.
(e) Power audit.  Ibias + Itail + Id2 = 12.000 + 22.235 + 102.797
    = 137.032 uA; times VDD = 1.8 V this is 246.66 uW, which is the
    margin-corrected target 248.8 * 0.99145 = 246.66 uW, i.e. 0.86 % below the
    spec value on purpose so the measurement lands on 248.8 uW.
(f) Nothing above survives on continuous widths alone: _reevaluate() re-solves
    (a)-(e) from the GRIDDED widths that are actually shipped -- vbias from the
    rounded W3, every mirror current from that vbias, every overdrive from the
    rounded W -- and the reported prediction is that re-solve, not the
    continuous design point.  The 5 nm grid moves the crossing by 0.008 %.
================================================================================
(7) PYTHON CODE
================================================================================
"""

import math

# ---------------------------------------------------------------- process data
COX = 8.4e-3        # F/m^2   gate oxide capacitance (Sky130 1.8 V, tox ~ 4.1 nm)
COV = 0.20e-9       # F/m     gate-drain / gate-source overlap per unit width
CJD = 0.50e-9       # F/m     drain junction capacitance per unit width

# ------------------------------------------------------------ design decisions
LN = 3.0e-6         # nfet channel length  -- UNCHANGED: the calibrated lam_n
LP = 0.5e-6         # pfet channel length  -- UNCHANGED: the calibrated lam_p
VOVP0 = 0.095       # overdrive of PM0 (sets Av2 and gm2/Id2)
VOVB = 0.180        # overdrive of the nfet mirror family NM2/NM3/NM4
IBIAS = 12.0e-6     # I0 reference current (unchanged from round 0)
VOV1_MIN = 0.100    # validity band for the input-pair overdrive
VOV1_MAX = 0.260
PM_GUARD = 5.0      # deg demanded above the spec's phase-margin floor
CC_MIN, CC_MAX, CC_STEP = 0.10e-12, 1.60e-12, 1.0e-15
W_FINGER_MAX = 60e-6
W_MIN, W_MAX = 0.42e-6, 100e-6
L_MIN, L_MAX = 0.15e-6, 8.0e-6
W_GRID = 5e-9

# ------------------------------------------- margins from the round-0 residual
# The model BELOW, fed the calibrated parameters and the round-0 geometry,
# predicts 78.944 dB / 38.4544 MHz / 259.68 uW against measurements of
# 78.8492 dB / 40.1460 MHz / 261.92 uW.  Those residuals are the model error
# that survives recalibration, and the margin rules turn them into:
GAIN_MARGIN_DB = +0.095     # over-predicted by 0.095 dB -> design for +0.095 dB
GBW_MARGIN = -0.0421        # over-predicted by -4.21 %  -> design for 0.9579 x
POWER_MARGIN = -0.00855     # over-predicted by -0.86 %  -> design for 0.9914 x


def initial_params():
    """Calibrated Sky130 1.8 V parameters (round-0 operating point).

    Ignored from round 1 on -- compute_sizing() is called with these values --
    but kept so the file runs standalone and so the source of every number in
    the sections above is visible.
    """
    return {
        "NM0": {"type": "NMOS", "muCox": 317.3e-6, "a_gm": 0.762,
                "lam": 0.07618, "vth": 0.625},
        "NM1": {"type": "NMOS", "muCox": 316.8e-6, "a_gm": 0.763,
                "lam": 0.07855, "vth": 0.625},
        "NM2": {"type": "NMOS", "muCox": 247.7e-6, "a_gm": 0.973,
                "lam": 0.07266, "vth": 0.536},
        "NM3": {"type": "NMOS", "muCox": 252.1e-6, "a_gm": 0.974,
                "lam": 0.04522, "vth": 0.538},
        "NM4": {"type": "NMOS", "muCox": 254.8e-6, "a_gm": 0.964,
                "lam": 0.03124, "vth": 0.534},
        "PM0": {"type": "PMOS", "muCox": 160.8e-6, "a_gm": 0.510,
                "lam": 0.111, "vth": 0.997},
        "PM1": {"type": "PMOS", "muCox": 176.4e-6, "a_gm": 0.484,
                "lam": 0.09123, "vth": 0.992},
        "PM2": {"type": "PMOS", "muCox": 176.4e-6, "a_gm": 0.483,
                "lam": 0.09162, "vth": 0.992},
    }


# --------------------------------------------------------------------- helpers
def _finger(w_total):
    """Split a total width into m legal fingers on the 5 nm layout grid."""
    m = max(1, int(math.ceil(w_total / W_FINGER_MAX)))
    w = w_total / m
    while w < W_MIN and m > 1:
        m -= 1
        w = w_total / m
    w = max(W_MIN, min(W_MAX, round(w / W_GRID) * W_GRID))
    return w, m


def _ac(gm1, gm2, ro1, ro2, cc_eff, c1, c2, p3):
    """Loop response -> (Adc, w_c, PM, p1, p2, z, p3).

        A(s) = Adc * (1 - s/z) * (1 + s/(2*p3)) / ((1+s/p1)(1+s/p2)(1+s/p3))

    p1, p2 are the split Miller poles, z = +gm2/Cc_eff the RHP zero, and p3
    with its zero at 2*p3 the PM2/PM1 mirror doublet at node A.  |A(w_c)| = 1
    is solved by geometric bisection.
    """
    adc = gm1 * ro1 * gm2 * ro2
    p1 = 1.0 / (gm2 * ro1 * ro2 * cc_eff)
    p2 = gm2 * cc_eff / (c1 * c2 + cc_eff * (c1 + c2))
    z = gm2 / cc_eff

    def mag(w):
        return (adc * math.sqrt(1.0 + (w / z) ** 2)
                * math.sqrt(1.0 + (w / (2.0 * p3)) ** 2)
                / (math.sqrt(1.0 + (w / p1) ** 2)
                   * math.sqrt(1.0 + (w / p2) ** 2)
                   * math.sqrt(1.0 + (w / p3) ** 2)))

    lo, hi = 1.0e3, 1.0e12
    if mag(lo) < 1.0 or mag(hi) > 1.0:
        return None
    for _ in range(70):
        mid = math.sqrt(lo * hi)
        if mag(mid) > 1.0:
            lo = mid
        else:
            hi = mid
    wc = math.sqrt(lo * hi)
    pm = 180.0 - math.degrees(math.atan(wc / p1) + math.atan(wc / p2)
                              + math.atan(wc / z) + math.atan(wc / p3)
                              - math.atan(wc / (2.0 * p3)))
    return adc, wc, pm, p1, p2, z, p3


def _caps(w, pr):
    """Node capacitances from the widths (rule 4: the parasitics are carried)."""
    cgs_pm0 = (2.0 / 3.0) * w["PM0"] * LP * COX + COV * w["PM0"]
    cgs_pm2 = (2.0 / 3.0) * w["PM2"] * LP * COX + COV * w["PM2"]
    c1 = cgs_pm0 + (COV + CJD) * (w["PM1"] + w["NM1"])          # node B
    c2 = pr["cl"] + CJD * w["PM0"] + (CJD + COV) * w["NM4"]     # node vout
    c_a = 2.0 * cgs_pm2 + CJD * w["PM2"] + (CJD + COV) * w["NM0"]
    return c1, c2, c_a


def _widths(id1, id2, vov1, pr):
    """Every width from its own calibrated muCox / Vth at its own gate drive.

    INDEPENDENT:  NM3 (mirror reference), NM0, PM2.
    MATCHED:      NM1 = NM0, PM1 = PM2.
    MIRROR:       NM2, NM4 of NM3 (same L = LN, gate = vbias);
                  PM0 of PM2      (same L = LP, gate = node B).
    A mirror's width is the plain current ratio times the reference width,
    CORRECTED for the measured parameter offsets between the two devices --
    see section (1); with identical muCox and Vth the correction is 1.000.
    """
    w = {}
    w["NM3"] = 2.0 * IBIAS * LN / (pr["mu"]["NM3"] * VOVB ** 2)
    w["NM2"] = 2.0 * (2.0 * id1) * LN / (pr["mu"]["NM2"] * pr["vov"]["NM2"] ** 2)
    w["NM4"] = 2.0 * id2 * LN / (pr["mu"]["NM4"] * pr["vov"]["NM4"] ** 2)
    w["NM0"] = 2.0 * id1 * LN / (pr["mu"]["NM0"] * vov1 ** 2)
    w["NM1"] = w["NM0"]
    w["PM2"] = 2.0 * id1 * LP / (pr["mu"]["PM2"] * pr["vov"]["PM2"] ** 2)
    w["PM1"] = w["PM2"]
    w["PM0"] = 2.0 * id2 * LP / (pr["mu"]["PM0"] * VOVP0 ** 2)
    return w


def _operating_point(gm1, vov1, cc, isig, pr):
    """Everything downstream of a trial (gm1, C0): currents, widths, caps, AC."""
    id1 = gm1 * vov1 / (2.0 * pr["a"]["NM0"])
    id2 = isig - 2.0 * id1                                      # (E2)
    if id2 <= 15e-6 or id1 <= 1e-6:
        return None
    gm2 = 2.0 * pr["a"]["PM0"] * id2 / VOVP0
    gm_pm2 = 2.0 * pr["a"]["PM2"] * id1 / pr["vov"]["PM2"]

    w = _widths(id1, id2, vov1, pr)
    if min(w.values()) < W_MIN or max(w.values()) > 8.0 * W_FINGER_MAX:
        return None
    c1, c2, c_a = _caps(w, pr)
    cc_eff = cc + COV * w["PM0"]            # Cgd,PM0 parallels the Miller cap
    p3 = gm_pm2 / c_a

    ro1 = 1.0 / (id1 * pr["s1"])
    ro2 = 1.0 / (id2 * pr["s2"])
    res = _ac(gm1, gm2, ro1, ro2, cc_eff, c1, c2, p3)
    if res is None:
        return None
    adc, wc, pm, p1, p2, z, p3 = res
    return {"id1": id1, "id2": id2, "gm1": gm1, "gm2": gm2, "gm_pm2": gm_pm2,
            "ro1": ro1, "ro2": ro2, "c1": c1, "c2": c2, "c_a": c_a, "cc": cc,
            "cc_eff": cc_eff, "adc": adc, "wc": wc, "pm": pm, "p1": p1,
            "p2": p2, "z": z, "p3": p3, "vov1": vov1, "w": w}


def _solve_for_cc(cc, vov1, isig, pr):
    """(E3): scale gm1 until the true unity-gain crossing equals the target."""
    gm1 = pr["wu"] * cc                                 # first-order start
    op = None
    for _ in range(120):
        op = _operating_point(gm1, vov1, cc, isig, pr)
        if op is None:
            return None
        err = op["wc"] / pr["wu"]
        if abs(err - 1.0) < 1e-11:
            break
        gm1 = gm1 / err ** 0.6                          # damped fixed point
        if not (1e-6 < gm1 < 5e-3):
            return None
    if op is None or abs(op["wc"] / pr["wu"] - 1.0) > 1e-6:
        return None
    return op


def _reevaluate(w, pr, vdd):
    """Re-run the DC and AC on the GRIDDED widths that are actually shipped.

    Nothing is assumed to survive rounding: the bias branch is re-solved from
    the gridded NM3, every mirror current is recomputed from vbias / node B,
    and the reported prediction comes from those numbers.
    """
    vbias = pr["vth"]["NM3"] + math.sqrt(
        2.0 * IBIAS * LN / (pr["mu"]["NM3"] * w["NM3"]))
    vov = {d: vbias - pr["vth"][d] for d in ("NM2", "NM4")}
    itail = 0.5 * pr["mu"]["NM2"] * (w["NM2"] / LN) * vov["NM2"] ** 2
    id2 = 0.5 * pr["mu"]["NM4"] * (w["NM4"] / LN) * vov["NM4"] ** 2
    id1 = 0.5 * itail

    vov1 = math.sqrt(2.0 * id1 * LN / (pr["mu"]["NM0"] * w["NM0"]))
    vovp2 = math.sqrt(2.0 * id1 * LP / (pr["mu"]["PM2"] * w["PM2"]))
    vovp0 = math.sqrt(2.0 * id2 * LP / (pr["mu"]["PM0"] * w["PM0"]))

    gm1 = 2.0 * pr["a"]["NM0"] * id1 / vov1
    gm2 = 2.0 * pr["a"]["PM0"] * id2 / vovp0
    gm_pm2 = 2.0 * pr["a"]["PM2"] * id1 / vovp2
    ro1 = 1.0 / (id1 * pr["s1"])
    ro2 = 1.0 / (id2 * pr["s2"])
    c1, c2, c_a = _caps(w, pr)
    cc_eff = pr["cc"] + COV * w["PM0"]
    res = _ac(gm1, gm2, ro1, ro2, cc_eff, c1, c2, gm_pm2 / c_a)
    adc, wc, pm, p1, p2, z, p3 = res
    return {"vbias": vbias, "itail": itail, "id1": id1, "id2": id2,
            "vov1": vov1, "vovp2": vovp2, "vovp0": vovp0, "vov": vov,
            "gm1": gm1, "gm2": gm2, "gm_pm2": gm_pm2, "ro1": ro1, "ro2": ro2,
            "c1": c1, "c2": c2, "c_a": c_a, "cc_eff": cc_eff, "adc": adc,
            "wc": wc, "pm": pm, "p1": p1, "p2": p2, "z": z, "p3": p3,
            "power": vdd * (IBIAS + itail + id2)}


def compute_sizing(spec, params):
    tgt = spec["targets"]
    cond = spec["conditions"]
    vdd = cond["vdd"]
    cl = cond["cl"]
    pm_floor = spec.get("constraints", {}).get("pm_deg", {}).get("min", 45.0)

    # margin-corrected design targets (see the header block above)
    av_t = 10.0 ** ((tgt["gain_dB"] + GAIN_MARGIN_DB) / 20.0)
    wu_t = 2.0 * math.pi * tgt["gbw_Hz"] * (1.0 + GBW_MARGIN)
    itot = tgt["power_W"] * (1.0 + POWER_MARGIN) / vdd

    dev = ("NM0", "NM1", "NM2", "NM3", "NM4", "PM0", "PM1", "PM2")
    cal = initial_params()
    p = {d: dict(cal[d], **params.get(d, {})) for d in dev}
    pr = {"mu": {d: p[d]["muCox"] for d in dev},
          "a": {d: p[d]["a_gm"] for d in dev},
          "vth": {d: p[d]["vth"] for d in dev},
          "s1": p["NM1"]["lam"] + p["PM1"]["lam"],      # node B
          "s2": p["PM0"]["lam"] + p["NM4"]["lam"],      # node vout
          "cl": cl, "wu": wu_t}

    # ---- DC plan: every gate drive computed from the DRIVING device (rule 3)
    vbias = pr["vth"]["NM3"] + VOVB                     # NM3 diode produces it
    v_b = vdd - pr["vth"]["PM0"] - VOVP0                # PM0 needs it
    pr["vov"] = {"NM2": vbias - pr["vth"]["NM2"],
                 "NM4": vbias - pr["vth"]["NM4"],
                 "PM2": vdd - v_b - pr["vth"]["PM2"],   # so that V(A) = V(B)
                 "PM0": VOVP0}
    v_a = vdd - pr["vth"]["PM2"] - pr["vov"]["PM2"]
    if min(pr["vov"].values()) <= 0.0:
        raise RuntimeError("a gate drive came out non-positive")

    # ---- (E1) the gain fixes the product of the two stage overdrives
    av2 = 2.0 * pr["a"]["PM0"] / (VOVP0 * pr["s2"])
    vov1 = 2.0 * pr["a"]["NM0"] * av2 / (av_t * pr["s1"])
    if not (VOV1_MIN <= vov1 <= VOV1_MAX):
        raise RuntimeError("Vov1 = %.4f V is outside the calibrated validity "
                           "band; move VOVP0" % vov1)

    # ---- input common mode: centre of the window the two stages leave
    vcm_lo = pr["vth"]["NM0"] + vov1 + pr["vov"]["NM2"]     # tail stays in sat
    vcm_hi = v_a + pr["vth"]["NM0"]                        # NM0 stays in sat
    vcm = 0.5 * (vcm_lo + vcm_hi)
    if not (vcm_lo < vcm < vcm_hi):
        raise RuntimeError("empty input common-mode window")
    if vdd - vcm <= VOVP0 or vcm <= pr["vov"]["NM4"]:
        raise RuntimeError("output branch has no headroom at vout = vcm")

    # ---- (E2)/(E3)/(E4): C0 is the one knob left for the phase margin
    isig = itot - IBIAS
    best = None
    n = int(round((CC_MAX - CC_MIN) / CC_STEP))
    for i in range(n + 1):
        op = _solve_for_cc(CC_MIN + i * CC_STEP, vov1, isig, pr)
        if op is None:
            continue
        if best is None or op["pm"] > best["pm"]:
            best = op
    if best is None:
        raise RuntimeError("no sizing hits the gain/GBW/power targets")
    if best["pm"] < pm_floor + PM_GUARD:
        raise RuntimeError("best phase margin %.2f deg misses the %.1f deg "
                           "floor plus %.1f deg guard"
                           % (best["pm"], pm_floor, PM_GUARD))

    # ---- geometry, then an honest re-evaluation on the gridded widths
    g = {d: _finger(best["w"][d]) for d in ("NM0", "NM2", "NM3", "NM4",
                                            "PM0", "PM2")}
    g["NM1"] = g["NM0"]                     # MATCHED pair
    g["PM1"] = g["PM2"]                     # MATCHED load
    sizes = {}
    for d in dev:
        sizes[d] = {"w": g[d][0], "l": LN if d.startswith("NM") else LP,
                    "m": g[d][1]}
        assert W_MIN - 1e-12 <= sizes[d]["w"] <= W_MAX, d
        assert L_MIN <= sizes[d]["l"] <= L_MAX, d

    pr["cc"] = best["cc"]
    fin = _reevaluate({d: g[d][0] * g[d][1] for d in dev}, pr, vdd)

    return {
        "sizes": sizes,
        "biases": {},
        "currents": {"I0": IBIAS},
        "caps": {"C0": best["cc"]},
        "vcm": vcm,
        "predicted": {
            "gain_dB": 20.0 * math.log10(fin["adc"]),
            "gbw_Hz": fin["wc"] / (2.0 * math.pi),
            "pm_deg": fin["pm"],
            "power_W": fin["power"],
        },
    }


if __name__ == "__main__":   # local check of the numbers quoted in sections 4-6
    import json
    _spec = {
        "targets": {"gain_dB": 70.0, "gbw_Hz": 28159000.0, "power_W": 0.0002488},
        "conditions": {"vdd": 1.8, "cl": 2e-12, "vcm": None},
        "constraints": {"pm_deg": {"min": 45.0}},
    }
    _out = compute_sizing(_spec, initial_params())
    for _d, _s in sorted(_out["sizes"].items()):
        print("%-4s W = %8.4f um  L = %.2f um  m = %d  (total %8.4f um)"
              % (_d, 1e6 * _s["w"], 1e6 * _s["l"], _s["m"],
                 1e6 * _s["w"] * _s["m"]))
    print("I0   = %.3f uA" % (1e6 * _out["currents"]["I0"]))
    print("C0   = %.4f pF" % (1e12 * _out["caps"]["C0"]))
    print("vcm  = %.4f V" % _out["vcm"])
    print(json.dumps(_out["predicted"], indent=1))
