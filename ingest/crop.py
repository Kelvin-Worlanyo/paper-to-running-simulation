"""The rectangle a figure caption names, and a gate that refuses a bad one.

Everything downstream of block B reads pixels from here, and the failure mode
is silent: a clipped schematic still yields a netlist that parses, and every
later stage runs happily on the wrong circuit. So this module proposes
rectangles from geometry and is allowed to REJECT them, but a model is never
permitted to move an edge - only to pick among candidates or refuse.

The candidate is a band, bounded by three things that are all measured:

    one side   the caption itself
    sides      the column the caption sits in
    other side the nearest line that is real prose, or another caption

A caption does not always sit under its figure. IEEE prints it below; ACM
prints many above, and AMSnet-KG's appendix figures are all captioned from
above - 12 of its 28 figures had no band at all while only the space above the
caption was searched. Both sides are tried and the one holding more ink wins.

Within the band, a born-digital page is tightened to the ink actually there.
A scan cannot be: the whole page is one image, so the band IS the answer, and
this is why docclass runs first.

Global figure zones are deliberately not used. Merging every graphics box on a
page joins neighbouring figures across the text between them - measured on
AMSnet-KG p6, where two figures and the prose between them become one 42%
region. A band is bounded by the caption it belongs to, so it cannot.
"""

MIN_H = 30.0          # a band shorter than this holds no schematic
MIN_W = 40.0
PROSE_FRAC = 0.55     # a line this wide, in its column, is a paragraph
PROSE_CHARS = 40


def _lines_of_page(m, page):
    return next((p for p in m["pages"] if p["n"] == page), None)


def _ink(pg, r):
    """Area of graphics inside r, ignoring a page-sized scan substrate."""
    page_area = pg["w"] * pg["h"]
    tot = 0.0
    for g in pg["graphics"]:
        a = (g[2] - g[0]) * (g[3] - g[1])
        if a < 100 or a > 0.5 * page_area:
            continue
        ix = max(0.0, min(r[2], g[2]) - max(r[0], g[0]))
        iy = max(0.0, min(r[3], g[3]) - max(r[1], g[1]))
        tot += ix * iy
    return tot


def band(m, cap, side="above"):
    """The caption's figure band on one side, from geometry alone."""
    pg = _lines_of_page(m, cap["page"])
    if not pg:
        return None
    line = next((l for l in pg["lines"] if l["idx"] == cap["idx"]), None)
    if not line:
        return None
    col = line["col"]
    cl, cr = pg["bounds"][col] if col < len(pg["bounds"]) else pg["bounds"][0]
    top = line["bbox"][1]

    bot = line["bbox"][3]
    if side == "above":
        run = sorted([l for l in pg["lines"] if l["col"] == col and l["bbox"][3] <= top + 1],
                     key=lambda l: -l["bbox"][1])
        stop = 0.0
    else:
        run = sorted([l for l in pg["lines"] if l["col"] == col and l["bbox"][1] >= bot - 1],
                     key=lambda l: l["bbox"][1])
        stop = float(pg["h"])
    for l in run:
        wide = (l["bbox"][2] - l["bbox"][0]) > PROSE_FRAC * (cr - cl)
        if l["kind"] in ("caption", "section", "subsection") or \
           (l["kind"] == "body" and wide and len(l["text"]) > PROSE_CHARS):
            stop = l["bbox"][3] if side == "above" else l["bbox"][1]
            break
    r = ((cl - 4, stop + 3, cr + 4, top - 2) if side == "above"
         else (cl - 4, bot + 2, cr + 4, stop - 3))
    return r if (r[3] - r[1]) >= MIN_H and (r[2] - r[0]) >= MIN_W else None


def tighten(m, cap, b):
    """Shrink a band to the graphics inside it. Born-digital pages only."""
    pg = _lines_of_page(m, cap["page"])
    if not pg or not b:
        return b
    hits = [g for g in pg["graphics"]
            if g[0] < b[2] and g[2] > b[0] and g[1] < b[3] and g[3] > b[1]
            and (g[2] - g[0]) * (g[3] - g[1]) > 100]
    if not hits:
        return b
    x0 = max(b[0], min(g[0] for g in hits) - 4)
    y0 = max(b[1], min(g[1] for g in hits) - 4)
    x1 = min(b[2], max(g[2] for g in hits) + 4)
    y1 = min(b[3], max(g[3] for g in hits) + 4)
    t = (x0, y0, x1, y1)
    return t if (y1 - y0) >= MIN_H and (x1 - x0) >= MIN_W else b


def candidates(m, cap, doc_class):
    """Rectangles to consider, best first. A model may pick or refuse, never move."""
    pg = _lines_of_page(m, cap["page"])
    bands = [b for b in (band(m, cap, "above"), band(m, cap, "below")) if b]
    if not bands or not pg:
        return []
    bands.sort(key=lambda b: -_ink(pg, b))     # the side the figure is actually on
    out = []
    for b in bands:
        if doc_class.get("document_class") == "born_digital":
            t = tighten(m, cap, b)
            if t != b:
                out.append(t)
        out.append(b)
    return out


def check(m, cap, r):
    """Deterministic gate. Returns a list of reasons the crop is unusable."""
    bad = []
    pg = _lines_of_page(m, cap["page"])
    if not r or not pg:
        return ["no band"]
    if (r[3] - r[1]) < MIN_H or (r[2] - r[0]) < MIN_W:
        bad.append("degenerate")
    # ink continuing past an edge means the figure is bigger than the crop.
    # The page-sized image on a scan is not ink: it is the page itself, and it
    # crosses every boundary by construction, so it is excluded here.
    page_area = pg["w"] * pg["h"]
    for g in pg["graphics"]:
        area = (g[2] - g[0]) * (g[3] - g[1])
        if area < 100 or area > 0.5 * page_area:
            continue
        inside = g[0] >= r[0] - 2 and g[2] <= r[2] + 2 and g[1] >= r[1] - 2 and g[3] <= r[3] + 2
        overlaps = g[0] < r[2] and g[2] > r[0] and g[1] < r[3] and g[3] > r[1]
        if overlaps and not inside:
            bad.append("graphics cross the boundary")
            break
    return bad


# ------------------------------------------------------------------ the gate
# Resolution is a requirement, not a default: a dense three-stage amplifier at
# 150 dpi is unreadable, and a full-page appendix figure at 300 dpi is wasted
# pixels. Render to a target long edge instead, clamped to a sane dpi range.
TARGET_PX = 1400
DPI_MIN, DPI_MAX = 150, 300

VERDICT_PROMPT = """This image was cropped from a research paper. It is meant \
to contain exactly the figure named by the caption below, and nothing else.

CAPTION: {ref} {caption}

Reply with JSON only, no prose:
{{"shows": "schematic" | "plot" | "block_diagram" | "photo" | "table" | "text" \
| "mixed" | "nothing",
  "complete": true if the whole figure the caption names is inside the image,
  "clipped": true if any part of the drawing is cut off by an edge,
  "extra": true if content belonging to something else is included}}"""


def dpi_for(rect):
    long_pt = max(rect[2] - rect[0], rect[3] - rect[1]) or 1.0
    return max(DPI_MIN, min(DPI_MAX, round(TARGET_PX * 72.0 / long_pt)))


def verify(m, cap, cands, render, ask, ref=""):
    """Pick the first candidate a model confirms.

    Returns {rect, status, detail}. status is:
        verified   a model looked and accepted it
        rejected   every candidate was looked at and refused
        deferred   no model was reachable

    `deferred` deliberately still carries the best geometric rectangle, but it
    is NOT the same claim as `verified` and downstream must not read it as one -
    the same distinction `mark_absent` enforces between not asking and asking
    and finding nothing.

    The model never sees a rectangle it can edit. It is shown a rendered
    candidate and answers about that image only, so its influence is limited to
    choosing among rectangles geometry proposed, or refusing all of them.
    """
    usable = [c for c in cands if not check(m, cap, c)]
    if not usable:
        return dict(rect=cands[0] if cands else None, status="rejected",
                    detail="no candidate passed the geometric gate")
    refused = []
    for c in usable:
        try:
            got = ask("crop_check",
                      VERDICT_PROMPT.format(ref=ref, caption=cap["text"][:300]),
                      image=render(c, dpi_for(c)))
        except Exception as e:                      # ModelUnavailable, by duck type
            if type(e).__name__ != "ModelUnavailable":
                raise
            return dict(rect=usable[0], status="deferred", detail=str(e))
        if got.get("complete") and not got.get("clipped"):
            return dict(rect=c, status="verified", detail=got.get("shows", "?"))
        refused.append({k: got.get(k) for k in ("shows", "complete", "clipped", "extra")})
    return dict(rect=usable[0], status="rejected", detail=refused)
