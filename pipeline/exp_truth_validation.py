"""Validation of block E's record->SPICE path: AnalogGym answer netlists, converted
to circuit records and back to SPICE by the pipeline, against the independently
built bench (design/run_ag.py, which simulates AnalogGym's own netlist files)."""
import csv
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ag_truth  # noqa: E402
import sim  # noqa: E402
import tospice  # noqa: E402
from exp_analoggym import NAMES  # noqa: E402


def one(n):
    c = ag_truth.record(n + "_Pin_3", with_body=True)
    sub, params, _ = tospice.build(c, "dut")
    r = sim.simulate(sub, "dut", params, 1.8, 0.45, 500e-12, points=200)
    return n, {k: r.get(k) for k in ("converges", "follows", "gain_dB", "gbw_Hz", "pm_deg")}


if __name__ == "__main__":
    bench = {r["amp"].replace("_Pin_3", ""): r for r in
             csv.DictReader(open(os.path.join(HERE, "..", "design", "out", "ag", "compare.csv")))}
    rows = []
    with ThreadPoolExecutor(6) as ex:
        for n, r in ex.map(one, NAMES):
            b = bench.get(n)
            rows.append(dict(name=n, pipeline=r, bench=None if not b else dict(
                gain_dB=float(b["gain_dB"]), gbw_Hz=float(b["gbw_Hz"]), pm_deg=float(b["pm_deg"]))))
    json.dump(rows, open(os.path.join(HERE, "..", "cases", "analoggym", "truth_validation.json"), "w"), indent=1)
    for r in rows:
        print(r["name"], r["pipeline"].get("gain_dB"), r["bench"] and r["bench"]["gain_dB"])
