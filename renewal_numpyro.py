"""
Multi-Signal Delay-Calibrated Renewal Model — Production Version
================================================================
Direction B of the Yuan & Dhanasekaran methods redesign.

Core idea: the latent process is a discrete renewal equation driven by R(t)
parameterized as a cubic spline. Each surveillance signal (positivity,
admissions, ILI) is mapped from latent incidence I(t) via a signal-specific
discretized-gamma delay kernel, an ascertainment factor, and an endemic
baseline. Log-normal likelihoods.

What this version adds over the scipy MAP prototype (renewal_v2.py):
- Proper Bayesian inference via NumPyro (SVI with mean-field normal guide,
  optional NUTS validation on a subset).
- Posterior samples for R(t), I(t), signal-specific params.
- Principled uncertainty on onset date: P(R(t) > 1 | data) trajectories.
- Hierarchical partial pooling of ascertainment across seasons (optional).
- Nowcasting harness: fit with data ≤ week k, extract predictive posterior.

Run requirements:
    pip install numpyro jax jaxlib pandas numpy matplotlib

Run times (approximate, CPU):
    Single season SVI (10k steps):      ~30-60 seconds
    Single season NUTS (1000 warmup+draws, 4 chains): ~3-5 minutes
    Multi-season hierarchical SVI:      ~3-5 minutes

Thomas Yuan - HKU PhD, Pathogen Evolution Lab - v1.0
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import jax
import jax.numpy as jnp
from jax import random, lax
import numpyro
import numpyro.distributions as dist
from numpyro.infer import SVI, Trace_ELBO, MCMC, NUTS, autoguide, Predictive
from scipy.stats import gamma as sps_gamma
from scipy.interpolate import CubicSpline
import matplotlib.pyplot as plt

numpyro.set_host_device_count(4)  # for multi-chain NUTS


# =================================================================
# 1. KERNELS (fixed, not inferred in v1 — extension path: infer them)
# =================================================================

def discretized_gamma_pmf(mean: float, sd: float, max_days: int) -> np.ndarray:
    shape = (mean / sd) ** 2
    scale = sd ** 2 / mean
    cdf = sps_gamma.cdf(np.arange(max_days + 1), a=shape, scale=scale)
    pmf = np.diff(cdf); pmf /= pmf.sum()
    return pmf


# Influenza serial / generation interval: Cowling et al. 2009 (3.0 ± 1.5 d)
GT_PMF    = jnp.array(discretized_gamma_pmf(3.0, 1.5, 14))

# Delay kernels — literature-informed means, 50% CV on shape:
#   positivity:  infection -> symptom -> test swab at sentinel (short)
#   ILI GP:      infection -> symptomatic care-seeking -> GP visit
#   admission:   infection -> symptoms -> worsening -> admission (long, wider)
DELAYS = {
    'pos': jnp.array(discretized_gamma_pmf(2.0, 1.0, 14)),
    'ili': jnp.array(discretized_gamma_pmf(4.0, 2.0, 21)),
    'adm': jnp.array(discretized_gamma_pmf(9.0, 4.0, 28)),
}


# =================================================================
# 2. RENEWAL AND CONVOLUTION — JAX
# =================================================================

@jax.jit
def jax_renewal(log_R: jnp.ndarray, I0: float, g: jnp.ndarray) -> jnp.ndarray:
    """Discrete renewal under jax.lax.scan (JIT-compiled).

    I_ext of length T + L; inner recurrence:
        I_ext[t] = exp(log_R[t-L]) * sum_{tau=0..L-1} g[L-1-tau] * I_ext[t-1-tau]

    Returns I[0..T-1].
    """
    T, L = log_R.shape[0], g.shape[0]
    g_rev = g[::-1]

    # State: last L values of I
    def step(window, log_r_t):
        I_t = jnp.exp(log_r_t) * jnp.dot(window, g_rev)
        new_window = jnp.concatenate([window[1:], I_t[None]])
        return new_window, I_t

    init_window = jnp.full((L,), I0)
    _, I = lax.scan(step, init_window, log_R)
    return I


@jax.jit
def convolve_signal(I: jnp.ndarray, delay: jnp.ndarray) -> jnp.ndarray:
    """Full convolution truncated to len(I)."""
    return jnp.convolve(I, delay, mode='full')[:I.shape[0]]


# =================================================================
# 3. SPLINE BASIS (precomputed in Python, passed as constant)
# =================================================================

def spline_basis_matrix(T: int, knot_times: np.ndarray) -> np.ndarray:
    """Return (T, K) matrix B such that log_R = B @ log_R_knots gives
    cubic-spline interpolation at times 0..T-1."""
    K = len(knot_times)
    B = np.zeros((T, K))
    for i in range(K):
        e = np.zeros(K); e[i] = 1.0
        cs = CubicSpline(knot_times, e, bc_type='natural')
        B[:, i] = cs(np.arange(T))
    return B


# =================================================================
# 4. MODEL — single season, multi-signal
# =================================================================

def renewal_model(B: jnp.ndarray,
                  obs_days: jnp.ndarray,
                  y: dict,                          # {'pos': ..., 'adm': ..., 'ili': ...}
                  baselines_ref: dict,              # {'pos': float, ...}
                  g_pmf: jnp.ndarray = GT_PMF,
                  delays: dict | None = None,
                  active_signals: tuple = ('pos', 'adm', 'ili'),
                  log_R_prior_scale: float = 1.5,
                  log_R_smooth_scale: float = 0.35,
                  log_R_curv_scale: float = 0.25):
    """
    NumPyro generative model.
    
    Args:
        B:             (T, K) spline basis matrix
        obs_days:      (W,) integer day indices of observations
        y:             dict of (W,) arrays of signal observations
        baselines_ref: dict of typical baseline values per signal
                       (used to set prior scale of baseline param)
        active_signals: subset of y to include in likelihood
    """
    T, K = B.shape
    delays = delays or DELAYS

    # --- log R(t) prior: AR-like smoothness on knots ---
    # log R_knots_raw ~ N(0, log_R_prior_scale); then differences & curvatures penalized
    log_R_knots = numpyro.sample('log_R_knots',
                                 dist.Normal(0.0, log_R_prior_scale).expand([K]).to_event(1))
    # Smoothness: first and second differences, as additional factors in the prior
    numpyro.factor('smooth_1', -0.5 * jnp.sum(jnp.diff(log_R_knots)**2) / log_R_smooth_scale**2)
    numpyro.factor('smooth_2', -0.5 * jnp.sum(jnp.diff(log_R_knots, 2)**2) / log_R_curv_scale**2)

    # --- log R on daily grid via spline basis ---
    log_R = B @ log_R_knots
    log_R = jnp.clip(log_R, -3.0, 3.0)

    # --- latent I(t) ---
    I = jax_renewal(log_R, I0=1.0, g=g_pmf)
    numpyro.deterministic('log_R', log_R)
    numpyro.deterministic('I', I)

    # --- observation model per signal ---
    for k in active_signals:
        # log alpha ~ weakly informative, centered so alpha * I_peak ~ y_peak
        log_alpha = numpyro.sample(f'log_alpha_{k}', dist.Normal(-2.0, 2.0))
        # baseline b_k: half-normal-like, scaled to typical baseline
        # Reparameterize: b_k = baseline_ref * abs(N(0,1)) -> HalfNormal(baseline_ref)
        b_k_raw = numpyro.sample(f'b_{k}_raw', dist.HalfNormal(1.0))
        b_k = baselines_ref[k] * b_k_raw
        # sigma (log-normal SD): half-normal prior with scale 0.3
        sigma = numpyro.sample(f'sigma_{k}', dist.HalfNormal(0.3))

        # Predicted weekly signal = baseline + alpha * (delay_k * I)[obs_days]
        signal_full = convolve_signal(I, delays[k])
        signal_obs  = signal_full[obs_days]
        pred = b_k + jnp.exp(log_alpha) * signal_obs
        pred = jnp.clip(pred, 1e-8, None)
        numpyro.deterministic(f'pred_{k}', pred)

        # Log-normal likelihood
        numpyro.sample(
            f'y_{k}',
            dist.LogNormal(jnp.log(pred), sigma),
            obs=jnp.clip(y[k], 1e-8, None),
        )


# =================================================================
# 5. HIERARCHICAL MULTI-SEASON MODEL
# =================================================================

def hierarchical_renewal_model(B_list, obs_days_list, y_list,
                               baselines_ref_list,
                               g_pmf=GT_PMF, delays=None,
                               active_signals=('pos','adm','ili')):
    """Partial pooling of ascertainment (alpha) and noise (sigma) across seasons.
    
    - Each season has its own log_R_knots (no pooling; seasons genuinely differ).
    - log_alpha_k pooled across seasons: per-season = mu_alpha_k + tau_alpha_k * z_i
    - sigma_k pooled: per-season = HalfNormal(tau_sigma_k)
    - baselines per-season (not pooled — depend on surveillance variation).
    """
    S = len(B_list)
    delays = delays or DELAYS

    # Hyperpriors
    mu_alpha = {k: numpyro.sample(f'mu_alpha_{k}', dist.Normal(-2.0, 2.0))
                for k in active_signals}
    tau_alpha = {k: numpyro.sample(f'tau_alpha_{k}', dist.HalfNormal(1.0))
                 for k in active_signals}
    tau_sigma = {k: numpyro.sample(f'tau_sigma_{k}', dist.HalfNormal(0.5))
                 for k in active_signals}

    for i in range(S):
        B_i = B_list[i]; obs_days_i = obs_days_list[i]; y_i = y_list[i]
        base_i = baselines_ref_list[i]
        T, K = B_i.shape

        with numpyro.plate(f'season_{i}', 1):
            log_R_knots = numpyro.sample(f'log_R_knots_{i}',
                                         dist.Normal(0.0, 1.5).expand([K]).to_event(1))
        numpyro.factor(f'smooth1_{i}',
                       -0.5 * jnp.sum(jnp.diff(log_R_knots)**2) / 0.35**2)
        numpyro.factor(f'smooth2_{i}',
                       -0.5 * jnp.sum(jnp.diff(log_R_knots, 2)**2) / 0.25**2)

        log_R = jnp.clip(B_i @ log_R_knots, -3.0, 3.0)
        I = jax_renewal(log_R, 1.0, g_pmf)
        numpyro.deterministic(f'log_R_{i}', log_R)

        for k in active_signals:
            z_alpha = numpyro.sample(f'z_alpha_{k}_{i}', dist.Normal(0.0, 1.0))
            log_alpha = mu_alpha[k] + tau_alpha[k] * z_alpha

            b_raw = numpyro.sample(f'b_{k}_raw_{i}', dist.HalfNormal(1.0))
            b = base_i[k] * b_raw

            sigma = numpyro.sample(f'sigma_{k}_{i}', dist.HalfNormal(tau_sigma[k]))

            signal_full = convolve_signal(I, delays[k])
            signal_obs  = signal_full[obs_days_i]
            pred = jnp.clip(b + jnp.exp(log_alpha) * signal_obs, 1e-8, None)

            numpyro.sample(f'y_{k}_{i}',
                           dist.LogNormal(jnp.log(pred), sigma),
                           obs=jnp.clip(y_i[k], 1e-8, None))


# =================================================================
# 6. FITTING WRAPPERS
# =================================================================

def fit_svi(model_fn, model_args: dict, num_steps: int = 10_000,
            lr: float = 0.01, seed: int = 0, verbose: bool = True):
    """Fit via stochastic variational inference (mean-field normal guide)."""
    guide = autoguide.AutoNormal(model_fn)
    optim = numpyro.optim.Adam(lr)
    svi = SVI(model_fn, guide, optim, loss=Trace_ELBO(num_particles=4))
    rng = random.PRNGKey(seed)
    result = svi.run(rng, num_steps, **model_args, progress_bar=verbose)
    return dict(svi=svi, guide=guide, params=result.params, losses=result.losses)


def sample_posterior(svi_result, model_fn, model_args: dict,
                     num_samples: int = 1000, seed: int = 1):
    """Draw posterior samples from fitted variational approximation."""
    rng = random.PRNGKey(seed)
    predictive = Predictive(
        svi_result['guide'], params=svi_result['params'],
        num_samples=num_samples,
    )
    latent = predictive(rng, **model_args)
    # Also generate deterministics via the model
    rng2 = random.PRNGKey(seed + 1)
    det_predictive = Predictive(model_fn, posterior_samples=latent, num_samples=num_samples)
    draws = det_predictive(rng2, **model_args)
    return draws


def fit_nuts(model_fn, model_args: dict, num_warmup=1000, num_samples=1000,
             num_chains=4, seed=0):
    """Fit via full HMC/NUTS. Slower but gold-standard for checking SVI."""
    kernel = NUTS(model_fn, target_accept_prob=0.9)
    mcmc = MCMC(kernel, num_warmup=num_warmup, num_samples=num_samples,
                num_chains=num_chains, progress_bar=True)
    mcmc.run(random.PRNGKey(seed), **model_args)
    mcmc.print_summary(exclude_deterministic=True)
    return mcmc


# =================================================================
# 7. ONSET DETECTION
# =================================================================

def detect_onset_posterior(log_R_samples: np.ndarray,
                           ref_date: pd.Timestamp,
                           sup_thresh: float = 1.0,
                           sup_days: int = 7,
                           sub_thresh: float = 0.95,
                           sub_days: int = 14,
                           alert_prob: float = 0.80) -> dict:
    """Posterior onset detection.

    For each posterior draw, compute the first day of sustained sup-crossing
    (with preceding sub-crossing). Return:
      - onset_dates: list of per-draw onset dates (or None)
      - p_onset_by_day: (T,) prob of onset having occurred by each day
      - alert_date: first day where p_onset >= alert_prob
      - point_onset: posterior median onset day
    """
    N, T = log_R_samples.shape
    R_samples = np.exp(log_R_samples)
    onset_days = np.full(N, np.nan)
    for i in range(N):
        R = R_samples[i]
        for t in range(T - sup_days + 1):
            if not (R[t:t+sup_days] > sup_thresh).all(): continue
            # Look back for sub stretch
            for t0 in range(max(0, t - sub_days - 60), t - sub_days + 1):
                if (R[t0:t0+sub_days] < sub_thresh).all():
                    onset_days[i] = t
                    break
            if not np.isnan(onset_days[i]): break

    # P(onset by day t)
    p_onset = np.zeros(T)
    for t in range(T):
        p_onset[t] = np.mean(~np.isnan(onset_days) & (onset_days <= t))

    # Alert date: first day p >= alert_prob
    alert_idx = None
    if (p_onset >= alert_prob).any():
        alert_idx = int(np.argmax(p_onset >= alert_prob))

    onset_dates = [
        ref_date + pd.Timedelta(days=int(d)) if not np.isnan(d) else None
        for d in onset_days
    ]
    valid = [d for d in onset_dates if d is not None]
    point_onset = pd.Series(valid).median() if valid else None

    return dict(
        onset_days=onset_days,
        onset_dates=onset_dates,
        p_onset_by_day=p_onset,
        alert_date=(ref_date + pd.Timedelta(days=alert_idx)) if alert_idx is not None else None,
        point_onset=point_onset,
        detection_rate=np.mean(~np.isnan(onset_days)),
    )


# =================================================================
# 8. NOWCASTING: fit with first k weeks of data only
# =================================================================

def nowcast(season_df: pd.DataFrame,
            cutoff_week: int,
            active_signals=('pos','adm','ili'),
            num_steps: int = 8000,
            num_samples: int = 500) -> dict:
    """Fit model using only first `cutoff_week` weeks of season.
    Returns posterior over R(t), I(t), predictive signals, and onset stats.
    """
    s_trunc = season_df.iloc[:cutoff_week].reset_index(drop=True)
    if len(s_trunc) < 4:
        raise ValueError(f"cutoff_week {cutoff_week} too early")

    ref = pd.to_datetime(s_trunc['MidDate'].iloc[0])
    obs_days = np.array(
        [(pd.to_datetime(s_trunc['MidDate'].iloc[i]) - ref).days
         for i in range(len(s_trunc))])
    T = int(obs_days[-1]) + 1
    knot_spacing = 14
    knots = np.arange(0, T, knot_spacing)
    if knots[-1] != T - 1: knots = np.append(knots, T - 1)
    B = spline_basis_matrix(T, knots)

    y = {
        'pos': s_trunc['AandB_proportion'].values,
        'adm': s_trunc['Adm_All'].values,
        'ili': s_trunc['ILI_PMP'].values,
    }
    baselines = {k: float(np.quantile(y[k], 0.2)) for k in y}

    model_args = dict(
        B=jnp.array(B),
        obs_days=jnp.array(obs_days),
        y={k: jnp.array(v) for k, v in y.items()},
        baselines_ref=baselines,
        active_signals=active_signals,
    )
    svi_res = fit_svi(renewal_model, model_args, num_steps=num_steps, verbose=False)
    draws  = sample_posterior(svi_res, renewal_model, model_args,
                              num_samples=num_samples)
    log_R_samples = np.asarray(draws['log_R'])
    onset = detect_onset_posterior(log_R_samples, ref)

    return dict(
        cutoff_week=cutoff_week,
        T=T, ref=ref, obs_days=obs_days,
        svi=svi_res, draws=draws, onset=onset,
        log_R_mean=np.exp(log_R_samples).mean(axis=0),
        log_R_q05=np.quantile(np.exp(log_R_samples), 0.05, axis=0),
        log_R_q95=np.quantile(np.exp(log_R_samples), 0.95, axis=0),
    )


# =================================================================
# 9. TOP-LEVEL DRIVER
# =================================================================

def run_single_season_demo(csv_path='flux_data.csv',
                           season_start='2018-06-01',
                           season_end='2019-06-01',
                           num_steps=10000, num_samples=1000):
    """Fit full season with SVI + validate onset posterior."""
    df = pd.read_csv(csv_path)
    df['From'] = pd.to_datetime(df['From'], format='%d/%m/%Y')
    df['To']   = pd.to_datetime(df['To'],   format='%d/%m/%Y')
    df['MidDate'] = df['From'] + (df['To'] - df['From']) / 2
    mask = (df['MidDate'] >= season_start) & (df['MidDate'] <= season_end)
    s = df.loc[mask, ['MidDate', 'AandB_proportion', 'Adm_All', 'ILI_PMP']]\
          .dropna().reset_index(drop=True)
    print(f"Loaded {len(s)} weeks: {season_start} -> {season_end}")

    ref = pd.to_datetime(s['MidDate'].iloc[0])
    obs_days = np.array([(pd.to_datetime(d) - ref).days for d in s['MidDate']])
    T = int(obs_days[-1]) + 1
    knot_spacing = 14
    knots = np.arange(0, T, knot_spacing)
    if knots[-1] != T - 1: knots = np.append(knots, T - 1)
    B = spline_basis_matrix(T, knots)
    print(f"T = {T} days, K = {len(knots)} knots")

    y = {
        'pos': s['AandB_proportion'].values,
        'adm': s['Adm_All'].values,
        'ili': s['ILI_PMP'].values,
    }
    baselines = {k: float(np.quantile(y[k], 0.2)) for k in y}

    # Multi-signal fit
    model_args_multi = dict(
        B=jnp.array(B), obs_days=jnp.array(obs_days),
        y={k: jnp.array(v) for k, v in y.items()},
        baselines_ref=baselines,
        active_signals=('pos','adm','ili'),
    )
    print("\nFitting multi-signal (SVI)...")
    res_multi = fit_svi(renewal_model, model_args_multi, num_steps=num_steps)
    draws_multi = sample_posterior(res_multi, renewal_model, model_args_multi,
                                    num_samples=num_samples)
    onset_multi = detect_onset_posterior(np.asarray(draws_multi['log_R']), ref)

    # Single-signal (pos-only) fit
    model_args_pos = dict(model_args_multi, active_signals=('pos',))
    print("\nFitting pos-only (SVI)...")
    res_pos = fit_svi(renewal_model, model_args_pos, num_steps=num_steps)
    draws_pos = sample_posterior(res_pos, renewal_model, model_args_pos,
                                  num_samples=num_samples)
    onset_pos = detect_onset_posterior(np.asarray(draws_pos['log_R']), ref)

    # CHP onset
    chp = None
    mask = s['AandB_proportion'] > 0.0494
    if mask.any():
        chp = pd.to_datetime(s.loc[mask, 'MidDate'].iloc[0])

    print(f"\n{'='*70}")
    print(f"RESULTS")
    print(f"{'='*70}")
    print(f"CHP onset:       {chp.strftime('%Y-%m-%d') if chp else 'N/D'}")
    print(f"\nMULTI-SIGNAL:")
    print(f"  Detection rate: {onset_multi['detection_rate']*100:.1f}%")
    print(f"  Point onset:    {onset_multi['point_onset'].strftime('%Y-%m-%d') if onset_multi['point_onset'] is not None else 'N/D'}")
    print(f"  Alert (P>=80%): {onset_multi['alert_date'].strftime('%Y-%m-%d') if onset_multi['alert_date'] else 'N/D'}")
    print(f"  Posterior R peak (mean): {np.exp(np.asarray(draws_multi['log_R'])).max(axis=1).mean():.2f}")
    if chp and onset_multi['point_onset'] is not None:
        print(f"  Lead over CHP: {(chp - onset_multi['point_onset']).days:+d} days")

    print(f"\nPOS-ONLY:")
    print(f"  Detection rate: {onset_pos['detection_rate']*100:.1f}%")
    print(f"  Point onset:    {onset_pos['point_onset'].strftime('%Y-%m-%d') if onset_pos['point_onset'] is not None else 'N/D'}")
    print(f"  Alert (P>=80%): {onset_pos['alert_date'].strftime('%Y-%m-%d') if onset_pos['alert_date'] else 'N/D'}")
    print(f"  Posterior R peak (mean): {np.exp(np.asarray(draws_pos['log_R'])).max(axis=1).mean():.2f}")

    # Plot
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    t_grid = np.arange(T)
    dates_grid = ref + pd.to_timedelta(t_grid, unit='D')

    # Positivity fit with uncertainty
    ax = axes[0,0]
    ax.scatter(s['MidDate'], y['pos']*100, c='k', s=25, zorder=5, label='obs')
    for draws, lbl, col in [(draws_multi, 'multi', 'b'), (draws_pos, 'pos', 'r')]:
        pred = np.asarray(draws['pred_pos']) * 100
        ax.plot(s['MidDate'], pred.mean(axis=0), color=col, lw=2, label=f'{lbl} mean')
        ax.fill_between(s['MidDate'],
                        np.quantile(pred, 0.05, axis=0),
                        np.quantile(pred, 0.95, axis=0),
                        color=col, alpha=0.15)
    ax.axhline(4.94, color='gray', ls=':', label='CHP')
    ax.set_ylabel('lab positivity (%)'); ax.set_title('Positivity fit with 90% PI')
    ax.legend(fontsize=8); ax.grid(alpha=0.3)

    # R(t) with uncertainty
    ax = axes[0,1]
    for draws, lbl, col in [(draws_multi, 'multi', 'b'), (draws_pos, 'pos', 'r')]:
        R = np.exp(np.asarray(draws['log_R']))
        ax.plot(dates_grid, R.mean(axis=0), color=col, lw=2.5, label=f'{lbl} mean')
        ax.fill_between(dates_grid,
                        np.quantile(R, 0.05, axis=0),
                        np.quantile(R, 0.95, axis=0),
                        color=col, alpha=0.15)
    ax.axhline(1.0, color='k', ls=':', lw=1)
    if chp: ax.axvline(chp, color='gray', ls='--', alpha=0.6, label='CHP')
    ax.set_ylim(0.3, 2.2); ax.set_ylabel('R(t)')
    ax.set_title('R(t) posterior mean ± 90% PI')
    ax.legend(fontsize=8); ax.grid(alpha=0.3)

    # P(onset occurred by day t)
    ax = axes[1,0]
    ax.plot(dates_grid, onset_multi['p_onset_by_day'], 'b-', lw=2, label='multi')
    ax.plot(dates_grid, onset_pos['p_onset_by_day'], 'r--', lw=1.5, label='pos only')
    ax.axhline(0.80, color='k', ls=':', label='alert threshold 80%')
    if chp: ax.axvline(chp, color='gray', ls='--', alpha=0.6, label='CHP')
    ax.set_ylabel('P(onset occurred by this day | data)')
    ax.set_title('Posterior onset probability')
    ax.legend(fontsize=8); ax.grid(alpha=0.3); ax.set_ylim(-0.05, 1.05)

    # Admissions fit
    ax = axes[1,1]
    ax.scatter(s['MidDate'], y['adm'], c='k', s=25, zorder=5, label='obs')
    pred = np.asarray(draws_multi['pred_adm'])
    ax.plot(s['MidDate'], pred.mean(axis=0), 'b-', lw=2, label='multi mean')
    ax.fill_between(s['MidDate'],
                    np.quantile(pred, 0.05, axis=0),
                    np.quantile(pred, 0.95, axis=0),
                    color='b', alpha=0.15)
    ax.set_ylabel('admissions / 10k'); ax.set_title('Admissions fit (multi only)')
    ax.legend(fontsize=8); ax.grid(alpha=0.3)

    plt.tight_layout()
    out = 'renewal_production_demo.png'
    plt.savefig(out, dpi=140, bbox_inches='tight')
    print(f"\nFigure: {out}")

    return dict(s=s, draws_multi=draws_multi, draws_pos=draws_pos,
                onset_multi=onset_multi, onset_pos=onset_pos, chp=chp,
                res_multi=res_multi, res_pos=res_pos, ref=ref, B=B, obs_days=obs_days)


# =================================================================
# 10. NOWCASTING SWEEP
# =================================================================

def run_nowcast_sweep(csv_path='flux_data.csv',
                      season_start='2018-06-01',
                      season_end='2019-06-01',
                      cutoffs=(8, 12, 16, 20, 24, 28, 36),
                      active_sets=(('pos','adm','ili'), ('pos',)),
                      num_steps=6000, num_samples=500):
    df = pd.read_csv(csv_path)
    df['From'] = pd.to_datetime(df['From'], format='%d/%m/%Y')
    df['To']   = pd.to_datetime(df['To'],   format='%d/%m/%Y')
    df['MidDate'] = df['From'] + (df['To'] - df['From']) / 2
    mask = (df['MidDate'] >= season_start) & (df['MidDate'] <= season_end)
    s = df.loc[mask, ['MidDate', 'AandB_proportion', 'Adm_All', 'ILI_PMP']]\
          .dropna().reset_index(drop=True)
    chp = None
    m = s['AandB_proportion'] > 0.0494
    if m.any(): chp = pd.to_datetime(s.loc[m, 'MidDate'].iloc[0])

    rows = []
    results = {}
    for k in cutoffs:
        if k > len(s): continue
        for active in active_sets:
            lbl = '+'.join(active)
            print(f"\n--- cutoff={k} weeks, signals={lbl} ---")
            try:
                nc = nowcast(s, cutoff_week=k, active_signals=active,
                             num_steps=num_steps, num_samples=num_samples)
                onset = nc['onset']
                data_end = pd.to_datetime(s['MidDate'].iloc[k-1])
                row = dict(
                    cutoff_week=k, signals=lbl,
                    data_end=data_end,
                    chp=chp,
                    chp_declared_by_cutoff=(chp is not None and chp <= data_end),
                    detection_rate=onset['detection_rate'],
                    point_onset=onset['point_onset'],
                    alert_date=onset['alert_date'],
                    lead_over_chp=((chp - onset['point_onset']).days
                                   if (chp and onset['point_onset']) else None),
                )
                rows.append(row)
                results[(k, lbl)] = nc
            except Exception as e:
                print(f"  FAILED: {e}")
    return pd.DataFrame(rows), results


# =================================================================
if __name__ == '__main__':
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else 'demo'

    if mode == 'demo':
        # Single-season SVI demo (10k steps, ~1 minute on laptop)
        run_single_season_demo()

    elif mode == 'nowcast':
        # Nowcasting sweep on 2018/19 (~8-12 minutes on laptop)
        df, results = run_nowcast_sweep()
        df.to_csv('nowcast_posterior.csv', index=False)
        print("\n" + df.to_string())

    elif mode == 'nuts':
        # Full NUTS on 2018/19 for SVI validation (~5 minutes on laptop)
        df = pd.read_csv('flux_data.csv')
        df['From'] = pd.to_datetime(df['From'], format='%d/%m/%Y')
        df['To']   = pd.to_datetime(df['To'],   format='%d/%m/%Y')
        df['MidDate'] = df['From'] + (df['To'] - df['From']) / 2
        mask = (df['MidDate'] >= '2018-06-01') & (df['MidDate'] <= '2019-06-01')
        s = df.loc[mask, ['MidDate','AandB_proportion','Adm_All','ILI_PMP']]\
              .dropna().reset_index(drop=True)
        ref = pd.to_datetime(s['MidDate'].iloc[0])
        obs_days = np.array([(pd.to_datetime(d) - ref).days for d in s['MidDate']])
        T = int(obs_days[-1]) + 1
        knots = np.arange(0, T, 14)
        if knots[-1] != T - 1: knots = np.append(knots, T - 1)
        B = spline_basis_matrix(T, knots)
        y = {'pos': s['AandB_proportion'].values,
             'adm': s['Adm_All'].values,
             'ili': s['ILI_PMP'].values}
        baselines = {k: float(np.quantile(y[k], 0.2)) for k in y}
        args = dict(B=jnp.array(B), obs_days=jnp.array(obs_days),
                    y={k: jnp.array(v) for k, v in y.items()},
                    baselines_ref=baselines,
                    active_signals=('pos','adm','ili'))
        print("Running NUTS for SVI validation (slow)...")
        mcmc = fit_nuts(renewal_model, args, num_warmup=1000, num_samples=1000)
        import pickle
        with open('nuts_samples.pkl', 'wb') as f:
            pickle.dump(mcmc.get_samples(), f)
        print("Saved: nuts_samples.pkl")

    else:
        print(f"Unknown mode: {mode}. Use 'demo', 'nowcast', or 'nuts'.")
