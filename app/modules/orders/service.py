# orders/service.py
from app.modules.orders.repository import OrderRepository


class NotFoundError(ValueError):
    """Сущность не найдена. Наследник ValueError: транспортный слой
    отличает его от прочих нарушений правил и отвечает кодом 404, как в MVP."""


class OrderService:
    """
    Класс инкапсулирует бизнес-правила обработки заказов.
    Не имеет зависимостей от инфраструктурных фреймворков.
    """

    def __init__(self, repository: OrderRepository):
        # Внедрение зависимости через конструктор.
        self.repository = repository

    def create_order(self, user_id: int, item_id: int, quantity: int) -> int:
        """
        Исполнение сценария оформления заказа.
        Возвращает идентификатор созданного заказа.
        Возбуждает ValueError при нарушении бизнес-правил.
        """
        user = self.repository.get_user_by_id(user_id)
        if not user:
            raise NotFoundError("Пользователь не найден")

        item = self.repository.get_menu_item_by_id(item_id)
        if not item:
            raise NotFoundError("Блюдо не найдено")

        if not item.is_available:
            raise ValueError("Блюдо недоступно")

        total_cost = item.price * quantity
        if user.balance < total_cost:
            raise ValueError("Недостаточно средств на балансе студента")

        # Изменение состояния доменных данных.
        user.balance -= total_cost
        self.repository.update_user_balance(user, user.balance)

        # Делегирование операции сохранения инфраструктурному слою.
        order_id = self.repository.save_order(user_id, item_id, quantity)
        return order_id
