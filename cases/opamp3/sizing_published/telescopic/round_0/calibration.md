## Calibration (one DC operating point, this round's sizing)

| Dev | Type | W/L (um) x m | Id (uA) | Vov (mV) | Vds (mV) | gm (uS) | Region | muCox (uA/V2) | a_gm | lambda (1/V) | Vth (mV) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| NM0 | NMOS | 6/0.5x1 | 0.00169 | -304 | 648 | 0.05007 | OFF | 0 | - | 0.2335 | 838 |
| NM1 | NMOS | 0.461/0.5x1 | 0.00168 | -212 | 465 | 0.04477 | OFF | 0 | - | 0.2479 | 754 |
| NM2 | NMOS | 3/0.5x1 | 6.32 | 66 | 687 | 102.8 | SAT | 477.4 | 0.540 | 0.1241 | 632 |
| NM3 | NMOS | 6/0.5x1 | 6.31 | 12 | 827 | 123.9 | SAT | 7331 | 0.118 | 0.1483 | 795 |
| NM4 | NMOS | 0.461/0.5x1 | 6.31 | 264 | 192 | 35.48 | TRIODE | 196.9 | 0.741 | 2.313 | 755 |
| PM0 | PMOS | 7/0.5x1 | 0.00169 | 103 | 0 | 0.0126 | TRIODE | 0.02262 | 0.385 | 6.824e+04 | 993 |
| PM1 | PMOS | 7/0.5x1 | 0.00169 | 449 | 0 | 0.003614 | TRIODE | 0.001199 | 0.480 | 2.682e+05 | 993 |
| PM2 | PMOS | 7/0.5x1 | 6.31 | 104 | 76 | 58.9 | TRIODE | 84.17 | 0.483 | 8.309 | 993 |
| PM3 | PMOS | 7/0.5x1 | 6.31 | 353 | 18 | 17.87 | TRIODE | 7.219 | 0.500 | 53.69 | 1012 |

WARNING: NM0 in OFF (Vds=648 mV, Vov=-304 mV)
WARNING: NM1 in OFF (Vds=465 mV, Vov=-212 mV)
WARNING: NM4 in TRIODE (Vds=192 mV, Vov=264 mV)
WARNING: PM0 in TRIODE (Vds=0 mV, Vov=103 mV)
WARNING: PM1 in TRIODE (Vds=0 mV, Vov=449 mV)
WARNING: PM2 in TRIODE (Vds=76 mV, Vov=104 mV)
WARNING: PM3 in TRIODE (Vds=18 mV, Vov=353 mV)

## Predicted vs measured (fitted targets)

| Metric | Target | Predicted | Measured | Prediction error |
|---|---|---|---|---|
| gain_dB | 52.0 | 52.0 | -38.2663059 | +90.27 dB |

Follower settles at vcm: False; saturated 2/9.

## History (all rounds so far)

| Round | gain_dB | saturated |
|---|---|---|
| 0 | -38.2663059 | 2/9 |