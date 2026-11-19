"""Fig 3 redrawn for PLOS: no title inside the figure, panels lettered A and B.
Calculation copied unchanged from v10_build/make_v10_figs.py (Spearman rho, exact permutation p).
Run: python3 make_fig3_plos.py <data_dir> <out_dir>
"""
import itertools
import math
import os

import numpy as np, pandas as pd, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.labelsize':8.5,
 'axes.titlesize':12,'xtick.labelsize':7.5,'ytick.labelsize':7.5,'legend.fontsize':8,
 'figure.dpi':200,'savefig.dpi':300,'savefig.bbox':'tight',
 'axes.spines.top':False,'axes.spines.right':False})
FLU='#2166AC'; RSV='#D6604D'; GRAY='#999999'
INK='#222222'; MUTED='#666666'

HERE = os.path.dirname(os.path.abspath(__file__))
import sys
DATA, OUT = sys.argv[1], sys.argv[2]
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
fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.6), sharey=True)
stats = {}
for ax, (grp, col) in zip(axes, [('Influenza', FLU), ('RSV', RSV)]):
    sub = snr[snr.pathogen == grp]
    x = sub.snr.values; y = sub.epiestim_lead.values.astype(float)
    rho = spearman(x, y); p = perm_p(x, y)
    stats[grp] = (len(sub), rho, p)
    ax.axhline(0, color=GRAY, ls='--', lw=1, alpha=0.8, zorder=1)
    ax.scatter(x, y, s=80, c=col, edgecolors='white', linewidths=1.6, zorder=5,
               marker='s' if grp == 'Influenza' else 'o')
    ax.set_title(f"{'A' if grp == 'Influenza' else 'B'}  {grp} (n = {len(sub)})", fontweight='bold', fontsize=10, color=INK, loc='left')
    ax.set_xlabel('Signal-to-noise ratio\n(peak positivity / non-season SD)')
    ax.set_xlim(0, 30)
    ax.text(0.97, 0.05, f'Spearman $\\rho$ = {rho:+.2f}\nexact permutation $p$ = {p:.2f}',
            transform=ax.transAxes, ha='right', va='bottom', fontsize=7, color=MUTED,
            bbox=dict(boxstyle='round,pad=0.4', fc='white', ec=GRAY, lw=0.6, alpha=0.9))

# selective direct labels: only the two seasons that make the point
flu = snr[snr.pathogen == 'Influenza']
for season, tx, ty, ha in [('2017/18', 20.5, -62, 'center'), ('2024/25', 1.2, 93, 'left')]:
    r = flu[flu.season == season].iloc[0]
    axes[0].annotate(f'{season}: lowest SNR,\ndetected early ({int(r.epiestim_lead):+d} d)'
                     if season == '2024/25' else
                     f'{season}: highest SNR,\ndetected late ({int(r.epiestim_lead):+d} d)',
                     xy=(r.snr, r.epiestim_lead), xytext=(tx, ty),
                     fontsize=6.8, color=MUTED, ha=ha, va='center',
                     arrowprops=dict(arrowstyle='->', color=GRAY, lw=0.8,
                                     shrinkA=2, shrinkB=6,
                                     connectionstyle='arc3,rad=0.18'))

axes[0].set_ylabel('EpiEstim lead time (days)\n(positive = earlier than threshold)')
axes[0].set_ylim(-120, 110)
plt.tight_layout()
png=os.path.join(OUT,'Fig3.png'); plt.savefig(png); plt.close()
from PIL import Image
im=Image.open(png).convert('RGB'); im.save(os.path.join(OUT,'Fig3.tif'),format='TIFF',compression='tiff_lzw',dpi=(300,300))
w,h=im.size; print('Fig3',w,h,round(w/300*2.54,2),'cm'); assert w/300*2.54<=19.05
for g,(n_,rho,p) in stats.items(): print(g,n_,round(rho,3),round(p,4))
