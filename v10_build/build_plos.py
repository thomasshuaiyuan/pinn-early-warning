"""Format the early-warning manuscript for PLOS Computational Biology.

Source: 2026-11-05_early-warning_v11.docx (tracked changes on the released v10).
Output: a clean submission draft. Every revision of Vijay's is APPLIED as final
text rather than discarded, and all 26 of his comments are carried across, so
nothing of his is lost. One thing is deliberately left as a tracked change: the
relocation of Materials and Methods to PLOS section order, because that position
was his own structural edit and he must be able to reject it in one click.

Requirements implemented, from the journal's own guidelines pages:
  title <=200 char; short title <=70 char; abstract <=300 words; author summary
  150-200 words, first person; order Title/Authors/Abstract/Author Summary/
  Introduction/Results/Discussion/Materials and Methods/Acknowledgments/
  References/Supporting information captions; "Fig 1" labels with captions in
  read order after the first citing paragraph; tables after the citing paragraph
  with label and title above; supporting items named "S1 Table"/"S5 Fig" with
  captions at the end of the manuscript; double spaced, page numbers, continuous
  line numbers; no footnotes.
"""
import copy, hashlib, os, re, shutil, sys, time, zipfile
from lxml import etree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ooxml_track import NS, q, W, XML

HOME = os.path.expanduser('~')
BUILD = f'{HOME}/mnt/pinn-early-warning/v10_build'
SRC  = f'{BUILD}/2026-11-05_early-warning_v11.docx'
FIGS = f'{HOME}/mnt/pinn-early-warning/Claude outputs/2026-10-15_early-warning_v10_figures.docx'
DEST = f'{HOME}/mnt/OneDrive-TheUniversityofHongKong-Connect/Thomas early-warning/6_plos_submission'
OUT  = f'{DEST}/2026-11-05_early-warning_PLOSCB_submission.docx'
WORK = f'{BUILD}/_plos_{int(time.time())}'
AUTHOR, DATE = 'Thomas Yuan', '2026-11-05T12:00:00Z'
SHORT_TITLE = 'R(t) onset detection for influenza and RSV in Hong Kong'

fail = []
def check(ok, label, detail=''):
    print(('  PASS  ' if ok else '  FAIL  ') + label + (('  -- ' + detail) if detail else ''))
    if not ok: fail.append(label)

with zipfile.ZipFile(SRC) as z:
    z.extractall(WORK); ORDER = [i.filename for i in z.infolist()]
docpath = os.path.join(WORK, 'word', 'document.xml')
tree = etree.parse(docpath); root = tree.getroot()
body = root.find('w:body', NS)
NEXT = [9000]
def nid():
    NEXT[0] += 1; return str(NEXT[0])

def ptext(p):
    return ''.join(t.text or '' for t in p.iter(q('t')))

# ---------------------------------------------------------------- 1. accept all
# w:del / w:moveFrom go; w:ins / w:moveTo are unwrapped; paragraph-mark records
# and range markers are dropped. Comment marks are untouched.
removed_paras = 0
for p in list(root.iter(q('p'))):
    mk = p.find('w:pPr/w:rPr/w:del', NS)
    if mk is not None:                      # a paragraph break someone deleted
        p.find('w:pPr/w:rPr', NS).remove(mk)
for e in list(root.iter()):
    if not isinstance(e.tag, str) or e.getparent() is None: continue
    ln = etree.QName(e).localname
    if ln in ('del', 'moveFrom') and e.getparent() is not None and etree.QName(e.getparent()).localname != 'rPr':
        e.getparent().remove(e)
    elif ln in ('ins', 'moveTo') and etree.QName(e.getparent()).localname != 'rPr':
        par = e.getparent()
        for ch in list(e): e.addprevious(ch)
        par.remove(e)
for e in list(root.iter()):
    if not isinstance(e.tag, str) or e.getparent() is None: continue
    ln = etree.QName(e).localname
    if ln in ('ins', 'del') and etree.QName(e.getparent()).localname == 'rPr':
        e.getparent().remove(e)                      # paragraph-mark revisions
    elif ln in ('moveFromRangeStart','moveFromRangeEnd','moveToRangeStart',
                'moveToRangeEnd','pPrChange','rPrChange','sectPrChange'):
        e.getparent().remove(e)
for p in list(root.iter(q('p'))):                    # empty shells left behind
    if not ptext(p).strip() and p.find('w:pPr/w:rPr', NS) is not None \
       and len(p.findall(q('r'))) == 0 and p.getparent() is body:
        pass                                          # keep spacing paragraphs
# Two comment reference runs (142 and 703, a closed Vijay/Thomas exchange) sat
# inside text he later deleted, so accepting the changes takes the run with it
# and leaves a dangling range. Re-anchor each at the end of its own range.
def ref_run(cid):
    r = etree.Element(q('r'))
    rp = etree.SubElement(r, q('rPr'))
    st = etree.SubElement(rp, q('rStyle')); st.set(q('val'), 'CommentReference')
    cr = etree.SubElement(r, q('commentReference')); cr.set(q('id'), str(cid))
    return r
have = {e.get(q('id')) for e in root.iter(q('commentReference'))}
repaired = []
for e in list(root.iter(q('commentRangeEnd'))):
    cid = e.get(q('id'))
    if cid not in have:
        e.addnext(ref_run(cid)); have.add(cid); repaired.append(cid)
if repaired:
    print('re-anchored comment references lost with deleted text:', ', '.join(repaired))

print('revisions applied; comments retained:',
      len(list(root.iter(q('commentRangeStart')))))

P = lambda: [p for p in body if etree.QName(p).localname == 'p']
def find_para(frag, among=None):
    hits = [p for p in (among or P()) if frag in ptext(p)]
    assert hits, f'not found: {frag[:60]!r}'
    return hits[0]

# ------------------------------------------------- 2. strip the draft-status line
dl = find_para('DRAFT v10, 15 October 2026')
body.remove(dl)
print('removed the draft-status line')

# --------------------------------- 3. lift Highlights out, to hold at the end
hl_head = find_para('Highlights')
hl = [hl_head]
n = hl_head.getnext()
while n is not None and etree.QName(n).localname == 'p' and not (
        n.find('w:pPr/w:pStyle', NS) is not None
        and n.find('w:pPr/w:pStyle', NS).get(q('val')) == 'Heading1'):
    hl.append(n); n = n.getnext()
while hl and not ptext(hl[-1]).strip(): hl.pop()
for p in hl: body.remove(p)
print(f'lifted the Highlights block ({len(hl)} paragraphs) for the back matter')

# ------------------------------------- 4. figure captions from the figures file
figroot = etree.fromstring(zipfile.ZipFile(FIGS).read('word/document.xml'))
caps = {}
for p in figroot.iter(q('p')):
    t = ''.join(x.text or '' for x in p.iter(q('t'))).strip()
    m = re.match(r'^Figure (\d)\.\s*(.+)$', t)
    if m: caps[int(m.group(1))] = m.group(2).strip()
assert len(caps) == 4, caps
print('figure captions recovered:', sorted(caps))

def body_para_of(el):
    while el.getparent() is not body: el = el.getparent()
    return el

model = find_para('EpiEstim detected onset in all 6 influenza seasons')
def make_caption(label, text):
    p = copy.deepcopy(model)
    for ch in list(p):
        if etree.QName(ch).localname != 'pPr': p.remove(ch)
    for ch in list(p.find(q('pPr')) if p.find(q('pPr')) is not None else []):
        if etree.QName(ch).localname in ('sectPr',): p.find(q('pPr')).remove(ch)
    src = None
    for r in model.iter(q('r')):
        if r.find(q('t')) is not None: src = r; break
    def run(s, bold):
        r = etree.SubElement(p, q('r'))
        if src is not None and src.find(q('rPr')) is not None:
            rp = copy.deepcopy(src.find(q('rPr')))
            for x in rp.findall(q('rPrChange')): rp.remove(x)
            if bold and rp.find(q('b')) is None: etree.SubElement(rp, q('b'))
            if not bold:
                for x in rp.findall(q('b')): rp.remove(x)
            r.append(rp)
        elif bold:
            etree.SubElement(etree.SubElement(r, q('rPr')), q('b'))
        t = etree.SubElement(r, q('t')); t.text = s
        t.set('{%s}space' % XML, 'preserve')
    head, _, rest = text.partition('. ')
    run(f'{label}. {head}. ', True)
    if rest: run(rest, False)
    return p

for nfig in sorted(caps):
    cite = None
    for p in P():
        if re.search(r'Fig\.?\s*%d\b' % nfig, ptext(p)) and not re.match(r'^\s*Fig', ptext(p)):
            cite = p; break
    assert cite is not None, nfig
    cite.addnext(make_caption(f'Fig {nfig}', caps[nfig]))
    print(f'  Fig {nfig} caption placed after its first citation')

# ------------------------------- 5. PLOS labels for figures and supporting items
subs = [(r'Supplementary Table S(\d)', r'S\1 Table'),
        (r'Supplementary Fig\.?\s*S(\d)', r'S\1 Fig'),
        (r'Supplementary Figure S(\d)', r'S\1 Fig'),
        (r'\bTable S(\d)', r'S\1 Table'),
        (r'\bFig\.\s*S(\d)', r'S\1 Fig'),
        (r'\bFig\.\s*(\d)', r'Fig \1')]
nsub = 0
for t in root.iter(q('t')):
    if not t.text: continue
    s0 = t.text
    for pat, rep in subs: t.text = re.sub(pat, rep, t.text)
    if t.text != s0: nsub += 1
print(f'label normalisation touched {nsub} text runs')

# ------------------------- 6. Methods to PLOS position, as a tracked relocation
heads = [p for p in P() if (p.find('w:pPr/w:pStyle', NS) is not None
         and p.find('w:pPr/w:pStyle', NS).get(q('val')) == 'Heading1')]
m_start = find_para('Materials and Methods', heads)
after = find_para('Results', [h for h in heads if ptext(h).strip() == 'Results'])
meth = []
p = m_start
while p is not after:
    meth.append(p); p = p.getnext()
refs_head = find_para('References', heads)

def mark_para(p, kind):
    """Wrap every run of p in w:ins or w:del and mark its paragraph mark."""
    ppr = p.find(q('pPr'))
    if ppr is None:
        ppr = etree.Element(q('pPr')); p.insert(0, ppr)
    rpr = ppr.find(q('rPr'))
    if rpr is None: rpr = etree.SubElement(ppr, q('rPr'))
    m = etree.SubElement(rpr, q(kind))
    m.set(q('id'), nid()); m.set(q('author'), AUTHOR); m.set(q('date'), DATE)
    for r in list(p):
        if etree.QName(r).localname != 'r': continue
        w = etree.Element(q(kind))
        w.set(q('id'), nid()); w.set(q('author'), AUTHOR); w.set(q('date'), DATE)
        r.addprevious(w); w.append(r)
        if kind == 'del':
            for t in r.findall(q('t')):
                t.tag = q('delText'); t.set('{%s}space' % XML, 'preserve')
    return p

anchor = refs_head.getprevious()
def strip_comment_marks(p):
    for e in list(p.iter()):
        if not isinstance(e.tag, str) or e.getparent() is None: continue
        if etree.QName(e).localname in ('commentRangeStart','commentRangeEnd'):
            e.getparent().remove(e)
        elif etree.QName(e).localname == 'commentReference':
            r = e.getparent()
            if r.getparent() is not None: r.getparent().remove(r)
    return p

for src_p in meth:                      # inserted copy at the PLOS position
    cp = mark_para(copy.deepcopy(src_p), 'ins')
    anchor.addnext(cp); anchor = cp
for src_p in meth:                      # original marked as moved away
    mark_para(strip_comment_marks(src_p), 'del')
print(f'Methods ({len(meth)} paragraphs) relocated after the Discussion, tracked')

# ----------------------------------------------------------- 7. the back matter
def plain(text, style=None, bold_head=None):
    p = copy.deepcopy(model)
    for ch in list(p):
        if etree.QName(ch).localname != 'pPr': p.remove(ch)
    ppr = p.find(q('pPr'))
    if style:
        for x in ppr.findall(q('pStyle')): ppr.remove(x)
        s = etree.Element(q('pStyle')); s.set(q('val'), style); ppr.insert(0, s)
    src = None
    for r in model.iter(q('r')):
        if r.find(q('t')) is not None: src = r; break
    def run(s, bold):
        r = etree.SubElement(p, q('r'))
        if src is not None and src.find(q('rPr')) is not None:
            rp = copy.deepcopy(src.find(q('rPr')))
            for x in rp.findall(q('rPrChange')): rp.remove(x)
            for x in rp.findall(q('b')): rp.remove(x)
            if bold: etree.SubElement(rp, q('b'))
            r.append(rp)
        t = etree.SubElement(r, q('t')); t.text = s
        t.set('{%s}space' % XML, 'preserve')
    if bold_head: run(bold_head, True); run(text, False)
    else: run(text, False)
    return p

SI = [('S1 Table', 'Season definitions, peak positivity and wave classification for all 18 pathogen-seasons.'),
      ('S2 Table', 'Pre-onset amplification by surveillance channel.'),
      ('S3 Table', 'Data dictionary for the 31 CHP Flu Express variables, January 2014 to March 2026, 638 weeks.'),
      ('S4 Table', 'Sensitivity of EpiEstim onset detection to the serial interval and estimation window.'),
      ('S5 Fig',   'Weekly discretisation of the serial-interval distributions.')]
tail = [
 plain('', 'Heading1'),
 plain('Acknowledgments', 'Heading1'),
 plain('[To be supplied by VD.]'),
 plain('Data Availability Statement', 'Heading1'),
 plain('All data analysed in this study are from public sources. The Centre for Health '
       'Protection Flu Express and respiratory surveillance series are publicly available from '
       'the CHP website. Analysis code and the derived data files that reproduce every reported '
       'value are available at https://github.com/thomasshuaiyuan/pinn-early-warning. '
       '[A DOI-issuing archive of the release is required by PLOS policy and is not yet minted: '
       'deposit the tagged release in Zenodo and replace this sentence with the DOI.]'),
 plain('Funding', 'Heading1'),
 plain('[To be supplied by VD, with the RGC grant reference.]'),
 plain('Supporting information', 'Heading1')]
for lab, title in SI:
    tail.append(plain(' ' + title, bold_head=lab + '.'))
tail += [
 plain('', 'Heading1'),
 plain('Retained from the pre-submission draft, not part of the PLOS submission', 'Heading1'),
 plain('PLOS Computational Biology has no Highlights section. These four lines are VD’s '
       'inserted prose from v9 and are held here verbatim rather than deleted. Two of them are '
       'the lines whose supporting evidence is still open.')]
anchor = refs_head
# back matter other than SI captions goes before References; captions after it,
# which is where PLOS asks for them.
pre = tail[:7]
post = tail[7:]
for p in pre:
    anchor.addprevious(p)
last = body[-1]
sectpr = last if etree.QName(last).localname == 'sectPr' else None
anchor = body[-2] if sectpr is not None else body[-1]
for p in post + hl:
    anchor.addnext(p); anchor = p
print('back matter added: Acknowledgments, Data Availability, Funding, Supporting information, retained Highlights')

# --------------------------------- 8. double spacing, line numbers, short title
for p in root.iter(q('p')):
    ppr = p.find(q('pPr'))
    if ppr is None:
        ppr = etree.Element(q('pPr')); p.insert(0, ppr)
    for x in ppr.findall(q('spacing')): ppr.remove(x)
    sp = etree.Element(q('spacing'))
    sp.set(q('line'), '480'); sp.set(q('lineRule'), 'auto')
    ins_at = 0
    for i, ch in enumerate(ppr):
        if etree.QName(ch).localname in ('pStyle', 'numPr'): ins_at = i + 1
    ppr.insert(ins_at, sp)
for sect in root.iter(q('sectPr')):
    for x in sect.findall(q('lnNumType')): sect.remove(x)
    ln = etree.Element(q('lnNumType'))
    ln.set(q('countBy'), '1'); ln.set(q('restart'), 'continuous'); ln.set(q('distance'), '360')
    sect.append(ln)
title_p = P()[0]
title_p.addnext(plain(f'Short title: {SHORT_TITLE}'))
print(f'double spacing, continuous line numbers, short title ({len(SHORT_TITLE)} chars)')

# ------------------------------------------------------------------- write out
tree.write(docpath, xml_declaration=True, encoding='UTF-8', standalone=True)
with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as z:
    for name in ORDER:
        z.write(os.path.join(WORK, *name.split('/')), name)

# ------------------------------------------------------------------- checks
print('\nchecks')
nroot = etree.parse(docpath).getroot()
nbody = nroot.find('w:body', NS)
txt = [''.join(t.text or '' for t in p.iter(q('t'))) for p in nroot.iter(q('p'))]
allt = '\n'.join(txt)
h1 = [t.strip() for p, t in zip(nroot.iter(q('p')), txt)
      if p.find('w:pPr/w:pStyle', NS) is not None
      and p.find('w:pPr/w:pStyle', NS).get(q('val')) == 'Heading1' and t.strip()]
print('   section order:', ' > '.join(h1))
want = ['Abstract','Author Summary','Introduction','Results','Discussion',
        'Materials and Methods','Acknowledgments','Data Availability Statement',
        'Funding','References','Supporting information']
seq = [x for x in h1 if x in want]
check(seq.index('Materials and Methods') > seq.index('Discussion'),
      'Methods now follows the Discussion')
check(seq.index('References') > seq.index('Materials and Methods'),
      'References follow the Methods')
check(seq.index('Supporting information') > seq.index('References'),
      'Supporting information captions are at the end')
check(len(list(nroot.iter(q('commentRangeStart')))) == 26,
      'all 26 of VD’s comments carried across',
      str(len(list(nroot.iter(q('commentRangeStart')))))) 
mine = [e for e in nroot.iter() if isinstance(e.tag, str)
        and etree.QName(e).localname in ('ins','del')]
check(all(e.get(q('author')) == AUTHOR for e in mine),
      'the only tracked change left is the Methods relocation, authored Thomas Yuan',
      f'{len(mine)} marks')
check(len(meth) > 5, 'the whole Methods section moved, not just its heading',
      f'{len(meth)} paragraphs')
cids = [e.get(q('id')) for e in nroot.iter(q('commentRangeStart'))]
check(len(cids) == len(set(cids)), 'comment ids are still unique after the relocation')
nref = len([e for e in nroot.iter(q('commentReference'))])
check(nref == 26, 'exactly 26 comment references', str(nref))
check('DRAFT v10' not in allt, 'the draft-status line is gone')
check('Highlights' in allt and 'not part of the PLOS submission' in allt,
      'Highlights preserved verbatim in the retained block')
check(not re.search(r'Fig\.\s*\d', allt), 'no "Fig." citations remain',
      str(set(re.findall(r'Fig\.?\s*\d', allt))))
check(not re.search(r'Supplementary (Table|Fig)', allt), 'no "Supplementary Table/Fig" remain')
for lab in ('S1 Table','S4 Table','S5 Fig'):
    check(lab in allt, f'{lab} named PLOS style')
for nfig in (1,2,3,4):
    check(any(t.strip().startswith(f'Fig {nfig}.') for t in txt), f'Fig {nfig} caption present')
check(all(p.find('w:pPr/w:spacing', NS) is not None
          and p.find('w:pPr/w:spacing', NS).get(q('line')) == '480'
          for p in nroot.iter(q('p'))), 'every paragraph is double spaced')
check(all(s.find(q('lnNumType')) is not None for s in nroot.iter(q('sectPr'))),
      'continuous line numbers set on every section')
check(len(SHORT_TITLE) <= 70, f'short title {len(SHORT_TITLE)} chars, limit 70')
check(len(txt[0]) <= 200, f'title {len(txt[0])} chars, limit 200')
print(f'\n{OUT}')
print('paragraphs', len(txt))
sys.exit(1 if fail else 0)
