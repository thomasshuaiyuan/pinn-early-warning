# Cross-Pathogen R(t) Onset Detection — Hong Kong 2014-2026

Code and data for "Surveillance-based R(t) estimation for respiratory pathogen onset detection: a retrospective cross-pathogen evaluation of influenza and RSV in Hong Kong, 2014-2026"

Yuan T, Dhanasekaran V. School of Public Health, The University of Hong Kong and HKU-Pasteur Research Pole.

## Data
- flux_data.csv — CHP Flu Express (638 weeks, 31 variables)
- chp_respiratory_cleaned.csv — CHP RSV and other respiratory viruses (641 weeks)
- data_dictionary_flu_express.csv — Variable definitions for all 31 flu variables
- supplementary_table_S1_seasons.csv — Season definitions with start/end dates

## Primary analysis scripts
- seir_pinn_v6.py — SEIR-PINN with corrected onset definition
- pinn_gamma_sensitivity.py — Recovery rate sensitivity (gamma 0.1/0.2/0.33)
- pinn_multi_restart.py — Multi-seed stability analysis (5 seeds)
- epiestim_admissions.py — EpiEstim on 6 signals x 8 seasons
- epiestim_rsv.py — EpiEstim on 10 RSV seasons
- epiestim_si_sensitivity.py — SI sensitivity (20 configs x 6 seasons)
- simulation_study.py — Synthetic epidemic simulation (50 replicates x 6 scenarios)
- snr_analysis.py — Signal-to-noise ratio per season
- preonset_analysis.py — Pre-onset amplification with variability
- remaining_analyses.py — Non-season sensitivity and CI-based onset
- final_supplementary.py — COVID exclusion, scraper validation, peak detection
- pseudo_prospective.py — Pseudo-prospective evaluation
- generate_figures.py — Manuscript figures 1-4

## Environment
Requires conda env pinn: Python 3.11, PyTorch 2.2.2, numpy, scipy, pandas, matplotlib. See environment.yml.
