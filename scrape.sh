#!/bin/bash
set -e

./download.sh 'https://www.petstock.com.au/sitemap-0.xml'

./scripts/extract-stores.py

# Sample phase: only fetch one store page for now so we can inspect its HTML
# and build a parser. Once that's done, bump MAX_FETCHES up for a full run.
MAX_FETCHES=1 ./scripts/scrape-store-details.sh
