"""Spectre back end for the PDK path. Runs ON the machine that holds the PDK,
next to the private files, so operating-point data never leaves it.

Three uses:
  setup   one-time: model includes from the designer's source testbench and, per
          MOS type, the model name and source/drain geometry rule from a probe
          netlist written by the design environment at the PDK's default sizes
          (-> PRIV/simsetup/models.scs, devices.json). Prints no PDK content.
  tb      simulate a testbench the design environment netlisted (the placed
          record's standard bench) and print circuit metrics only.
  simulate(spec, rec, sol)
          drop-in for sizing_local.simulate: builds the deck from a circuit
          record, same result keys as sim.simulate.

The bench is the one used everywhere in the pipeline: unity-gain loop through a
1 T inductor, AC injected at the inverting input through 1 T, load CL, 27 C.
Nothing PDK-specific is written in this file.
"""
import cmath
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(HERE, "..", "..", "design"))
import circuit as CI  # noqa: E402
import run as R  # noqa: E402  validated measure()
import sizing as A  # noqa: E402

# private_dir/code/pipeline/cadence/spectre_backend.py -> private_dir
PRIV = os.environ.get("PR_PRIV") or os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SETUP = os.path.join(PRIV, "simsetup")
SUBCKT = "DUT"
_SI = {"T": 1e12, "G": 1e9, "M": 1e6, "K": 1e3, "k": 1e3, "_": 1.0, "m": 1e-3, "u": 1e-6,
       "n": 1e-9, "p": 1e-12, "f": 1e-15, "a": 1e-18}
ANALYSES = "\n".join([
    "simulatorOptions options reltol=1e-4 vabstol=1e-6 iabstol=1e-12 temp=27 tnom=27 gmin=1e-12",
    "dcOp dc maxiters=150 maxsteps=10000",
    'opinfo info what=oppoint where=file file="op.txt"',
    "ac ac start=0.01 stop=1e9 dec=50",
    "saveOptions options save=allpub currents=all", ""])


def cfg():
    return json.load(open(os.path.join(PRIV, "pr_config.json")))


def num(s):
    """Spectre number, with a scale suffix or a spaced unit: '12.3u', '10.6 uA', '0.5'."""
    m = re.match(r"^\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)\s*([TGMKkmunpfa_]?)(?=[A-Za-z]*\s*$|[A-Z])", s) or \
        re.match(r"^\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)()", s)
    if not m:
        raise ValueError(s)
    return float(m.group(1)) * _SI.get(m.group(2), 1.0)


def _join(text):
    return text.replace("\\\n", " ")


# ----------------------------------------------------------------------- setup
def _lib_paths(work_dir):
    """cds.lib DEFINE name -> absolute path (follows INCLUDE / SOFTINCLUDE)."""
    out, seen = {}, set()

    def read(path):
        path = os.path.expanduser(os.path.expandvars(path))
        if path in seen or not os.path.exists(path):
            return
        seen.add(path)
        base = os.path.dirname(path)
        for line in open(path):
            p = line.split("#")[0].split()
            if len(p) >= 3 and p[0].upper() == "DEFINE":
                d = os.path.expanduser(os.path.expandvars(p[2]))
                out[p[1]] = d if os.path.isabs(d) else os.path.normpath(os.path.join(base, d))
            elif len(p) >= 2 and p[0].upper() in ("INCLUDE", "SOFTINCLUDE"):
                d = os.path.expanduser(os.path.expandvars(p[1]))
                read(d if os.path.isabs(d) else os.path.join(base, d))
    read(os.path.join(work_dir, "cds.lib"))
    return out


def _source_models(c):
    """Model includes of the designer's source testbench (maestro / adexl state)."""
    lib = _lib_paths(c["work_dir"]).get(c["source_testbench"]["lib"])
    if not lib:
        raise SystemExit("setup: source testbench library not found in cds.lib")
    for kind in ("maestro", "adexl"):
        st = os.path.join(lib, c["source_testbench"]["cell"], kind, "active.state")
        if os.path.exists(st):
            for line in open(st):
                if 'Name="modelFiles"' in line:
                    pairs = re.findall(r'\("([^"]+)"\s+"([^"]*)"\)', line)
                    if pairs:
                        return [f'include "{f}"' + (f" section={s}" if s else "") for f, s in pairs]
    raise SystemExit("setup: no model files found in the source testbench's state")


def _netlist_file(cell):
    f = os.path.join(PRIV, "simulation", cell, "spectre", "schematic", "netlist", "input.scs")
    if not os.path.exists(f):
        raise SystemExit(f"no netlist for {cell}: run the netlist step first")
    return f


def setup():
    c = cfg()
    os.makedirs(SETUP, mode=0o700, exist_ok=True)
    models = _source_models(c)
    open(os.path.join(SETUP, "models.scs"), "w").write("\n".join(models) + "\n")
    devs = {}
    for line in _join(open(_netlist_file("PR_PROBE")).read()).splitlines():
        m = re.match(r"^\s*PROBE_(N|P)\s+\(([^)]*)\)\s+(\S+)\s+(.*)$", line)
        if not m:
            continue
        p = dict(re.findall(r"(\w+)=(\S+)", m.group(4)))
        w = num(p["w"])
        devs["NMOS" if m.group(1) == "N" else "PMOS"] = dict(
            model=m.group(3), w_default=w,
            hdif=num(p["ad"]) / w if "ad" in p else None,          # ad = W * hdif at the default
            nr=num(p["nrd"]) * w if "nrd" in p else None)          # nrd = nr / W
    if set(devs) != {"NMOS", "PMOS"}:
        raise SystemExit("setup: probe netlist lacks one of the two devices")
    json.dump(devs, open(os.path.join(SETUP, "devices.json"), "w"))
    os.chmod(os.path.join(SETUP, "devices.json"), 0o600)
    os.chmod(os.path.join(SETUP, "models.scs"), 0o600)
    print(f"setup: {len(models)} model includes, NMOS and PMOS geometry rules "
          f"({'with' if devs['NMOS']['hdif'] else 'without'} source/drain areas)")


# --------------------------------------------------------------------- decks
def _header():
    return "simulator lang=spectre\nglobal 0\n" + open(os.path.join(SETUP, "models.scs")).read()


def _mos_line(name, nets, kind, w, l, m):
    t = json.load(open(os.path.join(SETUP, "devices.json")))[kind]
    s = f"    {name} ({' '.join(nets)}) {t['model']} l={l:.6g} w={w:.6g} m={int(m)}"
    if t.get("hdif"):
        a, p = w * t["hdif"], 2 * (w + t["hdif"])
        s += f" ad={a:.6g} as={a:.6g} pd={p:.6g} ps={p:.6g}"
    if t.get("nr"):
        s += f" nrd={t['nr'] / w:.6g} nrs={t['nr'] / w:.6g}"
    return s


def netlist(rec, spec, vcm):
    """Deck from a circuit record: the circuit as a subckt, the bench, analyses."""
    cond = spec["conditions"]
    pins = rec["pins"]
    inv = spec.get("inverting_input") or pins["in"][0]
    non = [x for x in pins["in"] if x != inv][0]
    rename = {inv: "vinn", non: "vinp", pins["gnd"]: "gnd", pins["vdd"]: "vdd", pins["out"]: "vout"}
    n = lambda x: rename.get(x, x)                                       # noqa: E731
    lines = [f"subckt {SUBCKT} gnd vdd vinn vinp vout"]
    for d in rec["ckt_netlist"]:
        if d.get("role", "core") in CI.HARNESS:
            continue
        pc, t = d["port_connection"], d["component_type"]
        if t in CI.MOS:
            s = d["size"]
            body = pc.get("Body", pins["vdd"] if t == "PMOS" else pins["gnd"])
            nets = [n(pc["Drain"]), n(pc["Gate"]), n(pc["Source"]), n(body)]
            lines.append(_mos_line(d["id"], nets, t, CI.value(s["w"]), CI.value(s["l"]), CI.value(s.get("m", 1)) or 1))
        elif t == "Current":
            lines.append(f"    {d['id']} ({n(pc['In'])} {n(pc['Out'])}) isource dc={CI.value(d['value']):.6g} type=dc")
        elif t == "Cap":
            lines.append(f"    {d['id']} ({n(pc['Pos'])} {n(pc['Neg'])}) capacitor c={CI.value(d['value']):.6g}")
        elif t == "Res":
            lines.append(f"    {d['id']} ({n(pc['Pos'])} {n(pc['Neg'])}) resistor r={CI.value(d['value']):.6g}")
        elif t == "Voltage":
            lines.append(f"    {d['id']} ({n(pc['Positive'])} {n(pc['Negative'])}) vsource dc={CI.value(d['value']):.6g} type=dc")
        else:
            raise ValueError(f"{d['id']}: component type {t} not supported by the Spectre back end")
    lines.append(f"ends {SUBCKT}")
    sub = "\n".join(lines)
    bench = "\n".join([
        f"X0 (0 vdd vinn vcm vout) {SUBCKT}",
        f"V_DD (vdd 0) vsource dc={cond['vdd']:.6g} type=dc",
        f"V_CM (vcm 0) vsource dc={vcm:.6g} type=dc",
        f"V_AC (vac 0) vsource dc={vcm:.6g} mag=1 type=dc",
        "L_FB (vinn vout) inductor l=1T",
        "C_AC (vac vinn) capacitor c=1T",
        f"C_L (vout 0) capacitor c={cond['cl']:.6g}"] +
        ([f"R_L (vout 0) resistor r={cond['rl']:.6g}"] if cond.get("rl") else []))
    return sub, _header() + sub + "\n" + bench + "\n" + ANALYSES


_ADE_CTRL = re.compile(r"^\s*(simulatorOptions|ac|dc|dcOp|dcOpInfo|modelParameter|element|outputParameter|"
                       r"designParamVals|primitives|subckts|saveOptions|finalTimeOP|tran|noise)\s")


def tb_deck(cell):
    """Deck from a testbench the design environment netlisted: its circuit, with the
    model includes of the source testbench and the standard analyses."""
    body = _join(open(_netlist_file(cell)).read())
    keep = [l for l in body.splitlines()
            if not l.strip().startswith("include") and not l.startswith("simulator lang")
            and not _ADE_CTRL.match(l)]
    # scripted edits do not fire the PDK's CDF callbacks, so source/drain geometry
    # in the design environment's netlist can be stale: rebuild it from the rule
    devs = json.load(open(os.path.join(SETUP, "devices.json")))
    kind = {v["model"]: k for k, v in devs.items()}
    for n, l in enumerate(keep):
        m = re.match(r"^(\s*)(\w+)\s+\(([^)]*)\)\s+(\S+)\s+(.*)$", l)
        if m and m.group(4) in kind:
            p = dict(re.findall(r"(\w+)=(\S+)", m.group(5)))
            keep[n] = m.group(1) + _mos_line(m.group(2), m.group(3).split(), kind[m.group(4)],
                                             num(p["w"]), num(p["l"]), num(p.get("m", "1"))).lstrip()
    text = "\n".join(keep)
    val = lambda name: num(re.search(r"^" + name + r"\s+\([^)]*\)\s+vsource\s+dc=(\S+)", text, re.M).group(1))  # noqa: E731
    return _header() + text + "\n" + ANALYSES, val("V_CM"), val("V_DD")


# ----------------------------------------------------------------- run + read
def _oppoint(path):
    """Instance -> {param: value} from Spectre's readable op-point file."""
    devs, cur = {}, None
    for line in open(path):
        m = re.match(r"^Instance:\s+(\S+)", line)
        if m:
            cur = devs.setdefault(m.group(1), {})
            continue
        # values carry a spaced unit with its scale: "10.6 uA", "512.3 mV"
        m = re.match(r"^\s*(\w+)\s*=\s*(\S+(?:\s+[TGMKkmunpfa]?[A-Za-z]*)?)\s*$", line)
        if cur is not None and m:
            try:
                cur[m.group(1)] = num(m.group(2))
            except ValueError:
                pass
    return devs


def _psf_values(path, names):
    txt = open(path).read()
    out = {}
    for nm in names:
        m = re.search(r'^"' + re.escape(nm) + r'"\s+(?:"\w+"\s+)?([-+\deE.]+)', txt, re.M)
        if m:
            out[nm] = float(m.group(1))
    return out


def _ac_vout(path):
    txt = open(path).read()
    vals = txt.split("VALUE", 1)[1]
    f, mag, ph = [], [], []
    for blk in re.split(r'\n"freq" ', vals)[1:]:
        fr = float(blk.split()[0])
        m = re.search(r'"vout" \(([-+\deE.]+) ([-+\deE.]+)\)', blk)
        if m:
            v = complex(float(m.group(1)), float(m.group(2)))
            f.append(fr)
            mag.append(20 * math.log10(max(abs(v), 1e-30)))
            ph.append(cmath.phase(v))
    return f, mag, ph


def run_deck(deck, vcm, vdd, keep=None):
    tmp = keep or tempfile.mkdtemp(prefix="sb_", dir=PRIV)
    open(os.path.join(tmp, "deck.scs"), "w").write(deck)
    subprocess.run(["tcsh", "-c", f"{cfg()['shell_init']}; cd {tmp}; "
                    "spectre -64 deck.scs -format psfascii -raw raw =log spectre.log"],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=600)
    r = dict(converges=False)
    logf = os.path.join(tmp, "spectre.log")
    log = open(logf).read() if os.path.exists(logf) else ""
    m = re.search(r"completes with (\d+) errors", log)
    dcf, opf = os.path.join(tmp, "raw", "dcOp.dc"), os.path.join(tmp, "op.txt")
    if not (m and m.group(1) == "0" and os.path.exists(dcf) and os.path.exists(opf)):
        r["error"] = "spectre failed" if not m else f"spectre: {m.group(1)} errors"
        return r, tmp
    v = _psf_values(dcf, ["vout", "V_DD:p"])
    if "vout" not in v:
        return r, tmp
    op = _oppoint(opf)
    idd = v.get("V_DD:p")
    r.update(converges=True, vout=v["vout"], power_W=abs(idd) * vdd if idd is not None else None)
    r["follows"] = abs(r["vout"] - vcm) < 0.05
    devs = {}
    for inst, x in op.items():
        mm = re.match(r"^X0\.(\w+)$", inst)
        if not mm or not all(k in x for k in ("ids", "vgs", "vds", "vth", "vdsat")):
            continue
        # magnitudes: PMOS values are negative in Spectre; calibration and the
        # region test use the NMOS-positive convention for both types
        devs[mm.group(1).lower()] = dict(id=abs(x["ids"]), vgs=abs(x["vgs"]), vds=abs(x["vds"]),
                                         vth=abs(x["vth"]), vdsat=abs(x["vdsat"]),
                                         gm=abs(x.get("gm", 0.0)), gds=abs(x.get("gds", 0.0)))
    r["devices"] = devs
    import sim as _sim                      # the same region test as the open back end
    sat = _sim.regions(devs)
    r["n_mos"], r["n_sat"] = len(devs), sum(sat.values())
    r["not_saturated"] = sorted(d for d, ok in sat.items() if not ok)
    acf = os.path.join(tmp, "raw", "ac.ac")
    if os.path.exists(acf):
        f, mag, ph = _ac_vout(acf)
        if f:
            meas, phd = R.measure(f, mag, ph)
            r.update(meas)
            r["bode"] = (f, mag, phd)
            r["stable"] = meas["gbw_Hz"] is not None and meas["pm_deg"] is not None and meas["pm_deg"] > 0
    return r, tmp


def simulate(spec, rec, sol):
    """Drop-in for sizing_local.simulate."""
    sized = A.apply(rec, spec, sol)
    cond = spec["conditions"]
    vcm = sol.get("vcm") if spec["variables"].get("vcm") else cond["vcm"]
    vcm = vcm if isinstance(vcm, (int, float)) else cond["vdd"] / 2
    sub, deck = netlist(sized, spec, vcm)
    res, tmp = run_deck(deck, vcm, cond["vdd"])
    shutil.rmtree(tmp, ignore_errors=True)
    return sized, res, sub


def _public(res, bode=False):
    """Circuit-level results only; with bode, the loop gain curve (every 5th point)."""
    out = {k: res.get(k) for k in PUBLIC}
    if bode and res.get("bode"):
        f, mag, ph = res["bode"]
        out["bode"] = [f[::5], mag[::5], ph[::5]]
    return out


PUBLIC = ("converges", "follows", "n_sat", "n_mos", "not_saturated", "gain_dB", "gbw_Hz", "pm_deg",
          "power_W", "vout", "error")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "setup":
        setup()
    elif cmd == "tb":                      # tb CELL: circuit metrics only
        deck, vcm, vdd = tb_deck(sys.argv[2])
        res, tmp = run_deck(deck, vcm, vdd)
        shutil.rmtree(tmp, ignore_errors=True)
        print("RESULT " + json.dumps(_public(res, "bode" in sys.argv[3:])))
    elif cmd == "record":                  # record SPEC.json: the record as printed
        spec = json.load(open(sys.argv[2]))
        rec = json.load(open(spec["record"]))
        vcm = spec["conditions"].get("vcm") or spec["conditions"]["vdd"] / 2
        _, deck = netlist(rec, spec, vcm)
        res, tmp = run_deck(deck, vcm, spec["conditions"]["vdd"])
        shutil.rmtree(tmp, ignore_errors=True)
        print("RESULT " + json.dumps(_public(res, "bode" in sys.argv[3:])))
    else:
        raise SystemExit(__doc__)
