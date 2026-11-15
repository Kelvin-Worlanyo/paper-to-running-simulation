"""Design bench: build, simulate, measure. No numpy on this machine, so the
sweep is analysed in plain Python.

Phase margin is computed from the LOOP transfer with the phase UNWRAPPED.
AnalogGym's baseline reports 261, 188 and 142 degrees for its amplifiers,
which are not phase margins - they are what you get from a wrapped phase read
at a single point. Here the DC phase is normalised to 180 (the inverting
input is driven, so that is where it must start) and PM is the unwrapped
phase at the 0 dB crossing: one dominant pole gives 90, two coincident poles
give 0.
"""
import math, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
MODELS = os.path.join(HERE, "..", "AnalogGym", "AnalogGym", "Amplifier",
                      "mosfet_model", "sky130_pdk", "libs.tech", "ngspice",
                      "corners", "tt.spice")


def build(template, name, netlist, out):
    t = open(os.path.join(HERE, template)).read()
    t = (t.replace("__NETLIST__", os.path.join(HERE, "netlist", netlist))
          .replace("__MODELS__", os.path.abspath(MODELS))
          .replace("__NAME__", name).replace("__OUT__", out))
    deck = os.path.join(out, f"{name}_{template}")
    open(deck, "w").write(t)
    return deck


def run(deck, out):
    log = os.path.join(out, "log.txt")
    subprocess.run(["ngspice", "-b", "-o", log, deck], cwd=HERE,
                   capture_output=True, text=True)
    return open(log).read()


def read_ac(path):
    """wrdata writes 'freq vdb freq vp' per row."""
    f, mag, ph = [], [], []
    for line in open(path):
        p = line.split()
        if len(p) >= 4:
            f.append(float(p[0])); mag.append(float(p[1])); ph.append(float(p[3]))
    return f, mag, ph


def unwrap_deg(ph_rad):
    out, off = [], 0.0
    prev = ph_rad[0]
    for p in ph_rad:
        d = p - prev
        if d > math.pi:
            off -= 2 * math.pi
        elif d < -math.pi:
            off += 2 * math.pi
        out.append((p + off) * 180.0 / math.pi)
        prev = p
    # the inverting input is driven, so the loop transfer starts at 180 deg
    shift = 180.0 - out[0]
    return [x + shift for x in out]


def measure(f, mag, ph):
    phd = unwrap_deg(ph)
    gain = mag[0]
    gbw = pm = None
    for i in range(1, len(mag)):
        if mag[i - 1] > 0 >= mag[i]:                    # 0 dB crossing
            t = (0 - mag[i - 1]) / (mag[i] - mag[i - 1])
            gbw = f[i - 1] * (f[i] / f[i - 1]) ** t     # log interpolation
            pm = phd[i - 1] + t * (phd[i] - phd[i - 1])
            break
    return dict(gain_dB=gain, gbw_Hz=gbw, pm_deg=pm), phd


def power_from(log):
    m = re.search(r"i\(v1\)\s*=\s*([-\d.eE+]+)", log)
    return abs(float(m.group(1))) * 1.8 if m else None


def op_from(log):
    d = {}
    for k in ("v(vout)", "v(vinn)", "v(vinp)"):
        m = re.search(re.escape(k) + r"\s*=\s*([-\d.eE+]+)", log)
        if m:
            d[k] = float(m.group(1))
    return d


COND = {                       # VCM, CL. Loads from the paper where given.
    "ota5t":      (0.9, "10p"),
    "miller2":    (0.9, "10p"),
    "telescopic": (0.6, "20p"),   # NMOS pair; C0 = 20 pF in Fig. 2
    "folded":     (0.6, "10p"),   # PMOS pair; no load stated in Fig. 3
    "twostage":   (0.9, "2p"),    # NMOS pair; C1 = 2 pF in Fig. 4
}


def _apply(deck, name):
    vcm, cl = COND.get(name, (0.9, "10p"))
    t = open(deck).read()
    t = t.replace(".param VCM=0.9", f".param VCM={vcm}").replace(".param CL=10p", f".param CL={cl}")
    open(deck, "w").write(t)


def characterise(name, netlist):
    out = os.path.join(HERE, "out", name)
    os.makedirs(out, exist_ok=True)
    deck = build("tb_ac.cir", name, netlist, out)
    _apply(deck, name)
    log = run(deck, out)
    if "error" in log.lower() and "ac.txt" not in log:
        pass
    f, mag, ph = read_ac(os.path.join(out, "ac.txt"))
    res, phd = measure(f, mag, ph)
    op = open(os.path.join(out, "op.txt")).read()
    res["power_W"] = power_from(op)
    res.update({k: v for k, v in op_from(op).items()})
    return res, (f, mag, phd)


def read_cols(path, n):
    cols = [[] for _ in range(n)]
    for line in open(path):
        q = line.split()
        if len(q) >= 2 * n - 1:
            cols[0].append(float(q[0]))
            for k in range(1, n):
                cols[k].append(float(q[2 * k - 1]))
    return cols


def swing(dcfile):
    """Output range over which the unity-gain follower still tracks its input.

    The DC feedback inductor is a short, so this sweep is CLOSED loop - the
    slope is 1 by construction and an open-loop gain criterion finds nothing.
    What it does show is where the follower stops following, which is the
    usable output range and is the number a testbench actually needs.
    Tracking is taken as |vout - vin| < 50 mV."""
    vin, vout = [], []
    for line in open(dcfile):
        q = line.split()
        if len(q) >= 2:
            vin.append(float(q[0])); vout.append(float(q[1]))
    ok = [vout[i] for i in range(len(vin)) if abs(vout[i] - vin[i]) < 0.05]
    return (min(ok), max(ok)) if ok else (None, None)


def slew(tranfile):
    """V/us on the rising edge, 10% to 90% of the step.

    Only a slew rate if the step actually steers the input pair; compare
    against I_tail/CL to check. Otherwise it is 2.2/(2*pi*GBW) in disguise."""
    t, vo = [], []
    for line in open(tranfile):
        q = line.split()
        if len(q) >= 2:
            t.append(float(q[0])); vo.append(float(q[1]))
    lo, hi = min(vo), max(vo)
    a, b = lo + 0.1 * (hi - lo), lo + 0.9 * (hi - lo)
    ta = tb = None
    for i in range(1, len(t)):
        if ta is None and vo[i - 1] < a <= vo[i]:
            ta = t[i]
        elif ta is not None and vo[i - 1] < b <= vo[i]:
            tb = t[i]; break
    return (b - a) / (tb - ta) / 1e6 if ta and tb and tb > ta else None


def transient(name, netlist):
    out = os.path.join(HERE, "out", name)
    deck = build("tb_tran.cir", name, netlist, out)
    _apply(deck, name)
    run(deck, out)
    return os.path.join(out, "tran.txt")


if __name__ == "__main__":
    import plot as P
    rows = []
    import sys as _s
    CIRCUITS = (("ota5t", "ota5t.sp"), ("miller2", "miller2.sp"),
                ("telescopic", "telescopic.sp"), ("folded", "folded.sp"),
                ("twostage", "twostage.sp"))
    if len(_s.argv) > 1:
        CIRCUITS = tuple(c for c in CIRCUITS if c[0] in _s.argv[1:])
    for nm, nl in CIRCUITS:
        r, (f, mag, phd) = characterise(nm, nl)
        out = os.path.join(HERE, "out", nm)
        lo, hi = swing(os.path.join(out, "dc.txt"))
        r["swing_lo_V"], r["swing_hi_V"] = lo, hi
        tf = transient(nm, nl)
        r["slew_V_per_us"] = slew(tf)
        rows.append((nm, r))

        P.plot(os.path.join(out, "bode.svg"), [
            dict(xlabel="frequency (Hz)", ylabel="|A| (dB)", logx=True,
                 series=[(f, mag, P.C1, "gain")],
                 marks=[(r["gbw_Hz"], 0.0, f'GBW {r["gbw_Hz"]/1e6:.2f} MHz')]),
            dict(xlabel="frequency (Hz)", ylabel="phase (deg, unwrapped)", logx=True,
                 series=[(f, phd, P.C2, "phase")],
                 marks=[(r["gbw_Hz"], r["pm_deg"], f'PM {r["pm_deg"]:.1f} deg')]),
        ], title=f"{nm}  -  loop gain",
           sub=f"Sky130 1.8 V, CL = {COND.get(nm, (0.9,'10p'))[1]}, "
               f"VCM = {COND.get(nm, (0.9,'10p'))[0]} V, TT, 27 C")

        # zoom on the edge: at full scale the transition is one pixel wide
        tran_rows = [l.split() for l in open(tf) if len(l.split()) >= 4]
        win = [(float(q[0]), float(q[1]), float(q[3])) for q in tran_rows
               if 0.85e-6 <= float(q[0]) <= 3.2e-6]
        tt = [a for a, _, _ in win]
        tv = [b for _, b, _ in win]
        vin_col = [c for _, _, c in win]
        P.plot(os.path.join(out, "step.svg"), [
            dict(xlabel="time (s)", ylabel="V", logx=False,
                 series=[(tt, vin_col, P.C2, "vin"), (tt, tv, P.C1, "vout")])],
            title=f"{nm}  -  unity-gain step, 0.5 V to 0.9 V",
            sub=f'400 mV step into 10 pF; slew {r["slew_V_per_us"]:.2f} V/us'
                f' (I/CL bound {r["power_W"]/1.8/10e-12/1e6:.2f} V/us)'
                if r["slew_V_per_us"] else "400 mV step into 10 pF")

        dvin, dvout = [], []
        for line in open(os.path.join(out, "dc.txt")):
            q = line.split()
            if len(q) >= 2:
                dvin.append(float(q[0])); dvout.append(float(q[1]))
        P.plot(os.path.join(out, "dc.svg"), [
            dict(xlabel="V(vinp)  (V)", ylabel="V(vout)  (V)", logx=False,
                 series=[(dvin, dvout, P.C1, "vout")])],
            title=f"{nm}  -  DC transfer, unity-gain follower",
            sub=f"tracks from {lo:.2f} to {hi:.2f} V" if lo else "does not track")

    hdr = ["gain_dB", "gbw_Hz", "pm_deg", "power_W", "swing_lo_V", "swing_hi_V",
           "slew_V_per_us", "v(vout)"]
    with open(os.path.join(HERE, "out", "results.csv"), "w") as fh:
        fh.write("amp," + ",".join(hdr) + "\n")
        for nm, r in rows:
            fh.write(nm + "," + ",".join(str(r.get(k, "")) for k in hdr) + "\n")
    for nm, r in rows:
        print(f"{nm:9s} gain {r['gain_dB']:6.1f} dB   GBW {r['gbw_Hz']/1e6:7.3f} MHz   "
              f"PM {r['pm_deg']:5.1f} deg   P {r['power_W']*1e6:7.1f} uW   "
              f"swing {r['swing_lo_V']:.2f}-{r['swing_hi_V']:.2f} V   "
              f"SR {r['slew_V_per_us']:.2f} V/us")
