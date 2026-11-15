## Calibration (one DC operating point, this round's sizing)

| Dev | Type | W/L (um) x m | Id (uA) | Vov (mV) | Vds (mV) | gm (uS) | Region | muCox (uA/V2) | a_gm | lambda (1/V) | Vth (mV) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| NM0 | NMOS | 4.4/2x1 | 22.2 | 290 | 366 | 145.1 | SAT | 240.2 | 0.946 | 0.1858 | 604 |
| NM1 | NMOS | 4.4/2x1 | 22.2 | 290 | 369 | 145.2 | SAT | 240.3 | 0.947 | 0.1812 | 604 |
| NM2 | NMOS | 16.6/2x3 | 44.5 | 118 | 218 | 660.7 | SAT | 256.4 | 0.876 | 0.2592 | 544 |
| NM3 | NMOS | 8.99/2x1 | 8 | 115 | 662 | 120.7 | SAT | 269.4 | 0.867 | 0.07738 | 547 |
| NM4 | NMOS | 19.7/2x4 | 76.2 | 118 | 1112 | 1121 | SAT | 276 | 0.872 | 0.05558 | 544 |
| PM0 | PMOS | 17.4/2x7 | 76.2 | 165 | 688 | 734.6 | SAT | 92.29 | 0.794 | 0.01851 | 1049 |
| PM1 | PMOS | 17.2/2x2 | 22.2 | 167 | 1214 | 212.3 | SAT | 92.35 | 0.799 | 0.01064 | 1049 |
| PM2 | PMOS | 17.2/2x2 | 22.2 | 167 | 1216 | 212.3 | SAT | 92.35 | 0.799 | 0.01062 | 1049 |

All transistors saturated.

## Predicted vs measured (fitted targets)

| Metric | Target | Predicted | Measured | Prediction error |
|---|---|---|---|---|
| gain_dB | 70.0 | 70.00000000007118 | 72.9128317 | -2.91 dB |
| gbw_Hz | 28159000.0 | 28159000.000000007 | 22131109.941993073 | +27.2 % |
| power_W | 0.0002488 | 0.00024755599999999996 | 0.0002315556 | +6.9 % |

Follower settles at vcm: True; saturated 8/8.

## History (all rounds so far)

| Round | gain_dB | gbw_Hz | power_W | saturated |
|---|---|---|---|---|
| 0 | 64.6758152 | 20117880.78282816 | 0.000279198 | 8/8 |
| 1 | 72.9128317 | 22131109.941993073 | 0.0002315556 | 8/8 |