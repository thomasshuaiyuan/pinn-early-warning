"""
Post-COVID vs pre-COVID influenza peak positivity (manuscript Results, "Post-COVID seasonal shift").

Reads the season peaks from supplementary_table_S1_seasons.csv (influenza rows only):
pre-COVID = seasons starting 2014-2019 (n = 5), post-COVID = seasons starting 2023 or later (n = 3).
Reports means, the difference with a pooled-variance (equal-variance) t interval, the
equal-variance and Welch t-tests and a two-sided Mann-Whitney test.

Run: python postcovid_peak_comparison.py
Writes: postcovid_peak_comparison_results.csv
"""
import numpy as np
import pandas as pd
from scipy import stats

s1 = pd.read_csv("supplementary_table_S1_seasons.csv")
flu = s1[s1["pathogen"] == "Influenza"].copy()
flu["start_year"] = pd.to_datetime(flu["start_date"]).dt.year
pre = flu.loc[flu["start_year"] <= 2019, "peak_positivity_pct"].to_numpy(float)
post = flu.loc[flu["start_year"] >= 2023, "peak_positivity_pct"].to_numpy(float)
assert len(pre) == 5 and len(post) == 3, (len(pre), len(post))

n1, n2 = len(pre), len(post)
diff = pre.mean() - post.mean()
sp2 = ((n1 - 1) * pre.var(ddof=1) + (n2 - 1) * post.var(ddof=1)) / (n1 + n2 - 2)
se = np.sqrt(sp2 * (1 / n1 + 1 / n2))
df = n1 + n2 - 2
tcrit = stats.t.ppf(0.975, df)
t_eq = stats.ttest_ind(pre, post, equal_var=True)
t_w = stats.ttest_ind(pre, post, equal_var=False)
mw = stats.mannwhitneyu(pre, post, alternative="two-sided")

row = {
    "n_pre": n1, "n_post": n2,
    "mean_pre": round(pre.mean(), 2), "mean_post": round(post.mean(), 2),
    "difference": round(diff, 2),
    "ci95_low_pooled_t": round(diff - tcrit * se, 2), "ci95_high_pooled_t": round(diff + tcrit * se, 2),
    "t_equal_var": round(t_eq.statistic, 2), "df": df, "p_equal_var": round(t_eq.pvalue, 3),
    "p_welch": round(t_w.pvalue, 3), "p_mann_whitney": round(mw.pvalue, 3),
}
pd.DataFrame([row]).to_csv("postcovid_peak_comparison_results.csv", index=False)
for k, v in row.items():
    print(f"{k:>20}: {v}")
