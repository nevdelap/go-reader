#!/usr/bin/env bash
set -euo pipefail

git filter-repo --invert-paths --path jmdict-compact.json.gz --force
git remote add origin git@github.com:nevdelap/go-reader.git
git add jmdict-compact.json.gz
git commit -m "Restore current dictionary after history rewrite."
git gc --aggressive --prune=now
git fetch origin
git diff HEAD origin/main
read -rp "Push force to origin/main? (y/N) " confirm
[[ "$confirm" == [yY] ]] && git push --force || echo "Aborted."
