"""Negative control for the claim-verification check.

Every claim in the three case studies carries a quote that the checker found in
the paper, so the check never rejected anything. A safeguard that never fires
is not evidence that it works, so this exercises it against claims that are
deliberately wrong, built mechanically from the real ones:

  digit     one digit of the quoted number is changed -- a misread value, which
            is the failure the check exists to catch
  swapped   the quote is replaced by a real quote from a different paper, so the
            text is genuine but does not belong to this claim
  invented  a fluent sentence in the papers' own register that appears in none
            of them

A corrupted quote that the checker still accepts is a miss, and is reported as
one rather than dropped. Run from the repository root:

    exp_quote_control.py [OUT.json]
"""
import copy
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import compare as CMP  # noqa: E402

ROOT = os.path.join(HERE, "..")
CASES = ["opamp3", "affc", "subvt"]
INVENTED = [
    "the amplifier achieves a measured phase margin of 58.3 degrees",
    "the proposed topology dissipates 12.4 uW from a 1.2 V supply",
    "a unity-gain frequency of 41.7 MHz was obtained in simulation",
]


def _load(case):
    rep = json.load(open(os.path.join(ROOT, "cases", case, "reported.json")))
    d = os.path.join(ROOT, "cases", case)
    tmap = os.path.join(d, "table_ocr.json")
    # the map holds caption -> file; the checker wants caption -> OCR result
    tocr = {cap: json.load(open(os.path.join(d, f)))
            for cap, f in json.load(open(tmap)).items()} if os.path.exists(tmap) else None
    return rep, os.path.join(d, "paper.pdf"), tocr


def _bump_digits(s):
    """Change one digit of the first number, avoiding a no-op."""
    m = re.search(r"\d", s or "")
    if not m:
        return None
    i = m.start()
    # perturb the LAST digit of the first number: a plausible transcription slip
    n = re.match(r"\d+(?:\.\d+)?", s[i:])
    j = i + len(n.group(0)) - 1
    d = s[j]
    return s[:j] + ("8" if d != "8" else "3") + s[j + 1:]


def corrupt(rep, kind, donor_quotes):
    out = copy.deepcopy(rep)
    n = 0
    for circ in out.get("circuits", {}).values():
        for cl in circ.get("claims", []):
            if kind == "digit":
                # the table-image path checks the cell's numbers, the text path the quote
                key = "table_text" if cl.get("from_table_image") else "quote"
                new = _bump_digits(cl.get(key) or cl.get("quote"))
                if new is None:
                    # no digit to alter, so this claim cannot be corrupted this way;
                    # it is excluded rather than counted as a check that failed
                    cl["_skip"] = True
                    continue
                cl[key] = new
            elif kind == "swapped":
                cl["quote"] = donor_quotes[n % len(donor_quotes)]
                cl.pop("from_table_image", None)
            elif kind == "invented":
                cl["quote"] = INVENTED[n % len(INVENTED)]
                cl.pop("from_table_image", None)
            n += 1
    return out, n


def main(out_path=None):
    donors = {}
    for case in CASES:
        rep, _, _ = _load(case)
        donors[case] = [cl["quote"] for c in rep["circuits"].values()
                        for cl in c["claims"] if cl.get("quote")]

    rows, totals = [], {}
    for kind in ("original", "digit", "swapped", "invented"):
        acc = rej = 0
        for case in CASES:
            rep, pdf, tocr = _load(case)
            if kind != "original":
                other = [q for c2, qs in donors.items() if c2 != case for q in qs]
                rep, _ = corrupt(rep, kind, other)
            skipped = {(c, cl["metric"], str(cl.get("value")))
                       for c, circ in rep.get("circuits", {}).items()
                       for cl in circ.get("claims", []) if cl.pop("_skip", False)}
            res = [r for r in CMP.verify_quotes(rep, pdf, tocr)
                   if (r["circuit"], r["metric"], str(r["value"])) not in skipped]
            a = sum(1 for r in res if r["quote_found"])
            acc += a
            rej += len(res) - a
            rows.append(dict(kind=kind, case=case, claims=len(res), accepted=a,
                             rejected=len(res) - a, skipped=len(skipped) if kind != "original" else 0,
                             misses=[dict(metric=r["metric"], value=r["value"], how=r["how"])
                                     for r in res if r["quote_found"]] if kind != "original" else []))
        totals[kind] = dict(accepted=acc, rejected=rej, n=acc + rej,
                            skipped=sum(r.get("skipped", 0) for r in rows if r["kind"] == kind))
    rep_out = dict(totals=totals, per_case=rows)
    if out_path:
        json.dump(rep_out, open(out_path, "w"), indent=2)
    print(f"{'variant':10}{'tested':>8}{'accepted':>10}{'rejected':>10}{'skipped':>9}   expected")
    for kind in ("original", "digit", "swapped", "invented"):
        t = totals[kind]
        exp = "all accepted" if kind == "original" else "all rejected"
        print(f"{kind:10}{t['n']:>8}{t['accepted']:>10}{t['rejected']:>10}"
              f"{t.get('skipped', 0):>9}   {exp}")
    misses = [m for r in rows if r["kind"] != "original" for m in r["misses"]]
    if misses:
        print(f"\n{len(misses)} corrupted claim(s) still accepted:")
        for m in misses[:10]:
            print(f"   {m['metric']:10} {m['value']}  via {m['how']}")
    return rep_out


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
