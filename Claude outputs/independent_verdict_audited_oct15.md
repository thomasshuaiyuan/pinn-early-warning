# Audit of the independent verdict on the four estimator defects

**15 October 2026.** Audits `claude/verification_brief_estimator_defects_oct15.md` (the brief) and
the independent session's verdict returned against it. Nothing has been sent to Vijay. No code or
manuscript file has been changed.

This record exists because Part I's rule applies one level up: an independent pass's findings are
claims carrying the same burden as the claims they assess, and that includes its non-existence
claims. One of them does not survive.

---

## 1. Verdict on the verdict

All four defects stand. Three corrections the independent pass made to the brief are accepted.
One finding it added is **withdrawn** — it was a non-existence claim made against one output file
of several, which is the exact failure mode Part I names. One finding it added reproduces exactly.
Two consequences neither pass reached are established below, and one of them changes reported
dates rather than reported framing.

---

## 2. Corrections to the brief, accepted

**C1 — the scaled branch consumes an extra RNG draw.** Confirmed at `simulation_study.py:113`:
`observed = weekly_I * rng.uniform(0.10, 0.20)` advances the generator, so the subsequent Poisson
stream differs from the perfect arm's. A naive same-seed element-wise comparison, which §2 of the
brief proposed as the falsification test, would show a difference and would be read as refuting
Claim A. **The brief's falsification test was wrong** and would have produced a false clearance.

**C2 — Claim C is identical outcomes, not identical distributions.** Max total-variation distance
between the five discretised SI vectors is 0.01330, so they are not literally the same vector. The
brief overstated it. The outcome-level claim is nonetheless confirmed directly from the committed
output rather than from the discretisation arithmetic — see §4.

**C3 — the admissions onset rule is "first week R(t) > 1", not "crossing from below".** Confirmed
at `epiestim_admissions.py:124–126`: `onset_rows = rt_df[rt_df["Rt_mean"] > 1.0]`, then
`.iloc[0]`. There is no crossing test. This makes Claim D worse, not milder, and §5 below is the
consequence.

---

## 3. One finding added by the independent pass is withdrawn

The pass reported that the manuscript's ">100,000" does not reproduce from committed outputs,
giving committed maxima of 49,005 / 26,005 / 27,505.

Those three values are correct **for `epiestim_admissions_results.csv`**. They are not the only
committed maxima. `epiestim_fixed_scaling.csv`, written by `wilcoxon_admissions.py` and
`outstanding_analyses.py`, carries:

| season | signal | best_Rt |
|---|---|---|
| 2015/16 | 12-17y | **144,357.96** |
| 2014/15 | 12-17y | **125,302.20** |
| 2014/15 | 6-11y | 77,717.10 |

Two values above 100,000, in exactly the two seasons the Methods name. **The manuscript's
">100,000 in 2014/15 and 2015/16" reproduces.** The non-reproduction claim rested on one file and
did not name the surface it searched.

Surfaces queried for this: every `*.csv` under `/Users/mac/pinn-early-warning` (21 files), grepped
for `best_Rt`/`Rt_max`/`max_Rt`. Not queried: the GitHub remote (not reachable from this session),
the project store, any other machine.

---

## 4. One finding added by the independent pass reproduces exactly

The reported SI-sensitivity lead-time SDs are deflated by fivefold duplication. Recomputed from
`epiestim_si_sensitivity_flu.csv` (120 rows = 6 seasons × 5 SI means × 4 windows):

| season | SD over all 20 configs | SD over 4 distinct windows |
|---|---|---|
| 2014/15 | 3.1 | 3.5 |
| 2015/16 | 8.8 | 9.9 |
| 2018/19 | 3.6 | 4.0 |
| 2023 S | 11.4 | 12.8 |
| 2023/24 | 8.0 | 9.0 |
| 2024/25 | 6.0 | 6.7 |
| **range / mean** | **3.1–11.4, 6.81** | **3.5–12.8, 7.66** |

The left column is the manuscript's printed "3.1 to 11.4 days, mean 6.8". Confirmed.

**And this file settles Claim C at the data level, independent of the discretisation arithmetic.**
In all six seasons, for every one of the four windows, all five SI means return the *identical*
onset date. The grid has four distinct configurations, not twenty. "Robust to serial interval
assumptions" is not a finding; no serial interval was varied in a way the estimator could see.

---

## 5. Two consequences neither pass reached

**5a. The degenerate fits are prior-dominated, provably.** All three degenerate values satisfy
`best_Rt × 0.2` = an exact integer: 49,005 → 9,801; 26,005 → 5,201; 27,505 → 5,501. Since
`post_rate = prior_rate + sum_L` and `prior_rate = 0.2`, this requires `sum_L = 0` exactly — zero
total infectiousness across the window. The posterior is `(1 + sum_I) / 0.2`, with the prior alone
setting the denominator. Claim D's mechanism is confirmed, and it is not limited to the zero-input
case the brief described: it fires whenever the preceding weeks are empty, whatever the current
week holds.

**5b. The reported onsets for those channels fall in runs of zero admissions.** Combining 5a with
correction C3 — "first week R(t) > 1", no crossing test — the estimator returns a large R on the
first estimable week of an empty channel, and the onset rule accepts it. Checked against
`flux_data.csv`:

| season | channel | reported onset | admissions that week and the 3 before |
|---|---|---|---|
| 2014/15 | Adm_6_11 | 2014-11-12 | 0, 0, 0, 0 (first nonzero 2014-12-10) |
| 2014/15 | Adm_12_17 | 2014-10-29 | 0, 0, 0, 0 (first nonzero 2014-12-10) |
| 2015/16 | Adm_12_17 | 2015-11-04 | 0, 0, 0, 0 (first nonzero 2015-12-09) |

These are not noisy onsets. They are onsets declared on weeks with no admissions at all, four to
five weeks before the channel records its first case. **This changes reported dates, not only
reported framing**, and it is the only one of the four defects with that property.

---

## 6. The brief's §2 reasoning on Claim A was right for the wrong reason

The rescale is `scale_factor = 1000 / observed.max()`, applied before `rng.poisson`. So every arm
— perfect, scaled, noisy, delayed, filtered, thresholded — enters the Poisson step with a peak of
exactly 1000. Poisson observation noise is a function of the mean, so **the rescale pins the
signal-to-noise ratio across arms by construction**, which is the quantity the amplitude
manipulation existed to vary.

This disposes of both framings at once. The manuscript cannot cite the simulation as evidence that
amplitude degrades estimation. The external review cannot cite it for the counter-claim that SNR
rather than amplitude is the mechanism. The simulation holds SNR fixed on purpose and is silent on
both.

---

## 7. Spread of the defective discretiser, with the surfaces named

The function has **two names**, which is why an earlier grep on one name returned an incomplete
list. `discretized_si` and `discretized_serial_interval` are the same body.

Under `/Users/mac/pinn-early-warning` (8 files): `simulation_study.py`, `pseudo_prospective.py`,
`remaining_analyses.py`, `outstanding_analyses.py`, `epiestim_si_sensitivity.py`,
`epiestim_admissions.py`, `epiestim_rsv.py`, `generate_figures.py`.

Under `/Users/mac/HKU-influenza` (1 file): `scripts/epiestim_si_sensitivity.py`, MD5-identical to
the `pinn-early-warning` copy (`01abd115b9b66411e2580dfe0239008d`).

**Paper 3 is clean.** The only specification-curve scripts present anywhere under the connected
folders are `paper3_v8_agecross_diagnostic.py` (76 lines) and `paper3_v8_threshold_audit.py`
(26 lines). Both are threshold-crossing arithmetic on `AandB_proportion`. Neither imports scipy,
neither references a serial interval, neither computes R(t). The specification curve's EpiEstim
method family, if it exists, is not in these two files.

**Surfaces queried**: all four connected folders (`HKU-influenza`,
`OneDrive-TheUniversityofHongKong-Connect`, `OneDrive.localized`, `pinn-early-warning`), by
recursive grep on the two function names, on the discretiser's distinctive expressions
(`t - 0.5`, `time_unit`, `gamma.cdf`, `gamma_dist.cdf`), and by filename pattern for
`*paper3*`, `*speccurve*`, `*spec_curve*`. **Not queried**: the GitHub remotes (not reachable from
this session), the project store, the `avoidable-vs-irreducible` and `pathogen-pipeline`
repositories, any machine other than this one. The Paper 3 clearance is therefore a statement
about the two committed scripts on this machine, not about Paper 3.

---

## 8. The cost estimate is too low

The independent pass put the repair at "one code-fix commit, one rerun afternoon". That is right
for Claim A and wrong for Claims B, C and D.

Claim A is one line removed and one arm relabelled or dropped.

Claim B has no one-line fix. The discretiser is wrong because weekly bins cannot represent a
3.0-day serial interval at all; `si[1]` would have to carry the mass between 0 and 10.5 days
whatever the bin edges are. The choices are to reconstruct the analysis at daily resolution, which
the CHP data does not support, to reparameterise the renewal equation so the weekly step is
explicit, or to state in Methods that the effective influenza serial interval is one week and
accept that the pathogen contrast is between a degenerate instrument and a non-degenerate one.
**That is a modelling decision, not a bug fix**, and it propagates through nine files and every
reported day-level lead.

Claim C is downstream of B. Until B is settled the grid cannot be rerun, because there is no
serial interval to vary.

Claim D needs a rule, not a patch. Lowering `prior_rate` moves the degenerate value without
removing the behaviour; the actual requirement is an estimability condition — a minimum total
infectiousness, or a minimum count in the window — fixed in writing before the rerun, under Part
II's rule that a threshold is written down before it is applied. Three reported onset dates depend
on which rule is chosen.

A realistic sequence is: decide the weekly-renewal question, decide the estimability rule, write
both down with their justification, then one rerun. The rerun is an afternoon. The two decisions
are not.

---

## 9. Division of ownership, under the 25 September practices

The code defects, the reruns and the two decisions in §8 are Thomas's, and are made and recorded
before anything goes to Vijay.

The framing consequences are Vijay's and are not pre-empted. Specifically: the Highlights sentence
"Low-amplitude laboratory signals degraded both estimators in the same direction" is his inserted
prose and §6 removes its evidence; the Abstract's framing of the pathogen contrast is affected by
§4 and §7; and the Methods passage flagging the degenerate age-channel fits is affected by §5b.
**His wording is not altered without asking him first**, and the ask is a question, not a
redlined draft.

The one item that is neither is reference [8] (Lessler et al. 2009, cited for an influenza serial
interval and a 5-day infectious period, containing neither). That is a citation error under Part
I's hardest rule and is fixed on sight.

---

## 10. What this record does not establish

- Whether the GitHub remotes match the local working copies. Not reachable from this session.
- Whether any EpiEstim-based specification-curve arm exists outside the two `paper3_v8_*` scripts.
- The magnitude or direction of the change to reported leads after a corrected rerun. Not
  predictable from the discretisation arithmetic; it needs the rerun.
- Whether the three degenerate onsets are the only ones affected by §5b. Only the three channels
  with `best_Rt` above 1,000 were checked; channels with modest prior-dominated values would not
  stand out in `best_Rt` and were not searched for.
