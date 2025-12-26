#!/bin/bash
# Quick script to access CSV files

echo "=== CSV Files in output/ directory ==="
ls -lt output/*.csv | head -5

echo ""
echo "=== Most recent full dataset ==="
LATEST_FULL=$(ls -t output/CH_plants_full_*.csv | head -1)
echo "File: $LATEST_FULL"
echo ""
head -5 "$LATEST_FULL" | column -t -s,

echo ""
echo "=== Most recent valid dataset ==="
LATEST_VALID=$(ls -t output/CH_plants_valid_*.csv | head -1)
echo "File: $LATEST_VALID"
echo ""
head -5 "$LATEST_VALID" | column -t -s,

echo ""
echo "=== To view full file, use: ==="
echo "  cat $LATEST_FULL"
echo "  less $LATEST_FULL"
echo "  open $LATEST_FULL  # Opens in default app (Excel/Numbers)"

