"""
Generate a BDSS tree with KNOWN parameters,
then see if PhyloDeep can recover them.
"""
from treesimulator.simulate_forest_bdss import generate, BirthDeathWithSuperSpreadingModel
from treesimulator import save_forest
from phylodeep import paramdeep, modeldeep
import tempfile, os

# ============================================
# SET TRUE PARAMETERS
# ============================================
# We want:
#   R0 ~ 2.0
#   Infectious period = 5 (1/psi)
#   Xss = 5.0 (superspreaders transmit 5x more)
#   fss = 10% superspreaders
#
# BDSS parameterization:
#   psi = removal rate = 1/infectious_period = 0.2
#   p = sampling probability
#   fss determines the ratio of la_nn vs la_ss
#   la_nn = base transmission rate for normal spreaders
#   la_ns = la_nn (normal infects, creates superspreader at rate fss)
#   la_sn = la_nn * Xss
#   la_ss = la_nn * Xss

psi = 0.2       # removal rate -> infectious period = 5
p = 0.5         # sampling probability
R0 = 2.0
Xss = 5.0       # superspreader transmission multiplier
fss = 0.10      # 10% are superspreaders

# Compute transmission rates
# R0 = ((1-fss)*la_n + fss*la_s) / psi  (approximate)
# la_n = base rate, la_s = Xss * la_n
# R0 = la_n * ((1-fss) + fss*Xss) / psi
la_n = R0 * psi / ((1 - fss) + fss * Xss)
la_s = la_n * Xss

print("=== TRUE PARAMETERS ===")
print(f"  R0 = {R0}")
print(f"  Infectious period = {1/psi}")
print(f"  Xss = {Xss}")
print(f"  fss = {fss}")
print(f"  la_n = {la_n:.4f}, la_s = {la_s:.4f}, psi = {psi}")

# ============================================
# SIMULATE TREE
# ============================================
model = BirthDeathWithSuperSpreadingModel(
    la_nn=la_n * (1 - fss),
    la_ns=la_n * fss,
    la_sn=la_s * (1 - fss),
    la_ss=la_s * fss,
    psi=psi,
    p=p
)

print("\nSimulating BDSS tree (200-500 tips)...")
forest, _, _, _ = generate(
    models=[model],
    min_tips=200,
    max_tips=500,
    random_seed=42
)

tree = forest[0]
n_tips = len(tree)
print(f"  Generated tree with {n_tips} tips")

# Save to temp file
tmp = tempfile.NamedTemporaryFile(suffix='.nwk', delete=False, mode='w')
save_forest([tree], tmp.name)
print(f"  Saved to {tmp.name}")

# ============================================
# RUN PHYLODEEP ON SIMULATED TREE
# ============================================
print("\n=== PHYLODEEP MODEL SELECTION ===")
model_probs = modeldeep.modeldeep(tmp.name, proba_sampling=p, representation='FULL')
print(model_probs)

print("\n=== PHYLODEEP PARAMETER ESTIMATION (BDSS) ===")
params = paramdeep.paramdeep(tmp.name, proba_sampling=p, model='BDSS', representation='FULL')
import pandas as pd
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
print(params)

print("\n=== COMPARISON ===")
print(f"  R0:   true={R0:.2f}  estimated={params['R_naught'].values[0]:.2f}")
print(f"  Inf:  true={1/psi:.1f}  estimated={params['Infectious_period'].values[0]:.2f}")
print(f"  Xss:  true={Xss:.1f}  estimated={params['X_transmission'].values[0]:.2f}")
print(f"  fss:  true={fss:.2f}  estimated={params['Superspreading_individuals_fraction'].values[0]:.4f}")

os.unlink(tmp.name)
