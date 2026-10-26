"""In-place tracked-change editor for a .docx document.xml (lxml).

Edits are made as w:del / w:ins by a new author, leaving every existing
revision (w:ins, w:del, w:moveFrom, w:moveTo), comment and property change
of other authors in place. Text matching is done against the *visible*
text of a paragraph: runs inside w:del or w:moveFrom are skipped.
"""
import copy
from lxml import etree

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
XML = 'http://www.w3.org/XML/1998/namespace'
NS = {'w': W}


def q(tag):
    return '{%s}%s' % (W, tag)


def L(e):
    return etree.QName(e).localname if isinstance(e.tag, str) else ''


WRAPPERS = ('ins', 'moveTo', 'smartTag', 'customXml')


class Editor:
    def __init__(self, root, author, date, first_id=900):
        self.root = root
        self.author = author
        self.date = date
        self.next_id = first_id
        self.log = []

    def nid(self):
        self.next_id += 1
        return str(self.next_id)

    # ---------- visible runs ----------
    def vis_runs(self, p):
        out = []
        for r in p.iter(q('r')):
            hidden = False
            a = r.getparent()
            while a is not None and a is not p:
                if L(a) in ('del', 'moveFrom'):
                    hidden = True
                    break
                a = a.getparent()
            if hidden:
                continue
            ts = r.findall(q('t'))
            if not ts:
                continue
            assert len(ts) == 1, 'run with multiple w:t'
            out.append(r)
        return out

    @staticmethod
    def rtext(r):
        return r.find(q('t')).text or ''

    def vis_text(self, p):
        return ''.join(self.rtext(r) for r in self.vis_runs(p))

    @staticmethod
    def set_text(r, s):
        t = r.find(q('t'))
        t.text = s
        t.set('{%s}space' % XML, 'preserve')

    def split(self, r, k):
        """Split run r at char offset k; return (left, right)."""
        s = self.rtext(r)
        assert 0 < k < len(s)
        r2 = copy.deepcopy(r)
        self.set_text(r, s[:k])
        self.set_text(r2, s[k:])
        r.addnext(r2)
        return r, r2

    def isolate(self, p, old, occurrence=0):
        """Split runs so that `old` is covered exactly by whole visible runs."""
        text = self.vis_text(p)
        idx = -1
        start = 0
        for _ in range(occurrence + 1):
            idx = text.find(old, start)
            if idx < 0:
                raise ValueError('not found: %r\nin: %r' % (old[:80], text[:200]))
            start = idx + 1
        if occurrence == 0 and text.find(old, idx + 1) >= 0:
            raise ValueError('ambiguous: %r' % old[:80])
        end = idx + len(old)
        # split at start
        for pos in (idx, end):
            off = 0
            for r in self.vis_runs(p):
                n = len(self.rtext(r))
                if off < pos < off + n:
                    self.split(r, pos - off)
                    break
                off += n
        sel = []
        off = 0
        for r in self.vis_runs(p):
            n = len(self.rtext(r))
            if off >= idx and off + n <= end and n > 0:
                sel.append(r)
            off += n
        assert ''.join(self.rtext(r) for r in sel) == old, 'isolate mismatch'
        return sel

    # ---------- structural helpers ----------
    def _clone_wrapper(self, w):
        c = etree.Element(w.tag, nsmap=w.nsmap)
        for k, v in w.attrib.items():
            c.set(k, v)
        if c.get(q('id')) is not None:
            c.set(q('id'), self.nid())
        return c

    def hoist(self, el, p):
        """Split wrappers so that the point right after `el` is a direct child
        position of p. Returns the direct child of p that `el` ends in."""
        while el.getparent() is not p:
            parent = el.getparent()
            assert L(parent) in WRAPPERS, 'cannot hoist out of ' + L(parent)
            tail = []
            nxt = el.getnext()
            while nxt is not None:
                tail.append(nxt)
                nxt = nxt.getnext()
            if tail:
                c = self._clone_wrapper(parent)
                for t in tail:
                    c.append(t)
                parent.addnext(c)
            el = parent
        return el

    def hoist_before(self, el, p):
        """Split wrappers so that the point right before `el` is a p-level position.
        Returns the direct child of p that now starts with `el`."""
        while el.getparent() is not p:
            parent = el.getparent()
            assert L(parent) in WRAPPERS, 'cannot hoist out of ' + L(parent)
            head = []
            prv = el.getprevious()
            while prv is not None:
                head.insert(0, prv)
                prv = prv.getprevious()
            if head:
                c = self._clone_wrapper(parent)
                for h in head:
                    c.append(h)
                parent.addprevious(c)
            el = parent
        return el

    def wrap_del(self, runs):
        dels = []
        # group consecutive siblings
        groups = []
        for r in runs:
            if groups and groups[-1][-1].getnext() is r:
                groups[-1].append(r)
            else:
                groups.append([r])
        for g in groups:
            d = etree.Element(q('del'))
            d.set(q('id'), self.nid())
            d.set(q('author'), self.author)
            d.set(q('date'), self.date)
            g[0].addprevious(d)
            for r in g:
                d.append(r)
                t = r.find(q('t'))
                t.tag = q('delText')
                t.set('{%s}space' % XML, 'preserve')
            dels.append(d)
        return dels

    def make_ins(self, text, rpr_src):
        ins = etree.Element(q('ins'))
        ins.set(q('id'), self.nid())
        ins.set(q('author'), self.author)
        ins.set(q('date'), self.date)
        r = etree.SubElement(ins, q('r'))
        if rpr_src is not None and rpr_src.find(q('rPr')) is not None:
            rp = copy.deepcopy(rpr_src.find(q('rPr')))
            # drop any revision marks that belong to the source run's formatting history
            for x in rp.findall(q('rPrChange')):
                rp.remove(x)
            r.append(rp)
        t = etree.SubElement(r, q('t'))
        t.text = text
        t.set('{%s}space' % XML, 'preserve')
        return ins

    # ---------- public operations ----------
    def replace(self, p, old, new, occurrence=0):
        """Tracked replacement. Returns (first_el, last_el) at p level-ish for comment anchoring."""
        sel = self.isolate(p, old, occurrence)
        rpr_src = sel[0]
        dels = self.wrap_del(sel)
        first = dels[0]
        last_top = self.hoist(dels[-1], p)
        last = last_top
        if new:
            ins = self.make_ins(new, rpr_src)
            last_top.addnext(ins)
            last = ins
        self.log.append(('replace', old, new))
        return first, last

    def insert_after(self, p, anchor, new, occurrence=0):
        sel = self.isolate(p, anchor, occurrence)
        top = self.hoist(sel[-1], p)
        ins = self.make_ins(new, sel[-1])
        top.addnext(ins)
        self.log.append(('insert', anchor, new))
        return ins, ins

    def span(self, p, text, occurrence=0):
        """Isolate visible text for a comment anchor (no edit)."""
        sel = self.isolate(p, text, occurrence)
        return sel[0], self.hoist(sel[-1], p)

    def add_comment_marks(self, p, first, last, cid):
        """commentRangeStart before `first`, commentRangeEnd + reference run after `last`
        (`last` must be a direct child of p)."""
        assert last.getparent() is p
        cs = etree.Element(q('commentRangeStart'))
        cs.set(q('id'), str(cid))
        first.addprevious(cs)
        ce = etree.Element(q('commentRangeEnd'))
        ce.set(q('id'), str(cid))
        last.addnext(ce)
        ce.addnext(self.ref_run(cid))

    @staticmethod
    def ref_run(cid):
        r = etree.Element(q('r'))
        rp = etree.SubElement(r, q('rPr'))
        st = etree.SubElement(rp, q('rStyle'))
        st.set(q('val'), 'CommentReference')
        cr = etree.SubElement(r, q('commentReference'))
        cr.set(q('id'), str(cid))
        return r

    def reply_marks(self, parent_cid, cid):
        """Anchor a reply on exactly the same range as an existing comment."""
        root = self.root
        s = root.find('.//w:commentRangeStart[@w:id="%s"]' % parent_cid, NS)
        e = root.find('.//w:commentRangeEnd[@w:id="%s"]' % parent_cid, NS)
        ref = [x for x in root.iter(q('commentReference')) if x.get(q('id')) == str(parent_cid)][0]
        cs = etree.Element(q('commentRangeStart')); cs.set(q('id'), str(cid))
        s.addnext(cs)
        ce = etree.Element(q('commentRangeEnd')); ce.set(q('id'), str(cid))
        e.addnext(ce)
        ref.getparent().addnext(self.ref_run(cid))
