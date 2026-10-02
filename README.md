# ALTAIR – Airline Data Analysis

ALTAIR is a student project for analysing an airline dataset and presenting the results through an interactive web dashboard.

The project follows a complete data-analysis workflow: collecting/loading the dataset, exploring the data, cleaning and preparing records, creating useful features, performing exploratory and statistical analysis, preparing visualizations, and presenting the findings through the ALTAIR dashboard.

## Live Dashboard

**Live project:**  
https://firdausjaha.github.io/ALTAIR-Python-Airline-Data-Analysis/

## Project Overview

The project studies passenger and flight-related information such as:

- Passenger age and gender
- Nationality and country distribution
- Departure airports
- Arrival airports
- Continents
- Flight status
- Departure dates and time-based patterns
- Age groups and other derived features

The project is designed to demonstrate practical data-analysis concepts using a real-world airline dataset and a browser-based dashboard.

## Objectives

1. Load and inspect airline data.
2. Understand the structure, types, missing values, and duplicate records.
3. Clean and prepare the dataset for analysis.
4. Create additional analytical features from existing fields.
5. Perform exploratory data analysis (EDA).
6. Apply descriptive and basic statistical analysis.
7. Create different types of data visualizations.
8. Generate processed datasets and analytical outputs.
9. Present the results through an interactive dashboard.
10. Provide a Data Explorer for searching, filtering, editing, adding, deleting, and exporting records.

## Dataset

The project uses the **Airline Dataset** available through Kaggle:

https://www.kaggle.com/datasets/iamsouravbanerjee/airline-dataset

The working dataset contains passenger, airport, geographic, date, and flight-status information.

The original dataset includes fields such as:

- Passenger ID
- First Name
- Last Name
- Gender
- Age
- Nationality
- Airport Name
- Airport Country Code
- Country Name
- Airport Continent
- Continents
- Departure Date
- Arrival Airport
- Pilot Name
- Flight Status

For analysis, the data is cleaned and additional features are created where useful.

## Analytical Workflow

The project follows these stages:

1. **Data Collection** – Obtain the airline dataset.
2. **Data Loading** – Load the CSV data for analysis.
3. **Data Exploration** – Inspect dimensions, columns, data types, descriptive statistics, missing values, and duplicates.
4. **Data Cleaning** – Handle invalid values, missing data, duplicates, and unnecessary fields.
5. **Feature Engineering** – Create analytical fields such as departure year/month/day, day of week, weekend/weekday, and age group.
6. **Exploratory Data Analysis** – Study distributions, frequencies, relationships, and grouped summaries.
7. **Data Visualization** – Prepare charts for passenger, flight, geographic, airport, and time-based analysis.
8. **Statistical Analysis** – Use descriptive statistics, cross-tabulation, and selected statistical tests.
9. **Data Interpretation** – Identify meaningful patterns from the analysis.
10. **Reporting and Presentation** – Present processed data, visualizations, findings, and the interactive dashboard.

## Analysis Areas

### Passenger Analysis

The dashboard examines:

- Gender distribution
- Age distribution
- Age groups
- Average age
- Nationality distribution

### Flight Analysis

The project examines:

- Flight-status distribution
- Flight-status relationships with selected passenger and geographic attributes
- Summary counts and percentages

### Geographic Analysis

The project studies:

- Country distribution
- Continent distribution
- Nationalities
- Geographic patterns in the dataset

### Time Analysis

The project derives and analyses:

- Departure year
- Departure month
- Month name
- Day of month
- Day of week
- Weekend/weekday patterns

### Airport Analysis

The dashboard provides:

- Departure airport frequency
- Arrival airport frequency
- Airport-level summaries

### Statistical Analysis

The project includes:

- Descriptive statistics
- Frequency tables
- Grouped summaries
- Cross-tabulation
- Chi-square analysis where applicable
- Numerical preprocessing demonstrations

## Data Preprocessing

The analysis includes practical preprocessing steps such as:

- Data type inspection
- Missing-value checks
- Duplicate checks
- Invalid age handling
- Date conversion
- Feature creation
- Categorical encoding examples
- One-hot encoding
- Standardization/scaling examples
- Preparation of cleaned analytical data

Preprocessing is applied where appropriate to the airline-analysis problem rather than forcing techniques that are not useful for the dataset.

## Technologies Used

### Analysis

- Python
- NumPy
- Pandas
- Matplotlib

### Dashboard

- HTML
- CSS
- JavaScript
- Chart.js
- Papa Parse

### Deployment

- GitHub
- GitHub Pages

## Dashboard Features

The ALTAIR dashboard contains:

- **Overview** – Key project and dataset metrics
- **Passengers** – Passenger demographic analysis
- **Flights** – Flight-status analysis
- **Geography** – Geographic analysis
- **Time Analysis** – Date and time-based patterns
- **Airports** – Airport-level analysis
- **Statistics** – Statistical summaries and analysis
- **Data Explorer** – Interactive record-level exploration
- **Insights** – Key findings from the analysis

### Data Explorer

The Data Explorer provides:

- Field-specific search
- Gender filter
- Continent filter
- Flight-status filter
- Age-group filter
- Pagination
- Add record
- Edit record
- Delete record
- Reset changes
- Download current filtered data

Search is intentionally focused on useful fields instead of matching every column indiscriminately. This makes searches more predictable and reduces unrelated matches.

Changes made through the Data Explorer are maintained in the browser using local storage and are reflected in the dashboard analysis during the current session.

## Visualizations

The Python analysis produces examples of:

- Bar charts
- Pie charts
- Box plots
- Histograms
- Line charts
- Scatter plots
- Combined subplot visualizations

The generated visualizations are stored in:

```text
outputs/visualizations/
```

## Project Structure

```text
ALTAIR-Python-Airline-Data-Analysis/
│
├── index.html
│
├── assets/
│   ├── altair-logo.png
│   ├── app.js
│   └── style.css
│
├── data/
│   ├── airline_cleaned.csv
│   └── analysis.json
│
├── outputs/
│   ├── airport_summary.csv
│   ├── analysis_report.json
│   ├── analysis_report.md
│   ├── analysis_report.txt
│   ├── continent_summary.csv
│   ├── data_profile.json
│   ├── gender_age_summary.csv
│   ├── monthly_summary.csv
│   ├── numpy_preprocessing_demo.json
│   ├── project_manifest.json
│   ├── status_summary.csv
│   └── visualizations/
│       ├── 01_flight_status_bar.png
│       ├── 02_gender_pie.png
│       ├── 03_age_box.png
│       ├── 04_age_histogram.png
│       ├── 05_monthly_line.png
│       ├── 06_age_scatter.png
│       └── 07_summary_subplots.png
│
├── python/
│   └── airline_analysis.py
│
├── ACADEMIC_GUIDE.md
├── PROJECT_INFO.txt
├── README.md
├── requirements.txt
├── .gitignore
└── .gitattributes
```

## Running the Analysis

If Python is available locally:

```bash
pip install -r requirements.txt
```

Then run:

```bash
python python/airline_analysis.py
```

The script reads the project dataset, performs the analysis workflow, and generates processed outputs and visualization files.

## Running the Dashboard

The dashboard is a static web application and can be deployed using GitHub Pages.

For local testing, serve the project directory through a local HTTP server rather than opening `index.html` directly. This allows the browser to load the CSV and JSON files correctly.

The deployed dashboard is available at:

https://firdausjaha.github.io/ALTAIR-Python-Airline-Data-Analysis/

## Academic Relevance

This project is designed for the **Data Analysis Essentials** course:

**Course Code: 2501AI06**

The project demonstrates practical use of:

- NumPy arrays and operations
- Pandas DataFrame operations
- CSV data handling
- Data cleaning and preprocessing
- Grouping and aggregation
- Exploratory data analysis
- Matplotlib visualizations
- Statistical analysis
- Web-based presentation of analytical results

The project also includes an academic guide containing the project's workflow, learning alignment, and explanation points useful for project presentation and viva preparation.

## Web Scraping

Web scraping is part of the broader course syllabus. It is not artificially included in the main airline-analysis workflow because the selected dataset and dashboard do not require scraped data for their core analysis.

A suitable future extension would be to collect supplementary airport information from an appropriate public source and combine it with the existing dataset.

## Limitations

- The dataset represents a particular airline/passenger sample and should not automatically be interpreted as a complete representation of global air travel.
- Some geographic fields may contain inconsistent naming conventions.
- Domestic/international classification, if derived from nationality and country information, is only an approximation and should not be treated as an actual ticket-level route classification.
- The dashboard is intended for educational analysis and visualization rather than operational airline decision-making.

## Future Enhancements

Possible extensions include:

- Additional external data sources
- Weather or airport-information integration
- More advanced statistical testing
- Interactive date-range controls
- Additional geographic maps
- Automated data refresh
- More advanced predictive analysis
- Expanded web-scraping integration

## Project Documentation

Additional academic information is available in:

```text
ACADEMIC_GUIDE.md
```

Project information is also available in:

```text
PROJECT_INFO.txt
```

## Author

**Firdaus Jaha**

Student Project – Data Analysis Essentials

## Acknowledgement

The project uses the publicly available Airline Dataset referenced above for educational analysis and visualization purposes.

---

**ALTAIR – Airline Data Analysis**
