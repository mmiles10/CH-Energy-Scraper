#!/bin/bash
# Create power stack visualization from CSV

# Find most recent CSV file
CSV_FILE=$(ls -t output/CH_plants_full_*.csv 2>/dev/null | head -1)

if [ -z "$CSV_FILE" ]; then
    echo "Error: No CSV files found in output/ directory"
    exit 1
fi

echo "Using CSV: $CSV_FILE"
echo "Creating visualization..."

# Run Python script to create visualization
python3 create_visualization.py "$CSV_FILE"

