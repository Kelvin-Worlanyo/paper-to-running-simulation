"""Closed-loop step response: the time-domain companion to the phase margin.

Phase margin is a small-signal frequency-domain number read off the loop gain
with the loop broken by a 1 T inductor. A low margin is a prediction about
behaviour -- overshoot and slowly decaying ringing -- and that prediction is
worth testing directly, because a reader asked to trust a 6 deg margin wants to
see what the amplifier actually does. This module closes the loop for real
(output wired to the inverting input, no inductor), steps the input, and
measures the response.

Reported, all from the trace alone:
  overshoot_pct   (peak - final) / step, in percent
  settle_1pct_s   first time after which |v - final| stays under 1% of the step
  ring_cycles     crossings of the final value after the first peak, / 2
  decay_ratio     second overshoot peak / first, as a fraction (< 1 decays)
  final_err_V     final value minus the commanded level

The analysis is process-independent and shared by both back ends; only the deck
differs. Nothing here changes the AC bench, which stays as validated.
"""
import math
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "design"))


def analyse(t, v, v0, v1):
    """Step metrics from a trace. v0/v1 are the COMMANDED levels before/after.

    Overshoot is normalised by the step the output actually took, not the
    commanded one, so a standing offset between vout and vcm -- which the
    operating-point check already tolerates up to 50 mV -- cannot inflate or
    deflate it. The offset itself is reported separately rather than folded in.
    """
    cmd = v1 - v0
    if not t or abs(cmd) < 1e-9:
        return dict(error="no step")
    final, initial = v[-1], v[0]
    measured = final - initial
    # the output's own excursion is the right normaliser; fall back to the
    # commanded step if the output barely moved (then overshoot is meaningless
    # anyway and the tracking numbers below say so)
    denom = abs(measured) if abs(measured) > 0.1 * abs(cmd) else abs(cmd)
    sgn = 1.0 if cmd > 0 else -1.0
    peak_i = max(range(len(v)), key=lambda i: sgn * (v[i] - final))
    overshoot = sgn * (v[peak_i] - final) / denom * 100.0
    # settling: last time the trace is outside the 1% band, then the next sample
    band = 0.01 * denom
    settle = None
    for i in range(len(v) - 1, -1, -1):
        if abs(v[i] - final) > band:
            settle = t[i + 1] if i + 1 < len(t) else None
            break
    else:
        settle = t[0]
    # ringing: crossings of the final value after the first peak
    cross = 0
    for i in range(peak_i, len(v) - 1):
        if (v[i] - final) == 0.0:
            continue
        if (v[i] - final) * (v[i + 1] - final) < 0:
            cross += 1
    # second overshoot peak, for the decay ratio
    peaks = []
    for i in range(1, len(v) - 1):
        if sgn * (v[i] - final) > 0 and v[i] >= v[i - 1] and v[i] > v[i + 1]:
            peaks.append(sgn * (v[i] - final))
    decay = (peaks[1] / peaks[0]) if len(peaks) > 1 and peaks[0] > 0 else None
    return dict(overshoot_pct=overshoot, settle_1pct_s=settle, ring_cycles=cross / 2.0,
                decay_ratio=decay, initial_V=initial, final_V=final,
                commanded_step_V=cmd, measured_step_V=measured,
                tracking_pct=100.0 * measured / cmd,
                offset_V=initial - v0,                 # standing vout - vcm before the step
                peak_V=v[peak_i], t_peak_s=t[peak_i], samples=len(t))


def window(gbw_Hz, periods=120.0, settle_frac=0.1, samples=20000):
    """Deck timing from the measured unity-gain crossing: a window long enough
    for ringing at that frequency to decay, sampled finely enough to see it."""
    gbw = gbw_Hz if gbw_Hz and gbw_Hz > 0 else 1e6
    span = periods / gbw
    t0 = settle_frac * span
    return dict(t0=t0, tr=0.002 / gbw, tstop=t0 + span, tstep=(t0 + span) / samples)


# ------------------------------------------------------------------- ngspice
def deck(sub, name, params, vdd, vcm, cl, dv, w, rl=None):
    """Unity-gain follower with real feedback, stepped at the non-inverting input."""
    import sim as SIM
    ps = "\n".join(f".param {k}={v:.6g}" for k, v in params.items())
    rload = f"RLo  vout 0 {rl}\n" if rl else ""
    t0, tr, tstop, tstep = w["t0"], w["tr"], w["tstop"], w["tstep"]
    return f"""* step response bench (closed loop, no inductor)
.include {sub}
.param mc_mm_switch=0
.param mc_pr_switch=0
.include {SIM.MODELS}
{ps}
V1   vdd  0    {vdd}
Vin  vinp 0    PWL(0 {vcm:.6g} {t0:.6g} {vcm:.6g} {t0 + tr:.6g} {vcm + dv:.6g} {tstop:.6g} {vcm + dv:.6g})
Xop  0 vdd vout vinp vout {name}
CLo  vout 0 {cl}
{rload}.control
op
tran {tstep:.6g} {tstop:.6g}
wrdata {{OUT}}/tran.txt v(vout)
.endc
.end
"""


def run_ngspice(sub_text, name, params, vdd, vcm, cl, gbw_Hz, dv=0.05, rl=None,
                keep_trace=False):
    w = window(gbw_Hz)
    with tempfile.TemporaryDirectory() as tmp:
        sub = os.path.join(tmp, "dut.sp")
        open(sub, "w").write(sub_text)
        path = os.path.join(tmp, "tb.cir")
        open(path, "w").write(deck(sub, name, params, vdd, vcm, cl, dv, w, rl).replace("{OUT}", tmp))
        p = subprocess.run(["ngspice", "-b", path], capture_output=True, text=True, timeout=600)
        f = os.path.join(tmp, "tran.txt")
        if not os.path.exists(f):
            return dict(error="no transient output", log_tail=(p.stdout + p.stderr)[-600:])
        t, v = [], []
        for line in open(f):
            s = line.split()
            if len(s) >= 2:
                try:
                    t.append(float(s[0])); v.append(float(s[1]))
                except ValueError:
                    pass
        r = analyse(t, v, vcm, vcm + dv)
        r.update(step_V=dv, tstop_s=w["tstop"])
        if keep_trace:                      # every 4th sample is plenty to plot
            r["trace_t"] = t[::4]
            r["trace_v"] = v[::4]
        return r
