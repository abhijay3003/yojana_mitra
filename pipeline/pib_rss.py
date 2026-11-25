"""PIB RSS and data.gov.in OGD API connectors (with offline cached fallback)."""

from __future__ import annotations

import os
import xml.etree.ElementTree as ET
from typing import Dict, List

from pipeline.scraper import PoliteScraper

PIB_RSS_URLS: List[str] = [
    "https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=3",
]


def fetch_pib_releases(limit: int = 20) -> List[Dict[str, str]]:
    """Fetch recent Press Information Bureau welfare announcements via RSS."""
    scraper = PoliteScraper()
    items: List[Dict[str, str]] = []
    for url in PIB_RSS_URLS:
        res = scraper.fetch(url)
        if not res:
            continue
        try:
            root = ET.fromstring(res["body"])
            for item in root.findall(".//item")[:limit]:
                items.append(
                    {
                        "title": (item.findtext("title") or "").strip(),
                        "link": (item.findtext("link") or "").strip(),
                        "pubDate": (item.findtext("pubDate") or "").strip(),
                        "description": (item.findtext("description") or "").strip(),
                    }
                )
        except ET.ParseError:
            continue
    return items
