"""
EpiEstim: Hospital Admissions vs Lab Positivity
=================================================
Same EpiEstim R(t) framework, different input signal.
Tests whether admissions-based R(t) detects onset earlier
than positivity-based R(t).

If it does, the paper goes from "here's a problem" to
"here's the problem AND the solution."

Run: conda activate pinn && python epiestim_admissions.py
Requires: flux_data.csv in same directory

Thomas Yuan — HKU PhD, Pathogen Evolution Lab
"""

import numpy as np
import pandas as pd
from scipy.stats import gamma as gamma_dist
import warnings
import os

warnings.filterwarnings("ignore")

# ============================================================
# PARAMETERS
# ============================================================
SI_MEAN_DAYS = 3.0
SI_SD_DAYS = 1.5
CHP_THRESHOLD = 0.0494  # for lab positivity onset reference

# Admission signals to test
ADMISSION_SIGNALS = [
    ("Adm_All", "All ages"),
    ("Adm_0_5", "0-5 years"),
    ("Adm_6_11", "6-11 years"),
    ("Adm_12_17", "12-17 years"),
    ("Adm_65_higher", "65+ years"),
]

# ============================================================
# CORI et al. 2013
# ============================================================

def discretized_serial_interval(mean_si, sd_si, max_t, time_unit=7.0):
    shape = (mean_si / sd_si) ** 2
    scale = sd_si ** 2 / mean_si
    si = np.zeros(max_t)
    for t in range(1, max_t):
        lo = (t - 0.5) * time_unit
        hi = (t + 0.5) * time_unit
        si[t] = gamma_dist.cdf(hi, a=shape, scale=scale) - \
                gamma_dist.cdf(max(0, lo), a=shape, scale=scale)
    total = si.sum()
    if total > 0:
        si /= total
    return si


def estimate_R(incidence, si, window=4, prior_shape=1.0, prior_rate=0.2):
    n = len(incidence)
    max_si = len(si)
    lambdas = np.zeros(n)
    for t in range(1, n):
        for s in range(1, min(t + 1, max_si)):
            lambdas[t] += incidence[t - s] * si[s]
    results = []
    for t in range(window, n):
        t_start = t - window + 1
        sum_I = np.sum(incidence[t_start:t + 1])
        sum_L = np.sum(lambdas[t_start:t + 1])
        post_shape = prior_shape + sum_I
        post_rate = prior_rate + sum_L
        if post_rate > 0:
            rt_mean = post_shape / post_rate
        else:
            rt_mean = np.nan
        results.append({"t_idx": t, "Rt_mean": rt_mean})
    return pd.DataFrame(results)


# ============================================================
# SEASON DEFINITIONS
# ============================================================

SEASONS = [
    ("2014/15 winter", "2014-10-01", "2015-06-01"),
    ("2015/16 winter", "2015-10-01", "2016-06-01"),
    ("2016/17 winter", "2016-09-15", "2017-06-01"),
    ("2017/18 summer", "2017-04-01", "2018-04-01"),
    ("2018/19 winter", "2018-09-15", "2019-06-01"),
    ("2023 summer",    "2023-01-15", "2023-10-01"),
    ("2023/24 winter", "2023-07-15", "2024-04-01"),
    ("2024/25 winter", "2024-08-01", "2025-04-01"),
]

SCALE_FACTOR = 10000


# ============================================================
# RUN EpiEstim ON ONE SIGNAL FOR ONE SEASON
# ============================================================

def run_epiestim(df, start_date, end_date, season_name, signal_col, scale=SCALE_FACTOR):
    mask = (df["MidDate"] >= start_date) & (df["MidDate"] <= end_date)
    season = df.loc[mask].dropna(subset=[signal_col]).copy()
    season = season.sort_values("MidDate").reset_index(drop=True)

    if len(season) < 8:
        return None

    incidence = (season[signal_col].values * scale).astype(float)
    incidence = np.maximum(incidence, 0)

    si = discretized_serial_interval(SI_MEAN_DAYS, SI_SD_DAYS, max_t=len(season))
    rt_df = estimate_R(incidence, si, window=4)

    if len(rt_df) == 0:
        return None

    rt_df["MidDate"] = season.iloc[rt_df["t_idx"].values]["MidDate"].values
    best_Rt = rt_df["Rt_mean"].max()

    # Onset: first week R(t) > 1
    onset_rows = rt_df[rt_df["Rt_mean"] > 1.0]
    onset_date = onset_rows.iloc[0]["MidDate"].strftime("%Y-%m-%d") if len(onset_rows) > 0 else None

    return {
        "season_name": season_name,
        "signal": signal_col,
        "onset_date": onset_date,
        "best_Rt": round(best_Rt, 3),
        "n_weeks": len(season),
    }


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print("=" * 90)
    print("EpiEstim: HOSPITAL ADMISSIONS vs LAB POSITIVITY")
    print("Which signal detects influenza onset earliest?")
    print("=" * 90)

    df = pd.read_csv("flux_data.csv")
    df["From"] = pd.to_datetime(df["From"], format="%d/%m/%Y")
    df["To"] = pd.to_datetime(df["To"], format="%d/%m/%Y")
    df["MidDate"] = df["From"] + (df["To"] - df["From"]) / 2

    print(f"\nLoaded {len(df)} weeks of CHP Flu Express data")

    # All signals to test: positivity + 5 admission signals
    all_signals = [("AandB_proportion", "Lab positivity")] + ADMISSION_SIGNALS

    # ========================================================
    # RUN ALL COMBINATIONS
    # ========================================================
    all_results = []

    for signal_col, signal_name in all_signals:
        # Check data availability
        n_valid = df[signal_col].notna().sum()
        print(f"\n  Signal: {signal_name} ({signal_col}) — {n_valid}/{len(df)} weeks available")

        for season_name, start, end in SEASONS:
            # For admissions, scale differently (values are per 10,000 already)
            # Use raw values * 10000 for pseudo-incidence
            if signal_col.startswith("Adm"):
                scale = 100000  # admissions are small numbers, need bigger scale
            else:
                scale = SCALE_FACTOR

            res = run_epiestim(df, start, end, season_name, signal_col, scale=scale)
            if res is not None:
                res["signal_name"] = signal_name
                all_results.append(res)

    results_df = pd.DataFrame(all_results)

    # ========================================================
    # GET CHP THRESHOLD ONSET FOR REFERENCE
    # ========================================================
    chp_onsets = {}
    for season_name, start, end in SEASONS:
        mask = (df["MidDate"] >= start) & (df["MidDate"] <= end)
        season = df.loc[mask]
        above = season[season["AandB_proportion"] > CHP_THRESHOLD]
        if len(above) > 0:
            chp_onsets[season_name] = above.iloc[0]["MidDate"].strftime("%Y-%m-%d")
        else:
            chp_onsets[season_name] = None

    # ========================================================
    # COMPARISON TABLE
    # ========================================================
    print(f"\n\n{'='*120}")
    print("TABLE: EpiEstim Onset Detection by Signal — All Seasons")
    print(f"{'='*120}")

    # Pivot: rows = seasons, columns = signals
    print(f"\n{'Season':<18} {'CHP thresh':>12}", end="")
    for _, signal_name in all_signals:
        print(f" {signal_name:>14}", end="")
    print()
    print("-" * 120)

    for season_name, start, end in SEASONS:
        chp = chp_onsets.get(season_name, "N/A")
        print(f"{season_name:<18} {str(chp):>12}", end="")

        for signal_col, signal_name in all_signals:
            match = results_df[(results_df["season_name"] == season_name) &
                              (results_df["signal"] == signal_col)]
            if len(match) > 0 and match.iloc[0]["onset_date"]:
                print(f" {match.iloc[0]['onset_date']:>14}", end="")
            else:
                print(f" {'N/D':>14}", end="")
        print()

    # ========================================================
    # LEAD TIME COMPARISON
    # ========================================================
    print(f"\n\n{'='*120}")
    print("TABLE: Lead Time (days) by Signal Relative to CHP Threshold")
    print("(Positive = signal detects earlier)")
    print(f"{'='*120}")

    print(f"\n{'Season':<18}", end="")
    for _, signal_name in all_signals:
        print(f" {signal_name:>14}", end="")
    print()
    print("-" * 120)

    lead_by_signal = {col: [] for col, _ in all_signals}

    for season_name, start, end in SEASONS:
        chp = chp_onsets.get(season_name)
        print(f"{season_name:<18}", end="")

        for signal_col, signal_name in all_signals:
            match = results_df[(results_df["season_name"] == season_name) &
                              (results_df["signal"] == signal_col)]
            if len(match) > 0 and match.iloc[0]["onset_date"] and chp:
                lead = (pd.to_datetime(chp) - pd.to_datetime(match.iloc[0]["onset_date"])).days
                lead_by_signal[signal_col].append(lead)
                color = "+" if lead > 0 else ""
                print(f" {color}{lead:>13}", end="")
            else:
                print(f" {'N/A':>14}", end="")
        print()

    # ========================================================
    # SUMMARY
    # ========================================================
    print(f"\n\n{'='*90}")
    print("SUMMARY: Which signal provides earliest onset detection?")
    print(f"{'='*90}")

    print(f"\n{'Signal':<25} {'Seasons':>8} {'Leads':>7} {'Median':>8} {'Mean':>8} {'Best':>8}")
    print("-" * 70)

    for signal_col, signal_name in all_signals:
        leads = lead_by_signal[signal_col]
        if len(leads) > 0:
            leads_arr = np.array(leads)
            n_leads = np.sum(leads_arr > 0)
            median_lead = np.median(leads_arr)
            mean_lead = np.mean(leads_arr)
            best_lead = np.max(leads_arr)
            print(f"{signal_name:<25} {len(leads):>8} {n_leads}/{len(leads):>5} "
                  f"{median_lead:>7.0f}d {mean_lead:>7.1f}d {best_lead:>7.0f}d")

    # ========================================================
    # HEAD-TO-HEAD: ADMISSIONS vs POSITIVITY
    # ========================================================
    print(f"\n\n{'='*90}")
    print("HEAD-TO-HEAD: Does admissions-based R(t) lead positivity-based R(t)?")
    print(f"{'='*90}")

    pos_results = results_df[results_df["signal"] == "AandB_proportion"].set_index("season_name")

    for adm_col, adm_name in ADMISSION_SIGNALS:
        adm_results = results_df[results_df["signal"] == adm_col].set_index("season_name")

        diffs = []
        print(f"\n  {adm_name} vs Lab positivity:")
        for season_name, _, _ in SEASONS:
            if season_name in pos_results.index and season_name in adm_results.index:
                pos_onset = pos_results.loc[season_name, "onset_date"]
                adm_onset = adm_results.loc[season_name, "onset_date"]
                if pos_onset and adm_onset:
                    diff = (pd.to_datetime(pos_onset) - pd.to_datetime(adm_onset)).days
                    diffs.append(diff)
                    sign = "Adm leads" if diff > 0 else ("Pos leads" if diff < 0 else "Same")
                    print(f"    {season_name:<18}: Adm={adm_onset}  Pos={pos_onset}  "
                          f"Diff={diff:+d}d ({sign})")

        if len(diffs) > 0:
            diffs_arr = np.array(diffs)
            adm_leads = np.sum(diffs_arr > 0)
            print(f"    --- {adm_name}: Adm leads in {adm_leads}/{len(diffs)} seasons, "
                  f"median diff = {np.median(diffs_arr):+.0f} days ---")

    # ========================================================
    # SAVE
    # ========================================================
    results_df.to_csv("epiestim_admissions_results.csv", index=False)
    print(f"\n\nResults saved to epiestim_admissions_results.csv")

    print(f"\n{'='*90}")
    print("IF ADMISSIONS LEAD POSITIVITY CONSISTENTLY:")
    print("  -> Paper becomes: 'R(t) from lab positivity fails for low-amplitude")
    print("     pathogens, but hospital admissions resolve this limitation.'")
    print("  -> That's a problem + solution paper = higher-impact journal.")
    print(f"{'='*90}")
