"""OCR of a ruled table printed as an image (no PDF text layer).

Used only to verify the quotes of claims read from raster tables: the claims
agent reads the image, and a claim counts as verified only if its value is
found in the OCR text of the table. Deterministic: the grid is found from the
ruling lines (rows / columns that are mostly dark), each cell is cut out and
read by Tesseract as a single text line.

    table_ocr.py IMAGE.png [OUT.json]    -> {"cells": [[row0...], ...], "text": "..."}
"""
import json
import subprocess
import sys
import tempfile

from PIL import Image

DARK = 128


def _runs(profile, frac, size):
    """Indices where the dark fraction exceeds frac, merged into line centres."""
    idx = [i for i, v in enumerate(profile) if v > frac * size]
    lines, cur = [], []
    for i in idx:
        if cur and i - cur[-1] > 2:
            lines.append((cur[0], cur[-1]))
            cur = []
        cur.append(i)
    if cur:
        lines.append((cur[0], cur[-1]))
    return lines


def grid(im):
    w, h = im.size
    px = im.load()
    rows = [sum(px[x, y] < DARK for x in range(w)) for y in range(h)]
    hl = _runs(rows, 0.5, w)
    # vertical lines only need to span the table body, which starts below the caption
    top = hl[0][1] if hl else 0
    cols = [sum(px[x, y] < DARK for y in range(top, h)) for x in range(w)]
    vl = _runs(cols, 0.5, h - top)
    return hl, vl


def ocr_cell(im):
    with tempfile.NamedTemporaryFile(suffix=".png") as f:
        big = im.resize((im.width * 2, im.height * 2), Image.LANCZOS)
        big.save(f.name)
        r = subprocess.run(["tesseract", f.name, "-", "--psm", "7"], capture_output=True, text=True)
    return " ".join(r.stdout.split())


def table(path):
    im = Image.open(path).convert("L")
    hl, vl = grid(im)
    xs = [0] + [(a + b) // 2 for a, b in vl] + [im.width]
    ys = [(a + b) // 2 for a, b in hl]
    cells = []
    for y0, y1 in zip(ys, ys[1:]):
        if y1 - y0 < 12:
            continue                                   # double rule
        row = []
        for x0, x1 in zip(xs, xs[1:]):
            if x1 - x0 < 12:
                continue
            c = im.crop((x0 + 4, y0 + 4, x1 - 4, y1 - 4))
            row.append(ocr_cell(c) if min(c.size) > 8 else "")
        cells.append(row)
    return dict(cells=cells, text="\n".join(" | ".join(r) for r in cells))


if __name__ == "__main__":
    out = table(sys.argv[1])
    if len(sys.argv) > 2:
        json.dump(out, open(sys.argv[2], "w"), indent=1)
    print(out["text"])
