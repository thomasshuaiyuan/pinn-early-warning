# Kimberly Edwards's 33 comments, scored one by one — 7 November 2026

Checked against the built submission copy, not from memory. The short answer first, because it is
not the flattering one.

**Her 233 edits are fully merged. Her 33 comments are mostly preserved, not answered.** Two were
already answered by text she had not reached; three are substantially done; five are escalated to
Vijay with the evidence attached; three wait on figure work that is deliberately deferred; and
**twenty are carried into the editing copy and otherwise untouched.** Carrying a comment is not
the same as addressing it, and this document does not pretend otherwise.

Ten of the twenty are cheap — a sentence or a word each — and are listed at the end.

## Scoring key

**DONE** the text now answers it · **PARTIAL** answered in some places, not others ·
**ESCALATED** a decision, put to Vijay with evidence, text unchanged ·
**DEFERRED** waits on figure work under `[TY-6]` · **CARRIED** her comment is in the file and
nothing else happened.

## The 33

| # | Her comment, in short | Status | What we actually did |
|---|---|---|---|
| 1 | Does CHP use a % increase, not a threshold? | CARRIED | Nothing. Her own source answers it: the CHP release she quotes says positivity "exceeded the baseline levels (4.94 per cent…)", i.e. a level, not an increase. One sentence would close it. |
| 2 | "4.94% was reconstructed from the CHP Flu Express dataset" — challenged, with the CHP press release attached | ESCALATED | Text unchanged, deliberately: this is `[VD-5]`, Vijay's own comment on the same sentence says "This shouldnt be here", and the wording is his. Her URL is now in `VD_INPUT_SHEET.md` and in the R3 comment. Strongest single contribution of her review. |
| 3 | Part of this Introduction paragraph could move to the Discussion | CARRIED | Nothing. Introduction and Discussion are Vijay's half by the April 2026 division. |
| 4 | The onset-rule preamble should move to Methods | CARRIED | Nothing. Note this is my prose, added 5 November, and the adversarial brief had already named it as the one block nobody had reviewed. She is probably right. |
| 5 | "six of eight?" on the season count | **PARTIAL, and it got worse** | Her Author Summary edit was adopted (eight + ten). But Tables 1 and 2 both carry six influenza seasons, Results says EpiEstim detected onset in all six, and PINN was never run on RSV. See the warning below. |
| 6 | Post-hoc season classifications → Discussion, definitions → Methods | CARRIED | Nothing. The sentence still sits in Results and still says "assigned post hoc". |
| 7 | Define γ at first mention; keep nomenclature consistent | PARTIAL | First use does read "the clamped recovery rate: with γ = 0.1/day (10-day infectious period)". But the symbol γ is used 26 times and the word "gamma" 5 times in the same document. Not reconciled. |
| 8 | Sensitivity analysis later, or to supplementary | CARRIED | Nothing. |
| 9 | Split Table 1 by pathogen, or make it a figure | CARRIED | Nothing. A structural call. |
| 10 | If age groups are tied, say which ones | **NOT DONE** | We restored the generic legend "Multi = multiple age groups tied" she had deleted, which preserves the definition but declines her request. The data exists: 2018/19 is 6–11y and 12–17y, 2024/25 is 0–5y and 6–11y. |
| 11 | Use one y-axis scale across all three Fig 1 panels | DEFERRED | Figure regeneration is waived until a provisional accept, under `[TY-6]`. |
| 12 | "RSV behaves differently… follows from the reporting interval rather than the biology" is presumptuous | ESCALATED | Text unchanged. Committed to answering in the Discussion before submission. This is the claim the cover letter leads on, so it is the most consequential comment in her review after #2. |
| 13 | "At 7.5 days the specified mean…" — opening unclear | CARRIED | Nothing. |
| 14 | Do not name analysis scripts in the running text | PARTIAL | Three removed: the SI-sensitivity CSV, the SNR stats file (replaced with the method in words), and the pre-onset script (replaced with "per-season values in S2 Table"). **Eleven remain**, including `si_invariance_check.py`, `simulation_study.py`, `scrape_chp_respiratory.py`, `wilcoxon_admissions.py`, `final_supplementary.py` and four CSVs. |
| 15 | Define every variable at first use (on β(t)·S(t)) | **NOT DONE** | The text still reads "since R(t) = β(t)·S(t)/γ" with β and S undefined. |
| 16 | How are "stable" seasons defined? | **NOT DONE** | "onset date ranges of 7–20 days for stable seasons (3/6)" still carries no definition. |
| 17 | Keep abbreviations consistent (12–17y vs 12–17 year) | **NOT DONE** | One "12–17y" against seven "12–17 year". |
| 18 | "there's no way one person could infect 100,000 people!" | **DONE, before she wrote it** | The bracketed note already quarantines those three channel-seasons, and the mechanism paragraph explains that `sum_L = 0` leaves the prior's rate as the whole denominator. Her comment is answered by text she had not reached. Worth telling her. |
| 19 | "see above" on the same degenerate fits | DONE | As #18. |
| 20 | Add all-ages, 0–5y and 65+ bars to Fig 2 | DEFERRED | `[TY-6]`. |
| 21 | "where is this published?" on the 4.94% | ESCALATED | No citation added to the text yet. She supplied the source herself; adding it is one reference and is held with `[VD-5]` because the surrounding sentence is Vijay's. |
| 22 | Confounders, not "unidentified" — population immunity, variant transmissibility | **NOT DONE** | "the drivers of within-pathogen variation remain unidentified" is unchanged. A one-sentence fix. |
| 23 | Did you look at dominant subtype (H1/H3/B, RSV-A/B)? | CARRIED | Nothing. A real research question; the subtype columns exist in `flux_data.csv`. |
| 24 | All hospitalisations, or ILI-related? | **NOT DONE** | Answerable from Methods, which says "influenza-associated hospital admission rates per 10,000 population". One clause in the Results paragraph would close it. |
| 25 | Show standard error not SD; reorder age groups; ILI on its own panel | DEFERRED / PARTIAL | The panel work is `[TY-6]`. The SD-to-SE change in the text was not made. |
| 26 | Assumptions violated, p-values test-dependent, cut significance testing | ESCALATED | Text unchanged. It aligns with the project's own D9 unit-of-analysis rule, so it is a decision that reaches beyond this paper. |
| 27 | What does "specimen mix" mean? | **NOT DONE** | Unchanged. |
| 28 | Bootstrap CI too narrow for the unit of analysis; use a block bootstrap | ESCALATED | Text unchanged. This one needs a rerun, not an edit. |
| 29 | Move the Hu et al. comparison to the Discussion | CARRIED | Nothing; still in Results. |
| 30 | Number supporting figures and tables separately | **WITHHELD, now consistent** | Not done, by decision. Her in-text renumbering had left the same figure cited as both "S1 Fig" and "S5 Fig"; that is fixed and it is "S5 Fig" throughout, matching the caption and `S5_Fig.tif`. |
| 31 | Add detail on how CHP collects these data, and justify representativeness | CARRIED | Nothing. |
| 32 | Testing denominators are on the CHP website (URL supplied) | CARRIED | Nothing. The URL is in her comment in the file. |
| 33 | Cite every supporting item, in order | CARRIED, UNVERIFIED | Nothing, and we have not checked whether they are cited in ascending order. |

## One warning, and it is the most important line here

**Her fix to the season count may have introduced an error.** The Author Summary now reads "Two
methods were evaluated across eight influenza and ten RSV peaks". Eight is the number of influenza
seasons in the dataset and in the admissions and signal-to-noise analyses. It is not the number
the two estimators were evaluated on: Tables 1 and 2 both carry six influenza seasons, Results
says EpiEstim detected onset in all six, and PINN was not run on RSV at all.

Six plus ten is true of the primary evaluation. Eight plus ten is true of the study. The sentence
says "two methods were evaluated", so six plus ten is the honest reading — but the number is
Thomas's and the sentence is about what the paper claims, so it is not a session's to pick. The
Q1 comment in the editing copy now states this in full. **Her question was right and her answer
may not be.**

## What a merge of someone's edits cannot do

Her edits were mechanical: apply them and they are done. Her comments are of four kinds and only
one kind can be merged at all.

Corrections with an obvious fix (two of thirty-three). Questions whose answer is in the document
already (two, both the 100,000 one). Decisions about what the paper claims or where material sits
(eleven). And requests that need new work — a figure regenerated, a bootstrap rerun, a subtype
analysis (eight). The remaining ten are small text fixes nobody has done yet.

So the honest score is: **we merged her review well and answered it badly.** The merge was the
part that could be automated, and it was.

## The ten cheap fixes, if you want them done before this goes further

1. Define β and S where R(t) = β(t)·S(t)/γ first appears (#15).
2. Define "stable seasons" at its one use (#16).
3. Make "12–17y" read "12–17 year" (#17).
4. Replace "remain unidentified" with named confounders: population immunity and variant
   transmissibility (#22).
5. Say "influenza-associated hospital admissions" in the admissions paragraph (#24).
6. Replace "specimen mix" with "the mix of co-circulating viruses" (#27).
7. Name the tied age groups in the Table 1 footnote (#10).
8. Reconcile "gamma" and γ to one form (#7).
9. Strip the remaining eleven script and data filenames from the running text (#14).
10. Answer her % increase question in one clause, citing the release she found (#1).

None of these touches Vijay's prose except where noted, and none changes a number. Say the word
and they go in as tracked changes under Thomas's name, with the build checks extended to hold
each one.
