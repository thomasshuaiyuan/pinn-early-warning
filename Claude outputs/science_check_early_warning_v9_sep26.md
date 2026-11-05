# Independent check of the early-warning v9 package: handoff to the science session, 26 September 2026

*Written by the Cowork session that built v9, for a session that did not. **Treat everything this session
claims as unverified.** The same session produced v8, which its own later audit found had two of Vijay's
19 August points unclosed, and it produced the first v9, which had five. The check exists because
Vijay's 25 September note, rule 9, says checks run before sending, not after. **Nothing has been sent.***

---

## 0. The job, in one paragraph

Before Thomas sends Vijay a OneDrive link to the v9 package, establish independently whether (a) every
number in the manuscript, figures and supplementary traces to a committed repository output, (b) each of
Vijay's 19 August points is actually closed, (c) the package obeys his 25 September note, and (d) the
manuscript is a faithful edit of the file Vijay commented on. Report findings; **do not edit any
Vijay-facing file.** Section 3 lists problems a fresh read has already found. Confirm or refute each, and
find the ones it missed.

---

## 1. Where everything is

| What | Where |
|---|---|
| Shared folder (Vijay's single source of truth) | `~/Library/CloudStorage/OneDrive-TheUniversityofHongKong-Connect/Thomas early-warning/` with `0_raw_data`, `1_clean_data`, `2_results`, `3_docs`, `4_arc`, `5_bin`, `README.txt` |
| The package under check | `3_docs/2026-09-26_early-warning_v9.docx`, `_v9_figures.docx`, `_v9_supplementary.docx`, `_v9_CHANGELOG.txt` |
| Repository | `~/pinn-early-warning` (GitHub `thomasshuaiyuan/pinn-early-warning`). Last commit `e6ba71e`. **Seven files modified or new and uncommitted**: `generate_supplementary.py`, `outstanding_analyses.py`, `rsv_si_sensitivity.csv`, `supplementary_table_S1_seasons.csv`, `wilcoxon_admissions.py` (new), `wilcoxon_admissions_results.csv` (new). A stale `.git/index.lock` is present (0 bytes). |
| Build scripts for the three .docx | Project store: `claude/early_warning_v9_build_manuscript.py`, `claude/early_warning_v9_build_supp_figs.py`. They carry the Cowork container's absolute paths; adjust before re-running. |
| The Cowork session's own audit | `claude/early_warning_v9_audit_sep26.md`. Read it as a list of claims to test, not as a result. |
| Vijay's instructions | 19 August email (verbatim in §2), 25 September note (rules quoted in §2), his four manuscript comments (§2) |
| Vijay's commented base file | **Not in the folder.** `manuscript_v7_vijay_4_VJ.docx`, attached to his email of 19 Aug 21:54 (Gmail thread "Re: Pre-arrival update: revised manuscript (v7)"). Thomas is to place it in `4_arc/`. The project store holds only a **text export** of it (`manuscript_v7_vijay_4_VJ.docx` via `project_read`). |

---

## 2. Ground truth: what Vijay asked for

**19 August, 09:22 (verbatim bullets):**
1. The PINN date-anchoring problem remains in the gamma-sensitivity and multi-restart scripts. Correct it and regenerate the affected onset dates, lead times, tables, and text.
2. The committed multi-restart results support three stable seasons with detection in 5/5 runs and onset ranges of 7–20 days, not four.
3. W=10.5 reproduces, but the reported one-sided p=0.31 does not. Confirm the Wilcoxon implementation, handling of zeros and ties, software version, and saved output.
4. Most of the 50 simulation runs appear to be deterministic repetitions rather than independent replicates. Introduce stochastic variation or describe them as repeated scenario evaluations and revise the uncertainty estimates accordingly.
5. The reported SNR medians and logistic-regression probabilities do not reproduce from the committed table.
6. Reconcile the threshold values of 4.94%, 5.70%, and 6.47%; the PINN leads in Tables 1 and 2; the 6.8 versus 8-day serial-interval result; and the admissions and GP percentage changes.
7. Correct the RSV analysis windows in Table S1 and the coverage values in the data dictionary.
8. (Note) The pseudo-prospective analysis shows the implementation does not use future observations; it does not demonstrate zero operational delay.
9. (Process) First update the repository with corrected analyses and saved outputs, then regenerate manuscript, tables, figures and supplementary from those outputs.

**19 August, 21:54:** he returned his revision of the Abstract, Introduction and Methods opening ("<VJ stopped here>") and asked that it be incorporated into the version generated from corrected outputs. **His 25 September note calls this "the commented manuscript" and makes it the base.**

**His four comments in that file:** (1) title alternative, "Signal amplitude and recovery-rate assumptions limit R(t)-based season onset detection for influenza and RSV"; (2) on "Timely": "the practical utility of epidemic onset in HK or other regions is not quite clear, affecting impact of study."; (3) on the threshold: "i.e. what does this drive?"; (4) on the threshold-derivation parenthetical: "This shouldnt be here."

**25 September note, the rules that bind this package:** 1 single shared OneDrive location with the repo linked; 2 date and version in filenames; 3 changelog of one or two lines per revision; 5 state what is superseded; 6 the commented manuscript is the base, do not branch from it, point-by-point responses in the document; 8 numbers from tested, frozen outputs; 9 checks before reporting; 11 corrections live in documents; 14 close August comments before new work; 16 do not alter his wording or framing without asking first; 17 no silent restructuring, e.g. the adolescent-admissions finding; 19–21 short email, one marked question, summary first; 25 one current version, one open question, one next step. Immediate next step: the manuscript with point-by-point responses via a link, plus one line on whether "the methods paper and the thesis chapter are one draft or two".

---

## 3. What a fresh read already found (unfixed; confirm or refute each)

Severity: **A** blocks sending; **B** should be fixed or explicitly raised before sending; **C** minor.

| # | Sev | Finding | Evidence | What would settle it |
|---|---|---|---|---|
| F1 | **A** | **v9 was reconstructed from a text export of Vijay's file, not built on his .docx.** His tracked changes appear flattened into base text, his four comments were re-created (they now carry today's date), and the anchor of his comment 3 was guessed ("baseline threshold value"). | The export contains patterns that look like a deletion and an insertion rendered side by side: "and spould be read as and should be read as"; "modelling studies.studies."; "[to be confirmed with institutional review]. data."; and two overlapping ethics sentences. v9 "fixed" the first three as typos (tracked, Thomas Yuan) and raised the ethics pair as a question (comment 10). **If these are his tracked edits, v9 changes his chosen wording and asks him a question he already answered**, against rules 6 and 16. | C1 |
| F2 | B | The Results say EpiEstim detected onset in "all 6 single-wave influenza seasons", but one of the six (2023/24) is multi-wave in Table 1 and Table S1; the pre-onset Results correctly say 5 single-wave seasons. Inherited from v7. | v9 accepted text; Table 1 "Multi†"; S1 | Read; decide whether it is his text (raise) or Thomas's (fix) |
| F3 | B | An unfilled citation placeholder, "(ref)", in Introduction paragraph 1 (RSV calendar months). Vijay's text. [1] Obando-Pacheco appears to be intended. | v9 accepted text | Read; raise with him rather than edit (rule 16) |
| F4 | B | Internal scope mismatches: the Abstract says "2014 and 2025", the title "2014–2026"; the Author Summary says "16 influenza and RSV seasons", the Introduction "18 pathogen-seasons". Vijay's wording in part. | v9 accepted text | Read; list for him |
| F5 | B | The Methods state 157 excluded COVID-era weeks with mean positivity 0.68%. A recompute from `flux_data.csv` (From parsed as DD/MM/YYYY, 2020-01-01 to 2022-12-31) gives **156 weeks, 0.62%**. Not traced to a committed output. | Cowork recompute; `final_supplementary.py` presumably holds the original | C2 and C3; find the window definition that gives 157 |
| F6 | B | Table 1 "Adm sig." mislabels ties. The caption defines "Multi = multiple age groups tied", but 2018/19 (6–11y and 12–17y both onset 2018-10-17) reads "12-17y" and 2024/25 (0–5y and 6–11y both 2024-09-04) reads "0-5y". | `epiestim_admissions_results.csv` | C2 |
| F7 | B | Three committed outputs still carry pre-revert CHP onset dates (e.g. 2015/16 2016-01-20, not 2016-01-13): `pseudo_prospective_results.csv`, `epiestim_ci_onset_comparison.csv`, `epiestim_si_sensitivity_flu.csv`. The manuscript uses only quantities that do not depend on the threshold (the 0-day delay, CI-vs-mean differences, SI spread), but **these files are now copied into `2_results/`, where Vijay will read them**, and they contradict Table 1. | the CSVs | C3: regenerate at 4.94% and confirm the manuscript values do not move |
| F8 | B | **Supplementary Table S4A (influenza) is computed inside the .docx build script**, which re-anchors the SI-sweep leads to 4.94% dates; no committed script produces it. The build scripts are not in the repository at all. This goes against "tables from code" and rule 8. | `early_warning_v9_build_supp_figs.py` | C3/C9 |
| F9 | B | References: only refs 4, 11 and 13 were checked this pass. The other twelve have not been through `verify_citations.py` for this version. Ref 12's DOI ends in "v2" (`10.64898/2026.01.16.26344284v2`), which is a URL version suffix, not part of a DOI. | reference list | C6 |
| F10 | B | Comment 8 tells Vijay that CHP publishes 4.94% "verified in the 2 July 2026 report and the 3 January 2026 press release". That rests on project notes (`v8_threshold_correction_494.md`), not on a primary source read in this pass. It is now a factual claim put to him. | project notes only | C7 |
| F11 | B | Repository changes are uncommitted, so README and CHANGELOG carry `RECORD-HASH` and rule 8 is not yet met. `Claude outputs/` in the repo holds a stale v9 copy. The OneDrive rename left an empty `early-warning/` folder. | git status; OneDrive listing | C5 |
| F12 | C | The Methods say the Wilcoxon used "the exact null distribution", but two absolute differences are tied (21, 21). p = 0.0625 = 1/16 is also the sign-flip permutation minimum for 4 all-positive pairs, so the value stands; the wording may overclaim. scipy 1.17.1 default gives 0.0625 with no warning; `method='approx'` gives 0.0328. | cloud run | C8 wording check |
| F13 | C | The Results cite Fig. 2 for the SNR logistic relationship, but Fig. 2 plots peak positivity, not SNR. The Methods give "Intel MacBook Pro" as the software platform, while current compute is Apple Silicon; confirm which produced the reported PINN runs. The Discussion says the CHP 4.94% "was derived primarily from pre-pandemic data" with no source. | figures; Methods; Discussion | Read |
| F14 | C | 20 comments in the manuscript: Vijay's 4, Thomas's 4 replies, 2 open questions (ethics wording, degenerate adolescent fits), and 10 point-by-point responses to 19 August. Against rule 25 ("one open question"), judge whether the load is right, and whether comment 10 should exist at all once F1 is resolved. | comments.xml | C5 |

**Also claimed by the Cowork session, and each needs independent confirmation, not acceptance:**
- **Wilcoxon:** the committed `outstanding_analyses.py` tested the normalised-scaling rerun (W = 10.5, p = 0.25, the source of v7's 10.5). The new `wilcoxon_admissions.py` tests the primary admissions output: W = 10.0, one-sided p = 0.0625, median 10.5, bootstrap CI 0 to 42. Excluding the degenerate 2014/15 and 2015/16 fits gives W = 6.0, p = 0.125.
- **Table S1:** its RSV windows previously differed from `epiestim_rsv.py`. They were regenerated, and weeks and peaks now match `epiestim_rsv_results.csv` exactly. `rsv_si_sensitivity.csv` was rerun on the same windows, giving SD 8.0–8.2 days (previously stated as 9–12).
- **The threshold:** no data-derived variant reproduces 4.94%. The 2014–2019 method gives 6.47%, 2014–2026 excluding COVID gives 5.70% (recompute 5.73%), and including COVID gives 3.15%.
- **The eight tracked changes inside Vijay's edited region** are one requested number, one citation and six typos. F1 may overturn "typos".

---

## 4. Registered checks

Write each check's pass criterion into the results file **before** running it. The criteria below are fixed now.

**C1. Fidelity to Vijay's file (settles F1). Run first; it can change everything downstream.**
Needs the real `manuscript_v7_vijay_4_VJ.docx` in `4_arc/`. If it is absent, stop C1, record it as blocking, and continue with the others.
- Extract from his .docx: every `w:ins` and `w:del` with author and text, every comment with its id, anchor text and date, and the accepted-all text.
- Diff his accepted-all text against v9's text with Thomas's tracked changes rejected. **Pass:** every difference is either one of v9's listed tracked changes or explained. **Fail:** any of his tracked edits that v9 reverses, duplicates or flattens, or any comment whose anchor differs.
- Specifically settle whether "spould be read as and should be read as", "studies.studies.", ". data." and the two ethics sentences are his del/ins pairs. If they are, v9's "typo fixes" and comment 10 are wrong, and the correct rebuild is **edit his .docx in place** (add Thomas's tracked changes and comments to his XML) rather than regenerate it.

**C2. Number trace.** Extract every numeric token from v9's accepted text, the table cells, the figure legends and the supplementary tables. Map each to a committed file and row. **Pass:** 100% mapped, or each unmapped number listed with a reason. Starting extractor (operates on `word/document.xml`, skips deleted text):
```python
import re, zipfile
from lxml import etree
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
root = etree.fromstring(zipfile.ZipFile("2026-09-26_early-warning_v9.docx").read("word/document.xml"))
def text(p):
    out = []
    for t in p.iter(W + "t"):
        a = t
        while a is not None and a.tag != W + "del":
            a = a.getparent()
        if a is None:
            out.append(t.text or "")
    return "".join(out)
for i, p in enumerate(root.iter(W + "p")):
    s = text(p)
    for m in re.finditer(r"[−\-+]?\d+(?:\.\d+)?%?", s):
        print(i, m.group(), "|", s[max(0, m.start()-50):m.end()+30].replace("\n", " "))
```

**C3. Regenerate from scripts.** In the `pinn` environment, at the repository state to be committed: run `generate_supplementary.py`, `wilcoxon_admissions.py`, `snr_analysis.py`, `preonset_analysis.py`, `outstanding_analyses.py` (RSV sweep section), and the scripts behind the three stale CSVs in F7 (`pseudo_prospective.py`, `remaining_analyses.py`, `epiestim_si_sensitivity.py`), all with `CHP_THRESHOLD = 0.0494`. **Pass:** outputs byte-identical to committed files, or every difference explained. For F7 in particular: **the manuscript quantities must not move** (0-day delay in 6/6; CI-vs-mean median 0, range 0–21, 4/6 identical; influenza SI SD 3.1–11.4, mean 6.8, range 7–28). Put the S4A re-anchoring into a repository script (F8). Record `scipy`, `numpy` and `pandas` versions.

**C4. The 19 August list.** For each of points 1–9 in §2, re-derive independently from the repository and state *closed*, *partly closed* or *open*, with the evidence. Do not start from the Cowork audit's table; compare against it only at the end.

**C5. The 25 September note.** Check each binding rule in §2 against the actual files: folder layout and README link; every filename dated and versioned; changelog one or two lines per revision; supersedes stated; responses in the document; nothing in his wording changed without a question; the adolescent section untouched; the draft email (below) one marked question, summary first. Record the commit hash that should replace `RECORD-HASH`.

**C6. Citations.** Run `verify_citations.py` on all 15 references **from a machine that reaches api.crossref.org** (the Cowork container cannot). Read `refs_check_sep12.json`, `refs_check_sep19.md` and `refs_check_sep20.md` first; they are one record. Check retraction status (`update-to`, `relation`). **Pass:** 15/15 OK, with UNVERIFIED hand-resolved and recorded. Include ref 12's DOI form and the content claim "Garrido-Garcia et al. [4] deliberately avoided R(t)".

**C7. The 4.94% claim.** Locate a CHP primary source that states the 4.94% laboratory-positivity baseline (a Flu Express issue or press release, with URL and date). **Pass:** quoted and recorded. If it cannot be found, comment 8 and the draft email's question must not go to Vijay as written.

**C8. Document integrity.** Open all three .docx in Word or LibreOffice. Check that tracked changes are attributed to "Thomas Yuan" and render; every comment is anchored where its text says; there are no em dashes, contractions or first-person singular in Thomas-added manuscript text (comments are exempt); the format spec holds (Times New Roman 12, 1.5 spacing, page numbers, bulleted Highlights, Methods after the Introduction). Check the Wilcoxon wording (F12).

**C9. Cross-document agreement.** Every value stated in more than one place (Abstract, Results, tables, figure legends, supplementary, comments) agrees. **Pass:** no disagreements.

**C10. The draft email.** Thomas intends to send:
> v9 is at [link], in 3_docs, with figures, supplementary and a changelog. It is built on your 19 August revision with your wording unchanged; my responses to your comments and to each point of your 19 August email are comments in the document. / Methods paper and thesis chapter: [his line]. / **Question:** the Abstract and Introduction describe 4.94% as a reconstruction from 2014–2019 data. That wording began in my earlier draft and is wrong: that method gives 6.47%, and 4.94% is the baseline CHP publishes. May I replace both sentences with the wording proposed in the comment on the Introduction?

Test every factual clause against C1–C9. **"Built on your 19 August revision with your wording unchanged" fails if C1 fails.** "Each point … is closed" fails if C4 finds any point open. Note separately: the methods-paper line refers to the avoidable-vs-irreducible work (Vijay's 24 September reply: "chapter, conditional on the grid"), not to this manuscript.

---

## 5. Constraints

- **Read-only on everything Vijay will see**: `3_docs/`, the comments, the email. Findings go in `claude/science_check_early_warning_v9_results_sep26.md`. Proposed fixes are listed there, not applied.
- Repository: regenerating existing outputs (C3) is in scope. **No new analysis, dataset or specification** (rules 12–13). Commit only on Thomas's instruction, and stage explicit paths. Remove `.git/index.lock` only if no git process is running.
- Do not contact Vijay. Do not re-open any question his 19 August list or 24 September reply settled.
- **Stopping rule:** one pass through C1–C10. If C1 fails, stop after C1 and C6, report, and let the rebuild happen before running the rest; re-checking a document that is about to be replaced is the loop Part II's stopping rule exists to prevent.

## 6. Report format

One table: check, pass criterion, result (PASS / FAIL / BLOCKED), evidence (file and row, or command and output). Then, separately:
1. Findings from §3 confirmed, refuted or modified.
2. New findings, with the same severity scale.
3. The one-line verdict: **send**, **send after listed B-fixes**, or **do not send; rebuild required**.

## 7. Verification status of this handoff

- The 19 August email text and the 25 September rules are quoted from Thomas's paste of the Gmail thread and the note on 26 September.
- F5, F6, F12 and the Wilcoxon and threshold claims come from computations run in the Cowork container on staged copies of the repository files; they are not reproduced on the Mac.
- F1 is an inference from patterns in a text export; it is the most consequential claim here and the least verified.
- Nothing in this document has been put to Vijay.
