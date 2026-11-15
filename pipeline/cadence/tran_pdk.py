"""Step response on the foundry back end (runs on the PDK machine).

    python3 tran_pdk.py JOB.json   -> prints STEP {...} (step metrics only)

JOB.json: {"record":path, "biases":{...}, "vcm":V, "conditions":{...},
           "inverting_input":net, "gbw_Hz":float, "step_V":float}

Same circuit and bias point as the recorded AC run; the loop is closed for real
(output wired to the inverting input, no inductor) and the input is stepped.
Prints step metrics and nothing else: no PDK content, no device data.
"""
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import case_pdk as CP  # noqa: E402  same record preparation as the recorded run
import circuit as CI  # noqa: E402
import erc  # noqa: E402
import spectre_backend as SB  # noqa: E402
import step_response as SR  # noqa: E402


def prepare(c):
    """The preparation the recorded run applied, in the same order: bias terminals
    for floating gates, then the stated median-width policy for unprinted sizes."""
    found = erc.check(c)
    floating = [f["message"].split()[1] for f in found if f["code"] == "FLOATING_GATE"]
    c, _, _ = CI.bias_terminals(c, floating)
    CP.fill_sizes(c, [])
    return c


def _with_biases(c, biases):
    import copy
    r = copy.deepcopy(c)
    for d in r["ckt_netlist"]:
        if d["id"] in biases:
            d["value"] = f"{biases[d['id']]:.6g}"
    return r


def _tran_vout(path):
    """(t, v) for vout from a psfascii transient result."""
    txt = open(path).read()
    if "VALUE" not in txt:
        return [], []
    t, v = [], []
    for blk in re.split(r'\n"time"\s', txt.split("VALUE", 1)[1])[1:]:
        try:
            tt = float(blk.split()[0])
        except (ValueError, IndexError):
            continue
        m = re.search(r'"vout"\s+([-+\deE.]+)', blk)
        if m:
            t.append(tt)
            v.append(float(m.group(1)))
    return t, v


def deck(rec, spec, vcm, w, step_V):
    """Closed-loop follower, stepped. Subckt built by the shared back end."""
    sub, _ = SB.netlist(rec, spec, vcm)
    cond = spec["conditions"]
    t0, tr, tstop, tstep = w["t0"], w["tr"], w["tstop"], w["tstep"]
    bench = "\n".join([
        f"X0 (0 vdd vout vin vout) {SB.SUBCKT}",
        f"V_DD (vdd 0) vsource dc={cond['vdd']:.6g} type=dc",
        f"V_IN (vin 0) vsource type=pwl wave=[0 {vcm:.6g} {t0:.6g} {vcm:.6g} "
        f"{t0 + tr:.6g} {vcm + step_V:.6g} {tstop:.6g} {vcm + step_V:.6g}]",
        f"C_L (vout 0) capacitor c={cond['cl']:.6g}"] +
        ([f"R_L (vout 0) resistor r={cond['rl']:.6g}"] if cond.get("rl") else []))
    analyses = "\n".join([
        "simulatorOptions options reltol=1e-4 vabstol=1e-6 iabstol=1e-12 temp=27 tnom=27 gmin=1e-12",
        "dcOp dc maxiters=150 maxsteps=10000",
        f"tranA tran stop={tstop:.6g} maxstep={tstep:.6g} errpreset=conservative",
        "saveOptions options save=allpub", ""])
    return SB._header() + sub + "\n" + bench + "\n" + analyses


def main(job_path):
    job = json.load(open(job_path))
    rec = json.load(open(job["record"]))
    cond = job["conditions"]
    vcm, dv = job["vcm"], job.get("step_V", 0.05)
    spec = dict(conditions=cond, inverting_input=job.get("inverting_input"))
    w = SR.window(job.get("gbw_Hz"))
    d = deck(_with_biases(prepare(rec), job.get("biases") or {}), spec, vcm, w, dv)
    tmp = SB.tempfile.mkdtemp(prefix="tr_", dir=SB.PRIV)
    try:
        open(os.path.join(tmp, "deck.scs"), "w").write(d)
        SB.subprocess.run(["tcsh", "-c", f"{SB.cfg()['shell_init']}; cd {tmp}; "
                           "spectre -64 deck.scs -format psfascii -raw raw =log spectre.log"],
                          stdout=SB.subprocess.DEVNULL, stderr=SB.subprocess.DEVNULL, timeout=1800)
        logf = os.path.join(tmp, "spectre.log")
        log = open(logf).read() if os.path.exists(logf) else ""
        m = re.search(r"completes with (\d+) errors", log)
        cand = [f for f in os.listdir(os.path.join(tmp, "raw"))] if os.path.isdir(os.path.join(tmp, "raw")) else []
        trf = next((os.path.join(tmp, "raw", f) for f in cand if f.startswith("tranA")), None)
        if not trf:
            print("STEP " + json.dumps(dict(error="no transient output",
                                            spectre=(m.group(0) if m else "no completion line"),
                                            files=sorted(cand)[:8])))
            return
        t, v = _tran_vout(trf)
        r = SR.analyse(t, v, vcm, vcm + dv)
        r.update(step_V=dv, tstop_s=w["tstop"], pm_deg=job.get("pm_deg"),
                 gbw_Hz=job.get("gbw_Hz"), process="pdk")
        # the waveform itself, thinned: node voltages only, no PDK content
        step = max(1, len(t) // 1200)
        r["trace_t"] = [float(x) for x in t[::step]]
        r["trace_v"] = [float(x) for x in v[::step]]
        print("STEP " + json.dumps(r))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main(sys.argv[1])
