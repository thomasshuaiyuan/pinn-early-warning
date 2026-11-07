# What VD needs to supply — PLOS Computational Biology submission

**Five of the recommendations are now one-click.** They are tracked changes in the editing copy,
authored **"Thomas Yuan — recommendation"**, each with a Word comment anchored to it carrying the
reasoning. In the Review pane he clicks **Accept** to apply or **Reject** to discard, and because
the author label is distinct he can filter the pane to see only recommendations, separately from
the Methods relocation. Rejecting any of them restores the current text exactly — verified in the
build, not assumed.

| Tracked change | What it proposes |
|---|---|
| **R1** | the title with respiratory syncytial virus spelled out, 189 of 200 characters |
| **R2a–c** | three edits converting the Author Summary to first person, touching no number |
| **R3** | the Abstract's "an analytical reconstruction" becomes "the published operational influenza threshold", which is the 30 October question |
| **Q1** | a comment with no edit: sixteen seasons here against eighteen elsewhere, because there is no single replacement to accept |

**Everything that cannot be one-click is still bracketed**, because it is a blank to fill or a
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
Summary are not mine to rephrase. Each bracket carries the proposed wording in full so it can be
accepted or rejected in place.

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
