"""
Multi-Signal Delay-Calibrated Renewal Model — Pyro / PyTorch Version
====================================================================
Functional twin of renewal_numpyro.py, rewritten against Pyro + PyTorch
for people whose CPU lacks AVX2 (older Intel Macs) or who already have
Pyro 1.9.x + torch 2.2.x installed.

Same mathematical model, same command-line interface:
    python renewal_pyro.py demo     # single-season SVI, ~2-3 min
    python renewal_pyro.py nowcast  # nowcasting sweep, ~20-40 min
    python renewal_pyro.py nuts     # HMC validation, ~10-15 min

Thomas Yuan — HKU PhD, Pathogen Evolution Lab
"""
from __future__ import annotations

import sys
import math
import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
import pyro
import pyro.distributions as dist
from pyro.infer import SVI, Trace_ELBO, MCMC, NUTS, Predictive
from pyro.infer.autoguide import AutoNormal
from scipy.stats import gamma as sps_gamma
from scipy.interpolate import CubicSpline
import matplotlib.pyplot as plt


# Keep things on CPU and in double for numerical stability on long renewals
DTYPE = torch.float64
torch.set_default_dtype(DTYPE)


# =================================================================
# 1. KERNELS
# =================================================================

def discretized_gamma_pmf(mean: float, sd: float, max_days: int) -> np.ndarray:
    shape = (mean / sd) ** 2
    scale = sd ** 2 / mean
    cdf = sps_gamma.cdf(np.arange(max_days + 1), a=shape, scale=scale)
    pmf = np.diff(cdf); pmf /= pmf.sum()
    return pmf


# Influenza generation interval: Cowling et al. 2009 (3.0 ± 1.5 d)
GT_PMF_NP = discretized_gamma_pmf(3.0, 1.5, 14)

# Delay kernels
DELAYS_NP = {
    'pos': discretized_gamma_pmf(2.0, 1.0, 14),
    'ili': discretized_gamma_pmf(4.0, 2.0, 21),
    'adm': discretized_gamma_pmf(9.0, 4.0, 28),
}


def _to_tensor(x):
    return torch.as_tensor(x, dtype=DTYPE)


# =================================================================
# 2. RENEWAL (PyTorch — supports autograd)
# =================================================================

def torch_renewal(log_R: torch.Tensor, I0: float, g: torch.Tensor) -> torch.Tensor:
    """Discrete renewal: I[t] = exp(log_R[t]) * sum_tau g[tau] I[t-1-tau].

    log_R: (T,) tensor with gradient support.
    g:     (L,) tensor, generation-time PMF.
    Returns I of shape (T,). Inner loop in Python but vectorized over tau.
    """
    T = log_R.shape[0]
    L = g.shape[0]
    g_rev = torch.flip(g, dims=[0])
    # Build I_ext using a list to keep autograd happy (can't in-place into a Param)
    I_ext = [torch.full((), I0, dtype=DTYPE) for _ in range(L)]
    R = torch.exp(log_R)
    for t in range(T):
        window = torch.stack(I_ext[-L:])      # (L,)
        I_t = R[t] * (window * g_rev).sum()
        I_ext.append(I_t)
    I = torch.stack(I_ext[L:])
    return I


def convolve_signal(I: torch.Tensor, delay: torch.Tensor) -> torch.Tensor:
    """Same as np.convolve(I, delay, 'full')[:len(I)] but with autograd."""
    T = I.shape[0]
    L = delay.shape[0]
    # Use conv1d: flip kernel convention
    # conv1d does cross-correlation; for convolution we flip the kernel
    k = torch.flip(delay, dims=[0]).view(1, 1, L)
    x = I.view(1, 1, T)
    # Pad left by L-1 zeros to get full convolution truncated to T
    x_pad = F.pad(x, (L - 1, 0))
    y = F.conv1d(x_pad, k).view(-1)
    return y[:T]


# =================================================================
# 3. SPLINE BASIS
# =================================================================

def spline_basis_matrix(T: int, knot_times: np.ndarray) -> np.ndarray:
    K = len(knot_times)
    B = np.zeros((T, K))
    for i in range(K):
        e = np.zeros(K); e[i] = 1.0
        cs = CubicSpline(knot_times, e, bc_type='natural')
        B[:, i] = cs(np.arange(T))
    return B


# =================================================================
# 4. MODEL (Pyro generative function)
# =================================================================

def renewal_model(B: torch.Tensor,
                  obs_days: torch.Tensor,        # LongTensor indices
                  y: dict,                        # dict of torch tensors
                  baselines_ref: dict,
                  g_pmf: torch.Tensor,
                  delays: dict,
                  active_signals: tuple = ('pos', 'adm', 'ili'),
                  log_R_prior_scale: float = 1.5,
                  log_R_smooth_scale: float = 0.35,
                  log_R_curv_scale: float = 0.25):

    T, K = B.shape

    # log R knots
    log_R_knots = pyro.sample(
        'log_R_knots',
        dist.Normal(torch.zeros(K), torch.full((K,), log_R_prior_scale))
            .to_event(1)
    )
    # Smoothness factors
    d1 = torch.diff(log_R_knots)
    d2 = torch.diff(log_R_knots, n=2)
    pyro.factor('smooth_1', -0.5 * (d1.pow(2).sum()) / (log_R_smooth_scale ** 2))
    pyro.factor('smooth_2', -0.5 * (d2.pow(2).sum()) / (log_R_curv_scale ** 2))

    log_R = (B @ log_R_knots).clamp(-3.0, 3.0)
    I = torch_renewal(log_R, I0=1.0, g=g_pmf)
    pyro.deterministic('log_R', log_R)
    pyro.deterministic('I', I)

    for k in active_signals:
        log_alpha = pyro.sample(
            f'log_alpha_{k}', dist.Normal(torch.tensor(-2.0), torch.tensor(2.0))
        )
        b_raw = pyro.sample(f'b_{k}_raw', dist.HalfNormal(torch.tensor(1.0)))
        b_k = baselines_ref[k] * b_raw
        sigma = pyro.sample(f'sigma_{k}', dist.HalfNormal(torch.tensor(0.3)))

        signal_full = convolve_signal(I, delays[k])
        signal_obs = signal_full[obs_days]
        pred = (b_k + torch.exp(log_alpha) * signal_obs).clamp(min=1e-8)
        pyro.deterministic(f'pred_{k}', pred)

        pyro.sample(
            f'y_{k}',
            dist.LogNormal(torch.log(pred), sigma),
            obs=y[k].clamp(min=1e-8),
        )


# =================================================================
# 5. FITTING
# =================================================================

def fit_svi(model_fn, model_args: dict, num_steps: int = 10000, lr: float = 0.01,
            num_particles: int = 4, seed: int = 0, verbose: bool = True):
    pyro.clear_param_store()
    pyro.set_rng_seed(seed)
    guide = AutoNormal(model_fn)
    optim = pyro.optim.Adam({'lr': lr})
    svi = SVI(model_fn, guide, optim, loss=Trace_ELBO(num_particles=num_particles))
    losses = []
    for step in range(num_steps):
        loss = svi.step(**model_args)
        losses.append(loss)
        if verbose and (step % 500 == 0 or step == num_steps - 1):
            recent = np.mean(losses[-50:])
            print(f'  step {step:5d}  ELBO loss ≈ {recent:.2f}')
    return dict(guide=guide, losses=losses)


def sample_posterior(fit_result, model_fn, model_args: dict,
                     num_samples: int = 1000):
    """Draw posterior samples by running the guide, then re-executing the
    model with substituted latents to recover deterministics."""
    guide = fit_result['guide']
    # Draw latent samples via guide
    predictive = Predictive(model_fn, guide=guide, num_samples=num_samples,
                            return_sites=None)
    draws = predictive(**model_args)
    return {k: v.detach().cpu().numpy() for k, v in draws.items()}


def fit_nuts(model_fn, model_args: dict, num_warmup=500, num_samples=500,
             num_chains=2, seed=0):
    pyro.set_rng_seed(seed)
    kernel = NUTS(model_fn, target_accept_prob=0.85)
    mcmc = MCMC(kernel, num_warmup=num_warmup, num_samples=num_samples,
                num_chains=num_chains)
    mcmc.run(**model_args)
    mcmc.summary()
    return mcmc


# =================================================================
# 6. ONSET DETECTION (identical logic)
# =================================================================

def detect_onset_posterior(log_R_samples: np.ndarray,
                           ref_date: pd.Timestamp,
                           sup_thresh: float = 1.0,
                           sup_days: int = 7,
                           sub_thresh: float = 0.95,
                           sub_days: int = 14,
                           alert_prob: float = 0.80) -> dict:
    N, T = log_R_samples.shape
    R_samples = np.exp(log_R_samples)
    onset_days = np.full(N, np.nan)
    for i in range(N):
        R = R_samples[i]
        for t in range(T - sup_days + 1):
            if not (R[t:t+sup_days] > sup_thresh).all(): continue
            for t0 in range(max(0, t - sub_days - 60), t - sub_days + 1):
                if (R[t0:t0+sub_days] < sub_thresh).all():
                    onset_days[i] = t; break
            if not np.isnan(onset_days[i]): break

    p_onset = np.zeros(T)
    for t in range(T):
        p_onset[t] = np.mean(~np.isnan(onset_days) & (onset_days <= t))

    alert_idx = int(np.argmax(p_onset >= alert_prob)) if (p_onset >= alert_prob).any() else None
    onset_dates = [ref_date + pd.Timedelta(days=int(d)) if not np.isnan(d) else None
                   for d in onset_days]
    valid = [d for d in onset_dates if d is not None]
    point_onset = pd.Series(valid).median() if valid else None

    return dict(
        onset_days=onset_days, onset_dates=onset_dates,
        p_onset_by_day=p_onset,
        alert_date=(ref_date + pd.Timedelta(days=alert_idx)) if alert_idx is not None else None,
        point_onset=point_onset,
        detection_rate=float(np.mean(~np.isnan(onset_days))),
    )


# =================================================================
# 7. SETUP UTILITY
# =================================================================

def prepare_season_inputs(csv_path, season_start, season_end, knot_spacing=14):
    df = pd.read_csv(csv_path)
    df['From'] = pd.to_datetime(df['From'], format='%d/%m/%Y')
    df['To']   = pd.to_datetime(df['To'],   format='%d/%m/%Y')
    df['MidDate'] = df['From'] + (df['To'] - df['From']) / 2
    mask = (df['MidDate'] >= season_start) & (df['MidDate'] <= season_end)
    s = df.loc[mask, ['MidDate', 'AandB_proportion', 'Adm_All', 'ILI_PMP']] \
          .dropna().reset_index(drop=True)

    ref = pd.to_datetime(s['MidDate'].iloc[0])
    obs_days_np = np.array([(pd.to_datetime(d) - ref).days for d in s['MidDate']])
    T = int(obs_days_np[-1]) + 1
    knots = np.arange(0, T, knot_spacing)
    if knots[-1] != T - 1: knots = np.append(knots, T - 1)
    B_np = spline_basis_matrix(T, knots)

    y_np = {'pos': s['AandB_proportion'].values,
            'adm': s['Adm_All'].values,
            'ili': s['ILI_PMP'].values}
    baselines = {k: float(np.quantile(y_np[k], 0.2)) for k in y_np}

    model_args = dict(
        B=_to_tensor(B_np),
        obs_days=torch.as_tensor(obs_days_np, dtype=torch.long),
        y={k: _to_tensor(v) for k, v in y_np.items()},
        baselines_ref={k: float(v) for k, v in baselines.items()},
        g_pmf=_to_tensor(GT_PMF_NP),
        delays={k: _to_tensor(v) for k, v in DELAYS_NP.items()},
    )
    return s, ref, T, B_np, obs_days_np, y_np, baselines, model_args


# =================================================================
# 8. DEMO
# =================================================================

def run_demo(csv_path='flux_data.csv',
             season_start='2018-06-01', season_end='2019-06-01',
             num_steps=10000, num_samples=1000):
    s, ref, T, _, _, y_np, _, args_multi_base = prepare_season_inputs(
        csv_path, season_start, season_end)
    print(f"Loaded {len(s)} weeks.  T = {T} days,  K = {args_multi_base['B'].shape[1]} knots")

    args_multi = dict(args_multi_base, active_signals=('pos', 'adm', 'ili'))
    args_pos   = dict(args_multi_base, active_signals=('pos',))

    print("\nFitting multi-signal (SVI)...")
    fit_m = fit_svi(renewal_model, args_multi, num_steps=num_steps)
    draws_m = sample_posterior(fit_m, renewal_model, args_multi, num_samples=num_samples)
    onset_m = detect_onset_posterior(draws_m['log_R'], ref)

    print("\nFitting pos-only (SVI)...")
    fit_p = fit_svi(renewal_model, args_pos, num_steps=num_steps)
    draws_p = sample_posterior(fit_p, renewal_model, args_pos, num_samples=num_samples)
    onset_p = detect_onset_posterior(draws_p['log_R'], ref)

    chp = None
    mask = s['AandB_proportion'] > 0.0494
    if mask.any(): chp = pd.to_datetime(s.loc[mask, 'MidDate'].iloc[0])

    # ---- Report ----
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(f"CHP onset:       {chp.strftime('%Y-%m-%d') if chp else 'N/D'}")
    print("\nMULTI-SIGNAL:")
    print(f"  Detection rate: {onset_m['detection_rate']*100:.1f}%")
    print(f"  Point onset:    "
          f"{onset_m['point_onset'].strftime('%Y-%m-%d') if onset_m['point_onset'] is not None else 'N/D'}")
    print(f"  Alert (P>=80%): "
          f"{onset_m['alert_date'].strftime('%Y-%m-%d') if onset_m['alert_date'] else 'N/D'}")
    Rmax_m = np.exp(draws_m['log_R']).max(axis=1)
    print(f"  Posterior R peak: mean {Rmax_m.mean():.2f}, 90%PI [{np.quantile(Rmax_m, 0.05):.2f}, {np.quantile(Rmax_m, 0.95):.2f}]")
    if chp and onset_m['point_onset'] is not None:
        print(f"  Lead over CHP:  {(chp - onset_m['point_onset']).days:+d} days")

    print("\nPOS-ONLY:")
    print(f"  Detection rate: {onset_p['detection_rate']*100:.1f}%")
    print(f"  Point onset:    "
          f"{onset_p['point_onset'].strftime('%Y-%m-%d') if onset_p['point_onset'] is not None else 'N/D'}")
    print(f"  Alert (P>=80%): "
          f"{onset_p['alert_date'].strftime('%Y-%m-%d') if onset_p['alert_date'] else 'N/D'}")
    Rmax_p = np.exp(draws_p['log_R']).max(axis=1)
    print(f"  Posterior R peak: mean {Rmax_p.mean():.2f}, 90%PI [{np.quantile(Rmax_p, 0.05):.2f}, {np.quantile(Rmax_p, 0.95):.2f}]")

    # ---- Plot ----
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    dates_grid = ref + pd.to_timedelta(np.arange(T), unit='D')

    # Positivity with uncertainty
    ax = axes[0, 0]
    ax.scatter(s['MidDate'], y_np['pos']*100, c='k', s=25, zorder=5, label='obs')
    for draws, lbl, col in [(draws_m, 'multi', 'b'), (draws_p, 'pos', 'r')]:
        pred = draws['pred_pos'] * 100
        ax.plot(s['MidDate'], pred.mean(axis=0), color=col, lw=2, label=f'{lbl} mean')
        ax.fill_between(s['MidDate'],
                        np.quantile(pred, 0.05, axis=0),
                        np.quantile(pred, 0.95, axis=0),
                        color=col, alpha=0.15)
    ax.axhline(4.94, color='gray', ls=':', label='CHP')
    ax.set_ylabel('lab positivity (%)'); ax.set_title('Positivity fit with 90% PI')
    ax.legend(fontsize=8); ax.grid(alpha=0.3)

    # R(t)
    ax = axes[0, 1]
    for draws, lbl, col in [(draws_m, 'multi', 'b'), (draws_p, 'pos', 'r')]:
        R = np.exp(draws['log_R'])
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

    # P(onset by day t)
    ax = axes[1, 0]
    ax.plot(dates_grid, onset_m['p_onset_by_day'], 'b-', lw=2, label='multi')
    ax.plot(dates_grid, onset_p['p_onset_by_day'], 'r--', lw=1.5, label='pos only')
    ax.axhline(0.80, color='k', ls=':', label='alert 80%')
    if chp: ax.axvline(chp, color='gray', ls='--', alpha=0.6, label='CHP')
    ax.set_ylabel('P(onset by day t | data)')
    ax.set_title('Posterior onset probability')
    ax.legend(fontsize=8); ax.grid(alpha=0.3); ax.set_ylim(-0.05, 1.05)

    # Admissions fit
    ax = axes[1, 1]
    ax.scatter(s['MidDate'], y_np['adm'], c='k', s=25, zorder=5, label='obs')
    pred = draws_m['pred_adm']
    ax.plot(s['MidDate'], pred.mean(axis=0), 'b-', lw=2, label='multi mean')
    ax.fill_between(s['MidDate'],
                    np.quantile(pred, 0.05, axis=0),
                    np.quantile(pred, 0.95, axis=0),
                    color='b', alpha=0.15)
    ax.set_ylabel('admissions / 10k'); ax.set_title('Admissions fit (multi only)')
    ax.legend(fontsize=8); ax.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig('renewal_production_demo.png', dpi=140, bbox_inches='tight')
    print("\nFigure: renewal_production_demo.png")

    return dict(s=s, draws_multi=draws_m, draws_pos=draws_p,
                onset_multi=onset_m, onset_pos=onset_p, chp=chp, ref=ref)


# =================================================================
# 9. NOWCASTING SWEEP
# =================================================================

def nowcast(season_df, cutoff_week, active_signals=('pos','adm','ili'),
            num_steps=6000, num_samples=500):
    s_trunc = season_df.iloc[:cutoff_week].reset_index(drop=True)
    ref = pd.to_datetime(s_trunc['MidDate'].iloc[0])
    obs_days_np = np.array([(pd.to_datetime(d) - ref).days for d in s_trunc['MidDate']])
    T = int(obs_days_np[-1]) + 1
    knots = np.arange(0, T, 14)
    if knots[-1] != T - 1: knots = np.append(knots, T - 1)
    B_np = spline_basis_matrix(T, knots)
    y_np = {'pos': s_trunc['AandB_proportion'].values,
            'adm': s_trunc['Adm_All'].values,
            'ili': s_trunc['ILI_PMP'].values}
    baselines = {k: float(np.quantile(y_np[k], 0.2)) for k in y_np}

    args = dict(
        B=_to_tensor(B_np),
        obs_days=torch.as_tensor(obs_days_np, dtype=torch.long),
        y={k: _to_tensor(v) for k, v in y_np.items()},
        baselines_ref=baselines,
        g_pmf=_to_tensor(GT_PMF_NP),
        delays={k: _to_tensor(v) for k, v in DELAYS_NP.items()},
        active_signals=active_signals,
    )
    fit = fit_svi(renewal_model, args, num_steps=num_steps, verbose=False)
    draws = sample_posterior(fit, renewal_model, args, num_samples=num_samples)
    onset = detect_onset_posterior(draws['log_R'], ref)
    return dict(cutoff_week=cutoff_week, ref=ref, T=T, draws=draws, onset=onset)


def run_nowcast_sweep(csv_path='flux_data.csv',
                      season_start='2018-06-01', season_end='2019-06-01',
                      cutoffs=(8, 12, 16, 20, 24, 28, 36),
                      active_sets=(('pos','adm','ili'), ('pos',))):
    df = pd.read_csv(csv_path)
    df['From'] = pd.to_datetime(df['From'], format='%d/%m/%Y')
    df['To']   = pd.to_datetime(df['To'],   format='%d/%m/%Y')
    df['MidDate'] = df['From'] + (df['To'] - df['From']) / 2
    mask = (df['MidDate'] >= season_start) & (df['MidDate'] <= season_end)
    s = df.loc[mask, ['MidDate','AandB_proportion','Adm_All','ILI_PMP']] \
          .dropna().reset_index(drop=True)
    chp = None
    m = s['AandB_proportion'] > 0.0494
    if m.any(): chp = pd.to_datetime(s.loc[m, 'MidDate'].iloc[0])

    rows = []
    for k in cutoffs:
        if k > len(s): continue
        for active in active_sets:
            lbl = '+'.join(active)
            print(f"\n[nowcast] cutoff={k}wk, signals={lbl}")
            try:
                nc = nowcast(s, cutoff_week=k, active_signals=active)
                onset = nc['onset']
                data_end = pd.to_datetime(s['MidDate'].iloc[k-1])
                rows.append(dict(
                    cutoff_week=k, signals=lbl,
                    data_end=data_end, chp=chp,
                    chp_declared_by_cutoff=(chp is not None and chp <= data_end),
                    detection_rate=onset['detection_rate'],
                    point_onset=onset['point_onset'],
                    alert_date=onset['alert_date'],
                    lead_over_chp=((chp - onset['point_onset']).days
                                   if (chp and onset['point_onset']) else None),
                ))
                print(f"  detection={onset['detection_rate']*100:.0f}%  "
                      f"point={onset['point_onset']}  alert={onset['alert_date']}")
            except Exception as e:
                print(f"  FAILED: {e}")
    return pd.DataFrame(rows)


# =================================================================
if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'demo'

    if mode == 'demo':
        run_demo()
    elif mode == 'nowcast':
        df = run_nowcast_sweep()
        df.to_csv('nowcast_posterior.csv', index=False)
        print("\n" + df.to_string())
    elif mode == 'nuts':
        s, ref, T, _, _, _, _, args = prepare_season_inputs(
            'flux_data.csv', '2018-06-01', '2019-06-01')
        args['active_signals'] = ('pos','adm','ili')
        print("Running NUTS... this is slow (~10-15 min)")
        mcmc = fit_nuts(renewal_model, args, num_warmup=500, num_samples=500, num_chains=2)
        import pickle
        samples = {k: v.detach().cpu().numpy() for k, v in mcmc.get_samples().items()}
        with open('nuts_samples.pkl', 'wb') as f:
            pickle.dump(samples, f)
        print("Saved: nuts_samples.pkl")
    else:
        print(f"Unknown mode: {mode}")
