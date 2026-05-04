#!/usr/bin/env bash
# Checks for a new JMdict release, downloads it if available, rewrites git
# history to remove old compact dictionary blobs, rebuilds the compact
# dictionary, and prompts before force-pushing to origin/main.
#
# Usage:
#   scripts/update_jmdict_and_compact_repo.sh [-f|--force]
#
#   -f, --force  Re-download even if the zip for the latest release is already present
#
# Prerequisites: git-filter-repo, curl, unzip, uv
#
# The downloaded jmdict-eng-*.json.zip is kept in the working directory as the
# source for compact_jmdict.py. Re-running the script skips the download if the
# zip for the latest release is already present (use --force to override).
set -euo pipefail

force=false
[[ "${1:-}" == "--force" || "${1:-}" == "-f" ]] && force=true

# ── Check for newer JMdict release ───────────────────────────────────────────
current=$(find . -maxdepth 1 -name 'jmdict-eng-*.json.zip' | sort -V | tail -1 | grep -oP '\d+\.\d+\.\d+' || true)
[[ -z "$current" ]] && current="0.0.0"
echo "Current JMdict version: ${current}"

latest=$(curl -sf "https://api.github.com/repos/scriptin/jmdict-simplified/releases/latest" |
  grep -oP '"tag_name":\s*"\K[^"]+' || true)

if [[ -z "$latest" ]]; then
  echo "Could not reach GitHub API — proceeding with existing local file."
elif [[ "$current" != "0.0.0" &&
  "$(printf '%s\n' "$current" "$latest" | sort -V | tail -1)" == "$current" ]]; then
  echo "Already up to date (${current}). Nothing to do."
  exit 0
else
  if [[ -f "jmdict-eng-${latest}.json.zip" ]] && [[ "$force" == false ]]; then
    echo "New version available: ${latest}. Already downloaded."
  else
    echo "New version available: ${latest}. Downloading..."
    curl -L --progress-bar \
      "https://github.com/scriptin/jmdict-simplified/releases/download/${latest}/jmdict-eng-${latest}.json.zip" \
      -o "jmdict-eng-${latest}.json.zip"
    echo "Download complete."
  fi
  find . -maxdepth 1 -name 'jmdict-eng-*.json.zip' ! -name "jmdict-eng-${latest}.json.zip" -delete
fi

# Show the remote comparison before filter-repo removes remote-tracking refs.
git rev-parse --verify --quiet origin/main >/dev/null
echo "Current diff against origin/main before history rewrite:"
git diff origin/main HEAD

# ── Rewrite history and rebuild ───────────────────────────────────────────────
git filter-repo --invert-paths \
  --path jmdict-compact.json.gz \
  --path dict/jmdict-compact.json.gz \
  --force
git remote add origin git@github.com:nevdelap/go-reader.git 2>/dev/null ||
  git remote set-url origin git@github.com:nevdelap/go-reader.git
scripts/compact_jmdict.py
git add dict/jmdict-compact.json.gz
git commit -m "Restore current dictionary after history rewrite."
git gc --aggressive --prune=now
read -rp "Push force to origin/main? (y/N) " confirm
[[ "$confirm" == [yY] ]] && git push origin HEAD:main --force && git push origin --tags --force --no-verify || echo "Aborted."
