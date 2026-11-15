## Calibration (one DC operating point, this round's sizing)

| Dev | Type | W/L (um) x m | Id (uA) | Vov (mV) | Vds (mV) | gm (uS) | Region | muCox (uA/V2) | a_gm | lambda (1/V) | Vth (mV) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| NM0 | NMOS | 15.5/2x1 | 23 | 149 | 225 | 280.3 | SAT | 267.1 | 0.908 | 0.3351 | 623 |
| NM1 | NMOS | 15.5/2x1 | 23 | 150 | 191 | 274.3 | SAT | 262.4 | 0.896 | 0.6304 | 623 |
| NM2 | NMOS | 13.1/1.5x1 | 46 | 204 | 329 | 434.8 | SAT | 251.6 | 0.967 | 0.1729 | 554 |
| NM3 | NMOS | 6/1.5x1 | 20 | 196 | 758 | 196.6 | SAT | 260.5 | 0.963 | 0.06205 | 562 |
| NM4 | NMOS | 86.1/1.5x7 | 2.37e+03 | 212 | 1101 | 2.185e+04 | SAT | 262 | 0.977 | 0.04114 | 546 |
| PM0 | PMOS | 97.5/0.6x5 | 2.37e+03 | 268 | 699 | 1.556e+04 | SAT | 81.4 | 0.879 | 0.0772 | 1012 |
| PM1 | PMOS | 5.3/0.6x1 | 23 | 248 | 1280 | 161.7 | SAT | 84.9 | 0.871 | 0.04567 | 998 |
| PM2 | PMOS | 5.3/0.6x1 | 23 | 248 | 1246 | 161.5 | SAT | 84.81 | 0.871 | 0.0466 | 998 |

All transistors saturated.

## Predicted vs measured (fitted targets)

| Metric | Target | Predicted | Measured | Prediction error |
|---|---|---|---|---|
| gain_dB | 70.0 | 69.52182056470812 | 59.9415239 | +9.58 dB |
| gbw_Hz | 28159000.0 | 28159000.000000004 | 25243218.099208564 | +11.6 % |
| pm_deg | 82.116 | 82.1236213780607 | 81.12427678587251 | +1.00 deg |

Follower settles at vcm: True; saturated 8/8.

## History (all rounds so far)

| Round | gain_dB | gbw_Hz | pm_deg | saturated |
|---|---|---|---|---|
| 0 | 59.9415239 | 25243218.099208564 | 81.12427678587251 | 8/8 |