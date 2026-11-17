"""Kimberly Edwards's second pass, 10 November 2026 — what is applied, and what is not.

Her file is `2026-11-10_early-warning_PLOSCB_SUBMISSION-READY_KME.docx`. She continued
in her own 6 November copy rather than starting from the 7 November build, so it carries
321 revisions dated 6 November that are already merged here, on a base that predates the
twenty-three follow-up edits. Only the **192 revisions dated 10 November** and the
**15 comments dated 10 November** are new, and only those are considered below.

Three rules govern what is applied.

  1. Nothing supersedes text Vijay authored. Checked per mark against
     `vd_revisions_v11.json`: exactly one of her 10 November edits lands on his words
     (the ethics sentence), and it is held. The Methods block appears under his name in
     that record because he *moved* it; the prose inside it is Thomas's, so her Methods
     work is available to us.
  2. Nothing is applied that loses a reported fact, reverses a repair already made, or
     puts a placeholder in the manuscript.
  3. The Introduction and Discussion are his half by the April 2026 division, so her
     requests to expand them are carried as comments and not written.

Every HELD entry says which rule holds it. Nothing here changes a number.
"""

AUTHOR_KEY = 'KME2'

EDITS = [

 dict(id='KME2-01',
      source='Her comment 577, "repetition - trim", anchored on "that does not incorporate '
             'future observations. This confirms that the implementation does not use future '
             'observations".',
      evidence='The clause is stated twice in consecutive sentences. Removing the first '
               'occurrence leaves the inference intact and the second statement is the one '
               'that carries the caveat.',
      old='because EpiEstim uses a backward-looking sliding window that does not incorporate '
          'future observations. This confirms that the implementation does not use future '
          'observations',
      new='because EpiEstim uses a backward-looking sliding window. This confirms that the '
          'implementation does not use future observations'),

 dict(id='KME2-02',
      source='Her comment 559: "It’s not exactly the wrong parameter, per se, but the '
             'result of setting a prior value that assumes a longer duration of '
             'infectiousness and slower recovery."',
      evidence='Her own wording, in the manuscript’s vocabulary. The Methods already '
               'state that γ = 0.1/day is a 10-day infectious period against the '
               'literature-standard 0.2/day, so nothing is asserted that the paper does not '
               'already establish.',
      old='were largely an artefact of using the wrong parameter.',
      new='were largely an artefact of setting the recovery rate to a value that assumes a '
          'longer infectious period and slower recovery than the literature standard.'),

 dict(id='KME2-03',
      source='Her comment 571: "adjective as a noun here is slightly awkward... consider '
             'replacing with “an alternative metric” or “an alternative '
             'parameter”".',
      evidence='Her grammatical objection is right. Neither of her suggestions fits: '
               'wastewater is a different data source rather than a metric or a parameter, '
               'so the replacement uses the paper’s own term, "surveillance signal". '
               '**Her own version of this sentence reads "wastewater positivity", and that '
               'is not applied**: wastewater surveillance reports viral concentration, not '
               'percentage positivity.',
      old='or an alternative observable (e.g. wastewater)',
      new='or an alternative surveillance signal (e.g. wastewater)'),

 dict(id='KME2-04',
      source='Her comment 672, "no need to list scripts or files in the text", and her own '
             'deletion of the filename in the same paragraph.',
      evidence='Fifteen of the sixteen filenames she objects to were already out of the '
               'running text before she asked. This is the last one. The validation itself '
               '— five weeks checked against the published CHP tables — is kept, '
               'because it is the evidence that the scraped series is right; her own version '
               'deletes it, and that deletion is held.',
      old='the verification record, with the source page for each week, is '
          'rsv_source_verification_2026-11-05.md in the repository',
      new='the verification record, with the source page for each week, is committed to the '
          'repository'),

 dict(id='KME2-05',
      source='Her comment 739 on the Data availability statement: "insert hyperlink or '
             'reference."',
      evidence='The statement named the CHP pages without giving an address. The domain is '
               'the one already cited twice in Methods for the same series, so no new source '
               'enters the document.',
      old='and are available from its Flu Express and respiratory surveillance pages.',
      new='and are available from its Flu Express and respiratory surveillance pages at '
          'https://www.chp.gov.hk.'),

 dict(id='KME2-06',
      source='Her rewrite of the Methods "Data and code availability" paragraph, which '
             'removes the duplicated repository URL and the two sentences written as notes '
             'to ourselves.',
      evidence='"Unrelated files (phylodeep, treesimulator tests) remain in the repository '
               'and will be removed before submission" and "A licence file and archived DOI '
               '(Zenodo) will be added at submission" are internal notes that must not ship, '
               'and the URL appeared twice in consecutive sentences. The archived-DOI job is '
               'already carried by [TY-1] under Code availability, so **her placeholder '
               '"Zenodo (DOI: xxxxxxx)" is not used**.',
      old='All analysis code is available at https://github.com/thomasshuaiyuan/pinn-early-warning. '
          'The repository (https://github.com/thomasshuaiyuan/pinn-early-warning) includes all '
          'analysis scripts, data files, and supplementary materials. An environment.yml with '
          'version pinning, a data dictionary, supplementary season table, and all simulation '
          'and sensitivity scripts have been committed. Unrelated files (phylodeep, '
          'treesimulator tests) remain in the repository and will be removed before submission. '
          'A licence file and archived DOI (Zenodo) will be added at submission.',
      new='All analysis scripts, data files, and supplementary files are available at '
          'https://github.com/thomasshuaiyuan/pinn-early-warning, including an environment.yml '
          'with version pinning, a data dictionary, the supplementary season table, and all '
          'simulation and sensitivity scripts. The archived release is cited under Code '
          'availability.'),

 dict(id='KME2-07',
      source='Her comment 681, "restructure your parameters as a complete sentence".',
      evidence='The training settings were a telegraphic list. The settings themselves are '
               'unchanged, including the seed, which is **not** dropped: see the held item on '
               'the multi-restart seed list.',
      old='Training: 15,000 epochs, Adam optimiser, learning rate 10⁻³, StepLR '
          'scheduling (factor 0.5 every 3,000 epochs), gradient clipping at max norm 1.0. '
          'Random seed: 42. Single fit per season.',
      new='Each model was trained for 15,000 epochs with the Adam optimiser at a learning '
          'rate of 10⁻³, with StepLR scheduling (factor 0.5 every 3,000 epochs) and '
          'gradient clipping at a maximum norm of 1.0, as a single fit per season at random '
          'seed 42.'),

 # ---- her number convention, in the places where the words are Thomas's ----
 # She spells out numbers under ten in prose. Round one applied this wherever the
 # sentence was Thomas's; these are the sites her 10 November pass reached that round
 # one did not. The Abstract's "5 of 6" and "all 6 seasons" are NOT here: those words
 # are Vijay's, and the held list says so.

 dict(id='KME2-08',
      source='Her number convention, applied on 10 November to the Fig 2 legend.',
      evidence='The legend read "8" where the Results paragraph beside it already reads '
               '"eight".',
      # Anchored from "Fig 2." so it cannot also match the quotation of her own
      # version inside the held list, which reads "Fig 3."
      old='Fig 2. Admissions-based versus positivity-based onset detection. EpiEstim lead '
          'time relative to the CHP 4.94% threshold for laboratory positivity and for '
          '12–17 and 6–11 year hospital admissions across 8 influenza seasons',
      new='Fig 2. Admissions-based versus positivity-based onset detection. EpiEstim lead '
          'time relative to the CHP 4.94% threshold for laboratory positivity and for '
          '12–17 and 6–11 year hospital admissions across eight influenza seasons'),

 dict(id='KME2-09',
      source='Her number convention and her expansion of "SI" to "serial interval", both '
             'applied on 10 November.',
      evidence='"SI" is used as an abbreviation twice in this sentence and spelled out '
               'everywhere else in Methods. The count of 20 configurations is unchanged: the '
               'RSV grid genuinely varies, unlike the influenza grid, which the same '
               'paragraph already reports as resolving to four distinct outcomes.',
      old='RSV SI sensitivity was assessed across 20 configurations (5 SI means × 4 '
          'window widths) on 3 test seasons.',
      new='RSV serial-interval sensitivity was assessed across 20 configurations (five '
          'serial-interval means × four window widths) on three test seasons.'),

 dict(id='KME2-10',
      source='Her number convention, applied on 10 November in the Methods sensitivity '
             'sentences.',
      evidence='Same convention, same paragraph, Thomas’s prose.',
      old='range 0–21 days across 6 seasons, with 4 of 6 identical',
      new='range 0–21 days across six seasons, with four of six identical'),

 dict(id='KME2-11',
      source='Her number convention, applied on 10 November.',
      evidence='Same convention. The grid size itself is untouched.',
      old='a grid of 5 serial-interval means and 4 window widths for influenza',
      new='a grid of five serial-interval means and four window widths for influenza'),

 dict(id='KME2-12',
      source='Her number convention, applied on 10 November.',
      evidence='Same convention. "20" stays as a numeral because it is over ten.',
      old='the grid resolves to 4 distinct onset outcomes rather than 20',
      new='the grid resolves to four distinct onset outcomes rather than 20'),

 dict(id='KME2-13',
      source='Her number convention, applied on 10 November.',
      evidence='Same convention. **She also deleted the "(Results)" cross-reference here and '
               'that deletion is not applied**, because it is the only pointer from Methods '
               'to where the moved onset dates are reported.',
      old='moving in 3 of 12 season-window cells by 7 to 14 days',
      new='moving in three of 12 season-window cells by 7 to 14 days'),

 dict(id='KME2-14',
      source='Her edit to the S1 Table caption on 10 November.',
      evidence='Serial comma, matching the captions of S2 to S4 Table.',
      old='S1 Table. Season definitions, peak positivity and wave classification for all 18 '
          'pathogen-seasons.',
      new='S1 Table. Season definitions, peak positivity, and wave classification for all 18 '
          'pathogen-seasons.'),

 # ---- 10 Nov, Thomas: her number convention carried to every remaining count in
 # Thomas's own prose, so the text no longer mixes "four of six" with "5 of 6".
 # Rule: words for counts one to ten, numerals for 11 and above, and numerals kept for
 # n =, measurements, model settings, seed values and references. The Abstract
 # numerals stay as they are: they are Vijay's words (see HELD).
 dict(id='KME2-15',
      source='Number-convention sweep, Thomas, 10 November, carrying her convention '
             'from KME2-08 to KME2-14 to the sites her pass did not reach.',
      evidence='Count in running text, not a measurement. Results, SI sensitivity: the Methods sentence on the same result already reads "three of 12".',
      old='shift the detected onset in 3 of 12 season-window cells',
      new='shift the detected onset in three of 12 season-window cells'),

 dict(id='KME2-16',
      source='Number-convention sweep, Thomas, 10 November, carrying her convention '
             'from KME2-08 to KME2-14 to the sites her pass did not reach.',
      evidence='Count in running text, not a measurement. Results, pre-onset admissions.',
      old='range 120% to 786% across 3 seasons)',
      new='range 120% to 786% across three seasons)'),

 dict(id='KME2-17',
      source='Number-convention sweep, Thomas, 10 November, carrying her convention '
             'from KME2-08 to KME2-14 to the sites her pass did not reach.',
      evidence='Count in running text, not a measurement. Results, post-COVID comparison.',
      old='With only 3 post-COVID seasons,',
      new='With only three post-COVID seasons,'),

 dict(id='KME2-18',
      source='Number-convention sweep, Thomas, 10 November, carrying her convention '
             'from KME2-08 to KME2-14 to the sites her pass did not reach.',
      evidence='Count in running text, not a measurement. Results, RSV: the same sentence opens "Across ten RSV seasons", in her wording.',
      old='(median −18 days across all 10 seasons)',
      new='(median −18 days across all ten seasons)'),

 dict(id='KME2-19',
      source='Number-convention sweep, Thomas, 10 November, carrying her convention '
             'from KME2-08 to KME2-14 to the sites her pass did not reach.',
      evidence='Count in running text, not a measurement. Results, recovery-rate sensitivity.',
      old='from detecting onset in 3 of 6 seasons to 6 of 6, with burn-in R(t) dropping below 1.0 in 5 of 6 seasons.',
      new='from detecting onset in three of six seasons to six of six, with burn-in R(t) dropping below 1.0 in five of six seasons.'),

 dict(id='KME2-20',
      source='Number-convention sweep, Thomas, 10 November, carrying her convention '
             'from KME2-08 to KME2-14 to the sites her pass did not reach.',
      evidence='Count in running text, not a measurement. Results, pseudo-prospective.',
      old='identical to the retrospective analysis in all 6 influenza seasons',
      new='identical to the retrospective analysis in all six influenza seasons'),

 dict(id='KME2-21',
      source='Number-convention sweep, Thomas, 10 November, carrying her convention '
             'from KME2-08 to KME2-14 to the sites her pass did not reach.',
      evidence='Count in running text, not a measurement. Discussion, limitations.',
      old='(0-day delay across 6 seasons)',
      new='(0-day delay across six seasons)'),

 dict(id='KME2-22',
      source='Number-convention sweep, Thomas, 10 November, carrying her convention '
             'from KME2-08 to KME2-14 to the sites her pass did not reach.',
      evidence='Count in running text, not a measurement. Discussion, limitations.',
      old='a multi-restart analysis with 5 seeds was conducted and showed stable results for 3 of 6 seasons',
      new='a multi-restart analysis with five seeds was conducted and showed stable results for three of six seasons'),

 dict(id='KME2-23',
      source='Number-convention sweep, Thomas, 10 November, carrying her convention '
             'from KME2-08 to KME2-14 to the sites her pass did not reach.',
      evidence='Count in running text, not a measurement. Discussion, limitations: her round-one insertion elsewhere reads "eight influenza and ten RSV".',
      old='(6 influenza, 10 RSV)',
      new='(six influenza, ten RSV)'),

 dict(id='KME2-24',
      source='Number-convention sweep, Thomas, 10 November, carrying her convention '
             'from KME2-08 to KME2-14 to the sites her pass did not reach.',
      evidence='Count in running text, not a measurement. Methods, season definitions.',
      old='in the admissions comparison (8 seasons total). For RSV, 10 seasons were defined spanning peak timing from April to December. S1 Table gives',
      new='in the admissions comparison (eight seasons total). For RSV, ten seasons were defined spanning peak timing from April to December. S1 Table gives'),

 dict(id='KME2-25',
      source='Number-convention sweep, Thomas, 10 November, carrying her convention '
             'from KME2-08 to KME2-14 to the sites her pass did not reach.',
      evidence='Count in running text, not a measurement. Methods, season classification.',
      old='as multi-wave (2 peaks each) and the remaining 6 influenza seasons',
      new='as multi-wave (two peaks each) and the remaining six influenza seasons'),

 dict(id='KME2-26',
      source='Number-convention sweep, Thomas, 10 November, carrying her convention '
             'from KME2-08 to KME2-14 to the sites her pass did not reach.',
      evidence='Count in running text, not a measurement. Methods, PINN. The seed list itself stays numerals.',
      old='Multi-restart analysis with 5 seeds (42, 123, 456, 789, 1024) showed stable results for 3 of 6 seasons',
      new='Multi-restart analysis with five seeds (42, 123, 456, 789, 1024) showed stable results for three of six seasons'),

 dict(id='KME2-27',
      source='Number-convention sweep, Thomas, 10 November, carrying her convention '
             'from KME2-08 to KME2-14 to the sites her pass did not reach.',
      evidence='Count in running text, not a measurement. Methods, PINN.',
      old='later than the other 4)',
      new='later than the other four)'),

 dict(id='KME2-28',
      source='Number-convention sweep, Thomas, 10 November, carrying her convention '
             'from KME2-08 to KME2-14 to the sites her pass did not reach.',
      evidence='Count in running text, not a measurement. Fig 3 legend.',
      old='averaged across 5 single-wave seasons',
      new='averaged across five single-wave seasons'),
]


# Her 15 comments of 10 November, carried into the editing copy under her own name.
# (paragraph context, span to anchor on, comment text)
COMMENTS = [
 ('Whether adolescents serve as early amplifiers of community transmission',
  'Whether adolescents serve as early amplifiers of community transmission',
  'this is okay here, but could be further elucidated in the discussion - including '
  'alternative interpretations with additional references.'),

 ('Discussion', 'Discussion',
  'I think you still need to address the practical implications of these results. Is an '
  "earlier detection necessarily 'better' if it predicts epidemic onset >30 days in "
  'advance? How can these retrospective analyses & tools inform future public health '
  'preparedness?'),

 ('The finding that changes the interpretation of the entire analysis',
  'an artefact of setting the recovery rate',
  "Rephrase here. It's not exactly the wrong parameter, per se, but the result of setting a "
  'prior value that assumes a longer duration of infectiousness and slower recovery.'),

 ('The structural interpretation could be tested by applying these methods',
  'an alternative surveillance signal',
  'adjective as a noun here is slightly awkward... consider replacing with "an alternative '
  'metric" or "an alternative parameter", etc.'),

 ('a pseudo-prospective evaluation was conducted',
  'a backward-looking sliding window',
  'repetition - trim'),

 ('This analysis has several limitations worth noting', 'Eighth',
  'Vary your transitions and sentence structure. Once you get to the fifth, sixth, seventh, '
  'limitation, it starts to read like a list of bullet points. Alternatively, incorporate '
  'each of these limitations into the other subsections above. You can also consider '
  'combining the results and discussion into a single section, as some of the subheadings '
  'are redundant.'),

 ('Finally, the COVID-era exclusion', 'Finally, the COVID-era exclusion',
  "Don't end on limitations, give an overarching conclusion. Summarize contributions of this "
  'paper to existing body of knowledge and highlight knowledge gaps for further '
  'study/consideration.'),

 ('The Cori et al. [2] Bayesian renewal equation framework was implemented in Python',
  'The Cori et al. [2] Bayesian renewal equation framework was implemented in Python',
  'no need to list scripts or files in the text.'),

 ('and a parameter network (2 hidden layers, 32 neurons) outputting time-varying',
  'R(t) = β(t)·S(t)/γ',
  'from PLOS Comp Bio guidelines: We recommend using MathType for display and inline '
  'equations, as it will provide the most reliable outcome. If this is not possible, '
  "Equation Editor or Microsoft's Insert→Equation function is acceptable."),

 ('Each model was trained for 15,000 epochs',
  'Each model was trained for 15,000 epochs',
  'restructure your parameters as a complete sentence. Probably unnecessary to say the exact '
  'random number seeds used, as those should be available in the code repository.'),

 ('Multi-restart analysis with five seeds',
  'Multi-restart analysis with five seeds (42, 123, 456, 789, 1024)',
  'move to results'),

 ('Pre-onset amplification was measured as percentage change',
  '1.645, 1.96, 2.58',
  'use a consistent number of significant digits'),

 ('[VD-1 — ETHICS STATEMENT]', '[VD-1 — ETHICS STATEMENT]',
  'update'),

 ('All data analysed in this study are from public sources',
  'https://www.chp.gov.hk',
  'insert hyperlink or reference.'),

 ('References', 'References',
  'you have very few references cited here. Expand on some of the more general claims in the '
  'intro and discussion. For example, "Lau et al. [6] did not evaluate R(t)-based onset '
  'detection; Garrido-Garcia et al. [4] deliberately avoided R(t); and Millevoi et al. [9] '
  'applied PINNs to parameter estimation without cross-pathogen comparison or onset '
  'detection benchmarking."'),
]


# Her 10 November changes that are NOT applied, with the rule that holds each.
HELD = [
 dict(what="The Abstract's remaining numerals: “5 of 6 seasons”, “detected in "
           "3”, “all 6 seasons” → “five of six”, “three”, "
           "“six”.",
      rule='Rule 1 — Vijay authored it',
      why="Those exact fragments are in vd_ins: “of 6”, “and onset was "
          "detected”, “in 3, whereas”, “recovered onset in all 6 "
          "seasons”. This is why the first half of the sentence reads “five of "
          "six” and the second half does not: round one applied her convention only "
          "where the words were Thomas’s. Her version is listed for him to adopt."),

 dict(what='The ethics sentence: “As all data are publicly available in aggregate form '
           'from CHP, with no individual-level information” → “As all data are '
           'de-identified and publicly available in aggregate”.',
      rule='Rule 1 — Vijay authored it, and it is his determination',
      why='The phrase she deletes is his inserted wording, and the ethics determination is '
          '[VD-1], which is his to supply. Her comment 738, “update”, anchors on '
          'that bracket. Separately, “de-identified” would be a drift rather than a '
          'tidy: aggregate surveillance counts were never identified, and “de-identified” '
          'implies individual records existed and were stripped.'),

 dict(what='“onset dates shifted by 0–7 days for most seasons” → '
           '“shifted by 7 days”.',
      rule='Rule 2 — reverses a repair already made',
      why='This is the same edit of hers that was repaired on 6 November, made a second time. '
          'The range includes zero because several seasons do not move at all; “7 days” '
          'states that every season moves by a week.'),

 dict(what='“EpiEstim detected epidemic onset in all 10 but led the threshold in only '
           'four” → “could detect epidemic onset but predicted ahead … in '
           'only four”.',
      rule='Rule 2 — loses a reported fact',
      why='Detection in all ten RSV seasons is a result. Her version drops it and leaves the '
          'sentence reporting only the failure to lead.'),

 dict(what='Deleting the five manually validated weeks from the RSV Methods paragraph.',
      rule='Rule 2 — loses the evidence',
      why='2015-W21, 2015-W35, 2019-W44, 2019-W52 and 2022-W18 were checked against the '
          'published CHP tables and matched exactly. That is the only evidence the scraped '
          'series is correct, and the scraper is the sole source of the RSV arm. The filename '
          'is removed instead — KME2-04.'),

 dict(what='“scipy.signal.find_peaks on 3-week rolling-mean smoothed positivity” '
           '→ “a smoothed three-week rolling-mean positivity”.',
      rule='Rule 2 — misdescribes the method',
      why='The rolling mean is the smoothing; find_peaks with prominence and distance is the '
          'detection. Her version names the smoothing and drops the algorithm, which leaves '
          'the prominence and distance settings attached to nothing. The filename in the same '
          'sentence was already removed before she asked.'),

 dict(what='“and is not modelling-free” deleted from the sentence on '
           'threshold-crossing.',
      rule='Rule 2 — loses a reported fact',
      why='It is the point of the sentence: the comparator is not assumption-free either.'),

 dict(what='“R(t) > 1.0” → “R(t) >1.0”, in two places.',
      rule='Rule 2 — inconsistent with the rest of the manuscript',
      why='The spaced form is used at every other occurrence. PLOS sets no such style.'),

 dict(what='“Supplementary Appendix”, and an unnumbered “S” placeholder, in four places.',
      rule='Rule 2 — placeholder, and the text already names the right item',
      why='Each site already cites a numbered supporting item (S2 Table, S3 Table, S4 Table). '
          'An unnumbered placeholder is a note to herself, not final text.'),

 dict(what='“What this means is that the preliminary results …” → '
           '“The preliminary results …”, and “If this holds up” '
           '→ “If this holds”.',
      rule='Rule 2 — against the voice spec fixed at v8',
      why='“What this means is that” and “If this holds up” are both on '
          'the list of Thomas’s own constructions the manuscript preserves deliberately. '
          'They are also what keeps the prose off the AI-detection register. Overruling that '
          'is Thomas’s call, not a session’s.'),

 dict(what='Deleting the TY-3 provenance-date bracket from the data-sources paragraph.',
      rule='Rule 2 — ours to fill, not to drop',
      why='The access date and the last data week still disagree. Removing the bracket '
          'removes the reminder, not the inconsistency.'),

 dict(what='Deleting the multi-restart seed list (42, 123, 456, 789, 1024), and the hardware '
           'line.',
      rule='Rule 2 — reproducibility, and a decision rather than an edit',
      why='Her reasoning in comment 681 is sound — seeds belong in the repository — '
          'but the five seeds are what makes the stability claim checkable, and the paper '
          'reports results from one of them. Her restructuring of the training settings is '
          'applied without the deletion (KME2-07). Thomas’s call.'),

 dict(what='“percentage change” → “percent change”.',
      rule='Rule 2 — inconsistent with the manuscript’s spelling',
      why='The manuscript is in British spelling throughout (normalised, characterisation, '
          'modelling).'),

 dict(what='“an alternative observable (e.g. wastewater)” → “(e.g., '
           'wastewater positivity)”.',
      rule='Rule 2 — factually wrong',
      why='Wastewater surveillance reports viral concentration or detection, not percentage '
          'positivity. Her grammatical point about “observable” is applied '
          '(KME2-03); the word “positivity” is not.'),

 dict(what='“S5 Fig” → “S1 Fig”, in both places.',
      rule='Decision — now applicable, and it moves a file',
      why='Round one withheld this because her renumbering left one figure cited as both S1 '
          'Fig and S5 Fig. She has now made it consistent, so the objection is gone. Two '
          'things to know before adopting it. It renames S5_Fig.tif, which sits under the '
          'deferred figure work [TY-6], and the text would cite S1 Fig while the file is still '
          'S5_Fig.tif until that happens. And it is a preference rather than a requirement: '
          'the PLOS submission guidelines, read at source on 10 November, ask only that a '
          'supporting item’s name “contains an “S” and number” and '
          'set no separate sequence for figures and tables.'),

 dict(what='Her comment 716, consistent significant digits on the multipliers 1.645, 1.96, '
           '2.58.',
      rule='Decision — cannot be made from the manuscript alone',
      why='The three thresholds (5.21%, 5.70%, 6.65%) were computed from whichever values the '
          'code used. Printing 1.645, 1.960, 2.576 without checking the code would risk the '
          'manuscript disagreeing with the committed output. Read the multiplier out of the '
          'script first, then print it to matching precision.'),

 dict(what='Her comment 682, move the multi-restart sentence from Methods to Results.',
      rule='Decision — structural, and the same kind as round one’s three move '
           'requests',
      why='Her first pass asked for three other relocations, all still open. These belong in '
          'one decision rather than one at a time.'),

 dict(what='Her comments 524, 540, 595, 596 and 740: expand the Discussion, add an '
           'overarching conclusion, restructure the limitations, cite more of the general '
           'claims.',
      rule='Rule 3 — his half of the writing',
      why='The Introduction and Discussion are Vijay’s by the April 2026 division. These '
          'are the strongest comments in her second pass and they are carried to him intact, '
          'not pre-written. Comment 595 also proposes merging Results and Discussion, which '
          'would change the PLOS section order he set.'),

 dict(what='Her comment 680, MathType for the equations.',
      rule='Decision — production, and her quotation checks out',
      why='Her quotation is verbatim from the PLOS Computational Biology submission '
          'guidelines, verified at source on 10 November. The same page also says to avoid '
          'MathType for single variables, and most of this manuscript’s mathematics is '
          'single variables and one short inline relation. It is a decision about the upload, '
          'not a text edit.'),
]
