## Calibration (one DC operating point, this round's sizing)

| Dev | Type | W/L (um) x m | Id (uA) | Vov (mV) | Vds (mV) | gm (uS) | Region | muCox (uA/V2) | a_gm | lambda (1/V) | Vth (mV) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| NM0 | NMOS | 42.3/2x1 | 47.7 | 128 | 263 | 658.7 | SAT | 275.8 | 0.882 | 0.1793 | 608 |
| NM1 | NMOS | 42.3/2x1 | 47.8 | 128 | 242 | 656.9 | SAT | 274.5 | 0.881 | 0.2196 | 608 |
| NM2 | NMOS | 35.7/1.5x1 | 95.5 | 180 | 271 | 1026 | SAT | 248.8 | 0.965 | 0.2441 | 548 |
| NM3 | NMOS | 7.97/1.5x1 | 20 | 168 | 727 | 225.5 | SAT | 267.1 | 0.947 | 0.06608 | 559 |
| NM4 | NMOS | 96.4/1.5x16 | 4.46e+03 | 182 | 1007 | 4.782e+04 | SAT | 262.8 | 0.974 | 0.04603 | 546 |
| PM0 | PMOS | 97.3/0.6x9 | 4.46e+03 | 274 | 793 | 2.874e+04 | SAT | 81.44 | 0.882 | 0.06849 | 1012 |
| PM1 | PMOS | 10.1/0.6x1 | 47.8 | 259 | 1286 | 323.8 | SAT | 84.36 | 0.877 | 0.04571 | 1007 |
| PM2 | PMOS | 10.1/0.6x1 | 47.7 | 259 | 1265 | 323.5 | SAT | 84.31 | 0.877 | 0.04627 | 1007 |

All transistors saturated.

## Predicted vs measured (fitted targets)

| Metric | Target | Predicted | Measured | Prediction error |
|---|---|---|---|---|
| gain_dB | 70.0 | 70.0592 | 69.2753219 | +0.78 dB |
| gbw_Hz | 28159000.0 | 31425444.000000004 | 29837328.27400075 | +5.3 % |
| pm_deg | 82.116 | 83.11684749165337 | 81.19754831159636 | +1.92 deg |

Follower settles at vcm: True; saturated 8/8.

## History (all rounds so far)

| Round | gain_dB | gbw_Hz | pm_deg | saturated |
|---|---|---|---|---|
| 0 | 59.9415239 | 25243218.099208564 | 81.12427678587251 | 8/8 |
| 1 | 69.2753219 | 29837328.27400075 | 81.19754831159636 | 8/8 |