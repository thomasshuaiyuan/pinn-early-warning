"""Build early-warning v10 as tracked changes on top of v9.

Every one of Vijay's tracked revisions, moves, formatting changes and his comments
is left in place. Thomas's changes are added as tracked changes by "Thomas Yuan".
No structural surgery: nothing is moved, no section is deleted.
"""
import copy, os, shutil, sys, zipfile
from lxml import etree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ooxml_track import Editor, NS, q, W, XML

SRC = '/home/claude/vjbuild/2026-09-26_early-warning_v9.docx'
OUT = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/vjbuild/2026-10-15_early-warning_v10.docx'
WORK = '/home/claude/vjbuild/_v10'
AUTHOR, DATE = 'Thomas Yuan', '2026-10-15T12:00:00Z'

if os.path.exists(WORK):
    shutil.rmtree(WORK)
with zipfile.ZipFile(SRC) as z:
    z.extractall(WORK)
    ORDER = [i.filename for i in z.infolist()]

docpath = os.path.join(WORK, 'word', 'document.xml')
tree = etree.parse(docpath)
root = tree.getroot()
body = root.find('w:body', NS)
ed = Editor(root, AUTHOR, DATE, first_id=5000)
P = [p for p in body if etree.QName(p).localname == 'p']


def new_para_after(model_p, text, run_model=None):
    """Insert a wholly new paragraph (tracked as an insertion) after model_p.

    The clone is taken for its formatting only. Three things have to be stripped
    from it, and all three were live defects in the first build of this file:

      1. Any revision mark inherited from the model's paragraph mark. Cloning in
         a chain (each new paragraph modelled on the previous new one) made these
         accumulate, and because the ids came with them the document ended up with
         w:id 5042 on three different elements. Duplicate revision ids are invalid
         and Word may silently repair them.
      2. w:pPrChange. On the reference paragraphs the model carried a pPrChange
         authored "Vijay", dated 2026-08-20. Cloned onto a paragraph created on
         15 October, it is a fabricated record of him having reformatted something
         that did not exist when he worked on the file. Nothing in this build may
         attribute anything to him that he did not do.
      3. w:sectPr, which would start a new section mid-document.

    The inserted paragraph mark is then placed in a fresh w:rPr positioned BEFORE
    any remaining pPrChange, which is the order CT_PPr requires.
    """
    np = copy.deepcopy(model_p)
    # strip every child except pPr
    for ch in list(np):
        if etree.QName(ch).localname != 'pPr':
            np.remove(ch)
    ppr = np.find(q('pPr'))
    if ppr is None:
        ppr = etree.Element(q('pPr'))
        np.insert(0, ppr)
    # drop inherited revision records and section breaks
    for ch in list(ppr):
        if etree.QName(ch).localname in ('rPr', 'pPrChange', 'sectPr'):
            ppr.remove(ch)
    # mark the paragraph mark itself as inserted, in a clean rPr at the end of pPr
    rpr = etree.SubElement(ppr, q('rPr'))
    ins_mark = etree.SubElement(rpr, q('ins'))
    ins_mark.set(q('id'), ed.nid())
    ins_mark.set(q('author'), AUTHOR)
    ins_mark.set(q('date'), DATE)
    # the text, as an insertion; formatting from run_model, never from the chain
    src_run = None
    for r in (run_model if run_model is not None else model_p).iter(q('r')):
        if r.find(q('t')) is not None:
            src_run = r
            break
    np.append(ed.make_ins(text, src_run))
    model_p.addnext(np)
    return np


# ============================================================
# E1  Methods — serial interval, discretisation, removal rate
# ============================================================
ed.replace(P[45],
 'Pathogen-specific serial intervals were used: mean 3.0 days (SD 1.5) for influenza [8] and mean 7.5 days (SD 3.5) for RSV [14] (Vink et al. 2014, systematic review estimating RSV mean SI at 7.5 days, SD 2.1 days; note that weekly data with a 7.5-day SI provides approximately one observation per generation, limiting temporal resolution).',
 'Pathogen-specific serial intervals were specified as mean 3.0 days (SD 1.5) for influenza and '
 'mean 7.5 days for RSV [14], with a standard deviation of 3.5 days. Published influenza estimates '
 'span approximately 2.2 to 3.6 '
 'days, from 2.2 days for A(H3N2) and 2.8 days for A(H1N1)pdm09 in a systematic reanalysis of '
 'household outbreaks [14] to 3.6 days (95% CI 2.9 to 4.3) in a Hong Kong household transmission '
 'study [16]; the value used here is central to that range rather than taken from a single estimate. '
 'Because the incidence series are weekly, each gamma distribution was discretised onto weekly bins, '
 'the first of which begins at 3.5 days, so that probability mass below that edge is dropped and the '
 'remainder renormalised. The serial interval available to the estimator is therefore not the one '
 'specified: for influenza, approximately 68.5% of the distribution falls below the first bin edge, '
 'the first weekly weight becomes 0.998, and the effective mean is 7.01 days; for RSV the '
 'corresponding values are 9.9%, 0.800 and 8.50 days (Supplementary Fig. S5). Under the exact '
 'week-lag distribution implied by weekly aggregation, approximately 57% of influenza transmission '
 'occurs within the same week and is unrepresentable in a renewal model that sets the zero-lag '
 'weight to zero; conditioned on a lag of at least one week, the binning used here is closer to that '
 'exact distribution than the alternative of left-aligned weekly bins (total-variation distance '
 '0.004 against 0.011 for influenza, 0.052 against 0.244 for RSV). The limitation therefore applies to any renewal-equation analysis that '
 'discretises the serial interval onto the weekly grid, and methods that reconstruct daily incidence '
 'from temporally aggregated data before estimation are the available alternative [17,18].')

ed.replace(P[45],
 'Sensitivity was assessed across 20 SI/window configurations for influenza.',
 'Sensitivity was assessed across a grid of 5 serial-interval means and 4 window widths for '
 'influenza; because all five means coincide after weekly discretisation, the grid resolves to 4 '
 'distinct configurations.')

ed.replace(P[45],
 'the degenerate R(t) maxima (~26,000) observed for some adolescent admissions runs are a symptom of this',
 'the degenerate R(t) maxima observed for some age-stratified admissions runs (up to 49,005, in the '
 '6-11 and 12-17 year channels) are a symptom of this')

# ============================================================
# E2  Methods — the scaled simulation scenario
# ============================================================
ed.replace(P[49],
 'Weekly observations were created under six scenarios: perfect I(t), scaled (factor 0.10–0.20), noisy',
 'Weekly observations were created under six scenarios, of which five are reported: perfect I(t), '
 'scaled (factor 0.10–0.20; specified but not reported, see below), noisy')

ed.insert_after(P[49],
 'with Poisson observation noise applied in every scenario.',
 ' The scaled scenario is not reported because the pseudo-count construction rescales every series '
 'to a common peak of 1,000 before Poisson noise is applied, so a constant multiplier cancels '
 'exactly and the scaled arm reproduces the perfect arm. The same rescaling fixes the '
 'signal-to-noise ratio across arms by construction, so this simulation does not bear on signal '
 'amplitude in either direction.')

# ============================================================
# E3  Results — simulation
# ============================================================
ed.replace(P[75],
 'median correlation r = 0.72 (perfect, scaled, and filtered scenarios; range 0.71 to 0.73)',
 'median correlation r = 0.72 (perfect and filtered scenarios; range 0.71 to 0.73)')

ed.replace(P[75],
 'Serial interval misspecification (mean 7.0 days instead of 3.0 days) had minimal effect on R(t) recovery (change in median r of 0.03 or less in the clean scenarios), consistent with the finding that onset detection was robust to SI assumptions in the empirical analysis.',
 'Serial interval misspecification (mean 7.0 days instead of 3.0 days) had minimal effect on R(t) '
 'recovery (change in median r of 0.03 or less in the clean scenarios), consistent with the finding '
 'that onset detection was robust to SI assumptions in the empirical analysis. This comparison is '
 'bounded by the same weekly discretisation described in the Methods: both arms are discretised onto '
 'the weekly grid, so the effective contrast is between mean lags of 7.01 and 8.00 days rather than '
 'between 3.0 and 7.0 days, and the result should not be read as bounding the cost of the '
 'discretisation itself.')

# ============================================================
# E4  Results — serial-interval sensitivity
# ============================================================
ed.replace(P[59],
 'Onset timing was robust to serial interval assumptions: across 20 configurations (5 SI means × 4 window widths) applied to all 6 seasons, all configurations detected onset in every season. Lead time SD ranged from 3.1 days (2014/15) to 11.4 days (2023 summer) with a mean of 6.8 days across seasons, and lead time range from 7 to 28 days',
 'Onset timing was insensitive to the serial interval, for a structural reason rather than an '
 'empirical one. The grid varied five serial-interval means from 2.0 to 4.0 days and four window '
 'widths, but after weekly discretisation all five means produce weekly weights that differ by at '
 'most 0.013 in total variation, and in every season and at every window width the five means '
 'returned identical onset dates. The grid therefore resolves to four distinct configurations rather '
 'than twenty, and all four detected onset in every season. Across the four window widths, lead-time '
 'SD ranged from 3.5 days (2014/15) to 12.8 days (2023 summer), with a mean of 7.7 days across '
 'seasons')

# ============================================================
# E5  Results — RSV and signal-to-noise
# ============================================================
ed.replace(P[69],
 'Logistic regression of lead > 0 on SNR estimated P(lead > 0) = 0.34 at SNR = 5 and 0.62 at SNR = 20, consistent with a continuous relationship between signal amplitude and method performance rather than a sharp boundary (Fig. 2).',
 'This association does not survive stratification by pathogen. Within influenza the rank '
 'correlation between SNR and lead time is −0.06 (n = 8, permutation p = 0.90), and within RSV it is '
 '+0.23 (n = 10, p = 0.52); the highest-SNR influenza season detected onset 28 days after its '
 'threshold, while the lowest-SNR season detected it 49 days before (Fig. 2; correlations and '
 'permutation p-values in snr_within_pathogen_stats.csv, 20,000 permutations, seed 0). What this means is '
 'that the apparent amplitude effect is carried by the contrast between the two pathogens rather '
 'than by variation in amplitude within either of them. The pooled association is therefore reported '
 'as a hypothesis rather than as a demonstrated driver, and the drivers of within-pathogen variation '
 'remain unidentified.')

# ============================================================
# E6  Results — degenerate admissions fits
# ============================================================
ed.replace(P[67],
 'These age groups have near-zero admission rates in some weeks, creating structurally degenerate denominators.',
 'The mechanism is specific, and it has two parts. Total infectiousness at a given week is a '
 'weighted sum over preceding weeks only, so when those weeks carry no admissions it is zero and '
 'the rate parameter of the Gamma(1, 0.2) prior becomes the entire posterior denominator. Where the '
 'current week is also empty, the posterior mean is 1/0.2 = 5.0; where it carries the first '
 'sustained admissions of the season, the posterior mean is (1 + ΣI)/0.2, which is the source of '
 'the reported maxima: all three affected channel-seasons satisfy this exactly, at 49,005, 26,005 '
 'and 27,505. Because onset is defined as the first week with R(t) above 1.0, the first case fires '
 'the onset rule, and in all three channel-seasons every week of the four-week estimation window '
 'ending on the reported onset date carries zero admissions.')

ed.insert_after(P[67],
 'which produced non-degenerate estimates.',
 ' Excluding the two affected seasons leaves the median difference unchanged at +10.5 days (n = 6, '
 'three non-zero pairs, Wilcoxon W = 6.0, one-sided p = 0.125).')

# ============================================================
# E7  Discussion — cross-pathogen amplitude
# ============================================================
ed.insert_after(P[82],
 'could each contribute to concordant degradation through a mechanism other than signal amplitude.',
 ' The last of these can be quantified: weekly discretisation removes approximately 68.5% of the '
 'specified influenza serial interval but only 9.9% of the RSV one, so the two pathogens are '
 'estimated with structurally different instruments and temporal resolution is confounded with '
 'amplitude. The direction of the difference does not favour resolution as the explanation, since '
 'the pathogen whose serial interval is more severely truncated is the one on which the estimator '
 'performs better.')

# ============================================================
# E8  Limitations
# ============================================================
ed.replace(P[88],
 'Second, weekly temporal resolution is coarse relative to the influenza serial interval (3 days), meaning that each data point spans approximately two transmission generations.',
 'Second, weekly temporal resolution is coarse relative to the influenza serial interval (3 days), '
 'meaning that each data point spans approximately two transmission generations and that the '
 'discretised serial interval available to the estimator is effectively a point mass at one week '
 'rather than the 3.0-day distribution specified (Supplementary Fig. S5). This constrains any '
 'renewal-equation analysis that discretises the serial interval onto the weekly grid, not only the '
 'present one.')

# ============================================================
# E9  Results heading — remove the unsupported comparative
#
# The v9 heading reads "Age-stratified admissions outperform positivity on
# difficult seasons". Two problems, both checkable against
# wilcoxon_admissions_results.csv (the source of record named in
# wilcoxon_admissions.py).
#
# "Outperform" asserts more than the test carries: one-sided Wilcoxon on the
# 12-17y channel gives W = 10.0, p = 0.0625 on all eight seasons, which is the
# exact test's floor at four non-zero pairs and therefore cannot reach 0.05 at
# any effect size, and p = 0.125 with the two degenerate seasons excluded.
#
# "On difficult seasons" is false as a description of which seasons lead.
# The per-season differences are 2014/15 +21, 2015/16 0, 2016/17 +42,
# 2017/18 0, 2018/19 +21, 2023 S 0, 2023/24 0, 2024/25 +63. Ranked by peak
# positivity the eight seasons run 2017/18 40.6, 2014/15 38.6, 2018/19 30.0,
# 2015/16 25.7, 2023 S 18.2, 2016/17 15.6, 2023/24 14.9, 2024/25 10.5. The four
# leads therefore include the second- and third-highest-amplitude seasons
# (2014/15 and 2018/19) alongside the lowest (2024/25), so neither low amplitude
# nor multi-wave structure picks them out.
#
# 2018/19 is quoted as 30.0 to match Table 1 and the Figure 1 caption. The true
# maximum is 0.2995 of the A-and-B series, which is 29.95%; the 0.299 stored in
# snr_analysis_results.csv is that value rounded to three decimals, and reading
# the percentage off the CSV gives 29.9 and disagrees with the table. The
# reconciler now takes peak positivity from flux_data.csv for this reason. An earlier
# draft of this edit proposed "lead lab positivity on low-amplitude and
# multi-wave seasons", which is wrong for exactly this reason and was dropped.
#
# What replaces it states only the count and the direction, both exact: four
# leads, four ties, no season in which admissions were later. The degenerate
# caveat stays where it already is, in the body text and in Figure 4's hatching.
# The heading is original text that Vijay did not write and did not revise, and
# the change is tracked, so he can reject it in one click.
# ============================================================
ed.replace(P[66],
 'Age-stratified admissions outperform positivity on difficult seasons',
 '12–17 year admissions led positivity in four of eight influenza seasons and were never later')

# ============================================================
# E10  Methods — the mean influenza lead-time SD
#
# Found by reconciling the manuscript against the restated Table S4, not by the
# review. The Methods compare RSV's 8.0-8.2 day spread to "the mean influenza SD
# of 6.8 days". 6.8 is the mean of the six v9 per-season SDs (3.1, 8.8, 3.6,
# 11.4, 8.0, 6.0), which were computed over 20 grid points with each distinct
# configuration counted five times. On the 4 distinct configurations the per-season
# SDs are 3.5, 9.9, 4.0, 12.8, 9.0 and 6.7 and their mean is 7.7, which is what
# the revised Results and the rebuilt Table S4 now report. Leaving 6.8 here would
# have put two different means of the same six numbers in one manuscript.
#
# The sentence is Thomas's own, inserted 26 September, so this is a number
# correction to his text and not a change to Vijay's.
# ============================================================
ed.replace(P[45],
 'comparable to the mean influenza SD of 6.8 days',
 'comparable to the mean influenza SD of 7.7 days')

# ============================================================
# E11  The visible draft banner
# ============================================================
ed.replace(P[5],
 'DRAFT v9, 26 September 2026 (built on VD’s 19 August revision of v7; supersedes v8 of 25 August 2026)',
 'DRAFT v10, 15 October 2026 (built on VD’s 19 August revision of v7; supersedes v9 of 26 September 2026)')

# ============================================================
# E12  Introduction — the provenance of 4.94%
#
# The Introduction said CHP does not publish the threshold and that 4.94% was
# reconstructed here. Methods, Results and the Table 1 caption all say the
# opposite, that 4.94% is CHP's published operational value. They cannot all be
# right, and the project record settles it: 4.94% is CHP's published baseline,
# verified against the CHP report of 2 July 2026 and the press release of
# 3 January 2026. The opposite claim was made once before, on the false premise
# that CHP publishes no value, and was reverted on 23 August 2026. This sentence
# is what survived that reversion.
#
# The arithmetic agrees. Applying the formula this sentence describes to the
# committed weekly data gives 6.4677% (n = 156 baseline weeks, mean 0.030848,
# SD 0.017260), which is the figure Methods already reports as the 2014-2019
# reconstruction. So the sentence describes the sensitivity analysis and labels
# it as the comparator's provenance.
#
# Vijay's words are preserved exactly. His insertion of 2026-08-20 begins at
# "should be read as an analytical approximation of CHP practice rather than an
# official operational value", and that clause is true of a data-derived
# reconstruction. The edit stops immediately before it and re-points it at the
# reconstruction instead of at the comparator, so his sentence keeps its job and
# every one of his words stays in place and in order.
# ============================================================
ed.replace(P[28],
 'CHP does not publish the exact threshold value or its derivation; the value of 4.94% used here was '
 'reconstructed from the CHP Flu Express dataset (2014–2019 non-season weeks, defined as weeks with '
 'positivity below the series median; mean + 1.96 standard deviations of the combined A and B '
 'positivity) and ',
 'CHP publishes the threshold value but not its derivation, and the 4.94% used here is that published '
 'value. A reconstruction from the CHP Flu Express dataset (2014–2019 non-season weeks, defined as '
 'weeks with positivity below the series median; mean + 1.96 standard deviations of the combined A and '
 'B positivity) yields 6.47% rather than 4.94% (Methods); that reconstruction, and not the comparator, ')

# ============================================================
# E13  Methods — "coincide" overstates what the kernels do
#
# The five discretised means are five different kernels: their first weekly
# weights run from 0.9867 to 0.99998 and their effective means from 7.0001 to
# 7.0936 days. What is established is empirical, that they returned the same
# onset date in all 24 season-window cells, not that they are the same
# distribution. Stated as the measurement rather than as an identity.
# ============================================================
ed.replace(P[45],
 'Sensitivity was assessed across a grid of 5 serial-interval means and 4 window widths for influenza; '
 'because all five means coincide after weekly discretisation, the grid resolves to 4 distinct configurations.',
 'Sensitivity was assessed across a grid of 5 serial-interval means and 4 window widths for influenza; '
 'because the five discretised means returned identical onset dates in all 24 season-window cells, the '
 'grid resolves to 4 distinct onset outcomes rather than 20.')

# ============================================================
# E14  Methods — the RSV serial-interval SD is not Vink's
#
# Resolved by the independent review's full-text read, which this build accepts
# because it cites the table: Vink et al. Table 3 gives the RSV estimate as
# N(7.5, 2.1^2), from Crowcroft's England data, n = 59. The repository uses 3.5.
# The analysis is not changed here; the attribution is. This matters more than
# it did before v10, because the discretisation figures now reported for RSV
# (9.9% dropped, first weight 0.800, effective mean 8.50 days) are computed from
# that SD.
# ============================================================
ed.replace(P[45],
 'mean 7.5 days for RSV [14], with a standard deviation of 3.5 days.',
 'mean 7.5 days for RSV [14], with a standard deviation of 3.5 days. The mean is taken from [14]; the '
 'standard deviation is not, as [14] reports 2.1 days for RSV, and the wider value used here is a '
 'modelling choice that has not been sourced. The RSV discretisation figures reported below depend on it.')

# ============================================================
# E15  Methods — "literature standard" asks [8] for the wrong quantity
#
# [8] is Carrat, which measures viral shedding duration in volunteer challenge
# studies. The five-day SEIR infectious period is justified from it as a proxy,
# with the caveat, further down this section. This parenthetical called it the
# literature standard and cited [8] bare, which is the same estimand mismatch
# without the caveat.
# ============================================================
ed.replace(P[47],
 '0.2/day (5-day, literature standard [8])',
 '0.2/day (5-day, the value used in the primary analysis; its basis and the proxy caveat it carries are '
 'given below [8])')

# ============================================================
# E16  Methods — the rescaling does not fix SNR across arms
#
# Wrong as written, and wrong in my own text from the first v10 build. Rescaling
# a series to a common peak leaves that series' own peak-to-SD ratio unchanged;
# it does not equalise the ratio across arms that then receive different noise,
# filtering or thresholding. What actually cancels is the constant multiplier
# between the perfect and scaled arms, which is the narrower and correct reason
# the scaled arm carries no information about amplitude.
# ============================================================
ed.replace(P[49],
 'The same rescaling fixes the signal-to-noise ratio across arms by construction, so this simulation '
 'does not bear on signal amplitude in either direction.',
 'What cancels is that constant multiplier and not the peak-to-background ratio: rescaling a series '
 'leaves its own peak-to-SD ratio unchanged and does not equalise that ratio across arms that then '
 'receive different noise, filtering or thresholding. The simulation therefore does not bear on signal '
 'amplitude in either direction.')

# ============================================================
# E17  Results — the same correction, and the bound rounds the wrong way
#
# The maximum pairwise TV across the five influenza kernels is 0.01330247. "At
# most 0.013" rounds a maximum down, which is the one direction a stated bound
# may not round.
# ============================================================
ed.replace(P[59],
 'all five means produce weekly weights that differ by at most 0.013 in total variation, and in every '
 'season and at every window width the five means returned identical onset dates. The grid therefore '
 'resolves to four distinct configurations rather than twenty, and all four detected onset in every season.',
 'all five means produce weekly weights whose maximum pairwise total-variation distance is 0.0133, and '
 'in every season and at every window width the five means returned identical onset dates. The five '
 'kernels are not identical, their first weekly weights running from 0.9867 to 0.99998, but the grid '
 'resolves to four distinct onset outcomes rather than twenty, and all four detected onset in every season.')

# ============================================================
# E18  Results — the degenerate posterior is not exactly 5.0 in every case
#
# Recomputed from flux_data.csv against the committed estimator. At the reported
# onset week the posterior mean is exactly 5.0 for 12-17y in 2014/15 and
# 2015/16, where total infectiousness is zero, and 4.9539 for 6-11y in 2014/15,
# where an isolated admission on 1 October contributes 0.0018596 through the
# tail of the kernel six weeks later. The maxima reproduce exactly at
# (1 + sum I)/0.2 in all three. Also qualified: the zero in the denominator is
# the value the implementation computes by CDF subtraction; evaluated through
# the survival function the same quantity is about 1.8e-18, so "no
# infectiousness" is a property of the computation rather than of the kernel.
# ============================================================
ed.replace(P[67],
 'Where the current week is also empty, the posterior mean is 1/0.2 = 5.0; where it carries the first '
 'sustained admissions of the season, the posterior mean is (1 + ΣI)/0.2, which is the source of the '
 'reported maxima: all three affected channel-seasons satisfy this exactly, at 49,005, 26,005 and 27,505.',
 'Where the current week is also empty, the posterior mean approaches 1/0.2 = 5.0, reaching it exactly '
 'in the two 12–17 year channel-seasons and 4.95 in the 6–11 year 2014/15 channel, where a single '
 'isolated admission six weeks earlier still contributes 0.0019 through the tail of the kernel. Where '
 'the current week carries the first sustained admissions of the season, the posterior mean is '
 '(1 + ΣI)/0.2, which is the source of the reported maxima: all three affected channel-seasons satisfy '
 'this exactly, at 49,005, 26,005 and 27,505, the preceding weeks contributing no infectiousness at the '
 'precision the implementation computes.')

# ============================================================
# E19  Results — the amplitude claim its own list refutes
#
# "Concentrated on low-amplitude and multi-wave seasons" is contradicted by the
# enumeration that follows it: 2014/15 is the highest-amplitude season in the
# set at peak 38.6% and 2018/19 the third-highest at 29.9%. This is the same
# false claim as the heading corrected in E9, surviving one sentence lower.
# ============================================================
ed.replace(P[67],
 'The overall advantage was not statistically significant, but what stands out is that the advantage '
 'showed up specifically on the difficult seasons where the effect sizes were large. The advantage was '
 'concentrated on low-amplitude and multi-wave seasons: +63 days (2024/25, peak 10.5%), +42 days '
 '(2016/17, multi-wave), and +21 days (2014/15, 2018/19).',
 'The overall advantage was not statistically significant, but what stands out is that where the '
 'advantage appeared it was large rather than marginal. The four seasons in which admissions led do not '
 'share an amplitude or a wave structure: +63 days (2024/25, the lowest-amplitude season at peak 10.5%), '
 '+42 days (2016/17, multi-wave), and +21 days each in 2014/15 and 2018/19, which are the '
 'second- and third-highest-amplitude seasons in the set at 38.6% and 30.0%.')

# ============================================================
# E21  Author Summary — the same unsupported characterisation
#
# "On the most difficult seasons" is the plain-language form of the claim
# corrected in E9 and E19, and it fails for the same reason: the four seasons in
# which admissions led include the second- and third-highest-amplitude seasons in
# the set. Unrevised text, so ours to correct. The replacement states the count
# and the direction, which is what the Wilcoxon table supports, and softens the
# recommendation to match a test that does not reach significance.
# ============================================================
ed.replace(P[24],
 'Hospital admissions, especially for adolescents, provided earlier onset detection than laboratory '
 'positivity on the most difficult seasons, suggesting that admission-based signals should be '
 'incorporated into multi-pathogen surveillance systems.',
 'Hospital admissions, especially for adolescents, detected onset earlier than laboratory positivity '
 'in four of the eight influenza seasons examined and later in none, which suggests that '
 'admission-based signals are worth evaluating as a complement in multi-pathogen surveillance systems.')

# ============================================================
# E22  Discussion — and again, one section further on
#
# "On low-amplitude influenza seasons" is the third site of the same claim.
# Unrevised text. Replaced with the count, the direction, and the fact that the
# seasons in which admissions led do not line up with amplitude.
# ============================================================
ed.replace(P[84],
 'Age-stratified hospital admissions, particularly for adolescents (12–17 years), provided earlier '
 'onset detection than laboratory positivity on low-amplitude influenza seasons.',
 'Age-stratified hospital admissions, particularly for adolescents (12–17 years), provided earlier '
 'onset detection than laboratory positivity in four of the eight influenza seasons examined and later '
 'detection in none, without a consistent relationship to season amplitude.')

# ============================================================
# E20  Results — exact permutation p-values
#
# n = 8 and n = 10 admit exhaustive enumeration: 40,320 and 3,628,800
# permutations, computed here in seconds. The exact two-sided values are
# 0.8946 and 0.5161. Reporting them removes the seed from the reported number
# altogether, and corrects influenza from 0.90, which was a Monte Carlo estimate
# of a quantity that rounds to 0.89.
# ============================================================
ed.replace(P[69],
 '−0.06 (n = 8, permutation p = 0.90), and within RSV it is +0.23 (n = 10, p = 0.52)',
 '−0.06 (n = 8, exact permutation p = 0.89), and within RSV it is +0.23 (n = 10, exact p = 0.52)')

ed.replace(P[69],
 '(Fig. 2; correlations and permutation p-values in snr_within_pathogen_stats.csv, 20,000 permutations, seed 0)',
 '(Fig. 2; correlations and p-values in snr_within_pathogen_stats.csv, enumerated over all 8! and 10! '
 'permutations rather than sampled)')

# ============================================================
# R1  Reference [8]: Lessler -> Carrat
# ============================================================
ed.replace(P[117],
 'Lessler J, Reich NG, Brookmeyer R, et al. Incubation periods of acute respiratory viral infections: a systematic review. Lancet Infect Dis. 2009;9(5):291–300.',
 'Carrat F, Vergu E, Ferguson NM, Lemaitre M, Cauchemez S, Leach S, Valleron AJ. Time lines of '
 'infection and disease in human influenza: a review of volunteer challenge studies. Am J Epidemiol. '
 '2008;167(7):775–785.')

# R1b  the in-text use of [8] for the 5-day infectious period
ed.replace(P[62],
 '(5-day infectious period, consistent with influenza viral shedding duration estimates [8])',
 '(5-day infectious period, against a pooled viral-shedding duration of 4.80 days, 95% CI 4.31 to '
 '5.29, from volunteer challenge studies [8]; viral shedding is used here as a proxy for the '
 'infectious period, and those data are from adults only)')

# ============================================================
# R2  New references 16-18
# ============================================================
# The run formatting is taken from reference 15 for all three, not from the
# previous new paragraph, so the chain cannot carry anything forward.
REF_MODEL = P[124]
last = P[124]
for t in [
 '16. Cowling BJ, Fang VJ, Riley S, Malik Peiris JS, Leung GM. Estimation of the serial interval of '
 'influenza. Epidemiology. 2009;20(3):344–347.',
 '17. Nash RK, Bhatt S, Cori A, Nouvellet P. Estimating the epidemic reproduction number from '
 'temporally aggregated incidence data: a statistical modelling approach and software tool. PLOS '
 'Comput Biol. 2023;19(8):e1011439.',
 '18. Ogi-Gittins I, Hart WS, Song J, Nash RK, Polonsky J, Cori A, Hill EM, Thompson RN. A '
 'simulation-based approach for estimating the time-dependent reproduction number from temporally '
 'aggregated disease incidence time series data. Epidemics. 2024;47:100773.',
]:
    last = new_para_after(last, t, run_model=REF_MODEL)

# ============================================================
tree.write(docpath, xml_declaration=True, encoding='UTF-8', standalone=True)
if os.path.exists(OUT):
    os.remove(OUT)
with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as zo:
    for name in ORDER:
        zo.write(os.path.join(WORK, name), name)

print('edits applied: %d' % len(ed.log))
for kind, old, new in ed.log:
    print('  %-8s %s' % (kind, old[:72].replace('\n', ' ')))
print('wrote', OUT)
