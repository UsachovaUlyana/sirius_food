"""
Unit-тесты слоя бизнес-логики orders/service.py.
СУБД и веб-сервер не запускаются: вместо репозитория используется заглушка.
"""
from types import SimpleNamespace

import pytest

from app.modules.orders.service import OrderService, NotFoundError


class FakeOrderRepository:
    """Заглушка репозитория: данные лежат в памяти."""

    def __init__(self, user=None, item=None):
        self.user = user
        self.item = item
        self.saved_orders = []

    def get_user_by_id(self, user_id):
        return self.user

    def get_menu_item_by_id(self, item_id):
        return self.item

    def save_order(self, user_id, item_id, quantity):
        self.saved_orders.append((user_id, item_id, quantity))
        return len(self.saved_orders)

    def update_user_balance(self, user, new_balance):
        user.balance = new_balance


def make_service(balance=500.0, price=100.0, available=True, user=True, item=True):
    repo = FakeOrderRepository(
        user=SimpleNamespace(id=1, balance=balance) if user else None,
        item=SimpleNamespace(id=1, price=price, is_available=available) if item else None,
    )
    return OrderService(repo), repo


def test_create_order_success_deducts_balance_and_saves_order():
    service, repo = make_service(balance=500, price=100)
    order_id = service.create_order(user_id=1, item_id=1, quantity=3)
    assert order_id == 1
    assert repo.user.balance == 200
    assert repo.saved_orders == [(1, 1, 3)]


def test_create_order_not_enough_money():
    service, repo = make_service(balance=50, price=100)
    with pytest.raises(ValueError, match="Недостаточно средств"):
        service.create_order(1, 1, 1)
    assert repo.user.balance == 50
    assert repo.saved_orders == []


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
