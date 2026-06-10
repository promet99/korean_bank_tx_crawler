#!/bin/sh
# Install repo git hooks (pre-commit, etc.) into .git/hooks.
# Run this once after cloning: ./scripts/install-hooks.sh

set -e
repo_root=$(git rev-parse --show-toplevel)
cp "$repo_root/hooks/pre-commit" "$repo_root/.git/hooks/pre-commit"
chmod +x "$repo_root/.git/hooks/pre-commit"
echo "Installed pre-commit hook."
