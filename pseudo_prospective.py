"""
Pseudo-Prospective EpiEstim Evaluation (Vijay Comment 93)
============================================================
"The single most valuable addition to the paper."

Simulates real-time deployment: at each week t, EpiEstim runs
using only data available up to week t (no future data).
Compares pseudo-prospective onset to retrospective onset.

This addresses:
- Right truncation (EpiEstim window needs future data it won't have)
- Reporting delays (not modelled here, but the truncation effect is)
- Whether the retrospective lead times are achievable in practice

Run: conda activate pinn && python pseudo_prospective.py
Requires: flux_data.csv

Thomas Yuan — HKU PhD, Pathogen Evolution Lab
"""

import numpy as np
import pandas as pd
from scipy.stats import gamma as gamma_dist
import warnings
warnings.filterwarnings("ignore")

# ============================================================
# EpiEstim on truncated data
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

def epiestim_at_week(incidence_up_to_t, si, window=4):
    """Run EpiEstim using only data up to current week.
    Returns R(t) mean and CI at the latest available week."""
    n = len(incidence_up_to_t)
    if n < window + 1:
        return None, None, None

    lambdas = np.zeros(n)
    for t in range(1, n):
        for s in range(1, min(t + 1, len(si))):
            lambdas[t] += incidence_up_to_t[t - s] * si[s]

    t = n - 1  # latest week
    t_start = max(0, t - window + 1)
    sum_I = np.sum(incidence_up_to_t[t_start:t + 1])
    sum_L = np.sum(lambdas[t_start:t + 1])

    post_shape = 1.0 + sum_I
    post_rate = 0.2 + sum_L

    if post_rate > 0:
        rt_mean = post_shape / post_rate
        rt_lower = gamma_dist.ppf(0.025, a=post_shape, scale=1.0/post_rate)
        rt_upper = gamma_dist.ppf(0.975, a=post_shape, scale=1.0/post_rate)
        return rt_mean, rt_lower, rt_upper
    return None, None, None


# ============================================================
# RETROSPECTIVE EpiEstim (full season, for comparison)
# ============================================================

def epiestim_retrospective(incidence, si, window=4):
    """Standard retrospective EpiEstim using all data."""
    n = len(incidence)
    lambdas = np.zeros(n)
    for t in range(1, n):
        for s in range(1, min(t + 1, len(si))):
            lambdas[t] += incidence[t - s] * si[s]

    onset_idx = None
    for t in range(window, n):
        t_start = t - window + 1
        sum_I = np.sum(incidence[t_start:t + 1])
        sum_L = np.sum(lambdas[t_start:t + 1])
        if (0.2 + sum_L) > 0:
            rt = (1.0 + sum_I) / (0.2 + sum_L)
            if rt > 1.0 and onset_idx is None:
                onset_idx = t
    return onset_idx


# ============================================================
# MAIN
# ============================================================

CHP_THRESHOLD = 0.0494
SI_MEAN = 3.0
SI_SD = 1.5

SEASONS = [
    ("2014/15", "2014-10-01", "2015-06-01"),
    ("2015/16", "2015-10-01", "2016-06-01"),
    ("2018/19", "2018-09-15", "2019-06-01"),
    ("2023 S", "2023-01-15", "2023-10-01"),
    ("2023/24", "2023-07-15", "2024-04-01"),
    ("2024/25", "2024-08-01", "2025-04-01"),
]

print("=" * 80)
print("PSEUDO-PROSPECTIVE EpiEstim EVALUATION (Vijay Comment 93)")
print("  At each week t, EpiEstim uses only data up to week t")
print("  Simulates real-time deployment without future data")
print("=" * 80)

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
    positivity = season["AandB_proportion"].values
    incidence = (positivity * 10000).astype(float)
    incidence = np.maximum(incidence, 0)

    si = discretized_si(SI_MEAN, SI_SD, max_t=len(season))

    # CHP threshold onset
    above = season[season["AandB_proportion"] > CHP_THRESHOLD]
    chp_onset_idx = season.index.get_loc(above.index[0]) if len(above) > 0 else None
    chp_onset_date = dates[chp_onset_idx] if chp_onset_idx is not None else None

    # Retrospective onset (full season)
    retro_idx = epiestim_retrospective(incidence, si)
    retro_date = dates[retro_idx] if retro_idx is not None else None

    # Pseudo-prospective: week by week
    prospective_onset_idx = None
    prospective_rt_series = []

    for t in range(4, len(season)):
        # Use only data up to week t
        truncated = incidence[:t + 1]
        si_trunc = discretized_si(SI_MEAN, SI_SD, max_t=len(truncated))
        rt_mean, rt_lower, rt_upper = epiestim_at_week(truncated, si_trunc)

        prospective_rt_series.append({
            "week": t,
            "date": dates[t],
            "rt_mean": rt_mean,
            "rt_lower": rt_lower,
            "rt_upper": rt_upper,
        })

        if rt_mean is not None and rt_mean > 1.0 and prospective_onset_idx is None:
            prospective_onset_idx = t

    prosp_date = dates[prospective_onset_idx] if prospective_onset_idx is not None else None

    # Compute delays
    retro_lead = None
    prosp_lead = None
    prosp_delay = None

    if chp_onset_date is not None:
        if retro_date is not None:
            retro_lead = (pd.Timestamp(chp_onset_date) - pd.Timestamp(retro_date)).days
        if prosp_date is not None:
            prosp_lead = (pd.Timestamp(chp_onset_date) - pd.Timestamp(prosp_date)).days
    if retro_date is not None and prosp_date is not None:
        prosp_delay = (pd.Timestamp(prosp_date) - pd.Timestamp(retro_date)).days

    result = {
        "season": sname,
        "chp_onset": pd.Timestamp(chp_onset_date).strftime("%Y-%m-%d") if chp_onset_date is not None else None,
        "retro_onset": pd.Timestamp(retro_date).strftime("%Y-%m-%d") if retro_date is not None else None,
        "retro_lead": retro_lead,
        "prosp_onset": pd.Timestamp(prosp_date).strftime("%Y-%m-%d") if prosp_date is not None else None,
        "prosp_lead": prosp_lead,
        "prosp_delay": prosp_delay,
    }
    results.append(result)

    print(f"\n  {sname}:")
    print(f"    CHP threshold:     {result['chp_onset']}")
    print(f"    Retro onset:       {result['retro_onset']} (lead: {retro_lead:+d}d)" if retro_lead is not None else f"    Retro onset:       N/D")
    print(f"    Prospective onset: {result['prosp_onset']} (lead: {prosp_lead:+d}d)" if prosp_lead is not None else f"    Prospective onset: N/D")
    if prosp_delay is not None:
        print(f"    Prospective delay: {prosp_delay:+d}d vs retrospective")

results_df = pd.DataFrame(results)
results_df.to_csv("pseudo_prospective_results.csv", index=False)

# ============================================================
# SUMMARY
# ============================================================
print(f"\n\n{'='*80}")
print("SUMMARY: Retrospective vs Pseudo-Prospective Onset Detection")
print(f"{'='*80}")
print(f"\n{'Season':<12} {'CHP':>12} {'Retro':>12} {'Retro lead':>12} {'Prosp':>12} {'Prosp lead':>12} {'Delay':>8}")
print("-" * 82)

for r in results:
    chp = r["chp_onset"] or "N/D"
    retro = r["retro_onset"] or "N/D"
    rl = f"{r['retro_lead']:+d}" if r["retro_lead"] is not None else "N/A"
    prosp = r["prosp_onset"] or "N/D"
    pl = f"{r['prosp_lead']:+d}" if r["prosp_lead"] is not None else "N/A"
    delay = f"{r['prosp_delay']:+d}" if r["prosp_delay"] is not None else "N/A"
    print(f"{r['season']:<12} {chp:>12} {retro:>12} {rl:>12} {prosp:>12} {pl:>12} {delay:>8}")

valid = [r for r in results if r["prosp_delay"] is not None]
if valid:
    delays = [r["prosp_delay"] for r in valid]
    print(f"\n  Prospective delay vs retrospective:")
    print(f"    Median: {np.median(delays):.0f} days")
    print(f"    Mean: {np.mean(delays):.1f} days")
    print(f"    Range: {min(delays)} to {max(delays)} days")

    # How many seasons still lead CHP prospectively?
    prosp_leads = [r for r in results if r["prosp_lead"] is not None and r["prosp_lead"] > 0]
    print(f"    Seasons where prospective still leads CHP: {len(prosp_leads)}/{len(valid)}")

print(f"\n{'='*80}")
print("INTERPRETATION:")
print("  If prospective delay is small (0-7 days):")
print("    -> Retrospective lead times are achievable in practice")
print("  If prospective delay is large (>14 days):")
print("    -> Retrospective results overstate real-time performance")
print("  If some seasons lose their lead entirely:")
print("    -> Report which seasons and by how much")
print(f"{'='*80}")
print(f"\nResults saved to pseudo_prospective_results.csv")
