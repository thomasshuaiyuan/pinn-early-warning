"""Consistency check, 19 Nov 2026. The positivity series in flux_data.csv (Flu Express) counts Hospital Authority
specimens as well as Public Health Laboratory Services Branch specimens from the week of 24 July 2022; CHP's
statistics pages give a Branch-only series for the whole of 2014-2026. This script reruns, on the Branch-only
series, (a) the threshold date and EpiEstim onset for the influenza seasons and (b) the pre/post-COVID peak comparison.
EpiEstim settings as in rerun_full_series.py: weekly, SI mean 3.0 SD 1.5 days, 4-week window, Gamma(1, rate 0.2)
prior, incidence = positivity x 10000. Onset = first week in the season window with posterior mean R(t) > 1
(lower 2.5% bound also reported). Threshold date = first week in the window with positivity >= 4.94%.
Usage: python3 -I epiestim_consistent_series.py <dir with flux_data.csv etc.> <dir with series_comparison_weekly.csv>"""
import sys, numpy as np, pandas as pd
from scipy import stats
from scipy.stats import gamma as G
D, C = sys.argv[1], sys.argv[2]
df = pd.read_csv(f"{D}/flux_data.csv")
for c in ("From", "To"): df[c] = pd.to_datetime(df[c], format="%d/%m/%Y")
df["Mid"] = df["From"] + (df["To"] - df["From"]) / 2
cmp_ = pd.read_csv(f"{C}/series_comparison_weekly.csv")
df = df.merge(cmp_[["year", "week", "stat_pct"]], left_on=["Year", "Week"], right_on=["year", "week"], how="left")
df = df.dropna(subset=["AandB_proportion"]).sort_values("Mid").reset_index(drop=True)
df["flux"] = df.AandB_proportion; df["branch"] = df.stat_pct / 100
print("weeks:", len(df), " weeks without a Branch-only value:", int(df.branch.isna().sum()))
print("max |difference| before 24 Jul 2022 (percentage points):", round(float((df.flux - df.branch)[df.Mid < "2022-07-24"].abs().max() * 100), 3))
def epi(inc, si_mean=3.0, si_sd=1.5, window=4, tu=7.0):
    n = len(inc); sh = (si_mean / si_sd) ** 2; sc = si_sd ** 2 / si_mean; si = np.zeros(n)
    for t in range(1, n): si[t] = G.cdf((t + .5) * tu, a=sh, scale=sc) - G.cdf(max(0, (t - .5) * tu), a=sh, scale=sc)
    si /= si.sum(); lam = np.zeros(n)
    for t in range(1, n): lam[t] = np.dot(inc[t - 1::-1][:t], si[1:t + 1])
    mean = np.full(n, np.nan); low = np.full(n, np.nan)
    for t in range(window, n):
        a = t - window + 1; sI = inc[a:t + 1].sum(); sL = lam[a:t + 1].sum()
        mean[t] = (1 + sI) / (0.2 + sL); low[t] = G.ppf(0.025, a=1 + sI, scale=1 / (0.2 + sL))
    return mean, low
s1 = pd.read_csv(f"{D}/supplementary_table_S1_seasons.csv"); s1 = s1[s1.pathogen == "Influenza"]
ci = pd.read_csv(f"{D}/epiestim_ci_onset_comparison.csv").set_index("season")
short = {"2014/15 winter": "2014/15", "2015/16 winter": "2015/16", "2016/17 winter": "2016/17", "2017/18 summer": "2017/18", "2018/19 winter": "2018/19", "2023 summer": "2023 S", "2023/24 winter": "2023/24", "2024/25 winter": "2024/25"}
rows = []
for r in s1.itertuples():
    sub = df[(df.Mid >= r.start_date) & (df.Mid <= r.end_date)]; k = short[r.season]; row = {"season": k}
    for name in ("flux", "branch"):
        p = sub[name].values.astype(float); m, l = epi(p * 10000)
        on = sub.Mid.values[np.nanargmax(m > 1)] if np.nansum(m > 1) else None
        onl = sub.Mid.values[np.nanargmax(l > 1)] if np.nansum(l > 1) else None
        th = sub.Mid.values[np.argmax(p >= 0.0494)] if (p >= 0.0494).any() else None
        d = lambda x: pd.Timestamp(x).date() if x is not None else ""
        row.update({f"{name}_threshold": d(th), f"{name}_onset_mean": d(on), f"{name}_onset_lower": d(onl),
                    f"{name}_lead_days": (pd.Timestamp(th) - pd.Timestamp(on)).days if th is not None and on is not None else "",
                    f"{name}_peak_pct": round(float(np.nanmax(p)) * 100, 2)})
    row["committed_onset"] = ci.loc[k].mean_onset if k in ci.index else ""; row["committed_threshold"] = ci.loc[k].chp_onset if k in ci.index else ""
    rows.append(row)
out = pd.DataFrame(rows); out.to_csv("epiestim_consistent_series_results.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30); print(out.to_string(index=False))

# ---- (b) pre/post-COVID peak comparison, as in postcovid_peak_comparison.py, on both series
out["start_year"] = pd.to_datetime(s1.start_date.values).year
lead = lambda col: [x for x in out.loc[out.committed_onset != "", col]]
for name in ("flux", "branch"):
    L = lead(f"{name}_lead_days"); print(f"\n{name}: leads in the six primary seasons {L}  median {np.median(L)}  led in {sum(x > 0 for x in L)} of {len(L)}")
    pre = out.loc[out.start_year <= 2019, f"{name}_peak_pct"].to_numpy(float); post = out.loc[out.start_year >= 2023, f"{name}_peak_pct"].to_numpy(float)
    n1, n2 = len(pre), len(post); diff = pre.mean() - post.mean()
    sp2 = ((n1 - 1) * pre.var(ddof=1) + (n2 - 1) * post.var(ddof=1)) / (n1 + n2 - 2); se = np.sqrt(sp2 * (1 / n1 + 1 / n2)); tc = stats.t.ppf(0.975, n1 + n2 - 2)
    print(f"{name}: peaks pre {pre.round(2).tolist()} post {post.round(2).tolist()}  mean pre {pre.mean():.2f} post {post.mean():.2f} diff {diff:.2f} "
          f"CI {diff - tc * se:.2f} to {diff + tc * se:.2f}  p equal-var {stats.ttest_ind(pre, post).pvalue:.3f}  Welch {stats.ttest_ind(pre, post, equal_var=False).pvalue:.3f}  "
          f"Mann-Whitney {stats.mannwhitneyu(pre, post, alternative='two-sided').pvalue:.3f}")
