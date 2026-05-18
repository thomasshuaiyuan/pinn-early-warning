"""
SEIR-PINN on Hospital Admissions Data
=======================================
Tests whether the PINN's failure is signal-dependent or structural.

Logic:
- EpiEstim on admissions beats EpiEstim on positivity (established)
- PINN on positivity fails (R(t) stuck above 1.0)
- Question: does PINN on admissions also fail?
  - If yes: gamma confounding is the bottleneck, not the signal
  - If no: signal quality was the bottleneck, PINN works with better input

We test on the 4 seasons where positivity-PINN failed:
  2014/15 (R(t)@burnin = 1.343)
  2018/19 (R(t)@burnin = 1.494)
  2023 summer (R(t)@burnin = 1.796)
  2023/24 (R(t)@burnin = 1.160)

Plus 2024/25 where PINN worked (R(t)@burnin = 0.895) as positive control.

Run: conda activate pinn && python seir_pinn_admissions.py
Requires: flux_data.csv

Thomas Yuan — HKU PhD, Pathogen Evolution Lab
"""

import torch
import torch.nn as nn
import numpy as np
import pandas as pd
import warnings
import os

warnings.filterwarnings("ignore")

CHP_THRESHOLD = 0.0494
GAMMA_CLAMP = 0.1

# ============================================================
# MODEL (identical to v6)
# ============================================================

class SEIR_PINN(nn.Module):
    def __init__(self, hidden_layers=4, hidden_neurons=64):
        super().__init__()
        self.gamma_clamp = GAMMA_CLAMP
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


def find_onset_crossing_from_below(Rt_array, dates_array, burn_in_idx):
    Rt = Rt_array[burn_in_idx:]
    dates = dates_array[burn_in_idx:]
    if len(Rt) < 5:
        return None, None, None
    below_one = np.where(Rt < 1.0)[0]
    if len(below_one) == 0:
        return None, "R(t) always >= 1", float(Rt_array[burn_in_idx])
    search_start = below_one[0]
    Rt_search = Rt[search_start:]
    dates_search = dates[search_start:]
    above_one = np.where(Rt_search > 1.0)[0]
    if len(above_one) < 3:
        return None, "R(t) never sustained above 1", float(Rt_array[burn_in_idx])
    consec = 1
    for i in range(1, len(above_one)):
        if above_one[i] == above_one[i-1] + 1:
            consec += 1
            if consec >= 3:
                onset_idx = above_one[i - 2]
                return dates_search[onset_idx].strftime("%Y-%m-%d"), None, float(Rt_array[burn_in_idx])
        else:
            consec = 1
    return None, "No 3 consecutive R(t) > 1", float(Rt_array[burn_in_idx])


# ============================================================
# RUN ONE SEASON
# ============================================================

def run_pinn(df, start_date, end_date, season_name, signal_col,
             n_epochs=15000, n_colloc=300, seed=42, verbose=True):

    mask = (df["MidDate"] >= start_date) & (df["MidDate"] <= end_date)
    season = df.loc[mask].dropna(subset=[signal_col]).copy()
    season = season.reset_index(drop=True)

    if len(season) < 8:
        return None

    t_days = (season["MidDate"] - season["MidDate"].min()).dt.days.values.astype(float)
    t_max = t_days.max()
    if t_max == 0:
        return None
    t_norm = t_days / t_max
    I_obs = season[signal_col].values
    peak = I_obs.max()

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
        print(f"  {season_name}  |  signal: {signal_col}  |  {len(season)} wks  |  peak {peak:.4f}")
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
                  f"data={d_loss.item():.6f}  phys={p_loss.item():.6f}")

    t_eval = torch.linspace(0, 1, 500, dtype=torch.float32).reshape(-1, 1)
    with torch.no_grad():
        Rt_pred = model.compute_Rt(t_eval).numpy().flatten()

    t_eval_days = t_eval.numpy().flatten() * t_max
    dates_eval = pd.to_datetime(start_date) + pd.to_timedelta(t_eval_days, unit="D")

    burn_in_idx = int(28 / t_max * 500) if t_max > 28 else 0

    pinn_onset, fail_reason, rt_burnin = find_onset_crossing_from_below(
        Rt_pred, dates_eval, burn_in_idx
    )

    # CHP threshold onset (for reference)
    above = season[season["AandB_proportion"] > CHP_THRESHOLD] if "AandB_proportion" in season.columns else pd.DataFrame()
    chp_onset = above.iloc[0]["MidDate"].strftime("%Y-%m-%d") if len(above) > 0 else None

    lead = None
    if pinn_onset and chp_onset:
        lead = (pd.to_datetime(chp_onset) - pd.to_datetime(pinn_onset)).days

    result = {
        "season": season_name,
        "signal": signal_col,
        "peak_value": round(peak, 4),
        "Rt_at_burnin": round(rt_burnin, 3) if rt_burnin else None,
        "pinn_onset": pinn_onset,
        "chp_onset": chp_onset,
        "lead_days": lead,
        "best_Rt": round(float(Rt_pred.max()), 3),
        "fail_reason": fail_reason,
    }

    if verbose:
        print(f"  -> R(t)@burnin:  {result['Rt_at_burnin']}")
        print(f"  -> PINN onset:   {pinn_onset or 'N/D'}")
        if fail_reason:
            print(f"  -> Reason:       {fail_reason}")
        print(f"  -> CHP onset:    {chp_onset or 'N/A'}")
        if lead is not None:
            sign = "PINN leads" if lead > 0 else "CHP leads"
            print(f"  -> Lead:         {abs(lead)}d ({sign})")
        print(f"  -> Best R(t):    {result['best_Rt']}")

    return result


# ============================================================
# TEST SEASONS (where positivity-PINN failed + 1 control)
# ============================================================

TEST_SEASONS = [
    ("2014/15 winter", "2014-10-01", "2015-06-01"),
    ("2018/19 winter", "2018-09-15", "2019-06-01"),
    ("2023 summer",    "2023-01-15", "2023-10-01"),
    ("2023/24 winter", "2023-07-15", "2024-04-01"),
    ("2024/25 winter", "2024-08-01", "2025-04-01"),  # control: positivity PINN worked
]

ADMISSION_SIGNALS = [
    "Adm_All",
    "Adm_0_5",
    "Adm_6_11",
    "Adm_12_17",
    "Adm_65_higher",
]


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print("=" * 70)
    print("SEIR-PINN on HOSPITAL ADMISSIONS vs LAB POSITIVITY")
    print("Does better input signal rescue the PINN?")
    print("=" * 70)

    df = pd.read_csv("flux_data.csv")
    df["From"] = pd.to_datetime(df["From"], format="%d/%m/%Y")
    df["To"] = pd.to_datetime(df["To"], format="%d/%m/%Y")
    df["MidDate"] = df["From"] + (df["To"] - df["From"]) / 2

    results = []

    for season_name, start, end in TEST_SEASONS:
        # First: positivity (baseline)
        res = run_pinn(df, start, end, season_name, "AandB_proportion",
                      n_epochs=15000, verbose=True)
        if res:
            results.append(res)

        # Then: best admission signal (12-17y based on EpiEstim results)
        for adm_col in ["Adm_12_17", "Adm_0_5"]:
            res = run_pinn(df, start, end, season_name, adm_col,
                          n_epochs=15000, verbose=True)
            if res:
                results.append(res)

    # ========================================================
    # RESULTS
    # ========================================================
    results_df = pd.DataFrame(results)
    results_df.to_csv("pinn_admissions_results.csv", index=False)

    print(f"\n\n{'='*100}")
    print("COMPARISON: PINN on positivity vs PINN on admissions")
    print(f"{'='*100}")
    print(f"{'Season':<18} {'Signal':<18} {'R(t)@burn':>10} {'Onset':>12} {'Lead(d)':>8} {'R(t)max':>8}")
    print("-" * 80)

    for _, r in results_df.iterrows():
        onset_str = r["pinn_onset"] if r["pinn_onset"] else "N/D"
        lead_str = f"{r['lead_days']:.0f}" if pd.notna(r.get("lead_days")) and r["lead_days"] is not None else "N/A"
        rt_str = f"{r['Rt_at_burnin']:.3f}" if r["Rt_at_burnin"] is not None else "N/A"
        print(f"{r['season']:<18} {r['signal']:<18} {rt_str:>10} {onset_str:>12} {lead_str:>8} {r['best_Rt']:>8.3f}")

    # Summary
    print(f"\n{'='*70}")
    print("KEY QUESTION: Does R(t)@burnin drop below 1.0 with admissions input?")
    print(f"{'='*70}")

    for season_name, _, _ in TEST_SEASONS:
        season_results = results_df[results_df["season"] == season_name]
        pos_row = season_results[season_results["signal"] == "AandB_proportion"]
        adm_rows = season_results[season_results["signal"] != "AandB_proportion"]

        if len(pos_row) > 0:
            pos_rt = pos_row.iloc[0]["Rt_at_burnin"]
            print(f"\n  {season_name}:")
            print(f"    Positivity R(t)@burnin: {pos_rt}")
            for _, ar in adm_rows.iterrows():
                adm_rt = ar["Rt_at_burnin"]
                improved = "YES" if adm_rt is not None and adm_rt < 1.0 else "NO"
                print(f"    {ar['signal']:>15} R(t)@burnin: {adm_rt}  Below 1? {improved}")

    print(f"\n{'='*70}")
    print("IF admissions R(t)@burnin < 1.0 where positivity was > 1.0:")
    print("  -> Signal quality is the bottleneck, not gamma confounding")
    print("  -> Add one paragraph to paper: 'admissions rescue PINN onset detection'")
    print("")
    print("IF admissions R(t)@burnin still > 1.0:")
    print("  -> Gamma confounding persists regardless of input signal")
    print("  -> Add one paragraph: 'multi-signal observation model needed'")
    print("  -> Directly motivates PhD Aim 2")
    print(f"{'='*70}")
    print(f"\nResults saved to pinn_admissions_results.csv")
