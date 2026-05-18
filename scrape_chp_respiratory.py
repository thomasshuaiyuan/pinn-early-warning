"""
CHP Respiratory Pathogen Scraper
=================================
Scrapes weekly RSV, adenovirus, metapneumovirus, rhinovirus/enterovirus,
parainfluenza, and Mycoplasma pneumoniae data from CHP's public pages.

Run: pip install requests beautifulsoup4 pandas lxml
     python scrape_chp_respiratory.py

Output: chp_other_respiratory_2014_2026.csv
        chp_parainfluenza_2014_2026.csv
        chp_all_pathogens_combined.csv  (merged with your flux_data.csv)

Thomas Yuan — HKU PhD, Pathogen Evolution Lab
"""

import requests
import pandas as pd
from bs4 import BeautifulSoup
import time
import re
import sys

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# ============================================================
# URL MAPPINGS (from CHP index page)
# ============================================================

# "Other respiratory viruses" pages (RSV, adenovirus, metapneumovirus, etc.)
OTHER_RESP_URLS = {
    2014: "https://www.chp.gov.hk/en/statistics/data/10/641/642/2278.html",
    2015: "https://www.chp.gov.hk/en/statistics/data/10/641/642/3671.html",
    2016: "https://www.chp.gov.hk/en/statistics/data/10/641/642/4970.html",
    2017: "https://www.chp.gov.hk/en/statistics/data/10/641/642/6321.html",
    2018: "https://www.chp.gov.hk/en/statistics/data/10/641/642/6780.html",
    2019: "https://www.chp.gov.hk/en/statistics/data/10/641/642/6823.html",
    2020: "https://www.chp.gov.hk/en/statistics/data/10/641/642/6887.html",
    2021: "https://www.chp.gov.hk/en/statistics/data/10/641/642/6933.html",
    2022: "https://www.chp.gov.hk/en/statistics/data/10/641/642/6989.html",
    2023: "https://www.chp.gov.hk/en/statistics/data/10/641/642/7024.html",
    2024: "https://www.chp.gov.hk/en/statistics/data/10/641/642/7054.html",
    2025: "https://www.chp.gov.hk/en/statistics/data/10/641/642/7081.html",
    2026: "https://www.chp.gov.hk/en/statistics/data/10/641/642/7103.html",
}

# Parainfluenza virus pages
PARA_URLS = {
    2014: "https://www.chp.gov.hk/en/statistics/data/10/641/642/2277.html",
    2015: "https://www.chp.gov.hk/en/statistics/data/10/641/642/3673.html",
    2016: "https://www.chp.gov.hk/en/statistics/data/10/641/642/4969.html",
    2017: "https://www.chp.gov.hk/en/statistics/data/10/641/642/6279.html",
    2018: "https://www.chp.gov.hk/en/statistics/data/10/641/642/6779.html",
    2019: "https://www.chp.gov.hk/en/statistics/data/10/641/642/6822.html",
    2020: "https://www.chp.gov.hk/en/statistics/data/10/641/642/6886.html",
    2021: "https://www.chp.gov.hk/en/statistics/data/10/641/642/6934.html",
    2022: "https://www.chp.gov.hk/en/statistics/data/10/641/642/6990.html",
    2023: "https://www.chp.gov.hk/en/statistics/data/10/641/642/7023.html",
    2024: "https://www.chp.gov.hk/en/statistics/data/10/641/642/7053.html",
    2025: "https://www.chp.gov.hk/en/statistics/data/10/641/642/7080.html",
    2026: "https://www.chp.gov.hk/en/statistics/data/10/641/642/7102.html",
}

# Mycoplasma pneumoniae pages
MYCO_URLS = {
    2015: "https://www.chp.gov.hk/en/statistics/data/10/641/642/4824.html",
    2016: "https://www.chp.gov.hk/en/statistics/data/10/641/642/5136.html",
    2017: "https://www.chp.gov.hk/en/statistics/data/10/641/642/6443.html",
    2018: "https://www.chp.gov.hk/en/statistics/data/10/641/642/6791.html",
    2019: "https://www.chp.gov.hk/en/statistics/data/10/641/642/6827.html",
    2020: "https://www.chp.gov.hk/en/statistics/data/10/641/642/6901.html",
    2021: "https://www.chp.gov.hk/en/statistics/data/10/641/642/6938.html",
    2022: "https://www.chp.gov.hk/en/statistics/data/10/641/642/6993.html",
    2023: "https://www.chp.gov.hk/en/statistics/data/10/641/642/7030.html",
    2024: "https://www.chp.gov.hk/en/statistics/data/10/641/642/7062.html",
    2025: "https://www.chp.gov.hk/en/statistics/data/10/641/642/7089.html",
    2026: "https://www.chp.gov.hk/en/statistics/data/10/641/642/7104.html",
}


def fetch_page(url, year):
    """Fetch a CHP page with retry logic."""
    for attempt in range(3):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            return resp.text
        except Exception as e:
            print(f"  Attempt {attempt+1} failed for {year}: {e}")
            time.sleep(2)
    print(f"  FAILED to fetch {year} after 3 attempts")
    return None


def parse_other_respiratory(html, year):
    """Parse 'Other respiratory viruses' table.
    
    Columns vary by year:
    - Pre-2023: no SARS-CoV-2 column
    - 2023+: includes SARS-CoV-2
    - Some years have slightly different column arrangements
    
    We extract: Week, Date, Specimens, Adenovirus (No/%), RSV (No/%),
    Metapneumovirus (No/%), and optionally SARS-CoV-2 (No/%).
    """
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table")
    if not table:
        print(f"  WARNING: No table found for {year}")
        return pd.DataFrame()

    rows = table.find_all("tr")
    data = []

    for row in rows:
        cells = row.find_all(["td", "th"])
        values = [c.get_text(strip=True) for c in cells]

        # Skip header rows and empty rows
        if len(values) < 6:
            continue

        # First cell should be a week number (integer)
        try:
            week = int(values[0])
        except (ValueError, IndexError):
            continue

        date_str = values[1]
        
        # Parse specimens tested
        try:
            specimens = int(values[2].replace(",", ""))
        except (ValueError, IndexError):
            specimens = None

        # Now parse pathogen columns — layout varies by year
        # We'll use a flexible approach: find RSV by scanning for it
        # The typical order is: Adeno (No, %), RSV (No, %), Metapneumo (No, %), ...
        # Starting from index 3
        nums = values[3:]
        
        record = {
            "Year": year,
            "Week": week,
            "Date": date_str,
            "Specimens_Other": specimens,
        }

        # Parse pairs (count, percentage) for each pathogen
        # Typical layout: Adeno_No, Adeno_%, RSV_No, RSV_%, MPV_No, MPV_%, ...
        pathogen_names = ["Adenovirus", "RSV", "Metapneumovirus"]
        
        # Check if SARS-CoV-2 column exists (2023+)
        has_sarscov2 = year >= 2023 or any("sars" in v.lower() or "coronavirus" in v.lower() 
                                            for v in values)
        if has_sarscov2:
            pathogen_names.append("SARS_CoV_2")
        
        pathogen_names.append("Rhinovirus_Enterovirus")

        idx = 0
        for pname in pathogen_names:
            if idx + 1 < len(nums):
                try:
                    count = int(nums[idx].replace(",", ""))
                except ValueError:
                    count = None
                try:
                    pct = float(nums[idx + 1])
                except ValueError:
                    pct = None
                record[f"{pname}_count"] = count
                record[f"{pname}_pct"] = pct
                idx += 2
            else:
                record[f"{pname}_count"] = None
                record[f"{pname}_pct"] = None
                idx += 2

        data.append(record)

    return pd.DataFrame(data)


def parse_parainfluenza(html, year):
    """Parse parainfluenza virus table.
    
    Columns typically: Week, Date, Specimens, PIV1 (No/%), PIV2, PIV3, PIV4, Total.
    Layout may vary.
    """
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table")
    if not table:
        print(f"  WARNING: No table found for parainfluenza {year}")
        return pd.DataFrame()

    rows = table.find_all("tr")
    data = []

    for row in rows:
        cells = row.find_all(["td", "th"])
        values = [c.get_text(strip=True) for c in cells]

        if len(values) < 6:
            continue
        try:
            week = int(values[0])
        except (ValueError, IndexError):
            continue

        date_str = values[1]
        try:
            specimens = int(values[2].replace(",", ""))
        except (ValueError, IndexError):
            specimens = None

        record = {
            "Year": year,
            "Week": week,
            "Date": date_str,
            "Specimens_Para": specimens,
        }

        nums = values[3:]
        # PIV1, PIV2, PIV3, PIV4, then possibly total
        piv_names = ["PIV1", "PIV2", "PIV3", "PIV4"]
        idx = 0
        for pname in piv_names:
            if idx + 1 < len(nums):
                try:
                    count = int(nums[idx].replace(",", ""))
                except ValueError:
                    count = None
                try:
                    pct = float(nums[idx + 1])
                except ValueError:
                    pct = None
                record[f"{pname}_count"] = count
                record[f"{pname}_pct"] = pct
                idx += 2
            else:
                break

        # Total parainfluenza (if present)
        if idx + 1 < len(nums):
            try:
                record["PIV_total_count"] = int(nums[idx].replace(",", ""))
            except ValueError:
                record["PIV_total_count"] = None
            try:
                record["PIV_total_pct"] = float(nums[idx + 1])
            except ValueError:
                record["PIV_total_pct"] = None

        data.append(record)

    return pd.DataFrame(data)


def parse_mycoplasma(html, year):
    """Parse Mycoplasma pneumoniae table."""
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table")
    if not table:
        print(f"  WARNING: No table found for mycoplasma {year}")
        return pd.DataFrame()

    rows = table.find_all("tr")
    data = []

    for row in rows:
        cells = row.find_all(["td", "th"])
        values = [c.get_text(strip=True) for c in cells]

        if len(values) < 4:
            continue
        try:
            week = int(values[0])
        except (ValueError, IndexError):
            continue

        date_str = values[1]
        try:
            specimens = int(values[2].replace(",", ""))
        except ValueError:
            specimens = None

        try:
            mp_count = int(values[3].replace(",", ""))
        except (ValueError, IndexError):
            mp_count = None
        try:
            mp_pct = float(values[4])
        except (ValueError, IndexError):
            mp_pct = None

        data.append({
            "Year": year,
            "Week": week,
            "Date": date_str,
            "Specimens_Myco": specimens,
            "Mycoplasma_count": mp_count,
            "Mycoplasma_pct": mp_pct,
        })

    return pd.DataFrame(data)


def parse_date_range(date_str, year):
    """Convert CHP date string to From/To dates.
    
    Formats seen:
      '29/12/2024 - 04/01'   (cross-year)
      '05/01 - 11/01'        (same year)
      '29/12 - 04/01/2025'   (some pages)
    """
    date_str = date_str.strip()
    # Try to split on ' - ' or '-'
    parts = re.split(r'\s*-\s*', date_str)
    if len(parts) != 2:
        return None, None

    def parse_part(p, default_year):
        p = p.strip()
        # Try DD/MM/YYYY
        try:
            return pd.to_datetime(p, format="%d/%m/%Y")
        except:
            pass
        # Try DD/MM (use default year)
        try:
            return pd.to_datetime(f"{p}/{default_year}", format="%d/%m/%Y")
        except:
            pass
        return None

    from_date = parse_part(parts[0], year)
    to_date = parse_part(parts[1], year)

    # Handle cross-year: if To < From, To is next year
    if from_date and to_date and to_date < from_date:
        to_date = parse_part(parts[1], year + 1)

    return from_date, to_date


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("CHP RESPIRATORY PATHOGEN SCRAPER")
    print("RSV + Parainfluenza + Adenovirus + Metapneumovirus + Mycoplasma")
    print("=" * 70)

    # --- Scrape "Other respiratory viruses" (RSV etc.) ---
    print("\n--- Scraping 'Other respiratory viruses' (RSV, Adeno, MPV) ---")
    other_frames = []
    for year, url in sorted(OTHER_RESP_URLS.items()):
        print(f"  Fetching {year}...", end=" ")
        html = fetch_page(url, year)
        if html:
            df = parse_other_respiratory(html, year)
            print(f"{len(df)} weeks")
            other_frames.append(df)
        time.sleep(1)  # be polite to CHP's server

    other_df = pd.concat(other_frames, ignore_index=True) if other_frames else pd.DataFrame()
    print(f"\n  Total 'other respiratory': {len(other_df)} rows")

    # --- Scrape parainfluenza ---
    print("\n--- Scraping parainfluenza ---")
    para_frames = []
    for year, url in sorted(PARA_URLS.items()):
        print(f"  Fetching {year}...", end=" ")
        html = fetch_page(url, year)
        if html:
            df = parse_parainfluenza(html, year)
            print(f"{len(df)} weeks")
            para_frames.append(df)
        time.sleep(1)

    para_df = pd.concat(para_frames, ignore_index=True) if para_frames else pd.DataFrame()
    print(f"\n  Total parainfluenza: {len(para_df)} rows")

    # --- Scrape Mycoplasma ---
    print("\n--- Scraping Mycoplasma pneumoniae ---")
    myco_frames = []
    for year, url in sorted(MYCO_URLS.items()):
        print(f"  Fetching {year}...", end=" ")
        html = fetch_page(url, year)
        if html:
            df = parse_mycoplasma(html, year)
            print(f"{len(df)} weeks")
            myco_frames.append(df)
        time.sleep(1)

    myco_df = pd.concat(myco_frames, ignore_index=True) if myco_frames else pd.DataFrame()
    print(f"\n  Total mycoplasma: {len(myco_df)} rows")

    # --- Parse dates ---
    print("\n--- Parsing dates ---")
    for df in [other_df, para_df, myco_df]:
        if len(df) > 0 and "Date" in df.columns:
            froms, tos = [], []
            for _, row in df.iterrows():
                f, t = parse_date_range(row["Date"], row["Year"])
                froms.append(f)
                tos.append(t)
            df["From"] = froms
            df["To"] = tos
            df["MidDate"] = df["From"] + (df["To"] - df["From"]) / 2
            n_parsed = df["From"].notna().sum()
            print(f"  Parsed {n_parsed}/{len(df)} dates")

    # --- Save individual datasets ---
    if len(other_df) > 0:
        other_df.to_csv("chp_other_respiratory_2014_2026.csv", index=False)
        print(f"\n  Saved: chp_other_respiratory_2014_2026.csv ({len(other_df)} rows)")
        print(f"  Columns: {list(other_df.columns)}")

    if len(para_df) > 0:
        para_df.to_csv("chp_parainfluenza_2014_2026.csv", index=False)
        print(f"  Saved: chp_parainfluenza_2014_2026.csv ({len(para_df)} rows)")

    if len(myco_df) > 0:
        myco_df.to_csv("chp_mycoplasma_2015_2026.csv", index=False)
        print(f"  Saved: chp_mycoplasma_2015_2026.csv ({len(myco_df)} rows)")

    # --- Merge with flu data if available ---
    print("\n--- Merging with influenza data ---")
    try:
        flu_df = pd.read_csv("flux_data.csv")
        flu_df["From"] = pd.to_datetime(flu_df["From"], format="%d/%m/%Y")
        flu_df["To"] = pd.to_datetime(flu_df["To"], format="%d/%m/%Y")

        # Merge on Year + Week
        combined = flu_df.copy()

        if len(other_df) > 0:
            merge_cols = [c for c in other_df.columns
                          if c not in ["Date", "From", "To", "MidDate"]]
            combined = combined.merge(
                other_df[merge_cols], on=["Year", "Week"], how="left"
            )

        if len(para_df) > 0:
            merge_cols = [c for c in para_df.columns
                          if c not in ["Date", "From", "To", "MidDate"]]
            combined = combined.merge(
                para_df[merge_cols], on=["Year", "Week"], how="left"
            )

        if len(myco_df) > 0:
            merge_cols = [c for c in myco_df.columns
                          if c not in ["Date", "From", "To", "MidDate"]]
            combined = combined.merge(
                myco_df[merge_cols], on=["Year", "Week"], how="left"
            )

        combined.to_csv("chp_all_pathogens_combined.csv", index=False)
        print(f"  Saved: chp_all_pathogens_combined.csv ({len(combined)} rows, {len(combined.columns)} columns)")

    except FileNotFoundError:
        print("  flux_data.csv not found — skipping merge")
        print("  Place flux_data.csv in the same directory and re-run to get the combined file")

    # --- Quick summary ---
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    if len(other_df) > 0 and "RSV_pct" in other_df.columns:
        rsv = other_df.dropna(subset=["RSV_pct"])
        print(f"\n  RSV: {len(rsv)} weeks of data")
        print(f"    Date range: {rsv['From'].min()} to {rsv['To'].max()}")
        print(f"    Mean positivity: {rsv['RSV_pct'].mean():.2f}%")
        print(f"    Max positivity:  {rsv['RSV_pct'].max():.2f}%")
        print(f"    Peak year/week:  {rsv.loc[rsv['RSV_pct'].idxmax(), 'Year']}-W{rsv.loc[rsv['RSV_pct'].idxmax(), 'Week']}")

    if len(para_df) > 0 and "PIV_total_pct" in para_df.columns:
        piv = para_df.dropna(subset=["PIV_total_pct"])
        print(f"\n  Parainfluenza: {len(piv)} weeks of data")
        print(f"    Mean positivity: {piv['PIV_total_pct'].mean():.2f}%")
        print(f"    Max positivity:  {piv['PIV_total_pct'].max():.2f}%")

    if len(myco_df) > 0 and "Mycoplasma_pct" in myco_df.columns:
        mp = myco_df.dropna(subset=["Mycoplasma_pct"])
        print(f"\n  Mycoplasma: {len(mp)} weeks of data")
        print(f"    Mean positivity: {mp['Mycoplasma_pct'].mean():.2f}%")
        print(f"    Max positivity:  {mp['Mycoplasma_pct'].max():.2f}%")

    print(f"\n{'='*70}")
    print("NEXT STEPS:")
    print("  1. Upload chp_other_respiratory_2014_2026.csv to Claude")
    print("  2. Or upload chp_all_pathogens_combined.csv for the full picture")
    print("  3. We'll build the RSV PINN demo for Vijay")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
