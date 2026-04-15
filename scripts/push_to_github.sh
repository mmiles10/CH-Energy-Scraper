#!/bin/bash
# Push CHPower to GitHub repository

cd /Users/matthewmiles/CHPower

echo "Initializing git repository..."
git init

echo "Adding remote repository..."
git remote add origin https://github.com/mmiles10/CH-Power-Plant-Scraper-.git 2>/dev/null || git remote set-url origin https://github.com/mmiles10/CH-Power-Plant-Scraper-.git

echo "Adding all files..."
git add .

echo "Creating commit..."
git commit -m "Initial commit: Swiss Power Plant Scraper with CSV export and visualization"

echo "Setting main branch..."
git branch -M main

echo "Pushing to GitHub..."
git push -u origin main

echo ""
echo "✓ Done! Your code has been pushed to GitHub"
echo "Repository: https://github.com/mmiles10/CH-Power-Plant-Scraper-"

