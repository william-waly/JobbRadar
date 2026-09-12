import json
import logging
from datetime import datetime, timezone
import redis

from app.database.base import SessionLocal
from app.database.repository import get_or_create_company, get_or_create_source, upsert_job
from app.llm.extractor import extract_job_info
from app.queue.redis_client import get_redis_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

QUEUE_KEY = "jobs:queue"
SOURCE_NAME = "NAV Arbeidsplassen"
SOURCE_BASE_URL = "https://arbeidsplassen.nav.no"


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

def process_job(cleaned: dict) -> None:
    extraction = extract_job_info(cleaned["title"], cleaned["description"])
    category = extraction.category if extraction else None
    seniority = extraction.seniority if extraction else None
    skills = extraction.skills if extraction else []

    session = SessionLocal()
    try:
        source = get_or_create_source(session, SOURCE_NAME, SOURCE_BASE_URL)
        company_name = cleaned["company"] or "Ukjent arbeidsgiver"
        company = get_or_create_company(session, company_name)

        job_data = {**cleaned, "category": category, "seniority": seniority}
        job_id = upsert_job(
            session, source=source, company=company, job_data=job_data, skill_names=skills
        )

        session.commit()
        logger.info(
            "Upsertet job_id=%s: %s (%s) -> kategori=%s, senioritet=%s, skills=%s",
            job_id, cleaned["title"], company_name, category, seniority, skills,
        )
    except Exception as e:
        session.rollback()
        logger.error("Kunne ikke lagre jobb %s: %s", cleaned.get("external_id"), e)
    finally:
        session.close()

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

        process_job(cleaned)


if __name__ == "__main__":
    run_worker()