"""Run AnalogGym's three-stage amplifiers through our bench.

Same circuits, same simulator, same test conditions as AnalogGym's own
baseline. The one thing that differs is how phase margin is measured: from the
loop transfer with the phase unwrapped, rather than read off a single wrapped
point.
"""
import csv, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run as R
import plot as P

HERE = os.path.dirname(os.path.abspath(__file__))
AG = os.path.join(HERE, "..", "AnalogGym", "AnalogGym", "Amplifier")


def baseline():
    out = {}
    with open(os.path.join(AG, "run", "baseline.csv")) as fh:
        for row in csv.DictReader(fh):
            out[row["amp"]] = row          # baseline keys drop the _Pin_N suffix
    return out


def build(name, out):
    t = open(os.path.join(HERE, "tb_ag.cir")).read()
    t = (t.replace("__NETLIST__", os.path.abspath(os.path.join(AG, "spice_netlist", name)))
          .replace("__DVARS__", os.path.abspath(os.path.join(AG, "design_variables", name)))
          .replace("__MODELS__", os.path.abspath(R.MODELS))
          .replace("__NAME__", name.lower()).replace("__OUT__", out))
    deck = os.path.join(out, f"{name}.cir")
    open(deck, "w").write(t)
    return deck


def characterise(name):
    out = os.path.join(HERE, "out", "ag", name)
    os.makedirs(out, exist_ok=True)
    deck = build(name, out)
    subprocess.run(["ngspice", "-b", "-o", os.path.join(out, "log.txt"), deck],
                   cwd=HERE, capture_output=True, text=True)
    f, mag, ph = R.read_ac(os.path.join(out, "ac.txt"))
    res, phd = R.measure(f, mag, ph)
    op = open(os.path.join(out, "op.txt")).read()
    res["power_W"] = R.power_from(op)
    return res, (f, mag, phd), out


if __name__ == "__main__":
    base = baseline()
    # netlist files carry the _Pin_N suffix; baseline.csv keys do not
    names = sys.argv[1:] or sorted(os.listdir(os.path.join(AG, "spice_netlist")))
    print(f'{"amplifier":22s} {"gain dB (theirs)":>20s} {"GBW MHz (theirs)":>20s} '
          f'{"PM deg (theirs)":>20s}')
    rows = []
    for n in names:
        try:
            r, (f, mag, phd), out = characterise(n)
        except Exception as e:
            print(f"{n:22s} FAILED {type(e).__name__}: {e}"); continue
        b = base.get(n, {}) or base.get(n.rsplit("_Pin_", 1)[0], {})
        bg, bgbw, bpm = (float(b.get("gain_dB", "nan")), float(b.get("GBW_Hz", "nan")),
                         float(b.get("PM_deg", "nan"))) if b else (float("nan"),) * 3
        if r["gbw_Hz"] is None:
            print(f"{n:22s} no 0 dB crossing"); continue
        print(f'{n:22s} {r["gain_dB"]:9.1f} ({bg:7.1f}) {r["gbw_Hz"]/1e6:10.3f} ({bgbw/1e6:7.3f})'
              f' {r["pm_deg"]:10.1f} ({bpm:7.1f})')
        rows.append((n, r, bg, bgbw, bpm))
        P.plot(os.path.join(out, "bode.svg"), [
            dict(xlabel="frequency (Hz)", ylabel="|A| (dB)", logx=True,
                 series=[(f, mag, P.C1, "gain")],
                 marks=[(r["gbw_Hz"], 0.0, f'GBW {r["gbw_Hz"]/1e6:.2f} MHz')]),
            dict(xlabel="frequency (Hz)", ylabel="phase (deg, unwrapped)", logx=True,
                 series=[(f, phd, P.C2, "phase")],
                 marks=[(r["gbw_Hz"], r["pm_deg"], f'PM {r["pm_deg"]:.1f} deg')]),
        ], title=f"{n}  -  loop gain", sub="Sky130 1.8 V, CL = 500 pF, VCM = 0.45 V, TT, 27 C")
    with open(os.path.join(HERE, "out", "ag", "compare.csv"), "w") as fh:
        fh.write("amp,gain_dB,gain_dB_baseline,gbw_Hz,gbw_Hz_baseline,pm_deg,pm_deg_baseline,power_W\n")
        for n, r, bg, bgbw, bpm in rows:
            fh.write(f'{n},{r["gain_dB"]},{bg},{r["gbw_Hz"]},{bgbw},{r["pm_deg"]},{bpm},{r["power_W"]}\n')
