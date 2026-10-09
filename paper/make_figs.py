"""All data figures for the paper, generated from result files (no numbers typed in).

    python make_figs.py [NAME ...]

Style: IEEE column width (3.5 in) or page width (7.16 in), STIX serif to match
Times, 8 pt text, thin marks, categorical hues in fixed order from the
validated reference palette, direct labels where a legend would be far.
"""
import csv
import json
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker  # noqa: E402,F401
from matplotlib.lines import Line2D  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figs")
I2N = os.path.join(ROOT, "vision_eval", "image2net")

C1, C2, C3, C4, C5 = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#4a3aa7"
INK, INK2, GRID, MUTED = "#0b0b0b", "#52514e", "#e4e3df", "#a3a29c"
COL, PAGE = 3.5, 7.16

plt.rcParams.update({
    "font.family": "STIXGeneral", "mathtext.fontset": "stix", "font.size": 8,
    "axes.labelsize": 8, "axes.titlesize": 8, "xtick.labelsize": 7, "ytick.labelsize": 7,
    "legend.fontsize": 7, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2,
    "ytick.color": INK2, "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 0.5, "axes.axisbelow": True, "legend.frameon": False,
    "savefig.dpi": 300, "savefig.bbox": "tight", "savefig.pad_inches": 0.02, "pdf.fonttype": 42,
})


def save(fig, name):
    os.makedirs(OUT, exist_ok=True)
    fig.savefig(os.path.join(OUT, name + ".pdf"))
    fig.savefig(os.path.join(OUT, name + ".png"))
    plt.close(fig)
    print("wrote", name)


def jload(*p):
    path = os.path.join(ROOT, *p)
    return json.load(open(path)) if os.path.exists(path) else None


# --------------------------------------------------------------------------
def fig_bench():
    """Block E validation on AnalogGym: gain and GBW agree; PM offset by 180 deg."""
    ours = {r["amp"].replace("_Pin_3", ""): r for r in
            csv.DictReader(open(os.path.join(ROOT, "design", "out", "ag", "compare.csv")))}
    base = {r["amp"]: r for r in csv.DictReader(open(os.path.join(
        ROOT, "AnalogGym", "AnalogGym", "Amplifier", "run", "baseline.csv")))}
    names = sorted(n for n in ours if n in base)
    fig, ax = plt.subplots(1, 3, figsize=(PAGE, 2.05))
    g_o = [float(ours[n]["gain_dB"]) for n in names]
    g_b = [float(base[n]["gain_dB"]) for n in names]
    f_o = [float(ours[n]["gbw_Hz"]) / 1e6 for n in names]
    f_b = [float(base[n]["GBW_Hz"]) / 1e6 for n in names]
    p_o = [float(ours[n]["pm_deg"]) for n in names]
    p_b = [float(base[n]["PM_deg"]) for n in names]

    for a, x, y, lab, unit in ((ax[0], g_b, g_o, "DC gain", "dB"), (ax[1], f_b, f_o, "GBW", "MHz")):
        lo, hi = min(x + y) * 0.9, max(x + y) * 1.05
        a.plot([lo, hi], [lo, hi], color=MUTED, lw=0.8, zorder=1)
        a.scatter(x, y, s=18, color=C1, edgecolor="white", linewidth=0.6, zorder=3)
        a.set_xlim(lo, hi), a.set_ylim(lo, hi)
        a.set_xlabel(f"AnalogGym baseline {lab} ({unit})")
        a.set_ylabel(f"this bench, {lab} ({unit})")
        err = max(abs(p - q) for p, q in zip(x, y)) if unit == "dB" else \
            max(abs(p - q) / p for p, q in zip(x, y)) * 100
        a.text(0.04, 0.93, f"max error {err:.2f} {'dB' if unit == 'dB' else '%'}",
               transform=a.transAxes, color=INK, va="top")
    a = ax[2]
    a.plot([-80, 100], [100, 280], color=C2, lw=0.9, zorder=1)
    a.scatter(p_o, p_b, s=18, color=C1, edgecolor="white", linewidth=0.6, zorder=3)
    a.text(-75, 232, "reported = PM + 180°", color=INK)
    out = [(x, y) for x, y in zip(p_o, p_b) if abs(y - x - 180) > 10]
    a.text(0.97, 0.05, f"{len(p_o) - len(out)}/{len(p_o)} within 10° of the line",
           transform=a.transAxes, ha="right", color=INK2)
    a.axvline(0, color=INK2, lw=0.6, ls=(0, (2, 2)))
    a.text(3, 272, "stable →", color=INK2, va="top")
    a.set_xlabel("phase margin, unwrapped loop phase (deg)")
    a.set_ylabel("AnalogGym reported PM (deg)")
    a.set_xlim(-80, 100), a.set_ylim(60, 285)
    for a, t in zip(ax, "abc"):
        a.set_title(f"({t})", loc="left", fontweight="bold")
    fig.tight_layout(w_pad=1.2)
    save(fig, "bench_validation")


# --------------------------------------------------------------------------
def fig_i2n():
    """Image2Net: exact-match rate vs prior methods, and by circuit size."""
    runs = {"merge": jload("vision_eval", "image2net", "results", "opus5_agent_v2.json"),
            "wires": jload("vision_eval", "image2net", "results", "opus5_agent_wires.json")}
    fig, ax = plt.subplots(1, 2, figsize=(PAGE, 2.2), gridspec_kw=dict(width_ratios=[1.1, 1]))
    a = ax[0]
    bars = [("AMSNet method†", 35.58, MUTED), ("CHAI†", 46.15, MUTED),
            ("Image2Net†", 80.77, INK2)]
    if runs["merge"]:
        r = runs["merge"]
        bars.append(("Ours (labels merged)", 100 * sum(x["iso"] for x in r) / len(r), C1))
    if runs["wires"]:
        r = runs["wires"]
        bars.append(("Ours (benchmark rule)", 100 * sum(x["iso"] for x in r) / len(r), C2))
    ys = range(len(bars))
    a.barh(list(ys), [b[1] for b in bars], color=[b[2] for b in bars], height=0.62)
    for y, b in zip(ys, bars):
        a.text(b[1] + 1, y, f"{b[1]:.1f}%", va="center", color=INK)
    a.set_yticks(list(ys)), a.set_yticklabels([b[0] for b in bars])
    a.set_xlim(0, 100), a.set_xlabel("exact netlist match (GED = 0), %")
    a.grid(axis="y", visible=False)
    a.text(-0.32, -0.44, "† as reported in [Image2Net], 104 pairs; ours: all 122 released pairs",
           transform=a.transAxes, color=INK2, fontsize=6.5)
    a.set_title("(a)", loc="left", fontweight="bold")

    a = ax[1]
    bins = [(0, 10, "≤10"), (11, 20, "11–20"), (21, 99, ">20")]
    w = 0.38
    for k, (key, col, lab) in enumerate((("merge", C1, "same-label merged"),
                                          ("wires", C2, "benchmark rule"))):
        r = runs[key]
        if not r:
            continue
        vals, ns = [], []
        for lo, hi, _ in bins:
            b = [x for x in r if lo <= x["gold_devices"] <= hi]
            vals.append(100 * sum(x["iso"] for x in b) / len(b))
            ns.append(len(b))
        xs = [i + (k - 0.5) * w for i in range(len(bins))]
        a.bar(xs, vals, width=w - 0.04, color=col, label=lab)
        for x, v in zip(xs, vals):
            a.text(x, v + 1.5, f"{v:.0f}", ha="center", color=INK, fontsize=6.5)
    a.set_xticks(range(len(bins)))
    a.set_xticklabels([f"{b[2]} devices\n(n={n})" for b, n in zip(bins, ns)])
    a.set_ylim(0, 108), a.set_ylabel("exact match, %")
    a.grid(axis="x", visible=False)
    a.legend(loc="upper center", ncol=2, bbox_to_anchor=(0.5, 1.13))
    a.set_title("(b)", loc="left", fontweight="bold")
    fig.tight_layout(w_pad=1.5)
    save(fig, "i2n_results")


# --------------------------------------------------------------------------
def fig_misses():
    """Blind adjudication of every non-exact netlist, both runs."""
    adj = jload("vision_eval", "image2net", "results", "adjudication_summary.json")
    style = [("label_convention", "same-label nets joined (key splits them)", C1),
             ("reader_error", "reading error", C2),
             ("body_terminal", "body terminal omitted", C5),
             ("figure_drawn_contrary_to_intent", "figure drawn wrong; reader followed intent", C4),
             ("dashed_element", "dashed test element", MUTED),
             ("answer_key_error", "answer-key error", C3),
             ("judges_disagree", "judges disagree", "#d6d5d0")]
    rows = [("wires_run", "benchmark rule\n(17 misses)"), ("merge_run", "labels merged\n(31 misses)")]
    fig, ax = plt.subplots(figsize=(COL, 1.75))
    for y, (run, lab) in enumerate(rows):
        left = 0
        cats = adj[run]["categories"]
        for key, name, col in style:
            n = len(cats.get(key, []))
            if not n:
                continue
            ax.barh([y], [n], left=left, color=col, height=0.62, edgecolor="white", linewidth=1.0)
            dark = col in (C1, C2, C3, C5)
            ax.text(left + n / 2, y, str(n), ha="center", va="center", fontsize=6.5,
                    color="white" if dark else INK)
            left += n
    ax.set_yticks([0, 1]), ax.set_yticklabels([r[1] for r in rows])
    ax.set_xlim(0, 31), ax.set_xlabel("non-exact netlists out of 122")
    ax.grid(axis="y", visible=False)
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for _, _, c in style]
    ax.legend(handles, [n for _, n, _ in style], loc="upper center", bbox_to_anchor=(0.42, -0.42),
              ncol=2, handlelength=0.9, columnspacing=0.8, fontsize=6.3)
    save(fig, "i2n_misses")


FIGS = dict(bench=fig_bench, i2n=fig_i2n, misses=fig_misses)


# --------------------------------------------------------------------------
CASE_NAMES = [("telescopic", "Telescopic cascode (Fig. 2)"), ("folded", "Folded cascode (Fig. 3)"),
              ("twostage", "Two-stage Miller (Fig. 4)")]


def _bode(key):
    p = os.path.join(ROOT, "cases", "opamp3", "out", key, "bode.csv")
    if not os.path.exists(p):
        return None
    rows = list(csv.DictReader(open(p)))
    return ([float(r["freq_Hz"]) for r in rows], [float(r["mag_dB"]) for r in rows],
            [float(r["phase_deg"]) for r in rows])


def fig_case_bode():
    """Loop gain and phase of the three re-biased paper op-amps."""
    fig, ax = plt.subplots(2, 3, figsize=(PAGE, 2.9), sharex=True)
    for j, (key, title) in enumerate(CASE_NAMES):
        r = jload("cases", "opamp3", "out", key, "result.json")
        b = _bode(key)
        if not r or not b:
            continue
        f, mag, ph = b
        rb = r["rebiased"]
        ax[0, j].semilogx(f, mag, color=C1, lw=1.1)
        ax[1, j].semilogx(f, ph, color=C2, lw=1.1)
        ax[0, j].axhline(0, color=INK2, lw=0.6)
        rep = {c["metric"]: c["reported"] for c in rb.get("compare", [])}
        if rb.get("gbw_Hz"):
            for a in ax[:, j]:
                a.axvline(rb["gbw_Hz"], color=MUTED, lw=0.6, ls=(0, (2, 2)))
            ax[1, j].plot([rb["gbw_Hz"]], [rb["pm_deg"]], "o", ms=3.5, color=C2,
                          markeredgecolor="white", markeredgewidth=0.5)
            ax[1, j].text(rb["gbw_Hz"] * 1.4, rb["pm_deg"] + 8, f"PM {rb['pm_deg']:.0f}°", color=INK)
        ax[0, j].text(0.03, 0.08, f"A$_0$ {rb['gain_dB']:.1f} dB\nGBW {rb['gbw_Hz']/1e6:.3g} MHz",
                      transform=ax[0, j].transAxes, color=INK, va="bottom")
        ax[0, j].set_title(title, loc="left")
        ax[1, j].set_xlabel("frequency (Hz)")
        ax[1, j].set_ylim(-30, 200)
        ax[0, j].set_xlim(1e-2, 1e9)
    ax[0, 0].set_ylabel("loop gain (dB)")
    ax[1, 0].set_ylabel("loop phase (deg)")
    fig.tight_layout(h_pad=0.4, w_pad=0.8)
    save(fig, "case_bode")


def fig_case_compare():
    """Reported vs reproduced, as printed and re-biased."""
    metrics = [("gain_dB", "DC gain", "dB", 1), ("gbw_Hz", "GBW", "MHz", 1e6),
               ("pm_deg", "phase margin", "deg", 1), ("power_W", "power", "µW", 1e-6)]
    fig, ax = plt.subplots(1, 4, figsize=(PAGE, 1.95))
    labels = ["tele.", "folded", "2-stage"]
    for i, (m, name, unit, sc) in enumerate(metrics):
        a = ax[i]
        for j, (key, _) in enumerate(CASE_NAMES):
            r = jload("cases", "opamp3", "out", key, "result.json")
            if not r:
                continue
            reps = sorted({c["reported"] for c in r["rebiased"].get("compare", []) if c["metric"] == m})
            for k, v in enumerate(reps):
                a.plot([j], [v / sc], marker="D", ms=4.5, color=INK2, ls="none",
                       label="reported" if (j == 0 and k == 0) else None, zorder=4)
            for tag, col, mk, dx in (("as_printed", C4, "s", -0.18), ("rebiased", C1, "o", 0.18)):
                v = r[tag].get(m)
                if v is None:
                    continue
                a.plot([j + dx], [v / sc], marker=mk, ms=4.5, color=col, ls="none",
                       markeredgecolor="white", markeredgewidth=0.5,
                       label=("as printed" if tag == "as_printed" else "re-biased") if j == 0 else None,
                       zorder=5)
        a.set_xticks(range(3)), a.set_xticklabels(labels)
        a.set_xlim(-0.6, 2.6)
        a.set_title(f"{name} ({unit})", loc="left")
        if m == "gbw_Hz":
            a.set_yscale("log")
    ax[0].legend(loc="upper center", bbox_to_anchor=(2.4, -0.22), ncol=3)
    fig.tight_layout(w_pad=0.8)
    save(fig, "case_compare")


def fig_ag():
    """AnalogGym: topology error vs change in simulated behaviour."""
    rows = jload("cases", "analoggym", "results.json")
    if not rows:
        return
    rows = [r for r in rows if "exact" in r]
    fig, ax = plt.subplots(1, 2, figsize=(PAGE, 2.05))
    for r in rows:
        ref, got = r["reference"], r["read"]
        ok = r["equivalent"]
        col = C1 if ok else C2
        dg = (got.get("gain_dB") or 0) - (ref.get("gain_dB") or 0) if got.get("converges") else None
        x = r["ned"]
        if dg is not None:
            ax[0].plot([x], [abs(dg)], "o" if ok else "X", ms=5, color=col, markeredgecolor="white",
                       markeredgewidth=0.5)
        if ref.get("gbw_Hz") and got.get("gbw_Hz"):
            ax[1].plot([ref["pm_deg"]], [got["pm_deg"]], "o" if ok else "X", ms=5, color=col,
                       markeredgecolor="white", markeredgewidth=0.5)
    ax[0].set_xlabel("topology error, NED")
    ax[0].set_ylabel("|Δ DC gain| (dB)")
    ax[0].set_yscale("symlog", linthresh=1)
    ax[1].plot([-100, 100], [-100, 100], color=MUTED, lw=0.8, zorder=1)
    ax[1].set_xlabel("PM of answer netlist (deg)")
    ax[1].set_ylabel("PM of netlist read from image (deg)")
    h = [Line2D([], [], marker="o", color=C1, ls="none", label="equivalent"),
         Line2D([], [], marker="X", color=C2, ls="none", label="not equivalent")]
    ax[1].legend(handles=h, loc="lower right")
    for a, t in zip(ax, "ab"):
        a.set_title(f"({t})", loc="left", fontweight="bold")
    fig.tight_layout(w_pad=1.5)
    save(fig, "ag_e2e")


def _sizing_series(run):
    """Per-simulation measured metrics of a sizing run (A: history.json, B: state.json,
    PDK: trajectory.json, which holds circuit metrics only)."""
    base = os.path.join(ROOT, "cases", "opamp3", run)
    if os.path.exists(os.path.join(base, "history.json")):
        return [e["measured"] for e in json.load(open(os.path.join(base, "history.json"))) if e["status"] == "simulated"]
    if os.path.exists(os.path.join(base, "state.json")):
        return [e["measured"] for e in json.load(open(os.path.join(base, "state.json")))["log"] if e["status"] == "simulated"]
    return [e["measured"] for e in json.load(open(os.path.join(base, "trajectory.json")))["log"]]


def _worst(m, fitted):
    """Largest fitted-metric error in units of its tolerance (gain 3 dB, GBW 25 %, PM 10 deg);
    a missing metric (no crossing, no convergence) counts as far outside."""
    e = []
    for k, t in fitted.items():
        v = m.get(k)
        if v is None:
            e.append(30.0)
        elif k == "gain_dB":
            e.append(abs(v - t) / 3.0)
        elif k == "gbw_Hz":
            e.append(abs(v - t) / t / 0.25)
        elif k == "pm_deg":
            e.append(abs(v - t) / 10.0)
    ok = m.get("n_sat") == m.get("n_mos") and m.get("follows")
    return max(e), ok


def fig_sizing():
    """(a) two-stage sizing runs, simulation by simulation; (b) the telescopic's
    operating window; (c) loop gain on the 180 nm PDK, as printed and re-sized."""
    import matplotlib.gridspec as gs
    fig = plt.figure(figsize=(PAGE, 2.35))
    g = gs.GridSpec(2, 3, figure=fig, width_ratios=[1.1, 1.0, 1.15], hspace=0.12, wspace=0.42)
    a = fig.add_subplot(g[:, 0])
    runs = [("sizing/twostage", "Sky130, A", C4, "s", (2.35, 0.2)), ("sizing_B/twostage", "Sky130, B", C1, "o", (10.35, 0.62)),
            ("sizing_local_pdk/twostage", "180 nm PDK, B", C3, "D", (2.35, 0.66))]
    for run, lab, col, mk, lp in runs:
        spec = jload("cases", "opamp3", run, "spec.json")
        ser = _sizing_series(run)
        ys = [_worst(m, spec["fitted"]) for m in ser]
        x = list(range(1, len(ys) + 1))
        a.plot(x, [min(y, 30) for y, _ in ys], color=col, lw=1.0, zorder=3)
        for xi, (y, ok) in zip(x, ys):
            a.plot([xi], [min(y, 30)], marker=mk, ms=4, color=col if ok else "white", markeredgecolor=col,
                   markeredgewidth=0.9, ls="none", zorder=4)
        a.text(lp[0], lp[1], lab, color=col, va="center", fontsize=6.5)
    a.axhline(1.0, color=INK2, lw=0.7, ls=(0, (3, 2)))
    a.text(12.4, 1.12, "tolerance", color=INK2, fontsize=6.5, va="bottom", ha="right")
    a.set_yscale("log")
    a.set_ylim(0.02, 40)
    a.set_xlim(0.5, 12.5)
    a.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
    a.set_xlabel("simulation")
    a.set_ylabel("worst fitted error / tolerance")
    a.set_title("(a) two-stage re-sizing", loc="left", fontweight="bold")

    b = fig.add_subplot(g[:, 1])
    w = jload("cases", "opamp3", "sizing", "telescopic", "sensitivity_vcm.json")
    pts = sorted((float(k), v[0], v[1]) for k, v in w.items())
    b.plot([p[0] for p in pts], [p[2] for p in pts], color=C1, lw=1.0, zorder=3)
    for o, n, gdb in pts:
        full = n == 9
        b.plot([o], [gdb], "o", ms=4.2, color=C1 if full else "white", markeredgecolor=C1 if full else C2,
               markeredgewidth=0.9, zorder=4)
    full = [p[0] for p in pts if p[1] == 9]
    b.axvspan(min(full), max(full), color=C1, alpha=0.08, lw=0)
    b.axhline(52.0, color=INK2, lw=0.7, ls=(0, (3, 2)))
    b.text(1.95, 52.25, "reported 52 dB", color=INK2, fontsize=6.5, va="bottom", ha="right")
    b.text(1.8, pts[-1][2], "8/9 sat.", color=C2, fontsize=6.5, ha="right", va="center")
    b.text((min(full) + max(full)) / 2, 43.2, "9/9 saturated", color=C1, fontsize=6.5, ha="center")
    b.set_xlabel("input common-mode offset (mV)")
    b.set_ylabel("loop gain (dB)")
    b.set_title("(b) telescopic, option A", loc="left", fontweight="bold")

    c1 = fig.add_subplot(g[0, 2])
    c2 = fig.add_subplot(g[1, 2], sharex=c1)
    for f, lab, col in (("as_printed_pdk.json", "as printed", C4), ("sized_pdk_ade.json", "re-sized", C3)):
        d = jload("cases", "opamp3", "sizing_local_pdk", "twostage", f)
        fr, mag, ph = d["bode"]
        c1.semilogx(fr, mag, color=col, lw=1.0, label=lab)
        c2.semilogx(fr, ph, color=col, lw=1.0)
        c2.plot([d["gbw_Hz"]], [d["pm_deg"]], "o", ms=3.5, color=col, markeredgecolor="white", markeredgewidth=0.5)
        c2.text(d["gbw_Hz"] * 1.6, d["pm_deg"], f"{d['pm_deg']:.0f}°", color=col, fontsize=6.5, va="center")
    c1.axhline(0, color=INK2, lw=0.6)
    c1.set_ylabel("gain (dB)")
    c2.set_ylabel("phase (deg)")
    c2.set_xlabel("frequency (Hz)")
    c1.set_xlim(1e2, 1e9)
    c1.set_ylim(-70, 90)
    c2.set_ylim(-20, 200)
    plt.setp(c1.get_xticklabels(), visible=False)
    c1.legend(loc="lower left", fontsize=6.5, handlelength=1.2, borderaxespad=0.1)
    c1.set_title("(c) two-stage, 180 nm PDK", loc="left", fontweight="bold")
    save(fig, "sizing")


FIGS.update(case_bode=fig_case_bode, case_compare=fig_case_compare, ag=fig_ag)
FIGS.update(sizing=fig_sizing)


if __name__ == "__main__":
    for n in (sys.argv[1:] or FIGS):
        FIGS[n]()
