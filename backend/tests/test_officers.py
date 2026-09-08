def test_get_demo_officers(client):
    res = client.get("/api/officers/demo")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 4
    emails = [o["email"] for o in data]
    assert "ronak.pandey@gmail.com" in emails
    assert "himanshu.verma@gmail.com" in emails
    assert "vibha.pawar@yahoo.com" in emails
    assert "harsh.nagvekar@icloud.com" in emails


def test_verify_registered_officer(client):
    payload = {
        "email": "ronak.pandey@gmail.com",
        "provider": "gmail",
    }
    res = client.post("/api/officers/verify", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["verified"] is True
    assert data["officer"] is not None
    assert data["officer"]["name"] == "Ronak Pandey"
    assert data["officer"]["officer_badge"] == "LM-2026-001"
    assert "Enforcement Officer" in data["officer"]["designation"]


def test_verify_case_insensitive_email(client):
    payload = {
        "email": "HIMANSHU.VERMA@GMAIL.COM",
        "provider": "gmail",
    }
    res = client.post("/api/officers/verify", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["verified"] is True
    assert data["officer"]["name"] == "Himanshu Verma"
    assert data["officer"]["officer_badge"] == "LM-2026-002"


def test_verify_unregistered_email_triggers_helpdesk_ticket(client):
    unregistered_email = "unauthorized.citizen@gmail.com"
    payload = {
        "email": unregistered_email,
        "provider": "gmail",
        "claimed_name": "Test Citizen"
    }
    res = client.post("/api/officers/verify", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["verified"] is False
    assert data["officer"] is None
    assert "ticket_no" in data
    assert data["ticket_no"].startswith("LM-HLP-")
    assert "Helpdesk" in data["message"]

    # Check that ticket exists in helpdesk queue
    tickets_res = client.get("/api/officers/tickets")
    assert tickets_res.status_code == 200
    ticket_data = tickets_res.json()
    ticket_numbers = [t["ticket_no"] for t in ticket_data]
    assert data["ticket_no"] in ticket_numbers


def test_verify_empty_email_rejected(client):
    res = client.post("/api/officers/verify", json={"email": "   "})
    assert res.status_code == 400
