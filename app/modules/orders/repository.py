# orders/repository.py
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass

from sqlalchemy.orm import Session
from app.models import Order, User, MenuItem


class AbstractOrderRepository(ABC):
    """Контракт хранилища заказов. Сервис зависит только от него."""

    @abstractmethod
    def get_user_by_id(self, user_id: int):
        """Извлечение объекта пользователя по идентификатору."""

    @abstractmethod
    def get_menu_item_by_id(self, item_id: int):
        """Извлечение объекта блюда из меню по идентификатору."""

    @abstractmethod
    def save_order(self, user_id: int, item_id: int, quantity: int) -> int:
        """Создание заказа. Возвращает идентификатор созданного заказа."""

    @abstractmethod
    def update_user_balance(self, user, new_balance: float) -> None:
        """Изменение значения баланса пользователя."""


class OrderRepository(AbstractOrderRepository):
    """
    Реализация 1: PostgreSQL через SQLAlchemy ORM.
    Бизнес-правила в данном классе отсутствуют.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_user_by_id(self, user_id: int):
        return self.db.query(User).filter(User.id == user_id).first()

    def get_menu_item_by_id(self, item_id: int):
        return self.db.query(MenuItem).filter(MenuItem.id == item_id).first()

    def save_order(self, user_id: int, item_id: int, quantity: int) -> int:
        new_order = Order(
            user_id=user_id,
            item_id=item_id,
            quantity=quantity,
            status="processing",
        )
        self.db.add(new_order)
        self.db.commit()
        self.db.refresh(new_order)
        return new_order.id

    def update_user_balance(self, user, new_balance: float) -> None:
        user.balance = new_balance
        self.db.add(user)
        self.db.commit()


@dataclass
class UserRecord:
    id: int
    balance: float


@dataclass
class MenuItemRecord:
    id: int
    price: float
    is_available: bool = True


class InMemoryOrderRepository(AbstractOrderRepository):
    """Реализация 2: хранилище в оперативной памяти (для тестов и демо без СУБД)."""

    def __init__(self):
        self.users = {}
        self.items = {}
        self.orders = []

    def add_user(self, user_id: int, balance: float) -> None:
        self.users[user_id] = UserRecord(user_id, balance)

    def add_menu_item(self, item_id: int, price: float, is_available: bool = True) -> None:
        self.items[item_id] = MenuItemRecord(item_id, price, is_available)

    def get_user_by_id(self, user_id: int):
        return self.users.get(user_id)

    def get_menu_item_by_id(self, item_id: int):
        return self.items.get(item_id)

    def save_order(self, user_id: int, item_id: int, quantity: int) -> int:
        self.orders.append((user_id, item_id, quantity))
        return len(self.orders)

    def update_user_balance(self, user, new_balance: float) -> None:
        user.balance = new_balance


# Единственный экземпляр in-memory хранилища на процесс.
memory_repository = InMemoryOrderRepository()


def get_repository(db: Session) -> AbstractOrderRepository:
    """
    Выбор реализации хранилища по переменной окружения REPO_BACKEND
    ("postgres" по умолчанию или "memory"). Остальной код об этом не знает.
    """
    if os.getenv("REPO_BACKEND", "postgres") == "memory":
        return memory_repository
    return OrderRepository(db)
