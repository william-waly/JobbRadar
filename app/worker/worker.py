import json
import logging
import redis

from app.llm.extractor import extract_job_info
from app.queue.redis_client import get_redis_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

QUEUE_KEY = "jobs:queue"


def clean_job(raw: dict) -> dict | None:
    """Grunnleggende trimming og validering av et rått jobb-item."""
    title = (raw.get("title") or "").strip()
    url = (raw.get("url") or "").strip()

    if not title or not url:
        logger.warning("Hopper over jobb uten tittel/URL: %s", raw.get("external_id"))
        return None

    return {
        "external_id": raw.get("external_id"),
        "title": title,
        "description": (raw.get("description") or "").strip(),
        "company": (raw.get("company") or "").strip() or None,
        "location": (raw.get("location") or "").strip() or None,
        "url": url,
        "published_at": raw.get("published_at"),
        "source_name": raw.get("source_name"),
    }


def run_worker():
    redis_client = get_redis_client()
    logger.info("Worker startet. Venter på jobber på kø '%s'...", QUEUE_KEY)

    while True:
        try:
            result = redis_client.blpop(QUEUE_KEY, timeout=5)
        except redis.exceptions.TimeoutError:
            continue
        
        if result is None:
            continue

        _, raw_payload = result
        try:
            raw_job = json.loads(raw_payload)
        except json.JSONDecodeError:
            logger.error("Kunne ikke parse JSON fra kø: %s", raw_payload[:200])
            continue

        cleaned = clean_job(raw_job)
        if cleaned is None:
            continue

        extraction = extract_job_info(cleaned["title"], cleaned["description"])
        if extraction is not None:
            cleaned["category"] = extraction.category
            cleaned["seniority"] = extraction.seniority
            cleaned["skills"] = extraction.skills
        else:
            cleaned["category"] = None
            cleaned["seniority"] = None
            cleaned["skills"] = []

        logger.info(
            "Behandlet: %s (%s) -> kategori=%s, senioritet=%s, skills=%s",
            cleaned["title"],
            cleaned["company"],
            cleaned["category"],
            cleaned["seniority"],
            cleaned["skills"],
        )


if __name__ == "__main__":
    run_worker()