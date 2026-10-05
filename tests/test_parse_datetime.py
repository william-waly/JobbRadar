from app.database.repository import parse_datetime


def test_valid_iso_datetime_is_parsed():
    result = parse_datetime("2026-09-01T12:00:00+02:00")
    assert result is not None
    assert result.year == 2026
    assert result.month == 9


def test_none_input_returns_none():
    assert parse_datetime(None) is None


def test_empty_string_returns_none():
    assert parse_datetime("") is None


def test_invalid_format_returns_none():
    assert parse_datetime("not-a-date") is None