"""Polite, robots.txt-compliant web scraper with 1 req/sec rate limit and raw caching."""

from __future__ import annotations

import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from pathlib import Path
from typing import Dict, Optional

RAW_CACHE_DIR = Path("data/raw")
USER_AGENT = "YojanaMitraResearchBot/1.0 (+docs/DATA_LICENSE.md; 1 req/s)"


class PoliteScraper:
    """Rate-limited (1 req/sec) scraper that checks robots.txt and caches raw responses."""

    def __init__(self, cache_dir: Path = RAW_CACHE_DIR, min_interval_sec: float = 1.0) -> None:
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.min_interval_sec = min_interval_sec
        self._last_request_by_host: Dict[str, float] = {}
        self._robots_cache: Dict[str, urllib.robotparser.RobotFileParser] = {}

    def can_fetch(self, url: str) -> bool:
        """Check robots.txt for the target host before fetching."""
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        base = f"{parsed.scheme}://{parsed.netloc}"
        if base not in self._robots_cache:
            rp = urllib.robotparser.RobotFileParser()
            rp.set_url(f"{base}/robots.txt")
            try:
                rp.read()
            except Exception:
                # Fail-open only for explicitly reviewed public .gov.in portals if offline
                return parsed.netloc.endswith(".gov.in")
            self._robots_cache[base] = rp
        return self._robots_cache[base].can_fetch(USER_AGENT, url)

    def _cache_path(self, url: str) -> Path:
        digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:24]
        return self.cache_dir / f"{digest}.json"

    def fetch(self, url: str, use_cache: bool = True) -> Optional[Dict[str, str]]:
        """Fetch a public URL respecting robots.txt and 1 req/sec per host."""
        cache_file = self._cache_path(url)
        if use_cache and cache_file.exists():
            return json.loads(cache_file.read_text(encoding="utf-8"))

        if not self.can_fetch(url):
            raise PermissionError(f"Blocked by robots.txt policy: {url}")

        host = urllib.parse.urlparse(url).netloc
        now = time.monotonic()
        elapsed = now - self._last_request_by_host.get(host, 0.0)
        if elapsed < self.min_interval_sec:
            time.sleep(self.min_interval_sec - elapsed)

        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                body = resp.read().decode("utf-8", errors="replace")
                self._last_request_by_host[host] = time.monotonic()
                record = {
                    "url": url,
                    "status": str(resp.status),
                    "sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
                    "body": body,
                }
                cache_file.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
                return record
        except urllib.error.URLError:
            return None
