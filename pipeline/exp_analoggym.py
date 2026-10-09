"""Experiment: does a schematic read from an image simulate like the real circuit?

For each AnalogGym amplifier with both a schematic image and a netlist:
  1. topology of the agent's record vs the answer netlist (exact match, NED)
  2. static checks on the agent's record
  3. sizes: AnalogGym images print none, so the answer's sizes are carried onto
     the agent's devices through the graph alignment. This isolates the effect
     of READING errors on performance: sizes are right by construction,
     only the connectivity can be wrong.
  4. both circuits through the same pipeline bench, AnalogGym conditions
     (1.8 V, VCM 0.45 V, CL 500 pF); input polarity chosen by the polarity check
  5. performance deltas; "equivalent" = gain within 1 dB, GBW within 10 %,
     PM within 5 deg, same stability class

Bodies: the reader omits them (the Virtuoso symbols do not show them), so
the reference is the answer netlist simulated with bodies on the rails as
well; the body effect of the real netlist is reported separately.
"""
import copy
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "vision_eval", "image2net"))
import ag_truth  # noqa: E402
import erc  # noqa: E402
import run_case  # noqa: E402
import score as S  # noqa: E402
import sim  # noqa: E402

CASE = os.path.join(HERE, "..", "cases", "analoggym")
NAMES = ["Fan_SMC", "HoiLee_AFFC", "Leung_DFCFC1", "Leung_DFCFC2", "Leung_NMCF", "Leung_NMCNR",
         "Peng_ACBC", "Peng_IAC", "Qu2017_AZC", "Ramos_PFC", "Sau_CFCC", "Song_DACFC",
         "Tan_CLIA", "Yan_AZ"]
VDD, VCM, CL = 1.8, 0.45, 500e-12
KEEP = ("converges", "follows", "gain_dB", "gbw_Hz", "pm_deg", "power_W", "n_sat", "n_mos", "stable")


def strip_body(c):
    c = copy.deepcopy(c)
    for d in c["ckt_netlist"]:
        d["port_connection"].pop("Body", None)
    return c


def carry_sizes(pred, truth):
    """Copy size/value from the aligned answer device; report what could not be."""
    pg, tg = S.graph(pred), S.graph(truth)
    _, m = S.best_mapping(pg, tg)
    out = copy.deepcopy(pred)
    unmatched = []
    for v, w in m.items():
        if v[0] != "d":
            continue
        d = out["ckt_netlist"][v[1]]
        t = truth["ckt_netlist"][w[1]] if w and w[0] == "d" else None
        if t is None or t["component_type"] != d["component_type"]:
            unmatched.append(d.get("id"))
            continue
        for k in ("size", "value"):
            if k in t:
                d[k] = copy.deepcopy(t[k])
    return out, unmatched


def equivalent(a, b):
    if not (a.get("converges") and b.get("converges")):
        return False
    if bool(a.get("stable")) != bool(b.get("stable")) or bool(a.get("follows")) != bool(b.get("follows")):
        return False
    ok = abs((a.get("gain_dB") or 0) - (b.get("gain_dB") or 0)) <= 1.0
    if a.get("gbw_Hz") and b.get("gbw_Hz"):
        ok &= abs(a["gbw_Hz"] - b["gbw_Hz"]) / b["gbw_Hz"] <= 0.10
        ok &= abs(a["pm_deg"] - b["pm_deg"]) <= 5.0
    else:
        ok &= a.get("gbw_Hz") == b.get("gbw_Hz")
    return bool(ok)


def one(name):
    rec = os.path.join(CASE, "records", f"{name}.json")
    if not os.path.exists(rec):
        return dict(name=name, status="no record")
    pred = json.load(open(rec))
    truth_b = ag_truth.record(name + "_Pin_3", with_body=True)
    truth = strip_body(truth_b)
    pg, tg = S.graph(pred), S.graph(truth)
    iso = S.nx.is_isomorphic(pg, tg, S.node_match, S.edge_match4iso)
    ged = 0 if iso else min(S.upper_bound(pg, tg), S.size(tg))
    row = dict(name=name, devices_true=len(truth["ckt_netlist"]), devices_read=len(pred["ckt_netlist"]),
               exact=iso, ged=ged, ged_lb=0 if iso else S.lower_bound(pg, tg),
               ned=ged / S.size(tg), erc=[f["code"] for f in erc.check(pred, need_sizes=False)])
    sized, unmatched = carry_sizes(pred, truth)
    row["unmatched_devices"] = unmatched
    ref_flip, ref, _ = run_case.pick(truth, "dut", {}, VDD, VCM, CL)
    body_flip, body, _ = run_case.pick(truth_b, "dut", {}, VDD, VCM, CL)
    got_flip, got, _ = run_case.pick(sized, "dut", {}, VDD, VCM, CL)
    row["reference"] = {k: ref.get(k) for k in KEEP}
    row["reference_with_body"] = {k: body.get(k) for k in KEEP}
    row["read"] = {k: got.get(k) for k in KEEP}
    # polarity: the reader lists inputs as [VINN, VINP]; flip=False keeps that
    row["polarity_check_agrees_with_labels"] = (got_flip is False)
    row["equivalent"] = equivalent(got, ref)
    json.dump(sized, open(os.path.join(CASE, "sized", f"{name}.json"), "w"), indent=1)
    return row


if __name__ == "__main__":
    os.makedirs(os.path.join(CASE, "sized"), exist_ok=True)
    names = sys.argv[1:] or NAMES
    with ThreadPoolExecutor(4) as ex:
        rows = list(ex.map(one, names))
    json.dump(rows, open(os.path.join(CASE, "results.json"), "w"), indent=1, default=str)
    for r in rows:
        if "exact" not in r:
            print(r)
            continue
        f = lambda x, k, s=1: (f"{x[k]/s:.3g}" if isinstance(x.get(k), (int, float)) else "-")
        print(f"{r['name']:13s} exact={str(r['exact']):5s} ned={r['ned']:.3f} erc={r['erc']} "
              f"equiv={r['equivalent']} | ref gain {f(r['reference'],'gain_dB')} gbw {f(r['reference'],'gbw_Hz',1e6)} "
              f"pm {f(r['reference'],'pm_deg')} | read gain {f(r['read'],'gain_dB')} gbw {f(r['read'],'gbw_Hz',1e6)} "
              f"pm {f(r['read'],'pm_deg')}")
