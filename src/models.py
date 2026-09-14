import scapy.all as scapy
import locale as lc
import datetime as dt

ID = 0
QUERY_ENTITY = 3
FEEDBACK_QUERY = 5
QUERY_COLS = (
    "identifier",
    "datetime",
    "parameter",
    "entity",
    "description",
    "tags",
    "status",
)

lang, _ = lc.getlocale()
if not lang:
    lang = "en-US"

entities = [
    (1, 1715145600, "127.0.0.1", "en-US", "Web"),
    (2, 1715145600, "127.0.0.1", "en-US", "Web"),
]

queries = [
    (1, 1715145600, "query1", 1, "description1", "tags1", "status1"),
    (2, 1715145600, "query2", 2, "description2", "tags2", "status2"),
]

feedbacks = [
    (1, 1715145600, "response1", "status1", "failure1", 1),
    (2, 1715145600, "response2", "status2", "failure2", 2),
]


def _local_ip() -> str:
    for iface in scapy.get_if_list():
        if iface == "lo":
            continue
        try:
            addr = scapy.get_if_addr(iface)
        except Exception:
            continue
        if addr and addr != "0.0.0.0":
            return addr
    return scapy.get_if_addr("lo")


def new_entity(*, identifier: int) -> None:
    entities.append((
        identifier,
        dt.datetime.now().timestamp(),
        _local_ip(),
        lang,
        "Web",
    ))


def new_query(
    *,
    identifier: int,
    parameter: str,
    entity: int,
    description: str,
    tags: str,
    status: str,
) -> None:
    queries.append((
        identifier,
        dt.datetime.now().timestamp(),
        parameter,
        entity,
        description,
        tags,
        status,
    ))


def new_feedback(
    *,
    identifier: int,
    response: str,
    status: str,
    failure: str,
    query: int,
) -> None:
    feedbacks.append((
        identifier,
        dt.datetime.now().timestamp(),
        response,
        status,
        failure,
        query,
    ))


def del_feedback(identifier: int) -> None:
    feedbacks[:] = [row for row in feedbacks if row[ID] != identifier]


def del_query(identifier: int) -> None:
    for row in list(feedbacks):
        if row[FEEDBACK_QUERY] == identifier:
            del_feedback(row[ID])
    queries[:] = [row for row in queries if row[ID] != identifier]


def del_entity(identifier: int) -> None:
    for row in list(queries):
        if row[QUERY_ENTITY] == identifier:
            del_query(row[ID])
    entities[:] = [row for row in entities if row[ID] != identifier]


def get_feedbacks() -> list[tuple]:
    return list(feedbacks)


def get_queries() -> list[tuple]:
    return list(queries)


def get_entities() -> list[tuple]:
    return list(entities)


def edit_entity(
    *,
    identifier: int,
    datetime: int | None = None,
    ip: str | None = None,
    locale: str | None = None,
    platform: str | None = None,
) -> None:
    for i, (eid, dt, e_ip, e_locale, e_platform) in enumerate(entities):
        if eid == identifier:
            entities[i] = (
                eid,
                dt if datetime is None else datetime,
                e_ip if ip is None else ip,
                e_locale if locale is None else locale,
                e_platform if platform is None else platform,
            )
            return
    raise ValueError(f"Entity with identifier {identifier} not found")


def _updated(row: tuple, names: tuple[str, ...], fields: dict) -> tuple:
    result = []
    for index, name in enumerate(names):
        value = fields.get(name)
        if name == "identifier" or value is None:
            result.append(row[index])
        else:
            result.append(value)
    return tuple(result)


def edit_query(identifier: int, **fields) -> None:
    for i, row in enumerate(queries):
        if row[ID] == identifier:
            queries[i] = _updated(row, QUERY_COLS, fields)
            return
    raise ValueError(f"Query with identifier {identifier} not found")


def edit_feedback(
    *,
    identifier: int,
    datetime: int | None = None,
    response: str | None = None,
    status: str | None = None,
    failure: str | None = None,
    query: int | None = None,
) -> None:
    for i, (
        fid,
        dt,
        f_response,
        f_status,
        f_failure,
        f_query,
    ) in enumerate(feedbacks):
        if fid == identifier:
            feedbacks[i] = (
                fid,
                dt if datetime is None else datetime,
                f_response if response is None else response,
                f_status if status is None else status,
                f_failure if failure is None else failure,
                f_query if query is None else query,
            )
            return
    raise ValueError(f"Feedback with identifier {identifier} not found")
