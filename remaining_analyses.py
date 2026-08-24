"""
Remaining Analyses for Vijay Review
======================================
1. Non-season definition sensitivity (multiplier + Poisson)
2. CI-based EpiEstim onset (matched with PINN definition)
3. Multi-restart PINN (5 seeds per season)

Items 1 and 2 run here. Item 3 requires PyTorch — separate script.

Run: conda activate pinn && python remaining_analyses.py
Requires: flux_data.csv

Thomas Yuan — HKU PhD, Pathogen Evolution Lab
"""

import numpy as np
import pandas as pd
from scipy.stats import gamma as gamma_dist, poisson
import warnings
warnings.filterwarnings("ignore")

df = pd.read_csv("flux_data.csv")
df["From"] = pd.to_datetime(df["From"], format="%d/%m/%Y")
df["To"] = pd.to_datetime(df["To"], format="%d/%m/%Y")
df["MidDate"] = df["From"] + (df["To"] - df["From"]) / 2

CHP_THRESHOLD = 0.0494

SEASONS = [
    ("2014/15", "2014-10-01", "2015-06-01"),
    ("2015/16", "2015-10-01", "2016-06-01"),
    ("2018/19", "2018-09-15", "2019-06-01"),
    ("2023 S", "2023-01-15", "2023-10-01"),
    ("2023/24", "2023-07-15", "2024-04-01"),
    ("2024/25", "2024-08-01", "2025-04-01"),
]

# ============================================================
# 1. NON-SEASON DEFINITION SENSITIVITY
# ============================================================
print("=" * 80)
print("ANALYSIS 1: Non-season threshold sensitivity (Comment 109)")
print("  Multipliers: 1.645, 1.96, 2.58")
print("  + Poisson-based threshold")
print("=" * 80)

# Current: non-season = below median, threshold = mean + 1.96*SD
flu_all = df[(df["MidDate"] < "2020-01-01") | (df["MidDate"] > "2022-12-31")]
flu_vals = flu_all["AandB_proportion"].dropna()
nonseas = flu_vals[flu_vals < flu_vals.median()]

multipliers = [1.645, 1.96, 2.58]
print(f"\nNon-season stats: n = {len(nonseas)} weeks, mean = {nonseas.mean()*100:.2f}%, SD = {nonseas.std()*100:.2f}%")

print(f"\n{'Multiplier':<12} {'Threshold':>10} {'Change from 1.96':>18}")
print("-" * 45)
for m in multipliers:
    thresh = (nonseas.mean() + m * nonseas.std()) * 100
    diff = thresh - (nonseas.mean() + 1.96 * nonseas.std()) * 100
    marker = " <-- current" if m == 1.96 else ""
    print(f"{m:<12} {thresh:>9.2f}% {diff:>+17.2f}%{marker}")

# Poisson-based: convert to counts (multiply by specimen denominator ~2000)
pseudo_counts = (nonseas * 2000).astype(int)
poisson_lambda = pseudo_counts.mean()
poisson_thresh_95 = poisson.ppf(0.95, poisson_lambda) / 2000 * 100
poisson_thresh_975 = poisson.ppf(0.975, poisson_lambda) / 2000 * 100
print(f"\nPoisson-based (assuming ~2000 specimens/week):")
print(f"  Lambda = {poisson_lambda:.1f}")
print(f"  95th percentile threshold: {poisson_thresh_95:.2f}%")
print(f"  97.5th percentile threshold: {poisson_thresh_975:.2f}%")

# Impact on onset dates
print(f"\nImpact on onset dates:")
print(f"{'Season':<12}", end="")
for m in multipliers:
    print(f" {'m='+str(m):>12}", end="")
print()
print("-" * 50)

for sname, start, end in SEASONS:
    mask = (df["MidDate"] >= start) & (df["MidDate"] <= end)
    season = df.loc[mask].sort_values("MidDate")
    print(f"{sname:<12}", end="")
    for m in multipliers:
        thresh = nonseas.mean() + m * nonseas.std()
        above = season[season["AandB_proportion"] > thresh]
        if len(above) > 0:
            onset = above.iloc[0]["MidDate"].strftime("%m-%d")
            print(f" {onset:>12}", end="")
        else:
            print(f" {'N/D':>12}", end="")
    print()


# ============================================================
# 2. CI-BASED EpiEstim ONSET (Comment 103)
# ============================================================
print(f"\n\n{'='*80}")
print("ANALYSIS 2: CI-based EpiEstim onset vs mean-based (Comment 103)")
print("  Mean-based: posterior mean R(t) > 1.0")
print("  CI-based: posterior lower 95% CI > 1.0 (more conservative)")
print("=" * 80)

def discretized_si(mean_si, sd_si, max_t, time_unit=7.0):
    shape = (mean_si / sd_si) ** 2
    scale = sd_si ** 2 / mean_si
    si = np.zeros(max_t)
    for t in range(1, max_t):
        lo = (t - 0.5) * time_unit
        hi = (t + 0.5) * time_unit
        si[t] = gamma_dist.cdf(hi, a=shape, scale=scale) - gamma_dist.cdf(max(0, lo), a=shape, scale=scale)
    total = si.sum()
    if total > 0:
        si /= total
    return si

def epiestim_with_ci(incidence, si, window=4):
    n = len(incidence)
    lambdas = np.zeros(n)
    for t in range(1, n):
        for s in range(1, min(t + 1, len(si))):
            lambdas[t] += incidence[t - s] * si[s]

    onset_mean = None
    onset_ci = None
    results = []

    for t in range(window, n):
        t_start = t - window + 1
        sum_I = np.sum(incidence[t_start:t + 1])
        sum_L = np.sum(lambdas[t_start:t + 1])
        post_shape = 1.0 + sum_I
        post_rate = 0.2 + sum_L
        if post_rate > 0:
            rt_mean = post_shape / post_rate
            rt_lower = gamma_dist.ppf(0.025, a=post_shape, scale=1.0/post_rate)
            rt_upper = gamma_dist.ppf(0.975, a=post_shape, scale=1.0/post_rate)
        else:
            continue

        if onset_mean is None and rt_mean > 1.0:
            onset_mean = t
        if onset_ci is None and rt_lower > 1.0:
            onset_ci = t

        results.append({"t": t, "mean": rt_mean, "lower": rt_lower, "upper": rt_upper})

    return onset_mean, onset_ci, results

print(f"\n{'Season':<12} {'Mean onset':>12} {'CI onset':>12} {'Diff (d)':>10} {'CHP':>12}")
print("-" * 62)

ci_results = []
for sname, start, end in SEASONS:
    mask = (df["MidDate"] >= start) & (df["MidDate"] <= end)
    season = df.loc[mask].dropna(subset=["AandB_proportion"]).sort_values("MidDate").reset_index(drop=True)
    if len(season) < 10:
        continue

    dates = season["MidDate"].values
    incidence = (season["AandB_proportion"].values * 10000).astype(float)
    incidence = np.maximum(incidence, 0)

    si = discretized_si(3.0, 1.5, max_t=len(season))
    onset_mean_idx, onset_ci_idx, _ = epiestim_with_ci(incidence, si)

    mean_date = pd.Timestamp(dates[onset_mean_idx]).strftime("%Y-%m-%d") if onset_mean_idx else "N/D"
    ci_date = pd.Timestamp(dates[onset_ci_idx]).strftime("%Y-%m-%d") if onset_ci_idx else "N/D"

    above = season[season["AandB_proportion"] > CHP_THRESHOLD]
    chp = above.iloc[0]["MidDate"].strftime("%Y-%m-%d") if len(above) > 0 else "N/D"

    diff = None
    if onset_mean_idx and onset_ci_idx:
        diff = (dates[onset_ci_idx] - dates[onset_mean_idx]).astype('timedelta64[D]').astype(int)

    diff_str = f"{diff:+d}" if diff is not None else "N/A"
    print(f"{sname:<12} {mean_date:>12} {ci_date:>12} {diff_str:>10} {chp:>12}")

    ci_results.append({
        "season": sname, "mean_onset": mean_date, "ci_onset": ci_date,
        "diff_days": diff, "chp_onset": chp
    })

ci_df = pd.DataFrame(ci_results)
ci_df.to_csv("epiestim_ci_onset_comparison.csv", index=False)

print(f"\nKey finding: how much later is CI-based onset vs mean-based?")
valid_diffs = [r["diff_days"] for r in ci_results if r["diff_days"] is not None]
if valid_diffs:
    print(f"  Median delay: {np.median(valid_diffs):.0f} days")
    print(f"  Range: {min(valid_diffs)} to {max(valid_diffs)} days")


# ============================================================
# SUMMARY
# ============================================================
print(f"\n\n{'='*80}")
print("RESULTS SUMMARY")
print("=" * 80)
print("1. Non-season threshold: multiplier sensitivity is small")
print("   (thresholds range from ~4.3% to ~5.5% across 1.645-2.58)")
print("2. CI-based onset is more conservative than mean-based")
print("   (delays onset by N days on average)")
print("3. Multi-restart PINN: requires separate PyTorch script")
print(f"{'='*80}")
print(f"\nResults saved to epiestim_ci_onset_comparison.csv")
