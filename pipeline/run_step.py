"""Step response for a recorded case result, in the open process.

    run_step.py CASE_DIR KEY [as_printed|rebiased]

Rebuilds the exact circuit and bias point the recorded run reached -- same
record, same flip, same bias sources, same input common mode, same load -- and
closes the loop for real to measure overshoot, settling and ringing. Writes
CASE_DIR/out/KEY/step_<variant>.json. The AC bench is untouched.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import circuit  # noqa: E402
import erc  # noqa: E402
import step_response as SR  # noqa: E402
import tospice  # noqa: E402


def run(case, key, variant="rebiased", dv=0.05):
    out = os.path.join(case, "out", key)
    res = json.load(open(os.path.join(out, "result.json")))
    x = res[variant]
    cond = res["conditions"]
    c = circuit.load(os.path.join(case, "records", f"{key}.json"))
    found = erc.check(c)
    floating = [f["message"].split()[1] for f in found if f["code"] == "FLOATING_GATE"]
    c, _, _ = circuit.bias_terminals(c, floating)
    name = "dut"
    sub, params, _ = tospice.build(c, name, bool(x.get("flip")))
    # the bias point the recorded run used
    p = dict(x.get("biases") or {k: (v if v is not None else cond["vdd"] / 2)
                                 for k, v in params.items()})
    for k, v in params.items():
        p.setdefault(k, v if v is not None else cond["vdd"] / 2)
    r = SR.run_ngspice(sub, name, p, cond["vdd"], x["vcm"], cond["cl"],
                       x.get("gbw_Hz"), dv=dv, rl=cond.get("rl"), keep_trace=True)
    r.update(case=os.path.basename(os.path.normpath(case)), key=key, variant=variant,
             pm_deg=x.get("pm_deg"), gbw_Hz=x.get("gbw_Hz"), process="sky130")
    tt, tv = r.pop("trace_t", None), r.pop("trace_v", None)
    json.dump(r, open(os.path.join(out, f"step_{variant}.json"), "w"), indent=1)
    if tt:
        with open(os.path.join(out, f"step_{variant}.csv"), "w") as fh:
            fh.write("t_s,vout_V\n")
            for a, b in zip(tt, tv):
                fh.write(f"{a},{b}\n")
    return r


if __name__ == "__main__":
    v = sys.argv[3] if len(sys.argv) > 3 else "rebiased"
    r = run(sys.argv[1], sys.argv[2], v)
    print(json.dumps({k: r.get(k) for k in ("pm_deg", "overshoot_pct", "settle_1pct_s",
                                            "ring_cycles", "decay_ratio", "final_err_V",
                                            "samples", "error")}, indent=1))
