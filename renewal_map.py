"""
Multi-Signal Delay-Calibrated Renewal Model — Pure numpy/scipy Version
======================================================================
Works on any Python install. No PyTorch, no JAX, no Pyro.
Uses MAP fit (L-BFGS-B) + Laplace approximation for posterior uncertainty.

Same model as renewal_numpyro.py / renewal_pyro.py. Same command-line API:
    python renewal_map.py demo     # single-season, ~30-60 seconds
    python renewal_map.py nowcast  # nowcast sweep, ~5-10 minutes
    python renewal_map.py retro    # multi-season retrospective

The Laplace approximation gives you:
  - Posterior mean and covariance of all parameters (incl. R(t) spline knots)
  - 500+ posterior samples drawn from N(MAP, H^{-1})
  - Proper posterior onset probability P(R(t) > 1 | data)
  - 90% posterior intervals on R(t), I(t), signal predictions

Limitations vs full VI/NUTS:
  - Assumes posterior is Gaussian in unconstrained parameters (usually fine here)
  - Doesn't capture multimodality if it exists (not expected in this model)
  - HalfNormal-constrained params are approximated as unconstrained + softplus

Thomas Yuan — HKU PhD, Pathogen Evolution Lab
"""
from __future__ import annotations

import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import minimize
from scipy.interpolate import CubicSpline
from scipy.stats import gamma as sps_gamma
from scipy.linalg import cho_factor, cho_solve
import warnings
warnings.filterwarnings('ignore')


# =================================================================
# 1. KERNELS
# =================================================================

def discretized_gamma_pmf(mean, sd, max_days):
    shape = (mean / sd) ** 2
    scale = sd ** 2 / mean
    cdf = sps_gamma.cdf(np.arange(max_days + 1), a=shape, scale=scale)
    pmf = np.diff(cdf); pmf /= pmf.sum()
    return pmf

GT_PMF    = discretized_gamma_pmf(3.0, 1.5, 14)        # Cowling 2009 influenza GT
DELAY_POS = discretized_gamma_pmf(2.0, 1.0, 14)        # infection -> test
DELAY_ILI = discretized_gamma_pmf(4.0, 2.0, 21)        # infection -> GP visit
DELAY_ADM = discretized_gamma_pmf(9.0, 4.0, 28)        # infection -> admission
DELAYS = {'pos': DELAY_POS, 'ili': DELAY_ILI, 'adm': DELAY_ADM}


# =================================================================
# 2. RENEWAL AND CONVOLUTION
# =================================================================

def run_renewal(log_R, I0, g):
    """Discrete renewal: I[t] = exp(log_R[t]) * sum_tau g[tau] I[t-1-tau]."""
    T, L = len(log_R), len(g)
    I_ext = np.empty(T + L)
    I_ext[:L] = I0
    g_rev = g[::-1].copy()
    R = np.exp(log_R)
    for t in range(L, T + L):
        I_ext[t] = R[t - L] * (I_ext[t - L:t] @ g_rev)
    return I_ext[L:]


def convolve_delay(I, delay):
    return np.convolve(I, delay, mode='full')[:len(I)]


# =================================================================
# 3. SPLINE BASIS
# =================================================================

def spline_basis_matrix(T, knot_times):
    K = len(knot_times)
    B = np.zeros((T, K))
    for i in range(K):
        e = np.zeros(K); e[i] = 1.0
        cs = CubicSpline(knot_times, e, bc_type='natural')
        B[:, i] = cs(np.arange(T))
    return B


# =================================================================
# 4. MODEL
# =================================================================

class RenewalModel:
    """Multi-signal delay-calibrated renewal model.

    Parameter vector layout (flat, all unconstrained):
      [log_R_knots (K)]
      [log_alpha_pos, log_alpha_adm, log_alpha_ili]           (3)
      [log_sigma_pos, log_sigma_adm, log_sigma_ili]           (3)
      [raw_b_pos, raw_b_adm, raw_b_ili]                       (3)
    Total dimension: K + 9

    Transformations:
      alpha_k = exp(log_alpha_k)   — positive
      sigma_k = exp(log_sigma_k)   — positive
      b_k     = 2 * baseline_ref_k * sigmoid(raw_b_k)  — in [0, 2*ref_k]
    """

    def __init__(self, dates, y_pos, y_adm, y_ili,
                 knot_spacing_days=14, g_pmf=GT_PMF, delays=None):
        self.dates = pd.to_datetime(dates).reset_index(drop=True)
        self.y = {'pos': np.asarray(y_pos, float),
                  'adm': np.asarray(y_adm, float),
                  'ili': np.asarray(y_ili, float)}
        self.W = len(self.dates)
        self.obs_days = np.array(
            [(self.dates[i] - self.dates[0]).days for i in range(self.W)])
        self.T = int(self.obs_days[-1]) + 1
        self.g = g_pmf
        self.delays = delays or DELAYS

        self.knot_times = np.arange(0, self.T, knot_spacing_days)
        if self.knot_times[-1] != self.T - 1:
            self.knot_times = np.append(self.knot_times, self.T - 1)
        self.K = len(self.knot_times)

        # Precompute spline basis so forward pass is a single matmul
        self.B = spline_basis_matrix(self.T, self.knot_times)

        self.y_baseline_ref = {k: float(np.quantile(v, 0.15)) for k, v in self.y.items()}
        self.y_peak_ref     = {k: float(np.max(v))           for k, v in self.y.items()}

        self.n_params = self.K + 9
        self._signals = ('pos', 'adm', 'ili')

    # ---- parameter unpacking ----
    def unpack(self, params):
        K = self.K
        p = {}
        p['log_R_knots'] = params[:K]
        p['log_alpha']   = dict(zip(self._signals, params[K:K+3]))
        p['log_sigma']   = dict(zip(self._signals, params[K+3:K+6]))
        p['raw_b']       = dict(zip(self._signals, params[K+6:K+9]))
        return p

    def get_baseline(self, raw_b, k):
        return 2.0 * self.y_baseline_ref[k] / (1.0 + np.exp(-raw_b))

    def init_params(self):
        log_R = np.zeros(self.K)
        log_alpha = [np.log(max((self.y_peak_ref[k] - self.y_baseline_ref[k]) / 3.0, 1e-6))
                     for k in self._signals]
        log_sigma = [np.log(0.2), np.log(0.25), np.log(0.2)]
        raw_b = [0.0, 0.0, 0.0]
        return np.concatenate([log_R, log_alpha, log_sigma, raw_b])

    # ---- forward ----
    def forward(self, params):
        p = self.unpack(params)
        log_R = np.clip(self.B @ p['log_R_knots'], -3.0, 3.0)
        I = run_renewal(log_R, 1.0, self.g)
        preds = {}
        for k in self._signals:
            sig = convolve_delay(I, self.delays[k])
            b = self.get_baseline(p['raw_b'][k], k)
            preds[k] = b + np.exp(p['log_alpha'][k]) * sig[self.obs_days]
        return dict(log_R=log_R, I=I, preds=preds, params=p)

    # ---- negative log posterior ----
    def nlp(self, params, active=('pos','adm','ili'),
            prior_R_knot_sd=1.5, prior_R_smooth_sd=0.35, prior_R_curv_sd=0.25,
            prior_sigma_scale=0.3):
        fwd = self.forward(params); p = fwd['params']
        nll = 0.0
        for k in active:
            pred = np.clip(fwd['preds'][k], 1e-8, None)
            obs  = np.clip(self.y[k], 1e-8, None)
            resid = (np.log(obs) - np.log(pred)) / np.exp(p['log_sigma'][k])
            nll += 0.5 * np.sum(resid**2) + len(obs) * p['log_sigma'][k]
        nlp = nll
        # log R priors (smoothness via 1st and 2nd differences)
        log_R = p['log_R_knots']
        nlp += 0.5 * np.sum(log_R**2) / prior_R_knot_sd**2
        nlp += 0.5 * np.sum(np.diff(log_R)**2) / prior_R_smooth_sd**2
        nlp += 0.5 * np.sum(np.diff(log_R, 2)**2) / prior_R_curv_sd**2
        # Half-normal on sigma_k (log-space Jacobian)
        for k in active:
            sigma = np.exp(p['log_sigma'][k])
            nlp += 0.5 * sigma**2 / prior_sigma_scale**2 - p['log_sigma'][k]
        return float(nlp)

    def fit_map(self, active=('pos','adm','ili'), x0=None, maxiter=2000):
        if x0 is None: x0 = self.init_params()
        res = minimize(self.nlp, x0, args=(active,), method='L-BFGS-B',
                       options={'maxiter': maxiter})
        return dict(res=res, fwd=self.forward(res.x), params=res.x,
                    active=active)


# =================================================================
# 5. LAPLACE APPROXIMATION
# =================================================================

def numerical_hessian(fn, x0, epsilon=None):
    """Central-difference Hessian. O(n^2) function evaluations."""
    x0 = np.asarray(x0, float)
    n = len(x0)
    if epsilon is None:
        epsilon = 1e-4 * np.maximum(np.abs(x0), 1.0)
    else:
        epsilon = np.full(n, epsilon)

    H = np.zeros((n, n))
    f0 = fn(x0)

    # Diagonal: f(x+e) - 2f(x) + f(x-e)
    for i in range(n):
        ei = np.zeros(n); ei[i] = epsilon[i]
        H[i, i] = (fn(x0 + ei) - 2.0 * f0 + fn(x0 - ei)) / epsilon[i]**2

    # Off-diagonal: (f(x+ei+ej) - f(x+ei-ej) - f(x-ei+ej) + f(x-ei-ej)) / 4eiej
    for i in range(n):
        for j in range(i + 1, n):
            ei = np.zeros(n); ei[i] = epsilon[i]
            ej = np.zeros(n); ej[j] = epsilon[j]
            fpp = fn(x0 + ei + ej); fpm = fn(x0 + ei - ej)
            fmp = fn(x0 - ei + ej); fmm = fn(x0 - ei - ej)
            H[i, j] = H[j, i] = (fpp - fpm - fmp + fmm) / (4.0 * epsilon[i] * epsilon[j])
    return H


def laplace_samples(model, map_params, active, n_samples=500, seed=0,
                    regularize=1e-5, verbose=True):
    """Draw posterior samples from Laplace approximation at MAP.

    Posterior ≈ N(map_params, H^{-1}) where H is the Hessian of -log p at MAP.
    """
    if verbose:
        print(f"  Computing Hessian ({model.n_params}x{model.n_params})...")
    H = numerical_hessian(lambda x: model.nlp(x, active), map_params)

    # Symmetrize (numerical)
    H = 0.5 * (H + H.T)

    # Regularize for positive-definiteness (Hessian of MAP should be PD;
    # numerical issues can break this)
    eigvals, eigvecs = np.linalg.eigh(H)
    min_eig = eigvals.min()
    if min_eig < regularize:
        if verbose:
            print(f"  Hessian min eigenvalue {min_eig:.3g} < {regularize:.3g}; regularizing.")
        eigvals = np.maximum(eigvals, regularize)
        H = eigvecs @ np.diag(eigvals) @ eigvecs.T

    # Covariance = H^{-1}. Factor once.
    try:
        L = np.linalg.cholesky(H)
    except np.linalg.LinAlgError:
        # Shouldn't happen after regularization, but just in case
        L = np.linalg.cholesky(H + 1e-3 * np.eye(model.n_params))

    # To sample from N(MAP, H^{-1}):
    #   H^{-1} = L^{-T} L^{-1}   (since H = L L^T)
    #   x = MAP + L^{-T} z  where z ~ N(0, I)
    # Solve L^T @ u = z  -> u = L^{-T} z
    rng = np.random.default_rng(seed)
    z = rng.standard_normal(size=(n_samples, model.n_params))
    u = np.linalg.solve(L.T, z.T).T  # (n_samples, n_params)
    samples = map_params[None, :] + u
    return samples, H


def posterior_trajectories(model, param_samples, verbose=True,
                            max_R=5.0, max_pred_multiplier=10.0):
    """Evaluate forward model at each parameter sample. Filters out
    pathological samples (R>max_R anywhere, or predictions > max_pred_multiplier * observed peak).

    These pathologies come from the Gaussian tail of the Laplace approximation
    in unconstrained log-parameter space, which can produce absurd alpha values.
    """
    N = len(param_samples)
    T = model.T; W = model.W
    log_R = np.zeros((N, T))
    I_arr = np.zeros((N, T))
    preds = {k: np.zeros((N, W)) for k in model._signals}
    obs_peaks = {k: np.nanmax(model.y[k]) for k in model._signals}
    accept = np.ones(N, dtype=bool)

    for i, p in enumerate(param_samples):
        try:
            fwd = model.forward(p)
            lr = fwd['log_R']
            # Reject if implied R exceeds max_R anywhere
            if np.exp(lr).max() > max_R:
                accept[i] = False; continue
            # Reject if any predicted signal is > max_pred_multiplier * observed peak
            bad = False
            for k in model._signals:
                pk = fwd['preds'][k]
                if (not np.all(np.isfinite(pk))) or pk.max() > max_pred_multiplier * obs_peaks[k]:
                    bad = True; break
            if bad:
                accept[i] = False; continue
            log_R[i] = lr
            I_arr[i] = fwd['I']
            for k in model._signals:
                preds[k][i] = fwd['preds'][k]
        except Exception:
            accept[i] = False
        if verbose and (i + 1) % 100 == 0:
            print(f"    trajectory {i+1}/{N}  ({accept[:i+1].sum()} accepted)")

    n_accept = accept.sum()
    if verbose:
        print(f"    accepted {n_accept}/{N} posterior samples "
              f"({100*(N-n_accept)/N:.1f}% rejected as pathological)")
    if n_accept < max(20, N // 10):
        raise RuntimeError(
            f"Laplace approximation too wide: only {n_accept}/{N} samples accepted. "
            f"Try tightening priors or narrowing the analysis window."
        )
    return dict(log_R=log_R[accept], I=I_arr[accept],
                preds={k: v[accept] for k, v in preds.items()})


# =================================================================
# 6. ONSET DETECTION (same logic as Pyro/NumPyro versions)
# =================================================================

def detect_onset_posterior(log_R_samples, ref_date,
                           sup_thresh=1.0, sup_days=7,
                           sub_thresh=0.95, sub_days=14,
                           alert_prob=0.80):
    N, T = log_R_samples.shape
    R = np.exp(log_R_samples)
    onset_days = np.full(N, np.nan)
    for i in range(N):
        Ri = R[i]
        for t in range(T - sup_days + 1):
            if not (Ri[t:t+sup_days] > sup_thresh).all(): continue
            for t0 in range(max(0, t - sub_days - 60), t - sub_days + 1):
                if (Ri[t0:t0+sub_days] < sub_thresh).all():
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
# 7. I/O
# =================================================================

def load_season(csv_path, start, end):
    df = pd.read_csv(csv_path)
    df['From'] = pd.to_datetime(df['From'], format='%d/%m/%Y')
    df['To']   = pd.to_datetime(df['To'],   format='%d/%m/%Y')
    df['MidDate'] = df['From'] + (df['To'] - df['From']) / 2
    mask = (df['MidDate'] >= start) & (df['MidDate'] <= end)
    return df.loc[mask, ['MidDate', 'AandB_proportion', 'Adm_All', 'ILI_PMP']]\
             .dropna().reset_index(drop=True)


def chp_onset_from(y_pos, dates, thresh=0.0494):
    mask = np.asarray(y_pos) > thresh
    return pd.to_datetime(dates).iloc[np.argmax(mask)] if mask.any() else None


# =================================================================
# 8. FULL-SEASON PIPELINE (MAP + Laplace + posterior analysis)
# =================================================================

def fit_season(model, active, n_samples=500, verbose=True):
    if verbose: print(f"  Fitting MAP (signals={'+'.join(active)})...")
    fit = model.fit_map(active=active)
    if verbose:
        print(f"    converged: {fit['res'].success}, nlp = {fit['res'].fun:.2f}")

    samples, H = laplace_samples(model, fit['params'], active,
                                 n_samples=n_samples, verbose=verbose)
    post = posterior_trajectories(model, samples, verbose=verbose)
    return dict(fit=fit, samples=samples, H=H, **post)


def run_demo(csv_path='flux_data.csv',
             season_start='2018-08-15', season_end='2019-05-15',
             n_samples=500):
    s = load_season(csv_path, season_start, season_end)
    print(f"Loaded {len(s)} weeks: {season_start} -> {season_end}")

    model = RenewalModel(
        dates=s['MidDate'],
        y_pos=s['AandB_proportion'].values,
        y_adm=s['Adm_All'].values,
        y_ili=s['ILI_PMP'].values,
    )
    ref = pd.to_datetime(s['MidDate'].iloc[0])
    print(f"  T = {model.T} days, K = {model.K} knots, n_params = {model.n_params}")

    print("\n--- Multi-signal (pos + adm + ili) ---")
    r_multi = fit_season(model, active=('pos','adm','ili'), n_samples=n_samples)
    onset_m = detect_onset_posterior(r_multi['log_R'], ref)

    print("\n--- Pos-only ---")
    r_pos = fit_season(model, active=('pos',), n_samples=n_samples)
    onset_p = detect_onset_posterior(r_pos['log_R'], ref)

    chp = chp_onset_from(s['AandB_proportion'].values, s['MidDate'])

    # ---- Report ----
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(f"CHP onset:       {chp.strftime('%Y-%m-%d') if chp else 'N/D'}")
    for label, onset, r in [('MULTI-SIGNAL', onset_m, r_multi),
                             ('POS-ONLY',    onset_p, r_pos)]:
        Rmax = np.exp(r['log_R']).max(axis=1)
        map_R_peak = float(np.exp(r['fit']['fwd']['log_R']).max())
        print(f"\n{label}:")
        print(f"  Posterior samples retained: {len(r['log_R'])}")
        print(f"  Detection rate:       {onset['detection_rate']*100:.1f}%")
        print(f"  Point onset (median): "
              f"{onset['point_onset'].strftime('%Y-%m-%d') if onset['point_onset'] is not None else 'N/D'}")
        print(f"  Alert date (P>=80%):  "
              f"{onset['alert_date'].strftime('%Y-%m-%d') if onset['alert_date'] else 'N/D'}")
        print(f"  MAP peak R:           {map_R_peak:.2f}")
        print(f"  Posterior peak R:     median {np.median(Rmax):.2f}, "
              f"90%PI [{np.quantile(Rmax, 0.05):.2f}, {np.quantile(Rmax, 0.95):.2f}]")
        if chp and onset['point_onset'] is not None:
            print(f"  Lead over CHP:        {(chp - onset['point_onset']).days:+d} days")

    # ---- Plot ----
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    dates_grid = ref + pd.to_timedelta(np.arange(model.T), unit='D')

    # Positivity fit
    ax = axes[0, 0]
    ax.scatter(s['MidDate'], model.y['pos']*100, c='k', s=25, zorder=5, label='obs')
    for r, lbl, col in [(r_multi, 'multi', 'b'), (r_pos, 'pos', 'r')]:
        pred = r['preds']['pos'] * 100
        ax.plot(s['MidDate'], np.median(pred, axis=0), color=col, lw=2, label=f'{lbl} median')
        ax.fill_between(s['MidDate'],
                        np.quantile(pred, 0.05, axis=0),
                        np.quantile(pred, 0.95, axis=0),
                        color=col, alpha=0.15)
    ax.axhline(4.94, color='gray', ls=':', label='CHP threshold')
    if chp: ax.axvline(chp, color='gray', ls='--', alpha=0.5)
    ax.set_ylabel('lab positivity (%)'); ax.set_title('Positivity fit ± 90% PI')
    ax.legend(fontsize=8); ax.grid(alpha=0.3)

    # R(t) with PI
    ax = axes[0, 1]
    for r, lbl, col in [(r_multi, 'multi', 'b'), (r_pos, 'pos', 'r')]:
        R = np.exp(r['log_R'])
        ax.plot(dates_grid, np.median(R, axis=0), color=col, lw=2.5, label=f'{lbl} median')
        ax.fill_between(dates_grid,
                        np.quantile(R, 0.05, axis=0),
                        np.quantile(R, 0.95, axis=0),
                        color=col, alpha=0.15)
    ax.axhline(1.0, color='k', ls=':', lw=1)
    ax.axhline(0.95, color='gray', ls=':', lw=0.5)
    if chp: ax.axvline(chp, color='gray', ls='--', alpha=0.6, label='CHP')
    ax.set_ylim(0.3, 2.2); ax.set_ylabel('R(t)')
    ax.set_title('R(t) posterior median ± 90% PI')
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
    ax.scatter(s['MidDate'], model.y['adm'], c='k', s=25, zorder=5, label='obs')
    pred = r_multi['preds']['adm']
    ax.plot(s['MidDate'], np.median(pred, axis=0), 'b-', lw=2, label='multi median')
    ax.fill_between(s['MidDate'],
                    np.quantile(pred, 0.05, axis=0),
                    np.quantile(pred, 0.95, axis=0),
                    color='b', alpha=0.15)
    ax.set_ylabel('admissions / 10k')
    ax.set_title('Admissions fit (multi) ± 90% PI')
    ax.legend(fontsize=8); ax.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig('renewal_map_demo.png', dpi=140, bbox_inches='tight')
    print(f"\nFigure: renewal_map_demo.png")

    return dict(s=s, model=model, r_multi=r_multi, r_pos=r_pos,
                onset_m=onset_m, onset_p=onset_p, chp=chp, ref=ref)


# =================================================================
# 9. NOWCAST SWEEP
# =================================================================

def nowcast(season_df, cutoff_week, active_signals=('pos','adm','ili'),
            n_samples=300):
    s_trunc = season_df.iloc[:cutoff_week].reset_index(drop=True)
    model = RenewalModel(
        dates=s_trunc['MidDate'],
        y_pos=s_trunc['AandB_proportion'].values,
        y_adm=s_trunc['Adm_All'].values,
        y_ili=s_trunc['ILI_PMP'].values,
    )
    ref = pd.to_datetime(s_trunc['MidDate'].iloc[0])
    r = fit_season(model, active=active_signals, n_samples=n_samples, verbose=False)
    onset = detect_onset_posterior(r['log_R'], ref)
    return dict(cutoff_week=cutoff_week, ref=ref, T=model.T, onset=onset, r=r)


def run_nowcast_sweep(csv_path='flux_data.csv',
                      season_start='2018-06-01', season_end='2019-06-01',
                      cutoffs=(8, 12, 16, 20, 24, 28, 36),
                      active_sets=(('pos','adm','ili'), ('pos',)),
                      n_samples=300):
    s = load_season(csv_path, season_start, season_end)
    chp = chp_onset_from(s['AandB_proportion'].values, s['MidDate'])
    rows = []
    for k in cutoffs:
        if k > len(s): continue
        for active in active_sets:
            lbl = '+'.join(active)
            print(f"\n[nowcast] cutoff={k}wk  signals={lbl}")
            try:
                nc = nowcast(s, cutoff_week=k, active_signals=active, n_samples=n_samples)
                onset = nc['onset']
                data_end = pd.to_datetime(s['MidDate'].iloc[k-1])
                row = dict(
                    cutoff_week=k, signals=lbl,
                    data_end=data_end, chp=chp,
                    chp_declared_by_cutoff=(chp is not None and chp <= data_end),
                    detection_rate=onset['detection_rate'],
                    point_onset=onset['point_onset'],
                    alert_date=onset['alert_date'],
                    lead_over_chp=((chp - onset['point_onset']).days
                                   if (chp and onset['point_onset']) else None),
                )
                rows.append(row)
                print(f"  detect={onset['detection_rate']*100:.0f}%  "
                      f"point={row['point_onset']}  alert={row['alert_date']}  "
                      f"lead={row['lead_over_chp']}")
            except Exception as e:
                print(f"  FAILED: {e}")
    return pd.DataFrame(rows)


# =================================================================
# 10. MULTI-SEASON RETROSPECTIVE
# =================================================================

RETRO_SEASONS = [
    ('2014/15 W', '2014-06-01', '2015-06-01'),
    ('2015/16 W', '2015-06-01', '2016-06-01'),
    ('2018/19 W', '2018-06-01', '2019-06-01'),
    ('2023 S',    '2022-12-01', '2023-08-01'),
    ('2024/25 W', '2024-06-01', '2025-05-01'),
]


def run_retrospective(csv_path='flux_data.csv', n_samples=300):
    rows = []
    for name, start, end in RETRO_SEASONS:
        try:
            s = load_season(csv_path, start, end)
            if len(s) < 20:
                print(f"SKIP {name}: {len(s)} weeks")
                continue
            print(f"\n=== {name} | {start} -> {end} | {len(s)} wks ===")
            model = RenewalModel(
                dates=s['MidDate'],
                y_pos=s['AandB_proportion'].values,
                y_adm=s['Adm_All'].values,
                y_ili=s['ILI_PMP'].values,
            )
            ref = pd.to_datetime(s['MidDate'].iloc[0])
            chp = chp_onset_from(s['AandB_proportion'].values, s['MidDate'])

            r_m = fit_season(model, active=('pos','adm','ili'), n_samples=n_samples, verbose=False)
            r_p = fit_season(model, active=('pos',), n_samples=n_samples, verbose=False)
            onset_m = detect_onset_posterior(r_m['log_R'], ref)
            onset_p = detect_onset_posterior(r_p['log_R'], ref)

            lead_m = (chp - onset_m['point_onset']).days if (chp and onset_m['point_onset']) else None
            lead_p = (chp - onset_p['point_onset']).days if (chp and onset_p['point_onset']) else None

            rows.append(dict(
                season=name, n_weeks=len(s),
                chp_onset=chp,
                multi_onset=onset_m['point_onset'], multi_alert=onset_m['alert_date'],
                multi_lead=lead_m, multi_detrate=onset_m['detection_rate'],
                multi_peakR_mean=float(np.exp(r_m['log_R']).max(axis=1).mean()),
                pos_onset=onset_p['point_onset'], pos_alert=onset_p['alert_date'],
                pos_lead=lead_p, pos_detrate=onset_p['detection_rate'],
                pos_peakR_mean=float(np.exp(r_p['log_R']).max(axis=1).mean()),
            ))
            print(f"  CHP: {chp}  Multi: {onset_m['point_onset']} (lead {lead_m})  "
                  f"Pos: {onset_p['point_onset']} (lead {lead_p})")
        except Exception as e:
            print(f"FAIL {name}: {e}")
    return pd.DataFrame(rows)


# =================================================================
if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'demo'

    if mode == 'demo':
        run_demo()

    elif mode == 'nowcast':
        df = run_nowcast_sweep()
        df.to_csv('nowcast_map.csv', index=False)
        print("\n" + df.to_string())

    elif mode == 'retro':
        df = run_retrospective()
        df.to_csv('retro_map.csv', index=False)
        print("\n" + df.to_string())

    else:
        print(f"Unknown mode: {mode}. Use demo / nowcast / retro.")
