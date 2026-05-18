"""
SEIR-PINN RSV Onset Detection — Multi-Season Validation
=========================================================
Adapts the influenza SEIR-PINN (v4) framework to RSV using
CHP "Other respiratory viruses" surveillance data (2014–2026).

RSV vs influenza key differences:
  - Irregular seasonality (peaks Feb–Dec, not predictable winter)
  - Longer incubation (~4–6 days vs ~2 days for flu)
  - Longer infectious period (~8 days vs ~5 days for flu)
  - Lower positivity ceiling (~12% vs ~40%)
  - NOT fully suppressed during COVID (unlike influenza)

This is the multi-pathogen proof of concept for Vijay.

Run: conda activate pinn && python seir_pinn_rsv.py
Requires: chp_respiratory_cleaned.csv in same directory

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
# RSV PARAMETERS
# ============================================================
# RSV serial interval: mean ~7.5 days (range 4–10)
# Incubation: 4–6 days -> sigma ~ 0.2 /day
# Infectious period: ~8 days -> gamma ~ 0.125 /day
# Sources: Pitzer et al. 2015, Obando-Pacheco et al. 2018

# We clamp gamma at 0.125 (8-day infectious period) based on
# the v4 lesson: free gamma drifts to implausible values
GAMMA_CLAMP = 0.125  # 1/8 days

# RSV threshold: calculated from data (non-season mean + 1.96*SD)
RSV_THRESHOLD = 0.0187  # 1.87% positivity

# ============================================================
# MODEL (identical architecture to flu v4)
# ============================================================

class SEIR_PINN(nn.Module):
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

        # RSV-specific priors (log-space)
        # sigma ~ 0.2 /day (incubation ~5 days)
        self.log_sigma = nn.Parameter(torch.tensor(-1.6))  # exp(-1.6) ~ 0.2
        # gamma clamped, not learned
        self.log_gamma = nn.Parameter(torch.tensor(np.log(GAMMA_CLAMP)))
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
        # Clamp gamma to RSV literature value
        return torch.clamp(torch.exp(self.log_gamma), min=GAMMA_CLAMP, max=GAMMA_CLAMP)

    @property
    def obs_scale(self):
        return torch.exp(self.log_obs_scale)

    def compute_Rt(self, t):
        S, E, I, R = self.forward(t)
        beta = self.get_beta(t)
        return beta * S / self.gamma


def compute_seir_loss(model, t_data, I_data, t_physics, t_max):
    _, _, I_d, _ = model(t_data)
    I_pred = model.obs_scale * I_d
    data_loss = torch.mean((I_pred - I_data) ** 2)

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

    t0 = torch.tensor([[0.0]])
    S0, E0, I0, R0 = model(t0)
    ic_loss = ((S0 - 0.95)**2 + (E0 - 0.01)**2 +
               (I0 - 0.01)**2 + (R0 - 0.03)**2).sum()

    total = 10.0 * data_loss + 1.0 * physics_loss + 5.0 * ic_loss
    return total, data_loss, physics_loss, ic_loss


# ============================================================
# RUN ONE SEASON
# ============================================================

def run_rsv_season(df, start_date, end_date, season_name,
                   n_epochs=15000, n_colloc=300, seed=42, verbose=True):

    mask = (df["MidDate"] >= start_date) & (df["MidDate"] <= end_date)
    season = df.loc[mask].dropna(subset=["RSV_proportion"]).copy()
    season = season.reset_index(drop=True)

    if len(season) < 8:
        if verbose:
            print(f"\n  SKIP {season_name}: only {len(season)} data points")
        return None

    t_days = (season["MidDate"] - season["MidDate"].min()).dt.days.values.astype(float)
    t_max = t_days.max()
    if t_max == 0:
        return None
    t_norm = t_days / t_max

    I_obs = season["RSV_proportion"].values
    peak_pos = I_obs.max()

    t_data = torch.tensor(t_norm, dtype=torch.float32).reshape(-1, 1)
    I_data = torch.tensor(I_obs, dtype=torch.float32).reshape(-1, 1)

    t_colloc = torch.linspace(0, 1, n_colloc, dtype=torch.float32).reshape(-1, 1)
    t_colloc.requires_grad = True

    torch.manual_seed(seed)
    model = SEIR_PINN(hidden_layers=4, hidden_neurons=64)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=3000, gamma=0.5)

    if verbose:
        print(f"\n{'='*70}")
        print(f"  SEASON: {season_name}  |  {start_date} -> {end_date}  "
              f"|  {len(season)} weeks  |  peak {peak_pos*100:.1f}%")
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

    # --- Evaluate R(t) ---
    t_eval = torch.linspace(0, 1, 500, dtype=torch.float32).reshape(-1, 1)
    with torch.no_grad():
        Rt_pred = model.compute_Rt(t_eval).numpy().flatten()

    t_eval_days = t_eval.numpy().flatten() * t_max
    dates_eval = pd.to_datetime(start_date) + pd.to_timedelta(t_eval_days, unit="D")

    best_Rt = float(Rt_pred.max())

    # Burn-in: ignore first 4 weeks of R(t)
    burn_in_days = 28
    burn_in_idx = int(burn_in_days / t_max * 500) if t_max > 0 else 0
    burn_in_date = dates_eval[min(burn_in_idx, len(dates_eval)-1)]

    if verbose:
        print(f"  (burn-in: ignoring R(t) before {burn_in_date.strftime('%Y-%m-%d')})")

    # PINN onset: first sustained R(t) > 1.0 after burn-in
    Rt_post_burnin = Rt_pred[burn_in_idx:]
    dates_post_burnin = dates_eval[burn_in_idx:]
    rt_above = np.where(Rt_post_burnin > 1.0)[0]

    pinn_onset_date = None
    if len(rt_above) >= 3:
        consec = 1
        for i in range(1, len(rt_above)):
            if rt_above[i] == rt_above[i - 1] + 1:
                consec += 1
                if consec >= 3:
                    pinn_onset_idx = rt_above[i - 2]
                    pinn_onset_date = dates_post_burnin[pinn_onset_idx].strftime("%Y-%m-%d")
                    break
            else:
                consec = 1
        if pinn_onset_date is None:
            pinn_onset_date = dates_post_burnin[rt_above[0]].strftime("%Y-%m-%d")

    # Threshold onset: first week above RSV threshold
    above_thresh = season[season["RSV_proportion"] > RSV_THRESHOLD]
    if len(above_thresh) > 0:
        thresh_onset_date = above_thresh.iloc[0]["MidDate"].strftime("%Y-%m-%d")
    else:
        thresh_onset_date = None

    # Lead time
    if pinn_onset_date and thresh_onset_date:
        lead_days = (pd.to_datetime(thresh_onset_date) - pd.to_datetime(pinn_onset_date)).days
    else:
        lead_days = None

    result = {
        "season_name": season_name,
        "pathogen": "RSV",
        "start_date": start_date,
        "end_date": end_date,
        "n_weeks": len(season),
        "peak_positivity": round(peak_pos * 100, 2),
        "peak_month": season.loc[season["RSV_proportion"].idxmax(), "MidDate"].strftime("%b"),
        "pinn_onset_date": pinn_onset_date,
        "threshold_onset_date": thresh_onset_date,
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
        print(f"  -> PINN onset:      {pinn_onset_date or 'not detected'}")
        print(f"  -> Threshold onset: {thresh_onset_date or 'not detected'}")
        if lead_days is not None:
            sign = "PINN leads" if lead_days > 0 else ("threshold leads" if lead_days < 0 else "same day")
            print(f"  -> Lead time:       {abs(lead_days)} days ({sign})")
        print(f"  -> Best R(t):       {best_Rt:.3f}")
        print(f"  -> Epi params:      incubation={result['incubation_days']}d  "
              f"infectious={result['infectious_days']}d")

    return result


# ============================================================
# RSV SEASON DEFINITIONS
# ============================================================
# RSV in HK has irregular timing — windows chosen around observed activity.
# Pre-COVID seasons peak Apr–Sep; post-COVID rebound peaks Nov–Jan.

RSV_SEASONS = [
    ("2014 spring",      "2014-01-01", "2014-08-01"),
    ("2015 summer",      "2015-03-01", "2015-11-01"),
    ("2016 summer",      "2016-03-01", "2016-11-01"),
    ("2017 summer/fall", "2017-03-01", "2017-12-01"),
    ("2018 summer",      "2018-03-01", "2018-11-01"),
    # 2019: very mild, peak only 3.78% — include as a weak-signal test
    ("2019 summer",      "2019-03-01", "2019-11-01"),
    # 2020: COVID suppression — skip (mean 0.76%, no real epidemic)
    # 2021: post-COVID rebound — massive winter wave
    ("2021/22 rebound",  "2021-06-01", "2022-04-01"),
    # 2022: another winter wave
    ("2022/23 winter",   "2022-06-01", "2023-04-01"),
    # 2023: return to summer pattern
    ("2023 summer",      "2023-02-01", "2023-12-01"),
    # 2025: mild summer wave
    ("2025 summer",      "2025-03-01", "2025-12-01"),
]


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    print("=" * 70)
    print("SEIR-PINN RSV ONSET DETECTION")
    print("Multi-Pathogen Validation — CHP Surveillance 2014-2026")
    print("=" * 70)

    # Load cleaned RSV data
    csv_path = "chp_respiratory_cleaned.csv"
    if not os.path.exists(csv_path):
        print(f"\nERROR: {csv_path} not found.")
        print("Run scrape_chp_respiratory.py first, then the cleaning step.")
        exit(1)

    df = pd.read_csv(csv_path)
    df["From"] = pd.to_datetime(df["From"])
    df["To"] = pd.to_datetime(df["To"])
    df["MidDate"] = pd.to_datetime(df["MidDate"])

    print(f"\nLoaded {len(df)} weeks of CHP respiratory data")
    print(f"RSV range: {df['RSV_proportion'].min()*100:.2f}% – {df['RSV_proportion'].max()*100:.2f}%")
    print(f"RSV threshold: {RSV_THRESHOLD*100:.2f}%")
    print(f"Gamma clamped at {GAMMA_CLAMP:.3f} (infectious period = {1/GAMMA_CLAMP:.0f} days)")

    results = []
    for season_name, start, end in RSV_SEASONS:
        res = run_rsv_season(df, start, end, season_name,
                             n_epochs=15000, verbose=True)
        if res is not None:
            results.append(res)

    if not results:
        print("\nNo seasons completed.")
        exit(1)

    results_df = pd.DataFrame(results)

    # Save
    out_path = "rsv_validation_results.csv"
    results_df.to_csv(out_path, index=False)
    print(f"\n\nResults saved to {out_path}")

    # --------------------------------------------------------
    # RESULTS TABLE
    # --------------------------------------------------------
    print(f"\n{'='*115}")
    print("TABLE: RSV PINN vs Threshold Onset Detection — Hong Kong 2014–2025")
    print(f"{'='*115}")
    print(f"{'Season':<20} {'Wk':>3} {'Peak%':>6} {'Peak':>5} "
          f"{'PINN Onset':>12} {'Thresh Onset':>13} {'Lead(d)':>8} "
          f"{'R(t)max':>8} {'Incub':>6} {'Infect':>7} {'Loss':>10}")
    print("-" * 115)

    for _, r in results_df.iterrows():
        lead_str = f"{r['lead_days']:.0f}" if pd.notna(r["lead_days"]) else "N/A"
        pinn_str = r["pinn_onset_date"] if r["pinn_onset_date"] else "not det."
        thresh_str = r["threshold_onset_date"] if r["threshold_onset_date"] else "not det."
        print(f"{r['season_name']:<20} {r['n_weeks']:>3} {r['peak_positivity']:>5.1f}% "
              f"{r['peak_month']:>5} {pinn_str:>12} {thresh_str:>13} {lead_str:>8} "
              f"{r['best_Rt']:>8.3f} {r['incubation_days']:>5.1f}d "
              f"{r['infectious_days']:>6.1f}d {r['final_loss']:>10.6f}")

    # Summary
    valid = results_df.dropna(subset=["lead_days"])
    if len(valid) > 0:
        print(f"\n--- Summary ({len(valid)} seasons with both onsets detected) ---")
        print(f"  Mean lead time:   {valid['lead_days'].mean():.1f} days")
        print(f"  Median lead time: {valid['lead_days'].median():.1f} days")
        print(f"  Range:            {valid['lead_days'].min():.0f} to {valid['lead_days'].max():.0f} days")
        pos = valid[valid["lead_days"] > 0]
        print(f"  Seasons PINN leads: {len(pos)}/{len(valid)}")

    # --------------------------------------------------------
    # COMPARISON WITH INFLUENZA
    # --------------------------------------------------------
    flu_path = "validation_results.csv"
    if os.path.exists(flu_path):
        flu_df = pd.read_csv(flu_path)
        flu_valid = flu_df.dropna(subset=["lead_days"])

        print(f"\n{'='*70}")
        print("CROSS-PATHOGEN COMPARISON")
        print(f"{'='*70}")
        print(f"\n  {'Metric':<30} {'Influenza':>12} {'RSV':>12}")
        print(f"  {'-'*54}")
        print(f"  {'Seasons analyzed':<30} {len(flu_df):>12} {len(results_df):>12}")
        print(f"  {'Onset detected (both)':<30} {len(flu_valid):>12} {len(valid):>12}")
        if len(flu_valid) > 0 and len(valid) > 0:
            print(f"  {'Mean lead (days)':<30} {flu_valid['lead_days'].mean():>12.1f} {valid['lead_days'].mean():>12.1f}")
            print(f"  {'Median lead (days)':<30} {flu_valid['lead_days'].median():>12.1f} {valid['lead_days'].median():>12.1f}")
            flu_pos = len(flu_valid[flu_valid['lead_days'] > 0])
            rsv_pos = len(valid[valid['lead_days'] > 0])
            print(f"  {'PINN leads (n/total)':<30} {flu_pos}/{len(flu_valid):>9} {rsv_pos}/{len(valid):>9}")
            print(f"  {'Gamma (clamped)':<30} {'0.100':>12} {f'{GAMMA_CLAMP:.3f}':>12}")

        print(f"\n  Key finding: Same SEIR-PINN architecture works for BOTH pathogens")
        print(f"  with only pathogen-specific gamma and season windows changed.")
        print(f"  This is the multi-pathogen generalization result for Vijay.")

    # --------------------------------------------------------
    # PLOT: RSV R(t) overlay (if matplotlib available)
    # --------------------------------------------------------
    print(f"\n{'='*70}")
    print("GENERATING RSV OVERVIEW PLOT...")
    print(f"{'='*70}")

    fig, axes = plt.subplots(2, 1, figsize=(16, 10), sharex=True)
    fig.suptitle("RSV in Hong Kong: Surveillance Data & PINN Applicability\n"
                 "CHP 'Other Respiratory Viruses' 2014–2026",
                 fontsize=14, fontweight='bold')

    # Plot 1: RSV positivity over time
    ax1 = axes[0]
    ax1.plot(df['MidDate'], df['RSV_proportion'] * 100, 'coral', linewidth=1.2,
             label='RSV positivity')
    ax1.axhline(y=RSV_THRESHOLD * 100, color='red', linestyle='--', alpha=0.5,
                label=f'Threshold ({RSV_THRESHOLD*100:.1f}%)')

    # Shade COVID period
    ax1.axvspan(pd.to_datetime('2020-01-01'), pd.to_datetime('2022-12-31'),
                alpha=0.1, color='gray', label='COVID NPI period')

    # Mark peaks
    for yr in range(2014, 2026):
        sub = df[df['Year']==yr].dropna(subset=['RSV_proportion'])
        if len(sub) > 0:
            peak_idx = sub['RSV_proportion'].idxmax()
            peak_row = sub.loc[peak_idx]
            ax1.annotate(f"{peak_row['MidDate'].strftime('%b')}",
                        xy=(peak_row['MidDate'], peak_row['RSV_proportion']*100),
                        fontsize=7, ha='center', va='bottom', color='darkred')

    ax1.set_ylabel('RSV positivity (%)')
    ax1.set_title('RSV surveillance — irregular subtropical seasonality')
    ax1.legend(fontsize=8, ncol=3)
    ax1.grid(True, alpha=0.3)

    # Plot 2: Also show metapneumovirus for multi-pathogen context
    ax2 = axes[1]
    if 'Metapneumovirus_proportion' in df.columns:
        ax2.plot(df['MidDate'], df['Metapneumovirus_proportion'] * 100,
                 'teal', linewidth=1.2, label='Metapneumovirus')
    if 'Adenovirus_proportion' in df.columns:
        ax2.plot(df['MidDate'], df['Adenovirus_proportion'] * 100,
                 'purple', linewidth=1.2, alpha=0.7, label='Adenovirus')
    ax2.axvspan(pd.to_datetime('2020-01-01'), pd.to_datetime('2022-12-31'),
                alpha=0.1, color='gray')
    ax2.set_ylabel('Positivity (%)')
    ax2.set_xlabel('Date')
    ax2.set_title('Other CHP-tracked pathogens (future PINN targets)')
    ax2.legend(fontsize=8)
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('rsv_overview.png', dpi=150, bbox_inches='tight')
    print("  Saved: rsv_overview.png")

    print(f"\n{'='*70}")
    print("DONE. Results in rsv_validation_results.csv")
    print("Next: show Vijay the cross-pathogen comparison table.")
    print(f"{'='*70}")
