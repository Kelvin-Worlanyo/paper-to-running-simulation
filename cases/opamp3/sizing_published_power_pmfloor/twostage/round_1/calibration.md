## Calibration (one DC operating point, this round's sizing)

| Dev | Type | W/L (um) x m | Id (uA) | Vov (mV) | Vds (mV) | gm (uS) | Region | muCox (uA/V2) | a_gm | lambda (1/V) | Vth (mV) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| NM0 | NMOS | 4.67/3x1 | 11.1 | 239 | 368 | 88.64 | SAT | 249.5 | 0.954 | 0.1123 | 619 |
| NM1 | NMOS | 4.67/3x1 | 11.1 | 239 | 373 | 88.68 | SAT | 249.7 | 0.954 | 0.108 | 619 |
| NM2 | NMOS | 16.2/3x1 | 22.2 | 183 | 319 | 235.8 | SAT | 246.5 | 0.971 | 0.1042 | 536 |
| NM3 | NMOS | 8.81/3x1 | 12 | 180 | 719 | 129.9 | SAT | 252.1 | 0.975 | 0.04521 | 539 |
| NM4 | NMOS | 35.4/3x2 | 103 | 185 | 1177 | 1074 | SAT | 255.5 | 0.964 | 0.03094 | 534 |
| PM0 | PMOS | 35.4/0.5x2 | 103 | 111 | 623 | 1201 | SAT | 117.8 | 0.648 | 0.1144 | 997 |
| PM1 | PMOS | 6.29/0.5x1 | 11.1 | 126 | 1108 | 122.4 | SAT | 110.6 | 0.696 | 0.08293 | 987 |
| PM2 | PMOS | 6.29/0.5x1 | 11.1 | 126 | 1113 | 122.5 | SAT | 110.6 | 0.696 | 0.08274 | 987 |

All transistors saturated.

## Predicted vs measured (fitted targets)

| Metric | Target | Predicted | Measured | Prediction error |
|---|---|---|---|---|
| gain_dB | 70.0 | 70.09624375580101 | 70.4866769 | -0.39 dB |
| gbw_Hz | 28159000.0 | 26971298.69473285 | 29801163.234184504 | -9.5 % |
| power_W | 0.0002488 | 0.0002466377130247297 | 0.00024685019999999997 | -0.1 % |

Follower settles at vcm: True; saturated 8/8.

## History (all rounds so far)

| Round | gain_dB | gbw_Hz | power_W | saturated |
|---|---|---|---|---|
| 0 | 78.8491919 | 40145969.47228519 | 0.0002619216 | 8/8 |
| 1 | 70.4866769 | 29801163.234184504 | 0.00024685019999999997 | 8/8 |