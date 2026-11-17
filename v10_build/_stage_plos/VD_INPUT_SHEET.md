# What VD needs to supply — PLOS Computational Biology submission

> **Updated 11 November 2026** (recommendations converted from tracked changes to questions; see
> below). **Earlier update, 10 November 2026.** Kimberly Edwards returned the second half of her review —
> the Discussion and Methods she had not reached — on 10 November: 192 further tracked
> revisions and 15 further comments. A section on what in that is yours sits below, before
> the bracket list. **Everything else in this sheet is reproduced unchanged from
> 6 November**, so a mismatch anywhere else is this rewrite's fault rather than a change of
> position. Nothing has been sent to you or to her.

**Nothing in this copy rewrites your words or framing, and nothing is a tracked change you have
to reject.** Updated 11 November, under your note of 25 September ("ask before, not after"). The
title, Author Summary and Abstract recommendations were tracked changes until today; they are now
questions. Each is a Word comment authored **"Thomas Yuan — recommendation"**, anchored on the
sentence it concerns, with the proposed wording in full for you to take or leave in a word:

| Comment | What it asks |
|---|---|
| **[VD-6]** on the title | spell out respiratory syncytial virus, 189 of 200 characters |
| **[VD-7]** on the Author Summary | three changes converting it to first person, touching no number |
| **[Q1]** on "eight influenza and ten RSV peaks" | six plus ten or eight plus ten, and "peaks" against "pathogen-seasons" |

The Abstract's "an analytical reconstruction" is asked in the `[VD-5]` bracket and is not
touched.

**Everything else is bracketed**, because it is a blank to fill or a
decision with no proposed wording. Search for `[VD-` or `[TY-`: eight in the editing copy, four in
the submission copy. The label names the owner — **VD** is his, **TY** is Thomas's — and the build
counts them, so none can be lost.

| Bracket | Where it sits | What it needs |
|---|---|---|
| `[VD-1]` | Methods, ethics subsection | confirm or replace the ethics statement; name the determining body |
| `[VD-2]` | Acknowledgments | contributors who do not meet authorship criteria |
| `[VD-3]` | Open queries | the Highlights line on low-amplitude signals — a question, not an edit |
| `[VD-4]` | Open queries | the Highlights line on age-stratified admissions |
| `[VD-5]` | Open queries | the threshold consistency question, outstanding since 30 October |
| `[VD-6]` | On the title | specialist abbreviations in the title and abstract — **recommended wording supplied, not applied** |
| `[VD-7]` | On the Author Summary | PLOS requires first person and this is third person — **recommended conversion supplied, not applied** — plus sixteen seasons here against eighteen elsewhere |
| `[TY-1]` | Code availability | the Zenodo DOI for the code archive |
| `[TY-3]` | Methods, provenance | the access date that predates the last week of data |
| `[TY-6]` | Open queries | the figure files' embedded titles and unlabelled panels |

### `[VD-6]` and `[VD-7]` are recommendations, deliberately not edits

Both would rewrite words rather than correct a number, and the title, abstract and Author
Summary are not mine to rephrase. Each comment carries the proposed wording in full; nothing is
applied until you say so.

`[VD-6]` PLOS asks that the title avoid specialist abbreviations and that the abstract carry
none. The title uses RSV; the abstract introduces SEIR, PINN, CHP and RSV. The recommended title
spells out respiratory syncytial virus and comes to **189 of the permitted 200 characters**, so
it fits. For the abstract, defining the four on first use as now is common practice and low
risk — the alternative is naming the methods rather than abbreviating them.

`[VD-7]` The Author Summary is 152 words and suitably non-technical, but third person
throughout, and PLOS requires first person. The bracket gives a minimal conversion that changes
no number. **It also raises a discrepancy worth settling**: that paragraph says sixteen influenza
and RSV seasons, while the title, abstract and Results work from eighteen. Sixteen reconciles as
the six influenza seasons of the primary EpiEstim evaluation plus ten RSV; eighteen is eight plus
ten. Both are defensible, a referee will ask, and only you know which set the sentence meant.

### One abbreviation was fixed rather than recommended

"SI" was used four times and undefined at its first use, because that first use is in Results
and the definition sits in the Methods behind it. It is now spelled out there. Expanding an
abbreviation is not rephrasing, so it did not need to wait.

**Three brackets were closed on 5 November and are gone from the document.**

- `[TY-2]`, **the five-week source verification** — done. 2015-W21, 2015-W35, 2019-W44,
  2019-W52 and 2022-W18 were checked against the published CHP tables and **all five match
  exactly** on specimens tested, RSV detections and percentage positive. The Methods sentence no
  longer says "pending"; it cites `rsv_source_verification_2026-11-05.md`, which records the
  source page for each week. *The comparability assumption in the same paragraph is a different
  claim and still stands as a stated limitation.*
- `[TY-4]`, **the date range** — the Abstract now reads "seasons labelled 2014/15 to 2024/25,
  drawn from surveillance records spanning January 2014 to March 2026", which reconciles with the
  title's 2014–2026. VD's phrase "an analytical reconstruction" in the same sentence was not
  touched; it belongs to `[VD-5]`.
- `[TY-5]`, **the single-use abbreviations** — IQR, GP ILI, GPU and COVID NPIs are spelled out.

**Also fixed, and not a bracket**: the terms the review found used before definition. A short
preamble now opens the Results, defining onset for both estimators, lead time, the four-week
burn-in and what "multi-wave" means, because moving the Methods to the end left all four used
before they were explained.

**The submission copy cannot be uploaded while any bracket remains.** It holds four: VD-1, VD-2,
TY-1, TY-3. The four in Open queries are editorial questions and that whole block is absent from
the submission copy by construction.

Each bracket states the evidence inline, so neither of you has to come back to this sheet to act
on one. What follows is the longer version, plus the submission-system fields that never appear
in the manuscript at all.

---

## What you sent on 6 November, and what became of it

**The affiliation block is applied, and it fixed a real defect.** v10 carried HKU SPH and
HKU-Pasteur merged onto one numbered line with an ampersand. Your two strings separate them, so
the numbering is now **1 SPH, 2 HKU-Pasteur, 3 Columbia**, and the superscripts moved with it:
Thomas 1,3 and yours 1,2. The change is a tracked change in the editing copy with a comment on
it, so rejecting it restores v10's line exactly — the build asserts that, including the
superscripts. **Two parts of it are yours to settle.** You sent two affiliations and v10 carries
three, so Columbia is kept rather than dropped; say if it should go. And Thomas is not listed on
HKU-Pasteur, because whether he is affiliated there is not something a session can decide.

**The two availability headings are adopted; three clauses of the template are not.** The
structure you sent is now two sections, **Data availability** and **Code availability**, sitting
between Acknowledgments and References. What is not carried in, because it describes a different
paper:

| Clause in the template | Why it is not in this manuscript |
|---|---|
| consensus genome sequences deposited in GISAID (Supplementary Data) | this study generates and uses no sequence data at all |
| XML input files for BEAST analysis and the resulting log files | there is no BEAST analysis |
| custom R scripts for plotting and subsampling | the analysis is Python throughout, which the Methods already state |

The R point is the one worth a sentence, because an R file does exist. `epiestim_benchmark.R`
sits in the `HKU-influenza/scripts` working directory, outside the cited repository. It is not
load-bearing: the manuscript names no R anywhere and says "implemented in Python" and "Software:
Python 3"; the `epiestim_results.csv` it writes **exists nowhere under the connected folders**;
and the reported EpiEstim values come from the committed Python outputs. Surfaces searched were
the `pinn-early-warning` repository (no `.R` files, 39 Python files), `HKU-influenza/scripts`
(four `.R` files, two of them duplicate `(1)` copies) and every mount to four levels for
`epiestim_results.csv`. **Not searched**: the GitHub remotes or any other machine.

**One clause was dropped on a journal rule rather than a preference.** "Or from the corresponding
author upon reasonable request" is standard at other journals and is not acceptable at PLOS as a
default — see system field 7 below.

---

## Kimberly Edwards's second pass, 10 November — what in it is yours

She has now been through the whole paper. Across both rounds: **459 tracked revisions and
48 comments**, all in the editing copy under her own name, filterable in the Review pane.
Her second round is dated 10 November so the two passes are distinguishable on sight.

She worked from the submission copy both times, so **she has still not seen your comments**,
and everything she raises she raised independently.

### Five of her comments are your half of the writing

By the April 2026 division the Introduction and Discussion are yours, so these are carried
into the document and **not** pre-written:

- **An overarching conclusion.** "Don't end on limitations… Summarize contributions of this
  paper to existing body of knowledge and highlight knowledge gaps for further study."
  The paper currently ends on the limitations paragraph.
- **The practical implications.** "Is an earlier detection necessarily 'better' if it
  predicts epidemic onset >30 days in advance? How can these retrospective analyses & tools
  inform future public health preparedness?"
  **Your own comment of 19 August makes the same point**: "the practical utility of epidemic
  onset in HK or other regions is not quite clear, affecting impact of study." She raised it
  without having seen your comments, so it has now come from two readers.
- **The limitations structure.** They read as a numbered list by the fifth item; she
  suggests folding each into the subsection it belongs to. She also proposes **merging
  Results and Discussion**, which would change the PLOS section order, so that one is a
  question rather than a suggestion.
- **More references behind the general claims**, in the Introduction and Discussion.
- **The adolescent-amplifier reading** could be "further elucidated in the discussion —
  including alternative interpretations with additional references".

These are the strongest comments in her second pass, and all five land in your half.

### Two of her edits would have changed your words, and were not applied

- **The ethics sentence.** She rewrote "As all data are publicly available in aggregate form
  from CHP, with no individual-level information" to "As all data are de-identified and
  publicly available in aggregate". The phrase she deletes is yours, and the determination is
  `[VD-1]`, which is yours to make. Her own comment on that bracket reads simply **"update"**.
  Worth knowing before you settle it: *de-identified* would be a drift rather than a tidy,
  because aggregate surveillance counts were never identified, and the word implies individual
  records existed and were stripped.
- **The Abstract's remaining numerals.** Her convention is to spell out numbers under ten.
  Round one applied it wherever the words were Thomas's, which is why the sentence now reads
  "five of six seasons" in its first half and "5 of 6 seasons" and "all 6 seasons" in its
  second. The second half is yours. One word from you runs her convention through the whole
  sentence or takes it out of the first half.

### Three decisions that are not edits

- **Supporting figure numbering.** She has asked twice for `S5 Fig` to become `S1 Fig`, and
  her second pass made the renumbering consistent where the first left one figure cited under
  two names, so it is now adoptable. Two things to weigh: it renames `S5_Fig.tif`, which sits
  with the deferred figure work; and it is a preference rather than a rule — the PLOS
  Computational Biology guidelines, read at source on 10 November, ask only that a supporting
  item's name "contains an 'S' and number" and set no separate sequence for figures and tables.
- **Equations.** She quotes the PLOS guidance that MathType is recommended for display and
  inline equations, and the quotation is verbatim correct. The same page also says to **avoid**
  MathType for single variables, and almost all of this manuscript's mathematics is single
  variables plus one short inline relation. A production decision at upload, not a text edit.
- **Three relocations.** Post-hoc season classifications to the Discussion, the Hu et al.
  comparison to the Discussion, and the multi-restart sentence from Methods to Results. All
  three move material between your half and Thomas's, so they belong in one decision rather
  than three.

### What was applied, and what was held

Fourteen of her 10 November changes are in, as tracked changes authored **"Thomas Yuan —
answers KME round 2"**, so they filter separately from everything else. Under the same author,
fourteen further counts in my own prose now follow her number convention (11 November), so the
text no longer mixes "four of six" with "5 of 6"; the Abstract keeps its numerals because they
are your words. Nineteen are held,
each with its reason stated in the Open queries block of the editing copy.

Five of the held ones are worth knowing about because they would have cost the paper
something: detection in all ten RSV seasons; "onset dates shifted by 0–7 days" becoming
"7 days", which repeats an edit of hers already repaired on 6 November; the five manually
validated CHP weeks that are the only evidence the RSV scraper is right; `scipy.signal.find_peaks`
replaced by a description of the smoothing, which leaves the prominence and distance settings
attached to nothing; and "and is not modelling-free", which is the point of the sentence it ends.

### Her role, against the journal's own criteria

Across two rounds this is 459 edits and 48 comments, including the Methods and Discussion.
**The call is yours**, and nothing has been said to her. What follows is the criterion rather
than an opinion.

PLOS Computational Biology's authorship page, read at source on 10 November, sets three
requirements, all of which must be met. The first is "substantial contributions to one or
more of" a list that includes **"drafting or substantially revising the article"**. Note the
*one or more*: this is not the four-part ICMJE formulation, and revision alone can satisfy
the first criterion. On the record in the file she meets it.

The second and third are that the author "approved the submitted version" and agrees to "be
personally accountable for the author's own contributions". **Neither can be settled without
asking her.** So the honest position is not "acknowledge her" and not "add her" — it is that
she meets the first criterion and the remaining two are a question to put to her.

One consequence either way: if the decision is acknowledgment, the same page requires that
"those being acknowledged have given their permission to be named", so she has to be asked
in that case too. `[VD-2]` is where the name would go.

---

## In the manuscript — search for `[VD-` or `[TY-`

### `[VD-1]` Ethics statement — Materials and Methods, last subsection
PLOS requires this **in the Methods**, not in the submission system. Draft, ready to accept:

> This study analysed only aggregate, publicly available surveillance statistics published by
> the Centre for Health Protection of the Government of the Hong Kong Special Administrative
> Region. No individual-level or identifiable patient data were accessed and no human
> participants were recruited, so the study did not require review by an institutional review
> board.

**Only he can confirm** whether a formal exemption determination is nonetheless needed, and
supply its reference number if one was obtained. This is the same outstanding item as in v10.

### `[VD-2]` Acknowledgments
For people who contributed but do not meet authorship criteria, each with their contribution.
**PLOS forbids funding sources here** — those go in the system field below. If there is nobody
to thank, the section is deleted rather than left empty.

### `[TY-1]` Code archive DOI — Code availability
PLOS requires author-generated code in a repository that **issues DOIs**; a GitHub URL alone
does not satisfy the policy. The sentence is already written around the gap: tag the release at
`github.com/thomasshuaiyuan/pinn-early-warning`, push it to Zenodo, paste the DOI. Open decision
D18. **Also still owed in the repository**: `snr_within_pathogen_stats.csv` sits untracked in the
working tree, so the manuscript's claim that every reported value reproduces from the repository
does not yet hold for Fig 3's two rank-test rows.

### `[TY-2]` The source verification the Methods called pending — **discharged 5 November**
Methods named five randomly selected RSV weeks for manual validation — 2015-W21, 2015-W35,
2019-W44, 2019-W52, 2022-W18 — and stated that verification against the CHP website was
pending. **All five were checked against the published CHP tables and all five matched exactly**
on specimens tested, respiratory syncytial virus detections and percentage positive. The record,
with the source page for each week, is `rsv_source_verification_2026-11-05.md` in the folder and
in the repository, and the Methods sentence has been rewritten to state the completed check
rather than a pending one. The build asserts that no "is pending" string survives.
**This section previously called it the one real reason not to submit; that is no longer true.**
The wider sentence in the same paragraph, that cross-pathogen comparability "requires further
evidence rather than assertion", remains an author-level scientific decision and is untouched.

### `[TY-3]` A provenance date that cannot be right
Methods states the CHP site was accessed on 15 March 2026. The last row of `flux_data.csv` is
the week running 15 to 21 March 2026. A week cannot have been downloaded before it ended.

### `[TY-4]` The date range
The title says 2014–2026, the Abstract says seasons between 2014 and 2025. Both are defensible —
the record runs to 21 March 2026 and the eighteen seasons are labelled to 2024/25 — but one
wording should be chosen. The bracket carries a suggested form. Note that the same Abstract
sentence contains VD's phrase "an analytical reconstruction", which `[VD-5]` would change, so
settle them together.

---

## In the submission system only

### 1. Financial disclosure
Entered **only** in the system; PLOS states it must not appear in the manuscript. Needs the
grant number, author initials, sponsor URL, and whether the sponsor had any role. If none:

> The funders had no role in study design, data collection and analysis.

**Two cautions.** The **RGC grant reference is still outstanding** — it has been on the list
since the v8 round. And **NIH/NIAID contract 75N93021C00016 should not be entered on the
strength of the acknowledgement record alone**: it is his contract, acknowledged on other
papers, and whether it supported *this* work is his call.

### 2. Competing interests
The corresponding author declares on behalf of all authors. The standard wording is:

> The authors have declared that no competing interests exist.

**This one needs a decision rather than a default**, and there is one potential disclosure to
weigh that is personal to Thomas rather than scientific. It has no connection to this
manuscript, but PLOS asks for anything that *could be seen* as influencing the work, and a
disclosure costs nothing while an omission that surfaces later costs a correction. **Raised with
VD directly rather than written out here**, since this sheet now sits in a folder shared beyond
the two authors.

### 3. Author contributions — CRediT
At least one role per author, published with the article. Proposed split, to amend:

- **Thomas Yuan** — Data curation, Formal analysis, Investigation, Methodology, Software,
  Validation, Visualization, Writing – original draft
- **Vijaykrishna Dhanasekaran** — Conceptualization, Funding acquisition, Project
  administration, Resources, Supervision, Writing – review and editing

### 4. ORCID
The **corresponding author must supply an ORCID iD at submission**, in the user profile. The
corresponding author on this manuscript is VD.

### 5. Four suggested reviewers
PLOS asks for **at least four**. Candidates below are drawn from the methods literature the
paper engages with and are chosen to avoid conflicts. **Affiliations to confirm on the form; no
contact details are asserted here.**

| Candidate | Why they fit |
|---|---|
| Anne Cori | author of the renewal-equation framework the paper evaluates |
| Robin N. Thompson | reproduction-number estimation from temporally aggregated data |
| Kris V. Parag | R(t) estimation under surveillance noise and reporting artefacts |
| Sebastian Funk | real-time estimation and surveillance evaluation |
| Jacco Wallinga | R(t) methodology and its use in public-health decisions |
| Cécile Viboud | influenza and RSV surveillance epidemiology |

**Must be excluded as conflicted**, being co-authors or inside the group: Benjamin Cowling,
Tim Tsang, Olivier Gascuel, Anna Zhukova, Ruopeng Xie, Oliver Pybus, Moritz Kraemer,
Dillon Adam, Sheik Taslim Ali, Nancy Leung, Tommy Lam.

### 6. Section, related manuscripts, cover letter
One section must be chosen on the form. The submission must confirm that no related or
duplicate manuscript is under consideration elsewhere — true; nothing is submitted anywhere.
A cover letter uploads as a separate file; a full draft is in `COVER_LETTER_DRAFT.md`, built
into `COVER_LETTER.docx` by `make_cover_letter.sh`, needing only his sign-off and the date.

### 7. Data Availability Statement — a form field as well as a manuscript section
PLOS asks for this **when the manuscript is submitted**, as its own field, and it is the field
the journal publishes. The manuscript now carries the same text under **Data availability** so
that a reader of the .docx sees it, but the form field is what counts and it has to be pasted
in. Two things about the policy, read at source on 6 November. The statement **must name the
repository and give the DOI, accession or other persistent identifier**, with placeholder
wording allowed at submission and the identifier requested before publication — which is what
`[TY-1]` is. And **"available from the corresponding author upon reasonable request" is not
acceptable here**: PLOS allows request-based access only for sensitive human data, and states
that it is not acceptable for an author to be the sole named individual responsible for access.
Nothing in this study is sensitive, so the statement points at the public sources and the
archive instead.

---

## The three content questions — now `[VD-3]`, `[VD-4]` and `[VD-5]` in the document

These are not submission fields. They sit in an **Open queries** block at the end of the editing
copy, each with its evidence attached, and that whole block is absent from the submission copy.
They are the reason the meeting matters more than the formatting.

1. **The Highlights sentence** *"Low-amplitude laboratory signals degraded both estimators in
   the same direction."* His inserted prose. The real-data signal-to-noise result does not
   carry it: pooled median SNR 16.7 against 10.2 at one-sided p = 0.166, within influenza
   −0.06 (exact p = 0.89), within RSV +0.23 (exact p = 0.52), and that figure's own title says
   so — it is Fig 3 after the 5 November renumbering, and was Fig 2 before it.
   What is solid is the between-pathogen contrast, 5 of 6 seasons at +35 days against 4 of 10
   at −18. PLOS has no Highlights section, so this does not block submission — but the same
   claim appears in the Discussion.
2. **The second Highlights line** *"Age-stratified admissions led positivity exactly on the
   hardest, low-amplitude seasons."* The committed differences are +21, 0, +42, 0, +21, 0, 0,
   +63 — four leads, four ties, none later — and the leads include the second- and
   third-highest-amplitude seasons. The Abstract already states the weaker, correct version.
3. **The threshold consistency question** from the note of 30 October, still unanswered:
   4.94% as CHP's published operational baseline throughout, 6.47% and 5.70% as data-derived
   sensitivity analyses, 1.87% always flagged as data-derived. It needs his word because it
   changes "an analytical reconstruction" in the Abstract, which is his wording.

---

## Small fixes that are Thomas's, listed so they are not forgotten

- **The reference author lists are done — all eight, verified.** Resolved against Crossref
  metadata records on 5 November, with journal, volume, issue, pages and year checked against
  what the manuscript states in each case. Refs 5, 8 and 18 truncated to the first six authors;
  ref 13 Xie expanded from this project's own verified record; refs 1, 7, 10 and 15 expanded
  from Crossref. **Ref 10 Kharazmi turned out to have exactly six authors**, so it now lists all
  six with no "et al." at all. One candidate that a loose query returned for ref 1 was a
  *different paper* — Waris and White, Clin Infect Dis 2006 — and was discarded on the field
  check rather than used.
- **The repository has no licence file**, and PLOS's materials, software and code policy asks
  authors to license their code under an open-source licence, and requires it of anything
  presented as software. Adding a `LICENSE` (MIT is the usual choice for analysis code) costs
  one commit and should happen **before** the Zenodo release is tagged, because the archive
  snapshots whatever is in the tree. The availability statement deliberately claims no licence
  until one exists.
- **Five abbreviations are used once each** — GP, GPU, IQR, NPI, SAR — now `[TY-5]`.
- **The date range**, now `[TY-4]` in the Abstract.
- **The figure files**, now `[TY-6]`: PLOS states a figure file must not contain the figure title
  or caption, and Fig 2 to Fig 4 embed titles that duplicate caption material, while Fig 1 and
  Fig 3 have unlabelled panels. Fixing it means rerunning the figure scripts, so it was not done
  unasked. Figure formatting is waived until a provisional editorial accept decision.
