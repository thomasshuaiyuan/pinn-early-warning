# Verification brief: three suspected estimator defects in the early-warning analysis

**Prepared 15 October 2026. For an independent session that did not produce these findings.**

**Treat every claim in this document as unverified until you reproduce it.** Nothing here has
been sent to Vijay. No code or manuscript file has been changed. The purpose of this brief is a
single question: are the three defects below real, and if so what is their magnitude?

---

## 0. Why this needs an independent pass

Three model-generated audits of the session record converged on two of these findings. **That
convergence is weak evidence, not strong.** The passes shared context, inspected the same
artifacts, and later passes read earlier conclusions; the near-identical wording of the
amplitude finding across all three is consistent with one pass finding it and two inheriting it.

A fourth pass that reads this document and agrees adds nothing. What adds something is
re-deriving each number from the code and the data, and reporting any that do not reproduce.

This project has twice adopted an external finding as verified without re-derivation and been
wrong — a fabricated quotation attributed to Featherstone et al. 2022 on 8 October, and a Table 1
column transposition promoted into the v10 revision brief as "F-1 (verified, blocking)" on
14 October. Both looked authoritative. Assume this document can be wrong in the same way.

---

## 1. Where the code is

Local working copy, connected folder: `/Users/mac/pinn-early-warning`
GitHub: `thomasshuaiyuan/pinn-early-warning` (not reachable from the session that wrote this;
findings below come from the local copy only — **confirm the local copy matches the remote**)

Files that matter:

- `simulation_study.py`
- `epiestim_admissions.py`
- `epiestim_rsv.py`
- `epiestim_si_sensitivity.py`
- `2_results/simulation_study_results.csv` (also in the OneDrive folder `Thomas early-warning/2_results/`)

Manuscript under review: `2026-09-26_early-warning_v9.docx`, MD5 `9c1d41767d1f1c8bb3c2832d3d3b7c49`,
in OneDrive `Thomas early-warning/3_docs/`.

---

## 2. Claim A — the simulation's amplitude arm cancels its own manipulation

**What the manuscript says.** Results, Simulation study: EpiEstim recovered R(t) with median
r = 0.72 across the perfect, scaled and filtered scenarios (range 0.71 to 0.73), against 0.22 for
noise and 0.25 for delay. The Highlights carry "Low-amplitude laboratory signals degraded both
estimators in the same direction."

**What the code appears to do.** In `simulation_study.py`:

```
line 113-114   elif scenario == "scaled":
                   observed = weekly_I * rng.uniform(0.10, 0.20)
...
line 129-130   scale_factor = 1000 / max(observed.max(), 1e-10)
               pseudo_counts = np.round(observed * scale_factor).astype(int)
```

**The suspected defect.** Multiplying the series by a constant c and then dividing by its own
maximum returns the identical series. The scaled arm is therefore the perfect arm with a
different seed, and the simulation never varied amplitude.

**How to falsify.** Run the scaled and perfect arms on the *same* seed and compare
`pseudo_counts` element-wise. If they are identical, the manipulation is cancelled. If they
differ, say how and by how much — integer rounding after rescaling is the only plausible
residual and should be negligible.

**What follows if it holds.** The simulation is silent on amplitude. It cannot be cited as
evidence that amplitude degrades estimation (the manuscript's framing) **or** that amplitude is
harmless and SNR is the real mechanism (the external review's counter-framing). Both readings
would need withdrawing. What the simulation does legitimately show is that additive noise,
reporting delay and detection-thresholding degrade recovery.

---

## 3. Claim B — the weekly serial-interval discretisation discards most of the influenza distribution

**What the manuscript says.** Methods, EpiEstim R(t) estimation: pathogen-specific serial
intervals of mean 3.0 days (SD 1.5) for influenza and mean 7.5 days (SD 3.5) for RSV.

**What the code appears to do.** The same function appears in four files
(`simulation_study.py` ~line 20, `epiestim_admissions.py` ~line 45, `epiestim_rsv.py` ~line 49,
`epiestim_si_sensitivity.py` ~line 27):

```python
def discretized_si(mean_si, sd_si, max_t, time_unit=7.0):
    shape = (mean_si / sd_si) ** 2
    scale = sd_si ** 2 / mean_si
    si = np.zeros(max_t)
    for t in range(1, max_t):                    # note: starts at 1, si[0] stays 0
        lo = (t - 0.5) * time_unit               # t=1 -> 3.5 days
        hi = (t + 0.5) * time_unit               # t=1 -> 10.5 days
        si[t] = gamma.cdf(hi, ...) - gamma.cdf(max(0, lo), ...)
    si /= si.sum()                               # renormalise what survived
    return si
```

The first bin begins at 3.5 days. All probability mass below 3.5 days is dropped, then the
remainder is renormalised to sum to 1.

**Reproduce with this — it needs no data:**

```python
from scipy.stats import gamma as G
import numpy as np

def audit(mean_si, sd_si, max_t=20, tu=7.0):
    shape = (mean_si / sd_si) ** 2
    scale = sd_si ** 2 / mean_si
    si = np.zeros(max_t)
    for t in range(1, max_t):
        si[t] = G.cdf((t + .5) * tu, a=shape, scale=scale) \
              - G.cdf(max(0, (t - .5) * tu), a=shape, scale=scale)
    dropped = 1 - si.sum()
    n = si / si.sum()
    eff_mean_days = sum(t * n[t] for t in range(max_t)) * 7
    return dropped, n[1], eff_mean_days

print(audit(3.0, 1.5))   # influenza as specified
print(audit(7.5, 3.5))   # RSV as specified
```

**Values obtained in the pass that wrote this brief.** Confirm or refute each.

| | stated mean | mass dropped | si[1] | effective mean |
|---|---|---|---|---|
| Influenza | 3.0 d | **68.5%** | 0.9985 | **7.01 d** |
| RSV | 7.5 d | 9.9% | 0.8002 | 8.50 d |

**What follows if it holds.** Every influenza R(t) series in the paper ran with a degenerate
serial interval — effectively a point mass at one week — rather than the 3.0-day distribution the
Methods describe. RSV retains a genuine shape. The two pathogens are therefore estimated by
structurally different instruments, which compounds the comparability problem the paper already
flags rather than sitting beside it. Reported day-level leads are affected; the direction and
size of the change is not predictable from this analysis alone and needs a rerun.

---

## 4. Claim C — the serial-interval sensitivity analysis may vary nothing

**What the manuscript says.** Results: "Onset timing was robust to serial interval assumptions:
across 20 configurations (5 SI means × 4 window widths) applied to all 6 seasons, all
configurations detected onset in every season." Lead-time SD 3.1–11.4 days, mean 6.8. Table S4.

**What the code appears to do.** `epiestim_si_sensitivity.py` lines 61–63:

```python
SI_MEANS = [2.0, 2.5, 3.0, 3.5, 4.0]
SI_SDS   = None          # SD set to mean * 0.5 for each
WINDOWS  = [3, 4, 5, 6]
```

**The suspected defect.** Run the snippet in §3 across that grid. The pass that wrote this brief
obtained si[1] between 0.9867 and 1.0000 and effective means between 7.00 and 7.09 days for all
five SI settings — i.e. the five serial intervals are the same distribution after discretisation.

**What follows if it holds.** The sensitivity analysis varied the window (4 values) and not the
serial interval, so there were four distinct configurations rather than twenty, and "robust to
serial interval assumptions" is an arithmetic consequence of the discretisation rather than a
finding. This claim is load-bearing in the Results and in Table S4.

**This specific point was not raised by any of the three prior audits.** It is the one most likely
to be wrong, and the one worth checking first.

---

## 5. Claim D — the admissions estimator returns R = 5 on zero input

`epiestim_admissions.py` line 60 onward:

```python
def estimate_R(incidence, si, window=4, prior_shape=1.0, prior_rate=0.2):
    ...
    post_shape = prior_shape + sum_I
    post_rate  = prior_rate  + sum_L
```

With an all-zero window the gamma posterior mean is 1.0 / 0.2 = 5.0. Confirm by calling
`estimate_R` on a zero vector.

**What follows if it holds.** A channel with no admissions returns R = 5, which the onset rule
("crosses 1.0 from below") cannot distinguish from growth, and which plausibly relates to the
degenerate 12–17y and 6–11y fits the Methods already flag (max R(t) > 100,000 in 2014/15 and
2015/16). Whether this is the mechanism behind those specific fits is **not** established here
and should be tested rather than assumed.

---

## 6. Findings from earlier passes that this brief treats as settled — re-check if cheap

**Verified in the pass that wrote this brief:**

- Reference [8] in v9 is Lessler J, Reich NG, Brookmeyer R, et al., *Incubation periods of acute
  respiratory viral infections: a systematic review*, Lancet Infect Dis 2009;9(5):291–300. It is
  cited in Methods for the influenza serial interval and in Results for a 5-day infectious
  period. It contains neither.
- Table 1's column order is `Season | Peak% | Thresh. | EpiEstim | Epi lead | PINN lead | Adm
  lead | Adm sig. | Type`, confirmed because Table 2 independently gives CHP onset 2014-12-24 for
  2014/15 and that date is Table 1's third field. The 2025-sum row (Thresh 07-02, EpiEstim 04-02,
  lead +91) is therefore internally consistent — 2 April to 2 July is 91 days. **The external
  review's finding B1, and the v10 brief's "F-1 (verified, blocking)", are wrong.** The RSV column
  gives leads of +35, −21, −28, −28, −14, −28, +49, +133, −28, +91: four positive of ten, median
  −17.5, matching the Abstract as printed.
- SNR ranges overlap heavily (influenza 6.8–26.4, RSV 6.1–21.5), so the external review's claim
  that SNR is "nearly collinear with pathogen" is not supported by the paper's own numbers.
- The 2024/25 admissions-minus-positivity difference is 119 − 49 = 70 from Table 1, against +63
  in the Results text. One of the two is wrong; the CSV decides.

**Claimed by earlier passes and NOT verified here. Treat as open:**

- In 6 of 10 RSV seasons the threshold crossing precedes EpiEstim's first estimable week, making a
  negative lead structurally unavoidable.
- The committed sensitivity tally is 45/48 (37/40 on admissions channels), not 52/56.
- The within-pathogen SNR test and the quoted logistic interval [−0.088, 0.515] are absent from
  the committed scripts.
- The influenza and RSV PINNs use different onset rules.
- UKHSA's 4–6.2-day figure concerns RT-PCR viral clearance and is not a direct estimate of an SEIR
  infectious period, so it does not by itself replace the Lessler citation.

---

## 7. What to report back

For each of Claims A–D: **reproduces / does not reproduce / could not test**, with the command or
calculation that decided it. Where a claim reproduces, state the magnitude you obtained rather
than confirming the one above.

Then, and only for claims that reproduce: what is the minimum rerun that would produce correct
numbers, and which reported values in the manuscript, figures and Table S4 would change.

**Do not** propose manuscript wording. Several of the affected passages — the Abstract's framing,
the Highlights — are the supervisor's own inserted prose, and under his 25 September working
practices they are not altered without asking him first. The code defects and the reruns belong to
the student; the framing consequences belong to him. Keep the two separate.

**Do not** open a new analysis arm, add a dataset, or extend scope. If a defect holds, the
deliverable is a corrected number, not a larger study.
