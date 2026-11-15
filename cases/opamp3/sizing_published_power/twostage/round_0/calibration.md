## Calibration (one DC operating point, this round's sizing)

| Dev | Type | W/L (um) x m | Id (uA) | Vov (mV) | Vds (mV) | gm (uS) | Region | muCox (uA/V2) | a_gm | lambda (1/V) | Vth (mV) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| NM0 | NMOS | 4.33/2x1 | 10.6 | 201 | 232 | 99.4 | SAT | 242.3 | 0.941 | 0.509 | 626 |
| NM1 | NMOS | 4.33/2x1 | 10.6 | 202 | 221 | 98.19 | SAT | 240.6 | 0.933 | 0.6355 | 626 |
| NM2 | NMOS | 13.3/2x1 | 21.3 | 160 | 316 | 256 | SAT | 248.8 | 0.963 | 0.1387 | 545 |
| NM3 | NMOS | 5.33/2x1 | 8 | 156 | 705 | 99.75 | SAT | 247.2 | 0.971 | 0.06906 | 549 |
| NM4 | NMOS | 18.4/2x4 | 126 | 161 | 1143 | 1493 | SAT | 263 | 0.957 | 0.04696 | 544 |
| PM0 | PMOS | 18.6/2x7 | 126 | 214 | 657 | 1008 | SAT | 84.27 | 0.857 | 0.02058 | 1049 |
| PM1 | PMOS | 11.8/2x1 | 10.6 | 204 | 1263 | 88.35 | SAT | 86.13 | 0.848 | 0.01009 | 1047 |
| PM2 | PMOS | 11.8/2x1 | 10.6 | 204 | 1252 | 88.34 | SAT | 86.12 | 0.848 | 0.01017 | 1047 |

All transistors saturated.

## Predicted vs measured (fitted targets)

| Metric | Target | Predicted | Measured | Prediction error |
|---|---|---|---|---|
| gain_dB | 70.0 | 70.0 | 64.6758152 | +5.32 dB |
| gbw_Hz | 28159000.0 | 28159000.000000004 | 20117880.78282816 | +40.0 % |
| power_W | 0.0002488 | 0.0002488 | 0.000279198 | -10.9 % |

Follower settles at vcm: True; saturated 8/8.

## History (all rounds so far)

| Round | gain_dB | gbw_Hz | power_W | saturated |
|---|---|---|---|---|
| 0 | 64.6758152 | 20117880.78282816 | 0.000279198 | 8/8 |