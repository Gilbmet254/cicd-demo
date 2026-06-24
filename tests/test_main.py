from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_create_and_get_item():
    create_resp = client.post(
        "/items", json={"name": "Widget", "price": 9.99, "in_stock": True}
    )
    assert create_resp.status_code == 201
    created = create_resp.json()
    assert created["name"] == "Widget"
    assert "id" in created

    get_resp = client.get(f"/items/{created['id']}")
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "Widget"


def test_list_items():
    client.post("/items", json={"name": "Gadget", "price": 5.0})
    response = client.get("/items")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1


def test_get_item_not_found():
    response = client.get("/items/99999")
    assert response.status_code == 404


def test_delete_item():
    create_resp = client.post("/items", json={"name": "Temp", "price": 1.0})
    item_id = create_resp.json()["id"]

    delete_resp = client.delete(f"/items/{item_id}")
    assert delete_resp.status_code == 204

    get_resp = client.get(f"/items/{item_id}")
    assert get_resp.status_code == 404


def test_delete_item_not_found():
    response = client.delete("/items/99999")
    assert response.status_code == 404


def test_create_item_validation_error():
    response = client.post("/items", json={"name": "Bad"})  # missing price
    assert response.status_code == 422
