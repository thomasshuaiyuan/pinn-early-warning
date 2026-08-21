"""
Signal-to-Noise Ratio Analysis (Vijay Comment 36)
====================================================
Computes peak positivity / non-season SD per season
and tests its relationship to EpiEstim lead time.

Run: conda activate pinn && python snr_analysis.py
Requires: flux_data.csv, chp_respiratory_cleaned.csv

Thomas Yuan — HKU PhD, Pathogen Evolution Lab
"""

import numpy as np
import pandas as pd
from scipy.stats import spearmanr, pearsonr
import warnings
warnings.filterwarnings("ignore")

# ============================================================
# LOAD DATA
# ============================================================

df = pd.read_csv("flux_data.csv")
df["From"] = pd.to_datetime(df["From"], format="%d/%m/%Y")
df["To"] = pd.to_datetime(df["To"], format="%d/%m/%Y")
df["MidDate"] = df["From"] + (df["To"] - df["From"]) / 2

try:
    rsv_df = pd.read_csv("chp_respiratory_cleaned.csv")
    rsv_df["From"] = pd.to_datetime(rsv_df["From"])
    rsv_df["To"] = pd.to_datetime(rsv_df["To"])
    rsv_df["MidDate"] = rsv_df["From"] + (rsv_df["To"] - rsv_df["From"]) / 2
    has_rsv = True
except:
    has_rsv = False

# ============================================================
# COMPUTE NON-SEASON BASELINE STATS
# ============================================================

# Influenza: non-season = below median (excluding 2020-2022)
flu_data = df[(df["MidDate"] < "2020-01-01") | (df["MidDate"] > "2022-12-31")]
flu_vals = flu_data["AandB_proportion"].dropna()
flu_nonseas = flu_vals[flu_vals < flu_vals.median()]
flu_baseline_mean = flu_nonseas.mean()
flu_baseline_sd = flu_nonseas.std()
print(f"Influenza baseline: mean = {flu_baseline_mean*100:.2f}%, SD = {flu_baseline_sd*100:.2f}%")
print(f"  Threshold (mean + 1.96*SD) = {(flu_baseline_mean + 1.96*flu_baseline_sd)*100:.2f}%")

# RSV
if has_rsv:
    rsv_vals = rsv_df["RSV_pct"].dropna() / 100  # convert to proportion
    rsv_nonseas = rsv_vals[rsv_vals < rsv_vals.median()]
    rsv_baseline_mean = rsv_nonseas.mean()
    rsv_baseline_sd = rsv_nonseas.std()
    print(f"\nRSV baseline: mean = {rsv_baseline_mean*100:.2f}%, SD = {rsv_baseline_sd*100:.2f}%")
    print(f"  Threshold (mean + 1.96*SD) = {(rsv_baseline_mean + 1.96*rsv_baseline_sd)*100:.2f}%")

# ============================================================
# SNR PER SEASON
# ============================================================

flu_seasons = [
    ("2014/15", 0.386, 35),
    ("2015/16", 0.257, 70),
    ("2016/17", 0.156, -98),
    ("2017/18", 0.406, -28),
    ("2018/19", 0.299, 28),
    ("2023 S", 0.182, 35),
    ("2023/24", 0.149, -28),
    ("2024/25", 0.105, 49),
]

rsv_seasons = [
    ("2014 spr", 0.073, 35),
    ("2015 sum", 0.054, -21),
    ("2016 sum", 0.050, -28),
    ("2017 sum", 0.099, -28),
    ("2018 sum", 0.062, -14),
    ("2019 sum", 0.038, -28),
    ("2021/22", 0.124, 49),
    ("2022/23", 0.101, 133),
    ("2023 sum", 0.083, -28),
    ("2025 sum", 0.035, 91),
]

print(f"\n{'='*80}")
print("SIGNAL-TO-NOISE RATIO PER SEASON")
print(f"  SNR = peak positivity / non-season SD")
print(f"{'='*80}")

print(f"\n{'Pathogen':<12} {'Season':<12} {'Peak%':>7} {'SNR':>7} {'Lead(d)':>9} {'Lead>0':>7}")
print("-" * 58)

all_snr = []
all_lead = []
all_pathogen = []

for name, peak, lead in flu_seasons:
    snr = peak / flu_baseline_sd
    print(f"{'Influenza':<12} {name:<12} {peak*100:>6.1f}% {snr:>7.1f} {lead:>+8d} {'yes' if lead > 0 else 'no':>7}")
    all_snr.append(snr)
    all_lead.append(lead)
    all_pathogen.append("Influenza")

if has_rsv:
    for name, peak, lead in rsv_seasons:
        snr = peak / rsv_baseline_sd
        print(f"{'RSV':<12} {name:<12} {peak*100:>6.1f}% {snr:>7.1f} {lead:>+8d} {'yes' if lead > 0 else 'no':>7}")
        all_snr.append(snr)
        all_lead.append(lead)
        all_pathogen.append("RSV")

# ============================================================
# STATISTICAL TESTS
# ============================================================

snr_arr = np.array(all_snr)
lead_arr = np.array(all_lead)

print(f"\n{'='*80}")
print("RELATIONSHIP: SNR vs Lead Time")
print(f"{'='*80}")

# Continuous
r_pearson, p_pearson = pearsonr(snr_arr, lead_arr)
r_spearman, p_spearman = spearmanr(snr_arr, lead_arr)
print(f"\n  Pearson r = {r_pearson:.3f} (p = {p_pearson:.3f})")
print(f"  Spearman rho = {r_spearman:.3f} (p = {p_spearman:.3f})")

# Binary: does SNR predict lead > 0?
from scipy.stats import mannwhitneyu
positive = snr_arr[lead_arr > 0]
negative = snr_arr[lead_arr <= 0]
if len(positive) > 1 and len(negative) > 1:
    u_stat, u_p = mannwhitneyu(positive, negative, alternative='greater')
    print(f"\n  SNR for leading seasons (n={len(positive)}): median = {np.median(positive):.1f}")
    print(f"  SNR for lagging seasons (n={len(negative)}): median = {np.median(negative):.1f}")
    print(f"  Mann-Whitney U = {u_stat:.1f}, p = {u_p:.3f} (one-sided: leading > lagging)")

# Logistic regression (simple)
try:
    from sklearn.linear_model import LogisticRegression
    X = snr_arr.reshape(-1, 1)
    y = (lead_arr > 0).astype(int)
    model = LogisticRegression()
    model.fit(X, y)
    print(f"\n  Logistic regression: coef = {model.coef_[0][0]:.3f}, intercept = {model.intercept_[0]:.3f}")
    # Predicted probability at SNR thresholds
    for snr_val in [5, 10, 15, 20]:
        prob = model.predict_proba([[snr_val]])[0][1]
        print(f"    P(lead > 0 | SNR = {snr_val}) = {prob:.2f}")
except ImportError:
    print("\n  sklearn not available for logistic regression")

# Also compute data-derived flu threshold for sensitivity
print(f"\n{'='*80}")
print("SENSITIVITY: Data-derived influenza threshold")
print(f"{'='*80}")
print(f"  Operational (hard-coded): 4.94%")
print(f"  Data-derived (mean + 1.96*SD): {(flu_baseline_mean + 1.96*flu_baseline_sd)*100:.2f}%")
print(f"  Difference: {abs(0.0494 - (flu_baseline_mean + 1.96*flu_baseline_sd))*100:.2f} percentage points")

# Save
results = pd.DataFrame({
    "pathogen": all_pathogen,
    "season": [s[0] for s in flu_seasons] + ([s[0] for s in rsv_seasons] if has_rsv else []),
    "peak_positivity": [s[1] for s in flu_seasons] + ([s[1] for s in rsv_seasons] if has_rsv else []),
    "snr": all_snr,
    "epiestim_lead": all_lead,
    "leads_threshold": [l > 0 for l in all_lead],
})
results.to_csv("snr_analysis_results.csv", index=False)
print(f"\nResults saved to snr_analysis_results.csv")
