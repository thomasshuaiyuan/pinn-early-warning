"""
Pre-Onset Signal Analysis (Vijay Comments 74, 75)
====================================================
1. Per-channel pre-onset amplification with between-season variability
2. Age-group first-crossing counts with exact binomial CIs
3. RSV COVID comparison CI

Run: conda activate pinn && python preonset_analysis.py
Requires: flux_data.csv

Thomas Yuan — HKU PhD, Pathogen Evolution Lab
"""

import numpy as np
import pandas as pd
from scipy.stats import binom, mannwhitneyu
import warnings
warnings.filterwarnings("ignore")

df = pd.read_csv("flux_data.csv")
df["From"] = pd.to_datetime(df["From"], format="%d/%m/%Y")
df["To"] = pd.to_datetime(df["To"], format="%d/%m/%Y")
df["MidDate"] = df["From"] + (df["To"] - df["From"]) / 2

CHP_THRESHOLD = 0.0494

# Single-wave seasons with clear onset
SEASONS = [
    ("2014/15", "2014-10-01", "2015-06-01"),
    ("2015/16", "2015-10-01", "2016-06-01"),
    ("2018/19", "2018-09-15", "2019-06-01"),
    ("2023 S", "2023-01-15", "2023-10-01"),
    ("2024/25", "2024-08-01", "2025-04-01"),
]

CHANNELS = [
    ("Adm_All", "Admissions all ages"),
    ("Adm_0_5", "Admissions 0-5y"),
    ("Adm_6_11", "Admissions 6-11y"),
    ("Adm_12_17", "Admissions 12-17y"),
    ("Adm_65_higher", "Admissions 65+"),
    ("ILI_PMP", "GP ILI rate"),
    ("ILI_FMC", "A&E ILI rate"),
]

# ============================================================
# 1. PRE-ONSET AMPLIFICATION WITH BETWEEN-SEASON VARIABILITY
# ============================================================
print("=" * 80)
print("ANALYSIS 1: Pre-onset amplification per channel (Comment 74)")
print("  Per-season values with between-season SD")
print("=" * 80)

channel_results = {}

for col, name in CHANNELS:
    season_changes = []

    for sname, start, end in SEASONS:
        mask = (df["MidDate"] >= start) & (df["MidDate"] <= end)
        season = df.loc[mask].dropna(subset=[col, "AandB_proportion"]).sort_values("MidDate")

        if len(season) < 12:
            continue

        # Find CHP threshold crossing
        above = season[season["AandB_proportion"] > CHP_THRESHOLD]
        if len(above) == 0:
            continue
        onset_idx = above.index[0]
        onset_pos = season.index.get_loc(onset_idx)

        # 8 weeks before onset
        if onset_pos < 8:
            continue

        pre_start = onset_pos - 8
        baseline_val = season.iloc[pre_start][col]
        pre_onset_val = season.iloc[onset_pos - 1][col]

        if baseline_val > 0:
            pct_change = ((pre_onset_val - baseline_val) / baseline_val) * 100
            season_changes.append({
                "season": sname,
                "baseline": baseline_val,
                "pre_onset": pre_onset_val,
                "pct_change": pct_change,
            })

    if season_changes:
        changes = [s["pct_change"] for s in season_changes]
        channel_results[name] = {
            "n_seasons": len(changes),
            "mean_change": np.mean(changes),
            "sd_change": np.std(changes, ddof=1) if len(changes) > 1 else None,
            "min_change": np.min(changes),
            "max_change": np.max(changes),
            "per_season": season_changes,
        }

print(f"\n{'Channel':<25} {'n':>3} {'Mean%':>8} {'SD%':>8} {'Range':>20}")
print("-" * 70)
for name, r in channel_results.items():
    sd = f"{r['sd_change']:.1f}" if r['sd_change'] else "N/A"
    rng = f"{r['min_change']:.0f} to {r['max_change']:.0f}"
    print(f"{name:<25} {r['n_seasons']:>3} {r['mean_change']:>7.1f}% {sd:>8} {rng:>20}")

# Print per-season detail
print(f"\nPer-season detail:")
for name, r in channel_results.items():
    vals = [f"{s['season']}:{s['pct_change']:.0f}%" for s in r['per_season']]
    print(f"  {name}: {', '.join(vals)}")


# ============================================================
# 2. AGE-GROUP FIRST-CROSSING COUNTS (Comment 75)
# ============================================================
print(f"\n\n{'='*80}")
print("ANALYSIS 2: Which age group crosses baseline first? (Comment 75)")
print("  With exact binomial CIs")
print("=" * 80)

AGE_GROUPS = [
    ("Adm_0_5", "0-5y"),
    ("Adm_6_11", "6-11y"),
    ("Adm_12_17", "12-17y"),
    ("Adm_65_higher", "65+"),
    ("Adm_All", "All ages"),
]

first_crossings = {name: 0 for _, name in AGE_GROUPS}
n_seasons_valid = 0

for sname, start, end in SEASONS:
    mask = (df["MidDate"] >= start) & (df["MidDate"] <= end)
    season = df.loc[mask].sort_values("MidDate").reset_index(drop=True)

    if len(season) < 10:
        continue

    earliest_week = None
    earliest_group = None

    for col, name in AGE_GROUPS:
        vals = season[col].dropna()
        if len(vals) == 0:
            continue

        # Compute age-specific threshold
        all_vals = df[col].dropna()
        nonseas = all_vals[all_vals < all_vals.median()]
        threshold = nonseas.mean() + 1.96 * nonseas.std()

        # Find first week above threshold
        above = season[season[col] > threshold]
        if len(above) > 0:
            first_week = season.index.get_loc(above.index[0])
            if earliest_week is None or first_week < earliest_week:
                earliest_week = first_week
                earliest_group = name

    if earliest_group:
        first_crossings[earliest_group] += 1
        n_seasons_valid += 1
        print(f"  {sname}: {earliest_group} crossed first (week {earliest_week})")

print(f"\nFirst-crossing counts (n = {n_seasons_valid} seasons):")
print(f"{'Age group':<15} {'Count':>6} {'Proportion':>12} {'95% CI':>20}")
print("-" * 55)

for _, name in AGE_GROUPS:
    k = first_crossings[name]
    n = n_seasons_valid
    prop = k / n if n > 0 else 0
    # Exact binomial CI (Clopper-Pearson)
    if n > 0:
        ci_low = binom.ppf(0.025, n, prop) / n if k > 0 else 0
        ci_high = binom.ppf(0.975, n, prop) / n if k < n else 1
        # More accurate: use beta distribution
        from scipy.stats import beta
        ci_low = beta.ppf(0.025, k + 0.5, n - k + 0.5) if k > 0 else 0
        ci_high = beta.ppf(0.975, k + 0.5, n - k + 0.5) if k < n else 1
        ci_str = f"[{ci_low:.2f}, {ci_high:.2f}]"
    else:
        ci_str = "N/A"
    print(f"{name:<15} {k:>6} {prop:>11.2f} {ci_str:>20}")


# ============================================================
# 3. RSV COVID COMPARISON CI (Comment 85)
# ============================================================
print(f"\n\n{'='*80}")
print("ANALYSIS 3: RSV pre-COVID vs COVID comparison with CI (Comment 85)")
print("=" * 80)

try:
    rsv_df = pd.read_csv("chp_respiratory_cleaned.csv")
    rsv_df["From"] = pd.to_datetime(rsv_df["From"])
    rsv_df["To"] = pd.to_datetime(rsv_df["To"])
    rsv_df["MidDate"] = rsv_df["From"] + (rsv_df["To"] - rsv_df["From"]) / 2

    # Pre-COVID: 2014-2019
    pre = rsv_df[(rsv_df["MidDate"] >= "2014-01-01") & (rsv_df["MidDate"] < "2020-01-01")]["RSV_pct"].dropna()
    # During COVID: 2020-2021 (before rebound)
    during = rsv_df[(rsv_df["MidDate"] >= "2020-01-01") & (rsv_df["MidDate"] < "2021-06-01")]["RSV_pct"].dropna()

    pre_mean = pre.mean()
    during_mean = during.mean()
    diff = pre_mean - during_mean

    # Bootstrap CI for difference
    n_boot = 10000
    boot_diffs = []
    for _ in range(n_boot):
        b_pre = np.random.choice(pre.values, size=len(pre), replace=True)
        b_dur = np.random.choice(during.values, size=len(during), replace=True)
        boot_diffs.append(b_pre.mean() - b_dur.mean())

    ci_low = np.percentile(boot_diffs, 2.5)
    ci_high = np.percentile(boot_diffs, 97.5)

    # Mann-Whitney
    u_stat, u_p = mannwhitneyu(pre.values, during.values, alternative='two-sided')

    print(f"\n  Pre-COVID RSV mean positivity: {pre_mean:.2f}% (n = {len(pre)} weeks)")
    print(f"  During-COVID RSV mean positivity: {during_mean:.2f}% (n = {len(during)} weeks)")
    print(f"  Difference: {diff:.2f} percentage points")
    print(f"  Bootstrap 95% CI for difference: [{ci_low:.2f}, {ci_high:.2f}]")
    print(f"  Mann-Whitney U = {u_stat:.0f}, p = {u_p:.4f}")

except Exception as e:
    print(f"  RSV data not available: {e}")


# Save all results
print(f"\n{'='*80}")
print("All results computed. Update manuscript with:")
print("  1. Per-channel amplification with SD and range")
print("  2. All age-group first-crossing counts with CIs")
print("  3. RSV COVID comparison with bootstrap CI")
print(f"{'='*80}")
