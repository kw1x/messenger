# HexaChat

Распределённый мессенджер на двух микросервисах. Один отвечает за REST API, регистрацию, аутентификацию и хранение сообщений. Второй держит WebSocket-соединения и раздаёт сообщения клиентам в реальном времени. Сервисы не общаются напрямую — всё через Kafka.

## Что использовалось

- **Python, FastAPI** — оба сервиса
- **PostgreSQL + SQLAlchemy + Alembic** — хранение сообщений, чатов, пользователей
- **Apache Kafka** — шина событий между сервисами, transactional outbox
- **Redis** — хранение статусов присутствия (online/offline) с TTL
- **JWT** — аутентификация, access + refresh токены
- **uv** — управление зависимостями и воркспейс
- **ruff, mypy, pytest** — линтинг, типизация, тесты

## Модули

- `libs/hexachat-shared` — общие контракты событий Kafka, утилиты JWT, логирование
- `services/chat-core` — HTTP API: регистрация, логин, чаты, сообщения, история
- `services/presence-gateway` — WebSocket хаб: доставка сообщений, статус присутствия, read receipts
- `docs/adr/` — решения по архитектуре (Kafka vs NATS, outbox, fan-out)

## Быстрый старт

Требования: Docker, Docker Compose, uv.

```bash
# 1. Установить зависимости
make install

# 2. Поднять весь стек (инфра + сервисы)
make up

# 3. Применить миграции
make migrate

# 4. Создать топики Kafka (если не созданы автоматически)
make topics
```

После запуска:
- REST API и документация: http://localhost:8000/api/docs
- WebSocket: `ws://localhost:8001/api/v1/ws?token=<JWT>`

## Полезные команды

```bash
make logs        # логи всех контейнеров
make test        # запустить тесты
make lint        # ruff + mypy
make format      # автоформатирование
make down        # остановить и удалить контейнеры
make psql        # открыть psql в контейнере
make redis-cli   # открыть redis-cli
```
