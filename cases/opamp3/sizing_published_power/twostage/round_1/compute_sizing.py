"""Round-1 sizing for the two-stage Miller op-amp of Fig. 4, Sky130 1.8 V.

Round 0 measured 64.676 dB / 20.118 MHz / 279.2 uW against 70 dB / 28.159 MHz /
248.8 uW.  Everything below is rebuilt on the round-0 calibration table.

================================================================================
(1) DEVICE ROLES  (unchanged from round 0; the classification is still correct)
================================================================================
I0   : ideal bias reference current pushed into the diode-connected NMOS NM3.
NM3  : diode-connected NMOS (Drain=Gate=vbias), gate reference of every NMOS
       current source.  INDEPENDENT -- its width sets Vov_b and hence vbias.
NM2  : tail source of the input pair (Gate=vbias).  MIRROR of NM3, same L.
NM0  : input device, gate = vin1 (inverting), drain = A.  INDEPENDENT.
NM1  : input device, gate = vin2, drain = B.  MATCHED to NM0 (identical W/L/m).
PM2  : diode-connected PMOS load of the NM0 branch (Drain=Gate=A).  INDEPENDENT;
       it sets the p-side Vgs and therefore V(A).
PM1  : PMOS mirror load of the NM1 branch (Gate=A, Drain=B).  MATCHED to PM2.
PM0  : second-stage common-source driver (Gate=B, Drain=vout).  MIRROR of PM2
       (same Vgs because V(B)=V(A), same L, W scaled by I2/Id1).
NM4  : second-stage current-source load (Gate=vbias).  MIRROR of NM3, same L.
C0   : Miller compensation capacitor from B to vout.
No variable voltage sources exist, so "biases" is empty; vcm is the only free DC
voltage and it is what places V(C), i.e. the input pair's Vds.

================================================================================
(2) DEVICE CONSTRAINTS  -- and what the calibration changed
================================================================================
Square law, same form as round 0:
    Id = (muCox/2)(m W/L) Vov^2,   gm = a_gm 2 Id/Vov,   gds = lam Id.
L = 2 um on every variable device (mirrors inherit it, rule 2).

The calibration table corrected three things that round 0 got wrong.

(a) PROCESS CONSTANTS.  muCox_n ~ 245 uA/V^2 (not 150), muCox_p ~ 85 uA/V^2
    (not 50), |Vth_p| = 1.047 V (not 0.90), Vth_n0 = 0.545-0.549 V.  These are
    passed in `params` and used verbatim.  The large |Vth_p| is the dominant
    structural fact of this circuit: V(A) = vdd - |Vth_p| - Vov_p = 0.753 - Vov_p,
    so the whole first-stage headroom budget is only
        Vov_p + Vov_b + margin(NM2) + Vov_n + margin(NM1) <= 0.753 V.
    Round 0 assumed 0.90 V and therefore believed V(A) = 0.640 V when the
    silicon gave 0.548 V -- 92 mV of first-stage headroom that never existed.

(b) WHICH lambda ENTERS THE GAIN.  Round 0 used lam(NM0) for stage 1.  Node A is
    the low-impedance diode node; the stage-1 output is node B, loaded by NM1 and
    PM1.  Recomputing round 0 with the calibrated numbers and the correct devices
        ro1 = 1/(Id1 (lam_NM1 + lam_PM1)) = 1/(10.6u * (0.6355+0.01009)) = 146.1 k
        A1  = gm_NM0 ro1 = 99.25u * 146.1k = 14.504
        ro2 = 1/(I2 (lam_PM0 + lam_NM4)) = 1/(126u * (0.02058+0.04696)) = 117.5 k
        A2  = gm_PM0 ro2 = 1009u * 117.5k = 118.59
        A   = 1720.0 -> 64.71 dB     vs measured 64.676 dB   (+0.03 dB)
    The gain model is therefore EXACT once the right lambdas are used; the
    +5.32 dB round-0 error was entirely lam = 0.07 (a guess) versus lam_NM1 =
    0.6355 (measured).  Gain is designed for 70.0 dB + 0.03 dB of residual, i.e.
    70.0 dB; no blanket +5.32 dB margin is applied because that error is now
    explained, not statistical.

(c) lambda IS A FUNCTION OF SATURATION MARGIN, NOT A CONSTANT.  The table is five
    NMOS points at the same L = 2 um, ordered by margin m = Vds - Vov:
        NM1  m = 19 mV   lam = 0.6355   VA = 1.574 V
        NM0  m = 31 mV   lam = 0.509    VA = 1.965 V
        NM2  m = 156 mV  lam = 0.1387   VA = 7.210 V
        NM3  m = 549 mV  lam = 0.06906  VA = 14.480 V
        NM4  m = 982 mV  lam = 0.04696  VA = 21.295 V
    and three PMOS points
        PM0  m = 443 mV  lam = 0.02058  VA = 48.591 V
        PM2  m = 1048 mV lam = 0.01017  VA = 98.328 V
        PM1  m = 1059 mV lam = 0.01009  VA = 99.108 V
    A log-log least-squares fit (done at run time from these pairs) gives
        VA_n = 22.28 * m^0.674   (max residual 12 % over 19 mV .. 982 mV)
        VA_p = 94.60 * m^0.818   (max residual 0.1 %)
    This is not a re-estimate of a device parameter: it is the given lambdas,
    read as the function of operating point that they actually are.  It is the
    key design lever this round -- round 0's input pair had only 19 mV of margin,
    which is why its ro1 was 146 k and its gain 5 dB short.  Moving the pair to
    63 mV of margin cuts lam_NM1 from 0.6355 to 0.290, i.e. 2.19x more intrinsic
    output resistance per unit of drain current, bought with headroom instead of
    current.
    Sensitivity: a +-20 % error in lam_NM1 at the chosen margin moves the gain to
    71.86 dB / 68.47 dB, i.e. +1.86/-1.53 dB, inside the +-3 dB window.

(d) MIRROR RATIOS ARE NOT PURE WIDTH RATIOS.  Round 0 asked for Itail = 20.0 uA
    and I2 = 110.2 uA and got 21.3 uA and 126 uA (+6.5 % and +14 %), which is the
    whole -10.9 % power error.  Cause: muCox and Vth differ slightly per device
    (NM4 263 uA/V^2 / 544 mV versus NM3 247.2 / 549), and the mirror shares Vgs,
    not Vov.  Correct mirror law, same L (rule 2) with the calibrated correction:
        vbias   = vth_NM3 + Vov_b                        (NM3 diode produces it)
        Vov_dev = vbias - vth_dev                        (what the mirror sees)
        W_dev   = 2 Id L /(muCox_dev Vov_dev^2)
                = W_NM3 (Id/I0) (muCox_NM3/muCox_dev)(Vov_b/Vov_dev)^2
    Replaying round 0's netlist through this law: Vov_NM3 = 155.8 mV (table 156),
    vbias = 704.8 mV (table 705), Vov_NM2 = 159.8 mV (table 160), Itail =
    21.14 uA (measured 21.3), Vov_NM4 = 160.8 mV (table 161), I2 = 125.2 uA
    (measured 126), total 277.8 uW (measured 279.2).  Residual -0.5 %, so power
    is designed for 0.995 x 248.8 uW = 247.6 uW instead of carrying a 12 % bias.
    The same law applied to PM0 removes the 12 mV V(A)-V(B) offset the table
    shows (PM0 needed Vov = 214 mV but V(A) only offered 202 mV, so node B had to
    sag 12 mV): sizing PM0 from its OWN muCox/vth makes V(B) = V(A) exactly.

(e) THE MISSING GBW CAPACITANCE.  GBW = gm1/(2 pi (C0 + Cpar)) is structurally
    right (it is gain x dominant pole with the Miller term dominating), and gm1
    was measured as 99.25 uS with C0 = 429.3 fF in the netlist, so
        Cpar = 99.25u/(2 pi 20.1179 MHz) - 429.3 fF = 786.4 - 429.3 = 357.1 fF
    on a PM0 that is 130.44 um wide -> 2.737 fF per um of PM0 width, versus the
    0.20 fF/um overlap-only guess of round 0, a 13.7x miss.  It is charged per
    micron of PM0 (it tracks PM0's gate area at fixed L), so it is modelled as
        Cpar = K_CPAR * W_PM0,  K_CPAR = 2.737e-9 F/m   (fitted, round 0)
    Rule 4 therefore bites hard here: PM0's width is now a GBW cost, not just a
    phase-margin cost, and the margin rule's "+40 %" is implemented physically
    through this constant rather than as a blind 1.4x on the target.  Check: with
    round-0 sizes this model reproduces 20.118 MHz exactly, by construction.

Free shape variables this round (chosen in (4)/(5) against the budget in (2a)):
    Vov_b = 0.12 V, Vov_p = 0.18 V, Vov_n = 0.30 V, I0 = 8 uA, Itail = 48 uA,
    and margin(NM1) SOLVED from the gain target.

================================================================================
(3) SIGNAL PATH
================================================================================
vin1 (inverting) -> NM0 gate.  The pair splits Itail; the NM0 half enters the
diode PM2 and is mirrored by PM1 into node B, so the single-ended first-stage
transconductance is the full gm of one input device:
    stage 1:  vB   = -gm_NM0 * (ro_NM1 || ro_PM1) * vid        (node B, high-Z)
    stage 2:  vout = -gm_PM0 * (ro_PM0 || ro_NM4) * vB
Node A is diode-loaded and low impedance, so lam_NM0 and lam_PM2 do not appear
in the gain -- only lam_NM1, lam_PM1 (node B) and lam_PM0, lam_NM4 (node vout).
C0 bridges B and vout, Miller-splits the poles, and makes B the dominant pole.
Bench: vout -> vin1 through the DC inductor, AC injected at vin1, so the measured
quantity is this two-stage loop gain.

================================================================================
(4) DESIGN EQUATIONS (symbolic)
================================================================================
Power (fitted target, +-25 %):
    P = vdd (I0 + Itail + I2)   ->   I2 = K_P P_target/vdd - I0 - Itail    (P)
    K_P = 0.995 (model-vs-measured residual of the corrected mirror law, (2d)).

Headroom / node voltages, each from the device that drives it (rule 3):
    vbias = vth_NM3 + Vov_b                                   (NM3 diode)
    V(A)  = V(B) = vdd - vth_PM2 - Vov_p                      (PM2 diode)
    V(C)  = V(A) - Vov_n - m1,   m1 = saturation margin of NM1              (H)
    vcm   = vout = V(C) + vth_NM0(V(C)) + Vov_n               (NM0 gate)
    vth_NM0(Vsb) = vth0_n + gamma (sqrt(phi+Vsb) - sqrt(phi)),  gamma = 0.4495
    from the table itself: NM0 reads 626 mV at Vsb = 316 mV while its Vsb = 0
    sibling NM3 reads 549 mV, so gamma = 0.077/(sqrt(1.016)-sqrt(0.7)).
Saturation margins, all expressed in the above:
    m(NM3) = vbias - Vov_b                 m(NM2) = V(C) - Vov_NM2
    m(NM1) = m1                            m(PM1) = vth_PM2  (independent of Vov_p)
    m(PM0) = (vdd - vout) - Vov_PM0        m(NM4) = vout - Vov_NM4

Gain (with lam = 1/VA(m) from (2c)):
    A1 = 2 a_gm_NM0 / (Vov_n (lam_NM1(m1) + lam_PM1))                      (A1)
    A2 = 2 a_gm_PM0 / (Vov_PM0 (lam_PM0 + lam_NM4))                        (A2)
    A  = A1 A2,  gain_dB = 20 log10 A
Both stage gains are still current-independent, but they are now functions of the
BIAS POINT through VA(m).  A2 is pinned by Vov_p and the output swing (151.3,
i.e. 43.60 dB, at Vov_p = 0.18 V), so (A1) is solved for the only remaining
degree of freedom, the input pair's saturation margin m1:
    lam_NM1,req = 2 a_gm_NM0 /(Vov_n A_req/A2) - lam_PM1
    m1 = (1/(lam_NM1,req C_N))^(1/P_N)                                     (m1)
and (H) turns m1 into V(C) and hence vcm.  This is the round-1 replacement for
round 0's "solve Vov_n from the gain": Vov_n is now spent on GBW (it sets gm1)
and the gain is bought with headroom, which is free in current.

GBW (dominant pole at B, Miller term dominant):
    gm1 = a_gm_NM0 Itail / Vov_n
    GBW = gm1 / (2 pi (C0 + K_CPAR W_PM0))                                  (G)
solved for C0:   C0 = gm1/(2 pi GBW_target) - K_CPAR W_PM0.
C0 exists only if gm1/(2 pi GBW_target) > K_CPAR W_PM0, i.e. the GBW target caps
PM0's width.  That is what sets Itail = 48 uA (large gm1) and Vov_p = 0.18 V
(W_PM0 = 122 um, Cpar = 334 fF): required C_eff = 851.0 fF, Cpar = 334.3 fF,
C0 = 517 fF, so the Miller cap is still 61 % of the dominant-node capacitance
and the compensation is real rather than parasitic.  Had Itail stayed at 20 uA
(gm1 = 63 uS) the required C_eff would be 354 fF, LESS than Cpar alone, and
28.159 MHz would be unreachable at any C0 -- this is why the current split moved.

Phase margin (not a target; computed and reported):
    gm2 = 2 a_gm_PM0 I2/Vov_PM0
    p2 = gm2/(2 pi Cl_eff),  Cl_eff = CL + CJ_DRAIN (W_PM0 + W_NM4)
    z  = gm2/(2 pi (C0 + K_CPAR W_PM0))        (RHP zero, no nulling resistor)
    PM = 90 - atan(GBW/p2) - atan(GBW/z)   -> 53.1 deg here.
No measured PM came back this round, so CJ_DRAIN keeps its round-0 value and no
margin rule is applied to PM; sizing is not distorted to chase it.

================================================================================
(5) DC BIAS VERIFICATION (numbers, vdd = 1.8 V)
================================================================================
Currents:  P_design = 0.995 x 248.8 uW = 247.6 uW -> I_tot = 137.53 uA
           I0 = 8.00 uA, Itail = 48.00 uA, I2 = 81.53 uA, Id1 = 24.00 uA.
Overdrives: Vov_b = 0.120 V -> vbias = 0.549 + 0.120 = 0.669 V
            Vov_NM2 = 0.669 - 0.545 = 0.124 V,  Vov_NM4 = 0.669 - 0.544 = 0.125 V
            Vov_p   = 0.180 V (PM2/PM1), Vov_PM0 = 1.047 + 0.180 - 1.049 = 0.178 V
            Vov_n   = 0.300 V
Nodes, each from its driving device (rule 3):
  vbias = vth_NM3 + Vov_b                    = 0.549 + 0.120 = 0.669 V (NM3 diode)
  V(A)  = vdd - vth_PM2 - Vov_p              = 1.800 - 1.047 - 0.180 = 0.573 V
  V(B)  = V(A) = 0.573 V  (PM1 matched to PM2 at the same 24 uA; and PM0 is sized
          for I2 at exactly this Vgs, so node B does not have to sag -- see (6b))
  m1 solved from the gain target                              = 0.063 V
  V(C)  = V(A) - Vov_n - m1 = 0.573 - 0.300 - 0.063           = 0.210 V
  vth_NM0(Vsb=0.210) = 0.549 + 0.4495(sqrt(0.910)-sqrt(0.700)) = 0.602 V
  vcm   = V(C) + vth_NM0 + Vov_n = 0.210 + 0.602 + 0.300      = 1.111 V
  vout  = vcm = 1.111 V on the unity-gain bench.
Resulting stage split: A1 = 20.89 (26.40 dB), A2 = 151.3 (43.60 dB) -> 70.00 dB.
Saturation check, branch by branch (margin = Vds - Vov):
  NM3  Vds = vbias = 0.669 V      > Vov_b    = 0.120 V     margin +0.549 V  SAT
  NM2  Vds = V(C)  = 0.210 V      > Vov_NM2  = 0.124 V     margin +0.086 V  SAT
  NM0  Vds = V(A)-V(C) = 0.363 V  > Vov_n    = 0.300 V     margin +0.063 V  SAT
  NM1  Vds = V(B)-V(C) = 0.363 V  > 0.300 V                margin +0.063 V  SAT
  PM2  |Vds| = vdd-V(A) = 1.227 V > Vov_p    = 0.180 V     margin +1.047 V  SAT
  PM1  |Vds| = vdd-V(B) = 1.227 V > 0.180 V                margin +1.047 V  SAT
  PM0  |Vds| = vdd-vout = 0.689 V > Vov_PM0  = 0.178 V     margin +0.510 V  SAT
  NM4  Vds = vout = 1.111 V       > Vov_NM4  = 0.125 V     margin +0.987 V  SAT
Tightest branch is the input pair at +63 mV, against round 0's measured +19 mV
(NM1) and +31 mV (NM0): every device is further from the triode edge than the
round-0 point that the simulator already reported as 8/8 saturated, and NM2 went
from +156 mV to +86 mV, still three times the round-0 pair margin.
Input-CM window: V(C) may run from Vov_NM2 = 0.124 V (NM2 leaves saturation) to
V(A) - Vov_n = 0.273 V (pair leaves saturation), width 149 mV, and V(C) = 0.210 V
sits 86 mV above the bottom and 63 mV below the top, so vcm may drift -86/+63 mV.
The 63 mV is deliberate, not an accident: (m1) spends exactly the headroom the
70 dB target needs and no more, because surplus headroom would overshoot 73 dB.

================================================================================
(6) DC OPERATING-POINT CONSISTENCY (produced vs needed, with arithmetic)
================================================================================
a) Bias branch -> tail and output source.  NM3 at I0 = 8 uA with muCox = 247.2
   uA/V^2 needs W = 2(8u)(2u)/(247.2u x 0.120^2) = 8.99 um, and PRODUCES
   vbias = 0.549 + 0.120 = 0.669 V.
   NM2 NEEDS Itail = 48.00 uA at that same gate voltage.  Its own Vth is 545 mV,
   so it sees Vov = 0.669 - 0.545 = 0.124 V, and with its own muCox = 248.8
   W_NM2 = 2(48u)(2u)/(248.8u x 0.124^2) = 50.18 um (m=3 x 16.73 um).
   Back-check: Id = (248.8u/2)(50.18/2)(0.124^2) = 48.00 uA.  Wanted 48.00 uA.
   NM4 NEEDS I2 = 81.53 uA; Vth = 544 mV -> Vov = 0.125 V, muCox = 263,
   W_NM4 = 2(81.53u)(2u)/(263u x 0.125^2) = 79.36 um (m=4 x 19.84 um).
   Back-check: Id = (263u/2)(79.36/2)(0.125^2) = 81.53 uA.  Wanted 81.53 uA.
   Note the width ratios are 5.58 and 8.83, not the naive Itail/I0 = 6.00 and
   I2/I0 = 10.19: the (muCox_NM3/muCox_dev)(Vov_b/Vov_dev)^2 factors are 0.930 and
   0.867.  Applying them is exactly what removes round 0's +6.5 %/+14 % current
   error, i.e. the whole power miss.
b) First stage -> second-stage gate.  The pair splits Itail into Id1 = 24.00 uA.
   PM2 must sink 24.00 uA; W_PM2 = 2(24u)(2u)/(86.12u x 0.180^2) = 34.41 um
   (m=2 x 17.20 um), so it does so at Vov = sqrt(2(24u)(2u)/(86.12u x 34.41u)) =
   0.180 V and PRODUCES V(A) = 1.800 - 1.047 - 0.180 = 0.573 V.  PM1 is its twin
   carrying the other 24.00 uA at the same Vgs, so V(B) = 0.573 V.
   PM0 NEEDS a gate voltage that makes it carry I2 = 81.53 uA.  At V(B) = 0.573 V
   its Vgs is 1.227 V and, with its OWN Vth = 1.049 V, its overdrive is
   1.227 - 1.049 = 0.178 V -- 2 mV more than PM2's 0.180 V because PM0's Vth is
   2 mV higher.  The width that carries 81.53 uA at 0.178 V with muCox = 84.27 is
   W_PM0 = 2(81.53u)(2u)/(84.27u x 0.178^2) = 122.14 um (m=7 x 17.45 um), a ratio
   of 3.550 to PM2 and not I2/Id1 = 3.397.  Needed gate 0.573 V, produced gate
   0.573 V: the 3.550 ratio is what makes those two numbers equal.  Round 0 used
   the naive ratio and the table shows the consequence -- PM0 needed 214 mV of
   overdrive but was offered 202 mV, so node B sagged 12 mV below node A.
c) Second stage -> output node / feedback.  PM0 at V(B) = 0.573 V delivers
   81.53 uA; NM4 at vbias = 0.669 V sinks 81.53 uA; difference 0.00 uA by (a)+(b),
   so the output node balances at the vout the feedback enforces.  Residual
   mismatch dI is absorbed by node B moving dI/gm_PM0 = dI/785 uS: a 10 % current
   error (8.2 uA) moves V(B) by 10.4 mV, which is 17 % of NM1's 63 mV margin, so
   the first stage stays saturated.  (Round 0's 12 mV sag, measured, is the same
   mechanism and it cost it 12 mV of pair Vds -- part of why lam_NM1 was 0.6355.)
d) Input side.  The pair needs Vgs = vth_NM0(Vsb = 0.210) + Vov_n = 0.602 + 0.300
   = 0.902 V.  The bench holds vin = vcm and the follower holds vout = vcm, so
   with vcm = 1.111 V the pair's source sits at V(C) = 1.111 - 0.902 = 0.210 V,
   which is the value used in (5): produced by NM0/NM1, needed by NM2 (>= 0.124 V
   for saturation, 0.210 V gives it +86 mV).  The body-effect term matters here:
   at Vsb = 0.210 V, Vth_NM0 is 602 mV, not the 626 mV the table reports at
   round 0's Vsb = 316 mV, and ignoring the 24 mV would misplace V(C) by 24 mV --
   38 % of the pair's margin.  Round 0 misplaced V(C) by +21 mV for exactly this
   reason (it assumed Vgs = 0.848 V; the silicon needed 0.827 V).

(7) code below.
"""
import math

# ---------------------------------------------------------------------------
# Round-0 calibration, read off the table in the prompt.
# ---------------------------------------------------------------------------
# (saturation margin m = Vds - Vov [V],  lambda [1/V])  at L = 2 um.
LAM_CAL_N = [(0.019, 0.6355), (0.031, 0.509), (0.156, 0.1387),
             (0.549, 0.06906), (0.982, 0.04696)]
LAM_CAL_P = [(0.443, 0.02058), (1.048, 0.01017), (1.059, 0.01009)]

# Body effect, from NM0 (626 mV at Vsb = 316 mV) vs NM3 (549 mV at Vsb = 0).
PHI_B = 0.70                      # V, 2*phi_F
GAMMA_N = 0.077 / (math.sqrt(PHI_B + 0.316) - math.sqrt(PHI_B))   # ~0.4495
VSB_CAL_NM0 = 0.316               # V, the Vsb at which vth_NM0 was measured

# Node-B parasitic in parallel with C0, fitted from round 0 (see (2e)):
#   Cpar = 99.25uS/(2 pi 20.1179 MHz) - 429.3 fF = 357.1 fF  at W_PM0 = 130.44 um
K_CPAR = 2.737e-9                 # F per metre of PM0 width
CJ_DRAIN = 0.80e-9                # F/m of width, drain junction at vout (PM only)

K_POWER = 0.995                   # corrected mirror law still 0.5 % optimistic

# ---------------------------------------------------------------------------
# Chosen shape variables (justified in (4)/(5))
# ---------------------------------------------------------------------------
L_ALL = 2.0e-6
VOV_B = 0.12                      # NM3 overdrive -> vbias
VOV_P = 0.18                      # PM2/PM1 overdrive
VOV_N = 0.30                      # input-pair overdrive (sets gm1 for GBW)
I_REF = 8.0e-6                    # I0
I_TAIL = 48.0e-6                  # tail current (chosen so C0 > 0, see (4)/(G))

M1_MIN = 0.050                    # V, floor on the input pair's margin
M_NM2_MIN = 0.050                 # V, floor on the tail source's margin

W_MIN, W_MAX = 0.42e-6, 100e-6
W_FINGER = 20e-6


def _fit_loglog(pairs):
    """Least squares of ln(VA) vs ln(m); returns (C, p) with VA = C m**p."""
    xs = [math.log(m) for m, lam in pairs]
    ys = [math.log(1.0 / lam) for m, lam in pairs]
    n = len(xs)
    xbar = sum(xs) / n
    ybar = sum(ys) / n
    sxy = sum((x - xbar) * (y - ybar) for x, y in zip(xs, ys))
    sxx = sum((x - xbar) ** 2 for x in xs)
    p = sxy / sxx
    return math.exp(ybar - p * xbar), p


C_VAN, P_VAN = _fit_loglog(LAM_CAL_N)     # ~ (22.28, 0.674)
C_VAP, P_VAP = _fit_loglog(LAM_CAL_P)     # ~ (94.60, 0.818)


def _lam_n(m):
    return 1.0 / (C_VAN * max(m, 1e-3) ** P_VAN)


def _lam_p(m):
    return 1.0 / (C_VAP * max(m, 1e-3) ** P_VAP)


def _m_from_lam_n(lam):
    """Invert VA_n = C m**p for the margin that yields this lambda."""
    return (1.0 / (lam * C_VAN)) ** (1.0 / P_VAN)


def initial_params():
    """Round-0 calibrated values (round 0 only; ignored from round 1 on)."""
    tbl = {
        "NM0": (242.3e-6, 0.941, 0.509, 0.626),
        "NM1": (240.6e-6, 0.933, 0.6355, 0.626),
        "NM2": (248.8e-6, 0.963, 0.1387, 0.545),
        "NM3": (247.2e-6, 0.971, 0.06906, 0.549),
        "NM4": (263.0e-6, 0.957, 0.04696, 0.544),
        "PM0": (84.27e-6, 0.857, 0.02058, -1.049),
        "PM1": (86.13e-6, 0.848, 0.01009, -1.047),
        "PM2": (86.12e-6, 0.848, 0.01017, -1.047),
    }
    out = {}
    for d, (mc, ag, lam, vth) in tbl.items():
        out[d] = dict(type="NMOS" if d.startswith("NM") else "PMOS",
                      muCox=mc, a_gm=ag, lam=lam, vth=vth)
    return out


def _g(params, dev, key, default):
    v = params.get(dev, {}).get(key)
    return default if v is None else v


def _fingers(w_tot):
    """Split a total width into m fingers, keeping m*W = w_tot exactly."""
    w_tot = max(w_tot, W_MIN)
    m = max(1, int(math.ceil(w_tot / W_FINGER)))
    w = w_tot / m
    if w < W_MIN:
        m, w = 1, W_MIN
    if w > W_MAX:
        m = int(math.ceil(w_tot / W_MAX))
        w = w_tot / m
    return {"w": w, "l": L_ALL, "m": int(m)}


def compute_sizing(spec, params):
    t = spec["targets"]
    c = spec["conditions"]
    vdd = c["vdd"]
    cl = c["cl"]
    gain_req_dB = t["gain_dB"]
    gbw_req = t["gbw_Hz"]
    p_req = t.get("power_W")

    d = initial_params()
    for k in d:
        d[k].update({kk: vv for kk, vv in params.get(k, {}).items()
                     if vv is not None})

    mc = {k: d[k]["muCox"] for k in d}
    ag = {k: d[k]["a_gm"] for k in d}
    vth = {k: abs(d[k]["vth"]) for k in d}

    # --- (P) power target -> branch currents -------------------------------
    i0 = I_REF
    i_tail = I_TAIL
    if p_req:
        i2 = K_POWER * p_req / vdd - i0 - i_tail
    else:
        i2 = 80.0e-6
    i2 = max(i2, 10.0e-6)
    id1 = i_tail / 2.0

    # --- mirror overdrives from the shared gate voltages (2d) --------------
    vbias = vth["NM3"] + VOV_B
    vov_nm2 = max(vbias - vth["NM2"], 0.02)
    vov_nm4 = max(vbias - vth["NM4"], 0.02)
    v_a = vdd - vth["PM2"] - VOV_P                 # = V(B)
    vov_pm0 = max(vth["PM2"] + VOV_P - vth["PM0"], 0.02)

    # --- widths -------------------------------------------------------------
    w_nm3 = 2.0 * i0 * L_ALL / (mc["NM3"] * VOV_B ** 2)          # INDEPENDENT
    w_nm2 = 2.0 * i_tail * L_ALL / (mc["NM2"] * vov_nm2 ** 2)    # MIRROR of NM3
    w_nm4 = 2.0 * i2 * L_ALL / (mc["NM4"] * vov_nm4 ** 2)        # MIRROR of NM3
    w_n = 2.0 * id1 * L_ALL / (mc["NM0"] * VOV_N ** 2)           # NM0, NM1 matched
    w_p = 2.0 * id1 * L_ALL / (mc["PM2"] * VOV_P ** 2)           # PM2, PM1 matched
    w_pm0 = 2.0 * i2 * L_ALL / (mc["PM0"] * vov_pm0 ** 2)        # MIRROR of PM2

    # --- (m1) gain target -> input-pair saturation margin -------------------
    a_req = 10.0 ** (gain_req_dB / 20.0)
    lam_pm1 = _lam_p(vth["PM2"])                   # m(PM1) = vth_PM2 exactly
    vth0_n = vth["NM0"] - GAMMA_N * (math.sqrt(PHI_B + VSB_CAL_NM0)
                                     - math.sqrt(PHI_B))
    m1_hi = max(v_a - VOV_N - vov_nm2 - M_NM2_MIN, M1_MIN)

    m1 = min(0.070, m1_hi)
    for _ in range(60):
        v_c = v_a - VOV_N - m1
        vth_n0 = vth0_n + GAMMA_N * (math.sqrt(PHI_B + max(v_c, 0.0))
                                     - math.sqrt(PHI_B))
        vcm = v_c + vth_n0 + VOV_N
        vout = vcm
        lam_pm0 = _lam_p(max(vdd - vout - vov_pm0, 0.01))
        lam_nm4 = _lam_n(max(vout - vov_nm4, 0.01))
        a2 = 2.0 * ag["PM0"] / (vov_pm0 * (lam_pm0 + lam_nm4))
        a1_req = a_req / a2
        lam_nm1_req = 2.0 * ag["NM0"] / (VOV_N * a1_req) - lam_pm1
        if lam_nm1_req <= 0.0:
            m1_new = m1_hi
        else:
            m1_new = _m_from_lam_n(lam_nm1_req)
        m1_new = min(max(m1_new, M1_MIN), m1_hi)
        if abs(m1_new - m1) < 1e-9:
            m1 = m1_new
            break
        m1 = m1_new

    # final operating point at the converged margin
    v_c = v_a - VOV_N - m1
    vth_n0 = vth0_n + GAMMA_N * (math.sqrt(PHI_B + max(v_c, 0.0))
                                 - math.sqrt(PHI_B))
    vcm = v_c + vth_n0 + VOV_N
    vout = vcm
    lam_nm1 = _lam_n(m1)
    lam_pm0 = _lam_p(max(vdd - vout - vov_pm0, 0.01))
    lam_nm4 = _lam_n(max(vout - vov_nm4, 0.01))

    # --- transconductances --------------------------------------------------
    gm1 = ag["NM0"] * 2.0 * id1 / VOV_N
    gm2 = ag["PM0"] * 2.0 * i2 / vov_pm0

    # --- (G) GBW target -> compensation capacitor ---------------------------
    c_par = K_CPAR * w_pm0
    cc_tot = gm1 / (2.0 * math.pi * gbw_req)
    c0 = max(cc_tot - c_par, 20e-15)
    cc_eff = c0 + c_par

    sizes = {
        "NM0": _fingers(w_n), "NM1": _fingers(w_n),
        "NM2": _fingers(w_nm2), "NM3": _fingers(w_nm3), "NM4": _fingers(w_nm4),
        "PM2": _fingers(w_p), "PM1": _fingers(w_p), "PM0": _fingers(w_pm0),
    }

    # --- predictions --------------------------------------------------------
    a1 = 2.0 * ag["NM0"] / (VOV_N * (lam_nm1 + lam_pm1))
    a2 = 2.0 * ag["PM0"] / (vov_pm0 * (lam_pm0 + lam_nm4))
    gain_db = 20.0 * math.log10(a1 * a2)
    gbw = gm1 / (2.0 * math.pi * cc_eff)
    cl_eff = cl + CJ_DRAIN * (w_pm0 + w_nm4)
    f_p2 = gm2 / (2.0 * math.pi * cl_eff)
    f_z = gm2 / (2.0 * math.pi * cc_eff)
    pm = 90.0 - math.degrees(math.atan(gbw / f_p2)) \
              - math.degrees(math.atan(gbw / f_z))
    power = vdd * (i0 + i_tail + i2)

    return {
        "sizes": sizes,
        "biases": {},
        "currents": {"I0": i0},
        "caps": {"C0": c0},
        "vcm": vcm,
        "predicted": {"gain_dB": gain_db, "gbw_Hz": gbw, "pm_deg": pm,
                      "power_W": power},
    }
