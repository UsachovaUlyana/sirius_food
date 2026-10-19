# users/router.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import UserCreate
from app.modules.users.repository import UserRepository
from app.modules.users.service import UserService, NotFoundError, ForbiddenError

router = APIRouter()


@router.post("/register")
def register_user(payload: UserCreate, db: Session = Depends(get_db)):
    # Формат email проверяет Pydantic (EmailStr).
    # Техническая валидация формата телефона.
    if payload.phone and len(payload.phone) < 10:
        raise HTTPException(status_code=400, detail="Некорректный формат номера телефона")

    # Сборка архитектурных слоёв.
    service = UserService(UserRepository(db))

    try:
        result = service.register_user(payload.email, payload.phone)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"status": "success", **result}


@router.post("/{user_id}/topup")
def top_up_balance(user_id: int, amount: float, db: Session = Depends(get_db)):
    # Техническая валидация положительности суммы.
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Сумма пополнения должна быть положительной")

    service = UserService(UserRepository(db))

    try:
        new_balance = service.top_up_balance(user_id, amount)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"status": "success", "new_balance": new_balance}
