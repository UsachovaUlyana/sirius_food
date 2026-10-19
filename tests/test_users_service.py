"""
Unit-тесты слоя бизнес-логики users/service.py (без СУБД и веб-сервера).
"""
from types import SimpleNamespace

import pytest

from app.modules.users.service import UserService, NotFoundError, ForbiddenError


class FakeUserRepository:
    def __init__(self):
        self.users = {}

    def get_user_by_id(self, user_id):
        return self.users.get(user_id)

    def get_user_by_email(self, email):
        return next((u for u in self.users.values() if u.email == email), None)

    def save_user(self, email, phone):
        user = SimpleNamespace(id=len(self.users) + 1, email=email, phone=phone,
                               balance=0.0, is_blocked=False)
        self.users[user.id] = user
        return user

    def update_user_balance(self, user, new_balance):
        user.balance = new_balance


def test_register_user_success():
    service = UserService(FakeUserRepository())
    assert service.register_user("a@b.ru", None) == {"user_id": 1, "email": "a@b.ru"}


def test_register_user_duplicate_email():
    service = UserService(FakeUserRepository())
    service.register_user("a@b.ru", None)
    with pytest.raises(ValueError, match="уже зарегистрирован"):
        service.register_user("a@b.ru", None)


def test_top_up_success():
    repo = FakeUserRepository()
    service = UserService(repo)
    service.register_user("a@b.ru", None)
    assert service.top_up_balance(1, 100) == 100
    assert service.top_up_balance(1, 50) == 150


def test_top_up_user_not_found():
    with pytest.raises(NotFoundError):
        UserService(FakeUserRepository()).top_up_balance(1, 100)


def test_top_up_blocked_user():
    repo = FakeUserRepository()
    service = UserService(repo)
    service.register_user("a@b.ru", None)
    repo.users[1].is_blocked = True
    with pytest.raises(ForbiddenError):
        service.top_up_balance(1, 100)


def test_top_up_over_limit():
    repo = FakeUserRepository()
    service = UserService(repo)
    service.register_user("a@b.ru", None)
    with pytest.raises(ValueError, match="50000"):
        service.top_up_balance(1, 50001)
    assert repo.users[1].balance == 0
