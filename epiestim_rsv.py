"""
EpiEstim R(t) Benchmark for RSV
=================================
Estimates R(t) from CHP RSV surveillance data using the Cori et al. 2013
Bayesian framework, and compares onset detection against:
  - RSV positivity threshold (1.87%)
  - SEIR-PINN R(t) estimates (from rsv_validation_results.csv)

RSV serial interval: mean 7.5 days, SD 3.5 days
(Pitzer et al. 2015, Obando-Pacheco et al. 2018)
cf. influenza SI: mean 3.0 days, SD 1.5 days

Run: conda activate pinn && python epiestim_rsv.py
Requires: chp_respiratory_cleaned.csv in same directory

Thomas Yuan — HKU PhD, Pathogen Evolution Lab
"""

import numpy as np
import pandas as pd
from scipy.stats import gamma as gamma_dist
import warnings
import os

warnings.filterwarnings("ignore")

# ============================================================
# RSV SERIAL INTERVAL
# ============================================================
# RSV SI is longer than influenza:
#   Mean: 7.5 days (range 5-10)
#   SD:   3.5 days (range 2-5)
# Sources: Pitzer et al. 2015, Obando-Pacheco et al. 2018
#
# Data is weekly, so we convert to weeks:
#   Mean: 7.5/7 = 1.07 weeks
#   SD:   3.5/7 = 0.50 weeks

SI_MEAN_DAYS = 7.5
SI_SD_DAYS = 3.5

# RSV threshold (from data: non-season mean + 1.96*SD)
RSV_THRESHOLD = 0.0187  # 1.87%

# ============================================================
# CORI et al. 2013 IMPLEMENTATION
# ============================================================

def discretized_serial_interval(mean_si, sd_si, max_t, time_unit=7.0):
    """Discretized gamma-distributed serial interval.

    Args:
        mean_si: mean SI in days
        sd_si: SD of SI in days
        max_t: maximum number of time steps
        time_unit: days per time step (7 for weekly data)
    """
    shape = (mean_si / sd_si) ** 2
    scale = sd_si ** 2 / mean_si

    si = np.zeros(max_t)
    for t in range(1, max_t):
        # probability mass in [t-0.5, t+0.5] time units
        lo = (t - 0.5) * time_unit
        hi = (t + 0.5) * time_unit
        si[t] = gamma_dist.cdf(hi, a=shape, scale=scale) - \
                gamma_dist.cdf(max(0, lo), a=shape, scale=scale)

    total = si.sum()
    if total > 0:
        si /= total
    return si


def estimate_R(incidence, si, window=4, prior_shape=1.0, prior_rate=0.2):
    """Bayesian R(t) estimation (Cori et al. 2013).

    The posterior R(t) is Gamma-distributed:
      shape = prior_shape + sum(I[t-w:t])
      rate  = prior_rate + sum(Lambda[t-w:t])
    where Lambda[t] = sum_s(I[t-s] * w_s) is total infectiousness.

    Returns DataFrame with Rt_mean, Rt_lower (2.5%), Rt_upper (97.5%).
    """
    n = len(incidence)
    max_si = len(si)

    # Compute total infectiousness Lambda[t]
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
            rt_lower = gamma_dist.ppf(0.025, a=post_shape, scale=1.0 / post_rate)
            rt_upper = gamma_dist.ppf(0.975, a=post_shape, scale=1.0 / post_rate)
        else:
            rt_mean = rt_lower = rt_upper = np.nan

        results.append({
            "t_idx": t,
            "Rt_mean": rt_mean,
            "Rt_lower": rt_lower,
            "Rt_upper": rt_upper,
        })

    return pd.DataFrame(results)


# ============================================================
# RSV SEASON DEFINITIONS (matching PINN analysis)
# ============================================================

RSV_SEASONS = [
    ("2014 spring",      "2014-01-01", "2014-08-01"),
    ("2015 summer",      "2015-03-01", "2015-11-01"),
    ("2016 summer",      "2016-03-01", "2016-11-01"),
    ("2017 summer/fall", "2017-03-01", "2017-12-01"),
    ("2018 summer",      "2018-03-01", "2018-11-01"),
    ("2019 summer",      "2019-03-01", "2019-11-01"),
    ("2021/22 rebound",  "2021-06-01", "2022-04-01"),
    ("2022/23 winter",   "2022-06-01", "2023-04-01"),
    ("2023 summer",      "2023-02-01", "2023-12-01"),
    ("2025 summer",      "2025-03-01", "2025-12-01"),
]

SCALE_FACTOR = 10000  # positivity -> pseudo-incidence


# ============================================================
# RUN ONE SEASON
# ============================================================

def run_epiestim_rsv(df, start_date, end_date, season_name, verbose=True):

    mask = (df["MidDate"] >= start_date) & (df["MidDate"] <= end_date)
    season = df.loc[mask].dropna(subset=["RSV_proportion"]).copy()
    season = season.sort_values("MidDate").reset_index(drop=True)

    if len(season) < 8:
        if verbose:
            print(f"  SKIP {season_name}: only {len(season)} data points")
        return None

    if verbose:
        peak_pos = season["RSV_proportion"].max()
        print(f"\n{'='*70}")
        print(f"  SEASON: {season_name}  |  {start_date} -> {end_date}  "
              f"|  {len(season)} weeks  |  peak {peak_pos*100:.1f}%")
        print(f"{'='*70}")

    # Pseudo-incidence from positivity
    incidence = (season["RSV_proportion"].values * SCALE_FACTOR).astype(float)
    incidence = np.maximum(incidence, 0)

    # Serial interval
    si = discretized_serial_interval(SI_MEAN_DAYS, SI_SD_DAYS, max_t=len(season))

    # Estimate R(t)
    rt_df = estimate_R(incidence, si, window=4)

    if len(rt_df) == 0:
        if verbose:
            print("  Not enough data for R(t) estimation")
        return None

    # Map back to dates
    rt_df["MidDate"] = season.iloc[rt_df["t_idx"].values]["MidDate"].values

    best_Rt = rt_df["Rt_mean"].max()

    # EpiEstim onset: first week R(t) mean > 1
    onset_mean = rt_df[rt_df["Rt_mean"] > 1.0]
    epiestim_onset = onset_mean.iloc[0]["MidDate"].strftime("%Y-%m-%d") \
        if len(onset_mean) > 0 else None

    # Strict onset: first week lower CI > 1
    onset_strict = rt_df[rt_df["Rt_lower"] > 1.0]
    epiestim_strict = onset_strict.iloc[0]["MidDate"].strftime("%Y-%m-%d") \
        if len(onset_strict) > 0 else None

    # Threshold onset
    above = season[season["RSV_proportion"] > RSV_THRESHOLD]
    thresh_onset = above.iloc[0]["MidDate"].strftime("%Y-%m-%d") \
        if len(above) > 0 else None

    # Lead time
    if epiestim_onset and thresh_onset:
        lead_days = (pd.to_datetime(thresh_onset) - pd.to_datetime(epiestim_onset)).days
    else:
        lead_days = None

    if verbose:
        print(f"  -> EpiEstim onset (R>1):   {epiestim_onset or 'not detected'}")
        print(f"  -> EpiEstim onset (CI>1):  {epiestim_strict or 'not detected'}")
        print(f"  -> Threshold onset:        {thresh_onset or 'not detected'}")
        if lead_days is not None:
            sign = "EpiEstim leads" if lead_days > 0 else \
                   ("threshold leads" if lead_days < 0 else "same day")
            print(f"  -> Lead time:              {abs(lead_days)} days ({sign})")
        print(f"  -> Best R(t):              {best_Rt:.3f}")

    return {
        "season_name": season_name,
        "pathogen": "RSV",
        "n_weeks": len(season),
        "peak_positivity": round(season["RSV_proportion"].max() * 100, 2),
        "epiestim_onset": epiestim_onset,
        "epiestim_onset_strict": epiestim_strict,
        "threshold_onset": thresh_onset,
        "lead_days": lead_days,
        "best_Rt": round(best_Rt, 3),
    }


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print("=" * 70)
    print("EpiEstim R(t) BENCHMARK — RSV")
    print("Hong Kong CHP Surveillance 2014-2026")
    print("Algorithm: Cori et al. 2013, Am J Epidemiol")
    print(f"Serial interval: mean {SI_MEAN_DAYS} days, SD {SI_SD_DAYS} days")
    print("=" * 70)

    csv_path = "chp_respiratory_cleaned.csv"
    if not os.path.exists(csv_path):
        print(f"\nERROR: {csv_path} not found.")
        exit(1)

    df = pd.read_csv(csv_path)
    df["From"] = pd.to_datetime(df["From"])
    df["To"] = pd.to_datetime(df["To"])
    df["MidDate"] = pd.to_datetime(df["MidDate"])

    print(f"\nLoaded {len(df)} weeks of CHP respiratory data")
    print(f"RSV threshold: {RSV_THRESHOLD*100:.2f}%")

    results = []
    for name, start, end in RSV_SEASONS:
        res = run_epiestim_rsv(df, start, end, name, verbose=True)
        if res is not None:
            results.append(res)

    if not results:
        print("\nNo seasons completed.")
        exit(1)

    results_df = pd.DataFrame(results)
    results_df.to_csv("epiestim_rsv_results.csv", index=False)

    # --------------------------------------------------------
    # RESULTS TABLE
    # --------------------------------------------------------
    print(f"\n\n{'='*100}")
    print("TABLE: EpiEstim R(t) vs Threshold — RSV Onset Detection")
    print(f"{'='*100}")
    print(f"{'Season':<20} {'Wk':>3} {'Peak%':>6} {'EpiEstim':>12} "
          f"{'Threshold':>12} {'Lead(d)':>8} {'R(t)max':>8}")
    print("-" * 100)

    for _, r in results_df.iterrows():
        lead_str = f"{r['lead_days']:.0f}" if pd.notna(r["lead_days"]) else "N/A"
        epi_str = r["epiestim_onset"] if r["epiestim_onset"] else "not det."
        thr_str = r["threshold_onset"] if r["threshold_onset"] else "not det."
        print(f"{r['season_name']:<20} {r['n_weeks']:>3} {r['peak_positivity']:>5.1f}% "
              f"{epi_str:>12} {thr_str:>12} {lead_str:>8} {r['best_Rt']:>8.3f}")

    # Summary
    valid = results_df.dropna(subset=["lead_days"])
    if len(valid) > 0:
        print(f"\n--- Summary ({len(valid)} seasons with both onsets) ---")
        print(f"  Mean lead:   {valid['lead_days'].mean():.1f} days")
        print(f"  Median lead: {valid['lead_days'].median():.1f} days")
        print(f"  Range:       {valid['lead_days'].min():.0f} to {valid['lead_days'].max():.0f} days")
        pos = valid[valid["lead_days"] > 0]
        print(f"  EpiEstim leads: {len(pos)}/{len(valid)}")

    # --------------------------------------------------------
    # CROSS-METHOD COMPARISON (PINN + EpiEstim + threshold)
    # --------------------------------------------------------
    pinn_path = "rsv_validation_results.csv"
    if os.path.exists(pinn_path):
        pinn_df = pd.read_csv(pinn_path)

        print(f"\n\n{'='*120}")
        print("THREE-METHOD RSV COMPARISON: PINN vs EpiEstim vs Threshold")
        print(f"{'='*120}")
        print(f"{'Season':<20} {'Peak%':>6} {'Threshold':>12} "
              f"{'PINN':>12} {'PINN d':>8} "
              f"{'EpiEstim':>12} {'Epi d':>8} {'PINN R(t)':>9} {'Epi R(t)':>9}")
        print("-" * 120)

        for _, epi_row in results_df.iterrows():
            name = epi_row["season_name"]
            pinn_match = pinn_df[pinn_df["season_name"] == name]

            thr_str = epi_row["threshold_onset"] or "N/A"
            epi_str = epi_row["epiestim_onset"] or "N/A"
            epi_lead = f"{epi_row['lead_days']:.0f}" if pd.notna(epi_row["lead_days"]) else "N/A"

            if len(pinn_match) > 0:
                pr = pinn_match.iloc[0]
                pinn_str = pr["pinn_onset_date"] if pd.notna(pr["pinn_onset_date"]) and pr["pinn_onset_date"] else "N/A"
                pinn_lead = f"{pr['lead_days']:.0f}" if pd.notna(pr["lead_days"]) else "N/A"
                pinn_rt = f"{pr['best_Rt']:.3f}"
            else:
                pinn_str = "—"
                pinn_lead = "—"
                pinn_rt = "—"

            print(f"{name:<20} {epi_row['peak_positivity']:>5.1f}% {thr_str:>12} "
                  f"{pinn_str:>12} {pinn_lead:>8} "
                  f"{epi_str:>12} {epi_lead:>8} {pinn_rt:>9} {epi_row['best_Rt']:>9.3f}")

        # Cross-method summary
        print(f"\n--- Cross-method summary ---")
        pinn_valid = pinn_df.dropna(subset=["lead_days"])
        epi_valid = results_df.dropna(subset=["lead_days"])

        print(f"\n  {'Metric':<30} {'PINN':>12} {'EpiEstim':>12}")
        print(f"  {'-'*54}")
        if len(pinn_valid) > 0:
            pinn_pos = len(pinn_valid[pinn_valid["lead_days"] > 0])
            print(f"  {'Seasons analyzed':<30} {len(pinn_df):>12} {len(results_df):>12}")
            print(f"  {'Both onsets detected':<30} {len(pinn_valid):>12} {len(epi_valid):>12}")
            print(f"  {'Method leads (n)':<30} {pinn_pos:>12} {len(epi_valid[epi_valid['lead_days']>0]):>12}")
            print(f"  {'Mean lead (days)':<30} {pinn_valid['lead_days'].mean():>12.1f} {epi_valid['lead_days'].mean():>12.1f}")
            print(f"  {'Median lead (days)':<30} {pinn_valid['lead_days'].median():>12.1f} {epi_valid['lead_days'].median():>12.1f}")

    # --------------------------------------------------------
    # CROSS-PATHOGEN COMPARISON (Flu vs RSV for EpiEstim)
    # --------------------------------------------------------
    flu_epi_path = "epiestim_results.csv"
    if os.path.exists(flu_epi_path):
        flu_epi = pd.read_csv(flu_epi_path)
        flu_valid = flu_epi.dropna(subset=["lead_days"])

        print(f"\n\n{'='*70}")
        print("KEY FINDING: EpiEstim CROSS-PATHOGEN COMPARISON")
        print(f"{'='*70}")
        print(f"\n  {'Metric':<30} {'Flu EpiEstim':>15} {'RSV EpiEstim':>15}")
        print(f"  {'-'*60}")
        print(f"  {'Seasons':<30} {len(flu_epi):>15} {len(results_df):>15}")
        print(f"  {'Method leads':<30} {len(flu_valid[flu_valid['lead_days']>0])}/{len(flu_valid):>12} "
              f"{len(epi_valid[epi_valid['lead_days']>0])}/{len(epi_valid):>12}")
        print(f"  {'Mean lead (days)':<30} {flu_valid['lead_days'].mean():>15.1f} {epi_valid['lead_days'].mean():>15.1f}")
        print(f"  {'Median lead (days)':<30} {flu_valid['lead_days'].median():>15.1f} {epi_valid['lead_days'].median():>15.1f}")

        flu_leads = len(flu_valid[flu_valid['lead_days'] > 0]) / len(flu_valid) * 100
        rsv_leads = len(epi_valid[epi_valid['lead_days'] > 0]) / len(epi_valid) * 100 if len(epi_valid) > 0 else 0

        print(f"\n  INTERPRETATION:")
        if rsv_leads < flu_leads:
            print(f"  EpiEstim also performs WORSE on RSV than influenza.")
            print(f"  This confirms the problem is NOT PINN-specific —")
            print(f"  it's structural: low-amplitude pathogens with thresholds")
            print(f"  close to baseline are harder for ALL R(t) methods.")
            print(f"  This is a key finding for Section 4.5 of the manuscript.")
        else:
            print(f"  EpiEstim performs comparably on RSV and influenza.")

    print(f"\n{'='*70}")
    print("Results saved to epiestim_rsv_results.csv")
    print(f"{'='*70}")
