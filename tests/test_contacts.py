from fastapi.testclient import TestClient


def test_list_contacts_empty(client: TestClient) -> None:
    resp = client.get("/contacts/")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_contact(client: TestClient) -> None:
    resp = client.post("/contacts/", json={"name": "Alice"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Alice"
    assert data["id"]


def test_update_contact(client: TestClient) -> None:
    created = client.post("/contacts/", json={"name": "Bob"}).json()
    resp = client.patch(f"/contacts/{created['id']}", json={"warmth": "Hot"})
    assert resp.status_code == 200
    assert resp.json()["warmth"] == "Hot"
    assert resp.json()["name"] == "Bob"


def test_delete_contact(client: TestClient) -> None:
    created = client.post("/contacts/", json={"name": "Carol"}).json()
    resp = client.delete(f"/contacts/{created['id']}")
    assert resp.status_code == 204
    contacts = client.get("/contacts/").json()
    assert all(c["id"] != created["id"] for c in contacts)


def test_update_nonexistent_contact(client: TestClient) -> None:
    resp = client.patch("/contacts/does-not-exist", json={"name": "X"})
    assert resp.status_code == 404
