import pytest

from app.core.phone import normalize


@pytest.mark.parametrize("raw", ["050-1234567", "0501234567", "972501234567", "+972501234567", "+972 50 123 4567", "501234567"])
def test_israeli_variants_normalize_to_same_e164(raw):
    assert normalize(raw, "IL") == "+972501234567"


@pytest.mark.parametrize("raw", ["", "abc", "12345", "050123"])
def test_invalid(raw):
    assert normalize(raw, "IL") is None


def test_international_not_israel_only():
    assert normalize("+14155552671", "IL") == "+14155552671"
    assert normalize("(415) 555-2671", "US") == "+14155552671"
