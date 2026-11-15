"""The figure check, drawn: paper A's two-stage amplifier.

Three witnesses to one quantity on one pair of axes -- the gain curve recovered
from the paper's own Fig. 7, the same circuit simulated from its printed sizes
in Sky130, and the gain-bandwidth product its Table I reports. Nothing of the
published artwork is reproduced: the curve is our measurement of it, redrawn,
so the figure carries a "data from" credit rather than a permission line.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "ingest"))
import make_figs as M  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pymupdf  # noqa: E402

import digitize_plot as DP  # noqa: E402

ROOT = os.path.join(HERE, "..")
RECT, PAGE, LEFT_DECADE = (315, 50, 539, 221), 3, 2
TABLE_GBW = 28.159e6
# our measurement of the published curve, kept beside the case. The artwork is
# the publisher's and is not redistributed; this trace is derived data, so it
# travels with the released runs and lets the figure be rebuilt without the PDF.
TRACE = os.path.join(ROOT, "cases", "opamp3", "figure_trace_fig7.json")


def digitised():
    """The published gain curve, measured off the page.

    With the paper's PDF at hand the curve is re-measured and the trace
    rewritten; without it the recorded trace is used, which is what the public
    artifact tree carries.
    """
    pdf = os.path.join(ROOT, "cases", "opamp3", "paper.pdf")
    if not os.path.exists(pdf):
        t = json.load(open(TRACE))
        return np.array(t["f_Hz"]), np.array(t["gain_dB"]), t["metrics"]
    doc = pymupdf.open(pdf)
    pix = doc[PAGE].get_pixmap(dpi=600, clip=pymupdf.Rect(*RECT))
    tmp = os.path.join(HERE, "_fc.png")
    pix.save(tmp)
    try:
        d = DP.digitize(tmp, LEFT_DECADE)
    finally:
        os.remove(tmp)
    assert d.get("ok"), d.get("reason")
    m = DP.metrics(d)
    json.dump({"what": "paper A Fig. 7, gain curve, traced from the printed "
                       "figure by ingest/digitize_plot.py",
               "page": PAGE, "rect": list(RECT), "left_decade": LEFT_DECADE,
               "f_Hz": list(map(float, d["gain"]["f"])),
               "gain_dB": list(map(float, d["gain"]["v"])),
               "metrics": m}, open(TRACE, "w"), indent=1)
    return np.array(d["gain"]["f"]), np.array(d["gain"]["v"]), m


def best_shift(f_fig, g_fig, f_sim, mag):
    """The frequency scaling that best aligns the published curve with ours."""
    def rms(k):
        f2 = f_fig * k
        lo, hi = max(f2.min(), f_sim.min()), min(f2.max(), f_sim.max())
        if hi <= lo * 10:
            return np.nan
        grid = np.logspace(np.log10(lo), np.log10(hi), 300)
        a = np.interp(np.log10(grid), np.log10(f2), g_fig)
        b = np.interp(np.log10(grid), np.log10(f_sim), mag)
        return float(np.sqrt(np.mean((a - b) ** 2)))
    ks = np.logspace(0, 1.6, 200)
    r = [rms(k) for k in ks]
    k = float(ks[int(np.nanargmin(r))])
    return k, rms(1.0), rms(k)


def panel(w=3.4, h=2.0):
    f_fig, g_fig, m = digitised()
    f_sim, mag, _ph = M._bode("twostage")
    f_sim, mag = np.asarray(f_sim), np.asarray(mag)
    k, r1, rk = best_shift(f_fig, g_fig, f_sim, mag)

    fig, ax = plt.subplots(figsize=(w, h))
    ax.semilogx(f_sim, mag, color=M.C1, lw=1.1, label="our run, the printed sizes")
    ax.semilogx(f_fig, g_fig, color=M.C2, lw=1.1, label="paper's Fig. 7, as published")
    ax.semilogx(f_fig * k, g_fig, color=M.C2, lw=1.0, ls=(0, (3, 2)),
                label=f"the same curve, frequency $\\times${k:.0f}")
    ax.axhline(0, color=M.INK2, lw=0.5)
    ax.axvline(TABLE_GBW, color=M.MUTED, lw=0.8, ls=(0, (1, 1.5)))

    ax.text(TABLE_GBW * 1.6, -24, f"Table I\n{TABLE_GBW / 1e6:.1f} MHz",
            fontsize=5.5, color=M.INK, ha="left", va="top", linespacing=1.15)
    ax.text(0.035, 0.09,
            f"as published, {r1:.0f} dB rms from our run;\nshifted, {rk:.1f} dB",
            transform=ax.transAxes, fontsize=5.5, color=M.INK2, linespacing=1.2)

    ax.set_xlim(1e2, 1e9)
    ax.set_ylim(-45, 85)
    ax.set_xlabel("frequency (Hz)", fontsize=6)
    ax.set_ylabel("gain (dB)", fontsize=6)
    ax.tick_params(labelsize=5.5, length=2, pad=1)
    ax.legend(fontsize=5.5, loc="upper right", frameon=False, handlelength=1.8,
              borderaxespad=0.3)
    fig.tight_layout(pad=0.2)
    M.save(fig, "figcheck")
    print(f"figure GBW {m['gbw_Hz']/1e6:.2f} MHz; best shift x{k:.2f}; "
          f"rms {r1:.2f} -> {rk:.2f} dB")


if __name__ == "__main__":
    panel()
