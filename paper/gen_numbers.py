"""Every number quoted in the paper, computed from result files.

Writes numbers.tex (\\newcommand macros) and the generated tables. Run after
the experiments; the paper never contains a hand-typed result.
"""
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "vision_eval", "image2net"))
sys.path.insert(0, os.path.join(ROOT, "pipeline"))

M = {}


def j(*p):
    return json.load(open(os.path.join(ROOT, *p)))


def pct(a, b, d=1):
    return f"{100 * a / b:.{d}f}"


# ---------------------------------------------------------------- Image2Net
import score as S  # noqa: E402

r1 = {r["id"]: r for r in j("vision_eval", "image2net", "results", "opus5_agent.json")}
r2 = {r["id"]: r for r in j("vision_eval", "image2net", "results", "opus5_agent_v2.json")}
rw = {r["id"]: r for r in j("vision_eval", "image2net", "results", "opus5_agent_wires.json")}
N = len(rw)
M["INN"] = N
for tag, r in (("One", r1), ("Two", r2), ("Wires", rw)):
    ex = sum(x["iso"] for x in r.values())
    M[f"IIex{tag}"] = ex
    M[f"IIpct{tag}"] = pct(ex, N)
    M[f"IIned{tag}"] = f"{sum(x['ned'] for x in r.values()) / N:.3f}"
M["IInedTwoShort"] = f"{sum(min(x['ged_official'], x['norm']) / x['norm'] for x in r2.values()) / N:.3f}"
M["IInedWiresShort"] = f"{sum(min(x['ged_official'], x['norm']) / x['norm'] for x in rw.values()) / N:.3f}"
M["IIfixed"] = sum(rw[i]["iso"] and not r2[i]["iso"] for i in rw)
M["IIbroken"] = sum(r2[i]["iso"] and not rw[i]["iso"] for i in rw)
M["IIunion"] = sum(rw[i]["iso"] or r2[i]["iso"] for i in rw)
M["IIgoldGeTwenty"] = sum(x["gold_devices"] > 20 for x in rw.values())
M["IImaxDev"] = max(x["gold_devices"] for x in rw.values())
M["IImeanDev"] = f"{sum(x['gold_devices'] for x in rw.values()) / N:.1f}"
for tag, r in (("Two", r2), ("Wires", rw)):
    miss = [x for x in r.values() if not x["iso"]]
    M[f"IImissNed{tag}"] = f"{sum(x['ned'] for x in miss) / len(miss):.3f}"
    for name, lo, hi in (("Small", 0, 10), ("Mid", 11, 20), ("Large", 21, 999)):
        b = [x for x in r.values() if lo <= x["gold_devices"] <= hi]
        M[f"IIn{name}"] = len(b)
        M[f"IIex{name}{tag}"] = sum(x["iso"] for x in b)
        M[f"IIpct{name}{tag}"] = pct(sum(x["iso"] for x in b), len(b), 0)

# agreement between the two same-prompt-family runs
P1 = os.path.join(ROOT, "vision_eval", "image2net", "pred", "opus5_agent")
P2 = os.path.join(ROOT, "vision_eval", "image2net", "pred", "opus5_agent_v2")
agree = 0
for i in r2:
    g1 = S.graph(json.load(open(os.path.join(P1, f"{i}.json"))))
    g2 = S.graph(json.load(open(os.path.join(P2, f"{i}.json"))))
    agree += S.nx.is_isomorphic(g1, g2, S.node_match, S.edge_match4iso)
M["IIagree"] = agree
M["IIsameMistake"] = sum(1 for i in r2 if not r2[i]["iso"] and not r1[i]["iso"])

adj = j("vision_eval", "image2net", "results", "adjudication_summary.json")
for run, pre in (("merge_run", "AdjM"), ("wires_run", "AdjW")):
    M[f"{pre}Total"] = adj[run]["misses"]
    for k, v in adj[run]["categories"].items():
        M[pre + "".join(w.capitalize() for w in k.split("_"))] = len(v)

# ---------------------------------------------------------------- bench validation
ours = {r["amp"].replace("_Pin_3", ""): r for r in
        csv.DictReader(open(os.path.join(ROOT, "design", "out", "ag", "compare.csv")))}
base = {r["amp"]: r for r in csv.DictReader(open(os.path.join(
    ROOT, "AnalogGym", "AnalogGym", "Amplifier", "run", "baseline.csv")))}
names = [n for n in ours if n in base]
M["BVn"] = len(names)
M["BVgainErr"] = f"{max(abs(float(ours[n]['gain_dB']) - float(base[n]['gain_dB'])) for n in names):.2f}"
M["BVgbwErr"] = f"{100 * max(abs(float(ours[n]['gbw_Hz']) - float(base[n]['GBW_Hz'])) / float(base[n]['GBW_Hz']) for n in names):.1f}"
offs = sorted(float(base[n]["PM_deg"]) - float(ours[n]["pm_deg"]) for n in names)
M["BVpmOffMedian"] = f"{offs[len(offs) // 2]:.1f}"
M["BVpmWithinTen"] = sum(abs(o - 180) <= 10 for o in offs)
M["BVstable"] = sum(float(ours[n]["pm_deg"]) > 0 for n in names)
M["BVreportedOver"] = sum(float(base[n]["PM_deg"]) > 90 for n in names)
tv = j("cases", "analoggym", "truth_validation.json")
ok = [r for r in tv if r["pipeline"].get("gain_dB") is not None and r["bench"]]
M["TVn"] = len(ok)
M["TVwithin"] = sum(abs(r["pipeline"]["gain_dB"] - r["bench"]["gain_dB"]) <= 0.05 for r in ok)
M["TVgbwErr"] = f"{100 * max(abs(r['pipeline']['gbw_Hz'] - r['bench']['gbw_Hz']) / r['bench']['gbw_Hz'] for r in ok):.2f}"

# ---------------------------------------------------------------- AnalogGym image -> simulation
LABELLED = {"Fan_SMC", "Leung_NMCF", "Leung_NMCNR", "Ramos_PFC", "Sau_CFCC"}   # text visible in image
ag = [r for r in j("cases", "analoggym", "results.json") if "exact" in r]
M["AGn"] = len(ag)
M["AGexact"] = sum(r["exact"] for r in ag)
M["AGlabelled"] = sum(r["name"] in LABELLED for r in ag)
M["AGlabelledExact"] = sum(r["exact"] for r in ag if r["name"] in LABELLED)
M["AGunlabelled"] = sum(r["name"] not in LABELLED for r in ag)
M["AGunlabelledExact"] = sum(r["exact"] for r in ag if r["name"] not in LABELLED)
sim_ok = [r for r in ag if r["reference"].get("converges")]
M["AGsim"] = len(sim_ok)
M["AGequiv"] = sum(r["equivalent"] for r in sim_ok)
M["AGexactEquiv"] = sum(r["equivalent"] for r in sim_ok if r["exact"])
M["AGexactSim"] = sum(r["exact"] for r in sim_ok)
wrong = [r for r in ag if not r["exact"]]
M["AGwrong"] = len(wrong)
M["AGwrongFlagged"] = sum(bool(r["erc"]) for r in wrong)
M["AGrightFlagged"] = sum(bool(r["erc"]) for r in ag if r["exact"])
M["AGpolarityAgree"] = sum(r["polarity_check_agrees_with_labels"] for r in ag if r["exact"])

with open(os.path.join(HERE, "tab_ag.tex"), "w") as fh:
    fh.write("\\begin{tabular}{@{}lcrcrrrrc@{}}\n\\toprule\n")
    fh.write(" & text & & & & \\multicolumn{2}{c}{gain (dB)} & \\multicolumn{2}{c}{PM (deg)}\\\\\n")
    fh.write("\\cmidrule(lr){6-7}\\cmidrule(lr){8-9}\n")
    fh.write("Amplifier & in image & dev. & exact & checks & ans. & read & ans. & read\\\\\n\\midrule\n")
    for r in ag:
        f = lambda x, k: (f"{x[k]:.1f}" if isinstance(x.get(k), (int, float)) else "--")
        chk = "pass" if not r["erc"] else f"{len(r['erc'])} flag" + ("s" if len(r["erc"]) > 1 else "")
        exact = "\\checkmark" if r["exact"] else f"NED {r['ned']:.2f}"
        name = r["name"].replace("_", "\\_")
        text = "yes" if r["name"] in LABELLED else "no"
        fh.write(f"{name} & {text} & {r['devices_true']} & {exact} & {chk} & "
                 f"{f(r['reference'], 'gain_dB')} & {f(r['read'], 'gain_dB')} & "
                 f"{f(r['reference'], 'pm_deg')} & {f(r['read'], 'pm_deg')}\\\\\n")
    fh.write("\\bottomrule\n\\end{tabular}\n")

# ---------------------------------------------------------------- case study
CASES = [("telescopic", "Telescopic"), ("folded", "Folded cascode"), ("twostage", "Two-stage")]
case = {k: j("cases", "opamp3", "out", k, "result.json") for k, _ in CASES
        if os.path.exists(os.path.join(ROOT, "cases", "opamp3", "out", k, "result.json"))}
rep = j("cases", "opamp3", "reported.json")
M["CSclaims"] = sum(len(c["claims"]) for c in rep["circuits"].values())
M["CSquotes"] = sum(bool(cl.get("quote_found")) for c in rep["circuits"].values() for cl in c["claims"])
recs = {k: j("cases", "opamp3", "records", f"{k}.json") for k, _ in CASES}
M["CSdevices"] = sum(len([d for d in r["ckt_netlist"] if d.get("role", "core") in ("core", "bias")])
                     for r in recs.values())
M["CSabsent"] = sum(len(r.get("absent", [])) for r in recs.values())


def unit(m, v):
    if v is None:
        return "--"
    if m == "gbw_Hz" and v < 1e3:          # below the MHz column's resolution
        return "$<$0.001"
    if m == "power_W" and v < 1e-6:        # sub-microwatt (subthreshold designs)
        return f"{v * 1e6:.3f}" if v >= 1e-9 else "$<$0.001"
    return {"gain_dB": f"{v:.1f}", "gbw_Hz": f"{v / 1e6:#.3g}".rstrip("."), "pm_deg": f"{v:.1f}",
            "power_W": f"{v * 1e6:.1f}"}[m]


case_pdk = {k: j("cases", "opamp3", "out_pdk", k, "result.json") for k, _ in CASES
            if os.path.exists(os.path.join(ROOT, "cases", "opamp3", "out_pdk", k, "result.json"))}
import compare as CMP  # noqa: E402

# second paper: Lee & Mok, AFFC vs NMC (claims partly from an image table, verified by OCR)
CASES_B = [("affc", "AFFC"), ("nmc", "NMC")]
CASES_C = [("subvt180", "Subthreshold")]
PAPERS = [("opamp3", CASES, "Paper A: 180\\,nm op-amps"), ("affc", CASES_B, "Paper B: three-stage AFFC / NMC"),
          ("subvt", CASES_C, "Paper C: subthreshold two-stage, 0.5\\,V")]
PAPERS = [p_ for p_ in PAPERS if os.path.exists(os.path.join(ROOT, "cases", p_[0], "reported.json"))]


def _res(case_dir, sub, k):
    f = os.path.join(ROOT, "cases", case_dir, sub, k, "result.json")
    return json.load(open(f)) if os.path.exists(f) else None


def _rep_cell(m, claims):
    vs, lo = [], False
    for cl in claims:
        if CMP.ALIASES.get(cl["metric"], cl["metric"]) != m or not cl.get("quote_found", True) \
                or cl.get("qualifier", "measured") != "measured":
            continue
        if cl["value"] not in vs:
            vs.append(cl["value"])
        lo = lo or cl.get("bound") == "min"
    if not vs:
        return "--"
    txt = " / ".join(unit(m, v) for v in vs)
    return ("$>$" + txt) if lo else txt


# system-level outcome: what the pipeline delivered for every circuit-process pair
_RANK = {"fails": 0, "simulates": 1, "operates": 2, "reproduces": 3}
_lv = {0: "fails", 1: "simulates", 2: "operates", 3: "reproduces"}
_pairs, _best = 0, []
for cdir, cases_, _t in PAPERS:
    for k, _n in cases_:
        for sub in ("out", "out_pdk"):
            r = _res(cdir, sub, k)
            if not r:
                continue
            _pairs += 1
            _best.append(max(_RANK.get((r.get(t) or {}).get("level"), 0)
                             for t in ("as_printed", "rebiased")))
M["SysPairs"] = _pairs
M["SysOperates"] = sum(1 for b in _best if b >= 2)
M["SysSimulates"] = sum(1 for b in _best if b == 1)
M["SysReproduces"] = sum(1 for b in _best if b >= 3)

with open(os.path.join(HERE, "tab_case.tex"), "w") as fh:
    fh.write("\\begin{tabular}{@{}lllrrrrl@{}}\n\\toprule\n")
    fh.write("Circuit & Process & & Gain (dB) & GBW (MHz) & PM (deg) & Power ($\\mu$W) & Level\\\\\n")
    for pi, (cdir, cases_, title) in enumerate(PAPERS):
        rep_ = j("cases", cdir, "reported.json")
        fh.write("\\midrule\n\\multicolumn{8}{@{}l}{\\textit{" + title + "}}\\\\\n\\midrule\n")
        for ci, (k, name) in enumerate(cases_):
            r = _res(cdir, "out", k)
            rp = _res(cdir, "out_pdk", k)
            claims = rep_["circuits"][k]["claims"]
            ref = r or rp
            if ref:
                claims = CMP.at_load(claims, ref["conditions"]["cl"], ref["conditions"].get("rl"))
            cells = [_rep_cell(m, claims) for m in ("gain_dB", "gbw_Hz", "pm_deg", "power_W")]
            fh.write(f"{name} & & reported & {' & '.join(cells)} & \\\\\n")
            for proc, res_ in (("Sky130", r), ("180\\,nm PDK", rp)):
                if not res_:
                    continue
                for n_, (tag, lab) in enumerate((("as_printed", "as printed"), ("rebiased", "re-biased"))):
                    x = res_[tag]
                    sat = f"{x.get('n_sat')}/{x.get('n_mos')}"
                    fh.write(f" & {proc if n_ == 0 else ''} & {lab} & {unit('gain_dB', x.get('gain_dB'))} & {unit('gbw_Hz', x.get('gbw_Hz'))} & "
                             f"{unit('pm_deg', x.get('pm_deg'))} & {unit('power_W', x.get('power_W'))} & "
                             f"\\emph{{{x['level']}}} ({sat} sat.)\\\\\n")
            if ci != len(cases_) - 1:
                fh.write("\\cmidrule(l){2-8}\n")
    fh.write("\\bottomrule\n\\end{tabular}\n")

# second-paper counts and per-circuit numbers
repB = j("cases", "affc", "reported.json")
clB = [cl for c in repB["circuits"].values() for cl in c["claims"]]
M["CSBclaims"] = len(clB)
M["CSBtext"] = sum(1 for c in clB if c.get("verified_by") == "text layer")
M["CSBocr"] = sum(1 for c in clB if str(c.get("verified_by", "")).startswith("ocr:TABLE"))
M["CSBunverified"] = sum(1 for c in clB if not c.get("quote_found"))
recsB = {k: j("cases", "affc", "records", f"{k}.json") for k, _ in CASES_B}
M["CSBdevices"] = sum(len([d for d in r["ckt_netlist"] if d.get("role", "core") in ("core", "bias")]) for r in recsB.values())
M["CSBabsent"] = sum(len(r.get("absent", [])) for r in recsB.values())
for k, _ in CASES_B:
    for sub, pre in (("out", "CS"), ("out_pdk", "Pdk")):
        r = _res("affc", sub, k)
        if not r:
            continue
        t = pre + k.capitalize()
        for tag, suf in (("rebiased", ""), ("as_printed", "Printed")):
            x = r[tag]
            M[f"{t}Gain{suf}"] = f"{x['gain_dB']:.1f}" if x.get("gain_dB") is not None else "--"
            M[f"{t}Gbw{suf}"] = f"{x['gbw_Hz'] / 1e6:.3g}" if x.get("gbw_Hz") else "--"
            M[f"{t}Pm{suf}"] = f"{x['pm_deg']:.1f}" if x.get("pm_deg") is not None else "--"
            M[f"{t}Power{suf}"] = f"{x['power_W'] * 1e6:.1f}" if x.get("power_W") else "--"
            M[f"{t}Sat{suf}"] = x.get("n_sat")
            M[f"{t}Mos{suf}"] = x.get("n_mos")
            M[f"{t}Level{suf}"] = x["level"]
        M[f"{t}Dev"] = len(r.get("deviations", []))
        if "search_simulations" in r:
            M[f"{t}Search"] = r["search_simulations"]
for k, _ in CASES:
    r = case.get(k)
    if not r:
        continue
    t = k.capitalize()
    M[f"CS{t}Printed"] = r["as_printed"]["level"]
    M[f"CS{t}Rebiased"] = r["rebiased"]["level"]
    M[f"CS{t}Dev"] = len(r["deviations"])
    M[f"CS{t}Inv"] = str(r.get("inverting_input"))

# per-circuit case numbers (re-biased point unless stated)
import math
for k, _ in CASES:
    r = case.get(k)
    if not r:
        continue
    t = k.capitalize()
    for tag, suf in (("rebiased", ""), ("as_printed", "Printed")):
        x = r[tag]
        M[f"CS{t}Gain{suf}"] = f"{x['gain_dB']:.1f}" if x.get("gain_dB") is not None else "--"
        M[f"CS{t}Gbw{suf}"] = f"{x['gbw_Hz'] / 1e6:.3g}" if x.get("gbw_Hz") else "--"
        M[f"CS{t}Pm{suf}"] = f"{x['pm_deg']:.1f}" if x.get("pm_deg") is not None else "--"
        M[f"CS{t}Power{suf}"] = f"{x['power_W'] * 1e6:.1f}" if x.get("power_W") else "--"
        M[f"CS{t}Sat{suf}"] = x.get("n_sat")
        M[f"CS{t}Mos{suf}"] = x.get("n_mos")
        M[f"CS{t}Vcm{suf}"] = f"{x['vcm']:.1f}"
for k, _ in CASES:
    r = case_pdk.get(k)
    if not r:
        continue
    t = "Pdk" + k.capitalize()
    for tag, suf in (("rebiased", ""), ("as_printed", "Printed")):
        x = r[tag]
        M[f"{t}Gain{suf}"] = f"{x['gain_dB']:.1f}" if x.get("gain_dB") is not None else "--"
        M[f"{t}Gbw{suf}"] = f"{x['gbw_Hz'] / 1e6:.3g}" if x.get("gbw_Hz") else "--"
        M[f"{t}Pm{suf}"] = f"{x['pm_deg']:.1f}" if x.get("pm_deg") is not None else "--"
        M[f"{t}Power{suf}"] = f"{x['power_W'] * 1e6:.1f}" if x.get("power_W") else "--"
        M[f"{t}Sat{suf}"] = x.get("n_sat")
        M[f"{t}Mos{suf}"] = x.get("n_mos")
        M[f"{t}Level{suf}"] = x["level"]
        M[f"{t}Vcm{suf}"] = f"{x['vcm']:.1f}"
    M[f"{t}Search"] = r["search_simulations"]

# a bound from the paper's own numbers: single-stage OTA, GBW = gm/(2 pi CL),
# gm <= I_D / (n kT/q) <= I_D / 25.9 mV at 300 K (weak-inversion limit, n >= 1)
claims = {cl["metric"]: cl["value"] for cl in rep["circuits"]["telescopic"]["claims"]}
itot = claims["power_W"] / 1.8
cl_t = 20e-12                                   # C0 = 20 pF on the telescopic figure
gm_max = (itot / 2) / 0.02585                   # at most half the supply current per input device
gbw_max = gm_max / (2 * math.pi * cl_t)
M["BDitot"] = f"{itot * 1e6:.1f}"
M["BDgm"] = f"{gm_max * 1e3:.2f}"
M["BDgbw"] = f"{gbw_max / 1e6:.1f}"
M["BDrep"] = f"{claims['gbw_Hz'] / 1e6:.2f}"
M["BDratio"] = f"{claims['gbw_Hz'] / gbw_max:.0f}"

# ---------------------------------------------------------------- re-sizing (step 5)
# runs: the published loop (calibration table in the prompt) and our local loop
#       (relative feedback only); the PDK run uses the local loop on 180 nm
RUNS = [("SzAtwo", "sizing/twostage", "published", "Sky130"), ("SzBtwo", "sizing_B/twostage", "local", "Sky130"),
        ("SzAtel", "sizing/telescopic", "published", "Sky130"), ("SzBtel", "sizing_B/telescopic", "local", "Sky130"),
        ("SzPtwo", "sizing_local_pdk/twostage", "local", "PDK")]
sz = {}
for tag, run, mode, proc in RUNS:
    f = j("cases", "opamp3", run, "final.json")
    spec = j("cases", "opamp3", run, "spec.json")
    m = f["measured"]
    sz[tag] = dict(f=f, spec=spec, mode=mode, proc=proc)
    M[f"{tag}Sims"] = f["simulations"]
    M[f"{tag}Calls"] = f.get("llm_calls") or f.get("rounds")
    M[f"{tag}Sat"] = f"{m['n_sat']}/{m['n_mos']}"
    M[f"{tag}Gain"] = f"{m['gain_dB']:.1f}"
    M[f"{tag}Gbw"] = f"{m['gbw_Hz'] / 1e6:.1f}"
    M[f"{tag}Pm"] = f"{m['pm_deg']:.1f}"
    M[f"{tag}PowerMw"] = f"{m['power_W'] * 1e3:.2f}"
    M[f"{tag}PowerUw"] = f"{m['power_W'] * 1e6:.0f}"
    pw = spec["held_out"].get("power_W")
    if pw:
        M[f"{tag}PowerRatio"] = f"{m['power_W'] / pw:.0f}" if m["power_W"] / pw >= 10 else f"{m['power_W'] / pw:.1f}"
leak_b = [j("cases", "opamp3", r, x, "leak_audit.json") for r in ("sizing_B/twostage", "sizing_B/telescopic")
          for x in sorted(os.listdir(os.path.join(ROOT, "cases", "opamp3", r))) if x.startswith("llm_")
          and os.path.exists(os.path.join(ROOT, "cases", "opamp3", r, x, "leak_audit.json"))]
M["LeakPrompts"] = len(leak_b)
M["LeakChecked"] = f"{sum(a['checked'] for a in leak_b):,}".replace(",", "{,}")
M["LeakHits"] = sum(len(a["leaked"]) for a in leak_b)
M["SzPReported"] = f"{j('cases', 'opamp3', 'sizing_local_pdk', 'twostage', 'spec.json')['held_out']['power_W'] * 1e6:.1f}"
# telescopic (A) common-mode window: offsets in mV -> [n_sat, gain]
win = j("cases", "opamp3", "sizing", "telescopic", "sensitivity_vcm.json")
offs = sorted((float(k), v) for k, v in win.items())
full = [o for o, v in offs if v[0] == 9]
M["WinLo"] = f"{min(full):g}".replace("-", "$-$")
M["WinHi"] = f"{max(full):g}"
M["WinLose"] = f"{min(o for o, v in offs if v[0] < 9 and o > 0):g}"
M["WinGainLo"] = f"{dict(offs)[min(full)][1]:.1f}"
M["WinGainHi"] = f"{dict(offs)[max(full)][1]:.1f}"


def _cell(run, metric):
    f = sz[run]["f"]
    row = next((r for r in f["compare"] if r["metric"] == metric), None)
    if row is None:
        return "--"
    v = row["simulated"]
    txt = {"gain_dB": f"{v:.1f}", "gbw_Hz": f"{v / 1e6:.1f}", "pm_deg": f"{v:.1f}",
           "power_W": (f"{v * 1e3:.2f}" + r"\,m" if v >= 1e-3 else f"{v * 1e6:.0f}" + r"\,$\mu$")}[metric]
    txt += "" if metric != "power_W" else "W"
    mark = r"\,\checkmark" if row["within"] else r"\,$\times$"
    held = row["group"] == "held_out"
    return (r"\textit{" + txt + "}" if held else txt) + mark


with open(os.path.join(HERE, "tab_sizing.tex"), "w") as fh:
    fh.write("\\begin{tabular}{@{}llccrrcrrrr@{}}\n\\toprule\n")
    fh.write("Circuit & Process & Loop & Conv. & LLM & Sim. & Sat. & Gain (dB) & GBW (MHz) & PM ($^\\circ$) & Power\\\\\n\\midrule\n"
             )
    for tag, name in (("SzAtwo", "Two-stage"), ("SzBtwo", ""), ("SzPtwo", ""), ("SzAtel", "Telescopic"), ("SzBtel", "")):
        f = sz[tag]["f"]
        conv = "yes" if f["converged"] else "no"
        proc = "180\\,nm PDK" if sz[tag]["proc"] == "PDK" else "Sky130"
        fh.write(f"{name} & {proc} & {sz[tag]['mode']} & {conv} & {M[tag + 'Calls']} & {M[tag + 'Sims']} & {M[tag + 'Sat']} & "
                 f"{_cell(tag, 'gain_dB')} & {_cell(tag, 'gbw_Hz')} & {_cell(tag, 'pm_deg')} & {_cell(tag, 'power_W')}\\\\\n"
                 .replace("\\\\\\\\", "\\\\"))
        if tag == "SzPtwo":
            fh.write("\\midrule\n")
    fh.write("\\bottomrule\n\\end{tabular}\n")

# ---------------------------------------------------------------- PDK back end: placer
pl = j("cases", "pdk_placer", "results.json")
M["PlN"] = len(pl)
M["PlDevMin"] = min(r["devices"] for r in pl)
M["PlDevMax"] = max(r["devices"] for r in pl)
M["PlDevTotal"] = sum(r["devices"] for r in pl)
M["PlErr"] = sum(r["errors"] + r["tb_errors"] for r in pl)
M["PlMis"] = sum(r["mismatches"] + r["tb_mismatches"] for r in pl)
M["PlWarn"] = sum(r["warnings"] + r["tb_warnings"] for r in pl)
NAMES = {"TWOSTAGE": "Two-stage (case)", "FOLDED": "Folded cascode (case)", "TELESCOPIC": "Telescopic (case)",
         "AG_NMCNR": "Leung\\_NMCNR (AnalogGym)", "AG_AZC": "Qu2017\\_AZC (AnalogGym)"}
with open(os.path.join(HERE, "tab_placer.tex"), "w") as fh:
    fh.write("\\begin{tabular}{@{}lrrrcc@{}}\n\\toprule\n")
    fh.write("Circuit record & dev. & MOS & nets & errors / warn. & mismatches\\\\\n\\midrule\n")
    for r in pl:
        fh.write(f"{NAMES[r['cell']]} & {r['devices']} & {r['mos']} & {r['nets']} & "
                 f"{r['errors'] + r['tb_errors']} / {r['warnings'] + r['tb_warnings']} & {r['mismatches'] + r['tb_mismatches']}\\\\\n"
                 .replace("\\\\\\\\", "\\\\"))
    fh.write("\\bottomrule\n\\end{tabular}\n")

# ---------------------------------------------------------------- PDK back end: numbers
ade = j("cases", "opamp3", "sizing_local_pdk", "twostage", "ade_check.json")
a, b = ade["design_environment_netlist"], ade["sizing_loop"]
M["PdkAgree"] = f"{100 * max(abs(a[k] - b[k]) / abs(b[k]) for k in ('gain_dB', 'gbw_Hz', 'pm_deg', 'power_W')):.2f}"
ap = j("cases", "opamp3", "sizing_local_pdk", "twostage", "as_printed_pdk.json")
M["PdkPrGain"] = f"{ap['gain_dB']:.1f}"
M["PdkPrGbw"] = f"{ap['gbw_Hz'] / 1e6:.1f}"
M["PdkPrPm"] = f"{ap['pm_deg']:.1f}"
M["PdkPrPower"] = f"{ap['power_W'] * 1e6:.0f}"
tr = j("cases", "opamp3", "sizing_local_pdk", "twostage", "trajectory.json")
M["PdkFirstGain"] = f"{tr['log'][0]['measured']['gain_dB']:.1f}"
M["PdkFirstGbw"] = f"{tr['log'][0]['measured']['gbw_Hz'] / 1e6:.1f}"
M["PdkFirstPm"] = f"{tr['log'][0]['measured']['pm_deg']:.1f}"

# third paper: subthreshold two-stage op-amp, 180 nm, 0.5 V
if os.path.exists(os.path.join(ROOT, "cases", "subvt", "reported.json")):
    repC = j("cases", "subvt", "reported.json")
    clC = [cl for c in repC["circuits"].values() for cl in c["claims"]]
    M["CSCclaims"] = len(clC)
    M["CSCverified"] = sum(1 for c in clC if c.get("quote_found"))
    recC = j("cases", "subvt", "records", "subvt180.json")
    M["CSCdevices"] = len([d for d in recC["ckt_netlist"] if d.get("role", "core") in ("core", "bias")])
    for sub, pre in (("out", "CS"), ("out_pdk", "Pdk")):
        r = _res("subvt", sub, "subvt180")
        if not r:
            continue
        t = pre + "Subvt"
        for tag, suf in (("rebiased", ""), ("as_printed", "Printed")):
            x = r[tag]
            M[f"{t}Gain{suf}"] = f"{x['gain_dB']:.1f}" if x.get("gain_dB") is not None else "--"
            M[f"{t}Gbw{suf}"] = f"{x['gbw_Hz'] / 1e3:.3g}" if x.get("gbw_Hz") else "--"
            M[f"{t}Pm{suf}"] = f"{x['pm_deg']:.1f}" if x.get("pm_deg") is not None else "--"
            M[f"{t}Power{suf}"] = f"{x['power_W'] * 1e9:.0f}" if x.get("power_W") else "--"
            M[f"{t}Sat{suf}"] = x.get("n_sat")
            M[f"{t}Mos{suf}"] = x.get("n_mos")
            M[f"{t}Level{suf}"] = x["level"]
        M[f"{t}Dev"] = len(r.get("deviations", []))

# ---------------------------------------------------------------- the grid (node x specification)
# Placement is computed, not assigned: node relation from the paper's stated node
# and the process simulated; specification from the circuit record.
import re as _re
import circuit as CIR  # noqa: E402

NODE_NM = {"Sky130": 130, "PDK": 180}


def _paper_node(case_dir):
    v = j("cases", case_dir, "reported.json")["process"]["value"]
    m = _re.search(r"(\d+(?:\.\d+)?)\s*(nm|um|µm)", v)
    return float(m.group(1)) * (1000 if m.group(2) != "nm" else 1)


def _spec_col(rec):
    mos = [d for d in rec["ckt_netlist"] if d["component_type"] in CIR.MOS and d.get("role", "core") not in CIR.HARNESS]
    unsized = sum(CIR.value((d.get("size") or {}).get("w")) is None or CIR.value((d.get("size") or {}).get("l")) is None
                  for d in mos)
    bias_missing = sum(1 for d in rec["ckt_netlist"] if d["component_type"] == "Voltage" and d.get("role") == "bias"
                       and CIR.value(d.get("value")) is None) + \
        sum(1 for a in rec.get("absent", []) if "bias" in (str(a.get("why", "")) + str(a.get("item", ""))).lower())
    if unsized:
        return 2, unsized, len(mos), bias_missing
    return (1 if bias_missing else 0), unsized, len(mos), bias_missing


LEVEL_ORDER = ["fails", "simulates", "operates", "reproduces"]
LVCOL = {"fails": "lvFail", "simulates": "lvSim", "operates": "lvOp", "reproduces": "lvRep", "ref": "lvRef"}
cells = {(r, c): [] for r in (0, 1) for c in (0, 1, 2)}
grid_rows = []
for cdir, cases_, tag in [(p_[0], p_[1], "ABC"[i]) for i, p_ in enumerate(PAPERS)]:
    pn = _paper_node(cdir)
    for k, name in cases_:
        rec = j("cases", cdir, "records", f"{k}.json")
        col, uns, nmos, bmiss = _spec_col(rec)
        for proc, sub in (("PDK", "out_pdk"), ("Sky130", "out")):
            r = _res(cdir, sub, k)
            if not r:
                continue
            row = 0 if abs(NODE_NM[proc] - pn) < 1 else 1
            lv_p, lv_r = r["as_printed"]["level"], r["rebiased"]["level"]
            best = max(lv_p, lv_r, key=LEVEL_ORDER.index)
            if best in ("operates", "reproduces"):
                how = "as printed" if lv_p == best else "re-biased"
            else:                       # not operating: say how close the best point came
                bx = max((r["as_printed"], r["rebiased"]), key=lambda x: x.get("n_sat") or 0)
                how = f"(best {bx.get('n_sat')}/{bx.get('n_mos')} sat.)"
            note = ""
            if cdir == "opamp3" and k == "twostage":
                note = (f"; re-sized: targets met, power {M['SzAtwoPowerRatio']}$\\times$" if proc == "Sky130"
                        else f"; re-sized: targets met, power {M['SzPtwoPowerRatio']}$\\times$")
            if cdir == "opamp3" and k == "telescopic" and proc == "Sky130":
                note = "; re-sized: operates in a mV window"
            cells[(row, col)].append((best, f"{name.split()[0]} ({tag}), {'180\\,nm PDK' if proc == 'PDK' else 'Sky130'}: "
                                            f"\\emph{{{best}}} {how}{note}"))
            grid_rows.append(dict(circuit=k, paper=tag, process=proc, row=row, col=col, best=best, how=how,
                                  unsized=uns, mos=nmos, bias_missing=bmiss))
# AnalogGym: fully specified, run in the open PDK it was designed in
cells[(0, 0)].append(("ref", f"AnalogGym ({M['BVn']} amplifiers), Sky130: run as shipped; gain and GBW "
                                  f"match, reported PM off by 180$^\\circ$"))
json.dump(grid_rows, open(os.path.join(HERE, "grid_cells.json"), "w"), indent=1)

COLS = ["Sizes and biases given", "Sizes given, biases missing", "Sizes missing (in part)"]
PATH = {(0, 0): "run as printed", (0, 1): "derive the missing biases", (0, 2): "fill sizes by policy, re-bias",
        (1, 0): "re-bias, then re-size to the reported targets", (1, 1): "derive biases, then re-size",
        (1, 2): "fill sizes, re-bias, re-size; hold metrics out"}
ROWS = ["Same node\\newline {\\scriptsize (as the paper states it)}", "Different node"]
with open(os.path.join(HERE, "grid_fig.tex"), "w") as fh:
    fh.write("% generated by gen_numbers.py -- do not edit\n\\begin{figure*}[t]\n\\centering\n\\footnotesize\n")
    fh.write("\\renewcommand{\\arraystretch}{1.25}\n")
    fh.write("\\begin{tabular}{@{}>{\\raggedright}p{2.1cm}|>{\\raggedright}p{4.75cm}|>{\\raggedright}p{4.75cm}|>{\\raggedright\\arraybackslash}p{4.75cm}@{}}\n")
    fh.write(" & \\textbf{" + "} & \\textbf{".join(COLS) + "}\\\\\n\\hline\n")
    for r in (0, 1):
        fh.write(f"\\textbf{{{ROWS[r]}}}")
        for c in (0, 1, 2):
            items = sorted(cells[(r, c)], key=lambda t: -(LEVEL_ORDER.index(t[0]) if t[0] in LEVEL_ORDER else -1))
            body = f"\\textit{{path: {PATH[(r, c)]}}}\\par\\smallskip "
            body += " \\par ".join(f"\\lv{{{LVCOL[lv]}}}\\,{txt}" for lv, txt in items) if items else \
                "\\textcolor{black!45}{no case yet}"
            fh.write(f" & {body}")
        fh.write("\\\\\n\\hline\n" if r == 0 else "\\\\\n")
    fh.write("\\end{tabular}\n\n\\smallskip\n{\\scriptsize \\lv{lvRep}\\,reproduces\\quad \\lv{lvOp}\\,operates\\quad "
             "\\lv{lvSim}\\,simulates\\quad \\lv{lvFail}\\,fails\\quad \\lv{lvRef}\\,reference design}\n")
    fh.write("\\caption{Where a paper sits, and what the designer gets. Rows: the node the paper states against the "
             "designer's. Columns: how completely the paper specifies the circuit. Each cell gives the pipeline path "
             "it calls for and every circuit we ran there, with the highest level reached. Placement is computed from "
             "the record and the stated node.}\n"
             "\\label{fig:grid}\n\\end{figure*}\n")
M["GridEmpty"] = sum(1 for v in cells.values() if not v)

# ---------------------------------------------------------------- time per step
ts = j("cases", "affc", "timing_steps.json")
pdk_t = {l.split()[0]: float(l.split()[1]) for l in open(os.path.join(ROOT, "cases", "pdk_placer", "timing.txt")) if l.strip()}
rb = {"Sky130": [], "PDK": []}
nsim = []
for cdir, cases_ in [(p_[0], p_[1]) for p_ in PAPERS]:
    for k, _ in cases_:
        for proc, sub in (("Sky130", "out"), ("PDK", "out_pdk")):
            r = _res(cdir, sub, k)
            if r and r.get("timing_s"):
                rb[proc].append(r["timing_s"]["rebias"])
            if r and sub == "out_pdk" and r.get("search_simulations"):
                nsim.append(r["search_simulations"])


def _rng(v, unit="min", scale=60.0, fmt="{:.0f}"):
    if not v:
        return "--"
    lo, hi = min(v) / scale, max(v) / scale
    return (fmt.format(lo) + "--" + fmt.format(hi) if fmt.format(lo) != fmt.format(hi) else fmt.format(lo)) + f"\\,{unit}"


rows = [
    ("Ingest, verified crops (A)", "find and crop the figures and tables",
     f"{ts['ingest_pagemap_s'] + ts['crops_2_figures_s']:.0f}\\,s per paper"),
    ("Read a schematic (B+C)", "transcribe devices, nets, sizes, sources",
     f"{min(ts['agents_s']['read_affc'], ts['agents_s']['read_nmc']) / 60:.1f}--{max(ts['agents_s']['read_affc'], ts['agents_s']['read_nmc']) / 60:.1f}\\,min per figure"),
    ("Claims, quote check, table OCR", "collect the reported numbers and conditions",
     f"{ts['agents_s']['claims'] / 60:.1f}\\,min + {ts['quote_check_s'] + ts['table_ocr_s']:.0f}\\,s"),
    ("Checks (D)", "sanity-check the transcribed netlist", "$<$1\\,s"),
    ("As printed (E)", "build a testbench, first simulation", "1--3\\,s"),
    ("Bias re-derivation (E), Sky130", "tune biases for the local process", _rng(rb["Sky130"])),
    ("Bias re-derivation (E), PDK", "tune biases in the foundry flow",
     _rng(rb["PDK"]) + (f" ({min(nsim):,}--{max(nsim):,} sims)".replace(",", "{,}") if nsim else "")),
    ("PDK setup, once per install", "map devices, set up models",
     f"{pdk_t['devmap'] + pdk_t['setup']:.0f}\\,s"),
    ("Place + check, netlist + simulate", "draw schematic and testbench, run it",
     f"{pdk_t['place']:.1f}\\,s + {pdk_t['sim']:.0f}\\,s"),
    ("Re-size (G), per LLM call", "re-target the design to the paper's numbers",
     f"{ts['sizing_llm_call_s']['round0'] / 60:.1f}--{ts['sizing_llm_call_s']['round1'] / 60:.1f}\\,min; 2--18 sims per run"),
]
with open(os.path.join(HERE, "tab_time.tex"), "w") as fh:
    fh.write("\\begin{tabular}{@{}p{3.1cm}p{3.1cm}p{1.9cm}@{}}\n\\toprule\n")
    fh.write("Step & Manual task it replaces & Measured\\\\\n\\midrule\n")
    for a, b, c in rows:
        fh.write(f"{a} & {b} & {c}\\\\\n")
    fh.write("\\bottomrule\n\\end{tabular}\n")
M["TimeRebiasSkyMax"] = _rng(rb["Sky130"]).split("--")[-1] if rb["Sky130"] else "--"
M["TimeNcirc"] = len(rb["Sky130"]) + len(rb["PDK"])

with open(os.path.join(HERE, "numbers.tex"), "w") as fh:
    fh.write("% generated by gen_numbers.py -- do not edit\n")
    for k, v in M.items():
        assert k.isalpha(), k
        fh.write(f"\\newcommand{{\\{k}}}{{{v}}}\n")
print(f"{len(M)} macros")
for k, v in M.items():
    print(f"  {k} = {v}")
