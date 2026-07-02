#!/usr/bin/env bash
#
# scrape-store-details.sh - Fetch raw HTML for each store's detail page.
#
# The fetched HTML is a transient working file (see .gitignore) - only the
# structured data extracted from it is committed, to data/store-details.json.
#
# A store is (re)fetched when either is true:
#   - it has no entry in data/store-details.json yet (new store), or
#   - its recorded scrapedAt is more than STALE_DAYS ago (weekly refresh)
#
# MAX_FETCHES caps how many pages are fetched in a single run, so we don't
# hammer the site (and so early runs can be limited to a small sample while
# the parser is being built).
#
# Usage: ./scripts/scrape-store-details.sh
# Env vars: STALE_DAYS (default 7), MAX_FETCHES (default 10), SLEEP_SECONDS (default 1)

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STORES_JSON="$ROOT/data/stores.json"
DETAILS_JSON="$ROOT/data/store-details.json"
HTML_DIR="$ROOT/data/stores"

STALE_DAYS="${STALE_DAYS:-7}"
MAX_FETCHES="${MAX_FETCHES:-10}"
SLEEP_SECONDS="${SLEEP_SECONDS:-1}"

STALE_CUTOFF_ISO=$(date -u -d "-${STALE_DAYS} days" +%Y-%m-%dT%H:%M:%SZ)

fetched=0

needs_fetch() {
  local slug="$1"

  if [ ! -f "$DETAILS_JSON" ]; then
    return 0
  fi

  local scraped_at
  scraped_at=$(jq -r --arg slug "$slug" \
    'map(select(.slug == $slug)) | .[0].scrapedAt // empty' "$DETAILS_JSON")

  if [ -z "$scraped_at" ]; then
    return 0 # new store, or never successfully scraped
  fi

  if [[ "$scraped_at" < "$STALE_CUTOFF_ISO" ]]; then
    return 0 # stale, needs a refresh
  fi

  return 1
}

count=$(jq 'length' "$STORES_JSON")
echo "Checking $count stores (stale after ${STALE_DAYS}d, max ${MAX_FETCHES} fetches this run)"

for i in $(seq 0 $((count - 1))); do
  if [ "$fetched" -ge "$MAX_FETCHES" ]; then
    echo "Reached MAX_FETCHES=$MAX_FETCHES, stopping for this run"
    break
  fi

  slug=$(jq -r ".[$i].slug" "$STORES_JSON")
  url=$(jq -r ".[$i].url" "$STORES_JSON")
  html_path="$HTML_DIR/$slug.html"

  if needs_fetch "$slug"; then
    fetched=$((fetched + 1))
    if ! "$ROOT/scripts/fetch-store-page.sh" "$url" "$html_path"; then
      echo "Skipping $slug for this run after fetch failure" >&2
    fi
    sleep "$SLEEP_SECONDS"
  fi
done

echo "Fetched $fetched store page(s) this run"
