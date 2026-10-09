"""Tools the reading agents may call. Nothing here sees the golden netlists.

  zoom IMG X0 Y0 X1 Y1 OUT   crop a region given as fractions of width/height
                             (0..1) and upscale it so the long edge is ~1400 px
  grid IMG OUT               the whole image with a labelled 10x10 grid, so a
                             region can be named before zooming
  check PRED.json            schema check only: known types, complete ports
"""
import json
import sys

from PIL import Image, ImageDraw

TYPES = {
    "PMOS": ["Drain", "Gate", "Source", "Body"], "NMOS": ["Drain", "Gate", "Source", "Body"],
    "NPN": ["Collector", "Base", "Emitter"], "PNP": ["Collector", "Base", "Emitter"],
    "Res": ["Pos", "Neg"], "Cap": ["Pos", "Neg"], "Ind": ["Pos", "Neg"],
    "Diode": ["In", "Out"], "Current": ["In", "Out"], "Voltage": ["Positive", "Negative"],
    "Diso_amp": ["InP", "InN", "Out"], "Dido_amp": ["InP", "InN", "OutP", "OutN"],
    "Siso_amp": ["In", "Out"],
}
LONG = 1400


def zoom(img, x0, y0, x1, y1, out):
    im = Image.open(img).convert("RGB")
    W, H = im.size
    box = (int(float(x0) * W), int(float(y0) * H), int(float(x1) * W), int(float(y1) * H))
    c = im.crop(box)
    k = max(1.0, LONG / max(c.size))
    c.resize((int(c.width * k), int(c.height * k)), Image.LANCZOS).save(out)
    print(f"{out}: region px {box} of {W}x{H}, scaled x{k:.1f}")


def grid(img, out):
    im = Image.open(img).convert("RGB")
    k = max(1.0, LONG / max(im.size))
    im = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    for i in range(1, 10):
        x, y = im.width * i // 10, im.height * i // 10
        d.line([(x, 0), (x, im.height)], fill=(255, 0, 0), width=1)
        d.line([(0, y), (im.width, y)], fill=(255, 0, 0), width=1)
        d.text((x + 2, 2), f"{i/10:.1f}", fill=(255, 0, 0))
        d.text((2, y + 2), f"{i/10:.1f}", fill=(255, 0, 0))
    im.save(out)
    print(f"{out}: {im.width}x{im.height}, grid lines every 0.1")


def check(path):
    j = json.load(open(path))
    bad = []
    if "ckt_netlist" not in j or "ckt_type" not in j:
        bad.append("top level needs ckt_type and ckt_netlist")
    for i, d in enumerate(j.get("ckt_netlist", [])):
        t, pc = d.get("component_type"), d.get("port_connection", {})
        if t not in TYPES:
            bad.append(f"#{i}: unknown component_type {t!r}")
            continue
        need = [p for p in TYPES[t] if p != "Body"]
        miss = [p for p in need if p not in pc]
        extra = [p for p in pc if p not in TYPES[t]]
        if miss or extra:
            bad.append(f"#{i} {t}: missing {miss} unexpected {extra}")
        if any(not isinstance(v, str) or not v for v in pc.values()):
            bad.append(f"#{i} {t}: every port needs a net name")
    n = len(j.get("ckt_netlist", []))
    print("OK" if not bad else "\n".join(bad), f"({n} devices)")


if __name__ == "__main__":
    cmd, *a = sys.argv[1:]
    {"zoom": zoom, "grid": grid, "check": check}[cmd](*a)
