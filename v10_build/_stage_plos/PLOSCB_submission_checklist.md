# PLOS Computational Biology — compliance state, and what remains

**Built 5 November 2026 from `2026-11-05_early-warning_v11.docx`.** Every requirement below was
read at source on 5 November from the journal's own submission-guidelines and figures pages.

## What is in this folder

| File | Use |
|---|---|
| **`..._PLOSCB_FOR-EDITING.docx`** | **the one to work in.** VD's 26 comments, the Methods relocation as a tracked change he can reject, the Highlights block retained, three `[VD-n]` slots |
| **`..._PLOSCB_SUBMISSION-READY.docx`** | upload-shaped: no comments, no tracked changes, no Highlights block. Regenerated from the editing file after his pass |
| `VD_INPUT_SHEET.md` | the nine things he supplies, six of them pre-drafted |
| `COVER_LETTER_DRAFT.md` | full draft, needs his sign-off and a date |
| `Fig1.tif` – `Fig4.tif`, `S5_Fig.tif` | figures to the journal's TIFF spec |
| `S1_Table.docx` – `S4_Table.docx` | the four supporting tables, one file each |
| `ADVERSARIAL_REVIEW_BRIEF.md` | the brief for an independent review pass |
| `REMEDIATION_RECORD.md` | **read this second.** What the independent pass found on 5 November, which findings reproduced, what was changed and what was deliberately left |
| this file | the checklist |

**Figures were renumbered on 5 November.** First citations ran Fig 1, Fig 4, Fig 2, Fig 3, which
PLOS does not permit, so old Fig 4 is now Fig 2, old Fig 2 is now Fig 3 and old Fig 3 is now
Fig 4, in the text, the captions and the TIFF filenames. Every caption was re-checked against
its figure afterwards. Any earlier note referring to figure numbers predates this.

**Work in the editing file, not the submission file.** The submission file is a derivative; any
edit made there is lost the next time it is regenerated.

---

## Requirements met

**Every open item is bracketed in the document.** Search for `[VD-` or `[TY-`: eleven hits in
the editing copy, six in the submission copy. The label names the owner, the bracket carries the
evidence inline, and the build counts them so none can be lost. **The submission copy cannot be
uploaded while any bracket remains.** Full register in `VD_INPUT_SHEET.md`.

| Requirement | Specified | State |
|---|---|---|
| Article type | research articles have **no length limit** | 7,690 words, nothing to trim |
| Full title | ≤ 200 characters | 163 |
| Short title | required on the title page, ≤ 70 characters | 55, newly written, change freely |
| Abstract | ≤ 300 words, no citations, no headings, also entered in a system field | 278, compliant |
| Author Summary | 150–200 words, first person, non-technical, after the abstract | 152, already existed |
| Section order | Title, authors, Abstract, Author Summary, Introduction, Results, Discussion, Materials and Methods, Acknowledgments, References, SI captions | matches |
| Ethics statement | **in Materials and Methods**, not the system | added as the last Methods subsection, slot `[VD-1]` |
| Funding | **must not appear in the manuscript**; system field only | the Funding section the first build added has been removed |
| Acknowledgments | contributors only, no funding sources | slot `[VD-2]`, with that constraint stated |
| Affiliations | each author's affiliations, numbered, superscripted on the author line | **two HKU affiliations as VD supplied them on 6 November**, 1 SPH and 2 HKU-Pasteur, which v10 had merged with an ampersand; Columbia renumbered to 3; Thomas 1,3 and VD 1,2 |
| Data availability | names the repository and gives a DOI, accession or other persistent identifier; request-only access is for sensitive data | **split into Data availability and Code availability** at VD's request, 6 November; the DOI slot is `[TY-1]`, and the same text must also go in the system field |
| Heading depth | ≤ 3 levels | 2 used |
| Spacing, numbering | double-spaced, single column, page and continuous line numbers | all set |
| Figure labels | "Fig 1", matching the file name | `Fig 1`–`Fig 4`, files `Fig1.tif`–`Fig4.tif` |
| Figure captions | in the text, read order, directly after the first citing paragraph, title ≤ 15 words, not inside the figure files | moved in from the separate figures document and placed after each first citation |
| Tables | directly after the paragraph where first cited, label and title above, legend below, not separate files | **Table 1 moved up** from the end of the Results to directly after its first citation; Table 2 was already correct |
| Supporting information | named with S and a number, captions at the end of the manuscript, files uploaded separately under 20 MB | renamed throughout from "Supplementary Table S1"; captions are the last section |
| References | Vancouver, numbered by first citation, square brackets, first six authors then et al. | compliant; **all eight non-conforming author lists corrected and verified** |
| Footnotes | none permitted | none present |
| Figures at initial submission | **may be embedded**; separate files required only at revision | TIFFs ready either way |

### The figure files

| File | Pixels | dpi | On the page | MB |
|---|---|---|---|---|
| File | Content | Pixels | dpi | On the page | MB |
|---|---|---|---|---|---|
| Fig1.tif | R(t) trajectories | 4171 × 1168 | 557 | 19.02 × 5.33 cm | 0.44 |
| Fig2.tif | admissions versus positivity onset | 2733 × 1468 | 365 | 19.02 × 10.22 cm | 0.39 |
| Fig3.tif | signal-to-noise against lead time | 4498 × 2243 | 600 | 19.04 × 9.50 cm | 0.87 |
| Fig4.tif | pre-onset amplification | 2488 × 1412 | 332 | 19.03 × 10.80 cm | 0.22 |
| S5_Fig.tif | 4496 × 1833 | 600 | 19.03 × 7.76 cm | 1.01 |

All five: TIFF, LZW, single layer, no alpha channel, RGB 8-bit, 300–600 dpi, inside the
19.05 × 22.23 cm page box, under 10 MB.

**Provenance, because stale copies exist on this machine.** Figure numbers below are the ones
after the 5 November renumbering. Fig 3 and S5 Fig were rasterised
from the **26 October** vector PDFs in `_figcheck_oct26/`, which carry the exact permutation
p-values (0.89 and 0.52) rather than the Monte Carlo ones. Fig 1, Fig 2 and Fig 4 came from the
images embedded in `2026-10-15_early-warning_v10_figures.docx`, byte-matched to the shipped
file. **The `fig*.pdf` and `fig*.png` in the repository root are from 23 August and are stale**;
`fig2_signal_amplitude` is the superseded v9 figure, correctly archived under
`4_arc/superseded_figures_v9/`. The v10 figure is `fig2_snr_within_pathogen`. Do not submit from
the repository root.

---

## The one decision recorded as a tracked change

PLOS puts Materials and Methods after the Discussion. In v10 it sits after the Introduction, and
that position is VD's own structural edit — his revisions carry 48 moveTo and 38 moveFrom marks,
and his format spec says Methods after the Introduction. In the editing file the relocation is
therefore a tracked insertion at the new position and a tracked deletion at the old, authored
"Thomas Yuan", so **rejecting it restores his order in one click**. It is the only tracked change
in that file. In the submission file it is already applied.

All 26 of his comments are carried across. Two of them, 142 and 703, had lost their anchor
because the text they sat on was later deleted; both were re-attached rather than left dangling.
That pair is his *"i.e. what does this drive?"* and the reply to it.

---

## What remains, none of it formatting

**1. Reference author lists — closed.** All eight corrected to PLOS's first-six-then-et-al rule
and verified against Crossref metadata records on 5 November, each with journal, volume, issue,
pages and year checked against what the manuscript states.

| Ref | Action | Verified against |
|---|---|---|
| 1 Obando-Pacheco | expanded to six, 18 authors in total | doi:10.1093/infdis/jiy056 |
| 5 Lison | truncated from seven to six | already in the manuscript |
| 7 Yang | expanded to six, 11 authors in total | doi:10.3201/eid1510.081040 |
| 8 Carrat | truncated from seven to six | already in the manuscript |
| 10 Kharazmi | **has exactly six authors**, so all six listed and the "et al." removed | doi:10.1038/s43588-021-00158-0 |
| 13 Xie | expanded to six | this project's own verified reference record |
| 15 Mossong | expanded to six, 14 authors in total | doi:10.1371/journal.pmed.0050074 |
| 18 Ogi-Gittins | truncated from eight to six | already in the manuscript |

Every replacement was made inside a single text run, so no reference formatting was flattened.
**One near miss worth recording.** A loose bibliographic query for ref 1 returned
*Seasonality of Respiratory Syncytial Virus Infection*, Waris and White, Clin Infect Dis
2006 — a real paper, wrong one. It was discarded because its journal, year, volume and pages
did not match what the manuscript states. A search result is not a verification until the
metadata record is compared field by field against what is written.

**2. The nine items VD supplies**, six of them pre-drafted. See `VD_INPUT_SHEET.md`.

**3. A DOI-issuing archive for the code.** Open decision D18, and a hard PLOS policy rather than
a preference.

**4. Five single-use abbreviations** — GP, GPU, IQR, NPI, SAR. PLOS allows non-standard
abbreviations only at three or more uses.

**5. The title says 2014–2026 and the Abstract says seasons "between 2014 and 2025".** Both are
defensible — the record runs to 21 March 2026, the 18 seasons are labelled to 2024/25 — but the
sentence sits beside VD's wording, so it is flagged rather than edited.

**6. The figures carry internal titles and unlabelled panels.** PLOS states a figure file must
not contain the figure title or caption; Fig 2 to Fig 4 embed titles that duplicate caption
material, Fig 1 has three unlabelled panels, Fig 3 has two, and S5's `a`/`b` panels are not
described in its caption. Fixing this means rerunning the figure scripts, so it was not done
unasked. **Figure formatting is waived until a provisional editorial accept decision**, so it
does not block an initial submission.

**7. `snr_within_pathogen_stats.csv` is not committed to the repository**, so the manuscript's
claim that every reported value reproduces from the repository does not hold for Figure 3's two
rank-test rows. The file exists in three places locally; it needs committing, not regenerating.

**8. A provenance inconsistency to reconcile.** Methods states the CHP site was accessed on
15 March 2026, and `flux_data.csv`'s last row is the week running 15–21 March 2026. A week
cannot have been downloaded before it ended. Only Thomas knows which date is right.

**9. The RSV source verification — closed 5 November.** The five weeks named in Methods were
checked against the published CHP tables and **all five match exactly** on specimens tested, RSV
detections and percentage positive. Record: `rsv_source_verification_2026-11-05.md`, which names
the source page for each week and also independently corroborates the scraper's URL mapping for
2015, 2019 and 2022. **The comparability assumption in the same paragraph is a different claim
and still stands as a stated limitation** — it was not touched and is not discharged by this.

**10. Closed on 5 November with it**: the single-use abbreviations, the Abstract date range, and
the terms the review found used before definition. A short preamble now opens the Results
defining onset for both estimators, lead time, the four-week burn-in and "multi-wave", which
moving the Methods to the end had left unexplained. **The abstract is now 289 words against the
300-word limit** — that margin is worth watching before anything else is added to it.

**6. Three content questions reformatting cannot settle**: the two Highlights lines whose
evidence is disputed, and the threshold consistency question from 30 October. All three are on
the meeting agenda and detailed in the input sheet.

---

## Checked against published practice, 5 November

Two recent PLOS Computational Biology research articles were read for structure rather than
science: *Generative diffusion models for spatiotemporal influenza forecasting*
(pcbi.1014846) and *Infectivity and fatality of influenza in pre- and post-COVID-19 pandemic
year* (pcbi.1013229). **Nothing structurally required is missing from this package.** Five
observations, in order of what they change.

1. **The supporting-information numbering question is settled, and our labelling is wrong.**
   Both papers bundle everything into one item — `S1 Appendix` and `S1 Text` — with internal
   parts cited as "Fig A in S1 Text". Each starts its own type's sequence at 1, matching the
   journal's own examples. **So the single supporting figure should be `S1 Fig`, not `S5 Fig`**,
   beside `S1 Table` through `S4 Table`. Mechanical to change: the caption, the two in-text
   citations and the file name. **Not applied**, because it renames a deliverable on a reading of
   an instruction the journal does not state outright.
2. **Data Availability does not belong in the manuscript.** In both papers PLOS prints Data
   Availability, Funding and Competing interests in the front matter, generated from the
   submission-system fields, not as author-written sections. Funding is already out of our
   manuscript; the availability text is still in it, which is **redundant rather than
   non-compliant** — but the DOI must go in the system field regardless of what the manuscript
   says. **Updated 6 November**: VD asked for the text in the manuscript under two headings,
   Data availability and Code availability, so it stays and is now split that way. That does not
   change the conclusion of this item, which is about which copy the journal publishes. Two
   points from the policy pages read that day: the statement must name the repository and give a
   persistent identifier, with placeholder wording allowed at submission; and "available from
   the corresponding author upon reasonable request" is **not** an acceptable default here,
   being reserved for sensitive human data, with the further rule that an author may not be the
   sole named individual responsible for access.
3. **First person in the Author Summary is the norm**, which supports `[VD-7]`. One paper is
   "We propose, We show" throughout; the other is mostly third person with a single "we find",
   so a mixed voice does get published.
4. **Published Author Summaries run shorter than the stated minimum** — about 130 and 125 words
   against the guideline's 150–200. Our 152 is comfortable, and the band is evidently loose.
5. **Abbreviations in titles do get published** — one of the two has "COVID-19" in its title.
   That weakens the title half of `[VD-6]`: spelling out RSV is tidier, not required.

Also noted, neither requiring action: panel labels appear as both bold lowercase "a." and capital
"(A)", so either convention satisfies `[TY-6]`; section numbering is optional, one paper numbers
and the other does not; and the published running order places Supporting information before
Acknowledgments and References, which is PLOS typesetting rather than the submission order our
file follows.

## On a third-party guide, checked and not acted on

A commercial pre-submission service publishes a "PLOS Computational Biology submission guide"
(manusights.com), updated October 2026, which states its requirements were checked against PLOS
sources in **August 2026**. It was read on 5 November and **nothing in it changes this package.**

It is weaker than the primary pages on every point that matters here: it gives **no abstract word
limit, no Author Summary length, no section order, and no figure specifications at all** — four
things this package is built to, from the journal's own submission-guidelines and figures pages.
Where it does state something, it agrees with those pages: no general length limit for research
articles, a 200-character title cap, initial submission permitted as a single PDF with figures
embedded, a required Data Availability Statement, code available without restriction, and a cover
letter uploaded separately. Its inline citations are sparse and it lists PLOS pages only in a
general source list.

**Treated as evidence, not as a requirement.** A secondary summary of a journal's rules carries
the same burden as any other claim, and a date-stamped check against sources in August is older
than the pages read directly on 5 November. Requirements in this checklist come from the
journal's own pages and nowhere else.

## Two process facts worth knowing

**Figure formatting is waived until a provisional editorial accept decision**, and an initial
submission may be a single PDF with figures embedded. So the TIFFs do not gate anything now —
they are the revision-stage requirement, done early.

**Research articles at this journal carry no word, figure or supporting-information limit.** The
roughly 2,000-word trim that was on the list for a different venue is not needed here.
