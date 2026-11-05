# v10 preview — proposed figures and sentences, before anything is inserted

**15 October 2026.** Nothing has been written into the manuscript. This document shows every
figure and every sentence proposed for v10 so they can be accepted, changed or rejected first.
Sentences are marked **[T]** where the surrounding text is Thomas's and **[V]** where it is
Vijay's inserted prose — nothing marked [V] is drafted here, only flagged.

---

## 0. Three things found while locating the edits

**0a. The Methods section appears twice in v9.** Verified in `word/document.xml` under all three
views — raw, changes-accepted and changes-rejected — so it is not a tracked-change artefact. The
paragraph beginning *"The Cori et al. [2] Bayesian renewal equation framework was implemented in
Python"* occurs at two separate places, along with *Data sources*, the RSV extraction paragraph,
the COVID-exclusion paragraph and the ethics statement. One copy sits between the Author Summary
and the Introduction with no heading; the other sits after *Limitations*, under the heading
*Materials and Methods*. Vijay's format spec puts Methods after the Introduction, so the correctly
placed copy is the one that lost its heading. **This is in the version already sent to him and is
not in any review document, audit pass or session record.** It needs fixing regardless of
everything else below.

**0b. The paper already measured the serial-interval consequence.** Results, simulation study:
*"Serial interval misspecification (mean 7.0 days instead of 3.0 days) had minimal effect on R(t)
recovery (change in median r of 0.03 or less in the clean scenarios)."* That is exactly the
substitution weekly discretisation performs. The defect therefore arrives with its own bound
already committed, which is why none of the reported R(t) numbers need to move.

**0c. Limitations already flags the resolution mismatch** — *"weekly temporal resolution is coarse
relative to the influenza serial interval (3 days), meaning that each data point spans
approximately two transmission generations."* The new content quantifies a point the paper
already makes; it does not introduce one.

---

## 1. Figures

| | Figure | Action |
|---|---|---|
| 1 | R(t) trajectories | **Unchanged.** Computed with the weekly-discretised serial interval, which is what the revised Methods now describe. No regeneration |
| 2 | Signal amplitude vs lead | **Replaced** — see below |
| 3 | Pre-onset admissions surge | **Unchanged.** No EpiEstim, no serial interval anywhere in it |
| 4 | Admissions vs positivity leads | **Title only.** Degenerate cells are already hatched with a footnote |
| S5 | *(new)* Serial-interval discretisation | **Added** to the supplementary |

### Figure 2 (replacement) — `fig2_snr_within_pathogen.pdf`

Two changes from the old figure. The x-axis is now the signal-to-noise ratio, which is what the
Results text actually analyses — the old figure plotted peak positivity while the text cited it
for a logistic regression on SNR, so the figure and its citation did not match. And the points are
faceted by pathogen, which is where the association disappears.

> **Figure 2. Signal-to-noise ratio does not predict R(t) lead time within either pathogen.**
> EpiEstim lead time relative to the comparator threshold, plotted against the season
> signal-to-noise ratio (peak positivity divided by the non-season standard deviation), for 8
> influenza seasons and 10 RSV seasons. Positive values indicate detection earlier than the
> threshold. Spearman rank correlations with two-sided permutation p-values (20,000 permutations)
> are shown per panel. The two labelled influenza seasons are the extremes of the SNR range and run
> in opposite directions to the hypothesised relationship.

### Figure S5 (new) — `figS5_si_discretisation.pdf`

> **Supplementary Figure S5. Weekly discretisation of the serial-interval distributions.**
> (a) The gamma serial intervals specified in Methods. The dashed line marks the lower edge of the
> first weekly bin at 3.5 days; shading marks the probability mass below that edge, which the
> discretisation discards before renormalising. (b) The resulting weekly weights. For influenza,
> 68.5% of the distribution falls below the first bin edge, the week-1 weight becomes 0.998 and the
> effective mean is 7.01 days; for RSV the corresponding values are 9.9%, 0.800 and 8.50 days. No
> serial interval shorter than approximately one week is representable at weekly resolution.

### Figure 4 — title only

- Current: *Age-stratified admissions outperform lab positivity on difficult seasons*
- Proposed: *Age-stratified admissions lead lab positivity on low-amplitude and multi-wave seasons*

"Outperform" asserts more than p = 0.0625 at the test floor, or p = 0.125 with the degenerate
seasons excluded, can carry. The underlying bars do not change.

---

## 2. Sentences

### 2.1 Methods — serial interval **[T]**

**Current.** *"Pathogen-specific serial intervals were used: mean 3.0 days (SD 1.5) for influenza
[8] and mean 7.5 days (SD 3.5) for RSV [14] (Vink et al. 2014, systematic review estimating RSV
mean SI at 7.5 days, SD 2.1 days; note that weekly data with a 7.5-day SI provides approximately
one observation per generation, limiting temporal resolution)."*

**Proposed.**

> Pathogen-specific serial intervals were specified as mean 3.0 days (SD 1.5) for influenza and
> mean 7.5 days (SD 3.5) for RSV (Vink et al., 2014). Because the incidence series are weekly, each
> gamma distribution was discretised onto weekly bins, the first of which begins at 3.5 days; mass
> below that edge is discarded and the remainder renormalised. The serial interval the estimator
> uses is therefore not the one specified. For influenza, 68.5% of the distribution falls below the
> first bin edge, the week-1 weight becomes 0.998 and the effective mean is 7.01 days; for RSV the
> corresponding values are 9.9%, 0.800 and 8.50 days (Supplementary Fig. S5). The influenza serial
> interval is effectively a point mass at one week. This arises from the resolution of the
> surveillance data rather than from a modelling choice, since no sub-weekly generation interval is
> representable in weekly bins, and it applies to any renewal-equation analysis of weekly influenza
> data. The simulation study bounds the consequence, in that substituting a 7.0-day mean for a
> 3.0-day mean changes the median correlation by 0.03 or less in the clean scenarios.

**One question inside this edit, not resolved here.** The Methods sentence cites Vink et al. for
RSV and reports SD 2.1 days in the same breath, while the code uses SD 3.5. Which is intended is a
decision, not an edit. The figure above is drawn at SD 3.5, matching the code.

### 2.2 Methods — simulation scenarios **[T]**

**Current.** *"...six scenarios: perfect I(t), scaled (factor 0.10–0.20), noisy..."*

**Proposed.** Remove `scaled` from the scenario list and add:

> A scaled scenario, in which the series was multiplied by a constant between 0.10 and 0.20, was
> specified but is not reported. The pseudo-count construction rescales every series to a common
> peak of 1,000 before Poisson noise is applied, so a constant multiplier cancels exactly and the
> scaled arm reproduces the perfect arm. The same rescaling fixes the signal-to-noise ratio across
> all arms by construction, so this simulation does not bear on signal amplitude in either
> direction.

### 2.3 Results — simulation **[T]**

**Current.** *"...median correlation r = 0.72 (perfect, scaled, and filtered scenarios; range 0.71
to 0.73)"*

**Proposed.** *"...median correlation r = 0.72 (perfect and filtered scenarios; range 0.71 to
0.73)"*

### 2.4 Results — serial-interval sensitivity **[T]**

**Current.** *"Onset timing was robust to serial interval assumptions: across 20 configurations (5
SI means × 4 window widths) applied to all 6 seasons, all configurations detected onset in every
season. Lead time SD ranged from 3.1 days (2014/15) to 11.4 days (2023 summer) with a mean of 6.8
days across seasons..."*

**Proposed.**

> Onset timing was insensitive to the serial interval, for a structural reason rather than an
> empirical one. The grid varied five serial-interval means from 2.0 to 4.0 days and four window
> widths, but after weekly discretisation all five means produce the same weekly weights
> (Supplementary Fig. S5), and in every season and at every window width the five means returned
> identical onset dates. The grid therefore contains four distinct configurations rather than
> twenty, and all four detected onset in every season. Across the four window widths, lead-time SD
> ranged from 3.5 days (2014/15) to 12.8 days (2023 summer), with a mean of 7.7 days across seasons
> (Supplementary Table S4).

Table S4 needs the same recomputation; the numbers above are from the committed
`epiestim_si_sensitivity_flu.csv`, collapsing the five duplicate rows per window.

### 2.5 Results — RSV and signal-to-noise **[T]**

**Current, final two sentences.** *"Seasons where EpiEstim led the threshold had higher median SNR
than lagging seasons (16.7 vs 10.2; Mann–Whitney U = 52.0, one-sided p = 0.166). Logistic
regression of lead > 0 on SNR estimated P(lead > 0) = 0.34 at SNR = 5 and 0.62 at SNR = 20,
consistent with a continuous relationship between signal amplitude and method performance rather
than a sharp boundary (Fig. 2)."*

**Proposed.**

> Seasons where EpiEstim led the threshold had higher median SNR than lagging seasons (16.7 vs
> 10.2; Mann–Whitney U = 52.0, one-sided p = 0.166). This association does not survive
> stratification by pathogen. Within influenza the rank correlation between SNR and lead time is
> −0.06 (n = 8, permutation p = 0.90), and within RSV it is +0.23 (n = 10, p = 0.52); the
> highest-SNR influenza season detected onset 28 days after its threshold, while the lowest-SNR
> season detected it 49 days before (Fig. 2). What this means is that the apparent amplitude effect
> is carried by the contrast between the two pathogens rather than by variation in amplitude within
> either of them. The pooled association is therefore reported as a hypothesis rather than as a
> demonstrated driver, and the drivers of within-pathogen variation remain unidentified.

The logistic sentence is dropped: its interval is not reproducible from any committed script, and
the rank correlations above are.

### 2.6 Results — degenerate admissions fits **[T]**

**Current bracketed note, second sentence.** *"These age groups have near-zero admission rates in
some weeks, creating structurally degenerate denominators."*

**Proposed, replacing that sentence and extending the note.**

> The mechanism is specific. When every week in the sliding window carries zero admissions, total
> infectiousness over that window is zero, so the Gamma(1, 0.2) prior's rate parameter becomes the
> entire posterior denominator and the posterior mean reduces to (1 + ΣI)/0.2. All three affected
> channel-seasons satisfy this exactly, with posterior rates of 0.2 to three decimal places. Because
> onset is defined as the first week with R(t) above 1, the rule fires on a week in which no
> admissions were recorded; in each case the reported onset precedes the channel's first non-zero
> admission week by four to five weeks. Excluding the two affected seasons leaves the median
> difference unchanged at +10.5 days (n = 6, three non-zero pairs, Wilcoxon W = 6.0, one-sided
> p = 0.125).

That sensitivity analysis is already committed in `wilcoxon_admissions_results.csv` and is
currently unreported.

### 2.7 Discussion — cross-pathogen amplitude **[T]**

**Current, final clause.** *"...the common weekly temporal resolution could each contribute to
concordant degradation through a mechanism other than signal amplitude."*

**Proposed addition immediately after.**

> That alternative can now be quantified. Weekly discretisation removes 68.5% of the specified
> influenza serial interval but only 9.9% of the RSV one, so the two pathogens are estimated with
> structurally different instruments and temporal resolution is confounded with amplitude. The
> direction of the difference does not favour resolution as the explanation, since the pathogen
> whose serial interval is more severely truncated is the one on which the estimator performs
> better. A direct test requires no new data: re-estimating RSV with a deliberately degenerate
> one-week serial interval would indicate whether RSV performance moves toward the influenza
> result.

### 2.8 Limitations **[T]**

**Current.** *"Second, weekly temporal resolution is coarse relative to the influenza serial
interval (3 days), meaning that each data point spans approximately two transmission
generations."*

**Proposed.**

> Second, weekly temporal resolution is coarse relative to the influenza serial interval (3 days),
> meaning that each data point spans approximately two transmission generations and that the
> discretised serial interval available to the estimator is effectively a point mass at one week
> rather than the 3.0-day distribution specified (Supplementary Fig. S5). This constrains any
> renewal-equation analysis of weekly influenza surveillance, not only the present one.

### 2.9 Reference [8] — **not drafted, blocked on a source read**

Lessler et al. 2009 covers incubation periods only and is currently cited for the influenza serial
interval and for a 5-day infectious period. Both citations must be re-pointed. No replacement is
proposed here, because under the project's citation rule a reference does not enter a document
until its record has been resolved and the specific claim located in the full text. Two source
reads are owed before this line can be written.

---

## 3. Vijay's prose — flagged, not drafted **[V]**

Three passages are affected by §2.5 and are his inserted text. The question goes to him; no
replacement is written here.

1. Highlights: *"Low-amplitude laboratory signals degraded both estimators in the same direction."*
   The claim survives on the between-pathogen contrast, the SNR logistic and the admissions
   pattern, all real data. It does not survive as a within-pathogen claim.
2. Highlights: *"Age-stratified admissions led positivity exactly on the hardest, low-amplitude
   seasons."* Affected by the degenerate-season exclusion in §2.6.
3. Author Summary: *"R(t)-based onset detection is therefore contingent on signal amplitude and on
   parameter choices that should be reported explicitly."*

---

## 4. Not an edit — and this one must be struck from the working list

**Table 1's 2025 RSV row is correct and must not be changed.**
`epiestim_rsv_results.csv` records `epiestim_onset 2025-04-02, threshold_onset 2025-07-02,
lead_days 91`. Table 1's column order is Season | Peak% | Thresh. | EpiEstim | Epi lead, so
Thresh 07-02 with EpiEstim 04-02 matches the source exactly, and 2 April to 2 July is 91 days.

This began as finding B1 in the external review, became "F-1 (verified, blocking)" in the v10
revision brief, and appears as "resolved as a typo — one-cell fix" in the 14 October session
record. Each document inherited it without re-deriving it. **Applying the fix would introduce an
error into a correct table and change an Abstract number for no reason.**

---

## 5. What this does not change

No date in Table 1 moves. No figure needs new data. The Abstract's influenza median lead and IQR,
the post-COVID statistics block, both binomial confidence intervals, Table 2's R(t) values and
Tables S2 and S4's agreement with the prose all stand as verified. The total is one duplicated
section removed, one replaced figure, one new supplementary figure, one figure title, and roughly
a dozen sentences across Methods, Results, Discussion and Limitations, out of 314 paragraphs.
