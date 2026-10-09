"""Blind adjudication packets: prediction and golden netlist shown as readings
A and B (random order), aligned device by device, all nets renamed to neutral
N1..Nk so naming style can't reveal which is which.

  python blind.py PRED_DIR OUT_DIR ID ...   writes OUT_DIR/<id>.txt and key.json
"""
import json
import os
import random
import sys
from pathlib import Path

import score as S


def neutral(pred, gold):
    pg, gg = S.graph(pred), S.graph(gold)
    _, m = S.best_mapping(pg, gg)
    names = {}

    def nm(key):
        if key not in names:
            names[key] = f"N{len(names) + 1}"
        return names[key]
    gdev = [d for d in gold["ckt_netlist"] if S.spec(d)]
    gidx = [i for i, d in enumerate(gold["ckt_netlist"]) if S.spec(d)]
    for d in gdev:                                   # gold nets in gold order
        for n in d["port_connection"].values():
            nm(("g", n))
    pnet = {}
    for v, w in m.items():
        if v[0] == "n":
            pnet[v[1]] = nm(("g", w[1])) if w else None
    rows = {}                                        # slot -> [gold dev, pred dev]
    for k, i in enumerate(gidx):
        rows[("g", i)] = [gold["ckt_netlist"][i], None]
    extra = 0
    for v, w in m.items():
        if v[0] != "d":
            continue
        p = pred["ckt_netlist"][v[1]]
        if w and ("g", w[1]) in rows:
            rows[("g", w[1])][1] = p
        else:
            rows[("p", extra)] = [None, p]
            extra += 1
    out = []
    for key, (g, p) in rows.items():
        gg_ = {"type": g["component_type"], "ports": {k: nm(("g", n)) for k, n in g["port_connection"].items()}} if g else None
        pp_ = None
        if p:
            ports = {}
            for k, n in p["port_connection"].items():
                ports[k] = pnet.get(n) or nm(("p", n))
            pp_ = {"type": p["component_type"], "ports": ports}
        out.append((gg_, pp_))
    return out


def same(a, b):
    if not a or not b or a["type"] != b["type"]:
        return False
    pa, pb = a["ports"], b["ports"]
    if "Gate" in pa:
        k = lambda d: (d.get("Gate"), frozenset([d.get("Drain"), d.get("Source")]), d.get("Body"))
        return k(pa) == k(pb)
    if set(pa) == {"Pos", "Neg"}:
        return frozenset(pa.values()) == frozenset(pb.values())
    return pa == pb


def fmt(d):
    if d is None:
        return "(absent)"
    return f"{d['type']:8s} " + ", ".join(f"{k}={v}" for k, v in sorted(d["ports"].items()))


if __name__ == "__main__":
    pred_dir, out_dir, *ids = sys.argv[1:]
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(int(os.environ.get("BLIND_SEED", "2025")))
    key = {}
    for i in ids:
        pred = json.loads((Path(pred_dir) / f"{i}.json").read_text())
        gold = json.loads((S.VAL / "golden" / f"{i}.json").read_text())
        rows = neutral(pred, gold)
        gold_is_a = rng.random() < 0.5
        key[i] = "A" if gold_is_a else "B"
        lines = [f"Circuit {i}. Two readings of the same diagram, aligned device by device.",
                 "Rows marked * differ. Net names are neutral labels shared by both readings.",
                 "Body is listed only where a reading includes it; MOS Drain/Source are",
                 "interchangeable for scoring, and so are Pos/Neg of Res/Cap/Ind.", ""]
        for k, (g, p) in enumerate(rows):
            a, b = (g, p) if gold_is_a else (p, g)
            mark = " " if same(a, b) else "*"
            lines.append(f"{mark} {k:2d}  A: {fmt(a)}")
            lines.append(f"      B: {fmt(b)}")
        (out / f"{i}.txt").write_text("\n".join(lines) + "\n")
    (out / "key.json").write_text(json.dumps(key, indent=1))
    print(f"wrote {len(ids)} packets to {out}")
