# Edits that answer a comment — 7 November 2026

Twenty-one edits. **Each one exists because a named reviewer asked for it**, and each carries its
source and its evidence, in three places: this table, a paragraph per edit under Open queries in
the editing copy, and the author name on the tracked change itself.

Authorship splits by whose comment is being answered, so the Review pane filters to one reviewer:

| Author on the tracked change | Marks | Answers |
|---|---|---|
| `Thomas Yuan — answers KME` | 47 | Kimberly Edwards's comments of 6 November |
| `Thomas Yuan — answers VD` | 3 | Vijay's comments |

Build state: **139 checks pass, exit 0**, 21 of 21 edits anchored, 33 of 33 of her comments still
carried, and the editing copy with the recommendations rejected still reproduces the submission
copy exactly.

**Nothing here changes a number**, and nothing rests on a source this session could not read.

## The twenty-one

| id | Answers | Change | Evidence it rests on |
|---|---|---|---|
| `KME-15` | KME | `since R(t) = β(t)·S(t)/γ, a lower γ inflates R(t)` → `since R(t) = β(t)·S(t)/γ, where β(t) is the time-varying transmissio…` | Neither β nor S is defined anywhere in the manuscript: "transmission rate" and "susceptible fraction" each occur zero times. The definitions added are the standard SEIR ones already implied by the Methods. |
| `KME-16` | KME | `showed onset date ranges of 7–20 days for stable seasons (3/6).` → `showed onset date ranges of 7–20 days for the three seasons in which…` | The comment already in this file answering VD’s point 2 states that the committed multi-restart results support three stable seasons, 2014/15, 2018/19 and 2023 summer, at 5/5 detection with onset ranges of 7–20 days. The definit… |
| `KME-17` | KME | `for 12–17y and 6–11y admissions in` → `for 12–17 year and 6–11 year admissions in` | One occurrence of "12–17y" against seven of "12–17 year" in the same manuscript. |
| `KME-22` | KME | `and the drivers of within-pathogen variation remain unidentified.` → `and the drivers of within-pathogen variation are not identified by t…` | Her own wording, narrowed to what this design can and cannot separate. No claim is made about the size of either candidate. |
| `KME-24` | KME | `EpiEstim was applied to five age-stratified hospital admission signals` → `EpiEstim was applied to five age-stratified influenza-associated hos…` | Materials and Methods already defines the series as "influenza-associated hospital admission rates per 10,000 population". The word is carried into Results so the paragraph answers her where she asked. |
| `KME-27a` | KME | `as testing practice, specimen mix, or population immunity change` → `as testing practice, the mix of specimens submitted for testing, or …` | Her reading is one possibility and the sentence does not settle it, so the phrase is spelled out as what the surveillance series actually varies in, which specimens are submitted for testing. Her alternative reading is not adopt… |
| `KME-27b` | KME | `changes in testing behaviour and specimen mix that reduce measured p…` → `changes in testing behaviour and in the mix of specimens submitted t…` | As KME-27a. |
| `KME-10` | KME | `Multi = multiple age groups tied.` → `Multi = two age groups tied for the earliest onset (2018/19, 6–11 an…` | The comment already in this file names them from epiestim_admissions_results.csv: 2018/19, 6–11y and 12–17y both at 2018-10-17; 2024/25, 0–5y and 6–11y both at 2024-09-04. |
| `KME-7a` | KME | `across all gamma values tested` → `across all γ values tested` | The symbol γ is used 26 times and the word "gamma" five times. Two of the five name the parameter and become the symbol; the three that name the Gamma distribution stay words, and one gains the capital the other already has. |
| `KME-7b` | KME | `at all three gamma values (1.16, 1.06, 1.05)` → `at all three γ values (1.16, 1.06, 1.05)` | As KME-7a. |
| `KME-7c` | KME | `the rate parameter of the gamma (1, 0.2) prior` → `the rate parameter of the Gamma(1, 0.2) prior` | The same document writes "Gamma(0.001, 0.001)" and "gamma (1, 0.2)". |
| `KME-14a` | KME | `(invariance check and full results at si_invariance_check.py and rsv…` → `(invariance check and full results in the repository)` | Every filename below is reachable from the Code availability statement, so removing it from the running text loses nothing a reader can act on. Where a supporting item carries the same material, it is named instead. |
| `KME-14b` | KME | `A data dictionary for all 31 CHP Flu Express variables (data_diction…` → `A data dictionary for all 31 CHP Flu Express variables is provided a…` | S3 Table is the data dictionary, so it is named instead of the file. |
| `KME-14c` | KME | `using a custom scraper (scrape_chp_respiratory.py, committed to the …` → `using a custom scraper committed to the repository` | As KME-14a. |
| `KME-14d` | KME | `A supplementary table (S1 Table) with exact start and end dates, pea…` → `S1 Table gives exact start and end dates, peak timing, dominant subt…` | S1 Table is that supplementary table, so the sentence names it once instead of naming it and its source file. |
| `KME-14e` | KME | `as single-wave (script: final_supplementary.py).` → `as single-wave (classification script in the repository).` | As KME-14a. |
| `KME-14f` | KME | `(script wilcoxon_admissions.py; saved output wilcoxon_admissions_res…` → `(script and saved output in the repository)` | As KME-14a. |
| `KME-14g` | KME | `coincide numerically: simulation_study.py seeds each scenario separa…` → `coincide numerically: the simulation script seeds each scenario sepa…` | As KME-14a. |
| `KME-14h` | KME | `Code is available at simulation_study.py in the repository (seeds fi…` → `Code is available in the repository, with seeds fixed per scenario a…` | As KME-14a. |
| `KME-14i` | KME | `Full results at pinn_multi_restart_results.csv in the repository.` → `Full results are in the repository.` | As KME-14a. |
| `VD-146` | VD | `CHP does not publish the exact threshold value or its derivation; th…` → `*(deleted)*` | Acting on it rather than only replying, after two rounds in which it was carried. The sentence is also wrong by the manuscript’s own account: it says CHP does not publish the threshold value, while Results says "the 4.94% publis… |

## What was deliberately not done, and why

**Her question about whether CHP declares on a percentage increase rather than a level, and her
"where is this published?"** Both turn on the Hong Kong government press release she quoted. That
URL came to this session inside her document, not from the user, so it is outside the fetch
provenance set and could not be retrieved. **Under the project's hardest rule an unverified source
does not enter a document**, so nothing is cited to it and neither question is answered in the
text. Both remain open, and both are one verification away: open the URL, confirm the sentence,
and the citation can be added.

**Vijay's other three comments.** His "This shouldnt be here" is now acted on rather than replied
to, after two rounds carrying it. The remaining three are not edits a session can make:

| His comment | Why it is still open |
|---|---|
| The alternative title | Thomas has already replied that he would like to adopt it; it is a joint decision and the reply is in the file awaiting his word. |
| "the practical utility of epidemic onset in HK or other regions is not quite clear" | The Introduction and Discussion are his half by the April 2026 division, and answering it means asserting what a threshold crossing triggers operationally, which needs a source this session does not have. |
| "i.e. what does this drive?" | Same sentence, same problem. A clause naming the downstream response actions would answer it, and every version of that clause is an unsourced claim about CHP practice. |

**The two inconsistencies her edits introduced** are flagged in the editing copy rather than
resolved, because both sit in Vijay's prose or in a claim that is his to make: the Author Summary
now says the two methods were evaluated across eight influenza seasons when Tables 1 and 2 carry
six, and the Abstract's results sentence spells numbers out in her half and not in his.

## How to check any of this

Every edit's `old` and `new` string is in `followup_edits.py` in the build directory, with its
source and evidence as data rather than prose. The build refuses to run if any of the twenty-one
fails to anchor exactly once, so the file and the document cannot drift apart.

---

## Verification note, 7 November: the second source does not say what it was reported to say

`https://www.chp.gov.hk/en/statistics/data/10/641/642/2274.html` was relayed to this session as
carrying a column header **"No. of specimen tested"**, weekly counts of roughly 7,000 to 11,000
specimens, four numbered remarks, and a last revision date of **2026/11/04**.

Read first-hand, that page is **an index, not a table**. Its entire content below the heading is
one sentence — *"The information is based on testing for respiratory pathogens in clinical
specimens received during the designated week / month"* — followed by year links under five
pathogen groups: Influenza viruses, Parainfluenza viruses, Coronaviruses (2023 and 2024 only),
Other respiratory viruses, and Mycoplasma pneumoniae. It carries **no column headers, no specimen
counts and no numbered remarks**, and its stated last revision is **2026/01/07**.

So the relayed description is of a different page: one of the per-year tables the index links to,
most likely Influenza viruses 2026 at `.../7101.html`. The description may well be accurate of
that page. It is not accurate of the URL it was attached to.

**Nothing changes in the manuscript as a result.** `KME-32` was deliberately written to withdraw
an unsupported non-existence claim without asserting a replacement, precisely because this source
was unverified. That decision is what kept the error out of the text. Had the Methods been
rewritten on the relay to say denominators are published at that URL, the manuscript would now
cite an index page for a column it does not contain.

**Still open**: whether CHP publishes a weekly specimen denominator, and where. The check is a
first-hand read of a per-year table page, quoting its header and its remarks. Until that happens
the manuscript says only what the Flu Express series supports.

**And the 6.69 against 6.19 gap is not recorded**, because the 6.19 comes from a table this
session has not read. The rule it illustrates stands on its own and is worth keeping whatever the
numbers turn out to be: a figure from a press release and a figure from a surveillance table are
different quantities with different revision histories, and neither corrects the other.
