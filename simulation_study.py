"""
Simulation Study — FIXED (Vijay Round 2, Item 4)
===================================================
Previous version: 50 deterministic repetitions (not replicates)
This version: genuine stochastic variation via:
  1. Varied epidemic parameters (R0, sigma, gamma) per replicate
  2. Poisson observation noise on ALL scenarios
  3. Different epidemic trajectories per replicate

Run: python simulation_study.py
"""

import numpy as np
import pandas as pd
from scipy.integrate import odeint
from scipy.stats import gamma as gamma_dist
import warnings
warnings.filterwarnings("ignore")

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

def estimate_R_series(incidence, si, window=4):
    n = len(incidence)
    lambdas = np.zeros(n)
    for t in range(1, n):
        for s in range(1, min(t + 1, len(si))):
            lambdas[t] += incidence[t - s] * si[s]
    rt = np.full(n, np.nan)
    for t in range(window, n):
        t_start = t - window + 1
        sum_I = np.sum(incidence[t_start:t + 1])
        sum_L = np.sum(lambdas[t_start:t + 1])
        if (0.2 + sum_L) > 0:
            rt[t] = (1.0 + sum_I) / (0.2 + sum_L)
    return rt

def seir_odes(y, t, beta_func, sigma, gamma):
    S, E, I, R = y
    beta = beta_func(t)
    dSdt = -beta * S * I
    dEdt = beta * S * I - sigma * E
    dIdt = sigma * E - gamma * I
    dRdt = gamma * I
    return [dSdt, dEdt, dIdt, dRdt]

def make_beta_func(beta_min, beta_max, t_mid, k):
    def beta_func(t):
        return beta_min + (beta_max - beta_min) / (1 + np.exp(-k * (t - t_mid)))
    return beta_func

def make_twowave_func(base, amp1, t1, amp2, t2, width):
    def beta_func(t):
        w1 = amp1 * np.exp(-((t - t1) / width) ** 2)
        w2 = amp2 * np.exp(-((t - t2) / width) ** 2)
        return base + w1 + w2
    return beta_func

N_DAYS = 154
N_REPS = 50
SCENARIOS = ["perfect", "scaled", "noisy", "delayed", "filtered", "thresholded"]
SCENARIO_SEED = {name: 10000 * (i + 1) for i, name in enumerate(SCENARIOS)}  # distinct, fixed

print("=" * 80)
print("SIMULATION STUDY (FIXED): Genuine stochastic replicates")
print(f"  {N_REPS} replicates x {len(SCENARIOS)} scenarios x 2 SI conditions")
print("  Each replicate: varied R0 (1.6-2.0), sigma (0.4-0.6), gamma (0.15-0.25)")
print("  All scenarios include Poisson observation noise")
print("=" * 80)

results = []

for scenario in SCENARIOS:
    for si_label, si_mean, si_sd in [("correct", 3.0, 1.5), ("wrong", 7.0, 3.0)]:
        correlations = []
        onset_errors = []

        for rep in range(N_REPS):
            # Fixed seed per scenario and replicate. The earlier hash(scenario) was randomised
            # per Python process (PYTHONHASHSEED), so results did not reproduce between runs.
            rng = np.random.RandomState(SCENARIO_SEED[scenario] + rep)
            R0_peak = rng.uniform(1.6, 2.0)
            sigma_true = rng.uniform(0.4, 0.6)
            gamma_true = rng.uniform(0.15, 0.25)
            t_mid = rng.uniform(35, 45)
            k = rng.uniform(0.10, 0.20)
            beta_max = R0_peak * gamma_true
            beta_min = 0.5 * gamma_true
            beta_func = make_beta_func(beta_min, beta_max, t_mid, k)
            t_daily = np.arange(N_DAYS)
            E0 = rng.uniform(0.0003, 0.0007)
            I0 = rng.uniform(0.0003, 0.0007)
            y0 = [1 - E0 - I0, E0, I0, 0.0]
            sol = odeint(seir_odes, y0, t_daily, args=(beta_func, sigma_true, gamma_true))
            S = sol[:, 0]
            I_daily = sol[:, 2]
            true_Rt = np.array([beta_func(t) * S[t] / gamma_true for t in range(N_DAYS)])
            n_weeks = N_DAYS // 7
            weekly_I = np.array([np.sum(I_daily[w*7:(w+1)*7]) for w in range(n_weeks)])
            weekly_true_Rt = np.array([np.mean(true_Rt[w*7:(w+1)*7]) for w in range(n_weeks)])
            if scenario == "perfect":
                observed = weekly_I.copy()
            elif scenario == "scaled":
                observed = weekly_I * rng.uniform(0.10, 0.20)
            elif scenario == "noisy":
                noise_sd = np.std(weekly_I) * rng.uniform(0.15, 0.25)
                observed = weekly_I + rng.normal(0, noise_sd, n_weeks)
            elif scenario == "delayed":
                observed = np.zeros(n_weeks)
                observed[2:] = weekly_I[:-2]
            elif scenario == "filtered":
                kernel = np.ones(3) / 3
                observed = np.convolve(weekly_I, kernel, mode='same')
            elif scenario == "thresholded":
                observed = weekly_I.copy()
                thresh = np.percentile(weekly_I[weekly_I > 0], 10) if np.sum(weekly_I > 0) > 0 else 0
                observed[observed < thresh] = 0
            observed = np.maximum(observed, 0)
            scale_factor = 1000 / max(observed.max(), 1e-10)
            pseudo_counts = np.round(observed * scale_factor).astype(int)
            pseudo_counts = np.array([rng.poisson(max(c, 0)) for c in pseudo_counts])
            observed_noisy = pseudo_counts.astype(float)
            si = discretized_si(si_mean, si_sd, max_t=n_weeks)
            est_Rt = estimate_R_series(observed_noisy, si, window=4)
            valid_start = 4
            valid = ~np.isnan(est_Rt[valid_start:]) & ~np.isnan(weekly_true_Rt[valid_start:])
            if np.sum(valid) > 5:
                true_v = weekly_true_Rt[valid_start:][valid]
                est_v = est_Rt[valid_start:][valid]
                if np.std(true_v) > 0 and np.std(est_v) > 0:
                    corr = np.corrcoef(true_v, est_v)[0, 1]
                    if not np.isnan(corr):
                        correlations.append(corr)
            true_onset = est_onset = None
            for w in range(valid_start, n_weeks):
                if true_onset is None and weekly_true_Rt[w] > 1.0:
                    true_onset = w
                if est_onset is None and not np.isnan(est_Rt[w]) and est_Rt[w] > 1.0:
                    est_onset = w
            if true_onset is not None and est_onset is not None:
                onset_errors.append((est_onset - true_onset) * 7)

        if len(correlations) > 0:
            results.append({
                "scenario": scenario, "SI": si_label, "n_valid": len(correlations),
                "r_median": round(np.median(correlations), 3),
                "r_mean": round(np.mean(correlations), 3),
                "r_q025": round(np.percentile(correlations, 2.5), 3),
                "r_q975": round(np.percentile(correlations, 97.5), 3),
                "onset_err_median": round(np.median(onset_errors), 1) if onset_errors else None,
                "onset_err_range": f"{min(onset_errors):.0f} to {max(onset_errors):.0f}" if onset_errors else None,
                "n_onset": len(onset_errors),
            })

print("\nRunning two-wave...")
for si_label, si_mean, si_sd in [("correct", 3.0, 1.5), ("wrong", 7.0, 3.0)]:
    correlations = []
    for rep in range(N_REPS):
        rng = np.random.RandomState(rep * 2000)
        gamma_true = rng.uniform(0.15, 0.25)
        sigma_true = rng.uniform(0.4, 0.6)
        amp1 = rng.uniform(0.30, 0.40)
        amp2 = rng.uniform(0.25, 0.35)
        t1 = rng.uniform(25, 35)
        t2 = rng.uniform(90, 110)
        beta_func = make_twowave_func(0.10, amp1, t1, amp2, t2, rng.uniform(12, 18))
        t_daily = np.arange(N_DAYS)
        E0, I0 = rng.uniform(0.0003, 0.0007), rng.uniform(0.0003, 0.0007)
        sol = odeint(seir_odes, [1-E0-I0, E0, I0, 0.0], t_daily, args=(beta_func, sigma_true, gamma_true))
        S, I_daily = sol[:, 0], sol[:, 2]
        true_Rt = np.array([beta_func(t) * S[t] / gamma_true for t in range(N_DAYS)])
        n_weeks = N_DAYS // 7
        weekly_I = np.array([np.sum(I_daily[w*7:(w+1)*7]) for w in range(n_weeks)])
        weekly_true_Rt = np.array([np.mean(true_Rt[w*7:(w+1)*7]) for w in range(n_weeks)])
        scale_factor = 1000 / max(weekly_I.max(), 1e-10)
        pseudo = np.array([rng.poisson(max(int(c * scale_factor), 0)) for c in weekly_I]).astype(float)
        si = discretized_si(si_mean, si_sd, max_t=n_weeks)
        est_Rt = estimate_R_series(pseudo, si, window=4)
        valid = ~np.isnan(est_Rt[4:]) & ~np.isnan(weekly_true_Rt[4:])
        if np.sum(valid) > 5:
            true_v, est_v = weekly_true_Rt[4:][valid], est_Rt[4:][valid]
            if np.std(true_v) > 0 and np.std(est_v) > 0:
                corr = np.corrcoef(true_v, est_v)[0, 1]
                if not np.isnan(corr):
                    correlations.append(corr)
    if correlations:
        results.append({
            "scenario": "two-wave", "SI": si_label, "n_valid": len(correlations),
            "r_median": round(np.median(correlations), 3), "r_mean": round(np.mean(correlations), 3),
            "r_q025": round(np.percentile(correlations, 2.5), 3),
            "r_q975": round(np.percentile(correlations, 97.5), 3),
            "onset_err_median": None, "onset_err_range": None, "n_onset": 0,
        })

results_df = pd.DataFrame(results)
results_df.to_csv("simulation_study_results.csv", index=False)

print(f"\n{'Scenario':<14} {'SI':<8} {'n':>3} {'r median':>9} {'r [2.5, 97.5]':>20}")
print("-" * 60)
for _, r in results_df.iterrows():
    ci = f"[{r['r_q025']:.3f}, {r['r_q975']:.3f}]"
    print(f"{r['scenario']:<14} {r['SI']:<8} {r['n_valid']:>3} {r['r_median']:>9.3f} {ci:>20}")

print(f"\nCI width check:")
for _, r in results_df.iterrows():
    width = r['r_q975'] - r['r_q025']
    status = "OK" if width > 0 else "DETERMINISTIC"
    print(f"  {r['scenario']:14} {r['SI']:8} width = {width:.3f} {status}")

print(f"\nResults saved to simulation_study_results.csv")
