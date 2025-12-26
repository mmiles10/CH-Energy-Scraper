# Swiss Power Plant Scraper

A Python tool to scrape power plant data from OpenInfraMap and generate CSV files for power stack analysis.

## Features

- Scrapes power plant data from OpenInfraMap's Switzerland statistics page
- Extracts plant names, operators, output capacity, energy sources, and methods
- Includes URLs to plant pages and Wikidata entries
- Cleans and processes data with robust parsing of output values
- Generates multiple CSV outputs:
  - Full dataset with all scraped data
  - Valid output data (filtered for power stack analysis)
  - Power stack summary (capacity grouped by energy source)
- Creates visualization of power stack by source
- Comprehensive logging and error handling

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. The script will automatically download ChromeDriver using webdriver-manager.

## Usage

Run the main script:
```bash
python scrape_swiss_power_plants.py
```

The script will:
1. Scrape power plant data from OpenInfraMap
2. Process and clean the data
3. Save CSV files to the `output/` directory with timestamps
4. Generate a power stack visualization

## Output Files

All output files are saved in the `output/` directory with timestamps:

- `CH_plants_full_YYYYMMDD_HHMMSS.csv` - Complete dataset with all scraped data
- `CH_plants_valid_YYYYMMDD_HHMMSS.csv` - Only plants with valid output values
- `CH_power_stack_YYYYMMDD_HHMMSS.csv` - Summary of capacity by energy source
- `CH_power_stack_YYYYMMDD_HHMMSS.png` - Visualization of power stack

## Data Columns

- **Name**: Power plant name
- **Operator**: Operating company
- **Output**: Raw output string (e.g., "1,220 MW")
- **Output_MW**: Numeric output in megawatts
- **Source**: Energy source (nuclear, hydro, solar, wind, etc.)
- **Method**: Generation method (e.g., "run-of-the-river", "water-storage")
- **plant_url**: Link to plant's OpenInfraMap page
- **wikidata_url**: Link to plant's Wikidata entry (if available)

## Power Stack Analysis

The power stack data groups plants by energy source and calculates:
- Total installed capacity per source (MW)
- Number of plants per source
- Average capacity per plant per source

This data can be used for:
- Energy mix analysis
- Capacity planning
- Renewable energy tracking
- Infrastructure mapping

## Configuration

You can modify these settings in the script:
- `headless`: Set to `False` to see the browser during scraping
- `timeout`: Maximum wait time for page loading (default: 20 seconds)
- `URL`: Change to scrape different regions or data types

## Error Handling

The script includes robust error handling:
- Timeout handling for slow page loads
- Graceful handling of missing elements
- Data validation and cleaning
- Comprehensive logging

## Requirements

- Python 3.8+
- Chrome browser (for Selenium)
- Internet connection

## License

This tool is for educational and research purposes. Please respect OpenInfraMap's terms of service and rate limits.

