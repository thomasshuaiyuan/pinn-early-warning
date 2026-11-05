# RSV source verification — the five weeks named in Methods

**Run 5 November 2026.** Discharges the sentence that read *"manual verification against the CHP
website is pending"*.

The five weeks were fixed in the Methods before this check ran and were not chosen here. Each
was compared against the Centre for Health Protection's published table *Detection of other
respiratory viruses in respiratory specimens*, on the year page for that week, against
`chp_respiratory_cleaned.csv` in the repository.

## Result: 5 of 5 match exactly

| Week | Published dates | Specimens tested | RSV detections | RSV % | Source page |
|---|---|---|---|---|---|
| 2015-W21 | 17/05 – 23/05 | 2786 = 2786 | 91 = 91 | 3.27 = 3.27 | [CHP 2015](https://www.chp.gov.hk/en/statistics/data/10/641/642/3671.html) |
| 2015-W35 | 23/08 – 29/08 | 2759 = 2759 | 112 = 112 | 4.06 = 4.06 | [CHP 2015](https://www.chp.gov.hk/en/statistics/data/10/641/642/3671.html) |
| 2019-W44 | 27/10 – 02/11 | 4676 = 4676 | 60 = 60 | 1.28 = 1.28 | [CHP 2019](https://www.chp.gov.hk/en/statistics/data/10/641/642/6823.html) |
| 2019-W52 | 22/12 – 28/12 | 5366 = 5366 | 20 = 20 | 0.37 = 0.37 | [CHP 2019](https://www.chp.gov.hk/en/statistics/data/10/641/642/6823.html) |
| 2022-W18 | 24/04 – 30/04 | 363 = 363 | 0 = 0 | 0.00 = 0.00 | [CHP 2022](https://www.chp.gov.hk/en/statistics/data/10/641/642/6989.html) |

Left of each `=` is the published figure, right is the scraped series. Specimens tested, RSV
detections, RSV percentage positive and the week's date range all agree in all five weeks.

## How the source pages were established, and why that matters

The URLs were **not** taken on trust from `scrape_chp_respiratory.py`. The CHP index page
*Detection of pathogens from respiratory specimens* was retrieved first, and the year pages it
lists for 2015, 2019 and 2022 — `3671`, `6823` and `6989` — are identical to the ones the
scraper uses. **The scraper's URL mapping is therefore independently corroborated for those
three years**, which is a second result this check produced.

## Two things this does not establish

**It is a check on five weeks of 641, chosen at random and fixed in advance.** It says the
scraper transcribes the published tables faithfully where it was tested. It does not bound the
error rate across the series, and the Methods should not be read as claiming that.

**It says nothing about the comparability assumption in the same paragraph.** The manuscript
states that the specimen stream behind the RSV series is not the same stream as the influenza
positivity series, and that this is *"the key comparability assumption of the cross-pathogen
design"* which *"requires further evidence rather than assertion"*. That sentence stands
untouched and remains an open scientific item. **Discharging the transcription check does not
discharge it**, and a reader who conflated the two would take this record for more than it is.

## Column mapping, recorded because the published tables are awkward

The CHP tables put Adenovirus, RSV, hMPV and Rhinovirus/Enterovirus side by side as No./%
pairs, and on the retrieved pages the header row renders misaligned against the data. The RSV
pair was identified by arithmetic rather than by header position: 91/2786 = 3.27% and
112/2759 = 4.06% in 2015, which fixes the second pair as RSV and the first as Adenovirus. The
2022 row corroborates it from the other direction — the first pair reads 11 and 3.03%, and
`chp_respiratory_cleaned.csv` records exactly those as Adenovirus for that week.

**Sources:** [CHP, Detection of pathogens from respiratory specimens](https://www.chp.gov.hk/en/statistics/data/10/641/642/2274.html) · [2015](https://www.chp.gov.hk/en/statistics/data/10/641/642/3671.html) · [2019](https://www.chp.gov.hk/en/statistics/data/10/641/642/6823.html) · [2022](https://www.chp.gov.hk/en/statistics/data/10/641/642/6989.html)
