#!/bin/bash
# Setup script to push CHPower to GitHub
# Run this script, then follow the instructions

cd /Users/matthewmiles/CHPower

# Initialize git repository
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: Swiss Power Plant Scraper"

echo ""
echo "✓ Git repository initialized and files committed"
echo ""
echo "Next steps:"
echo "1. Go to https://github.com and create a new repository named 'CHPower'"
echo "2. Then run these commands:"
echo ""
echo "   git remote add origin https://github.com/YOUR_USERNAME/CHPower.git"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""
echo "Or if you already created the repo, just run:"
echo "   git remote add origin https://github.com/YOUR_USERNAME/CHPower.git"
echo "   git branch -M main"
echo "   git push -u origin main"

