# users/repository.py
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass

from sqlalchemy.orm import Session
from app.models import User


class AbstractUserRepository(ABC):
    """Контракт хранилища пользователей. Сервис зависит только от него."""

    @abstractmethod
    def get_user_by_id(self, user_id: int):
        """Извлечение пользователя по идентификатору."""

    @abstractmethod
    def get_user_by_email(self, email: str):
        """Извлечение пользователя по email."""

    @abstractmethod
    def save_user(self, email: str, phone: str | None):
        """Создание пользователя с нулевым балансом. Возвращает созданного пользователя."""

    @abstractmethod
    def update_user_balance(self, user, new_balance: float) -> None:
        """Изменение значения баланса пользователя."""


class UserRepository(AbstractUserRepository):
    """
    Реализация 1: PostgreSQL через SQLAlchemy ORM.
    Бизнес-правила в данном классе отсутствуют.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_user_by_id(self, user_id: int):
        return self.db.query(User).filter(User.id == user_id).first()

    def get_user_by_email(self, email: str):
        return self.db.query(User).filter(User.email == email).first()

    def save_user(self, email: str, phone: str | None):
        new_user = User(
            email=email,
            phone=phone,
            balance=0.0,
            is_blocked=False,
        )
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        return new_user

    def update_user_balance(self, user, new_balance: float) -> None:
        user.balance = new_balance
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)


@dataclass
class UserRecord:
    id: int
    email: str
    phone: str | None
    balance: float = 0.0
    is_blocked: bool = False


class InMemoryUserRepository(AbstractUserRepository):
    """Реализация 2: хранилище в оперативной памяти (для тестов и демо без СУБД)."""

    def __init__(self):
        self.users = {}

    def get_user_by_id(self, user_id: int):
        return self.users.get(user_id)

    def get_user_by_email(self, email: str):
        return next((u for u in self.users.values() if u.email == email), None)

    def save_user(self, email: str, phone: str | None):
        user = UserRecord(id=len(self.users) + 1, email=email, phone=phone)
        self.users[user.id] = user
        return user

    def update_user_balance(self, user, new_balance: float) -> None:
        user.balance = new_balance


# Единственный экземпляр in-memory хранилища на процесс.
memory_repository = InMemoryUserRepository()


def get_repository(db: Session) -> AbstractUserRepository:
    """
    Выбор реализации хранилища по переменной окружения REPO_BACKEND
    ("postgres" по умолчанию или "memory"). Остальной код об этом не знает.
    """
    if os.getenv("REPO_BACKEND", "postgres") == "memory":
        return memory_repository
    return UserRepository(db)
