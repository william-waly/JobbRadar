def test_project_is_wired_up():
    """Smoke test: bekrefter at pytest finner og kjører tester."""
    import app  # noqa: F401

    assert True