# web-python

Практика: слой доступа к данным (кортежи) и RPC по TCP.

Таблицы: Entity, Query, Feedback. Запись в памяти — кортеж.
RPC: little-endian шапка + тело XML, порт `localhost:8001`.

## Структура

- `src/models.py` — CRUD таблиц
- `src/view.py` — выборка запросов за 9 минут
- `src/REPL.py` — меню и demo всех функций
- `src/client.py` — RPC-клиент (`RpcClient`)
- `src/server.py` — RPC-сервер (`socketserver`)
- `run.sh` — repl, server или rpc
- `Makefile` — те же цели

## Зависимости

- Python 3.10+
- Scapy: `pip install scapy`
- Hypothesis и coverage: `pip install hypothesis coverage`

## Тесты

MBT через `RuleBasedStateMachine`: 13 RPC-методов сверяются
с `models` / `view` после каждого шага.

```bash
make test
```

Отчёт о покрытии ветвей пишется в `coverage.txt`.

## Запуск

Сервер (терминал 1):

```bash
./run.sh server
```

или `make server`.

RPC-клиент + то же меню (терминал 2):

```bash
./run.sh rpc
```

или `make rpc`.

Локальный REPL без сокета: `./run.sh` или `make run`.

В меню: `14` или `demo` — прогон всех функций модели.

Сервер слушает `localhost:8001`. Запросы клиента пишутся
в `journal.log`.
