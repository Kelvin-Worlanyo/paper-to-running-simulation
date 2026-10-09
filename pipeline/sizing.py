"""Block E, part 2: sizing by LLM-derived equations with one-shot calibration.

After Bujana & Karsilayan (arXiv 2604.07387). Each round:

  1. build_prompt   netlist + specs + constraint rules + (round >= 1) the
                    calibration table, predicted-vs-measured errors with
                    formulaic margin instructions, and the cumulative history
  2. LLM            a FRESH sub-agent writes compute_sizing() (round 0 also
                    initial_params(): muCox, a_gm, lambda, Vth per device)
  3. solve          the function is executed unmodified
  4. simulate       the pipeline bench (sim.py), same as every other result
  5. calibrate      per device, from one DC operating point:
                      muCox = 2 Id / ((W/L) Vov^2)
                      a_gm  = gm / (2 Id / Vov)
                      lambda = gds / Id
                      Vth    (as solved, incl. body effect)
                    plus triode flags and predicted-vs-measured

The LLM step is a Claude Code sub-agent launched by the orchestrator, so this
module is driven from the command line, one step at a time:

    sizing.py init  RUN_DIR           checks spec.json, writes round_0/prompt.md
    sizing.py dry   RUN_DIR ROUND     executes compute_sizing without simulating
    sizing.py step  RUN_DIR ROUND     solve -> simulate -> calibrate ->
                                      round_{N+1}/prompt.md, or CONVERGED/STOPPED

Addition for reproduction (not in the source method): spec.json splits the
paper's reported metrics into `fitted` targets, which drive sizing and
convergence, and `held_out` metrics, which are never shown to the LLM and are
only compared at the end. A metric fitted by sizing is not evidence of
reproduction.
"""
import copy
import importlib.util
import json
import math
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import circuit as CI  # noqa: E402
import compare  # noqa: E402
import sim  # noqa: E402
import tospice  # noqa: E402

MAX_ROUNDS = 8
W_RANGE, L_RANGE = (0.42e-6, 100e-6), (0.15e-6, 8e-6)      # Sky130 01v8 model bins
METRIC_UNIT = {"gain_dB": "dB", "gbw_Hz": "Hz", "pm_deg": "deg", "power_W": "W"}


# --------------------------------------------------------------------------- io
def jload(p):
    return json.load(open(p))


def jdump(obj, p):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(obj, open(p, "w"), indent=1, default=str)


def rdir(run, n):
    return os.path.join(run, f"round_{n}")


# ---------------------------------------------------------------- the netlist view
def netlist_text(rec, spec):
    """The circuit as the LLM sees it: devices, nets, roles, fixed or variable."""
    var = spec["variables"]
    free = set(var.get("devices", [])) | set(var.get("biases", [])) | \
        set(var.get("currents", [])) | set(var.get("caps", []))
    out = []
    p = rec["pins"]
    out.append(f"pins: vdd={p['vdd']} gnd={p['gnd']} out={p['out']} in={p['in']}")
    out.append(f"inverting input (decided by simulation): {spec.get('inverting_input', 'see pins')}")
    for d in rec["ckt_netlist"]:
        role = d.get("role", "core")
        if role in CI.HARNESS:
            continue
        pc = " ".join(f"{k}={v}" for k, v in d["port_connection"].items())
        if d["component_type"] in CI.MOS:
            s = d.get("size", {})
            val = "VARIABLE" if d["id"] in free else f"w={s.get('w')} l={s.get('l')} m={s.get('m', 1)} (fixed, printed)"
        else:
            val = "VARIABLE" if d["id"] in free else f"value={d.get('value')} (fixed, printed)"
        out.append(f"{d['id']:6s} {d['component_type']:8s} {role:5s} {pc:48s} {val}")
    return "\n".join(out)


RULES = """## Rules (apply them; do not restate them)

1. Structure your reasoning in seven sections, in order, BEFORE writing code:
   (1) Device roles  (2) Device constraints  (3) Signal path  (4) Design
   equations (gain, GBW, phase margin, power; symbolic)  (5) DC bias
   verification: show that every branch supports saturation, with numbers
   (6) DC operating-point consistency: show the voltage each stage produces is
   what the next stage needs, with explicit arithmetic  (7) Python code.
   Write sections (1)-(6) at the top of the file as a comment block.
2. Classify every variable transistor as MIRROR (W = Wref * Itarget/Iref *
   L/Lref, same L as its reference), MATCHED (copies its partner exactly) or
   INDEPENDENT (W = 2 Id L / (muCox Vov^2)). A mirror must use its reference's L.
3. Anti-circularity: compute every inter-stage node voltage from the driving
   stage's device parameters (e.g. V = VDD - |Vth,p| - Vov). Never assume a
   node voltage and then use it to justify itself.
4. Parasitics: large widths add gate and junction capacitance that lower GBW
   and phase margin. Prefer raising overdrive over widening devices when phase
   margin or GBW falls short.
5. Never write "self-adjusts" or "consistent by construction" without numbers.
6. Process: SkyWater Sky130, 1.8 V devices (sky130_fd_pr__nfet_01v8 /
   pfet_01v8). Allowed W 0.42-100 um, L 0.15-8 um per finger; use m > 1 for
   more width. Typical |Vth| is about 0.5-0.7 V (NMOS) and 0.9-1.0 V (PMOS)
   at L = 0.5 um, but trust calibrated values when given.
7. Do not change anything marked (fixed, printed). Size only VARIABLE items.
8. Bench: unity-gain feedback, DC loop through an ideal inductor, AC injected at
   the inverting input; gain = loop gain at 0.01 Hz, GBW = 0 dB crossing,
   PM = unwrapped phase margin, power = supply current x VDD.
"""

CONTRACT = """## Output contract

Write ONE Python file, `{path}`, standard library only (math allowed), with:

```python
def initial_params():          # required in round 0 only; ignored afterwards
    return {{"<device id>": {{"type": "NMOS"|"PMOS", "muCox": A_per_V2, "a_gm": float,
                              "lam": per_V, "vth": V}}, ...}}   # every MOS device

def compute_sizing(spec, params):
    # spec: the dict under "## Specification" below; params: per-device dict as above
    return {{
      "sizes":    {{"<device id>": {{"w": metres, "l": metres, "m": int}}, ...}},   # VARIABLE MOS only
      "biases":   {{"<source id>": volts, ...}},     # VARIABLE voltage sources only
      "currents": {{"<source id>": amps, ...}},      # VARIABLE current sources only
      "caps":     {{"<cap id>": farads, ...}},       # VARIABLE capacitors only
      "vcm": volts,                                # input common mode (if variable)
      "predicted": {{"gain_dB": .., "gbw_Hz": .., "pm_deg": .., "power_W": ..}},
    }}
```

Check that it executes before you finish:
`.venv/bin/python pipeline/sizing.py dry {run} {n}` must print OK. That command
does not simulate; do not run any simulation yourself.
"""


def rules(spec):
    """RULES with rule 6 (the process) taken from spec["process"]["rule"] when given."""
    rule = spec.get("process", {}).get("rule")
    if not rule:
        return RULES
    head, rest = RULES.split("6. Process:", 1)
    return head + "6. " + rule.strip() + "\n7." + rest.split("\n7.", 1)[1]


def build_prompt(run, n):
    spec = jload(os.path.join(run, "spec.json"))
    rec = jload(spec["record"])
    fitted = spec["fitted"]
    lines = [f"# Sizing round {n}: {spec['name']}", "",
             "You derive analytical design equations for an analog circuit and encode them as a",
             "Python sizing function. A script executes it unmodified, a simulator measures the",
             "result, and calibration data comes back in the next round (to a fresh session).",
             "Read only this prompt and the files it names. Do not open any other file.", "",
             "## Circuit (from the paper's figure; ids are the printed designators)", "```",
             netlist_text(rec, spec), "```", "",
             "## Specification", "```json",
             json.dumps({"targets": fitted, "tolerance": {k: compare.TOL[k] for k in fitted if k in compare.TOL},
                         "conditions": spec["conditions"],
                         "variables": spec["variables"],
                         "also_required": "every transistor saturated; unity-gain follower settles at vcm"},
                        indent=1), "```", "",
             "Targets are to be MET WITHIN TOLERANCE (not exceeded by as much as possible).", "",
             rules(spec)]
    if n == 0:
        lines += ["## Round 0", "Estimate initial_params() for every MOS device from your process knowledge,",
                  "then write compute_sizing().", ""]
    else:
        prev = rdir(run, n - 1)
        lines += ["## Previous sizing function (round %d)" % (n - 1), "```python",
                  open(os.path.join(prev, "compute_sizing.py")).read(), "```", ""]
        lines += [open(os.path.join(prev, "calibration.md")).read(), ""]
        lines += ["## This round",
                  "Do NOT re-estimate device parameters: compute_sizing() will be called with the",
                  "calibrated values above. Update compute_sizing() using the margin rules:",
                  "- linear metric (GBW, power) over-predicted by X%: design for (1 + X/100) x target",
                  "- gain over-predicted by Y dB: design for target + Y dB",
                  "- phase margin over-predicted by Z deg: design for target + Z deg",
                  "- if your predicted PM is catastrophically low but the measured PM passes, your PM",
                  "  equation is wrong: trust the measurement and do not distort sizing to fix it.",
                  "- any device flagged TRIODE is a bias-point failure: fix its headroom first.", ""]
    lines += [CONTRACT.format(path=os.path.join(rdir(run, n), "compute_sizing.py"), run=run, n=n)]
    os.makedirs(rdir(run, n), exist_ok=True)
    open(os.path.join(rdir(run, n), "prompt.md"), "w").write("\n".join(lines))
    return os.path.join(rdir(run, n), "prompt.md")


# --------------------------------------------------------------------------- solve
def _load(path):
    spec = importlib.util.spec_from_file_location("sizing_fn", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def solve(run, n, timeout=60):
    """Execute the LLM's function in a subprocess (it is untrusted code)."""
    spec_path = os.path.join(run, "spec.json")
    fn = os.path.join(rdir(run, n), "compute_sizing.py")
    calib = os.path.join(rdir(run, n - 1), "params.json") if n else None
    code = f"""
import json, importlib.util
s = importlib.util.spec_from_file_location("f", {fn!r}); m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
spec = json.load(open({spec_path!r}))
if {bool(n)!r}:
    p = json.load(open({os.path.join(run, "round_0", "initial_params.json")!r}))
    for dev, vals in json.load(open({calib!r})).items():
        p.setdefault(dev, {{}}).update({{k: v for k, v in vals.items() if v is not None}})
else:
    p = m.initial_params()
    json.dump(p, open({os.path.join(run, "round_0", "initial_params.json")!r}, "w"), indent=1)
view = dict(targets=spec["fitted"], conditions=spec["conditions"], variables=spec["variables"])
out = m.compute_sizing(view, p)
print(json.dumps(out))
"""
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        return None, r.stderr[-1500:]
    try:
        return json.loads(r.stdout.strip().splitlines()[-1]), None
    except Exception as e:
        return None, f"output is not JSON: {e}: {r.stdout[-500:]}"


def validate_solution(spec, rec, sol):
    bad = []
    var = spec["variables"]
    ids = {d["id"]: d for d in rec["ckt_netlist"]}
    for dev in var.get("devices", []):
        s = sol.get("sizes", {}).get(dev)
        if not s:
            bad.append(f"{dev}: no size returned")
            continue
        w, l, m = s.get("w"), s.get("l"), s.get("m", 1)
        if not all(isinstance(x, (int, float)) for x in (w, l, m)) or w <= 0 or l <= 0:
            bad.append(f"{dev}: invalid size {s}")
            continue
        wr, lr = spec.get("process", {}).get("w_range", W_RANGE), spec.get("process", {}).get("l_range", L_RANGE)
        if not (wr[0] <= w <= wr[1] and lr[0] <= l <= lr[1]):
            bad.append(f"{dev}: w={w:.3g} l={l:.3g} outside the process model range")
    for k, grp in (("biases", "biases"), ("currents", "currents"), ("caps", "caps")):
        for dev in var.get(grp, []):
            v = sol.get(k, {}).get(dev)
            if not isinstance(v, (int, float)):
                bad.append(f"{dev}: no numeric {k[:-1]} returned")
    for key, want in var.get("keep_printed", {}).items():
        dev, field = key.split(".")
        got = sol.get("sizes", {}).get(dev, {}).get(field)
        if got is None or abs(got - want) > 1e-3 * abs(want):
            bad.append(f"{key}: printed value {want} must be kept (got {got})")
    for dev in sol.get("sizes", {}):
        if dev not in var.get("devices", []):
            bad.append(f"{dev}: sized but not VARIABLE (fixed devices must not change)")
    if var.get("vcm") and not isinstance(sol.get("vcm"), (int, float)):
        bad.append("vcm not returned")
    if not isinstance(sol.get("predicted"), dict):
        bad.append("predicted metrics missing")
    return bad


def apply(rec, spec, sol):
    r = copy.deepcopy(rec)
    for d in r["ckt_netlist"]:
        i = d["id"]
        if i in sol.get("sizes", {}):
            s = sol["sizes"][i]
            d["size"] = dict(w=f"{s['w']:.6g}", l=f"{s['l']:.6g}", m=str(int(round(s.get('m', 1)))))
            d.setdefault("evidence", {})["size"] = "solved by sizing"
        for k in ("biases", "currents", "caps"):
            if i in sol.get(k, {}):
                d["value"] = f"{sol[k][i]:.6g}"
                d.setdefault("evidence", {})["value"] = "solved by sizing"
    return r


# ----------------------------------------------------------------------- calibrate
def calibrate(rec, res, flip):
    """Four parameters per MOS device from one DC operating point."""
    sizes = {d["id"].lower(): d for d in rec["ckt_netlist"] if d["component_type"] in CI.MOS}
    params, rows = {}, []
    for name, x in sorted(res.get("devices", {}).items()):
        d = sizes.get(name)
        if not d or not all(k in x for k in ("id", "vgs", "vth", "vds", "vdsat")):
            continue
        w, l = CI.value(d["size"]["w"]), CI.value(d["size"]["l"])
        m = int(CI.value(d["size"].get("m", 1)) or 1)
        idd, vov = abs(x["id"]), x["vgs"] - x["vth"]
        gm, gds = x.get("gm"), x.get("gds")
        region = "SAT" if (vov > -0.05 and x["vds"] > x["vdsat"]) else ("OFF" if vov <= -0.05 else "TRIODE")
        mucox = 2 * idd / ((m * w / l) * vov ** 2) if vov > 0.01 else None
        a_gm = gm / (2 * idd / vov) if (gm and vov > 0.01 and idd > 0) else None
        lam = gds / idd if (gds and idd > 0) else None
        params[d["id"]] = dict(type=d["component_type"], muCox=mucox, a_gm=a_gm, lam=lam, vth=x["vth"])
        rows.append((d["id"], d["component_type"], f"{w*1e6:.3g}/{l*1e6:.3g}x{m}", idd * 1e6, vov * 1e3,
                     x["vds"] * 1e3, (gm or 0) * 1e6, region, (mucox or 0) * 1e6, a_gm, lam, x["vth"] * 1e3))
    return params, rows


def calibration_md(rows, pred, meas, spec, history):
    L = ["## Calibration (one DC operating point, this round's sizing)", "",
         "| Dev | Type | W/L (um) x m | Id (uA) | Vov (mV) | Vds (mV) | gm (uS) | Region | muCox (uA/V2) | a_gm | lambda (1/V) | Vth (mV) |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        f = lambda v, fmt: (fmt.format(v) if isinstance(v, (int, float)) else "-")
        L.append(f"| {r[0]} | {r[1]} | {r[2]} | {r[3]:.3g} | {r[4]:.0f} | {r[5]:.0f} | {r[6]:.4g} | {r[7]} | "
                 f"{f(r[8], '{:.4g}')} | {f(r[9], '{:.3f}')} | {f(r[10], '{:.4g}')} | {r[11]:.0f} |")
    warn = [f"WARNING: {r[0]} in {r[7]} (Vds={r[5]:.0f} mV, Vov={r[4]:.0f} mV)" for r in rows if r[7] != "SAT"]
    L += [""] + (warn or ["All transistors saturated."]) + ["",
          "## Predicted vs measured (fitted targets)", "",
          "| Metric | Target | Predicted | Measured | Prediction error |", "|---|---|---|---|---|"]
    for k, t in spec["fitted"].items():
        p, m = pred.get(k), meas.get(k)
        if isinstance(p, (int, float)) and isinstance(m, (int, float)):
            err = f"{p - m:+.2f} {METRIC_UNIT[k]}" if k in ("gain_dB", "pm_deg") else f"{100 * (p - m) / m:+.1f} %"
        else:
            err = "-"
        L.append(f"| {k} | {t} | {p} | {m} | {err} |")
    L += ["", f"Follower settles at vcm: {meas.get('follows')}; saturated {meas.get('n_sat')}/{meas.get('n_mos')}.", "",
          "## History (all rounds so far)", "", "| Round | " + " | ".join(spec["fitted"]) + " | saturated |",
          "|---|" + "---|" * (len(spec["fitted"]) + 1)]
    for h in history:
        L.append(f"| {h['round']} | " + " | ".join(str(h['measured'].get(k)) for k in spec["fitted"]) +
                 f" | {h['measured'].get('n_sat')}/{h['measured'].get('n_mos')} |")
    return "\n".join(L)


def converged(spec, meas):
    if not (meas.get("follows") and meas.get("stable") and meas.get("n_mos")
            and meas.get("n_sat") == meas.get("n_mos")):
        return False
    for k, t in spec["fitted"].items():
        err, ok = compare.within(k, meas.get(k), t)
        if not ok:
            return False
    return True


# ---------------------------------------------------------------------------- step
KEEP = ("converges", "follows", "stable", "n_sat", "n_mos", "not_saturated", "gain_dB", "gbw_Hz", "pm_deg", "power_W")


def step(run, n):
    spec = jload(os.path.join(run, "spec.json"))
    rec = jload(spec["record"])
    d = rdir(run, n)
    history = jload(os.path.join(run, "history.json")) if os.path.exists(os.path.join(run, "history.json")) else []
    sol, err = solve(run, n)
    entry = dict(round=n)
    if sol is None:
        entry.update(status="solve_error", error=err, measured={})
    else:
        bad = validate_solution(spec, rec, sol)
        if bad:
            entry.update(status="invalid_solution", error=bad, measured={}, solution=sol)
        else:
            sized = apply(rec, spec, sol)
            jdump(sized, os.path.join(d, "record.json"))
            cond = spec["conditions"]
            vcm = sol.get("vcm") if spec["variables"].get("vcm") else cond["vcm"]
            flip = spec.get("flip", False)
            sub, params, _ = tospice.build(sized, "dut", flip)
            p = {k: (v if v is not None else cond["vdd"] / 2) for k, v in params.items()}
            res = sim.simulate(sub, "dut", p, cond["vdd"], vcm, cond["cl"], ac=True, points=100)
            meas = {k: res.get(k) for k in KEEP}
            cal, rows = calibrate(sized, res, flip)
            jdump(cal, os.path.join(d, "params.json"))
            entry.update(status="simulated", solution=sol, measured=meas, vcm=vcm, biases=p)
            if res.get("bode"):
                with open(os.path.join(d, "bode.csv"), "w") as fh:
                    fh.write("freq_Hz,mag_dB,phase_deg\n")
                    for a, b, c in zip(*res["bode"]):
                        fh.write(f"{a},{b},{c}\n")
            open(os.path.join(d, "dut.sp"), "w").write(sub)
    history.append(entry)
    jdump(history, os.path.join(run, "history.json"))
    if entry["status"] != "simulated":
        # a failed round still produces feedback: the error goes into the next prompt
        open(os.path.join(d, "calibration.md"), "w").write(
            f"## Round {n} did not simulate\n\nstatus: {entry['status']}\n\n```\n{entry['error']}\n```\n")
        if n == 0 or not os.path.exists(os.path.join(rdir(run, n - 1), "params.json")):
            status = "STOPPED" if n + 1 >= MAX_ROUNDS else "CONTINUE"
        else:
            import shutil
            shutil.copy(os.path.join(rdir(run, n - 1), "params.json"), os.path.join(d, "params.json"))
            status = "STOPPED" if n + 1 >= MAX_ROUNDS else "CONTINUE"
    else:
        md = calibration_md(rows, sol.get("predicted", {}), entry["measured"], spec,
                            [h for h in history if h.get("measured")])
        open(os.path.join(d, "calibration.md"), "w").write(md)
        status = "CONVERGED" if converged(spec, entry["measured"]) else \
            ("STOPPED" if n + 1 >= MAX_ROUNDS else "CONTINUE")
    if status == "CONTINUE":
        if n == 0 and not os.path.exists(os.path.join(d, "params.json")):
            # round 0 failed before calibration: fall back to the LLM's own estimates
            ip = os.path.join(run, "round_0", "initial_params.json")
            if os.path.exists(ip):
                import shutil
                shutil.copy(ip, os.path.join(d, "params.json"))
        build_prompt(run, n + 1)
    open(os.path.join(run, "STATUS"), "w").write(f"{status} after round {n}\n")
    return status, entry


def finalize(run):
    """Compare the best round with ALL reported metrics; fitted vs held-out kept apart."""
    spec = jload(os.path.join(run, "spec.json"))
    history = jload(os.path.join(run, "history.json"))
    sim_rounds = [h for h in history if h.get("status") == "simulated"]
    if not sim_rounds:
        out = dict(level="fails", rounds=len(history))
    else:
        best = next((h for h in sim_rounds if converged(spec, h["measured"])), sim_rounds[-1])
        rows = []
        for group in ("fitted", "held_out"):
            for k, v in spec.get(group, {}).items():
                err, ok = compare.within(k, best["measured"].get(k), v)
                rows.append(dict(group=group, metric=k, reported=v, simulated=best["measured"].get(k),
                                 error=err, within=ok))
        m = best["measured"]
        operates = bool(m.get("follows") and m.get("stable") and (m.get("gain_dB") or 0) > 20
                        and m.get("n_sat") == m.get("n_mos"))
        held = [r for r in rows if r["group"] == "held_out"]
        out = dict(converged=converged(spec, m), best_round=best["round"], simulations=len(sim_rounds),
                   rounds=len(history), measured=m, compare=rows, operates=operates,
                   held_out_within=sum(bool(r["within"]) for r in held), held_out_total=len(held))
    jdump(out, os.path.join(run, "final.json"))
    return out


if __name__ == "__main__":
    cmd, run = sys.argv[1], sys.argv[2]
    if cmd == "init":
        spec = jload(os.path.join(run, "spec.json"))
        rec = jload(spec["record"])
        for dev in spec["variables"].get("devices", []):
            assert any(d["id"] == dev for d in rec["ckt_netlist"]), dev
        print(build_prompt(run, 0))
    elif cmd == "dry":
        n = int(sys.argv[3])
        sol, err = solve(run, n)
        if sol is None:
            print("ERROR\n" + err)
            sys.exit(1)
        spec = jload(os.path.join(run, "spec.json"))
        bad = validate_solution(spec, jload(spec["record"]), sol)
        print("OK" if not bad else "INVALID\n" + "\n".join(bad))
        print(json.dumps(sol, indent=1)[:1500])
    elif cmd == "step":
        status, entry = step(run, int(sys.argv[3]))
        m = entry.get("measured", {})
        print(status, entry["status"], {k: m.get(k) for k in ("follows", "n_sat", "n_mos", "gain_dB", "gbw_Hz", "pm_deg", "power_W")},
              entry.get("error", "") if entry["status"] != "simulated" else "")
    elif cmd == "final":
        print(json.dumps(finalize(run), indent=1, default=str))
