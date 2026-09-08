# web-python

Практика: слой доступа к данным (кортежи) и RPC по TCP.

Таблицы: Entity, Query, Feedback. Запись в памяти — кортеж.
RPC: little-endian шапка + тело XML, порт `localhost:8000`.

## Структура

- `src/models.py` — CRUD таблиц
- `src/view.py` — выборка запросов за 9 минут
- `src/REPL.py` — меню и demo всех функций
- `src/client.py` — RPC-клиент (`RpcClient`)
- `src/server.py` — RPC-сервер (`socketserver`)
- `run.sh` — запуск REPL или сервера
- `Makefile` — те же цели

## Зависимости

- Python 3.10+
- Scapy: `pip install scapy`

## Запуск

Сервер (терминал 1):

```bash
./run.sh server
```

или `make server`.

REPL (терминал 2):

```bash
./run.sh
```

или `make run`.

В меню: `14` или `demo` — прогон всех функций модели.

Сервер слушает `localhost:8000`. Запросы клиента пишутся
в `journal.log`.
