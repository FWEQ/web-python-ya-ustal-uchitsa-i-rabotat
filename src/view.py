import time

from models import get_feedbacks, get_queries


Q_IDENTIFIER = 0
Q_DATETIME = 1
Q_DESCRIPTION = 4
Q_TAGS = 5

F_RESPONSE = 2
F_QUERY = 5

NINE_MINUTES = 9 * 60

def _full_join(queries: list[tuple], feedbacks: list[tuple]) -> list[tuple]:
    result = []
    for q in queries:
        if [(f[F_RESPONSE], q[Q_DESCRIPTION], q[Q_TAGS]) for f in feedbacks if f[F_QUERY] == q[Q_IDENTIFIER]] != None:
            result.append(([(f[F_RESPONSE], q[Q_DESCRIPTION], q[Q_TAGS]) for f in feedbacks if f[F_QUERY] == q[Q_IDENTIFIER]]))
        else:
            result.append((None, q[Q_DESCRIPTION], q[Q_TAGS]))
    return result

def recent_query_feedbacks() -> list[tuple[str, str, str]]:
    now = time.time()
    recent_queries = [
        q
        for q in get_queries()
        if q[Q_DATETIME] > now - NINE_MINUTES
    ]
    return _full_join(recent_queries, get_feedbacks())
