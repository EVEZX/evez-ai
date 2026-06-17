#!/usr/bin/env bash
set -euo pipefail

# Assumes you have a GitHub token in the environment variable GITHUB_TOKEN
# and that you want to push this OpenClaw workspace to a new repo.

if [ -z "${GITHUB_TOKEN:-}" ]; then
  echo "Error: GITHUB_TOKEN not set. Export it before running this script."
  exit 1
fi

REPO_NAME="evez-claw"
ORG="${GITHUB_USER:-your-github-username}"

# Create repository via GitHub API
echo "Creating GitHub repository $ORG/$REPO_NAME..."
curl -X POST -H "Authorization: token $GITHUB_TOKEN" \
     -d "{\"name\": \"$REPO_NAME\", \"private\": false}" \
     https://api.github.com/user/repos

# Initialize git repo if not already
if [ ! -d ".git" ]; then
  git init
  git add .
  git commit -m "Initial commit of OpenClaw workspace"
fi

# Add remote and push
git remote add origin https://github.com/$ORG/$REPO_NAME.git
git branch -M main
git push -u origin main

echo "Push complete. Repository available at https://github.com/$ORG/$REPO_NAME"
