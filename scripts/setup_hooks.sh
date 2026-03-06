#!/bin/bash
# Set up git hooks for the my-skills repository.
# Uses core.hooksPath so the tracked scripts/hooks/ directory is used directly.
# Run once after cloning: bash scripts/setup_hooks.sh

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

git -C "$REPO_ROOT" config core.hooksPath scripts/hooks
echo "Git hooks configured: core.hooksPath = scripts/hooks"
echo "Pre-push hook will auto-update changed skills on git push."
echo "Skip with: git push --no-verify"
