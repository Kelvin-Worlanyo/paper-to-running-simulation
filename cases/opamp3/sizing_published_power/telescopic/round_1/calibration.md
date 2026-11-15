## Calibration (one DC operating point, this round's sizing)

| Dev | Type | W/L (um) x m | Id (uA) | Vov (mV) | Vds (mV) | gm (uS) | Region | muCox (uA/V2) | a_gm | lambda (1/V) | Vth (mV) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| NM0 | NMOS | 6/0.5x1 | 19.9 | 79 | 792 | 298.5 | SAT | 531.9 | 0.592 | 0.124 | 785 |
| NM1 | NMOS | 1.95/0.5x1 | 19.9 | 189 | 507 | 181.1 | SAT | 286.7 | 0.859 | 0.1422 | 704 |
| NM2 | NMOS | 3/0.5x1 | 45.1 | 248 | 311 | 320.5 | SAT | 244.5 | 0.881 | 0.3893 | 633 |
| NM3 | NMOS | 6/0.5x1 | 25.1 | 99 | 431 | 344.1 | SAT | 431.7 | 0.674 | 0.1903 | 783 |
| NM4 | NMOS | 1.95/0.5x1 | 25.1 | 216 | 490 | 202.6 | SAT | 276 | 0.872 | 0.1521 | 704 |
| PM0 | PMOS | 7/0.5x1 | 19.9 | 209 | 135 | 124.6 | TRIODE | 65.43 | 0.652 | 4.153 | 992 |
| PM1 | PMOS | 7/0.5x1 | 19.9 | 392 | 54 | 52.73 | TRIODE | 18.51 | 0.519 | 16.91 | 1027 |
| PM2 | PMOS | 7/0.5x1 | 25.1 | 209 | 286 | 197.2 | SAT | 82.08 | 0.820 | 0.3606 | 992 |
| PM3 | PMOS | 7/0.5x1 | 25.1 | 208 | 282 | 197.6 | SAT | 83.16 | 0.817 | 0.388 | 1061 |

WARNING: PM0 in TRIODE (Vds=135 mV, Vov=209 mV)
WARNING: PM1 in TRIODE (Vds=54 mV, Vov=392 mV)

## Predicted vs measured (fitted targets)

| Metric | Target | Predicted | Measured | Prediction error |
|---|---|---|---|---|
| gain_dB | 52.0 | 52.006950958656624 | 48.7044186 | +3.30 dB |
| power_W | 8.57568e-05 | 7.975382400000001e-05 | 8.113302000000001e-05 | -1.7 % |

Follower settles at vcm: True; saturated 7/9.

## History (all rounds so far)

| Round | gain_dB | power_W | saturated |
|---|---|---|---|
| 0 | 46.6887981 | 0.00011441124 | 6/9 |
| 1 | 48.7044186 | 8.113302000000001e-05 | 7/9 |