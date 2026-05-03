#!/usr/bin/env bash
# Tag the release and push to origin.
# Usage: scripts/tag_and_push.sh

set -euo pipefail

cd "$(dirname "$0")/.."

# Extract version from index.html subtitle (e.g., "v1.14.0")
VERSION=$(grep "subtitle.*v" index.html | grep -oP 'v[0-9]+\.[0-9]+\.[0-9]+')

# Extract cache bust version from fetch URL (e.g., "14" from "v=14")
CACHE_BUST=$(grep -oP 'jmdict-compact\.json\.gz\?v=\K[0-9]+' index.html)

# Extract minor version number (e.g., "14" from "v1.14.0")
VERSION_MINOR=$(echo "$VERSION" | grep -oP 'v[0-9]+\.\K[0-9]+')

# Check if versions match (cache bust uses minor version)
if [[ "$CACHE_BUST" != "$VERSION_MINOR" ]]; then
  echo "Error: Version mismatch!"
  echo "  index.html subtitle: $VERSION (minor: $VERSION_MINOR)"
  echo "  cache bust version: $CACHE_BUST"
  exit 1
fi

echo "Version $VERSION matches cache bust v=$CACHE_BUST"

# Check if tag already exists
if git rev-parse "$VERSION" >/dev/null 2>&1; then
  echo "Error: Tag $VERSION already exists"
  exit 1
fi

# Create tag and push
echo "Creating tag $VERSION..."
git tag -a "$VERSION" -m "Release $VERSION"
echo "Pushing HEAD:main and tags..."
git push origin HEAD:main --tags --force
echo "Done! Released $VERSION"
