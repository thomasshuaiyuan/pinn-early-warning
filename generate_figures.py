"""
Manuscript Figures — Publication Quality (Fixed)
==================================================
Fix: RSV_pct is already in percent, not multiplied by 100.

Run: conda activate pinn && python generate_figures.py
Requires: flux_data.csv, chp_respiratory_cleaned.csv

Thomas Yuan — HKU PhD, Pathogen Evolution Lab
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy.stats import gamma as gamma_dist
import warnings
warnings.filterwarnings("ignore")

plt.rcParams.update({
    'font.family': 'Arial',
    'font.size': 10,
    'axes.labelsize': 11,
    'axes.titlesize': 12,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 8,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'axes.spines.top': False,
    'axes.spines.right': False,
})

FLU_COLOR = '#2166AC'
RSV_COLOR = '#D6604D'
ADM_COLOR = '#4DAF4A'
THRESHOLD_COLOR = '#E31A1C'
GRAY = '#999999'

print("Loading data...")
df = pd.read_csv("flux_data.csv")
df["From"] = pd.to_datetime(df["From"], format="%d/%m/%Y")
df["To"] = pd.to_datetime(df["To"], format="%d/%m/%Y")
df["MidDate"] = df["From"] + (df["To"] - df["From"]) / 2
CHP_THRESHOLD = 0.0494

try:
    rsv_df = pd.read_csv("chp_respiratory_cleaned.csv")
    rsv_df["From"] = pd.to_datetime(rsv_df["From"])
    rsv_df["To"] = pd.to_datetime(rsv_df["To"])
    rsv_df["MidDate"] = rsv_df["From"] + (rsv_df["To"] - rsv_df["From"]) / 2
    has_rsv = True
except:
    has_rsv = False

def compute_epiestim_rt(incidence, si_mean=3.0, si_sd=1.5, window=4, time_unit=7.0):
    n = len(incidence)
    shape = (si_mean / si_sd) ** 2
    scale = si_sd ** 2 / si_mean
    si = np.zeros(n)
    for t in range(1, n):
        lo = (t - 0.5) * time_unit
        hi = (t + 0.5) * time_unit
        si[t] = gamma_dist.cdf(hi, a=shape, scale=scale) - gamma_dist.cdf(max(0, lo), a=shape, scale=scale)
    total = si.sum()
    if total > 0:
        si /= total
    lambdas = np.zeros(n)
    for t in range(1, n):
        for s in range(1, min(t + 1, n)):
            lambdas[t] += incidence[t - s] * si[s]
    rt_times, rt_vals = [], []
    for t in range(window, n):
        t_start = t - window + 1
        sum_I = np.sum(incidence[t_start:t + 1])
        sum_L = np.sum(lambdas[t_start:t + 1])
        if (0.2 + sum_L) > 0:
            rt_times.append(t)
            rt_vals.append((1.0 + sum_I) / (0.2 + sum_L))
    return rt_times, rt_vals

# ============================================================
# FIGURE 1
# ============================================================
print("Generating Figure 1: R(t) trajectories...")
fig, axes = plt.subplots(1, 3, figsize=(14, 4))

panels = [
    ("2018/19 influenza\n(high amplitude, peak 30%)",
     "2018-09-15", "2019-06-01", df, "AandB_proportion",
     CHP_THRESHOLD, 3.0, 1.5, FLU_COLOR, False),
    ("2024/25 influenza\n(post-COVID, peak 10.5%)",
     "2024-08-01", "2025-04-01", df, "AandB_proportion",
     CHP_THRESHOLD, 3.0, 1.5, FLU_COLOR, False),
]
if has_rsv:
    panels.append(
        ("2017 RSV\n(low amplitude, peak 9.9%)",
         "2017-01-01", "2017-12-01", rsv_df, "RSV_pct",
         1.87, 7.5, 3.5, RSV_COLOR, True)
    )

for idx, panel in enumerate(panels):
    title, start, end, source, signal_col, threshold, si_mean, si_sd, color, is_pct = panel
    ax = axes[idx]
    mask = (source["MidDate"] >= start) & (source["MidDate"] <= end)
    season = source.loc[mask].dropna(subset=[signal_col]).sort_values("MidDate")
    if len(season) < 10:
        ax.text(0.5, 0.5, "Insufficient data", ha='center', va='center', transform=ax.transAxes)
        ax.set_title(title)
        continue
    dates = season["MidDate"].values
    positivity = season[signal_col].values
    if is_pct:
        pos_display = positivity
        thresh_display = threshold
        incidence = (positivity / 100 * 10000).astype(float)
    else:
        pos_display = positivity * 100
        thresh_display = threshold * 100
        incidence = (positivity * 10000).astype(float)
    incidence = np.maximum(incidence, 0)
    rt_idx, rt_vals = compute_epiestim_rt(incidence, si_mean=si_mean, si_sd=si_sd)
    rt_dates = dates[rt_idx]
    ax2 = ax.twinx()
    ax.fill_between(dates, pos_display, alpha=0.15, color=color)
    ax.plot(dates, pos_display, color=color, linewidth=1.5, label='Lab positivity')
    ax.axhline(y=thresh_display, color=THRESHOLD_COLOR, linestyle='--', linewidth=1, alpha=0.7, label='Threshold')
    ax2.plot(rt_dates, rt_vals, color='black', linewidth=1.5, label='R(t)')
    ax2.axhline(y=1.0, color='black', linestyle=':', linewidth=0.8, alpha=0.5)
    ax2.set_ylim(0, max(3, max(rt_vals) * 1.1) if rt_vals else 3)
    ax.set_title(title, fontweight='bold', fontsize=10)
    ax.set_ylabel('Positivity (%)')
    ax2.set_ylabel('R(t)')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b\n%Y'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    if idx == 0:
        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left', framealpha=0.9)

if not has_rsv:
    axes[2].text(0.5, 0.5, "RSV data not available", ha='center', va='center', transform=axes[2].transAxes)
    axes[2].set_title("2017 RSV")
plt.tight_layout()
plt.savefig("fig1_rt_trajectories.png")
plt.savefig("fig1_rt_trajectories.pdf")
print("  Saved: fig1_rt_trajectories.png/pdf")
plt.close()

# ============================================================
# FIGURE 2
# ============================================================
print("Generating Figure 2: Signal amplitude scatter...")
fig, ax = plt.subplots(figsize=(7, 5))
flu_peaks = [38.6, 25.7, 15.6, 40.6, 29.9, 18.2, 14.9, 10.5]
flu_leads = [35, 70, -98, -28, 28, 35, -28, 49]
rsv_peaks = [7.3, 5.4, 5.0, 9.9, 6.2, 3.8, 12.4, 10.1, 8.3, 3.5]
rsv_leads = [35, -21, -28, -28, -14, -28, 49, 133, -28, 91]
ax.scatter(flu_peaks, flu_leads, c=FLU_COLOR, s=80, marker='s', label='Influenza', edgecolors='black', linewidth=0.5, zorder=5)
ax.scatter(rsv_peaks, rsv_leads, c=RSV_COLOR, s=80, marker='o', label='RSV', edgecolors='black', linewidth=0.5, zorder=5)
ax.axhline(y=0, color=GRAY, linestyle='--', linewidth=1, alpha=0.7)
ax.axvspan(0, 10, alpha=0.06, color=RSV_COLOR, label='Peak < 10%')
notable = [
    (10.5, 49, '2024/25', FLU_COLOR, (-15, 10)),
    (12.4, 49, '2021/22', RSV_COLOR, (10, 5)),
    (10.1, 133, '2022/23', RSV_COLOR, (10, -5)),
    (40.6, -28, '2017/18\n(multi-wave)', FLU_COLOR, (10, -10)),
]
for x_, y_, label, color, offset in notable:
    ax.annotate(label, (x_, y_), xytext=offset, textcoords='offset points', fontsize=7, color=color, ha='center')
ax.set_xlabel('Peak season positivity (%)')
ax.set_ylabel('EpiEstim lead time (days)\n(positive = earlier than threshold)')
ax.set_xlim(0, 45)
ax.set_ylim(-120, 150)
ax.legend(loc='upper left', framealpha=0.9)
ax.set_title('Signal amplitude predicts R(t) method performance', fontweight='bold')
plt.tight_layout()
plt.savefig("fig2_signal_amplitude.png")
plt.savefig("fig2_signal_amplitude.pdf")
print("  Saved: fig2_signal_amplitude.png/pdf")
plt.close()

# ============================================================
# FIGURE 3
# ============================================================
print("Generating Figure 3: Pre-onset signals...")
fig, ax = plt.subplots(figsize=(8, 4.5))
signals = [
    ('Admissions 6-11y', 242, 0.62),
    ('Admissions 65+', 230, 0.86),
    ('Admissions all ages', 218, 0.84),
    ('Admissions 0-5y', 206, 0.79),
    ('School outbreaks', 102, 0.37),
    ('A&E ILI rate', 19, 0.71),
    ('GP ILI rate', 12, 0.66),
    ('Kindergarten fever', 2, 0.49),
    ('Care home fever', -5, 0.11),
]
names = [s[0] for s in signals]
vals = [s[1] for s in signals]
corrs = [s[2] for s in signals]
colors = [ADM_COLOR if c > 100 else ('#FFB347' if c > 10 else GRAY) for c in vals]
y_pos = range(len(names))
ax.barh(y_pos, vals, color=colors, edgecolor='white', height=0.7)
for i, (v, c) in enumerate(zip(vals, corrs)):
    ax.text(max(v + 8, 15), i, f'r = {c:.2f}', va='center', fontsize=8, color=GRAY)
ax.set_yticks(y_pos)
ax.set_yticklabels(names)
ax.set_xlabel('Pre-onset change (%)\n(8 weeks before CHP threshold crossing, averaged across 5 single-wave seasons)')
ax.set_title('Hospital admissions surge before lab positivity crosses threshold', fontweight='bold')
ax.invert_yaxis()
ax.axvline(x=0, color='black', linewidth=0.5)
plt.tight_layout()
plt.savefig("fig3_preonset_signals.png")
plt.savefig("fig3_preonset_signals.pdf")
print("  Saved: fig3_preonset_signals.png/pdf")
plt.close()

# ============================================================
# FIGURE 4
# ============================================================
print("Generating Figure 4: Admissions vs positivity comparison...")
fig, ax = plt.subplots(figsize=(9, 5))
seasons = ['2014/15', '2015/16', '2016/17', '2017/18', '2018/19', '2023 S', '2023/24', '2024/25']
pos_leads = [35, 70, -98, -28, 28, 35, -28, 49]
adm_12_17 = [56, 70, -56, -28, 49, 35, -28, 112]
adm_6_11 = [42, 42, -42, -28, 49, 35, -28, 119]
x = np.arange(len(seasons))
width = 0.25
ax.bar(x - width, pos_leads, width, label='Lab positivity', color=FLU_COLOR, alpha=0.8)
ax.bar(x, adm_12_17, width, label='12-17y admissions', color=ADM_COLOR, alpha=0.8)
ax.bar(x + width, adm_6_11, width, label='6-11y admissions', color='#FF7F00', alpha=0.8)
ax.axhline(y=0, color='black', linewidth=0.8)
ax.set_xticks(x)
ax.set_xticklabels(seasons, rotation=30, ha='right')
ax.set_ylabel('Lead time vs CHP threshold (days)\n(positive = earlier detection)')
ax.set_title('Age-stratified admissions outperform lab positivity on difficult seasons', fontweight='bold')
ax.legend(loc='upper left', framealpha=0.9)
for i in [2, 3, 6]:
    ax.axvspan(i - 0.4, i + 0.4, alpha=0.05, color='red')
ax.annotate('+63d', xy=(7, 112), xytext=(6.3, 130), arrowprops=dict(arrowstyle='->', color=GRAY), fontsize=8, color=ADM_COLOR)
ax.annotate('+70d', xy=(7.25, 119), xytext=(7.2, 140), fontsize=8, color='#FF7F00')
plt.tight_layout()
plt.savefig("fig4_admissions_comparison.png")
plt.savefig("fig4_admissions_comparison.pdf")
print("  Saved: fig4_admissions_comparison.png/pdf")
plt.close()

print(f"\n{'='*50}")
print("ALL FIGURES GENERATED")
print(f"{'='*50}")
