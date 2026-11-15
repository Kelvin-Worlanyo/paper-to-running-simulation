## Calibration (one DC operating point, this round's sizing)

| Dev | Type | W/L (um) x m | Id (uA) | Vov (mV) | Vds (mV) | gm (uS) | Region | muCox (uA/V2) | a_gm | lambda (1/V) | Vth (mV) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| NM0 | NMOS | 6/0.5x1 | 13.1 | 147 | 31 | 94.94 | TRIODE | 101.1 | 0.533 | 28.22 | 741 |
| NM1 | NMOS | 0.77/0.5x1 | 13.1 | 269 | 262 | 80.56 | SAT | 234.1 | 0.830 | 0.8717 | 690 |
| NM2 | NMOS | 3/0.5x1 | 26.1 | 182 | 290 | 247.3 | SAT | 262 | 0.864 | 0.3376 | 633 |
| NM3 | NMOS | 6/0.5x1 | 13 | 55 | 613 | 218.4 | SAT | 710.9 | 0.463 | 0.1524 | 754 |
| NM4 | NMOS | 0.77/0.5x1 | 13 | 262 | 340 | 86.39 | SAT | 246 | 0.869 | 0.3717 | 690 |
| PM0 | PMOS | 7/0.5x1 | 13.1 | 137 | 273 | 136.4 | SAT | 98.81 | 0.718 | 0.2665 | 992 |
| PM1 | PMOS | 7/0.5x1 | 13.1 | 131 | 944 | 142.5 | SAT | 109.3 | 0.713 | 0.08879 | 1056 |
| PM2 | PMOS | 7/0.5x1 | 13 | 137 | 267 | 136.1 | SAT | 98.68 | 0.717 | 0.2793 | 992 |
| PM3 | PMOS | 7/0.5x1 | 13 | 136 | 290 | 138 | SAT | 100.8 | 0.720 | 0.2399 | 1057 |

WARNING: NM0 in TRIODE (Vds=31 mV, Vov=147 mV)

## Predicted vs measured (fitted targets)

| Metric | Target | Predicted | Measured | Prediction error |
|---|---|---|---|---|
| gain_dB | 52.0 | 53.16788854323322 | 39.9964443 | +13.17 dB |

Follower settles at vcm: True; saturated 8/9.

## History (all rounds so far)

| Round | gain_dB | saturated |
|---|---|---|
| 0 | -38.2663059 | 2/9 |
| 1 | 26.8157731 | 6/9 |
| 2 | 63.020474 | 7/9 |
| 3 | 40.1024648 | 7/9 |
| 4 | 39.9964443 | 8/9 |