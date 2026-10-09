"""Two small panels for the overview figure, generated from the run files.

    ov_bode : loop gain and phase of paper A's two-stage amplifier as printed
              in Sky130, with the 0 dB crossing and the measured phase margin
              marked against the reported one.
    ov_conv : the two re-sizing loops, simulation by simulation, in units of
              each metric's tolerance.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_figs as M  # noqa: E402  (style, palette, loaders, save)
import matplotlib.pyplot as plt  # noqa: E402


def panel_bode(w=2.35, h=1.55):
    r = M.jload("cases", "opamp3", "out", "twostage", "result.json")
    f, mag, ph = M._bode("twostage")
    ap = r["as_printed"]
    fig, ax = plt.subplots(2, 1, figsize=(w, h), sharex=True)
    ax[0].semilogx(f, mag, color=M.C1, lw=1.0)
    ax[1].semilogx(f, ph, color=M.C2, lw=1.0)
    ax[0].axhline(0, color=M.INK2, lw=0.5)
    g = ap["gbw_Hz"]
    for a in ax:
        a.axvline(g, color=M.MUTED, lw=0.5, ls=(0, (2, 2)))
    ax[1].plot([g], [ap["pm_deg"]], "o", ms=3, color=M.C2, markeredgecolor="white", markeredgewidth=0.4)
    ax[1].annotate(f"PM {ap['pm_deg']:.0f}°\n(paper: 82°)", xy=(g, ap["pm_deg"]),
                   xytext=(3, 8), textcoords="offset points", fontsize=5.5, color=M.INK)
    ax[0].text(0.03, 0.1, f"{ap['gain_dB']:.0f} dB, {g / 1e6:.0f} MHz", transform=ax[0].transAxes,
               fontsize=5.5, color=M.INK)
    ax[0].set_ylabel("gain (dB)", fontsize=6)
    ax[1].set_ylabel("phase (°)", fontsize=6)
    ax[1].set_xlabel("frequency (Hz)", fontsize=6)
    ax[0].set_xlim(1e-1, 1e9)
    ax[1].set_ylim(-30, 200)
    for a in ax:
        a.tick_params(labelsize=5.5, length=2, pad=1)
    fig.tight_layout(h_pad=0.2, pad=0.15)
    M.save(fig, "ov_bode")


def panel_conv(w=2.35, h=1.55):
    fig, a = plt.subplots(figsize=(w, h))
    runs = [("sizing/twostage", "published loop", M.C4, "s"),
            ("sizing_B/twostage", "local loop", M.C1, "o")]
    for run, lab, col, mk in runs:
        spec = M.jload("cases", "opamp3", run, "spec.json")
        ys = [M._worst(m, spec["fitted"]) for m in M._sizing_series(run)]
        x = list(range(1, len(ys) + 1))
        a.plot(x, [min(y, 30) for y, _ in ys], color=col, lw=1.0, zorder=3, label=lab)
        for xi, (y, ok) in zip(x, ys):
            a.plot([xi], [min(y, 30)], marker=mk, ms=3.5, color=col if ok else "white",
                   markeredgecolor=col, markeredgewidth=0.8, ls="none", zorder=4)
    a.axhline(1.0, color=M.INK2, lw=0.6, ls=(0, (3, 2)))
    a.text(10.3, 1.15, "tolerance", color=M.INK2, fontsize=5.5, ha="right", va="bottom")
    a.set_yscale("log")
    a.set_ylim(0.02, 40)
    a.set_xlim(0.5, 10.5)
    a.set_xlabel("simulation", fontsize=6)
    a.set_ylabel("worst fitted error / tol.", fontsize=6)
    a.tick_params(labelsize=5.5, length=2, pad=1)
    a.legend(fontsize=5.5, frameon=False, loc="upper right", handlelength=1.2, borderpad=0.1)
    fig.tight_layout(pad=0.15)
    M.save(fig, "ov_conv")


if __name__ == "__main__":
    panel_bode()
    panel_conv()
    print("wrote figs/ov_bode.pdf, figs/ov_conv.pdf")
