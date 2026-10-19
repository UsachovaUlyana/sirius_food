# users/service.py
from app.modules.users.repository import UserRepository

MAX_TOP_UP = 50000


class NotFoundError(ValueError):
    """Пользователь не найден (транспортный слой отвечает кодом 404)."""


class ForbiddenError(ValueError):
    """Операция запрещена правилами предметной области (код 403)."""


class UserService:
    """
    Класс инкапсулирует бизнес-правила работы с пользователями.
    Не имеет зависимостей от инфраструктурных фреймворков.
    """

    def __init__(self, repository: UserRepository):
        # Внедрение зависимости через конструктор.
        self.repository = repository

    def register_user(self, email: str, phone: str | None) -> dict:
        """
        Регистрация пользователя. Возвращает его идентификатор и email.
        Возбуждает ValueError, если email уже занят.
        """
        # Бизнес-правило: email должен быть уникальным.
        if self.repository.get_user_by_email(email):
            raise ValueError("Пользователь с таким email уже зарегистрирован")

        user = self.repository.save_user(email, phone)
        return {"user_id": user.id, "email": user.email}

    def top_up_balance(self, user_id: int, amount: float) -> float:
        """
        Пополнение баланса. Возвращает новый баланс.
        Возбуждает ValueError (и наследников) при нарушении бизнес-правил.
        """
        user = self.repository.get_user_by_id(user_id)
        if not user:
            raise NotFoundError("Пользователь не найден")

        # Бизнес-правило: пополнение запрещено для заблокированных пользователей.
        if user.is_blocked:
            raise ForbiddenError("Пользователь заблокирован. Пополнение невозможно")

        # Бизнес-правило: максимальная сумма одного пополнения.
        if amount > MAX_TOP_UP:
            raise ValueError("Максимальная сумма пополнения — 50000 рублей")

        self.repository.update_user_balance(user, user.balance + amount)
        return user.balance
