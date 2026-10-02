# ALTAIR — Academic Guide

## Course alignment

**Course:** Data Analysis Essentials  
**Course Code:** 2501AI06  
**Project:** Airline Data Analysis  
**Project type:** Own-choice project using an airline dataset

The syllabus permits an own-choice project with prior instructor permission. This project therefore applies the prescribed data-analysis skills to airline data rather than changing the dataset to the prescribed loan-prediction project.

## Course outcome mapping

| Course Outcome | How ALTAIR demonstrates it |
|---|---|
| CO1 — NumPy arrays | Numeric age arrays, array conversion, reshape example, mean and standard deviation calculations. |
| CO2 — Pandas data import | CSV loading with `pd.read_csv`, DataFrame inspection, filtering, sorting, grouping and aggregation. |
| CO3 — Matplotlib charts | Python-generated bar, pie, box, histogram, line, scatter and subplot figures in `outputs/visualizations/`. |
| CO4 — Web scraping | Not required for the core airline analysis. It is documented as an optional enhancement because the selected dataset already contains the fields needed for the main study. |
| CO5 — Preprocessing | Missing-value checks, invalid-age/date handling, duplicate checks, feature engineering, standardization example, label encoding and one-hot encoding example. |

## Ten-stage workflow

1. **Data Collection** — retain the selected airline CSV as the project source.
2. **Data Loading** — import the CSV into a Pandas DataFrame.
3. **Data Exploration** — inspect shape, columns, data types, missing values and duplicates.
4. **Data Cleaning** — validate age/date fields, clean text and remove duplicate records.
5. **Feature Engineering** — derive month, weekday, weekend/weekday, age group and approximate travel type.
6. **Exploratory Data Analysis** — use counts, grouped summaries, crosstabs and descriptive statistics.
7. **Data Visualization** — generate Matplotlib figures and prepare dashboard-ready summaries.
8. **Statistical Analysis** — calculate descriptive statistics and selected chi-square association tests.
9. **Interpretation** — convert observed distributions and test results into concise, non-causal insights.
10. **Reporting / Presentation** — export reproducible reports and present the interactive ALTAIR dashboard.

## Main Python evidence

The file `python/airline_analysis.py` contains the reproducible pipeline. Running it regenerates the cleaned dataset, dashboard JSON, summary CSVs, academic reports, preprocessing demonstration and Matplotlib figures.

## Dashboard evidence

The browser dashboard provides:

- Overview KPIs
- Passenger analysis
- Flight-status analysis
- Geographic analysis
- Time analysis
- Airport analysis
- Statistical analysis
- Data Explorer with search, filters, pagination and CRUD
- Insights
- Light/dark theme

The dashboard is static and can be hosted on GitHub Pages. Python runs before deployment to generate the data artifacts consumed by the website.

## Viva points

A concise explanation for a viva can follow this order:

**Problem → Dataset → Cleaning → Feature Engineering → EDA → Matplotlib → Statistics → Dashboard → Insights → Limitations**

Important limitation: `Domestic/International` is only an approximate indicator based on passenger nationality versus airport country. The source dataset does not provide a complete itinerary-level origin/destination field for this classification.
