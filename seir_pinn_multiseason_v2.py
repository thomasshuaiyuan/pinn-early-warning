"""
SEIR-PINN Multi-Season Validation Framework
=============================================
Retrospective validation of PINN-based influenza onset detection
across all available CHP Flu Express seasons (2014–2026).

Compares PINN R(t) > 1 onset detection against CHP's static
threshold method (~4.94% lab positivity) to quantify lead time.

Output: validation_results.csv (Table 1 of your paper)

Run: conda activate pinn && python seir_pinn_multiseason.py

Thomas Yuan — HKU PhD, Pathogen Evolution Lab
"""

import torch
import torch.nn as nn
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import warnings
import os

warnings.filterwarnings("ignore")

# ============================================================
# CHP THRESHOLD (reported by Centre for Health Protection)
# ============================================================
CHP_THRESHOLD = 0.0494  # 4.94% lab positivity

# ============================================================
# MODEL DEFINITION
# ============================================================

class SEIR_PINN(nn.Module):
    """SEIR Physics-Informed Neural Network for influenza surveillance.

    Two sub-networks:
      1. State network:     t -> (S, E, I, R)   via softmax (population conservation)
      2. Parameter network:  t -> beta(t)        via softplus (positivity)

    Learnable scalar parameters: sigma (1/incubation), gamma (1/infectious),
    obs_scale (maps I(t) to observable lab positivity).
    """

    def __init__(self, hidden_layers=4, hidden_neurons=64):
        super().__init__()

        # State network: t -> S(t), E(t), I(t), R(t)
        layers = []
        layers.append(nn.Linear(1, hidden_neurons))
        layers.append(nn.Tanh())
        for _ in range(hidden_layers - 1):
            layers.append(nn.Linear(hidden_neurons, hidden_neurons))
            layers.append(nn.Tanh())
        layers.append(nn.Linear(hidden_neurons, 4))
        self.state_net = nn.Sequential(*layers)

        # Beta network: t -> beta(t)
        self.beta_net = nn.Sequential(
            nn.Linear(1, 32), nn.Tanh(),
            nn.Linear(32, 32), nn.Tanh(),
            nn.Linear(32, 1),
        )

        # Learnable epi parameters (log-space for positivity)
        self.log_sigma = nn.Parameter(torch.tensor(-0.7))   # ~0.5 /day  (incubation ~2d)
        self.log_gamma = nn.Parameter(torch.tensor(-1.6))   # ~0.2 /day  (infectious ~5d)
        self.log_obs_scale = nn.Parameter(torch.tensor(0.0))

    def forward(self, t):
        raw = self.state_net(t)
        states = torch.softmax(raw, dim=1)
        return states[:, 0:1], states[:, 1:2], states[:, 2:3], states[:, 3:4]

    def get_beta(self, t):
        return torch.nn.functional.softplus(self.beta_net(t)) * 0.5 + 0.05

    @property
    def sigma(self):
        return torch.exp(self.log_sigma)

    @property
    def gamma(self):
        return torch.exp(self.log_gamma)

    @property
    def obs_scale(self):
        return torch.exp(self.log_obs_scale)

    def compute_Rt(self, t):
        S, E, I, R = self.forward(t)
        beta = self.get_beta(t)
        return beta * S / self.gamma


def compute_seir_loss(model, t_data, I_data, t_physics, t_max):
    """SEIR-PINN loss: data fit + ODE residuals + initial conditions.

    Args:
        model:     SEIR_PINN instance
        t_data:    observation times (normalized [0,1])
        I_data:    observed lab positivity at t_data
        t_physics: collocation points (normalized, requires_grad=True)
        t_max:     season duration in days (for time-scaling derivatives)
    """
    # --- DATA LOSS ---
    _, _, I_d, _ = model(t_data)
    I_pred = model.obs_scale * I_d
    data_loss = torch.mean((I_pred - I_data) ** 2)

    # --- PHYSICS LOSS ---
    S, E, I, R = model(t_physics)
    beta = model.get_beta(t_physics)
    sigma = model.sigma
    gamma = model.gamma

    dSdt = torch.autograd.grad(S, t_physics, torch.ones_like(S), create_graph=True)[0]
    dEdt = torch.autograd.grad(E, t_physics, torch.ones_like(E), create_graph=True)[0]
    dIdt = torch.autograd.grad(I, t_physics, torch.ones_like(I), create_graph=True)[0]
    dRdt = torch.autograd.grad(R, t_physics, torch.ones_like(R), create_graph=True)[0]

    scale = t_max  # normalized -> real-time

    res_S = dSdt / scale + beta * S * I
    res_E = dEdt / scale - beta * S * I + sigma * E
    res_I = dIdt / scale - sigma * E + gamma * I
    res_R = dRdt / scale - gamma * I

    physics_loss = (torch.mean(res_S**2) + torch.mean(res_E**2) +
                    torch.mean(res_I**2) + torch.mean(res_R**2))

    # --- INITIAL CONDITION LOSS ---
    # With extended windows, t=0 is true baseline: near-zero infection
    t0 = torch.tensor([[0.0]])
    S0, E0, I0, R0 = model(t0)
    ic_loss = ((S0 - 0.98)**2 + (E0 - 0.005)**2 +
               (I0 - 0.005)**2 + (R0 - 0.01)**2).sum()

    # --- PARAMETER PRIOR LOSS ---
    # Penalise gamma outside biologically plausible range for influenza.
    # Infectious period = 1/gamma should be 3–7 days → gamma in [0.14, 0.33].
    # Similarly sigma: incubation 1–3 days → sigma in [0.33, 1.0].
    # Log-normal prior centred on gamma=0.2 (5d) and sigma=0.5 (2d).
    gamma = model.gamma
    sigma = model.sigma
    prior_loss = ((torch.log(gamma) - torch.log(torch.tensor(0.2)))**2 +
                  (torch.log(sigma) - torch.log(torch.tensor(0.5)))**2)

    # --- WEIGHTED TOTAL ---
    total = 10.0 * data_loss + 1.0 * physics_loss + 5.0 * ic_loss + 2.0 * prior_loss
    return total, data_loss, physics_loss, ic_loss


# ============================================================
# CORE FUNCTION: RUN ONE SEASON
# ============================================================

def run_season(df, start_date, end_date, season_name,
               burn_in_weeks=4,
               n_epochs=15000, hidden_layers=4, hidden_neurons=64,
               n_colloc=300, seed=42, verbose=True):
    """Train SEIR-PINN on one influenza season and extract onset metrics.

    Args:
        df:           Full CHP Flu Express DataFrame (with MidDate column)
        start_date:   Season window start (str, 'YYYY-MM-DD')
        end_date:     Season window end
        season_name:  Label for this season (e.g. '2017/18 winter')
        burn_in_weeks: Ignore R(t) during this initial period for onset detection.
                       Prevents boundary artifacts where R(t) > 1 at t=0.
        n_epochs:     Training iterations
        hidden_layers, hidden_neurons: Architecture
        n_colloc:     Number of physics collocation points
        seed:         Random seed for reproducibility
        verbose:      Print training progress

    Returns:
        dict with keys: season_name, n_weeks, peak_positivity,
                        pinn_onset_date, chp_onset_date, lead_days,
                        best_Rt, sigma, gamma, obs_scale, final_loss
        None if season has < 8 valid data points.
    """
    # --- Slice season ---
    mask = (df["MidDate"] >= start_date) & (df["MidDate"] <= end_date)
    season = df.loc[mask].dropna(subset=["AandB_proportion"]).copy()
    season = season.reset_index(drop=True)

    if len(season) < 8:
        if verbose:
            print(f"\n  SKIP {season_name}: only {len(season)} data points (need >=8)")
        return None

    # --- Prepare tensors ---
    t_days = (season["MidDate"] - season["MidDate"].min()).dt.days.values.astype(float)
    t_max = t_days.max()
    if t_max == 0:
        if verbose:
            print(f"\n  SKIP {season_name}: zero time span")
        return None
    t_norm = t_days / t_max

    I_obs = season["AandB_proportion"].values
    peak_pos = I_obs.max()

    t_data = torch.tensor(t_norm, dtype=torch.float32).reshape(-1, 1)
    I_data = torch.tensor(I_obs, dtype=torch.float32).reshape(-1, 1)

    t_colloc = torch.linspace(0, 1, n_colloc, dtype=torch.float32).reshape(-1, 1)
    t_colloc.requires_grad = True

    # --- Initialise model ---
    torch.manual_seed(seed)
    model = SEIR_PINN(hidden_layers=hidden_layers, hidden_neurons=hidden_neurons)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=3000, gamma=0.5)

    # --- Train ---
    if verbose:
        print(f"\n{'='*70}")
        print(f"  SEASON: {season_name}  |  {start_date} -> {end_date}  |  {len(season)} weeks  |  peak {peak_pos*100:.1f}%")
        print(f"{'='*70}")

    for epoch in range(n_epochs):
        optimizer.zero_grad()
        total, d_loss, p_loss, ic_loss = compute_seir_loss(
            model, t_data, I_data, t_colloc, t_max
        )
        total.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
        scheduler.step()

        if verbose and (epoch + 1) % 5000 == 0:
            print(f"    epoch {epoch+1:>6}  loss={total.item():.6f}  "
                  f"data={d_loss.item():.6f}  phys={p_loss.item():.6f}  "
                  f"sigma={model.sigma.item():.4f}  gamma={model.gamma.item():.4f}")

    final_loss = total.item()

    # --- Evaluate: extract R(t) ---
    t_eval = torch.linspace(0, 1, 500, dtype=torch.float32).reshape(-1, 1)
    with torch.no_grad():
        Rt_pred = model.compute_Rt(t_eval).numpy().flatten()
        S_pred, E_pred, I_pred, R_pred = model(t_eval)

    t_eval_days = t_eval.numpy().flatten() * t_max
    dates_eval = pd.to_datetime(start_date) + pd.to_timedelta(t_eval_days, unit="D")

    best_Rt = float(Rt_pred.max())

    # --- PINN onset: first time R(t) > 1.0 AFTER burn-in period ---
    burn_in_days = burn_in_weeks * 7
    burn_in_idx = int(np.searchsorted(t_eval_days, burn_in_days))
    if verbose:
        burn_in_date = (pd.to_datetime(start_date) +
                        pd.to_timedelta(burn_in_days, unit="D")).strftime("%Y-%m-%d")
        print(f"  (burn-in: ignoring R(t) before {burn_in_date})")

    # Only search for onset after the burn-in window
    rt_post_burnin = Rt_pred[burn_in_idx:]
    idx_offset = burn_in_idx  # map back to full array indices

    rt_above = np.where(rt_post_burnin > 1.0)[0]
    if len(rt_above) > 0:
        # Require R(t) > 1 for at least 3 consecutive eval points to avoid noise spikes
        consec = 1
        pinn_onset_idx = None
        for i in range(1, len(rt_above)):
            if rt_above[i] == rt_above[i - 1] + 1:
                consec += 1
                if consec >= 3:
                    pinn_onset_idx = rt_above[i - 2] + idx_offset
                    break
            else:
                consec = 1
        if pinn_onset_idx is None and len(rt_above) >= 3:
            pinn_onset_idx = rt_above[0] + idx_offset
        pinn_onset_date = dates_eval[pinn_onset_idx].strftime("%Y-%m-%d") if pinn_onset_idx is not None else None
    else:
        pinn_onset_date = None

    # --- CHP onset: first week above threshold ---
    above_thresh = season[season["AandB_proportion"] > CHP_THRESHOLD]
    if len(above_thresh) > 0:
        chp_onset_date = above_thresh.iloc[0]["MidDate"].strftime("%Y-%m-%d")
    else:
        chp_onset_date = None

    # --- Lead time ---
    if pinn_onset_date and chp_onset_date:
        lead_days = (pd.to_datetime(chp_onset_date) - pd.to_datetime(pinn_onset_date)).days
    else:
        lead_days = None

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
        "obs_scale": round(model.obs_scale.item(), 4),
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
# SEASON DEFINITIONS
# ============================================================
# Windows now start ~8 weeks BEFORE historical CHP onset so the
# PINN sees flat baseline data first.  This eliminates the
# boundary artifact where R(t) > 1 at t=0 just because the
# model has no pre-season context.
#
# Format: (name, window_start, window_end, burn_in_weeks)
# burn_in_weeks: ignore R(t) in this initial period for onset detection

SEASONS = [
    ("2014/15 winter", "2014-10-01", "2015-06-01", 4),
    ("2015/16 winter", "2015-10-01", "2016-06-01", 4),
    ("2016/17 winter", "2016-09-15", "2017-06-01", 4),
    ("2017/18 summer", "2017-04-01", "2018-04-01", 4),   # unusual summer wave
    ("2018/19 winter", "2018-09-15", "2019-06-01", 4),
    # 2020-2022: COVID NPIs — influenza near-zero, not trainable
    ("2023 summer",    "2023-01-15", "2023-10-01", 4),
    ("2023/24 winter", "2023-07-15", "2024-04-01", 4),
    ("2024/25 winter", "2024-08-01", "2025-04-01", 4),
]


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    print("=" * 70)
    print("SEIR-PINN MULTI-SEASON VALIDATION")
    print("Hong Kong Influenza Onset Detection — CHP Flu Express 2014-2026")
    print("=" * 70)

    # Load data
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

    # --------------------------------------------------------
    # RESULTS TABLE
    # --------------------------------------------------------
    if not results:
        print("\nNo seasons completed. Check data availability.")
    else:
        results_df = pd.DataFrame(results)

        # Save CSV — Table 1 of the paper
        csv_path = "validation_results.csv"
        results_df.to_csv(csv_path, index=False)
        print(f"\n\nResults saved to {csv_path}")

        # Print summary
        print("\n" + "=" * 110)
        print("TABLE 1: PINN vs CHP Onset Detection Across Hong Kong Influenza Seasons")
        print("=" * 110)
        print(f"{'Season':<18} {'Weeks':>5} {'Peak%':>6} {'PINN Onset':>12} "
              f"{'CHP Onset':>12} {'Lead (d)':>9} {'R(t)max':>8} {'Incub':>6} {'Infect':>7} {'Loss':>10}")
        print("-" * 110)
        for _, r in results_df.iterrows():
            lead_str = f"{r['lead_days']:.0f}" if pd.notna(r["lead_days"]) else "N/A"
            pinn_str = r["pinn_onset_date"] if r["pinn_onset_date"] else "not det."
            chp_str = r["chp_onset_date"] if r["chp_onset_date"] else "not det."
            print(f"{r['season_name']:<18} {r['n_weeks']:>5} {r['peak_positivity']:>5.1f}% "
                  f"{pinn_str:>12} {chp_str:>12} {lead_str:>9} "
                  f"{r['best_Rt']:>8.3f} {r['incubation_days']:>5.1f}d {r['infectious_days']:>6.1f}d "
                  f"{r['final_loss']:>10.6f}")

        # Summary statistics
        valid = results_df.dropna(subset=["lead_days"])
        if len(valid) > 0:
            print(f"\n--- Summary across {len(valid)} seasons with both onsets detected ---")
            print(f"  Mean lead time:   {valid['lead_days'].mean():.1f} days")
            print(f"  Median lead time: {valid['lead_days'].median():.1f} days")
            print(f"  Range:            {valid['lead_days'].min():.0f} to {valid['lead_days'].max():.0f} days")
            pos_lead = valid[valid["lead_days"] > 0]
            print(f"  Seasons where PINN leads: {len(pos_lead)}/{len(valid)}")
        else:
            print("\n  No seasons had both PINN and CHP onset detected.")

        print(f"\n{'='*70}")
        print("NEXT STEPS:")
        print("  1. Add MC Dropout uncertainty bands on R(t) onset date")
        print("  2. Add per-season R(t) overlay plot (Figure 2)")
        print("  3. Sensitivity analysis: vary n_epochs, architecture, loss weights")
        print("  4. Compare against EpiEstim R(t) as second benchmark")
        print("  5. Prospective deployment for 2026/27 season at HKU")
        print(f"{'='*70}")
