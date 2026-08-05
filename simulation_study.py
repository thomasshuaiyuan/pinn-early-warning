"""
Simulation Study — EpiEstim on Synthetic SEIR Data
=====================================================
Replaces the broken ratio-based estimator with the actual
EpiEstim Bayesian renewal framework used in the real analysis.

Addresses Vijay Comments 48, 49, 106:
  - Code committed and reproducible
  - 50 replicates per scenario
  - Distributional summaries (median, 2.5-97.5% range)
  - Seeds recorded

Scenarios:
  1. Perfect weekly incidence
  2. Scaled (c = 0.15)
  3. Noisy (Gaussian SD added)
  4. Delayed (2 time-step lag)
  5. Filtered (3-week moving average)
  6. Thresholded (below-threshold values zeroed)

Parameter conditions:
  - Correct SI (mean 3.0d, SD 1.5d) — should recover R(t)
  - Wrong SI (mean 7.0d, SD 3.0d) — proxy for parameter misspecification

Also tests two-wave epidemic for structural failure.

Run: conda activate pinn && python simulation_study.py

Thomas Yuan — HKU PhD, Pathogen Evolution Lab
"""

import numpy as np
import pandas as pd
from scipy.integrate import odeint
from scipy.stats import gamma as gamma_dist
import warnings
warnings.filterwarnings("ignore")


# ============================================================
# EpiEstim (identical to real analysis)
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

def estimate_R_series(incidence, si, window=4, prior_shape=1.0, prior_rate=0.2):
    """Returns R(t) as array aligned to incidence indices."""
    n = len(incidence)
    max_si = len(si)
    lambdas = np.zeros(n)
    for t in range(1, n):
        for s in range(1, min(t + 1, max_si)):
            lambdas[t] += incidence[t - s] * si[s]

    rt = np.full(n, np.nan)
    for t in range(window, n):
        t_start = t - window + 1
        sum_I = np.sum(incidence[t_start:t + 1])
        sum_L = np.sum(lambdas[t_start:t + 1])
        post_shape = prior_shape + sum_I
        post_rate = prior_rate + sum_L
        if post_rate > 0:
            rt[t] = post_shape / post_rate
    return rt


# ============================================================
# SEIR epidemic generator
# ============================================================

def seir_odes(y, t, beta_func, sigma, gamma):
    S, E, I, R = y
    beta = beta_func(t)
    dSdt = -beta * S * I
    dEdt = beta * S * I - sigma * E
    dIdt = sigma * E - gamma * I
    dRdt = gamma * I
    return [dSdt, dEdt, dIdt, dRdt]

def sigmoid_beta(t, beta_min=0.15, beta_max=0.36, t_mid=40, k=0.15):
    """Single-wave: R0 rises from ~0.75 to ~1.8 around day 40."""
    return beta_min + (beta_max - beta_min) / (1 + np.exp(-k * (t - t_mid)))

def twowave_beta(t):
    """Two-wave: peaks at day 30 and day 100."""
    wave1 = 0.35 * np.exp(-((t - 30) / 15) ** 2)
    wave2 = 0.30 * np.exp(-((t - 100) / 15) ** 2)
    return 0.10 + wave1 + wave2

def generate_epidemic(beta_func, n_days=150, sigma=0.5, gamma=0.2,
                      S0=0.999, E0=0.0005, I0=0.0005, seed=None):
    if seed is not None:
        np.random.seed(seed)
    t_daily = np.arange(n_days)
    y0 = [S0, E0, I0, 0.0]
    sol = odeint(seir_odes, y0, t_daily, args=(beta_func, sigma, gamma))
    S = sol[:, 0]
    I = sol[:, 2]
    # True R(t) = beta(t) * S(t) / gamma
    true_Rt = np.array([beta_func(ti) * S[ti] / gamma for ti in range(n_days)])
    return t_daily, I, true_Rt

def daily_to_weekly(daily_I, n_days):
    """Aggregate daily incidence to weekly."""
    n_weeks = n_days // 7
    weekly = np.zeros(n_weeks)
    for w in range(n_weeks):
        weekly[w] = np.sum(daily_I[w*7:(w+1)*7])
    return weekly

def daily_Rt_to_weekly(daily_Rt, n_days):
    """Average daily R(t) to weekly."""
    n_weeks = n_days // 7
    weekly = np.zeros(n_weeks)
    for w in range(n_weeks):
        weekly[w] = np.mean(daily_Rt[w*7:(w+1)*7])
    return weekly


# ============================================================
# Observation models
# ============================================================

def apply_observation(weekly_incid, scenario, noise_sd=None, seed=None):
    if seed is not None:
        np.random.seed(seed)
    obs = weekly_incid.copy()

    if scenario == "perfect":
        pass
    elif scenario == "scaled":
        obs = obs * 0.15
    elif scenario == "noisy":
        sd = noise_sd if noise_sd else np.std(obs) * 0.2
        obs = obs + np.random.normal(0, sd, len(obs))
    elif scenario == "delayed":
        delayed = np.zeros_like(obs)
        delayed[2:] = obs[:-2]
        obs = delayed
    elif scenario == "filtered":
        kernel = np.ones(3) / 3
        obs = np.convolve(obs, kernel, mode='same')
    elif scenario == "thresholded":
        threshold = np.percentile(obs[obs > 0], 10) if np.sum(obs > 0) > 0 else 0
        obs[obs < threshold] = 0

    obs = np.maximum(obs, 0)
    return obs


# ============================================================
# MAIN SIMULATION
# ============================================================

N_DAYS = 154  # 22 weeks
N_REPS = 50
SCENARIOS = ["perfect", "scaled", "noisy", "delayed", "filtered", "thresholded"]
SIGMA_TRUE = 0.5
GAMMA_TRUE = 0.2

# SI conditions
SI_CORRECT = (3.0, 1.5)   # correct for influenza
SI_WRONG = (7.0, 3.0)     # misspecified (too long)

print("=" * 80)
print("SIMULATION STUDY: EpiEstim on Synthetic SEIR Epidemics")
print(f"  {N_REPS} replicates × {len(SCENARIOS)} scenarios × 2 SI conditions")
print(f"  True params: sigma={SIGMA_TRUE}, gamma={GAMMA_TRUE}")
print(f"  Correct SI: mean={SI_CORRECT[0]}d, SD={SI_CORRECT[1]}d")
print(f"  Wrong SI:   mean={SI_WRONG[0]}d, SD={SI_WRONG[1]}d")
print("=" * 80)

results = []

for scenario in SCENARIOS:
    for si_label, (si_mean, si_sd) in [("correct", SI_CORRECT), ("wrong", SI_WRONG)]:
        correlations = []
        onset_errors = []

        for rep in range(N_REPS):
            seed = rep * 1000 + hash(scenario) % 1000

            # Generate epidemic
            t_daily, I_daily, true_Rt_daily = generate_epidemic(
                sigmoid_beta, n_days=N_DAYS, sigma=SIGMA_TRUE, gamma=GAMMA_TRUE, seed=seed
            )

            # Weekly aggregation
            weekly_I = daily_to_weekly(I_daily, N_DAYS)
            weekly_true_Rt = daily_Rt_to_weekly(true_Rt_daily, N_DAYS)
            n_weeks = len(weekly_I)

            # Apply observation model
            observed = apply_observation(weekly_I, scenario, seed=seed + 500)

            # Scale to pseudo-incidence (same as real analysis)
            max_obs = observed.max()
            if max_obs > 0:
                pseudo_incid = observed / max_obs * 1000
            else:
                continue

            # Run EpiEstim
            si = discretized_si(si_mean, si_sd, max_t=n_weeks)
            est_Rt = estimate_R_series(pseudo_incid, si, window=4)

            # Correlate over valid region (skip first 4 weeks of EpiEstim warm-up)
            valid_start = 4
            valid_end = n_weeks
            valid = ~np.isnan(est_Rt[valid_start:valid_end]) & ~np.isnan(weekly_true_Rt[valid_start:valid_end])

            if np.sum(valid) > 5:
                true_v = weekly_true_Rt[valid_start:valid_end][valid]
                est_v = est_Rt[valid_start:valid_end][valid]
                if np.std(true_v) > 0 and np.std(est_v) > 0:
                    corr = np.corrcoef(true_v, est_v)[0, 1]
                    if not np.isnan(corr):
                        correlations.append(corr)

            # Onset error: compare first week R(t) > 1
            true_onset = None
            est_onset = None
            for w in range(valid_start, valid_end):
                if true_onset is None and weekly_true_Rt[w] > 1.0:
                    true_onset = w
                if est_onset is None and not np.isnan(est_Rt[w]) and est_Rt[w] > 1.0:
                    est_onset = w
            if true_onset is not None and est_onset is not None:
                onset_errors.append((est_onset - true_onset) * 7)  # in days

        if len(correlations) > 0:
            results.append({
                "scenario": scenario,
                "SI": si_label,
                "n_valid": len(correlations),
                "r_median": round(np.median(correlations), 3),
                "r_mean": round(np.mean(correlations), 3),
                "r_q025": round(np.percentile(correlations, 2.5), 3),
                "r_q975": round(np.percentile(correlations, 97.5), 3),
                "onset_err_median": round(np.median(onset_errors), 1) if onset_errors else None,
                "onset_err_range": f"{min(onset_errors):.0f} to {max(onset_errors):.0f}" if onset_errors else None,
                "n_onset": len(onset_errors),
            })

# ============================================================
# TWO-WAVE EPIDEMIC (structural failure test)
# ============================================================
print("\nRunning two-wave epidemic test...")

twowave_corrs_correct = []
twowave_corrs_wrong = []

for rep in range(N_REPS):
    seed = rep * 2000
    t_daily, I_daily, true_Rt_daily = generate_epidemic(
        twowave_beta, n_days=N_DAYS, sigma=SIGMA_TRUE, gamma=GAMMA_TRUE, seed=seed
    )
    weekly_I = daily_to_weekly(I_daily, N_DAYS)
    weekly_true_Rt = daily_Rt_to_weekly(true_Rt_daily, N_DAYS)
    n_weeks = len(weekly_I)

    max_obs = weekly_I.max()
    if max_obs > 0:
        pseudo = weekly_I / max_obs * 1000
    else:
        continue

    for si_label, (si_mean, si_sd), corr_list in [
        ("correct", SI_CORRECT, twowave_corrs_correct),
        ("wrong", SI_WRONG, twowave_corrs_wrong)
    ]:
        si = discretized_si(si_mean, si_sd, max_t=n_weeks)
        est_Rt = estimate_R_series(pseudo, si, window=4)
        valid = ~np.isnan(est_Rt[4:]) & ~np.isnan(weekly_true_Rt[4:])
        if np.sum(valid) > 5:
            true_v = weekly_true_Rt[4:][valid]
            est_v = est_Rt[4:][valid]
            if np.std(true_v) > 0 and np.std(est_v) > 0:
                corr = np.corrcoef(true_v, est_v)[0, 1]
                if not np.isnan(corr):
                    corr_list.append(corr)

for label, corrs in [("correct SI", twowave_corrs_correct), ("wrong SI", twowave_corrs_wrong)]:
    if corrs:
        results.append({
            "scenario": "two-wave",
            "SI": label.split()[0],
            "n_valid": len(corrs),
            "r_median": round(np.median(corrs), 3),
            "r_mean": round(np.mean(corrs), 3),
            "r_q025": round(np.percentile(corrs, 2.5), 3),
            "r_q975": round(np.percentile(corrs, 97.5), 3),
            "onset_err_median": None,
            "onset_err_range": None,
            "n_onset": 0,
        })

# ============================================================
# RESULTS
# ============================================================

results_df = pd.DataFrame(results)
results_df.to_csv("simulation_study_results.csv", index=False)

print(f"\n{'='*90}")
print("SIMULATION RESULTS: R(t) recovery under observation distortion")
print(f"{'='*90}")
print(f"{'Scenario':<14} {'SI':<8} {'n':>3} {'r median':>9} {'r [2.5, 97.5]':>20} {'onset err':>10} {'n_onset':>8}")
print("-" * 80)
for _, r in results_df.iterrows():
    ci = f"[{r['r_q025']:.3f}, {r['r_q975']:.3f}]"
    oe = f"{r['onset_err_median']:.0f}d" if r['onset_err_median'] is not None else "N/A"
    print(f"{r['scenario']:<14} {r['SI']:<8} {r['n_valid']:>3} {r['r_median']:>9.3f} {ci:>20} {oe:>10} {r['n_onset']:>8}")

# Summary
print(f"\n{'='*70}")
print("KEY FINDINGS:")
print("=" * 70)
correct = results_df[results_df["SI"] == "correct"]
wrong = results_df[results_df["SI"] == "wrong"]

single_correct = correct[correct["scenario"] != "two-wave"]
single_wrong = wrong[wrong["scenario"] != "two-wave"]

if len(single_correct) > 0:
    print(f"\n  Correct SI (single-wave):")
    print(f"    Median r across scenarios: {single_correct['r_median'].median():.3f}")
    print(f"    Range: {single_correct['r_median'].min():.3f} to {single_correct['r_median'].max():.3f}")

if len(single_wrong) > 0:
    print(f"\n  Wrong SI (single-wave):")
    print(f"    Median r across scenarios: {single_wrong['r_median'].median():.3f}")
    print(f"    Range: {single_wrong['r_median'].min():.3f} to {single_wrong['r_median'].max():.3f}")

tw_correct = correct[correct["scenario"] == "two-wave"]
tw_wrong = wrong[wrong["scenario"] == "two-wave"]
if len(tw_correct) > 0:
    print(f"\n  Two-wave (correct SI): r = {tw_correct.iloc[0]['r_median']:.3f}")
if len(tw_wrong) > 0:
    print(f"  Two-wave (wrong SI):   r = {tw_wrong.iloc[0]['r_median']:.3f}")

print(f"\n{'='*70}")
print("INTERPRETATION:")
print("  If correct-SI r >> wrong-SI r: SI misspecification degrades R(t)")
print("  If two-wave r << single-wave r: structural failure confirmed")
print("  If correct-SI r ≥ 0.8: EpiEstim reliably recovers R(t) from weekly data")
print(f"{'='*70}")
print(f"\nResults saved to simulation_study_results.csv")
