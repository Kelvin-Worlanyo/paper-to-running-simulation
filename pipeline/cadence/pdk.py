"""PDK back end driver: runs the pipeline's steps 3-5 in the designer's own
Cadence installation.

Everything installation-specific comes from a private config
(~/.config/analog_repro/pdk.json, or $PR_PDK_CONFIG; see pdk_config.example.json):
the machine, the working directory, a reference schematic that uses the PDK's
transistors, a testbench that already simulates with the PDK, and an empty
target library attached to the PDK technology. Nothing PDK-specific is stored in
this repository or printed: device masters are known only by aliases (N1, P1),
and every line shown is redacted of paths.

    pdk.py init                          push config + code to the private directory
    pdk.py devmap                        device map from the reference schematic
    pdk.py setup                         model setup + default geometry (probe cell)
    pdk.py place RECORD CELL [--spec S] [--sizes Z] [--set ID=VALUE ...]
                                         draw the record + standard testbench in the
                                         live session and check the connections
    pdk.py sim CELL                      netlist CELL_TB, simulate, print metrics
    pdk.py record SPEC                   simulate a record directly (no schematic)
    pdk.py size init|inner|final RUN [K] Option B sizing, loop on the PDK machine
    pdk.py case CASE_DIR KEY             steps 3-4 of a case on the PDK (as printed,
                                         re-biased, compared) -> CASE_DIR/out_pdk/KEY
"""
import argparse
import json
import os
import re
import shlex
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(HERE, ".."))
import circuit as CI  # noqa: E402
import sizing as A  # noqa: E402

CODE = ["pipeline/sizing_local.py", "pipeline/sizing.py", "pipeline/circuit.py", "pipeline/compare.py",
        "pipeline/tospice.py", "pipeline/sim.py", "pipeline/erc.py", "design/run.py",
        "pipeline/cadence/spectre_backend.py", "pipeline/cadence/run_sizing.py", "pipeline/cadence/case_pdk.py"]
SKILL = ["pr_common.il", "pr_batch.il", "place_record.il", "devmap_extract.il"]


# ------------------------------------------------------------------ plumbing
def cfg():
    p = os.environ.get("PR_PDK_CONFIG") or os.path.expanduser("~/.config/analog_repro/pdk.json")
    if not os.path.exists(p):
        raise SystemExit(f"no config at {p}: copy pipeline/cadence/pdk_config.example.json there and fill it in")
    return json.load(open(p))


def redact(text):
    return re.sub(r"(?<![\w.])/[^\s\"'()<>]+", "<PATH>", text)


def ssh(script, check=True):
    c = cfg()
    r = subprocess.run(["ssh", "-o", "BatchMode=yes", c["ssh_host"], "sh", "-s"], input=script,
                       capture_output=True, text=True)
    if check and r.returncode != 0:
        raise SystemExit("remote step failed:\n" + redact(r.stderr[-1500:]))
    return r.stdout


def scp(local, remote):
    subprocess.run(["scp", "-q", local, f"{cfg()['ssh_host']}:{remote}"], check=True)


def skill_str(x):
    """Python value -> SKILL literal (dict = property list, keys as symbols)."""
    if isinstance(x, dict):
        return "(nil " + " ".join(f"{k} {skill_str(v)}" for k, v in x.items()) + ")"
    if isinstance(x, (list, tuple)):
        return "(" + " ".join(skill_str(v) for v in x) + ")"
    if isinstance(x, bool) or x is None:
        return "t" if x else "nil"
    if isinstance(x, (int, float)):
        return repr(float(x))
    return json.dumps(str(x))


def eng(x):
    """1.5e-06 -> '1.5u' (the form CDF fields expect)."""
    if x == 0:
        return "0"
    for s, f in (("T", 1e12), ("G", 1e9), ("M", 1e6), ("k", 1e3), ("", 1.0), ("m", 1e-3), ("u", 1e-6),
                 ("n", 1e-9), ("p", 1e-12), ("f", 1e-15), ("a", 1e-18)):
        if abs(x) >= f * 0.9995:
            return f"{x / f:.4g}{s}"
    return f"{x:.4g}"


def push_skill():
    c = cfg()
    for f in SKILL:
        scp(os.path.join(HERE, f), f"{c['remote_tmp']}_{f}")


def batch(body, tag):
    """Run SKILL in batch Virtuoso after the config and helpers; show PR:/DEVMAP: lines."""
    c = cfg()
    push_skill()
    t, priv = c["remote_tmp"], c["private_dir"]
    loads = "".join(f'load("{t}_{f}")\n' for f in ("pr_common.il", "pr_batch.il"))
    replay = f'load("{priv}/pr_config.il")\n{loads}{body}\nexit()\n'
    out = ssh(f"""set -e
cat > {t}_{tag}.il <<'EOF_R'
{replay}
EOF_R
mkdir -p -m 700 {priv}/logs
tcsh -c {shlex.quote(f"{c['shell_init']}; cd {c['work_dir']}; virtuoso -nograph -replay {t}_{tag}.il -log {priv}/logs/{tag}.log")} > /dev/null 2>&1 || true
grep -E '^.o (PR|DEVMAP):' {priv}/logs/{tag}.log | grep -v printf | sed 's/^.o //'
echo "(log error lines: $(grep -c '[*]Error[*]' {priv}/logs/{tag}.log))"
chmod -R go-rwx {priv}
""")
    print(redact(out).rstrip())
    return out


def gui(expr):
    """Evaluate SKILL in the live session (virtuoso-bridge), after config + helpers."""
    c = cfg()
    push_skill()
    t, priv = c["remote_tmp"], c["private_dir"]
    loads = " ".join(f'load("{t}_{f}")' for f in ("pr_common.il", "place_record.il"))
    code = f'load("{priv}/pr_config.il") {loads} let((r) r=errset({expr} t) if(r car(r) list("ERR" errset.errset)))'
    r = subprocess.run([c["bridge"], "eval", "--timeout", "600", "--stdin"], input=code,
                       capture_output=True, text=True)
    try:
        out = json.loads(r.stdout[r.stdout.index("{"):])["output"]
    except (ValueError, KeyError):
        out = r.stdout + r.stderr
    return redact(out)


def remote_py(args, cwd_code=True):
    c = cfg()
    return ssh(f"cd {c['private_dir']}/code && python3 {args}\n")


# ------------------------------------------------------------------ commands
def init():
    c = cfg()
    priv = c["private_dir"]
    ssh(f"mkdir -p -m 700 {priv} {priv}/code/pipeline/cadence {priv}/code/design {priv}/runs\n")
    il = ("PR_CFG = '" + skill_str(dict(work_dir=c["work_dir"], private_dir=priv,
                                         ref_lib=c["reference_cell"]["lib"], ref_cell=c["reference_cell"]["cell"],
                                         tb_lib=c["source_testbench"]["lib"], tb_cell=c["source_testbench"]["cell"],
                                         target_lib=c["target_library"], technology=c["technology"])) + "\n")
    tmp = os.path.join(os.path.expanduser("~/.config/analog_repro"), "pr_config.il")
    open(tmp, "w").write(il)
    scp(tmp, f"{priv}/pr_config.il")
    tmpj = tmp.replace(".il", ".json")
    json.dump(c, open(tmpj, "w"))
    scp(tmpj, f"{priv}/pr_config.json")
    for f in CODE:
        scp(os.path.join(ROOT, f), f"{priv}/code/{f}")
    ssh(f"chmod -R go-rwx {priv}\n")
    print(f"init: config and {len(CODE)} code files pushed to the private directory")


def devmap():
    c = cfg()
    push_skill()
    batch(f'load("{c["remote_tmp"]}_devmap_extract.il")', "devmap")


def setup():
    batch("PR_probe()", "probe")
    print(redact(remote_py("pipeline/cadence/spectre_backend.py setup")).rstrip())


def plan(rec, spec, cell, sizes=None, overrides=None):
    """Layout for any record: PMOS rows on top, passives and sources in the middle,
    NMOS rows below, pins on the sides; every terminal labelled with its net."""
    if sizes:
        rec = A.apply(rec, spec, sizes)
    overrides = overrides or {}
    pins = rec["pins"]
    inv = spec.get("inverting_input") or pins["in"][0]
    non = [x for x in pins["in"] if x != inv][0]
    rows = {k: [] for k in ("p_top", "p_mid", "misc", "n_mid", "n_bot")}
    devs = []
    for d in rec["ckt_netlist"]:
        if d.get("role", "core") in CI.HARNESS:
            continue
        t, pc, i = d["component_type"], d["port_connection"], d["id"]
        if t in CI.MOS:
            s = d.get("size") or {}
            if not s.get("w") or not s.get("l"):
                raise SystemExit(f"{i}: no size (give --sizes or --set)")
            body = pc.get("Body", pins["vdd"] if t == "PMOS" else pins["gnd"])
            e = dict(id=i, kind="mos", alias="N1" if t == "NMOS" else "P1",
                     w=eng(CI.value(s["w"])), l=eng(CI.value(s["l"])), m=str(int(CI.value(s.get("m", 1)) or 1)),
                     orient="R0", conns=[["Drain", pc["Drain"]], ["Gate", pc["Gate"]],
                                         ["Source", pc["Source"]], ["Body", body]])
            row = ("p_top" if pc["Source"] == pins["vdd"] else "p_mid") if t == "PMOS" else \
                  ("n_bot" if pc["Source"] == pins["gnd"] else "n_mid")
        else:
            cell_, key, a, b = {"Current": ("idc", "idc", "In", "Out"), "Cap": ("cap", "c", "Pos", "Neg"),
                                "Res": ("res", "r", "Pos", "Neg"),
                                "Voltage": ("vdc", "vdc", "Positive", "Negative")}.get(t, (None,) * 4)
            if not cell_:
                raise SystemExit(f"{i}: component type {t} not supported")
            v = overrides.get(i, d.get("value"))
            if v is None:
                raise SystemExit(f"{i}: no value (give --set {i}=VALUE)")
            e = dict(id=i, kind="lib", cell=cell_, params=[[key, eng(CI.value(v))]], orient="R0",
                     conns=[["PLUS", pc[a]], ["MINUS", pc[b]]])
            row = "misc"
        rows[row].append(e)
        devs.append(e)
    used = [k for k in rows if rows[k]]
    width = max(len(rows[k]) for k in used)
    for n, k in enumerate(used):
        y = 2.5 * (len(used) - 1 - n)
        x0 = -1.75 * (len(rows[k]) - 1) / 2.0
        for j, e in enumerate(rows[k]):
            e["xy"] = [x0 + 1.75 * j, y]
    xl, xr = -1.75 * (width - 1) / 2.0 - 2.0, 1.75 * (width - 1) / 2.0 + 2.0
    ytop, ymid = 2.5 * (len(used) - 1), 1.25 * (len(used) - 1)
    pin_list = [[pins["vdd"], "inputOutput", [xl, ytop + 1.0]], [pins["gnd"], "inputOutput", [xl, -1.0]],
                [inv, "input", [xl, ymid + 0.5]], [non, "input", [xl, ymid - 0.5]],
                [pins["out"], "output", [xr, ymid]]]
    cond = spec["conditions"]
    vcm = (sizes or {}).get("vcm") or cond.get("vcm") or cond["vdd"] / 2
    return dict(cell=cell, tbcell=cell + "_TB", devs=devs, pins=pin_list,
                symleft=[pins["gnd"], pins["vdd"], non, inv],
                tb=dict(supply=pins["vdd"], ground=pins["gnd"], inn=inv, inp=non, out=pins["out"],
                        vdd=eng(cond["vdd"]), vcm=eng(vcm), cl=eng(cond["cl"])))


def place(record, cell, spec=None, sizes=None, sets=()):
    rec = json.load(open(record))
    spec = json.load(open(spec)) if spec else dict(conditions=dict(vdd=1.8, cl=2e-12, vcm=None), variables={})
    sol = json.load(open(sizes))["solution"] if sizes else None
    ov = dict(s.split("=", 1) for s in sets)
    p = plan(rec, spec, cell, sol, ov)
    print(gui("PR_placeRecord('" + skill_str(p) + ")"))


def sim(cell, bode=False):
    batch(f'PR_netlist("{cell}_TB")', "netlist")
    out = remote_py(f"pipeline/cadence/spectre_backend.py tb {cell}_TB" + (" bode" if bode else ""))
    line = [l for l in out.splitlines() if l.startswith("RESULT ")]
    print(redact(line[-1] if line else out))


def record(spec_path, bode=False):
    c = cfg()
    spec = json.load(open(spec_path))
    remote = f"{c['private_dir']}/runs/_record"
    ssh(f"mkdir -p -m 700 {remote}\n")
    scp(spec["record"], f"{remote}/record.json")
    spec["record"] = f"{remote}/record.json"
    tmp = os.path.expanduser("~/.config/analog_repro/_spec.json")
    json.dump(spec, open(tmp, "w"))
    scp(tmp, f"{remote}/spec.json")
    out = remote_py(f"pipeline/cadence/spectre_backend.py record {remote}/spec.json" + (" bode" if bode else ""))
    line = [l for l in out.splitlines() if l.startswith("RESULT ")]
    print(redact(line[-1] if line else out))


def case(case_dir, key):
    """Run a case circuit through checks, as-printed, re-bias and compare on the PDK
    machine; circuit metrics (and the loop-gain curve) come back, nothing else."""
    c = cfg()
    remote = f"{c['private_dir']}/runs/case_{os.path.basename(os.path.normpath(case_dir))}_{key}"
    ssh(f"mkdir -p -m 700 {remote}\n")
    scp(os.path.join(case_dir, "records", f"{key}.json"), f"{remote}/record.json")
    rep = json.load(open(os.path.join(case_dir, "reported.json")))
    cfgp = os.path.join(case_dir, "case.json")
    region = json.load(open(cfgp)).get("region", "strong") if os.path.exists(cfgp) else "strong"
    job = dict(key=key, record=f"{remote}/record.json", claims=rep["circuits"].get(key, {}).get("claims", []),
               region=region)
    tmp = os.path.expanduser("~/.config/analog_repro/_job.json")
    json.dump(job, open(tmp, "w"))
    scp(tmp, f"{remote}/job.json")
    out = remote_py(f"pipeline/cadence/case_pdk.py {remote}/job.json")
    line = [l for l in out.splitlines() if l.startswith("RESULT ")]
    if not line:
        raise SystemExit("case failed:\n" + redact(out[-1500:]))
    res = json.loads(line[-1][7:])
    d = os.path.join(case_dir, "out_pdk", key)
    os.makedirs(d, exist_ok=True)
    json.dump(res, open(os.path.join(d, "result.json"), "w"), indent=1)
    for tag in ("as_printed", "rebiased"):
        x = res[tag]
        print(f"{key} {tag}: {x['level']} sat {x.get('n_sat')}/{x.get('n_mos')} gain {x.get('gain_dB')} "
              f"gbw {x.get('gbw_Hz')} pm {x.get('pm_deg')} power {x.get('power_W')}")
    print("deviations:", res["deviations"], "| search sims:", res["search_simulations"])


def size(action, run, k=None):
    """Option B with the local loop on the PDK machine. Only the public artifacts come
    back: the next prompt (relative feedback, leak-audited), the audit, final.json."""
    c = cfg()
    name = os.path.basename(os.path.normpath(run))
    remote = f"{c['private_dir']}/runs/{name}"
    rel = f"../runs/{name}"
    if action == "init":
        spec = json.load(open(os.path.join(run, "spec.json")))
        ssh(f"mkdir -p -m 700 {remote}/llm_0\n")
        scp(spec["record"], f"{remote}/record.json")
        spec["record"] = f"{remote}/record.json"
        tmp = os.path.expanduser("~/.config/analog_repro/_spec.json")
        json.dump(spec, open(tmp, "w"))
        scp(tmp, f"{remote}/spec.json")
        for f in ("compute_sizing.py", "prompt.md"):
            scp(os.path.join(run, "llm_0", f), f"{remote}/llm_0/{f}")
        print(f"size init: run {name} ready on the PDK machine")
    elif action == "inner":
        d = os.path.join(run, f"llm_{k}")
        ssh(f"mkdir -p -m 700 {remote}/llm_{k}\n")
        scp(os.path.join(d, "compute_sizing.py"), f"{remote}/llm_{k}/compute_sizing.py")
        out = remote_py(f"pipeline/cadence/run_sizing.py inner {rel} {k}")
        print(redact(out.strip().splitlines()[-1] if out.strip() else "(no output)"))
        nxt = int(k) + 1
        has = ssh(f"test -f {remote}/llm_{nxt}/prompt.md && echo yes || true\n").strip()
        if has == "yes":
            os.makedirs(os.path.join(run, f"llm_{nxt}"), exist_ok=True)
            for f in ("prompt.md", "leak_audit.json"):
                dst = os.path.join(run, f"llm_{nxt}", f)
                subprocess.run(["scp", "-q", f"{c['ssh_host']}:{remote}/llm_{nxt}/{f}", dst], check=True)
                if f == "prompt.md":
                    open(dst, "w").write(open(dst).read().replace(rel, run))
            print(f"next prompt: {run}/llm_{nxt}/prompt.md  audit: "
                  f"{json.load(open(os.path.join(run, f'llm_{nxt}', 'leak_audit.json')))}")
    elif action == "final":
        remote_py(f"pipeline/cadence/run_sizing.py final {rel}")
        subprocess.run(["scp", "-q", f"{c['ssh_host']}:{remote}/final.json", os.path.join(run, "final.json")], check=True)
        print(json.dumps({k2: v for k2, v in json.load(open(os.path.join(run, "final.json"))).items()
                          if k2 in ("converged", "llm_calls", "simulations", "compare", "leak_audit")}, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd")
    ap.add_argument("args", nargs="*")
    ap.add_argument("--spec")
    ap.add_argument("--sizes")
    ap.add_argument("--set", action="append", default=[])
    ap.add_argument("--bode", action="store_true", help="sim/record: also print the loop-gain curve")
    a = ap.parse_args()
    if a.cmd == "init":
        init()
    elif a.cmd == "devmap":
        devmap()
    elif a.cmd == "setup":
        setup()
    elif a.cmd == "place":
        place(a.args[0], a.args[1], a.spec, a.sizes, a.set)
    elif a.cmd == "sim":
        sim(a.args[0], a.bode)
    elif a.cmd == "record":
        record(a.args[0], a.bode)
    elif a.cmd == "case":
        case(a.args[0], a.args[1])
    elif a.cmd == "size":
        size(a.args[0], a.args[1], a.args[2] if len(a.args) > 2 else None)
    else:
        raise SystemExit(__doc__)
