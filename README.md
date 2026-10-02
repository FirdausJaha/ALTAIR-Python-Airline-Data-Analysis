# ALTAIR — Airline Data Analysis

ALTAIR is a student-friendly Airline Data Analysis project built around the Kaggle Airline Dataset. The project keeps the same interactive dashboard experience while making **Python the main analytical layer**.

## Project idea

The project analyzes passenger demographics, geographic distribution, airport activity, flight status, departure-date patterns, and categorical relationships. Python performs the data workflow and prepares the files consumed by the website.

## Analytical workflow

1. Data Collection
2. Data Loading
3. Data Exploration
4. Data Cleaning
5. Feature Engineering
6. Exploratory Data Analysis
7. Data Visualization preparation
8. Statistical Analysis
9. Data Interpretation / Insights
10. Reporting / Presentation of Findings

## Technology roles

### Python

Python is the core analysis layer. `python/airline_analysis.py` performs:

- CSV loading with Pandas
- Data inspection and profiling
- Missing-value and duplicate checks
- Age and date validation
- Data cleaning
- Feature engineering
- Frequency analysis and grouped analysis
- Descriptive statistics
- Crosstabulation
- Chi-square tests
- NumPy array and reshape examples
- Feature scaling / standardization example
- Label encoding and one-hot encoding examples
- Matplotlib bar, pie, box, histogram, line, scatter and subplot visualizations
- Insight generation
- Creation of dashboard-ready JSON
- Creation of the cleaned CSV used by Data Explorer
- Creation of additional academic report artifacts

### Web dashboard

HTML provides the dashboard structure, CSS provides the interface design, and JavaScript handles navigation, charts, filtering, Data Explorer interactions, theme switching, and local Add/Edit/Delete behavior.

The live GitHub Pages site does not require a Python server. Python runs during the analysis/build stage and exports `data/analysis.json` and `data/airline_cleaned.csv`.

## Folder structure

```text
ALTAIR-Python-Airline-Data-Analysis/
├── index.html
├── assets/
│   ├── altair-logo.png
│   ├── app.js
│   └── style.css
├── data/
│   ├── Airline Dataset Updated - v2.csv
│   ├── airline_cleaned.csv
│   └── analysis.json
├── python/
│   └── airline_analysis.py
├── outputs/
│   ├── analysis_report.json
│   ├── analysis_report.txt
│   ├── analysis_report.md
│   ├── data_profile.json
│   ├── project_manifest.json
│   └── summary CSV files
├── requirements.txt
├── ACADEMIC_GUIDE.md
├── PROJECT_INFO.txt
└── README.md
```

## Run the analysis

From the project root:

```bash
pip install -r requirements.txt
python python/airline_analysis.py
```

The script regenerates:

- `data/airline_cleaned.csv`
- `data/analysis.json`
- `outputs/data_profile.json`
- `outputs/analysis_report.json`
- `outputs/analysis_report.txt`
- `outputs/numpy_preprocessing_demo.json`
- `outputs/visualizations/*.png`

## Run the website

The dashboard is static and can be deployed directly with GitHub Pages. For local testing, use a simple local server so browser `fetch()` requests work correctly.

```bash
python -m http.server 8000
```

Then open the local server in a browser.

## Dashboard sections

- Overview
- Passengers
- Flights
- Geography
- Time Analysis
- Airports
- Statistics
- Data Explorer
- Insights

The Data Explorer supports search, filters, pagination, Add, Edit, Delete, Reset Changes, and downloading the current filtered view.

## Important analytical note

`Domestic/International` is an approximate classification created by comparing passenger `Nationality` with the airport `Country Name`. It is not a true itinerary-level domestic/international field because the source dataset does not provide a complete origin-destination itinerary for each passenger.

## Dataset

The project uses the Airline Dataset with passenger, airport, departure-date, and flight-status information. The raw CSV is retained in the `data/` folder so the Python workflow can be reproduced.

## GitHub language display

The repository includes a `.gitattributes` file that marks the dataset, generated analysis outputs, and logo as generated/data assets. This keeps GitHub's Languages panel focused on the actual source files instead of counting the large CSV and generated JSON artifacts as programming source. With the current source layout, Python is intentionally the largest source-language component.

## Academic alignment

The project is aligned to **Data Analysis Essentials (2501AI06)**. See `ACADEMIC_GUIDE.md` for the CO1–CO5 mapping, ten-stage workflow, viva points, and the reason web scraping is treated as an optional extension rather than forced into the core airline analysis.
