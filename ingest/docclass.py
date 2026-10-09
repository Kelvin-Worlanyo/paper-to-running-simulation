"""Document class: what kind of PDF is this, and what can be trusted in it.

This runs first in Block A because it gates everything after it. A scanned
paper has no reliable text layer, so table cells must come from pixels rather
than geometry, quantities arrive OCR-damaged, and font metrics cannot drive
heading detection.

Measured across 24 PDFs (papers/, AMSnet-KG, and the AI_Analog collection):

  full-page image   the decisive signal. A scan is one photograph per page:
                    badillo 4 of 4 sampled pages, katyal 4 of 4, and ZERO for
                    every one of the other 22 documents.
  image coverage    NOT usable alone. AMSnet-KG is born-digital and still has
                    0.60 of its page area covered by images, because its
                    schematics are raster figures. Coverage says what the
                    figures are made of, not what the document is.
  size jitter       corroborating. OCR assigns a slightly different size to
                    every span. Distinct sizes per sampled page: katyal 20,
                    badillo 11, against 5.2 or fewer for all 22 born-digital
                    documents. Note what this does and does not condemn: OCR
                    jitters SIZES but keeps bounding boxes accurate, which is
                    why the geometry-driven section detector still scores 7/7
                    on badillo and 6/6 on katyal. Position survives; size does
                    not. A downstream block that read one flag and disabled all
                    geometry on a scan would make its own results worse.
  subset prefixes   a dead end. Typeset PDFs embed fonts as "HBJION+Times-
                    Roman", but PyMuPDF strips that prefix from span fonts, so
                    the signal is not visible where the spans are read.

The output is deliberately not one label. Downstream needs capabilities - can
I trust the characters, can I trust the font metrics - and those do not always
move together.

Two things this module deliberately does NOT answer:

  are the figures raster?   Tried and removed. "One image covering >5% of the
                            median page" reports False for DocEDA, which builds
                            its figures from 48 small images on a single page.
                            The question is per-figure, not per-document, and
                            belongs to the figure step where the zones exist and
                            a zone can be asked whether it holds images or only
                            vector drawings.
  mixed / image_only        both branches exist and neither is exercised by the
                            24 documents measured. They are untested.
"""
import statistics
import pymupdf

SCAN_COVER = 0.6      # one image covering this much of a page is a photograph of it
OCR_CHARS = 200       # a scan page with fewer characters than this carries no OCR text
JITTER = 8.0          # distinct font sizes per page; measured 20 and 11 vs <= 5.2
SAMPLE = 6            # pages sampled; enough to classify, cheap on a 700-page book


def _page_facts(pg):
    W, H = pg.rect.width, pg.rect.height
    biggest = 0.0
    for im in pg.get_images(full=True):
        for r in pg.get_image_rects(im[0]):
            biggest = max(biggest, r.width * r.height / max(1.0, W * H))
    sizes, fonts = set(), set()
    for b in pg.get_text("dict")["blocks"]:
        for l in b.get("lines", []):
            for s in l["spans"]:
                if s["text"].strip():
                    sizes.add(round(s["size"], 1))
                    fonts.add(s["font"])
    return dict(biggest=biggest, chars=len(pg.get_text()), sizes=sizes, fonts=fonts)


def classify(path):
    doc = pymupdf.open(path)
    idx = list(range(min(doc.page_count, SAMPLE)))
    facts = [_page_facts(doc[i]) for i in idx]
    if not facts:
        return dict(document_class="empty", text_layer="none",
                    font_metrics_reliable=False, evidence={})

    scan_pages = [f for f in facts if f["biggest"] >= SCAN_COVER]
    frac = len(scan_pages) / len(facts)
    chars = statistics.median(f["chars"] for f in (scan_pages or facts))
    sizes = set().union(*(f["sizes"] for f in facts))
    jitter = len(sizes) / len(facts)
    fonts = set().union(*(f["fonts"] for f in facts))

    # A single full-page figure does not make a scan, so this is a majority
    # test rather than an any-test.
    if frac >= 0.6:
        cls = "ocr_scan" if chars >= OCR_CHARS else "image_only"
    elif frac == 0:
        cls = "born_digital"
    else:
        cls = "mixed"

    text_layer = {"ocr_scan": "ocr", "image_only": "none",
                  "born_digital": "native"}.get(cls, "mixed")
    return dict(
        document_class=cls,
        text_layer=text_layer,
        # size and weight only. Positions are NOT covered by this flag and
        # remain usable on a scan - see the note on size jitter above.
        font_sizes_reliable=(jitter < JITTER and cls == "born_digital"),
        evidence=dict(pages=doc.page_count, sampled=len(facts),
                      scan_page_fraction=round(frac, 2),
                      median_chars_per_page=int(chars),
                      distinct_sizes_per_page=round(jitter, 1),
                      has_courier=any("courier" in f.lower() for f in fonts)),
    )


if __name__ == "__main__":
    import sys, json
    for p in sys.argv[1:]:
        print(json.dumps({p.split("/")[-1]: classify(p)}, indent=1))
