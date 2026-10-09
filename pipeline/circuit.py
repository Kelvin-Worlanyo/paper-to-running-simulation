"""The circuit record that the reading agent writes and every later block reads.

It is the Image2Net netlist JSON (so topology can be scored with the same
code) with four additions a simulator needs and a benchmark does not:

    id        the designator printed on the figure (M1, NM0, C0 ...)
    role      core | bias | supply | input | load
              bias   = a source that is part of the circuit's biasing
              supply, input, load = test harness drawn on the figure; removed
              from the circuit and turned into bench conditions instead
    size      w, l, m for transistors; value for R, C, I, V (SPICE strings)
    evidence  where each number came from ("figure: 'w=4u' beside NM0")

plus top-level `pins` (which nets are vdd, gnd, the inputs, the output) and
`absent`, the list of things the figure does not give. Absence is recorded,
never filled in by the reader: the pipeline decides what to do about it, and
says so.
"""
import json
import re

PORTS = {
    "PMOS": ["Drain", "Gate", "Source", "Body"], "NMOS": ["Drain", "Gate", "Source", "Body"],
    "NPN": ["Collector", "Base", "Emitter"], "PNP": ["Collector", "Base", "Emitter"],
    "Res": ["Pos", "Neg"], "Cap": ["Pos", "Neg"], "Ind": ["Pos", "Neg"],
    "Diode": ["In", "Out"], "Current": ["In", "Out"], "Voltage": ["Positive", "Negative"],
    "Diso_amp": ["InP", "InN", "Out"], "Dido_amp": ["InP", "InN", "OutP", "OutN"],
    "Siso_amp": ["In", "Out"],
}
MOS = ("PMOS", "NMOS")
CONTROL = {"Gate", "Base"}
ROLES = ("core", "bias", "supply", "input", "load")
HARNESS = ("supply", "input", "load")

_SI = {"f": 1e-15, "p": 1e-12, "n": 1e-9, "u": 1e-6, "µ": 1e-6, "m": 1e-3,
       "k": 1e3, "meg": 1e6, "g": 1e9}


def value(s):
    """'4u' -> 4e-06, '500n' -> 5e-07, '1.8' -> 1.8, '20uA' -> 2e-05.
    None when the string is not a number (a symbol such as 'wn1' or 'VCM')."""
    if s is None:
        return None
    if isinstance(s, (int, float)):
        return float(s)
    t = str(s).strip().replace("µ", "u").replace("Ø", "0").replace("ø", "0")
    m = re.fullmatch(r"([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)\s*(meg|[fpnumkg])?\s*[a-zA-Z]*", t)
    if not m:
        return None
    return float(m.group(1)) * _SI.get((m.group(2) or "").lower(), 1.0)


def load(path):
    return json.load(open(path))


def devices(c, roles=None):
    for i, d in enumerate(c["ckt_netlist"]):
        if roles is None or d.get("role", "core") in roles:
            yield i, d


def schema_problems(c):
    bad = []
    if "ckt_netlist" not in c:
        return ["no ckt_netlist"]
    ids = [d.get("id") for d in c["ckt_netlist"]]
    for i, d in enumerate(c["ckt_netlist"]):
        t, pc = d.get("component_type"), d.get("port_connection", {})
        tag = d.get("id") or f"#{i}"
        if t not in PORTS:
            bad.append(f"{tag}: unknown type {t!r}")
            continue
        need = [p for p in PORTS[t] if p != "Body"]
        if [p for p in need if p not in pc] or [p for p in pc if p not in PORTS[t]]:
            bad.append(f"{tag}: ports {sorted(pc)} do not match {t}")
        if d.get("role", "core") not in ROLES:
            bad.append(f"{tag}: role {d.get('role')!r}")
    dup = {x for x in ids if x and ids.count(x) > 1}
    if dup:
        bad.append(f"duplicate ids {sorted(dup)}")
    pins = c.get("pins", {})
    for k in ("vdd", "gnd", "out", "in"):
        if k not in pins:
            bad.append(f"pins.{k} missing")
    return bad


def bias_terminals(c, floating):
    """Stated policy for bias terminals drawn without a source.

    A figure may print a bias as a labelled terminal ('o Vb1') instead of a
    voltage source. The reader then records a net that reaches only gates and
    lists the bias as absent. For each such net -- and only when the record's
    own absent list names it as a bias voltage -- a bias source to the ground
    pin is added with no value, so the bias search sets it. Any other net that
    reaches only gates stays a floating-gate error (a misreading signal).
    Returns (new record, [deviation strings], [nets resolved])."""
    import copy
    import re as _re
    names = {}
    for a in c.get("absent", []):
        item, why = str(a.get("item", "")), str(a.get("why", "")).lower()
        tok = _re.match(r"\s*([A-Za-z_][\w]*)", item)
        if tok and ("bias" in why or "bias" in item.lower()):
            names[tok.group(1).lower()] = tok.group(1)
    r = copy.deepcopy(c)
    dev, done = [], []
    for net in floating:
        if net.lower() in names:
            r["ckt_netlist"].append({"id": f"VB_{net}", "role": "bias", "component_type": "Voltage",
                                     "port_connection": {"Positive": net, "Negative": c["pins"]["gnd"]},
                                     "value": None, "evidence": {"value": "policy: bias terminal printed without a value"}})
            dev.append(f"{net}: bias terminal printed as the symbol '{names[net.lower()]}'; source added, value searched")
            done.append(net)
    return r, dev, done
