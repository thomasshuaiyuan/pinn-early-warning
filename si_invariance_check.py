#!/usr/bin/env python3
"""si_invariance_check.py -- does the estimated onset depend on the assumed serial interval?

Written 26 October 2026, following the weekly-discretisation measurement of 15 October
(manuscript/2026-10-15_meeting_brief_discretisation.md). The question had been drafted
for VD as a judgement call. It is not one: it is answerable from two CSVs that were
already tracked at commit 98f32ca, and this script is that answer.

WHY, recorded before the counts, because the prediction came first.

    Weekly aggregation discretises the serial-interval distribution onto bins whose
    first edge is 3.5 days. At the influenza mean of 3.0 days the renormalised kernel
    carries 0.9985 of its mass at a one-week lag, so EpiEstim's R(t) is close to a
    windowed week-on-week ratio of incidence, and R(t) = 1 is reached where incidence
    stops rising -- a condition that does not contain the serial interval. RSV's mean
    of 7.5 days straddles that first edge, so its kernel stays genuinely spread
    (first weight 0.800) and the crossing does depend on the kernel's shape.

    Prediction, stated here before the grids were tabulated: the influenza onset is
    invariant across its SI grid; the RSV onset is not.

    NOTE on status: the week-on-week reasoning above is an argument from the renewal
    equation under a near-degenerate kernel. It has NOT been derived on paper in this
    project. The counts below are the measurement; the mechanism is the explanation
    offered for them.

INPUTS, both tracked at 98f32ca
    epiestim_si_sensitivity_flu.csv   6 seasons x 5 SI means (2.0-4.0 d) x 4 windows
    rsv_si_sensitivity.csv            3 seasons x 5 SI means (5.0-10.0 d) x 4 windows

The two grids are NOT matched: the ranges differ, and the RSV range crosses the first
bin edge while the influenza range does not. That asymmetry is the subject, not a
defect of the comparison, but it means this is not a controlled contrast and must not
be reported as one.

OUTPUT   si_invariance_check.txt beside this script, plus stdout.
EXIT     0 if the influenza grid is invariant and the RSV grid is not; 1 otherwise,
         because either outcome changing is a finding that must not pass silently.
"""

import collections
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

GRIDS = [
    ("influenza", "epiestim_si_sensitivity_flu.csv", "onset_date"),
    ("RSV", "rsv_si_sensitivity.csv", "onset"),
]


def cells(path, onset_col):
    """Group onset dates by (season, window), keyed within a cell by SI mean."""
    with open(path, newline="") as fh:
        rows = list(csv.DictReader(fh))
    grid = collections.defaultdict(dict)
    for r in rows:
        grid[(r["season"], r["window"])][float(r["si_mean"])] = r[onset_col]
    sis = sorted({float(r["si_mean"]) for r in rows})
    return rows, sis, grid


def main():
    out = []

    def say(line=""):
        out.append(line)
        print(line)

    say("si_invariance_check.py -- 26 October 2026")
    say("Does the onset estimate move when the assumed serial interval moves?")
    say()

    verdict = {}
    for label, fname, onset_col in GRIDS:
        path = os.path.join(HERE, fname)
        rows, sis, grid = cells(path, onset_col)
        moving = {k: v for k, v in grid.items() if len(set(v.values())) > 1}
        verdict[label] = (len(moving), len(grid))

        say("%s -- %s" % (label, fname))
        say("  %d rows, SI means %s, windows %s, %d seasons"
            % (len(rows), sis, sorted({r["window"] for r in rows}),
               len({r["season"] for r in rows})))
        say("  onset varies with the SI mean in %d of %d season-window cells"
            % (len(moving), len(grid)))
        for k in sorted(moving):
            v = moving[k]
            span = sorted(set(v.values()))
            say("    %-12s window %s: %s" % (k[0], k[1],
                ", ".join("%.1fd -> %s" % (si, v[si]) for si in sorted(v))))
            say("    %-12s %s distinct onsets: %s"
                % ("", len(span), ", ".join(span)))
        say()

    flu_moving, flu_total = verdict["influenza"]
    rsv_moving, rsv_total = verdict["RSV"]

    say("WHAT THIS SUPPORTS")
    say("  Influenza: %d of %d cells move. The onset does not depend on the serial"
        % (flu_moving, flu_total))
    say("             interval, which is what the degenerate weekly kernel predicts,")
    say("             and it is why the five-mean SI sensitivity grid returns four")
    say("             distinct configurations rather than twenty.")
    say("  RSV:       %d of %d cells move. The onset does depend on it."
        % (rsv_moving, rsv_total))
    say("  So the two halves of the pathogen contrast are not the same instrument.")
    say()
    say("WHAT IT DOES NOT SUPPORT")
    say("  The RSV effect rests on a small base: count the seasons, not the cells,")
    say("  before quoting it. The grids are unmatched (see the header). And nothing")
    say("  here bears on the within-pathogen signal-to-noise result, which does not")
    say("  use the kernel and is where the amplitude claim now sits.")

    with open(os.path.join(HERE, "si_invariance_check.txt"), "w") as fh:
        fh.write("\n".join(out) + "\n")

    ok = (flu_moving == 0) and (rsv_moving > 0)
    if not ok:
        print()
        print("CHECK FAILED: the pattern this script was written to record has changed.")
        print("Do not quote the 0-of-%d / %d-of-%d counts until this is understood."
              % (flu_total, rsv_moving, rsv_total))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
