#!/usr/bin/env bash
set -euo pipefail

# ── Check for newer JMdict release ───────────────────────────────────────────
current=$(find . -maxdepth 1 -name 'jmdict-eng-*.json' | sort -V | tail -1 | grep -oP '\d+\.\d+\.\d+' || true)
[[ -z "$current" ]] && current="0.0.0"
echo "Current JMdict version: ${current}"

latest=$(curl -sf "https://api.github.com/repos/scriptin/jmdict-simplified/releases/latest" \
  | grep -oP '"tag_name":\s*"\K[^"]+' || true)

if [[ -z "$latest" ]]; then
  echo "Could not reach GitHub API — proceeding with existing local file."
elif [[ "$current" != "0.0.0" && \
       "$(printf '%s\n' "$current" "$latest" | sort -V | tail -1)" == "$current" ]]; then
  echo "Already up to date (${current}). Nothing to do."
  exit 0
else
  echo "New version available: ${latest}. Downloading..."
  curl -L --progress-bar \
    "https://github.com/scriptin/jmdict-simplified/releases/download/${latest}/jmdict-eng-${latest}.json" \
    -o "jmdict-eng-${latest}.json"
  [[ "$current" != "0.0.0" ]] && rm -f "jmdict-eng-${current}.json"
  echo "Download complete."
fi

# ── Rewrite history and rebuild ───────────────────────────────────────────────
git filter-repo --invert-paths --path jmdict-compact.json.gz --force
git remote add origin git@github.com:nevdelap/go-reader.git
uv run python compact_jmdict.py
git add jmdict-compact.json.gz
git commit -m "Restore current dictionary after history rewrite."
git gc --aggressive --prune=now
git fetch origin
git diff HEAD origin/main
read -rp "Push force to origin/main? (y/N) " confirm
[[ "$confirm" == [yY] ]] && git push origin HEAD:main --force || echo "Aborted."
