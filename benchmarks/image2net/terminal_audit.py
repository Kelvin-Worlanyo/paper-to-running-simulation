"""Per-terminal and per-net audit of a prediction run against the answer key.

Exact match (graph isomorphism) answers "is the whole netlist right?". A
reviewer asked the finer question: when a reading is not exact, how much of it
is right? This scores two things the benchmark's single number hides:

  devices    a predicted device is correct when the alignment pairs it with a
             gold device of the same type
  terminals  a terminal is correct when its device is correct and the net it
             connects to is the net the aligned gold terminal connects to,
             with the same port role (drain, gate, source, body, ...)

The alignment is the cheapest node mapping score.best_mapping finds, which is
the same machinery the edit distance uses, so nothing here is more generous
than the benchmark's own scorer.

    python terminal_audit.py pred/opus5_agent_wires [--json out.json]
"""
import collections
import json
import os
import sys

import networkx as nx
from networkx.algorithms import isomorphism

import score as S


def _terminals(g):
    """{device node: {port role: net node}} (multi-edges keep one per role)."""
    out = {}
    for n, attrs in g.nodes(data=True):
        if n[0] != "d":
            continue
        roles = {}
        for _, nb, ed in g.edges(n, data=True):
            roles.setdefault(ed["etype"], set()).add(nb)
        out[n] = roles
    return out


def audit_one(pred_path, gold_path):
    pred = json.load(open(pred_path))
    gold = json.load(open(gold_path))
    gp, gg = S.graph(pred), S.graph(gold)
    # When the two graphs are isomorphic, use that mapping: it is exact, and the
    # heuristic search below occasionally misses it, which would understate a
    # correct reading. Otherwise fall back to the cheapest mapping found, so the
    # numbers for inexact readings are a lower bound on how much is right.
    gm = isomorphism.MultiGraphMatcher(gg, gp, node_match=S.node_match,
                                       edge_match=S.edge_match4iso)
    if gm.is_isomorphic():
        mapping = gm.mapping
    else:
        _, mapping = S.best_mapping(gg, gp)      # gold node -> pred node

    tg, tp = _terminals(gg), _terminals(gp)
    dev_tot = dev_ok = term_tot = term_ok = 0
    for gd, groles in tg.items():
        dev_tot += 1
        pd = mapping.get(gd)
        same_type = (pd is not None and pd in tp
                     and gg.nodes[gd]["ntype"] == gp.nodes[pd]["ntype"])
        if same_type:
            dev_ok += 1
        for role, gnets in groles.items():
            term_tot += len(gnets)
            if not same_type:
                continue
            pnets = tp[pd].get(role, set())
            # a gold terminal is correct when the aligned pred device carries
            # the same role onto the aligned net
            for gn in gnets:
                if mapping.get(gn) in pnets:
                    term_ok += 1
    nets_g = sum(1 for n in gg.nodes if n[0] == "n")
    nets_p = sum(1 for n in gp.nodes if n[0] == "n")
    return dict(devices=dev_tot, devices_ok=dev_ok,
                terminals=term_tot, terminals_ok=term_ok,
                nets_gold=nets_g, nets_pred=nets_p)


def main(pred_dir, out_json=None):
    gold_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "ci2n_datasets", "validation", "golden")
    rows, tot = [], collections.Counter()
    for f in sorted(os.listdir(pred_dir)):
        if not f.endswith(".json"):
            continue
        gold = os.path.join(gold_dir, f)
        if not os.path.exists(gold):
            continue
        r = audit_one(os.path.join(pred_dir, f), gold)
        r["id"] = f[:-5]
        rows.append(r)
        for k, v in r.items():
            if k != "id":
                tot[k] += v
    print(f"circuits            {len(rows)}")
    print(f"devices             {tot['devices_ok']}/{tot['devices']} "
          f"= {100 * tot['devices_ok'] / tot['devices']:.1f}% correct type under alignment")
    print(f"device terminals    {tot['terminals_ok']}/{tot['terminals']} "
          f"= {100 * tot['terminals_ok'] / tot['terminals']:.1f}% on the right net with the right role")
    print(f"nets                {tot['nets_pred']} predicted vs {tot['nets_gold']} in the key")
    if out_json:
        json.dump(dict(total=dict(tot), per_circuit=rows), open(out_json, "w"), indent=1)
        print("wrote", out_json)


if __name__ == "__main__":
    a = sys.argv[1:]
    out = None
    if "--json" in a:
        i = a.index("--json")
        out = a[i + 1]
        a = a[:i] + a[i + 2:]
    main(a[0], out)
