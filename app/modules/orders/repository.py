# orders/repository.py
from sqlalchemy.orm import Session
from app.models import Order, User, MenuItem


class OrderRepository:
    """
    Класс отвечает исключительно за выполнение операций ввода-вывода
    в контексте СУБД PostgreSQL с использованием SQLAlchemy ORM.
    Бизнес-правила в данном классе отсутствуют.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_user_by_id(self, user_id: int):
        """Извлечение объекта пользователя по идентификатору."""
        return self.db.query(User).filter(User.id == user_id).first()

    def get_menu_item_by_id(self, item_id: int):
        """Извлечение объекта блюда из меню по идентификатору."""
        return self.db.query(MenuItem).filter(MenuItem.id == item_id).first()

    def save_order(self, user_id: int, item_id: int, quantity: int) -> int:
        """
        Создание новой записи заказа и фиксация транзакции.
        Возвращает идентификатор созданного заказа.
        """
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
        """Изменение значения баланса пользователя с фиксацией транзакции."""
        user.balance = new_balance
        self.db.add(user)
        self.db.commit()
