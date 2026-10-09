"""Block D, static part: electrical rule checks on a circuit record.

A netlist can be a perfect parse of the figure and still not be a circuit.
These checks need no simulator and no knowledge of what the circuit is meant
to do; they only ask whether it could be one. Each finding has a code so its
yield can be counted across a benchmark.

  FLOATING_GATE   a net touching only gates/bases, and not a pin
  DANGLING        an internal net with a single terminal
  PIN_MISSING     a declared pin net that no device touches
  INPUT_NO_GATE   an input pin that drives no gate or base
  OUTPUT_UNDRIVEN the output touches no drain, collector or amplifier output
  SUPPLY_SHORT    vdd and gnd are the same net, or a source is shorted
  SIZE_ABSENT     a transistor without a numeric W or L
  VALUE_ABSENT    a passive or source without a numeric value
  SHORTED_DEVICE  every terminal of a device on one net
  BIAS_RANGE      a bias source outside the supply range (a misread value)
"""
from collections import defaultdict

from circuit import CONTROL, HARNESS, MOS, devices, value

DRIVE_OUT = {"Drain", "Collector", "Out", "OutP", "OutN", "Emitter", "Source"}


def pins_of(c):
    p = c.get("pins", {})
    ins = p.get("in", [])
    ins = [ins] if isinstance(ins, str) else list(ins)
    return p.get("vdd"), p.get("gnd"), ins, p.get("out")


def terminals(c):
    net = defaultdict(list)
    for i, d in devices(c):
        if d.get("role", "core") in HARNESS:
            continue
        for port, n in d["port_connection"].items():
            net[n].append((d.get("id") or f"#{i}", d["component_type"], port))
    return net


def check(c, need_sizes=True):
    vdd, gnd, ins, out = pins_of(c)
    pins = {x for x in [vdd, gnd, out, *ins] if x}
    net = terminals(c)
    found = []
    supply = next((value(d.get("value")) for _, d in devices(c)
                   if d.get("role") == "supply" and value(d.get("value"))), None) or 1.8

    def add(code, msg, sev="error"):
        found.append(dict(code=code, severity=sev, message=msg))

    for n, ts in net.items():
        if n in pins:
            continue
        if all(p in CONTROL for _, _, p in ts):
            add("FLOATING_GATE", f"net {n} only reaches {', '.join(f'{i}.{p}' for i, _, p in ts)}")
        elif len(ts) == 1 and ts[0][2] != "Body":
            add("DANGLING", f"net {n} has one terminal, {ts[0][0]}.{ts[0][2]}")
    for name, n in (("vdd", vdd), ("gnd", gnd), ("out", out)):
        if not n or n not in net:
            add("PIN_MISSING", f"pin {name} ({n}) touches no device")
    for n in ins:
        if n not in net:
            add("PIN_MISSING", f"input {n} touches no device")
        elif not any(p in CONTROL or p in ("InP", "InN", "In") for _, _, p in net[n]):
            add("INPUT_NO_GATE", f"input {n} drives no gate: {net[n]}")
    if out in net and not any(p in DRIVE_OUT for _, _, p in net[out]):
        add("OUTPUT_UNDRIVEN", f"output {out} touches {net[out]}")
    if vdd and vdd == gnd:
        add("SUPPLY_SHORT", "vdd and gnd are the same net")
    for i, d in devices(c):
        if d.get("role", "core") in HARNESS:
            continue
        tag = d.get("id") or f"#{i}"
        pc = d["port_connection"]
        if len(set(v for k, v in pc.items() if k != "Body")) == 1:
            sev = "error" if d["component_type"] == "Voltage" else "warning"
            add("SUPPLY_SHORT" if d["component_type"] == "Voltage" else "SHORTED_DEVICE",
                f"{tag}: all terminals on {next(iter(pc.values()))}", sev)
        if d["component_type"] == "Voltage" and d.get("role") == "bias":
            v = value(d.get("value"))
            if v is not None and not (-0.01 <= v <= supply + 0.01):
                add("BIAS_RANGE", f"{tag}: {v:g} V is outside 0..{supply:g} V")
        if d["component_type"] in MOS and need_sizes:
            s = d.get("size", {})
            miss = [k for k in ("w", "l") if value(s.get(k)) is None]
            if miss:
                add("SIZE_ABSENT", f"{tag}: no numeric {'/'.join(miss)} ({s})")
        if d["component_type"] in ("Res", "Cap", "Current", "Voltage") and need_sizes:
            if value(d.get("value")) is None:
                add("VALUE_ABSENT", f"{tag}: no numeric value ({d.get('value')!r})")
    return found


def blocking(found):
    """Findings that stop simulation outright. Absent sizes/values are filled by a
    stated policy and an out-of-range bias is re-derived by the bias search, so
    those are repairable, not blocking."""
    return [f for f in found if f["severity"] == "error"
            and f["code"] not in ("SIZE_ABSENT", "VALUE_ABSENT", "BIAS_RANGE")]
