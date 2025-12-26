#!/usr/bin/env python3
"""
Quick CSV search tool for Swiss Power Plant data
Usage: python search_csv.py [search_term] [column_name]
"""

import pandas as pd
import sys
from pathlib import Path

def find_latest_csv():
    """Find the most recent CSV file."""
    csv_files = list(Path("output").glob("CH_plants_full_*.csv"))
    if not csv_files:
        print("No CSV files found in output/ directory")
        return None
    return sorted(csv_files, key=lambda x: x.stat().st_mtime, reverse=True)[0]

def search_csv(search_term=None, column=None, csv_path=None):
    """Search through the CSV file."""
    if csv_path is None:
        csv_path = find_latest_csv()
        if csv_path is None:
            return
    
    print(f"Loading: {csv_path}")
    df = pd.read_csv(csv_path)
    
    print(f"\nTotal rows: {len(df)}")
    print(f"Columns: {', '.join(df.columns)}")
    
    if search_term:
        search_term = search_term.lower()
        
        if column and column in df.columns:
            # Search in specific column
            mask = df[column].astype(str).str.lower().str.contains(search_term, na=False)
            results = df[mask]
            print(f"\nSearching for '{search_term}' in column '{column}':")
            print(f"Found {len(results)} matches")
        else:
            # Search in all columns
            mask = df.astype(str).apply(lambda x: x.str.lower().str.contains(search_term, na=False)).any(axis=1)
            results = df[mask]
            print(f"\nSearching for '{search_term}' in all columns:")
            print(f"Found {len(results)} matches")
        
        if len(results) > 0:
            # Show key columns
            display_cols = ["Name", "Output", "Output_MW", "Source", "Operator"]
            display_cols = [c for c in display_cols if c in results.columns]
            print(f"\nResults (showing {len(results)} rows):")
            print(results[display_cols].to_string())
        else:
            print("No matches found")
    else:
        # Show summary statistics
        print("\n" + "="*60)
        print("SUMMARY STATISTICS")
        print("="*60)
        
        if "Output_MW" in df.columns:
            valid_outputs = df[df["Output_MW"].notna()]
            print(f"\nPlants with valid output: {len(valid_outputs)}")
            if len(valid_outputs) > 0:
                print(f"Total capacity: {valid_outputs['Output_MW'].sum():,.2f} MW")
                print(f"Average capacity: {valid_outputs['Output_MW'].mean():.2f} MW")
                print(f"Min capacity: {valid_outputs['Output_MW'].min():.2f} MW")
                print(f"Max capacity: {valid_outputs['Output_MW'].max():.2f} MW")
        
        if "Source" in df.columns:
            print(f"\nBy Source:")
            source_counts = df["Source"].value_counts()
            print(source_counts.to_string())
        
        print("\n" + "="*60)
        print("FIRST 10 ROWS")
        print("="*60)
        display_cols = ["Name", "Output", "Output_MW", "Source"]
        display_cols = [c for c in display_cols if c in df.columns]
        print(df[display_cols].head(10).to_string())

if __name__ == "__main__":
    search_term = sys.argv[1] if len(sys.argv) > 1 else None
    column = sys.argv[2] if len(sys.argv) > 2 else None
    
    if len(sys.argv) > 1 and sys.argv[1] in ["-h", "--help"]:
        print("""
Usage: python search_csv.py [search_term] [column_name]

Examples:
  python search_csv.py                    # Show summary and first 10 rows
  python search_csv.py nuclear             # Search for 'nuclear' in all columns
  python search_csv.py hydro Source        # Search for 'hydro' in Source column
  python search_csv.py Leibstadt Name      # Search for 'Leibstadt' in Name column
  python search_csv.py 1000 Output        # Search for '1000' in Output column
        """)
        sys.exit(0)
    
    search_csv(search_term, column)

