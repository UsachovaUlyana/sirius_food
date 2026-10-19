"""
Проверка принципа подстановки: тот же router.py и service.py работают
с in-memory репозиторием вместо PostgreSQL (REPO_BACKEND=memory).
Ни один файл router.py / service.py при этом не меняется.
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.orders.router import router as orders_router
from app.modules.orders import repository as orders_repo
from app.modules.users.router import router as users_router
from app.modules.users import repository as users_repo


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("REPO_BACKEND", "memory")
    monkeypatch.setattr(orders_repo, "memory_repository", orders_repo.InMemoryOrderRepository())
    monkeypatch.setattr(users_repo, "memory_repository", users_repo.InMemoryUserRepository())
    app = FastAPI()
    app.include_router(orders_router, prefix="/orders")
    app.include_router(users_router, prefix="/users")
    return TestClient(app)


def test_register_and_topup(client):
    r = client.post("/users/register", json={"email": "a@b.ru"})
    assert r.status_code == 200
    assert r.json() == {"status": "success", "user_id": 1, "email": "a@b.ru"}
    r = client.post("/users/1/topup", params={"amount": 100})
    assert r.json() == {"status": "success", "new_balance": 100.0}


def test_register_duplicate_is_400(client):
    client.post("/users/register", json={"email": "a@b.ru"})
    r = client.post("/users/register", json={"email": "a@b.ru"})
    assert r.status_code == 400


def test_topup_user_not_found_is_404(client):
    assert client.post("/users/5/topup", params={"amount": 10}).status_code == 404


def test_topup_blocked_is_403(client):
    client.post("/users/register", json={"email": "a@b.ru"})
    users_repo.memory_repository.users[1].is_blocked = True
    assert client.post("/users/1/topup", params={"amount": 10}).status_code == 403


def test_create_order_success(client):
    orders_repo.memory_repository.add_user(1, 500)
    orders_repo.memory_repository.add_menu_item(1, 100)
    r = client.post("/orders/create", json={"user_id": 1, "item_id": 1, "quantity": 2})
    assert r.status_code == 200
    assert r.json() == {"status": "success", "order_id": 1}
    assert orders_repo.memory_repository.users[1].balance == 300


def test_create_order_errors_map_to_http_codes(client):
    orders_repo.memory_repository.add_user(1, 10)
    orders_repo.memory_repository.add_menu_item(1, 100)
    body = {"user_id": 1, "item_id": 1, "quantity": 1}
    assert client.post("/orders/create", json={**body, "quantity": 0}).status_code == 400
    assert client.post("/orders/create", json={**body, "user_id": 9}).status_code == 404
    assert client.post("/orders/create", json={**body, "item_id": 9}).status_code == 404
    assert client.post("/orders/create", json=body).status_code == 400  # мало денег
