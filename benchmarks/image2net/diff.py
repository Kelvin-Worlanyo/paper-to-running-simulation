"""What exactly is wrong in a predicted netlist: align it to the golden one
(best_mapping) and list the differences as device-level edits.

  python diff.py PRED_DIR [ID ...]     per-circuit edits + category totals
"""
import json
import sys
from collections import Counter
from pathlib import Path

import score as S

BODY = {"bp2n", "bn2n"}


def label(g, v):
    return f"{g.nodes[v]['ntype']}#{v[1]}"


def edits(pred, gold):
    pg, gg = S.graph(pred), S.graph(gold)
    cost, m = S.best_mapping(pg, gg)
    inv = {w: v for v, w in m.items() if w is not None}
    out = []
    for v, w in m.items():                       # nodes
        if w is None:
            out.append(("extra_net" if v[0] == "n" else "extra_device", label(pg, v)))
        elif pg.nodes[v]["ntype"] != gg.nodes[w]["ntype"]:
            out.append(("device_type", f"{label(pg, v)} is {gg.nodes[w]['ntype']}"))
    for w in gg.nodes:
        if w not in inv:
            out.append(("missing_net" if w[0] == "n" else "missing_device", label(gg, w)))
    # edges, device by device: (etype, net) multisets under the mapping
    for v in pg.nodes:
        if v[0] != "d":
            continue
        w = m.get(v)
        have = Counter((d["etype"], m.get(n)) for _, n, d in pg.edges(v, data=True))
        want = Counter((d["etype"], n) for _, n, d in gg.edges(w, data=True)) if w else Counter()
        for (e, n), c in (have - want).items():
            out.append(("body" if e in BODY else "wiring", f"{label(pg, v)} {e} wrong net"))
    return cost, out


if __name__ == "__main__":
    pred_dir, *ids = sys.argv[1:]
    pred_dir = Path(pred_dir)

    def miss(i):
        g = S.graph(json.loads((S.VAL / "golden" / f"{i}.json").read_text()))
        p = S.graph(json.loads((pred_dir / f"{i}.json").read_text()))
        return not S.nx.is_isomorphic(p, g, S.node_match, S.edge_match4iso)
    ids = ids or [i for i in sorted(p.stem for p in (S.VAL / "golden").glob("*.json")) if miss(i)]
    tot = Counter()
    per = {}
    for i in ids:
        pred = json.loads((pred_dir / f"{i}.json").read_text())
        gold = json.loads((S.VAL / "golden" / f"{i}.json").read_text())
        cost, e = edits(pred, gold)
        cats = Counter(c for c, _ in e)
        per[i] = cats
        tot.update({k: 1 for k in cats})
        print(f"{i} cost {cost:3d}  " + ", ".join(f"{k}:{v}" for k, v in sorted(cats.items())))
        for c, s in e:
            if c not in ("extra_net", "missing_net"):
                print("      ", c, s)
    print("\ncircuits affected per category:", dict(tot.most_common()))
    only = Counter(next(iter(c)) for c in per.values()
                   if len(set(c) - {"extra_net", "missing_net"}) == 1 for c in [set(c) - {"extra_net", "missing_net"}])
    print("circuits whose only error class is:", dict(only))
