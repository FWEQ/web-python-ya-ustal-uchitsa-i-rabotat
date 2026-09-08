import time

from models import get_feedbacks, get_queries


Q_IDENTIFIER = 0
Q_DATETIME = 1
Q_DESCRIPTION = 4
Q_TAGS = 5

F_RESPONSE = 2
F_QUERY = 5

NINE_MINUTES = 9 * 60


def recent_query_feedbacks() -> list[tuple[str, str, str]]:
    now = time.time()
    recent_queries = [
        q
        for q in get_queries()
        if q[Q_DATETIME] > now - NINE_MINUTES
    ]
    return [
        (f[F_RESPONSE], q[Q_DESCRIPTION], q[Q_TAGS])
        for q in recent_queries
        for f in get_feedbacks()
        if q[Q_IDENTIFIER] == f[F_QUERY]
    ]
