"""Format the early-warning manuscript for PLOS Computational Biology, twice.

  FOR-EDITING      what VD works on: his 26 comments kept, the Methods
                   relocation left as a tracked change he can reject, the
                   Highlights block retained, every slot he must fill marked
                   [VD-n].
  SUBMISSION-READY generated from the same pipeline with the comments removed,
                   the relocation accepted and the Highlights block dropped.
                   Upload-shaped; the [VD-n] slots must be filled first.

Requirements from the journal's submission-guidelines and figures pages, read at
source 5 November 2026. Three that the first build got wrong or missed:
  - funding must NOT appear in the manuscript; it is a submission-system field;
  - ethics statements go in Materials and Methods, not the system;
  - a table goes directly after the paragraph where it is first cited.
"""
import copy, os, re, sys, time, zipfile
from lxml import etree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ooxml_track import NS, q, W, XML

HOME = os.path.expanduser('~')
BUILD = f'{HOME}/mnt/pinn-early-warning/v10_build'
SRC   = f'{BUILD}/2026-11-05_early-warning_v11.docx'
FIGS  = f'{HOME}/mnt/pinn-early-warning/Claude outputs/2026-10-15_early-warning_v10_figures.docx'
DEST  = f'{HOME}/mnt/OneDrive-TheUniversityofHongKong-Connect/Thomas early-warning/6_plos_submission'
AUTHOR, DATE = 'Thomas Yuan', '2026-11-05T12:00:00Z'
SHORT_TITLE = 'R(t) onset detection for influenza and RSV in Hong Kong'

SLOTS = {
 1: ('ETHICS STATEMENT', 'required by PLOS in Materials and Methods. Draft offered in '
     'VD_INPUT_SHEET.md; confirm or replace, and name the HREC reference if one exists.'),
 2: ('ACKNOWLEDGMENTS', 'contributors who do not meet authorship criteria, with their '
     'contribution. PLOS forbids funding sources here.'),
 3: ('CODE ARCHIVE DOI', 'PLOS requires a DOI-issuing archive; a GitHub URL alone does not '
     'satisfy the policy. Mint a Zenodo DOI from the tagged release and paste it here.'),
}

fail = []
def check(ok, label, detail=''):
    print(('  PASS  ' if ok else '  FAIL  ') + label + (('  -- ' + detail) if detail else ''))
    if not ok: fail.append(label)

def ptext(e): return ''.join(t.text or '' for t in e.iter(q('t')))

def build(mode):
    out = (f'{DEST}/2026-11-05_early-warning_PLOSCB_FOR-EDITING.docx' if mode == 'edit'
           else f'{DEST}/2026-11-05_early-warning_PLOSCB_SUBMISSION-READY.docx')
    work = f'{BUILD}/_plos2_{mode}_{int(time.time())}'
    with zipfile.ZipFile(SRC) as z:
        z.extractall(work); order = [i.filename for i in z.infolist()]
    docpath = os.path.join(work, 'word', 'document.xml')
    tree = etree.parse(docpath); root = tree.getroot()
    body = root.find('w:body', NS)
    nxt = [9000]
    def nid():
        nxt[0] += 1; return str(nxt[0])

    # ---------------------------------------------------- 1. apply all revisions
    for p in root.iter(q('p')):
        mk = p.find('w:pPr/w:rPr/w:del', NS)
        if mk is not None: p.find('w:pPr/w:rPr', NS).remove(mk)
    for e in list(root.iter()):
        if not isinstance(e.tag, str) or e.getparent() is None: continue
        ln = etree.QName(e).localname
        par = e.getparent()
        if ln in ('del', 'moveFrom') and etree.QName(par).localname != 'rPr':
            par.remove(e)
        elif ln in ('ins', 'moveTo') and etree.QName(par).localname != 'rPr':
            for ch in list(e): e.addprevious(ch)
            par.remove(e)
    for e in list(root.iter()):
        if not isinstance(e.tag, str) or e.getparent() is None: continue
        ln = etree.QName(e).localname
        if ln in ('ins','del') and etree.QName(e.getparent()).localname == 'rPr':
            e.getparent().remove(e)
        elif ln in ('moveFromRangeStart','moveFromRangeEnd','moveToRangeStart',
                    'moveToRangeEnd','pPrChange','rPrChange','sectPrChange'):
            e.getparent().remove(e)

    def ref_run(cid):
        r = etree.Element(q('r'))
        rp = etree.SubElement(r, q('rPr'))
        st = etree.SubElement(rp, q('rStyle')); st.set(q('val'), 'CommentReference')
        cr = etree.SubElement(r, q('commentReference')); cr.set(q('id'), str(cid))
        return r
    have = {e.get(q('id')) for e in root.iter(q('commentReference'))}
    for e in list(root.iter(q('commentRangeEnd'))):
        if e.get(q('id')) not in have:
            e.addnext(ref_run(e.get(q('id')))); have.add(e.get(q('id')))

    P = lambda: [p for p in body if etree.QName(p).localname == 'p']
    def find_para(frag, among=None):
        hits = [p for p in (among or P()) if frag in ptext(p)]
        assert hits, f'not found: {frag[:60]!r}'
        return hits[0]
    model = find_para('EpiEstim detected onset in all 6 influenza seasons')

    def para(bits, style=None):
        """bits: list of (text, bold)."""
        p = copy.deepcopy(model)
        for ch in list(p):
            if etree.QName(ch).localname != 'pPr': p.remove(ch)
        ppr = p.find(q('pPr'))
        if ppr is None:
            ppr = etree.Element(q('pPr')); p.insert(0, ppr)
        for x in ppr.findall(q('pStyle')): ppr.remove(x)
        if style:
            s = etree.Element(q('pStyle')); s.set(q('val'), style); ppr.insert(0, s)
        src = None
        for r in model.iter(q('r')):
            if r.find(q('t')) is not None: src = r; break
        for text, bold in bits:
            r = etree.SubElement(p, q('r'))
            if src is not None and src.find(q('rPr')) is not None:
                rp = copy.deepcopy(src.find(q('rPr')))
                for x in rp.findall(q('rPrChange')): rp.remove(x)
                for x in rp.findall(q('b')): rp.remove(x)
                if bold: etree.SubElement(rp, q('b'))
                r.append(rp)
            elif bold:
                etree.SubElement(etree.SubElement(r, q('rPr')), q('b'))
            t = etree.SubElement(r, q('t')); t.text = text
            t.set('{%s}space' % XML, 'preserve')
        return p
    def slot(n):
        lab, guide = SLOTS[n]
        return para([(f'[VD-{n} — {lab}] ', True), (guide, False)])

    # ------------------------------------------- 2. remove the draft-status line
    body.remove(find_para('DRAFT v10, 15 October 2026'))

    # ------------------------------------------------- 3. lift Highlights aside
    hl_head = find_para('Highlights')
    hl = [hl_head]; n = hl_head.getnext()
    while n is not None and etree.QName(n).localname == 'p':
        s = n.find('w:pPr/w:pStyle', NS)
        if s is not None and s.get(q('val')) == 'Heading1': break
        hl.append(n); n = n.getnext()
    while hl and not ptext(hl[-1]).strip(): hl.pop()
    for p in hl: body.remove(p)

    # ------------------------------------------- 4. figure captions, in read order
    figroot = etree.fromstring(zipfile.ZipFile(FIGS).read('word/document.xml'))
    caps = {}
    for p in figroot.iter(q('p')):
        m = re.match(r'^Figure (\d)\.\s*(.+)$', ptext(p).strip())
        if m: caps[int(m.group(1))] = m.group(2).strip()
    assert len(caps) == 4
    for nfig in sorted(caps):
        cite = next(p for p in P()
                    if re.search(r'Fig\.?\s*%d\b' % nfig, ptext(p))
                    and not re.match(r'^\s*Fig', ptext(p)))
        head, _, rest = caps[nfig].partition('. ')
        bits = [(f'Fig {nfig}. {head}. ', True)] + ([(rest, False)] if rest else [])
        cite.addnext(para(bits))

    # ------------------------- 5. PLOS labels for figures and supporting items
    subs = [(r'Supplementary Table S(\d)', r'S\1 Table'),
            (r'Supplementary Fig\.?\s*S(\d)', r'S\1 Fig'),
            (r'Supplementary Figure S(\d)', r'S\1 Fig'),
            (r'\bTable S(\d)', r'S\1 Table'),
            (r'\bFig\.\s*S(\d)', r'S\1 Fig'),
            (r'\bFig\.\s*(\d)', r'Fig \1')]
    for t in root.iter(q('t')):
        if t.text:
            for pat, rep in subs: t.text = re.sub(pat, rep, t.text)

    # ----------------------------- 6. references: first six authors, then et al.
    REFFIX = {
      'Lison A, McLeod RE, Huisman JS, Munday JD, Ort C, Julian TR, Stadler T.':
      'Lison A, McLeod RE, Huisman JS, Munday JD, Ort C, Julian TR, et al.',
      'Carrat F, Vergu E, Ferguson NM, Lemaitre M, Cauchemez S, Leach S, Valleron AJ.':
      'Carrat F, Vergu E, Ferguson NM, Lemaitre M, Cauchemez S, Leach S, et al.',
      'Ogi-Gittins I, Hart WS, Song J, Nash RK, Polonsky J, Cori A, Hill EM, Thompson RN.':
      'Ogi-Gittins I, Hart WS, Song J, Nash RK, Polonsky J, Cori A, et al.',
      'Xie R, et al.':
      'Xie R, Adam DC, Hu S, Cowling BJ, Gascuel O, Zhukova A, et al.',
      'Obando-Pacheco P, et al.':
      'Obando-Pacheco P, Justicia-Grande AJ, Rivero-Calle I, Rodr\u00edguez-Tenreiro C, Sly P, Ramilo O, et al.',
      'Yang P, et al.':
      'Yang P, Duan W, Lv M, Shi W, Peng X, Wang X, et al.',
      'Kharazmi E, Cai M, Zheng X, et al.':
      'Kharazmi E, Cai M, Zheng X, Zhang Z, Lin G, Karniadakis GE.',
      'Mossong J, Hens N, Jit M, et al.':
      'Mossong J, Hens N, Jit M, Beutels P, Auranen K, Mikolajczyk R, et al.',
    }
    fixed = []
    for p in P():
        s = ptext(p)
        for old, new in REFFIX.items():
            if old in s:
                ts = [t for t in p.iter(q('t')) if t.text]
                single = [t for t in ts if old in t.text]
                if single:                      # contained in one run: surgical
                    single[0].text = single[0].text.replace(old, new)
                    single[0].set('{%s}space' % XML, 'preserve')
                    how = 'in-run'
                else:                           # spans runs: collapse, note it
                    joined = ''.join(t.text for t in ts).replace(old, new)
                    for t in ts[1:]: t.text = ''
                    ts[0].text = joined
                    ts[0].set('{%s}space' % XML, 'preserve')
                    how = 'COLLAPSED %d runs' % len(ts)
                fixed.append(f"{new.split(',')[0]} [{how}]"); break

    # --------------------------- 7. Table 1 directly after its first citation
    kids = list(body)
    cap = next(e for e in kids if ptext(e).strip().startswith('Table 1.'))
    blk = [cap]
    n = cap.getnext()
    while n is not None and etree.QName(n).localname in ('tbl', 'p'):
        blk.append(n)
        if etree.QName(n).localname == 'p' and not ptext(n).strip().startswith('†'):
            break
        n = n.getnext()
    if etree.QName(blk[-1]).localname == 'p' and not ptext(blk[-1]).strip().startswith('†'):
        blk.pop()
    cite1 = find_para('(Table 1)')
    anchor = cite1
    for e in blk:
        body.remove(e); anchor.addnext(e); anchor = e

    # ------------------- 8. Methods to PLOS position; tracked in the edit copy
    heads = [p for p in P() if (p.find('w:pPr/w:pStyle', NS) is not None
             and p.find('w:pPr/w:pStyle', NS).get(q('val')) == 'Heading1')]
    m_start = find_para('Materials and Methods', heads)
    stop = next(h for h in heads if ptext(h).strip() == 'Results')
    meth = []; p = m_start
    while p is not stop:
        meth.append(p); p = p.getnext()
    # the ethics statement PLOS requires lives at the end of the Methods
    eth_head = para([('Ethics statement', False)], style='Heading2')
    meth_tail = [eth_head, slot(1)]
    refs_head = find_para('References', heads)

    def mark(p, kind):
        ppr = p.find(q('pPr'))
        if ppr is None: ppr = etree.Element(q('pPr')); p.insert(0, ppr)
        rpr = ppr.find(q('rPr')) if ppr.find(q('rPr')) is not None else etree.SubElement(ppr, q('rPr'))
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
    def strip_comments_in(p):
        for e in list(p.iter()):
            if not isinstance(e.tag, str) or e.getparent() is None: continue
            ln = etree.QName(e).localname
            if ln in ('commentRangeStart','commentRangeEnd'):
                e.getparent().remove(e)
            elif ln == 'commentReference':
                r = e.getparent()
                if r.getparent() is not None: r.getparent().remove(r)
        return p

    anchor = refs_head.getprevious()
    if mode == 'edit':
        for s in meth + meth_tail:
            cp = mark(copy.deepcopy(s), 'ins'); anchor.addnext(cp); anchor = cp
        for s in meth: mark(strip_comments_in(s), 'del')
        for s in meth_tail[::-1]: pass
    else:
        for s in meth:
            body.remove(s); anchor.addnext(s); anchor = s
        for s in meth_tail:
            anchor.addnext(s); anchor = s

    # --------------------------------------------------------- 9. back matter
    SI = [('S1 Table', 'Season definitions, peak positivity and wave classification for all 18 pathogen-seasons.'),
          ('S2 Table', 'Pre-onset amplification by surveillance channel.'),
          ('S3 Table', 'Data dictionary for the 31 CHP Flu Express variables, January 2014 to March 2026, 638 weeks.'),
          ('S4 Table', 'Sensitivity of EpiEstim onset detection to the serial interval and estimation window.'),
          ('S5 Fig',   'Weekly discretisation of the serial-interval distributions.')]
    pre = [para([('Acknowledgments', False)], style='Heading1'), slot(2),
           para([('Data Availability Statement', False)], style='Heading1'),
           para([('All data analysed in this study are from public sources. The Centre for Health '
                  'Protection Flu Express and respiratory surveillance series are publicly '
                  'available from the CHP website. Analysis code and the derived data files that '
                  'reproduce every reported value are available at '
                  'https://github.com/thomasshuaiyuan/pinn-early-warning, archived at ', False),
                 ('[VD-3 — CODE ARCHIVE DOI]', True), ('.', False)])]
    for p in pre: refs_head.addprevious(p)

    post = [para([('Supporting information', False)], style='Heading1')]
    for lab, title in SI:
        post.append(para([(lab + '. ', True), (title, False)]))
    if mode == 'edit':
        post += [para([('Retained from the pre-submission draft, not part of the PLOS '
                        'submission', False)], style='Heading1'),
                 para([('PLOS Computational Biology has no Highlights section. These four lines '
                        'are VD’s inserted prose from v9, held here verbatim rather than '
                        'deleted. Two of them are the lines whose supporting evidence is still '
                        'open. This whole block is dropped from the submission-ready file.',
                        False)])] + hl
    last = body[-1]
    anchor = body[-2] if etree.QName(last).localname == 'sectPr' else last
    for p in post:
        anchor.addnext(p); anchor = p

    # ------------------------- 10. spacing, line numbers, short title, cleanup
    for p in root.iter(q('p')):
        ppr = p.find(q('pPr'))
        if ppr is None: ppr = etree.Element(q('pPr')); p.insert(0, ppr)
        for x in ppr.findall(q('spacing')): ppr.remove(x)
        sp = etree.Element(q('spacing')); sp.set(q('line'), '480'); sp.set(q('lineRule'), 'auto')
        at = 0
        for i, ch in enumerate(ppr):
            if etree.QName(ch).localname in ('pStyle', 'numPr'): at = i + 1
        ppr.insert(at, sp)
    for sect in root.iter(q('sectPr')):
        for x in sect.findall(q('lnNumType')): sect.remove(x)
        ln = etree.Element(q('lnNumType'))
        ln.set(q('countBy'), '1'); ln.set(q('restart'), 'continuous'); ln.set(q('distance'), '360')
        sect.append(ln)
    P()[0].addnext(para([('Short title: ', True), (SHORT_TITLE, False)]))

    ncomments = len(list(root.iter(q('commentRangeStart'))))
    if mode == 'submit':
        for e in list(root.iter()):
            if not isinstance(e.tag, str) or e.getparent() is None: continue
            ln = etree.QName(e).localname
            if ln in ('commentRangeStart','commentRangeEnd'):
                e.getparent().remove(e)
            elif ln == 'commentReference':
                r = e.getparent()
                if r.getparent() is not None: r.getparent().remove(r)
        ncomments = 0

    tree.write(docpath, xml_declaration=True, encoding='UTF-8', standalone=True)
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        for name in order:
            if mode == 'submit' and name in ('word/comments.xml',): continue
            z.write(os.path.join(work, *name.split('/')), name)
    return out, docpath, len(meth), fixed, ncomments

for mode in ('edit', 'submit'):
    out, docpath, nmeth, fixed, ncom = build(mode)
    print(f'\n==== {mode.upper()}  ->  {os.path.basename(out)}')
    print(f'     Methods block {nmeth} paragraphs | references normalised: {", ".join(fixed)} | comments {ncom}')
    root = etree.parse(docpath).getroot()
    txt = [ptext(p) for p in root.iter(q('p'))]
    allt = '\n'.join(txt)
    h1 = [t.strip() for p, t in zip(root.iter(q('p')), txt)
          if p.find('w:pPr/w:pStyle', NS) is not None
          and p.find('w:pPr/w:pStyle', NS).get(q('val')) == 'Heading1' and t.strip()]
    print('     order:', ' > '.join(h1))
    body = root.find('w:body', NS); kids = list(body)
    i_cite = next(i for i,e in enumerate(kids) if '(Table 1)' in ptext(e))
    i_cap  = next(i for i,e in enumerate(kids) if ptext(e).strip().startswith('Table 1.'))
    check(i_cap == i_cite + 1, 'Table 1 sits directly after its first citation',
          f'cite {i_cite}, caption {i_cap}')
    check(h1.index('Materials and Methods') > h1.index('Discussion'), 'Methods after Discussion')
    check('Ethics statement' in allt, 'ethics statement slot present in Methods')
    check('Funding' not in h1, 'no Funding section in the manuscript (PLOS: system field only)')
    check(not re.search(r'Fig\.\s*\d', allt), 'no "Fig." citations remain')
    check(not re.search(r'Supplementary (Table|Fig)', allt), 'no "Supplementary Table/Fig"')
    check('Xie R, Adam DC, Hu S, Cowling BJ, Gascuel O, Zhukova A, et al.' in allt,
          'ref 13 expanded to six authors then et al.')
    check(not re.search(r'Valleron AJ\.', allt), 'ref 8 truncated to six authors')
    nslots = len(re.findall(r'\[VD-\d', allt))
    check(nslots == 3, 'three [VD-n] slots marked', str(nslots))
    marks = [e for e in root.iter() if isinstance(e.tag, str)
             and etree.QName(e).localname in ('ins','del')]
    if mode == 'edit':
        check(len(marks) > 0 and all(e.get(q('author')) == AUTHOR for e in marks),
              'Methods relocation left as a rejectable tracked change', f'{len(marks)} marks')
        check(len(list(root.iter(q('commentRangeStart')))) == 26, 'all 26 comments kept')
        check('not part of the PLOS submission' in allt, 'Highlights retained in a labelled block')
    else:
        check(len(marks) == 0, 'no tracked changes', f'{len(marks)} marks')
        check(len(list(root.iter(q('commentReference')))) == 0, 'no comments')
        check('not part of the PLOS submission' not in allt, 'Highlights block dropped')
    print('     paragraphs', len(txt))

print()
print('abbreviations used fewer than three times (PLOS allows non-standard ones only at 3+):')
root = etree.parse(docpath).getroot()
allt = '\n'.join(ptext(p) for p in root.iter(q('p')))
import collections
cnt = collections.Counter(re.findall(r'\b[A-Z]{2,6}\b', allt))
rare = {k: v for k, v in cnt.items() if v < 3}
print('   ', ', '.join(f'{k}({v})' for k, v in sorted(rare.items())) or 'none')
sys.exit(1 if fail else 0)
