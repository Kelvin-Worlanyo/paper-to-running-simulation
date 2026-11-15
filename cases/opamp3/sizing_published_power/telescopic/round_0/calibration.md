## Calibration (one DC operating point, this round's sizing)

| Dev | Type | W/L (um) x m | Id (uA) | Vov (mV) | Vds (mV) | gm (uS) | Region | muCox (uA/V2) | a_gm | lambda (1/V) | Vth (mV) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| NM0 | NMOS | 6/0.5x1 | 31.9 | 635 | 17 | 45.17 | TRIODE | 13.15 | 0.450 | 58.97 | 686 |
| NM1 | NMOS | 3.82/0.5x1 | 31.9 | 311 | 58 | 113.9 | TRIODE | 86.16 | 0.556 | 15.06 | 679 |
| NM2 | NMOS | 3/0.5x1 | 63.6 | 323 | 209 | 294.5 | TRIODE | 202.6 | 0.749 | 2.125 | 633 |
| NM3 | NMOS | 6/0.5x1 | 31.7 | 118 | 349 | 393.8 | SAT | 376.5 | 0.736 | 0.245 | 767 |
| NM4 | NMOS | 3.82/0.5x1 | 31.7 | 165 | 494 | 320.9 | SAT | 303.2 | 0.838 | 0.1492 | 678 |
| PM0 | PMOS | 7/0.5x1 | 31.9 | 244 | 257 | 212.8 | SAT | 76.63 | 0.814 | 0.7353 | 992 |
| PM1 | PMOS | 7/0.5x1 | 31.9 | 227 | 1258 | 239.8 | SAT | 88.08 | 0.856 | 0.06602 | 1051 |
| PM2 | PMOS | 7/0.5x1 | 31.7 | 244 | 250 | 210 | SAT | 76.24 | 0.807 | 0.8229 | 992 |
| PM3 | PMOS | 7/0.5x1 | 31.7 | 233 | 497 | 232.2 | SAT | 83.26 | 0.854 | 0.138 | 1052 |

WARNING: NM0 in TRIODE (Vds=17 mV, Vov=635 mV)
WARNING: NM1 in TRIODE (Vds=58 mV, Vov=311 mV)
WARNING: NM2 in TRIODE (Vds=209 mV, Vov=323 mV)

## Predicted vs measured (fitted targets)

| Metric | Target | Predicted | Measured | Prediction error |
|---|---|---|---|---|
| gain_dB | 52.0 | 52.47780542388011 | 46.6887981 | +5.79 dB |
| power_W | 8.57568e-05 | 8.232652799999962e-05 | 0.00011441124 | -28.0 % |

Follower settles at vcm: False; saturated 6/9.

## History (all rounds so far)

| Round | gain_dB | power_W | saturated |
|---|---|---|---|
| 0 | 46.6887981 | 0.00011441124 | 6/9 |