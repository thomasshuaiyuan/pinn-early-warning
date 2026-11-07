# Kimberly Edwards's review, assessed — 6 November 2026

File: `2026-11-06_early-warning_PLOSCB_SUBMISSION-READY_KME.docx`, 1.99 MB, 31 pages,
8,661 words, worked 12:17 to 18:13 on 6 November.

Her pass: **190 insertions, 126 deletions, 26 run-format changes, 5 moves, 8 paragraph-mark
changes, 33 comments, and the four figures inserted into the text.**

---

## 1. Did she see Vijay's comments? No.

Three independent lines of evidence.

**The file carries none of them.** All 33 comments in it are authored "Kimberly Edwards". Her
base text is the **5 November SUBMISSION-READY copy**, identified by four markers it has and the
editing copy does not: the single `Data Availability Statement` heading, the old superscripts
`Thomas Yuan1,2, Vijaykrishna Dhanasekaran1,*`, the `[TY-3]` bracket, and Methods already sitting
after the Discussion rather than as a tracked relocation. That copy is built with every comment
stripped, so there was nothing of his in it to see.

**She re-raises his points as new questions.** Her comment on *"the value of 4.94% used here was
reconstructed from the CHP Flu Express dataset"* sits on **exactly the same sentence** as Vijay's
comment *"This shouldnt be here."* She asks it fresh, with her own evidence, rather than replying
to him. The same happens on *"threshold value"*, where he had written *"i.e. what does this
drive?"* and she writes *"I thought they used % increase?"* Two reviewers landing on the same two
sentences independently is strong corroboration; it is also what not having seen his markup looks
like.

**One thing that looks like his markup and is not.** Her file contains six paragraph-mark
insertions attributed to **"Vijay"**, dated 20 August 2026 09:51, and `people.xml` lists him. They
are not his comments and not his edits. They are an artifact of **a defect in my build**, now
fixed: the submission copy was leaving 19 `w:moveTo`/`w:moveFrom` paragraph-mark revisions inside
`w:rPr`, because step 1 stripped only `ins`/`del` at that level, and the "no tracked changes"
check only counted `ins`/`del` and so passed on a file that held 19 move revisions. The moves were
left unbalanced — 18 `moveTo` against 1 `moveFrom` — and Word repairs an unbalanced move on save
by downgrading it to a plain insertion, keeping the original author and date. Hence six marks in
his name in a file that should have had none.

**Fixed and reinstalled.** `build_plos3.py` now strips `moveTo`/`moveFrom` in `w:rPr` as well, and
the submit-mode check asserts **zero revision elements of any kind** — moves, range markers and
format changes included — rather than zero insertions and deletions. Rebuilt, verified at 0, and
the OneDrive copies replaced. The previous pair is in
`_superseded/2026-11-06b_pre-move-fix/`.

**What cannot be established from the file**: whether she also had the FOR-EDITING copy open
alongside. Nothing in her document shows it either way; the evidence above says only that she did
not work *in* it.

**A correction worth carrying.** The project record describes "VD's 26 comments". In the editing
copy exactly **4 comments are authored "Vijay"**; the other 22 of the inherited 26 are Thomas's
own replies and notes from v9 and v10. His four are: the alternative title; *"the practical
utility of epidemic onset in HK or other regions is not quite clear, affecting impact of study"*;
*"i.e. what does this drive?"*; and *"This shouldnt be here."*

---

## 2. Would editing to her preferences still give good changes? Mostly yes, with six exceptions.

### Where she and Vijay overlap, they agree

Of her 129 deletions, a positional test against a per-character authorship map of v11 puts **26 in
text Vijay wrote or moved, 26 in Thomas's, 64 in the v10 base, and 13 unresolvable**. (A substring
test gave a higher number for his and was wrong: short strings like "rather" or "where" match
anywhere in his prose. The positional figure is the one to use.)

Of the 26 in his text, 16 are five characters or longer, and after discounting alignment artifacts
on text the build inserted after v11, the genuine incursions into his prose are five:

| Where | What she does to his words |
|---|---|
| Abstract | rewrites his study-description clause: *"on routine weekly Hong Kong surveillance data covering influenza and RSV seasons labelled 2014/15 to 2024/25, drawn from surveillance records spanning January 2014 to March 2026"* → *"on routine weekly influenza and RSV surveillance from January 2014 to March 2026"* |
| Abstract | *"seasons in which EpiEstim led had higher signal-to-noise ratios"* → *"performed better in seasons with higher signal-to-noise ratios"* |
| Introduction | *"rather than an incidence level"* → *"as opposed to the date at which a baseline incidence threshold is surpassed"* |
| Results | drops *"for three seasons"* and *"post-COVID"* from his multi-restart sentence |
| Methods | removes the in-text variable codes and filenames he wrote: `(ILI_PMP)`, `(ILI_FMC)`, `(data_dictionary_flu_express.csv)`, `supplementary_table_S1_seasons.csv` |

None of these contradicts him on substance, and the Abstract one is an improvement: it removes the
season-label/date-range mismatch that `[TY-4]` existed to fix, and leaves the abstract saying
January 2014 to March 2026, which now agrees with the title's 2014–2026. **But they are his words,
so the Part I rule applies: they go to him as a question with her edit attached, not as something
accepted on his behalf.** The Methods filename removals are the cleanest case to put to him,
because her reasoning is in a comment and it is a journal-style point rather than a disagreement.

### Six things to fix before adopting her file

1. **A number went missing.** Results, RSV paragraph: *"led the threshold in only 4"* became
   *"predicted ahead of the  percent positive threshold in only four"* — the threshold value is
   gone and a double space is left where it was. An unfinished edit, not a decision.
2. **A range became a point value.** *"onset dates shifted by 0–7 days for most seasons"* became
   *"shifted by 7 days"*. That changes a reported result and must go back to 0–7.
3. **A result left the Fig 2 caption.** She deleted *"Admissions led positivity in four of the
   eight seasons and were later in none; the paired test on the 12–17 year channel is not
   significant (W = 10.0, one-sided p = 0.0625, which is the exact test's floor at four non-zero
   pairs)"*. This is deliberate — it follows her comment asking to cut significance testing in
   favour of effect sizes and intervals — but it is a decision about what the paper reports, not a
   copy-edit, and the four-of-eight count is the finding Vijay called "a very nice, practical
   angle".
4. **`[TY-3]` was deleted, not answered.** The provenance-date query is gone from her file while
   the inconsistency stands: Methods still says the site was accessed 15 March 2026 and the last
   data row is the week to 21 March 2026. Reinstate or resolve.
5. **The supporting-information renumbering is half done.** She renamed the caption to `S1 Fig`
   and commented that figures and tables should be numbered separately — which is the change the
   checklist recommended and we had not applied — but `S5 Fig` survives in the in-text citations.
   Finish it or revert it; do not ship both.
6. **A unit changed in the Author Summary.** *"16 influenza and RSV seasons"* became *"eight
   influenza and ten RSV peaks"*. The count is now right and settles the Q1 sixteen-against-
   eighteen question at 8 + 10 — but "peaks" is a different unit from the "pathogen-seasons" used
   everywhere else, and one word should govern throughout.

Two of her own comments she did not execute: she asks not to name analysis scripts in the text,
and `si_invariance_check` and `simulation_study.py` are still there.

### What she corroborates, independently

- **The 4.94% threshold question** — the oldest open item, `[VD-5]`, outstanding since 30 October.
  She challenges the sentence calling it reconstructed *and supplies the primary source that
  settles it*: the CHP press release reading *"have exceeded the baseline levels (4.94 per cent
  and 0.27 cases per 10 000 population respectively)"*. That is the citation `[TY-1]`-adjacent
  recommendation R3 needed, from a reader with no stake in it.
- **The degenerate admissions fits** — *"there's no way one person could infect 100,000 people!"*
  She found defect D cold, from the text alone.
- **The season count** — her "six of eight?" and the 8 + 10 rewrite are the same inconsistency
  Q1 raises.
- **The Results preamble should be in Methods.** That preamble is mine, added on 5 November, and
  the adversarial brief named it as the highest-value target precisely because nobody had reviewed
  it. The first independent reader says it is in the wrong section.
- **Supporting information numbering**, which the checklist flagged and we left unapplied.

### Where she pushes back on the paper's framing

Her comment on *"RSV behaves differently, and the difference follows from the reporting interval
rather than from the biology"*: **"this sounds presumptuous."** RSV causes prolonged infections of
up to two months with wide between-person variation, so the duration of infectiousness, and hence
the serial interval, is itself much more variable. **This is the claim the cover letter leads on.**
It is not refuted — the discretisation result stands as arithmetic — but a referee with her
knowledge will say the same thing, and the sentence claims more than the arithmetic supports. Her
objection is cheaper to answer now than after submission.

---

## 3. Her edit style

**She reviews like a journal referee, not a copy-editor.** Eight patterns, each with examples.

1. **Numbers under ten are spelled out in prose.** `5 of 6` → `five of six`, `3 of 6` → `three of
   six`, `10 RSV seasons` → `ten RSV seasons`. About eighteen instances, applied consistently.
2. **Table headers must carry units and full words.** `Peak%` → `Peak %(+)`; `Thresh.` → `Date
   %(+) exceeded threshold (MM-DD)`; `Epi lead` → `EpiEstim lead time (days)`; `Adm lead` →
   `Age-stratified hospital admission lead time (days)`; `Type` → `Single vs. multi-wave season`;
   `2023 S` → `2023 spr` and `2023 sum`.
3. **Captions are a short title plus legend keys; everything else becomes a lettered footnote.**
   She cut the Table 1 caption from 90 words to *"Detection of epidemic onset across influenza and
   RSV seasons. N/D = not detected. — = not available. Blue shading, influenza; salmon, RSV."* and
   moved the method detail into footnotes a, b and c, adding the markers to the column heads.
4. **She relocates material rather than rewriting it.** Five comments are move instructions:
   preamble to Methods, post-hoc season classifications to the Discussion with the definitions in
   Methods, the Hu et al. comparison to the Discussion, a sensitivity analysis later or to
   supplementary, part of an Introduction paragraph to the Discussion.
5. **Statistical scepticism, and competent.** She flags violated normality and equal-variance
   assumptions, notes that p = 0.048 / 0.024 / 0.071 across three tests makes the result
   test-dependent, and asks for effect sizes, intervals and individual points instead of
   significance tests. On a bootstrap CI of 2.12–2.62 around a difference of 2.37 she works out
   that it is too narrow for the unit of analysis, names autocorrelation of weekly values as the
   cause, and asks for a block bootstrap or a cluster-robust approach. **That is the same defect
   the project closed as D9 — pseudo-replication from treating nested units as independent — found
   by a reader who has never seen D9.**
6. **Domain pushback wherever biology is asserted.** The RSV serial-interval objection above;
   *"confounders — not captured by the model, but not unidentified"*, naming population immunity
   and variant transmissibility; and an unprompted research question, whether the dominant subtype
   (H1/H3/B, RSV-A/B) in each season explains anything.
7. **Housekeeping she applies without being asked.** Define every variable at first use; keep
   abbreviations consistent; number supporting figures and tables separately and cite them in
   order; do not name analysis scripts in the text, reference the supplementary file or the Methods
   subsection instead; cite the CHP source for the data-collection description; and she supplies
   the CHP testing-denominator URL unprompted.
8. **Figures.** She inserted all four into the text, and commented on their design: consistent
   y-axis scales across panels so amplitude differences are visible, add the all-ages, 0–5y and
   65+ bars, show standard error rather than standard deviation, reorder the age groups, split ILI
   rates into their own panel.

**One difference from Vijay worth knowing before merging both.** He tightens: *"regardless of
whether"* becomes *"even when"*. She prefers explicitness and is willing to spend words on it:
*"this did not work"* becomes *"PINN could not accurately predict epidemic onset"*; *"by
estimating the time-varying reproduction number rather than an incidence level"* becomes *"through
estimation of the time-varying reproduction number as opposed to the date at which a baseline
incidence threshold is surpassed"*. Both are defensible. They pull in opposite directions, and in
the places where her edit lands inside his sentence, that is the real conflict rather than any
disagreement about the science.

---

## Recommended order

1. Fix the six mechanical problems in her file (items 1–6 above). None is a judgement call.
2. Take her 4.94% source to Vijay. It closes `[VD-5]`, the oldest open item, and it arrived with a
   primary source attached.
3. Put the five incursions into his prose to him as questions with her edits attached, in one
   list. Do not accept them silently.
4. Decide the Fig 2 caption question — whether the W and p leave the caption — with him, since the
   four-of-eight admissions count is the finding he singled out.
5. Answer her RSV serial-interval objection in the Discussion before submission, not after.
6. Her role is still unsettled, and it is now a live authorship question rather than a courtesy
   one: 316 tracked changes and 33 substantive comments is a contribution that CRediT has
   categories for. Vijay's call.
