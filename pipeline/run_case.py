"""Paper case, end to end from the agent-written records to a verdict.

    run_case.py CASE_DIR [KEY ...]

CASE_DIR holds paper.pdf, records/<key>.json (blocks B+C, written by the
reading agent) and reported.json (claims with quotes). Nothing in here reads
a hand-made netlist. Output goes to CASE_DIR/out/<key>/.

For each circuit: schema -> static checks -> SPICE -> polarity -> as printed
-> re-biased -> compare -> level. Every value not taken from the paper is
listed as a deviation.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import circuit  # noqa: E402
import compare  # noqa: E402
import erc  # noqa: E402
import sim  # noqa: E402
import tospice  # noqa: E402

KEEP = ("converges", "vout", "follows", "n_sat", "n_mos", "not_saturated", "gain_dB",
        "gbw_Hz", "pm_deg", "power_W", "stable")


def pick(c, name, params, vdd, vcm, cl, rl=None):
    """Simulate both input assignments; the polarity check decides."""
    best = None
    for flip in (False, True):
        sub, _, _ = tospice.build(c, name, flip)
        p = {k: (v if v is not None else vdd / 2) for k, v in params.items()}
        r = sim.simulate(sub, name, p, vdd, vcm, cl, rl=rl)
        if best is None or sim.score(r) > sim.score(best[1]):
            best = (flip, r, sub)
    return best


def run(case, key, log=print):
    cfg = os.path.join(case, "case.json")
    sim.REGION = json.load(open(cfg)).get("region", "strong") if os.path.exists(cfg) else "strong"
    import time
    t0 = time.time()
    tm = {}
    out = os.path.join(case, "out", key)
    os.makedirs(out, exist_ok=True)
    c = circuit.load(os.path.join(case, "records", f"{key}.json"))
    res = dict(key=key, schema=circuit.schema_problems(c))
    if res["schema"]:
        res["level"] = "fails"
        return res
    found = erc.check(c)
    # bias terminals printed as symbols become searched bias sources (stated policy)
    floating = [f["message"].split()[1] for f in found if f["code"] == "FLOATING_GATE"]
    c, dev_bias, _ = circuit.bias_terminals(c, floating)
    if dev_bias:
        found = erc.check(c)
    res["erc"] = found
    tm["checks"] = time.time() - t0
    block = erc.blocking(found)
    cond = tospice.conditions(c)
    dev = list(dev_bias)
    vdd = cond["vdd"] or 1.8
    if cond["vdd"] is None:
        dev.append("supply not given on the figure; 1.8 V used")
    cl = cond["cl"]
    rl = cond.get("rl")
    if cl is None:
        cl = 10e-12
        dev.append("load capacitance not given; 10 pF used")
    name = "dut"
    _, params, dev_sp = tospice.build(c, name)
    dev += dev_sp
    printed = dict(params)
    for k, v in params.items():
        if v is None:
            dev.append(f"{k}: bias value not given (symbolic); searched")
    vcm_given = cond["vcm"]
    vcm0 = vcm_given if vcm_given is not None else vdd / 2
    res.update(conditions=dict(vdd=vdd, cl=cl, rl=rl, vcm_given=vcm_given), printed_biases=printed)

    if block:
        log(f"  {key}: static checks block simulation: {[f['code'] for f in block]}")
    # as printed: the paper's own bias values, in our process
    flip, r0, sub0 = pick(c, name, params, vdd, vcm0, cl, rl)
    tm["as_printed"] = time.time() - t0 - sum(tm.values())
    res["as_printed"] = {k: r0.get(k) for k in KEEP} | dict(flip=flip, vcm=vcm0)
    log(f"  {key} as printed: follows={r0.get('follows')} sat={r0.get('n_sat')}/{r0.get('n_mos')} "
        f"gain={r0.get('gain_dB')} pm={r0.get('pm_deg')}")

    # re-biased: bias sources (and VCM if not given) searched, sizes untouched
    best = None
    for fl in (False, True):
        sub, _, _ = tospice.build(c, name, fl)
        log(f"  {key} re-bias search, flip={fl}")
        p, vcm, r = sim.rebias(sub, name, params, vdd, vcm_given, cl,
                               search_vcm=vcm_given is None, log=log, rl=rl)
        if best is None or sim.score(r) > sim.score(best[3]):
            best = (fl, p, vcm, r, sub)
    fl, p, vcm, _, sub = best
    final = sim.simulate(sub, name, p, vdd, vcm, cl, ac=True, points=200, rl=rl)
    open(os.path.join(out, "dut.sp"), "w").write(sub)
    if final.get("bode"):
        f, mag, phd = final["bode"]
        with open(os.path.join(out, "bode.csv"), "w") as fh:
            fh.write("freq_Hz,mag_dB,phase_deg\n")
            for a, b, d in zip(f, mag, phd):
                fh.write(f"{a},{b},{d}\n")
    res["rebiased"] = {k: final.get(k) for k in KEEP} | dict(flip=fl, vcm=vcm, biases=p)
    for k, v in p.items():
        if printed.get(k) is not None and abs(printed[k] - v) > 1e-9:
            dev.append(f"{k}: printed {printed[k]:g} V, re-biased to {v:g} V for Sky130")
    if vcm_given is None:
        dev.append(f"input common mode not given; {vcm:g} V chosen by search")
    res["deviations"] = dev

    rep = json.load(open(os.path.join(case, "reported.json")))
    claims = compare.at_load(rep.get("circuits", {}).get(key, {}).get("claims", []), cl, rl)
    for tag in ("as_printed", "rebiased"):
        rows = compare.compare(res[tag], claims)
        res[tag]["compare"] = rows
        res[tag]["level"] = compare.LEVELS[compare.level(block, res[tag], rows)]
    res["inverting_input"] = (c["pins"]["in"][1] if fl else c["pins"]["in"][0]) \
        if isinstance(c["pins"]["in"], list) and len(c["pins"]["in"]) == 2 else None
    tm["rebias"] = time.time() - t0 - sum(tm.values())
    res["timing_s"] = tm
    json.dump(res, open(os.path.join(out, "result.json"), "w"), indent=1, default=str)
    log(f"  {key}: as printed -> {res['as_printed']['level']}, re-biased -> {res['rebiased']['level']}")
    return res


if __name__ == "__main__":
    case = sys.argv[1]
    rep_path = os.path.join(case, "reported.json")
    rep = json.load(open(rep_path))
    # tables printed as images are verified against a cell-wise OCR (ingest/table_ocr.py)
    tmap = os.path.join(case, "table_ocr.json")
    tocr = {cap: json.load(open(os.path.join(case, f))) for cap, f in json.load(open(tmap)).items()} \
        if os.path.exists(tmap) else None
    checked = compare.verify_quotes(rep, os.path.join(case, "paper.pdf"), tocr)
    json.dump(rep, open(os.path.join(case, "reported.verified.json"), "w"), indent=1)
    print(f"claims: {sum(x['quote_found'] for x in checked)}/{len(checked)} quotes found in the PDF")
    json.dump(rep, open(rep_path, "w"), indent=1)
    keys = sys.argv[2:] or sorted(k[:-5] for k in os.listdir(os.path.join(case, "records")) if k.endswith(".json"))
    for k in keys:
        run(case, k)
    allres = [json.load(open(os.path.join(case, "out", k, "result.json")))
              for k in sorted(d for d in os.listdir(os.path.join(case, "out"))
                              if os.path.exists(os.path.join(case, "out", d, "result.json")))]
    json.dump(allres, open(os.path.join(case, "out", "summary.json"), "w"), indent=1, default=str)
