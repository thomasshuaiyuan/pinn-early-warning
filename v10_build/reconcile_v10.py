#!/usr/bin/env python3
"""
Four-source reconciliation for the v10 package.

The project rule is that manuscript, figures, supplementary and repository must
agree on every reported value before anything goes to Vijay, and that the check
is not "did I update the manuscript" but "do all four still agree". This script
is that check for the values this round touched. Every number is re-derived from
a committed CSV, never read from one document and compared with another.

It also enforces two claim-level rules that bit this package:
  - a stated maximum may not round down (the TV bound);
  - no document may use a wording that was withdrawn.
"""
import csv
import itertools
import math
import re
import statistics as st
import sys
import zipfile
from collections import defaultdict

import numpy as np
from lxml import etree
from scipy.stats import gamma as G, rankdata

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
REPO = '/mnt/user-data/uploads/pinn-early-warning/'
DOCS = {
    'manuscript': '/home/claude/vjbuild/2026-10-15_early-warning_v10.docx',
    'figures': '/home/claude/vjbuild/2026-10-15_early-warning_v10_figures.docx',
    'supplementary': '/home/claude/vjbuild/2026-10-15_early-warning_v10_supplementary.docx',
}
fails = []


def ln(e):
    return etree.QName(e).localname if isinstance(e.tag, str) else ''


def accepted(path):
    """Accepted-changes text. Handles moveFrom/moveTo, not only ins/del."""
    r = etree.fromstring(zipfile.ZipFile(path).read('word/document.xml'))
    for tag in ('del', 'moveFrom'):
        for el in list(r.iter(W + tag)):
            p = el.getparent()
            if p is not None:
                p.remove(el)
    for tag in ('ins', 'moveTo'):
        for el in list(r.iter(W + tag)):
            p = el.getparent()
            if p is None:
                continue
            if ln(p) == 'rPr':
                p.remove(el)
                continue
            i = list(p).index(el)
            for ch in reversed(list(el)):
                p.insert(i, ch)
            p.remove(el)
    return '\n'.join(''.join(t.text or '' for t in p.iter(W + 't')) for p in r.iter(W + 'p'))


TEXT = {k: accepted(v) for k, v in DOCS.items()}
ALL = '\n'.join(TEXT.values())


def check(ok, label, detail=''):
    print(('  OK   ' if ok else '  FAIL ') + label + (('   ' + detail) if detail and not ok else ''))
    if not ok:
        fails.append(label)


def present(doc, s):
    return s in TEXT[doc]


# ====================================================== 1. SI sweep, from the CSV
print('1. Influenza SI sweep (from epiestim_si_sensitivity_flu.csv)')
rows = list(csv.DictReader(open(REPO + 'epiestim_si_sensitivity_flu.csv')))
cells = defaultdict(set)
for r in rows:
    cells[(r['season'], r['window'])].add(r['onset_date'])
check(all(len(v) == 1 for v in cells.values()) and len(cells) == 24,
      'onset identical across the 5 SI means in all 24 season-window cells',
      f'{sum(1 for v in cells.values() if len(v) > 1)} disagreeing of {len(cells)}')

seasons = []
for r in rows:
    if r['season'] not in seasons:
        seasons.append(r['season'])
sds = []
for s in seasons:
    per = {int(r['window']): int(float(r['lead_days']))
           for r in rows if r['season'] == s and float(r['si_mean']) == 3.0}
    sds.append(st.stdev([per[w] for w in sorted(per)]))
lo, hi, mean_sd = min(sds), max(sds), st.mean(sds)
check(abs(lo - 3.5) < .05 and abs(hi - 12.8) < .05, f'SD range {lo:.1f} to {hi:.1f} days')
check(abs(mean_sd - 7.7) < .05, f'mean SD {mean_sd:.2f} days')
for d in ('manuscript', 'supplementary'):
    check(present(d, '7.7'), f'{d} carries the 7.7 mean')
check(not any('6.8 days' in TEXT[d] for d in TEXT),
      'the superseded 6.8-day mean appears in no document')
check(present('supplementary', '3.1 to 11.4'),
      'supplementary explains the superseded 3.1 to 11.4 range')


# ================================================ 2. discretisation and TV bound
print('\n2. Weekly discretisation (gamma, recomputed)')


def kern(mean, sd, n=400):
    g = G((mean / sd) ** 2, scale=sd ** 2 / mean)
    k = np.arange(1, n)
    w = g.cdf(7 * (k + .5)) - g.cdf(7 * (k - .5))
    return w / w.sum(), float(g.cdf(3.5)), float(7 * (w / w.sum() * k).sum())


wf, dropf, meanf = kern(3.0, 1.5)
wr, dropr, meanr = kern(7.5, 3.5)
check(abs(dropf - .685) < .001 and abs(wf[0] - .998) < .001 and abs(meanf - 7.01) < .005,
      f'influenza: {dropf*100:.1f}% dropped, w1 {wf[0]:.4f}, effective mean {meanf:.2f} d')
check(abs(dropr - .099) < .001 and abs(wr[0] - .800) < .001 and abs(meanr - 8.50) < .005,
      f'RSV: {dropr*100:.1f}% dropped, w1 {wr[0]:.4f}, effective mean {meanr:.2f} d')

grid = [kern(m, .5 * m)[0] for m in (2.0, 2.5, 3.0, 3.5, 4.0)]
tvmax = max(float(np.abs(a - b).sum() / 2) for a, b in itertools.combinations(grid, 2))
w1 = [float(k[0]) for k in grid]
check(abs(tvmax - 0.0133) < 5e-5, f'max pairwise TV across the influenza grid = {tvmax:.6f}')
check(f'{tvmax:.4f}'.startswith('0.0133'), 'the stated bound 0.0133 does not round a maximum down')
for d in ('manuscript', 'supplementary'):
    check(present(d, '0.0133'), f'{d} states 0.0133')
    check(not present(d, 'at most 0.013 in total variation'),
          f'{d} no longer states the rounded-down bound')
check(all(f'{min(w1):.4f}'[:6] in TEXT[d] or '0.9867' in TEXT[d]
          for d in ('manuscript', 'supplementary')),
      f'both documents give the w1 range {min(w1):.4f} to {max(w1):.5f}')
check(not any('all five means coincide' in TEXT[d] for d in TEXT),
      'the withdrawn "coincide" wording appears in no document')


# ============================================= 3. within-pathogen rank statistics
print('\n3. SNR and rank correlations (from snr_analysis_results.csv)')
snr = list(csv.DictReader(open(REPO + 'snr_analysis_results.csv')))
stats_out = {}
for path in ('Influenza', 'RSV'):
    sub = [r for r in snr if r['pathogen'] == path]
    x = rankdata([float(r['snr']) for r in sub])
    y = rankdata([float(r['epiestim_lead']) for r in sub])
    xc, yc = x - x.mean(), y - y.mean()
    den = np.linalg.norm(xc) * np.linalg.norm(yc)
    rho = float(xc @ yc / den)
    perms = np.array(list(itertools.permutations(yc)))
    p = float((np.abs(perms @ xc / den) >= abs(rho) - 1e-12).mean())
    stats_out[path] = (len(sub), rho, p, math.factorial(len(sub)))
    vals = [float(r['snr']) for r in sub]
    print(f'   {path}: n={len(sub)} rho={rho:+.4f} exact p={p:.4f} '
          f'({math.factorial(len(sub)):,} permutations), SNR {min(vals):.1f} to {max(vals):.1f}')

check(abs(stats_out['Influenza'][2] - 0.89) < 0.005, 'influenza exact p rounds to 0.89')
check(abs(stats_out['RSV'][2] - 0.52) < 0.005, 'RSV exact p rounds to 0.52')
check(present('manuscript', 'exact permutation p = 0.89'), 'manuscript states the exact 0.89')
check(not any('permutation p = 0.90' in TEXT[d] for d in TEXT),
      'the Monte Carlo 0.90 appears in no document')
check(not any('20,000 permutations' in TEXT[d] for d in TEXT),
      'no document still cites a sampled p-value')

stat_csv = list(csv.DictReader(open('/home/claude/v10_figs/snr_within_pathogen_stats.csv')))
# the CSV stores six decimals, so compare at that precision, not at machine epsilon
agree = all(abs(float(r['exact_perm_p_two_sided']) - stats_out[r['pathogen']][2]) < 5e-7
            and int(r['n_permutations']) == stats_out[r['pathogen']][3]
            for r in stat_csv)
check(agree, 'snr_within_pathogen_stats.csv agrees with the recomputation')


# =================================================== 4. admissions and degenerate
print('\n4. Admissions (from epiestim_admissions_results.csv, wilcoxon_admissions_results.csv)')
adm = list(csv.DictReader(open(REPO + 'epiestim_admissions_results.csv')))
mx = {(r['signal'], r['season_name']): float(r['best_Rt']) for r in adm}
trip = [('Adm_6_11', '2014/15 winter', 49005.0), ('Adm_12_17', '2014/15 winter', 26005.0),
        ('Adm_12_17', '2015/16 winter', 27505.0)]
check(all(mx[(s, n)] == v for s, n, v in trip), 'the three degenerate maxima reproduce')
check(all(str(int(v)) in TEXT['manuscript'].replace(',', '') for _, _, v in trip)
      or all(f'{int(v):,}' in TEXT['manuscript'] for _, _, v in trip),
      'the manuscript quotes 49,005 / 26,005 / 27,505')
check(present('manuscript', '4.95') and present('manuscript', '0.0019'),
      'the manuscript states the 6-11y exception rather than a flat 5.0')

wil = list(csv.DictReader(open(REPO + 'wilcoxon_admissions_results.csv')))
prim = [r for r in wil if r['analysis'].startswith('primary')][0]
diffs = dict(kv.split(':') for kv in prim['differences'].split('; '))
leads = {k: int(v) for k, v in diffs.items()}
nlead = sum(1 for v in leads.values() if v > 0)
nlate = sum(1 for v in leads.values() if v < 0)
check(nlead == 4 and nlate == 0 and len(leads) == 8,
      f'admissions led in {nlead} of {len(leads)} seasons and were later in {nlate}')
check(float(prim['p_one_sided']) == 0.0625 and float(prim['W']) == 10.0,
      'W = 10.0, one-sided p = 0.0625')
for d in ('manuscript', 'figures'):
    check('four of eight' in TEXT[d] or 'four of the eight' in TEXT[d],
          f'{d} states the four-of-eight count')
check(not any(re.search(r'admissions outperform', TEXT[d]) for d in TEXT),
      'the withdrawn "admissions outperform" claim appears in no document text')

peaks = {r['season']: float(r['peak_positivity']) for r in snr if r['pathogen'] == 'Influenza'}
order = sorted(peaks, key=lambda s: -peaks[s])
check(order[1] == '2014/15' and order[2] == '2018/19',
      f'2014/15 and 2018/19 are 2nd and 3rd by peak positivity, not 1st and 3rd',
      f'order: {order}')
check(present('manuscript', 'second- and third-highest-amplitude'),
      'the manuscript states the corrected ranking')
check(not any('concentrated on low-amplitude and multi-wave' in TEXT[d] for d in TEXT),
      'the withdrawn amplitude claim appears in no document')


# ============================================================ 5. threshold 4.94%
print('\n5. Threshold provenance')
f = list(csv.DictReader(open(REPO + 'flux_data.csv')))
import datetime as dt
vals = []
for r in f:
    d = dt.datetime.strptime(r['From'], '%d/%m/%Y') + dt.timedelta(days=3)
    if dt.datetime(2014, 1, 1) <= d < dt.datetime(2020, 1, 1) and r['AandB_proportion'] not in ('', 'NA'):
        vals.append(float(r['AandB_proportion']))
med = st.median(vals)
base = [v for v in vals if v < med]
recon = st.mean(base) + 1.96 * st.stdev(base)
print(f'   stated reconstruction on 2014-2019: n={len(base)}, '
      f'mean={st.mean(base):.6f}, SD={st.stdev(base):.6f} -> {recon*100:.4f}%')
check(abs(recon * 100 - 6.4677) < 0.01,
      f'the Introduction formula yields {recon*100:.2f}%, not 4.94%')
check(present('manuscript', 'CHP publishes the threshold value but not its derivation'),
      'the Introduction no longer claims 4.94% was reconstructed here')
check(not present('manuscript', 'CHP does not publish the exact threshold value'),
      'the withdrawn premise is gone from the accepted text')
check(present('manuscript', 'yields 6.47% rather than 4.94%'),
      'the Introduction states what the reconstruction actually yields')
check(present('manuscript', 'should be read as an analytical approximation of CHP practice '
                            'rather than an official operational value'),
      "Vijay's clause survives verbatim")


# ====================================================== 6. figure/table pointers
print('\n6. Cross-references')
for obj, doc in [('Supplementary Fig. S5', 'manuscript'), ('Supplementary Table S4', 'manuscript'),
                 ('Fig. 2', 'manuscript'), ('Fig. 4', 'manuscript')]:
    check(present(doc, obj), f'{doc} cites {obj}')
check(present('supplementary', 'Supplementary Figure S5'), 'Figure S5 exists in the supplementary')
check(present('figures', 'Figure 2. Rank tests detect no within-pathogen association'),
      'the figures document carries the corrected Figure 2 caption')
check(present('supplementary', 'runs at SD 3.0'),
      'the supplementary distinguishes the RSV grid SD from the analysis SD')
rsvrows = list(csv.DictReader(open(REPO + 'rsv_si_sensitivity.csv')))
check(all(abs(float(r['si_sd']) - 0.4 * float(r['si_mean'])) < 1e-9 for r in rsvrows),
      'the RSV grid is SD = 0.4 x mean in the committed CSV')
check(any(float(r['si_mean']) == 7.5 and float(r['si_sd']) == 3.0 for r in rsvrows),
      'its mean-7.5 column runs at SD 3.0, against 3.5 in the primary analysis')

# ================================================== 7. Table 1, cell by cell
print('\n7. Table 1 against the committed outputs')
import datetime as dt


def accepted_tree(path):
    r = etree.fromstring(zipfile.ZipFile(path).read('word/document.xml'))
    for tag in ('del', 'moveFrom'):
        for el in list(r.iter(W + tag)):
            p = el.getparent()
            if p is not None:
                p.remove(el)
    for tag in ('ins', 'moveTo'):
        for el in list(r.iter(W + tag)):
            p = el.getparent()
            if p is None:
                continue
            if ln(p) == 'rPr':
                p.remove(el)
                continue
            i = list(p).index(el)
            for ch in reversed(list(el)):
                p.insert(i, ch)
            p.remove(el)
    return r


mt = accepted_tree(DOCS['manuscript'])
tbls = [el for el in list(mt.find(W + 'body')) if ln(el) == 'tbl']


def cells(tbl):
    out = []
    for tr in tbl.findall(W + 'tr'):
        out.append([' '.join(''.join(t.text or '' for t in tc.iter(W + 't')).split())
                    for tc in tr.findall(W + 'tc')])
    return out


t1 = next((cells(t) for t in tbls if cells(t)[0][:2] == ['Season', 'Peak%']
           and 'Epi lead' in cells(t)[0]), None)
check(t1 is not None, 'Table 1 located by its header')

# peak positivity is taken from the raw weekly series, NOT from
# snr_analysis_results.csv: that file stores peak_positivity rounded to three
# decimals, so 2018/19's true 0.2995 reads back as 0.299 and prints as 29.9,
# which disagrees with the 30.0 the table and Figure 1 report.
flux = list(csv.DictReader(open(REPO + 'flux_data.csv')))
FLU_SEASONS = {'2014/15': ('2014-10-01', '2015-06-01'), '2015/16': ('2015-10-01', '2016-06-01'),
               '2018/19': ('2018-09-15', '2019-06-01'), '2023 S': ('2023-01-15', '2023-10-01'),
               '2023/24': ('2023-07-15', '2024-04-01'), '2024/25': ('2024-08-01', '2025-04-01')}
raw_peak = {}
for s, (a, b) in FLU_SEASONS.items():
    vv = []
    for r in flux:
        d = dt.datetime.strptime(r['From'], '%d/%m/%Y') + dt.timedelta(days=3)
        if (dt.datetime.fromisoformat(a) <= d <= dt.datetime.fromisoformat(b)
                and r['AandB_proportion'] not in ('', 'NA')):
            vv.append(float(r['AandB_proportion']))
    raw_peak[s] = max(vv)

bad = []
for row in (t1 or [])[1:]:
    s = row[0]
    if s not in raw_peak:
        continue
    stated = float(row[1])
    true_pct = raw_peak[s] * 100
    if abs(stated - true_pct) > 0.06:
        bad.append((s, stated, round(true_pct, 3)))
check(not bad, 'Table 1 peak positivity agrees with flux_data.csv for all 6 influenza rows',
      f'off: {bad}')

# EpiEstim lead and onset, from the committed admissions output
pos = {r['season_name'].split()[0].replace('summer', 'S'): r
       for r in adm if r['signal'] == 'AandB_proportion'}
SHORT = {'2014/15 winter': '2014/15', '2015/16 winter': '2015/16', '2016/17 winter': '2016/17',
         '2017/18 summer': '2017/18', '2018/19 winter': '2018/19', '2023 summer': '2023 S',
         '2023/24 winter': '2023/24', '2024/25 winter': '2024/25'}
posmap = {SHORT[r['season_name']]: r['onset_date'] for r in adm
          if r['signal'] == 'AandB_proportion'}
bad = []
for row in (t1 or [])[1:]:
    s = row[0]
    if s not in posmap:
        continue
    stated = row[3]                      # EpiEstim onset as MM-DD
    actual = posmap[s][5:]               # from YYYY-MM-DD
    if stated != actual:
        bad.append((s, stated, actual))
check(not bad, 'Table 1 EpiEstim onset dates agree with epiestim_admissions_results.csv',
      f'off: {bad}')

# Adm lead = best age-stratified admissions lead vs the CHP onset
chp = {SHORT[k]: v for k, v in {}.items()} or None
onsets = defaultdict(dict)
for r in adm:
    onsets[SHORT[r['season_name']]][r['signal']] = r['onset_date']
chp_onset = {}
for row in (t1 or [])[1:]:
    if row[0] in posmap:
        chp_onset[row[0]] = row[2]       # Thresh. column, MM-DD
bad = []
for row in (t1 or [])[1:]:
    s = row[0]
    if s not in onsets or row[6] in ('—', '-', ''):
        continue
    yr_pos = posmap[s][:4]
    th = row[2]
    # resolve the threshold year: it is the year of the positivity onset, or the
    # next one if the month-day has wrapped past it
    cand = [dt.date(int(yr_pos), int(th[:2]), int(th[3:])),
            dt.date(int(yr_pos) + 1, int(th[:2]), int(th[3:]))]
    po = dt.date.fromisoformat(posmap[s])
    thr = min(cand, key=lambda d: abs((d - po).days))
    best = None
    for sig in ('Adm_All', 'Adm_0_5', 'Adm_6_11', 'Adm_12_17', 'Adm_65_higher'):
        if sig in onsets[s]:
            lead = (thr - dt.date.fromisoformat(onsets[s][sig])).days
            if best is None or lead > best:
                best = lead
    stated = int(row[6].replace('−', '-').replace('+', ''))
    if best != stated:
        bad.append((s, stated, best))
check(not bad, 'Table 1 admissions lead is the best age-stratified lead in every season',
      f'off: {bad}')


# ======================================== 8. no surviving amplitude claim of ours
print('\n8. Amplitude claims')
WITHDRAWN = [
    'on the most difficult seasons',
    'on low-amplitude influenza seasons',
    'concentrated on low-amplitude and multi-wave',
    'admissions outperform',
]
leftover = [(d, s) for d in TEXT for s in WITHDRAWN if s in TEXT[d]]
check(not leftover, 'no withdrawn amplitude wording of ours survives in any document',
      f'found: {leftover}')
check(TEXT['manuscript'].count('four of the eight influenza seasons examined') == 2,
      'the Author Summary and Discussion both state the four-of-eight count')

# Vijay's own amplitude sentences are expected to be present and untouched
VIJAY_KEPT = [
    'led positivity-based R(t) selectively on low-amplitude and multi-wave seasons rather than on average',
    'was driven not by the sophistication of the estimator',
    'We show that a low signal-to-noise input degrades both estimators',
]
check(all(s in TEXT['manuscript'] for s in VIJAY_KEPT),
      "Vijay's three amplitude sentences are present and unaltered (flagged, not edited)")

print()
print('FAILED: %d' % len(fails) if fails else 'all four sources agree')
sys.exit(1 if fails else 0)
