#!/bin/bash
set -e

./download.sh 'https://www.petstock.com.au/sitemap-0.xml'

./scripts/extract-stores.py

MAX_FETCHES=260 ./scripts/scrape-store-details.sh

./scripts/build-store-details.py
