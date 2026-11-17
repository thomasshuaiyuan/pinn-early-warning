# PLOS Computational Biology package — changelog

One or two lines per revision, what changed and why, newest first. Filenames carry the
date of the revision and its version, so a file named 5 November can never hold content
built on the 10th.

---

**v3.2 sent to Professor Dhanasekaran on 10 November 2026 (US Eastern).** Text of the email in `pinn-early-warning/Claude outputs/2026-11-10_email_to_vijay_SENT.md`. Open with him: threshold wording [VD-5], Highlights [VD-3]/[VD-4], and the items in `VD_INPUT_SHEET.md`.

## v3.2 — 11 November 2026

The five "Thomas Yuan — recommendation" tracked changes (R1 title, R2a–c Author Summary,
R3 Abstract) are withdrawn as edits, under Professor Dhanasekaran's note of 25 September
("ask before, not after"). The title and Author Summary are now comments [VD-6] and [VD-7]
carrying the proposed wording; R3 is asked in [VD-5]. The editing copy now contains no
tracked change to his words or framing. Submission copy text unchanged. 150 checks passing.

---

## v3.1 — 11 November 2026

Number convention made consistent: fourteen counts in Thomas's prose changed from numerals
to words to match the convention Kimberly Edwards applied at seven sites on 10 November.
The Abstract's numerals are Professor Dhanasekaran's words and are unchanged. No number
altered. Previous build in `_superseded/2026-11-11_pre-numeral-sweep/`. 150 checks passing.

---

## v3 — 10 November 2026

**Supersedes v2 of 7 November**, which is in `_superseded/2026-11-10_v2_stale-dated-filenames/`
(corrected 11 November; `_superseded/2026-11-10_pre-KME-round2/` holds only empty files).

Kimberly Edwards returned the second half of her review — the Discussion and Methods she
had not reached — as 192 further tracked revisions and 15 further comments. **Fourteen of
her changes applied, fifteen comments carried, nineteen held.** She worked in her own
6 November copy rather than this one, so her file also repeated the 321 revisions already
merged on a base predating the v2 follow-ups; only her 10 November work was considered, and
four new build checks now assert that no v2 edit was reverted and that Professor
Dhanasekaran's inserted text is untouched.

**One of her edits would have changed his wording and was not applied**: the ethics
sentence, which is also `[VD-1]` and his determination to make.

Also in v3: output filenames now carry the revision date and version; this changelog begins.

150 build checks, all passing.

---

## v2 — 7 November 2026

**Supersedes v1 of 6 November.** Twenty-three follow-up edits, each answering a named
comment and carrying its source and evidence in the document. Kimberly Edwards's first pass
merged: 233 edits applied, nine held because they would have deleted Professor
Dhanasekaran's words, 33 comments carried under her name.

Corrected from v1: her table-header edits had landed in the Abstract through a substring
match, and the supporting figure was briefly cited under two names. Both are now invariants
in the build.

---

## v1 — 6 November 2026

First PLOS Computational Biology package. Formatted to the journal's submission guidelines;
Materials and Methods relocated as a single tracked change that can be rejected in one
click; the affiliation block applied as supplied on 6 November; the data and code
availability template adapted, with three clauses belonging to a different paper removed
and named.

Split into two files from the start: **FOR-EDITING** carries every comment and tracked
change, **SUBMISSION-READY** is the same text upload-shaped, with no revisions, no comments
and no Highlights block. Accepting every revision in the editing copy except those authored
"Thomas Yuan — recommendation" reproduces the submission copy exactly, and the build asserts
it on every run.

---

## What each file in this folder is

| File | |
|---|---|
| `..._v3_FOR-EDITING.docx` | the copy to work in: all comments, all tracked changes, filterable by author in the Review pane |
| `..._v3_SUBMISSION-READY.docx` | the same text, upload-shaped. Cannot be uploaded while any `[VD-` or `[TY-` bracket remains |
| `PREVIEW_submission_readable.md` | the submission copy as plain text, for reading without Word |
| `VD_INPUT_SHEET.md` | the single list of what needs Professor Dhanasekaran |
| `VD_DISCUSSION_DRAFTS.md` | two Discussion paragraphs drafted to be cut, not in the manuscript |
| `KME_*` | the record of what was merged from Kimberly Edwards's two passes and what was held |
| `COVER_LETTER*`, `S1`–`S4_Table.docx`, `Fig1`–`4.tif`, `S5_Fig.tif` | the rest of the submission package |

"Submission-ready" in a filename means upload-shaped, not finished.
