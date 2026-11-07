# v10_build — the PLOS Computational Biology build

One command, from anywhere the repository is checked out:

    sh build.sh

That produces, in `_stage_plos/`:

| File | What it is |
|---|---|
| `..._PLOSCB_FOR-EDITING.docx` | the copy Vijay works in: his comments, Kimberly's tracked edits under her own name, the Methods relocation as a change he can reject in one click, every slot he must fill marked `[VD-n]` |
| `..._PLOSCB_SUBMISSION-READY.docx` | the same text, upload-shaped: no revisions, no comments, no Highlights block |
| `PREVIEW_submission_readable.md` | the submission copy as plain Markdown, for reading without Word |
| `COVER_LETTER.docx` | built from `COVER_LETTER_DRAFT.md` if one is in the staging directory and pandoc is installed |

"Submission-ready" in the file name means upload-shaped, not finished.

## Where it reads and writes

Every path is derived from this directory, so the build runs the same on the Mac, in
the Linux VM that mounts the repository under `~/mnt`, and in a cloud container that
has neither.

    inputs   ./2026-11-05_early-warning_v11.docx
             ../Claude outputs/2026-10-15_early-warning_v10_figures.docx
    output   ./_stage_plos            (override with PLOS_DEST)
    scratch  ./_plos2_edit, ./_plos2_submit

**The build never writes into OneDrive.** Delivery into the synced folder is a
separate copy step, done on purpose. Writing over a Files-On-Demand placeholder fails
with `Resource deadlock avoided`, and a build that half-wrote a `.docx` into the folder
a co-author is reading is worse than one that refused to start.

To deliver, after a clean build:

    D="$HOME/Library/CloudStorage/OneDrive-TheUniversityofHongKong-Connect/Thomas early-warning/6_plos_submission"
    cp _stage_plos/*.docx _stage_plos/PREVIEW_submission_readable.md "$D"/

## What a clean run looks like

139 checks, every one `PASS`, exit 0. **A nonzero exit means do not deliver what is in
the staging directory.** The checks are not a formality: they are what caught Kimberly's
table-header edits landing in the Abstract, the move revisions leaking into the
submission copy, and the same supporting figure being cited under two names.

The last check is the one worth knowing about:

> the editing copy, with the recommendations rejected, reproduces the submission copy

Accept every revision in the editing copy except those authored
`Thomas Yuan — recommendation`, and you get the submission copy exactly. That is the
invariant that stops the two files drifting apart, and it is why recommendations are a
separate author rather than ordinary tracked changes.

## Dependencies

`lxml` and `python-docx`; `pandoc` only for the cover letter. `build.sh` checks all
three up front and tells you the pip line if either Python package is missing.

## The parts

| File | |
|---|---|
| `build_plos3.py` | the build and its 139 checks |
| `ooxml_track.py` | namespace helpers and tracked-change construction |
| `kme_edits.py` | Kimberly Edwards's 31 paragraph edits, 9 held paragraphs, 33 comments — generated from her returned file, not hand-written |
| `followup_edits.py` | the 23 follow-up edits, each carrying its id, source and evidence |
| `make_preview.py` | the submission copy rendered as Markdown |
| `make_cover_letter.sh` | the letter only, cut from the draft between its first two horizontal rules |
| `build.sh` | all of the above, in order, stopping on failure |
| `_superseded_paths/` | the pre-portability copies of the three scripts. Nothing reads them |

## Scratch directories

`_plos2_edit` and `_plos2_submit` are reused rather than timestamped. They used to
carry a timestamp, which left a pair behind on every run, and the shell that drives
this over a mounted folder cannot delete files. Reuse is safe: the output `.docx` is
written only from the source package's own member list, so a stale file in a scratch
directory can never reach it.
