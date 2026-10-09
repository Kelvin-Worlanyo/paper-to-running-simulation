"""Ingest: PDF -> page map. Deterministic, no model."""
import re, sys, pymupdf

CAPTION = re.compile(r'^\s*(Fig(?:ure)?\.?\s*\d+|TABLE\s+[IVXL]+|Table\s+\d+)\b', re.I)
HEADING = re.compile(r'^\s*([IVXL]{1,6})\.\s+([A-Z][A-Z \-]{3,})\s*$')

def ingest(path, dpi=150):
    doc = pymupdf.open(path)
    pages = []
    for pno, page in enumerate(doc, 1):
        W, H = page.rect.width, page.rect.height
        d = page.get_text("dict")
        blocks = []
        for b in d["blocks"]:
            if b.get("type") != 0:            # 0 = text
                continue
            txt = "".join(s["text"] for l in b["lines"] for s in l["spans"]).strip()
            if not txt: continue
            sizes = [s["size"] for l in b["lines"] for s in l["spans"]]
            x0,y0,x1,y1 = b["bbox"]
            blocks.append(dict(text=txt, bbox=(x0,y0,x1,y1),
                               size=round(sum(sizes)/len(sizes),1),
                               col=0 if (x0+x1)/2 < W/2 else 1))
        # reading order: column, then vertical
        blocks.sort(key=lambda b: (b["col"], b["bbox"][1]))
        caps  = [b for b in blocks if CAPTION.match(b["text"])]
        heads = [b for b in blocks if HEADING.match(b["text"])]
        # vector drawings = where schematics live (they are not embedded images)
        draw = page.get_drawings()
        raster = page.get_images(full=True)
        pages.append(dict(n=pno, size=(round(W),round(H)), blocks=len(blocks),
                          captions=[c["text"][:58] for c in caps],
                          headings=[h["text"] for h in heads],
                          vector_ops=len(draw), raster_imgs=len(raster)))
    return pages

if __name__ == "__main__":
    for p in ingest(sys.argv[1]):
        print(f"p{p['n']:<3} {p['blocks']:>3} blocks  vec_ops {p['vector_ops']:>4}  imgs {p['raster_imgs']}")
        for h in p["headings"]: print(f"      HEADING  {h}")
        for c in p["captions"]: print(f"      CAPTION  {c}")
