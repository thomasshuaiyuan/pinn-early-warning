"""Edits that answer a specific comment, each traceable to its source.

Every entry names the comment it answers and the evidence it rests on. Nothing
here is a preference: an edit exists only because a reviewer asked for it, and
it goes no further than what the asking comment and the manuscript's own
committed material support.

Authorship in the editing copy splits by whose comment is being answered, so
the Review pane can be filtered to one reviewer at a time:

    "Thomas Yuan - answers KME"   answers Kimberly Edwards, 6 November 2026
    "Thomas Yuan - answers VD"    answers Vijaykrishna Dhanasekaran

Not here, and why: her question about whether CHP declares on a percentage
increase rather than a level, and her "where is this published?", both turn on
a Hong Kong government press release she quoted. That URL could not be fetched
from this session, so nothing is cited to it and neither question is answered
in the text. An unverified source does not enter a document.
"""

EDITS = [

 # ---------------------------------------------------------------- Kimberly
 dict(id='KME-15', who='KME',
      source='Her comment on "β(t)·S(t)": "need to define all variables when you '
             'first introduce them".',
      evidence='Neither β nor S is defined anywhere in the manuscript: "transmission '
               'rate" and "susceptible fraction" each occur zero times. The definitions added '
               'are the standard SEIR ones already implied by the Methods.',
      old='since R(t) = β(t)·S(t)/γ, a lower γ inflates R(t)',
      new='since R(t) = β(t)·S(t)/γ, where β(t) is the time-varying '
          'transmission rate and S(t) the susceptible fraction, a lower γ inflates R(t)'),

 dict(id='KME-16', who='KME',
      source='Her comment on "stable seasons": "how are \'stable\' seasons defined?"',
      evidence='The comment already in this file answering VD’s point 2 states that the '
               'committed multi-restart results support three stable seasons, 2014/15, '
               '2018/19 and 2023 summer, at 5/5 detection with onset ranges of 7–20 '
               'days. The definition is taken from there, not invented.',
      old='showed onset date ranges of 7–20 days for stable seasons (3/6).',
      new='showed onset date ranges of 7–20 days for the three seasons in which all five '
          'restarts detected onset (2014/15, 2018/19 and 2023 summer).'),

 dict(id='KME-17', who='KME',
      source='Her comment on "12–17y and 6–11y": "keep abbreviations consistent".',
      evidence='One occurrence of "12–17y" against seven of "12–17 year" in the '
               'same manuscript.',
      old='for 12–17y and 6–11y admissions in',
      new='for 12–17 year and 6–11 year admissions in'),

 dict(id='KME-22', who='KME',
      source='Her comment on "drivers of within-pathogen variation remain unidentified": '
             '"confounders - not captured by the model, but not unidentified. Population '
             'immunity, and features specific to the virus such as transmissibility or '
             'pathogenesis of the circulating variant(s) also play a major role."',
      evidence='Her own wording, narrowed to what this design can and cannot separate. No '
               'claim is made about the size of either candidate.',
      old='and the drivers of within-pathogen variation remain unidentified.',
      new='and the drivers of within-pathogen variation are not identified by this design; '
          'population immunity and the transmissibility of the circulating subtypes are '
          'candidates it cannot separate.'),

 dict(id='KME-24', who='KME',
      source='Her comment on the admissions paragraph: "is this paragraph considering all '
             'hospitalilzations, or ILI-related hospitalizations?"',
      evidence='Materials and Methods already defines the series as "influenza-associated '
               'hospital admission rates per 10,000 population". The word is carried into '
               'Results so the paragraph answers her where she asked.',
      old='EpiEstim was applied to five age-stratified hospital admission signals',
      new='EpiEstim was applied to five age-stratified influenza-associated hospital '
          'admission signals'),

 dict(id='KME-27a', who='KME',
      source='Her comment on "specimen mix": "what does this mean? cocirculating viruses?"',
      evidence='Her reading is one possibility and the sentence does not settle it, so the '
               'phrase is spelled out as what the surveillance series actually varies in, '
               'which specimens are submitted for testing. Her alternative reading is not '
               'adopted, because nothing here establishes it.',
      old='as testing practice, specimen mix, or population immunity change',
      new='as testing practice, the mix of specimens submitted for testing, or population '
          'immunity change'),

 dict(id='KME-27b', who='KME',
      source='As KME-27a: the same phrase, second occurrence.',
      evidence='As KME-27a.',
      old='changes in testing behaviour and specimen mix that reduce measured positivity',
      new='changes in testing behaviour and in the mix of specimens submitted that reduce '
          'measured positivity'),

 dict(id='KME-10', who='KME',
      source='Her comment on "Multi": "if multiple age groups are tied, explicitly state '
             'which ones."',
      evidence='The comment already in this file names them from '
               'epiestim_admissions_results.csv: 2018/19, 6–11y and 12–17y both at '
               '2018-10-17; 2024/25, 0–5y and 6–11y both at 2024-09-04.',
      old='Multi = multiple age groups tied.',
      new='Multi = two age groups tied for the earliest onset (2018/19, 6–11 and '
          '12–17 years; 2024/25, 0–5 and 6–11 years).'),

 dict(id='KME-7a', who='KME',
      source='Her comment on "gamma": "clarify at first mention and keep '
             'nomenclature/abbreviations consistent throughout."',
      evidence='The symbol γ is used 26 times and the word "gamma" five times. Two of '
               'the five name the parameter and become the symbol; the three that name the '
               'Gamma distribution stay words, and one gains the capital the other already '
               'has.',
      old='across all gamma values tested',
      new='across all γ values tested'),

 dict(id='KME-7b', who='KME', source='As KME-7a.', evidence='As KME-7a.',
      old='at all three gamma values (1.16, 1.06, 1.05)',
      new='at all three γ values (1.16, 1.06, 1.05)'),

 dict(id='KME-7c', who='KME',
      source='As KME-7a, on the distribution rather than the parameter.',
      evidence='The same document writes "Gamma(0.001, 0.001)" and "gamma (1, 0.2)".',
      old='the rate parameter of the gamma (1, 0.2) prior',
      new='the rate parameter of the Gamma(1, 0.2) prior'),

 dict(id='KME-14a', who='KME',
      source='Her comment: "reference supplementary data file(s) and/or subsections of '
             'Methods without explicitly naming the analysis script in text."',
      evidence='Every filename below is reachable from the Code availability statement, so '
               'removing it from the running text loses nothing a reader can act on. Where a '
               'supporting item carries the same material, it is named instead.',
      old='(invariance check and full results at si_invariance_check.py and '
          'rsv_si_sensitivity.csv in the repository)',
      new='(invariance check and full results in the repository)'),

 dict(id='KME-14b', who='KME', source='As KME-14a.',
      evidence='S3 Table is the data dictionary, so it is named instead of the file.',
      old='A data dictionary for all 31 CHP Flu Express variables '
          '(data_dictionary_flu_express.csv) is provided as supplementary material, including',
      new='A data dictionary for all 31 CHP Flu Express variables is provided as S3 Table, '
          'including'),

 dict(id='KME-14c', who='KME', source='As KME-14a.', evidence='As KME-14a.',
      old='using a custom scraper (scrape_chp_respiratory.py, committed to the repository)',
      new='using a custom scraper committed to the repository'),

 dict(id='KME-14d', who='KME', source='As KME-14a.',
      evidence='S1 Table is that supplementary table, so the sentence names it once instead '
               'of naming it and its source file.',
      old='A supplementary table (S1 Table) with exact start and end dates, peak timing, '
          'dominant subtype, and classification for all 18 seasons is provided '
          '(supplementary_table_S1_seasons.csv).',
      new='S1 Table gives exact start and end dates, peak timing, dominant subtype, and '
          'classification for all 18 seasons.'),

 dict(id='KME-14e', who='KME', source='As KME-14a.', evidence='As KME-14a.',
      old='as single-wave (script: final_supplementary.py).',
      new='as single-wave (classification script in the repository).'),

 dict(id='KME-14f', who='KME', source='As KME-14a.', evidence='As KME-14a.',
      old='(script wilcoxon_admissions.py; saved output wilcoxon_admissions_results.csv)',
      new='(script and saved output in the repository)'),

 dict(id='KME-14g', who='KME', source='As KME-14a.', evidence='As KME-14a.',
      old='coincide numerically: simulation_study.py seeds each scenario separately',
      new='coincide numerically: the simulation script seeds each scenario separately'),

 dict(id='KME-14h', who='KME', source='As KME-14a.', evidence='As KME-14a.',
      old='Code is available at simulation_study.py in the repository (seeds fixed per '
          'scenario and replicate; 50 replicates per condition; output: '
          'simulation_study_results.csv).',
      new='Code is available in the repository, with seeds fixed per scenario and replicate '
          'and 50 replicates per condition.'),

 dict(id='KME-14i', who='KME', source='As KME-14a.', evidence='As KME-14a.',
      old='Full results at pinn_multi_restart_results.csv in the repository.',
      new='Full results are in the repository.'),

 # -------------------------------------------------------------------- Vijay
 dict(id='VD-146', who='VD',
      source='His comment on this sentence: "This shouldnt be here."',
      evidence='Acting on it rather than only replying, after two rounds in which it was '
               'carried. The sentence is also wrong by the manuscript’s own account: it '
               'says CHP does not publish the threshold value, while Results says "the 4.94% '
               'published by CHP". Deleting it removes the contradiction in the direction his '
               'comment points. Kimberly Edwards raised the same sentence independently and '
               'supplied a CHP press release that names 4.94% as a published baseline; that '
               'source could not be fetched from this session, so it is not cited and no '
               'positive claim replaces the deleted one. The derivation of the data-derived '
               'thresholds stays in Methods and Results, where it is already stated with its '
               'numbers. The Abstract’s "an analytical reconstruction" is his wording and '
               'is untouched: recommendation R3 proposes that change and he decides it.',
      old='CHP does not publish the exact threshold value or its derivation; the value of '
          '4.94% used here was reconstructed from the CHP Flu Express dataset (2014–2019 '
          'non-season weeks, defined as weeks with positivity below the series median; mean + '
          '1.96 standard deviations of the combined A and B positivity) and should be read as '
          'an analytical approximation of CHP practice rather than an official operational '
          'value. ',
      new=''),

 # ---- added 7 November, after the press release was fetched and read in session ----
 dict(id='KME-21', who='KME',
      source='Her comments "where is this published?" on the 4.94% and "I thought they used % '
             'increase?" on the declaration rule.',
      evidence='Fetched and read in this session: Centre for Health Protection of the '
               'Department of Health, press release of 2 July 2026, 19:15 HKT, headed "As Hong '
               'Kong enters influenza season, DH urges public to maintain good personal and '
               'environmental hygiene at all times". It reads "Both indicators showed a '
               'significant increase from the previous week and have exceeded the baseline '
               'levels" followed by "(4.94 per cent and 0.27 cases per 10 000 population '
               'respectively)". So 4.94% is a published baseline LEVEL that is exceeded, not a '
               'rate of increase: her second question is answered by the same sentence that '
               'answers her first. The sentence this replaces already said level-exceedance; '
               'what it lacked was the source.',
      old='declares influenza season onset when laboratory positivity exceeds a baseline '
          'threshold value.',
      new='declares influenza season onset when laboratory positivity exceeds a baseline level '
          'that it publishes and reports against in its weekly statements (4.94% positivity '
          'and 0.27 influenza admissions per 10,000 population; Department of Health press '
          'release, 2 July 2026, '
          'https://www.info.gov.hk/gia/general/202607/02/P2026070200749.htm).'),

 dict(id='KME-32', who='KME',
      source='Her comment on the CHP data description: "not here, but testing denominators are '
             'available from the CHP website".',
      evidence='The Methods claim that denominators "are not published in CHP Flu Express and '
               'are therefore not available for this analysis" is a non-existence claim resting '
               'on one surface. The first clause is about Flu Express and is supportable; the '
               '"therefore not available" generalises it to CHP as a whole, which her comment '
               'disputes and which nothing here establishes. The inference is removed and the '
               'surface is named, which is what Part I requires of any claim that something '
               'does not exist. Whether the statistics page she names publishes a weekly '
               'specimen count is NOT yet verified in this session: that URL could not be '
               'fetched, so no positive claim replaces the one withdrawn.',
      old='Note that weekly specimen denominators (total specimens tested) are not published in '
          'CHP Flu Express and are therefore not available for this analysis.',
      new='Note that weekly specimen denominators (total specimens tested) are not published in '
          'CHP Flu Express, the series used here, and were not used in this analysis.'),
]
