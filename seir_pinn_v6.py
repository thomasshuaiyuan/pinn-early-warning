"""
SEIR-PINN v6: Fixed Onset Definition + Subtype Stratification
===============================================================
Two critical fixes from v4:

1. ONSET FIX: R(t) must cross 1.0 FROM BELOW (must be < 1 before > 1).
   This prevents the artifact where onset = burn-in boundary because
   R(t) was always > 1 from the start.

2. SUBTYPE STRATIFICATION: For multi-wave seasons (2016/17, 2017/18),
   run separate PINNs on H1, H3, B positivity instead of combined.
   Season onset = earliest subtype where R(t) crosses 1.0 from below.

Run: conda activate pinn && python seir_pinn_v6.py
Requires: flux_data.csv in same directory

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
# CONSTANTS
# ============================================================
CHP_THRESHOLD = 0.0494
GAMMA_CLAMP_FLU = 0.1  # 10-day infectious period

# ============================================================
# MODEL (same as v4)
# ============================================================

class SEIR_PINN(nn.Module):
    def __init__(self, hidden_layers=4, hidden_neurons=64, gamma_clamp=0.1):
        super().__init__()
        self.gamma_clamp = gamma_clamp
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
        self.log_sigma = nn.Parameter(torch.tensor(-0.7))
        self.log_gamma = nn.Parameter(torch.tensor(np.log(gamma_clamp)))
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
        return torch.clamp(torch.exp(self.log_gamma), min=self.gamma_clamp, max=self.gamma_clamp)

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
# FIXED ONSET DETECTION: R(t) must cross 1.0 FROM BELOW
# ============================================================

def find_onset_crossing_from_below(Rt_array, dates_array, burn_in_idx):
    """Find first time R(t) crosses 1.0 from below after burn-in.
    
    Requires:
    1. R(t) < 1.0 at some point after burn-in (establishes baseline)
    2. R(t) > 1.0 sustained for >= 3 consecutive points after that
    
    Returns onset date string or None.
    """
    Rt = Rt_array[burn_in_idx:]
    dates = dates_array[burn_in_idx:]
    
    if len(Rt) < 5:
        return None, None
    
    # Find first point where R(t) < 1.0 (establishes that we start below)
    below_one = np.where(Rt < 1.0)[0]
    if len(below_one) == 0:
        # R(t) never goes below 1 — can't detect a crossing
        return None, "R(t) always >= 1 (no crossing)"
    
    # Starting from after the first below-1 point, find sustained above-1
    search_start = below_one[0]
    Rt_search = Rt[search_start:]
    dates_search = dates[search_start:]
    
    above_one = np.where(Rt_search > 1.0)[0]
    if len(above_one) < 3:
        return None, "R(t) never sustained above 1"
    
    # Find 3 consecutive above-1 points
    consec = 1
    for i in range(1, len(above_one)):
        if above_one[i] == above_one[i-1] + 1:
            consec += 1
            if consec >= 3:
                onset_idx = above_one[i - 2]
                return dates_search[onset_idx].strftime("%Y-%m-%d"), None
        else:
            consec = 1
    
    return None, "No 3 consecutive R(t) > 1 points"


# ============================================================
# RUN ONE SEASON
# ============================================================

def run_season(df, start_date, end_date, season_name, obs_col="AandB_proportion",
               threshold=CHP_THRESHOLD, gamma_clamp=0.1,
               n_epochs=15000, n_colloc=300, seed=42, verbose=True):
    
    mask = (df["MidDate"] >= start_date) & (df["MidDate"] <= end_date)
    season = df.loc[mask].dropna(subset=[obs_col]).copy()
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
    I_obs = season[obs_col].values
    peak_pos = I_obs.max()
    
    t_data = torch.tensor(t_norm, dtype=torch.float32).reshape(-1, 1)
    I_data = torch.tensor(I_obs, dtype=torch.float32).reshape(-1, 1)
    t_colloc = torch.linspace(0, 1, n_colloc, dtype=torch.float32).reshape(-1, 1)
    t_colloc.requires_grad = True
    
    torch.manual_seed(seed)
    model = SEIR_PINN(hidden_layers=4, hidden_neurons=64, gamma_clamp=gamma_clamp)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=3000, gamma=0.5)
    
    if verbose:
        print(f"\n{'='*70}")
        print(f"  {season_name}  |  {start_date} -> {end_date}  "
              f"|  {len(season)} wks  |  peak {peak_pos*100:.1f}%  |  signal: {obs_col}")
        print(f"{'='*70}")
    
    for epoch in range(n_epochs):
        optimizer.zero_grad()
        total, d_loss, p_loss, ic_loss = compute_seir_loss(model, t_data, I_data, t_colloc, t_max)
        total.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
        scheduler.step()
        if verbose and (epoch + 1) % 5000 == 0:
            print(f"    epoch {epoch+1:>6}  loss={total.item():.6f}  "
                  f"data={d_loss.item():.6f}  phys={p_loss.item():.6f}  "
                  f"sigma={model.sigma.item():.4f}  gamma={model.gamma.item():.4f}")
    
    final_loss = total.item()
    
    # Evaluate R(t)
    t_eval = torch.linspace(0, 1, 500, dtype=torch.float32).reshape(-1, 1)
    with torch.no_grad():
        Rt_pred = model.compute_Rt(t_eval).numpy().flatten()
    
    t_eval_days = t_eval.numpy().flatten() * t_max
    dates_eval = pd.to_datetime(start_date) + pd.to_timedelta(t_eval_days, unit="D")
    
    best_Rt = float(Rt_pred.max())
    
    # Burn-in: 4 weeks
    burn_in_idx = int(28 / t_max * 500) if t_max > 28 else 0
    
    # NEW: Use crossing-from-below onset detection
    pinn_onset_date, fail_reason = find_onset_crossing_from_below(
        Rt_pred, dates_eval, burn_in_idx
    )
    
    if verbose and fail_reason:
        print(f"  (onset detection: {fail_reason})")
    
    # Threshold onset
    above_thresh = season[season[obs_col] > threshold]
    thresh_onset = above_thresh.iloc[0]["MidDate"].strftime("%Y-%m-%d") if len(above_thresh) > 0 else None
    
    # Lead time
    if pinn_onset_date and thresh_onset:
        lead_days = (pd.to_datetime(thresh_onset) - pd.to_datetime(pinn_onset_date)).days
    else:
        lead_days = None
    
    # Check: did R(t) start below 1?
    rt_at_burnin = Rt_pred[burn_in_idx] if burn_in_idx < len(Rt_pred) else None
    
    result = {
        "season_name": season_name,
        "obs_col": obs_col,
        "n_weeks": len(season),
        "peak_positivity": round(peak_pos * 100, 2),
        "pinn_onset_date": pinn_onset_date,
        "chp_onset_date": thresh_onset,
        "lead_days": lead_days,
        "best_Rt": round(best_Rt, 3),
        "Rt_at_burnin": round(float(rt_at_burnin), 3) if rt_at_burnin is not None else None,
        "sigma": round(model.sigma.item(), 4),
        "gamma": round(model.gamma.item(), 4),
        "incubation_days": round(1.0 / model.sigma.item(), 1),
        "infectious_days": round(1.0 / model.gamma.item(), 1),
        "obs_scale": round(model.obs_scale.item(), 4),
        "final_loss": round(final_loss, 6),
    }
    
    if verbose:
        print(f"  -> R(t) at burn-in: {result['Rt_at_burnin']}")
        print(f"  -> PINN onset:      {pinn_onset_date or 'not detected'}")
        print(f"  -> CHP onset:       {thresh_onset or 'not detected'}")
        if lead_days is not None:
            sign = "PINN leads" if lead_days > 0 else ("CHP leads" if lead_days < 0 else "same day")
            print(f"  -> Lead time:       {abs(lead_days)} days ({sign})")
        print(f"  -> Best R(t):       {best_Rt:.3f}")
    
    return result


# ============================================================
# SEASON DEFINITIONS
# ============================================================

# Standard seasons (single-wave analysis)
STANDARD_SEASONS = [
    ("2014/15 winter", "2014-10-01", "2015-06-01"),
    ("2015/16 winter", "2015-10-01", "2016-06-01"),
    ("2018/19 winter", "2018-09-15", "2019-06-01"),
    ("2023 summer",    "2023-01-15", "2023-10-01"),
    ("2023/24 winter", "2023-07-15", "2024-04-01"),
    ("2024/25 winter", "2024-08-01", "2025-04-01"),
]

# Multi-wave seasons — will be analyzed by subtype
MULTIWAVE_SEASONS = [
    ("2016/17", "2016-09-15", "2017-06-01"),
    ("2017/18", "2017-04-01", "2018-04-01"),
]


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print("=" * 70)
    print("SEIR-PINN v6: Fixed Onset + Subtype Stratification")
    print("=" * 70)
    
    df = pd.read_csv("flux_data.csv")
    df["From"] = pd.to_datetime(df["From"], format="%d/%m/%Y")
    df["To"] = pd.to_datetime(df["To"], format="%d/%m/%Y")
    df["MidDate"] = df["From"] + (df["To"] - df["From"]) / 2
    
    print(f"\nLoaded {len(df)} weeks of CHP Flu Express data")
    print(f"FIX APPLIED: Onset requires R(t) crossing 1.0 FROM BELOW")
    print(f"  (prevents burn-in boundary artifact)")
    
    # ========================================================
    # PART 1: Standard seasons with fixed onset detection
    # ========================================================
    print(f"\n\n{'#'*70}")
    print("PART 1: STANDARD SEASONS (fixed onset definition)")
    print(f"{'#'*70}")
    
    results = []
    for name, start, end in STANDARD_SEASONS:
        res = run_season(df, start, end, name, obs_col="AandB_proportion",
                        threshold=CHP_THRESHOLD, gamma_clamp=GAMMA_CLAMP_FLU,
                        n_epochs=15000, verbose=True)
        if res is not None:
            results.append(res)
    
    # ========================================================
    # PART 2: Multi-wave seasons — subtype stratified
    # ========================================================
    print(f"\n\n{'#'*70}")
    print("PART 2: MULTI-WAVE SEASONS (subtype-stratified PINNs)")
    print(f"{'#'*70}")
    
    subtype_results = []
    
    for mw_name, mw_start, mw_end in MULTIWAVE_SEASONS:
        print(f"\n{'='*70}")
        print(f"  MULTI-WAVE SEASON: {mw_name}")
        print(f"  Running separate PINNs on H1, H3, B subtypes")
        print(f"{'='*70}")
        
        earliest_onset = None
        earliest_subtype = None
        subtype_onsets = {}
        
        for subtype_col, subtype_name in [("H1_proportion", "H1N1"),
                                           ("H3_proportion", "H3N2"),
                                           ("B_proportion", "B")]:
            
            # Check if this subtype has enough signal
            mask = (df["MidDate"] >= mw_start) & (df["MidDate"] <= mw_end)
            season_data = df.loc[mask]
            sub_peak = season_data[subtype_col].max()
            
            if sub_peak < 0.02:  # less than 2% peak — skip
                print(f"\n  {subtype_name}: peak {sub_peak*100:.1f}% — too low, skipping")
                continue
            
            # Subtype-specific threshold (mean + 1.96*SD of below-median weeks)
            all_vals = df[subtype_col].dropna()
            non_season = all_vals[all_vals < all_vals.median()]
            sub_threshold = non_season.mean() + 1.96 * non_season.std()
            
            season_label = f"{mw_name} {subtype_name}"
            res = run_season(df, mw_start, mw_end, season_label,
                           obs_col=subtype_col, threshold=sub_threshold,
                           gamma_clamp=GAMMA_CLAMP_FLU,
                           n_epochs=15000, verbose=True)
            
            if res is not None:
                subtype_results.append(res)
                subtype_onsets[subtype_name] = res["pinn_onset_date"]
                
                if res["pinn_onset_date"]:
                    if earliest_onset is None or res["pinn_onset_date"] < earliest_onset:
                        earliest_onset = res["pinn_onset_date"]
                        earliest_subtype = subtype_name
        
        print(f"\n  --- {mw_name} Subtype Summary ---")
        for sub, onset in subtype_onsets.items():
            print(f"    {sub}: onset = {onset or 'not detected'}")
        if earliest_onset:
            print(f"    EARLIEST: {earliest_subtype} on {earliest_onset}")
        
        # Create a combined result for the multi-wave season
        # CHP onset for the combined signal
        mask = (df["MidDate"] >= mw_start) & (df["MidDate"] <= mw_end)
        season_data = df.loc[mask]
        above = season_data[season_data["AandB_proportion"] > CHP_THRESHOLD]
        chp_onset = above.iloc[0]["MidDate"].strftime("%Y-%m-%d") if len(above) > 0 else None
        
        combined_lead = None
        if earliest_onset and chp_onset:
            combined_lead = (pd.to_datetime(chp_onset) - pd.to_datetime(earliest_onset)).days
        
        results.append({
            "season_name": f"{mw_name} (subtype)",
            "obs_col": "subtype-stratified",
            "n_weeks": len(season_data),
            "peak_positivity": round(season_data["AandB_proportion"].max() * 100, 2),
            "pinn_onset_date": earliest_onset,
            "chp_onset_date": chp_onset,
            "lead_days": combined_lead,
            "best_Rt": None,
            "Rt_at_burnin": None,
            "sigma": None,
            "gamma": GAMMA_CLAMP_FLU,
            "incubation_days": None,
            "infectious_days": 10.0,
            "obs_scale": None,
            "final_loss": None,
            "earliest_subtype": earliest_subtype,
        })
    
    # ========================================================
    # RESULTS TABLE
    # ========================================================
    results_df = pd.DataFrame(results)
    results_df.to_csv("validation_results_v6.csv", index=False)
    
    print(f"\n\n{'='*115}")
    print("TABLE 1 (v6): PINN Onset Detection — Fixed Definition + Subtype Stratification")
    print(f"{'='*115}")
    print(f"{'Season':<22} {'Wk':>3} {'Peak%':>6} {'PINN Onset':>12} "
          f"{'CHP Onset':>12} {'Lead(d)':>8} {'R(t)':>7} {'R(t)@burn':>10} {'Note':>12}")
    print("-" * 115)
    
    for _, r in results_df.iterrows():
        lead_str = f"{r['lead_days']:.0f}" if pd.notna(r.get("lead_days")) and r["lead_days"] is not None else "N/A"
        pinn_str = r["pinn_onset_date"] if r["pinn_onset_date"] else "not det."
        chp_str = r["chp_onset_date"] if r["chp_onset_date"] else "not det."
        rt_str = f"{r['best_Rt']:.3f}" if r.get("best_Rt") is not None else "—"
        burn_str = f"{r['Rt_at_burnin']:.3f}" if r.get("Rt_at_burnin") is not None else "—"
        note = r.get("earliest_subtype", "") or ""
        
        print(f"{r['season_name']:<22} {r['n_weeks']:>3} {r['peak_positivity']:>5.1f}% "
              f"{pinn_str:>12} {chp_str:>12} {lead_str:>8} "
              f"{rt_str:>7} {burn_str:>10} {note:>12}")
    
    # Summary
    valid = results_df[results_df["lead_days"].notna()].copy()
    valid["lead_days"] = valid["lead_days"].astype(float)
    if len(valid) > 0:
        print(f"\n--- Summary ({len(valid)} seasons with both onsets) ---")
        print(f"  Mean lead:   {valid['lead_days'].mean():.1f} days")
        print(f"  Median lead: {valid['lead_days'].median():.1f} days")
        print(f"  Range:       {valid['lead_days'].min():.0f} to {valid['lead_days'].max():.0f} days")
        pos = valid[valid["lead_days"] > 0]
        print(f"  PINN leads:  {len(pos)}/{len(valid)}")
    
    # ========================================================
    # SUBTYPE DETAIL TABLE
    # ========================================================
    if subtype_results:
        sub_df = pd.DataFrame(subtype_results)
        print(f"\n\n{'='*100}")
        print("TABLE: Subtype-Stratified PINN Results for Multi-Wave Seasons")
        print(f"{'='*100}")
        print(f"{'Season':<22} {'Signal':>15} {'Peak%':>6} {'PINN':>12} "
              f"{'Thresh':>12} {'Lead(d)':>8} {'R(t)':>7}")
        print("-" * 100)
        
        for _, r in sub_df.iterrows():
            lead_str = f"{r['lead_days']:.0f}" if pd.notna(r.get("lead_days")) and r["lead_days"] is not None else "N/A"
            pinn_str = r["pinn_onset_date"] if r["pinn_onset_date"] else "not det."
            chp_str = r["chp_onset_date"] if r["chp_onset_date"] else "not det."
            rt_str = f"{r['best_Rt']:.3f}" if r.get("best_Rt") is not None else "—"
            print(f"{r['season_name']:<22} {r['obs_col']:>15} {r['peak_positivity']:>5.1f}% "
                  f"{pinn_str:>12} {chp_str:>12} {lead_str:>8} {rt_str:>7}")
    
    # ========================================================
    # COMPARISON: v4 vs v6
    # ========================================================
    v4_path = "validation_results.csv"
    if os.path.exists(v4_path):
        v4 = pd.read_csv(v4_path)
        print(f"\n\n{'='*70}")
        print("v4 vs v6 COMPARISON (same seasons)")
        print(f"{'='*70}")
        print(f"{'Season':<22} {'v4 onset':>12} {'v4 lead':>8} {'v6 onset':>12} {'v6 lead':>8} {'Change':>8}")
        print("-" * 70)
        
        for _, v6r in results_df.iterrows():
            name = v6r["season_name"].replace(" (subtype)", "")
            v4_match = v4[v4["season_name"].str.contains(name.split()[0])]
            if len(v4_match) > 0:
                v4r = v4_match.iloc[0]
                v4_onset = v4r["pinn_onset_date"] if pd.notna(v4r["pinn_onset_date"]) else "N/D"
                v4_lead = f"{v4r['lead_days']:.0f}" if pd.notna(v4r["lead_days"]) else "N/A"
                v6_onset = v6r["pinn_onset_date"] or "N/D"
                v6_lead = f"{v6r['lead_days']:.0f}" if v6r["lead_days"] is not None and pd.notna(v6r["lead_days"]) else "N/A"
                
                change = ""
                if v4_lead != "N/A" and v6_lead != "N/A":
                    diff = float(v6_lead) - float(v4_lead)
                    change = f"{diff:+.0f}d"
                
                print(f"{v6r['season_name']:<22} {str(v4_onset):>12} {v4_lead:>8} "
                      f"{v6_onset:>12} {v6_lead:>8} {change:>8}")
    
    print(f"\n{'='*70}")
    print("WHAT CHANGED IN v6:")
    print("  1. Onset requires R(t) to cross 1.0 FROM BELOW")
    print("     (eliminates burn-in boundary artifact)")
    print("  2. Multi-wave seasons analyzed by H1/H3/B separately")
    print("     (resolves 2016/17 and 2017/18 failures)")
    print("  3. Reports R(t) at burn-in to verify starting below 1")
    print(f"{'='*70}")
    print(f"\nResults saved to validation_results_v6.csv")
