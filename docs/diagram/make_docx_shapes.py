"""The same diagram as native Word shapes, so anyone can drag the boxes.

Word has no high-level shape API in python-docx, so this writes the
WordprocessingShape (wps) XML directly: one inline group holding a rounded
rectangle per node and line segments per arrow. Built from layout.py, so the
editable version and the rendered one always describe the same architecture.
"""
import sys; sys.path.insert(0, "/tmp/diag")
from layout import *
from xml.sax.saxutils import escape
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.oxml.ns import qn
from docx.oxml import parse_xml
from docx.enum.section import WD_ORIENT

EMU = 12700                      # per point
def e(v): return int(round(v * EMU))

_id = [100]
def nid():
    _id[0] += 1
    return _id[0]

def txt_para(text, size, bold, colour, align="ctr"):
    return (f'<w:p><w:pPr><w:jc w:val="{align}"/><w:spacing w:after="0" w:line="240" '
            f'w:lineRule="auto"/></w:pPr><w:r><w:rPr>'
            f'{"<w:b/>" if bold else ""}'
            f'<w:color w:val="{colour}"/><w:sz w:val="{int(size*2)}"/>'
            f'<w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/></w:rPr>'
            f'<w:t xml:space="preserve">{escape(text)}</w:t></w:r></w:p>')

def box_shape(b):
    bg, ln, fg = STYLES[b["kind"]]
    paras = [txt_para(b["title"], 10.5, True, fg.lstrip("#"))]
    for line in b["sub"].split("\n"):
        if line.strip():
            paras.append(txt_para(line, 8, False, MUTED.lstrip("#")))
    return f'''<wps:wsp>
  <wps:cNvPr id="{nid()}" name="{escape(b['title'])}"/><wps:cNvSpPr/>
  <wps:spPr>
    <a:xfrm><a:off x="{e(b['x'])}" y="{e(b['y'])}"/><a:ext cx="{e(b['w'])}" cy="{e(b['h'])}"/></a:xfrm>
    <a:prstGeom prst="roundRect"><a:avLst><a:gd name="adj" fmla="val 9000"/></a:avLst></a:prstGeom>
    <a:solidFill><a:srgbClr val="{bg.lstrip('#')}"/></a:solidFill>
    <a:ln w="9525"><a:solidFill><a:srgbClr val="{ln.lstrip('#')}"/></a:solidFill></a:ln>
  </wps:spPr>
  <wps:txbx><w:txbxContent>{''.join(paras)}</w:txbxContent></wps:txbx>
  <wps:bodyPr rot="0" anchor="ctr" lIns="36000" rIns="36000" tIns="36000" bIns="36000"/>
</wps:wsp>'''

def zone_shape(z):
    return f'''<wps:wsp>
  <wps:cNvPr id="{nid()}" name="{escape(z['label'])}"/><wps:cNvSpPr/>
  <wps:spPr>
    <a:xfrm><a:off x="{e(z['x'])}" y="{e(z['y'])}"/><a:ext cx="{e(z['w'])}" cy="{e(z['h'])}"/></a:xfrm>
    <a:prstGeom prst="roundRect"><a:avLst><a:gd name="adj" fmla="val 4000"/></a:avLst></a:prstGeom>
    <a:noFill/>
    <a:ln w="9525"><a:solidFill><a:srgbClr val="{LINE.lstrip('#')}"/></a:solidFill>
      <a:prstDash val="dash"/></a:ln>
  </wps:spPr>
  <wps:txbx><w:txbxContent>
    {txt_para(z["label"], 7.5, True, MUTED.lstrip("#"), align="left")}
  </w:txbxContent></wps:txbx>
  <wps:bodyPr rot="0" anchor="t" lIns="72000" tIns="54000"/>
</wps:wsp>'''

def line_shape(x1, y1, x2, y2, head=False, dashed=False):
    ox, oy = min(x1, x2), min(y1, y2)
    cx, cy = abs(x2 - x1), abs(y2 - y1)
    flipH = ' flipH="1"' if x2 < x1 else ""
    flipV = ' flipV="1"' if y2 < y1 else ""
    dash = '<a:prstDash val="dash"/>' if dashed else ""
    tail = '<a:tailEnd type="triangle" w="med" len="med"/>' if head else ""
    return f'''<wps:wsp>
  <wps:cNvPr id="{nid()}" name="flow"/><wps:cNvSpPr/>
  <wps:spPr>
    <a:xfrm{flipH}{flipV}><a:off x="{e(ox)}" y="{e(oy)}"/>
      <a:ext cx="{e(max(cx,0.5))}" cy="{e(max(cy,0.5))}"/></a:xfrm>
    <a:prstGeom prst="line"><a:avLst/></a:prstGeom>
    <a:ln w="12700"><a:solidFill><a:srgbClr val="{MUTED.lstrip('#')}"/></a:solidFill>
      {dash}{tail}</a:ln>
  </wps:spPr><wps:bodyPr/>
</wps:wsp>'''

def label_shape(x, y, text):
    """A small no-fill text box, so arrow labels survive into the editable copy."""
    w, h = max(34, len(text) * 4.9), 13
    return f'''<wps:wsp>
  <wps:cNvPr id="{nid()}" name="label"/><wps:cNvSpPr txBox="1"/>
  <wps:spPr>
    <a:xfrm><a:off x="{e(x - w/2)}" y="{e(y - h/2)}"/><a:ext cx="{e(w)}" cy="{e(h)}"/></a:xfrm>
    <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
    <a:solidFill><a:srgbClr val="FFFFFF"/></a:solidFill><a:ln><a:noFill/></a:ln>
  </wps:spPr>
  <wps:txbx><w:txbxContent>{txt_para(text, 7.5, False, MUTED.lstrip("#"))}</w:txbxContent></wps:txbx>
  <wps:bodyPr rot="0" anchor="ctr" lIns="0" rIns="0" tIns="0" bIns="0"/>
</wps:wsp>'''


def legend_shapes():
    out, lx, ly = [], 24, H - 42
    for kind, text in LEGEND:
        bg, ln, fg = STYLES[kind]
        out.append(f'''<wps:wsp>
  <wps:cNvPr id="{nid()}" name="key"/><wps:cNvSpPr/>
  <wps:spPr>
    <a:xfrm><a:off x="{e(lx)}" y="{e(ly)}"/><a:ext cx="{e(13)}" cy="{e(11)}"/></a:xfrm>
    <a:prstGeom prst="roundRect"><a:avLst/></a:prstGeom>
    <a:solidFill><a:srgbClr val="{bg.lstrip("#")}"/></a:solidFill>
    <a:ln w="9525"><a:solidFill><a:srgbClr val="{ln.lstrip("#")}"/></a:solidFill></a:ln>
  </wps:spPr><wps:bodyPr/>
</wps:wsp>''')
        out.append(label_shape(lx + 19 + len(text) * 2.6, ly + 5.5, text))
        lx += 30 + len(text) * 5.4
    return out


def anchor(a, b):
    ax, ay, aw, ah = a["x"], a["y"], a["w"], a["h"]
    bx, by, bw, bh = b["x"], b["y"], b["w"], b["h"]
    acx, acy, bcx, bcy = ax+aw/2, ay+ah/2, bx+bw/2, by+bh/2
    if bx >= ax + aw - 1: return (ax+aw, acy), (bx, bcy)
    if bx + bw <= ax + 1: return (ax, acy), (bx+bw, bcy)
    if bcy > acy:         return (acx, ay+ah), (bcx, by)
    return (acx, ay), (bcx, by+bh)

shapes = [zone_shape(z) for z in ZONES]
for a_id, b_id, label, style in ARROWS:
    a, b = BY_ID[a_id], BY_ID[b_id]
    (x1, y1), (x2, y2) = anchor(a, b)
    dashed = style == "dashed"
    if (a_id, b_id) == ("ui", "watcher"):
        gx = a["x"] - 16
        pts = [(a["x"], a["y"]+a["h"]/2), (gx, a["y"]+a["h"]/2),
               (gx, b["y"]+b["h"]/2), (b["x"], b["y"]+b["h"]/2)]
    elif abs(y1-y2) > 2 and abs(x1-x2) > 2:
        if abs(x2-x1) > abs(y2-y1):
            m = x1 + (x2-x1)/2
            pts = [(x1,y1),(m,y1),(m,y2),(x2,y2)]
        else:
            m = y1 + (y2-y1)/2
            pts = [(x1,y1),(x1,m),(x2,m),(x2,y2)]
    else:
        pts = [(x1,y1),(x2,y2)]
    for i in range(len(pts)-1):
        (px,py),(qx,qy) = pts[i], pts[i+1]
        shapes.append(line_shape(px,py,qx,qy, head=(i==len(pts)-2), dashed=dashed))
    if label:
        if (a_id, b_id) == ("ui", "watcher"):
            shapes.append(label_shape(a["x"] - 16, (a["y"] + b["y"] + b["h"]) / 2, label))
        else:
            shapes.append(label_shape((x1+x2)/2, (y1+y2)/2 - 7, label))
shapes += [box_shape(b) for b in BOXES]
shapes += legend_shapes()

group = f'''<w:p xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:r><w:drawing xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing">
<wp:inline distT="0" distB="0" distL="0" distR="0">
  <wp:extent cx="{e(W)}" cy="{e(H)}"/>
  <wp:docPr id="1" name="Orchestrator data flow"/>
  <a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
    <a:graphicData uri="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup">
      <wpg:wgp xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup"
               xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape">
        <wpg:cNvGrpSpPr/>
        <wpg:grpSpPr>
          <a:xfrm><a:off x="0" y="0"/><a:ext cx="{e(W)}" cy="{e(H)}"/>
            <a:chOff x="0" y="0"/><a:chExt cx="{e(W)}" cy="{e(H)}"/></a:xfrm>
        </wpg:grpSpPr>
        {''.join(shapes)}
      </wpg:wgp>
    </a:graphicData>
  </a:graphic>
</wp:inline></w:drawing></w:r></w:p>'''

d = docx.Document()
s = d.sections[0]
s.orientation = WD_ORIENT.LANDSCAPE
s.page_width, s.page_height = Inches(16), Inches(11)
for m in ("left_margin","right_margin","top_margin","bottom_margin"):
    setattr(s, m, Inches(0.5))

p = d.add_paragraph(); r = p.add_run(TITLE)
r.bold = True; r.font.size = Pt(19); r.font.name = "Calibri"
r.font.color.rgb = RGBColor.from_string(INK.lstrip("#"))
p2 = d.add_paragraph(); r2 = p2.add_run(SUBTITLE + "  (every box is editable — click to move or retype)")
r2.font.size = Pt(10); r2.font.name = "Calibri"
r2.font.color.rgb = RGBColor.from_string(MUTED.lstrip("#"))

d.element.body.insert(2, parse_xml(group))
d.save("/tmp/diag/RBSLab_Orchestrator_DataFlow_editable.docx")
print("shapes:", len(shapes), "→ editable docx written")
