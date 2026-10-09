"""Steps 3-4 of the case study on the PDK back end (runs on the PDK machine).

The same procedure as pipeline/run_case.py, with the foundry simulator in place
of ngspice: static checks, both input assignments (the operating point picks the
polarity), the paper's values as printed, then a multi-start coordinate search
over bias sources and the input common mode that never changes a size, then the
comparison with the verified claims and the ladder level. Unprinted sizes follow
the same stated policy (median width of the same device type).

    python3 case_pdk.py JOB.json    -> prints RESULT {...} (circuit metrics only)

JOB.json: {"record": path, "claims": [...], "key": name}
"""
import copy
import json
import os
import random
import statistics
import sys
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import circuit as CI  # noqa: E402
import compare  # noqa: E402
import erc  # noqa: E402
import sim  # noqa: E402  score(), violation()
import spectre_backend as SB  # noqa: E402
import tospice  # noqa: E402

KEEP = ("converges", "vout", "follows", "n_sat", "n_mos", "not_saturated", "gain_dB",
        "gbw_Hz", "pm_deg", "power_W", "stable")
THREADS = 4


def fill_sizes(c, dev):
    """Stated policy for sizes the figure does not print: median of the same type."""
    known = {t: [(CI.value((d.get("size") or {}).get("w")), CI.value((d.get("size") or {}).get("l")))
                 for d in c["ckt_netlist"] if d["component_type"] == t] for t in CI.MOS}
    for d in c["ckt_netlist"]:
        t = d["component_type"]
        if t not in CI.MOS or d.get("role", "core") in CI.HARNESS:
            continue
        s = d.setdefault("size", {})
        if CI.value(s.get("w")) is None:
            w = statistics.median([x for x, _ in known[t] if x] or [1e-6])
            s["w"] = f"{w:.6g}"
            dev.append(f"{d['id']}: W not given; median {t} width {w * 1e6:g} um used")
        if CI.value(s.get("l")) is None:
            l = statistics.median([y for _, y in known[t] if y] or [0.5e-6])
            s["l"] = f"{l:.6g}"
            dev.append(f"{d['id']}: L not given; median {t} length {l * 1e6:g} um used")
        s.setdefault("m", "1")


def with_biases(c, biases):
    r = copy.deepcopy(c)
    for d in r["ckt_netlist"]:
        if d["id"] in biases:
            d["value"] = f"{biases[d['id']]:.6g}"
    return r


def simulate(c, biases, inv, vdd, vcm, cl, bode=False, rl=None):
    spec = dict(conditions=dict(vdd=vdd, cl=cl, vcm=vcm, rl=rl), inverting_input=inv)
    _, deck = SB.netlist(with_biases(c, biases), spec, vcm)
    r, tmp = SB.run_deck(deck, vcm, vdd)
    SB.shutil.rmtree(tmp, ignore_errors=True)
    if not bode:
        r.pop("bode", None)
    return r


def rebias(c, biases, inv, vdd, vcm_given, cl, sweeps=3, starts=6, seed=1, rl=None):
    """Same search as sim.rebias: printed start (out-of-range clipped to VDD/2), all
    at VDD/2, then random starts; coordinate sweeps over a 0.1 V grid."""
    rng = random.Random(seed)
    grid = sim.bias_grid(vdd)
    search_vcm = vcm_given is None
    keys = list(biases) + (["VCM"] if search_vcm else [])
    printed = {k: (v if v is not None and 0 < v < vdd else vdd / 2) for k, v in biases.items()}
    v0 = vcm_given if vcm_given is not None else vdd / 2
    inits = [(printed, v0), ({k: vdd / 2 for k in biases}, v0)]
    for _ in range(starts):
        inits.append(({k: rng.choice(grid) for k in biases}, rng.choice(grid) if search_vcm else v0))
    overall, nsim = None, 0
    for n, (cur, cur_vcm) in enumerate(inits):
        cur = dict(cur)
        best = simulate(c, cur, inv, vdd, cur_vcm, cl, rl=rl)
        nsim += 1
        for _ in range(sweeps):
            changed = False
            for k in keys:
                def trial(x):
                    p, v = dict(cur), cur_vcm
                    if k == "VCM":
                        v = x
                    else:
                        p[k] = x
                    return x, simulate(c, p, inv, vdd, v, cl, rl=rl)
                with ThreadPoolExecutor(THREADS) as ex:
                    results = list(ex.map(trial, grid))
                nsim += len(grid)
                x, r = max(results, key=lambda t: sim.score(t[1]))
                if sim.score(r) > sim.score(best):
                    best, changed = r, True
                    if k == "VCM":
                        cur_vcm = x
                    else:
                        cur[k] = x
            if not changed:
                break
        if overall is None or sim.score(best) > sim.score(overall[2]):
            overall = (dict(cur), cur_vcm, best)
        if sim.score(best)[0] and best.get("n_sat") == best.get("n_mos") and n >= 1:
            break
    return overall + (nsim,)


def run(job):
    sim.REGION = job.get("region", "strong")
    import time
    t0 = time.time()
    tm = {}
    c = json.load(open(job["record"]))
    dev = []
    found = erc.check(c)
    floating = [f["message"].split()[1] for f in found if f["code"] == "FLOATING_GATE"]
    c, dev_bias, _ = CI.bias_terminals(c, floating)
    if dev_bias:
        dev += dev_bias
        found = erc.check(c)
    block = erc.blocking(found)
    cond = tospice.conditions(c)
    vdd = cond["vdd"] or 1.8
    if cond["vdd"] is None:
        dev.append("supply not given on the figure; 1.8 V used")
    cl = cond["cl"]
    rl = cond.get("rl")
    if cl is None:
        cl = 10e-12
        dev.append("load capacitance not given; 10 pF used")
    fill_sizes(c, dev)
    biases = {d["id"]: CI.value(d.get("value")) for d in c["ckt_netlist"]
              if d["component_type"] == "Voltage" and d.get("role") == "bias"}
    for k, v in biases.items():
        if v is None:
            dev.append(f"{k}: bias value not given (symbolic); searched")
    vcm_given = cond["vcm"]
    vcm0 = vcm_given if vcm_given is not None else vdd / 2
    ins = c["pins"]["in"]
    res = dict(key=job["key"], conditions=dict(vdd=vdd, cl=cl, rl=rl, vcm_given=vcm_given), printed_biases=biases,
               erc=[f["code"] for f in found])

    # as printed: both input assignments, the operating point decides
    p0 = {k: (v if v is not None else vdd / 2) for k, v in biases.items()}
    best = max(((inv, simulate(c, p0, inv, vdd, vcm0, cl, rl=rl)) for inv in ins), key=lambda t: sim.score(t[1]))
    tm["as_printed"] = time.time() - t0
    res["as_printed"] = dict({k: best[1].get(k) for k in KEEP}, inverting_input=best[0], vcm=vcm0)

    # re-biased: sizes untouched
    cand = []
    for inv in ins:
        p, vcm, r, nsim = rebias(c, biases, inv, vdd, vcm_given, cl, rl=rl)
        cand.append((inv, p, vcm, r, nsim))
    inv, p, vcm, _, _ = max(cand, key=lambda t: sim.score(t[3]))
    final = simulate(c, p, inv, vdd, vcm, cl, bode=True, rl=rl)
    res["rebiased"] = dict({k: final.get(k) for k in KEEP}, inverting_input=inv, vcm=vcm, biases=p)
    if final.get("bode"):
        f, mag, ph = final["bode"]
        res["rebiased"]["bode"] = [f[::5], mag[::5], ph[::5]]
    res["search_simulations"] = sum(t[4] for t in cand)
    for k, v in p.items():
        if biases.get(k) is not None and abs(biases[k] - v) > 1e-9:
            dev.append(f"{k}: printed {biases[k]:g} V, re-biased to {v:g} V")
    if vcm_given is None:
        dev.append(f"input common mode not given; {vcm:g} V chosen by search")
    res["deviations"] = dev
    for tag in ("as_printed", "rebiased"):
        rows = compare.compare(res[tag], compare.at_load(job["claims"], cl, rl))
        res[tag]["compare"] = rows
        res[tag]["level"] = compare.LEVELS[compare.level(block, res[tag], rows)]
    tm["rebias"] = time.time() - t0 - sum(tm.values())
    res["timing_s"] = tm
    return res


if __name__ == "__main__":
    print("RESULT " + json.dumps(run(json.load(open(sys.argv[1]))), default=str))
