import logging
from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.database.models import Company, Job, JobSkill, Skill, Source

logger = logging.getLogger(__name__)


def parse_datetime(value: str | None) -> datetime | None:
    """Parser en ISO 8601-dato fra scraperen. Returnerer None hvis parsing feiler."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        logger.warning("Kunne ikke parse dato: %s", value)
        return None


def get_or_create_source(session: Session, name: str, base_url: str) -> Source:
    stmt = pg_insert(Source).values(name=name, base_url=base_url)
    stmt = stmt.on_conflict_do_nothing(index_elements=["name"])
    session.execute(stmt)
    return session.scalar(select(Source).where(Source.name == name))


def get_or_create_company(session: Session, name: str) -> Company:
    stmt = pg_insert(Company).values(name=name)
    stmt = stmt.on_conflict_do_nothing(index_elements=["name"])
    session.execute(stmt)
    return session.scalar(select(Company).where(Company.name == name))


def get_or_create_skill(session: Session, name: str) -> Skill:
    normalized = name.strip().lower()
    stmt = pg_insert(Skill).values(name=normalized)
    stmt = stmt.on_conflict_do_nothing(index_elements=["name"])
    session.execute(stmt)
    return session.scalar(select(Skill).where(Skill.name == normalized))


def upsert_job(
    session: Session,
    *,
    source: Source,
    company: Company,
    job_data: dict,
    skill_names: list[str],
) -> int:
    """
    Setter inn jobben, eller oppdaterer den hvis (source_id, external_id)
    allerede finnes. Atomisk på databasenivå - trygt selv med flere
    samtidige workers.
    """
    stmt = pg_insert(Job).values(
        company_id=company.id,
        source_id=source.id,
        external_id=job_data["external_id"],
        title=job_data["title"],
        location=job_data["location"],
        description=job_data["description"],
        url=job_data["url"],
        published_at=parse_datetime(job_data["published_at"]),
        scraped_at=datetime.now(timezone.utc),
        category=job_data["category"],
        seniority=job_data["seniority"],
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=["source_id", "external_id"],
        set_={
            "company_id": stmt.excluded.company_id,
            "title": stmt.excluded.title,
            "location": stmt.excluded.location,
            "description": stmt.excluded.description,
            "url": stmt.excluded.url,
            "published_at": stmt.excluded.published_at,
            "scraped_at": stmt.excluded.scraped_at,
            "category": stmt.excluded.category,
            "seniority": stmt.excluded.seniority,
        },
    ).returning(Job.id)

    job_id = session.execute(stmt).scalar_one()

    # Skills-koblingen synkroniseres på nytt hver gang: enklere og mer robust
    # enn å prøve å regne ut diff (lagt til/fjernet skills) mellom kjøringer.
    session.execute(delete(JobSkill).where(JobSkill.job_id == job_id))
    for name in skill_names:
        if not name.strip():
            continue
        skill = get_or_create_skill(session, name)
        link_stmt = pg_insert(JobSkill).values(job_id=job_id, skill_id=skill.id)
        link_stmt = link_stmt.on_conflict_do_nothing(index_elements=["job_id", "skill_id"])
        session.execute(link_stmt)

    return job_id