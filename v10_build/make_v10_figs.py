"""
Proposed v10 figures. Palette, fonts and rcParams copied from generate_figures.py
so these sit beside the unchanged Figs 1, 3 and 4.

Fig 2 (replacement) : SNR vs EpiEstim lead, faceted by pathogen.
Fig S5 (new)        : what weekly discretisation does to each serial interval.

--------------------------------------------------------------------------------
REVISED 26 October 2026, after an independent audit found that this script as
preserved would NOT regenerate the figure that shipped in v10. Three mechanical
defects, no change to any reported quantity:

  1. The permutation p was a Monte Carlo estimate (n = 20,000, seed 0) returning
     0.897 and 0.520, which render as 0.90 and 0.52. The shipped figure carries
     the EXACT p, 0.8946 and 0.5161, rendering as 0.89 and 0.52. The exact test
     is now computed here by full enumeration -- 8! = 40,320 and 10! = 3,628,800
     -- so the script reproduces the artefact instead of a near-miss of it. The
     seed is no longer part of any reported number.
  2. scipy was imported for the gamma distribution while the header claimed no
     scipy dependency. The analysis machine has no scipy, so the chain could not
     run where the data lives. The regularised incomplete gamma is now computed
     from the standard library, and a self-check at import asserts it reproduces
     the four published discretisation figures.
  3. Input and output paths were hardcoded to a cloud container. They are now
     taken from V10_DATA and V10_OUT, defaulting to this script's directory.

Run:  V10_DATA=/path/to/pinn-early-warning V10_OUT=/tmp/figs python3 make_v10_figs.py
--------------------------------------------------------------------------------
"""
import itertools
import math
import os

import numpy as np, pandas as pd, matplotlib.pyplot as plt

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.labelsize':11,
 'axes.titlesize':12,'xtick.labelsize':9,'ytick.labelsize':9,'legend.fontsize':8,
 'figure.dpi':200,'savefig.dpi':300,'savefig.bbox':'tight',
 'axes.spines.top':False,'axes.spines.right':False})
FLU='#2166AC'; RSV='#D6604D'; GRAY='#999999'
INK='#222222'; MUTED='#666666'

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get('V10_DATA', HERE)
OUT  = os.environ.get('V10_OUT', HERE)
os.makedirs(OUT, exist_ok=True)

snr = pd.read_csv(os.path.join(DATA, 'snr_analysis_results.csv'))


# ---------- gamma distribution, standard library only ----------
def _gammainc_reg(a, x):
    """Regularised lower incomplete gamma P(a, x). Series below a+1, continued
    fraction above, after Numerical Recipes; both converge to ~1e-15 here."""
    if x < 0 or a <= 0:
        raise ValueError('gammainc domain')
    if x == 0:
        return 0.0
    gln = math.lgamma(a)
    if x < a + 1.0:
        ap = a; s = 1.0 / a; d = s
        for _ in range(500):
            ap += 1.0; d *= x / ap; s += d
            if abs(d) < abs(s) * 1e-16:
                break
        return s * math.exp(-x + a * math.log(x) - gln)
    b = x + 1.0 - a; c = 1e300; d = 1.0 / b; h = d
    for i in range(1, 500):
        an = -i * (i - a)
        b += 2.0; d = an * d + b
        if abs(d) < 1e-300: d = 1e-300
        c = b + an / c
        if abs(c) < 1e-300: c = 1e-300
        d = 1.0 / d; de = d * c; h *= de
        if abs(de - 1.0) < 1e-16:
            break
    return 1.0 - math.exp(-x + a * math.log(x) - gln) * h


def gamma_cdf(x, a, scale):
    return _gammainc_reg(a, x / scale)


def gamma_pdf(x, a, scale):
    x = np.asarray(x, float)
    return np.exp((a - 1) * np.log(x) - x / scale - a * math.log(scale) - math.lgamma(a))


# ---------- rank correlation + EXACT permutation p, no scipy dependency ----------
def rankdata(v):
    v = np.asarray(v, float); order = np.argsort(v, kind='mergesort'); r = np.empty(len(v))
    i = 0
    while i < len(v):
        j = i
        while j+1 < len(v) and v[order[j+1]] == v[order[i]]: j += 1
        r[order[i:j+1]] = (i+j)/2 + 1
        i = j+1
    return r
def spearman(x, y):
    rx, ry = rankdata(x), rankdata(y)
    return float(np.corrcoef(rx, ry)[0,1])
def perm_p(x, y, max_exact=10):
    """Two-sided permutation p for Spearman's rho.

    Exhaustive for n <= max_exact, so the returned value is the exact p and not
    an estimate: no seed, no draw-to-draw variation. Ranks are averaged over
    ties, which is why the correlation is recomputed from the rank-Pearson
    identity rather than from the no-ties d-squared formula. Falls back to a
    seeded Monte Carlo above max_exact, which this manuscript never reaches
    (n = 8 and n = 10)."""
    n = len(x)
    obs = abs(spearman(x, y))
    rx, ry = rankdata(x), rankdata(y)
    if n > max_exact:
        rng = np.random.default_rng(0)
        N = 20000
        c = sum(abs(spearman(x, rng.permutation(np.asarray(y, float)))) >= obs - 1e-12
                for _ in range(N))
        return (c + 1) / (N + 1)
    mx, my = rx.mean(), ry.mean(); sx, sy = rx.std(), ry.std()
    rxl = rx.tolist(); thr = obs - 1e-12
    c = 0; tot = 0
    for perm in itertools.permutations(ry.tolist()):
        d = 0.0
        for a_, b_ in zip(rxl, perm):
            d += a_ * b_
        tot += 1
        if abs((d / n - mx * my) / (sx * sy)) >= thr:
            c += 1
    return c / tot


# =====================================================================
# FIGURE 2 (replacement)
# =====================================================================
fig, axes = plt.subplots(1, 2, figsize=(9.0, 4.3), sharey=True)
stats = {}
for ax, (grp, col) in zip(axes, [('Influenza', FLU), ('RSV', RSV)]):
    sub = snr[snr.pathogen == grp]
    x = sub.snr.values; y = sub.epiestim_lead.values.astype(float)
    rho = spearman(x, y); p = perm_p(x, y)
    stats[grp] = (len(sub), rho, p)
    ax.axhline(0, color=GRAY, ls='--', lw=1, alpha=0.8, zorder=1)
    ax.scatter(x, y, s=80, c=col, edgecolors='white', linewidths=1.6, zorder=5,
               marker='s' if grp == 'Influenza' else 'o')
    ax.set_title(f'{grp}  (n = {len(sub)})', fontweight='bold', fontsize=10.5, color=INK)
    ax.set_xlabel('Signal-to-noise ratio\n(peak positivity / non-season SD)')
    ax.set_xlim(0, 30)
    ax.text(0.97, 0.05, f'Spearman $\\rho$ = {rho:+.2f}\nexact permutation $p$ = {p:.2f}',
            transform=ax.transAxes, ha='right', va='bottom', fontsize=8.5, color=MUTED,
            bbox=dict(boxstyle='round,pad=0.4', fc='white', ec=GRAY, lw=0.6, alpha=0.9))

# selective direct labels: only the two seasons that make the point
flu = snr[snr.pathogen == 'Influenza']
for season, tx, ty, ha in [('2017/18', 20.5, -62, 'center'), ('2024/25', 4.0, 86, 'center')]:
    r = flu[flu.season == season].iloc[0]
    axes[0].annotate(f'{season}: lowest SNR,\nearliest detection ({int(r.epiestim_lead):+d} d)'
                     if season == '2024/25' else
                     f'{season}: highest SNR,\ndetected late ({int(r.epiestim_lead):+d} d)',
                     xy=(r.snr, r.epiestim_lead), xytext=(tx, ty),
                     fontsize=7.8, color=MUTED, ha=ha, va='center',
                     arrowprops=dict(arrowstyle='->', color=GRAY, lw=0.8,
                                     shrinkA=2, shrinkB=6,
                                     connectionstyle='arc3,rad=0.18'))

axes[0].set_ylabel('EpiEstim lead time (days)\n(positive = earlier than threshold)')
axes[0].set_ylim(-120, 110)
fig.suptitle('Signal-to-noise ratio does not predict R(t) lead time within either pathogen',
             fontweight='bold', fontsize=11.5, y=1.02, color=INK)
plt.tight_layout()
plt.savefig(os.path.join(OUT, 'fig2_snr_within_pathogen.png'))
plt.savefig(os.path.join(OUT, 'fig2_snr_within_pathogen.pdf'))
plt.close()

# =====================================================================
# FIGURE S5 (new) : weekly discretisation of the serial interval
# =====================================================================
def discretise(mean_si, sd_si, max_t=12, tu=7.0):
    shape = (mean_si/sd_si)**2; scale = sd_si**2/mean_si
    w = np.zeros(max_t)
    for t in range(1, max_t):
        w[t] = (gamma_cdf((t+.5)*tu, a=shape, scale=scale)
                - gamma_cdf(max(0, (t-.5)*tu), a=shape, scale=scale))
    dropped = 1 - w.sum()
    n = w / w.sum()
    eff = sum(t*n[t] for t in range(max_t)) * 7
    return shape, scale, w, n, dropped, eff

PATH = [('Influenza', 3.0, 1.5, FLU), ('RSV', 7.5, 3.5, RSV)]

# Self-check: the stdlib gamma must reproduce the four published figures that
# Figure S5 and the Methods both report. Fails loudly rather than drawing a
# figure that disagrees with the text.
for _name, _m, _s, _ in PATH:
    _, _, _w, _n, _dropped, _eff = discretise(_m, _s)
    _want = {'Influenza': (0.685, 0.9985, 7.01), 'RSV': (0.099, 0.8002, 8.50)}[_name]
    assert abs(_dropped - _want[0]) < 5e-4, (_name, 'dropped', _dropped)
    assert abs(_n[1]  - _want[1]) < 5e-4, (_name, 'w1', _n[1])
    assert abs(_eff   - _want[2]) < 5e-3, (_name, 'effective mean', _eff)

fig, axes = plt.subplots(1, 2, figsize=(10.4, 4.3))
xs = np.linspace(0.01, 28, 800)

axA = axes[0]
for name, m, s, col in PATH:
    shape, scale, w, n, dropped, eff = discretise(m, s)
    pdf = gamma_pdf(xs, shape, scale)
    axA.plot(xs, pdf, color=col, lw=2, label=f'{name}: mean {m} d, SD {s} d', zorder=4)
    axA.fill_between(xs[xs < 3.5], pdf[xs < 3.5], color=col, alpha=0.28, lw=0, zorder=3)
axA.axvline(3.5, color=GRAY, ls='--', lw=1.2, zorder=2)
axA.set_ylim(0, 0.345); axA.set_xlim(0, 28)
axA.annotate('68.5% of the influenza\ndistribution is discarded',
             xy=(2.3, 0.14), xytext=(8.2, 0.205), fontsize=8.2, color=FLU, va='center',
             arrowprops=dict(arrowstyle='->', color=FLU, lw=0.9, shrinkB=2))
axA.annotate('9.9% of the RSV\ndistribution is discarded',
             xy=(3.0, 0.022), xytext=(14.5, 0.095), fontsize=8.2, color=RSV, va='center',
             arrowprops=dict(arrowstyle='->', color=RSV, lw=0.9, shrinkB=2))
axA.text(4.0, 0.258, 'first bin edge: 3.5 d', fontsize=8, color=MUTED, va='top')
axA.set_xlabel('Serial interval (days)'); axA.set_ylabel('Probability density')
axA.legend(loc='upper right', framealpha=0.95, borderpad=0.6)
axA.set_title('a   As specified in Methods',
              fontweight='bold', fontsize=10, loc='left', color=INK)

axB = axes[1]; width = 0.38; weeks = np.arange(1, 6)
for k, (name, m, s, col) in enumerate(PATH):
    _, _, w, n, dropped, eff = discretise(m, s)
    axB.bar(weeks + (k-0.5)*width, n[1:6], width*0.92, color=col,
            label=f'{name}: effective mean {eff:.2f} d', edgecolor='white', linewidth=1.2)
    axB.text(1 + (k-0.5)*width, n[1]+0.025, f'{n[1]:.3f}', ha='center', fontsize=8.2, color=MUTED)
axB.set_xticks(weeks); axB.set_xlabel('Weeks since infection of the index case')
axB.set_ylabel('Discretised weight (renormalised)')
axB.set_ylim(0, 1.18); axB.legend(loc='upper right', framealpha=0.95, borderpad=0.6)
axB.set_title('b   After weekly discretisation',
              fontweight='bold', fontsize=10, loc='left', color=INK)
plt.tight_layout()
plt.savefig(os.path.join(OUT, 'figS5_si_discretisation.png'))
plt.savefig(os.path.join(OUT, 'figS5_si_discretisation.pdf'))
plt.close()

# The figure annotation is not a citable record, so the statistics behind it are
# written out as a file the manuscript can name. The p-values are exact: every
# permutation of the rank vector is enumerated, 40,320 for influenza and
# 3,628,800 for RSV, so there is no seed and no draw-to-draw variation to record.
import csv as _csv
STATS_OUT = os.path.join(OUT, 'snr_within_pathogen_stats.csv')
with open(STATS_OUT, 'w', newline='') as fh:
    wr = _csv.writer(fh)
    wr.writerow(['pathogen', 'n_seasons', 'spearman_rho', 'perm_p_two_sided',
                 'p_method', 'n_permutations', 'source', 'script'])
    for g, (n_, rho, p) in stats.items():
        wr.writerow([g, n_, f'{rho:.3f}', f'{p:.4f}', 'exact enumeration',
                     math.factorial(n_), 'snr_analysis_results.csv', 'make_v10_figs.py'])
print('wrote', STATS_OUT)

print('Fig 2 within-pathogen statistics')
for g, (n_, rho, p) in stats.items():
    print(f'   {g:10} n={n_:2d}  rho={rho:+.3f}  exact p={p:.4f}  ({math.factorial(n_):,} permutations)')
print('\nFig S5 discretisation table')
print(f"   {'pathogen':10} {'stated':>8} {'dropped':>9} {'w[1]':>8} {'effective':>10}")
for name, m, s, _ in PATH:
    _, _, w, n, dropped, eff = discretise(m, s)
    print(f'   {name:10} {m:7.1f}d {dropped*100:8.1f}% {n[1]:8.4f} {eff:9.2f}d')
