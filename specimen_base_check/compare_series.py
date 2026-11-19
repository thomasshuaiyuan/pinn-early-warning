"""Compare the positivity series used in the paper (flux_data.csv, from Flu Express) with CHP's statistics-page
series (Public Health Laboratory Services Branch specimens only), week by week. 19 Nov 2026.
Usage: python3 compare_series.py <path to flux_data.csv>"""
import csv, sys, datetime as dt
flux = {}
for r in csv.DictReader(open(sys.argv[1])):
    try: flux[(int(r['Year']), int(r['Week']))] = (r['From'], float(r['AandB']), float(r['AandB_proportion']))
    except ValueError: pass
out = []
for r in csv.DictReader(open('chp_statistics_influenza_weekly.csv')):
    k = (int(r['year']), int(r['week']))
    if k not in flux: continue
    pos = (int(r['A_pos']) if r['layout'] == 'new' else int(r['H1']) + int(r['H3'])) + int(r['B_pos'])
    t = int(r['tested']); frm, fa, fp = flux[k]
    out.append(dict(year=k[0], week=k[1], week_start=frm, stat_tested=t, stat_pos=pos, stat_pct=round(100*pos/t, 2) if t else '',
                    flux_pos=int(fa), flux_pct=round(100*fp, 2), flux_implied_tested=round(fa/fp) if fp else '',
                    same=(int(fa) == pos)))
with open('series_comparison_weekly.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
print('weeks compared:', len(out), ' identical positives:', sum(o['same'] for o in out))
first = next(o for o in out if not o['same']); last_same = [o for o in out if o['same']][-1]
print('first week that differs:', first); print('last week identical:', last_same)
import collections
by = collections.Counter((o['year'], o['same']) for o in out); print(sorted(by.items()))
def runs(key, thr=4.94, minlen=4):
    res = []; cur = []
    for o in out:
        v = o[key]
        if v != '' and v >= thr: cur.append(o)
        else:
            if len(cur) >= minlen: res.append(cur)
            cur = []
    if len(cur) >= minlen: res.append(cur)
    return res
for key in ('flux_pct', 'stat_pct'):
    print('\n', key, 'runs of >=4 weeks at or above 4.94%:')
    for r in runs(key):
        if r[0]['year'] >= 2023 or r[0]['year'] <= 2019:
            print('  start', r[0]['week_start'], 'weeks', len(r), 'peak', max(x[key] for x in r))
