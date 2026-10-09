"""Block E, part 1: circuit record -> SPICE subcircuit for the bench.

Harness devices (supply, input stimulus, load) are dropped and become bench
conditions; bias sources stay, with their DC value exposed as a .param so the
bias search can move it. The subcircuit's port order is the bench's:
`gnda vdda vinn vinp vout`. Which drawn input is inverting is NOT decided
here: `flip` swaps the two, and the polarity check picks by simulation.

Anything the figure does not give is filled by a stated policy and returned
as a deviation, so a result is never silently built on an invented number.
"""
import math
import re
import statistics

from circuit import HARNESS, MOS, devices, value

MODEL = {"NMOS": "sky130_fd_pr__nfet_01v8", "PMOS": "sky130_fd_pr__pfet_01v8"}
W_MAX = 100e-6          # widest single device the Sky130 01v8 model bins cover


def _net(n):
    return re.sub(r"[^A-Za-z0-9_]", "_", str(n)).lower() or "n0"


def conditions(c):
    """VDD, CL, VCM and a resistive load RL as drawn on the harness, or None."""
    vdd = cl = vcm = rl = None
    for _, d in devices(c):
        r = d.get("role", "core")
        if r == "supply" and d["component_type"] == "Voltage":
            vdd = value(d.get("value"))
        elif r == "load" and d["component_type"] == "Cap":
            cl = value(d.get("value"))
        elif r == "load" and d["component_type"] == "Res":
            rl = value(d.get("value"))
        elif r == "input" and d["component_type"] == "Voltage" and vcm is None:
            v = value(d.get("value"))
            if v is not None and 0.1 < v < 1.7:   # a DC level, not a small-signal amplitude
                vcm = v
    return dict(vdd=vdd, cl=cl, vcm=vcm, rl=rl)


def build(c, name, flip=False):
    """(subckt text, bias params {name: initial volts or None}, deviations)."""
    p = c["pins"]
    ins = p["in"] if isinstance(p["in"], list) else [p["in"]]
    rename = {p["gnd"]: "gnda", p["vdd"]: "vdda", p["out"]: "vout"}
    if len(ins) == 2:
        a, b = ins
        rename[a], rename[b] = ("vinp", "vinn") if flip else ("vinn", "vinp")
    elif len(ins) == 1:
        rename[ins[0]] = "vinp"
    net = lambda n: rename.get(n, "n_" + _net(n))
    dev = []

    known = {t: [(value(d.get("size", {}).get("w")), value(d.get("size", {}).get("l")))
                 for _, d in devices(c) if d["component_type"] == t] for t in MOS}
    lines, params = [], {}
    for i, d in devices(c):
        role, t, pc = d.get("role", "core"), d["component_type"], d["port_connection"]
        if role in HARNESS:
            continue
        tag = re.sub(r"\W", "_", d.get("id") or f"d{i}")
        if t in MOS:
            s = d.get("size", {})
            w, l, m = value(s.get("w")), value(s.get("l")), value(s.get("m")) or 1
            if w is None:
                ws = [x for x, _ in known[t] if x]
                w = statistics.median(ws) if ws else 1e-6
                dev.append(f"{tag}: W not given ({s.get('w')!r}); median {t} width {w*1e6:g} um used")
            if l is None:
                ls = [y for _, y in known[t] if y]
                l = statistics.median(ls) if ls else 0.5e-6
                dev.append(f"{tag}: L not given; median {t} length {l*1e6:g} um used")
            if w > W_MAX:
                # beyond the process models' width range: equivalent parallel fingers
                k = math.ceil(w / W_MAX - 1e-9)
                dev.append(f"{tag}: W={w*1e6:g} um beyond the model range; built as {k} parallel "
                           f"devices of {w/k*1e6:.4g} um")
                w, m = w / k, m * k
            body = pc.get("Body") or (p["vdd"] if t == "PMOS" else p["gnd"])
            lines.append(f"X{tag} {net(pc['Drain'])} {net(pc['Gate'])} {net(pc['Source'])} {net(body)} "
                         f"{MODEL[t]} l={l*1e6:.4g} w={w*1e6:.4g} m={int(round(m))}")
        elif t in ("Res", "Cap"):
            v = value(d.get("value"))
            if v is None:
                v = 1e3 if t == "Res" else 1e-12
                dev.append(f"{tag}: value not given ({d.get('value')!r}); {v:g} used")
            lines.append(f"{'R' if t == 'Res' else 'C'}{tag} {net(pc['Pos'])} {net(pc['Neg'])} {v:.6g}")
        elif t == "Current":
            v = value(d.get("value"))
            if v is None:
                v = 10e-6
                dev.append(f"{tag}: current not given ({d.get('value')!r}); 10 uA used")
            lines.append(f"I{tag} {net(pc['In'])} {net(pc['Out'])} dc {v:.6g}")
        elif t == "Voltage":
            k = f"VB_{tag}".upper()
            params[k] = value(d.get("value"))
            lines.append(f"V{tag} {net(pc['Positive'])} {net(pc['Negative'])} dc {{{k}}}")
        else:
            raise ValueError(f"{tag}: {t} has no SPICE mapping in this pipeline")
    # bias params are declared by the bench at top level (a .param inside the
    # subckt would shadow the value the bias search sets)
    head = [f"* generated from the circuit record for {name}; flip={flip}",
            f"* bias params: {', '.join(params) or 'none'}",
            f".subckt {name} gnda vdda vinn vinp vout"]
    return "\n".join(head + lines + [".ends", ""]), params, dev
