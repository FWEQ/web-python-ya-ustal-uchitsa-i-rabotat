from __future__ import annotations

from models import (
    del_entity,
    del_feedback,
    del_query,
    edit_entity,
    edit_feedback,
    edit_query,
    get_entities,
    get_feedbacks,
    get_queries,
    new_entity,
    new_feedback,
    new_query,
)
from view import recent_query_feedbacks


ENTITY_HEADER = (
    "identifier",
    "datetime",
    "ip",
    "locale",
    "platform",
)
QUERY_HEADER = (
    "identifier",
    "datetime",
    "parameter",
    "entity",
    "description",
    "tags",
    "status",
)
FEEDBACK_HEADER = (
    "identifier",
    "datetime",
    "response",
    "status",
    "failure",
    "query",
)
VIEW_HEADER = ("response", "description", "tags")

MENU = """
=== REPL: слой доступа к данным ===
 1) get_entities
 2) get_queries
 3) get_feedbacks
 4) new_entity
 5) new_query
 6) new_feedback
 7) edit_entity
 8) edit_query
 9) edit_feedback
10) del_entity
11) del_query
12) del_feedback
13) recent_query_feedbacks  (view, запросы за 9 мин)
14) demo                    (прогон всех функций)
 0) выход
"""


def _print_table(
    title: str,
    header: tuple[str, ...],
    rows: list[tuple],
) -> None:
    print(f"\n{title} ({len(rows)})")
    print(" | ".join(header))
    print("-" * 80)
    if not rows:
        print("(пусто)")
        return
    for row in rows:
        print(" | ".join(str(cell) for cell in row))


def _ask(prompt: str) -> str:
    return input(prompt).strip()


def _ask_int(prompt: str) -> int:
    return int(_ask(prompt))


def _ask_optional(prompt: str) -> str | None:
    value = _ask(prompt)
    return value if value else None


def _ask_optional_int(prompt: str) -> int | None:
    value = _ask(prompt)
    return int(value) if value else None


def show_entities() -> None:
    _print_table("entities", ENTITY_HEADER, get_entities())


def show_queries() -> None:
    _print_table("queries", QUERY_HEADER, get_queries())


def show_feedbacks() -> None:
    _print_table("feedbacks", FEEDBACK_HEADER, get_feedbacks())


def show_view() -> None:
    _print_table(
        "recent_query_feedbacks",
        VIEW_HEADER,
        recent_query_feedbacks(),
    )


def create_entity() -> None:
    new_entity(identifier=_ask_int("identifier: "))
    print("entity создана")
    show_entities()


def create_query() -> None:
    new_query(
        identifier=_ask_int("identifier: "),
        parameter=_ask("parameter: "),
        entity=_ask_int("entity (id): "),
        description=_ask("description: "),
        tags=_ask("tags: "),
        status=_ask("status: "),
    )
    print("query создан")
    show_queries()


def create_feedback() -> None:
    new_feedback(
        identifier=_ask_int("identifier: "),
        response=_ask("response: "),
        status=_ask("status: "),
        failure=_ask("failure: "),
        query=_ask_int("query (id): "),
    )
    print("feedback создан")
    show_feedbacks()


def update_entity() -> None:
    edit_entity(
        identifier=_ask_int("identifier: "),
        ip=_ask_optional("ip (пусто = не менять): "),
        locale=_ask_optional("locale (пусто = не менять): "),
        platform=_ask_optional("platform (пусто = не менять): "),
    )
    print("entity обновлена")
    show_entities()


def update_query() -> None:
    edit_query(
        identifier=_ask_int("identifier: "),
        parameter=_ask_optional("parameter (пусто = не менять): "),
        entity=_ask_optional_int("entity (пусто = не менять): "),
        description=_ask_optional("description (пусто = не менять): "),
        tags=_ask_optional("tags (пусто = не менять): "),
        status=_ask_optional("status (пусто = не менять): "),
    )
    print("query обновлён")
    show_queries()


def update_feedback() -> None:
    edit_feedback(
        identifier=_ask_int("identifier: "),
        response=_ask_optional("response (пусто = не менять): "),
        status=_ask_optional("status (пусто = не менять): "),
        failure=_ask_optional("failure (пусто = не менять): "),
        query=_ask_optional_int("query (пусто = не менять): "),
    )
    print("feedback обновлён")
    show_feedbacks()


def remove_entity() -> None:
    del_entity(_ask_int("identifier: "))
    print("entity удалена (каскад: связанные query и feedback)")
    show_entities()
    show_queries()
    show_feedbacks()


def remove_query() -> None:
    del_query(_ask_int("identifier: "))
    print("query удалён (каскад: связанные feedback)")
    show_queries()
    show_feedbacks()


def remove_feedback() -> None:
    del_feedback(_ask_int("identifier: "))
    print("feedback удалён")
    show_feedbacks()


def _demo_read() -> None:
    print("\n--- 1. чтение таблиц ---")
    show_entities()
    show_queries()
    show_feedbacks()


def _demo_create() -> None:
    print("\n--- 2. создание ---")
    new_entity(identifier=3)
    new_query(
        identifier=3,
        parameter="search",
        entity=3,
        description="свежий запрос",
        tags="demo,repl",
        status="ok",
    )
    new_feedback(
        identifier=3,
        response="ответ на свежий запрос",
        status="success",
        failure="",
        query=3,
    )
    show_entities()
    show_queries()
    show_feedbacks()


def _demo_edit() -> None:
    print("\n--- 3. редактирование ---")
    edit_entity(identifier=3, platform="Linux")
    edit_query(identifier=3, status="done")
    edit_feedback(identifier=3, response="обновлённый ответ")
    show_entities()
    show_queries()
    show_feedbacks()


def _demo_view() -> None:
    print("\n--- 4. view: join запросов за 9 минут с feedback ---")
    show_view()


def _demo_delete_feedback() -> None:
    print("\n--- 5. удаление feedback ---")
    del_feedback(3)
    show_feedbacks()


def _demo_cascade_query() -> None:
    print("\n--- 6. снова feedback, затем каскад del_query ---")
    new_feedback(
        identifier=3,
        response="временный",
        status="ok",
        failure="",
        query=3,
    )
    del_query(3)
    show_queries()
    show_feedbacks()


def _demo_cascade_entity() -> None:
    print("\n--- 7. снова query+feedback, затем каскад del_entity ---")
    new_query(
        identifier=3,
        parameter="search",
        entity=3,
        description="ещё раз",
        tags="demo",
        status="ok",
    )
    new_feedback(
        identifier=3,
        response="ещё ответ",
        status="ok",
        failure="",
        query=3,
    )
    del_entity(3)
    show_entities()
    show_queries()
    show_feedbacks()


def demo() -> None:
    _demo_read()
    _demo_create()
    _demo_edit()
    _demo_view()
    _demo_delete_feedback()
    _demo_cascade_query()
    _demo_cascade_entity()
    print("\nдемо завершено")


ACTIONS = {
    "1": show_entities,
    "2": show_queries,
    "3": show_feedbacks,
    "4": create_entity,
    "5": create_query,
    "6": create_feedback,
    "7": update_entity,
    "8": update_query,
    "9": update_feedback,
    "10": remove_entity,
    "11": remove_query,
    "12": remove_feedback,
    "13": show_view,
    "14": demo,
    "demo": demo,
}


def repl() -> None:
    print("Введите номер команды. demo — автоматический прогон всех функций.")
    while True:
        print(MENU)
        choice = _ask("> ").lower()
        if choice in {"0", "exit", "quit", "q"}:
            print("выход")
            return
        action = ACTIONS.get(choice)
        if action is None:
            print("нет такой команды")
            continue
        try:
            action()
        except ValueError as exc:
            print(f"ошибка: {exc}")
        except KeyboardInterrupt:
            print("\nвыход")
            return


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "rpc":
        from client import RpcClient
        rpc = RpcClient()
        print("connected to {}:{}".format(rpc.host, rpc.port))
        get_entities = rpc.get_entities
        get_queries = rpc.get_queries
        get_feedbacks = rpc.get_feedbacks
        new_entity = rpc.new_entity
        new_query = rpc.new_query
        new_feedback = rpc.new_feedback
        edit_entity = rpc.edit_entity
        edit_query = rpc.edit_query
        edit_feedback = rpc.edit_feedback
        del_entity = rpc.del_entity
        del_query = rpc.del_query
        del_feedback = rpc.del_feedback
        recent_query_feedbacks = rpc.recent_query_feedbacks
    repl()
