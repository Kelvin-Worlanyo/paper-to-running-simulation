## Calibration (one DC operating point, this round's sizing)

| Dev | Type | W/L (um) x m | Id (uA) | Vov (mV) | Vds (mV) | gm (uS) | Region | muCox (uA/V2) | a_gm | lambda (1/V) | Vth (mV) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| NM0 | NMOS | 21.8/3x1 | 10.4 | 95 | 356 | 166.7 | SAT | 317.3 | 0.762 | 0.07618 | 625 |
| NM1 | NMOS | 21.8/3x1 | 10.4 | 95 | 346 | 166.8 | SAT | 316.8 | 0.763 | 0.07855 | 625 |
| NM2 | NMOS | 15.2/3x1 | 20.8 | 182 | 380 | 221.7 | SAT | 247.7 | 0.973 | 0.07266 | 536 |
| NM3 | NMOS | 8.86/3x1 | 12 | 180 | 718 | 130.2 | SAT | 252.1 | 0.974 | 0.04522 | 538 |
| NM4 | NMOS | 39/3x2 | 113 | 184 | 1100 | 1179 | SAT | 254.8 | 0.964 | 0.03124 | 534 |
| PM0 | PMOS | 58.7/0.5x2 | 113 | 77 | 700 | 1489 | SAT | 160.8 | 0.510 | 0.111 | 997 |
| PM1 | PMOS | 11.4/0.5x1 | 10.4 | 72 | 1075 | 139.8 | SAT | 176.4 | 0.484 | 0.09123 | 992 |
| PM2 | PMOS | 11.4/0.5x1 | 10.4 | 72 | 1064 | 139.7 | SAT | 176.4 | 0.483 | 0.09162 | 992 |

All transistors saturated.

## Predicted vs measured (fitted targets)

| Metric | Target | Predicted | Measured | Prediction error |
|---|---|---|---|---|
| gain_dB | 70.0 | 70.0 | 78.8491919 | -8.85 dB |
| gbw_Hz | 28159000.0 | 28158999.999726918 | 40145969.47228519 | -29.9 % |
| power_W | 0.0002488 | 0.0002488 | 0.0002619216 | -5.0 % |

Follower settles at vcm: True; saturated 8/8.

## History (all rounds so far)

| Round | gain_dB | gbw_Hz | power_W | saturated |
|---|---|---|---|---|
| 0 | 78.8491919 | 40145969.47228519 | 0.0002619216 | 8/8 |