#!/usr/bin/env python3
"""Extract the list of Petstock store URLs from the sitemap into data/stores.json."""

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITEMAP = ROOT / "petstock.com.au-sitemap-0.xml.xml"
OUTPUT = ROOT / "data" / "stores.json"

NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
STORE_URL_RE = re.compile(r"^https://petstock\.com\.au/store/(?!finder$)(?P<slug>[^/]+)$")
TRAILING_ID_RE = re.compile(r"-(\d+)$")


def main() -> None:
    tree = ET.parse(SITEMAP)
    root = tree.getroot()

    stores = []
    for url_el in root.findall("sm:url", NS):
        loc_el = url_el.find("sm:loc", NS)
        if loc_el is None or not loc_el.text:
            continue
        loc = loc_el.text.strip()
        match = STORE_URL_RE.match(loc)
        if not match:
            continue

        slug = match.group("slug")
        id_match = TRAILING_ID_RE.search(slug)
        lastmod_el = url_el.find("sm:lastmod", NS)

        stores.append(
            {
                "id": id_match.group(1) if id_match else None,
                "slug": slug,
                "url": loc,
                "lastmod": lastmod_el.text.strip() if lastmod_el is not None and lastmod_el.text else None,
            }
        )

    stores.sort(key=lambda s: s["slug"])

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w") as f:
        json.dump(stores, f, indent=2)
        f.write("\n")

    print(f"Wrote {len(stores)} stores to {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
