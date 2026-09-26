"""
Paired test: 12-17y admissions-based vs positivity-based EpiEstim onset (manuscript Results,
"Age-stratified admissions outperform positivity on difficult seasons").

Source of record for the reported test. Reads the primary EpiEstim admissions output, the same
file behind Table 1 and Figure 4, and writes wilcoxon_admissions_results.csv.

Method
- Difference per season = positivity onset - 12-17y admissions onset (days; positive = admissions earlier).
- One-sided Wilcoxon signed-rank test (H1: admissions earlier), zero differences excluded before
  ranking (Wilcoxon's method), tied absolute differences given average ranks, exact null distribution
  (scipy.stats.wilcoxon default for small n without zeros).
- Bootstrap 95% CI for the median difference: 10,000 resamples of the 8 seasons, numpy default_rng(42).
- Sensitivity row: excludes 2014/15 and 2015/16, whose 12-17y fits are degenerate (near-zero
  admission denominators).

Note: Analysis 2 in outstanding_analyses.py runs the same test on the normalised-scaling rerun
(epiestim_fixed_scaling.csv) and gives W = 10.5, p = 0.25. That is a different input, not the
reported test.

Run: python wilcoxon_admissions.py
"""
import numpy as np
import pandas as pd
import scipy
from scipy.stats import wilcoxon

IN = "epiestim_admissions_results.csv"
OUT = "wilcoxon_admissions_results.csv"
SEASONS = {"2014/15 winter": "2014/15", "2015/16 winter": "2015/16", "2016/17 winter": "2016/17",
           "2017/18 summer": "2017/18", "2018/19 winter": "2018/19", "2023 summer": "2023 S",
           "2023/24 winter": "2023/24", "2024/25 winter": "2024/25"}
DEGENERATE = {"2014/15", "2015/16"}

a = pd.read_csv(IN, parse_dates=["onset_date"])
a["season"] = a["season_name"].map(SEASONS)
pos = a[a.signal == "AandB_proportion"].set_index("season").onset_date
adm = a[a.signal == "Adm_12_17"].set_index("season").onset_date
order = list(SEASONS.values())
diffs = pd.Series({s: (pos[s] - adm[s]).days for s in order})


def test(d, label):
    d = np.asarray(d, dtype=float)
    nz = d[d != 0]
    res = wilcoxon(nz, alternative="greater")
    rng = np.random.default_rng(42)
    boot = [np.median(rng.choice(d, size=len(d), replace=True)) for _ in range(10000)]
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return {"analysis": label, "n_seasons": len(d), "n_zero_differences": int((d == 0).sum()),
            "n_nonzero_pairs": len(nz), "W": float(res.statistic), "p_one_sided": round(float(res.pvalue), 4),
            "median_difference_days": float(np.median(d)), "mean_difference_days": round(float(d.mean()), 1),
            "boot95_lo": float(lo), "boot95_hi": float(hi), "scipy_version": scipy.__version__,
            "differences": "; ".join(f"{s}:{int(x):+d}" for s, x in zip(d_index[label], d))}


d_index = {"primary (all 8 seasons)": order,
           "sensitivity (excluding degenerate 2014/15, 2015/16)": [s for s in order if s not in DEGENERATE]}
rows = [test(diffs[d_index[k]].values, k) for k in d_index]
tmp = OUT + ".tmp"
pd.DataFrame(rows).to_csv(tmp, index=False)
import os
os.replace(tmp, OUT)
print(pd.DataFrame(rows).drop(columns=["differences"]).to_string(index=False))
