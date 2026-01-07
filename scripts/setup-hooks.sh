#!/bin/bash

# =============================================================================
# setup-hooks.sh: Install git hooks from scripts/hooks to .git/hooks
# =============================================================================
#
# This script copies all hook scripts from the scripts/hooks directory
# to the .git/hooks directory, making them executable.
#
# Usage:
#   ./scripts/setup-hooks.sh
#
# Run this after cloning the repository to enable:
#   - Automatic changelog file creation for new branches
# =============================================================================

# Exit immediately if any command fails
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOKS_DIR="$SCRIPT_DIR/hooks"
GIT_HOOKS_DIR="$(git rev-parse --show-toplevel)/.git/hooks"

echo "Installing git hooks..."

# Check if hooks directory exists
if [ ! -d "$HOOKS_DIR" ]; then
    echo "Error: hooks directory not found at $HOOKS_DIR"
    exit 1
fi

# Copy all hooks from scripts/hooks to .git/hooks
for hook in "$HOOKS_DIR"/*; do
    if [ -f "$hook" ]; then
        hook_name=$(basename "$hook")
        cp "$hook" "$GIT_HOOKS_DIR/$hook_name"
        chmod +x "$GIT_HOOKS_DIR/$hook_name"
        echo "  Installed: $hook_name"
    fi
done

echo "Done! Git hooks installed."
