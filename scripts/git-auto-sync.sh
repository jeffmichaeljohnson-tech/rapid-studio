#!/bin/bash
# Git auto-commit and push script for Rapid Studio
# Runs every 5 minutes via launchd

set -e

PROJECT_DIR="/Users/computer/rapid-studio-1"
LOG_FILE="$PROJECT_DIR/.git-auto-sync.log"

cd "$PROJECT_DIR"

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "Starting auto-sync check..."

# Check if there are any changes
if [[ -z $(git status -s) ]]; then
    log "No changes detected. Skipping sync."
    exit 0
fi

log "Changes detected:"
git status -s | tee -a "$LOG_FILE"

# Stage all changes
git add -A
log "Staged all changes"

# Create commit with timestamp
COMMIT_MSG="Auto-sync: $(date '+%Y-%m-%d %H:%M:%S')"
git commit -m "$COMMIT_MSG" || {
    log "Commit failed or nothing to commit"
    exit 0
}
log "Created commit: $COMMIT_MSG"

# Push to remote
BRANCH=$(git rev-parse --abbrev-ref HEAD)
git push origin "$BRANCH" 2>&1 | tee -a "$LOG_FILE"
log "Pushed to origin/$BRANCH"

log "Auto-sync completed successfully"
