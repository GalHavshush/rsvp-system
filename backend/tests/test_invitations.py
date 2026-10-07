def _event(client):
    client.post("/api/auth/setup", json={"email": "o@example.com", "password": "correct-horse"})
    return client.post("/api/events", json={"name": "W"}).json()["id"]


COHEN = {
    "display_name": "Cohen Family", "group_name": "Groom Family",
    "members": [{"name": "David"}, {"name": "Yael"}, {"name": "Noa"}],
    "contacts": [{"phone": "050-1234567", "member_index": 0}, {"phone": "0521234567", "member_index": 1}, {"phone": "bad"}],
}


def test_create_normalized_structure(client):
    eid = _event(client)
    inv = client.post(f"/api/events/{eid}/invitations", json=COHEN).json()
    assert inv["rsvp_status"] == "no_response" and inv["attendee_count"] is None
    assert len(inv["rsvp_token"]) >= 32
    assert [m["name"] for m in inv["members"]] == ["David", "Yael", "Noa"]
    c = inv["contacts"]
    assert c[0]["phone_e164"] == "+972501234567" and c[0]["member_id"] == inv["members"][0]["id"]
    assert c[2]["phone_valid"] is False and c[2]["phone_e164"] is None and c[2]["member_id"] is None


def test_update_replaces_members_and_keeps_rsvp_and_token(client):
    eid = _event(client)
    inv = client.post(f"/api/events/{eid}/invitations", json=COHEN).json()
    new = {**COHEN, "members": [{"name": "David"}], "contacts": [{"phone": "0541112222", "member_index": 0}], "group_name": "Army"}
    out = client.put(f"/api/invitations/{inv['id']}", json=new).json()
    assert [m["name"] for m in out["members"]] == ["David"] and len(out["contacts"]) == 1
    assert out["group_name"] == "Army" and out["rsvp_token"] == inv["rsvp_token"]


def test_bad_member_index_rejected(client):
    eid = _event(client)
    bad = {**COHEN, "contacts": [{"phone": "0501234567", "member_index": 9}]}
    assert client.post(f"/api/events/{eid}/invitations", json=bad).status_code == 422


def test_filters_search_sort_delete(client):
    eid = _event(client)
    client.post(f"/api/events/{eid}/invitations", json=COHEN)
    client.post(f"/api/events/{eid}/invitations", json={"display_name": "Gal", "members": [{"name": "Gal"}]})
    url = f"/api/events/{eid}/invitations"
    total = lambda **p: client.get(url, params=p).json()["total"]
    assert total() == 2
    assert total(missing_phone=True) == 1 and total(invalid_phone=True) == 1
    assert total(q="yael") == 1 and total(q="1234567") == 1 and total(q="nobody") == 0
    assert total(rsvp_status="coming") == 0 and total(rsvp_status="no_response") == 2
    gid = client.get(f"/api/events/{eid}/groups").json()[0]["id"]
    assert total(group_id=gid) == 1
    assert [i["display_name"] for i in client.get(url, params={"sort": "-name"}).json()["items"]] == ["Gal", "Cohen Family"]
    cid = client.get(url, params={"q": "Cohen"}).json()["items"][0]["id"]
    assert client.delete(f"/api/invitations/{cid}").status_code == 204 and total() == 1


def test_deleting_event_deletes_guest_data(client):
    eid = _event(client)
    client.post(f"/api/events/{eid}/invitations", json=COHEN)
    client.delete(f"/api/events/{eid}")
    from sqlalchemy import text
    from app.core.db import engine
    with engine.connect() as c:
        for t in ("invitation", "invitation_member", "invitation_contact", "guest_group"):
            assert c.execute(text(f"select count(*) from {t}")).scalar() == 0


def test_export_roundtrips_import_shape_and_is_excel_safe(client):
    eid = _event(client)
    client.post(f"/api/events/{eid}/invitations", json={**COHEN, "display_name": "=EVIL()"})
    r = client.get(f"/api/events/{eid}/invitations/export", params={"lang": "en"})
    assert r.content.startswith(b"\xef\xbb\xbf")
    lines = r.content.decode("utf-8-sig").splitlines()
    assert lines[0].startswith("Invitation Name,Group,Status,Attendees,Notes,Person 1,Phone 1,Person 2,Phone 2,Person 3,Phone 3")
    assert lines[1].startswith("'=EVIL(),Groom Family,No response")
    assert "David,050-1234567" in lines[1] and ",,bad" in lines[1]


def test_endpoints_require_login(client):
    client.post("/api/auth/logout")
    assert client.get("/api/events/1/invitations").status_code == 401
    assert client.post("/api/events/1/imports/preview", json={"mapping": [], "rows": []}).status_code == 401
