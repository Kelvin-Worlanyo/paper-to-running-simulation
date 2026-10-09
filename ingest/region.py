"""Locate and crop the region a caption labels. Handles IEEE small-caps
letter-splitting, and finds figures from GRAPHICS bboxes, not text gaps.

Graphics come from pagemap.graphics_boxes, which drops a reader's highlight
annotations. Those are fill-only rects sized to a line of text; left in, one
sitting above a caption drags the top of the crop up into the paragraph."""
import re, sys, pymupdf
from pagemap import graphics_boxes, lines_of

def norm(t):
    # "T ABLE  I  M ODEL" -> "TABLE I MODEL"  (IEEE small-caps splits after the cap)
    t = re.sub(r'\b([A-Z])\s+([A-Z]{2,})', r'\1\2', t)
    return re.sub(r'\s+', ' ', t).strip()

CAP = re.compile(r'^(FIG(?:URE)?\.?\s*\d+|TABLE\s+[IVXL]+)\b', re.I)

def blocks(page):
    W=page.rect.width; out=[]
    for b in page.get_text("dict")["blocks"]:
        if b.get("type")!=0: continue
        t=" ".join(s["text"] for l in b["lines"] for s in l["spans"]).strip()
        if t: out.append(dict(t=norm(t), bb=b["bbox"],
                              col=0 if (b["bbox"][0]+b["bbox"][2])/2<W/2 else 1))
    return out

def crop(pdf,pno,want,out,dpi=200):
    doc=pymupdf.open(pdf); page=doc[pno-1]; bs=blocks(page)
    cap=next(b for b in bs if CAP.match(b["t"]) and b["t"].upper().startswith(want.upper()))
    x0,y0,x1,y1=cap["bb"]; is_tab=cap["t"].upper().startswith("TABLE")
    same=[b for b in bs if b["col"]==cap["col"] and b is not cap]
    if is_tab:
        # walk down from the caption, ACCUMULATING table rows, stop at the first prose block
        def prose(b): return len(b["t"])>80 and ". " in b["t"]
        below=sorted([b for b in same if b["bb"][1]>y1+2], key=lambda b:b["bb"][1])
        rows=[]
        for b in below:
            if prose(b): break
            rows.append(b)
        if not rows: raise SystemExit("no table rows found")
        top=y1+2; bot=max(b["bb"][3] for b in rows)+4
        left=min(b["bb"][0] for b in rows)-6; right=max(b["bb"][2] for b in rows)+6
    else:                                        # figure = graphics cluster ABOVE caption
        g=[r for r in graphics_boxes(page, lines_of(page)) if r[3]<=y0+4 and r[1]>40]
        if not g: raise SystemExit("no graphics above caption")
        top=min(r[1] for r in g); bot=max(r[3] for r in g)
        left=min(r[0] for r in g)-4; right=max(r[2] for r in g)+4
    rect=pymupdf.Rect(max(0,left if left is not None else x0-6), top,
                      min(page.rect.width, right if right is not None else x1+6), bot)
    page.get_pixmap(clip=rect, dpi=dpi).save(out)
    print(f"  {cap['t'][:52]:<54} -> {rect.width:.0f}x{rect.height:.0f}pt  {out.split('/')[-1]}")

if __name__ == "__main__":
    # smoke test: three regions whose crops were checked by eye
    D = "<local file, not part of this release>"
    S = sys.argv[1]
    crop(D, 5, "TABLE I", f"{S}/table1.png")
    crop(D, 6, "TABLE II", f"{S}/table2.png")
    crop(D, 6, "FIG. 10", f"{S}/fig10.png")
