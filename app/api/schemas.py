from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SkillOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class CompanyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class JobListOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    location: str | None
    category: str | None
    seniority: str | None
    company: CompanyOut


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    location: str | None
    description: str | None
    url: str
    published_at: datetime | None
    scraped_at: datetime
    category: str | None
    seniority: str | None
    company: CompanyOut
    skills: list[SkillOut]


class StatisticsOut(BaseModel):
    total_jobs: int
    total_companies: int
    total_skills: int


class SkillCountOut(BaseModel):
    skill: str
    count: int


class LocationCountOut(BaseModel):
    location: str
    count: int