"""
Модуль управления пользователями.
В исходной MVP-версии содержит смешение слоёв.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas import UserCreate

router = APIRouter()


@router.post("/register")
def register_user(payload: UserCreate, db: Session = Depends(get_db)):
    # Проверка корректности email выполняется Pydantic (EmailStr).
    # Проверка уникальности email требует обращения к СУБД.
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Пользователь с таким email уже зарегистрирован",
        )

    # Техническая проверка наличия телефона.
    if payload.phone and len(payload.phone) < 10:
        raise HTTPException(
            status_code=400,
            detail="Некорректный формат номера телефона",
        )

    # Создание пользователя с нулевым балансом.
    new_user = User(
        email=payload.email,
        phone=payload.phone,
        balance=0.0,
        is_blocked=False,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "status": "success",
        "user_id": new_user.id,
        "email": new_user.email,
    }


@router.post("/{user_id}/topup")
def top_up_balance(user_id: int, amount: float, db: Session = Depends(get_db)):
    # Техническая проверка положительности суммы пополнения.
    if amount <= 0:
        raise HTTPException(
            status_code=400,
            detail="Сумма пополнения должна быть положительной",
        )

    # Бизнес-правило: пополнение запрещено для заблокированных пользователей.
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    if user.is_blocked:
        raise HTTPException(
            status_code=403,
            detail="Пользователь заблокирован. Пополнение невозможно",
        )

    # Бизнес-правило: максимальная сумма одного пополнения.
    if amount > 50000:
        raise HTTPException(
            status_code=400,
            detail="Максимальная сумма пополнения — 50000 рублей",
        )

    user.balance += amount
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"status": "success", "new_balance": user.balance}
