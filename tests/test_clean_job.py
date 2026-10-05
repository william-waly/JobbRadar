from app.worker.worker import clean_job


def test_valid_job_is_cleaned():
    raw = {
        "external_id": "abc-123",
        "title": "  Backend-utvikler  ",
        "description": "  Vi søker en utvikler.  ",
        "company": "  Acme AS  ",
        "location": "  Oslo  ",
        "url": "  https://example.com/job/1  ",
        "published_at": "2026-09-01T00:00:00+02:00",
        "source_name": "NAV Arbeidsplassen",
    }
    cleaned = clean_job(raw)
    assert cleaned is not None
    assert cleaned["title"] == "Backend-utvikler"
    assert cleaned["company"] == "Acme AS"
    assert cleaned["url"] == "https://example.com/job/1"


def test_missing_title_returns_none():
    raw = {"title": "", "url": "https://example.com/job/1"}
    assert clean_job(raw) is None


def test_missing_url_returns_none():
    raw = {"title": "Utvikler", "url": ""}
    assert clean_job(raw) is None


def test_empty_optional_fields_become_none():
    raw = {
        "title": "Utvikler",
        "url": "https://example.com/job/1",
        "company": "   ",
        "location": "",
    }
    cleaned = clean_job(raw)
    assert cleaned["company"] is None
    assert cleaned["location"] is None