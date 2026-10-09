"""GED bounds must bracket the exact GED. Checked on small golden circuits,
where networkx's exact search finishes, after random edits."""
import json
import random

import networkx as nx

import score as S


def edit(j, rng, k):
    devs = [x for x in j["ckt_netlist"] if S.spec(x)]
    nets = sorted({n for x in devs for n in x["port_connection"].values()})
    for _ in range(k):
        x = rng.choice(devs)
        r = rng.random()
        if r < 0.6:                                   # move a port
            p = rng.choice(sorted(x["port_connection"]))
            x["port_connection"][p] = rng.choice(nets + ["new"])
        elif r < 0.8:                                 # flip a MOS type
            if x["component_type"] in ("PMOS", "NMOS"):
                x["component_type"] = {"PMOS": "NMOS", "NMOS": "PMOS"}[x["component_type"]]
        else:                                         # drop a device
            j["ckt_netlist"].remove(x)
            devs.remove(x)
    return j


if __name__ == "__main__":
    rng = random.Random(1)
    small = [f for f in sorted((S.VAL / "golden").glob("*.json"))
             if len(json.loads(f.read_text())["ckt_netlist"]) <= 5]
    bad = exact_hits = n = 0
    for f in small:
        for k in (1, 2, 3):
            gold = json.loads(f.read_text())
            gg = S.graph(gold)
            pg = S.graph(edit(json.loads(f.read_text()), rng, k))
            lb, ub = S.lower_bound(pg, gg), S.upper_bound(pg, gg)
            # search restricted to paths costing <= ub: finds the optimum if
            # ub is achievable, None if it is not (a timed-out unrestricted
            # search can return a worse path than ub, which proves nothing)
            true = nx.graph_edit_distance(pg, gg, S.node_match, S.edge_match,
                                          upper_bound=ub, timeout=300)
            n += 1
            exact_hits += ub == true
            if true is None or not lb <= true <= ub:
                bad += 1
                print("VIOLATION", f.stem, k, lb, true, ub)
    print(f"{n} cases on {len(small)} circuits: bracket violations {bad}, "
          f"upper bound optimal in {exact_hits}/{n}")
