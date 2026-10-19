"""
Модуль управления меню столовой.
В исходной MVP-версии содержит смешение слоёв.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import MenuItem
from app.schemas import MenuItemCreate, MenuItemUpdate

router = APIRouter()


@router.post("/items")
def create_menu_item(payload: MenuItemCreate, db: Session = Depends(get_db)):
    # Техническая валидация цены и названия.
    if payload.price <= 0:
        raise HTTPException(
            status_code=400,
            detail="Цена должна быть положительной",
        )
    if len(payload.name) < 2:
        raise HTTPException(
            status_code=400,
            detail="Название блюда слишком короткое",
        )

    # Бизнес-правило: название блюда должно быть уникальным.
    existing = db.query(MenuItem).filter(MenuItem.name == payload.name).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Блюдо с таким названием уже существует",
        )

    new_item = MenuItem(
        name=payload.name,
        price=payload.price,
        is_available=True,
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)

    return {"status": "success", "item_id": new_item.id}


@router.patch("/items/{item_id}")
def update_menu_item(
    item_id: int,
    payload: MenuItemUpdate,
    db: Session = Depends(get_db),
):
    # Поиск обновляемого блюда.
    item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Блюдо не найдено")

    # Техническая валидация нового значения цены.
    if payload.price is not None and payload.price <= 0:
        raise HTTPException(
            status_code=400,
            detail="Цена должна быть положительной",
        )

    # Применение изменений.
    if payload.name is not None:
        item.name = payload.name
    if payload.price is not None:
        item.price = payload.price
    if payload.is_available is not None:
        item.is_available = payload.is_available

    db.add(item)
    db.commit()
    db.refresh(item)

    return {"status": "success", "item_id": item.id}
