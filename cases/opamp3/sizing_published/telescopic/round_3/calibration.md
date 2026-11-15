## Calibration (one DC operating point, this round's sizing)

| Dev | Type | W/L (um) x m | Id (uA) | Vov (mV) | Vds (mV) | gm (uS) | Region | muCox (uA/V2) | a_gm | lambda (1/V) | Vth (mV) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| NM0 | NMOS | 6/0.5x1 | 13.1 | 501 | 8 | 24.4 | TRIODE | 8.688 | 0.467 | 117.1 | 733 |
| NM1 | NMOS | 0.77/0.5x1 | 13.1 | 279 | 214 | 71.96 | TRIODE | 217.4 | 0.769 | 1.791 | 692 |
| NM2 | NMOS | 3/0.5x1 | 26.1 | 182 | 295 | 247.9 | SAT | 262.4 | 0.864 | 0.3256 | 633 |
| NM3 | NMOS | 6/0.5x1 | 13.1 | 56 | 351 | 218.1 | SAT | 705 | 0.464 | 0.2352 | 798 |
| NM4 | NMOS | 0.77/0.5x1 | 13.1 | 256 | 594 | 90.76 | SAT | 259.1 | 0.889 | 0.1349 | 690 |
| PM0 | PMOS | 7/0.5x1 | 13.1 | 138 | 274 | 136.6 | SAT | 98.76 | 0.718 | 0.2655 | 992 |
| PM1 | PMOS | 7/0.5x1 | 13.1 | 130 | 1008 | 142.8 | SAT | 109.7 | 0.712 | 0.08576 | 1056 |
| PM2 | PMOS | 7/0.5x1 | 13.1 | 138 | 267 | 136.2 | SAT | 98.62 | 0.717 | 0.2791 | 992 |
| PM3 | PMOS | 7/0.5x1 | 13.1 | 136 | 292 | 138.2 | SAT | 100.8 | 0.720 | 0.2377 | 1057 |

WARNING: NM0 in TRIODE (Vds=8 mV, Vov=501 mV)
WARNING: NM1 in TRIODE (Vds=214 mV, Vov=279 mV)

## Predicted vs measured (fitted targets)

| Metric | Target | Predicted | Measured | Prediction error |
|---|---|---|---|---|
| gain_dB | 52.0 | 52.027963123134484 | 40.1024648 | +11.93 dB |

Follower settles at vcm: True; saturated 7/9.

## History (all rounds so far)

| Round | gain_dB | saturated |
|---|---|---|
| 0 | -38.2663059 | 2/9 |
| 1 | 26.8157731 | 6/9 |
| 2 | 63.020474 | 7/9 |
| 3 | 40.1024648 | 7/9 |