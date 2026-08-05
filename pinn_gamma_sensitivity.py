"""
SEIR-PINN Gamma Sensitivity Test
==================================
Vijay's Comment 104: gamma = 0.1 (10-day infectious period) is outside
the usual 3-5 day range for influenza. Since R(t) = beta*S/gamma,
this inflates R(t) by 2-3x and may be the direct cause of burn-in
values > 1.0 that we interpreted as structural failure.

Test: rerun all 6 standard seasons with gamma = 0.1, 0.2, 0.33
  - gamma = 0.1  → 10-day infectious period (current, too long)
  - gamma = 0.2  → 5-day infectious period (standard)
  - gamma = 0.33 → 3-day infectious period (short end)

If burn-in R(t) drops below 1.0 with gamma = 0.2-0.33,
then the PINN failure was a parameter choice, not structural.

Run: conda activate pinn && python pinn_gamma_sensitivity.py

Thomas Yuan — HKU PhD, Pathogen Evolution Lab
"""

import torch
import torch.nn as nn
import numpy as np
import pandas as pd
import warnings

warnings.filterwarnings("ignore")

CHP_THRESHOLD = 0.0494

# ============================================================
# MODEL
# ============================================================

class SEIR_PINN(nn.Module):
    def __init__(self, hidden_layers=4, hidden_neurons=64, gamma_val=0.1):
        super().__init__()
        self.gamma_val = gamma_val
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
        return self.gamma_val

    @property
    def obs_scale(self):
        return torch.exp(self.log_obs_scale)

    def compute_Rt(self, t):
        S, E, I, R = self.forward(t)
        beta = self.get_beta(t)
        return beta * S / self.gamma_val


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
        return None, None
    below_one = np.where(Rt < 1.0)[0]
    if len(below_one) == 0:
        return None, "always >= 1"
    search_start = below_one[0]
    Rt_search = Rt[search_start:]
    dates_search = dates[search_start:]
    above_one = np.where(Rt_search > 1.0)[0]
    if len(above_one) < 3:
        return None, "never sustained > 1"
    consec = 1
    for i in range(1, len(above_one)):
        if above_one[i] == above_one[i-1] + 1:
            consec += 1
            if consec >= 3:
                onset_idx = above_one[i - 2]
                return dates_search[onset_idx].strftime("%Y-%m-%d"), None
        else:
            consec = 1
    return None, "no 3 consec > 1"


# ============================================================
# RUN ONE SEASON WITH ONE GAMMA
# ============================================================

def run_one(df, start, end, name, gamma_val, n_epochs=15000, seed=42):
    mask = (df["MidDate"] >= start) & (df["MidDate"] <= end)
    season = df.loc[mask].dropna(subset=["AandB_proportion"]).copy().reset_index(drop=True)
    if len(season) < 8:
        return None

    t_days = (season["MidDate"] - season["MidDate"].min()).dt.days.values.astype(float)
    t_max = t_days.max()
    if t_max == 0:
        return None
    t_norm = t_days / t_max
    I_obs = season["AandB_proportion"].values

    t_data = torch.tensor(t_norm, dtype=torch.float32).reshape(-1, 1)
    I_data = torch.tensor(I_obs, dtype=torch.float32).reshape(-1, 1)
    t_colloc = torch.linspace(0, 1, 300, dtype=torch.float32).reshape(-1, 1)
    t_colloc.requires_grad = True

    torch.manual_seed(seed)
    model = SEIR_PINN(gamma_val=gamma_val)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=3000, gamma=0.5)

    for epoch in range(n_epochs):
        optimizer.zero_grad()
        total, d_loss, p_loss, ic_loss = compute_seir_loss(model, t_data, I_data, t_colloc, t_max)
        total.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
        scheduler.step()

    t_eval = torch.linspace(0, 1, 500, dtype=torch.float32).reshape(-1, 1)
    with torch.no_grad():
        Rt_pred = model.compute_Rt(t_eval).numpy().flatten()

    t_eval_days = t_eval.numpy().flatten() * t_max
    dates_eval = pd.to_datetime(start) + pd.to_timedelta(t_eval_days, unit="D")

    burn_in_idx = int(28 / t_max * 500) if t_max > 28 else 0
    rt_burnin = float(Rt_pred[burn_in_idx])

    onset, fail = find_onset_crossing_from_below(Rt_pred, dates_eval, burn_in_idx)

    above = season[season["AandB_proportion"] > CHP_THRESHOLD]
    chp_onset = above.iloc[0]["MidDate"].strftime("%Y-%m-%d") if len(above) > 0 else None
    lead = (pd.to_datetime(chp_onset) - pd.to_datetime(onset)).days if onset and chp_onset else None

    return {
        "season": name,
        "gamma": gamma_val,
        "infect_days": round(1.0/gamma_val, 1),
        "Rt_burnin": round(rt_burnin, 3),
        "best_Rt": round(float(Rt_pred.max()), 3),
        "onset": onset,
        "chp_onset": chp_onset,
        "lead": lead,
        "fail": fail,
        "loss": round(total.item(), 6),
    }


# ============================================================
# SEASONS AND GAMMAS
# ============================================================

SEASONS = [
    ("2014/15 winter", "2014-10-01", "2015-06-01"),
    ("2015/16 winter", "2015-10-01", "2016-06-01"),
    ("2018/19 winter", "2018-09-15", "2019-06-01"),
    ("2023 summer",    "2023-01-15", "2023-10-01"),
    ("2023/24 winter", "2023-07-15", "2024-04-01"),
    ("2024/25 winter", "2024-08-01", "2025-04-01"),
]

GAMMAS = [0.1, 0.2, 0.33]


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print("=" * 90)
    print("PINN GAMMA SENSITIVITY (Vijay Comment 104)")
    print("Does fixing gamma to 0.2-0.33 resolve the R(t) burn-in inflation?")
    print("=" * 90)

    df = pd.read_csv("flux_data.csv")
    df["From"] = pd.to_datetime(df["From"], format="%d/%m/%Y")
    df["To"] = pd.to_datetime(df["To"], format="%d/%m/%Y")
    df["MidDate"] = df["From"] + (df["To"] - df["From"]) / 2

    results = []
    for name, start, end in SEASONS:
        print(f"\n{'='*70}")
        print(f"  {name}")
        print(f"{'='*70}")
        for g in GAMMAS:
            print(f"  gamma={g} ({1/g:.1f}d infectious)...", end=" ", flush=True)
            res = run_one(df, start, end, name, g)
            if res:
                results.append(res)
                below = "YES" if res["Rt_burnin"] < 1.0 else "NO"
                det = res["onset"] or "N/D"
                ld = f"{res['lead']:+d}d" if res["lead"] is not None else "N/A"
                print(f"R(t)@burn={res['Rt_burnin']:.3f} (below 1? {below})  "
                      f"onset={det}  lead={ld}  bestRt={res['best_Rt']:.3f}")

    results_df = pd.DataFrame(results)
    results_df.to_csv("gamma_sensitivity_results.csv", index=False)

    # ========================================================
    # SUMMARY TABLE
    # ========================================================
    print(f"\n\n{'='*100}")
    print("GAMMA SENSITIVITY: R(t) at burn-in across gamma values")
    print(f"{'='*100}")
    print(f"{'Season':<18} {'gamma=0.1 (10d)':>16} {'gamma=0.2 (5d)':>16} {'gamma=0.33 (3d)':>17}")
    print(f"{'':18} {'Rt@burn  onset':>16} {'Rt@burn  onset':>16} {'Rt@burn  onset':>17}")
    print("-" * 70)

    for name, _, _ in SEASONS:
        print(f"{name:<18}", end="")
        for g in GAMMAS:
            match = results_df[(results_df["season"] == name) & (results_df["gamma"] == g)]
            if len(match) > 0:
                r = match.iloc[0]
                rt = f"{r['Rt_burnin']:.3f}"
                det = "YES" if r["onset"] else "no"
                print(f" {rt:>7} {det:>7}", end="")
            else:
                print(f" {'N/A':>7} {'N/A':>7}", end="")
        print()

    # Count how many start below 1
    print(f"\n{'='*70}")
    print("KEY METRIC: How many seasons start with R(t) < 1.0 at burn-in?")
    print(f"{'='*70}")
    for g in GAMMAS:
        subset = results_df[results_df["gamma"] == g]
        below = (subset["Rt_burnin"] < 1.0).sum()
        total = len(subset)
        detected = subset["onset"].notna().sum()
        print(f"  gamma={g:.2f} ({1/g:.0f}d): {below}/{total} below 1.0, {detected}/{total} onset detected")

    print(f"\n{'='*70}")
    print("IF gamma=0.2 fixes most burn-in inflation:")
    print("  -> The PINN failure was a parameter choice, not structural")
    print("  -> Rewrite paper: PINN works with correct gamma")
    print("")
    print("IF gamma=0.2 still shows burn-in > 1.0:")
    print("  -> Structural interpretation holds, gamma isn't the only cause")
    print("  -> Paper gains credibility: tested Vijay's alternative explanation")
    print(f"{'='*70}")
    print(f"\nResults saved to gamma_sensitivity_results.csv")
