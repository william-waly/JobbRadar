from pydantic import BaseModel, Field, field_validator


class JobExtraction(BaseModel):
    category: str = Field(description="Overordnet jobbkategori, f.eks. 'Backend Development'")
    seniority: str = Field(description="Erfaringsnivå: Junior, Medior, Senior, eller Ukjent")
    skills: list[str] = Field(default_factory=list)

    @field_validator("seniority")
    @classmethod
    def normalize_seniority(cls, v: str) -> str:
        allowed = {"Junior", "Medior", "Senior", "Ukjent"}
        v = v.strip().capitalize()
        return v if v in allowed else "Ukjent"