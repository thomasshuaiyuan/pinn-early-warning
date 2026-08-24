"""
EpiEstim Serial Interval Sensitivity Sweep
=============================================
Addresses Vijay Comment 25:
  - 5 SI means × 4 window widths = 20 configurations
  - Run on ALL 6 influenza seasons (not just 2018/19)
  - Output: supplementary table with onset date and lead time
    per configuration per season
  - Report range, not just SD

Run: conda activate pinn && python epiestim_si_sensitivity.py
Requires: flux_data.csv

Thomas Yuan — HKU PhD, Pathogen Evolution Lab
"""

import numpy as np
import pandas as pd
from scipy.stats import gamma as gamma_dist
import warnings
warnings.filterwarnings("ignore")

# ============================================================
# EpiEstim
# ============================================================

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

def run_epiestim(incidence, si, window=4):
    n = len(incidence)
    lambdas = np.zeros(n)
    for t in range(1, n):
        for s in range(1, min(t + 1, len(si))):
            lambdas[t] += incidence[t - s] * si[s]
    for t in range(window, n):
        t_start = t - window + 1
        sum_I = np.sum(incidence[t_start:t + 1])
        sum_L = np.sum(lambdas[t_start:t + 1])
        post_rate = 0.2 + sum_L
        if post_rate > 0:
            rt = (1.0 + sum_I) / post_rate
            if rt > 1.0:
                return t  # return index of first R(t) > 1
    return None

# ============================================================
# CONFIGURATION
# ============================================================

SI_MEANS = [2.0, 2.5, 3.0, 3.5, 4.0]
SI_SDS = None  # will use mean * 0.5 for each
WINDOWS = [3, 4, 5, 6]

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
# MAIN
# ============================================================

print("=" * 90)
print("EpiEstim SI Sensitivity Sweep (Vijay Comment 25)")
print(f"  {len(SI_MEANS)} SI means × {len(WINDOWS)} windows = {len(SI_MEANS)*len(WINDOWS)} configs")
print(f"  Across {len(SEASONS)} influenza seasons")
print("=" * 90)

df = pd.read_csv("flux_data.csv")
df["From"] = pd.to_datetime(df["From"], format="%d/%m/%Y")
df["To"] = pd.to_datetime(df["To"], format="%d/%m/%Y")
df["MidDate"] = df["From"] + (df["To"] - df["From"]) / 2

results = []

for sname, start, end in SEASONS:
    mask = (df["MidDate"] >= start) & (df["MidDate"] <= end)
    season = df.loc[mask].dropna(subset=["AandB_proportion"]).sort_values("MidDate").reset_index(drop=True)

    if len(season) < 10:
        continue

    dates = season["MidDate"].values
    incidence = (season["AandB_proportion"].values * 10000).astype(float)
    incidence = np.maximum(incidence, 0)

    # CHP threshold onset
    above = season[season["AandB_proportion"] > CHP_THRESHOLD]
    chp_onset = above.iloc[0]["MidDate"] if len(above) > 0 else None

    for si_mean in SI_MEANS:
        si_sd = si_mean * 0.5  # proportional SD
        for window in WINDOWS:
            si = discretized_si(si_mean, si_sd, max_t=len(season))
            onset_idx = run_epiestim(incidence, si, window=window)

            if onset_idx is not None:
                onset_date = dates[onset_idx]
                onset_str = pd.Timestamp(onset_date).strftime("%Y-%m-%d")
                lead = (chp_onset - pd.Timestamp(onset_date)).days if chp_onset is not None else None
            else:
                onset_str = None
                lead = None

            results.append({
                "season": sname,
                "si_mean": si_mean,
                "si_sd": round(si_sd, 1),
                "window": window,
                "onset_date": onset_str,
                "lead_days": lead,
                "chp_onset": chp_onset.strftime("%Y-%m-%d") if chp_onset is not None else None,
            })

results_df = pd.DataFrame(results)
results_df.to_csv("epiestim_si_sensitivity_flu.csv", index=False)

# ============================================================
# SUMMARY TABLE
# ============================================================

print(f"\n{'='*90}")
print("SUPPLEMENTARY TABLE: Onset date by SI configuration and season")
print(f"{'='*90}")

# Pivot: for each season, show range of onset dates and lead times
for sname, _, _ in SEASONS:
    sub = results_df[results_df["season"] == sname]
    valid = sub.dropna(subset=["lead_days"])

    if len(valid) == 0:
        print(f"\n  {sname}: no configurations detected onset")
        continue

    leads = valid["lead_days"].values
    onsets = pd.to_datetime(valid["onset_date"])

    print(f"\n  {sname} (CHP: {valid.iloc[0]['chp_onset']}):")
    print(f"    Configs detecting onset: {len(valid)}/{len(sub)}")
    print(f"    Onset date range: {onsets.min().strftime('%Y-%m-%d')} to {onsets.max().strftime('%Y-%m-%d')}")
    print(f"    Lead time range: {leads.min():.0f} to {leads.max():.0f} days")
    print(f"    Lead time mean: {leads.mean():.1f} days")
    print(f"    Lead time SD: {leads.std():.1f} days")
    print(f"    Lead time median: {np.median(leads):.0f} days")

# Cross-season summary
print(f"\n{'='*90}")
print("CROSS-SEASON SUMMARY")
print(f"{'='*90}")

all_sds = []
all_ranges = []
for sname, _, _ in SEASONS:
    sub = results_df[(results_df["season"] == sname)].dropna(subset=["lead_days"])
    if len(sub) > 1:
        sd = sub["lead_days"].std()
        rng = sub["lead_days"].max() - sub["lead_days"].min()
        all_sds.append(sd)
        all_ranges.append(rng)
        print(f"  {sname}: SD = {sd:.1f} days, range = {rng:.0f} days")

if all_sds:
    print(f"\n  Mean SD across seasons: {np.mean(all_sds):.1f} days")
    print(f"  Mean range across seasons: {np.mean(all_ranges):.0f} days")

# Detailed grid for one example season
print(f"\n{'='*90}")
print("DETAILED GRID: 2018/19 (onset date by SI mean × window)")
print(f"{'='*90}")
example = results_df[results_df["season"] == "2018/19"]
print(f"\n{'SI mean':>8} {'w=3':>12} {'w=4':>12} {'w=5':>12} {'w=6':>12}")
print("-" * 60)
for si_mean in SI_MEANS:
    row = f"{si_mean:>8}"
    for w in WINDOWS:
        match = example[(example["si_mean"] == si_mean) & (example["window"] == w)]
        if len(match) > 0 and match.iloc[0]["onset_date"] is not None:
            row += f" {match.iloc[0]['onset_date']:>12}"
        else:
            row += f" {'N/D':>12}"
    print(row)

print(f"\n{'='*90}")
print(f"Results saved to epiestim_si_sensitivity_flu.csv")
print(f"This file serves as the supplementary table for the manuscript.")
print(f"{'='*90}")
