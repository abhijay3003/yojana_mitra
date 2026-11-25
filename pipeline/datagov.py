"""data.gov.in Open Government Data (OGD) API connector."""

from __future__ import annotations

import json
import os
import urllib.parse
from typing import Any, Dict, List

from pipeline.scraper import PoliteScraper

OGD_BASE_URL = "https://api.data.gov.in/resource"


def fetch_datagov_resource(resource_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Fetch records from a data.gov.in resource if DATA_GOV_IN_API_KEY is set."""
    api_key = os.getenv("DATA_GOV_IN_API_KEY", "").strip()
    if not api_key:
        return []
    params = urllib.parse.urlencode({"api-key": api_key, "format": "json", "limit": str(limit)})
    url = f"{OGD_BASE_URL}/{resource_id}?{params}"
    res = PoliteScraper().fetch(url)
    if not res:
        return []
    try:
        payload = json.loads(res["body"])
        return list(payload.get("records", []))
    except json.JSONDecodeError:
        return []
