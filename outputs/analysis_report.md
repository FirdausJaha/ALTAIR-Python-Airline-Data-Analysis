# ALTAIR — Airline Data Analysis

## Project summary

This report summarizes the processed airline dataset and the analytical operations performed by the Python pipeline.

## Dataset metrics

- Records analyzed: **98,619**
- Average age: **45.5**
- Median age: **46.0**
- Nationalities represented: **240**
- Departure airports represented: **9,062**
- Arrival airports represented: **9,024**
- Continents represented: **6**

## Flight status distribution

| Status | Records | Percentage |
|---|---:|---:|
| Cancelled | 32,942 | 33.40% |
| Delayed | 32,831 | 33.29% |
| On Time | 32,846 | 33.31% |

## Key insights

- **Flight status:** Cancelled is the most frequent flight status, with 32,942 of 98,619 records (33.4%).
- **Nationality:** China is the most frequently represented nationality, with 18,317 records.
- **Airport activity:** San Pedro Airport is the most frequently represented departure airport, with 43 records.
- **Time pattern:** August has the highest monthly departure count (8,544), while Sunday is the busiest weekday category (14,289).
- **Geographic distribution:** North America contains the largest number of records (32,033) among the represented continents.
- **Travel classification:** The approximate nationality-vs-airport-country classification contains 96,844 International and 1,775 Domestic records.

## Statistical interpretation

The Chi-square tests examine association between selected categorical variables and flight status. A p-value below 0.05 is treated as significant for this academic analysis. Significance does not imply causation.

## Limitation

Domestic/International is an approximate classification derived from passenger nationality and recorded airport country because the source dataset does not provide a complete itinerary-level domestic/international field.
