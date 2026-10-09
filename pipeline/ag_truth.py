"""AnalogGym answer netlists as circuit records (the reference for block B/E).

AnalogGym ships, for each amplifier, a schematic screenshot and a parameterised
SPICE netlist. Resolving the design_variables gives a fully sized circuit in
the same record format the reading agent writes, so the two can be aligned,
scored and simulated through identical code.
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
AG = os.path.join(HERE, "..", "AnalogGym", "AnalogGym", "Amplifier")
KV = re.compile(r"(\w+)\s*=\s*'([^']*)'|(\w+)\s*=\s*(\S+)")
SI = {"f": 1e-15, "p": 1e-12, "n": 1e-9, "u": 1e-6, "m": 1e-3, "k": 1e3}


def _num(s):
    m = re.fullmatch(r"([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)(meg|[fpnumk])?", s.strip().lower())
    if not m:
        return None
    return float(m.group(1)) * (1e6 if m.group(2) == "meg" else SI.get(m.group(2) or "", 1.0))


def params(name):
    txt = open(os.path.join(AG, "design_variables", name)).read()
    return {k: _num(v) for k, v in re.findall(r"(\w+)\s*=\s*([-\d.eE+]+[a-zA-Z]*)", txt)}


def _eval(expr, pars):
    e = expr.strip().strip("'")
    for k in sorted(pars, key=len, reverse=True):
        if pars[k] is not None:
            e = re.sub(rf"\b{k}\b", repr(pars[k]), e)
    n = _num(e)
    if n is not None:
        return n
    try:
        return float(eval(e, {"__builtins__": {}}, {}))
    except Exception:
        return None


def record(name, with_body=True):
    pars = params(name)
    lines = open(os.path.join(AG, "spice_netlist", name)).read().splitlines()
    head = next(l for l in lines if l.lower().startswith(".subckt")).split()
    ports = [p.upper() for p in head[2:]]          # gnda vdda vinn vinp vout
    dev = []
    for l in lines:
        s = l.strip()
        if not s or s[0] in "*.+":
            continue
        tok = s.split()
        k = tok[0][0].lower()
        if k == "x" and len(tok) >= 6 and "fet" in tok[5]:
            d, g, src, b = (t.upper() for t in tok[1:5])
            kv = {(a or c).lower(): (x or y) for a, x, c, y in KV.findall(" ".join(tok[6:]))}
            w, ln, m = (_eval(kv.get(z, "1"), pars) for z in ("w", "l", "m"))
            pc = {"Drain": d, "Gate": g, "Source": src}
            if with_body:
                pc["Body"] = b
            dev.append(dict(id=tok[0], role="core",
                            component_type="PMOS" if "pfet" in tok[5] else "NMOS",
                            port_connection=pc,
                            size=dict(w=f"{w * 1e-6:.6g}", l=f"{ln * 1e-6:.6g}", m=f"{m:g}")))
        elif k in "icr" and len(tok) >= 4:
            a, b = tok[1].upper(), tok[2].upper()
            v = _eval(" ".join(tok[3:]), pars)
            t = {"i": "Current", "c": "Cap", "r": "Res"}[k]
            pc = {"In": a, "Out": b} if t == "Current" else {"Pos": a, "Neg": b}
            dev.append(dict(id=tok[0], role="core", component_type=t, port_connection=pc,
                            value=f"{v:.6g}" if v is not None else None))
    pm = dict(zip(["gnd", "vdd", "inn", "inp", "out"], ports))
    return {"ckt_type": "DISO-Amplifier", "source": f"AnalogGym {name}",
            "pins": {"vdd": pm["vdd"], "gnd": pm["gnd"], "out": pm["out"],
                     "in": [pm["inn"], pm["inp"]]},
            "ckt_netlist": dev}


if __name__ == "__main__":
    import json
    import sys
    r = record(sys.argv[1])
    print(json.dumps(r, indent=1)[:2000])
