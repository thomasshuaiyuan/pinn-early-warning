"""Render the PLOS submission-ready .docx as readable Markdown.

A plain-text twin of the upload-shaped file, so a reader who would rather not
open Word sees exactly the text that is in it. Generated, never hand-edited:
the .docx is the source of truth and this is a view of it.

  python3 make_preview.py [OUT_DIR]
"""
import os, sys, zipfile
from lxml import etree

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
def q(t): return '{%s}%s' % (W, t)
NS = {'w': W}

BUILD = os.path.dirname(os.path.abspath(__file__))
STAGE = os.environ.get('PLOS_DEST') or os.path.join(BUILD, '_stage_plos')
OUT = sys.argv[1] if len(sys.argv) > 1 else STAGE
SRC = os.path.join(OUT, '2026-11-05_early-warning_PLOSCB_SUBMISSION-READY.docx')
if not os.path.isfile(SRC):
    sys.stderr.write(f'make_preview.py: not found: {SRC}\n'
                     'Run build_plos3.py first, or pass the directory holding it.\n')
    raise SystemExit(2)

root = etree.fromstring(zipfile.ZipFile(SRC).read('word/document.xml'))
body = root.find('w:body', NS)
lines, nh, np_ = [], 0, 0
for p in body:
    if etree.QName(p).localname != 'p':
        continue
    txt = ''.join((t.text or '') for t in p.iter(q('t')))
    if not txt.strip():
        continue
    sty = p.find('w:pPr/w:pStyle', NS)
    sv = sty.get(q('val')) if sty is not None else None
    if sv == 'Heading1':
        lines += ['', '## ' + txt.strip(), '']; nh += 1
    elif sv in ('Heading2', 'Heading3'):
        lines += ['', '### ' + txt.strip(), '']; nh += 1
    else:
        lines += [txt.strip(), '']; np_ += 1

hdr = ['# PLOS Computational Biology submission, readable preview', '',
       'Generated from `2026-11-05_early-warning_PLOSCB_SUBMISSION-READY.docx` by',
       '`make_preview.py`. The .docx is the source of truth; this file is a view of it and',
       'is not edited by hand. Tracked changes and comments live in the FOR-EDITING copy',
       'and are not shown here, because the submission copy carries none.', '', '---', '']
dest = os.path.join(OUT, 'PREVIEW_submission_readable.md')
with open(dest, 'w', encoding='utf-8') as f:
    f.write('\n'.join(hdr + lines).rstrip() + '\n')
print(f'wrote {dest}: {nh} headings, {np_} paragraphs, {os.path.getsize(dest)} bytes')
