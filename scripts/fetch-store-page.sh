#!/usr/bin/env bash
#
# fetch-store-page.sh - Download a single store page's raw HTML
# Usage: ./scripts/fetch-store-page.sh URL OUTPUT_PATH

set -euo pipefail

if [ $# -ne 2 ]; then
  echo "Usage: $0 URL OUTPUT_PATH" >&2
  exit 1
fi

URL="$1"
OUTPUT_PATH="$2"

mkdir -p "$(dirname "$OUTPUT_PATH")"

curl -s -L "$URL" \
  -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36' \
  -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8' \
  -o "$OUTPUT_PATH" \
  --fail-with-body \
  --max-time 30 || {
    echo "Error: Failed to download $URL" >&2
    rm -f "$OUTPUT_PATH"
    exit 1
  }

# Record the fetch time alongside the HTML. build-store-details.py reads this
# for "scrapedAt" since, at parse time, the HTML file itself isn't committed
# yet this run, so git history can't tell us when it was actually fetched.
META_PATH="${OUTPUT_PATH%.html}.meta.json"
printf '{"fetchedAt": "%s"}\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$META_PATH"

echo "Saved $URL -> $OUTPUT_PATH"
