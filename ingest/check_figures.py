"""Check a paper's reported numbers against its own response figures.

    check_figures.py CASE_DIR OUT.json

Renders each declared figure region from the PDF, digitises the curve with
digitize_plot, and compares what the figure shows with what the paper's text
and table claim. The figure is an independent witness: a quote check can only
confirm that a number was printed, not that it is the number the simulation
produced.

The per-figure entries below are the declared inputs: which page region holds
the plot, the decade of its leftmost major tick, and -- only where the tick
labels are too small for OCR -- the value of the top tick and the step between
ticks. Tick POSITIONS are always measured. Everything else is derived.
"""
import json
import os
import sys

import pymupdf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import digitize_plot as DP  # noqa: E402

FIGURES = {
    "opamp3": [
        dict(key="telescopic", fig="Fig. 5", page=3, rect=(52, 50, 276, 221),
             left_decade=0,
             reported=dict(gain_dB=52.0, gbw_Hz=193.36e6, pm_deg=82.742)),
        dict(key="folded", fig="Fig. 6", page=3, rect=(52, 260, 280, 488),
             left_decade=1, declared=dict(gain=(60.0, -30.0), phase=(0.0, -50.0)),
             declared_why="tick labels are too small for OCR; positions measured",
             reported=dict(gain_dB=67.0, gbw_Hz=80.2207e6, pm_deg=90.1952),
             reported_alt=dict(gbw_Hz=8.0207e6, where="body text")),
        dict(key="twostage", fig="Fig. 7", page=3, rect=(315, 50, 539, 221),
             left_decade=2,
             reported=dict(gain_dB=70.0, gbw_Hz=28.159e6, pm_deg=82.116)),
    ],
}
DPI = 600


def run(case_dir, out_path):
    name = os.path.basename(os.path.normpath(case_dir))
    specs = FIGURES[name]
    doc = pymupdf.open(os.path.join(case_dir, "paper.pdf"))
    rows = []
    for sp in specs:
        page = doc[sp["page"]]
        pix = page.get_pixmap(dpi=DPI, clip=pymupdf.Rect(*sp["rect"]))
        tmp = os.path.join(os.path.dirname(out_path) or ".", f"_{name}_{sp['key']}.png")
        pix.save(tmp)
        try:
            d = DP.digitize(tmp, sp["left_decade"], declared=sp.get("declared"))
        finally:
            os.remove(tmp)
        r = dict(circuit=sp["key"], figure=sp["fig"], reported=sp["reported"])
        if sp.get("reported_alt"):
            r["reported_alt"] = sp["reported_alt"]
        if not d.get("ok"):
            r["read"] = None
            r["why"] = d["reason"]
        else:
            m = DP.metrics(d)
            r["read"] = m
            r["x_calibration"] = d["x"]
            r["declared_axis"] = bool(sp.get("declared"))
            if sp.get("declared"):
                r["declared_why"] = sp["declared_why"]
            rep = sp["reported"]
            r["ratio_gbw_table_over_figure"] = (
                rep["gbw_Hz"] / m["gbw_Hz"] if m.get("gbw_Hz") else None)
            if "phase_at_gbw_deg" in m:
                r["pm_figure_deg"] = abs(m["phase_at_gbw_deg"])
        rows.append(r)
    json.dump(dict(case=name, dpi=DPI, figures=rows), open(out_path, "w"), indent=1)
    return rows


if __name__ == "__main__":
    for r in run(sys.argv[1], sys.argv[2]):
        if not r["read"]:
            print(f"{r['circuit']:12} {r['figure']}: UNREADABLE -- {r['why']}")
            continue
        m, rep = r["read"], r["reported"]
        pm = r.get("pm_figure_deg")
        print(f"{r['circuit']:12} {r['figure']}  "
              f"gain {m['dc_gain_dB']:5.1f} dB (table {rep['gain_dB']:.0f})   "
              f"GBW {m['gbw_Hz'] / 1e6:7.2f} MHz (table {rep['gbw_Hz'] / 1e6:.3f})   "
              + (f"PM {pm:5.1f} deg (table {rep['pm_deg']:.3f})" if pm else "PM --"))
        if r.get("ratio_gbw_table_over_figure"):
            print(f"{'':12} table / figure GBW = {r['ratio_gbw_table_over_figure']:.1f}x")
