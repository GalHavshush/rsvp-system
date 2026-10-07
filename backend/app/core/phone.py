import phonenumbers

from app.core.config import settings


def normalize(raw: str, region: str | None = None) -> str | None:
    # is_possible (length/format) rather than is_valid: strict range checks reject real, newly allocated
    # carrier ranges and sample numbers like 050-1234567. Typos and junk still fail.
    """Return the E.164 form of `raw`, or None if empty/invalid. Region is the fallback for national numbers."""
    raw = raw.strip()
    if not raw:
        return None
    try:
        n = phonenumbers.parse(raw, region or settings.default_region)
    except phonenumbers.NumberParseException:
        return None
    return phonenumbers.format_number(n, phonenumbers.PhoneNumberFormat.E164) if phonenumbers.is_possible_number(n) else None
