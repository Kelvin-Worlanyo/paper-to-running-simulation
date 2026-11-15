## Calibration (one DC operating point, this round's sizing)

| Dev | Type | W/L (um) x m | Id (uA) | Vov (mV) | Vds (mV) | gm (uS) | Region | muCox (uA/V2) | a_gm | lambda (1/V) | Vth (mV) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| NM0 | NMOS | 6/0.5x1 | 12.6 | 51 | 873 | 214.4 | SAT | 808.4 | 0.433 | 0.1278 | 765 |
| NM1 | NMOS | 4.31/0.5x1 | 12.6 | 80 | 410 | 189.8 | SAT | 456.1 | 0.602 | 0.1864 | 694 |
| NM2 | NMOS | 3/0.5x1 | 26 | 182 | 291 | 247.1 | SAT | 262.2 | 0.864 | 0.3359 | 633 |
| NM3 | NMOS | 6/0.5x1 | 13.4 | 58 | 376 | 221.7 | SAT | 652.5 | 0.484 | 0.2194 | 765 |
| NM4 | NMOS | 4.31/0.5x1 | 13.4 | 84 | 403 | 197.6 | SAT | 438.7 | 0.621 | 0.189 | 694 |
| PM0 | PMOS | 7/0.5x1 | 12.6 | 141 | 161 | 120.7 | TRIODE | 90.94 | 0.673 | 1.613 | 992 |
| PM1 | PMOS | 7/0.5x1 | 12.6 | 220 | 66 | 63.36 | TRIODE | 37.32 | 0.551 | 12.63 | 1033 |
| PM2 | PMOS | 7/0.5x1 | 13.4 | 141 | 230 | 136.6 | SAT | 96.09 | 0.719 | 0.4244 | 992 |
| PM3 | PMOS | 7/0.5x1 | 13.4 | 136 | 501 | 142.7 | SAT | 103.5 | 0.724 | 0.1316 | 1047 |

WARNING: PM0 in TRIODE (Vds=161 mV, Vov=141 mV)
WARNING: PM1 in TRIODE (Vds=66 mV, Vov=220 mV)

## Predicted vs measured (fitted targets)

| Metric | Target | Predicted | Measured | Prediction error |
|---|---|---|---|---|
| gain_dB | 52.0 | 51.99658728801193 | 63.020474 | -11.02 dB |

Follower settles at vcm: True; saturated 7/9.

## History (all rounds so far)

| Round | gain_dB | saturated |
|---|---|---|
| 0 | -38.2663059 | 2/9 |
| 1 | 26.8157731 | 6/9 |
| 2 | 63.020474 | 7/9 |