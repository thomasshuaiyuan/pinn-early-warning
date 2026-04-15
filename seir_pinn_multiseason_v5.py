"""
SEIR-PINN Multi-Season Validation — v5 Multi-Signal
=====================================================
Key change from v4: the model now fits THREE surveillance signals
simultaneously, each mapped to a different SEIR compartment:

  1. Lab positivity (AandB_proportion) → obs_scale_pos * I(t)
     Prevalence proxy: fraction currently infected and tested.

  2. ILI GP consultations (ILI_PMP) → obs_scale_ili * sigma * E(t)
     Incidence proxy: people visit GP at symptom onset = E→I transition.
     This signal LEADS lab positivity because E peaks before I.

  3. Hospital admissions (Adm_All) → obs_scale_adm * I(t)
     Prevalence proxy with severity filter.

By fitting signals that map to DIFFERENT compartments (E vs I),
the model gets a timing constraint that properly identifies sigma
and gamma, instead of distorting gamma to match a single broad curve.

All signals are min-max normalized to [0, 1] before fitting so
MSE terms are comparable regardless of original units.

Run: conda activate pinn && python seir_pinn_multiseason_v5.py

Thomas Yuan — HKU PhD, Pathogen Evolution Lab
"""

import torch
import torch.nn as nn
import numpy as np
import pandas as pd
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

CHP_THRESHOLD = 0.0494

# ============================================================
# MODEL
# ============================================================

class SEIR_PINN(nn.Module):
    """Multi-signal SEIR-PINN.

    Three observation parameters map SEIR states to different signals:
      - obs_scale_pos:  positivity ≈ scale * I(t)
      - obs_scale_ili:  ILI rate   ≈ scale * sigma * E(t)   [incidence]
      - obs_scale_adm:  admissions ≈ scale * I(t)
    """

    def __init__(self, hidden_layers=4, hidden_neurons=64):
        super().__init__()

        layers = []
        layers.append(nn.Linear(1, hidden_neurons))
        layers.append(nn.Tanh())
        for _ in range(hidden_layers - 1):
            layers.append(nn.Linear(hidden_neurons, hidden_neurons))
            layers.append(nn.Tanh())
        layers.append(nn.Linear(hidden_neurons, 4))
        self.state_net = nn.Sequential(*layers)

        self.beta_net = nn.Sequential(
            nn.Linear(1, 32), nn.Tanh(),
            nn.Linear(32, 32), nn.Tanh(),
            nn.Linear(32, 1),
        )

        # Epi parameters (log-space)
        self.log_sigma = nn.Parameter(torch.tensor(-0.7))   # ~0.5/day
        self.log_gamma = nn.Parameter(torch.tensor(-1.6))   # ~0.2/day

        # Per-signal observation scales (log-space)
        self.log_obs_pos = nn.Parameter(torch.tensor(0.0))
        self.log_obs_ili = nn.Parameter(torch.tensor(0.0))
        self.log_obs_adm = nn.Parameter(torch.tensor(0.0))

    def forward(self, t):
        raw = self.state_net(t)
        states = torch.softmax(raw, dim=1)
        return states[:, 0:1], states[:, 1:2], states[:, 2:3], states[:, 3:4]

    def get_beta(self, t):
        return nn.functional.softplus(self.beta_net(t)) * 0.5 + 0.05

    @property
    def sigma(self):
        return torch.exp(self.log_sigma)

    @property
    def gamma(self):
        return torch.exp(self.log_gamma)

    def predict_signals(self, t):
        """Predict all three normalised surveillance signals."""
        S, E, I, R = self.forward(t)
        pos_pred = torch.exp(self.log_obs_pos) * I
        ili_pred = torch.exp(self.log_obs_ili) * self.sigma * E  # incidence
        adm_pred = torch.exp(self.log_obs_adm) * I
        return pos_pred, ili_pred, adm_pred

    def compute_Rt(self, t):
        S, E, I, R = self.forward(t)
        beta = self.get_beta(t)
        return beta * S / self.gamma


# ============================================================
# LOSS
# ============================================================

def compute_loss(model, t_data, targets, signal_mask, t_physics, t_max):
    """Multi-signal SEIR-PINN loss.

    Args:
        t_data:      observation times [N, 1]
        targets:     dict of signal_name → tensor [N, 1] (normalised)
        signal_mask: dict of signal_name → boolean tensor [N, 1]
                     (True where signal is valid / not NaN)
        t_physics:   collocation points (requires_grad)
        t_max:       season span in days
    """
    # --- MULTI-SIGNAL DATA LOSS ---
    pos_pred, ili_pred, adm_pred = model.predict_signals(t_data)
    preds = {"pos": pos_pred, "ili": ili_pred, "adm": adm_pred}

    data_loss = torch.tensor(0.0)
    n_signals = 0
    for key in ["pos", "ili", "adm"]:
        if key in targets and signal_mask[key].any():
            mask = signal_mask[key]
            diff = (preds[key][mask] - targets[key][mask]) ** 2
            data_loss = data_loss + diff.mean()
            n_signals += 1
    if n_signals > 0:
        data_loss = data_loss / n_signals  # average across active signals

    # --- PHYSICS LOSS ---
    S, E, I, R = model(t_physics)
    beta = model.get_beta(t_physics)
    sigma = model.sigma
    gamma = model.gamma

    dSdt = torch.autograd.grad(S, t_physics, torch.ones_like(S), create_graph=True)[0]
    dEdt = torch.autograd.grad(E, t_physics, torch.ones_like(E), create_graph=True)[0]
    dIdt = torch.autograd.grad(I, t_physics, torch.ones_like(I), create_graph=True)[0]
    dRdt = torch.autograd.grad(R, t_physics, torch.ones_like(R), create_graph=True)[0]

    scale = t_max
    res_S = dSdt / scale + beta * S * I
    res_E = dEdt / scale - beta * S * I + sigma * E
    res_I = dIdt / scale - sigma * E + gamma * I
    res_R = dRdt / scale - gamma * I

    physics_loss = (torch.mean(res_S**2) + torch.mean(res_E**2) +
                    torch.mean(res_I**2) + torch.mean(res_R**2))

    # --- INITIAL CONDITION LOSS ---
    t0 = torch.tensor([[0.0]])
    S0, E0, I0, R0 = model(t0)
    ic_loss = ((S0 - 0.98)**2 + (E0 - 0.005)**2 +
               (I0 - 0.005)**2 + (R0 - 0.01)**2).sum()

    total = 10.0 * data_loss + 1.0 * physics_loss + 5.0 * ic_loss
    return total, data_loss, physics_loss, ic_loss


# ============================================================
# NORMALISATION HELPERS
# ============================================================

def safe_normalise(arr):
    """Min-max normalise to [0, 1]. Returns (normalised, min, max)."""
    mn = np.nanmin(arr)
    mx = np.nanmax(arr)
    rng = mx - mn
    if rng < 1e-12:
        return np.zeros_like(arr), mn, mx
    return (arr - mn) / rng, mn, mx


# ============================================================
# RUN ONE SEASON
# ============================================================

def run_season(df, start_date, end_date, season_name,
               burn_in_weeks=4,
               n_epochs=15000, hidden_layers=4, hidden_neurons=64,
               n_colloc=300, seed=42, verbose=True):

    mask = (df["MidDate"] >= start_date) & (df["MidDate"] <= end_date)
    season = df.loc[mask].copy()
    # Need at least positivity; others can have gaps
    season = season.dropna(subset=["AandB_proportion"]).reset_index(drop=True)

    if len(season) < 8:
        if verbose:
            print(f"\n  SKIP {season_name}: only {len(season)} data points")
        return None

    t_days = (season["MidDate"] - season["MidDate"].min()).dt.days.values.astype(float)
    t_max = t_days.max()
    if t_max == 0:
        return None
    t_norm = t_days / t_max

    # --- Extract and normalise signals ---
    pos_raw = season["AandB_proportion"].values.astype(float)
    ili_raw = season["ILI_PMP"].values.astype(float) if "ILI_PMP" in season.columns else np.full(len(season), np.nan)
    adm_raw = season["Adm_All"].values.astype(float) if "Adm_All" in season.columns else np.full(len(season), np.nan)

    pos_norm, pos_mn, pos_mx = safe_normalise(pos_raw)
    ili_norm, ili_mn, ili_mx = safe_normalise(ili_raw)
    adm_norm, adm_mn, adm_mx = safe_normalise(adm_raw)

    peak_pos = pos_raw.max()

    # Build tensors + NaN masks
    t_data = torch.tensor(t_norm, dtype=torch.float32).reshape(-1, 1)

    targets = {}
    signal_mask = {}
    for key, arr in [("pos", pos_norm), ("ili", ili_norm), ("adm", adm_norm)]:
        valid = ~np.isnan(arr)
        vals = np.where(valid, arr, 0.0)
        targets[key] = torch.tensor(vals, dtype=torch.float32).reshape(-1, 1)
        signal_mask[key] = torch.tensor(valid, dtype=torch.bool).reshape(-1, 1)

    n_ili = signal_mask["ili"].sum().item()
    n_adm = signal_mask["adm"].sum().item()

    t_colloc = torch.linspace(0, 1, n_colloc, dtype=torch.float32).reshape(-1, 1)
    t_colloc.requires_grad = True

    # --- Model ---
    torch.manual_seed(seed)
    model = SEIR_PINN(hidden_layers=hidden_layers, hidden_neurons=hidden_neurons)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=3000, gamma=0.5)

    if verbose:
        print(f"\n{'='*70}")
        print(f"  SEASON: {season_name}  |  {start_date} -> {end_date}  |  {len(season)} wks  |  peak {peak_pos*100:.1f}%")
        print(f"  Signals: pos={len(season)}, ili={n_ili}, adm={n_adm}")
        print(f"{'='*70}")

    # --- Train ---
    for epoch in range(n_epochs):
        optimizer.zero_grad()
        total, d_loss, p_loss, ic_loss = compute_loss(
            model, t_data, targets, signal_mask, t_colloc, t_max
        )
        total.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
        scheduler.step()

        # Clamp epi params
        with torch.no_grad():
            model.log_gamma.clamp_(np.log(0.1), np.log(0.5))
            model.log_sigma.clamp_(np.log(0.2), np.log(1.0))

        if verbose and (epoch + 1) % 5000 == 0:
            print(f"    epoch {epoch+1:>6}  loss={total.item():.6f}  "
                  f"data={d_loss.item():.6f}  phys={p_loss.item():.6f}  "
                  f"sigma={model.sigma.item():.4f}  gamma={model.gamma.item():.4f}")

    final_loss = total.item()

    # --- Evaluate R(t) ---
    t_eval = torch.linspace(0, 1, 500, dtype=torch.float32).reshape(-1, 1)
    with torch.no_grad():
        Rt_pred = model.compute_Rt(t_eval).numpy().flatten()

    t_eval_days = t_eval.numpy().flatten() * t_max
    dates_eval = pd.to_datetime(start_date) + pd.to_timedelta(t_eval_days, unit="D")

    best_Rt = float(Rt_pred.max())

    # --- PINN onset (post burn-in) ---
    burn_in_days = burn_in_weeks * 7
    burn_in_idx = int(np.searchsorted(t_eval_days, burn_in_days))
    if verbose:
        burn_date = (pd.to_datetime(start_date) + pd.to_timedelta(burn_in_days, unit="D")).strftime("%Y-%m-%d")
        print(f"  (burn-in: ignoring R(t) before {burn_date})")

    rt_post = Rt_pred[burn_in_idx:]
    rt_above = np.where(rt_post > 1.0)[0]
    pinn_onset_date = None
    if len(rt_above) > 0:
        consec = 1
        onset_idx = None
        for i in range(1, len(rt_above)):
            if rt_above[i] == rt_above[i-1] + 1:
                consec += 1
                if consec >= 3:
                    onset_idx = rt_above[i-2] + burn_in_idx
                    break
            else:
                consec = 1
        if onset_idx is None and len(rt_above) >= 3:
            onset_idx = rt_above[0] + burn_in_idx
        if onset_idx is not None:
            pinn_onset_date = dates_eval[onset_idx].strftime("%Y-%m-%d")

    # --- CHP onset ---
    above_thresh = season[season["AandB_proportion"] > CHP_THRESHOLD]
    chp_onset_date = above_thresh.iloc[0]["MidDate"].strftime("%Y-%m-%d") if len(above_thresh) > 0 else None

    # --- Lead time ---
    lead_days = None
    if pinn_onset_date and chp_onset_date:
        lead_days = (pd.to_datetime(chp_onset_date) - pd.to_datetime(pinn_onset_date)).days

    result = {
        "season_name": season_name,
        "start_date": start_date,
        "end_date": end_date,
        "n_weeks": len(season),
        "peak_positivity": round(peak_pos * 100, 2),
        "pinn_onset_date": pinn_onset_date,
        "chp_onset_date": chp_onset_date,
        "lead_days": lead_days,
        "best_Rt": round(best_Rt, 3),
        "sigma": round(model.sigma.item(), 4),
        "gamma": round(model.gamma.item(), 4),
        "incubation_days": round(1.0 / model.sigma.item(), 1),
        "infectious_days": round(1.0 / model.gamma.item(), 1),
        "final_loss": round(final_loss, 6),
    }

    if verbose:
        print(f"  -> PINN onset:  {pinn_onset_date or 'not detected'}")
        print(f"  -> CHP onset:   {chp_onset_date or 'not detected'}")
        if lead_days is not None:
            sign = "PINN leads" if lead_days > 0 else ("CHP leads" if lead_days < 0 else "same day")
            print(f"  -> Lead time:   {abs(lead_days)} days ({sign})")
        print(f"  -> Best R(t):   {best_Rt:.3f}")
        print(f"  -> Epi params:  incubation={result['incubation_days']}d  infectious={result['infectious_days']}d")

    return result


# ============================================================
# SEASONS (extended windows with baseline lead-in)
# ============================================================
SEASONS = [
    ("2014/15 winter", "2014-10-01", "2015-06-01", 4),
    ("2015/16 winter", "2015-10-01", "2016-06-01", 4),
    ("2016/17 winter", "2016-09-15", "2017-06-01", 4),
    ("2017/18 summer", "2017-04-01", "2018-04-01", 4),
    ("2018/19 winter", "2018-09-15", "2019-06-01", 4),
    ("2023 summer",    "2023-01-15", "2023-10-01", 4),
    ("2023/24 winter", "2023-07-15", "2024-04-01", 4),
    ("2024/25 winter", "2024-08-01", "2025-04-01", 4),
]


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    print("=" * 70)
    print("SEIR-PINN MULTI-SEASON VALIDATION (v5: Multi-Signal)")
    print("Hong Kong Influenza Onset Detection — CHP Flu Express 2014-2026")
    print("=" * 70)

    df = pd.read_csv("flux_data.csv")
    df["From"] = pd.to_datetime(df["From"], format="%d/%m/%Y")
    df["To"] = pd.to_datetime(df["To"], format="%d/%m/%Y")
    df["MidDate"] = df["From"] + (df["To"] - df["From"]) / 2

    results = []
    for season_name, start, end, burn_in in SEASONS:
        res = run_season(df, start, end, season_name,
                         burn_in_weeks=burn_in, n_epochs=15000, verbose=True)
        if res is not None:
            results.append(res)

    if not results:
        print("\nNo seasons completed.")
    else:
        results_df = pd.DataFrame(results)
        results_df.to_csv("validation_results_v5.csv", index=False)
        print(f"\n\nResults saved to validation_results_v5.csv")

        print("\n" + "=" * 110)
        print("TABLE 1: PINN vs CHP Onset Detection (v5: Multi-Signal)")
        print("=" * 110)
        print(f"{'Season':<18} {'Wks':>4} {'Peak%':>6} {'PINN Onset':>12} "
              f"{'CHP Onset':>12} {'Lead(d)':>8} {'R(t)max':>8} {'Incub':>6} {'Infect':>7} {'Loss':>10}")
        print("-" * 110)
        for _, r in results_df.iterrows():
            lead_str = f"{r['lead_days']:.0f}" if pd.notna(r["lead_days"]) else "N/A"
            pinn_str = r["pinn_onset_date"] if r["pinn_onset_date"] else "not det."
            chp_str = r["chp_onset_date"] if r["chp_onset_date"] else "not det."
            print(f"{r['season_name']:<18} {r['n_weeks']:>4} {r['peak_positivity']:>5.1f}% "
                  f"{pinn_str:>12} {chp_str:>12} {lead_str:>8} "
                  f"{r['best_Rt']:>8.3f} {r['incubation_days']:>5.1f}d {r['infectious_days']:>6.1f}d "
                  f"{r['final_loss']:>10.6f}")

        valid = results_df.dropna(subset=["lead_days"])
        if len(valid) > 0:
            print(f"\n--- Summary ({len(valid)} seasons with both onsets) ---")
            print(f"  Mean lead:   {valid['lead_days'].mean():.1f} days")
            print(f"  Median lead: {valid['lead_days'].median():.1f} days")
            print(f"  Range:       {valid['lead_days'].min():.0f} to {valid['lead_days'].max():.0f} days")
            print(f"  PINN leads:  {(valid['lead_days'] > 0).sum()}/{len(valid)}")
