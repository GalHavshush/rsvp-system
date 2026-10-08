import io

from openpyxl import Workbook

from app.imports.mapping import detect_mapping, validate_mapping
from app.imports.parser import ParseError, parse_upload
import pytest

HE = "שם הזמנה,שם 1,טלפון 1,שם 2,טלפון 2,שם 3,טלפון 3,קבוצה\n"
CSV = (HE
       + "משפחת כהן,דוד כהן,0501234567,יעל כהן,0521234567,נועה כהן,,משפחה חתן\n"
       + "רון ודנה,רון לוי,0541234567,דנה לוי,0527654321,,,חברים\n"
       + "גל,גל,0509876543,,,,,צבא\n")


def test_detect_hebrew_and_english_headers():
    assert detect_mapping(HE.strip().split(",")) == [
        "invitation_name", "person:1", "phone:1", "person:2", "phone:2", "person:3", "phone:3", "group"]
    assert detect_mapping(["Invitation Name", "Person 1", "Phone 1", "Person 12", "Group", "Whatever"]) == [
        "invitation_name", "person:1", "phone:1", "person:12", "group", "ignore"]


def test_duplicate_header_mapping_first_wins_and_validation():
    assert detect_mapping(["Group", "קבוצה"]) == ["group", "ignore"]
    assert validate_mapping(["group", "group"]) == "duplicate_mapping"
    assert validate_mapping(["bogus"]) == "invalid_mapping"


def test_parse_csv_and_xlsx():
    headers, rows = parse_upload("g.csv", CSV.encode("utf-8-sig"))
    assert headers[0] == "שם הזמנה" and len(rows) == 3 and rows[2][2] == "0509876543"
    wb = Workbook(); ws = wb.active
    ws.append(["Invitation Name", "Person 1", "Phone 1"]); ws.append(["Gal", "Gal", 501234567]); ws.append([None, None, None])
    buf = io.BytesIO(); wb.save(buf)
    headers, rows = parse_upload("g.xlsx", buf.getvalue())
    assert rows == [["Gal", "Gal", "501234567"]]  # numeric phone kept, blank row dropped


def test_parse_rejects_bad_files():
    for name, data in [("a.txt", b"x"), ("a.csv", b""), ("a.xlsx", b"not a zip")]:
        with pytest.raises(ParseError):
            parse_upload(name, data)


def _login(client):
    client.post("/api/auth/setup", json={"email": "o@example.com", "password": "correct-horse"})
    return client.post("/api/events", json={"name": "W"}).json()["id"]


def _sheet(client, eid, text=CSV):
    r = client.post(f"/api/events/{eid}/imports/parse", files={"file": ("g.csv", text.encode("utf-8-sig"))})
    assert r.status_code == 200, r.text
    return r.json()


def test_import_preview_commit_and_one_row_one_invitation(client):
    eid = _login(client)
    sheet = _sheet(client, eid)
    body = {"mapping": sheet["mapping"], "rows": sheet["rows"]}
    prev = client.post(f"/api/events/{eid}/imports/preview", json=body).json()
    assert prev["counts"] == {"ok": 3, "warning": 0, "conflict": 0, "error": 0}
    cohen = prev["rows"][0]["draft"]
    assert [m["name"] for m in cohen["members"]] == ["דוד כהן", "יעל כהן", "נועה כהן"]
    assert [c["member_index"] for c in cohen["contacts"]] == [0, 1]
    assert client.post(f"/api/events/{eid}/imports/commit", json=body).json() == {"created": 3, "updated": 0, "skipped": 0}
    page = client.get(f"/api/events/{eid}/invitations").json()
    assert page["total"] == 3
    inv = next(i for i in page["items"] if i["display_name"] == "משפחת כהן")
    assert inv["group_name"] == "משפחה חתן" and len(inv["members"]) == 3
    assert [c["phone_e164"] for c in inv["contacts"]] == ["+972501234567", "+972521234567"]
    assert len({i["rsvp_token"] for i in page["items"]}) == 3
    assert {g["name"] for g in client.get(f"/api/events/{eid}/groups").json()} == {"משפחה חתן", "חברים", "צבא"}


def test_validation_issues(client):
    eid = _login(client)
    text = ("Invitation Name,Person 1,Phone 1\n"
            ",NoName,0501111111\n"          # missing name -> error
            "A,A,12345\n"                    # invalid phone -> warning
            "B,B,0502222222\n"
            "C,C,0502222222\n"               # duplicate phone in file -> warning
            "B,B,0502222222\n")              # duplicate row
    sheet = _sheet(client, eid, text)
    rows = client.post(f"/api/events/{eid}/imports/preview", json={"mapping": sheet["mapping"], "rows": sheet["rows"]}).json()["rows"]
    codes = [[i["code"] for i in r["issues"]] for r in rows]
    assert codes[0] == ["missing_name"] and rows[0]["status"] == "error"
    assert codes[1] == ["invalid_phone"]
    assert codes[2] == [] and "duplicate_phone_in_file" in codes[3]
    same_row = client.post(f"/api/events/{eid}/imports/preview", json={
        "mapping": ["invitation_name", "person:1", "phone:1", "person:2", "phone:2"],
        "rows": [["Pair", "A", "0502020202", "B", "0502020202"]]}).json()["rows"][0]
    assert [i["code"] for i in same_row["issues"]] == ["duplicate_phone_in_file"]
    assert "duplicate_row" in codes[4] and rows[4]["default_action"] == "skip"


def test_conflicts_never_overwrite_silently(client):
    eid = _login(client)
    sheet = _sheet(client, eid)
    body = {"mapping": sheet["mapping"], "rows": sheet["rows"]}
    client.post(f"/api/events/{eid}/imports/commit", json=body)
    # RSVP state on an existing invitation must survive re-import
    # re-import same file: everything conflicts, default is skip
    prev = client.post(f"/api/events/{eid}/imports/preview", json=body).json()
    assert prev["counts"]["conflict"] == 3 and all(r["default_action"] == "skip" for r in prev["rows"])
    assert client.post(f"/api/events/{eid}/imports/commit", json=body).json() == {"created": 0, "updated": 0, "skipped": 3}
    assert client.get(f"/api/events/{eid}/invitations").json()["total"] == 3
    # explicit choices: update row 0, import row 1 as new
    res = client.post(f"/api/events/{eid}/imports/commit", json={**body, "actions": {"0": "update", "1": "new"}}).json()
    assert res == {"created": 1, "updated": 1, "skipped": 1}
    assert client.get(f"/api/events/{eid}/invitations").json()["total"] == 4
