# users/repository.py
from sqlalchemy.orm import Session
from app.models import User


class UserRepository:
    """
    Класс отвечает исключительно за операции ввода-вывода с таблицей users
    через SQLAlchemy ORM. Бизнес-правила в данном классе отсутствуют.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_user_by_id(self, user_id: int):
        """Извлечение пользователя по идентификатору."""
        return self.db.query(User).filter(User.id == user_id).first()

    def get_user_by_email(self, email: str):
        """Извлечение пользователя по email."""
        return self.db.query(User).filter(User.email == email).first()

    def save_user(self, email: str, phone: str | None):
        """Создание пользователя с нулевым балансом. Возвращает созданного пользователя."""
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
        """Изменение значения баланса пользователя с фиксацией транзакции."""
        user.balance = new_balance
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
