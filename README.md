# Сириус.Еда — рефакторинг в Clean Architecture

Лабораторная работа № 2. Отрефакторены два модуля: **orders** (разбор вместе с преподавателем)
и **users** (самостоятельно). Модули `menu` и `delivery` остались в MVP-виде.

## Запуск

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
sudo docker-compose up -d db redis
uvicorn app.main:app --reload      # http://127.0.0.1:8000/docs
pytest                             # unit-тесты, СУБД не нужна
```

## Что изменилось

Каждый из модулей `orders` и `users` разделён на три файла:

| Файл | Слой | Круг модели Мартина | Что делает |
|---|---|---|---|
| `router.py` | API (транспортный) | 4. Frameworks & Drivers | принимает HTTP, техническая валидация, перевод исключений в HTTP-статусы |
| `service.py` | Бизнес-логика | 1–2. Entities, Use Cases | бизнес-правила, сценарий; **нет импортов `fastapi` и `sqlalchemy`** |
| `repository.py` | Инфраструктура | 3. Interface Adapters | SQL-запросы и транзакции через ORM |

* Репозиторий передаётся в сервис через конструктор (инверсия зависимостей).
* В `repository.py` выделен абстрактный класс (`AbstractOrderRepository`, `AbstractUserRepository`, ABC)
  и две реализации: **PostgreSQL** (SQLAlchemy) и **in-memory** (для тестов).
* Реализация выбирается функцией `get_repository` по переменной окружения `REPO_BACKEND`
  (`postgres` по умолчанию, `memory`). `service.py` и `router.py` при смене реализации не меняются.
* Бизнес-ошибки сервис сообщает через `ValueError` и его наследников
  (`NotFoundError` → 404, `ForbiddenError` → 403, остальные → 400).
  Благодаря этому HTTP-коды остаются теми же, что в MVP, а сервис ничего не знает про HTTP.

### Путь запроса через слои

```
POST /orders/create
        |
        v
+--------------------+   Pydantic-схема OrderCreate, quantity > 0 (техническая валидация)
|  router.py (API)   |   собирает слои: get_repository(db) -> OrderService(repository)
+--------------------+   ValueError -> HTTPException 400/404
        |  service.create_order(user_id, item_id, quantity)
        v
+--------------------+   бизнес-правила: пользователь и блюдо существуют,
|  service.py        |   блюдо доступно, хватает баланса; списывает баланс
|  (бизнес-логика)   |   (нет fastapi и sqlalchemy)
+--------------------+
        |  AbstractOrderRepository: get_user_by_id / get_menu_item_by_id /
        |                           update_user_balance / save_order
        v
+--------------------+       +------------------------------+
| repository.py      |  ---> | PostgreSQL (SQLAlchemy ORM)  |   REPO_BACKEND=postgres
| (инфраструктура)   |  ---> | in-memory (словари в памяти) |   REPO_BACKEND=memory
+--------------------+       +------------------------------+

Зависимости направлены снаружи внутрь: router -> service -> (абстракция репозитория) <- repository
```

### Особенности

* Тексты ошибок и структура ответов оставлены как в MVP (в примере из методички
  тексты двух сообщений другие, но задание требует идентичных ответов).
* В `users/register` проверка формата телефона (техническая) теперь выполняется в `router.py`
  раньше проверки уникальности email (бизнес-правило, в `service.py`). Если email занят и телефон
  некорректен одновременно, ответ будет про телефон, а не про email (в MVP наоборот).

## Тесты

`pytest` — 17 тестов, СУБД и веб-сервер не нужны:

* `tests/test_orders_service.py`, `tests/test_users_service.py` — unit-тесты `service.py`
  с `InMemory*Repository`;
* `tests/test_api_memory_backend.py` — весь путь `router -> service -> repository` с `REPO_BACKEND=memory`.

## История коммитов

Коммиты отражают процесс: исходный MVP -> `orders` (шаги 1–3) -> `users` (шаги 1–3) ->
unit-тесты -> абстрактные репозитории и in-memory реализации.
Посмотреть: `git log --oneline`.
