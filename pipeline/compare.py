"""Block F: reported vs reproduced, and the reproduction level.

Claims come from the paper with verbatim quotes; a quote that is not in the
PDF text layer is rejected before any comparison (a claim without a source is
not a claim). Only claims qualified as measured results are compared.

Levels (each requires the one before):
  0 fails       the netlist does not simulate
  1 simulates   the operating point converges
  2 operates    static checks pass, the unity-gain follower sits at its input
                (right polarity, DC loop closed), every transistor is on and
                saturated, the loop is stable (PM > 0) and the gain exceeds 20 dB
  3 reproduces  every compared metric is within tolerance of the report
"""
import re
import unicodedata

TOL = {                       # stated before any case was run
    "gain_dB": ("abs", 3.0),      # dB
    "gbw_Hz": ("rel", 0.25),
    "pm_deg": ("abs", 10.0),      # degrees
    "power_W": ("rel", 0.25),
}
LEVELS = ["fails", "simulates", "operates", "reproduces"]


def _norm(s):
    s = unicodedata.normalize("NFKC", s)
    s = s.replace("‐", "-").replace("‑", "-").replace("–", "-").replace("−", "-")
    s = re.sub(r"-\s*\n\s*", "", s)
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"\s+([,.;:)\]])", r"\1", s)       # extractors differ on space before punctuation
    return s.strip().lower()


def pdf_text(pdf):
    import pymupdf
    return _norm(" ".join(p.get_text("text") for p in pymupdf.open(pdf)))


_NUM = re.compile(r"\d+(?:\.\d+)?")


def _table_cell_has(ocr, cell_text, value):
    """True if one OCR'd cell of the table contains every number of the claimed
    cell text (or, lacking it, the value). Numbers only: OCR reads unit glyphs
    such as 'um' unreliably, digits reliably."""
    want = _NUM.findall(str(cell_text)) if cell_text else _NUM.findall(f"{value:g}" if isinstance(value, float) else str(value))
    if not want:
        return False
    for row in ocr["cells"]:
        for c in row:
            got = _NUM.findall(c.replace(" ", ""))
            if all(w in got for w in want):
                return True
    return False


def verify_quotes(reported, pdf, table_ocr=None):
    """Text quotes are matched against the PDF text layer. A claim read from a
    table printed as an image (from_table_image) is verified against a cell-wise
    OCR of that table instead: table_ocr maps the table's full caption to the
    OCR result of ingest/table_ocr.py; the claim's quote must be part of it."""
    text = pdf_text(pdf)
    out = []
    for key, circ in reported.get("circuits", {}).items():
        for cl in circ.get("claims", []):
            if cl.get("from_table_image"):
                q = _norm(cl.get("quote", ""))
                cap = next((c for c in (table_ocr or {}) if q and (q in _norm(c) or _norm(c) in q)), None)
                ok = bool(cap) and _table_cell_has(table_ocr[cap], cl.get("table_text"), cl["value"])
                how = f"ocr:{cap}" if ok else "ocr: not found"
            else:
                q = _norm(cl.get("quote", ""))
                ok = bool(q) and q in text
                how = "text layer"
            out.append(dict(circuit=key, metric=cl["metric"], value=cl["value"],
                            quote_found=ok, from_table_image=cl.get("from_table_image", False), how=how))
            cl["quote_found"] = ok
            cl["verified_by"] = how
    return out


def within(metric, sim, rep):
    kind, tol = TOL[metric]
    if sim is None or rep is None:
        return None, None
    if kind == "abs":
        err = sim - rep
        return err, abs(err) <= tol
    err = (sim - rep) / rep
    return err, abs(err) <= tol


def at_load(claims, cl, rl=None):
    """Claims measured at the simulated load: a claim naming a different load
    (e.g. '60 pF // 25 kOhm' when the bench drives 120 pF) is not comparable."""
    def pf(txt):
        m = re.search(r"(\d+(?:\.\d+)?)\s*pF", txt or "")
        return float(m.group(1)) * 1e-12 if m else None
    out = []
    for c in claims:
        v = pf(c.get("load"))
        if v is None or cl is None or abs(v - cl) <= 1e-3 * cl:
            out.append(c)
    return out


# names a paper may use for a metric the bench measures: the bench's GBW is the
# 0 dB crossing of the loop gain, i.e. the unity-gain frequency
ALIASES = {"ugf_Hz": "gbw_Hz", "ugb_Hz": "gbw_Hz", "unity_gbw_Hz": "gbw_Hz"}


def compare(sim, claims):
    rows = []
    for cl in claims:
        m = ALIASES.get(cl["metric"], cl["metric"])
        if m not in TOL or cl.get("qualifier", "measured") != "measured":
            continue
        if not cl.get("quote_found"):          # text or table OCR must verify it
            continue
        err, ok = within(m, sim.get(m), cl["value"])
        if cl.get("bound") == "min" and sim.get(m) is not None:      # reported as "over X"
            ok = sim[m] >= cl["value"] - (TOL[m][1] if TOL[m][0] == "abs" else TOL[m][1] * cl["value"])
        elif cl.get("bound") == "max" and sim.get(m) is not None:    # reported as "under X"
            ok = sim[m] <= cl["value"] + (TOL[m][1] if TOL[m][0] == "abs" else TOL[m][1] * cl["value"])
        rows.append(dict(metric=m, reported=cl["value"], simulated=sim.get(m), error=err,
                         within=ok, quote=cl.get("quote", "")))
    return rows


def level(static_blocking, sim, rows):
    if static_blocking or not sim or not sim.get("converges"):
        return 1 if sim and sim.get("converges") else 0
    op = sim.get("follows") and sim.get("stable") and (sim.get("gain_dB") or 0) > 20 \
        and sim.get("n_mos") and sim.get("n_sat") == sim.get("n_mos")
    if not op:
        return 1
    # a metric reported twice with different values (a disclosure conflict)
    # counts as reproduced if either reported value is matched
    by = {}
    for r in rows:
        by.setdefault(r["metric"], []).append(bool(r["within"]))
    if by and all(any(v) for v in by.values()):
        return 3
    return 2
