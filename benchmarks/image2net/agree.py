"""Two independent runs: does agreement between them predict correctness?"""
import json
import sys
from pathlib import Path

import score as S

if __name__ == "__main__":
    a, b = Path(sys.argv[1]), Path(sys.argv[2])
    ra = {r["id"]: r for r in json.loads(Path(f"results/{a.name}.json").read_text())}
    rb = {r["id"]: r for r in json.loads(Path(f"results/{b.name}.json").read_text())}
    rows = []
    for i in sorted(ra):
        ga = S.graph(json.loads((a / f"{i}.json").read_text()))
        gb = S.graph(json.loads((b / f"{i}.json").read_text()))
        same = S.nx.is_isomorphic(ga, gb, S.node_match, S.edge_match4iso)
        rows.append((i, same, ra[i]["iso"], rb[i]["iso"], ra[i]["gold_devices"]))
    n = len(rows)
    both = sum(x and y for _, _, x, y, _ in rows)
    either = sum(x or y for _, _, x, y, _ in rows)
    agree = [r for r in rows if r[1]]
    dis = [r for r in rows if not r[1]]
    print(f"run A exact {sum(r[2] for r in rows)}/{n}, run B exact {sum(r[3] for r in rows)}/{n}")
    print(f"exact in both {both}, in either {either} (best-of-2 oracle {100*either/n:.1f}%)")
    print(f"runs agree on {len(agree)}/{n}: of those, correct {sum(r[2] for r in agree)} "
          f"-> precision {100*sum(r[2] for r in agree)/len(agree):.1f}%")
    print(f"runs disagree on {len(dis)}: at least one wrong by construction; "
          f"A right {sum(r[2] for r in dis)}, B right {sum(r[3] for r in dis)}")
    wrong_b = [r for r in rows if not r[3]]
    caught = sum(1 for r in wrong_b if not r[1])
    print(f"run B's {len(wrong_b)} wrong netlists: flagged by disagreement {caught}, "
          f"silent (A made the same mistake) {len(wrong_b)-caught}: "
          f"{[r[0] for r in wrong_b if r[1]]}")
