import csv
import io
import re


def safe(cell: object) -> str:
    """Neutralise spreadsheet formula injection (cells starting with = + - @) except plain phone numbers."""
    s = "" if cell is None else str(cell)
    if re.fullmatch(r"\+?\d+", s) or not s or s[0] not in "=+-@\t\r":
        return s
    return "'" + s


def to_csv_bytes(rows: list[list[object]]) -> bytes:
    """UTF-8 with BOM so Excel shows Hebrew correctly."""
    out = io.StringIO()
    csv.writer(out).writerows([[safe(c) for c in r] for r in rows])
    return b"\xef\xbb\xbf" + out.getvalue().encode()
