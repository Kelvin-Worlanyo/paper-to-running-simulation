## Calibration (one DC operating point, this round's sizing)

| Dev | Type | W/L (um) x m | Id (uA) | Vov (mV) | Vds (mV) | gm (uS) | Region | muCox (uA/V2) | a_gm | lambda (1/V) | Vth (mV) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| NM0 | NMOS | 6/0.5x1 | 22.4 | 87 | 734 | 323 | SAT | 488.5 | 0.630 | 0.127 | 785 |
| NM1 | NMOS | 2.85/0.5x1 | 22.4 | 161 | 484 | 231.7 | SAT | 304.1 | 0.830 | 0.1487 | 708 |
| NM2 | NMOS | 3/0.5x1 | 47.3 | 254 | 333 | 330.3 | SAT | 245 | 0.886 | 0.3342 | 633 |
| NM3 | NMOS | 6/0.5x1 | 24.9 | 98 | 405 | 341.3 | SAT | 431.4 | 0.672 | 0.2028 | 784 |
| NM4 | NMOS | 2.85/0.5x1 | 24.9 | 171 | 474 | 244.8 | SAT | 297.5 | 0.842 | 0.153 | 708 |
| PM0 | PMOS | 7/0.5x1 | 22.4 | 207 | 178 | 156.4 | TRIODE | 74.68 | 0.722 | 2.095 | 992 |
| PM1 | PMOS | 7/0.5x1 | 22.4 | 348 | 71 | 69.47 | TRIODE | 26.43 | 0.539 | 12.32 | 1037 |
| PM2 | PMOS | 7/0.5x1 | 24.9 | 208 | 294 | 197 | SAT | 82.53 | 0.821 | 0.326 | 992 |
| PM3 | PMOS | 7/0.5x1 | 24.9 | 206 | 294 | 197.8 | SAT | 83.77 | 0.819 | 0.3369 | 1063 |

WARNING: PM0 in TRIODE (Vds=178 mV, Vov=207 mV)
WARNING: PM1 in TRIODE (Vds=71 mV, Vov=348 mV)

## Predicted vs measured (fitted targets)

| Metric | Target | Predicted | Measured | Prediction error |
|---|---|---|---|---|
| gain_dB | 52.0 | 52.30525243351693 | 52.5045667 | -0.20 dB |
| power_W | 8.57568e-05 | 8.549952959999999e-05 | 8.515908000000001e-05 | +0.4 % |

Follower settles at vcm: True; saturated 7/9.

## History (all rounds so far)

| Round | gain_dB | power_W | saturated |
|---|---|---|---|
| 0 | 46.6887981 | 0.00011441124 | 6/9 |
| 1 | 48.7044186 | 8.113302000000001e-05 | 7/9 |
| 2 | 52.5045667 | 8.515908000000001e-05 | 7/9 |