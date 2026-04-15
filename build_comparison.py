"""
Four-Method Comparison: PINN vs EpiEstim vs CHP Threshold vs ML
================================================================
Merges results from:
  1. SEIR-PINN R(t) onset detection (validation_results.csv)
  2. EpiEstim R(t) onset detection (epiestim_results.csv)
  3. CHP static threshold (computed from flux_data.csv)
  4. P8451 ML models (manual input from coursework results)

Outputs:
  - comparison_table.csv  (Table 1 of the paper)
  - comparison_figure.png (Figure: onset timing across methods and seasons)

Run: python3 build_comparison.py

Thomas Yuan — HKU PhD, Pathogen Evolution Lab
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# LOAD ALL RESULTS
# ============================================================

print("=" * 80)
print("FOUR-METHOD COMPARISON: Influenza Season Onset Detection")
print("Hong Kong CHP Flu Express 2014-2026")
print("=" * 80)

# --- EpiEstim ---
epi = pd.read_csv('epiestim_results.csv')
print(f"\nEpiEstim: {len(epi)} seasons loaded")

# --- PINN ---
try:
    pinn = pd.read_csv('validation_results.csv')
    print(f"PINN: {len(pinn)} seasons loaded")
    has_pinn = True
except FileNotFoundError:
    print("PINN: validation_results.csv NOT FOUND — will show EpiEstim + CHP only")
    has_pinn = False

# --- CHP raw data (for plotting) ---
df = pd.read_csv('flux_data.csv')
df['From'] = pd.to_datetime(df['From'], format='%d/%m/%Y')
df['To'] = pd.to_datetime(df['To'], format='%d/%m/%Y')
df['MidDate'] = df['From'] + (df['To'] - df['From']) / 2

CHP_THRESHOLD = 0.0494

# ============================================================
# MERGE INTO COMPARISON TABLE
# ============================================================

# Canonical season list (from PINN or EpiEstim)
if has_pinn:
    seasons = pinn[['season_name', 'n_weeks', 'peak_positivity',
                     'pinn_onset_date', 'chp_onset_date', 'lead_days',
                     'best_Rt']].copy()
    seasons.columns = ['season', 'n_weeks', 'peak_pct',
                        'pinn_onset', 'chp_onset', 'pinn_lead_days',
                        'pinn_Rt_max']
else:
    seasons = epi[['season_name', 'n_weeks', 'peak_positivity',
                    'chp_onset']].copy()
    seasons.columns = ['season', 'n_weeks', 'peak_pct', 'chp_onset']
    seasons['pinn_onset'] = None
    seasons['pinn_lead_days'] = None
    seasons['pinn_Rt_max'] = None

# Merge EpiEstim columns
epi_merge = epi[['season_name', 'epiestim_onset', 'epiestim_onset_strict',
                  'lead_days', 'best_Rt']].copy()
epi_merge.columns = ['season', 'epiestim_onset', 'epiestim_onset_strict',
                      'epiestim_lead_days', 'epiestim_Rt_max']

merged = seasons.merge(epi_merge, on='season', how='outer')

# Compute EpiEstim lead over CHP (if not already)
for idx, row in merged.iterrows():
    if pd.notna(row.get('epiestim_onset')) and pd.notna(row.get('chp_onset')):
        epi_dt = pd.to_datetime(row['epiestim_onset'])
        chp_dt = pd.to_datetime(row['chp_onset'])
        merged.loc[idx, 'epiestim_lead_days'] = (chp_dt - epi_dt).days

# ============================================================
# PRINT COMPARISON TABLE
# ============================================================

print(f"\n\n{'='*120}")
print("TABLE 1: Multi-Method Influenza Season Onset Detection — Hong Kong 2014–2025")
print(f"{'='*120}")

header = (f"{'Season':<18} {'Peak%':>6} "
          f"{'CHP Onset':>12} "
          f"{'PINN Onset':>12} {'PINN Lead':>10} "
          f"{'EpiEstim':>12} {'Epi Lead':>10} "
          f"{'PINN R(t)':>9} {'Epi R(t)':>9}")
print(header)
print("-" * 120)

for _, r in merged.iterrows():
    chp = r['chp_onset'] if pd.notna(r.get('chp_onset')) else 'N/A'
    
    pinn_o = r.get('pinn_onset', None)
    pinn_o = pinn_o if pd.notna(pinn_o) and pinn_o is not None else 'N/A'
    
    pinn_ld = r.get('pinn_lead_days', None)
    pinn_ld_str = f"{int(pinn_ld)}d" if pd.notna(pinn_ld) and pinn_ld is not None else 'N/A'
    
    epi_o = r.get('epiestim_onset', None)
    epi_o = epi_o if pd.notna(epi_o) and epi_o is not None else 'N/A'
    
    epi_ld = r.get('epiestim_lead_days', None)
    epi_ld_str = f"{int(epi_ld)}d" if pd.notna(epi_ld) and epi_ld is not None else 'N/A'
    
    pinn_rt = r.get('pinn_Rt_max', None)
    pinn_rt_str = f"{pinn_rt:.3f}" if pd.notna(pinn_rt) and pinn_rt is not None else 'N/A'
    
    epi_rt = r.get('epiestim_Rt_max', None)
    epi_rt_str = f"{epi_rt:.3f}" if pd.notna(epi_rt) and epi_rt is not None else 'N/A'
    
    print(f"{r['season']:<18} {r['peak_pct']:>5.1f}% "
          f"{chp:>12} "
          f"{pinn_o:>12} {pinn_ld_str:>10} "
          f"{epi_o:>12} {epi_ld_str:>10} "
          f"{pinn_rt_str:>9} {epi_rt_str:>9}")

# Summary statistics
print(f"\n{'='*80}")
print("SUMMARY STATISTICS")
print(f"{'='*80}")

for method, col in [('PINN', 'pinn_lead_days'), ('EpiEstim', 'epiestim_lead_days')]:
    valid = merged[col].dropna()
    if len(valid) > 0:
        print(f"\n  {method} vs CHP ({len(valid)} seasons):")
        print(f"    Mean lead:    {valid.mean():>6.1f} days")
        print(f"    Median lead:  {valid.median():>6.1f} days")
        print(f"    Range:        {valid.min():.0f} to {valid.max():.0f} days")
        leads = (valid > 0).sum()
        print(f"    Method leads: {leads}/{len(valid)} seasons")

# Save
merged.to_csv('comparison_table.csv', index=False)
print(f"\n\nTable saved to comparison_table.csv")

# ============================================================
# FIGURE 1: ONSET TIMELINE COMPARISON
# ============================================================

print("\nGenerating figures...")

fig, ax = plt.subplots(figsize=(14, 7))
fig.suptitle('Influenza Season Onset Detection: PINN vs EpiEstim vs CHP Threshold\n'
             'Hong Kong CHP Flu Express 2014–2025',
             fontsize=13, fontweight='bold')

season_labels = merged['season'].tolist()
y_positions = np.arange(len(season_labels))

# Plot CHP onset dates as reference
chp_dates = []
for _, r in merged.iterrows():
    if pd.notna(r.get('chp_onset')) and r['chp_onset'] != 'N/A':
        chp_dates.append(pd.to_datetime(r['chp_onset']))
    else:
        chp_dates.append(None)

# For each season, plot relative to CHP onset (= day 0)
# Positive = method detects BEFORE CHP (good)
# Negative = method detects AFTER CHP

bar_data = []
for i, (_, r) in enumerate(merged.iterrows()):
    entry = {'season': r['season'], 'y': i}
    
    pinn_ld = r.get('pinn_lead_days', None)
    if pd.notna(pinn_ld) and pinn_ld is not None:
        entry['pinn'] = float(pinn_ld)
    else:
        entry['pinn'] = None
    
    epi_ld = r.get('epiestim_lead_days', None)
    if pd.notna(epi_ld) and epi_ld is not None:
        entry['epi'] = float(epi_ld)
    else:
        entry['epi'] = None
    
    bar_data.append(entry)

# Horizontal bar chart: lead time relative to CHP
bar_height = 0.3
for entry in bar_data:
    y = entry['y']
    
    if entry.get('pinn') is not None:
        color = '#2196F3' if entry['pinn'] >= 0 else '#BBDEFB'
        ax.barh(y + bar_height/2, entry['pinn'], height=bar_height,
                color=color, edgecolor='#1565C0', linewidth=0.5,
                label='PINN lead' if y == 0 else '')
        ax.text(entry['pinn'] + (2 if entry['pinn'] >= 0 else -2), y + bar_height/2,
                f"{entry['pinn']:.0f}d", va='center',
                ha='left' if entry['pinn'] >= 0 else 'right',
                fontsize=8, color='#1565C0')
    
    if entry.get('epi') is not None:
        color = '#FF9800' if entry['epi'] >= 0 else '#FFE0B2'
        ax.barh(y - bar_height/2, entry['epi'], height=bar_height,
                color=color, edgecolor='#E65100', linewidth=0.5,
                label='EpiEstim lead' if y == 0 else '')
        ax.text(entry['epi'] + (2 if entry['epi'] >= 0 else -2), y - bar_height/2,
                f"{entry['epi']:.0f}d", va='center',
                ha='left' if entry['epi'] >= 0 else 'right',
                fontsize=8, color='#E65100')

ax.axvline(x=0, color='red', linewidth=2, linestyle='-', label='CHP threshold onset')
ax.set_yticks(y_positions)
ax.set_yticklabels(season_labels)
ax.set_xlabel('Lead time vs CHP threshold (days)\n← Method detects AFTER CHP    |    Method detects BEFORE CHP →',
              fontsize=10)
ax.set_title('')

# De-duplicate legend
handles, labels = ax.get_legend_handles_labels()
by_label = dict(zip(labels, handles))
ax.legend(by_label.values(), by_label.keys(), loc='lower right', fontsize=9)

ax.grid(True, axis='x', alpha=0.3)
ax.set_xlim(min(-40, merged[['pinn_lead_days', 'epiestim_lead_days']].min().min() - 10),
            max(80, merged[['pinn_lead_days', 'epiestim_lead_days']].max().max() + 10))

plt.tight_layout()
plt.savefig('comparison_onset_timeline.png', dpi=150, bbox_inches='tight')
print("  Saved: comparison_onset_timeline.png")


# ============================================================
# FIGURE 2: SURVEILLANCE DATA + ONSET MARKERS PER SEASON
# ============================================================

# Season windows for plotting (wider than analysis windows)
PLOT_SEASONS = [
    ("2014/15 winter", "2014-09-01", "2015-07-01"),
    ("2015/16 winter", "2015-09-01", "2016-07-01"),
    ("2016/17 winter", "2016-08-01", "2017-07-01"),
    ("2017/18 summer", "2017-03-01", "2018-05-01"),
    ("2018/19 winter", "2018-08-01", "2019-07-01"),
    ("2023 summer",    "2023-01-01", "2023-11-01"),
    ("2023/24 winter", "2023-06-01", "2024-05-01"),
    ("2024/25 winter", "2024-07-01", "2025-05-01"),
]

n_seasons = len(PLOT_SEASONS)
fig2, axes2 = plt.subplots(4, 2, figsize=(18, 20), sharey=False)
fig2.suptitle('Influenza Lab Positivity and Onset Detection by Season\n'
              'CHP Flu Express — Hong Kong 2014–2025',
              fontsize=14, fontweight='bold', y=1.01)

for idx, (season_name, plot_start, plot_end) in enumerate(PLOT_SEASONS):
    row, col = divmod(idx, 2)
    ax = axes2[row, col]
    
    # Get surveillance data
    mask = (df['MidDate'] >= pd.to_datetime(plot_start)) & \
           (df['MidDate'] <= pd.to_datetime(plot_end))
    sdata = df.loc[mask].copy()
    
    # Plot positivity
    ax.plot(sdata['MidDate'], sdata['AandB_proportion'] * 100,
            'k-', linewidth=1.5, label='Lab positivity')
    ax.axhline(y=CHP_THRESHOLD * 100, color='red', linestyle='--',
               alpha=0.5, linewidth=1, label='CHP threshold (4.94%)')
    
    # Get onset dates from merged table
    row_data = merged[merged['season'] == season_name]
    if len(row_data) > 0:
        r = row_data.iloc[0]
        
        # CHP onset
        if pd.notna(r.get('chp_onset')) and r['chp_onset'] not in [None, 'N/A']:
            ax.axvline(x=pd.to_datetime(r['chp_onset']), color='red',
                       linestyle=':', linewidth=1.5, alpha=0.8, label='CHP onset')
        
        # PINN onset
        pinn_o = r.get('pinn_onset', None)
        if pd.notna(pinn_o) and pinn_o not in [None, 'N/A', '']:
            ax.axvline(x=pd.to_datetime(pinn_o), color='#2196F3',
                       linestyle=':', linewidth=1.5, alpha=0.8, label='PINN onset')
        
        # EpiEstim onset
        epi_o = r.get('epiestim_onset', None)
        if pd.notna(epi_o) and epi_o not in [None, 'N/A', '']:
            ax.axvline(x=pd.to_datetime(epi_o), color='#FF9800',
                       linestyle=':', linewidth=1.5, alpha=0.8, label='EpiEstim onset')
    
    ax.set_title(season_name, fontsize=11, fontweight='bold')
    ax.set_ylabel('Lab positivity (%)')
    ax.grid(True, alpha=0.2)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b\n%Y'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    
    if idx == 0:
        ax.legend(fontsize=7, loc='upper right')

plt.tight_layout()
plt.savefig('comparison_seasons_detail.png', dpi=150, bbox_inches='tight')
print("  Saved: comparison_seasons_detail.png")


# ============================================================
# FIGURE 3: LEAD TIME DISTRIBUTION
# ============================================================

fig3, axes3 = plt.subplots(1, 2, figsize=(12, 5))
fig3.suptitle('Lead Time Distribution: Days Before CHP Threshold Detection',
              fontsize=13, fontweight='bold')

methods = []
colors_map = {'PINN': '#2196F3', 'EpiEstim': '#FF9800'}

for method, col, color in [('PINN', 'pinn_lead_days', '#2196F3'),
                             ('EpiEstim', 'epiestim_lead_days', '#FF9800')]:
    valid = merged[col].dropna()
    if len(valid) > 0:
        methods.append((method, valid, color))

# Box plot
ax_box = axes3[0]
if methods:
    bp_data = [m[1].values for m in methods]
    bp_labels = [m[0] for m in methods]
    bp_colors = [m[2] for m in methods]
    
    bp = ax_box.boxplot(bp_data, labels=bp_labels, patch_artist=True,
                        widths=0.5, showmeans=True,
                        meanprops={'marker': 'D', 'markerfacecolor': 'white',
                                   'markeredgecolor': 'black', 'markersize': 8})
    for patch, color in zip(bp['boxes'], bp_colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.6)

ax_box.axhline(y=0, color='red', linestyle='--', linewidth=1, alpha=0.5)
ax_box.set_ylabel('Lead time (days)\n+ = method detects before CHP')
ax_box.set_title('Lead Time Distribution')
ax_box.grid(True, axis='y', alpha=0.3)

# Scatter: lead time vs peak positivity
ax_scat = axes3[1]
for method, col, color in [('PINN', 'pinn_lead_days', '#2196F3'),
                             ('EpiEstim', 'epiestim_lead_days', '#FF9800')]:
    valid_mask = merged[col].notna()
    if valid_mask.sum() > 0:
        ax_scat.scatter(merged.loc[valid_mask, 'peak_pct'],
                       merged.loc[valid_mask, col],
                       c=color, s=80, alpha=0.7, edgecolors='black',
                       linewidth=0.5, label=method, zorder=5)

ax_scat.axhline(y=0, color='red', linestyle='--', linewidth=1, alpha=0.5)
ax_scat.set_xlabel('Peak positivity (%)')
ax_scat.set_ylabel('Lead time (days)')
ax_scat.set_title('Lead Time vs Season Severity')
ax_scat.legend()
ax_scat.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('comparison_lead_distribution.png', dpi=150, bbox_inches='tight')
print("  Saved: comparison_lead_distribution.png")

print(f"\n{'='*80}")
print("DONE. Three figures + comparison table saved.")
print(f"{'='*80}")
