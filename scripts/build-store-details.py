#!/usr/bin/env python3
"""Parse each fetched store HTML page into data/store-details.json.

Store pages are Next.js pages that embed their data as a JSON blob in
<script id="__NEXT_DATA__">, under props.pageProps.locationData.location.
"""

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HTML_DIR = ROOT / "data" / "stores"
OUTPUT = ROOT / "data" / "store-details.json"

NEXT_DATA_RE = re.compile(
    r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.S
)


def last_commit_iso(path: Path) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(ROOT), "log", "-1", "--format=%cI", "--", str(path)],
        capture_output=True,
        text=True,
    )
    output = result.stdout.strip()
    return output or None


def parse_store_html(path: Path) -> dict | None:
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
        "scrapedAt": last_commit_iso(path),
    }


def main() -> None:
    stores = []
    for html_path in sorted(HTML_DIR.glob("*.html")):
        details = parse_store_html(html_path)
        if details:
            stores.append(details)

    stores.sort(key=lambda s: s["slug"] or "")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w") as f:
        json.dump(stores, f, indent=2)
        f.write("\n")

    print(f"Wrote {len(stores)} store detail record(s) to {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
