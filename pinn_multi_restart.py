"""
Multi-Restart PINN Sensitivity (Vijay Comment 105)
=====================================================
Runs the PINN with 5 different random seeds per season
to assess whether results are stable or optimisation artefacts.

Run: conda activate pinn && python pinn_multi_restart.py
Requires: flux_data.csv
Expect: ~15 minutes (6 seasons × 5 seeds × ~30s each)

Thomas Yuan — HKU PhD, Pathogen Evolution Lab
"""

import torch
import torch.nn as nn
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings("ignore")

GAMMA_VAL = 0.2  # literature standard
CHP_THRESHOLD = 0.0494
SEEDS = [42, 123, 456, 789, 1024]

class SEIR_PINN(nn.Module):
    def __init__(self):
        super().__init__()
        layers = [nn.Linear(1, 64), nn.Tanh()]
        for _ in range(3):
            layers += [nn.Linear(64, 64), nn.Tanh()]
        layers.append(nn.Linear(64, 4))
        self.state_net = nn.Sequential(*layers)
        self.beta_net = nn.Sequential(
            nn.Linear(1, 32), nn.Tanh(), nn.Linear(32, 32), nn.Tanh(), nn.Linear(32, 1))
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
    def obs_scale(self):
        return torch.exp(self.log_obs_scale)

    def compute_Rt(self, t):
        S, E, I, R = self.forward(t)
        return self.get_beta(t) * S / GAMMA_VAL

def compute_loss(model, t_data, I_data, t_phys, t_max):
    _, _, I_d, _ = model(t_data)
    data_loss = torch.mean((model.obs_scale * I_d - I_data) ** 2)
    S, E, I, R = model(t_phys)
    beta = model.get_beta(t_phys)
    sigma, gamma = model.sigma, GAMMA_VAL
    dS = torch.autograd.grad(S, t_phys, torch.ones_like(S), create_graph=True)[0]
    dE = torch.autograd.grad(E, t_phys, torch.ones_like(E), create_graph=True)[0]
    dI = torch.autograd.grad(I, t_phys, torch.ones_like(I), create_graph=True)[0]
    dR = torch.autograd.grad(R, t_phys, torch.ones_like(R), create_graph=True)[0]
    sc = t_max
    phys = (torch.mean((dS/sc + beta*S*I)**2) + torch.mean((dE/sc - beta*S*I + sigma*E)**2) +
            torch.mean((dI/sc - sigma*E + gamma*I)**2) + torch.mean((dR/sc - gamma*I)**2))
    t0 = torch.tensor([[0.0]])
    S0, E0, I0, R0 = model(t0)
    ic = ((S0-0.95)**2 + (E0-0.01)**2 + (I0-0.01)**2 + (R0-0.03)**2).sum()
    return 10*data_loss + phys + 5*ic, data_loss

def find_onset(Rt, dates, burn_idx):
    Rt_b = Rt[burn_idx:]
    dates_b = dates[burn_idx:]
    below = np.where(Rt_b < 1.0)[0]
    if len(below) == 0:
        return None, float(Rt[burn_idx])
    start = below[0]
    above = np.where(Rt_b[start:] > 1.0)[0]
    if len(above) < 3:
        return None, float(Rt[burn_idx])
    consec = 1
    for i in range(1, len(above)):
        if above[i] == above[i-1] + 1:
            consec += 1
            if consec >= 3:
                return dates_b[start + above[i-2]].strftime("%Y-%m-%d"), float(Rt[burn_idx])
        else:
            consec = 1
    return None, float(Rt[burn_idx])

SEASONS = [
    ("2014/15", "2014-10-01", "2015-06-01"),
    ("2015/16", "2015-10-01", "2016-06-01"),
    ("2018/19", "2018-09-15", "2019-06-01"),
    ("2023 S", "2023-01-15", "2023-10-01"),
    ("2023/24", "2023-07-15", "2024-04-01"),
    ("2024/25", "2024-08-01", "2025-04-01"),
]

if __name__ == "__main__":
    print("=" * 80)
    print(f"MULTI-RESTART PINN (Comment 105): {len(SEEDS)} seeds × {len(SEASONS)} seasons")
    print(f"  gamma = {GAMMA_VAL}, epochs = 15000")
    print("=" * 80)

    df = pd.read_csv("flux_data.csv")
    df["From"] = pd.to_datetime(df["From"], format="%d/%m/%Y")
    df["To"] = pd.to_datetime(df["To"], format="%d/%m/%Y")
    df["MidDate"] = df["From"] + (df["To"] - df["From"]) / 2

    results = []
    for sname, start, end in SEASONS:
        mask = (df["MidDate"] >= start) & (df["MidDate"] <= end)
        season = df.loc[mask].dropna(subset=["AandB_proportion"]).sort_values("MidDate").reset_index(drop=True)
        if len(season) < 8:
            continue

        t_days = (season["MidDate"] - season["MidDate"].min()).dt.days.values.astype(float)
        t_max = t_days.max()
        t_norm = t_days / t_max
        I_obs = season["AandB_proportion"].values
        t_data = torch.tensor(t_norm, dtype=torch.float32).reshape(-1, 1)
        I_data = torch.tensor(I_obs, dtype=torch.float32).reshape(-1, 1)
        t_colloc = torch.linspace(0, 1, 300, dtype=torch.float32).reshape(-1, 1)
        t_colloc.requires_grad = True

        above = season[season["AandB_proportion"] > CHP_THRESHOLD]
        chp_onset = above.iloc[0]["MidDate"] if len(above) > 0 else None

        print(f"\n  {sname}:")
        for seed in SEEDS:
            torch.manual_seed(seed)
            model = SEIR_PINN()
            opt = torch.optim.Adam(model.parameters(), lr=1e-3)
            sched = torch.optim.lr_scheduler.StepLR(opt, step_size=3000, gamma=0.5)
            for ep in range(15000):
                opt.zero_grad()
                loss, dl = compute_loss(model, t_data, I_data, t_colloc, t_max)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                opt.step()
                sched.step()

            t_eval = torch.linspace(0, 1, 500, dtype=torch.float32).reshape(-1, 1)
            with torch.no_grad():
                Rt = model.compute_Rt(t_eval).numpy().flatten()
            dates_eval = pd.to_datetime(start) + pd.to_timedelta(t_eval.numpy().flatten() * t_max, unit="D")
            burn_idx = int(28 / t_max * 500) if t_max > 28 else 0

            onset, rt_burn = find_onset(Rt, dates_eval, burn_idx)
            lead = (chp_onset - pd.to_datetime(onset)).days if onset and chp_onset else None

            results.append({
                "season": sname, "seed": seed,
                "Rt_burnin": round(rt_burn, 3),
                "onset": onset,
                "lead": lead,
                "best_Rt": round(float(Rt.max()), 3),
                "final_loss": round(loss.item(), 6),
            })

            ld = f"{lead:+d}" if lead else "N/A"
            det = onset or "N/D"
            print(f"    seed={seed}: Rt@burn={rt_burn:.3f}  onset={det}  lead={ld}  loss={loss.item():.6f}")

    results_df = pd.DataFrame(results)
    results_df.to_csv("pinn_multi_restart_results.csv", index=False)

    # Summary
    print(f"\n{'='*80}")
    print("STABILITY SUMMARY")
    print(f"{'='*80}")
    print(f"{'Season':<12} {'Rt@burn range':>16} {'Onset range':>20} {'Detected':>10}")
    print("-" * 62)
    for sname, _, _ in SEASONS:
        sub = results_df[results_df["season"] == sname]
        rt_range = f"{sub['Rt_burnin'].min():.3f}-{sub['Rt_burnin'].max():.3f}"
        detected = sub["onset"].notna().sum()
        onsets = sub["onset"].dropna()
        if len(onsets) > 0:
            onset_range = f"{onsets.min()} to {onsets.max()}"
        else:
            onset_range = "N/D"
        print(f"{sname:<12} {rt_range:>16} {onset_range:>20} {detected}/{len(sub):>8}")

    print(f"\nResults saved to pinn_multi_restart_results.csv")
