"""
Paper 2 proof of concept:
Same epidemic -> two R(t) estimates -> do they agree?
"""
from treesimulator.simulate_forest_bdss import generate, BirthDeathWithSuperSpreadingModel
from treesimulator import save_forest
from phylodeep import paramdeep
import numpy as np
import tempfile

# ============================================
# SIMULATE EPIDEMIC
# ============================================
R0_true, psi, Xss, fss, p = 2.0, 0.2, 5.0, 0.1, 0.5
la_n = R0_true * psi / ((1 - fss) + fss * Xss)
la_s = la_n * Xss
model = BirthDeathWithSuperSpreadingModel(
    la_nn=la_n*(1-fss), la_ns=la_n*fss,
    la_sn=la_s*(1-fss), la_ss=la_s*fss,
    psi=psi, p=p
)

result = generate(models=[model], min_tips=200, max_tips=500, random_seed=42)
tree = result[0][0]

print("=" * 60)
print("PAIRED ESTIMATION: SAME EPIDEMIC, TWO METHODS")
print("=" * 60)
print(f"\nTrue parameters: R0={R0_true}, inf_period={1/psi}, Xss={Xss}, fss={fss}")
print(f"Tree tips: {len(tree)}")

# ============================================
# METHOD 1: PHYLOGENETIC (PhyloDeep)
# ============================================
tmp = tempfile.NamedTemporaryFile(suffix='.nwk', delete=False, mode='w')
save_forest([tree], tmp.name)

import pandas as pd
pd.set_option('display.max_columns', None)
params = paramdeep.paramdeep(tmp.name, proba_sampling=p, model='BDSS', representation='FULL')
R0_phylo = params['R_naught'].values[0]

print(f"\n--- METHOD 1: PhyloDeep (from tree shape) ---")
print(f"  R0 = {R0_phylo:.3f}")
print(f"  Infectious period = {params['Infectious_period'].values[0]:.2f}")

# ============================================
# METHOD 2: SURVEILLANCE (from incidence curve)
# ============================================
# Extract tip times = sampling times
tip_times = np.array([tree.get_distance(leaf) for leaf in tree.iter_leaves()])

# Bin into weekly incidence
bin_width = 1.0  # 1 time unit bins
bins = np.arange(tip_times.min(), tip_times.max() + bin_width, bin_width)
incidence, edges = np.histogram(tip_times, bins=bins)

# Simple exponential growth rate estimation
# During growth phase, incidence ~ exp(r*t)
# R0 ~ 1 + r * infectious_period (for SIR)
# Use the last 20 bins where growth is clearest
growth_phase = incidence[-20:]
times_growth = np.arange(len(growth_phase))

# Fit log-linear model to growth phase
valid = growth_phase > 0
if valid.sum() > 2:
    log_inc = np.log(growth_phase[valid])
    t_valid = times_growth[valid]
    # Linear regression on log(incidence) vs time
    slope, intercept = np.polyfit(t_valid, log_inc, 1)
    r_growth = slope  # exponential growth rate
    
    # Wallinga-Lipsitch approximation: R = 1 + r * D
    # where D = infectious period
    D_true = 1.0 / psi
    R0_surv = 1 + r_growth * D_true
    
    print(f"\n--- METHOD 2: Surveillance (from incidence curve) ---")
    print(f"  Growth rate r = {r_growth:.4f}")
    print(f"  R0 (Wallinga-Lipsitch) = {R0_surv:.3f}")
    print(f"  (using true infectious period = {D_true})")
else:
    R0_surv = None
    print("\n--- METHOD 2: Not enough data for growth rate ---")

# ============================================
# COMPARISON
# ============================================
print(f"\n{'=' * 60}")
print(f"COMPARISON")
print(f"{'=' * 60}")
print(f"  True R0:         {R0_true:.3f}")
print(f"  PhyloDeep R0:    {R0_phylo:.3f}  (error: {abs(R0_phylo-R0_true)/R0_true*100:.1f}%)")
if R0_surv:
    print(f"  Surveillance R0: {R0_surv:.3f}  (error: {abs(R0_surv-R0_true)/R0_true*100:.1f}%)")
    print(f"  Agreement:       {abs(R0_phylo-R0_surv):.3f} difference")

import os
os.unlink(tmp.name)
