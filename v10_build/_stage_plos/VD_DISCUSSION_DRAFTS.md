# Two Discussion paragraphs, drafted to be cut — 10 November 2026

**Neither of these is in the manuscript.** The Discussion is yours by the April 2026
division, and the editing copy carries Kimberly Edwards's two comments with nothing written
against them. These drafts exist so that the answer to her is something to cut rather than a
blank page, and they are offered on the understanding that you will rewrite or discard them.

**They add no interpretation and no number.** Every figure below is already in the Results,
and the uses named in the second paragraph are the ones your own Introduction names:
positioning antiviral and diagnostic stock, and accelerating outreach.

Her two comments, verbatim:

> **[Discussion]** I think you still need to address the practical implications of these
> results. Is an earlier detection necessarily 'better' if it predicts epidemic onset >30
> days in advance? How can these retrospective analyses & tools inform future public health
> preparedness?

> **[end of Limitations]** Don't end on limitations, give an overarching conclusion.
> Summarize contributions of this paper to existing body of knowledge and highlight
> knowledge gaps for further study/consideration.

---

## Draft A — operational implications

*Placement: a new subsection after "Hospital admissions as a sentinel signal", before
Limitations.*

Whether an earlier onset signal is a better one depends on what the extra time is used for,
and this design cannot answer that. The leads reported here are not small: where
adolescent admissions crossed first they did so by 21 to 63 days, and the largest lead came
in the lowest-amplitude season in the set. A declaration two months ahead of the
laboratory-positivity threshold is only an improvement if it is acted on, and the actions
that onset declaration is meant to trigger — positioning antiviral and diagnostic stock,
accelerating outreach — have their own lead times, below which further warning buys nothing.
Against that, the cost of acting early is a false start, and the present design does not
measure it: admissions led in four of eight seasons and lagged in none, but the paired test
does not reach significance and the confidence interval for the median difference includes
zero, so the rate at which an admissions-based trigger would fire in a season that does not
develop is not estimated here. Two further features bear on deployment. The gain is
concentrated where it is least convenient: on a high-amplitude season all signals crossed in
the same week, so the advantage appears only when the signal is weak and the estimate is
least stable. And R(t)-based detection is contingent on a fixed recovery
rate, which moved detection from three of six seasons to six of six when changed from a
10-day to a 5-day infectious period, so no R(t) trigger is deployable without that parameter
being justified for the pathogen and the setting rather than carried over. The practical
reading is therefore narrower than "earlier is better": age-stratified admissions are worth
monitoring alongside positivity, as a second signal whose disagreement with the first is
informative, and a prospective evaluation that counts false starts as well as leads is what
would turn that into an operational rule.

---

## Draft B — conclusion

*Placement: a short closing subsection after Limitations, so the paper does not end on them.*

This study set out to test whether R(t)-based onset detection transfers across two
pathogens measured by the same surveillance system, and the answer is that it does not
transfer cleanly, for reasons that are legible rather than mysterious. EpiEstim led the
operational influenza threshold in five of six seasons but led the RSV comparator in only
four of ten, and the apparent amplitude explanation does not survive stratification: within
each pathogen the rank correlation between signal-to-noise and lead time is weak and runs in
opposite directions, so the effect is carried by the contrast between the two pathogens
rather than by variation within either. The PINN result is sharper and less comfortable: onset detection moved from
three of six seasons to six of six on a change of the assumed recovery rate alone, which
makes the fixed parameter, not the method, the determinant of what the model reports.
Alongside those, the one positive finding is that age-stratified hospital admissions,
particularly for adolescents, led laboratory positivity in four of eight influenza seasons
and lagged in none, without a consistent relationship to season amplitude.

What this adds to the existing literature is a like-for-like cross-pathogen comparison on a
single surveillance system, with the fixed parameters and the comparator construction stated
rather than assumed, and with the negative results reported at the same weight as the
positive one. What it does not settle is where the cross-pathogen difference comes from.
Three candidates remain entangled: signal amplitude, the circularity of a data-derived RSV
comparator against an operational influenza one, and a weekly reporting interval that
removes most of the influenza serial interval while leaving most of the RSV one, so that the
two pathogens are estimated with structurally different instruments. Separating them needs
either a high-amplitude RSV season, an independent operational RSV threshold, or a
surveillance stream reported at finer than weekly resolution — and the last of those is the
condition under which any renewal-equation method of this kind should be expected to behave
as specified.

---

## Three things deliberately not claimed

- **No benefit is asserted.** Draft A says what the lead would have to be worth, not that it
  is worth it, because the false-start rate is not estimated here and the paired test does
  not reach significance.
- **No mechanism is asserted for the cross-pathogen difference.** Draft B names three
  entangled candidates and leaves them entangled, which is what the Results support.
- **Nothing is said about the simulation study.** The scaled arm cannot inform about signal
  amplitude in either direction, so neither draft leans on it.

## If the weekly-serial-interval question goes the other way

Both drafts are written for the outcome where that limitation is stated in Methods rather
than removed by a rebuild. If you decide on daily reconstruction instead, Draft B's closing
sentence and the third candidate in its final paragraph would have to be rewritten, because
the instrument would no longer differ between the two pathogens in the way the sentence
describes.
