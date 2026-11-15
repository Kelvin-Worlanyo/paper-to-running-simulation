# Sizing round 1: two-stage Miller op-amp (Fig. 4): port all sizes to Sky130 -- power fitted, phase margin floored at 45 deg

You derive analytical design equations for an analog circuit and encode them as a
Python sizing function. A script executes it unmodified, a simulator measures the
result, and calibration data comes back in the next round (to a fresh session).
Read only this prompt and the files it names. Do not open any other file.

## Circuit (from the paper's figure; ids are the printed designators)
```
pins: vdd=vdd gnd=gnd out=vout in=['vin1', 'vin2']
inverting input (decided by simulation): vin1
I0     Current  core  In=vdd Out=vbias                                 VARIABLE
PM2    PMOS     core  Drain=A Gate=A Source=vdd Body=vdd               VARIABLE
PM1    PMOS     core  Drain=B Gate=A Source=vdd Body=vdd               VARIABLE
PM0    PMOS     core  Drain=vout Gate=B Source=vdd Body=vdd            VARIABLE
NM0    NMOS     core  Drain=A Gate=vin1 Source=C Body=gnd              VARIABLE
NM1    NMOS     core  Drain=B Gate=vin2 Source=C Body=gnd              VARIABLE
NM2    NMOS     core  Drain=C Gate=vbias Source=gnd Body=gnd           VARIABLE
NM3    NMOS     core  Drain=vbias Gate=vbias Source=gnd Body=gnd       VARIABLE
NM4    NMOS     core  Drain=vout Gate=vbias Source=gnd Body=gnd        VARIABLE
C0     Cap      core  Pos=B Neg=vout                                   VARIABLE
```

## Specification
```json
{
 "targets": {
  "gain_dB": 70.0,
  "gbw_Hz": 28159000.0,
  "power_W": 0.0002488
 },
 "tolerance": {
  "gain_dB": [
   "abs",
   3.0
  ],
  "gbw_Hz": [
   "rel",
   0.25
  ],
  "power_W": [
   "rel",
   0.25
  ]
 },
 "conditions": {
  "vdd": 1.8,
  "cl": 2e-12,
  "vcm": null
 },
 "variables": {
  "devices": [
   "NM0",
   "NM1",
   "NM2",
   "NM3",
   "NM4",
   "PM0",
   "PM1",
   "PM2"
  ],
  "currents": [
   "I0"
  ],
  "caps": [
   "C0"
  ],
  "vcm": true
 },
 "constraints": {
  "pm_deg": {
   "min": 45.0,
   "why": "a design floor, not a value read from the paper"
  }
 },
 "also_required": "every transistor saturated; unity-gain follower settles at vcm"
}
```

Targets are to be MET WITHIN TOLERANCE (not exceeded by as much as possible).

## Rules (apply them; do not restate them)

1. Structure your reasoning in seven sections, in order, BEFORE writing code:
   (1) Device roles  (2) Device constraints  (3) Signal path  (4) Design
   equations (gain, GBW, phase margin, power; symbolic)  (5) DC bias
   verification: show that every branch supports saturation, with numbers
   (6) DC operating-point consistency: show the voltage each stage produces is
   what the next stage needs, with explicit arithmetic  (7) Python code.
   Write sections (1)-(6) at the top of the file as a comment block.
2. Classify every variable transistor as MIRROR (W = Wref * Itarget/Iref *
   L/Lref, same L as its reference), MATCHED (copies its partner exactly) or
   INDEPENDENT (W = 2 Id L / (muCox Vov^2)). A mirror must use its reference's L.
3. Anti-circularity: compute every inter-stage node voltage from the driving
   stage's device parameters (e.g. V = VDD - |Vth,p| - Vov). Never assume a
   node voltage and then use it to justify itself.
4. Parasitics: large widths add gate and junction capacitance that lower GBW
   and phase margin. Prefer raising overdrive over widening devices when phase
   margin or GBW falls short.
5. Never write "self-adjusts" or "consistent by construction" without numbers.
6. Process: SkyWater Sky130, 1.8 V devices (sky130_fd_pr__nfet_01v8 /
   pfet_01v8). Allowed W 0.42-100 um, L 0.15-8 um per finger; use m > 1 for
   more width. Typical |Vth| is about 0.5-0.7 V (NMOS) and 0.9-1.0 V (PMOS)
   at L = 0.5 um, but trust calibrated values when given.
7. Do not change anything marked (fixed, printed). Size only VARIABLE items.
8. Bench: unity-gain feedback, DC loop through an ideal inductor, AC injected at
   the inverting input; gain = loop gain at 0.01 Hz, GBW = 0 dB crossing,
   PM = unwrapped phase margin, power = supply current x VDD.

## Previous sizing function (round 0)
```python
"""Round-0 sizing for the two-stage Miller op-amp of Fig. 4, ported to Sky130.

================================================================================
(1) DEVICE ROLES
================================================================================
I0   -- bias reference current, vdd into node vbias.  Sets the whole DC plan.
NM3  -- diode-connected nfet (Drain=Gate=vbias).  It is the MIRROR REFERENCE:
        vbias = Vth,n + Vovb, and every other nfet current source copies it.
NM2  -- tail current source of the input pair (Drain=C, Gate=vbias).  MIRROR of
        NM3, ratio Itail/Ibias.
NM0 / NM1 -- NMOS differential input pair, sources at the tail node C, drains at
        A and B.  NM0 gate = vin1 (the inverting input, per the prompt), NM1
        gate = vin2.  INDEPENDENT (NM0) + MATCHED (NM1 copies NM0).
PM2  -- diode-connected pfet load on node A (Drain=Gate=A).  It is the pfet
        mirror reference and, because node B settles at the same potential, it
        also *defines the gate drive of PM0*.  INDEPENDENT.
PM1  -- pfet load on node B, gate tied to A.  MATCHED to PM2 (same current Id1,
        same Vgs), so the pair is a 1:1 active mirror load and the first stage
        output is single-ended at node B.
PM0  -- second-stage common-source pfet, gate = B, drain = vout.  MIRROR of PM2
        (same Vgs from node B, same L), ratio Id2/Id1.
NM4  -- second-stage current-source load (Drain=vout, Gate=vbias).  MIRROR of
        NM3, ratio Id2/Ibias.  It sets the stage-2 operating current; PM0 is
        then sized so that its mirrored gate drive carries exactly that current.
C0   -- Miller compensation capacitor from B to vout.  There is no nulling
        resistor anywhere in this topology, so the right-half-plane zero at
        +gm2/C0 cannot be cancelled and is a permanent phase-margin cost.

Classification required by rule 2 (a mirror uses its reference's L):
  NM3 INDEPENDENT      W3  = 2*Ibias*Ln/(unCox*Vovb^2)
  NM2 MIRROR of NM3    W2  = W3 * Itail/Ibias ,  L = Ln
  NM4 MIRROR of NM3    W4  = W3 * Id2/Ibias   ,  L = Ln
  NM0 INDEPENDENT      W0  = 2*Id1*Ln/(unCox*Vov1^2)
  NM1 MATCHED to NM0   W1  = W0 , L = Ln
  PM2 INDEPENDENT      Wp2 = 2*Id1*Lp/(upCox*Vov2^2)
  PM1 MATCHED to PM2   Wp1 = Wp2 , L = Lp
  PM0 MIRROR of PM2    Wp0 = Wp2 * Id2/Id1 , L = Lp

================================================================================
(2) DEVICE CONSTRAINTS
================================================================================
Process: Sky130 1.8 V devices.  Round-0 estimates, stored by initial_params():
  nfet_01v8 : unCox = 130 uA/V^2, Vth,n  = 0.60 V, a_gm = 0.85
  pfet_01v8 : upCox =  40 uA/V^2, |Vth,p| = 0.95 V, a_gm = 0.85
  Channel-length modulation is taken as lam = K/L with K_n = 0.10 V^-1*um and
  K_p = 0.085 V^-1*um, i.e. an Early voltage near 10 V per micron of channel.
  With the lengths chosen below (Ln = 3.0 um, Lp = 0.5 um):
      lam_n = 0.03333 /V  (VA,n = 30.0 V)      lam_p = 0.17000 /V  (VA,p = 5.9 V)
  Those are the per-device lam values in initial_params(); because every mirror
  inherits its reference's L, one lam per polarity is self-consistent.
Geometry: 0.42 um <= w <= 100 um per finger, 0.15 um <= L <= 8 um.  Wide devices
  are split with m > 1 so that no single finger exceeds 60 um.
Square law used throughout:  Id = 0.5*muCox*(W/L)*Vov^2,  gm = a_gm*2*Id/Vov,
  gds = lam*Id.  a_gm = 0.85 de-rates gm for mobility degradation, so the
  transconductance efficiency actually used is gm/Id = 1.7/Vov.  The chosen
  overdrives (Vov1 = 0.1474 V, Vov2 = 0.150 V) give gm/Id = 11.5 and 11.3 /V --
  strong inversion, where the square law is still trustworthy.  Vov = 0.13 V
  (gm/Id = 13) is treated as the hard lower limit of model validity.

WHY THE LENGTHS ARE SO ASYMMETRIC (Ln = 3.0 um, Lp = 0.5 um).  This is the
central geometric trade of the round, and it is what buys the phase margin.
The counter-intuitive part is that a BETTER output resistance is not wanted
here.  The gain target is fixed, so by (E1) any lambda the lengths improve is
handed straight back as a *larger* Vov1 -- and by (E3) a larger Vov1 means a
larger Id1 at the gm1 the GBW demands, which by (E2) is subtracted from the
second stage, lowering gm2 and with it both p2 and z.  Short channels are
therefore what phase margin wants, and the binding limit is not the gain but
the Vov >= 0.13 V square-law validity floor of section 2.
  Lengthening the pfets is doubly bad, because Cgs,PM0 also grows as Lp^2:

   Lp[um]  lam_p   Vov1(E1)   Id1      Id2     gm2/gm1  Cgs,PM0   best PM
    0.35   0.243   0.0799   4.6 uA  117.0 uA   13.6     197 fF   58.79 deg
    0.40   0.212   0.1008   6.3 uA  113.6 uA   12.2     246 fF   56.99 deg
    0.45   0.189   0.1234   8.2 uA  109.8 uA   11.0     299 fF   54.52 deg
    0.50   0.170   0.1474  10.3 uA  105.7 uA   10.1     352 fF   51.60 deg <==
    0.55   0.155   0.1726  12.5 uA  101.3 uA    9.4     406 fF   48.29 deg
    0.60   0.142   0.1989  14.8 uA   96.7 uA    8.7     459 fF   44.65 deg
    0.70   0.121   0.2544  19.6 uA   86.9 uA    7.5     557 fF   36.51 deg
    0.80   0.106   0.3127  24.7 uA   76.8 uA    6.5     639 fF   27.35 deg
    1.00   0.085   0.4351  35.6 uA   55.1 uA    4.5     710 fF    6.89 deg
(each row re-optimised over C0, with gain/GBW/power held exactly on target)
PM0 must carry ~106 uA at a gate drive fixed by the PM2 diode, so it is wide
(Wp0 = 117.4 um) and its gate sits on node B, the high-impedance first-stage
output; Lp = 0.60 um already fails the 45 deg floor outright.  Going below
0.50 um keeps improving PM, but Vov1 from (E1) falls through the validity floor
(0.1234 V at Lp = 0.45 um, 0.1008 V at 0.40 um where gm/Id = 17).  Lp = 0.5 um
is therefore the shortest pfet length at which the input pair is still a
credible square-law device at Vov2 = 0.150 V.
  Ln acts the same way but far more weakly, because lam_n = 0.10/Ln is the
smaller half of s.  At Lp = 0.50 um and Vov2 = 0.150 V:
   Ln[um]   lam_n    Vov1(E1)    Id1      Id2     best PM
    2.0    0.0500    0.1259    9.1 uA  108.0 uA   52.51 deg  (Vov1 < 0.13)
    2.5    0.0400    0.1382    9.8 uA  106.6 uA   52.02 deg
    3.0    0.0333    0.1474   10.3 uA  105.7 uA   51.60 deg  <==
    4.0    0.0250    0.1602   10.9 uA  104.4 uA   50.87 deg
    6.0    0.0167    0.1749   11.7 uA  102.8 uA   49.68 deg
    8.0    0.0125    0.1829   12.2 uA  101.9 uA   48.65 deg
Ln = 3.0 um is kept as the point that leaves Vov1 = 0.1474 V a clear notch
inside the validity floor (gm/Id = 11.5) rather than scraping it; the 0.9 deg
available at Ln = 2.5 um is not worth spending the model margin on.
  THE MORE PHASE MARGIN IS AVAILABLE, AND IT WAS DECLINED.  Pushing both
overdrives down onto the 0.130 V floor reaches PM = 56.90 deg at Ln = 5.0 um,
Lp = 0.40 um (and 55.08 deg at Ln = 3.0 um, Lp = 0.45 um, Vov2 = 0.130 V).
That is 5.3 deg more paper margin bought by running BOTH devices at gm/Id = 13,
i.e. exactly where the square law behind every number in this file stops being
trustworthy -- so the gain and GBW predictions would degrade along with it.
For a round-0 estimate whose purpose is to generate informative calibration
data, 51.60 deg with both stages at gm/Id = 11.4 is the better trade.  If
simulation reports less margin than predicted, that corner is the remedy, and
section 4 prices it.

================================================================================
(3) SIGNAL PATH
================================================================================
AC injection at vin1 (the inverting input, gate of NM0):
  vin1 -> gm,NM0 steers tail current into node A; the PM2/PM1 mirror folds that
  half into node B, so the first-stage transconductance to the single-ended
  output B is Gm1 = gm,NM0 (full gm, not gm/2).
  Node B impedance:   Ro1 = 1/(gds,NM1 + gds,PM1) = 1/(Id1*(lam_n + lam_p)).
  B -> gate of PM0 -> common-source inversion into vout, Gm2 = gm,PM0.
  Node vout impedance: Ro2 = 1/(gds,PM0 + gds,NM4) = 1/(Id2*(lam_p + lam_n)).
  C0 bridges B and vout: pole splitting plus a feed-forward RHP zero.
Two gain stages, two split poles, one right-half-plane zero, plus ONE more term
that is not negligible here: half the differential signal reaches node B through
the PM2 -> PM1 mirror, so node A contributes a pole-zero doublet
      p3 = gm,PM2/C_A = 116.3 uS / 89.4 fF = 207.1 MHz,  zero at 2*p3,
only 7.35x the 28.16 MHz crossover, which costs 3.85 deg of phase (55.45 deg of
margin without it, 51.60 deg with it).  It is therefore carried in (E4).
The tail node C is a common-mode node that the differential half-circuit does
not see, and the source of PM0 is vdd, so no other pole is in the signal path.

================================================================================
(4) DESIGN EQUATIONS (symbolic)
================================================================================
Let Vov1 = overdrive of NM0/NM1, Vov2 = overdrive of PM2/PM1/PM0 (ONE symbol:
the topology forces those three equal, see section 6), Id1 = per-input-device
current, Id2 = second-stage current, Itail = 2*Id1, Ibias = I0,
s = lam_n + lam_p (the same sum appears at both high-impedance nodes).

  gm1 = a_gm*2*Id1/Vov1          gm2 = a_gm*2*Id2/Vov2
  Ro1 = 1/(Id1*s)                Ro2 = 1/(Id2*s)

  GAIN   Av = gm1*Ro1*gm2*Ro2 = (2*a_gm/(Vov1*s)) * (2*a_gm/(Vov2*s))
         The currents cancel: the DC gain depends ONLY on the two overdrives
         and the two lambdas, so with Vov2 chosen,
            Vov1 = 4*a_gm^2 / (Av_target * s^2 * Vov2)                    (E1)

  POWER  P = VDD*(Ibias + 2*Id1 + Id2)  =>  Id2 = Itot - Ibias - 2*Id1    (E2)
         with Itot = P_target/VDD.

  GBW    the loop response is
            A(s) = Av*(1 - s/z)*(1 + s/(2*p3)) / ((1+s/p1)(1+s/p2)(1+s/p3))
         and the unity-gain crossing w_c solves |A(w_c)| = 1.  To first order
         w_c = gm1/Cc_eff; requiring w_c = 2*pi*GBW_target fixes gm1, hence
         Id1 = gm1*Vov1/(2*a_gm), once C0 is chosen.                    (E3)
         The first-order value is 15.5 % optimistic here (gm1/Cc_eff would read
         32.51 MHz against a true crossing of 28.159 MHz, because the p2 and p3
         terms have already eaten gain by then), so the code solves |A| = 1
         exactly and rescales gm1 until the true crossing equals the target.
         Cc_eff = C0 + Cgd,PM0: the PM0 gate-drain overlap is electrically in
         parallel with the Miller capacitor (23.5 fF of the 579.5 fF here).

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
         gm2 grows: phase margin is bought with second-stage transconductance,
         which at a fixed Vov2 means second-stage current, and nothing else.

  COUNTING THE DEGREES OF FREEDOM.  (E1), (E2), (E3) are three equations in
  Vov1, Id1, Id2 once Vov2, Ibias, Ln, Lp are chosen, so the three toleranced
  targets are met identically and exactly ONE knob is left for the phase-margin
  constraint (E4): the compensation capacitor C0.  C0 is therefore swept over
  0.20-1.60 pF in 1 fF steps and the feasible point of maximum PM is taken.
  PM(C0) has an interior maximum: raising C0 raises gm1 = w_c*Cc_eff, which by
  (E3) raises Id1, which by (E2) steals current from the second stage and so
  lowers gm2, dragging both p2 and z down; lowering C0 instead makes
  p2 ~ gm2*Cc_eff/(C1*C2) fall in proportion to C0 while w_c = gm1/Cc_eff rises.

      C0 = 0.300 pF -> PM = 48.76    C0 = 0.600 pF -> PM = 51.54
      C0 = 0.400 pF -> PM = 50.74    C0 = 0.700 pF -> PM = 51.10
      C0 = 0.450 pF -> PM = 51.23    C0 = 0.800 pF -> PM = 50.30
      C0 = 0.500 pF -> PM = 51.50    C0 = 1.000 pF -> PM = 47.86
      C0 = 0.556 pF -> PM = 51.60 <= C0 = 1.200 pF -> PM = 44.53
                                     C0 = 1.500 pF -> PM = 38.03

  WHAT PAYS FOR THE 45 deg FLOOR.  The current split, overwhelmingly: 105.70 uA
  of the 138.22 uA budget is spent on the second stage so that
  gm2/gm1 = 1197.9/118.4 = 10.12, which places p2 at 1.755*w_c (29.68 deg of
  loss) and the RHP zero at 11.68*w_c (4.89 deg).  The first stage is left with
  2 x 10.26 uA, i.e. 15 % of the budget, and still has to make 35.08 dB out of
  it -- which is what sets the lengths in section 2.  The phase budget at
  crossover is
      89.98 (p1) + 29.68 (p2) + 4.89 (RHP zero) + 3.85 (mirror doublet)
      = 128.40 deg  ->  PM = 51.60 deg,  i.e. 6.6 deg above the floor.
  That guard band is real but thin against MODEL error rather than against the
  knobs: re-running the whole procedure with the parasitic constants scaled
  gives PM = 60.66 deg at 0.5x, 51.60 at 1x, 47.55 at 1.25x, 43.71 at 1.5x and
  36.55 at 2x, so a 50 % underestimate of Cox/Cov/Cjd would break the floor.
  The exposure is bounded, though: 352 fF of the 376 fF at node B is Cgs,PM0,
  and 329 fF of that is the (2/3)*W*L*Cox term, which rests on the one constant
  here that is NOT a guess (tox = 4.1 nm).  Only the C0 sweep is self-
  correcting (it re-centres between 0.43 and 0.66 pF across that range).  If
  simulation reports less margin than predicted, the ranked remedies are
    (i)  Lp 0.50 -> 0.45 um with Vov2 = 0.130 V: PM 55.08 deg nominal, 47.56 at
         1.5x parasitics, at the cost of gm/Id = 13.1 in the second stage;
    (ii) Ln 3.0 -> 5.0 um with Lp = 0.40 um, Vov2 = 0.130 V: PM 56.90 deg
         nominal, 49.71 at 1.5x, with both stages at gm/Id = 13.1 and
         W4 = 134 um.
  Neither is free, and section 2 explains why neither was taken in round 0.

  RESULTING DESIGN POINT (all numbers produced by the equations above):
    s = 0.20333 /V,  Vov2 = 0.1500 V (chosen),  Vov1 = 0.14736 V (E1)
    Ibias = 12.000 uA (chosen), Id1 = 10.262 uA, Itail = 20.525 uA,
    Id2 = 105.697 uA, total 138.222 uA
    gm1 = 118.4 uS, gm2 = 1197.9 uS, gm,PM2 = 116.3 uS
    Ro1 = 479.2 kOhm, Ro2 = 46.53 kOhm
    Av1 = 56.73 (35.08 dB), Av2 = 55.74 (34.92 dB), Av = 3162.3 (70.000 dB)
    C0 = 0.556 pF, Cc_eff = 0.5795 pF, C1 = 0.3756 pF, C2 = 2.1134 pF,
    C_A = 0.0894 pF
    p1 = 10.28 kHz, p2 = 49.41 MHz, z = 329.0 MHz, p3 = 207.1 MHz,
    f_c = 28.159 MHz,  PM = 51.60 deg,  power = 248.8 uW
    W3 = 8.862 um, W2 = 15.157 um, W0 = W1 = 21.811 um,
    W4 = 78.053 um (m = 2), Wp2 = Wp1 = 11.403 um, Wp0 = 117.442 um (m = 2)

================================================================================
(5) DC BIAS VERIFICATION -- every branch supports saturation, with numbers
================================================================================
Bias branch.  NM3 is diode connected, so it produces
  vbias = Vth,n + Vovb = 0.600 + 0.250 = 0.850 V, and Vds = Vgs > Vov always:
  saturated with 0.600 V to spare.  W3 = 2*12.00u*3.0/(130u*0.250^2) = 8.86 um.
NM2 (tail).  Gate = vbias = 0.850 V -> overdrive 0.250 V.
  W2 = W3*20.525/12.000 = 15.157 um.  Needs Vds,NM2 = V(C) >= 0.250 V.
NM0/NM1.  Vgs = Vth,n + Vov1 = 0.600 + 0.1474 = 0.7474 V, so
  V(C) = vcm - 0.7474 = 1.100 - 0.7474 = 0.3526 V.
  NM2 check: 0.3526 V >= 0.250 V, margin +102.6 mV.                    [OK]
  W0 = W1 = 2*10.262u*3.0/(130u*0.14736^2) = 21.811 um.
PM2/PM1.  PM2's drain and gate are node A and its source is vdd, so (rule 3:
  computed from the pfet's own parameters, never assumed)
  V(A) = VDD - |Vth,p| - Vov2 = 1.800 - 0.950 - 0.150 = 0.700 V.
  |Vds,PM2| = |Vgs,PM2| = 1.100 V >= Vov2 = 0.150 V: saturated, margin 0.950 V.
  PM1 has the same Vgs and the same 10.262 uA; |Vds,PM1| = 1.800 - V(B) =
  1.100 V >= 0.150 V, margin 0.950 V.                                  [OK]
  Wp2 = Wp1 = 2*10.262u*0.5/(40u*0.150^2) = 11.403 um.
NM0/NM1 saturation.  Vds,NM0 = V(A) - V(C) = 0.700 - 0.3526 = 0.3474 V against
  a required Vov1 = 0.1474 V -> margin +200.0 mV.  Node B is identical.  [OK]
PM0.  |Vgs,PM0| = VDD - V(B) = 1.800 - 0.700 = 1.100 V -> overdrive 0.150 V,
  the same as PM2, as the topology demands.
  Wp0 = Wp2*105.697/10.262 = 117.442 um, split m = 2 x 58.72 um.  In the
  unity-gain follower vout = vcm = 1.100 V, so |Vds,PM0| = 0.700 V >= 0.150 V,
  margin +550 mV.                                                      [OK]
NM4.  Gate = vbias = 0.850 V -> overdrive 0.250 V; Vds = vout = 1.100 V >=
  0.250 V, margin +850 mV.  W4 = W3*105.697/12.000 = 78.053 um,
  split m = 2 x 39.03 um.                                              [OK]
Input common-mode window.
  lower edge: V(C) >= Vovb          -> vcm >= 0.250 + 0.7474 = 0.997 V
  upper edge: Vds,NM0 >= Vov1       -> vcm <= V(A) - Vov1 + Vgs,NM0
                                            = 0.700 - 0.1474 + 0.7474 = 1.300 V
  output side (vout = vcm in the follower) is looser:
                                       0.250 V <= vout <= 1.800 - 0.150 = 1.650 V
  vcm = 1.100 V sits 103 mV above the lower edge and 200 mV below the upper one,
  i.e. essentially mid-window.                                          [OK]

================================================================================
(6) DC OPERATING-POINT CONSISTENCY -- what each stage produces versus what the
    next stage needs (explicit arithmetic; nothing is asserted to "self-adjust")
================================================================================
(a) Bias branch -> nfet current sources.  NM3 PRODUCES vbias = 0.850 V.  What
    NM2 NEEDS to deliver Itail = 20.525 uA at that gate voltage is
    W2/L = 15.157/3.0 = 5.0523:
      Id = 0.5*130u*5.0523*0.250^2 = 20.525 uA at Vgs = 0.850 V.        match
    What NM4 NEEDS to deliver 105.697 uA is W4/L = 78.053/3.0 = 26.0178:
      Id = 0.5*130u*26.0178*0.250^2 = 105.697 uA at Vgs = 0.850 V.      match
    (Both ratios are W3/L = 2.9538 scaled by 1.7104 = Itail/Ibias and by
     8.8081 = Id2/Ibias, which is the mirror rule of section 1.)
(b) First stage -> its own load.  The tail delivers 20.525 uA, so NM0 and NM1
    each carry 10.262 uA and therefore PM2 and PM1 each carry 10.262 uA.  PM2
    is diode connected and reports that current back as a voltage:
      V(A) = VDD - |Vth,p| - sqrt(2*Id1*Lp/(upCox*Wp2))
           = 1.800 - 0.950 - sqrt(2*10.262u*0.5u/(40u*11.403u)) = 0.700 V.
    PM1 sees that same Vgs and is saturated, so it sources 10.262 uA into node B
    while NM1 sinks 10.262 uA out of it: the mirror load is balanced at
    V(B) = V(A) = 0.700 V with zero net current into node B.
(c) First stage -> second stage (the critical interface).  The voltage the first
    stage PRODUCES at B is 0.700 V.  The voltage PM0 NEEDS at its gate in order
    to carry NM4's 105.697 uA is
      V(B),req = VDD - |Vth,p| - sqrt(2*Id2*Lp/(upCox*Wp0))
               = 1.800 - 0.950 - sqrt(2*105.697u*0.5u/(40u*117.442u))
               = 1.800 - 0.950 - 0.15000 = 0.70000 V.
    Produced 0.700 V = needed 0.70000 V.  This is not luck: PM0 is a MIRROR of
    PM2 with Wp0/Wp2 = 117.442/11.403 = 10.2995 = Id2/Id1 = 105.697/10.262 at
    the same L, and equal width-per-ampere at equal L means equal Vgs.
    Checking the two output branch currents at that node voltage:
      Id,PM0 = 0.5*40u*(117.442/0.5)*0.150^2 = 105.697 uA
      Id,NM4 = 0.5*130u*(78.053/3.0)*0.250^2 = 105.697 uA  -> net 0.000 uA.
(d) Second stage -> output and back through the feedback.  In the unity-gain
    follower vout = vcm = 1.100 V; both output devices are saturated there
    (section 5), and PM0's gate at 0.700 V is 0.400 V BELOW its drain, so PM0
    is a saturated common-source amplifier and not a diode.  The feedback pins
    V(B) at the 0.700 V computed in (c), because that is the only gate voltage
    at which PM0's current equals NM4's.  Quantitatively, a 10 % error in NM4's
    current would move node B by only
      dV(B) = 0.5*Vov2*(dI/I) = 0.5*0.150*0.10 = 7.5 mV
    and the resulting output offset, divided by the 3162 of loop gain, is
      7.5 mV * Av2/Av = 7.5 mV * 55.74/3162 = 132 uV.
(e) Power audit.  Ibias + Itail + Id2 = 12.000 + 20.525 + 105.697
    = 138.222 uA; times VDD = 1.8 V this is 248.8 uW, the target exactly.
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
LN = 3.0e-6         # all nfet channel lengths (the NM3 mirror family shares it)
LP = 0.5e-6         # all pfet channel lengths (PM0 mirrors PM2, so same L)
VOV2 = 0.150        # overdrive of PM2/PM1/PM0 -- forced common by the topology
VOVB = 0.250        # overdrive of the nfet mirror family NM2/NM3/NM4
IBIAS = 12.0e-6     # I0 reference current
VCM = 1.100         # input common mode, mid-window (section 5)
VOV1_MIN = 0.13     # square-law validity floor for the input pair (section 2)
PM_GUARD = 5.0      # deg of guard demanded above the spec's phase-margin floor
CC_MIN, CC_MAX, CC_STEP = 0.20e-12, 1.60e-12, 1.0e-15
W_FINGER_MAX = 60e-6
W_MIN, W_MAX = 0.42e-6, 100e-6
L_MIN, L_MAX = 0.15e-6, 8.0e-6


def initial_params():
    """Round-0 process estimates for Sky130 1.8 V devices.

    lam is quoted at the length each device actually uses: lam = K/L with
    K_n = 0.10 V^-1*um (L = 3.0 um -> 0.03333) and K_p = 0.085 V^-1*um
    (L = 0.5 um -> 0.17000).  a_gm de-rates the square-law gm for mobility
    degradation, so gm/Id = 2*a_gm/Vov.
    """
    nfet = {"type": "NMOS", "muCox": 130e-6, "a_gm": 0.85,
            "lam": 0.10 / (LN * 1e6), "vth": 0.60}
    pfet = {"type": "PMOS", "muCox": 40e-6, "a_gm": 0.85,
            "lam": 0.085 / (LP * 1e6), "vth": 0.95}
    out = {}
    for d in ("NM0", "NM1", "NM2", "NM3", "NM4"):
        out[d] = dict(nfet)
    for d in ("PM0", "PM1", "PM2"):
        out[d] = dict(pfet)
    return out


# --------------------------------------------------------------------- helpers
def _finger(w_total):
    """Split a total width into m legal fingers (section 2 geometry limits)."""
    m = max(1, int(math.ceil(w_total / W_FINGER_MAX)))
    w = w_total / m
    while w < W_MIN and m > 1:              # never go below the minimum finger
        m -= 1
        w = w_total / m
    w = max(W_MIN, min(W_MAX, round(w / 5e-9) * 5e-9))   # 5 nm layout grid
    return w, m


def _ac(gm1, gm2, ro1, ro2, cc_eff, c1, c2, p3):
    """Loop response -> (Adc, w_c, PM, p1, p2, z, p3).

        A(s) = Adc * (1 - s/z) * (1 + s/(2*p3)) / ((1+s/p1)(1+s/p2)(1+s/p3))

    p1, p2 are the split Miller poles, z = +gm2/Cc_eff is the RHP zero, and
    p3 with its zero at 2*p3 is the mirror doublet of PM2/PM1 at node A (half
    the differential signal takes the mirror path, so the pole is accompanied
    by a zero one octave above it).  |A(w_c)| = 1 is solved by geometric
    bisection, which is exact to machine precision over the bracket used.
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
    for _ in range(60):
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


def _operating_point(gm1, vov1, cc, isig, pr):
    """Everything downstream of a trial (gm1, C0): currents, widths, caps, AC."""
    un, up = pr["un"], pr["up"]
    a = pr["a_gm"]
    s = pr["s"]
    id1 = gm1 * vov1 / (2.0 * a)                        # gm = a_gm*2*Id/Vov
    id2 = isig - 2.0 * id1                              # (E2)
    if id2 <= 15e-6 or id1 <= 1e-6:
        return None
    gm2 = 2.0 * a * id2 / VOV2

    w_nm0 = 2.0 * id1 * LN / (un * vov1 ** 2)           # INDEPENDENT
    w_pm2 = 2.0 * id1 * LP / (up * VOV2 ** 2)           # INDEPENDENT
    w_pm0 = w_pm2 * id2 / id1                           # MIRROR of PM2
    w_nm3 = 2.0 * IBIAS * LN / (un * VOVB ** 2)         # INDEPENDENT (reference)
    w_nm2 = w_nm3 * (2.0 * id1) / IBIAS                 # MIRROR of NM3
    w_nm4 = w_nm3 * id2 / IBIAS                         # MIRROR of NM3

    cgs_pm0 = (2.0 / 3.0) * w_pm0 * LP * COX + COV * w_pm0
    cgs_pm2 = (2.0 / 3.0) * w_pm2 * LP * COX + COV * w_pm2
    c1 = cgs_pm0 + (COV + CJD) * (w_pm2 + w_nm0)        # node B
    c2 = pr["cl"] + CJD * w_pm0 + (CJD + COV) * w_nm4   # node vout
    cc_eff = cc + COV * w_pm0                           # C0 in parallel Cgd,PM0
    # node A: both pfet gates, PM2's own junction, NM0's drain.  PM2 is diode
    # connected so the resistance there is 1/gm,PM2 and the mirror doublet is
    # p3 = gm,PM2/C_A with its zero at 2*p3.
    c_a = 2.0 * cgs_pm2 + CJD * w_pm2 + (CJD + COV) * w_nm0
    gm_pm2 = 2.0 * a * id1 / VOV2
    p3 = gm_pm2 / c_a

    ro1 = 1.0 / (id1 * s)
    ro2 = 1.0 / (id2 * s)
    res = _ac(gm1, gm2, ro1, ro2, cc_eff, c1, c2, p3)
    if res is None:
        return None
    adc, wc, pm, p1, p2, z, p3 = res
    return {"id1": id1, "id2": id2, "gm1": gm1, "gm2": gm2, "ro1": ro1,
            "ro2": ro2, "c1": c1, "c2": c2, "c_a": c_a, "cc": cc,
            "cc_eff": cc_eff, "adc": adc, "wc": wc, "pm": pm, "p1": p1,
            "p2": p2, "z": z, "p3": p3, "gm_pm2": gm_pm2,
            "w_nm0": w_nm0, "w_nm2": w_nm2, "w_nm3": w_nm3, "w_nm4": w_nm4,
            "w_pm0": w_pm0, "w_pm2": w_pm2, "vov1": vov1}


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
    if max(op["w_nm0"], op["w_nm2"], op["w_nm3"], op["w_nm4"],
           op["w_pm0"], op["w_pm2"]) > 8.0 * W_FINGER_MAX:
        return None
    return op


def compute_sizing(spec, params):
    tgt = spec["targets"]
    cond = spec["conditions"]
    vdd = cond["vdd"]
    cl = cond["cl"]
    av_t = 10.0 ** (tgt["gain_dB"] / 20.0)
    wu_t = 2.0 * math.pi * tgt["gbw_Hz"]
    itot = tgt["power_W"] / vdd
    pm_floor = spec.get("constraints", {}).get("pm_deg", {}).get("min", 45.0)

    p_n = params["NM0"]
    p_p = params["PM0"]
    a_gm = p_n["a_gm"]
    s = p_n["lam"] + p_p["lam"]             # lam_n + lam_p, at both nodes

    # (E1) the gain fixes the PRODUCT of the two overdrives; Vov2 is the design
    # choice, so Vov1 follows.  Nothing circular: s comes from the device
    # parameters, not from an assumed node voltage.
    vov1 = 4.0 * a_gm ** 2 / (av_t * s * s * VOV2)
    if vov1 < VOV1_MIN:
        raise RuntimeError("Vov1 = %.4f V is below the square-law floor; "
                           "shorten Ln or raise Vov2" % vov1)

    pr = {"un": p_n["muCox"], "up": p_p["muCox"], "a_gm": a_gm, "s": s,
          "cl": cl, "wu": wu_t}
    isig = itot - IBIAS                     # (E2) current left for the stages

    # (E4) C0 is the one remaining knob; PM(C0) has an interior maximum.
    best = None
    n = int(round((CC_MAX - CC_MIN) / CC_STEP))
    for i in range(n + 1):
        op = _solve_for_cc(CC_MIN + i * CC_STEP, vov1, isig, pr)
        if op is None:
            continue
        if best is None or op["pm"] > best["pm"]:
            best = op
    if best is None or best["pm"] < pm_floor + PM_GUARD:
        raise RuntimeError("no sizing meets the %.1f deg phase-margin floor"
                           % pm_floor)

    w = {k: _finger(best["w_" + k.lower()]) for k in
         ("NM0", "NM2", "NM3", "NM4", "PM0", "PM2")}
    w["NM1"] = w["NM0"]                     # MATCHED pair
    w["PM1"] = w["PM2"]                     # MATCHED load

    sizes = {}
    for dev in ("NM0", "NM1", "NM2", "NM3", "NM4"):
        sizes[dev] = {"w": w[dev][0], "l": LN, "m": w[dev][1]}
    for dev in ("PM0", "PM1", "PM2"):
        sizes[dev] = {"w": w[dev][0], "l": LP, "m": w[dev][1]}
    for dev, g in sizes.items():
        assert W_MIN - 1e-12 <= g["w"] <= W_MAX, dev
        assert L_MIN <= g["l"] <= L_MAX, dev

    power = vdd * (IBIAS + 2.0 * best["id1"] + best["id2"])
    return {
        "sizes": sizes,
        "biases": {},
        "currents": {"I0": IBIAS},
        "caps": {"C0": best["cc"]},
        "vcm": VCM,
        "predicted": {
            "gain_dB": 20.0 * math.log10(best["adc"]),
            "gbw_Hz": best["wc"] / (2.0 * math.pi),
            "pm_deg": best["pm"],
            "power_W": power,
        },
    }


if __name__ == "__main__":  # local check of the numbers quoted in sections 4-6
    import json
    _spec = {
        "targets": {"gain_dB": 70.0, "gbw_Hz": 28159000.0, "power_W": 0.0002488},
        "conditions": {"vdd": 1.8, "cl": 2e-12, "vcm": None},
        "constraints": {"pm_deg": {"min": 45.0}},
    }
    print(json.dumps(compute_sizing(_spec, initial_params()), indent=1))

```

## Calibration (one DC operating point, this round's sizing)

| Dev | Type | W/L (um) x m | Id (uA) | Vov (mV) | Vds (mV) | gm (uS) | Region | muCox (uA/V2) | a_gm | lambda (1/V) | Vth (mV) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| NM0 | NMOS | 21.8/3x1 | 10.4 | 95 | 356 | 166.7 | SAT | 317.3 | 0.762 | 0.07618 | 625 |
| NM1 | NMOS | 21.8/3x1 | 10.4 | 95 | 346 | 166.8 | SAT | 316.8 | 0.763 | 0.07855 | 625 |
| NM2 | NMOS | 15.2/3x1 | 20.8 | 182 | 380 | 221.7 | SAT | 247.7 | 0.973 | 0.07266 | 536 |
| NM3 | NMOS | 8.86/3x1 | 12 | 180 | 718 | 130.2 | SAT | 252.1 | 0.974 | 0.04522 | 538 |
| NM4 | NMOS | 39/3x2 | 113 | 184 | 1100 | 1179 | SAT | 254.8 | 0.964 | 0.03124 | 534 |
| PM0 | PMOS | 58.7/0.5x2 | 113 | 77 | 700 | 1489 | SAT | 160.8 | 0.510 | 0.111 | 997 |
| PM1 | PMOS | 11.4/0.5x1 | 10.4 | 72 | 1075 | 139.8 | SAT | 176.4 | 0.484 | 0.09123 | 992 |
| PM2 | PMOS | 11.4/0.5x1 | 10.4 | 72 | 1064 | 139.7 | SAT | 176.4 | 0.483 | 0.09162 | 992 |

All transistors saturated.

## Predicted vs measured (fitted targets)

| Metric | Target | Predicted | Measured | Prediction error |
|---|---|---|---|---|
| gain_dB | 70.0 | 70.0 | 78.8491919 | -8.85 dB |
| gbw_Hz | 28159000.0 | 28158999.999726918 | 40145969.47228519 | -29.9 % |
| power_W | 0.0002488 | 0.0002488 | 0.0002619216 | -5.0 % |

Follower settles at vcm: True; saturated 8/8.

## History (all rounds so far)

| Round | gain_dB | gbw_Hz | power_W | saturated |
|---|---|---|---|---|
| 0 | 78.8491919 | 40145969.47228519 | 0.0002619216 | 8/8 |

## This round
Do NOT re-estimate device parameters: compute_sizing() will be called with the
calibrated values above. Update compute_sizing() using the margin rules:
- linear metric (GBW, power) over-predicted by X%: design for (1 + X/100) x target
- gain over-predicted by Y dB: design for target + Y dB
- phase margin over-predicted by Z deg: design for target + Z deg
- if your predicted PM is catastrophically low but the measured PM passes, your PM
  equation is wrong: trust the measurement and do not distort sizing to fix it.
- any device flagged TRIODE is a bias-point failure: fix its headroom first.

## Output contract

Write ONE Python file, `cases/opamp3/sizing_published_power_pmfloor/twostage/round_1/compute_sizing.py`, standard library only (math allowed), with:

```python
def initial_params():          # required in round 0 only; ignored afterwards
    return {"<device id>": {"type": "NMOS"|"PMOS", "muCox": A_per_V2, "a_gm": float,
                              "lam": per_V, "vth": V}, ...}   # every MOS device

def compute_sizing(spec, params):
    # spec: the dict under "## Specification" below; params: per-device dict as above
    return {
      "sizes":    {"<device id>": {"w": metres, "l": metres, "m": int}, ...},   # VARIABLE MOS only
      "biases":   {"<source id>": volts, ...},     # VARIABLE voltage sources only
      "currents": {"<source id>": amps, ...},      # VARIABLE current sources only
      "caps":     {"<cap id>": farads, ...},       # VARIABLE capacitors only
      "vcm": volts,                                # input common mode (if variable)
      "predicted": {"gain_dB": .., "gbw_Hz": .., "pm_deg": .., "power_W": ..},
    }
```

Check that it executes before you finish:
`.venv/bin/python pipeline/sizing.py dry cases/opamp3/sizing_published_power_pmfloor/twostage 1` must print OK. That command
does not simulate; do not run any simulation yourself.
