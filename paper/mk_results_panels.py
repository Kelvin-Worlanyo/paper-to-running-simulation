"""Every circuit we ran, in both processes, against what its paper reports.

One panel per circuit: the loop gain measured in Sky130 and on the commercial
180 nm PDK, with the operating point each run reached, and a box giving the
paper's reported values beside ours. The reported column is read from the
verified claims at the load actually simulated, so a paper that reports the
same metric twice shows both values.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "pipeline"))
import compare as CMP  # noqa: E402
import make_figs as M  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ROOT = os.path.join(HERE, "..")
# One circuit per outcome rather than all six: a pair that never operates, a
# fully specified pair that does, and a pair carried across a node it was not
# designed for. The rest are in Table~\ref{tab:case}.
CASES = [("opamp3", "telescopic", "Telescopic (paper A)"),
         ("opamp3", "twostage", "Two-stage (paper A)"),
         ("affc", "nmc", "NMC (paper B)")]
SKY, PDK = M.C1, M.C2


def _res(case, sub, key):
    p = os.path.join(ROOT, "cases", case, sub, key, "result.json")
    return json.load(open(p)) if os.path.exists(p) else None


def _shown(r):
    """The re-biased point: that is the run whose loop gain was stored, so the
    numbers in the box describe the curve drawn beside them."""
    return (r.get("rebiased") or {}), "rebiased"


def _bode(case, sub, key):
    if sub == "out":
        p = os.path.join(ROOT, "cases", case, "out", key, "bode.csv")
        if not os.path.exists(p):
            return None
        import csv
        f, m, ph = [], [], []
        for row in csv.DictReader(open(p)):
            f.append(float(row["freq_Hz"])); m.append(float(row["mag_dB"]))
            ph.append(float(row["phase_deg"]))
        return np.array(f), np.array(m), np.array(ph)
    r = _res(case, sub, key)
    for t in ("rebiased", "as_printed"):
        b = (r.get(t) or {}).get("bode") if r else None
        if b:
            return np.array(b[0]), np.array(b[1]), np.array(b[2])
    return None


def reported(case, key, cond):
    claims = json.load(open(os.path.join(ROOT, "cases", case, "reported.json")))
    sel = CMP.at_load(claims["circuits"][key]["claims"], cond["cl"], cond.get("rl"))
    out = {}
    for cl in sel:
        m = CMP.ALIASES.get(cl["metric"], cl["metric"])
        if m in ("gain_dB", "gbw_Hz", "pm_deg") and cl.get("quote_found", True) \
                and cl.get("qualifier", "measured") == "measured":
            if cl["value"] not in out.setdefault(m, []):
                out[m].append(cl["value"])
    return out


def _fmt(metric, vals):
    if not vals:
        return "--"
    def one(v):
        if metric == "gbw_Hz":
            if v >= 1e6:
                return f"{v / 1e6:.3g}M"
            return f"{v / 1e3:.3g}k" if v >= 1e3 else f"{v:.3g}"
        return f"{v:.0f}" if abs(v - round(v)) < 0.05 else f"{v:.1f}"
    return " / ".join(one(v) for v in vals)


def panel(ax, axp, case, key, title):
    rs, rp = _res(case, "out", key), _res(case, "out_pdk", key)
    cond = (rs or rp)["conditions"]
    rep = reported(case, key, cond)
    ours, mark = {}, {}
    for sub, r, lab, col in (("out", rs, "Sky130", SKY), ("out_pdk", rp, "PDK", PDK)):
        b = _bode(case, sub, key)
        if b is not None:
            ax.semilogx(b[0], b[1], color=col, lw=1.1, label=lab)
            axp.semilogx(b[0], b[2], color=col, lw=1.0)
        if r:
            x, _which = _shown(r)
            ours[lab] = x
            mark[lab] = "" if x.get("level") in ("operates", "reproduces") else "*"
            if x.get("gbw_Hz"):
                for a in (ax, axp):
                    a.axvline(x["gbw_Hz"], color=col, lw=0.6, ls=(0, (2, 2)))
                if x.get("pm_deg") is not None:      # the phase margin, where it is read
                    axp.plot([x["gbw_Hz"]], [x["pm_deg"]], "o", ms=2.6, color=col,
                             markeredgecolor="white", markeredgewidth=0.4, zorder=5)
    rows = [("", "paper", "Sky130" + mark.get("Sky130", ""), "PDK" + mark.get("PDK", ""))]
    for m, nm in (("gain_dB", "gain (dB)"), ("gbw_Hz", "GBW (Hz)"), ("pm_deg", "PM (deg)")):
        rows.append((nm, _fmt(m, rep.get(m)),
                     _fmt(m, [ours["Sky130"][m]] if ours.get("Sky130", {}).get(m) is not None else []),
                     _fmt(m, [ours["PDK"][m]] if ours.get("PDK", {}).get(m) is not None else [])))
    txt = "\n".join(f"{a:<9}{b:>11}{c:>9}{d:>9}" for a, b, c, d in rows)
    ax.text(0.018, 0.04, txt, transform=ax.transAxes, fontsize=4.6, family="monospace",
            ha="left", va="bottom", linespacing=1.3,
            bbox=dict(boxstyle="round,pad=0.33", fc="white", ec=M.GRID, lw=0.6, alpha=0.94))
    ax.axhline(0, color=M.INK2, lw=0.5)
    axp.axhline(0, color=M.INK2, lw=0.5)
    ax.set_title(title, fontsize=7.5, loc="left", pad=2)
    ax.set_ylabel("gain (dB)", fontsize=6)
    axp.set_ylabel("phase (deg)", fontsize=6)
    for a in (ax, axp):
        a.tick_params(labelsize=5.5, length=2, pad=1)
        a.grid(alpha=0.22, lw=0.35)
    ax.tick_params(labelbottom=False)
    lo, hi = axp.get_ylim()
    axp.set_ylim(max(lo, -220), min(hi, 220))


def main(w=7.1, h=2.9):
    fig = plt.figure(figsize=(w, h))
    outer = fig.add_gridspec(1, 3, wspace=0.26,
                             left=0.055, right=0.995, top=0.93, bottom=0.135)
    for i, (case, key, title) in enumerate(CASES):
        inner = outer[0, i].subgridspec(2, 1, height_ratios=[2, 1], hspace=0.09)
        ax = fig.add_subplot(inner[0])
        axp = fig.add_subplot(inner[1], sharex=ax)
        panel(ax, axp, case, key, title)
        axp.set_xlabel("frequency (Hz)", fontsize=6)
    fig.axes[0].legend(fontsize=5.5, loc="upper right", frameon=False,
                   handlelength=1.6, borderaxespad=0.25)
    M.save(fig, "results_panels")
    print("wrote results_panels:", ", ".join(c[2] for c in CASES))


if __name__ == "__main__":
    main()
