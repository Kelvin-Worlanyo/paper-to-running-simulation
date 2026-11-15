## Calibration (one DC operating point, this round's sizing)

| Dev | Type | W/L (um) x m | Id (uA) | Vov (mV) | Vds (mV) | gm (uS) | Region | muCox (uA/V2) | a_gm | lambda (1/V) | Vth (mV) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| NM0 | NMOS | 6/0.5x1 | 13 | 57 | 384 | 217.1 | SAT | 659.5 | 0.478 | 0.2146 | 754 |
| NM1 | NMOS | 0.77/0.5x1 | 13 | 263 | 339 | 86.39 | SAT | 245.8 | 0.869 | 0.3743 | 690 |
| NM2 | NMOS | 3/0.5x1 | 26.1 | 182 | 289 | 247.2 | SAT | 261.9 | 0.863 | 0.341 | 633 |
| NM3 | NMOS | 6/0.5x1 | 13 | 55 | 611 | 218.4 | SAT | 710.5 | 0.463 | 0.1526 | 754 |
| NM4 | NMOS | 0.77/0.5x1 | 13 | 262 | 341 | 86.45 | SAT | 246 | 0.870 | 0.3679 | 690 |
| PM0 | PMOS | 7/0.5x1 | 13 | 137 | 270 | 136.2 | SAT | 98.74 | 0.717 | 0.2732 | 992 |
| PM1 | PMOS | 7/0.5x1 | 13 | 133 | 518 | 140.6 | SAT | 105 | 0.718 | 0.1286 | 1057 |
| PM2 | PMOS | 7/0.5x1 | 13 | 137 | 267 | 136.1 | SAT | 98.68 | 0.717 | 0.2793 | 992 |
| PM3 | PMOS | 7/0.5x1 | 13 | 136 | 292 | 138.1 | SAT | 100.8 | 0.720 | 0.2376 | 1057 |

All transistors saturated.

## Predicted vs measured (fitted targets)

| Metric | Target | Predicted | Measured | Prediction error |
|---|---|---|---|---|
| gain_dB | 52.0 | 53.08311042856478 | 51.1447044 | +1.94 dB |

Follower settles at vcm: True; saturated 9/9.

## History (all rounds so far)

| Round | gain_dB | saturated |
|---|---|---|
| 0 | -38.2663059 | 2/9 |
| 1 | 26.8157731 | 6/9 |
| 2 | 63.020474 | 7/9 |
| 3 | 40.1024648 | 7/9 |
| 4 | 39.9964443 | 8/9 |
| 5 | 51.1447044 | 9/9 |