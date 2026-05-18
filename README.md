# Cross-Pathogen R(t) Onset Detection — Hong Kong 2014–2026

Code and data for "Surveillance-based R(t) estimation for respiratory pathogen onset detection: a cross-pathogen evaluation of influenza and RSV in Hong Kong, 2014–2026"

## Data
- `flux_data.csv` — CHP Flu Express (638 weeks, 31 variables)
- `chp_respiratory_cleaned.csv` — CHP RSV and other respiratory viruses (641 weeks)

## Analysis scripts
- `epiestim_admissions.py` — EpiEstim on 6 signals (positivity + 5 admission age groups)
- `epiestim_rsv.py` — EpiEstim on 10 RSV seasons
- `seir_pinn_v6.py` — PINN with corrected onset definition + subtype stratification
- `seir_pinn_admissions.py` — PINN on admission signals (tests signal vs structural bottleneck)
- `seir_pinn_rsv.py` — PINN on RSV
- `chp_flu_explorer.py` — Data exploration and season identification

## Results
- `validation_results_v6.csv` — PINN v6 results (honest onset definition)
- `epiestim_admissions_results.csv` — Admissions vs positivity comparison
- `epiestim_rsv_results.csv` — RSV EpiEstim results
- `master_table_18_seasons.csv` — Unified table for manuscript
