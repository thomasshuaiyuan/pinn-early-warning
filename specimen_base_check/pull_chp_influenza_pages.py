"""Pull CHP's yearly pages "Detection of influenza viruses in respiratory specimens in <year>" (2014-2026),
keep the raw HTML, and write one weekly table: specimens tested, influenza A and B positives.
Source index: https://www.chp.gov.hk/en/statistics/data/10/641/642/2274.html   Pulled 19 Nov 2026.
Usage: python3 pull_chp_influenza_pages.py"""
import urllib.request, re, csv, html, time, os
URLS = {2014: 2276, 2015: 3674, 2016: 4968, 2017: 6277, 2018: 6778, 2019: 6821, 2020: 6885, 2021: 6932,
        2022: 6988, 2023: 7022, 2024: 7052, 2025: 7079, 2026: 7101}
BASE = 'https://www.chp.gov.hk/en/statistics/data/10/641/642/%d.html'
def cells(tr): return [re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', c))).strip()
                       for c in re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', tr, re.S)]
rows = []
for y, n in URLS.items():
    fn = 'raw_html/influenza_%d.html' % y
    if not os.path.exists(fn) or os.path.getsize(fn) < 20000:
        for attempt in range(5):
            try:
                req = urllib.request.Request(BASE % n, headers={'User-Agent': 'Mozilla/5.0'})
                data = urllib.request.urlopen(req, timeout=30).read()
                if b'</html>' in data: open(fn, 'wb').write(data); break
            except Exception as e: print(y, 'retry', attempt, e)
            time.sleep(2)
        time.sleep(1)
    page = open(fn, encoding='utf-8', errors='replace').read()
    trs = [cells(t) for t in re.findall(r'<tr[^>]*>(.*?)</tr>', page, re.S)]
    head = ' '.join(' '.join(t) for t in trs if t and not re.fullmatch(r'\d+', t[0] or 'x'))
    new_layout = 'Subtyping' in head
    for t in trs:
        if not t or not re.fullmatch(r'\d{1,2}', t[0]) or len(t) < 8: continue
        num = lambda s: float(s.replace(',', '')) if re.fullmatch(r'[\d.,]+', s) else None
        v = [num(x) for x in t[2:]]
        if v[0] is None: continue
        if new_layout:   # tested | A pos, %, subtyped, H1, H3, H5, H7, H9 | B pos, % (, lineage) | C no, %
            a, h1, h3, b = v[1], v[4], v[5], v[9]
        else:            # tested | H1 n,% | H3 n,% | H5 n,% | H7 n,% | H9 n,% | B n,% | C n,%
            h1, h3, b = v[1], v[3], v[11]; a = v[1] + v[3] + v[5] + v[7] + v[9]
        rows.append([y, int(t[0]), t[1], int(v[0]), int(a), int(h1), int(h3), int(b), 'new' if new_layout else 'old'])
with open('chp_statistics_influenza_weekly.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['year', 'week', 'dates', 'tested', 'A_pos', 'H1', 'H3', 'B_pos', 'layout']); w.writerows(rows)
print(len(rows), 'rows')
