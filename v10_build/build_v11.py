"""Build early-warning v11 as tracked changes on top of v10.

Four edits. Three were settled by Vijay on 27 October; the fourth is the second
site of the same defect as edit 3 and is Thomas's own prose.

Nothing of Vijay's is touched: his w:moveTo runs in the Methods paragraph, his
comments and his property changes are left exactly as they are. Every new
revision is authored "Thomas Yuan" and dated 2026-11-05, which is what lets the
round-trip check below reject precisely this build and nothing else.

Two items the v11 draft of 27 October listed are NOT here, because v10 already
contains them and a rebuild would have duplicated them:
  - the influenza half of the serial-interval result is already in Results p59
    ("the grid resolves to four distinct onset outcomes rather than twenty"),
    so only the RSV half is inserted;
  - Table S4 already reports 4 distinct influenza configurations and the
    3.5-12.8 day spread, and reference [8] is already Carrat et al. 2008 rather
    than Lessler. Neither needs changing.
"""
import copy, hashlib, os, shutil, sys, zipfile
from lxml import etree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ooxml_track import Editor, NS, q, W, XML

HOME = os.path.expanduser('~')
SRC  = f'{HOME}/mnt/HKU-influenza/manuscript/2026-10-15_early-warning_v10.docx'
OUT  = f'{HOME}/mnt/pinn-early-warning/v10_build/2026-11-05_early-warning_v11.docx'
import time
WORK = f'{HOME}/mnt/pinn-early-warning/v10_build/_v11_{int(time.time())}'  # fresh: this shell cannot delete
AUTHOR, DATE = 'Thomas Yuan', '2026-11-05T12:00:00Z'
SRC_MD5 = '5d56c38565a55fdeb8ddef8f71a7cf78'   # word/document.xml of the released v10

fail = []
def check(ok, label, detail=''):
    print(('  PASS  ' if ok else '  FAIL  ') + label + (('  -- ' + detail) if detail else ''))
    if not ok: fail.append(label)

# ---------------------------------------------------------------- load and pin
with zipfile.ZipFile(SRC) as z:
    base_doc = z.read('word/document.xml')
    ORDER = [i.filename for i in z.infolist()]
got = hashlib.md5(base_doc).hexdigest()
assert got == SRC_MD5, f'v10 document.xml md5 is {got}, expected {SRC_MD5}'
print(f'base: v10 word/document.xml md5 {got}  (the released copy)')

with zipfile.ZipFile(SRC) as z: z.extractall(WORK)
docpath = os.path.join(WORK, 'word', 'document.xml')
tree = etree.parse(docpath); root = tree.getroot()
body = root.find('w:body', NS)
P = list(root.iter(q('p')))   # same order as accepted(), so indices align

# every revision id already in the file, so the new ones cannot collide
old_ids = {e.get(q('id')) for e in root.iter() if isinstance(e.tag, str)
           and etree.QName(e).localname in ('ins','del','moveFrom','moveTo') and e.get(q('id'))}
ed = Editor(root, AUTHOR, DATE, first_id=7000)

def accepted(r):
    """Text a reader sees with changes applied, one string per paragraph."""
    out = []
    for p in r.iter(q('p')):
        buf = []
        for t in p.iter(q('t')):
            a, hidden = t.getparent(), False
            while a is not None and a is not p:
                if etree.QName(a).localname in ('del','moveFrom'): hidden = True; break
                a = a.getparent()
            if not hidden: buf.append(t.text or '')
        out.append(''.join(buf))
    return out

before = accepted(root)
def find(frag):
    hits = [i for i,t in enumerate(before) if frag in t]
    assert len(hits) == 1, f'{len(hits)} paragraphs contain {frag[:50]!r}'
    return hits[0]

# ------------------------------------------------ paragraph insertion, tracked
def new_para_after(model_p, text):
    np = copy.deepcopy(model_p)
    for ch in list(np):
        if etree.QName(ch).localname != 'pPr': np.remove(ch)
    ppr = np.find(q('pPr'))
    if ppr is None:
        ppr = etree.Element(q('pPr')); np.insert(0, ppr)
    for ch in list(ppr):                      # never inherit someone else's record
        if etree.QName(ch).localname in ('rPr','pPrChange','sectPr'): ppr.remove(ch)
    rpr = etree.SubElement(ppr, q('rPr'))
    m = etree.SubElement(rpr, q('ins'))
    m.set(q('id'), ed.nid()); m.set(q('author'), AUTHOR); m.set(q('date'), DATE)
    src = None
    for r in model_p.iter(q('r')):
        if r.find(q('t')) is not None: src = r; break
    np.append(ed.make_ins(text, src))
    model_p.addnext(np)
    return np

# =============================================================== E1  Results
i_res = find('EpiEstim detected onset in all 6 influenza seasons in the primary evaluation')
RSV_PARA = (
 'RSV behaves differently, and the difference follows from the reporting interval rather '
 'than from the biology. At 7.5 days the specified mean straddles the first weekly bin edge '
 'and leaves a genuinely spread kernel, first weekly weight 0.800, so unlike influenza the '
 'onset date does move: across the same four window widths the five RSV means shift the '
 'detected onset in 3 of 12 season-window cells, by 7 to 14 days, all within the 2017 summer '
 'season and all between the 6.0 and 7.5-day means. Where a pathogen’s serial interval sits '
 'relative to the reporting interval therefore determines whether the assumption can affect '
 'the estimated onset at all. Two limits apply to the contrast: the RSV movement rests on one '
 'of three test seasons, and the two grids are not matched, since every influenza mean tested '
 'falls below the first bin edge while the RSV means straddle it (invariance check and full '
 'results at si_invariance_check.py and rsv_si_sensitivity.csv in the repository).')
new_para_after(P[i_res], RSV_PARA)
print(f'E1  new Results paragraph after p{i_res}')

# =============================================================== E2  Methods SD
i_met = find('RSV onset detection was robust to SI assumptions')
ed.insert_after(P[i_met],
 'the value used here is central to that range rather than taken from a single estimate.',
 ' The influenza standard deviation of 1.5 days is likewise not taken from a single source; '
 'the nearest published value is 1.6 days, from the same Hong Kong household study [16]. The '
 'discretisation figures reported below are insensitive to this choice: the first weekly '
 'weight remains at or above 0.984 for standard deviations between 1.2 and 2.0 days.')
print(f'E2  influenza SD disclosed in p{i_met}')

# =============================================== E3  detection vs timing, Methods
ed.replace(P[i_met],
 'RSV onset detection was robust to SI assumptions despite the 7.5-day SI providing '
 'approximately one observation per weekly generation.',
 'Every RSV configuration detected onset in all three test seasons, so detection was robust '
 'to the serial-interval assumption; the onset date was not, moving in 3 of 12 season-window '
 'cells by 7 to 14 days (Results).')
print(f'E3  detection separated from timing in p{i_met}')

# ============================== E4  the same defect's second site, simulation Results
i_sim = find('consistent with the finding that onset detection was robust to SI assumptions')
ed.replace(P[i_sim],
 'consistent with the finding that onset detection was robust to SI assumptions in the '
 'empirical analysis.',
 'consistent with the empirical finding that onset detection was robust to the '
 'serial-interval assumption in both pathogens, although the onset date was not, moving in '
 '3 of 12 RSV season-window cells (Results).')
print(f'E4  second site corrected in p{i_sim}')

# ------------------------------------------------------------------- write out
tree.write(docpath, xml_declaration=True, encoding='UTF-8', standalone=True)
with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as z:
    for name in ORDER:
        z.write(os.path.join(WORK, *name.split('/')), name)

# =========================================================== checks
print('\nchecks')
nroot = etree.parse(OUT if False else docpath).getroot()
mine  = [e for e in nroot.iter() if isinstance(e.tag, str)
         and etree.QName(e).localname in ('ins','del') and e.get(q('date')) == DATE]
check(all(e.get(q('author')) == AUTHOR for e in mine),
      'C1 every new revision is authored Thomas Yuan', f'{len(mine)} elements')
new_ids = [e.get(q('id')) for e in mine]
check(len(set(new_ids)) == len(new_ids) and not (set(new_ids) & old_ids),
      'C2 new revision ids are unique and do not collide with v10 ids')

# C3 round trip: rejecting exactly this build must reproduce v10's accepted text
rej = etree.fromstring(etree.tostring(nroot))
for p in list(rej.iter(q('p'))):                      # whole paragraphs I inserted
    m = p.find('w:pPr/w:rPr/w:ins', NS)
    if m is not None and m.get(q('date')) == DATE: p.getparent().remove(p)
for e in list(rej.iter()):
    if not isinstance(e.tag, str): continue
    ln = etree.QName(e).localname
    if ln == 'ins' and e.get(q('date')) == DATE and e.getparent() is not None:
        e.getparent().remove(e)
    elif ln == 'del' and e.get(q('date')) == DATE:
        par = e.getparent()
        for ch in list(e):
            for dt in ch.iter(q('delText')): dt.tag = q('t')
            e.addprevious(ch)
        par.remove(e)
check(accepted(rej) == before,
      'C3 rejecting this build reproduces v10 exactly',
      'identical' if accepted(rej) == before else 'DIFFERS')

# C4 nobody else's revision count changed
def census(r):
    c = {}
    for e in r.iter():
        if not isinstance(e.tag, str): continue
        ln = etree.QName(e).localname
        if ln in ('ins','del','moveFrom','moveTo'):
            a = e.get(q('author'))
            if a and a != AUTHOR: c[(ln,a)] = c.get((ln,a),0)+1
    return c
oroot = etree.fromstring(base_doc)
check(census(oroot) == census(nroot), 'C4 no revision of anyone else was altered',
      str(census(nroot)))
check(len(list(oroot.iter(q('commentRangeStart')))) == len(list(nroot.iter(q('commentRangeStart')))),
      'C5 comment count unchanged',
      f"{len(list(nroot.iter(q('commentRangeStart'))))} anchors")

after = accepted(nroot)
for frag, label in [('3 of 12 season-window cells, by 7 to 14 days', 'C6 RSV contrast present'),
                    ('influenza standard deviation of 1.5 days', 'C7 SD disclosure present'),
                    ('so detection was robust', 'C8 detection/timing split present'),
                    ('in both pathogens', 'C9 second site corrected')]:
    check(any(frag in t for t in after), label)
check(not any('RSV onset detection was robust to SI assumptions' in t for t in after),
      'C10 the superseded RSV sentence is gone from the accepted text')

print(f'\n{OUT}')
print('word/document.xml md5', hashlib.md5(open(docpath,"rb").read()).hexdigest())
print('paragraphs', len(before), '->', len(after))
sys.exit(1 if fail else 0)
