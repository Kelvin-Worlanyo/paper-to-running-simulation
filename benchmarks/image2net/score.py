"""Score predicted netlists against the Image2Net golden set.

A dgl/torch-free port of ci2n_datasets/validation/utils_ged.py. The graph is
built exactly as theirs is, including its quirks, so a score here is a score
there:
  - device nodes typed by device kind, net nodes typed 'net'; edges typed by port
  - MOS drain and source share one edge type (aliased) -- except a 4-terminal
    NMOS, where their create_nmos4 gives the source its own type
  - a MOS carries a body edge only when it has all four ports
  - R, C, L: both ends share one edge type; everything else is polar
  - Gnd/Vdd devices are dropped; their nets are ordinary nets
GED comes from their my_networkx.py (isomorphism checked first, then an
anytime search whose last value at timeout is an upper bound).

NED = GED / (N_device + N_net + N_port) of the golden graph (paper, sec. IV).
The paper runs the search for 2 h per case; we run it briefly and take the
minimum with a mapping-based upper bound (see upper_bound), and report a
lower bound alongside, so a reported GED is never below the true one.
"""
import json
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import networkx as nx

HERE = Path(__file__).parent
VAL = HERE / "ci2n_datasets" / "validation"
sys.path.insert(0, str(VAL))
from my_networkx import my_graph_edit_distance  # noqa: E402

# component_type -> (node type, [(port, edge type), ...]) in their port order
MOS3 = {"PMOS": ("PMOS", [("Drain", "dp2n"), ("Gate", "gp2n"), ("Source", "dp2n")]),
        "NMOS": ("NMOS", [("Drain", "dn2n"), ("Gate", "gn2n"), ("Source", "dn2n")])}
MOS4 = {"PMOS": ("PMOS", [("Drain", "dp2n"), ("Gate", "gp2n"), ("Source", "dp2n"), ("Body", "bp2n")]),
        "NMOS": ("NMOS", [("Drain", "dn2n"), ("Gate", "gn2n"), ("Source", "sn2n"), ("Body", "bn2n")])}
DEVICES = {
    "PNP": ("PNP", [("Collector", "cpnp2n"), ("Base", "bpnp2n"), ("Emitter", "epnp2n")]),
    "NPN": ("NPN", [("Collector", "cnpn2n"), ("Base", "bnpn2n"), ("Emitter", "enpn2n")]),
    "Res": ("R", [("Pos", "r2n"), ("Neg", "r2n")]),
    "Cap": ("C", [("Pos", "c2n"), ("Neg", "c2n")]),
    "Ind": ("L", [("Pos", "l2n"), ("Neg", "l2n")]),
    "Switch": ("S", [("Pos", "s2n"), ("Neg", "s2n")]),
    "Diode": ("DIODE", [("In", "diode_p2n"), ("Out", "diode_n2n")]),
    "Current": ("ISOURCE", [("In", "iin2n"), ("Out", "iout2n")]),
    "Voltage": ("VSOURCE", [("Positive", "vp2n"), ("Negative", "vn2n")]),
    "Diso_amp": ("DISO", [("InP", "diso_vp2n"), ("InN", "diso_vn2n"), ("Out", "diso_vout2n")]),
    "Dido_amp": ("DIDO", [("InP", "dido_vp2n"), ("InN", "dido_vn2n"),
                          ("OutP", "dido_voutp2n"), ("OutN", "dido_voutn2n")]),
    "Siso_amp": ("SISO", [("In", "siso_vin2n"), ("Out", "siso_vout2n")]),
}
PORTS = {k: [p for p, _ in v[1]] for k, v in {**DEVICES, **MOS4}.items()}


def spec(dev):
    t, pc = dev["component_type"], dev["port_connection"]
    if t in MOS3:
        return (MOS4 if len(pc) == 4 else MOS3)[t]
    return DEVICES.get(t)


def graph(netlist):
    g = nx.MultiGraph()
    for i, dev in enumerate(netlist["ckt_netlist"]):
        s = spec(dev)
        if s is None:
            continue                      # Gnd, Vdd, unknown: dropped, as theirs
        ntype, ports = s
        pc = dev["port_connection"]
        g.add_node(("d", i), ntype=ntype)
        for port, etype in ports:
            if port in pc:
                g.add_node(("n", pc[port]), ntype="net")
                g.add_edge(("d", i), ("n", pc[port]), etype=etype)
    return g


def validate(netlist):
    """Problems that would make their parser drop or misread a device."""
    out = []
    for i, d in enumerate(netlist.get("ckt_netlist", [])):
        t, pc = d.get("component_type"), d.get("port_connection", {})
        if t in ("Gnd", "Vdd"):
            continue
        if t not in PORTS:
            out.append(f"#{i} unknown type {t}")
            continue
        need = set(PORTS[t]) - ({"Body"} if t in MOS3 else set())
        if not need <= set(pc) or not set(pc) <= set(PORTS[t]):
            out.append(f"#{i} {t} ports {sorted(pc)}")
    return out


def node_match(a, b):
    return a["ntype"] == b["ntype"]


def edge_match(a, b):
    return a["etype"] == b["etype"]


def edge_match4iso(a, b):
    return next(iter(a.values()))["etype"] == next(iter(b.values()))["etype"]


def size(g):
    return g.number_of_nodes() + g.number_of_edges()   # devices + nets + ports


def ged(g1, g2, timeout):
    if nx.is_isomorphic(g1, g2, node_match, edge_match4iso):
        return 0, True
    best = float("inf")
    for cost in my_graph_edit_distance(g1, g2, node_match, edge_match, timeout=timeout):
        best = int(cost)
    return best, False


# --- Bounds on the same GED (unit costs, networkx defaults) -----------------
# Their anytime search, cut off at a timeout, returns whatever path it last
# improved to; for a netlist one wire off it can report ~100 where the truth
# is 2. Any node mapping is an edit path, so the cost of a good mapping is a
# valid upper bound; type/edge-type multiset differences give a lower bound.
# When the two meet, the GED is exact.

def lower_bound(g1, g2):
    from collections import Counter
    n1 = Counter(d["ntype"] for _, d in g1.nodes(data=True))
    n2 = Counter(d["ntype"] for _, d in g2.nodes(data=True))
    e1 = Counter(d["etype"] for *_, d in g1.edges(data=True))
    e2 = Counter(d["etype"] for *_, d in g2.edges(data=True))
    return (max(sum(n1.values()), sum(n2.values())) - sum((n1 & n2).values())
            + max(sum(e1.values()), sum(e2.values())) - sum((e1 & e2).values()))


def _index(g, n):
    """Nodes padded to n with dummies (type None); adj[i][k] = Counter(etypes)."""
    from collections import Counter, defaultdict
    nodes = list(g.nodes)
    ix = {v: i for i, v in enumerate(nodes)}
    types = [g.nodes[v]["ntype"] for v in nodes] + [None] * (n - len(nodes))
    adj = defaultdict(dict)
    for u, v, d in g.edges(data=True):
        a, b = ix[u], ix[v]
        adj[a].setdefault(b, Counter())[d["etype"]] += 1
        adj[b].setdefault(a, Counter())[d["etype"]] += 1
    return types, adj


def _wl(types, adj, rounds=3):
    """Weisfeiler-Lehman labels per round, for a structure-aware start."""
    lab = [str(t) for t in types]
    out = [lab]
    for _ in range(rounds):
        lab = [lab[i] + "|" + ",".join(sorted(f"{e}:{lab[k]}" for k, c in adj[i].items()
                                              for e in c.elements()))
               for i in range(len(types))]
        lab = [str(hash(x)) for x in lab]
        out.append(lab)
    return out


def upper_bound(g1, g2, iters=40000, restarts=3, seed=0):
    return best_mapping(g1, g2, iters, restarts, seed)[0]


def best_mapping(g1, g2, iters=40000, restarts=3, seed=0):
    """(cost, {g1 node: g2 node or None}) for the cheapest mapping found."""
    import math
    import random
    n = max(g1.number_of_nodes(), g2.number_of_nodes())
    t1, a1 = _index(g1, n)
    t2, a2 = _index(g2, n)

    # start: pair nodes whose WL labels agree, deepest round first, then types
    w1, w2 = _wl(t1, a1), _wl(t2, a2)
    f = [None] * n
    free2 = set(range(n))
    for r in range(len(w1) - 1, -1, -1):
        by = {}
        for j in sorted(free2):
            by.setdefault(w2[r][j], []).append(j)
        for i in range(n):
            if f[i] is None and by.get(w1[r][i]):
                j = by[w1[r][i]].pop()
                f[i] = j
                free2.discard(j)
    rest = sorted(free2)
    for i in range(n):
        if f[i] is None:
            f[i] = rest.pop()

    def node_cost(i, f):
        return 0 if t1[i] == t2[f[i]] else 1

    def pair_cost(i, k, f):
        A = a1[i].get(k)
        B = a2[f[i]].get(f[k])
        if not A and not B:
            return 0
        A, B = A or {}, B or {}
        inter = sum(min(A[e], B.get(e, 0)) for e in A)
        return max(sum(A.values()), sum(B.values())) - inter

    def total(f):
        finv = {j: i for i, j in enumerate(f)}
        c = sum(node_cost(i, f) for i in range(n))
        seen = set()
        for i in range(n):
            ks = set(a1[i]) | {finv[y] for y in a2[f[i]]}
            for k in ks:
                p = (min(i, k), max(i, k))
                if p not in seen:
                    seen.add(p)
                    c += pair_cost(p[0], p[1], f)
        return c

    def local(a, b, f, finv):
        c = node_cost(a, f) + node_cost(b, f)
        seen = set()
        for i in (a, b):
            for k in set(a1[i]) | {finv[y] for y in a2[f[i]]}:
                p = (min(i, k), max(i, k))
                if p not in seen:
                    seen.add(p)
                    c += pair_cost(p[0], p[1], f)
        return c

    best = total(f)
    start = f[:]
    best_f = f[:]
    rng = random.Random(seed)
    for r in range(restarts):
        f = start[:]
        if r:
            for _ in range(n // 4):           # perturb the start on restarts
                a, b = rng.randrange(n), rng.randrange(n)
                f[a], f[b] = f[b], f[a]
        finv = [0] * n
        for i, j in enumerate(f):
            finv[j] = i
        cur = total(f)
        T0, T1 = 2.0, 0.02
        for it in range(iters):
            T = T0 * (T1 / T0) ** (it / iters)
            a, b = rng.randrange(n), rng.randrange(n)
            if a == b:
                continue
            before = local(a, b, f, finv)
            f[a], f[b] = f[b], f[a]
            finv[f[a]], finv[f[b]] = a, b
            d = local(a, b, f, finv) - before
            if d <= 0 or rng.random() < math.exp(-d / T):
                cur += d
                if cur < best:
                    best, best_f = cur, f[:]
            else:
                f[a], f[b] = f[b], f[a]
                finv[f[a]], finv[f[b]] = a, b
    n1, n2 = list(g1.nodes), list(g2.nodes)
    return best, {n1[i]: (n2[best_f[i]] if best_f[i] < len(n2) else None)
                  for i in range(len(n1))}


def score_one(args):
    stem, pred_dir, timeout = args
    gold = json.loads((VAL / "golden" / f"{stem}.json").read_text())
    gg = graph(gold)
    row = {"id": stem, "gold_devices": len(gold["ckt_netlist"]), "norm": size(gg)}
    p = Path(pred_dir) / f"{stem}.json"
    if not p.exists():
        return {**row, "status": "missing", "ged": row["norm"], "ned": 1.0}
    try:
        pred = json.loads(p.read_text())
    except json.JSONDecodeError:
        return {**row, "status": "bad_json", "ged": row["norm"], "ned": 1.0}
    t0 = time.time()
    pg = graph(pred)
    official, iso = ged(pg, gg, timeout)
    lb = ub = 0
    if not iso:
        lb, ub = lower_bound(pg, gg), upper_bound(pg, gg)
    d = min(official, ub) if not iso else 0
    return {**row, "status": "ok", "pred_devices": len(pred.get("ckt_netlist", [])),
            "problems": validate(pred), "iso": iso, "ged_official": official,
            "ged": d, "ged_lb": lb, "exact_ged": iso or d == lb,
            "ned": d / row["norm"], "secs": round(time.time() - t0, 1)}


def score(pred_dir, timeout=60, ids=None, procs=8):
    ids = ids or sorted(p.stem for p in (VAL / "golden").glob("*.json"))
    with Pool(procs) as pool:
        return pool.map(score_one, [(i, str(pred_dir), timeout) for i in ids])


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("pred_dir")
    ap.add_argument("--timeout", type=int, default=60)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    rows = score(a.pred_dir, a.timeout)
    n = len(rows)
    ok = sum(r.get("iso", False) for r in rows)
    print(f"{n} circuits  exact {ok}/{n} = {100*ok/n:.2f}%  "
          f"mean NED {sum(r['ned'] for r in rows)/n:.3f}")
    if a.out:
        Path(a.out).write_text(json.dumps(rows, indent=1))
