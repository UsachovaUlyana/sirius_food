"""
Unit-тесты слоя бизнес-логики orders/service.py.
СУБД и веб-сервер не запускаются: вместо PostgreSQL используется InMemoryOrderRepository.
"""
import pytest

from app.modules.orders.repository import InMemoryOrderRepository
from app.modules.orders.service import OrderService, NotFoundError


def make_service(balance=500.0, price=100.0, available=True, user=True, item=True):
    repo = InMemoryOrderRepository()
    if user:
        repo.add_user(1, balance)
    if item:
        repo.add_menu_item(1, price, available)
    return OrderService(repo), repo


def test_create_order_success_deducts_balance_and_saves_order():
    service, repo = make_service(balance=500, price=100)
    order_id = service.create_order(user_id=1, item_id=1, quantity=3)
    assert order_id == 1
    assert repo.users[1].balance == 200
    assert repo.orders == [(1, 1, 3)]


def test_create_order_not_enough_money():
    service, repo = make_service(balance=50, price=100)
    with pytest.raises(ValueError, match="Недостаточно средств"):
        service.create_order(1, 1, 1)
    assert repo.users[1].balance == 50
    assert repo.orders == []


def test_create_order_item_unavailable():
    service, _ = make_service(available=False)
    with pytest.raises(ValueError, match="Блюдо недоступно"):
        service.create_order(1, 1, 1)


def test_create_order_user_not_found():
    service, _ = make_service(user=False)
    with pytest.raises(NotFoundError):
        service.create_order(1, 1, 1)


def test_create_order_item_not_found():
    service, _ = make_service(item=False)
    with pytest.raises(NotFoundError):
        service.create_order(1, 1, 1)
