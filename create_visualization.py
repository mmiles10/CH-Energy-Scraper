#!/usr/bin/env python3
"""
Create power stack visualization from existing CSV file
Usage: python create_visualization.py [csv_file_path]
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys
from pathlib import Path
from datetime import datetime

def find_latest_csv():
    """Find the most recent CSV file."""
    csv_files = list(Path("output").glob("CH_plants_full_*.csv"))
    if not csv_files:
        print("No CSV files found in output/ directory")
        return None
    return sorted(csv_files, key=lambda x: x.stat().st_mtime, reverse=True)[0]

def plot_power_stack(df, save_path=None):
    """
    Create a stacked bar chart showing power capacity by source.
    
    Args:
        df: DataFrame with Output_MW and Source columns
        save_path: Optional path to save the plot
    """
    # Filter to rows with valid output
    df_valid = df.dropna(subset=["Output_MW"]).copy()
    
    if len(df_valid) == 0:
        print("WARNING: No valid data for plotting")
        return
    
    # Calculate capacity by source
    capacity_by_source = (
        df_valid.groupby("Source")["Output_MW"]
        .sum()
        .sort_values(ascending=False)
    )
    
    if len(capacity_by_source) == 0:
        print("WARNING: No capacity data to plot")
        return
    
    print(f"\nCapacity by source (MW):")
    print(capacity_by_source.to_string())
    print(f"\nTotal capacity: {capacity_by_source.sum():,.0f} MW")
    
    # Create plot
    fig, ax = plt.subplots(figsize=(12, 6))
    
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
        print(f"\n✓ Plot saved to {save_path}")
    
    plt.show()

def main():
    """Main execution function."""
    # Get CSV file path
    if len(sys.argv) > 1:
        csv_path = Path(sys.argv[1])
        if not csv_path.exists():
            print(f"Error: File not found: {csv_path}")
            return
    else:
        csv_path = find_latest_csv()
        if csv_path is None:
            return
        print(f"Using most recent CSV: {csv_path}")
    
    # Load the CSV
    print(f"\nLoading CSV: {csv_path}")
    try:
        df = pd.read_csv(csv_path)
        print(f"Loaded {len(df)} rows")
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return
    
    # Check required columns
    if "Output_MW" not in df.columns:
        print("Error: CSV file missing 'Output_MW' column")
        print(f"Available columns: {list(df.columns)}")
        return
    
    if "Source" not in df.columns:
        print("Error: CSV file missing 'Source' column")
        print(f"Available columns: {list(df.columns)}")
        return
    
    # Generate timestamp for output filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    plot_path = output_dir / f"CH_power_stack_{timestamp}.png"
    
    # Create visualization
    print("\nCreating visualization...")
    plot_power_stack(df, save_path=plot_path)
    
    print(f"\n✓ Done! Visualization saved to: {plot_path}")

if __name__ == "__main__":
    main()

