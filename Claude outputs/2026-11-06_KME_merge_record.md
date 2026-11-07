# Kimberly Edwards's review, merged — 6 November 2026

Thomas's rule: **in a conflict, Vijay wins; everything else is fixed.** This records what that
produced, so the decision is auditable rather than remembered.

## What is in the files now

| | Editing copy | Submission copy |
|---|---|---|
| Her tracked changes | **233 marks**, authored "Kimberly Edwards", filterable on their own in the Review pane | applied, no markup |
| Her comments | **all 33**, under her own name | none, by construction |
| Comments in total | **67** — 4 of Vijay's, 24 of Thomas's replies, 6 recommendations, 33 of hers | 0 |
| Revisions in total | 224 Thomas, 233 Kimberly, 10 recommendation | **none of any kind** |

**34 of her 34 adopted paragraphs are in**, as 115 separately rejectable hunks plus 3 paragraphs
replaced whole because their hunks could not be given unique anchors. 135 build checks pass and
the build exits 0.

## The rule, applied

Her deletions were mapped **positionally** against a per-character authorship map of v11, not by
substring match, which over-counted. In **9 paragraphs** an edit of hers would have deleted words
Vijay wrote. In those, his wording stands and her version is reproduced for him under
**`[KME — WITHHELD ON YOUR WORDING]`** in the Open queries block of the editing copy.

| Para | What was held |
|---|---|
| 11 | her rewrite of his Abstract study-description clause |
| 12 | `seasons in which EpiEstim led had higher SNR` → `performed better in seasons with higher SNR` |
| 23 | `rather than an incidence level` → `as opposed to the date at which a baseline incidence threshold is surpassed` |
| 30 | `(onset 28 days after threshold)` → `(-28 days)`, and two words from his multi-restart sentence |
| 187 | deletion of `seed = 42, single fit` from the Table 1 footnote |
| 256 | deletion of the Fig 2 caption's four-of-eight count and its W and p |
| 282 | removal of his in-text variable codes and filenames |
| 286 | `A supplementary table (S1 Table) with exact start` → `Start` |
| 320 | deletion of the `S5 Fig` caption, which is half of a renumbering |

Two classes were **not** treated as conflicts, because they change no word of his: punctuation, and
a numeral spelled out as a word. Withholding those would have left the convention applied
everywhere except inside his sentences, which is a worse defect than the one it avoids.

## Repairs made on top of her file

Seven, each because taking her text as it stands would have lost something.

1. **A threshold value she dropped.** `predicted ahead of the  percent positive threshold` →
   `ahead of the 1.87% positivity threshold`.
2. **A range she flattened.** `shifted by 7 days` → `shifted by 0–7 days`.
3. **A cross-reference she deleted.** `(Methods)` restored in the same sentence.
4. **Her `(SX Table/Data)` placeholders**, twice, written out: once as the permutation method in
   words, once as `per-season values in S2 Table`. Both satisfy her own comment asking that
   analysis scripts not be named in the text.
5. **Two table-marker legends** she removed while the markers are still live in the cells:
   `† 2023/24 classified as multi-wave…` and `Multi = multiple age groups tied`, restored into her
   lettered footnotes, which keeps her a/b/c scheme and the definitions both.
6. **Her `Fig. 3a`** normalised to `Fig 3a`, which is the journal's style and what the rest of the
   manuscript uses.
7. **The `[TY-3]` provenance bracket** she deleted without answering, restored: the CHP access date
   still predates the last week of data.

Her two own slips were repaired rather than used as grounds to drop the paragraphs: a double space
in the Table 2 caption and the missing value above.

## Three things her review settled

- **Q1, the season count.** She reached eight influenza plus ten RSV independently. Adopted. The
  comment on it now records that she resolved it, and leaves one thing: she wrote "peaks" where the
  rest of the manuscript says pathogen-seasons, and one word should govern.
- **The affiliations.** She split the merged HKU line exactly as Vijay's own block does, and she
  puts Thomas on HKU-Pasteur as well. Her superscripts are adopted: **Thomas 1,2,3 and Vijay 1,2**.
  She is in the group and that is hers to know.
- **The 4.94% threshold.** She challenged its provenance and attached the CHP press release that
  settles it. That is `[VD-5]`, open since 30 October, and it now has a primary source.

## Two defects in the build, found and fixed

1. **The submission copy was leaking 19 move revisions.** Step 1 stripped `ins`/`del` inside
   `w:rPr` but not `moveTo`/`moveFrom`, and the "no tracked changes" check counted only `ins` and
   `del`, so it passed on a file holding 19 of them, unbalanced 18 to 1. Word repairs an unbalanced
   move on save by turning it into a plain insertion with the original author kept, which is how six
   paragraph marks dated 20 August reappeared in her file under Vijay's name. Both fixed: the
   stripper covers moves, and the check now asserts **zero revision elements of any kind**.
2. **Nothing checked that the two copies agreed.** A dropped hunk would have left the editing copy's
   text different from the submission copy's with every other check still passing. There is now an
   invariant: the editing copy, with the recommendations rejected, reproduces the submission copy
   paragraph for paragraph. It passes at 0 differences, and hunks are applied only after a string
   simulation confirms the sequence is faithful.

## Still open

`[TY-1]` the Zenodo DOI; `[TY-3]` the access date; `[VD-1]` ethics; `[VD-2]` acknowledgments;
`[VD-3]`–`[VD-5]`; `[TY-6]` the figure files; the repository licence; the 9 held paragraphs above;
her RSV serial-interval objection, which should be answered in the Discussion before submission;
whether the S5 → S1 Fig renumbering is done or dropped; and her role, which 233 tracked changes and
33 comments now make an authorship question rather than a courtesy one. **Nothing has been sent.**
