"""
Outstanding Analyses — Vijay's Comments
==========================================
Addresses Comments 8, 26, 48/49, 101 in one run.

1. Fix degenerate EpiEstim admissions (Comment 8)
   - Re-run with Gamma(0.001, 0.001) vague prior and normalised scaling
2. Wilcoxon signed-rank test (Comment 26)
   - Paired test for admissions vs positivity with CI and effect size
3. Simulation study with multiple replicates (Comments 48/49)
   - 50 replicates per scenario, distributional summaries
4. RSV SI sensitivity sweep (Comment 101)
   - 20 configurations matching the influenza sweep

Run: conda activate pinn && python outstanding_analyses.py
Requires: flux_data.csv, chp_respiratory_cleaned.csv

Thomas Yuan — HKU PhD, Pathogen Evolution Lab
"""

import numpy as np
import pandas as pd
from scipy.stats import gamma as gamma_dist, wilcoxon, mannwhitneyu
from scipy.integrate import odeint
import warnings
warnings.filterwarnings("ignore")

np.random.seed(42)

# ============================================================
# SHARED: EpiEstim implementation
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
            # CI: gamma quantiles
            rt_lower = gamma_dist.ppf(0.025, a=post_shape, scale=1.0/post_rate)
            rt_upper = gamma_dist.ppf(0.975, a=post_shape, scale=1.0/post_rate)
        else:
            rt_mean = rt_lower = rt_upper = np.nan
        results.append({"t_idx": t, "Rt_mean": rt_mean, "Rt_lower": rt_lower, "Rt_upper": rt_upper})
    return pd.DataFrame(results)


# ============================================================
# ANALYSIS 1: Fix degenerate EpiEstim admissions
# ============================================================
print("=" * 80)
print("ANALYSIS 1: Fix degenerate EpiEstim admissions (Comment 8)")
print("  Using normalised scaling + vague prior Gamma(0.001, 0.001)")
print("=" * 80)

df = pd.read_csv("flux_data.csv")
df["From"] = pd.to_datetime(df["From"], format="%d/%m/%Y")
df["To"] = pd.to_datetime(df["To"], format="%d/%m/%Y")
df["MidDate"] = df["From"] + (df["To"] - df["From"]) / 2

CHP_THRESHOLD = 0.0494
SI_MEAN = 3.0
SI_SD = 1.5

SEASONS = [
    ("2014/15", "2014-10-01", "2015-06-01"),
    ("2015/16", "2015-10-01", "2016-06-01"),
    ("2016/17", "2016-09-15", "2017-06-01"),
    ("2017/18", "2017-04-01", "2018-04-01"),
    ("2018/19", "2018-09-15", "2019-06-01"),
    ("2023 S", "2023-01-15", "2023-10-01"),
    ("2023/24", "2023-07-15", "2024-04-01"),
    ("2024/25", "2024-08-01", "2025-04-01"),
]

SIGNALS = [
    ("AandB_proportion", "Lab positivity"),
    ("Adm_All", "All ages"),
    ("Adm_0_5", "0-5y"),
    ("Adm_6_11", "6-11y"),
    ("Adm_12_17", "12-17y"),
    ("Adm_65_higher", "65+"),
]

def run_epiestim_fixed(df, start, end, signal_col, si_mean=3.0, si_sd=1.5):
    mask = (df["MidDate"] >= start) & (df["MidDate"] <= end)
    season = df.loc[mask].dropna(subset=[signal_col]).sort_values("MidDate").reset_index(drop=True)
    if len(season) < 8:
        return None, None, None

    raw = season[signal_col].values
    # Normalise: divide by max to get 0-1 range, then multiply by 1000
    # This keeps all signals on the same scale
    max_val = raw.max()
    if max_val == 0:
        return None, None, None
    incidence = (raw / max_val * 1000).astype(float)

    si = discretized_si(si_mean, si_sd, max_t=len(season))
    # Use very vague prior so it doesn't dominate
    rt_df = estimate_R(incidence, si, window=4, prior_shape=0.001, prior_rate=0.001)

    if len(rt_df) == 0:
        return None, None, None

    rt_df["MidDate"] = season.iloc[rt_df["t_idx"].values]["MidDate"].values
    best_Rt = rt_df["Rt_mean"].max()

    # Onset: mean > 1
    onset_mean = rt_df[rt_df["Rt_mean"] > 1.0]
    onset_date = onset_mean.iloc[0]["MidDate"] if len(onset_mean) > 0 else None

    # Onset: CI lower > 1 (conservative)
    onset_ci = rt_df[rt_df["Rt_lower"] > 1.0]
    onset_ci_date = onset_ci.iloc[0]["MidDate"] if len(onset_ci) > 0 else None

    return onset_date, onset_ci_date, best_Rt

# Run all
fixed_results = []
for sname, start, end in SEASONS:
    chp_mask = (df["MidDate"] >= start) & (df["MidDate"] <= end)
    chp_season = df.loc[chp_mask]
    above = chp_season[chp_season["AandB_proportion"] > CHP_THRESHOLD]
    chp_onset = above.iloc[0]["MidDate"] if len(above) > 0 else None

    for scol, slab in SIGNALS:
        onset, onset_ci, best_rt = run_epiestim_fixed(df, start, end, scol)
        lead = (chp_onset - onset).days if onset is not None and chp_onset is not None else None
        lead_ci = (chp_onset - onset_ci).days if onset_ci is not None and chp_onset is not None else None
        fixed_results.append({
            "season": sname, "signal": slab, "onset_mean": onset,
            "onset_ci": onset_ci, "lead_mean": lead, "lead_ci": lead_ci,
            "best_Rt": round(best_rt, 2) if best_rt else None
        })

fixed_df = pd.DataFrame(fixed_results)
fixed_df.to_csv("epiestim_fixed_scaling.csv", index=False)

# Print comparison for the degenerate seasons
print("\nFixed scaling results for previously degenerate seasons:")
print(f"{'Season':<10} {'Signal':<15} {'Max R(t)':>10} {'Lead(mean)':>12} {'Lead(CI)':>10}")
print("-" * 60)
for _, r in fixed_df.iterrows():
    if r["season"] in ["2014/15", "2015/16"] and r["signal"] in ["12-17y", "Lab positivity"]:
        ld = f"{r['lead_mean']:+.0f}" if r["lead_mean"] is not None else "N/A"
        lci = f"{r['lead_ci']:+.0f}" if r["lead_ci"] is not None else "N/A"
        rt = f"{r['best_Rt']:.2f}" if r["best_Rt"] else "N/A"
        print(f"{r['season']:<10} {r['signal']:<15} {rt:>10} {ld:>12} {lci:>10}")

# Full table
print(f"\n{'Season':<10} {'Signal':<15} {'Max R(t)':>10} {'Lead(mean)':>12}")
print("-" * 50)
for _, r in fixed_df.iterrows():
    ld = f"{r['lead_mean']:+.0f}" if r["lead_mean"] is not None else "N/A"
    rt = f"{r['best_Rt']:.2f}" if r["best_Rt"] else "N/A"
    print(f"{r['season']:<10} {r['signal']:<15} {rt:>10} {ld:>12}")


# ============================================================
# ANALYSIS 2: Wilcoxon signed-rank test (Comment 26)
# ============================================================
print(f"\n\n{'='*80}")
print("ANALYSIS 2: Wilcoxon signed-rank test — admissions vs positivity (Comment 26)")
print("=" * 80)

# Get paired lead times: positivity vs 12-17y admissions
pos_leads = []
adm_leads = []
season_names = []

for sname, start, end in SEASONS:
    pos_row = fixed_df[(fixed_df["season"] == sname) & (fixed_df["signal"] == "Lab positivity")]
    adm_row = fixed_df[(fixed_df["season"] == sname) & (fixed_df["signal"] == "12-17y")]

    if len(pos_row) > 0 and len(adm_row) > 0:
        pl = pos_row.iloc[0]["lead_mean"]
        al = adm_row.iloc[0]["lead_mean"]
        if pl is not None and al is not None:
            pos_leads.append(pl)
            adm_leads.append(al)
            season_names.append(sname)

pos_arr = np.array(pos_leads)
adm_arr = np.array(adm_leads)
diffs = adm_arr - pos_arr

print(f"\nPaired differences (admissions lead - positivity lead):")
for i, sn in enumerate(season_names):
    print(f"  {sn}: pos={pos_arr[i]:+.0f}d, adm={adm_arr[i]:+.0f}d, diff={diffs[i]:+.0f}d")

print(f"\nMedian difference: {np.median(diffs):.1f} days")
print(f"Mean difference: {np.mean(diffs):.1f} days")
print(f"Ties (diff = 0): {np.sum(diffs == 0)}")

# Remove zeros for Wilcoxon
nonzero = diffs[diffs != 0]
if len(nonzero) >= 3:
    stat, pval = wilcoxon(nonzero, alternative='greater')
    print(f"\nWilcoxon signed-rank test (one-sided: admissions > positivity):")
    print(f"  Test statistic: {stat}")
    print(f"  p-value: {pval:.4f}")
    print(f"  n (non-zero pairs): {len(nonzero)}")

    # Bootstrap CI for median difference
    n_boot = 10000
    boot_medians = []
    for _ in range(n_boot):
        idx = np.random.choice(len(diffs), size=len(diffs), replace=True)
        boot_medians.append(np.median(diffs[idx]))
    ci_lower = np.percentile(boot_medians, 2.5)
    ci_upper = np.percentile(boot_medians, 97.5)
    print(f"\nBootstrap 95% CI for median difference: [{ci_lower:.1f}, {ci_upper:.1f}] days")
else:
    print(f"\nToo few non-zero pairs ({len(nonzero)}) for Wilcoxon test")

# Effect size: rank-biserial correlation
if len(nonzero) >= 3:
    r_effect = 1 - (2 * stat) / (len(nonzero) * (len(nonzero) + 1) / 2)
    print(f"Rank-biserial correlation (effect size): {r_effect:.3f}")


# ============================================================
# ANALYSIS 3: Simulation study with multiple replicates (Comments 48/49)
# ============================================================
print(f"\n\n{'='*80}")
print("ANALYSIS 3: Simulation study — 50 replicates per scenario (Comments 48/49)")
print("=" * 80)

def seir_odes(y, t, beta_func, sigma, gamma):
    S, E, I, R = y
    beta = beta_func(t)
    dSdt = -beta * S * I
    dEdt = beta * S * I - sigma * E
    dIdt = sigma * E - gamma * I
    dRdt = gamma * I
    return [dSdt, dIdt, dEdt, dRdt]

def sigmoid_beta(t, beta_min=0.15, beta_max=0.36, t_mid=40, k=0.15):
    return beta_min + (beta_max - beta_min) / (1 + np.exp(-k * (t - t_mid)))

# True parameters
SIGMA_TRUE = 0.5
GAMMA_TRUE = 0.2

# Generate one epidemic
def generate_epidemic(n_days=150, seed=None):
    if seed is not None:
        np.random.seed(seed)
    t = np.arange(n_days)
    y0 = [0.999, 0.0005, 0.0005, 0.0]
    sol = odeint(seir_odes, y0, t, args=(sigmoid_beta, SIGMA_TRUE, GAMMA_TRUE))
    S, E, I, R = sol[:, 0], sol[:, 1], sol[:, 2], sol[:, 3]
    true_Rt = np.array([sigmoid_beta(ti) * S[ti] / GAMMA_TRUE for ti in range(len(t))])
    return t, S, E, I, R, true_Rt

def apply_observation(I_true, scenario, seed=None):
    if seed is not None:
        np.random.seed(seed)
    if scenario == "perfect":
        return I_true.copy()
    elif scenario == "scaled":
        return I_true * 0.15
    elif scenario == "noisy":
        return I_true + np.random.normal(0, 0.005, len(I_true))
    elif scenario == "delayed":
        obs = np.zeros_like(I_true)
        obs[2:] = I_true[:-2]
        return obs
    elif scenario == "filtered":
        return np.convolve(I_true, np.ones(3)/3, mode='same')
    elif scenario == "thresholded":
        obs = I_true.copy()
        obs[obs < 0.01] = 0
        return obs
    return I_true

def estimate_Rt_simple(observed, gamma_est, window=7):
    """Simple ratio-based R(t) estimation for simulation."""
    n = len(observed)
    Rt = np.zeros(n)
    for t in range(window, n):
        denom = np.sum(observed[t-window:t]) * gamma_est
        if denom > 0:
            numer = observed[t] - observed[t-1] + gamma_est * observed[t]
            Rt[t] = max(0, numer / (observed[t] * gamma_est)) if observed[t] > 0 else 0
        # Simpler: R(t) ~ I(t+1) / I(t) at daily resolution
    # Use generation-based: R(t) ~ I(t+g) / I(t) where g ~ 1/gamma
    g = int(1.0 / gamma_est)
    for t in range(g, n - g):
        if observed[t] > 1e-8:
            Rt[t] = observed[t + g] / observed[t]
    return Rt

SCENARIOS = ["perfect", "scaled", "noisy", "delayed", "filtered", "thresholded"]
N_REPS = 50

print(f"\nRunning {N_REPS} replicates × {len(SCENARIOS)} scenarios × 2 param conditions...")

sim_results = []
for scenario in SCENARIOS:
    for param_type in ["fixed", "free"]:
        correlations = []
        gamma_estimates = []

        for rep in range(N_REPS):
            seed = rep * 100
            t, S, E, I, R, true_Rt = generate_epidemic(seed=seed)
            observed = apply_observation(I, scenario, seed=seed + 1)
            observed = np.maximum(observed, 0)

            if param_type == "fixed":
                gamma_est = GAMMA_TRUE
            else:
                # Free gamma: estimate from data (simulate drift)
                # Use observed peak timing to estimate gamma
                peak_idx = np.argmax(observed)
                if peak_idx > 10 and observed[peak_idx] > 0:
                    # Estimate from decay rate after peak
                    decay_window = min(20, len(observed) - peak_idx - 1)
                    if decay_window > 5:
                        post_peak = observed[peak_idx:peak_idx + decay_window]
                        post_peak = post_peak[post_peak > 0]
                        if len(post_peak) > 3:
                            log_decay = np.log(post_peak)
                            slope = np.polyfit(range(len(log_decay)), log_decay, 1)[0]
                            gamma_est = max(0.05, min(0.5, -slope))
                        else:
                            gamma_est = 0.15
                    else:
                        gamma_est = 0.15
                else:
                    gamma_est = 0.15

            est_Rt = estimate_Rt_simple(observed, gamma_est)

            # Correlate over the epidemic period (days 20-120)
            valid = (true_Rt[20:120] > 0.1) & (est_Rt[20:120] > 0.01)
            if np.sum(valid) > 10:
                corr = np.corrcoef(true_Rt[20:120][valid], est_Rt[20:120][valid])[0, 1]
                if not np.isnan(corr):
                    correlations.append(corr)
            gamma_estimates.append(gamma_est)

        if len(correlations) > 0:
            sim_results.append({
                "scenario": scenario,
                "params": param_type,
                "n_reps": len(correlations),
                "corr_median": round(np.median(correlations), 3),
                "corr_mean": round(np.mean(correlations), 3),
                "corr_q025": round(np.percentile(correlations, 2.5), 3),
                "corr_q975": round(np.percentile(correlations, 97.5), 3),
                "gamma_median": round(np.median(gamma_estimates), 4),
                "gamma_q025": round(np.percentile(gamma_estimates, 2.5), 4),
                "gamma_q975": round(np.percentile(gamma_estimates, 97.5), 4),
            })

sim_df = pd.DataFrame(sim_results)
sim_df.to_csv("simulation_results_50reps.csv", index=False)

print(f"\n{'Scenario':<14} {'Params':<6} {'n':>3} {'r median':>9} {'r [2.5%, 97.5%]':>20} {'gamma med':>10}")
print("-" * 70)
for _, r in sim_df.iterrows():
    ci_str = f"[{r['corr_q025']:.3f}, {r['corr_q975']:.3f}]"
    print(f"{r['scenario']:<14} {r['params']:<6} {r['n_reps']:>3} {r['corr_median']:>9.3f} {ci_str:>20} {r['gamma_median']:>10.4f}")


# ============================================================
# ANALYSIS 4: RSV SI sensitivity sweep (Comment 101)
# ============================================================
print(f"\n\n{'='*80}")
print("ANALYSIS 4: RSV EpiEstim SI sensitivity sweep (Comment 101)")
print("  20 configurations: 5 SI means × 4 window widths")
print("=" * 80)

try:
    rsv_df = pd.read_csv("chp_respiratory_cleaned.csv")
    rsv_df["From"] = pd.to_datetime(rsv_df["From"])
    rsv_df["To"] = pd.to_datetime(rsv_df["To"])
    rsv_df["MidDate"] = rsv_df["From"] + (rsv_df["To"] - rsv_df["From"]) / 2
    has_rsv = True
except:
    print("  RSV data not found, skipping")
    has_rsv = False

RSV_THRESHOLD = 0.0187
RSV_SEASONS = [
    ("2017 sum", "2017-01-01", "2017-12-01"),
    ("2018 sum", "2018-01-01", "2018-12-01"),
    ("2021/22", "2021-04-01", "2022-04-01"),
]

SI_MEANS = [5.0, 6.0, 7.5, 9.0, 10.0]
WINDOWS = [3, 4, 5, 6]

if has_rsv:
    rsv_sensitivity = []

    for test_season, start, end in RSV_SEASONS:
        mask = (rsv_df["MidDate"] >= start) & (rsv_df["MidDate"] <= end)
        season = rsv_df.loc[mask].dropna(subset=["RSV_pct"]).sort_values("MidDate").reset_index(drop=True)

        if len(season) < 10:
            continue

        # CHP-equivalent threshold onset
        above = season[season["RSV_pct"] > RSV_THRESHOLD * 100]
        rsv_chp = above.iloc[0]["MidDate"] if len(above) > 0 else None

        for si_mean in SI_MEANS:
            for win in WINDOWS:
                si_sd = si_mean * 0.4  # roughly proportional SD
                incidence = (season["RSV_pct"].values / 100 * 10000).astype(float)
                incidence = np.maximum(incidence, 0)

                si = discretized_si(si_mean, si_sd, max_t=len(season))
                rt_df = estimate_R(incidence, si, window=win)

                if len(rt_df) > 0:
                    rt_df["MidDate"] = season.iloc[rt_df["t_idx"].values]["MidDate"].values
                    onset_rows = rt_df[rt_df["Rt_mean"] > 1.0]
                    onset = onset_rows.iloc[0]["MidDate"] if len(onset_rows) > 0 else None
                    lead = (rsv_chp - onset).days if onset is not None and rsv_chp is not None else None

                    rsv_sensitivity.append({
                        "season": test_season,
                        "si_mean": si_mean,
                        "si_sd": round(si_sd, 1),
                        "window": win,
                        "onset": onset,
                        "lead": lead,
                    })

    rsv_sens_df = pd.DataFrame(rsv_sensitivity)
    rsv_sens_df.to_csv("rsv_si_sensitivity.csv", index=False)

    # Summary per season
    for test_season, _, _ in RSV_SEASONS:
        sub = rsv_sens_df[rsv_sens_df["season"] == test_season]
        valid = sub.dropna(subset=["lead"])
        if len(valid) > 0:
            print(f"\n  {test_season}: {len(valid)}/{len(sub)} configs detected onset")
            print(f"    Lead time range: {valid['lead'].min():.0f} to {valid['lead'].max():.0f} days")
            print(f"    Lead time SD: {valid['lead'].std():.1f} days")
            print(f"    Mean lead: {valid['lead'].mean():.1f} days")
        else:
            print(f"\n  {test_season}: no configs detected onset")


# ============================================================
# SUMMARY
# ============================================================
print(f"\n\n{'='*80}")
print("ALL ANALYSES COMPLETE")
print("=" * 80)
print("Output files:")
print("  epiestim_fixed_scaling.csv — fixed admissions scaling (Comment 8)")
print("  simulation_results_50reps.csv — simulation study (Comments 48/49)")
print("  rsv_si_sensitivity.csv — RSV SI sweep (Comment 101)")
print("\nResults to incorporate into manuscript:")
print("  1. Check whether degenerate R(t) is resolved with normalised scaling")
print("  2. Report Wilcoxon test statistic, p-value, and bootstrap CI")
print("  3. Replace single-replicate simulation numbers with distributional summaries")
print("  4. Report RSV SI sensitivity range and compare to influenza (SD 8 days)")
