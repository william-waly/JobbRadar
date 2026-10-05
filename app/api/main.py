from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.api.schemas import (
    CompanyOut,
    JobListOut,
    JobOut,
    LocationCountOut,
    SkillCountOut,
    SkillOut,
    StatisticsOut,
)
from app.database.models import Company, Job, JobSkill, Skill

app = FastAPI(title="JobbRadar API", version="0.1.0")


@app.get("/jobs", response_model=list[JobListOut])
def list_jobs(
    db: Session = Depends(get_db),
    category: str | None = None,
    location: str | None = None,
    limit: int = Query(default=20, le=100),
    offset: int = 0,
):
    stmt = select(Job)
    if category:
        stmt = stmt.where(Job.category == category)
    if location:
        stmt = stmt.where(Job.location == location)
    stmt = stmt.order_by(Job.scraped_at.desc()).limit(limit).offset(offset)
    return db.scalars(stmt).all()


@app.get("/jobs/{job_id}", response_model=JobOut)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Jobb ikke funnet")
    return job


@app.get("/companies", response_model=list[CompanyOut])
def list_companies(db: Session = Depends(get_db)):
    return db.scalars(select(Company).order_by(Company.name)).all()


@app.get("/skills", response_model=list[SkillOut])
def list_skills(db: Session = Depends(get_db)):
    return db.scalars(select(Skill).order_by(Skill.name)).all()


@app.get("/statistics", response_model=StatisticsOut)
def get_statistics(db: Session = Depends(get_db)):
    return StatisticsOut(
        total_jobs=db.scalar(select(func.count()).select_from(Job)),
        total_companies=db.scalar(select(func.count()).select_from(Company)),
        total_skills=db.scalar(select(func.count()).select_from(Skill)),
    )


@app.get("/statistics/skills", response_model=list[SkillCountOut])
def get_skill_statistics(db: Session = Depends(get_db), limit: int = Query(default=10, le=50)):
    stmt = (
        select(Skill.name, func.count(JobSkill.job_id).label("count"))
        .join(JobSkill, JobSkill.skill_id == Skill.id)
        .group_by(Skill.name)
        .order_by(func.count(JobSkill.job_id).desc())
        .limit(limit)
    )
    return [SkillCountOut(skill=row.name, count=row.count) for row in db.execute(stmt).all()]


@app.get("/statistics/locations", response_model=list[LocationCountOut])
def get_location_statistics(db: Session = Depends(get_db), limit: int = Query(default=10, le=50)):
    stmt = (
        select(Job.location, func.count(Job.id).label("count"))
        .where(Job.location.is_not(None))
        .group_by(Job.location)
        .order_by(func.count(Job.id).desc())
        .limit(limit)
    )
    return [LocationCountOut(location=row.location, count=row.count) for row in db.execute(stmt).all()]