#!/usr/bin/env python3
"""Parse freshly-fetched store HTML pages into data/store-details.json.

Store pages are Next.js pages that embed their data as a JSON blob in
<script id="__NEXT_DATA__">, under props.pageProps.locationData.location.

Fetched HTML is a transient working file (see .gitignore) - only the
structured data extracted from it is committed. So each run merges
newly-parsed stores into the existing output, rather than requiring every
store's HTML to be present locally.
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HTML_DIR = ROOT / "data" / "stores"
OUTPUT = ROOT / "data" / "store-details.json"

NEXT_DATA_RE = re.compile(
    r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.S
)


def parse_store_html(path: Path, scraped_at: str) -> dict | None:
    html = path.read_text(encoding="utf-8")
    match = NEXT_DATA_RE.search(html)
    if not match:
        print(f"Warning: no __NEXT_DATA__ found in {path.name}, skipping")
        return None

    try:
        next_data = json.loads(match.group(1))
        location = next_data["props"]["pageProps"]["locationData"]["location"]
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        print(f"Warning: couldn't extract location data from {path.name}: {e}")
        return None

    return {
        "id": location.get("warehouse"),
        "slug": location.get("handle"),
        "name": location.get("name"),
        "url": f"https://petstock.com.au/store/{location.get('handle')}",
        "isActive": location.get("isActive"),
        "address": {
            "line1": location.get("addressLine1"),
            "line2": location.get("addressLine2"),
            "suburb": location.get("suburb"),
            "state": location.get("state"),
            "postcode": location.get("postcode"),
            "country": location.get("country"),
        },
        "latitude": location.get("latitude"),
        "longitude": location.get("longitude"),
        "phone": location.get("phone"),
        "email": location.get("email"),
        "services": location.get("locationServices"),
        "openingHours": location.get("openingHours"),
        "scrapedAt": scraped_at,
    }


def main() -> None:
    stores_by_slug = {}
    if OUTPUT.exists():
        for store in json.loads(OUTPUT.read_text()):
            stores_by_slug[store["slug"]] = store

    scraped_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    updated = 0
    for html_path in sorted(HTML_DIR.glob("*.html")):
        details = parse_store_html(html_path, scraped_at)
        if details:
            stores_by_slug[details["slug"]] = details
            updated += 1

    stores = sorted(stores_by_slug.values(), key=lambda s: s["slug"] or "")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w") as f:
        json.dump(stores, f, indent=2)
        f.write("\n")

    print(f"Updated {updated} store(s), {len(stores)} total in {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
