import sys; sys.path.insert(0, "/tmp/diag")
from layout import *
from xml.sax.saxutils import escape

def anchor(a, b):
    """Edge points on the two boxes, picking the side that faces the other."""
    ax, ay, aw, ah = a["x"], a["y"], a["w"], a["h"]
    bx, by, bw, bh = b["x"], b["y"], b["w"], b["h"]
    acx, acy, bcx, bcy = ax+aw/2, ay+ah/2, bx+bw/2, by+bh/2
    if bx >= ax + aw - 1:                       # b is to the right
        return (ax+aw, acy), (bx, bcy)
    if bx + bw <= ax + 1:                       # b is to the left
        return (ax, acy), (bx+bw, bcy)
    if bcy > acy:                               # below
        return (acx, ay+ah), (bcx, by)
    return (acx, ay), (bcx, by+bh)

def wrap(text, width):
    out, line = [], ""
    for word in text.split():
        t = (line + " " + word).strip()
        if len(t) > width and line:
            out.append(line); line = word
        else:
            line = t
    if line: out.append(line)
    return out

p = []
p.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
         f'viewBox="0 0 {W} {H}" font-family="Helvetica,Arial,sans-serif">')
p.append(f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>')
p.append('<defs>'
         f'<marker id="ah" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto">'
         f'<path d="M0,0 L9,4.5 L0,9 z" fill="{MUTED}"/></marker>'
         f'<marker id="ahb" markerWidth="9" markerHeight="9" refX="1" refY="4.5" orient="auto">'
         f'<path d="M9,0 L0,4.5 L9,9 z" fill="{MUTED}"/></marker></defs>')

p.append(f'<text x="24" y="38" font-size="21" font-weight="700" fill="{INK}">{escape(TITLE)}</text>')
for i, ln in enumerate(wrap(SUBTITLE, 96)):
    p.append(f'<text x="24" y="{58+i*15}" font-size="11.5" fill="{MUTED}">{escape(ln)}</text>')

for z in ZONES:
    p.append(f'<rect x="{z["x"]}" y="{z["y"]}" width="{z["w"]}" height="{z["h"]}" rx="10" '
             f'fill="none" stroke="{LINE}" stroke-dasharray="4 4"/>')
    p.append(f'<text x="{z["x"]+12}" y="{z["y"]+18}" font-size="9.5" font-weight="700" '
             f'fill="{MUTED}" letter-spacing="1.1">{escape(z["label"])}</text>')
    p.append(f'<text x="{z["x"]+12}" y="{z["y"]+31}" font-size="9" fill="{LINE}">'
             f'{escape(z["note"])}</text>')

for a_id, b_id, label, style in ARROWS:
    a, b = BY_ID[a_id], BY_ID[b_id]
    (x1, y1), (x2, y2) = anchor(a, b)
    dash = ' stroke-dasharray="5 4"' if style == "dashed" else ""
    mk = 'marker-end="url(#ah)"' if style != "back" else 'marker-start="url(#ahb)"'
    if (a_id, b_id) == ("ui", "watcher"):
        mk = 'marker-end="url(#ah)"'
    if (a_id, b_id) == ("ui", "watcher"):
        # Up the outside of the column, so it crosses nothing.
        gx = a["x"] - 16
        d = (f"M{a['x']},{a['y']+a['h']/2} H{gx} V{b['y']+b['h']/2} H{b['x']}")
        x1 = y1 = x2 = y2 = None
    elif abs(y1 - y2) > 2 and abs(x1 - x2) > 2:
        horizontal = abs(x2 - x1) > abs(y2 - y1)
        if horizontal:
            mid = x1 + (x2 - x1) * 0.5
            d = f"M{x1},{y1} H{mid} V{y2} H{x2}"
        else:
            mid = y1 + (y2 - y1) * 0.5
            d = f"M{x1},{y1} V{mid} H{x2} V{y2}"
    else:
        d = f"M{x1},{y1} L{x2},{y2}"
    p.append(f'<path d="{d}" fill="none" stroke="{MUTED}" stroke-width="1.4"{dash} {mk}/>')
    if label:
        if x1 is None:                       # the routed feedback arrow
            lx, ly = a["x"] - 16, (a["y"] + b["y"] + b["h"]) / 2 - 4
        else:
            lx, ly = (x1 + x2) / 2, (y1 + y2) / 2 - 5
        p.append(f'<rect x="{lx-len(label)*3.1-4}" y="{ly-10}" width="{len(label)*6.2+8}" '
                 f'height="13" fill="#FFFFFF" opacity="0.95"/>')
        p.append(f'<text x="{lx}" y="{ly}" font-size="9" fill="{MUTED}" '
                 f'text-anchor="middle">{escape(label)}</text>')

for b in BOXES:
    bg, ln, fg = STYLES[b["kind"]]
    p.append(f'<rect x="{b["x"]}" y="{b["y"]}" width="{b["w"]}" height="{b["h"]}" rx="7" '
             f'fill="{bg}" stroke="{ln}"/>')
    cx = b["x"] + b["w"] / 2
    p.append(f'<text x="{cx}" y="{b["y"]+19}" font-size="12" font-weight="700" fill="{fg}" '
             f'text-anchor="middle">{escape(b["title"])}</text>')
    y = b["y"] + 33
    for raw in b["sub"].split("\n"):
        for ln2 in wrap(raw, int(b["w"] / 5.4)):
            p.append(f'<text x="{cx}" y="{y}" font-size="9.5" fill="{MUTED}" '
                     f'text-anchor="middle">{escape(ln2)}</text>')
            y += 11.5

lx, ly = 24, H - 40
for kind, text in LEGEND:
    bg, ln, fg = STYLES[kind]
    p.append(f'<rect x="{lx}" y="{ly-9}" width="13" height="11" rx="2.5" fill="{bg}" stroke="{ln}"/>')
    p.append(f'<text x="{lx+19}" y="{ly}" font-size="10" fill="{MUTED}">{escape(text)}</text>')
    lx += 24 + len(text) * 5.6
p.append(f'<text x="{W-24}" y="{H-18}" font-size="9" fill="{LINE}" text-anchor="end">'
         f'Orchestration-MEA · Ben-Shalom Lab</text>')
p.append("</svg>")

open("/tmp/diag/orchestrator_dataflow.svg", "w").write("\n".join(p))
print("svg written:", len("\n".join(p)), "bytes")
