#!/usr/bin/env python3
"""
Validate 2026-10-15_early-warning_v10.docx against 2026-09-26_early-warning_v9.docx.

Written after the first build passed a weaker check. The weaker check counted
revision ELEMENTS by author and found them unchanged, which is not the property
that matters: splitting a run inside an existing revision legitimately creates a
second element with the same author, while cloning a paragraph can create a new
element with someone else's name on it. Element counts move in both cases and
distinguish neither.

What is checked here instead:

  C1  Rejecting only the 15 October revisions reproduces v9's text exactly,
      including dropping paragraphs whose paragraph mark is a 15 October
      insertion.
  C2  Every piece of text not authored on 15 October still has the same owner
      (author and revision kind) that it had in v9. This is the property the
      standing constraint needs: nothing of Vijay's is altered or re-attributed.
  C3  No revision id is used twice. Duplicate ids are invalid and Word repairs
      them silently.
  C4  No paragraph created on 15 October carries a revision record authored by
      anyone else.
  C5  Vijay's comments are all still present and unchanged.
  C6  The accepted text says what the changelog says it says.
"""
import sys
import zipfile
import copy
import collections
from lxml import etree

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
MINE_DATE = '2026-10-15'
MINE_AUTHOR = 'Thomas Yuan'
REV = ('ins', 'del', 'moveFrom', 'moveTo', 'pPrChange', 'rPrChange')

V9 = sys.argv[1] if len(sys.argv) > 1 else '2026-09-26_early-warning_v9.docx'
V10 = sys.argv[2] if len(sys.argv) > 2 else '2026-10-15_early-warning_v10.docx'

fails = []


def check(ok, label, detail=''):
    print(('OK   ' if ok else 'FAIL ') + label + (('  ' + detail) if detail and not ok else ''))
    if not ok:
        fails.append(label)


def part(path, name='word/document.xml'):
    with zipfile.ZipFile(path) as z:
        return etree.fromstring(z.read(name))


def ln(e):
    return etree.QName(e).localname if isinstance(e.tag, str) else ''


def mine(e):
    return (e.get(W + 'date') or '').startswith(MINE_DATE) and e.get(W + 'author') == MINE_AUTHOR


def para_mark_mine(p):
    ppr = p.find(W + 'pPr')
    if ppr is None:
        return False
    rpr = ppr.find(W + 'rPr')
    if rpr is None:
        return False
    i = rpr.find(W + 'ins')
    return i is not None and mine(i)


# ---------------------------------------------------------------- C1 round trip
def reject_mine_tree(root):
    """Reject only the 15 October revisions, leaving everything else as it was.

    The paragraphs I created are dropped whole. They have to be identified BEFORE
    the removal loop runs, because that loop deletes the very paragraph-mark w:ins
    that identifies them — the first version of this function looked for the mark
    afterwards and silently kept three empty paragraphs.
    """
    r = copy.deepcopy(root)
    drop = {p for p in r.iter(W + 'p') if para_mark_mine(p)}
    for el in list(r.iter(W + 'ins')):
        if mine(el):
            par = el.getparent()
            if par is not None:
                par.remove(el)
    for el in list(r.iter(W + 'del')):
        if not mine(el):
            continue
        par = el.getparent()
        if par is None:
            continue
        if ln(par) == 'rPr':
            par.remove(el)
            continue
        i = list(par).index(el)
        for ch in reversed(list(el)):
            par.insert(i, ch)
        par.remove(el)
    for dt in list(r.iter(W + 'delText')):
        if not any(ln(a) == 'del' for a in dt.iterancestors()):
            dt.tag = W + 't'
    for p in drop:
        par = p.getparent()
        if par is not None:
            par.remove(p)
    return r


def plain_text(root):
    out = []
    for p in root.iter(W + 'p'):
        out.append(''.join(t.text or '' for t in p.iter(W + 't')))
    return '\n'.join(out)


d9, d10 = part(V9), part(V10)
d10_rej = reject_mine_tree(d10)
rt, base = plain_text(d10_rej), plain_text(d9)
check(rt == base, 'C1  rejecting only the 15 October revisions reproduces v9 exactly')
if rt != base:
    import difflib
    for line in list(difflib.unified_diff(base.split('\n'), rt.split('\n'), lineterm=''))[:24]:
        print('     ' + line)


# -------------------------------------------------------------- C2 text ownership
def owner_stream(root):
    """Text in document order, labelled by the revision that owns it.

    Run boundaries are not stable: an edit beside existing text splits its run,
    which changes the element count without changing who owns the characters. So
    the comparison is made on the concatenated character stream per owner, which
    splitting leaves untouched.
    """
    d = collections.defaultdict(list)
    for t in root.iter(W + 't', W + 'delText'):
        owner = ('', '')
        for a in t.iterancestors():
            if ln(a) in ('ins', 'del', 'moveFrom', 'moveTo'):
                owner = (a.get(W + 'author') or '', ln(a))
                break
        d[owner].append(t.text or '')
    return {k: ''.join(v) for k, v in d.items()}


# Compared on the rejected tree, not on v10 itself: rejecting my deletions puts
# the text back under its original owner, so any owner-level difference that
# survives is text of someone else's that this build altered.
s9, s10 = owner_stream(d9), owner_stream(d10_rej)
mism = [k for k in sorted(set(s9) | set(s10)) if s9.get(k, '') != s10.get(k, '')]
check(not mism, 'C2  with my revisions rejected, every owner holds exactly the text it held in v9',
      'differing owners: %s' % mism)
for k in mism[:4]:
    a, b = s9.get(k, ''), s10.get(k, '')
    i = next((j for j in range(min(len(a), len(b))) if a[j] != b[j]), min(len(a), len(b)))
    print('     owner %s: v9 %d chars, v10 %d chars; first difference at %d'
          % (k, len(a), len(b), i))
    print('       v9  %r' % a[i:i + 70])
    print('       v10 %r' % b[i:i + 70])
print('     owners checked: %s' % sorted(set(s9) | set(s10)))

# --------------------------------------------------------------- C3 unique ids
ids = collections.Counter()
for tag in REV + ('commentRangeStart', 'commentRangeEnd'):
    for e in d10.iter(W + tag):
        v = e.get(W + 'id')
        if v is not None:
            ids[(tag in ('commentRangeStart', 'commentRangeEnd'), v)] += 1
dupes = {k: n for k, n in ids.items() if n > 1 and not k[0]}
check(not dupes, 'C3  every revision id is unique', 'duplicates: %s' % dupes)

# ------------------------------------------- C4 my paragraphs carry only my marks
foreign = []
for p in d10.iter(W + 'p'):
    if not para_mark_mine(p):
        continue
    for e in p.iter():
        if ln(e) in REV and not mine(e):
            foreign.append((ln(e), e.get(W + 'author'), (e.get(W + 'date') or '')[:10]))
check(not foreign, 'C4  paragraphs created on 15 October carry no other author\'s revisions',
      'found: %s' % foreign)

# ------------------------------------------------------------------- C5 comments
c9, c10 = part(V9, 'word/comments.xml'), part(V10, 'word/comments.xml')


def comment_map(root):
    d = {}
    for c in root.findall(W + 'comment'):
        d[c.get(W + 'id')] = (c.get(W + 'author'), ' '.join(''.join(
            t.text or '' for t in c.iter(W + 't')).split()))
    return d


m9, m10 = comment_map(c9), comment_map(c10)
check(m9 == m10, 'C5  all %d comments present and unchanged' % len(m9),
      'differences: %s' % [k for k in set(m9) | set(m10) if m9.get(k) != m10.get(k)])
anchors9 = sorted(e.get(W + 'id') for e in d9.iter(W + 'commentRangeStart'))
anchors10 = sorted(e.get(W + 'id') for e in d10.iter(W + 'commentRangeStart'))
check(anchors9 == anchors10, 'C5b all comment anchors still in the document')

# -------------------------------------------------------------------- C6 content
def accept_text(root):
    """The reading view: all revisions accepted.

    w:moveFrom must be dropped and w:moveTo unwrapped, not only w:del and w:ins.
    v9 carries a tracked move of the Methods block by Vijay, so the moved-from
    copy is still in the XML; a view that ignores moveFrom reads the Methods
    section twice and reports pre-move wording as if it were current. The first
    version of this check did exactly that and reported two phantom failures.
    """
    r = copy.deepcopy(root)
    for tag in ('del', 'moveFrom'):
        for el in list(r.iter(W + tag)):
            par = el.getparent()
            if par is not None:
                par.remove(el)
    for tag in ('ins', 'moveTo'):
        for el in list(r.iter(W + tag)):
            par = el.getparent()
            if par is None:
                continue
            if ln(par) == 'rPr':
                par.remove(el)
                continue
            i = list(par).index(el)
            for ch in reversed(list(el)):
                par.insert(i, ch)
            par.remove(el)
    return plain_text(r)


acc = accept_text(d10)
WANT = [
    ('12–17 year admissions led positivity in four of eight influenza seasons and were never later', True),
    ('outperform', False),
    ('four to six weeks', False),
    ('(~26,000)', False),
    ('49,005, 26,005 and 27,505', True),
    ('every week of the four-week estimation window ending on the reported onset date carries zero admissions', True),
    ('conditioned on a lag of at least one week', True),
    ('Carrat F, Vergu E', True),
    ('Lessler', False),
    ('Supplementary Fig. S5', True),
    ('mean 7.5 days for RSV [14], with a standard deviation of 3.5 days', True),
    ('20 SI/window configurations', False),
    ('Logistic regression of lead > 0 on SNR', False),
    ('16. Cowling BJ', True),
    ('17. Nash RK', True),
    ('18. Ogi-Gittins I', True),
]
bad = []
for s, want in WANT:
    got = s in acc
    if got != want:
        bad.append((s, want, got))
check(not bad, 'C6  accepted text matches the changelog on %d checks' % len(WANT),
      'mismatches: %s' % [(s[:48], w) for s, w, g in bad])

print()
print('FAILED: %d' % len(fails) if fails else 'all checks passed')
sys.exit(1 if fails else 0)
