import json
import logging
from datetime import datetime, timedelta, timezone

import scrapy

from app.scraper.items import JobItem

logger = logging.getLogger(__name__)


class NavFeedSpider(scrapy.Spider):
    """
    Henter jobbannonser fra NAV sin pam-stilling-feed API.

    Kjøres med f.eks.:
        scrapy crawl nav_feed -a hours_back=24 -a max_pages=3 -o output/jobs.json
    """

    name = "nav_feed"

    base_url = "https://pam-stilling-feed.nav.no"
    token_url = "https://pam-stilling-feed.nav.no/api/publicToken"
    feed_path = "/api/v1/feed"

    def __init__(self, hours_back=24, max_pages=5, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hours_back = int(hours_back)
        self.max_pages = int(max_pages)
        self.pages_fetched = 0
        self.token = None

    async def start(self):
        # Steg 1: hent et gyldig offentlig token dynamisk (det roterer over tid)
        yield scrapy.Request(
            url=self.token_url,
            callback=self.parse_token,
            dont_filter=True,
        )

    def parse_token(self, response):
        # Responsen er ren tekst: "Current public token ...:\n<token>"
        lines = response.text.strip().splitlines()
        self.token = lines[-1].strip()
        logger.info("Hentet offentlig token fra NAV.")

        since = datetime.now(timezone.utc) - timedelta(hours=self.hours_back)
        since_header = since.strftime("%a, %d %b %Y %H:%M:%S GMT")

        yield scrapy.Request(
            url=f"{self.base_url}{self.feed_path}",
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/json",
                "If-Modified-Since": since_header,
            },
            callback=self.parse_feed_page,
        )

    def parse_feed_page(self, response):
        self.pages_fetched += 1
        data = json.loads(response.text)

        for entry in data.get("items", []):
            feed_entry = entry.get("_feed_entry", {})
            if feed_entry.get("status") != "ACTIVE":
                continue  # kun aktive annonser er interessante nå

            detail_url = entry.get("url")
            if not detail_url:
                continue

            full_detail_url = (
                f"{self.base_url}{detail_url}" if detail_url.startswith("/") else detail_url
            )

            yield scrapy.Request(
                url=full_detail_url,
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Accept": "application/json",
                },
                callback=self.parse_ad_detail,
            )

        next_url = data.get("next_url")
        if next_url and self.pages_fetched < self.max_pages:
            full_next_url = (
                f"{self.base_url}{next_url}" if next_url.startswith("/") else next_url
            )
            yield scrapy.Request(
                url=full_next_url,
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Accept": "application/json",
                },
                callback=self.parse_feed_page,
            )

    def parse_ad_detail(self, response):
        data = json.loads(response.text)
        ad = data.get("ad_content")
        if not ad:
            return  # annonsen er inaktiv eller mangler innhold

        work_locations = ad.get("workLocations") or [{}]
        location = work_locations[0]

        item = JobItem()
        item["external_id"] = ad.get("uuid")
        item["title"] = ad.get("title")
        item["description"] = ad.get("description")
        item["company"] = (ad.get("employer") or {}).get("name")
        item["location"] = location.get("municipal") or location.get("city")
        item["url"] = ad.get("link") or ad.get("sourceurl")
        item["published_at"] = ad.get("published")
        item["source_name"] = "NAV Arbeidsplassen"

        yield item