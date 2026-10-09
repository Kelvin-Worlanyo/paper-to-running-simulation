"""Scorer sanity: golden scores exact against itself; one moved port does not."""
import json
import random
import shutil
import tempfile
from pathlib import Path

import score as S

if __name__ == "__main__":
    rows = S.score(S.VAL / "golden", timeout=5)
    exact = sum(r["iso"] for r in rows)
    print(f"self: {exact}/{len(rows)} exact, "
          f"{sum(len(r['problems']) for r in rows)} schema problems")

    random.seed(0)
    d = Path(tempfile.mkdtemp())
    for f in (S.VAL / "golden").glob("*.json"):
        j = json.loads(f.read_text())
        devs = [x for x in j["ckt_netlist"] if S.spec(x)]
        nets = sorted({n for x in devs for n in x["port_connection"].values()})
        x = random.choice(devs)
        p = random.choice(sorted(x["port_connection"]))
        x["port_connection"][p] = random.choice([n for n in nets if n != x["port_connection"][p]])
        (d / f.name).write_text(json.dumps(j))
    rows = S.score(d, timeout=10)
    geds = sorted(r["ged"] for r in rows)
    print(f"perturbed: {sum(r['iso'] for r in rows)}/{len(rows)} still exact "
          f"(aliased ports can survive a move), GED range {geds[0]}..{geds[-1]}")
    shutil.rmtree(d)
