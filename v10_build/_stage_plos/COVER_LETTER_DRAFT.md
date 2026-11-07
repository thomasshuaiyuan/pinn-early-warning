# Cover letter — DRAFT for VD's sign-off

PLOS uploads this as a separate file and only editors and journal staff see it. The journal asks
it to explain why the manuscript suits the journal and how the study advances its field.

Two slots need him: the date, and whether he wants the last paragraph at all.

---

Dear Editors,

We submit for your consideration a research article titled *Surveillance-based R(t) estimation
for respiratory pathogen onset detection: a retrospective cross-pathogen evaluation of influenza
and RSV in Hong Kong, 2014–2026*.

Static laboratory-positivity thresholds remain the operational basis for declaring respiratory
virus season onset in most surveillance systems, and time-varying reproduction number methods
are widely proposed as a replacement. The question of when those methods actually deliver an
earlier and more reliable signal, and when they do not, has not been settled on long
observational records. We evaluate two R(t) estimators across eighteen pathogen-seasons of Hong
Kong surveillance data, using influenza as the primary case and RSV as a deliberately
low-amplitude contrast. The influenza comparator is the Centre for Health Protection's published
operational positivity threshold; because no RSV threshold is published, the RSV comparator is
derived from the same series and is not an independent operational benchmark.

The study reports three things that bear on computational practice rather than on one city's
surveillance. First, estimator performance is not uniform across pathogens: the renewal-equation
estimator led the influenza threshold by a median of 35 days but lagged for RSV. Second, the
physics-informed neural network's onset estimate tracked the clamped recovery rate across the
three values tested, which is a cautionary result for a rapidly growing literature applying
these architectures to surveillance counts. Third, and we think most useful to this journal's
readership, whether the serial-interval assumption can affect an estimated onset at all depends
on where that interval sits relative to the reporting interval: influenza's 3.0-day interval
falls below the first weekly bin edge, so after discretisation the onset date is identical at
every serial-interval mean tested in all 24 season-window cells, while RSV's 7.5-day interval
straddles that edge and the onset date does move, in 3 of 12 season-window cells and within one
of three test seasons. The two grids are not matched, since every influenza mean tested falls
below the first bin edge while the RSV means straddle it. With those limits stated, the
observation is a general point about renewal-equation analyses of weekly aggregated data rather
than a property of these particular series.

We report the negative and null results alongside the positive ones, including a
signal-to-noise analysis that does not predict lead time within either pathogen and is titled
accordingly. All analysis code and the derived data files that reproduce every reported value
are publicly available, and the data are from public surveillance sources throughout.

The manuscript has not been published elsewhere and is not under consideration at another
journal. We have no related or duplicate submissions.

[VD — optional closing paragraph on the group's work and the fit with the journal, or delete.]

Thank you for considering our submission.

Yours sincerely,

Vijaykrishna Dhanasekaran
School of Public Health, LKS Faculty of Medicine, The University of Hong Kong
HKU-Pasteur Research Pole, The University of Hong Kong
veej@hku.hk

on behalf of Thomas Yuan and Vijaykrishna Dhanasekaran

[Date]

---

## Notes on what is and is not claimed above

Every number in the letter is in the manuscript and reproducible from committed outputs: the
median +35 day influenza lead, the RSV lag, the 0 of 24 and the 3 of 12 season-window cells.

**The letter deliberately does not claim the amplitude mechanism.** The Highlights line
*"Low-amplitude laboratory signals degraded both estimators in the same direction"* is not used,
because the real-data signal-to-noise result is null on every test the paper reports and the
simulation holds signal-to-noise fixed by construction. The letter leads on the
serial-interval asymmetry instead, which is measured, scripted and reproducible, and which is
the finding most likely to interest this particular journal.

**The signature block gained HKU-Pasteur on 6 November**, when VD supplied the affiliation block
and it turned out to separate HKU SPH from HKU-Pasteur, which v10 had merged onto one numbered
line. The manuscript's author block now carries 1 SPH, 2 HKU-Pasteur, 3 Columbia, so the letter
names both of his rather than only the first. Nothing else in the letter changed.

**Three claims were softened on 5 November after an independent review pass.** The comparator
was described as "the published operational threshold" across all eighteen seasons, which is
true of the 4.94% influenza threshold and false of the 1.87% RSV comparator; the two are now
distinguished in the letter itself rather than only in these notes. The serial-interval result
said the question "is decided by" the reporting interval, with the 3-of-12 and
one-season-of-three limits present only in the drafting notes; those limits are now in the
paragraph. And *"governed by the clamped recovery rate rather than by model skill"* overstated
what a single-seed comparison across three γ values supports, so the letter now says the onset
estimate tracked the recovery rate across the values tested. **The "model skill" phrasing
originates in VD's Highlights line, so it goes to him as a question and is not rewritten in his
text** — only this letter, which is ours, was changed.
