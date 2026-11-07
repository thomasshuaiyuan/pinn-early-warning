# The PLOS build made portable — 7 November 2026

The build ran only in one place. `build_plos3.py`, `make_preview.py` and
`make_cover_letter.sh` each hardcoded `$HOME/mnt/pinn-early-warning/...`, which is how
the Linux VM sees the repository and is not a path that exists on the Mac. Five lines
across three files. The default output directory was the synced OneDrive folder, which
is the other half of the same problem.

## What changed

**Paths are derived from the script's own location.** `BUILD` is
`os.path.dirname(os.path.abspath(__file__))`, `REPO` is its parent, and the two inputs
hang off those. `make_cover_letter.sh` does the same with
`HERE=$(cd "$(dirname "$0")" && pwd)`. Nothing reads `$HOME` any more.

**The default destination is `_stage_plos` beside the script, not OneDrive.** This is
the substantive change and not only a portability fix. Writing over a Files-On-Demand
placeholder fails with `Resource deadlock avoided`, and a build that half-wrote a
`.docx` into the folder a co-author is reading is worse than one that refused to start.
Delivery is now a deliberate `cp`, not a side effect of building. `PLOS_DEST` still
overrides.

**A preflight.** Missing input, or an unwritable destination, now gives a named path and
exit 2 instead of a traceback from inside the build. `make_preview.py` and
`make_cover_letter.sh` do the same, and `make_cover_letter.sh` checks for pandoc before
assuming it.

**The scratch directories are reused rather than timestamped.** `_plos2_{mode}_{epoch}`
left a pair behind on every run, and the shell that drives this over a mounted folder
cannot delete files, so they accumulated. Reuse is safe because the output zip is
written only from `order`, the source package's own member list, so a stale file in a
scratch directory cannot reach the `.docx`. The two modes keep separate directories
because the cross-copy check reads both at the end.

**`build.sh` and `README.md`.** One command runs the three steps in order and stops on
failure, after checking `lxml`, `python-docx` and pandoc up front and printing the pip
line if a Python package is missing.

## How it was checked

Four runs, every one 139 checks, 0 failures, exit 0:

| Where | Why it is a test |
|---|---|
| Cloud container, `/home/claude/portable/` | No `~/mnt` exists at all, so a surviving hardcoded path fails loudly |
| A relocated copy under a directory name containing a space | Location independence, and quoting |
| The real repository tree, through the VM mount | The path resolved as `/sessions/rcw-…/mnt/pinn-early-warning/v10_build`, which is a third spelling of the same folder |
| The real tree again, via `sh build.sh` | The one command, including the cover letter |

The two `.docx` packages built in the container and in the relocated copy were compared
member by member: **same member list, no member differing.** Only the zip entry
timestamps differ, which is expected. Two consecutive runs in the same directory are
byte-identical.

Failure paths exercised deliberately: no inputs present (exit 2, both missing paths
named), `PLOS_DEST` honoured, `make_preview.py` with nothing built (exit 2),
`make_cover_letter.sh` with no draft (exit 2).

## The limit, stated rather than left implicit

**This was not run in macOS's own shell.** `device_bash` runs in a Linux VM that mounts
the folder; it is the same file tree but a different interpreter and a different `PATH`.
So what is proven is that the scripts no longer depend on any particular location, and
that they run under two different Pythons (3.10.12 and 3.13.17). What is not proven is
that `python3` on the Mac's `PATH` has `lxml` and `python-docx`, or that pandoc is
installed there. That is exactly what `build.sh`'s dependency block checks and reports
before touching anything, so the failure is one legible line rather than a traceback.

One command on the Mac settles it:

    cd ~/pinn-early-warning/v10_build && sh build.sh

## What was kept

`_superseded_paths/` holds the pre-portability copy of each of the three scripts with a
README saying why. `build_plos3.py` is tracked in git so its old version is in the
history too; the other two were untracked, which is the reason for the folder.
`_plos2_*` scratch directories from the timestamped era were moved to
`_to_delete/plos2_scratch_20261107/` rather than deleted, because this shell cannot
delete inside a mounted folder.

## What did not change

No manuscript content. The source `.docx`, `kme_edits.py`, `followup_edits.py` and
`ooxml_track.py` are untouched, and the output packages are content-identical to the
ones already in OneDrive. This was a change to where the build reads and writes, not to
what it produces.
