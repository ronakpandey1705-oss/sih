import io
import uuid
from PIL import Image


def _png_bytes(color=(200, 30, 30)):
    buf = io.BytesIO()
    Image.new("RGB", (64, 48), color).save(buf, format="PNG")
    return buf.getvalue()


def _signup(client, **overrides):
    payload = {
        "name": "Test Officer",
        "email": f"officer.{uuid.uuid4().hex[:8]}@example.gov.in",
        "password": "StrongPass#1",
        "designation": "Inspector",
        "jurisdiction": "Pune",
    }
    payload.update(overrides)
    return client.post("/api/auth/signup", json=payload), payload


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_signup_login_and_me(client):
    res, payload = _signup(client)
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["token"]
    assert data["officer"]["email"] == payload["email"]
    assert data["officer"]["officer_badge"].startswith("LM-2026-")

    login = client.post("/api/auth/login", json={"email": payload["email"].upper(), "password": payload["password"]})
    assert login.status_code == 200
    token = login.json()["token"]

    me = client.get("/api/auth/me", headers=_auth(token))
    assert me.status_code == 200
    assert me.json()["email"] == payload["email"]


def test_signup_duplicate_email_rejected(client):
    res, payload = _signup(client)
    assert res.status_code == 201
    dup, _ = _signup(client, email=payload["email"])
    assert dup.status_code == 409


def test_signup_short_password_rejected(client):
    res, _ = _signup(client, password="short")
    assert res.status_code == 422


def test_login_wrong_password(client):
    _, payload = _signup(client)
    res = client.post("/api/auth/login", json={"email": payload["email"], "password": "wrong-password"})
    assert res.status_code == 401


def test_me_rejects_missing_and_tampered_token(client):
    assert client.get("/api/auth/me").status_code == 401
    res, _ = _signup(client)
    token = res.json()["token"]
    tampered = token[:-2] + ("AA" if not token.endswith("AA") else "BB")
    assert client.get("/api/auth/me", headers=_auth(tampered)).status_code == 401


def test_password_account_cannot_use_email_only_verify(client):
    _, payload = _signup(client)
    res = client.post("/api/officers/verify", json={"email": payload["email"], "provider": "email"})
    assert res.status_code == 200
    body = res.json()
    assert body["verified"] is False
    assert body["token"] is None


def test_demo_verify_returns_token(client):
    res = client.post("/api/officers/verify", json={"email": "ronak.pandey@gmail.com", "provider": "demo"})
    body = res.json()
    assert body["verified"] is True
    assert client.get("/api/auth/me", headers=_auth(body["token"])).status_code == 200


def test_public_complaint_flow(client):
    form = {
        "product_name": "Masala Namkeen 200g",
        "brand": "Tasty Co",
        "issue_types": ["MRP_MISSING", "CONSUMER_CARE"],
        "description": "No MRP printed anywhere on the pack.",
        "location": "Nagpur, Maharashtra",
        "store_name": "Local Kirana",
    }
    files = [
        ("photos", ("front.png", _png_bytes(), "image/png")),
        ("photos", ("back.png", _png_bytes((10, 10, 200)), "image/png")),
    ]
    created = client.post("/api/public-complaints", data=form, files=files)
    assert created.status_code == 201, created.text
    ref = created.json()["reference_no"]
    assert created.json()["photo_count"] == 2

    # Anyone can track by reference
    track = client.get(f"/api/public-complaints/track/{ref.lower()}")
    assert track.status_code == 200
    assert track.json()["status"] == "NEW"

    # Officer inbox requires sign-in
    assert client.get("/api/public-complaints").status_code == 401
    assert client.get("/api/public-complaints/summary").status_code == 401

    token = _signup(client)[0].json()["token"]
    summary = client.get("/api/public-complaints/summary", headers=_auth(token)).json()
    assert summary["new_count"] >= 1

    listing = client.get("/api/public-complaints?status=NEW", headers=_auth(token)).json()
    item = next(c for c in listing if c["reference_no"] == ref)
    assert item["issue_types"] == ["MRP_MISSING", "CONSUMER_CARE"]
    assert len(item["photos"]) == 2
    assert item["contact"] is None

    photo = client.get(item["photos"][0]["url"], headers=_auth(token))
    assert photo.status_code == 200
    assert photo.headers["content-type"].startswith("image/")
    assert client.get(item["photos"][0]["url"]).status_code == 401

    updated = client.patch(
        f"/api/public-complaints/{item['id']}",
        json={"status": "under_review", "officer_notes": "Assigned for market check"},
        headers=_auth(token),
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "UNDER_REVIEW"
    assert updated.json()["handled_by_badge"]

    bad = client.patch(f"/api/public-complaints/{item['id']}", json={"status": "CLOSED"}, headers=_auth(token))
    assert bad.status_code == 422

    assert client.get(f"/api/public-complaints/track/{ref}").json()["status"] == "UNDER_REVIEW"


def test_public_complaint_without_photos_and_comma_issue_list(client):
    res = client.post("/api/public-complaints", data={
        "product_name": "Juice 1L",
        "issue_types": "NET_QUANTITY,EXPIRY_DATE",
        "description": "Quantity and expiry missing",
        "location": "Delhi",
        "contact": "9999999999",
    })
    assert res.status_code == 201, res.text
    assert res.json()["photo_count"] == 0


def test_public_complaint_validation(client):
    base = {"product_name": "X", "description": "Y", "location": "Z"}
    assert client.post("/api/public-complaints", data={**base, "issue_types": "NOT_A_CODE"}).status_code == 422
    bad_file = [("photos", ("notes.txt", b"hello", "text/plain"))]
    res = client.post("/api/public-complaints", data={**base, "issue_types": "OTHER"}, files=bad_file)
    assert res.status_code == 400
    assert client.get("/api/public-complaints/track/PC-0000-NOPE").status_code == 404
