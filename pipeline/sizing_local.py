"""Option B: Bujana sizing with the process numbers kept on the local machine.

The LLM writes compute_sizing(spec, params) once, from public information only
(the paper's circuit, the targets, the rules): the same round-0 prompt as the
published method. After that, an INNER loop runs locally with no LLM:

    params -> compute_sizing -> simulate -> calibrate -> params -> ...

It stops when the fitted targets are met (converged), or when the numbers
stop helping (stalled: sizes settle, oscillate, or the inner budget runs out).
Only a stall costs another LLM call, and that prompt carries RELATIVE feedback
only: metric errors against the target and the prediction, and which devices
are out of saturation. Device parameters, currents and node voltages never
leave. `audit()` checks every outgoing prompt for any calibrated number.

    sizing_local.py init   RUN_DIR [SEED_ROUND0_DIR]   seed round 0 or write its prompt
    sizing_local.py inner  RUN_DIR K                   run the local loop for LLM round K
    sizing_local.py final  RUN_DIR

RUN_DIR/spec.json has the same format as sizing.py (fitted, held_out, ...).
"""
import copy
import json
import math
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import compare  # noqa: E402
import sizing as A  # noqa: E402  build_prompt pieces, validate, apply, calibrate
import sim  # noqa: E402
import tospice  # noqa: E402

INNER_MAX = 6          # local iterations per LLM round
LLM_MAX = 4            # LLM calls in total (round 0 included)
SETTLE = 0.01          # sizes/biases changing < 1 % = settled


def kdir(run, k):
    return os.path.join(run, f"llm_{k}")


# ------------------------------------------------------------------- execution
def run_fn(fn, spec, params, timeout=60):
    code = f"""
import json, importlib.util
s = importlib.util.spec_from_file_location("f", {fn!r}); m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
spec = json.loads({json.dumps(json.dumps(spec))})
p = json.loads({json.dumps(json.dumps(params))}) if {params is not None!r} else m.initial_params()
out = m.compute_sizing(dict(targets=spec["fitted"], conditions=spec["conditions"], variables=spec["variables"]), p)
print(json.dumps({{"params": p, "out": out}}))
"""
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        return None, None, r.stderr[-1200:]
    d = json.loads(r.stdout.strip().splitlines()[-1])
    return d["params"], d["out"], None


def vector(sol):
    """All design variables as one flat dict, for the settle / oscillation tests."""
    v = {}
    for dev, s in sol.get("sizes", {}).items():
        for f in ("w", "l"):
            v[f"{dev}.{f}"] = s[f]
    for k in ("biases", "currents", "caps"):
        for dev, x in sol.get(k, {}).items():
            v[f"{dev}"] = x
    if isinstance(sol.get("vcm"), (int, float)):
        v["vcm"] = sol["vcm"]
    return v


def change(a, b):
    ks = set(a) & set(b)
    return max((abs(a[k] - b[k]) / max(abs(b[k]), 1e-15) for k in ks), default=1.0)


def simulate(spec, rec, sol):
    sized = A.apply(rec, spec, sol)
    cond = spec["conditions"]
    vcm = sol.get("vcm") if spec["variables"].get("vcm") else cond["vcm"]
    sub, params, _ = tospice.build(sized, "dut", spec.get("flip", False))
    p = {k: (v if v is not None else cond["vdd"] / 2) for k, v in params.items()}
    res = sim.simulate(sub, "dut", p, cond["vdd"], vcm, cond["cl"], ac=True, points=100)
    return sized, res, sub


def merge_params(old, cal, rows):
    """Local update: take calibrated values only from saturated devices (an OFF or
    triode operating point gives meaningless square-law parameters), and move
    only halfway toward them (undamped updates see-saw: measured 53 -> 8 dB)."""
    sat = {r[0] for r in rows if r[7] == "SAT"}
    new = copy.deepcopy(old)
    for dev, vals in cal.items():
        if dev not in sat:
            continue
        cur = new.setdefault(dev, {})
        for k, v in vals.items():
            if v is None or k == "type":
                continue
            o = cur.get(k)
            if not isinstance(o, (int, float)):
                cur[k] = v
            elif k == "vth":
                cur[k] = 0.5 * (o + v)                       # damped: halfway
            elif o > 0 and v > 0:
                cur[k] = math.sqrt(o * v)                    # damped: geometric halfway
            else:
                cur[k] = v
    return new


# ----------------------------------------------------------------- inner loop
def inner(run, k):
    spec = A.jload(os.path.join(run, "spec.json"))
    rec = A.jload(spec["record"])
    d = kdir(run, k)
    fn = os.path.join(d, "compute_sizing.py")
    state_p = os.path.join(run, "state.json")
    state = A.jload(state_p) if os.path.exists(state_p) else dict(params=None, sims=0, llm_calls=0, log=[])
    state["llm_calls"] = k + 1
    params = state["params"]
    prev_vec, vecs, last = None, [], None
    best, best_params, worse = None, params, 0
    for it in range(INNER_MAX):
        p_used, sol, err = run_fn(fn, spec, params)
        if sol is None:
            last = dict(k=k, it=it, status="solve_error", error=err)
            state["log"].append(last)
            break
        if params is None:
            params = p_used                      # the LLM's round-0 estimates, kept locally
        bad = A.validate_solution(spec, rec, sol)
        if bad:
            last = dict(k=k, it=it, status="invalid_solution", error=bad, solution=sol)
            state["log"].append(last)
            break
        sized, res, sub = simulate(spec, rec, sol)
        state["sims"] += 1
        meas = {x: res.get(x) for x in A.KEEP}
        cal, rows = A.calibrate(sized, res, spec.get("flip", False))
        # everything measured by simulation is confidential: calibrated parameters
        # and the raw operating point (Id, Vov, Vds, gm, Vth per device)
        sec = state.setdefault("secrets", [])
        for v in cal.values():
            sec += [x for x in (v.get("muCox"), v.get("a_gm"), v.get("lam"), v.get("vth")) if isinstance(x, (int, float))]
        for r in rows:
            sec += [r[3] * 1e-6, r[4] * 1e-3, r[5] * 1e-3, r[6] * 1e-6, r[11] * 1e-3]
        last = dict(k=k, it=it, sim=state["sims"], status="simulated", measured=meas,
                    predicted=sol.get("predicted", {}), solution=sol,
                    regions={r[0]: r[7] for r in rows})
        state["log"].append(last)
        A.jdump(sized, os.path.join(d, f"record_it{it}.json"))
        open(os.path.join(d, f"dut_it{it}.sp"), "w").write(sub)
        if res.get("bode"):
            with open(os.path.join(d, f"bode_it{it}.csv"), "w") as fh:
                fh.write("freq_Hz,mag_dB,phase_deg\n")
                for a, b, c in zip(*res["bode"]):
                    fh.write(f"{a},{b},{c}\n")
        new_params = merge_params(params, cal, rows)
        if best is None or sim.score(res) > best[0]:
            best, best_params, worse = (sim.score(res), len(state["log"]) - 1), new_params, 0
        else:
            worse += 1
        if A.converged(spec, meas):
            state.update(params=new_params, status="CONVERGED", best_entry=len(state["log"]) - 1)
            break
        if worse >= 2:
            state.update(params=best_params, status="STALLED_DIVERGING", best_entry=best[1])
            break
        params = new_params
        vec = vector(sol)
        if prev_vec is not None and change(vec, prev_vec) < SETTLE:
            state.update(params=best_params, status="STALLED_SETTLED", best_entry=best[1])
            break
        if any(change(vec, v) < SETTLE for v in vecs[:-1]):
            state.update(params=best_params, status="STALLED_OSCILLATING", best_entry=best[1])
            break
        vecs.append(vec)
        prev_vec = vec
    else:
        state.update(params=best_params, status="STALLED_BUDGET", best_entry=best[1] if best else None)
    if last and last["status"] != "simulated":
        state.update(params=params, status="LLM_ERROR")
    A.jdump(state, state_p)          # local only: holds the calibrated parameters
    if state["status"] != "CONVERGED" and k + 1 < LLM_MAX:
        build_prompt(run, k + 1, state)
        state["next"] = "LLM"
    elif state["status"] != "CONVERGED":
        state["next"] = "STOP"
    A.jdump(state, state_p)
    return state


# ------------------------------------------------------ relative-feedback prompt
def feedback_md(spec, state):
    """What the LLM may see: metric errors and region flags. No device numbers."""
    sims = [e for e in state["log"] if e["status"] == "simulated"]
    L = ["## Result of your previous function (relative feedback only)", "",
         "Your function was run by local code, which also re-fitted the device",
         "parameters it receives from simulation and re-ran it "
         f"{len([e for e in sims if e['k'] == sims[-1]['k']]) if sims else 0} time(s).",
         "Device parameters, currents and node voltages are confidential and are not shown;",
         "only errors relative to your targets and predictions are.",
         f"Local outcome: {state['status'].replace('_', ' ').lower()}. The best design of that",
         "local run is reported below.", ""]
    if not sims:
        errs = [e for e in state["log"] if e["status"] != "simulated"]
        L += ["The function did not produce a simulatable design:", "```", str(errs[-1].get("error"))[:1200], "```"]
        return "\n".join(L)
    be = state.get("best_entry")
    e = state["log"][be] if isinstance(be, int) and state["log"][be]["status"] == "simulated" else sims[-1]
    m, p = e["measured"], e["predicted"]
    L += ["| Metric | vs target | vs your prediction |", "|---|---|---|"]
    for k, t in spec["fitted"].items():
        mv, pv = m.get(k), p.get(k)
        if mv is None:
            L.append(f"| {k} | not measurable (no unity-gain crossing / no operating point) | - |")
            continue
        if k in ("gain_dB", "pm_deg"):
            u = "dB" if k == "gain_dB" else "deg"
            vt = f"{mv - t:+.1f} {u}"
            vp = f"{mv - pv:+.1f} {u}" if isinstance(pv, (int, float)) else "-"
        else:
            vt = f"{100 * (mv - t) / t:+.0f} %"
            vp = f"{100 * (mv - pv) / pv:+.0f} %" if isinstance(pv, (int, float)) and pv else "-"
        ok = compare.within(k, mv, t)[1]
        L.append(f"| {k} | {vt} ({'within' if ok else 'outside'} tolerance) | {vp} |")
    off = sorted(d for d, r in e["regions"].items() if r != "SAT")
    offs = ", ".join(f"{d} ({e['regions'][d].lower()})" for d in off) or "none"
    L += ["", f"Follower settles at the input common mode: {bool(m.get('follows'))}.",
          f"Transistors not saturated: {offs}.",
          "", "Rows are measured minus target / measured minus predicted."]
    return "\n".join(L)


def build_prompt(run, k, state):
    """A's prompt skeleton with the calibration section replaced by relative feedback."""
    spec = A.jload(os.path.join(run, "spec.json"))
    rec = A.jload(spec["record"])
    prev_fn = open(os.path.join(kdir(run, k - 1), "compute_sizing.py")).read()
    lines = [f"# Sizing, LLM round {k}: {spec['name']}", "",
             "You derive analytical design equations for an analog circuit and encode them as a",
             "Python sizing function. Local code runs it with device parameters it measures itself",
             "and never shows you; you see only how far the results are from the targets.",
             "Read only this prompt and the files it names. Do not open any other file.", "",
             "## Circuit", "```", A.netlist_text(rec, spec), "```", "",
             "## Specification", "```json",
             json.dumps({"targets": spec["fitted"],
                         "tolerance": {x: compare.TOL[x] for x in spec["fitted"] if x in compare.TOL},
                         "conditions": spec["conditions"], "variables": spec["variables"],
                         "also_required": "every transistor saturated; unity-gain follower settles at vcm"},
                        indent=1), "```", "",
             A.rules(spec),
             "## Your previous function", "```python", prev_fn, "```", "",
             feedback_md(spec, state), "",
             "## This round",
             "The parameters your function receives are already fitted to simulation, so a",
             "remaining error comes from the EQUATIONS or the DESIGN STRATEGY, not from numbers.",
             "Revise the structure: missing poles or zeros, wrong gain expression, headroom",
             "allocation, which device sets which current. Keep initial_params() (it is only",
             "used if local fitting has no data for a device).",
             "", A.CONTRACT.format(path=os.path.join(kdir(run, k), "compute_sizing.py"), run=run, n=k)
             .replace("pipeline/sizing.py dry", "pipeline/sizing_local.py dry")]
    os.makedirs(kdir(run, k), exist_ok=True)
    text = "\n".join(lines)
    open(os.path.join(kdir(run, k), "prompt.md"), "w").write(text)
    # the feedback section is the only channel through which simulation data can
    # reach the prompt (the previous function was written without seeing any)
    leaks = audit(feedback_md(spec, state), state)
    A.jdump(leaks, os.path.join(kdir(run, k), "leak_audit.json"))
    return text


# ------------------------------------------------------------------------ audit
def audit(text, state):
    """Every number that came out of simulation (calibrated parameters and the
    raw operating point), in the formats a prompt could plausibly carry, must be
    absent from `text`. The LLM's own guesses are not secrets: it wrote them."""
    secrets = set()
    for x in state.get("secrets", []):      # simulation-derived values only
        if isinstance(x, (int, float)) and x:
            for f in (f"{x:.3g}", f"{x:.4g}", f"{x * 1e6:.3g}", f"{x * 1e3:.0f}", f"{x * 1e6:.0f}"):
                if len(f.replace("-", "").replace(".", "").lstrip("0")) >= 3:
                    secrets.add(f)
    nums = set(re.findall(r"-?\d+\.?\d*(?:e-?\d+)?", text))
    hits = sorted(s for s in secrets if s in nums)
    return dict(checked=len(secrets), leaked=hits)


# ------------------------------------------------------------------- dry + final
def dry(run, k):
    spec = A.jload(os.path.join(run, "spec.json"))
    state_p = os.path.join(run, "state.json")
    params = A.jload(state_p)["params"] if os.path.exists(state_p) else None
    _, sol, err = run_fn(os.path.join(kdir(run, k), "compute_sizing.py"), spec, params)
    if sol is None:
        print("ERROR\n" + err)
        sys.exit(1)
    bad = A.validate_solution(spec, A.jload(spec["record"]), sol)
    print("OK" if not bad else "INVALID\n" + "\n".join(bad))


def final(run):
    spec = A.jload(os.path.join(run, "spec.json"))
    state = A.jload(os.path.join(run, "state.json"))
    sims = [e for e in state["log"] if e["status"] == "simulated"]
    best = next((e for e in sims if A.converged(spec, e["measured"])), None) or \
        (max(sims, key=lambda e: sim.score({**e["measured"], "converges": True})) if sims else None)
    rows = []
    if best:
        for group in ("fitted", "held_out"):
            for k, v in spec.get(group, {}).items():
                err, ok = compare.within(k, best["measured"].get(k), v)
                rows.append(dict(group=group, metric=k, reported=v, simulated=best["measured"].get(k),
                                 error=err, within=ok))
    audits = [A.jload(os.path.join(run, x, "leak_audit.json")) for x in sorted(os.listdir(run))
              if x.startswith("llm_") and os.path.exists(os.path.join(run, x, "leak_audit.json"))]
    out = dict(mode="B", converged=state.get("status") == "CONVERGED", llm_calls=state["llm_calls"],
               simulations=state["sims"], best=best and dict(k=best["k"], it=best["it"], sim=best["sim"]),
               measured=best and best["measured"], compare=rows,
               leak_audit=dict(prompts=len(audits), numbers_checked=sum(a["checked"] for a in audits),
                               leaked=sum(len(a["leaked"]) for a in audits)))
    A.jdump(out, os.path.join(run, "final.json"))
    return out


# the PDK path: PR_BACKEND=spectre swaps in the Spectre backend (run on the server,
# where the models are; operating-point data stays there with state.json)
if os.environ.get("PR_BACKEND") == "spectre":
    sys.path.insert(0, os.path.join(HERE, "cadence"))
    import spectre_backend  # noqa: E402
    simulate = spectre_backend.simulate


if __name__ == "__main__":
    cmd, run = sys.argv[1], sys.argv[2]
    if cmd == "init":
        seed = sys.argv[3] if len(sys.argv) > 3 else None
        os.makedirs(kdir(run, 0), exist_ok=True)
        if seed:
            shutil.copy(os.path.join(seed, "compute_sizing.py"), os.path.join(kdir(run, 0), "compute_sizing.py"))
            shutil.copy(os.path.join(seed, "prompt.md"), os.path.join(kdir(run, 0), "prompt.md"))
            print("seeded round 0 from", seed)
        else:
            print(A.build_prompt(run, 0))
    elif cmd == "inner":
        s = inner(run, int(sys.argv[3]))
        e = [x for x in s["log"] if x["status"] == "simulated"]
        m = e[-1]["measured"] if e else {}
        print(s["status"], "next:", s.get("next"), "sims:", s["sims"],
              {x: m.get(x) for x in ("follows", "n_sat", "n_mos", "gain_dB", "gbw_Hz", "pm_deg", "power_W")})
    elif cmd == "dry":
        dry(run, int(sys.argv[3]))
    elif cmd == "final":
        print(json.dumps(final(run), indent=1, default=str))
