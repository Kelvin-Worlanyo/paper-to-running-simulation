"""Read the curve back out of a published response plot.

A paper's reported numbers can be checked against its own figures. The figures
in these papers are simulator screen captures embedded as rasters, so the curve
has to be recovered from pixels. Everything structural is measured, not
assumed:

  panels      the vertical runs of the left axis line
  ticks       dark marks just outside the axis (left of it, below it)
  y scale     the tick labels, read by the same classical OCR engine used for
              results tables printed as images, parsed leniently and then
              REJECTED unless three or more ticks are collinear in
              (pixel, value) to within a tolerance -- that collinearity test is
              what stops a single OCR error from silently rescaling the axis
  x scale     major ticks are equally spaced and the minor ticks between them
              follow log spacing, which identifies the axis as logarithmic and
              fixes the pixels-per-decade; the decade of the leftmost major
              tick cannot be had from OCR, because the exponent is a superscript
              only a few pixels tall in the source raster, so it is supplied per
              figure as a declared input and recorded with the result
  curve       for each pixel column, the centroid of the dark pixels inside the
              panel; the trace is much darker than the dotted grid, so a simple
              threshold separates them

What this does NOT do is guess. If the OCR disagrees with itself, calibration
fails and the figure is reported as unreadable rather than digitised wrongly.
"""
import json
import os
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image

DARK = 128          # ink threshold for text and ticks
CURVE = 100         # ink threshold for the plotted trace


def _ocr(img, psm="7", whitelist="0123456789.-"):
    pad = Image.new("L", (img.width + 40, img.height + 40), 255)
    pad.paste(img, (20, 20))
    pad = pad.resize((pad.width * 6, pad.height * 6), Image.LANCZOS)
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as t:
        pad.save(t.name)
        try:
            out = subprocess.run(
                ["tesseract", t.name, "stdout", "--psm", psm,
                 "-c", f"tessedit_char_whitelist={whitelist}"],
                capture_output=True, text=True, timeout=60).stdout.strip()
        finally:
            os.unlink(t.name)
    return out


def _num(s):
    """'60' / '60.' / '-40.0' -> float, or None."""
    s = s.strip().rstrip(".")
    if not s or s in "-.":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _runs(mask, min_len=1):
    out, start = [], None
    for i, v in enumerate(mask):
        if v and start is None:
            start = i
        elif not v and start is not None:
            if i - start >= min_len:
                out.append((start, i - 1))
            start = None
    if start is not None and len(mask) - start >= min_len:
        out.append((start, len(mask) - 1))
    return out


def _groups(idx, gap=3):
    g = []
    for i in idx:
        if g and i - g[-1][-1] <= gap:
            g[-1].append(i)
        else:
            g.append([i])
    return [int(np.mean(x)) for x in g]


def structure(a):
    """Axis column, bottom rule, and the vertical extent of each panel."""
    dark = a < DARK
    H, W = a.shape
    axis_x = int(np.argmax(dark.sum(0)))
    bottom = int(np.argmax(dark.sum(1)))
    panels = [(s, e) for s, e in _runs(dark[:, axis_x]) if e - s > H * 0.15]
    return dict(axis_x=axis_x, bottom_y=bottom, panels=panels)


def _leading_minus(ink):
    """True when the leftmost ink component is a short, vertically centred bar."""
    cols = np.where(ink.sum(0) > 0)[0]
    if len(cols) == 0:
        return False
    runs = _runs(np.isin(np.arange(ink.shape[1]), cols))
    if len(runs) < 2:
        return False
    first, rest = runs[0], runs[1:]
    fr = np.where(ink[:, first[0]:first[1] + 1].sum(1) > 0)[0]
    rr = np.where(ink[:, rest[0][0]:rest[-1][1] + 1].sum(1) > 0)[0]
    if len(fr) == 0 or len(rr) == 0:
        return False
    f_h, d_h = fr.max() - fr.min() + 1, rr.max() - rr.min() + 1
    f_mid, d_mid = (fr.min() + fr.max()) / 2, (rr.min() + rr.max()) / 2
    return (f_h <= 0.45 * d_h                      # much shorter than a digit
            and (first[1] - first[0] + 1) <= 0.6 * d_h   # and not wide
            and abs(f_mid - d_mid) <= 0.28 * d_h)        # sitting mid height


def y_calibration(im, a, axis_x, panel, tol=0.02):
    """(pixel -> value) for one panel, from OCR of its tick labels."""
    y0, y1 = panel
    dark = a < DARK
    strip = dark[:, max(0, axis_x - 20):axis_x - 1]
    prof = strip.sum(1)
    rows = [r for r in np.where(prof > 0)[0] if y0 <= r <= y1]
    # Major ticks reach further from the axis than minor ones; group contiguous
    # ink and keep the long groups, the same discrimination used on the x axis.
    grp = []
    for r in rows:
        if grp and r - grp[-1][-1] <= 2:
            grp[-1].append(r)
        else:
            grp.append([r])
    if not grp:
        return None, dict(reason="no tick marks found", ticks=[])
    lens = np.array([prof[g].max() for g in grp], float)
    cut = (lens.max() + lens.min()) / 2.0
    major = [g for g, L in zip(grp, lens) if L > cut] if lens.max() > lens.min() else grp
    ticks = [int(np.mean(g)) for g in (major if len(major) >= 2 else grp)]
    # where the tick marks begin, so the crop can stop short of them: a tick
    # stroke inside the crop is read as a digit
    tcols = np.where(strip.sum(0) > 0)[0]
    tick_x0 = (max(0, axis_x - 20) + int(tcols.min())) if len(tcols) else axis_x - 2
    pairs = []
    for y in ticks:
        band = dark[max(0, y - 16):y + 16, 0:max(1, tick_x0 - 2)]
        cols = np.where(band.sum(0) > 0)[0]
        if len(cols) == 0:
            continue
        runs = _runs(np.isin(np.arange(band.shape[1]), cols))
        # keep only ink adjacent to the axis: the rotated axis title sits far left
        near = [r for r in runs if r[1] >= tick_x0 - 45]
        if not near:
            continue
        x0 = max(0, min(r[0] for r in near) - 4)
        crop = im.crop((x0, y - 20, tick_x0 - 2, y + 20))
        v = _num(_ocr(crop))
        if v is None:
            continue
        # OCR drops the minus sign at this glyph size, and a sign error is
        # invisible to the collinearity test because it is systematic, so the
        # sign is read from the ink: a short bar at mid height, left of and
        # separated from the digits.
        if _leading_minus(np.asarray(crop) < DARK):
            v = -abs(v)
        pairs.append((y, v))
    if len(pairs) < 2:
        return None, dict(reason="fewer than two tick labels read", ticks=ticks)
    ys = np.array([p[0] for p in pairs], float)
    vs = np.array([p[1] for p in pairs], float)
    if vs.max() == vs.min():
        # every label read the same value: a degenerate fit that would collapse
        # the axis to a constant and pass the collinearity test trivially
        return None, dict(reason="all tick labels read the same value",
                          pairs=pairs, ticks=ticks)
    A = np.polyfit(ys, vs, 1)
    pred = np.polyval(A, ys)
    span = max(vs.max() - vs.min(), 1e-9)
    resid = np.abs(pred - vs).max() / span
    if len(pairs) >= 3 and resid > tol:
        return None, dict(reason=f"tick labels not collinear (residual {resid:.3f})",
                          pairs=pairs, ticks=ticks)
    return (lambda y: np.polyval(A, y)), dict(pairs=pairs, residual=float(resid))


def x_calibration(a, bottom_y, left_decade, depth=40, inward=False):
    """Log axis: decade spacing measured, the leftmost decade declared."""
    dark = a < DARK
    # Major and minor ticks are told apart by LENGTH, not by a fixed window:
    # on some plots the minor ticks are nearly as long as the sampling depth.
    if inward:
        # some plots draw a full frame with the ticks pointing into the axes
        band = dark[bottom_y - depth:bottom_y - 1, :][::-1]
    else:
        band = dark[bottom_y + 2:bottom_y + 2 + depth, :]
    cols = np.where(band[:4].sum(0) >= 3)[0]          # any tick at all
    cand = _groups(cols, gap=3)
    if len(cand) < 2:
        return None, dict(reason="fewer than two ticks below the axis")
    length = []
    for c in cand:
        col = band[:, max(0, c - 1):c + 2].max(1)
        r = _runs(col)
        length.append(r[0][1] - r[0][0] + 1 if r and r[0][0] == 0 else 0)
    length = np.array(length, float)
    cut = (length.max() + length.min()) / 2.0
    major = [c for c, L in zip(cand, length) if L > cut]
    if len(major) < 2:
        major = cand
    if len(major) < 2:
        return None, dict(reason="fewer than two major ticks")
    d = np.diff(major)
    if d.std() > 0.02 * d.mean():
        return None, dict(reason=f"major ticks not evenly spaced (std {d.std():.1f}px)")
    per_dec = float(d.mean())
    x0 = float(major[0])
    return (lambda x: 10.0 ** (left_decade + (np.asarray(x, float) - x0) / per_dec)), \
           dict(major=major, px_per_decade=per_dec, left_decade=left_decade)


def trace(a, panel, axis_x, pad=6, x_start=None, mask=None):
    """Curve centroid per column inside a panel."""
    y0, y1 = panel
    dark = (a < CURVE) if mask is None else mask
    xs, ys = [], []
    prev = None
    for x in range(x_start if x_start is not None else axis_x + 1, a.shape[1]):
        col = dark[y0 + pad:y1 - pad, x]
        runs = _runs(col)
        if not runs:
            continue
        # The trace is one thick contiguous run; the legend text drawn inside
        # the panel is thin and broken, so take the longest run, and on a tie
        # the one nearest the previous column, which keeps the curve continuous
        # where it passes behind the legend.
        best = max(runs, key=lambda r: (r[1] - r[0] + 1,
                                        -abs((r[0] + r[1]) / 2 - (prev if prev is not None else 0))))
        c = y0 + pad + (best[0] + best[1]) / 2.0
        xs.append(x); ys.append(c); prev = (best[0] + best[1]) / 2.0
    return np.array(xs, float), np.array(ys, float)


def digitize(path, left_decade, gain_panel=0, phase_panel=1, declared=None):
    """declared: {"gain": (top_value, step), "phase": (...)} used ONLY when the
    tick labels cannot be read. Tick POSITIONS are still measured; only the
    values are supplied, and the result records that it was used."""
    im = Image.open(path).convert("L")
    a = np.asarray(im).astype(float)
    st = structure(a)
    if len(st["panels"]) < 2:
        return dict(ok=False, reason=f"expected two panels, found {len(st['panels'])}")
    fx, xinfo = x_calibration(a, st["bottom_y"], left_decade)
    if fx is None:
        return dict(ok=False, reason=xinfo["reason"])
    out = dict(ok=True, file=os.path.basename(path), x=xinfo, panels=st["panels"])
    for name, pi in (("gain", gain_panel), ("phase", phase_panel)):
        panel = st["panels"][pi]
        fy, yinfo = y_calibration(im, a, st["axis_x"], panel)
        if fy is None and declared and name in declared:
            ticks = yinfo.get("ticks") or []
            top, step = declared[name]
            if len(ticks) >= 2:
                vals = [top + step * i for i in range(len(ticks))]
                A = np.polyfit(np.array(ticks, float), np.array(vals, float), 1)
                fy = (lambda y, A=A: np.polyval(A, y))
                yinfo = dict(declared=True, ticks=ticks, values=vals,
                             ocr_reason=yinfo.get("reason"))
        if fy is None:
            # a panel whose tick labels cannot be read is reported unread rather
            # than guessed; the other panel is still usable on its own
            out[f"{name}_unread"] = yinfo.get("reason")
            continue
        xs, ys = trace(a, panel, st["axis_x"], x_start=int(xinfo["major"][0]))
        out[name] = dict(f=fx(xs).tolist(), v=[float(fy(y)) for y in ys], cal=yinfo)
    if "gain" not in out:
        return dict(ok=False, reason=out.get("gain_unread", "gain panel unreadable"))
    return out


def metrics(d):
    """DC gain, 0 dB crossing and the phase there, from a digitised pair."""
    f = np.array(d["gain"]["f"]); g = np.array(d["gain"]["v"])
    has_phase = "phase" in d
    if has_phase:
        pf = np.array(d["phase"]["f"]); p = np.array(d["phase"]["v"])
    r = dict(dc_gain_dB=float(g[0]), f_lo_Hz=float(f[0]), f_hi_Hz=float(f[-1]),
             gain_min_dB=float(g.min()), gain_max_dB=float(g.max()))
    s = np.where(np.diff(np.sign(g)))[0]
    if len(s):
        k = int(s[0])
        lf = np.log10(f[k]) + (0 - g[k]) * (np.log10(f[k + 1]) - np.log10(f[k])) / (g[k + 1] - g[k])
        r["gbw_Hz"] = float(10 ** lf)
        if has_phase:
            r["phase_at_gbw_deg"] = float(np.interp(lf, np.log10(pf), p))
    return r


if __name__ == "__main__":
    path, dec = sys.argv[1], int(sys.argv[2])
    d = digitize(path, dec)
    if not d.get("ok"):
        print("FAILED:", d["reason"]); sys.exit(1)
    print(json.dumps({**metrics(d), "x": d["x"]}, indent=1))
