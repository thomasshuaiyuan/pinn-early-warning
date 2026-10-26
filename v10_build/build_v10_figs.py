#!/usr/bin/env python3
"""
Build 2026-10-15_early-warning_v10_figures.docx from
2026-09-26_early-warning_v9_figures.docx.

One figure changes. Figure 2 in v9 plots EpiEstim lead time against peak season
positivity, while the Results text cited it for a logistic regression on the
signal-to-noise ratio. The figure and the sentence that cited it were therefore
about different x-axes, and the sentence has been withdrawn in v10 (it is not
reproducible from any committed script). The replacement plots lead time against
SNR, which is the quantity the revised Results actually analyses, and facets by
pathogen, which is where the association disappears: Spearman rho = -0.06
(n = 8, permutation p = 0.90) within influenza and +0.23 (n = 10, p = 0.52)
within RSV, against the pooled impression the old figure gave.

Figures 1, 3 and 4 are unchanged. Figure 1 is already computed with the
weekly-discretised serial interval that the revised Methods now describe, so it
needs no regeneration; Figure 3 contains no EpiEstim and no serial interval at
all; Figure 4's bars are unchanged and its degenerate cells are already hatched
with a footnote.

A note on Figure 4, because an earlier plan for this build was wrong about it.
The preview document listed a "Figure 4 title change, outperform to lead". There
is no such title: "Age-stratified admissions outperform positivity on difficult
seasons" is a Results subsection heading in the manuscript, not a figure title,
and it is edited there (build_v10.py, E9). Nothing in this document carries the
word.

The caption and version-line edits are tracked as insertions and deletions
authored "Thomas Yuan", dated 2026-10-15, so rejecting them restores the v9
caption. The image itself cannot be tracked: a replaced image part is a binary
substitution, which is why the caption edit beside it is the visible record.
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
       'Thomas early-warning/3_docs/2026-09-26_early-warning_v9_figures.docx')
OUT = '/home/claude/vjbuild/2026-10-15_early-warning_v10_figures.docx'
NEWFIG = '/home/claude/v10_figs/fig2_snr_within_pathogen.png'
WORK = '/home/claude/vjbuild/_v10figs'
AUTHOR, DATE = 'Thomas Yuan', '2026-10-15T12:00:00Z'
WP = '{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}'
A = '{http://schemas.openxmlformats.org/drawingml/2006/main}'
PIC = '{http://schemas.openxmlformats.org/drawingml/2006/picture}'
EMU_PER_IN = 914400
WIDTH_IN = 6.5           # every figure in this document is displayed 6.5 in wide

if os.path.exists(WORK):
    shutil.rmtree(WORK)
with zipfile.ZipFile(SRC) as z:
    z.extractall(WORK)
    ORDER = [i.filename for i in z.infolist()]

docpath = os.path.join(WORK, 'word', 'document.xml')
tree = etree.parse(docpath)
root = tree.getroot()
body = root.find('w:body', NS)
ed = Editor(root, AUTHOR, DATE, first_id=7000)
P = [p for p in body if etree.QName(p).localname == 'p']

# ------------------------------------------------- 1. swap the image part itself
shutil.copy(NEWFIG, os.path.join(WORK, 'word', 'media', 'image2.png'))
w, h = Image.open(NEWFIG).size
cx = int(round(WIDTH_IN * EMU_PER_IN))
cy = int(round(WIDTH_IN * (h / w) * EMU_PER_IN))

# the drawing is the paragraph before the Figure 2 caption
target = None
for p in P:
    if p.find('.//' + WP + 'inline') is not None:
        blip = p.find('.//' + A + 'blip')
        if blip is not None and blip.get(
                '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed') == 'rId11':
            target = p
            break
if target is None:
    raise SystemExit('rId11 drawing not found')

ext = target.find('.//' + WP + 'extent')
ext.set('cx', str(cx))
ext.set('cy', str(cy))
aext = target.find('.//' + A + 'ext')
aext.set('cx', str(cx))
aext.set('cy', str(cy))
cnv = target.find('.//' + PIC + 'cNvPr')
cnv.set('name', os.path.basename(NEWFIG))
print('image2.png replaced; displayed %.2f x %.2f in' % (cx / EMU_PER_IN, cy / EMU_PER_IN))

# ----------------------------------------------------------- 2. version line
ed.replace(P[3],
           'Version: 2026-09-26, v9 (supersedes figures_v8 of 25 August 2026).',
           'Version: 2026-10-15, v10 (supersedes figures_v9 of 26 September 2026). '
           'Figure 2 is replaced; Figures 1, 3 and 4 are unchanged from v9.')

# ----------------------------------------------------------- 3. Figure 2 caption
cap = None
for p in P:
    if ed.vis_text(p).startswith('Figure 2.'):
        cap = p
        break
if cap is None:
    raise SystemExit('Figure 2 caption not found')

ed.replace(
    cap,
    'Figure 2. Signal amplitude and EpiEstim onset performance. EpiEstim lead time relative to the '
    'onset comparator (positive = earlier than the threshold) against peak season positivity for 8 '
    'influenza seasons (squares) and 10 RSV seasons (circles). Shaded region: peak positivity below '
    '10%. The corresponding signal-to-noise analysis is reported in the Results.',
    'Figure 2. Signal-to-noise ratio does not predict EpiEstim lead time within either pathogen. '
    'EpiEstim lead time relative to the onset comparator (positive = earlier than the threshold) '
    'against the season signal-to-noise ratio, defined as peak positivity divided by the non-season '
    'standard deviation, for 8 influenza seasons and 10 RSV seasons. Spearman rank correlations with '
    'two-sided permutation p-values (20,000 permutations) are shown per panel. The two labelled '
    'influenza seasons are the extremes of the signal-to-noise range and run in opposite directions '
    'to the hypothesised relationship. Lead times and signal-to-noise ratios are listed in '
    'snr_analysis_results.csv; the correlations and permutation p-values, which are Monte Carlo '
    'estimates, are in snr_within_pathogen_stats.csv with the seed used to produce them.')

# --------------------------------------------------------------------- write out
tree.write(docpath, xml_declaration=True, encoding='UTF-8', standalone=True)
if os.path.exists(OUT):
    os.remove(OUT)
with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as zo:
    for name in ORDER:
        zo.write(os.path.join(WORK, name), name)
print('edits applied: %d' % len(ed.log))
print('wrote', OUT)
