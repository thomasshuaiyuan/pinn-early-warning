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

    # --------------------------------------------------------- 9. back matter
    SI = [('S1 Table', 'Season definitions, peak positivity and wave classification for all 18 pathogen-seasons.'),
          ('S2 Table', 'Pre-onset amplification by surveillance channel.'),
          ('S3 Table', 'Data dictionary for the 31 CHP Flu Express variables, January 2014 to March 2026, 638 weeks.'),
          ('S4 Table', 'Sensitivity of EpiEstim onset detection to the serial interval and estimation window.'),
          ('S5 Fig',   'Weekly discretisation of the serial-interval distributions.')]
    pre = [para([('Acknowledgments', False)], style='Heading1'), slot('VD-2'),
           para([('Data Availability Statement', False)], style='Heading1'),
           para([('All data analysed in this study are from public sources. The Centre for Health '
                  'Protection Flu Express and respiratory surveillance series are publicly '
                  'available from the CHP website. Analysis code and the derived data files that '
                  'reproduce every reported value are available at '
                  'https://github.com/thomasshuaiyuan/pinn-early-warning, archived at ', False),
                 ('[TY-1 — CODE ARCHIVE DOI]', True), ('.', False)])]
    for p in pre: refs_head.addprevious(p)

    post = [para([('Supporting information', False)], style='Heading1')]
    for lab, title in SI:
        post.append(para([(lab + '. ', True), (title, False)]))
    if mode == 'edit':
        post += [para([('Open queries, not part of the PLOS submission', False)], style='Heading1'),
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
                 para([('Retained from the pre-submission draft, not part of the PLOS '
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

    if append_bracket('a retrospective cross-pathogen evaluation of influenza and RSV',
        'VD-6', 'SPECIALIST ABBREVIATIONS IN TITLE AND ABSTRACT',
        'PLOS asks that the title avoid specialist abbreviations and that the abstract carry '
        'none. The title uses RSV; the abstract introduces SEIR, PINN, CHP and RSV. Recommended '
        'title, 189 of the permitted 200 characters: Surveillance-based R(t) estimation for '
        'respiratory pathogen onset detection: a retrospective cross-pathogen evaluation of '
        'influenza and respiratory syncytial virus in Hong Kong, 2014\u20132026. For the abstract, '
        'either spell the four out on first use as now, which is common practice and low risk, or '
        'remove SEIR and PINN by naming the method rather than abbreviating it. Not applied, '
        'because the title and abstract are yours'):
        print('     VD-6 recommendation placed on the title')

    if append_bracket('worth evaluating as a complement in multi-pathogen surveillance',
        'VD-7', 'AUTHOR SUMMARY VOICE AND SEASON COUNT',
        'PLOS requires the Author Summary in the first person; this one is third person '
        'throughout. Recommended opening, as a minimal conversion that keeps every number: '
        '\u201cHong Kong declares influenza season when laboratory positivity crosses a fixed '
        'threshold. We tested whether methods that estimate the viral reproduction number can '
        'detect season onset earlier, and whether this generalises across respiratory viruses. We '
        'evaluated two methods across \u2026\u201d and likewise \u201cWhat mattered most was '
        'that \u2026\u201d. Separately, this paragraph says sixteen influenza and RSV seasons '
        'while the title, abstract and Results work from eighteen. Sixteen reconciles as the six '
        'influenza seasons of the primary EpiEstim evaluation plus ten RSV; eighteen is eight plus '
        'ten. A referee will ask, so one number should be stated with its basis. Not applied, '
        'because converting the voice rewrites the paragraph and the count needs your decision'):
        print('     VD-7 recommendation placed on the Author Summary')

    # a short Results preamble: burn-in, multi-wave and the onset rules were all
    # used before definition once the Methods moved to the end
    PREAMBLE = ('Onset is reported throughout as the first week in which estimated R(t) exceeds '
        '1.0. For EpiEstim this is the first week with posterior mean R(t) above 1.0; for the '
        'SEIR-PINN it is the first crossing from below, sustained over at least three consecutive '
        'evaluation points, after a four-week burn-in. Lead time is the interval in days between '
        'that date and the comparator threshold crossing, positive when the estimator is earlier. '
        'Seasons are described as multi-wave when automatic peak detection identifies more than '
        'one distinct positivity peak; those classifications were assigned after the data were '
        'examined, as noted below. Materials and Methods gives the full specifications.')
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
    for ab in ('IQR:', 'GP ILI', 'GPU', 'COVID NPIs'):
        check(ab not in allt, f'single-use abbreviation {ab!r} spelled out')
    check('seasons between 2014 and 2025' not in allt
          and 'labelled 2014/15 to 2024/25' in allt, 'abstract date range explicit')
    check('Onset is reported throughout as the first week' in allt, 'Results preamble present')
    check('with the correct serial interval' in allt and 'with correct SI' not in allt,
          'serial interval spelled out at first use in Results')
    for k in ('VD-6', 'VD-7'):
        check(k in allt, f'{k} recommendation present')
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
    want = 10 if mode == 'edit' else 6
    check(len(brackets) == want, f'{want} input brackets present',
          ', '.join(f'{a}' for a, b in brackets))
    print('     input brackets: ' + '; '.join(f'[{a}] {b.strip()}' for a, b in brackets))
    marks = [e for e in root.iter() if isinstance(e.tag, str)
             and etree.QName(e).localname in ('ins','del')]
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
        check(len(marks) > 0 and all(e.get(q('author')) == AUTHOR for e in marks),
              'Methods relocation left as a rejectable tracked change', f'{len(marks)} marks')
        check(len(list(root.iter(q('commentRangeStart')))) == 26, 'all 26 comments kept')
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
