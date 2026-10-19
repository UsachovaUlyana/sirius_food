"""
Unit-тесты слоя бизнес-логики users/service.py (без СУБД и веб-сервера).
Вместо PostgreSQL используется InMemoryUserRepository.
"""
import pytest

from app.modules.users.repository import InMemoryUserRepository
from app.modules.users.service import UserService, NotFoundError, ForbiddenError


def test_register_user_success():
    service = UserService(InMemoryUserRepository())
    assert service.register_user("a@b.ru", None) == {"user_id": 1, "email": "a@b.ru"}


def test_register_user_duplicate_email():
    service = UserService(InMemoryUserRepository())
    service.register_user("a@b.ru", None)
    with pytest.raises(ValueError, match="уже зарегистрирован"):
        service.register_user("a@b.ru", None)


def test_top_up_success():
    repo = InMemoryUserRepository()
    service = UserService(repo)
    service.register_user("a@b.ru", None)
    assert service.top_up_balance(1, 100) == 100
    assert service.top_up_balance(1, 50) == 150


def test_top_up_user_not_found():
    with pytest.raises(NotFoundError):
        UserService(InMemoryUserRepository()).top_up_balance(1, 100)


def test_top_up_blocked_user():
    repo = InMemoryUserRepository()
    service = UserService(repo)
    service.register_user("a@b.ru", None)
    repo.users[1].is_blocked = True
    with pytest.raises(ForbiddenError):
        service.top_up_balance(1, 100)


def test_top_up_over_limit():
    repo = InMemoryUserRepository()
    service = UserService(repo)
    service.register_user("a@b.ru", None)
    with pytest.raises(ValueError, match="50000"):
        service.top_up_balance(1, 50001)
    assert repo.users[1].balance == 0
