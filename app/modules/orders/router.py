"""
Модуль управления заказами.
В исходной MVP-версии содержит смешение слоёв: HTTP-обработка,
бизнес-проверки и SQL-запросы находятся в одной функции.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Order, User, MenuItem
from app.schemas import OrderCreate

router = APIRouter()


@router.post("/create")
def create_order(payload: OrderCreate, db: Session = Depends(get_db)):
    # Блок 1: Первичная техническая валидация параметров запроса.
    if payload.quantity <= 0:
        raise HTTPException(
            status_code=400,
            detail="Количество должно быть больше нуля",
        )

    # Блок 2: Бизнес-проверки предметной области с обращением к СУБД.
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    item = db.query(MenuItem).filter(MenuItem.id == payload.item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Блюдо не найдено")

    if not item.is_available:
        raise HTTPException(status_code=400, detail="Блюдо недоступно")

    total_cost = item.price * payload.quantity
    if user.balance < total_cost:
        raise HTTPException(
            status_code=400,
            detail="Недостаточно средств на балансе студента",
        )

    # Блок 3: Инфраструктурный код сохранения изменений.
    user.balance -= total_cost
    new_order = Order(
        user_id=payload.user_id,
        item_id=payload.item_id,
        quantity=payload.quantity,
        status="processing",
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    return {"status": "success", "order_id": new_order.id}
