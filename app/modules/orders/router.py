# orders/router.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import OrderCreate
from app.modules.orders.repository import get_repository
from app.modules.orders.service import OrderService, NotFoundError

router = APIRouter()


@router.post("/create")
def create_order(payload: OrderCreate, db: Session = Depends(get_db)):
    # Техническая валидация уровня транспортного протокола.
    if payload.quantity <= 0:
        raise HTTPException(status_code=400, detail="Количество должно быть больше нуля")

    # Сборка архитектурных слоёв.
    repository = get_repository(db)
    service = OrderService(repository)

    # Делегирование выполнения сценария слою бизнес-логики.
    try:
        order_id = service.create_order(
            user_id=payload.user_id,
            item_id=payload.item_id,
            quantity=payload.quantity,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        # Трансляция внутреннего исключения в HTTP-статус.
        raise HTTPException(status_code=400, detail=str(e))

    return {"status": "success", "order_id": order_id}
