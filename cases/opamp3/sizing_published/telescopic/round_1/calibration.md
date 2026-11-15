## Calibration (one DC operating point, this round's sizing)

| Dev | Type | W/L (um) x m | Id (uA) | Vov (mV) | Vds (mV) | gm (uS) | Region | muCox (uA/V2) | a_gm | lambda (1/V) | Vth (mV) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| NM0 | NMOS | 6/0.5x1 | 10.5 | 39 | 712 | 187 | SAT | 1137 | 0.349 | 0.1464 | 810 |
| NM1 | NMOS | 0.42/0.5x1 | 10.5 | 338 | 662 | 55.95 | SAT | 218.5 | 0.901 | 0.1487 | 681 |
| NM2 | NMOS | 3/0.5x1 | 26.2 | 182 | 310 | 249.3 | SAT | 263.6 | 0.866 | 0.2933 | 633 |
| NM3 | NMOS | 6/0.5x1 | 15.7 | 65 | 466 | 250.8 | SAT | 617.9 | 0.520 | 0.182 | 807 |
| NM4 | NMOS | 0.42/0.5x1 | 15.7 | 424 | 639 | 65.04 | SAT | 207.3 | 0.880 | 0.1691 | 681 |
| PM0 | PMOS | 7/0.5x1 | 10.5 | 157 | 85 | 75.41 | TRIODE | 61.18 | 0.562 | 8.101 | 993 |
| PM1 | PMOS | 7/0.5x1 | 10.5 | 344 | 32 | 31.23 | TRIODE | 12.7 | 0.511 | 29.96 | 1014 |
| PM2 | PMOS | 7/0.5x1 | 15.7 | 157 | 229 | 149.2 | SAT | 90.71 | 0.748 | 0.4952 | 992 |
| PM3 | PMOS | 7/0.5x1 | 15.7 | 166 | 155 | 129.2 | TRIODE | 81.65 | 0.682 | 2.378 | 1048 |

WARNING: PM0 in TRIODE (Vds=85 mV, Vov=157 mV)
WARNING: PM1 in TRIODE (Vds=32 mV, Vov=344 mV)
WARNING: PM3 in TRIODE (Vds=155 mV, Vov=166 mV)

## Predicted vs measured (fitted targets)

| Metric | Target | Predicted | Measured | Prediction error |
|---|---|---|---|---|
| gain_dB | 52.0 | 60.22538866877405 | 26.8157731 | +33.41 dB |

Follower settles at vcm: False; saturated 6/9.

## History (all rounds so far)

| Round | gain_dB | saturated |
|---|---|---|
| 0 | -38.2663059 | 2/9 |
| 1 | 26.8157731 | 6/9 |