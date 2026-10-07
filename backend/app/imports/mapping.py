import re

# Column targets: invitation_name | group | note | ignore | person:N | phone:N
TARGET_RE = re.compile(r"^(invitation_name|group|note|ignore|person:\d+|phone:\d+)$")

# Header synonyms (normalized). Add a language by adding words here.
SYNONYMS = {
    "invitation_name": {"שם הזמנה", "הזמנה", "שם משפחה", "invitation name", "invitation", "family", "family name"},
    "group": {"קבוצה", "group", "category", "קטגוריה"},
    "note": {"הערות", "הערה", "notes", "note", "comments"},
}
PERSON_RE = re.compile(r"^(?:שם|שם אורח|אורח|person|name|guest)\s*(\d+)$")
PHONE_RE = re.compile(r"^(?:טלפון|נייד|פלאפון|phone|mobile|cell)\s*(\d+)$")


def _norm(header: str) -> str:
    return re.sub(r"[\s_\-]+", " ", header.strip().lower())


def detect_mapping(headers: list[str]) -> list[str]:
    result, used = [], set()
    for h in headers:
        n = _norm(h)
        target = "ignore"
        if m := PERSON_RE.match(n):
            target = f"person:{int(m[1])}"
        elif m := PHONE_RE.match(n):
            target = f"phone:{int(m[1])}"
        else:
            target = next((t for t, words in SYNONYMS.items() if n in words), "ignore")
        if target != "ignore" and target in used:
            target = "ignore"  # first column wins; admin can fix in the UI
        used.add(target)
        result.append(target)
    return result


def validate_mapping(mapping: list[str]) -> str | None:
    """Error code, or None if valid."""
    if any(not TARGET_RE.match(t) for t in mapping):
        return "invalid_mapping"
    real = [t for t in mapping if t != "ignore"]
    return "duplicate_mapping" if len(real) != len(set(real)) else None
