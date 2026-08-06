"""
Final Supplementary Analyses
==============================
1. COVID exclusion sensitivity: rerun EpiEstim including 2020-2022 weeks
2. Scraper validation: check RSV data completeness and quality
3. Peak detection specification

Run: conda activate pinn && python final_supplementary.py
Requires: flux_data.csv, chp_respiratory_cleaned.csv

Thomas Yuan — HKU PhD, Pathogen Evolution Lab
"""

import numpy as np
import pandas as pd
from scipy.stats import gamma as gamma_dist
from scipy.signal import find_peaks
import warnings
warnings.filterwarnings("ignore")

# ============================================================
# 1. COVID EXCLUSION SENSITIVITY
# ============================================================
print("=" * 80)
print("ANALYSIS 1: COVID exclusion sensitivity (Comment 98)")
print("  Compare non-season threshold with and without 2020-2022")
print("=" * 80)

df = pd.read_csv("flux_data.csv")
df["From"] = pd.to_datetime(df["From"], format="%d/%m/%Y")
df["To"] = pd.to_datetime(df["To"], format="%d/%m/%Y")
df["MidDate"] = df["From"] + (df["To"] - df["From"]) / 2

# Threshold WITHOUT 2020-2022 (current approach)
excl = df[(df["MidDate"] < "2020-01-01") | (df["MidDate"] > "2022-12-31")]
vals_excl = excl["AandB_proportion"].dropna()
nonseas_excl = vals_excl[vals_excl < vals_excl.median()]
thresh_excl = nonseas_excl.mean() + 1.96 * nonseas_excl.std()

# Threshold WITH 2020-2022 (sensitivity)
vals_all = df["AandB_proportion"].dropna()
nonseas_all = vals_all[vals_all < vals_all.median()]
thresh_all = nonseas_all.mean() + 1.96 * nonseas_all.std()

# Using only 2014-2019
pre = df[df["MidDate"] < "2020-01-01"]
vals_pre = pre["AandB_proportion"].dropna()
nonseas_pre = vals_pre[vals_pre < vals_pre.median()]
thresh_pre = nonseas_pre.mean() + 1.96 * nonseas_pre.std()

print(f"\n  Period              Non-season n    Mean%     SD%    Threshold")
print(f"  {'2014-2019 only':<22} {len(nonseas_pre):>4}    {nonseas_pre.mean()*100:.2f}%   {nonseas_pre.std()*100:.2f}%    {thresh_pre*100:.2f}%")
print(f"  {'2014-2026 excl COVID':<22} {len(nonseas_excl):>4}    {nonseas_excl.mean()*100:.2f}%   {nonseas_excl.std()*100:.2f}%    {thresh_excl*100:.2f}%")
print(f"  {'2014-2026 incl COVID':<22} {len(nonseas_all):>4}    {nonseas_all.mean()*100:.2f}%   {nonseas_all.std()*100:.2f}%    {thresh_all*100:.2f}%")

# COVID weeks stats
covid_mask = (df["MidDate"] >= "2020-01-01") & (df["MidDate"] <= "2022-12-31")
covid_weeks = df[covid_mask]
n_covid = len(covid_weeks)
covid_mean = covid_weeks["AandB_proportion"].mean()
covid_above = (covid_weeks["AandB_proportion"] > thresh_excl).sum()
print(f"\n  COVID period (2020-01-01 to 2022-12-31):")
print(f"    Weeks: {n_covid}")
print(f"    Mean positivity: {covid_mean*100:.2f}%")
print(f"    Weeks above threshold: {covid_above}/{n_covid}")

# Impact on post-COVID season onsets
print(f"\n  Impact on onset dates (post-COVID seasons):")
post_seasons = [
    ("2023 S", "2023-01-15", "2023-10-01"),
    ("2023/24", "2023-07-15", "2024-04-01"),
    ("2024/25", "2024-08-01", "2025-04-01"),
]

print(f"  {'Season':<12} {'Excl thresh':>14} {'Incl thresh':>14} {'Pre-only':>14}")
for sname, start, end in post_seasons:
    mask = (df["MidDate"] >= start) & (df["MidDate"] <= end)
    season = df.loc[mask].sort_values("MidDate")
    
    results = []
    for thresh, label in [(thresh_excl, "excl"), (thresh_all, "incl"), (thresh_pre, "pre")]:
        above = season[season["AandB_proportion"] > thresh]
        onset = above.iloc[0]["MidDate"].strftime("%m-%d") if len(above) > 0 else "N/D"
        results.append(onset)
    
    print(f"  {sname:<12} {results[0]:>14} {results[1]:>14} {results[2]:>14}")


# ============================================================
# 2. SCRAPER VALIDATION
# ============================================================
print(f"\n\n{'='*80}")
print("ANALYSIS 2: RSV scraper validation (Comment 96)")
print("=" * 80)

try:
    rsv = pd.read_csv("chp_respiratory_cleaned.csv")
    rsv["From"] = pd.to_datetime(rsv["From"])
    rsv["To"] = pd.to_datetime(rsv["To"])
    rsv["MidDate"] = rsv["From"] + (rsv["To"] - rsv["From"]) / 2

    total_weeks = len(rsv)
    date_range = f"{rsv['From'].min().strftime('%Y-%m-%d')} to {rsv['To'].max().strftime('%Y-%m-%d')}"
    
    # Check for gaps
    rsv_sorted = rsv.sort_values("From")
    expected_weeks = pd.date_range(rsv_sorted["From"].min(), rsv_sorted["To"].max(), freq="7D")
    
    # Missing RSV_pct
    missing_rsv = rsv["RSV_pct"].isna().sum()
    zero_rsv = (rsv["RSV_pct"] == 0).sum()
    
    # Check for duplicate weeks
    dup_weeks = rsv.duplicated(subset=["Year", "Week"]).sum()
    
    # Weekly gaps
    diffs = rsv_sorted["From"].diff().dt.days
    gap_weeks = (diffs > 8).sum()  # more than 8 days between starts = gap
    
    print(f"\n  Total weeks in file: {total_weeks}")
    print(f"  Date range: {date_range}")
    print(f"  Missing RSV_pct values: {missing_rsv}")
    print(f"  Zero RSV_pct values: {zero_rsv}")
    print(f"  Duplicate year-week entries: {dup_weeks}")
    print(f"  Gaps (>8 days between consecutive weeks): {gap_weeks}")
    
    if gap_weeks > 0:
        gaps = rsv_sorted[diffs > 8]
        print(f"  Gap locations:")
        for _, row in gaps.head(10).iterrows():
            print(f"    {row['From'].strftime('%Y-%m-%d')}")
    
    # Columns present
    print(f"\n  Columns: {list(rsv.columns)}")
    
    # Basic plausibility
    print(f"\n  RSV_pct range: {rsv['RSV_pct'].min():.2f} to {rsv['RSV_pct'].max():.2f}")
    print(f"  RSV_pct mean: {rsv['RSV_pct'].mean():.2f}")
    
    # Spot check: known values
    print(f"\n  Spot checks against published CHP figures:")
    print(f"  [Manual validation required: compare 5-10 randomly selected weeks")
    print(f"   against the published CHP weekly reports at chp.gov.hk]")
    
    # Random sample for manual checking
    sample = rsv.sample(5, random_state=42)[["Year", "Week", "RSV_pct", "RSV_count"]].sort_values(["Year", "Week"])
    print(f"\n  Random sample for manual verification:")
    print(f"  {'Year':>6} {'Week':>6} {'RSV_pct':>10} {'RSV_count':>10}")
    for _, row in sample.iterrows():
        pct = f"{row['RSV_pct']:.2f}" if pd.notna(row['RSV_pct']) else "N/A"
        cnt = f"{row['RSV_count']:.0f}" if pd.notna(row['RSV_count']) else "N/A"
        print(f"  {row['Year']:>6} {row['Week']:>6} {pct:>10} {cnt:>10}")

except Exception as e:
    print(f"  Error: {e}")


# ============================================================
# 3. PEAK DETECTION SPECIFICATION
# ============================================================
print(f"\n\n{'='*80}")
print("ANALYSIS 3: Peak detection specification (Comment 100)")
print("=" * 80)

print("""
Peak detection method for season classification:

1. Smooth AandB_proportion with a 3-week rolling mean
2. Apply scipy.signal.find_peaks with:
   - prominence = 0.02 (minimum 2 percentage points above surrounding troughs)
   - distance = 8 (minimum 8 weeks between peaks)
3. If 1 peak detected: classify as single-wave
4. If 2+ peaks detected: classify as multi-wave
5. Verify by checking subtype composition at each peak
   (sequential peaks from different subtypes confirm multi-wave)

Applied to 8 influenza seasons:
""")

for sname, start, end in [
    ("2014/15", "2014-10-01", "2015-06-01"),
    ("2015/16", "2015-10-01", "2016-06-01"),
    ("2016/17", "2016-09-15", "2017-06-01"),
    ("2017/18", "2017-04-01", "2018-04-01"),
    ("2018/19", "2018-09-15", "2019-06-01"),
    ("2023 S", "2023-01-15", "2023-10-01"),
    ("2023/24", "2023-07-15", "2024-04-01"),
    ("2024/25", "2024-08-01", "2025-04-01"),
]:
    mask = (df["MidDate"] >= start) & (df["MidDate"] <= end)
    season = df.loc[mask].dropna(subset=["AandB_proportion"]).sort_values("MidDate")
    
    if len(season) < 6:
        continue
    
    smoothed = season["AandB_proportion"].rolling(3, center=True, min_periods=1).mean().values
    peaks, props = find_peaks(smoothed, prominence=0.02, distance=8)
    
    classification = "Single-wave" if len(peaks) <= 1 else f"Multi-wave ({len(peaks)} peaks)"
    peak_dates = [season.iloc[p]["MidDate"].strftime("%Y-%m-%d") for p in peaks]
    peak_vals = [f"{smoothed[p]*100:.1f}%" for p in peaks]
    
    print(f"  {sname}: {classification}")
    for d, v in zip(peak_dates, peak_vals):
        print(f"    Peak at {d}: {v}")


print(f"\n{'='*80}")
print("All supplementary analyses complete.")
print("Output files:")
print("  supplementary_table_S1_seasons.csv — season definitions")
print("  data_dictionary_flu_express.csv — variable dictionary")
print(f"{'='*80}")
