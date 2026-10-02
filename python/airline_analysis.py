"""
ALTAIR — Airline Data Analysis Engine
======================================

This module is the analytical core of the ALTAIR Airline Data Analysis
project.  The website is intentionally kept as the presentation layer: the
actual data workflow is performed here with Python and Pandas, and the final
results are exported as a cleaned CSV file and a chart-ready JSON file.

The implementation follows the ten-stage workflow used for the lab project:

1. Data Collection
2. Data Loading
3. Data Exploration
4. Data Cleaning
5. Feature Engineering
6. Exploratory Data Analysis (EDA)
7. Data Visualization preparation
8. Statistical Analysis
9. Data Interpretation / Insights
10. Reporting / Presentation of Findings

The script can be executed from the project root:

    pip install -r requirements.txt
    python python/airline_analysis.py

The generated files are consumed by the static GitHub Pages dashboard.
No server is required for the dashboard itself.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
import argparse
import json
import math
import re
import sys

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import chi2_contingency


# ---------------------------------------------------------------------------
# Project paths and constants
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "outputs"

INPUT_CSV = DATA_DIR / "Airline Dataset Updated - v2.csv"
CLEANED_CSV = DATA_DIR / "airline_cleaned.csv"
ANALYSIS_JSON = DATA_DIR / "analysis.json"
PROFILE_JSON = OUTPUT_DIR / "data_profile.json"
REPORT_JSON = OUTPUT_DIR / "analysis_report.json"

MONTH_ORDER = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]
DAY_ORDER = [
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
]
STATUS_ORDER = ["Cancelled", "Delayed", "On Time"]
AGE_GROUP_ORDER = ["Child", "Teenager", "Young Adult", "Adult", "Senior"]
AGE_GROUP_LABELS = {
    "Child": "Child (1–12)",
    "Teenager": "Teenager (13–19)",
    "Young Adult": "Young Adult (20–29)",
    "Adult": "Adult (30–59)",
    "Senior": "Senior (60–100)",
}
CONTINENT_ORDER = [
    "Africa", "Asia", "Europe", "North America", "Oceania", "South America"
]
TRAVEL_ORDER = ["Domestic", "International"]
AGE_HISTOGRAM_ORDER = [
    "1–9", "9–18", "18–27", "27–36", "36–45",
    "45–54", "54–63", "63–72", "72–81", "81–90",
]

RAW_COLUMNS = [
    "Passenger ID", "First Name", "Last Name", "Gender", "Age",
    "Nationality", "Airport Name", "Airport Country Code", "Country Name",
    "Airport Continent", "Continents", "Departure Date", "Arrival Airport",
    "Pilot Name", "Flight Status",
]

REMOVED_COLUMNS = [
    "Passenger ID",
    "First Name",
    "Last Name",
    "Pilot Name",
    "Airport Continent",
    "Airport Country Code",
]

REQUIRED_COLUMNS = [
    "Gender", "Age", "Nationality", "Airport Name", "Country Name",
    "Continents", "Departure Date", "Arrival Airport", "Flight Status",
]


@dataclass
class DataQualitySummary:
    """Compact data-quality information retained for the final report."""

    raw_rows: int
    raw_columns: int
    duplicate_rows: int
    missing_values_before_cleaning: int
    missing_values_after_cleaning: int
    invalid_age_values: int
    invalid_dates: int
    rows_after_cleaning: int
    columns_after_cleaning: int


@dataclass
class AnalysisSummary:
    """Dashboard-level descriptive statistics."""

    total_records: int
    average_age: float
    median_age: float
    minimum_age: int
    maximum_age: int
    std_age: float
    nationalities: int
    airports: int
    arrival_airports: int
    continents: int
    years: int
    statuses: int
    duplicate_records_removed: int
    missing_values_total: int


# ---------------------------------------------------------------------------
# General-purpose conversion and JSON helpers
# ---------------------------------------------------------------------------


def json_safe(value: Any) -> Any:
    """Convert Pandas/NumPy values into JSON-safe Python values.

    Pandas often returns NumPy scalar types such as ``np.int64`` and
    ``np.float64``.  They are perfectly valid analytical values but are not
    always serializable by the standard JSON encoder.  This helper keeps the
    exported file portable and easy to consume from JavaScript.
    """

    if value is None:
        return None
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        if not np.isfinite(value):
            return None
        return float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, (pd.Timestamp,)):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, Mapping):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [json_safe(v) for v in value]
    return value


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    """Write a formatted UTF-8 JSON artifact."""

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(json_safe(payload), handle, ensure_ascii=False, indent=2)


def clean_text(series: pd.Series) -> pd.Series:
    """Normalize a text column without changing its semantic values."""

    return series.astype("string").str.strip()


def series_counts(
    series: pd.Series,
    *,
    order: Sequence[str] | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """Return frequency counts in the structure expected by Chart.js."""

    values = series.dropna().astype(str).str.strip()
    counts = values[values.ne("")].value_counts()

    if order is not None:
        ordered = counts.reindex(order).fillna(0)
        items = [{"label": label, "value": int(value)} for label, value in ordered.items() if value]
    else:
        items = [
            {"label": str(label), "value": int(value)}
            for label, value in counts.items()
        ]

    return items[:limit] if limit else items


def mean_round(series: pd.Series, digits: int = 2) -> float:
    """Return a rounded mean with a stable Python float result."""

    value = pd.to_numeric(series, errors="coerce").mean()
    return round(float(value), digits) if pd.notna(value) else 0.0


def median_round(series: pd.Series, digits: int = 2) -> float:
    """Return a rounded median with a stable Python float result."""

    value = pd.to_numeric(series, errors="coerce").median()
    return round(float(value), digits) if pd.notna(value) else 0.0


def std_round(series: pd.Series, digits: int = 2) -> float:
    """Return sample standard deviation in a dashboard-safe form."""

    value = pd.to_numeric(series, errors="coerce").std()
    return round(float(value), digits) if pd.notna(value) else 0.0


def top_frequency(series: pd.Series) -> tuple[str, int]:
    """Return the most frequent non-empty value and its count."""

    counts = series_counts(series)
    if not counts:
        return "No data", 0
    return str(counts[0]["label"]), int(counts[0]["value"])


# ---------------------------------------------------------------------------
# Stage 1 — Data Collection
# ---------------------------------------------------------------------------


def verify_input_dataset(path: Path = INPUT_CSV) -> Path:
    """Verify that the source CSV exists before analysis starts."""

    if not path.exists():
        raise FileNotFoundError(
            f"Input dataset was not found: {path}\n"
            "Place the airline CSV in the project's data folder."
        )
    if path.stat().st_size == 0:
        raise ValueError(f"Input dataset is empty: {path}")
    return path


def describe_collection_source(path: Path) -> dict[str, Any]:
    """Describe the local dataset used for reproducible analysis."""

    return {
        "source_type": "CSV dataset",
        "source_file": path.name,
        "source_location": "data/",
        "file_size_bytes": path.stat().st_size,
        "purpose": "Airline passenger and flight-status analysis",
        "note": "The dashboard uses the processed outputs generated by this script.",
    }


# ---------------------------------------------------------------------------
# Stage 2 — Data Loading
# ---------------------------------------------------------------------------


def load_dataset(path: Path = INPUT_CSV) -> pd.DataFrame:
    """Load the source CSV using Pandas."""

    verify_input_dataset(path)
    frame = pd.read_csv(path)

    # Keep the loading stage explicit: it is useful during a lab demonstration
    # because the student can show that the project begins with a DataFrame.
    if frame.empty:
        raise ValueError("The loaded dataset contains no rows.")

    return frame


def validate_required_columns(df: pd.DataFrame) -> None:
    """Check the expected airline-dataset fields."""

    missing = [column for column in RAW_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"Dataset is missing expected columns: {missing}")


def dataframe_overview(df: pd.DataFrame) -> dict[str, Any]:
    """Collect the same basic exploration information used in the lab."""

    object_columns = df.select_dtypes(include=["object", "string"]).columns.tolist()

    return {
        "shape": {"rows": int(df.shape[0]), "columns": int(df.shape[1])},
        "columns": [str(column) for column in df.columns],
        "dtypes": {str(column): str(dtype) for column, dtype in df.dtypes.items()},
        "numeric_summary": json_safe(df.describe(include=[np.number]).round(2).to_dict()),
        "categorical_columns": object_columns,
        "categorical_summary": json_safe(
            df[object_columns].describe().to_dict() if object_columns else {}
        ),
        "missing_values": {
            str(column): int(value)
            for column, value in df.isna().sum().items()
        },
        "duplicate_rows": int(df.duplicated().sum()),
    }


# ---------------------------------------------------------------------------
# Stage 3 — Data Exploration
# ---------------------------------------------------------------------------


def exploration_report(df: pd.DataFrame) -> dict[str, Any]:
    """Create a student-friendly exploration report before cleaning."""

    report = dataframe_overview(df)
    report["first_five_rows"] = json_safe(df.head(5).to_dict(orient="records"))
    report["last_five_rows"] = json_safe(df.tail(5).to_dict(orient="records"))

    unique_counts = {}
    for column in df.columns:
        unique_counts[str(column)] = int(df[column].nunique(dropna=True))
    report["unique_value_counts"] = unique_counts

    return report


# ---------------------------------------------------------------------------
# Stage 4 — Data Cleaning
# ---------------------------------------------------------------------------


def parse_departure_dates(series: pd.Series) -> pd.Series:
    """Parse common date representations used in the source dataset."""

    text = clean_text(series)
    parsed = pd.to_datetime(text, format="%m/%d/%Y", errors="coerce")
    missing = parsed.isna()

    if missing.any():
        parsed_alt = pd.to_datetime(text[missing], errors="coerce")
        parsed.loc[missing] = parsed_alt

    return parsed


def clean_age_values(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Validate ages and replace only invalid age cells.

    The original classroom notebook used a whole-row assignment for invalid
    ages.  That approach can accidentally blank every column in an affected
    record.  This implementation changes only the Age field and therefore
    preserves the rest of the passenger record.
    """

    frame = df.copy()
    age = pd.to_numeric(frame["Age"], errors="coerce")
    invalid_mask = age.notna() & ~age.between(1, 100)
    invalid_count = int(invalid_mask.sum())

    age.loc[invalid_mask] = np.nan
    if age.isna().any():
        age = age.fillna(age.median())

    frame["Age"] = age.round().astype("Int64")
    return frame, invalid_count


def clean_text_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Trim and standardize the categorical fields used by the analysis."""

    frame = df.copy()
    for column in [
        "Gender", "Nationality", "Airport Name", "Country Name",
        "Continents", "Arrival Airport", "Flight Status",
    ]:
        if column in frame.columns:
            frame[column] = clean_text(frame[column])

    return frame


def remove_duplicate_records(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Remove exact duplicate records and return the removed-row count."""

    before = len(df)
    frame = df.drop_duplicates().reset_index(drop=True)
    return frame, int(before - len(frame))


def clean_dataset(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Execute the complete cleaning stage."""

    frame = df.copy()
    missing_before = int(frame.isna().sum().sum())
    duplicate_count = int(frame.duplicated().sum())

    frame, removed_duplicates = remove_duplicate_records(frame)
    frame, invalid_age_count = clean_age_values(frame)
    frame = clean_text_columns(frame)

    parsed_dates = parse_departure_dates(frame["Departure Date"])
    invalid_date_count = int(parsed_dates.isna().sum())
    frame["Departure Date"] = parsed_dates

    # The following fields are identifiers or redundant fields.  They are not
    # required for passenger, flight, geographic, time, or statistical analysis.
    frame = frame.drop(columns=REMOVED_COLUMNS, errors="ignore")

    # Keep records with usable core analytical fields.  Missing categorical
    # values are retained as empty strings so the dashboard can still inspect
    # the record rather than silently losing a row.
    for column in REQUIRED_COLUMNS:
        if column not in frame.columns:
            frame[column] = ""
    for column in REQUIRED_COLUMNS:
        if frame[column].dtype.name == "string":
            frame[column] = frame[column].fillna("")
        elif frame[column].dtype == object:
            frame[column] = frame[column].fillna("")

    missing_after = int(frame.isna().sum().sum())

    quality = {
        "raw_rows": int(len(df)),
        "raw_columns": int(df.shape[1]),
        "duplicate_rows_detected": duplicate_count,
        "duplicate_rows_removed": removed_duplicates,
        "missing_values_before_cleaning": missing_before,
        "missing_values_after_cleaning": missing_after,
        "invalid_age_values": invalid_age_count,
        "invalid_dates": invalid_date_count,
        "removed_columns": REMOVED_COLUMNS,
        "rows_after_cleaning": int(len(frame)),
        "columns_after_cleaning": int(frame.shape[1]),
    }

    return frame, quality


# ---------------------------------------------------------------------------
# Stage 5 — Feature Engineering
# ---------------------------------------------------------------------------


def age_group_from_value(age: Any) -> str:
    """Map a numeric age to the project's five age groups."""

    try:
        value = float(age)
    except (TypeError, ValueError):
        return ""

    if 1 <= value <= 12:
        return "Child"
    if value <= 19:
        return "Teenager"
    if value <= 29:
        return "Young Adult"
    if value <= 59:
        return "Adult"
    if value <= 100:
        return "Senior"
    return ""


def age_histogram_label(age: Any) -> str:
    """Create the ten age intervals displayed by the dashboard."""

    try:
        value = float(age)
    except (TypeError, ValueError):
        return ""

    boundaries = [9, 18, 27, 36, 45, 54, 63, 72, 81, 90]
    lower = 1
    for upper in boundaries:
        if value <= upper:
            return f"{lower}–{upper}"
        lower = upper
    return ""


def classify_travel(nationality: Any, country: Any) -> str:
    """Create the project's approximate domestic/international indicator."""

    left = str(nationality or "").strip().casefold()
    right = str(country or "").strip().casefold()
    if not left or not right:
        return ""
    return "Domestic" if left == right else "International"


def feature_engineering(df: pd.DataFrame) -> pd.DataFrame:
    """Create reusable analytical variables from the cleaned dataset."""

    frame = df.copy()
    date = pd.to_datetime(frame["Departure Date"], errors="coerce")

    frame["Departure Year"] = date.dt.year.astype("Int64")
    frame["Departure Month"] = date.dt.month.astype("Int64")
    frame["Departure Month Name"] = date.dt.month_name()
    frame["Departure Day"] = date.dt.day.astype("Int64")
    frame["Day of Week"] = date.dt.day_name()
    frame["Weekend/Weekday"] = np.where(
        date.dt.dayofweek >= 5,
        "Weekend",
        "Weekday",
    )
    frame["Age Group"] = frame["Age"].apply(age_group_from_value)
    frame["Domestic/International"] = [
        classify_travel(nationality, country)
        for nationality, country in zip(frame["Nationality"], frame["Country Name"])
    ]
    frame["Age Histogram"] = frame["Age"].apply(age_histogram_label)

    return frame


def feature_dictionary() -> dict[str, str]:
    """Explain each engineered field for the project documentation."""

    return {
        "Departure Year": "Year extracted from Departure Date.",
        "Departure Month": "Numeric month extracted from Departure Date.",
        "Departure Month Name": "Month name extracted from Departure Date.",
        "Departure Day": "Calendar day extracted from Departure Date.",
        "Day of Week": "Weekday name extracted from Departure Date.",
        "Weekend/Weekday": "Weekend when Saturday/Sunday, otherwise Weekday.",
        "Age Group": "Child, Teenager, Young Adult, Adult, or Senior.",
        "Domestic/International": "Approximate comparison of passenger nationality and airport country.",
        "Age Histogram": "Ten age intervals used for the dashboard age distribution chart.",
    }


# ---------------------------------------------------------------------------
# Stage 6 — Exploratory Data Analysis
# ---------------------------------------------------------------------------


def average_by_group(df: pd.DataFrame, group_column: str) -> list[dict[str, Any]]:
    """Calculate average age for each group."""

    grouped = (
        df.assign(Age=pd.to_numeric(df["Age"], errors="coerce"))
        .dropna(subset=[group_column, "Age"])
        .groupby(group_column, dropna=False)["Age"]
        .mean()
        .sort_values(ascending=False)
    )

    return [
        {"label": str(label), "value": round(float(value), 2)}
        for label, value in grouped.items()
    ]


def top_n_table(df: pd.DataFrame, column: str, n: int = 10) -> list[dict[str, Any]]:
    """Return the most common values in a categorical column."""

    return series_counts(df[column], limit=n)


def cross_tabulation(
    df: pd.DataFrame,
    row_column: str,
    column: str = "Flight Status",
    row_order: Sequence[str] | None = None,
) -> pd.DataFrame:
    """Create a crosstab used by both charts and statistical tests."""

    table = pd.crosstab(df[row_column], df[column])
    if row_order is not None:
        table = table.reindex(row_order, fill_value=0)
    table = table.reindex(columns=STATUS_ORDER, fill_value=0)
    return table


def crosstab_chart_payload(
    df: pd.DataFrame,
    row_column: str,
    row_order: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Convert a crosstab into a Chart.js stacked-bar payload."""

    table = cross_tabulation(df, row_column, "Flight Status", row_order)
    categories = [str(index) for index in table.index if table.loc[index].sum() > 0]

    return {
        "categories": categories,
        "series": [
            {
                "name": status,
                "data": [int(table.loc[category, status]) for category in categories],
            }
            for status in STATUS_ORDER
        ],
    }


def time_analysis(df: pd.DataFrame) -> dict[str, Any]:
    """Build month, year, and weekday analysis."""

    year = series_counts(df["Departure Year"].dropna().astype(int).astype(str))
    year = sorted(year, key=lambda item: int(item["label"]))

    month = series_counts(df["Departure Month Name"], order=MONTH_ORDER)
    day = series_counts(df["Day of Week"], order=DAY_ORDER)
    weekend = series_counts(df["Weekend/Weekday"], order=["Weekday", "Weekend"])

    status_month = {
        "categories": [
            month_name
            for month_name in MONTH_ORDER
            if (df["Departure Month Name"] == month_name).any()
        ],
        "series": [
            {
                "name": status,
                "data": [
                    int(
                        ((df["Departure Month Name"] == month_name) &
                         (df["Flight Status"] == status)).sum()
                    )
                    for month_name in MONTH_ORDER
                ],
            }
            for status in STATUS_ORDER
        ],
    }

    return {
        "year": year,
        "month": month,
        "day_of_week": day,
        "weekend_weekday": weekend,
        "status_month": status_month,
    }


# ---------------------------------------------------------------------------
# Stage 7 — Data Visualization Preparation
# ---------------------------------------------------------------------------


def chart_payloads(df: pd.DataFrame) -> dict[str, Any]:
    """Prepare every chart's labels and values in one place.

    The browser does not need to understand the raw CSV to draw a chart.
    Python performs the aggregation here, and the frontend simply consumes the
    resulting JSON arrays.  This keeps the analytical responsibility in the
    Python layer while keeping the website lightweight.
    """

    return {
        "gender": series_counts(df["Gender"]),
        "age_histogram": series_counts(df["Age Histogram"], order=AGE_HISTOGRAM_ORDER),
        "age_group": series_counts(df["Age Group"], order=AGE_GROUP_ORDER),
        "nationality_top10": top_n_table(df, "Nationality", 10),
        "continent": series_counts(df["Continents"], order=CONTINENT_ORDER),
        "country_top10": top_n_table(df, "Country Name", 10),
        "status": series_counts(df["Flight Status"], order=STATUS_ORDER),
        "airport_top10": top_n_table(df, "Airport Name", 10),
        "arrival_top10": top_n_table(df, "Arrival Airport", 10),
        **time_analysis(df),
        "gender_status": crosstab_chart_payload(df, "Gender", ["Female", "Male"]),
        "continent_status": crosstab_chart_payload(df, "Continents", CONTINENT_ORDER),
        "age_status": crosstab_chart_payload(df, "Age Group", AGE_GROUP_ORDER),
        "domestic_status": crosstab_chart_payload(df, "Domestic/International", TRAVEL_ORDER),
        "avg_age_gender": average_by_group(df, "Gender"),
        "avg_age_continent": average_by_group(df, "Continents"),
    }


# ---------------------------------------------------------------------------
# Stage 8 — Statistical Analysis
# ---------------------------------------------------------------------------


def chi_square_result(
    df: pd.DataFrame,
    category_column: str,
    status_column: str = "Flight Status",
    category_order: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Run a Chi-square test of independence for two categorical variables."""

    table = pd.crosstab(df[category_column], df[status_column])

    if category_order is not None:
        table = table.reindex(category_order, fill_value=0)
    table = table.reindex(columns=STATUS_ORDER, fill_value=0)

    table = table.loc[table.sum(axis=1) > 0]
    table = table.loc[:, table.sum(axis=0) > 0]

    if table.shape[0] < 2 or table.shape[1] < 2:
        return {
            "chi2": 0.0,
            "p_value": 1.0,
            "degrees_of_freedom": 0,
            "significant_at_0_05": False,
            "sample_size": int(table.to_numpy().sum()),
        }

    chi2, p_value, degrees, expected = chi2_contingency(table)

    return {
        "chi2": round(float(chi2), 4),
        "p_value": float(p_value),
        "degrees_of_freedom": int(degrees),
        "significant_at_0_05": bool(p_value < 0.05),
        "sample_size": int(table.to_numpy().sum()),
    }


def statistical_analysis(df: pd.DataFrame) -> dict[str, Any]:
    """Run all categorical association tests displayed in the dashboard."""

    return {
        "gender_vs_status": chi_square_result(
            df, "Gender", "Flight Status", ["Female", "Male"]
        ),
        "continent_vs_status": chi_square_result(
            df, "Continents", "Flight Status", CONTINENT_ORDER
        ),
        "age_group_vs_status": chi_square_result(
            df, "Age Group", "Flight Status", AGE_GROUP_ORDER
        ),
        "domestic_vs_status": chi_square_result(
            df, "Domestic/International", "Flight Status", TRAVEL_ORDER
        ),
    }


def descriptive_statistics(df: pd.DataFrame) -> dict[str, Any]:
    """Calculate descriptive statistics used in the Statistics section."""

    ages = pd.to_numeric(df["Age"], errors="coerce").dropna()
    return {
        "count": int(ages.count()),
        "mean": round(float(ages.mean()), 2),
        "median": round(float(ages.median()), 2),
        "mode": round(float(ages.mode().iloc[0]), 2) if not ages.mode().empty else None,
        "minimum": int(ages.min()) if not ages.empty else 0,
        "maximum": int(ages.max()) if not ages.empty else 0,
        "range": int(ages.max() - ages.min()) if not ages.empty else 0,
        "standard_deviation": round(float(ages.std()), 2) if len(ages) > 1 else 0.0,
        "variance": round(float(ages.var()), 2) if len(ages) > 1 else 0.0,
        "quartiles": {
            "Q1": round(float(ages.quantile(0.25)), 2) if not ages.empty else None,
            "Q2": round(float(ages.quantile(0.50)), 2) if not ages.empty else None,
            "Q3": round(float(ages.quantile(0.75)), 2) if not ages.empty else None,
        },
    }


# ---------------------------------------------------------------------------
# Stage 9 — Data Interpretation / Insights
# ---------------------------------------------------------------------------


def percentage(part: int | float, total: int | float) -> float:
    """Return a safe percentage rounded to two decimals."""

    if not total:
        return 0.0
    return round(float(part) / float(total) * 100, 2)


def insight_texts(df: pd.DataFrame) -> list[dict[str, str]]:
    """Generate concise, data-driven statements for the Insights page."""

    total = len(df)
    status_name, status_count = top_frequency(df["Flight Status"])
    nationality_name, nationality_count = top_frequency(df["Nationality"])
    airport_name, airport_count = top_frequency(df["Airport Name"])
    month_name, month_count = top_frequency(df["Departure Month Name"])
    day_name, day_count = top_frequency(df["Day of Week"])
    continent_name, continent_count = top_frequency(df["Continents"])

    international_count = int((df["Domestic/International"] == "International").sum())
    domestic_count = int((df["Domestic/International"] == "Domestic").sum())

    return [
        {
            "icon": "✈",
            "title": "Flight status",
            "text": (
                f"{status_name} is the most frequent flight status, with "
                f"{status_count:,} of {total:,} records ({percentage(status_count, total)}%)."
            ),
        },
        {
            "icon": "🧭",
            "title": "Nationality",
            "text": (
                f"{nationality_name} is the most frequently represented nationality, "
                f"with {nationality_count:,} records."
            ),
        },
        {
            "icon": "🏢",
            "title": "Airport activity",
            "text": (
                f"{airport_name} is the most frequently represented departure airport, "
                f"with {airport_count:,} records."
            ),
        },
        {
            "icon": "📅",
            "title": "Time pattern",
            "text": (
                f"{month_name} has the highest monthly departure count ({month_count:,}), "
                f"while {day_name} is the busiest weekday category ({day_count:,})."
            ),
        },
        {
            "icon": "🌍",
            "title": "Geographic distribution",
            "text": (
                f"{continent_name} contains the largest number of records ({continent_count:,}) "
                "among the represented continents."
            ),
        },
        {
            "icon": "🌐",
            "title": "Travel classification",
            "text": (
                f"The approximate nationality-vs-airport-country classification contains "
                f"{international_count:,} International and {domestic_count:,} Domestic records."
            ),
        },
    ]


def interpretation_notes(statistics: Mapping[str, Any]) -> list[str]:
    """Create neutral notes explaining how to interpret the tests."""

    notes = [
        "A p-value below 0.05 is treated as statistically significant for this project.",
        "Statistical association does not establish causation.",
        "The Domestic/International field is an approximation based on nationality and airport country.",
    ]

    significant_tests = [
        name for name, result in statistics.items()
        if result.get("significant_at_0_05")
    ]

    if significant_tests:
        notes.append(
            "Significant associations were detected for: "
            + ", ".join(significant_tests)
            + "."
        )
    else:
        notes.append("No tested categorical relationship met the 0.05 significance threshold.")

    return notes


# ---------------------------------------------------------------------------
# Stage 10 — Reporting / Presentation of Findings
# ---------------------------------------------------------------------------


def make_summary(df: pd.DataFrame, quality: Mapping[str, Any]) -> AnalysisSummary:
    """Build the dashboard summary object."""

    ages = pd.to_numeric(df["Age"], errors="coerce").dropna()
    return AnalysisSummary(
        total_records=int(len(df)),
        average_age=mean_round(ages),
        median_age=median_round(ages),
        minimum_age=int(ages.min()) if not ages.empty else 0,
        maximum_age=int(ages.max()) if not ages.empty else 0,
        std_age=std_round(ages),
        nationalities=int(df["Nationality"].nunique()),
        airports=int(df["Airport Name"].nunique()),
        arrival_airports=int(df["Arrival Airport"].nunique()),
        continents=int(df["Continents"].nunique()),
        years=int(df["Departure Year"].nunique(dropna=True)),
        statuses=int(df["Flight Status"].nunique()),
        duplicate_records_removed=int(quality.get("duplicate_rows_removed", 0)),
        missing_values_total=int(df.isna().sum().sum()),
    )


def build_metadata(
    source: Mapping[str, Any],
    quality: Mapping[str, Any],
) -> dict[str, Any]:
    """Describe the analytical pipeline represented by the JSON artifact."""

    return {
        "project": "ALTAIR",
        "title": "Airline Data Analysis",
        "dataset": source,
        "workflow": [
            "Data Collection",
            "Data Loading",
            "Data Exploration",
            "Data Cleaning",
            "Feature Engineering",
            "Exploratory Data Analysis",
            "Data Visualization",
            "Statistical Analysis",
            "Data Interpretation / Insights",
            "Reporting / Presentation of Findings",
        ],
        "removed_columns": REMOVED_COLUMNS,
        "feature_definitions": feature_dictionary(),
        "data_quality": quality,
        "generated_by": "python/airline_analysis.py",
    }


def build_dashboard_payload(
    df: pd.DataFrame,
    source: Mapping[str, Any],
    quality: Mapping[str, Any],
) -> dict[str, Any]:
    """Assemble the complete JSON contract consumed by the website."""

    summary = make_summary(df, quality)
    charts = chart_payloads(df)
    statistics = statistical_analysis(df)
    descriptive = descriptive_statistics(df)

    payload: dict[str, Any] = {
        "metadata": build_metadata(source, quality),
        "summary": asdict(summary),
        **charts,
        "statistics": statistics,
        "descriptive_statistics": descriptive,
        "insights": insight_texts(df),
        "interpretation_notes": interpretation_notes(statistics),
    }

    return json_safe(payload)


def build_profile_report(
    raw: pd.DataFrame,
    cleaned: pd.DataFrame,
    quality: Mapping[str, Any],
) -> dict[str, Any]:
    """Create a detailed profile artifact for academic demonstration."""

    numeric_columns = cleaned.select_dtypes(include=[np.number]).columns.tolist()
    categorical_columns = cleaned.select_dtypes(include=["object", "string"]).columns.tolist()

    numeric_profile = {}
    for column in numeric_columns:
        values = pd.to_numeric(cleaned[column], errors="coerce")
        numeric_profile[column] = {
            "count": int(values.count()),
            "mean": mean_round(values),
            "median": median_round(values),
            "minimum": float(values.min()) if values.notna().any() else None,
            "maximum": float(values.max()) if values.notna().any() else None,
            "std": std_round(values),
        }

    categorical_profile = {}
    for column in categorical_columns:
        categorical_profile[column] = {
            "unique_values": int(cleaned[column].nunique(dropna=True)),
            "top_values": series_counts(cleaned[column], limit=10),
        }

    return {
        "dataset_before_cleaning": dataframe_overview(raw),
        "dataset_after_cleaning": dataframe_overview(cleaned),
        "quality": quality,
        "numeric_profile": numeric_profile,
        "categorical_profile": categorical_profile,
    }


def build_analysis_report(
    df: pd.DataFrame,
    dashboard: Mapping[str, Any],
) -> dict[str, Any]:
    """Create a human-readable report artifact alongside the dashboard JSON."""

    summary = dashboard["summary"]
    statistics = dashboard["statistics"]

    return {
        "project": "ALTAIR — Airline Data Analysis",
        "purpose": (
            "Analyze passenger demographics, geographic distribution, flight status, "
            "airport activity, time patterns, and categorical relationships."
        ),
        "record_count": summary["total_records"],
        "passenger_statistics": dashboard["descriptive_statistics"],
        "key_distributions": {
            "gender": dashboard["gender"],
            "age_group": dashboard["age_group"],
            "flight_status": dashboard["status"],
            "continent": dashboard["continent"],
        },
        "top_airports": {
            "departure": dashboard["airport_top10"],
            "arrival": dashboard["arrival_top10"],
        },
        "top_nationalities": dashboard["nationality_top10"],
        "statistical_tests": statistics,
        "insights": dashboard["insights"],
        "limitations": [
            "The source dataset represents records in a single dataset period rather than a live airline operation.",
            "Domestic/International is an approximate classification because it compares nationality with airport country; it is not a ticket itinerary field.",
            "The dashboard presents associations and descriptive patterns; it does not infer causal relationships.",
        ],
    }


def export_cleaned_dataset(df: pd.DataFrame, path: Path = CLEANED_CSV) -> None:
    """Export the processed DataFrame used by the website Data Explorer."""

    export = df.copy()
    if "Departure Date" in export.columns:
        export["Departure Date"] = pd.to_datetime(
            export["Departure Date"], errors="coerce"
        ).dt.strftime("%Y-%m-%d")

    # Convert nullable integer columns to strings only where necessary so the
    # browser's CSV parser receives predictable values.
    export.to_csv(path, index=False)


def numpy_and_preprocessing_demo(df: pd.DataFrame) -> dict[str, Any]:
    """Create small, reproducible artifacts that demonstrate course preprocessing.

    The project does not need a machine-learning model. These operations are kept
    as analysis examples so the chosen airline project visibly demonstrates
    NumPy arrays, scaling, label encoding, and one-hot encoding.
    """

    age = pd.to_numeric(df["Age"], errors="coerce").dropna().to_numpy(dtype=float)
    sample = age[:12]
    sample_matrix = sample.reshape(3, 4) if sample.size >= 12 else sample.reshape(1, -1)
    standardized = (age - np.mean(age)) / np.std(age, ddof=0)

    status_order = ["On Time", "Delayed", "Cancelled"]
    status_map = {label: index for index, label in enumerate(status_order)}
    label_encoded = df["Flight Status"].map(status_map).fillna(-1).astype(int)
    one_hot = pd.get_dummies(df["Flight Status"], prefix="Status", dtype=int)

    return {
        "numpy_array_shape": list(sample.shape),
        "numpy_reshaped_matrix_shape": list(sample_matrix.shape),
        "numpy_reshape_example": sample_matrix.tolist(),
        "age_standardization": {
            "mean_before": round(float(np.mean(age)), 4),
            "std_before": round(float(np.std(age, ddof=0)), 4),
            "mean_after": round(float(np.mean(standardized)), 6),
            "std_after": round(float(np.std(standardized, ddof=0)), 6),
        },
        "label_encoding": status_map,
        "one_hot_columns": list(one_hot.columns),
        "one_hot_sample": one_hot.head(5).to_dict(orient="records"),
    }


def export_matplotlib_visualizations(df: pd.DataFrame) -> list[Path]:
    """Generate Matplotlib figures required for the DAE visualization outcome."""

    visual_dir = OUTPUT_DIR / "visualizations"
    visual_dir.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []

    # 1. Bar chart — flight status distribution
    status = df["Flight Status"].value_counts()
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(status.index.astype(str), status.values)
    ax.set_title("Flight Status Distribution")
    ax.set_xlabel("Flight Status")
    ax.set_ylabel("Passenger Records")
    fig.tight_layout()
    path = visual_dir / "01_flight_status_bar.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    generated.append(path)

    # 2. Pie chart — passenger gender distribution
    gender = df["Gender"].value_counts()
    fig, ax = plt.subplots(figsize=(7, 7))
    ax.pie(gender.values, labels=gender.index.astype(str), autopct="%1.1f%%", startangle=90)
    ax.set_title("Passenger Gender Distribution")
    fig.tight_layout()
    path = visual_dir / "02_gender_pie.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    generated.append(path)

    # 3. Box plot — passenger age
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.boxplot(df["Age"].dropna().to_numpy())
    ax.set_title("Passenger Age Box Plot")
    ax.set_ylabel("Age")
    fig.tight_layout()
    path = visual_dir / "03_age_box.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    generated.append(path)

    # 4. Histogram — passenger age distribution
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(df["Age"].dropna(), bins=18)
    ax.set_title("Passenger Age Distribution")
    ax.set_xlabel("Age")
    ax.set_ylabel("Frequency")
    fig.tight_layout()
    path = visual_dir / "04_age_histogram.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    generated.append(path)

    # 5. Line chart — monthly passenger records
    month_counts = df.groupby("Departure Month", observed=False).size().reindex(range(1, 13), fill_value=0)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(month_counts.index, month_counts.values, marker="o")
    ax.set_title("Passenger Records by Departure Month")
    ax.set_xlabel("Month")
    ax.set_ylabel("Passenger Records")
    ax.set_xticks(range(1, 13))
    fig.tight_layout()
    path = visual_dir / "05_monthly_line.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    generated.append(path)

    # 6. Scatter plot — age against a deterministic row sample index.
    # This is intentionally descriptive rather than a claim of causation.
    sample = df[["Age"]].reset_index(drop=True).iloc[::max(1, len(df) // 1500)]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(sample.index, sample["Age"], s=12, alpha=0.6)
    ax.set_title("Passenger Age Scatter View")
    ax.set_xlabel("Sample Row Index")
    ax.set_ylabel("Age")
    fig.tight_layout()
    path = visual_dir / "06_age_scatter.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    generated.append(path)

    # 7. Subplots — two compact views in one Matplotlib figure.
    continent = df["Continents"].value_counts().head(6)
    age_group = df["Age Group"].value_counts().reindex(
        ["Child", "Teenager", "Young Adult", "Adult", "Senior"], fill_value=0
    )
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    axes[0].bar(continent.index.astype(str), continent.values)
    axes[0].set_title("Records by Continent")
    axes[0].tick_params(axis="x", rotation=30)
    axes[1].plot(age_group.index.astype(str), age_group.values, marker="o")
    axes[1].set_title("Records by Age Group")
    axes[1].tick_params(axis="x", rotation=30)
    fig.tight_layout()
    path = visual_dir / "07_summary_subplots.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    generated.append(path)

    return generated


def export_all(
    raw: pd.DataFrame,
    processed: pd.DataFrame,
    dashboard: Mapping[str, Any],
    quality: Mapping[str, Any],
    source: Mapping[str, Any],
) -> None:
    """Write every reproducible project artifact."""

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    export_cleaned_dataset(processed, CLEANED_CSV)
    write_json(ANALYSIS_JSON, dashboard)
    write_json(PROFILE_JSON, build_profile_report(raw, processed, quality))
    write_json(REPORT_JSON, build_analysis_report(processed, dashboard))

    # A compact text report is useful for a lab demonstration and does not
    # affect the live website.
    report_lines = [
        "ALTAIR — Airline Data Analysis Report",
        "=" * 42,
        f"Input file: {source['source_file']}",
        f"Records analyzed: {dashboard['summary']['total_records']:,}",
        f"Average age: {dashboard['summary']['average_age']}",
        f"Median age: {dashboard['summary']['median_age']}",
        f"Unique nationalities: {dashboard['summary']['nationalities']:,}",
        f"Unique departure airports: {dashboard['summary']['airports']:,}",
        f"Unique arrival airports: {dashboard['summary']['arrival_airports']:,}",
        f"Duplicate rows removed: {quality['duplicate_rows_removed']:,}",
        f"Invalid ages handled: {quality['invalid_age_values']:,}",
        f"Invalid dates detected: {quality['invalid_dates']:,}",
        "",
        "Insights",
        "--------",
    ]
    report_lines.extend(f"- {item['text']}" for item in dashboard["insights"])
    (OUTPUT_DIR / "analysis_report.txt").write_text(
        "\n".join(report_lines) + "\n", encoding="utf-8"
    )
    export_markdown_report(processed, dashboard)
    export_summary_csvs(processed)
    write_json(OUTPUT_DIR / "numpy_preprocessing_demo.json", numpy_and_preprocessing_demo(processed))
    export_matplotlib_visualizations(processed)
    write_json(OUTPUT_DIR / "project_manifest.json", final_project_manifest())


# ---------------------------------------------------------------------------
# Validation and command-line execution
# ---------------------------------------------------------------------------


def validate_processed_dataset(df: pd.DataFrame) -> None:
    """Perform final checks before writing dashboard artifacts."""

    missing_required = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing_required:
        raise ValueError(f"Processed data is missing required fields: {missing_required}")

    if df.empty:
        raise ValueError("Processed dataset is empty.")

    if not pd.api.types.is_numeric_dtype(df["Age"]):
        raise TypeError("Age must remain numeric after cleaning.")

    invalid_age = ~pd.to_numeric(df["Age"], errors="coerce").between(1, 100)
    if invalid_age.any():
        raise ValueError("Processed dataset contains an Age value outside 1–100.")

    if not pd.api.types.is_datetime64_any_dtype(df["Departure Date"]):
        raise TypeError("Departure Date must be parsed as datetime before export.")

    if df["Flight Status"].astype(str).str.strip().eq("").all():
        raise ValueError("Flight Status contains no usable values.")


def print_stage_summary(
    raw: pd.DataFrame,
    processed: pd.DataFrame,
    quality: Mapping[str, Any],
    dashboard: Mapping[str, Any],
) -> None:
    """Print a concise terminal summary for a classroom demonstration."""

    summary = dashboard["summary"]
    print("\n" + "=" * 72)
    print("ALTAIR — AIRLINE DATA ANALYSIS")
    print("=" * 72)
    print(f"Raw dataset shape       : {raw.shape[0]:,} rows × {raw.shape[1]} columns")
    print(f"Processed dataset shape : {processed.shape[0]:,} rows × {processed.shape[1]} columns")
    print(f"Duplicate rows removed  : {quality['duplicate_rows_removed']:,}")
    print(f"Invalid ages handled    : {quality['invalid_age_values']:,}")
    print(f"Invalid dates detected  : {quality['invalid_dates']:,}")
    print(f"Average passenger age   : {summary['average_age']}")
    print(f"Median passenger age    : {summary['median_age']}")
    print(f"Nationalities           : {summary['nationalities']:,}")
    print(f"Departure airports      : {summary['airports']:,}")
    print(f"Arrival airports        : {summary['arrival_airports']:,}")
    print(f"Continents              : {summary['continents']:,}")
    print("\nFlight status distribution:")
    for item in dashboard["status"]:
        print(f"  - {item['label']}: {item['value']:,}")

    print("\nStatistical tests:")
    for name, result in dashboard["statistics"].items():
        print(
            f"  - {name}: chi2={result['chi2']}, "
            f"p={result['p_value']:.6g}, "
            f"df={result['degrees_of_freedom']}"
        )

    print("\nGenerated files:")
    print(f"  - {CLEANED_CSV.relative_to(ROOT)}")
    print(f"  - {ANALYSIS_JSON.relative_to(ROOT)}")
    print(f"  - {PROFILE_JSON.relative_to(ROOT)}")
    print(f"  - {REPORT_JSON.relative_to(ROOT)}")
    print("=" * 72)


def parse_arguments(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse optional command-line arguments."""

    parser = argparse.ArgumentParser(
        description="Run the ALTAIR airline data-analysis pipeline."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=INPUT_CSV,
        help="Path to the source airline CSV.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress the final console summary.",
    )
    return parser.parse_args(argv)


def run_pipeline(input_path: Path = INPUT_CSV) -> dict[str, Any]:
    """Run all ten project stages and return the dashboard payload."""

    # 1. Data Collection
    source = describe_collection_source(verify_input_dataset(input_path))

    # 2. Data Loading
    raw = load_dataset(input_path)
    validate_required_columns(raw)

    # 3. Data Exploration
    exploration = exploration_report(raw)

    # 4. Data Cleaning
    cleaned, quality = clean_dataset(raw)

    # 5. Feature Engineering
    processed = feature_engineering(cleaned)
    validate_processed_dataset(processed)

    # 6–8. EDA, visualization preparation, and statistics
    dashboard = build_dashboard_payload(processed, source, quality)
    dashboard["metadata"]["exploration_snapshot"] = {
        "raw_shape": exploration["shape"],
        "duplicate_rows": exploration["duplicate_rows"],
        "missing_values": exploration["missing_values"],
    }

    # 9–10. Interpretation and reporting are represented in the dashboard and
    # separate report artifacts so the findings remain reproducible.
    export_all(raw, processed, dashboard, quality, source)

    if not dashboard["summary"]["total_records"]:
        raise RuntimeError("No records were available after processing.")

    return dashboard


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    args = parse_arguments(argv)
    try:
        dashboard = run_pipeline(args.input)
        if not args.quiet:
            # Reloading the cleaned CSV is unnecessary; use the payload and a
            # lightweight message here because run_pipeline already validated
            # and exported every artifact.
            print("\nALTAIR analysis completed successfully.")
            print(f"Records analyzed: {dashboard['summary']['total_records']:,}")
            print(f"Dashboard JSON : {ANALYSIS_JSON}")
            print(f"Cleaned CSV    : {CLEANED_CSV}")
        return 0
    except Exception as exc:  # pragma: no cover - CLI safety net
        print(f"Analysis failed: {exc}", file=sys.stderr)
        return 1



# ---------------------------------------------------------------------------
# Extended analytical modules
# ---------------------------------------------------------------------------
# The functions below keep the Python layer useful beyond the exact numbers
# required by the web page.  They are deliberately written as small reusable
# operations so the project can be demonstrated section by section in a lab.
# They also make the exported report easier to extend for future datasets.


def distribution_table(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """Return count and percentage for every non-empty category.

    This is a common EDA operation: frequency counts answer how many records
    belong to each category, while percentages make the same distribution easy
    to compare when the dataset size changes.
    """

    values = clean_text(df[column])
    counts = values[values.ne("")].value_counts(dropna=False)
    total = int(counts.sum())
    table = pd.DataFrame({"Count": counts.astype(int)})
    table["Percentage"] = (table["Count"] / total * 100).round(2) if total else 0
    table.index.name = column
    return table.reset_index()


def status_percentage_table(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate flight-status percentages for the complete dataset."""

    table = distribution_table(df, "Flight Status")
    return table.rename(columns={"Count": "Records", "Percentage": "Percentage of Records"})


def grouped_status_rates(df: pd.DataFrame, group_column: str) -> pd.DataFrame:
    """Calculate flight-status rates within each category.

    Unlike a raw crosstab, rates answer the question "what percentage of this
    group has each status?".  This makes the analysis more informative when
    groups have very different record counts.
    """

    table = pd.crosstab(df[group_column], df["Flight Status"])
    table = table.reindex(columns=STATUS_ORDER, fill_value=0)
    totals = table.sum(axis=1).replace(0, np.nan)
    rates = table.div(totals, axis=0).mul(100).round(2)
    rates["Total Records"] = table.sum(axis=1).astype(int)
    rates.index.name = group_column
    return rates.reset_index()


def gender_age_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Create a descriptive table combining gender and age statistics."""

    work = df.copy()
    work["Age"] = pd.to_numeric(work["Age"], errors="coerce")
    grouped = work.dropna(subset=["Age"]).groupby("Gender")["Age"]
    result = grouped.agg(["count", "mean", "median", "min", "max", "std"]).reset_index()
    result.columns = ["Gender", "Records", "Mean Age", "Median Age", "Minimum Age", "Maximum Age", "Std. Deviation"]
    for column in ["Mean Age", "Median Age", "Std. Deviation"]:
        result[column] = result[column].round(2)
    return result


def age_group_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Summarize passenger counts and status distributions by age group."""

    table = pd.crosstab(df["Age Group"], df["Flight Status"])
    table = table.reindex(AGE_GROUP_ORDER, fill_value=0)
    table = table.reindex(columns=STATUS_ORDER, fill_value=0)
    table["Total"] = table.sum(axis=1)
    table["Percentage"] = np.where(
        len(df), (table["Total"] / len(df) * 100).round(2), 0
    )
    return table.reset_index()


def continent_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Build a geographic summary using continent-level counts and ages."""

    grouped = df.copy()
    grouped["Age"] = pd.to_numeric(grouped["Age"], errors="coerce")
    result = (
        grouped.groupby("Continents", dropna=False)
        .agg(
            Records=("Continents", "size"),
            Average_Age=("Age", "mean"),
            Nationalities=("Nationality", "nunique"),
            Airports=("Airport Name", "nunique"),
        )
        .reset_index()
    )
    result["Average_Age"] = result["Average_Age"].round(2)
    result["Percentage"] = (result["Records"] / len(grouped) * 100).round(2)
    return result.sort_values("Records", ascending=False).reset_index(drop=True)


def country_summary(df: pd.DataFrame, limit: int = 20) -> pd.DataFrame:
    """Return country-level record counts and average passenger age."""

    work = df.copy()
    work["Age"] = pd.to_numeric(work["Age"], errors="coerce")
    result = (
        work.groupby("Country Name", dropna=False)
        .agg(Records=("Country Name", "size"), Average_Age=("Age", "mean"))
        .reset_index()
    )
    result["Average_Age"] = result["Average_Age"].round(2)
    result["Percentage"] = (result["Records"] / len(work) * 100).round(2)
    return result.sort_values("Records", ascending=False).head(limit).reset_index(drop=True)


def airport_summary(df: pd.DataFrame, limit: int = 20) -> pd.DataFrame:
    """Summarize departure airports by record volume and flight status."""

    counts = df["Airport Name"].value_counts().rename("Records").to_frame()
    status = pd.crosstab(df["Airport Name"], df["Flight Status"])
    status = status.reindex(columns=STATUS_ORDER, fill_value=0)
    result = counts.join(status, how="left").reset_index()
    result = result.rename(columns={"index": "Airport Name"})
    result["Percentage"] = (result["Records"] / len(df) * 100).round(2)
    return result.sort_values("Records", ascending=False).head(limit).reset_index(drop=True)


def arrival_airport_summary(df: pd.DataFrame, limit: int = 20) -> pd.DataFrame:
    """Summarize the most frequently occurring arrival airport codes."""

    counts = df["Arrival Airport"].value_counts().rename("Records").reset_index()
    counts.columns = ["Arrival Airport", "Records"]
    counts["Percentage"] = (counts["Records"] / len(df) * 100).round(2)
    return counts.head(limit)


def monthly_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Create a month-by-month table containing counts and status totals."""

    table = pd.crosstab(df["Departure Month Name"], df["Flight Status"])
    table = table.reindex(MONTH_ORDER, fill_value=0)
    table = table.reindex(columns=STATUS_ORDER, fill_value=0)
    table["Total Records"] = table.sum(axis=1)
    table["Percentage"] = (table["Total Records"] / len(df) * 100).round(2)
    return table.reset_index().rename(columns={"Departure Month Name": "Month"})


def weekday_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Create weekday and weekend statistics."""

    table = pd.crosstab(df["Day of Week"], df["Flight Status"])
    table = table.reindex(DAY_ORDER, fill_value=0)
    table = table.reindex(columns=STATUS_ORDER, fill_value=0)
    table["Total Records"] = table.sum(axis=1)
    table["Percentage"] = (table["Total Records"] / len(df) * 100).round(2)
    table["Week Type"] = np.where(table.index.isin(["Saturday", "Sunday"]), "Weekend", "Weekday")
    return table.reset_index().rename(columns={"Day of Week": "Day"})


def year_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Create a year-level record summary."""

    table = pd.crosstab(df["Departure Year"], df["Flight Status"])
    table = table.reindex(columns=STATUS_ORDER, fill_value=0)
    table["Total Records"] = table.sum(axis=1)
    table["Percentage"] = (table["Total Records"] / len(df) * 100).round(2)
    return table.reset_index()


def weekend_status_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Compare weekday and weekend flight-status distributions."""

    table = pd.crosstab(df["Weekend/Weekday"], df["Flight Status"])
    table = table.reindex(["Weekday", "Weekend"], fill_value=0)
    table = table.reindex(columns=STATUS_ORDER, fill_value=0)
    table["Total Records"] = table.sum(axis=1)
    for status in STATUS_ORDER:
        table[f"{status} %"] = np.where(
            table["Total Records"] > 0,
            table[status] / table["Total Records"] * 100,
            0,
        ).round(2)
    return table.reset_index()


def nationality_continent_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Build a nationality-to-continent frequency matrix for EDA."""

    table = pd.crosstab(df["Nationality"], df["Continents"])
    table = table.reindex(columns=[c for c in CONTINENT_ORDER if c in table.columns], fill_value=0)
    table["Total"] = table.sum(axis=1)
    return table.sort_values("Total", ascending=False).head(20).reset_index()


def country_continent_consistency(df: pd.DataFrame) -> dict[str, Any]:
    """Measure how often country and continent fields are populated together."""

    country = clean_text(df["Country Name"])
    continent = clean_text(df["Continents"])
    valid = country.ne("") & continent.ne("")
    return {
        "records_with_country": int(country.ne("").sum()),
        "records_with_continent": int(continent.ne("").sum()),
        "records_with_both": int(valid.sum()),
        "records_missing_one_or_both": int((~valid).sum()),
        "coverage_percentage": percentage(valid.sum(), len(df)),
    }


def date_coverage(df: pd.DataFrame) -> dict[str, Any]:
    """Describe the temporal coverage represented in the dataset."""

    dates = pd.to_datetime(df["Departure Date"], errors="coerce").dropna()
    if dates.empty:
        return {"minimum": None, "maximum": None, "days": 0, "years": []}

    minimum = dates.min()
    maximum = dates.max()
    return {
        "minimum": minimum.strftime("%Y-%m-%d"),
        "maximum": maximum.strftime("%Y-%m-%d"),
        "days": int((maximum - minimum).days + 1),
        "years": sorted({int(value) for value in dates.dt.year.unique()}),
    }


def age_outlier_summary(df: pd.DataFrame) -> dict[str, Any]:
    """Identify statistical age outliers using the IQR rule.

    The result is descriptive only.  It is not used to delete records because
    a statistically unusual age is not automatically a data error.
    """

    ages = pd.to_numeric(df["Age"], errors="coerce").dropna()
    if ages.empty:
        return {"Q1": None, "Q3": None, "IQR": None, "lower_bound": None, "upper_bound": None, "outlier_count": 0}

    q1 = float(ages.quantile(0.25))
    q3 = float(ages.quantile(0.75))
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    count = int(((ages < lower) | (ages > upper)).sum())
    return {
        "Q1": round(q1, 2),
        "Q3": round(q3, 2),
        "IQR": round(iqr, 2),
        "lower_bound": round(lower, 2),
        "upper_bound": round(upper, 2),
        "outlier_count": count,
    }


def numeric_correlation_matrix(df: pd.DataFrame) -> dict[str, Any]:
    """Return correlations among the numeric analytical fields."""

    numeric = df.select_dtypes(include=[np.number])
    if numeric.empty:
        return {}
    return json_safe(numeric.corr(numeric_only=True).round(4).to_dict())


def status_rate_by_gender(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Convert gender status rates into JSON-ready records."""

    table = grouped_status_rates(df, "Gender")
    return json_safe(table.to_dict(orient="records"))


def status_rate_by_age_group(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Convert age-group status rates into JSON-ready records."""

    table = grouped_status_rates(df, "Age Group")
    return json_safe(table.to_dict(orient="records"))


def status_rate_by_continent(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Convert continent status rates into JSON-ready records."""

    table = grouped_status_rates(df, "Continents")
    return json_safe(table.to_dict(orient="records"))


def status_rate_by_travel_type(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Convert approximate travel-type status rates into JSON records."""

    table = grouped_status_rates(df, "Domestic/International")
    return json_safe(table.to_dict(orient="records"))


def top_status_airports(df: pd.DataFrame, limit: int = 10) -> list[dict[str, Any]]:
    """Identify airports with the highest On Time record counts."""

    work = df[df["Flight Status"].eq("On Time")]
    values = work["Airport Name"].value_counts().head(limit)
    return [{"label": str(label), "value": int(value)} for label, value in values.items()]


def delayed_airports(df: pd.DataFrame, limit: int = 10) -> list[dict[str, Any]]:
    """Identify airports with the highest Delayed record counts."""

    work = df[df["Flight Status"].eq("Delayed")]
    values = work["Airport Name"].value_counts().head(limit)
    return [{"label": str(label), "value": int(value)} for label, value in values.items()]


def cancelled_airports(df: pd.DataFrame, limit: int = 10) -> list[dict[str, Any]]:
    """Identify airports with the highest Cancelled record counts."""

    work = df[df["Flight Status"].eq("Cancelled")]
    values = work["Airport Name"].value_counts().head(limit)
    return [{"label": str(label), "value": int(value)} for label, value in values.items()]


def build_extended_report(df: pd.DataFrame) -> dict[str, Any]:
    """Assemble reusable EDA tables for the academic report.

    These tables are deliberately separate from the compact dashboard JSON.
    The dashboard needs only chart-ready arrays, while the report artifact can
    retain richer tables that demonstrate Pandas operations during evaluation.
    """

    return {
        "status_distribution": json_safe(status_percentage_table(df).to_dict(orient="records")),
        "gender_age_summary": json_safe(gender_age_summary(df).to_dict(orient="records")),
        "age_group_summary": json_safe(age_group_summary(df).to_dict(orient="records")),
        "continent_summary": json_safe(continent_summary(df).to_dict(orient="records")),
        "country_summary_top20": json_safe(country_summary(df).to_dict(orient="records")),
        "airport_summary_top20": json_safe(airport_summary(df).to_dict(orient="records")),
        "arrival_airport_summary_top20": json_safe(arrival_airport_summary(df).to_dict(orient="records")),
        "monthly_summary": json_safe(monthly_summary(df).to_dict(orient="records")),
        "weekday_summary": json_safe(weekday_summary(df).to_dict(orient="records")),
        "year_summary": json_safe(year_summary(df).to_dict(orient="records")),
        "weekend_status_summary": json_safe(weekend_status_summary(df).to_dict(orient="records")),
        "nationality_continent_matrix": json_safe(nationality_continent_matrix(df).to_dict(orient="records")),
        "country_continent_consistency": country_continent_consistency(df),
        "date_coverage": date_coverage(df),
        "age_outlier_summary": age_outlier_summary(df),
        "numeric_correlations": numeric_correlation_matrix(df),
        "status_rate_by_gender": status_rate_by_gender(df),
        "status_rate_by_age_group": status_rate_by_age_group(df),
        "status_rate_by_continent": status_rate_by_continent(df),
        "status_rate_by_travel_type": status_rate_by_travel_type(df),
        "top_on_time_airports": top_status_airports(df),
        "top_delayed_airports": delayed_airports(df),
        "top_cancelled_airports": cancelled_airports(df),
    }


def validate_category_values(df: pd.DataFrame) -> dict[str, Any]:
    """Check the categorical fields used by the dashboard for unexpected values."""

    expected = {
        "Gender": {"Female", "Male"},
        "Flight Status": set(STATUS_ORDER),
        "Continents": set(CONTINENT_ORDER),
        "Age Group": set(AGE_GROUP_ORDER),
        "Domestic/International": set(TRAVEL_ORDER),
        "Weekend/Weekday": {"Weekday", "Weekend"},
    }

    result = {}
    for column, allowed in expected.items():
        actual = set(clean_text(df[column]).dropna().unique())
        unexpected = sorted(value for value in actual if value and value not in allowed)
        result[column] = {
            "observed_values": sorted(value for value in actual if value),
            "unexpected_values": unexpected,
            "valid": not unexpected,
        }
    return result


def row_completeness(df: pd.DataFrame) -> dict[str, Any]:
    """Measure how complete each processed record is."""

    relevant = df[REQUIRED_COLUMNS].copy()
    empty_mask = relevant.isna() | relevant.astype(str).apply(lambda column: column.str.strip().eq(""))
    empty_per_row = empty_mask.sum(axis=1)
    complete = int((empty_per_row == 0).sum())
    incomplete = int((empty_per_row > 0).sum())
    return {
        "complete_records": complete,
        "incomplete_records": incomplete,
        "complete_percentage": percentage(complete, len(df)),
        "average_missing_fields_per_record": round(float(empty_per_row.mean()), 4),
    }


def field_quality_report(df: pd.DataFrame) -> dict[str, Any]:
    """Produce field-level quality percentages for the report."""

    report = {}
    for column in df.columns:
        series = df[column]
        if pd.api.types.is_numeric_dtype(series):
            valid = series.notna()
        else:
            valid = series.notna() & series.astype(str).str.strip().ne("")
        valid_count = int(valid.sum())
        report[column] = {
            "valid_records": valid_count,
            "missing_records": int(len(df) - valid_count),
            "completeness_percentage": percentage(valid_count, len(df)),
            "unique_values": int(series.nunique(dropna=True)),
        }
    return report


def build_quality_extension(raw: pd.DataFrame, processed: pd.DataFrame) -> dict[str, Any]:
    """Build a more detailed data-quality appendix."""

    return {
        "raw_duplicates": int(raw.duplicated().sum()),
        "raw_missing_by_field": {
            str(k): int(v) for k, v in raw.isna().sum().items()
        },
        "processed_field_quality": field_quality_report(processed),
        "processed_row_completeness": row_completeness(processed),
        "category_validation": validate_category_values(processed),
    }


# ---------------------------------------------------------------------------
# Extend the report artifact without changing the compact website contract.
# ---------------------------------------------------------------------------

_original_build_analysis_report = build_analysis_report


def build_analysis_report(
    df: pd.DataFrame,
    dashboard: Mapping[str, Any],
) -> dict[str, Any]:
    """Build the full academic report with descriptive and diagnostic tables."""

    report = _original_build_analysis_report(df, dashboard)
    report["extended_eda"] = build_extended_report(df)
    report["quality_appendix"] = build_quality_extension(df, df)
    return report


def gender_status_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Produce a compact gender-versus-status table for the report."""

    table = cross_tabulation(df, "Gender", "Flight Status", ["Female", "Male"])
    table["Total"] = table.sum(axis=1)
    table["On Time %"] = np.where(table["Total"] > 0, table["On Time"] / table["Total"] * 100, 0).round(2)
    table["Delayed %"] = np.where(table["Total"] > 0, table["Delayed"] / table["Total"] * 100, 0).round(2)
    table["Cancelled %"] = np.where(table["Total"] > 0, table["Cancelled"] / table["Total"] * 100, 0).round(2)
    return table.reset_index()


def airport_country_summary(df: pd.DataFrame, limit: int = 20) -> pd.DataFrame:
    """Summarize airports together with their recorded country and continent."""

    result = (
        df.groupby(["Airport Name", "Country Name", "Continents"], dropna=False)
        .size()
        .rename("Records")
        .reset_index()
        .sort_values("Records", ascending=False)
        .head(limit)
        .reset_index(drop=True)
    )
    result["Percentage"] = (result["Records"] / len(df) * 100).round(2)
    return result


def flight_status_by_month(df: pd.DataFrame) -> pd.DataFrame:
    """Return a month-by-status matrix with row totals and rates."""

    table = pd.crosstab(df["Departure Month Name"], df["Flight Status"])
    table = table.reindex(MONTH_ORDER, fill_value=0)
    table = table.reindex(columns=STATUS_ORDER, fill_value=0)
    table["Total"] = table.sum(axis=1)
    for status in STATUS_ORDER:
        table[f"{status} %"] = np.where(
            table["Total"] > 0,
            table[status] / table["Total"] * 100,
            0,
        ).round(2)
    return table.reset_index().rename(columns={"Departure Month Name": "Month"})


def flight_status_by_continent(df: pd.DataFrame) -> pd.DataFrame:
    """Return a continent-by-status matrix suitable for a report table."""

    table = cross_tabulation(df, "Continents", "Flight Status", CONTINENT_ORDER)
    table["Total"] = table.sum(axis=1)
    table["On Time %"] = np.where(table["Total"] > 0, table["On Time"] / table["Total"] * 100, 0).round(2)
    table["Delayed %"] = np.where(table["Total"] > 0, table["Delayed"] / table["Total"] * 100, 0).round(2)
    table["Cancelled %"] = np.where(table["Total"] > 0, table["Cancelled"] / table["Total"] * 100, 0).round(2)
    return table.reset_index()


def passenger_age_by_nationality(df: pd.DataFrame, limit: int = 20) -> pd.DataFrame:
    """Find nationalities with the largest record counts and their mean ages."""

    work = df.copy()
    work["Age"] = pd.to_numeric(work["Age"], errors="coerce")
    result = (
        work.groupby("Nationality", dropna=False)
        .agg(Records=("Nationality", "size"), Average_Age=("Age", "mean"))
        .reset_index()
        .sort_values("Records", ascending=False)
        .head(limit)
        .reset_index(drop=True)
    )
    result["Average_Age"] = result["Average_Age"].round(2)
    return result


def record_level_validation(df: pd.DataFrame) -> dict[str, Any]:
    """Check logical ranges used by the project before export."""

    checks = {
        "age_between_1_and_100": bool(pd.to_numeric(df["Age"], errors="coerce").between(1, 100).all()),
        "departure_dates_valid": bool(pd.to_datetime(df["Departure Date"], errors="coerce").notna().all()),
        "gender_values_valid": bool(clean_text(df["Gender"]).isin(["Female", "Male"]).all()),
        "status_values_valid": bool(clean_text(df["Flight Status"]).isin(STATUS_ORDER).all()),
        "continent_values_valid": bool(clean_text(df["Continents"]).isin(CONTINENT_ORDER).all()),
        "age_group_values_valid": bool(clean_text(df["Age Group"]).isin(AGE_GROUP_ORDER).all()),
    }
    checks["all_checks_passed"] = all(checks.values())
    return checks


def dashboard_metric_dictionary(df: pd.DataFrame) -> dict[str, Any]:
    """Document the main KPI definitions used by the website."""

    return {
        "total_records": "Number of processed passenger/flight records.",
        "average_age": "Arithmetic mean of the cleaned Age field.",
        "nationalities": "Number of distinct non-empty Nationality values.",
        "airports": "Number of distinct departure Airport Name values.",
        "arrival_airports": "Number of distinct Arrival Airport values.",
        "continents": "Number of distinct Continents values.",
        "flight_status": "Frequency of Cancelled, Delayed, and On Time records.",
        "age_group": "Frequency of the five engineered Age Group categories.",
        "time_analysis": "Counts grouped by departure year, month, and day of week.",
        "chi_square": "Chi-square test of independence between categorical variables and Flight Status.",
    }


def report_section_titles() -> list[str]:
    """Return a consistent outline for the academic report."""

    return [
        "1. Data Collection",
        "2. Data Loading",
        "3. Data Exploration",
        "4. Data Cleaning",
        "5. Feature Engineering",
        "6. Exploratory Data Analysis",
        "7. Data Visualization",
        "8. Statistical Analysis",
        "9. Data Interpretation / Insights",
        "10. Reporting / Presentation of Findings",
    ]


def build_academic_appendix(df: pd.DataFrame) -> dict[str, Any]:
    """Create an expanded appendix demonstrating additional Pandas analysis."""

    return {
        "report_outline": report_section_titles(),
        "metric_definitions": dashboard_metric_dictionary(df),
        "record_level_validation": record_level_validation(df),
        "gender_status_summary": json_safe(gender_status_summary(df).to_dict(orient="records")),
        "airport_country_summary": json_safe(airport_country_summary(df).to_dict(orient="records")),
        "flight_status_by_month": json_safe(flight_status_by_month(df).to_dict(orient="records")),
        "flight_status_by_continent": json_safe(flight_status_by_continent(df).to_dict(orient="records")),
        "passenger_age_by_nationality": json_safe(passenger_age_by_nationality(df).to_dict(orient="records")),
    }


# Keep these helper names explicit in the source because they are useful when
# the student explains the project during a viva: load -> clean -> engineer ->
# analyze -> export.  The dashboard remains a consumer of these outputs.
ANALYSIS_STAGES = {
    1: "Data Collection",
    2: "Data Loading",
    3: "Data Exploration",
    4: "Data Cleaning",
    5: "Feature Engineering",
    6: "Exploratory Data Analysis",
    7: "Data Visualization",
    8: "Statistical Analysis",
    9: "Data Interpretation / Insights",
    10: "Reporting / Presentation of Findings",
}


# Patch the extended report one final time so the additional appendix is
# available in outputs/analysis_report.json while the website JSON stays small.
_previous_build_analysis_report = build_analysis_report


def build_analysis_report(
    df: pd.DataFrame,
    dashboard: Mapping[str, Any],
) -> dict[str, Any]:
    """Build the final report artifact used for documentation and viva work."""

    report = _previous_build_analysis_report(df, dashboard)
    report["academic_appendix"] = build_academic_appendix(df)
    return report


def markdown_report(df: pd.DataFrame, dashboard: Mapping[str, Any]) -> str:
    """Generate a compact Markdown report for classroom submission.

    Keeping report generation in Python demonstrates that the analysis results
    are not hard-coded into the website.  The same DataFrame that produces the
    dashboard can also produce a readable project report.
    """

    summary = dashboard["summary"]
    lines = [
        "# ALTAIR — Airline Data Analysis",
        "",
        "## Project summary",
        "",
        "This report summarizes the processed airline dataset and the analytical operations performed by the Python pipeline.",
        "",
        "## Dataset metrics",
        "",
        f"- Records analyzed: **{summary['total_records']:,}**",
        f"- Average age: **{summary['average_age']}**",
        f"- Median age: **{summary['median_age']}**",
        f"- Nationalities represented: **{summary['nationalities']:,}**",
        f"- Departure airports represented: **{summary['airports']:,}**",
        f"- Arrival airports represented: **{summary['arrival_airports']:,}**",
        f"- Continents represented: **{summary['continents']}**",
        "",
        "## Flight status distribution",
        "",
        "| Status | Records | Percentage |",
        "|---|---:|---:|",
    ]

    total = summary["total_records"]
    for item in dashboard["status"]:
        lines.append(
            f"| {item['label']} | {item['value']:,} | {percentage(item['value'], total):.2f}% |"
        )

    lines += ["", "## Key insights", ""]
    for item in dashboard["insights"]:
        lines.append(f"- **{item['title']}:** {item['text']}")

    lines += [
        "",
        "## Statistical interpretation",
        "",
        "The Chi-square tests examine association between selected categorical variables and flight status. A p-value below 0.05 is treated as significant for this academic analysis. Significance does not imply causation.",
        "",
        "## Limitation",
        "",
        "Domestic/International is an approximate classification derived from passenger nationality and recorded airport country because the source dataset does not provide a complete itinerary-level domestic/international field.",
        "",
    ]
    return "\n".join(lines)


def export_markdown_report(df: pd.DataFrame, dashboard: Mapping[str, Any]) -> Path:
    """Write the generated Markdown report to the output directory."""

    path = OUTPUT_DIR / "analysis_report.md"
    path.write_text(markdown_report(df, dashboard), encoding="utf-8")
    return path


def export_summary_csvs(df: pd.DataFrame) -> list[Path]:
    """Export a small set of reusable summary tables for further study."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    exports = {
        "status_summary.csv": status_percentage_table(df),
        "continent_summary.csv": continent_summary(df),
        "monthly_summary.csv": monthly_summary(df),
        "airport_summary.csv": airport_summary(df, 20),
        "gender_age_summary.csv": gender_age_summary(df),
    }

    paths = []
    for filename, table in exports.items():
        path = OUTPUT_DIR / filename
        table.to_csv(path, index=False)
        paths.append(path)
    return paths


def final_project_manifest() -> dict[str, Any]:
    """Describe the generated project contract for reproducibility."""

    return {
        "input": "data/Airline Dataset Updated - v2.csv",
        "cleaned_data": "data/airline_cleaned.csv",
        "dashboard_data": "data/analysis.json",
        "python_engine": "python/airline_analysis.py",
        "dashboard_entry": "index.html",
        "frontend_assets": ["assets/app.js", "assets/style.css"],
        "report_outputs": [
            "outputs/analysis_report.json",
            "outputs/analysis_report.txt",
            "outputs/analysis_report.md",
            "outputs/data_profile.json",
            "outputs/numpy_preprocessing_demo.json",
            "outputs/visualizations/*.png",
        ],
        "rebuild_command": "python python/airline_analysis.py",
        "deployment": "GitHub Pages",
    }


if __name__ == "__main__":
    raise SystemExit(main())
