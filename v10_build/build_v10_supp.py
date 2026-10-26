#!/usr/bin/env python3
"""
Build 2026-10-15_early-warning_v10_supplementary.docx from
2026-09-26_early-warning_v9_supplementary.docx.

Two changes.

(1) Table S4 is restated on the number of DISTINCT configurations.

The influenza panel swept serial-interval means of 2.0, 2.5, 3.0, 3.5 and 4.0
days against estimation windows of 3, 4, 5 and 6 weeks, and reported SD across
all 20 grid points. After discretisation onto the weekly grid the five means
give weekly serial-interval distributions that differ by a maximum pairwise
total-variation distance of 0.013, and the detected onset is identical across
all five means in all 24 season-window cells (verified from
epiestim_si_sensitivity_flu.csv). So the grid holds 4 distinct configurations,
each counted five times, and counting each five times narrows the reported SD
through the n-1 denominator alone: 3.1 to 11.4 becomes 3.5 to 12.8. Medians,
ranges and range widths are identical under both counts and are unchanged here;
only the Configurations, Onset detected and SD columns move.

The RSV panel is NOT collapsed. There the serial-interval mean changes the
detected onset in 3 of the 12 season-window cells, so all 20 grid points are
kept and panel B's numbers are unchanged.

Decision record: the asymmetry between the two panels is a property of the
distributions, not a choice. Influenza means of 2.0 to 4.0 days all fall inside
the first weekly bin, which begins at 3.5 days; RSV means of 5.0 to 10.0 days
straddle the first two bins.

(2) Supplementary Figure S5 is added, showing the discretisation itself. The
revised Limitations cite it for the claim that the discretised influenza serial
interval is effectively a point mass at one week, so the figure has to exist in
a document the reader can open.

All text edits are tracked as insertions and deletions authored "Thomas Yuan",
dated 2026-10-15, so rejecting them reproduces the v9 supplementary exactly.
The image part itself is a binary addition and cannot be tracked; the tracked
caption beside it is the visible record.
"""
import os
import shutil
import sys
import zipfile

from lxml import etree
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ooxml_track import Editor, NS, q  # noqa: E402

SRC = ('/mnt/user-data/uploads/OneDrive-TheUniversityofHongKong-Connect/'
       'Thomas early-warning/3_docs/2026-09-26_early-warning_v9_supplementary.docx')
OUT = '/home/claude/vjbuild/2026-10-15_early-warning_v10_supplementary.docx'
FIGS5 = '/home/claude/v10_figs/figS5_si_discretisation.png'
WORK = '/home/claude/vjbuild/_v10supp'
AUTHOR, DATE = 'Thomas Yuan', '2026-10-15T12:00:00Z'
EMU_PER_IN = 914400
WIDTH_IN = 6.5
RID = 'rId100'
PNG_NAME = 'image1.png'

if os.path.exists(WORK):
    shutil.rmtree(WORK)
with zipfile.ZipFile(SRC) as z:
    z.extractall(WORK)
    ORDER = [i.filename for i in z.infolist()]

docpath = os.path.join(WORK, 'word', 'document.xml')
tree = etree.parse(docpath)
root = tree.getroot()
body = root.find('w:body', NS)
ed = Editor(root, AUTHOR, DATE, first_id=6000)
items = list(body)


def cell_replace(tbl, row, col, old, new):
    tr = tbl.findall(q('tr'))[row]
    tc = tr.findall(q('tc'))[col]
    for p in tc.findall(q('p')):
        if old in ed.vis_text(p):
            ed.replace(p, old, new)
            return
    raise SystemExit('cell [%d][%d] has no %r' % (row, col, old))


# ---------------------------------------------------------------- version line
ed.replace(items[3],
           'Version: 2026-09-26, v9 (supersedes supplementary_v8 of 25 August 2026).',
           'Version: 2026-10-15, v10 (supersedes supplementary_v9 of 26 September 2026).')

# -------------------------------------------------------------------- contents
ed.replace(items[4],
           'Table S4, serial interval and window sensitivity of EpiEstim onset detection.',
           'Table S4, serial interval and window sensitivity of EpiEstim onset detection. '
           'Figure S5, weekly discretisation of the serial-interval distributions.')

# --------------------------------------------------------------- panel A caption
ed.replace(
    items[16],
    'A. Influenza (6 seasons, 20 configurations each: serial interval mean 2.0, 2.5, 3.0, 3.5 or 4.0 days by window 3, 4, 5 or 6 weeks).',
    'A. Influenza (6 seasons, 4 distinct configurations each). The sweep covers a 5 by 4 grid: '
    'serial interval mean 2.0, 2.5, 3.0, 3.5 or 4.0 days by window 3, 4, 5 or 6 weeks. All five '
    'means fall below 3.5 days, where the first weekly bin begins, so after discretisation onto the '
    'weekly grid they give distributions differing by at most 0.013 in total variation (Figure S5) '
    'and the detected onset is identical across the five means in all 24 season-window cells. The '
    'grid therefore resolves to the four estimation windows, and the counts and standard deviations '
    'below are taken over those four rather than over the 20 grid points.')

# ------------------------------------------------------------------- panel A table
tblA = items[17]
NEW_SD = {1: ('3.1', '3.5'), 2: ('8.8', '9.9'), 3: ('3.6', '4.0'),
          4: ('11.4', '12.8'), 5: ('8.0', '9.0'), 6: ('6.0', '6.7')}
for row in range(1, 7):
    cell_replace(tblA, row, 1, '20', '4')
    cell_replace(tblA, row, 2, '20/20', '4/4')
    old, new = NEW_SD[row]
    cell_replace(tblA, row, 5, old, new)

# --------------------------------------------------------------- panel B caption
ed.insert_after(
    items[18],
    'SD 0.4 times the mean, by window 3, 4, 5 or 6 weeks).',
    ' This panel is not collapsed: the RSV means straddle the first two weekly bins, the serial '
    'interval mean changes the detected onset in 3 of the 12 season-window cells, and all 20 grid '
    'points are retained.')

# ---------------------------------------------------------------------- footnote
ed.replace(
    items[20],
    'SD is the sample standard deviation across the 20 configurations.',
    'SD is the sample standard deviation across the distinct configurations, 4 for influenza and 20 '
    'for RSV. The influenza SDs are wider than those reported in the v9 supplementary (3.1 to 11.4) '
    'because each distinct configuration was previously counted five times, which narrows the sample '
    'standard deviation through its denominator without adding information. Medians, ranges and '
    'range widths are unchanged.')

# ============================================================================
# Figure S5
# ============================================================================
media = os.path.join(WORK, 'word', 'media')
os.makedirs(media, exist_ok=True)
shutil.copy(FIGS5, os.path.join(media, PNG_NAME))
w, h = Image.open(FIGS5).size
cx = int(round(WIDTH_IN * EMU_PER_IN))
cy = int(round(WIDTH_IN * (h / w) * EMU_PER_IN))

# content type: this document had no png part, so the default has to be added
ctpath = os.path.join(WORK, '[Content_Types].xml')
ct = etree.parse(ctpath)
CT = '{http://schemas.openxmlformats.org/package/2006/content-types}'
if not any(d.get('Extension') == 'png' for d in ct.getroot().findall(CT + 'Default')):
    d = etree.Element(CT + 'Default')
    d.set('Extension', 'png')
    d.set('ContentType', 'image/png')
    ct.getroot().insert(0, d)
    ct.write(ctpath, xml_declaration=True, encoding='UTF-8', standalone=True)

relpath = os.path.join(WORK, 'word', '_rels', 'document.xml.rels')
rels = etree.parse(relpath)
RL = '{http://schemas.openxmlformats.org/package/2006/relationships}'
assert not any(r.get('Id') == RID for r in rels.getroot()), 'rel id already used'
r = etree.SubElement(rels.getroot(), RL + 'Relationship')
r.set('Id', RID)
r.set('Type', 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/image')
r.set('Target', 'media/' + PNG_NAME)
rels.write(relpath, xml_declaration=True, encoding='UTF-8', standalone=True)

DRAWING = '''<w:p xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
   xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
   xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
   xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"
   xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
 <w:pPr><w:jc w:val="center"/><w:rPr><w:ins w:id="{id1}" w:author="{au}" w:date="{dt}"/></w:rPr></w:pPr>
 <w:ins w:id="{id2}" w:author="{au}" w:date="{dt}">
  <w:r><w:drawing><wp:inline>
    <wp:extent cx="{cx}" cy="{cy}"/>
    <wp:docPr id="90" name="Figure S5"/>
    <wp:cNvGraphicFramePr><a:graphicFrameLocks noChangeAspect="1"/></wp:cNvGraphicFramePr>
    <a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">
      <pic:pic>
        <pic:nvPicPr><pic:cNvPr id="0" name="figS5_si_discretisation.png"/><pic:cNvPicPr/></pic:nvPicPr>
        <pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>
        <pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"/></pic:spPr>
      </pic:pic>
    </a:graphicData></a:graphic>
  </wp:inline></w:drawing></w:r>
 </w:ins>
</w:p>'''

CAPTION_TEXT = (
    'Supplementary Figure S5. Weekly discretisation of the serial-interval distributions. '
    '(a) The gamma serial intervals specified in Methods. The dashed line marks the lower edge of '
    'the first weekly bin at 3.5 days; shading marks the probability mass below that edge, which '
    'the discretisation discards before renormalising. (b) The resulting weekly weights. For '
    'influenza, 68.5% of the distribution falls below the first bin edge, the week-1 weight becomes '
    '0.998 and the effective mean is 7.01 days; for RSV the corresponding values are 9.9%, 0.800 '
    'and 8.50 days. No serial interval shorter than approximately one week is representable at '
    'weekly resolution, which is the basis for the second limitation in the manuscript. Generated '
    'by make_v10_figs.py.')

# the caption paragraph is modelled on the Table S4 footnote, for its formatting
model = items[20]
cap = etree.fromstring(etree.tostring(model))
for ch in list(cap):
    if etree.QName(ch).localname != 'pPr':
        cap.remove(ch)
ppr = cap.find(q('pPr'))
if ppr is None:
    ppr = etree.Element(q('pPr'))
    cap.insert(0, ppr)
for ch in list(ppr):
    if etree.QName(ch).localname in ('rPr', 'pPrChange', 'sectPr'):
        ppr.remove(ch)
rpr = etree.SubElement(ppr, q('rPr'))
m = etree.SubElement(rpr, q('ins'))
m.set(q('id'), ed.nid())
m.set(q('author'), AUTHOR)
m.set(q('date'), DATE)
src_run = next((rr for rr in model.iter(q('r')) if rr.find(q('t')) is not None), None)
cap.append(ed.make_ins(CAPTION_TEXT, src_run))

drawing = etree.fromstring(DRAWING.format(id1=ed.nid(), id2=ed.nid(), au=AUTHOR, dt=DATE,
                                          cx=cx, cy=cy, rid=RID))

# placed after the Table S4 footnote, before the final sectPr
items[20].addnext(cap)
items[20].addnext(drawing)
print('Figure S5 added, displayed %.2f x %.2f in' % (cx / EMU_PER_IN, cy / EMU_PER_IN))

# --------------------------------------------------------------------- write out
tree.write(docpath, xml_declaration=True, encoding='UTF-8', standalone=True)
if os.path.exists(OUT):
    os.remove(OUT)
with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as zo:
    for name in ORDER:
        zo.write(os.path.join(WORK, name), name)
    zo.write(os.path.join(media, PNG_NAME), 'word/media/' + PNG_NAME)
print('edits applied: %d' % len(ed.log))
print('wrote', OUT)
