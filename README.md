# Global GDP Explorer

An interactive Streamlit dashboard for analysing World Bank GDP data across 217 countries and territories from 1960 to 2022.

---

## 📌 Project Overview

The World Bank publishes GDP (current US$) as a wide spreadsheet — one row per entity, one column per year. In that form it is difficult to analyse, and it carries a trap: the file mixes individual economies with 49 aggregate rows such as *World*, *European Union*, *High income* and *IDA total*. Analysed naively, those aggregates outrank every real country and cause global totals to be counted several times over.

This project reshapes that file into a tidy dataset, separates real economies from aggregates, recomputes growth from scratch, and presents the result as a fourteen-section analytical dashboard.

It was built to turn a raw statistical export into something that can actually be interrogated — where a recruiter, analyst or student can change a period or a focus year and watch every ranking, chart, map and metric recalculate consistently.

## 🎯 Project Objectives

- Track how world GDP has changed over time, and separate real growth from widening reporting coverage
- Rank economies by GDP, share, annual growth, CAGR, average growth and volatility
- Measure long-run growth and its variability at country level
- Quantify how concentrated global output is among the largest economies
- Compare countries against each other over any chosen period
- Make the underlying data quality visible rather than assumed
- Keep every calculation reproducible and every limitation stated

## ✨ Key Features

**Overview** — KPI band (world GDP, largest economy, world CAGR, median economy), world GDP trend, top-five chart, ranked economy cards, and executive insights generated from the current filters.

**Global Economy** — World GDP trend with linear or logarithmic axis, year-on-year growth bars, reporting coverage by year, GDP distribution (log-scale histogram and box plot), concentration analysis (cumulative share curve, donut breakdown, top 5 / 10 / 20 shares, HHI, Gini), top economies chart and GDP share over time.

**Growth Analysis** — CAGR and volatility leaderboards, an adjustable minimum-observations threshold, a growth-versus-volatility scatter with median quadrant lines, a countries × years growth heatmap, and a sortable growth table.

**World Map** — Choropleth across four metrics (GDP, GDP share, year-on-year growth, CAGR), with hover showing country, year, world rank, GDP, share, growth and CAGR. Aggregates are excluded and unmappable territories are reported explicitly.

**Rankings** — Six ranking metrics, ascending or descending, with a leaderboard chart, a GDP treemap and a full ranked table.

**Country Profiles** — GDP, world rank, global share, CAGR, average growth, volatility, peak GDP and peak year, plus country code, first and last reported year, observation count and missing years. Charts cover GDP history, annual growth against the period average, and share of world GDP.

**Country Comparison** — Up to ten countries in three views (absolute GDP, indexed to period start, share of world GDP), a growth comparison, a metric table and a normalised radar chart.

**Head to Head** — Two economies across ten metrics, with the higher value marked per metric, a GDP chart and a GDP ratio chart.

**Custom Analysis** — Compare any two endpoint years, with per-metric eligibility: CAGR and total growth require reported values at both endpoints, average growth requires at least one annual change, volatility requires at least two. Countries that fail a rule show a blank cell and an explicit status.

**Data Explorer** — Search by country name or ISO-3 code, filter by year range, entity type (countries / aggregates / everything) and reported-only or including missing years. The download returns exactly the rows displayed.

**Data Quality** — Countries and aggregates assessed separately: rows, entities, missing GDP, duplicate keys, year range, complete series, internal gaps, negative and zero values, a coverage-by-year chart, integrity checks and a per-entity coverage table.

**Download Center** — Nine CSV exports covering the full dataset, countries only, aggregates only, the current snapshot, the current ranking, growth analysis, country summary, coverage report and the current period's explorer data.

**Methodology** and **About** — Full documentation of every formula, the classification approach, the data pipeline and the project's limitations.

**Presentation mode** hides the sidebar, moves navigation to the top and enlarges figures for screen sharing.

## 📊 Dataset

| Attribute | Value |
|---|---|
| Source | World Bank, World Development Indicators |
| Indicator | GDP (current US$) |
| Indicator code | `NY.GDP.MKTP.CD` |
| Primary file | `gdp_data.csv` (wide format, one column per year) |
| Fallback file | `gdp_data_long.csv` (long format) |
| Years covered | 1960–2022 (63 years) |
| Total entities | 266 |
| Countries and territories | 217 |
| World Bank aggregates | 49 |
| Country-year records | 16,758 |
| Records with a GDP value | 13,200 |
| Missing values | 3,558 (21.23%) |
| Duplicate country-year keys | 0 |
| Negative or zero GDP values | 0 |

`gdp_data.csv` is the source of truth because it carries country names. `gdp_data_long.csv` is used only if the wide file is unavailable.

## 🔧 Data Preparation & Methodology

**Loading.** The app searches for the CSV files beside `streamlit_app.py`, then in `./data` and `../data`. Results are cached with `@st.cache_data`, keyed on each file's size and modification time, so editing a CSV refreshes the dashboard automatically.

**Reshaping.** Generated empty columns are dropped, year columns are melted into one row per country-year, types are coerced, and duplicate country-year keys are removed.

**Entity classification.** Aggregates are identified from their ISO-3 codes, backed by a whole-word name check. Real economies keep every country-level view to themselves; aggregates remain available in the Data Explorer and Download Center.

**Missing values.** Nothing is filled, interpolated or estimated. A missing year stays missing everywhere it appears.

**Year-on-year growth.** Recomputed inside the app rather than trusted from any pre-calculated column, and only between consecutive observed years.

**CAGR.** `(last ÷ first)^(1 ÷ years) − 1`. On the growth pages it uses the first and last observed years inside the selected period; in Custom Analysis it uses the two chosen endpoint years and stays blank unless both were reported.

**Global GDP.** The sum of reporting countries for a given year, aggregates excluded.

**GDP share.** A country's GDP divided by that same world total.

**Average growth and volatility.** The mean and the standard deviation (in percentage points) of annual changes inside the period. Average growth needs at least one change; volatility needs at least two.

**Concentration.** Cumulative share, a Herfindahl–Hirschman index computed on percentage shares, and a Gini coefficient across economies.

## 🧭 Important Data Decisions

**Aggregates are excluded from country-level analysis.** *World* alone would top every ranking, and summing rows that already contain each other would count the same output many times. Aggregates are separated, not deleted — they stay browsable and downloadable.

**Growth is only calculated between consecutive years.** Fifteen series in this dataset contain internal gaps. Computing growth after simply dropping missing rows produces 17 values that look like one-year changes but actually span years or decades — Afghanistan's series jumps from 1980 to 2002, and Switzerland's skips 1979. Those cells are left blank instead.

**Each metric carries its own data requirement.** A single blanket filter would either hide valid data or publish a CAGR built from two arbitrary years. Custom Analysis therefore tests eligibility per metric and reports why a value is absent.

**No `pycountry` dependency.** ISO-3 codes plus a whole-word name check are sufficient to separate the two populations, keeping the deployment to four libraries.

**World totals are stated as what they are.** The 2022 total covers reporting countries only and is labelled as such, rather than being presented as the World Bank's own world figure.

## 🗂 Dashboard Structure

1. Overview
2. Global Economy
3. Growth Analysis
4. World Map
5. Rankings
6. Country Profiles
7. Country Comparison
8. Head to Head
9. Custom Analysis
10. Data Explorer
11. Data Quality
12. Download Center
13. Methodology
14. About

## 🎛 Interactive Controls

| Control | Effect |
|---|---|
| **Analysis period** | The window every period metric is calculated inside — CAGR, average growth, volatility, trends, heatmap and coverage |
| **Focus year** | Drives the KPI band, rankings, the map, GDP distribution, shares, concentration and executive insights. Constrained to the analysis period |
| **Countries to compare** | Feeds Country Comparison, the Head to Head defaults, the growth heatmap and the Custom Analysis default selection (up to 10) |
| **Leaderboard size** | Controls how many economies appear in rankings, ranked cards, top-economy charts and the ranking export (5–30) |
| **Presentation mode** | Hides the sidebar, moves navigation to the top and enlarges figures |
| **Reset all filters** | Returns every control to its default |

Page-level controls are also available where relevant: chart scale, map metric, ranking metric and order, minimum observations, custom endpoint years, explorer filters and data-quality scope.

## 🛠 Technology Stack

| Purpose | Library |
|---|---|
| Application framework | Streamlit `>=1.40` |
| Data manipulation | pandas `>=2.0` |
| Numerical operations | numpy `>=1.24` |
| Visualisation | Plotly `>=5.18` (Graph Objects and Express) |

Four dependencies, no more. The exploratory notebook additionally uses matplotlib, which the application does not require.

## 📁 Project Structure

```
.
├── streamlit_app.py                    # the dashboard
├── requirements.txt                    # four dependencies
├── README.md
├── gdp_data.csv                        # World Bank wide export (primary source)
├── gdp_data_long.csv                   # long-format export (fallback)
└── Global_GDP_Explorer_Analysis.ipynb  # exploratory analysis notebook
```

## ⚙️ Installation

Place the project files in one folder, then:

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## ▶️ Run Locally

```bash
streamlit run streamlit_app.py
```

The dashboard opens at `http://localhost:8501`.

## 🚀 Deployment

The project runs on Streamlit Community Cloud without modification: it has a `requirements.txt`, uses only relative paths resolved from the script location, needs no secrets or environment variables, and requires no system packages.

1. Push `streamlit_app.py`, `requirements.txt` and both CSV files to a public GitHub repository
2. Create a new app at [share.streamlit.io](https://share.streamlit.io) pointing at that repository
3. Set the main file path to `streamlit_app.py`
4. Deploy

## 📈 Results

Figures below are produced from the bundled dataset.

**Dataset findings**

- Overall data coverage is **78.77%** — 13,200 of 16,758 country-year cells carry a GDP value
- **Four entities report no GDP at all**: Gibraltar, Korea (Dem. People's Rep.), British Virgin Islands and *Not classified*
- **Fifteen series contain internal gaps**, which is what makes consecutive-year growth necessary
- Reporting widens sharply over time: **96 countries reported GDP in 1960**, against **195 in 2022**

**Analytical findings**

- Reporting countries totalled **$100.07 trillion** in 2022. The World Bank's own `WLD` aggregate is $101.33 trillion; the difference is output the World Bank estimates for non-reporting economies, which this project does not
- Global output is highly concentrated: the largest economy holds **25.4%** of the 2022 total, the top five hold **55.1%**, the top ten **67.4%** and the top twenty **80.7%**. **Four countries** account for the first half of world GDP
- The Gini coefficient across economies is **0.871** and the HHI is **1,072**
- Measured between the 1960 and 2022 endpoints, **Botswana recorded the highest CAGR at 11.06%**, followed by Singapore at 11.05% and Korea, Rep. at 10.24%. Only **93 of 217 countries** reported GDP in both endpoint years, so the remainder are excluded from that comparison rather than approximated

## ⚠️ Limitations

- GDP is measured in **current US dollars**, unadjusted for inflation or purchasing power, so growth partly reflects prices and exchange-rate movement
- **21.23% of observations are missing**, and coverage widens over time — part of the apparent rise in world GDP before the 1990s reflects more countries reporting rather than more output
- **GDP does not measure welfare, quality of life or distribution** within a country
- The analysis describes trends and relationships; it does **not establish causation**
- Countries that dissolved or formed mid-series carry broken histories, so a long-run CAGR for them spans two different political entities
- World totals here cover reporting countries only and differ from the World Bank's published world aggregate
- A few territories have no standard map geometry and cannot be shaded, though they remain in every table and ranking
- Country codes are used as stable identifiers; country names are retained for presentation only

## 🔭 Future Improvements

These are ideas for future versions, not current features.

- GDP per capita and constant-price series, so real growth can be separated from inflation and exchange-rate effects
- Regional groupings as an optional analysis layer, kept distinct from country rankings
- Upload support for other World Bank indicator exports
- PNG or PDF export of individual charts
- An automated test suite in the repository

## 👤 Author
<div align="center">
  
**Noura Maher Elamin**

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Profile-0A66C2?style=for-the-badge\&logo=linkedin\&logoColor=white)](https://www.linkedin.com/in/nouramaherelamin/)
[![GitHub](https://img.shields.io/badge/GitHub-Profile-181717?style=for-the-badge\&logo=github\&logoColor=white)](https://github.com/nouramaherelamin)

</div>

## 📚 Data Source

World Bank — World Development Indicators
GDP (current US$), indicator code `NY.GDP.MKTP.CD`

## 📄 License

© 2026 Noura Maher Elamin · Global GDP Explorer

All rights reserved.
