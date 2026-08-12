#!/bin/bash

# ============================================================
# Wedding Planner - Push Project to GitHub
# Repository: git@github.com:ngangu63/weddingPlanner.git
# ============================================================

set -e

echo "🚀 Starting GitHub deployment..."

# Check that we're inside a Git project
if [ -d ".git" ]; then
    echo "Git repository already initialized."
else
    echo "Initializing Git repository..."
    git init
fi

# Check README exists
if [ ! -f "README.md" ]; then
    echo "❌ README.md not found."
    echo "Please run this script from the weddingPlanner project directory."
    exit 1
fi

# Add README
echo "📄 Adding README.md..."
git add README.md

# Commit
echo "📝 Creating commit..."
git commit -m "first commit" || echo "Nothing new to commit."

# Set main branch
echo "🌿 Setting main branch..."
git branch -M main

# Add remote if it doesn't already exist
if git remote get-url origin >/dev/null 2>&1; then
    echo "🔗 Remote 'origin' already exists:"
    git remote get-url origin
else
    echo "🔗 Adding GitHub remote..."
    git remote add origin git@github.com:ngangu63/weddingPlanner.git
fi

# Push
echo "⬆️ Pushing project to GitHub..."
git push -u origin main

echo ""
echo "✅ Project successfully pushed to GitHub!"
echo "🔗 Repository: https://github.com/ngangu63/weddingPlanner"