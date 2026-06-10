import os

# Use an isolated SQLite DB for tests - must be set BEFORE importing the app
os.environ["DATABASE_URL"] = "sqlite:///./test_expenses.db"

from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def test_health():
    with TestClient(app) as client:
        resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_create_expense_returns_201():
    with TestClient(app) as client:
        resp = client.post(
            "/expenses",
            json={"description": "pizza", "amount": 45.0, "category": "food"},
        )
    assert resp.status_code == 201
    body = resp.json()
    assert body["description"] == "pizza"
    assert body["amount"] == 45.0
    assert body["id"] == 1


def test_create_rejects_negative_amount():
    with TestClient(app) as client:
        resp = client.post(
            "/expenses",
            json={"description": "bug", "amount": -5, "category": "food"},
        )
    assert resp.status_code == 422


def test_list_expenses():
    with TestClient(app) as client:
        client.post("/expenses", json={"description": "bus", "amount": 6, "category": "transport"})
        client.post("/expenses", json={"description": "pizza", "amount": 45, "category": "food"})
        resp = client.get("/expenses")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_delete_expense():
    with TestClient(app) as client:
        created = client.post(
            "/expenses", json={"description": "coffee", "amount": 12, "category": "food"}
        ).json()
        resp = client.delete(f"/expenses/{created['id']}")
        assert resp.status_code == 204
        assert client.get("/expenses").json() == []


def test_delete_missing_expense_returns_404():
    with TestClient(app) as client:
        resp = client.delete("/expenses/999")
    assert resp.status_code == 404


def test_summary_groups_by_category():
    with TestClient(app) as client:
        client.post("/expenses", json={"description": "pizza", "amount": 45, "category": "food"})
        client.post("/expenses", json={"description": "coffee", "amount": 12, "category": "food"})
        client.post("/expenses", json={"description": "bus", "amount": 6, "category": "transport"})
        resp = client.get("/summary")
    assert resp.status_code == 200
    totals = {row["category"]: row["total"] for row in resp.json()}
    assert totals == {"food": 57.0, "transport": 6.0}
