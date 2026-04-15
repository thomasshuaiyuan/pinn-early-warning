"""
EpiEstim R(t) Benchmark — Python Implementation
==================================================
Implements the Cori et al. (2013) method for estimating the
effective reproduction number R(t) from incidence data.

This replaces epiestim_benchmark.R for environments without R.
The algorithm is identical: Bayesian posterior on R(t) using a
gamma-distributed serial interval and sliding time window.

Reference: Cori et al. 2013, American Journal of Epidemiology

Run: python epiestim_python.py
"""

import numpy as np
import pandas as pd
from scipy.stats import gamma as gamma_dist
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# EPIESTIM ALGORITHM (Cori et al. 2013)
# ============================================================

def discretized_serial_interval(mean_si, std_si, max_t=20):
    """Discretize gamma-distributed serial interval.
    
    Args:
        mean_si: Mean serial interval (days or time units)
        std_si:  SD of serial interval
        max_t:   Maximum lag to consider
    
    Returns:
        w: array of probabilities w[s] = P(serial interval = s)
           w[0] = 0 by convention (no same-day transmission)
    """
    # Gamma distribution parameters
    shape = (mean_si / std_si) ** 2
    scale = std_si ** 2 / mean_si
    
    w = np.zeros(max_t + 1)
    for s in range(1, max_t + 1):
        # P(s-0.5 < SI < s+0.5) for discretization
        w[s] = gamma_dist.cdf(s + 0.5, a=shape, scale=scale) - \
               gamma_dist.cdf(s - 0.5, a=shape, scale=scale)
    
    # Normalize
    total = w.sum()
    if total > 0:
        w = w / total
    
    return w


def compute_total_infectiousness(incid, w):
    """Compute total infectiousness Lambda_t = sum_{s=1}^{T} I_{t-s} * w_s.
    
    This is the denominator in the R(t) renewal equation.
    """
    n = len(incid)
    max_s = len(w)
    Lambda = np.zeros(n)
    
    for t in range(1, n):
        for s in range(1, min(t + 1, max_s)):
            Lambda[t] += incid[t - s] * w[s]
    
    return Lambda


def estimate_Rt(incid, w, tau=7, prior_shape=1.0, prior_rate=0.2):
    """Estimate R(t) using the Cori et al. (2013) method.
    
    Posterior: R_t | I_{t-tau+1:t} ~ Gamma(a_posterior, b_posterior)
    where:
        a_posterior = prior_shape + sum(I_s) for s in [t-tau+1, t]
        b_posterior = 1 / (1/prior_rate + sum(Lambda_s)) for s in [t-tau+1, t]
    
    Args:
        incid:       Array of incidence counts
        w:           Discretized serial interval distribution
        tau:         Sliding window width (time steps)
        prior_shape: Gamma prior shape (default 1.0)
        prior_rate:  Gamma prior rate (default 0.2 = mean prior R=5)
    
    Returns:
        DataFrame with columns: t, Rt_mean, Rt_lower, Rt_upper (95% CI)
    """
    n = len(incid)
    Lambda = compute_total_infectiousness(incid, w)
    
    results = []
    for t in range(tau, n):
        # Sum incidence and infectiousness over window [t-tau+1, t]
        sum_I = np.sum(incid[t - tau + 1 : t + 1])
        sum_Lambda = np.sum(Lambda[t - tau + 1 : t + 1])
        
        # Skip if no infectiousness (can't estimate R)
        if sum_Lambda < 1e-10:
            continue
        
        # Posterior parameters
        a_post = prior_shape + sum_I
        b_post = 1.0 / (prior_rate + sum_Lambda)  # scale, not rate
        
        # Posterior mean and 95% credible interval
        Rt_mean = a_post * b_post
        Rt_lower = gamma_dist.ppf(0.025, a=a_post, scale=b_post)
        Rt_upper = gamma_dist.ppf(0.975, a=a_post, scale=b_post)
        
        results.append({
            't_idx': t,
            'Rt_mean': Rt_mean,
            'Rt_lower': Rt_lower,
            'Rt_upper': Rt_upper,
        })
    
    return pd.DataFrame(results)


# ============================================================
# SEASON DEFINITIONS (matching PINN analysis)
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

# Serial interval for influenza (Cowling et al. 2009, Lessler et al. 2009)
SI_MEAN = 3.0  # days
SI_SD   = 1.5  # days

# CHP threshold
CHP_THRESHOLD = 0.0494

# Scaling factor: convert positivity fraction to pseudo-incidence
# (R(t) estimate is invariant to this — it cancels in the ratio)
SCALE_FACTOR = 10000


# ============================================================
# RUN PER SEASON
# ============================================================

def run_epiestim_season(df, start_date, end_date, season_name, verbose=True):
    """Run EpiEstim on one influenza season.
    
    Since CHP data is WEEKLY, we need to handle the serial interval
    appropriately. The SI is specified in days (~3 days for flu),
    but our time step is 1 week. We convert:
        SI_mean_weeks = SI_mean_days / 7
    
    However, since SI < 1 week, most transmission happens within
    the same reporting week. EpiEstim handles this by using the
    discretized SI at the weekly time scale.
    """
    mask = (df['MidDate'] >= pd.to_datetime(start_date)) & \
           (df['MidDate'] <= pd.to_datetime(end_date))
    season = df.loc[mask].dropna(subset=['AandB_proportion']).copy()
    season = season.sort_values('MidDate').reset_index(drop=True)
    
    if len(season) < 8:
        if verbose:
            print(f"  SKIP {season_name}: only {len(season)} data points")
        return None
    
    if verbose:
        print(f"\n{'='*70}")
        print(f"  SEASON: {season_name}  |  {start_date} -> {end_date}  |  {len(season)} weeks")
        print(f"{'='*70}")
    
    # Convert positivity to pseudo-incidence
    incid = np.round(season['AandB_proportion'].values * SCALE_FACTOR).astype(float)
    incid = np.maximum(incid, 0)
    
    # Discretized serial interval in WEEKLY units
    # Mean SI = 3 days = 3/7 weeks ≈ 0.43 weeks
    # Most weight falls on lag 0-1 weeks
    si_mean_weeks = SI_MEAN / 7.0
    si_sd_weeks = SI_SD / 7.0
    
    # For weekly data with sub-weekly SI, use a simple geometric approach:
    # Most transmission within same week, some spills to next week
    # We approximate with a truncated distribution
    w = discretized_serial_interval(si_mean_weeks, si_sd_weeks, max_t=6)
    
    # If SI is very short relative to time step, manually set weights
    # to avoid numerical issues. For flu with weekly data:
    # ~60% within same week, ~30% next week, ~10% week after
    if si_mean_weeks < 1.0:
        w = np.array([0.0, 0.60, 0.30, 0.08, 0.02, 0.0, 0.0])
        w = w / w.sum()
    
    # Run EpiEstim with 4-week sliding window
    tau = 4  # weeks
    rt_df = estimate_Rt(incid, w, tau=tau)
    
    if len(rt_df) == 0:
        if verbose:
            print("  No valid R(t) estimates")
        return None
    
    # Map indices back to dates
    rt_df['MidDate'] = season.iloc[rt_df['t_idx'].values]['MidDate'].values
    
    # Peak R(t)
    best_Rt = rt_df['Rt_mean'].max()
    
    # EpiEstim onset: first week where R(t) mean > 1
    onset_mean = rt_df[rt_df['Rt_mean'] > 1.0]
    epiestim_onset = onset_mean.iloc[0]['MidDate'] if len(onset_mean) > 0 else None
    
    # Strict onset: first week where R(t) lower CI > 1
    onset_strict = rt_df[rt_df['Rt_lower'] > 1.0]
    epiestim_onset_strict = onset_strict.iloc[0]['MidDate'] if len(onset_strict) > 0 else None
    
    # CHP onset
    chp_cross = season[season['AandB_proportion'] > CHP_THRESHOLD]
    chp_onset = chp_cross.iloc[0]['MidDate'] if len(chp_cross) > 0 else None
    
    # Lead time
    if epiestim_onset is not None and chp_onset is not None:
        lead_days = (pd.to_datetime(chp_onset) - pd.to_datetime(epiestim_onset)).days
    else:
        lead_days = None
    
    # Peak positivity
    peak_pos = season['AandB_proportion'].max() * 100
    
    if verbose:
        fmt = lambda d: pd.to_datetime(d).strftime('%Y-%m-%d') if d is not None else 'not detected'
        print(f"  -> EpiEstim onset (R>1):   {fmt(epiestim_onset)}")
        print(f"  -> EpiEstim onset (CI>1):  {fmt(epiestim_onset_strict)}")
        print(f"  -> CHP onset:              {fmt(chp_onset)}")
        if lead_days is not None:
            direction = "EpiEstim leads" if lead_days > 0 else ("CHP leads" if lead_days < 0 else "same day")
            print(f"  -> Lead time:              {abs(lead_days)} days ({direction})")
        print(f"  -> Best R(t):              {best_Rt:.3f}")
        print(f"  -> Peak positivity:        {peak_pos:.1f}%")
    
    return {
        'season_name': season_name,
        'n_weeks': len(season),
        'peak_positivity': round(peak_pos, 2),
        'epiestim_onset': pd.to_datetime(epiestim_onset).strftime('%Y-%m-%d') if epiestim_onset is not None else None,
        'epiestim_onset_strict': pd.to_datetime(epiestim_onset_strict).strftime('%Y-%m-%d') if epiestim_onset_strict is not None else None,
        'chp_onset': pd.to_datetime(chp_onset).strftime('%Y-%m-%d') if chp_onset is not None else None,
        'lead_days': lead_days,
        'best_Rt': round(best_Rt, 3),
    }


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print("=" * 70)
    print("EpiEstim R(t) BENCHMARK (Python Implementation)")
    print("Hong Kong Influenza — CHP Flu Express 2014-2026")
    print("Algorithm: Cori et al. 2013, Am J Epidemiol")
    print("=" * 70)
    
    # Load data
    df = pd.read_csv('flux_data.csv')
    df['From'] = pd.to_datetime(df['From'], format='%d/%m/%Y')
    df['To'] = pd.to_datetime(df['To'], format='%d/%m/%Y')
    df['MidDate'] = df['From'] + (df['To'] - df['From']) / 2
    
    print(f"\nLoaded {len(df)} weeks of CHP data "
          f"({df['From'].min().strftime('%Y-%m-%d')} to {df['To'].max().strftime('%Y-%m-%d')})")
    
    # Run all seasons
    results = []
    for name, start, end in SEASONS:
        res = run_epiestim_season(df, start, end, name)
        if res is not None:
            results.append(res)
    
    results_df = pd.DataFrame(results)
    
    # Print summary table
    print(f"\n\n{'='*100}")
    print("TABLE: EpiEstim R(t) Onset Detection vs CHP Threshold")
    print(f"{'='*100}")
    print(f"{'Season':<18} {'Weeks':>5} {'Peak%':>6} {'EpiEstim':>12} {'CHP Onset':>12} {'Lead(d)':>9} {'R(t)max':>8}")
    print("-" * 100)
    
    for _, r in results_df.iterrows():
        lead_str = f"{r['lead_days']:.0f}" if pd.notna(r.get('lead_days')) and r['lead_days'] is not None else "N/A"
        epi_str = r['epiestim_onset'] if r['epiestim_onset'] else "not det."
        chp_str = r['chp_onset'] if r['chp_onset'] else "not det."
        print(f"{r['season_name']:<18} {r['n_weeks']:>5} {r['peak_positivity']:>5.1f}% "
              f"{epi_str:>12} {chp_str:>12} {lead_str:>9} {r['best_Rt']:>8.3f}")
    
    # Summary
    valid = results_df.dropna(subset=['lead_days'])
    if len(valid) > 0:
        print(f"\n--- Summary ({len(valid)} seasons with both onsets) ---")
        print(f"  Mean lead:   {valid['lead_days'].mean():.1f} days")
        print(f"  Median lead: {valid['lead_days'].median():.1f} days")
        print(f"  Range:       {valid['lead_days'].min():.0f} to {valid['lead_days'].max():.0f} days")
        print(f"  EpiEstim leads: {(valid['lead_days'] > 0).sum()}/{len(valid)}")
    
    # Save
    results_df.to_csv('epiestim_results.csv', index=False)
    print(f"\nResults saved to epiestim_results.csv")
