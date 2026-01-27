#!/bin/bash
# Script to push changes to GitHub

cd /Users/abu/Documents/DN/Test

echo "Pushing to GitHub..."
git push origin main

if [ $? -eq 0 ]; then
    echo "✅ Successfully pushed to GitHub!"
    echo "GitHub Actions will now deploy automatically."
else
    echo "❌ Push failed. Please check your network connection and try again."
    exit 1
fi
