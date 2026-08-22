from fastapi.testclient import TestClient


def test_list_companies_empty(client: TestClient) -> None:
    resp = client.get("/companies/")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_company(client: TestClient) -> None:
    resp = client.post("/companies/", json={"name": "Acme"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Acme"
    assert data["contact_names"] == []


def test_update_company(client: TestClient) -> None:
    created = client.post("/companies/", json={"name": "Globex"}).json()
    resp = client.patch(f"/companies/{created['id']}", json={"stage": "Series A"})
    assert resp.status_code == 200
    assert resp.json()["stage"] == "Series A"
    assert resp.json()["name"] == "Globex"


def test_company_shows_linked_contacts(client: TestClient) -> None:
    company = client.post("/companies/", json={"name": "Initech"}).json()
    client.post("/contacts/", json={"name": "Dave", "company_id": company["id"]})
    resp = client.get("/companies/")
    initech = next(c for c in resp.json() if c["id"] == company["id"])
    assert "Dave" in initech["contact_names"]


def test_delete_company_nullifies_contacts(client: TestClient) -> None:
    company = client.post("/companies/", json={"name": "Umbrella"}).json()
    contact = client.post(
        "/contacts/", json={"name": "Eve", "company_id": company["id"]}
    ).json()
    client.delete(f"/companies/{company['id']}")
    updated = client.get("/contacts/").json()
    eve = next(c for c in updated if c["id"] == contact["id"])
    assert eve["company_id"] is None


def test_delete_nonexistent_company(client: TestClient) -> None:
    resp = client.delete("/companies/does-not-exist")
    assert resp.status_code == 404
