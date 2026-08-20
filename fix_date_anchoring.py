"""
Date-Anchoring Fix (Vijay Round 2, Item 1)
============================================
The bug: onset dates computed as pd.to_datetime(start) + timedelta
but t_max computed from season["MidDate"].min()
If start != MidDate.min(), dates shift by the difference (0-6 days)

Fix: replace pd.to_datetime(start) with season["MidDate"].min()
in all PINN scripts that compute onset dates.

This script:
1. Patches pinn_gamma_sensitivity.py
2. Patches pinn_multi_restart.py  
3. Reruns both and saves corrected CSVs

Run: python fix_date_anchoring.py
"""

import re
import os
import subprocess

SCRIPTS_TO_FIX = [
    "pinn_gamma_sensitivity.py",
    "pinn_multi_restart.py",
]

def fix_script(filepath):
    with open(filepath, 'r') as f:
        code = f.read()
    
    # Count occurrences of the bug
    bug_pattern = "pd.to_datetime(start) + pd.to_timedelta"
    count = code.count(bug_pattern)
    
    if count > 0:
        fix = 'season["MidDate"].min() + pd.to_timedelta'
        code = code.replace(bug_pattern, fix)
        with open(filepath, 'w') as f:
            f.write(code)
        print(f"  Fixed {filepath}: {count} occurrence(s)")
        return True
    else:
        # Check if already fixed
        if 'season["MidDate"].min() + pd.to_timedelta' in code:
            print(f"  {filepath}: already fixed")
        else:
            # Check for alternative patterns
            alt = "pd.to_datetime(start)"
            alt_count = code.count(alt)
            if alt_count > 0:
                print(f"  WARNING: {filepath} has {alt_count} uses of pd.to_datetime(start)")
                print(f"  Manual review needed")
            else:
                print(f"  {filepath}: no date-anchoring pattern found")
        return False

print("=" * 60)
print("DATE-ANCHORING FIX")
print("=" * 60)

any_fixed = False
for script in SCRIPTS_TO_FIX:
    if os.path.exists(script):
        fixed = fix_script(script)
        any_fixed = any_fixed or fixed
    else:
        print(f"  {script}: FILE NOT FOUND")

if any_fixed:
    print("\nScripts patched. Now rerun:")
    print("  python pinn_gamma_sensitivity.py")
    print("  python pinn_multi_restart.py")
    print("\nThen commit the fixed scripts AND new CSV outputs.")
else:
    print("\nNo changes needed - scripts already patched or pattern not found.")
    print("If results still show old numbers, the scripts may use a different pattern.")
    print("Check manually for any use of 'start' as a date anchor.")
