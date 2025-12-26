"""
Swiss Power Plant Scraper
==========================
Scrapes power plant data from OpenInfraMap and exports to CSV for power stack analysis.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import logging
import re
from typing import Optional, Dict, List
from pathlib import Path
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

URL = "https://openinframap.org/stats/area/Switzerland/plants"
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)


def setup_driver(headless: bool = True) -> webdriver.Chrome:
    """
    Set up and return a Chrome WebDriver instance.
    
    Args:
        headless: Whether to run browser in headless mode
        
    Returns:
        Configured Chrome WebDriver
    """
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options,
    )
    return driver


def extract_numeric_mw(output_str: str) -> Optional[float]:
    """
    Extract numeric MW value from output string.
    
    Handles formats like:
    - "1,220 MW"
    - "21.00 MW"
    - "1,234.56 MW"
    - "500 kW" (converts to MW)
    - "1.5 GW" (converts to MW)
    - "." or empty strings
    - Values with various separators and formats
    
    Args:
        output_str: String containing output value
        
    Returns:
        Numeric MW value or None if not parseable
    """
    # Handle NaN, None, or empty values
    if pd.isna(output_str) or output_str is None:
        return None
    
    output_str = str(output_str).strip()
    
    # Handle empty strings, dots, dashes, or other placeholders
    if output_str == "" or output_str == "." or output_str == "-" or output_str == "—":
        return None
    
    # Normalize the string - remove extra whitespace
    output_str = re.sub(r'\s+', ' ', output_str)
    
    # Try to extract number and unit
    # Pattern 1: Number with optional commas/dots, followed by optional unit (MW, kW, GW, etc.)
    # This handles: "1,220 MW", "1,220 mw", "500 kW", "1.5 GW", "1220", etc.
    # Make unit matching more flexible - match any whitespace and optional unit
    pattern = r'([\d\.,]+)\s*(?:m?w|kw|gw|wh)?'
    match = re.search(pattern, output_str, re.IGNORECASE)
    
    if not match:
        # Pattern 2: Just try to find any number in the string (fallback)
        match = re.search(r'([\d\.,]+)', output_str)
        if not match:
            return None
    
    numeric_str = match.group(1)
    
    # Remove thousands separators (commas)
    numeric_str = numeric_str.replace(",", "").strip()
    
    # Handle cases where dot might be thousands separator (European format)
    # e.g., "1.220" could be 1220 or 1.22
    # We'll assume if there's a dot and it's followed by 3 digits, it's thousands separator
    if '.' in numeric_str:
        parts = numeric_str.split('.')
        if len(parts) == 2 and len(parts[1]) == 3:
            # Likely thousands separator (e.g., "1.220")
            numeric_str = parts[0] + parts[1]
        # Otherwise treat as decimal
    
    try:
        value = float(numeric_str)
    except ValueError:
        return None
    
    # Detect and convert unit to MW
    output_lower = output_str.lower()
    if 'kw' in output_lower or 'kwh' in output_lower:
        # Convert kW to MW
        value = value / 1000.0
    elif 'gw' in output_lower or 'gwh' in output_lower:
        # Convert GW to MW
        value = value * 1000.0
    elif 'w' in output_lower and 'mw' not in output_lower and 'kw' not in output_lower and 'gw' not in output_lower:
        # Just "W" (watts) - convert to MW
        value = value / 1000000.0
    # If MW is explicitly mentioned or no unit, assume it's already in MW
    
    return value


def scrape_switzerland_plants(headless: bool = True, timeout: int = 20) -> pd.DataFrame:
    """
    Scrape the OpenInfraMap Switzerland 'Power Plants' stats table
    and return a pandas DataFrame with all columns from the table
    plus plant_url + wikidata_url.
    
    Args:
        headless: Whether to run browser in headless mode
        timeout: Maximum time to wait for table to load (seconds)
        
    Returns:
        DataFrame with power plant data
    """
    driver = None
    try:
        logger.info(f"Setting up Chrome driver (headless={headless})...")
        driver = setup_driver(headless=headless)
        
        logger.info(f"Loading URL: {URL}")
        driver.get(URL)
        
        # Wait until the table appears
        logger.info("Waiting for table to load...")
        try:
            table = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table"))
            )
        except TimeoutException:
            logger.error(f"Table did not load within {timeout} seconds")
            raise
        
        logger.info("Table loaded successfully")
        
        # --------------------
        # 1. Grab column names
        # --------------------
        header_cells = table.find_elements(By.CSS_SELECTOR, "thead tr th")
        headers = [h.text.strip() for h in header_cells]
        
        # Give empty headers fallback names
        headers = [
            (name if name != "" else f"col_{i}")
            for i, name in enumerate(headers)
        ]
        
        logger.info(f"Found {len(headers)} columns: {headers}")
        
        rows_data = []
        
        # -------------------
        # 2. Grab each row
        # -------------------
        rows = table.find_elements(By.CSS_SELECTOR, "tbody tr")
        logger.info(f"Found {len(rows)} rows to process")
        
        for idx, tr in enumerate(rows):
            try:
                tds = tr.find_elements(By.TAG_NAME, "td")
                if not tds:
                    continue
                
                # Text content for each cell - get both text and inner HTML for better data extraction
                values = []
                for td in tds:
                    # Try to get text, but also check for inner text which might have better formatting
                    cell_text = td.text.strip()
                    # Sometimes the actual value is in a child element or has special formatting
                    # Try to get the innerHTML or textContent
                    try:
                        # Check if there are any child elements with the actual value
                        child_elements = td.find_elements(By.XPATH, ".//*")
                        if child_elements:
                            # Sometimes the number is in a span or other element
                            for child in child_elements:
                                child_text = child.text.strip()
                                if child_text and re.search(r'\d', child_text):
                                    cell_text = child_text
                                    break
                    except:
                        pass
                    values.append(cell_text)
                
                # Map values to headers
                if len(values) == len(headers):
                    record = dict(zip(headers, values))
                else:
                    # Handle mismatch by creating generic column names
                    record = {f"col_{i}": v for i, v in enumerate(values)}
                    if idx < 3:  # Only log first few mismatches to avoid spam
                        logger.warning(
                            f"Row {idx}: Column count mismatch "
                            f"(expected {len(headers)}, got {len(values)})"
                        )
                
                # 3. Add URLs
                # plant page URL (first cell's link)
                try:
                    name_link = tds[0].find_element(By.TAG_NAME, "a")
                    record["plant_url"] = name_link.get_attribute("href")
                except (NoSuchElementException, Exception) as e:
                    record["plant_url"] = None
                
                # wikidata URL (last cell's link, if present)
                try:
                    wiki_links = tds[-1].find_elements(By.TAG_NAME, "a")
                    record["wikidata_url"] = (
                        wiki_links[0].get_attribute("href") if wiki_links else None
                    )
                except (NoSuchElementException, Exception) as e:
                    record["wikidata_url"] = None
                
                rows_data.append(record)
                
            except Exception as e:
                logger.warning(f"Error processing row {idx}: {e}")
                continue
        
        df = pd.DataFrame(rows_data)
        logger.info(f"Successfully scraped {len(df)} power plants")
        
        # Log sample of first row for debugging
        if len(df) > 0:
            logger.info(f"Sample first row data: {df.iloc[0].to_dict()}")
            # Try to identify which column likely contains output data
            for col in df.columns:
                sample_values = df[col].head(5).tolist()
                # Check if column contains numbers with units (likely output)
                has_power_units = any(
                    re.search(r'\d+.*(MW|kW|GW|W)', str(v), re.IGNORECASE) 
                    for v in sample_values if pd.notna(v)
                )
                if has_power_units:
                    logger.info(f"Column '{col}' appears to contain output data: {sample_values}")
        
        return df
        
    except Exception as e:
        logger.error(f"Error during scraping: {e}")
        raise
    finally:
        if driver:
            driver.quit()
            logger.info("Browser closed")


def clean_and_process_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and process the scraped data.
    
    Args:
        df: Raw scraped DataFrame
        
    Returns:
        Cleaned and processed DataFrame
    """
    df = df.copy()
    
    # First, try to identify columns by their content patterns
    # This helps if column order is different than expected
    
    # Try to find Output column by content (contains numbers with MW/kW/GW)
    output_col = None
    for col in df.columns:
        if 'output' in col.lower() or 'power' in col.lower() or 'capacity' in col.lower():
            output_col = col
            break
        # Check if column contains power unit patterns
        sample = df[col].dropna().head(10)
        if len(sample) > 0:
            has_power_units = sum(
                1 for v in sample 
                if re.search(r'\d+.*(MW|kW|GW|W)', str(v), re.IGNORECASE)
            )
            if has_power_units >= len(sample) * 0.5:  # At least 50% match
                output_col = col
                logger.info(f"Auto-detected Output column: '{col}'")
                break
    
    # First, detect which column has power values BEFORE renaming
    # This way we don't accidentally rename the power column to "Source"
    power_col_before_rename = output_col  # This was detected earlier
    
    # Rename generic columns to meaningful names
    # But if col_3 has power values, don't rename it to Source
    rename_map = {
        "col_0": "Name",
        "col_1": "Operator", 
        "col_2": "Operator_Name",  # Usually operator name, not power
    }
    
    # Handle col_3 and col_4 based on what they actually contain
    if power_col_before_rename == "col_3":
        # col_3 has power values, col_4 has energy source type
        rename_map["col_3"] = "Power_Output"  # Temporary name
        rename_map["col_4"] = "Source"  # This is the actual energy source
        rename_map["col_5"] = "Method"
    else:
        # Standard mapping (if power is elsewhere)
        rename_map["col_3"] = "Source"
        rename_map["col_4"] = "Method"
    
    # Only rename columns that exist
    rename_map = {k: v for k, v in rename_map.items() if k in df.columns}
    df = df.rename(columns=rename_map)
    
    # Find the actual column containing power output values after renaming
    logger.info("Searching for column with power output values...")
    power_output_col = None
    
    # Check Power_Output first (if we renamed col_3 to this)
    if "Power_Output" in df.columns:
        power_output_col = "Power_Output"
        logger.info("Found power values in 'Power_Output' column")
    else:
        # Check all columns for power unit patterns
        for col in df.columns:
            if col in ["Output_MW", "Source", "Name", "Operator"]:
                continue
            sample = df[col].dropna().head(20)
            if len(sample) > 0:
                has_power_units = sum(
                    1 for v in sample 
                    if isinstance(v, str) and re.search(r'\d+.*(MW|kW|GW|mw|kw|gw)', str(v), re.IGNORECASE)
                )
                if has_power_units >= len(sample) * 0.3:  # At least 30% match
                    power_output_col = col
                    logger.info(f"Found power values in '{col}' column ({has_power_units}/{len(sample)} matches)")
                    break
    
    # Use the detected column for power output extraction
    if power_output_col:
        logger.info(f"Using '{power_output_col}' column for power output extraction")
        # Store the raw power values (e.g., "1,220 mw")
        df["Output_Raw"] = df[power_output_col].copy()
        # Extract numeric MW values (e.g., 1220.0)
        df["Output_MW"] = df["Output_Raw"].apply(extract_numeric_mw)
        
        # Remove redundant columns - drop the original power column since we have Output_Raw
        cols_to_drop = []
        if power_output_col in df.columns and power_output_col != "Output_Raw":
            # Drop the original column since we have Output_Raw
            cols_to_drop.append(power_output_col)
        
        # Remove duplicates (but keep Source - that's the energy type!)
        for col in cols_to_drop:
            if col in df.columns and col != "Source":  # Never drop Source!
                df = df.drop(columns=[col])
                logger.info(f"Dropped redundant column: {col}")
                
    elif "Output" in df.columns:
        # Output column exists - use it
        df["Output_Raw"] = df["Output"].copy()
        df["Output_MW"] = df["Output"].apply(extract_numeric_mw)
        # Drop the original Output since we have Output_Raw
        if "Output" in df.columns:
            df = df.drop(columns=["Output"])
    else:
        logger.warning("Could not find column with power output values!")
        df["Output_MW"] = None
        return df
    
    # Debug: Show sample of values
    if "Output_Raw" in df.columns:
        sample_outputs = df["Output_Raw"].head(10).tolist()
        logger.info(f"Sample Output_Raw values: {sample_outputs}")
    
    # Log statistics with more detail
    non_null_count = df["Output_MW"].notna().sum()
    null_count = df["Output_MW"].isna().sum()
    logger.info(f"Successfully parsed {non_null_count} out of {len(df)} output values")
    logger.info(f"Failed to parse {null_count} values")
    
    # Show examples of failed extractions for debugging
    if null_count > 0:
        failed_df = df[df["Output_MW"].isna()].copy()
        if len(failed_df) > 0:
            # Show all columns for failed rows to help debug
            cols_to_show = ["Name"] if "Name" in failed_df.columns else []
            if "Output" in failed_df.columns:
                cols_to_show.append("Output")
            # Add a few other columns for context
            for col in ["col_0", "col_1", "col_2", "col_3", "col_4", "Source", "Operator"]:
                if col in failed_df.columns and col not in cols_to_show:
                    cols_to_show.append(col)
            
            failed_samples = failed_df[cols_to_show].head(10)
            logger.warning(f"Sample failed extractions (showing {len(failed_samples)} of {len(failed_df)}):")
            logger.warning(f"\n{failed_samples.to_string()}")
            
            # Show unique Output values that failed
            if "Output" in failed_df.columns:
                unique_failed = failed_df["Output"].value_counts().head(10)
                logger.warning(f"Most common failed Output values:\n{unique_failed.to_string()}")
    
    # Clean Source column (standardize capitalization)
    if "Source" in df.columns:
        df["Source"] = df["Source"].str.strip().str.lower()
    
    # Clean Method column
    if "Method" in df.columns:
        df["Method"] = df["Method"].str.strip()
    
    # Clean Name and Operator
    if "Name" in df.columns:
        df["Name"] = df["Name"].str.strip()
    if "Operator" in df.columns:
        df["Operator"] = df["Operator"].str.strip()
    
    return df


def generate_power_stack_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate power stack data grouped by source.
    
    Args:
        df: DataFrame with Output_MW column
        
    Returns:
        DataFrame with capacity by source
    """
    # Filter to rows with valid output
    df_valid = df.dropna(subset=["Output_MW"]).copy()
    
    if len(df_valid) == 0:
        logger.warning("No valid output data found for power stack")
        return pd.DataFrame()
    
    # Group by source and sum capacity
    capacity_by_source = (
        df_valid.groupby("Source")["Output_MW"]
        .agg(["sum", "count", "mean"])
        .round(2)
    )
    capacity_by_source.columns = ["Total_MW", "Plant_Count", "Avg_MW"]
    capacity_by_source = capacity_by_source.sort_values("Total_MW", ascending=False)
    
    logger.info(f"\nCapacity by source (MW):")
    logger.info(f"\n{capacity_by_source.to_string()}")
    
    return capacity_by_source


def plot_power_stack(df: pd.DataFrame, save_path: Optional[Path] = None):
    """
    Create a stacked bar chart showing power capacity by source.
    
    Args:
        df: DataFrame with Output_MW and Source columns
        save_path: Optional path to save the plot
    """
    # Filter to rows with valid output
    df_valid = df.dropna(subset=["Output_MW"]).copy()
    
    if len(df_valid) == 0:
        logger.warning("No valid data for plotting")
        return
    
    # Calculate capacity by source
    capacity_by_source = (
        df_valid.groupby("Source")["Output_MW"]
        .sum()
        .sort_values(ascending=False)
    )
    
    if len(capacity_by_source) == 0:
        logger.warning("No capacity data to plot")
        return
    
    # Create plot
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Color palette for different sources
    colors = plt.cm.Set3(np.linspace(0, 1, len(capacity_by_source)))
    
    bottom = 0.0
    for (source, cap), color in zip(capacity_by_source.items(), colors):
        ax.bar(
            "Switzerland",
            cap,
            bottom=bottom,
            label=f"{source.title()} ({cap:,.0f} MW)",
            color=color,
        )
        bottom += cap
    
    ax.set_ylabel("Installed Capacity (MW)", fontsize=12)
    ax.set_title("Switzerland Power Stack by Source", fontsize=14, fontweight="bold")
    ax.legend(title="Source", bbox_to_anchor=(1.05, 1), loc="upper left", fontsize=9)
    
    # Add total capacity annotation
    total_capacity = capacity_by_source.sum()
    ax.text(
        0, total_capacity * 1.02,
        f"Total: {total_capacity:,.0f} MW",
        ha="center",
        fontsize=10,
        fontweight="bold"
    )
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        logger.info(f"Plot saved to {save_path}")
    
    plt.show()


def main():
    """Main execution function."""
    try:
        # Scrape data
        df = scrape_switzerland_plants(headless=True)
        
        if df.empty:
            logger.error("No data scraped!")
            return
        
        # Clean and process
        df_cleaned = clean_and_process_data(df)
        
        # Generate timestamp for filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save full dataset FIRST (before visualization)
        csv_path = OUTPUT_DIR / f"CH_plants_full_{timestamp}.csv"
        df_cleaned.to_csv(csv_path, index=False, encoding="utf-8")
        logger.info(f"Full dataset saved to {csv_path}")
        print(f"\n✓ CSV saved: {csv_path}")
        
        # Save only valid output data (for power stack)
        df_valid = df_cleaned.dropna(subset=["Output_MW"])
        csv_valid_path = OUTPUT_DIR / f"CH_plants_valid_{timestamp}.csv"
        df_valid.to_csv(csv_valid_path, index=False, encoding="utf-8")
        logger.info(f"Valid output data saved to {csv_valid_path}")
        print(f"✓ Valid data CSV saved: {csv_valid_path}")
        
        # Generate power stack summary
        power_stack_df = generate_power_stack_data(df_cleaned)
        if not power_stack_df.empty:
            stack_csv_path = OUTPUT_DIR / f"CH_power_stack_{timestamp}.csv"
            power_stack_df.to_csv(stack_csv_path, encoding="utf-8")
            logger.info(f"Power stack summary saved to {stack_csv_path}")
        
        # Display summary
        print("\n" + "="*60)
        print("SCRAPING SUMMARY")
        print("="*60)
        print(f"Total plants scraped: {len(df_cleaned)}")
        print(f"Plants with valid output: {len(df_valid)}")
        print(f"\nColumns: {list(df_cleaned.columns)}")
        
        # Show Output column statistics
        if "Output" in df_cleaned.columns:
            print(f"\nOutput column statistics:")
            print(f"  - Non-null values: {df_cleaned['Output'].notna().sum()}")
            print(f"  - Unique values: {df_cleaned['Output'].nunique()}")
            print(f"  - Sample values: {df_cleaned['Output'].head(10).tolist()}")
        
        if "Output_MW" in df_cleaned.columns:
            print(f"\nOutput_MW column statistics:")
            print(f"  - Non-null values: {df_cleaned['Output_MW'].notna().sum()}")
            if df_cleaned['Output_MW'].notna().sum() > 0:
                print(f"  - Min: {df_cleaned['Output_MW'].min():.2f} MW")
                print(f"  - Max: {df_cleaned['Output_MW'].max():.2f} MW")
                print(f"  - Mean: {df_cleaned['Output_MW'].mean():.2f} MW")
                print(f"  - Total: {df_cleaned['Output_MW'].sum():.2f} MW")
        
        # Print full CSV data to console BEFORE visualization
        print("\n" + "="*60)
        print("FULL DATASET (CSV Preview)")
        print("="*60)
        print(f"\nCSV saved to: {csv_path}")
        print(f"\nFull dataset preview (all columns):")
        print(df_cleaned.to_string())
        
        print("\n" + "="*60)
        print("KEY COLUMNS PREVIEW")
        print("="*60)
        display_cols = ["Name", "Output", "Output_MW", "Source"]
        display_cols = [c for c in display_cols if c in df_cleaned.columns]
        print(f"\nFirst 20 rows with key columns:")
        print(df_cleaned[display_cols].head(20).to_string())
        
        # Only create visualization if we have valid data
        if len(df_valid) > 0:
            print("\n" + "="*60)
            print("CREATING VISUALIZATION")
            print("="*60)
            plot_path = OUTPUT_DIR / f"CH_power_stack_{timestamp}.png"
            plot_power_stack(df_cleaned, save_path=plot_path)
        else:
            print("\n" + "="*60)
            print("WARNING: NO VALID OUTPUT DATA FOR VISUALIZATION")
            print("="*60)
            print("Skipping visualization because all Output_MW values are NaN.")
            print("Please check the CSV files to see the raw data and debug the extraction.")
            print(f"\nCSV files saved:")
            print(f"  - Full data: {csv_path}")
            print(f"  - Valid data: {csv_valid_path} (empty - no valid outputs)")
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()

