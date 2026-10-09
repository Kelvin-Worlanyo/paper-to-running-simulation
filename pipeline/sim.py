"""Block D (dynamic checks) and block E (simulation).

One bench, the one validated against AnalogGym (design/run.py): unity-gain
feedback through a 1 T inductor fixes the DC point, a 1 T capacitor injects AC
at the inverting input, so vout/vac is the loop transfer. Phase margin is the
unwrapped loop phase at the 0 dB crossing with the DC phase set to 180 deg.

Checks, in the order they can fail:
  converges    the operating point solves
  follows      closed-loop vout sits at the input common mode (|dV| < 50 mV).
               Wrong input polarity is positive feedback and latches to a rail,
               so this is the polarity test.
  regions      each transistor is on (vgs > vth - 50 mV) and saturated
               (vds > vdsat); reported as a count, not a gate
  stable       a 0 dB crossing exists and PM > 0

Bias voltages are process-specific. The re-bias search moves only bias
sources (and the input common mode when the paper does not give it), never a
device size, and maximises (follows, transistors saturated, gain).
"""
import itertools
import math
import os
import re
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "design"))
import run as R  # noqa: E402  validated measure(), unwrap_deg(), MODELS

MODELS = os.path.abspath(R.MODELS)


def deck(sub, name, params, vdd, vcm, cl, ac=True, points=100, rl=None):
    ps = "\n".join(f".param {k}={v:.6g}" for k, v in params.items())
    rload = f"RLo  vout 0 {rl}\n" if rl else ""
    acl = f"ac dec {points} 0.01 1G\nwrdata {{OUT}}/ac.txt vdb(vout) vp(vout)" if ac else ""
    return f"""* pipeline bench
.include {sub}
.param mc_mm_switch=0
.param mc_pr_switch=0
.include {MODELS}
{ps}
V1   vdd  0    {vdd}
Vac  vac  0    dc {vcm} ac 1
Vip  vinp 0    {vcm}
Lfb  vout vinn 1T
Cac  vinn vac  1T
Xop  0 vdd vinn vinp vout {name}
CLo  vout 0 {cl}
{rload}.control
op
print v(vout) i(v1)
show m : vds vgs vth vdsat id gm gds
{acl}
.endc
.end
"""


def _parse_show(log):
    devs, cur = {}, None
    for line in log.splitlines():
        s = line.split()
        if not s:
            continue
        if s[0] == "device":
            cur = [re.sub(r"^m\.xop\.x?", "", x).split(".")[0] for x in s[1:]]
            for d in cur:
                devs.setdefault(d, {})
        elif cur and s[0] in ("vds", "vgs", "vth", "vdsat", "id", "gm", "gds") and len(s) == len(cur) + 1:
            for d, v in zip(cur, s[1:]):
                try:
                    devs[d][s[0]] = float(v)
                except ValueError:
                    pass
    return devs


def simulate(sub_text, name, params, vdd, vcm, cl, ac=True, points=100, rl=None):
    with tempfile.TemporaryDirectory() as tmp:
        sub = os.path.join(tmp, "dut.sp")
        open(sub, "w").write(sub_text)
        path = os.path.join(tmp, "tb.cir")
        open(path, "w").write(deck(sub, name, params, vdd, vcm, cl, ac, points, rl).replace("{OUT}", tmp))
        p = subprocess.run(["ngspice", "-b", path], capture_output=True, text=True, timeout=120)
        log = p.stdout + p.stderr
        r = dict(converges=False, log_tail=log[-600:])
        m = re.search(r"v\(vout\)\s*=\s*([-\d.eE+]+)", log)
        i = re.search(r"i\(v1\)\s*=\s*([-\d.eE+]+)", log)
        if not m:
            return r
        r.update(converges=True, vout=float(m.group(1)),
                 power_W=abs(float(i.group(1))) * vdd if i else None)
        r["follows"] = abs(r["vout"] - vcm) < 0.05
        devs = _parse_show(log)
        r["devices"] = devs
        sat = regions(devs)
        r["n_mos"], r["n_sat"] = len(devs), sum(sat.values())
        r["not_saturated"] = sorted(d for d, ok in sat.items() if not ok)
        acf = os.path.join(tmp, "ac.txt")
        if ac and os.path.exists(acf):
            f, mag, ph = R.read_ac(acf)
            if f:
                meas, phd = R.measure(f, mag, ph)
                r.update(meas)
                r["bode"] = (f, mag, phd)
                r["stable"] = meas["gbw_Hz"] is not None and meas["pm_deg"] is not None \
                    and meas["pm_deg"] > 0
        return r


# Region test. "strong" (default): on when V_GS > V_th - 50 mV, saturated when
# V_DS > V_Dsat. "weak" is used only for a paper that declares subthreshold
# design, where every device sits below threshold by intent: a device is on when
# it conducts at least 100 pA and saturated when V_DS > max(V_Dsat, 4 kT/q).
REGION = "strong"
UT4 = 4 * 0.02585


def regions(devs, mode=None):
    mode = mode or REGION
    sat = {}
    for d, x in devs.items():
        if not all(k in x for k in ("vgs", "vth", "vds", "vdsat")):
            continue
        if mode == "weak":
            sat[d] = abs(x.get("id", 0.0)) >= 1e-10 and x["vds"] > max(x["vdsat"], UT4)
        else:
            sat[d] = x["vgs"] > x["vth"] - 0.05 and x["vds"] > x["vdsat"]
    return sat


def violation(r):
    """How far the transistors are from saturation, in volts (0 = all saturated)."""
    v = 0.0
    for x in r.get("devices", {}).values():
        if all(k in x for k in ("vgs", "vth", "vds", "vdsat")):
            if REGION == "weak":
                v += max(0.0, max(x["vdsat"], UT4) - x["vds"]) + (0.05 if abs(x.get("id", 0.0)) < 1e-10 else 0.0)
            else:
                v += max(0.0, (x["vth"] - 0.05) - x["vgs"]) + max(0.0, x["vdsat"] - x["vds"])
    return v


def bias_grid(vdd):
    """0.1 V steps; at supplies below 1.8 V, 17 steps across the supply."""
    step = min(0.1, vdd / 18)
    return [round(step * k, 4) for k in range(1, int(round(vdd / step)))]


def score(r):
    """Lexicographic: follows with gain > 20 dB, transistors saturated, closeness to
    saturation, gain. Following alone is not enough: a dead loop can sit at the
    common mode by coincidence."""
    if not r.get("converges"):
        return (-1, 0, -1e9, -1e9)
    amp = r.get("follows", False) and (r.get("gain_dB") or -1e9) > 20   # tracks AND amplifies
    return (int(amp), r.get("n_sat", 0), -round(violation(r), 3), r.get("gain_dB") or -1e9)


def rebias(sub_text, name, params, vdd, vcm, cl, search_vcm, sweeps=3, grid=None, rl=None,
           starts=6, seed=1, log=print):
    """Multi-start coordinate search over bias sources (and VCM).

    Starts: the printed values (out-of-range ones clipped to VDD/2), all at
    VDD/2, and random points. Each start runs coordinate sweeps over a 0.1 V
    grid. Returns (params, vcm, result) for the best point found."""
    import random
    rng = random.Random(seed)
    grid = grid or bias_grid(vdd)
    keys = list(params) + (["VCM"] if search_vcm else [])
    printed = {k: (v if v is not None and 0 < v < vdd else vdd / 2) for k, v in params.items()}
    v0 = vcm if vcm is not None else vdd / 2
    inits = [(printed, v0), ({k: vdd / 2 for k in params}, v0)]
    for _ in range(starts):
        inits.append(({k: rng.choice(grid) for k in params},
                      rng.choice(grid) if search_vcm else v0))
    overall = None
    for n, (cur, cur_vcm) in enumerate(inits):
        cur = dict(cur)
        best = simulate(sub_text, name, cur, vdd, cur_vcm, cl, ac=True, points=20, rl=rl)
        for sweep in range(sweeps):
            changed = False
            for k in keys:
                def trial(x):
                    p = dict(cur)
                    v = cur_vcm
                    if k == "VCM":
                        v = x
                    else:
                        p[k] = x
                    return x, simulate(sub_text, name, p, vdd, v, cl, ac=True, points=20, rl=rl)
                with ThreadPoolExecutor(8) as ex:
                    results = list(ex.map(trial, grid))
                x, r = max(results, key=lambda t: score(t[1]))
                if score(r) > score(best):
                    best, changed = r, True
                    if k == "VCM":
                        cur_vcm = x
                    else:
                        cur[k] = x
            if not changed:
                break
        log(f"    start {n}: follows={best.get('follows')} sat={best.get('n_sat')}/"
            f"{best.get('n_mos')} viol={violation(best):.3f} gain={best.get('gain_dB')} "
            f"biases={cur} vcm={cur_vcm}")
        if overall is None or score(best) > score(overall[2]):
            overall = (dict(cur), cur_vcm, best)
        if score(best)[0] and best.get("n_sat") == best.get("n_mos") and n >= 1:
            break          # all saturated from a deterministic start: done
    return overall
