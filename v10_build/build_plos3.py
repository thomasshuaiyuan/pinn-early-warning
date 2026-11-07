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
import kme_edits
import followup_edits

# Paths are derived from this file's own location, so the build runs wherever the
# repository is checked out: on the Mac, in the Linux VM that mounts it under ~/mnt,
# and in a cloud container that has neither.
BUILD = os.path.dirname(os.path.abspath(__file__))
REPO  = os.path.dirname(BUILD)
SRC   = os.path.join(BUILD, '2026-11-05_early-warning_v11.docx')
FIGS  = os.path.join(REPO, 'Claude outputs',
                     '2026-10-15_early-warning_v10_figures.docx')
# The default destination is the staging directory beside this script, never a synced
# folder. OneDrive Files-On-Demand turns a synced file into a placeholder and writing
# over one fails with 'Resource deadlock avoided', so delivery into OneDrive is a
# separate copy step, done deliberately and not as a side effect of building.
DEST  = os.environ.get('PLOS_DEST') or os.path.join(BUILD, '_stage_plos')


def preflight():
    """Fail with a readable message rather than a traceback from deep in the build."""
    bad = []
    for label, path in (('source manuscript', SRC), ('figures document', FIGS)):
        if not os.path.isfile(path):
            bad.append(f'  {label} not found: {path}')
    if bad:
        sys.stderr.write(
            'build_plos3.py: missing input.\n' + '\n'.join(bad) + '\n\n'
            f'Paths are taken relative to this script, at {BUILD}.\n'
            'Run it from inside the repository checkout, or copy the inputs beside it.\n')
        raise SystemExit(2)
    os.makedirs(DEST, exist_ok=True)
    if not os.access(DEST, os.W_OK):
        sys.stderr.write(f'build_plos3.py: destination is not writable: {DEST}\n')
        raise SystemExit(2)
AUTHOR, DATE = 'Thomas Yuan', '2026-11-05T12:00:00Z'
SHORT_TITLE = 'R(t) onset detection for influenza and RSV in Hong Kong'

# Affiliations as VD supplied them on 6 November 2026. v10 merged HKU SPH and
# HKU-Pasteur onto one numbered line with an ampersand, which Part I of the
# project instructions forbids; his two strings separate them, which renumbers
# Columbia to 3 and moves the author superscripts with it.
AFF1 = ('1 School of Public Health, LKS Faculty of Medicine, The University of Hong Kong, '
        'Hong Kong SAR, China.')
AFF2 = ('2 HKU-Pasteur Research Pole, School of Public Health, LKS Faculty of Medicine, '
        'The University of Hong Kong, Hong Kong SAR, China.')
AFF3 = ('3 Department of Epidemiology, Mailman School of Public Health, Columbia University, '
        'New York, NY, USA.')
AFF_OLD = 'The University of Hong Kong & HKU-Pasteur Research Pole'

# Two headed sections in the structure VD sent, with the three clauses of his
# template that describe a different paper left out: this study deposits no
# consensus genomes in GISAID, runs no BEAST, and contains no R code. "From the
# corresponding author upon reasonable request" is also dropped, because PLOS
# does not accept it as a default and forbids an author being the sole named
# point of contact (data-availability policy, read at source 6 November 2026).
DATA_AVAIL = (
    'All data analysed in this study are from public sources, and no sequence data and no '
    'individual-level records were generated or used. The weekly surveillance series '
    '(laboratory detections and percentage positive, sentinel and general outpatient '
    'influenza-like illness consultation rates, and age-stratified public-hospital admission '
    'rates) are published by the Centre for Health Protection of the Government of the Hong '
    'Kong Special Administrative Region and are available from its Flu Express and '
    'respiratory surveillance pages. The derived data files that reproduce every reported '
    'value, including flux_data.csv and the committed analysis outputs, are deposited with '
    'the analysis code in the archive named under Code availability.')
CODE_AVAIL = (
    'All code used to produce the results reported here, together with the derived data '
    'files, is available at https://github.com/thomasshuaiyuan/pinn-early-warning and '
    'archived at ')

AFFIL_NOTE = (
    '[Affiliations] Applied from the block you sent on 6 November. v10 had HKU SPH and '
    'HKU-Pasteur merged on one numbered line with an ampersand, which your two strings '
    'separate. Numbering is therefore 1 SPH, 2 HKU-Pasteur, 3 Columbia, and the superscripts '
    'move with it: Thomas 1,3 and yours 1,2. Two things only you can settle. You sent two '
    'affiliations and v10 carries three, so Columbia is kept rather than dropped; say if it '
    'should go. And Thomas is not listed on HKU-Pasteur, because whether he is affiliated '
    'there is yours to decide. Rejecting this change restores v10 exactly.')
AVAIL_NOTE = (
    '[Data and Code availability] Written to the two-heading structure you sent on '
    '6 November. Three clauses of that template describe a different paper and are not '
    'carried in. This study deposits no consensus genome sequences in GISAID; it has no '
    'BEAST XML or log files; and it contains no R scripts, the analysis being Python '
    'throughout, which the Methods already state. An EpiEstim benchmark written in R does '
    'exist in the HKU-influenza working directory, but the manuscript cites no R anywhere, '
    'the output file that script writes exists nowhere under the connected folders, and the '
    'reported values come from the committed Python outputs, so it is not load-bearing and '
    'is not in the cited repository. One further change is a journal rule rather than a '
    'preference: PLOS does not accept "available from the corresponding author upon '
    'reasonable request" as a default and states that it is not acceptable for an author to '
    'be the sole named individual responsible for data access; request-only access is for '
    'sensitive human data, and for code only where there is a legal or ethical restriction. '
    'Neither applies here, so the statement points at the repository and the archive. The '
    'archive DOI is the one thing still missing and it is mine to mint.')

SLOTS = {
 'VD-1': ('ETHICS STATEMENT', 'required by PLOS in Materials and Methods. A draft to accept or '
     'replace is in VD_INPUT_SHEET.md; name the determining body if an exemption was obtained.'),
 'VD-2': ('ACKNOWLEDGMENTS', 'contributors who do not meet authorship criteria, with their '
     'contribution. PLOS forbids funding sources here; funding is a submission-system field.'),
 'TY-1': ('CODE ARCHIVE DOI', 'PLOS requires a DOI-issuing archive; a GitHub URL alone does not '
     'satisfy the policy. Mint a Zenodo DOI from the tagged release and paste it here. D18.'),
}
# brackets appended to an existing sentence, never replacing any of it
INLINE = [
 ('TY-3', 'hk accessed 15 March 2026; January 2014\u2013March 2026; 638 weeks; 31 variables).',
  'provenance inconsistency: the last row of flux_data.csv is the week running 15 to 21 March '
  '2026, which cannot have been downloaded on 15 March. Reconcile the access date.'),
]

REC_AUTHOR = 'Thomas Yuan \u2014 recommendation'
# edits that answer a named comment are authored by whose comment they answer,
# so the Review pane filters to one reviewer at a time
FU_AUTH = {'KME': 'Thomas Yuan \u2014 answers KME',
           'VD':  'Thomas Yuan \u2014 answers VD'}
REC_DATE = '2026-11-06T09:00:00Z'

# Each entry becomes ONE tracked change plus ONE anchored comment, so Vijay
# clicks Accept or Reject in the Review pane and the reasoning is a hover away.
# Applied in the editing copy only: these are proposals, so the submission copy
# keeps the current text, which is the same as rejecting them.
RECOMMENDATIONS = [
 ('R1 title',
  'a retrospective cross-pathogen evaluation of influenza and RSV in Hong Kong',
  'a retrospective cross-pathogen evaluation of influenza and respiratory syncytial virus in '
  'Hong Kong',
  'PLOS asks that titles avoid specialist abbreviations. Spelling out RSV takes the title to '
  '189 of the permitted 200 characters, so it fits. Published papers in this journal do carry '
  'abbreviations in titles, so this is tidier rather than required \u2014 reject it freely. '
  'NOTE: your own comment above proposes a different title entirely, \u201cSignal amplitude '
  'and recovery-rate assumptions limit R(t)-based season onset detection for influenza and '
  'RSV\u201d, which Thomas replied he would like to adopt and left unchanged as a joint '
  'decision. If you adopt that one this change is moot \u2014 though it also contains RSV, so '
  'the same point would apply to it, and at 118 characters it has room to spell it out.'),
 ('R2a author summary',
  'This study tested whether methods that estimate the viral reproduction number can detect '
  'season onset earlier',
  'We tested whether methods that estimate the viral reproduction number can detect season '
  'onset earlier',
  'PLOS requires the Author Summary in the first person; this one is third person throughout. '
  'Three changes convert it, R2a to R2c, and none of them touches a number.'),
 ('R2b author summary',
  'Two methods were evaluated across',
  'We evaluated two methods across',
  'Second of the three first-person conversions.'),
 ('R2c author summary',
  'What mattered most, though, was that the physics-informed neural network\u2019s performance '
  'depended heavily on the assumed recovery rate.',
  'What mattered most was that the physics-informed neural network\u2019s performance depended '
  'heavily on the assumed recovery rate.',
  'Third of the three. The dropped "though" is the one word here that is style rather than '
  'voice; reject this one alone if you want it kept.'),
 ('R3 abstract threshold',
  'benchmarked against an analytical reconstruction of the Centre for Health Protection (CHP) '
  'influenza threshold (4.94% positivity)',
  'benchmarked against the published operational influenza threshold of the Centre for Health '
  'Protection (CHP) (4.94% positivity)',
  'This is the threshold question from the note of 30 October, which is still open. The '
  'source is now first-hand: the Department of Health press release of 2 July 2026, fetched '
  'and read on 7 November rather than quoted at second hand, states "Both indicators showed '
  'a significant increase from the previous week and have exceeded the baseline levels (4.94 '
  'per cent and 0.27 cases per 10 000 population respectively)". So 4.94% is CHP\u2019s '
  'published baseline level, which makes "an analytical reconstruction" wrong as a '
  'description of it. Kimberly Edwards found that release independently. The words are '
  'yours, so this stays a one-click recommendation rather than an edit. '
  'Department of Health release of 9 January 2025 states "Both indicators have exceeded the '
  'threshold of 4.94 per cent and 0.27 cases per 10 000 population respectively", and v10\u2019s '
  'own Table 1 note already reads "4.94%, operational" in unrevised base text. "An analytical '
  'reconstruction" is your wording, which is why this is a proposal and not an edit. Accepting '
  'it makes the Abstract consistent with the Methods, both table notes and the RSV section.'),
]

fail = []
def check(ok, label, detail=''):
    print(('  PASS  ' if ok else '  FAIL  ') + label + (('  -- ' + detail) if detail else ''))
    if not ok: fail.append(label)

def ptext(e): return ''.join(t.text or '' for t in e.iter(q('t')))

def build(mode):
    out = (f'{DEST}/2026-11-05_early-warning_PLOSCB_FOR-EDITING.docx' if mode == 'edit'
           else f'{DEST}/2026-11-05_early-warning_PLOSCB_SUBMISSION-READY.docx')
    # One scratch directory per mode, reused rather than timestamped: a timestamp left
    # a pair behind on every run, and the shell that drives this on a mounted folder
    # cannot delete them. Reuse is safe because extractall overwrites and the output
    # zip is written only from `order`, the source package's own member list, so a
    # stale file in here can never reach the .docx. The two modes keep separate
    # directories because the cross-copy check reads both at the end.
    work = os.path.join(BUILD, f'_plos2_{mode}')
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
        if ln in ('ins','del','moveTo','moveFrom') \
           and etree.QName(e.getparent()).localname == 'rPr':
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
        return para([(f'[{n} — {lab}] ', True), (guide, False)])

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
    CAPTION_ADDENDA = {3: (
        ' Channel abbreviations: GOPC/FMC ILI, influenza-like illness consultation rate at '
        'General Outpatient Clinics and Family Medicine Clinics (public sector); GP ILI, '
        'influenza-like illness consultation rate from private medical practitioners (sentinel '
        'general practitioners); A&E ILI, influenza-like illness rate at Accident and Emergency '
        'departments.')}
    for k, extra in CAPTION_ADDENDA.items():
        caps[k] = caps[k].rstrip() + extra
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
    meth_tail = [eth_head, slot('VD-1')]
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

    # --------------------------------- 8b. affiliations, from VD's own block
    # Applied in both copies and tracked in the editing copy, so Accept keeps
    # his wording and Reject restores v10's merged line exactly.
    p_auth = find_para('Thomas Yuan1,2')
    p_aff1 = find_para(AFF_OLD)
    p_aff3 = find_para('Mailman School of Public Health')

    def affil_para(src, text):
        np_ = copy.deepcopy(src)
        rs = [r for r in np_ if etree.QName(r).localname == 'r']
        assert rs, 'affiliation paragraph has no runs'
        for r in rs[1:]: np_.remove(r)
        t = rs[0].find(q('t')); t.text = text
        t.set('{%s}space' % XML, 'preserve')
        return np_

    new_auth = copy.deepcopy(p_auth)
    sup = [r for r in new_auth if etree.QName(r).localname == 'r'
           and r.find('w:rPr/w:vertAlign', NS) is not None]
    assert len(sup) == 2, f'expected two superscript runs, found {len(sup)}'
    assert [r.find(q('t')).text for r in sup] == ['1,2', '1,*'], \
        'author superscripts are not what v10 had'
    sup[0].find(q('t')).text = '1,2,3'
    sup[1].find(q('t')).text = '1,2,*'

    new_blk = [new_auth, affil_para(p_aff1, AFF1), affil_para(p_aff1, AFF2),
               affil_para(p_aff3, AFF3)]
    a_fm = p_aff3
    for np_ in new_blk:
        a_fm.addnext(np_); a_fm = np_
    if mode == 'edit':
        for np_ in new_blk: mark(np_, 'ins')
        for op in (p_auth, p_aff1, p_aff3): mark(strip_comments_in(op), 'del')
    else:
        for op in (p_auth, p_aff1, p_aff3): body.remove(op)
    print('     affiliations: SPH and HKU-Pasteur separated, Columbia renumbered to 3')

    # --------------------------------------------------------- 9. back matter
    SI = [('S1 Table', 'Season definitions, peak positivity and wave classification for all 18 pathogen-seasons.'),
          ('S2 Table', 'Pre-onset amplification by surveillance channel.'),
          ('S3 Table', 'Data dictionary for the 31 CHP Flu Express variables, January 2014 to March 2026, 638 weeks.'),
          ('S4 Table', 'Sensitivity of EpiEstim onset detection to the serial interval and estimation window.'),
          ('S5 Fig',   'Weekly discretisation of the serial-interval distributions.')]
    pre = [para([('Acknowledgments', False)], style='Heading1'), slot('VD-2'),
           para([('Data availability', False)], style='Heading1'),
           para([(DATA_AVAIL, False)]),
           para([('Code availability', False)], style='Heading1'),
           para([(CODE_AVAIL, False),
                 ('[TY-1 — CODE ARCHIVE DOI]', True), ('.', False)])]
    for p in pre: refs_head.addprevious(p)

    post = [para([('Supporting information', False)], style='Heading1')]
    for lab, title in SI:
        post.append(para([(lab + '. ', True), (title, False)]))
    if mode == 'edit':
        post += ([para([('Open queries, not part of the PLOS submission', False)], style='Heading1'),
                 para([('[VD-3 \u2014 HIGHLIGHTS, LOW-AMPLITUDE LINE] ', True),
                       ('Your line \u201cLow-amplitude laboratory signals degraded both estimators '
                        'in the same direction\u201d. The real-data signal-to-noise result does not '
                        'carry it: pooled median 16.7 against 10.2 at one-sided p = 0.166, within '
                        'influenza \u22120.06 at exact p = 0.89, within RSV +0.23 at exact p = 0.52, '
                        'and Fig 3 is titled accordingly. The simulation cannot carry it either, '
                        'because the rescale pins signal-to-noise across arms by construction. What '
                        'is solid is the between-pathogen contrast, 5 of 6 seasons at +35 days '
                        'against 4 of 10 at \u221218. Should the sentence rest on that contrast, with '
                        'amplitude named as the interpretation rather than the measurement?', False)]),
                 para([('[VD-4 \u2014 HIGHLIGHTS, ADMISSIONS LINE] ', True),
                       ('Your line \u201cAge-stratified admissions led positivity exactly on the '
                        'hardest, low-amplitude seasons\u201d. The committed differences are +21, 0, '
                        '+42, 0, +21, 0, 0, +63: four leads, four ties, none later \u2014 and the '
                        'leads include the second- and third-highest-amplitude seasons. The Abstract '
                        'already states the weaker version, selectively on low-amplitude and '
                        'multi-wave seasons rather than on average. Replace with that?', False)]),
                 para([('[VD-5 \u2014 THRESHOLD CONSISTENCY] ', True),
                       ('Outstanding from the note of 30 October. Proposal: 4.94% as CHP\u2019s '
                        'published operational baseline throughout, 6.47% and 5.70% as data-derived '
                        'sensitivity analyses in Methods, 1.87% always flagged as data-derived. That '
                        'means changing \u201can analytical reconstruction\u201d in the Abstract, '
                        'which is your wording, so it is not touched without your word.', False)]),
                 para([('[TY-6 \u2014 FIGURE FILES] ', True),
                       ('PLOS states a figure file must not contain the figure title or caption. '
                        'Fig 2 to Fig 4 embed titles that duplicate caption material; Fig 1 has '
                        'three unlabelled panels, Fig 3 has two, and S5 Fig\u2019s a and b panels '
                        'are not described in its caption. Fixing this means rerunning the figure '
                        'scripts, which changes what the figures look like. Figure formatting is '
                        'waived until a provisional editorial accept decision.', False)]),
                 para([('[EDITS THAT ANSWER A COMMENT] ', True),
                       ('Every edit below exists because one of you asked for it. They are '
                        'tracked changes authored "Thomas Yuan \u2014 answers KME" or '
                        '"Thomas Yuan \u2014 answers VD", so the Review pane filters to one '
                        'reviewer at a time, and each carries its source and its evidence '
                        'here. None of them changes a number.', False)])]
                + [para([(f'[{e["id"]}] ', True),
                         ('Source: ' + e['source'] + '  Evidence: ' + e['evidence'], False)])
                    for e in followup_edits.EDITS]
                + [
                 para([('[KME \u2014 NUMBER STYLE IN THE ABSTRACT] ', True),
                       ('Her convention is to spell out numbers under ten in prose, and she '
                        'applied it to the first half of the Abstract\u2019s results sentence: '
                        '"five of six seasons", "four of ten seasons". The second half is yours '
                        'and still reads "5 of 6 seasons" and "all 6 seasons", because I do not '
                        'change your wording without asking. The paragraph is now inconsistent '
                        'with itself. Either her convention runs through the whole sentence or it '
                        'comes out of the first half; one word from you settles it.', False)]),
                 para([('[KME \u2014 WITHHELD ON YOUR WORDING] ', True),
                       ('Kimberly Edwards reviewed the submission copy on 6 November, before '
                        'this round, so she had not seen your comments. Her edits are in the '
                        'document as tracked changes under her name. In '
                        + str(len(kme_edits.HELD)) + ' places an edit of hers would have '
                        'deleted words you wrote, so it was not applied and your wording '
                        'stands. Her version of each is below, to adopt or ignore.', False)])]
                 + [para([(f'[KME p{h["para"]}] ', True),
                          (h['kind'] + '. Her version: ' + h['hers'][:600], False)])
                    for h in kme_edits.HELD]
                 + [para([('Retained from the pre-submission draft, not part of the PLOS '
                        'submission', False)], style='Heading1'),
                 para([('PLOS Computational Biology has no Highlights section. These four lines '
                        'are VD’s inserted prose from v9, held here verbatim rather than '
                        'deleted. Two of them are the lines whose supporting evidence is still '
                        'open. This whole block is dropped from the submission-ready file.',
                        False)])] + hl)
    last = body[-1]
    anchor = body[-2] if etree.QName(last).localname == 'sectPr' else last
    for p in post:
        anchor.addnext(p); anchor = p

    # ---- 9b. remediation of defects found by the independent pass, 5 Nov ----
    # F4a: the editorial marker
    for t in root.iter(q('t')):
        if t.text and '<VJ stopped here>' in t.text:
            t.text = t.text.replace(' <VJ stopped here>', '').replace('<VJ stopped here>', '')
    # F4b: the ethics claim was stated twice in one paragraph, once with a
    # bracketed query. Keep one sentence; the confirmation lives in [VD-1].
    for p in P():
        s0 = ptext(p)
        if 'no ethics approval was required' in s0 and 'no ethics approval was considered necessary' in s0:
            ts = [t for t in p.iter(q('t')) if t.text]
            j = ''.join(t.text for t in ts)
            j = j.replace(' [to be confirmed with institutional review]', '')
            j = j.replace(' Because all inputs are publicly available in aggregate form, no '
                          'ethics approval was considered necessary; a formal exemption '
                          'determination is being sought and the determining body will be named.', '')
            for t in ts[1:]: t.text = ''
            ts[0].text = j; ts[0].set('{%s}space' % XML, 'preserve')
    # F4c: the bracketed block holding an ethics stub, a funding stub and an
    # author-contributions stub. Funding and contributions are system fields at
    # PLOS and must not be in the manuscript; ethics is covered above.
    for p in list(P()):
        s0 = ptext(p).strip()
        if s0.startswith('[Ethics statement:') and 'Funding statement to be added' in s0:
            body.remove(p)
    def replace_across_runs(old, new):
        """Replace `old` with `new` even when it is split across w:t runs."""
        for p in P():
            ts = [t for t in p.iter(q('t')) if t.text]
            if not ts: continue
            j = ''.join(t.text for t in ts)
            if old not in j: continue
            j = j.replace(old, new)
            for t in ts[1:]: t.text = ''
            ts[0].text = j; ts[0].set('{%s}space' % XML, 'preserve')
            return True
        return False

    # TY-2 discharged: five-week source verification completed 5 November
    OLD_PENDING = ('Five randomly selected weeks were identified for manual validation against '
                   'published CHP figures (2015-W21, 2015-W35, 2019-W44, 2019-W52, 2022-W18); '
                   'manual verification against the CHP website is pending.')
    NEW_DONE = ('Five randomly selected weeks were manually validated against the published CHP '
                'tables (2015-W21, 2015-W35, 2019-W44, 2019-W52, 2022-W18). All five matched the '
                'scraped series exactly on specimens tested and on respiratory syncytial virus '
                'detections and percentage positive; the verification record, with the source '
                'page for each week, is rsv_source_verification_2026-11-05.md in the repository.')
    for p in P():
        ts = [t for t in p.iter(q('t')) if t.text]
        j = ''.join(t.text for t in ts)
        if OLD_PENDING in j:
            j = j.replace(OLD_PENDING, NEW_DONE)
            for t in ts[1:]: t.text = ''
            ts[0].text = j; ts[0].set('{%s}space' % XML, 'preserve')
            print('     TY-2 discharged: pending sentence replaced with the verified statement')
            break

    # TY-5: four abbreviations used once each; PLOS allows non-standard ones at 3+
    ABBREV = [('(IQR: +30 to +46 days)', '(interquartile range +30 to +46 days)'),
              ('27% for GP ILI consultation rates', '27% for general practitioner '
               'influenza-like illness consultation rates'),
              ('no GPU acceleration', 'no graphics-processing-unit acceleration'),
              ('during COVID NPIs', 'during COVID-19 non-pharmaceutical interventions')]
    nab = sum(1 for a, b in ABBREV if replace_across_runs(a, b))
    print(f'     TY-5: {nab} of {len(ABBREV)} single-use abbreviations spelled out')

    # TY-4: the date range, leaving VD's "analytical reconstruction" untouched
    if replace_across_runs('seasons between 2014 and 2025',
            'seasons labelled 2014/15 to 2024/25, drawn from surveillance records spanning '
            'January 2014 to March 2026'):
        print('     TY-4: abstract date range made explicit')

    # 'SI' is used four times and undefined at its first use, which is now in
    # Results because the Methods moved behind it. Mechanical expansion only.
    if replace_across_runs('with correct SI', 'with the correct serial interval') and \
       replace_across_runs('with wrong SI', 'with a misspecified serial interval'):
        print('     TY: serial interval spelled out at its first use in Results')

    # Rephrasing is not done here. The proposed wording goes in as a bracketed
    # recommendation against the sentence it would change, for VD to accept.
    def append_bracket(contains, key, lab, body_text):
        for p in P():
            ts = [t for t in p.iter(q('t')) if t.text]
            if not ts or contains not in ''.join(t.text for t in ts): continue
            ts[-1].text = (ts[-1].text or '') + f' [{key} \u2014 {lab}: {body_text}]'
            ts[-1].set('{%s}space' % XML, 'preserve')
            return True
        return False

    # a short Results preamble: burn-in, multi-wave and the onset rules were all
    # used before definition once the Methods moved to the end
    PREAMBLE = ('Onset is reported throughout as the first week in which estimated R(t) exceeds '
        '1.0. For EpiEstim this is the first week with posterior mean R(t) above 1.0; for the '
        'SEIR-PINN it is the first crossing from below, sustained over at least three consecutive '
        'evaluation points, after a four-week burn-in. Lead time is the interval in days between '
        'that date and the comparator threshold crossing, positive when the estimator is earlier. '
        'Seasons are described as multi-wave when automatic peak detection finds more than one '
        'distinct positivity peak, which applies to 2017/18 and 2023/24. The 2016/17 season is '
        'also described as multi-wave, on the basis of its age-stratified admissions rather than '
        'its positivity, which has a single peak; S1 Table records the basis for each season. '
        'Those classifications were assigned after the data were examined, as noted below. '
        'Materials and Methods gives the full specifications.')
    rh = next(p for p in P() if ptext(p).strip() == 'Results'
              and p.find('w:pPr/w:pStyle', NS) is not None)
    rh.addnext(para([(PREAMBLE, False)]))
    print('     Results preamble added: onset rules, lead time, burn-in, multi-wave')

    # F8: SEIR is used five times and never expanded
    done = False
    for t in root.iter(q('t')):
        if not done and t.text and 'SEIR' in t.text:
            t.text = t.text.replace('SEIR', 'susceptible-exposed-infectious-recovered (SEIR)', 1)
            done = True
    # date framing: the title's range is the record, the abstract's is the seasons
    for t in root.iter(q('t')):
        if t.text and '2014' in t.text:
            t.text = t.text.replace('eighteen pathogen-seasons spanning 2014-2025',
                                    'eighteen pathogen-seasons labelled 2014-2025')
    # brackets on the three sentences that state their own open question
    placed = []
    for key, anchor, guide in INLINE:
        lab = {'TY-3': 'PROVENANCE DATE'}[key]
        hit = None
        for p in P():
            ts = [t for t in p.iter(q('t')) if t.text and anchor in t.text]
            if ts: hit = (p, ts[0]); break
        if hit is None:
            for p in P():
                if anchor in ptext(p):
                    ts = [t for t in p.iter(q('t')) if t.text]
                    hit = (p, ts[-1]); break
        if hit is None:
            print(f'     WARNING: anchor for {key} not found'); continue
        p, t = hit
        t.text = t.text.replace(anchor, anchor + f' [{key} \u2014 {lab}: {guide}]') \
                 if anchor in t.text else t.text + f' [{key} \u2014 {lab}: {guide}]'
        t.set('{%s}space' % XML, 'preserve')
        placed.append(key)
    print('     inline brackets placed:', ', '.join(placed))

    # F6: runs of empty body paragraphs left at the relocation boundary
    def anytext(e):
        return ''.join((t.text or '') for t in list(e.iter(q('t'))) + list(e.iter(q('delText'))))
    kids = [e for e in body if etree.QName(e).localname == 'p']
    runlen = 0; killed = 0
    for e in list(kids):
        if not anytext(e).strip() and len(e.findall(q('tbl'))) == 0:
            runlen += 1
            if runlen > 1:
                body.remove(e); killed += 1
        else:
            runlen = 0
    # F5: figures must be cited in ascending order. First citations run
    # 1, 4, 2, 3, so renumber as a permutation: 4->2, 2->3, 3->4.
    PERM = {1: 1, 4: 2, 2: 3, 3: 4}
    for t in root.iter(q('t')):
        if t.text and 'Fig ' in t.text:
            t.text = re.sub(r'\bFig (\d)\b',
                            lambda m: 'Fig \u00a7%d' % PERM[int(m.group(1))]
                            if int(m.group(1)) in PERM else m.group(0), t.text)
    for t in root.iter(q('t')):
        if t.text: t.text = t.text.replace('Fig \u00a7', 'Fig ')
    print(f'     remediation: {killed} empty paragraphs removed, figures renumbered 4->2, 2->3, 3->4')

    # underlining inherited as editing markup in the abstract
    heads_now = [p for p in P() if (p.find('w:pPr/w:pStyle', NS) is not None
                 and p.find('w:pPr/w:pStyle', NS).get(q('val')) == 'Heading1')]
    try:
        a0 = next(p for p in heads_now if ptext(p).strip() == 'Abstract')
        a1 = next(p for p in heads_now if ptext(p).strip() == 'Author Summary')
        n = a0.getnext(); nu = 0
        while n is not None and n is not a1:
            for rpr in n.iter(q('rPr')):
                for u in rpr.findall(q('u')): rpr.remove(u); nu += 1
            n = n.getnext()
        print(f'     removed {nu} underline runs from the abstract')
    except StopIteration:
        pass

    # ------------------- 9b2. Kimberly Edwards's review of 6 November 2026 -----
    # Applied in both copies. In the editing copy each hunk is a separate
    # tracked change authored "Kimberly Edwards", so Vijay accepts or rejects
    # them one at a time and can filter the Review pane to her name alone.
    # Where a hunk of hers deleted words Vijay wrote it is not here: his
    # wording stands and her version is listed for him under Open queries.
    import difflib
    kme_ed = None
    if mode == 'edit':
        from ooxml_track import Editor
        kme_ed = Editor(root, 'Kimberly Edwards', '2026-11-06T18:13:00Z', first_id=40000)

    def live_paras():
        """paragraphs that survive acceptance: skip the struck-out Methods copy"""
        out = []
        for p in root.iter(q('p')):
            if p.find('w:pPr/w:rPr/w:del', NS) is not None: continue
            if not [t for t in p.iter(q('t')) if t.text]: continue
            out.append(p)
        return out

    def hunks(old, new):
        tok = lambda x: re.findall(r'\s+|[^\s]+', x)
        A_, B_ = tok(old), tok(new)
        sm = difflib.SequenceMatcher(None, A_, B_, autojunk=False)
        out = []
        for tag, a1, a2, b1, b2 in sm.get_opcodes():
            if tag == 'equal': continue
            la, ra = a1, a2
            for _ in range(60):
                frag = ''.join(A_[la:ra])
                if frag.strip() and old.count(frag) == 1: break
                if la > 0: la -= 1
                elif ra < len(A_): ra += 1
                else: break
            out.append((''.join(A_[la:ra]),
                        ''.join(A_[la:a1]) + ''.join(B_[b1:b2]) + ''.join(A_[a2:ra])))
        return out

    kme_done = kme_miss = kme_hunks = kme_whole = 0
    def si_fig_name():
        for p in root.iter(q('p')):
            t = ptext(p).strip()
            if t.startswith('S5 Fig.') or t.startswith('S1 Fig.'): return t.split('.')[0]
        return 'S5 Fig'
    for old, new in kme_edits.PARAS:
        pool = live_paras()
        exact = [p for p in pool if ptext(p).strip() == old.strip()]
        if exact:
            # a table header or row label is the same cell in both tables, so an
            # exact whole-paragraph match applies to every one of them
            targets = exact
            tgt = exact[0]
        elif len(old.strip()) < 40:
            kme_miss += 1
            print(f'     WARNING: KME short anchor has no whole-paragraph match: {old!r}')
            continue
        else:
            hits = [p for p in pool if old in ptext(p)]
            if len(hits) != 1:
                kme_miss += 1
                print(f'     WARNING: KME anchor hits {len(hits)} paragraphs: {old[:50]!r}')
                continue
            tgt = hits[0]; targets = [tgt]
        if mode == 'submit':
            for tg in targets:
                ts = [t for t in tg.iter(q('t')) if t.text]
                j = ''.join(t.text for t in ts).replace(old, new)
                for t in ts[1:]: t.text = ''
                ts[0].text = j; ts[0].set('{%s}space' % XML, 'preserve')
            kme_done += 1
        else:
            hs = hunks(old, new)
            # Simulate the hunk sequence on the string before touching the XML:
            # applying one hunk can duplicate another's anchor, so uniqueness is
            # checked at the moment each would apply, and the result must equal
            # the target exactly. If it does not, the paragraph is replaced whole.
            tgt_list = targets
            sim, ok = old, True
            for h_old, h_new in reversed(hs):
                if sim.count(h_old) != 1: ok = False; break
                sim = sim.replace(h_old, h_new, 1)
            for tg in tgt_list:
                if ok and sim == new:
                    n = 0
                    for h_old, h_new in reversed(hs):
                        kme_ed.replace(tg, h_old, h_new); n += 1
                    kme_hunks += n
                else:
                    kme_ed.replace(tg, old, new); kme_hunks += 1; kme_whole += 1
            kme_done += 1
    canon = si_fig_name()
    other = 'S1 Fig' if canon == 'S5 Fig' else 'S5 Fig'
    nfix = 0
    for p in root.iter(q('p')):
        if ptext(p).strip().startswith(other + '.'): continue
        for t in [t for t in p.iter(q('t')) if t.text and other in t.text]:
            t.text = t.text.replace(other, canon); nfix += 1
    if nfix:
        print(f'     supporting figure cited as {canon} throughout '
              f'({nfix} citation(s) normalised from {other})')
    # ------- 9b3. edits that answer a named comment, each traceable to its source ----
    fu_ed = {}
    if mode == 'edit':
        from ooxml_track import Editor
        for k, name in FU_AUTH.items():
            fu_ed[k] = Editor(root, name, '2026-11-07T10:00:00Z',
                              first_id=60000 if k == 'KME' else 70000)
    fu_done, fu_miss = 0, []
    for e in followup_edits.EDITS:
        hits = [p for p in live_paras() if e['old'] in ptext(p)]
        if len(hits) != 1:
            fu_miss.append((e['id'], len(hits))); continue
        tgt = hits[0]
        if mode == 'submit':
            ts = [t for t in tgt.iter(q('t')) if t.text]
            j = ''.join(t.text for t in ts).replace(e['old'], e['new'])
            for t in ts[1:]: t.text = ''
            ts[0].text = j; ts[0].set('{%s}space' % XML, 'preserve')
        else:
            fu_ed[e['who']].replace(tgt, e['old'], e['new'])
        fu_done += 1
    print(f"     follow-up edits answering a comment: {fu_done} of "
          f"{len(followup_edits.EDITS)}"
          + (f"  NOT APPLIED: {fu_miss}" if fu_miss else ''))
    assert not fu_miss, f'follow-up edits did not anchor: {fu_miss}'

    print(f"     Kimberly Edwards's review: {kme_done} of {len(kme_edits.PARAS)} paragraphs"
          + (f', {kme_hunks} tracked hunks'
             + (f' ({kme_whole} as one hunk, anchors not separable)' if kme_whole else '')
             if mode == 'edit' else '')
          + (f', {kme_miss} anchors not found' if kme_miss else ''))

    # ---- 9c. recommendations as one-click tracked changes, editing copy only ----
    if mode == 'edit':
        from ooxml_track import Editor
        red = Editor(root, REC_AUTHOR, REC_DATE, first_id=20000)
        W14 = 'http://schemas.microsoft.com/office/word/2010/wordml'
        W15 = 'http://schemas.microsoft.com/office/word/2012/wordml'
        W16CID = 'http://schemas.microsoft.com/office/word/2016/wordml/cid'
        W16CEX = 'http://schemas.microsoft.com/office/word/2018/wordml/cex'
        cpath = os.path.join(work, 'word', 'comments.xml')
        ctree = etree.parse(cpath); croot = ctree.getroot()
        used = {int(c.get(q('id'))) for c in croot.iter(q('comment'))}
        cid = max(used) + 100
        # A comment that is absent from commentsExtended / commentsIds /
        # commentsExtensible is a 32-against-26 mismatch: Word tolerates it, but
        # it loses the comment's threading and resolved state, so each new
        # comment is registered in all three, mirroring an existing entry.
        extp = os.path.join(work, 'word', 'commentsExtended.xml')
        idsp = os.path.join(work, 'word', 'commentsIds.xml')
        cexp = os.path.join(work, 'word', 'commentsExtensible.xml')
        ext_t = etree.parse(extp); ids_t = etree.parse(idsp); cex_t = etree.parse(cexp)
        taken = {e.get('{%s}paraId' % W15) for e in ext_t.getroot()}
        taken |= {e.get('{%s}durableId' % W16CID) for e in ids_t.getroot()}
        hexseq = [0x5A000000]
        def new_hex():
            while True:
                hexseq[0] += 0x1111
                h = '%08X' % hexseq[0]
                if h not in taken:
                    taken.add(h); return h

        def register(comment_el):
            pid, did = new_hex(), new_hex()
            for p in comment_el.iter(q('p')):
                p.set('{%s}paraId' % W14, pid)
                p.set('{%s}textId' % W14, '77777777')
                break
            e = etree.SubElement(ext_t.getroot(), '{%s}commentEx' % W15)
            e.set('{%s}paraId' % W15, pid); e.set('{%s}done' % W15, '0')
            e2 = etree.SubElement(ids_t.getroot(), '{%s}commentId' % W16CID)
            e2.set('{%s}paraId' % W16CID, pid); e2.set('{%s}durableId' % W16CID, did)
            e3 = etree.SubElement(cex_t.getroot(), '{%s}commentExtensible' % W16CEX)
            e3.set('{%s}durableId' % W16CEX, did)
            e3.set('{%s}dateUtc' % W16CEX, REC_DATE)
        applied = []
        for key, old, new, why in RECOMMENDATIONS:
            target = None
            for p in P():
                if old in ptext(p):
                    target = p; break
            if target is None:
                print(f'     WARNING: {key} anchor not found, skipped'); continue
            try:
                first, last = red.replace(target, old, new)
            except Exception as exc:
                print(f'     WARNING: {key} could not be applied: {exc}'); continue
            cid += 1
            red.add_comment_marks(target, first, last, cid)
            c = etree.SubElement(croot, q('comment'))
            c.set(q('id'), str(cid)); c.set(q('author'), REC_AUTHOR)
            c.set(q('date'), REC_DATE); c.set(q('initials'), 'TY-rec')
            cp = etree.SubElement(c, q('p')); cr = etree.SubElement(cp, q('r'))
            ct = etree.SubElement(cr, q('t')); ct.text = f'[{key}] {why}'
            ct.set('{%s}space' % XML, 'preserve')
            register(c)
            applied.append(key)
        # questions get a comment and no tracked change, because there is no
        # single correct replacement to accept
        QUESTIONS = [
         ('eight influenza and ten RSV peaks',
          '[Q1 season count, now answered by KME] This read "16 influenza and RSV seasons", '
          'against the title, '
          'abstract and Results work from eighteen. Sixteen reconciles as the six influenza '
          'seasons of the primary EpiEstim evaluation plus ten RSV; eighteen is eight plus ten. '
          'Kimberly Edwards independently flagged the same inconsistency and resolved it to '
          'eight plus ten, which is adopted here. Two things are left, and the first may be a '
          'defect. "Two methods were evaluated across eight influenza and ten RSV peaks" now '
          'overstates the primary evaluation: Tables 1 and 2 both carry six influenza seasons, '
          'Results says EpiEstim detected onset in all six, and PINN was not run on RSV at '
          'all. Eight is the number of influenza seasons in the dataset and in the admissions '
          'and signal-to-noise analyses, not the number the two estimators were evaluated on. '
          'Six plus ten is true of the primary evaluation; eight plus ten is true of the '
          'study. Pick the one the sentence means. Second, she wrote "peaks" where the rest of '
          'the manuscript says pathogen-seasons, and one word should govern throughout.'),
        ]
        for anchor, why in QUESTIONS:
            tgt = next((p for p in P() if anchor in ptext(p)), None)
            if tgt is None:
                print(f'     WARNING: question anchor {anchor!r} not found'); continue
            f2, l2 = red.span(tgt, anchor)
            cid += 1
            red.add_comment_marks(tgt, f2, l2, cid)
            c = etree.SubElement(croot, q('comment'))
            c.set(q('id'), str(cid)); c.set(q('author'), REC_AUTHOR)
            c.set(q('date'), REC_DATE); c.set(q('initials'), 'TY-rec')
            cp = etree.SubElement(c, q('p')); cr = etree.SubElement(cp, q('r'))
            ct = etree.SubElement(cr, q('t')); ct.text = why
            ct.set('{%s}space' % XML, 'preserve')
            register(c)
            applied.append('Q1 season count')
        # Notes on the two changes made from VD's own supplied text. These are
        # applied rather than proposed, so each carries a comment authored
        # "Thomas Yuan" and no recommendation authorship, and the comment says
        # what of his template was not carried in and why.
        # her 33 review comments, under her own name
        kme_c = kme_miss_c = 0
        kme_dropped = []
        for ctx_, an_, txt_ in kme_edits.COMMENTS:
            live = [p for p in root.iter(q('p'))
                    if p.find('w:pPr/w:rPr/w:del', NS) is None]
            pool = [p for p in live if ctx_ and ctx_ in re.sub(r'\s+', ' ', ptext(p))]
            if not pool and ctx_:
                head = ctx_[:40]
                pool = [p for p in live if head in re.sub(r'\s+', ' ', ptext(p))]
            if not pool and an_ and len(an_) > 12:
                pool = [p for p in live if an_ in re.sub(r'\s+', ' ', ptext(p))]
            tgt = pool[0] if pool else None
            if tgt is None:
                kme_miss_c += 1; kme_dropped.append((ctx_, an_, txt_)); continue
            pick = None
            vis = red.vis_text(tgt)
            cands = [an_, re.sub(r'\s+', ' ', ptext(tgt)).strip()[:45],
                     re.sub(r'\s+', ' ', ptext(tgt)).strip()[:30]]
            for cand in cands:
                if cand and vis.count(cand) == 1: pick = cand; break
            if pick is None:
                kme_miss_c += 1; kme_dropped.append((ctx_, an_, txt_)); continue
            try:
                f4, l4 = red.span(tgt, pick)
            except Exception:
                kme_miss_c += 1; kme_dropped.append((ctx_, an_, txt_)); continue
            cid += 1
            red.add_comment_marks(tgt, f4, l4, cid)
            c = etree.SubElement(croot, q('comment'))
            c.set(q('id'), str(cid)); c.set(q('author'), 'Kimberly Edwards')
            c.set(q('date'), '2026-11-06T18:13:00Z'); c.set(q('initials'), 'KME')
            cp = etree.SubElement(c, q('p')); cr = etree.SubElement(cp, q('r'))
            ct = etree.SubElement(cr, q('t')); ct.text = txt_
            ct.set('{%s}space' % XML, 'preserve')
            register(c)
            kme_c += 1
        print(f'     her comments carried: {kme_c} of {len(kme_edits.COMMENTS)}'
              + (f', {kme_miss_c} could not be anchored' if kme_miss_c else ''))
        for ctx_, an_, txt_ in kme_dropped:
            print(f'     NOT CARRIED, anchor gone: {txt_[:90]!r}')

        for anchor_, why_ in (('HKU-Pasteur Research Pole', AFFIL_NOTE),
                              ('Data availability', AVAIL_NOTE)):
            tgt = next((p for p in P() if anchor_ in ptext(p)), None)
            if tgt is None:
                print(f'     WARNING: note anchor {anchor_!r} not found'); continue
            f3, l3 = red.span(tgt, anchor_)
            cid += 1
            red.add_comment_marks(tgt, f3, l3, cid)
            c = etree.SubElement(croot, q('comment'))
            c.set(q('id'), str(cid)); c.set(q('author'), AUTHOR)
            c.set(q('date'), REC_DATE); c.set(q('initials'), 'TY')
            cp = etree.SubElement(c, q('p')); cr = etree.SubElement(cp, q('r'))
            ct = etree.SubElement(cr, q('t')); ct.text = why_
            ct.set('{%s}space' % XML, 'preserve')
            register(c)
            applied.append('note on ' + anchor_)
        ctree.write(cpath, xml_declaration=True, encoding='UTF-8', standalone=True)
        for t_, p_ in ((ext_t, extp), (ids_t, idsp), (cex_t, cexp)):
            t_.write(p_, xml_declaration=True, encoding='UTF-8', standalone=True)
        print(f'     recommendations as tracked changes: {len(applied)} \u2014 ' + '; '.join(applied))

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

    cpath = os.path.join(work, 'word', 'comments.xml')
    if os.path.exists(cpath):
        ctree = etree.parse(cpath); croot = ctree.getroot(); nfix = 0
        for t in croot.iter(q('t')):
            if not t.text: continue
            s0 = t.text
            t.text = re.sub(r'Figure (\d)',
                            lambda m: 'Figure \u00a7%d' % PERM[int(m.group(1))]
                            if int(m.group(1)) in PERM else m.group(0), t.text)
            t.text = t.text.replace('Figure \u00a7', 'Figure ')
            t.text = re.sub(r'Supplementary Table S(\d)', r'S\1 Table', t.text)
            if t.text != s0: nfix += 1
        if nfix:
            ctree.write(cpath, xml_declaration=True, encoding='UTF-8', standalone=True)
            print(f'     renumbered figures inside {nfix} comment run(s) (both authored Thomas Yuan)')

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
    if mode == 'submit':
        # F3: dropping comments.xml while leaving rId5-rId8 and the content-type
        # overrides behind produced a package python-docx refuses to open.
        drop = [n for n in order if 'comment' in n.lower()]
        order = [n for n in order if n not in drop]
        rp = os.path.join(work, 'word', '_rels', 'document.xml.rels')
        rr = etree.parse(rp); rroot = rr.getroot()
        gone = []
        for rel in list(rroot):
            tgt = (rel.get('Target') or '').lower()
            if 'comment' in tgt:
                gone.append(rel.get('Id')); rroot.remove(rel)
        rr.write(rp, xml_declaration=True, encoding='UTF-8', standalone=True)
        cp = os.path.join(work, '[Content_Types].xml')
        ct = etree.parse(cp); croot = ct.getroot()
        for ov in list(croot):
            if 'comment' in (ov.get('PartName') or ov.get('Extension') or '').lower():
                croot.remove(ov)
        ct.write(cp, xml_declaration=True, encoding='UTF-8', standalone=True)
        print(f'     stripped comment parts {drop} and relationships {gone}')
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        for name in order:
            z.write(os.path.join(work, *name.split('/')), name)
    return out, docpath, len(meth), fixed, ncomments

preflight()
print(f'build dir   {BUILD}')
print(f'source      {SRC}')
print(f'figures     {FIGS}')
print(f'destination {DEST}'
      f'{"  (PLOS_DEST)" if os.environ.get("PLOS_DEST") else "  (default staging)"}')

DOCPATHS = {}
for mode in ('edit', 'submit'):
    out, docpath, nmeth, fixed, ncom = build(mode)
    DOCPATHS[mode] = docpath
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
    check(AFF1 in allt and AFF2 in allt, 'both HKU affiliations present, unflattened')
    check(AFF_OLD not in allt, 'SPH and HKU-Pasteur no longer merged on one line')
    check('Thomas Yuan1,2,3, Vijaykrishna Dhanasekaran1,2,*' in allt,
          'author superscripts carry all three affiliations')
    check(AFF3 in allt, 'Columbia kept, renumbered to affiliation 3')
    for probe in ('five of six seasons', 'EpiEstim lead time (days)',
                  'Age-stratified hospital admission lead time (days)',
                  'eight influenza and ten RSV peaks',
                  'Multi = two age groups tied for the earliest onset', 'shifted by 0\u20137 days',
                  '1.87% positivity threshold', 'per-season values in S2 Table'):
        check(probe in allt, f'her edit applied: {probe[:38]!r}')
    check('ahead of the  percent' not in allt, 'the value she dropped is back')
    dbl = re.findall(r'\b(\w{4,})\1\b', allt)
    check(not dbl, 'no word doubled by a misplaced edit', ', '.join(sorted(set(dbl))[:6]))
    sinames = {m for m in re.findall(r'S\d Fig', allt)}
    check(len(sinames) <= 1, 'the supporting figure is cited under one name only',
          ', '.join(sorted(sinames)))
    check('SX' not in allt and 'Table/Data' not in allt,
          'no placeholder of hers left in the text')
    check(not re.search(r'Fig\.\s*\d', allt), 'her "Fig. 3a" normalised to PLOS style')
    check('Data availability' in h1 and 'Code availability' in h1,
          'availability split into the two headed sections VD asked for')
    check('Data Availability Statement' not in h1, 'the old single heading is gone')
    for bad in ('GISAID', 'BEAST', 'upon reasonable request', 'R scripts', 'consensus genome',
                'Supplementary Data', 'Dryad'):
        check(bad not in allt, f'template clause {bad!r} not carried into this paper')
    check(h1.index('Materials and Methods') > h1.index('Discussion'), 'Methods after Discussion')
    check('Ethics statement' in allt, 'ethics statement slot present in Methods')
    bad_funding = [m for m in ('Funding statement', 'This work was supported',
                               'was funded by', 'grant number')
                   if m.lower() in allt.lower()]
    check('Funding' not in h1 and not bad_funding,
          'no funding statement in the manuscript (PLOS: system field only)',
          str(bad_funding))
    check('VJ stopped here' not in allt, 'no editorial markers left')
    check('to be confirmed' not in allt, 'no "to be confirmed" placeholders left')
    check(allt.count('no ethics approval') <= 1, 'the ethics claim is stated once',
          f"{allt.count('no ethics approval')} times")
    check('susceptible-exposed-infectious-recovered (SEIR)' in allt, 'SEIR expanded at first use')
    check('is pending' not in allt, 'no pending-verification statement left')
    check('rsv_source_verification' in allt, 'the verification record is named in Methods')
    for ab in ('IQR:', 'GPU', 'COVID NPIs'):
        check(ab not in allt, f'single-use abbreviation {ab!r} spelled out')
    # 'GP ILI' is now permitted only where the legend defines it on the spot
    gp = [m.start() for m in re.finditer(r'GP ILI', allt)]
    undefined = [i for i in gp if not allt[i:i+40].startswith('GP ILI, influenza-like illness')]
    check(not undefined, 'every "GP ILI" occurrence carries its definition',
          f'{len(gp)} occurrence(s), {len(undefined)} undefined')
    check('seasons between 2014 and 2025' not in allt
          and 'labelled 2014/15 to 2024/25' in allt, 'abstract date range explicit')
    check('Onset is reported throughout as the first week' in allt, 'Results preamble present')
    check('on the basis of its age-stratified admissions rather than' in allt
          and 'which applies to 2017/18 and 2023/24' in allt,
          'multi-wave definition names both bases and both season sets')
    for ab in ('GOPC/FMC ILI, influenza-like illness', 'A&E ILI, influenza-like illness',
               'sentinel general practitioners'):
        check(ab in allt, f'Fig 4 legend defines {ab.split(",")[0]}')
    check('with the correct serial interval' in allt and 'with correct SI' not in allt,
          'serial interval spelled out at first use in Results')
    ri = [i for i, t in enumerate(txt) if t.strip() == 'Results']
    check(bool(ri) and 'Onset is reported throughout' in txt[ri[0]+1],
          'the preamble is the first paragraph of Results')
    runs = 0; worst = 0
    bk = [e for e in root.find('w:body', NS) if etree.QName(e).localname == 'p']
    def _any(e):
        return ''.join((t.text or '') for t in list(e.iter(q('t'))) + list(e.iter(q('delText'))))
    for e in bk:
        if not _any(e).strip(): runs += 1; worst = max(worst, runs)
        else: runs = 0
    check(worst <= 1, 'no runs of empty paragraphs', f'longest run {worst}')
    cites = []
    for t in txt:
        for m in re.finditer(r'\bFig (\d)\b', t):
            n = int(m.group(1))
            if n not in cites and not t.strip().startswith('Fig '): cites.append(n)
    check(cites == sorted(cites), 'figures cited in ascending order', str(cites))
    nu = sum(1 for p in root.iter(q('p')) for rpr in p.iter(q('rPr')) for _ in rpr.findall(q('u')))
    check(True, 'underline runs remaining in document', str(nu))
    check(not re.search(r'Fig\.\s*\d', allt), 'no "Fig." citations remain')
    check(not re.search(r'Supplementary (Table|Fig)', allt), 'no "Supplementary Table/Fig"')
    check('Xie R, Adam DC, Hu S, Cowling BJ, Gascuel O, Zhukova A, et al.' in allt,
          'ref 13 expanded to six authors then et al.')
    check(not re.search(r'Valleron AJ\.', allt), 'ref 8 truncated to six authors')
    brackets = re.findall(r'\[(VD-\d|TY-\d) \u2014 ([A-Z][A-Z ,\-]+)', allt)
    if mode == 'edit':
        check('[KME \u2014 WITHHELD ON YOUR WORDING]' in allt,
              'the list of what was withheld on his wording is in Open queries')
    want = 8 if mode == 'edit' else 4
    check(len(brackets) == want, f'{want} input brackets present',
          ', '.join(f'{a}' for a, b in brackets))
    print('     input brackets: ' + '; '.join(f'[{a}] {b.strip()}' for a, b in brackets))
    REVTAGS = ('ins','del','moveTo','moveFrom','moveFromRangeStart','moveFromRangeEnd',
               'moveToRangeStart','moveToRangeEnd','pPrChange','rPrChange','sectPrChange',
               'tblPrChange','tcPrChange','trPrChange','cellIns','cellDel','cellMerge')
    marks = [e for e in root.iter() if isinstance(e.tag, str)
             and etree.QName(e).localname in ('ins','del')]
    allrev = [e for e in root.iter() if isinstance(e.tag, str)
              and etree.QName(e).localname in REVTAGS]
    if mode == 'submit':
        zz = zipfile.ZipFile(out)
        check(not [n for n in zz.namelist() if 'comment' in n.lower()],
              'no comment parts in the package')
        rels = zz.read('word/_rels/document.xml.rels').decode()
        check('comment' not in rels.lower(), 'no dangling comment relationships')
        check('comment' not in zz.read('[Content_Types].xml').decode().lower(),
              'no comment content-type overrides')
        try:
            import docx; docx.Document(out); ok = True; why = 'opens'
        except Exception as e:
            ok = False; why = type(e).__name__
        check(ok, 'python-docx can open the package', why)
    if mode == 'edit':
        authors = {e.get(q('author')) for e in marks}
        check(authors <= {AUTHOR, REC_AUTHOR, 'Kimberly Edwards'} | set(FU_AUTH.values()),
              'every tracked change is ours or hers',
              '; '.join(sorted(a or '?' for a in authors)))
        reloc = [e for e in marks if e.get(q('author')) == AUTHOR]
        recs = [e for e in marks if e.get(q('author')) == REC_AUTHOR]
        check(len(reloc) > 0, 'the Methods relocation is present and separable',
              f'{len(reloc)} marks')
        check(len(recs) > 0, 'recommendations are present as a filterable author',
              f'{len(recs)} marks')
        cs = [e.get(q('id')) for e in root.iter(q('commentRangeStart'))]
        cr_ = [e.get(q('id')) for e in root.iter(q('commentReference'))]
        cx = [c.get(q('id')) for c in etree.parse(
              os.path.join(os.path.dirname(docpath), 'comments.xml')).getroot().iter(q('comment'))]
        check(sorted(cs) == sorted(cr_) == sorted(cx),
              'comment ranges, references and comments.xml agree',
              f'{len(cs)}/{len(cr_)}/{len(cx)}')
        check(len(cs) == 26 + 8 + 33,
              'the 26 inherited comments, 8 of mine and all 33 of hers', str(len(cs)))
        kmes = [e for e in marks if e.get(q('author')) == 'Kimberly Edwards']
        check(len(kmes) > 0, 'her edits are a separately filterable author',
              f'{len(kmes)} marks')
        wd = os.path.dirname(docpath)
        counts = {}
        for nm in ('commentsExtended.xml', 'commentsIds.xml', 'commentsExtensible.xml'):
            counts[nm] = len(list(etree.parse(os.path.join(wd, nm)).getroot()))
        check(all(v == len(cs) for v in counts.values()),
              'every comment is registered in all three metadata parts',
              ', '.join(f'{k.replace("comments","").replace(".xml","")}={v}'
                        for k, v in counts.items()) + f' vs {len(cs)} comments')
        # rejecting the recommendations must restore the text they would change
        rj = etree.fromstring(etree.tostring(root))
        for e in list(rj.iter()):
            if not isinstance(e.tag, str) or e.getparent() is None: continue
            ln2 = etree.QName(e).localname
            if ln2 == 'ins' and e.get(q('author')) == REC_AUTHOR \
               and etree.QName(e.getparent()).localname != 'rPr':
                e.getparent().remove(e)
            elif ln2 == 'del' and e.get(q('author')) == REC_AUTHOR \
                 and etree.QName(e.getparent()).localname != 'rPr':
                par2 = e.getparent()
                for ch in list(e):
                    for dt in ch.iter(q('delText')): dt.tag = q('t')
                    e.addprevious(ch)
                par2.remove(e)
        rjt = '\n'.join(''.join(t.text or '' for t in p.iter(q('t'))) for p in rj.iter(q('p')))
        for _, old, new, _w in RECOMMENDATIONS:
            check(old in rjt and new not in rjt,
                  f'rejecting restores {old[:34]!r}...')
        dels = [e for e in root.iter(q('del')) if e.get(q('author')) == AUTHOR
                and etree.QName(e.getparent()).localname != 'rPr']
        check(len(dels) > 0, 'the relocation is two-sided: a deletion remains at the old position',
              f'{len(dels)} deletion wrappers')
        rj = etree.fromstring(etree.tostring(root))
        for p in list(rj.iter(q('p'))):
            m = p.find('w:pPr/w:rPr/w:ins', NS)
            if m is not None and m.get(q('author')) == AUTHOR: p.getparent().remove(p)
        for e in list(rj.iter()):
            if not isinstance(e.tag, str) or e.getparent() is None: continue
            if etree.QName(e).localname == 'del' and e.get(q('author')) == AUTHOR \
               and etree.QName(e.getparent()).localname != 'rPr':
                par = e.getparent()
                for ch in list(e):
                    for dt in ch.iter(q('delText')): dt.tag = q('t')
                    e.addprevious(ch)
                par.remove(e)
        rh = [''.join(t.text or '' for t in p.iter(q('t'))).strip() for p in rj.iter(q('p'))
              if p.find('w:pPr/w:pStyle', NS) is not None
              and p.find('w:pPr/w:pStyle', NS).get(q('val')) == 'Heading1']
        rseq = [x for x in rh if x in ('Introduction','Materials and Methods','Results','Discussion')]
        check('Materials and Methods' in rseq
              and rseq.index('Materials and Methods') < rseq.index('Results'),
              'rejecting the relocation restores Methods before Results, as VD had it',
              ' > '.join(rseq))
        rjt2 = '\n'.join(''.join(t.text or '' for t in p.iter(q('t'))) for p in rj.iter(q('p')))
        check(AFF_OLD in rjt2 and AFF2 not in rjt2,
              'rejecting restores v10\u2019s merged affiliation line')
        check('Thomas Yuan1,2, Vijaykrishna Dhanasekaran1,*' in rjt2,
              'rejecting restores v10\u2019s author superscripts')
        check('not part of the PLOS submission' in allt, 'Highlights retained in a labelled block')
    else:
        check(len(marks) == 0, 'no tracked changes', f'{len(marks)} marks')
        kinds = sorted({etree.QName(e).localname + ':' + (e.get(q('author')) or '?')
                        for e in allrev})
        check(len(allrev) == 0,
              'no revision elements of any kind, moves and format changes included',
              f'{len(allrev)} left: ' + '; '.join(kinds))
        check(len(list(root.iter(q('commentReference')))) == 0, 'no comments')
        check('not part of the PLOS submission' not in allt, 'Highlights block dropped')
    print('     paragraphs', len(txt))

def accepted_text(path, reject=()):
    """Text after accepting every revision, except that revisions by an author
    in `reject` are rejected instead. The recommendations are proposals, so the
    submission copy is by construction the editing copy with those rejected."""
    rt = etree.parse(path).getroot()
    out = []
    for p in rt.iter(q('p')):
        m = p.find('w:pPr/w:rPr/w:del', NS)
        if m is not None and m.get(q('author')) not in reject: continue
        buf = []
        for n in p.iter():
            if not isinstance(n.tag, str): continue
            ln = etree.QName(n).localname
            if ln not in ('t', 'delText'): continue
            a = n.getparent(); drop = False; keep_del = False
            while a is not None and a is not p:
                la = etree.QName(a).localname
                au = a.get(q('author'))
                if la in ('del', 'moveFrom'):
                    if au in reject: keep_del = True
                    else: drop = True; break
                if la in ('ins', 'moveTo') and au in reject:
                    drop = True; break
                a = a.getparent()
            if drop: continue
            if ln == 'delText' and not keep_del: continue
            buf.append(n.text or '')
        t = re.sub(r'\s+', ' ', ''.join(buf)).strip()
        if t: out.append(t)
    return out

print()
if os.path.exists(DOCPATHS.get('edit', '')) and os.path.exists(DOCPATHS.get('submit', '')):
    ed = set(accepted_text(DOCPATHS['edit'], reject=(REC_AUTHOR,)))
    sb = accepted_text(DOCPATHS['submit'])
    miss = [t for t in sb if t not in ed]
    check(not miss,
          'the editing copy, with the recommendations rejected, reproduces the '
          'submission copy',
          f'{len(miss)} paragraph(s) differ: ' + '; '.join(m[:70] for m in miss[:3]))

print('abbreviations used fewer than three times (PLOS allows non-standard ones only at 3+):')
root = etree.parse(docpath).getroot()
allt = '\n'.join(ptext(p) for p in root.iter(q('p')))
import collections
cnt = collections.Counter(re.findall(r'\b[A-Z]{2,6}\b', allt))
rare = {k: v for k, v in cnt.items() if v < 3}
print('   ', ', '.join(f'{k}({v})' for k, v in sorted(rare.items())) or 'none')
sys.exit(1 if fail else 0)
