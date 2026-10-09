"""Query surface over the page map. This is what the agent actually calls.

The page map itself is 25k-89k tokens of JSON; a single section's prose is
1-3.5k. Handing the map to a model would recreate the very problem the ingest
solves, one level up, so nothing here ever prints the map. Every command
answers a question against it and prints only the answer.

    doc.py PDF outline                 sections, subsections, and their size
    doc.py PDF read SECTION            the prose of one section
    doc.py PDF find PATTERN [-w] [--in SECTION]      search; -w = whole words
    doc.py PDF captions [--figures|--tables]
    doc.py PDF render CAPTION OUT.png  crop the region a caption names

`find` is the primitive behind priority ordering: it answers "which section
should I read for this field?" without reading any of them.
"""
import hashlib, json, os, re, sys
from pagemap import pagemap

CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache")


def load(path):
    """Page map, cached on the file's identity. 3.6s for a 40-page paper is
    fine once and not fine on every one of a few dozen queries."""
    st = os.stat(path)
    key = hashlib.sha1(f"{os.path.abspath(path)}:{st.st_mtime_ns}:{st.st_size}".encode()).hexdigest()[:16]
    f = os.path.join(CACHE, key + ".json")
    if os.path.exists(f):
        return json.load(open(f))
    m = pagemap(path)
    os.makedirs(CACHE, exist_ok=True)
    json.dump(m, open(f, "w"))
    return m


def lines_by_idx(m):
    return {l["idx"]: l for p in m["pages"] for l in p["lines"]}


def page_of_idx(m):
    return {l["idx"]: p["n"] for p in m["pages"] for l in p["lines"]}


def extent(m, i):
    """Where section i really ends.

    A section's raw span stops at its first subsection, which is not what
    anyone means by "read section IV". A section runs to the next section; a
    subsection runs to the next heading of any kind."""
    secs = m["sections"]
    here = secs[i]
    for j in range(i + 1, len(secs)):
        if here["kind"] == "subsection" or secs[j]["kind"] == "section":
            return here["span"][0], secs[j]["span"][0] - 1
    return here["span"][0], max(l["idx"] for p in m["pages"] for l in p["lines"])


def prose(m, a, b, kinds=("body",)):
    by = lines_by_idx(m)
    return " ".join(by[i]["text"] for i in range(a + 1, b + 1)
                    if i in by and by[i]["kind"] in kinds)


def resolve(m, q):
    """Match a section loosely: the agent knows 'experimental', not the exact
    title. Tries whole title, then substring, then the leading number."""
    secs = m["sections"]
    ql = q.strip().lower()
    exact = [i for i, s in enumerate(secs) if s["title"].lower() == ql]
    sub = [i for i, s in enumerate(secs) if ql in s["title"].lower()]
    num = [i for i, s in enumerate(secs)
           if re.match(r'^\s*' + re.escape(ql) + r'[.\s]', s["title"].lower())]
    for hits in (exact, num, sub):
        if len(hits) == 1:
            return hits[0]
        if len(hits) > 1:
            print(f"ambiguous: {q!r} matches", file=sys.stderr)
            for i in hits:
                print(f'   {secs[i]["title"]}', file=sys.stderr)
            sys.exit(2)
    print(f"no section matching {q!r}. Try: doc.py PDF outline", file=sys.stderr)
    sys.exit(2)


def section_of(m, idx):
    """The innermost heading covering a line, for reporting search hits."""
    best = None
    for s in m["sections"]:
        if s["span"][0] <= idx:
            best = s
    return best["title"] if best else "(front matter)"


# ---------------------------------------------------------------- commands
def cmd_outline(m, args):
    print(f'{m["file"]}  {len(m["pages"])} pages, '
          f'{sum(1 for s in m["sections"] if s["kind"]=="section")} sections, '
          f'{len(m["captions"])} captions')
    for i, s in enumerate(m["sections"]):
        a, b = extent(m, i)
        n = len(prose(m, a, b))
        pad = "  " if s["kind"] == "section" else "      "
        print(f'{pad}p{s["page"]:<3d} {s["title"][:58]:<58} {n//4:>6,d} tok')


def cmd_read(m, args):
    raw = "--raw" in args
    i = resolve(m, [a for a in args if not a.startswith("--")][0])
    s = m["sections"][i]
    a, b = extent(m, i)
    kinds = ("body", "caption", "graphic") if raw else ("body",)
    t = prose(m, a, b, kinds)
    print(f'# {s["title"]}   (page {s["page"]}, lines {a}-{b}, ~{len(t)//4:,d} tok)\n')
    print(t if t else "(no prose in this section)")


def cmd_find(m, args):
    pos = [a for a in args if not a.startswith("-")]
    p = pos[0]
    if "-w" in args:
        p = r"\b(?:" + p + r")\b"
    pat = re.compile(p, re.I)
    by, pg = lines_by_idx(m), page_of_idx(m)
    lo, hi = 0, max(by)
    if "--in" in args:
        i = resolve(m, args[args.index("--in") + 1])
        lo, hi = extent(m, i)
        print(f'searching only {m["sections"][i]["title"]!r}\n')
    hits = [(i, l) for i, l in sorted(by.items()) if lo <= i <= hi and pat.search(l["text"])]
    if not hits:
        print("no match")
        return
    # ranked summary first: this is the priority-ordering answer
    tally = {}
    for i, l in hits:
        tally.setdefault(section_of(m, i), []).append(l)
    print(f'{len(hits)} hits in {len(tally)} sections\n')
    for sec, ls in sorted(tally.items(), key=lambda kv: -len(kv[1])):
        print(f'  {len(ls):>3d}  {sec[:70]}')
    print()
    for i, l in hits[:40]:
        print(f'  p{pg[i]:<3d}[{l["kind"]}] {l["text"][:150]}')
    if len(hits) > 40:
        print(f'  ... {len(hits)-40} more')


def cmd_captions(m, args):
    want = "figures" if "--figures" in args else "tables" if "--tables" in args else "all"
    for c in m["captions"]:
        is_tab = c["text"].upper().lstrip().startswith(("TABLE", "TABEL"))
        if want == "figures" and is_tab:
            continue
        if want == "tables" and not is_tab:
            continue
        print(f'  p{c["page"]:<3d} {c["text"][:100]}')


def cmd_render(m, args):
    want, out = args[0], args[1]
    c = next((c for c in m["captions"] if c["text"].upper().startswith(want.upper())), None)
    if not c:
        print(f"no caption starting {want!r}. Try: doc.py PDF captions", file=sys.stderr)
        sys.exit(2)
    if not c["text"].upper().startswith("TABLE"):
        # figures: the caption's own column band (crop.py), so two figures
        # printed side by side are not merged into one picture
        import pymupdf
        import crop as C
        from docclass import classify
        cands = [r for r in C.candidates(m, c, classify(m["path"])) if not C.check(m, c, r)]
        if cands:
            r = cands[0]
            page = pymupdf.open(m["path"])[c["page"] - 1]
            page.get_pixmap(clip=pymupdf.Rect(*r), dpi=C.dpi_for(r)).save(out)
            print(f"  {c['text'][:52]:<54} -> {r[2]-r[0]:.0f}x{r[3]-r[1]:.0f}pt  {os.path.basename(out)}")
            return
    from region import crop
    crop(m["path"], c["page"], want, out)


CMDS = dict(outline=cmd_outline, read=cmd_read, find=cmd_find,
            captions=cmd_captions, render=cmd_render)

if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[2] not in CMDS:
        print(__doc__)
        sys.exit(1)
    pdf = sys.argv[1]
    m = load(pdf)
    m["path"] = pdf
    CMDS[sys.argv[2]](m, sys.argv[3:])
