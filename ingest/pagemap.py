"""PDF -> page map + section index. Deterministic, no model.

Every rule below was measured on real papers, not assumed:

  spans      join by GEOMETRY. Small-caps spans abut at 0.01-0.06pt while real
             word gaps are 1.4-4.3pt, so a 0.4pt threshold separates them.
             Joining with " " yields "T ABLE"; joining with "" yields "IV.PARAMETER".
  headings   font size and weight do NOT separate an IEEE section head from
             body text - both are 10pt Times, unbolded. What separates them:
             sections are CENTRED in their column with SYMMETRIC margins,
             subsections are ITALIC (though APCCAS sets them upright), and ACM
             sets both LARGER than body.
  numbers    a section number is often split from its title. ACM puts it on the
             line above; IEEE splits it into its own fragment on the SAME
             baseline (measured: EDocNet I/II/V split at a 10-13pt gap, while
             III/IV/VI in the same paper did not). Both are merged before
             heading detection.
  columns    column bounds are measured from the body lines themselves, not
             assumed to be W/2. On a 612pt IEEE page the left column runs
             47-302, so its true centre is 174, not 153 - a 21pt error, enough
             to lose a centred heading.
  baselines  lines are grouped into rows by vertical overlap WITHIN a column.
             A heading is alone on its row; a table cell is not. That one test
             is what rejects a centred "OPAMP" cell and an author initial "R."
             sitting beside a surname.
  runover    a title that wraps arrives as two lines; the all-caps second line
             is folded back into the first.
  sequence   lettered subsections run A, B, C... and restart at each section.
             A reference entry "L. Sumanen, M. Waltari..." has the same shape
             and no place in that sequence, which is what rejects it.
  graphics   image and vector boxes, merged into zones. Text inside a zone is
             a figure label, not prose. Two things had to be measured first:
             figure labels are NOT drawn on top of an image (0 of 166 lines on
             DocEDA p2 sit inside an image rect - the labels are vector text
             beside many small graphics), so containment needs the merged
             zone; and a reader's HIGHLIGHTS are fill-only rects, one per text
             line, spanning the column, which would otherwise make three whole
             prose paragraphs read as figure content. A zone is finally tested
             against the text it holds: inline equations are vector graphics
             too, and a paragraph containing them clusters into a zone whose
             text fragments are individually short. What gives it away is that
             those fragments still reach BOTH column edges - they are justified
             prose. Figure labels never are.
  captions   "Fig N" / "TABLE N", located with their bbox - but only when the
             line does not CONTINUE the sentence above it. Prose wraps onto
             "Table II. The transformation accuracy..." and "Table III, the
             optimized LNA...", which are references to a table, not captions.
             The true caption is preceded by a finished sentence ("in Table I.");
             the false ones by "summarized in" and "The results shown in".
  figures    taken from GRAPHICS bboxes above the caption. Text-gap heuristics
             fail: a caption's nearest text above is often an "(a) (b)" sublabel.
  order      reading order is per page, column by column, so section spans are
             expressed as reading-index ranges, never as (page, y). A line that
             SPANS both columns - an abstract, a title, a wide table - belongs
             to neither, and sorting it into one by its midpoint shreds the
             text: katyal's abstract came out as "resolution high analog-to-
             digital application speed has been designed". Spanning lines cut
             the page into bands instead, and each band is read column by
             column below the line that opens it.
"""
import collections, re, json, sys, statistics, pymupdf

ROMAN = re.compile(r'^\s*([IVXL]{1,6})\.\s+(\S.*)$')
ARABIC = re.compile(r'^\s*(\d+(?:\.\d+)*)\.?\s+(\S.*)$')
LETTER = re.compile(r'^\s*([A-Z])\.\s+(\S.*)$')
BARE = re.compile(r'^\s*(\d+(?:\.\d+)*|[IVXL]{1,6}|[A-Z])\.?\s*$')
CAP = re.compile(r'^\s*(Fig(?:ure)?\.?\s*\d+|TABLE\s+[IVXL]+|Table\s+\d+)\b', re.I)
ITAL, BOLD = 2**1, 2**4


def join_spans(spans):
    out = ""
    for i, s in enumerate(spans):
        if i:
            gap = s["bbox"][0] - spans[i - 1]["bbox"][2]
            if gap > max(0.4, 0.05 * s["size"]) and not out.endswith(" ") \
               and not s["text"].startswith(" "):
                out += " "
        out += s["text"]
    return re.sub(r"\s+", " ", out).strip()


def lines_of(page):
    out = []
    for b in page.get_text("dict")["blocks"]:
        if b.get("type") != 0:
            continue
        for l in b["lines"]:
            spans = [s for s in l["spans"] if s["text"].strip()]
            if not spans:
                continue
            t = join_spans(spans)
            if t:
                out.append(dict(text=t, bbox=list(l["bbox"]),
                                size=round(statistics.median(s["size"] for s in spans), 1),
                                ital=bool(spans[0]["flags"] & ITAL),
                                bold=bool(spans[0]["flags"] & BOLD)))
    return out


def char_median(lines, key):
    """Median of `key` weighted by characters, so the value describes the size
    or width of most of the TEXT, not of most of the lines. A page whose lines
    are mostly short table cells has a line-median body size that no paragraph
    on it actually uses."""
    vals = []
    for l in lines:
        vals += [key(l)] * max(1, len(l["text"]))
    return statistics.median(vals) if vals else None


def baseline_rows(lines):
    """Group lines into visual rows by vertical overlap, within a column.

    Grouping must be per column: on a two-column page a heading in the left
    column overlaps unrelated body text in the right one."""
    rows, taken = [], set()
    for i, l in enumerate(lines):
        if i in taken:
            continue
        taken.add(i)
        grp = [l]
        y0, y1 = l["bbox"][1], l["bbox"][3]
        for j, m in enumerate(lines):
            if j in taken or m["col"] != l["col"]:
                continue
            n0, n1 = m["bbox"][1], m["bbox"][3]
            if min(y1, n1) - max(y0, n0) > 0.5 * min(y1 - y0, n1 - n0):
                grp.append(m); taken.add(j)
        rows.append(sorted(grp, key=lambda x: x["bbox"][0]))
    return rows


def page_columns(lines, W):
    """One column if text covers the page centre; two if a gutter runs down it.

    Measured over 15 pages whose column count was checked by eye - fraction of
    lines whose box spans x = W/2:

        two-column   0.0, 0.0, 0.6, 1.2, 1.5, 2.2, 3.6, 4.5, 6.1, 9.5 %
        one-column   18.4, 44.6, 63.6, 75.5, 82.0 %

    Two earlier rules are replaced by this one. Median line width called
    badillo two-column only by luck and failed on any page with a full-width
    abstract. Counting lines that sit wholly in a half called AMSnet-KG p30
    two-column, because a wide TABLE puts cells in both halves - that page is
    the 18.4% entry, and it is the tightest margin here.
    """
    if len(lines) < 8:
        return None
    c = W / 2
    covers = sum(1 for l in lines if l["bbox"][0] <= c <= l["bbox"][2])
    return 1 if covers >= 0.14 * len(lines) else 2


def doc_columns(per_page):
    """One column count for the whole paper, by majority.

    Deciding per page fails on a page that is mostly figure: AMSnet-KG p10 has
    few prose lines, so the centre test saw scattered figure labels and called
    a single-column paper two-column. The caption then fell into a phantom
    right column and its band came out 70pt wide. Papers do not change column
    count page to page, so the majority over pages that had enough text to
    judge is a better answer for every page than each page's own guess."""
    votes = [c for c in per_page if c]
    if not votes:
        return 1
    return 1 if votes.count(1) >= votes.count(2) else 2


def column_bounds(lines, W, ncol):
    """Left and right edge of each column, measured from body lines."""
    out = []
    for c in range(ncol):
        lo, hi = (0, W) if ncol == 1 else ((0, W / 2) if c == 0 else (W / 2, W))
        # entirely inside the half: a full-width footer whose midpoint falls in
        # the right half would otherwise drag the right column's left edge to 78.
        # The length threshold relaxes, because a sparse OCR page can have no
        # long line wholly inside a column at all - badillo p2 has exactly one
        # long line and it spans both columns, which left the bounds at 0-306.
        body = []
        for min_len in (60, 20, 0):
            body = [l["bbox"] for l in lines if len(l["text"]) > min_len
                    and lo - 4 <= l["bbox"][0] and l["bbox"][2] <= hi + 4]
            if body:
                break
        out.append((min(b[0] for b in body), max(b[2] for b in body)) if body else (lo, hi))
    return out


def graphics_boxes(page, lines):
    """Image and drawing boxes, with reader highlights removed.

    A highlight is a fill-only rect drawn to fit one line of text. Keeping them
    would merge whole paragraphs into a figure zone."""
    g = [tuple(r) for im in page.get_images(full=True) for r in page.get_image_rects(im[0])]
    for d in page.get_drawings():
        r = d["rect"]
        if r.width <= 8 or r.height <= 8:
            continue
        area = r.width * r.height
        if d["type"] == "f" and any(
                overlap(l["bbox"], r) > 0.6 * area and r.height <= 1.6 * (l["bbox"][3] - l["bbox"][1])
                for l in lines):
            continue
        g.append(tuple(r))
    return g


def overlap(a, b):
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    return ix * iy


def merge(zones, pad):
    """Union boxes whose padded rectangles touch."""
    zones = [list(b) for b in zones]
    changed = True
    while changed:
        changed, out = False, []
        for r in zones:
            for o in out:
                if (r[0] - pad < o[2] and o[0] - pad < r[2]
                        and r[1] - pad < o[3] and o[1] - pad < r[3]):
                    o[0], o[1] = min(o[0], r[0]), min(o[1], r[1])
                    o[2], o[3] = max(o[2], r[2]), max(o[3], r[3])
                    changed = True
                    break
            else:
                out.append(list(r))
        zones = out
    return zones


def figure_zones(boxes, lines, bounds, W, H, pad=6):
    """Merge graphics boxes that touch into zones, keeping only real figures.

    Merging is required because a figure is drawn as dozens of small images and
    strokes; no single box covers its labels.

    A zone is then kept only if the text inside it reads like labels rather than
    prose. Geometry alone cannot decide this: on a scanned paper the whole page
    is one image, so every line of the OCR layer sits inside a graphics box.
    Without the content test that marked 1847 lines of AMSnet-KG, 691 of katyal
    and 220 of badillo as figure text."""
    # Two-stage merge. The first pad is small, because a wide one bridges a
    # figure into the paragraph beside it. The survivors are then merged again
    # at a wide pad: they are already known to be figures, so joining two
    # halves of one diagram across the gap between them is safe. Every merged
    # zone is validated again.
    keep = []
    for z in merge(boxes, pad) + merge([z for z in ok(merge(boxes, pad), lines, bounds, W, H)], 40):
        if is_figure(z, lines, bounds, W, H):
            keep.append(z)
    return keep


def ok(zones, lines, bounds, W, H):
    return [z for z in zones if is_figure(z, lines, bounds, W, H)]


def is_figure(z, lines, bounds, W, H):
    """A zone is a figure if it is substantial and the text inside it reads as
    labels: short, and not justified to the column measure."""
    if (z[2] - z[0]) * (z[3] - z[1]) <= 0.015 * W * H:
        return False
    inside = [l for l in lines if contained(l["bbox"], z)]
    if inside and (any(len(l["text"]) > 80 and ". " in l["text"] for l in inside)
                   or statistics.median(len(l["text"]) for l in inside) > 40
                   or justified(inside, lines, bounds)):
        return False
    return True


def contained(b, z):
    return overlap(b, z) > 0.7 * max(1e-6, (b[2] - b[0]) * (b[3] - b[1]))


def justified(inside, lines, bounds):
    """True if ANY row these lines sit on reaches both column edges.

    Justified rows are prose. A paragraph broken up by inline equations leaves
    short fragments that pass a length test but still start at the left margin
    and end at the right one. One such row is enough to condemn the zone: a
    figure never contains a line set to the column measure, and the wide second
    merge would otherwise swallow the paragraph beside a diagram."""
    for r in {l["row"] for l in inside}:
        same = [l for l in lines if l["row"] == r]
        cl, cr = bounds[same[0]["col"]]
        tol = 0.03 * (cr - cl)
        x0 = min(l["bbox"][0] for l in same)
        x1 = max(l["bbox"][2] for l in same)
        if not (x0 - cl < tol and cr - x1 < tol):
            continue
        # reaching both margins is not enough: a wide TABLE row reaches them
        # too, as a handful of cells with large gaps between them. Prose fills
        # the measure it spans; a table row covers about half of it. Measured
        # on AMSnet-KG p30: table rows cover 0.47 of their span, against 0.92
        # for a paragraph line broken up by inline equations.
        covered = sum(l["bbox"][2] - l["bbox"][0] for l in same)
        if covered >= 0.85 * (x1 - x0):
            return True
    return False


def is_heading(l, body_size, body_w, bounds, col):
    """'section' | 'subsection?' | 'unnumbered' | None.

    A numbering pattern is NECESSARY; style only confirms. Style alone
    over-fires on titles, author lines and any narrow body line. The two
    provisional kinds are resolved document-wide in pagemap(): 'subsection?'
    against the letter sequence, 'unnumbered' against where numbering starts."""
    t = l["text"]
    if len(t) > 90:
        return None
    x0, _, x1, _ = l["bbox"]
    cl, cr = bounds[col]
    cw = cr - cl
    # symmetric margins, not a width cap: a long section title such as
    # "II. RANDOM OFFSET VOLTAGE IN DYNAMIC COMPARATORS" fills most of its
    # column and is still centred. Justified body text has zero margin on
    # both sides, so requiring a real indent separates the two.
    ml, mr = x0 - cl, cr - x1
    centred = abs(ml - mr) < 0.06 * cw and min(ml, mr) > 0.012 * cw
    # not wider than a body line. An 8% margin was too tight: a centred title
    # that fills its column ("II. RANDOM OFFSET VOLTAGE IN DYNAMIC COMPARATORS",
    # 238pt against a 251pt column) is only 5% narrower than body text.
    narrow = (x1 - x0) < body_w + 2
    big = l["size"] > body_size + 0.4
    if not narrow:
        return None

    m = ARABIC.match(t) or ROMAN.match(t)
    num, title = (m.group(1), m.group(2)) if m else ("", "")
    # the title must open with a capital: excludes "90 nm CMOS: Vdd = +0.6 V".
    if m and not title[:1].isupper():
        return None

    if re.fullmatch(r'\d{1,2}(\.\d{1,2}){1,2}', num.rstrip(".")):        # 2.1 Title
        return "subsection" if (centred or l["bold"] or big) else None
    if re.fullmatch(r'[IVXL]{1,6}', num.rstrip(".")):                    # IV. Title
        # IEEE roman sections are centred and set in caps. Requiring that
        # excludes in-paragraph list items like "I. Structural Correctness: ...".
        return "section" if (centred and title.upper() == title) else None
    if re.fullmatch(r'\d{1,2}', num.rstrip(".")):                        # 2 Title
        return "section" if (centred or l["bold"] or big) else None
    if LETTER.match(t):                                            # A. Title
        # italic is the IEEE convention but not universal (APCCAS sets
        # subsections upright). Falling back on shape alone would promote every
        # reference-list initial, so an upright candidate must additionally be
        # alone on its row, clearly short, and title-cased. The letters are then
        # checked for sequence at document level, which is the real signal.
        title = LETTER.match(t).group(2)
        words = [w for w in title.split() if len(w) >= 4]
        titlish = words and sum(w[:1].isupper() for w in words) >= 0.6 * len(words)
        if l["ital"] or (l["alone"] and (x1 - x0) < 0.75 * body_w and titlish):
            return "subsection?"
    # unnumbered heads: REFERENCES, ACKNOWLEDGMENT, APPENDIX. Three guards,
    # one per observed false positive:
    #   alone-on-row  rejects a centred table cell, e.g. "OPAMP";
    #   ASCII capitals rejects display equations, whose math glyphs are caseless
    #                 and so pass any t.upper() == t test;
    #   size window   rejects the centred all-caps TABLE title, 2.7pt under
    #                 body. It is a window, not an equality: IEEE sets these
    #                 heads in 9pt against a 10pt body, and REFERENCES on a
    #                 small-type reference page runs 1.3pt over it.
    if (centred and l["alone"] and -1.5 <= l["size"] - body_size <= 2.0
            and re.fullmatch(r"[A-Z][A-Z0-9 &'\-]{2,38}", t)):
        return "unnumbered"
    return None


def premerge_numbers(lines, body_size):
    """Rejoin a section number that was split off from its title.

    Two measured forms:
      ACM   the number sits on its own line ABOVE the title, both set larger
            than body text.
      IEEE  the number is a separate fragment on the SAME row, a 10-13pt gap
            to its left. EDocNet splits I/II/V this way and leaves III/IV/VI
            whole, so the form cannot be decided per paper.

    The same-row merge fires only when the pair is the ENTIRE row. Without
    that, an author initial merges with the surname beside it ("R." + "Chen")
    and a two-cell table row merges into a heading-shaped string."""
    def fuse(a, b, sep):
        m = dict(b)
        m["text"] = f'{a["text"].strip().rstrip(".")}{sep}{b["text"]}'
        m["bbox"] = [min(a["bbox"][0], b["bbox"][0]), min(a["bbox"][1], b["bbox"][1]),
                     max(a["bbox"][2], b["bbox"][2]), max(a["bbox"][3], b["bbox"][3])]
        return m

    merged = {}
    for row in baseline_rows(lines):
        if len(row) != 2:
            continue
        a, b = row
        if (BARE.fullmatch(a["text"].strip()) and re.match(r'^[A-Z]', b["text"])
                and 0 < b["bbox"][0] - a["bbox"][2] < 25):
            merged[id(a)] = fuse(a, b, ". ")
            merged[id(b)] = None

    out, i = [], 0
    while i < len(lines):
        l = lines[i]
        if id(l) in merged:
            if merged[id(l)] is not None:
                out.append(merged[id(l)])
            i += 1
            continue
        nxt = lines[i + 1] if i + 1 < len(lines) else None
        if (nxt and id(nxt) not in merged
                and l["size"] > body_size + 0.4 and nxt["size"] > body_size + 0.4
                and re.fullmatch(r'\d+(\.\d+)*\.?', l["text"].strip())
                and re.match(r'^[A-Z]', nxt["text"])):
            out.append(fuse(l, nxt, " ")); i += 2; continue
        out.append(l); i += 1
    return out


def demote_continuations(ls):
    """A caption cannot continue the sentence above it.

    Only the line directly above, in the same column, counts: across a column
    break the previous line legitimately ends mid-sentence."""
    for i, l in enumerate(ls):
        if l["kind"] != "caption" or i == 0:
            continue
        prev = ls[i - 1]
        h = prev["bbox"][3] - prev["bbox"][1]
        if (prev["kind"] == "body" and prev["col"] == l["col"]
                and 0 <= l["bbox"][1] - prev["bbox"][3] < 1.5 * h
                and not prev["text"].rstrip().endswith((".", ":", "!", "?"))):
            l["kind"] = "body"


ENDS = (".", ":", "!", "?")


def demote_references(ls):
    """Turn a caption that is really a mid-sentence reference back into body.

    The test is that the line sits INSIDE a flowing sentence: it does not
    finish one, the line after it does not begin one, and the line before it
    did not finish one either. Requiring the previous line to be body is what
    protects a genuine caption sitting directly under figure artwork."""
    for i, l in enumerate(ls):
        if l["kind"] != "caption" or i == 0 or i + 1 >= len(ls):
            continue
        prev, nxt = ls[i - 1], ls[i + 1]
        if (prev["col"] == l["col"] == nxt["col"]
                and prev["kind"] == "body"
                and not l["text"].rstrip().endswith(ENDS)
                and nxt["text"][:1].islower()
                and not prev["text"].rstrip().endswith(ENDS)):
            l["kind"] = "body"


def absorb_runover(ls):
    """A section title that wraps is emitted as two lines. Fold the second into
    the first: "III. NUMBERICAL EXAMPLES AND MONTE CARLO" + "SIMULATION RESULTS".

    Only an all-caps continuation, alone on its row, in the same column, set at
    the same size, and sitting directly beneath - which is what keeps it from
    swallowing the first line of the paragraph that follows."""
    for i, l in enumerate(ls[:-1]):
        n = ls[i + 1]
        if l["kind"] not in ("section", "unnumbered") or n["kind"] not in ("body", "unnumbered"):
            continue
        h = l["bbox"][3] - l["bbox"][1]
        if (n["col"] == l["col"] and n["alone"] and abs(n["size"] - l["size"]) < 1.5
                # lines can overlap slightly, so the gap floor is negative
                and -0.4 * h <= n["bbox"][1] - l["bbox"][3] < 0.8 * h
                and re.fullmatch(r"[A-Z][A-Z0-9 &\'\-]{2,38}", n["text"])
                and l["text"].upper() == l["text"]):
            l["text"] += " " + n["text"]
            l["bbox"] = [min(l["bbox"][0], n["bbox"][0]), l["bbox"][1],
                         max(l["bbox"][2], n["bbox"][2]), n["bbox"][3]]
            n["kind"] = "runover"


def pagemap(path):
    doc = pymupdf.open(path)
    per_page = [page_columns(lines_of(p), p.rect.width) for p in doc]
    ncol_doc = doc_columns(per_page)

    # A graphics box repeated at the same coordinates across pages is page
    # furniture - a template panel or watermark - not figure ink. AMSnet-KG
    # carries one at [112,209,500,583] on many pages; left in, it crosses every
    # figure band boundary and the crop gate rejects every figure in the paper.
    seen = collections.Counter()
    raw = []
    for page in doc:
        b = graphics_boxes(page, lines_of(page))
        raw.append(b)
        seen.update({tuple(round(v) for v in x) for x in b})
    furniture = {k for k, n in seen.items() if n > 2 and n >= 0.25 * len(raw)}

    all_lines = []
    for pno, page in enumerate(doc, 1):
        W, H = page.rect.width, page.rect.height
        ls = lines_of(page)
        ncol = ncol_doc
        long = [l for l in ls if len(l["text"]) > 60]
        body_w = char_median(long, lambda l: l["bbox"][2] - l["bbox"][0]) or W
        body_size = char_median(ls, lambda l: l["size"]) or 10.0
        for l in ls:
            x0, _, x1, _ = l["bbox"]
            l["col"] = 0 if (ncol == 1 or (x0 + x1) / 2 < W / 2) else 1
        ls = premerge_numbers(ls, body_size)
        bounds = column_bounds(ls, W, ncol)
        for r, row in enumerate(baseline_rows(ls)):
            top = min(x["bbox"][1] for x in row)
            for l in row:
                # row_y, not the line's own y: OCR gives words on one visual
                # line slightly different tops, and sorting on those scrambles
                # them. katyal's abstract read "resolution high analog-to-
                # digital application speed" because five fragments of one line
                # were ordered by block, not by x.
                l["alone"], l["row"], l["row_y"] = len(row) == 1, r, top
        for l in ls:
            l["page"], l["w"], l["h"], l["cols"] = pno, round(W), round(H), ncol
            l["kind"] = "caption" if CAP.match(l["text"]) else \
                (is_heading(l, body_size, body_w, bounds, l["col"]) or "body")
        # bands: a spanning line ends the two-column flow above it and starts
        # a new one below, so it reads in y order with the columns nested inside
        spanning = sorted([l for l in ls
                           if l["bbox"][0] <= W / 2 <= l["bbox"][2] and ncol > 1],
                          key=lambda l: l["bbox"][1])
        cuts = [l["bbox"][1] for l in spanning]
        for l in ls:
            l["band"] = sum(1 for c in cuts if c < l["bbox"][1] - 0.5)
            l["spans"] = l in spanning
        ls.sort(key=lambda l: (l["band"], -1 if l["spans"] else l["col"],
                               l["row_y"], l["bbox"][0]))
        absorb_runover(ls)
        # Zones keep the furniture: they decide which TEXT is figure content,
        # and excluding a big panel there lets prose leak in (AMSnet-KG went to
        # 552 marked lines, 2 of them prose). The crop is the other consumer and
        # wants it gone, so it gets its own filtered list below. Two questions,
        # two answers, from the same boxes.
        boxes = raw[pno - 1]
        crop_boxes = [b for b in boxes
                      if tuple(round(v) for v in b) not in furniture]
        zones = figure_zones(boxes, ls, bounds, W, H)
        for l in ls:
            if l["kind"] != "body":
                continue
            halo = [[z[0] - 12, z[1] - 12, z[2] + 12, z[3] + 12] for z in zones]
            # inside a validated figure zone, or just outside one and not part
            # of a justified row: a diagram's labels sit in the whitespace
            # between its sub-clusters, which no graphics box covers.
            if (any(contained(l["bbox"], z) for z in zones)
                    or (len(l["text"]) < 40 and any(contained(l["bbox"], z) for z in halo)
                        and not justified([l], ls, bounds))):
                l["kind"] = "graphic"
        # last: it asks whether the previous line is body, which is only true
        # once the graphics pass has claimed the figure artwork above a caption
        demote_references(ls)
        gfx = [[round(v) for v in b] for b in crop_boxes]
        for l in ls:
            l["gfx"], l["zones"] = gfx, [[round(v) for v in z] for z in zones]
            # the crop needs these: a figure is bounded by its column, and the
            # bounds must come from lines wholly inside the half, not from a
            # full-width footer whose midpoint lands in one of them
            l["bounds"] = [[round(v) for v in b] for b in bounds]
        all_lines += ls

    merged = all_lines
    for i, l in enumerate(merged):
        l["idx"] = i

    # An unnumbered head (REFERENCES, ACKNOWLEDGMENT) is only trusted once the
    # numbering has started. Before that, the same shape is the tail of a
    # centred bold TITLE - "... WITH WIDE TEMPERATURE / RANGE".
    # Lettered subsections advance A, B, C... A reference entry
    # "L. Sumanen, M. Waltari..." has the same shape but no place in that
    # sequence, so sequence is what separates them. Two tolerances, both
    # measured: "A" restarts at any point, because most papers reletter at each
    # section but EDocNet runs A-G straight through III, IV and V; and one skip
    # is allowed, because katyal's "C." is lost upstream and "D. Inverter" is
    # still a heading.
    expect = "A"
    for l in merged:
        if l["kind"] != "subsection?":
            continue
        c = LETTER.match(l["text"]).group(1)
        if c == "A" or c in (expect, chr(ord(expect) + 1)):
            l["kind"], expect = "subsection", chr(ord(c) + 1)
        else:
            l["kind"] = "body"

    first = next((l["idx"] for l in merged if l["kind"] in ("section", "subsection")), None)
    for l in merged:
        if l["kind"] == "unnumbered":
            l["kind"] = "section" if (first is not None and l["idx"] > first) else "body"

    heads = [l for l in merged if l["kind"] in ("section", "subsection")]
    sections = [dict(kind=h["kind"], title=h["text"], page=h["page"],
                     span=[h["idx"], (heads[j + 1]["idx"] if j + 1 < len(heads) else len(merged)) - 1])
                for j, h in enumerate(heads)]
    pages = []
    for pno in sorted({l["page"] for l in merged}):
        pl = [l for l in merged if l["page"] == pno]
        pages.append(dict(n=pno, w=pl[0]["w"], h=pl[0]["h"], cols=pl[0]["cols"],
                          graphics=pl[0]["gfx"], zones=pl[0]["zones"],
                          bounds=pl[0]["bounds"],
                          lines=[dict(idx=l["idx"], kind=l["kind"], col=l["col"],
                                      bbox=[round(v) for v in l["bbox"]], text=l["text"])
                                 for l in pl]))
    caps = [dict(idx=l["idx"], page=l["page"], bbox=[round(v) for v in l["bbox"]],
                 text=l["text"]) for l in merged if l["kind"] == "caption"]
    return dict(file=path.split("/")[-1], pages=pages, sections=sections, captions=caps)


if __name__ == "__main__":
    print(json.dumps(pagemap(sys.argv[1]), indent=1))
