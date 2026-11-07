# Affiliations and the availability statements — decisions, 6 November 2026

Thomas supplied, in chat, Vijay's affiliation block and a Data/Code availability template.
Both were applied to the PLOS Computational Biology package; this records what was applied,
what was not, and why, because the second half is the part a later session would otherwise
re-litigate or silently undo.

**Filed here rather than in the project store**, because the store refused the write: it is at
its maximum size. Part II of the project instructions already names deduplicating the store as
a prerequisite for filing rather than housekeeping, and this is the second record now sitting
in a working tree for that reason.

## The affiliation block — applied, and it fixed a defect

Supplied verbatim:

> 1 School of Public Health, LKS Faculty of Medicine, The University of Hong Kong, Hong Kong SAR, China.
> 2 HKU-Pasteur Research Pole, School of Public Health, LKS Faculty of Medicine, The University of Hong Kong, Hong Kong SAR, China.

v10 (`5d56c38565a55fdeb8ddef8f71a7cf78`, verified by hash) carried these **merged onto one
numbered line with an ampersand**: *"1 School of Public Health, LKS Faculty of Medicine, The
University of Hong Kong & HKU-Pasteur Research Pole, Hong Kong SAR, China"*. Part I of the
project instructions forbids flattening the two, so his block is a correction, not a
preference. Numbering is now **1 SPH, 2 HKU-Pasteur, 3 Columbia**; superscripts **Thomas 1,3
and VD 1,2**.

Applied in both copies; tracked in the editing copy authored "Thomas Yuan" with an anchored
comment, so Reject restores v10 exactly. The build asserts both the forward state and the
reject round-trip, including the superscripts.

**Two parts left to him, deliberately.** He sent two affiliations and v10 carries three, so
**Columbia is kept rather than dropped** — the non-destructive choice, flagged in the comment
and in `VD_INPUT_SHEET.md`. And **Thomas is not listed on HKU-Pasteur**, because nothing
establishes that he is affiliated there.

**One claim that was checked and does not hold.** The author block carries **no tracked
revision by VD in v10** — checked for `ins`, `del`, `moveTo`, `moveFrom` and
`commentRangeStart` on paragraphs 1 to 4, all absent. So Columbia being in v10 is *untouched*,
not *endorsed*. Do not cite v10 as his approval of it.

## The availability template — structure applied, three clauses not

Supplied: a two-heading structure (`Data availability`, `Code Availability`) whose body
described consensus genome sequences deposited in GISAID, BEAST XML and log files in a
Zenodo/Dryad repository, and custom R scripts for plotting and subsampling available "or from
the corresponding author upon reasonable request".

The **structure is adopted**: two headed sections between Acknowledgments and References,
replacing the single "Data Availability Statement". The **body is rewritten**, because three
clauses describe a different paper. Carrying them verbatim would have put three false claims
into a submitted manuscript, which is the failure mode Part I's hardest rule exists for.

| Clause | Why not |
|---|---|
| consensus genomes deposited in GISAID (Supplementary Data) | no sequence data is generated or used |
| BEAST XML input and log files | there is no BEAST analysis |
| custom R scripts for plotting and subsampling | the analysis is Python throughout |

**The R clause, with its surfaces named, because an R file does exist.**
`epiestim_benchmark.R` is in `HKU-influenza/scripts`, outside the cited repository. It is not
load-bearing: the manuscript contains no "R package", no "R version" and no "epiestim_results",
and states "implemented in Python" and "Software: Python 3"; the `epiestim_results.csv` that
script writes is **absent from every mount searched to four levels**; the reported values come
from the committed Python outputs. Surfaces searched: `pinn-early-warning` (0 `.R` files, 39
`.py` at depth ≤ 2), `HKU-influenza/scripts` (4 `.R` files, two of them duplicate `(1)`
copies), and all mounts for the output filename. **Not searched: the GitHub remotes, any other
machine.**

**The fourth clause was dropped on a journal rule, not a preference.** PLOS's data-availability
and materials/software/code-sharing policies, read at source 6 November: the statement **must
name the repository and give a DOI, accession or other persistent identifier**, with
placeholder wording allowed at submission; **"upon reasonable request" is reserved for
sensitive human data**, and "it is not acceptable for an author to be the sole named individual
responsible for ensuring data access"; for code, request-only access applies only where there
is a legal or ethical restriction. Neither applies here. The statement therefore names the
public CHP sources and the archive, and keeps one `[TY-1]` slot for the DOI.

**New item found while doing this.** The repository has **no licence file**. PLOS asks authors
to license code under an open-source licence and requires it of anything presented as software.
A `LICENSE` must land **before** the Zenodo release is tagged, because the archive snapshots
the tree. The availability text deliberately claims no licence until one exists.

## Collateral changes

- The cover-letter signature now names HKU-Pasteur as well as SPH, and
  **`make_cover_letter.sh`** was written so the letter is a build output rather than a
  hand-edit: it extracts the body between the two horizontal rules of `COVER_LETTER_DRAFT.md`
  and asserts that neither the instructions above nor the notes below leak into the `.docx`.
- **`make_preview.py`** now generates `PREVIEW_submission_readable.md` from the
  submission-ready `.docx`, which was previously made by hand.
- `VD_INPUT_SHEET.md` gained a section on what became of his two blocks, a seventh
  submission-system field for the Data Availability Statement, and the licence item.
  **Its `[TY-2]` section was stale** — four days after the five RSV weeks were verified 5 of 5
  it still called the verification pending and "the one real reason not to submit yet".
  Corrected in place, with the sentence that corrects it.
- `PLOSCB_submission_checklist.md` gained an Affiliations row, a corrected Data availability
  row (it cited the wrong slot, `[VD-3]` instead of `[TY-1]`) and a dated update to the item
  that argued availability text does not belong in the manuscript at all.
- Build state: all checks pass in both modes, **34 comments** (VD's 26 plus 8), editing copy
  `64,215` bytes, submission copy `43,588`. All seven installed files verified byte-identical
  to `v10_build/_stage_plos`, and the three `.docx` opened and checked.

## Two operational hazards worth carrying forward

1. **Writing over a file inside the OneDrive folder fails with "Resource deadlock avoided"**
   once the sync client has made it a Files-On-Demand placeholder, and reading one fails the
   same way. `build_plos3.py` now honours `PLOS_DEST`: build to `v10_build/_stage_plos`, then
   move the old file aside and copy the new one in.
2. **The OneDrive folder is not a backup.** Seven files moved into
   `_superseded/2026-11-06_pre-affiliations/` were removed by the sync client within minutes.
   A `README.txt` in that folder records it. The durable copy is `_stage_plos`, in this
   working tree.

## Still open on this package

`[TY-1]` the Zenodo DOI; `[TY-3]` the CHP access date; `[VD-1]` ethics; `[VD-2]`
acknowledgments; `[VD-3]` to `[VD-5]` the three content questions; `[TY-6]` the figure files.
Unchanged by today's work, plus the licence file and the two affiliation questions above.
**Nothing has been sent to Vijay, and no session sends mail on his behalf.**
