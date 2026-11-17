"""Split the v10 supplementary into the PLOS supporting-information files.

Run: python3 make_plos_si.py <outdir>

Writes S1_Table.docx .. S4_Table.docx. The supporting figure is produced as a
TIFF by make_plos_figures.py and is not emitted here.

Three things this does that a naive body-slice does not, each of which was a
real defect in the first attempt of 5 November 2026:

  1. The last item's slice is bounded by the supporting FIGURE, not by the end
     of the body. The v10 supplementary ends with the S5 drawing and a caption
     beginning "Supplementary Figure S5", which does not match a "Table S<n>."
     or "Figure S<n>." pattern, so an unbounded last slice swallowed both and
     S4_Table.docx silently contained the whole S5 figure that is supplied
     separately as its own file.
  2. Tracked changes are accepted. The v10 supplementary carries Thomas Yuan's
     revisions, 26 insertions and 21 deletions concentrated in the S4 section,
     and they rendered visibly, showing superseded and replacement values in the
     same cells. PLOS publishes supporting files exactly as supplied and does
     not copyedit them, so edit history must not ship.
  3. S2 gets a legend defining its channel abbreviations. PLOS asks legends to
     define non-standard abbreviations, and GOPC/FMC, A&E and GP appear in S2
     and in Fig 4 without definition. The expansions are taken from
     data_dictionary_flu_express.csv, not from assumption:
       ILI_FMC  General Outpatient Clinics / Family Medicine Clinics, public sector
       ILI_PMP  private medical practitioners, sentinel general practitioners
       ILI_AED  Accident and Emergency departments
"""
import copy, os, re, sys, tempfile, zipfile

from lxml import etree

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
XML = 'http://www.w3.org/XML/1998/namespace'
def q(t): return '{%s}%s' % (W, t)

REPO = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(REPO, 'Claude outputs',
                   '2026-10-15_early-warning_v10_supplementary.docx')
S2_LEGEND = (
    'Channel abbreviations: GOPC/FMC ILI, influenza-like illness consultation rate at General '
    'Outpatient Clinics and Family Medicine Clinics (public sector); GP ILI, influenza-like '
    'illness consultation rate from private medical practitioners (sentinel general '
    'practitioners); A&E ILI, influenza-like illness rate at Accident and Emergency '
    'departments. Definitions follow the data dictionary in S3 Table.')


def text_of(e):
    return ''.join(x.text or '' for x in e.iter(q('t')))


def accept_revisions(root):
    """Apply every tracked change, so no edit history ships."""
    for p in root.iter(q('p')):
        rpr = p.find(q('pPr') + '/' + q('rPr'))
        if rpr is not None:
            for mk in rpr.findall(q('del')) + rpr.findall(q('ins')):
                rpr.remove(mk)
    for e in list(root.iter()):
        if not isinstance(e.tag, str) or e.getparent() is None:
            continue
        ln = etree.QName(e).localname
        par = e.getparent()
        if ln in ('del', 'moveFrom') and etree.QName(par).localname != 'rPr':
            par.remove(e)
        elif ln in ('ins', 'moveTo') and etree.QName(par).localname != 'rPr':
            for ch in list(e):
                e.addprevious(ch)
            par.remove(e)
    for e in list(root.iter()):
        if not isinstance(e.tag, str) or e.getparent() is None:
            continue
        if etree.QName(e).localname in ('pPrChange', 'rPrChange', 'sectPrChange',
                                        'moveFromRangeStart', 'moveFromRangeEnd',
                                        'moveToRangeStart', 'moveToRangeEnd'):
            e.getparent().remove(e)
    return root


def legend_para(model, body_text):
    p = copy.deepcopy(model)
    for ch in list(p):
        if etree.QName(ch).localname != 'pPr':
            p.remove(ch)
    src = None
    for r in model.iter(q('r')):
        if r.find(q('t')) is not None:
            src = r
            break
    r = etree.SubElement(p, q('r'))
    if src is not None and src.find(q('rPr')) is not None:
        r.append(copy.deepcopy(src.find(q('rPr'))))
    t = etree.SubElement(r, q('t'))
    t.text = body_text
    t.set('{%s}space' % XML, 'preserve')
    return p


def main(outdir):
    os.makedirs(outdir, exist_ok=True)
    with zipfile.ZipFile(SRC) as z:
        order = [i.filename for i in z.infolist()]
        base = z.read('word/document.xml')

    probe = etree.fromstring(base)
    pbody = probe.find(q('body'))
    kids = list(pbody)

    starts = {}
    for i, e in enumerate(kids):
        m = re.match(r'^\s*Table S(\d)\.', text_of(e))
        if m and int(m.group(1)) not in starts:
            starts[int(m.group(1))] = i
    assert starts, 'no "Table S<n>." captions found'
    # The supporting figure bounds the last table, however its caption is worded.
    # Search only AFTER the last table caption: the contents listing near the top
    # also names "Figure S5", and matching that put the boundary at index 4.
    last_cap = max(starts.values())
    # Match the figure's own CAPTION or its drawing, never a mention: S4's panel
    # A legitimately cites "(Figure S5)" in its text, and matching that cut S4
    # off before its two tables.
    figure_at = next((i for i, e in enumerate(kids)
                      if i > last_cap and (list(e.iter(q('drawing')))
                      or re.match(r'^\s*(Supplementary )?Figure S\d\.', text_of(e)))),
                     len(kids))
    ordered = sorted(starts.items(), key=lambda kv: kv[1])
    print(f'captions at body indices {dict(ordered)}; supporting figure begins at {figure_at}')

    made = []
    with tempfile.TemporaryDirectory() as scratch:
        with zipfile.ZipFile(SRC) as z:
            z.extractall(scratch)
        docpath = os.path.join(scratch, 'word', 'document.xml')
        for pos, (n, start) in enumerate(ordered):
            end = ordered[pos + 1][1] if pos + 1 < len(ordered) else figure_at
            assert end <= figure_at, f'S{n} slice would reach into the supporting figure'
            root = etree.fromstring(base)
            body = root.find(q('body'))
            all_kids = list(body)
            keep = all_kids[start:end]
            sect = [e for e in all_kids if etree.QName(e).localname == 'sectPr']
            for e in all_kids:
                if e not in keep and e not in sect:
                    body.remove(e)
            accept_revisions(root)
            for t in root.iter(q('t')):
                if not t.text: continue
                t.text = re.sub(r'Supplementary Table S(\d)', r'S\1 Table', t.text)
                t.text = re.sub(r'\(Supplementary Figure S(\d)\)', r'(S\1 Fig)', t.text)
                t.text = re.sub(r'\(Figure S(\d)\)', r'(S\1 Fig)', t.text)
            if n == 2:
                model = next(p for p in body.iter(q('p')) if text_of(p).strip())
                anchor = [e for e in body if etree.QName(e).localname in ('p', 'tbl')][-1]
                anchor.addnext(legend_para(model, S2_LEGEND))
            etree.ElementTree(root).write(docpath, xml_declaration=True,
                                          encoding='UTF-8', standalone=True)
            out = os.path.join(outdir, f'S{n}_Table.docx')
            with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
                for name in order:
                    z.write(os.path.join(scratch, *name.split('/')), name)
            made.append((out, n))

    print()
    bad = []
    for out, n in made:
        z = zipfile.ZipFile(out)
        r = etree.fromstring(z.read('word/document.xml'))
        ins = len(list(r.iter(q('ins'))))
        dele = len(list(r.iter(q('del'))))
        drw = len(list(r.iter(q('drawing'))))
        ntbl = len(list(r.iter(q('tbl'))))
        txt = '\n'.join(text_of(p) for p in r.iter(q('p')))
        s5 = any(re.match(r'^\s*(Supplementary )?Figure S\d\.', t)
                 for t in (text_of(p) for p in r.iter(q('p'))))
        cap = next(t for t in (text_of(p) for p in r.iter(q('p'))) if t.strip())
        fails = []
        if ins or dele:
            fails.append(f'{ins} ins / {dele} del remain')
        if drw:
            fails.append(f'{drw} drawing(s)')
        if s5:
            fails.append('supporting-figure caption present')
        if n == 4 and ntbl != 2:
            fails.append(f'S4 should carry both panels, found {ntbl} table(s)')
        if n != 4 and ntbl != 1:
            fails.append(f'expected 1 table, found {ntbl}')
        if not cap.strip().startswith(f'Table S{n}.'):
            fails.append('wrong opening caption')
        if n == 2 and 'GOPC/FMC ILI' not in txt:
            fails.append('S2 legend missing')
        print(f'  S{n}_Table.docx  {ntbl} table(s)  {os.path.getsize(out)/1024:.0f} KB  '
              + ('PASS' if not fails else '; '.join(fails)))
        print(f'      {cap[:92]}')
        if fails:
            bad.append(n)
    if bad:
        print('\nFAILED: S' + ', S'.join(str(b) for b in bad))
        return 1
    print('\nall supporting tables clean: no revisions, no embedded figure, captions aligned')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else '.'))
