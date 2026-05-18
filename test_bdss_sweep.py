from treesimulator.simulate_forest_bdss import generate as gen_bdss, BirthDeathWithSuperSpreadingModel
from treesimulator.simulate_forest_bd import generate as gen_bd, BirthDeathModel
from treesimulator import save_forest
from phylodeep import paramdeep, modeldeep
import pandas as pd
import tempfile, os

pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)

def simulate_bdss_tree(R0, psi, Xss, fss, p, min_tips, max_tips, seed):
    la_n = R0 * psi / ((1 - fss) + fss * Xss)
    la_s = la_n * Xss
    model = BirthDeathWithSuperSpreadingModel(
        la_nn=la_n*(1-fss), la_ns=la_n*fss,
        la_sn=la_s*(1-fss), la_ss=la_s*fss,
        psi=psi, p=p
    )
    result = gen_bdss(models=[model], min_tips=min_tips, max_tips=max_tips, random_seed=seed)
    tree = result[0][0]  # Epidemic -> forest list -> first tree
    tmp = tempfile.NamedTemporaryFile(suffix='.nwk', delete=False, mode='w')
    save_forest([tree], tmp.name)
    return tmp.name, len(tree)

# ============================================
# EXPERIMENT 1: R0 sweep
# ============================================
print("=" * 70)
print("EXPERIMENT 1: R0 SWEEP (Xss=5, fss=0.1, 200-500 tips)")
print("=" * 70)

for R0 in [0.8, 1.2, 2.0, 3.0, 5.0]:
    try:
        path, ntips = simulate_bdss_tree(R0, 0.2, 5.0, 0.1, 0.5, 200, 500, seed=42)
        params = paramdeep.paramdeep(path, proba_sampling=0.5, model='BDSS', representation='FULL')
        est = params['R_naught'].values[0]
        err = abs(est - R0) / R0 * 100
        print(f"  R0={R0:.1f}  est={est:.2f}  err={err:.1f}%  tips={ntips}")
        os.unlink(path)
    except Exception as e:
        print(f"  R0={R0:.1f}  FAILED: {e}")

# ============================================
# EXPERIMENT 2: Tree size sweep
# ============================================
print("\n" + "=" * 70)
print("EXPERIMENT 2: TREE SIZE (R0=2.0, Xss=5, fss=0.1)")
print("=" * 70)

for min_t, max_t in [(20, 50), (50, 100), (100, 200), (200, 500)]:
    try:
        path, ntips = simulate_bdss_tree(2.0, 0.2, 5.0, 0.1, 0.5, min_t, max_t, seed=42)
        params = paramdeep.paramdeep(path, proba_sampling=0.5, model='BDSS', representation='FULL')
        r0_est = params['R_naught'].values[0]
        xss_est = params['X_transmission'].values[0]
        fss_est = params['Superspreading_individuals_fraction'].values[0]
        print(f"  tips={ntips:4d}  R0: 2.0->{r0_est:.2f}  "
              f"Xss: 5.0->{xss_est:.1f}  fss: 0.10->{fss_est:.3f}")
        os.unlink(path)
    except Exception as e:
        print(f"  tips={min_t}-{max_t}  FAILED: {e}")

# ============================================
# EXPERIMENT 3: Model selection
# ============================================
print("\n" + "=" * 70)
print("EXPERIMENT 3: MODEL SELECTION (BD vs BDSS)")
print("=" * 70)

print("\n  BDSS tree (superspreading present):")
path, ntips = simulate_bdss_tree(2.0, 0.2, 5.0, 0.1, 0.5, 200, 500, seed=42)
mp = modeldeep.modeldeep(path, proba_sampling=0.5, representation='FULL')
print(f"    tips={ntips}  BD={mp['Probability_BD'].values[0]:.4f}  "
      f"BDEI={mp['Probability_BDEI'].values[0]:.4f}  BDSS={mp['Probability_BDSS'].values[0]:.4f}")
os.unlink(path)

print("\n  BD tree (NO superspreading):")
bd_model = BirthDeathModel(la=0.4, psi=0.2, p=0.5)
result_bd = gen_bd(models=[bd_model], min_tips=200, max_tips=500, random_seed=42)
tree_bd = result_bd[0][0]  # same structure
tmp_bd = tempfile.NamedTemporaryFile(suffix='.nwk', delete=False, mode='w')
save_forest([tree_bd], tmp_bd.name)
ntips_bd = len(tree_bd)
mp_bd = modeldeep.modeldeep(tmp_bd.name, proba_sampling=0.5, representation='FULL')
print(f"    tips={ntips_bd}  BD={mp_bd['Probability_BD'].values[0]:.4f}  "
      f"BDEI={mp_bd['Probability_BDEI'].values[0]:.4f}  BDSS={mp_bd['Probability_BDSS'].values[0]:.4f}")
os.unlink(tmp_bd.name)

print("\nDONE")
