#!/bin/bash
# Quick Git Workflow Script for Error Handling Refactor
# Copy and paste these commands into your terminal

echo "🚀 Starting Git workflow for error-handling-refactor"
echo ""

# Step 1: Verify current state
echo "Step 1: Checking current state..."
git status
git branch
echo ""
read -p "Are you on the main branch with a clean state? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "❌ Please commit or stash changes and ensure you're on main branch"
    exit 1
fi

# Step 2: Create new branch
echo "Step 2: Creating error-handling-refactor branch..."
git checkout -b error-handling-refactor
echo "✅ Branch created"
echo ""

# Step 3: Copy files (YOU NEED TO ADJUST THESE PATHS)
echo "Step 3: Copying improved files..."
echo "⚠️  IMPORTANT: Adjust the source paths below to match where you saved the files"
echo ""
echo "Example commands:"
echo "  cp /path/to/downloads/telegram_harvester.py telegram-reader/"
echo "  cp /path/to/downloads/FileOrderBridge.cs ninjatrader-strategy/"
echo "  cp /path/to/downloads/trade_bridge.py mpc-server/plugins/"
echo "  cp /path/to/downloads/logger.py mpc-server/plugins/"
echo "  cp /path/to/downloads/*.md docs/"
echo ""
read -p "Have you copied all the improved files? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "❌ Please copy the improved files first"
    exit 1
fi

# Step 4: Stage changes
echo "Step 4: Staging changes..."
git add telegram-reader/telegram_harvester.py
git add ninjatrader-strategy/FileOrderBridge.cs
git add mpc-server/plugins/trade_bridge.py
git add mpc-server/plugins/logger.py
git add docs/
echo "✅ Files staged"
echo ""

# Step 5: Show what will be committed
echo "Step 5: Reviewing changes to be committed..."
git status
echo ""
read -p "Do these changes look correct? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "❌ Cancelling. Use 'git reset HEAD' to unstage changes"
    exit 1
fi

# Step 6: Commit
echo "Step 6: Committing changes..."
git commit -m "feat: Add robust error handling to all file operations

- Added comprehensive try-catch blocks around all I/O operations
- Implemented atomic file writes (temp file + rename pattern)
- Added structured logging with rotating file handlers
- Validated all input data before processing
- Enhanced error recovery with retry logic and cleanup
- Added graceful degradation for non-critical failures

Files modified:
- telegram-reader/telegram_harvester.py (~150 lines)
- ninjatrader-strategy/FileOrderBridge.cs (~200 lines)
- mpc-server/plugins/trade_bridge.py (~120 lines)
- mpc-server/plugins/logger.py (~60 lines)

Added documentation:
- docs/README.md
- docs/QUICK_REFERENCE.md
- docs/IMPLEMENTATION_SUMMARY.md
- docs/DEPLOYMENT_COMPLETE.md
- docs/ERROR_HANDLING_IMPROVEMENTS.md
- docs/signal_trader_health_check.md
- docs/GIT_WORKFLOW_GUIDE.md

Benefits:
- Atomic file operations prevent partial writes
- Retry logic handles transient file locks
- All errors logged with context and stack traces
- System continues running even when errors occur
- No silent failures

Testing: Tested on development environment with paper account"

echo "✅ Committed"
echo ""

# Step 7: Push to GitHub
echo "Step 7: Pushing to GitHub..."
git push -u origin error-handling-refactor
echo "✅ Pushed to GitHub"
echo ""

# Step 8: Instructions for PR
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 SUCCESS! Branch pushed to GitHub"
echo ""
echo "Next steps:"
echo "1. Go to your repository on GitHub"
echo "2. Click 'Compare & pull request'"
echo "3. Review the changes"
echo "4. Click 'Create pull request'"
echo "5. Review and click 'Merge pull request'"
echo "6. Come back here and run the following commands:"
echo ""
echo "   git checkout main"
echo "   git pull origin main"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
