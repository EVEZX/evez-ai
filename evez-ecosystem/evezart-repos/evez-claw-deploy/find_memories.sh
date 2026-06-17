#!/usr/bin/env bash
set -euo pipefail
output_file="memory_files.txt"
> "$output_file"
repos=(
$(gh repo list EvezArt --limit 200 --json name | jq -r '.[].name')
)
for repo in "${repos[@]}"; do
  url=$(gh api -X GET repos/EvezArt/$repo/contents/MEMORY.md --jq '.download_url' 2>/dev/null || true)
  if [[ -n "$url" ]]; then
    echo "$repo: $url" >> "$output_file"
  fi
done

echo "Done. Results in $output_file"
