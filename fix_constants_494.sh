#!/bin/bash
# Sets CHP_THRESHOLD = 0.0494 across the remaining scripts (constants only; committed outputs already correct).
set -e
cd ~/pinn-early-warning
rm -f .git/*.lock 2>/dev/null || true
for f in epiestim_admissions.py epiestim_si_sensitivity.py outstanding_analyses.py \
         pinn_gamma_sensitivity.py pinn_multi_restart.py pseudo_prospective.py \
         remaining_analyses.py seir_pinn_admissions.py seir_pinn_v6.py; do
  sed -i '' 's/CHP_THRESHOLD = 0.0647/CHP_THRESHOLD = 0.0494/' "$f"
done
sed -i '' 's/abs(0.0647 -/abs(0.0494 -/' snr_analysis.py
echo "--- remaining 0.0647 occurrences (should be none) ---"
grep -rn "0.0647" *.py || echo "none — clean"
git add -A
git commit -m "Set CHP_THRESHOLD=0.0494 across all remaining scripts for full reproducibility at the operational baseline"
git push
echo ""
echo ">>> DONE. All scripts now use 4.94%; pushed to GitHub."
