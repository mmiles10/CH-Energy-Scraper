# Swiss Power Plant Scraper

A scraper for Swiss power plant data from OpenInfraMap. It collects plant-level information, cleans the results, and produces files that can be used for capacity and generation mix analysis.

## Overview

The project pulls data from the Switzerland statistics page on OpenInfraMap and converts it into a more usable dataset. The outputs are intended for energy mix analysis, infrastructure review, and simple charting.

## Outputs

The script produces:

- a full plant-level dataset
- a filtered dataset with valid output values
- a capacity summary grouped by source
- a chart of installed capacity by source

## Data Fields

The dataset includes fields such as:

- plant name
- operator
- output
- output in MW
- energy source
- generation method
- plant URL
- Wikidata URL

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Make sure Chrome is available for Selenium.

## Usage

Run:

```bash
python scrape_swiss_power_plants.py
```

Supporting shell utilities are kept in the `scripts/` folder. A local spreadsheet export is stored in `artifacts/`.

## Notes

This repository is meant for research and analysis. Please respect the source site's terms and rate limits.
