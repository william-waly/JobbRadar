from app.llm.schemas import JobExtraction


def test_valid_seniority_is_kept():
    extraction = JobExtraction(category="Backend", seniority="Senior", skills=["Python"])
    assert extraction.seniority == "Senior"


def test_lowercase_seniority_is_normalized():
    extraction = JobExtraction(category="Backend", seniority="junior", skills=[])
    assert extraction.seniority == "Junior"


def test_invalid_seniority_falls_back_to_ukjent():
    extraction = JobExtraction(category="Backend", seniority="Ekspert", skills=[])
    assert extraction.seniority == "Ukjent"


def test_skills_default_to_empty_list():
    extraction = JobExtraction(category="Backend", seniority="Ukjent")
    assert extraction.skills == []