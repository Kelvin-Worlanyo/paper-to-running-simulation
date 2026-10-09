"""Side by side for one circuit: each mismatched pred device vs its aligned gold
device, with nets translated into gold names."""
import json
import sys
from pathlib import Path

import score as S

if __name__ == "__main__":
    pred_dir, *ids = sys.argv[1:]
    for i in ids:
        pred = json.loads((Path(pred_dir) / f"{i}.json").read_text())
        gold = json.loads((S.VAL / "golden" / f"{i}.json").read_text())
        pg, gg = S.graph(pred), S.graph(gold)
        cost, m = S.best_mapping(pg, gg)
        net = {v[1]: (w[1] if w else None) for v, w in m.items() if v[0] == "n"}
        print(f"== {i}  cost {cost}")
        for v, w in m.items():
            if v[0] != "d":
                continue
            p = pred["ckt_netlist"][v[1]]
            pp = {k: net.get(n) for k, n in p["port_connection"].items()}
            g = gold["ckt_netlist"][w[1]] if w else None
            if g is None or g["component_type"] != p["component_type"] or \
               S.graph({"ckt_netlist": [p | {"port_connection": pp}]}).edges != () and \
               sorted((k, pp[k]) for k in pp) != sorted(g["port_connection"].items()):
                # compare with D/S aliasing
                al = lambda d: (d.get("Gate"), frozenset([d.get("Drain"), d.get("Source")]), d.get("Body")) \
                    if "Gate" in d else (frozenset(d.values()) if set(d) == {"Pos", "Neg"}
                                         else tuple(sorted(d.items())))
                if g and g["component_type"] == p["component_type"] and al(pp) == al(g["port_connection"]):
                    continue
                print(f"  pred #{v[1]:2d} {p['component_type']:5s} {p['port_connection']}")
                print(f"      in gold names  {pp}")
                print(f"  gold #{w[1] if w else '-':>2} {g['component_type'] if g else '':5s} {g['port_connection'] if g else ''}")
