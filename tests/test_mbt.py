import sys
import threading
import time
import unittest
from pathlib import Path

from hypothesis import HealthCheck, settings, strategies as st
from hypothesis.stateful import (
    RuleBasedStateMachine,
    initialize,
    invariant,
    rule,
)

_SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(_SRC))

import models
import view
from client import RpcClient, _rows_from_xml
from server import (
    ENTITY_FIELDS,
    FEEDBACK_FIELDS,
    QUERY_FIELDS,
    VIEW_FIELDS,
    RpcHandler,
    RpcServer,
    rows_to_xml,
)

SEED_ENTITIES = [tuple(row) for row in models.entities]
SEED_QUERIES = [tuple(row) for row in models.queries]
SEED_FEEDBACKS = [tuple(row) for row in models.feedbacks]

WORDS = st.text(alphabet="abcxyz", min_size=1, max_size=5)
IDS = st.integers(min_value=3, max_value=25)


def reset_tables() -> None:
    models.entities[:] = [tuple(row) for row in SEED_ENTITIES]
    models.queries[:] = [tuple(row) for row in SEED_QUERIES]
    models.feedbacks[:] = [tuple(row) for row in SEED_FEEDBACKS]


def encoded(rows: list[tuple], names: tuple[str, ...]) -> list[tuple]:
    return _rows_from_xml(rows_to_xml(rows, names))


def start_rpc():
    server = RpcServer(("127.0.0.1", 0), RpcHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    last_error = None
    for _ in range(20):
        try:
            return server, thread, RpcClient(host, port)
        except ConnectionRefusedError as exc:
            last_error = exc
            time.sleep(0.05)
    raise last_error


def stop_rpc(server, thread, client) -> None:
    try:
        client.close()
    except OSError:
        pass
    server.shutdown()
    server.server_close()
    thread.join(timeout=2)


def pick_id(data, table: list[tuple]):
    ids = [row[0] for row in table]
    if ids:
        return data.draw(st.one_of(st.sampled_from(ids), IDS))
    return data.draw(IDS)


class RpcMachine(RuleBasedStateMachine):
    @initialize()
    def start(self) -> None:
        reset_tables()
        self.server, self.thread, self.rpc = start_rpc()

    def teardown(self) -> None:
        if getattr(self, "server", None) is not None:
            stop_rpc(self.server, self.thread, self.rpc)
        reset_tables()

    def check(self, rpc_rows, loader, names) -> None:
        assert rpc_rows == encoded(loader(), names)

    @invariant()
    def tables_match(self) -> None:
        self.check(self.rpc.get_entities(), models.get_entities, ENTITY_FIELDS)
        self.check(self.rpc.get_queries(), models.get_queries, QUERY_FIELDS)
        self.check(
            self.rpc.get_feedbacks(),
            models.get_feedbacks,
            FEEDBACK_FIELDS,
        )

    @rule()
    def get_entities(self) -> None:
        self.check(self.rpc.get_entities(), models.get_entities, ENTITY_FIELDS)

    @rule()
    def get_queries(self) -> None:
        self.check(self.rpc.get_queries(), models.get_queries, QUERY_FIELDS)

    @rule()
    def get_feedbacks(self) -> None:
        self.check(
            self.rpc.get_feedbacks(),
            models.get_feedbacks,
            FEEDBACK_FIELDS,
        )

    @rule()
    def recent_query_feedbacks(self) -> None:
        self.check(
            self.rpc.recent_query_feedbacks(),
            view.recent_query_feedbacks,
            VIEW_FIELDS,
        )

    @rule(identifier=IDS)
    def new_entity(self, identifier: int) -> None:
        self.rpc.new_entity(identifier=identifier)

    @rule(data=st.data())
    def new_query(self, data) -> None:
        self.rpc.new_query(
            identifier=data.draw(IDS),
            parameter=data.draw(WORDS),
            entity=pick_id(data, models.entities),
            description=data.draw(WORDS),
            tags=data.draw(WORDS),
            status=data.draw(WORDS),
        )

    @rule(data=st.data())
    def new_feedback(self, data) -> None:
        self.rpc.new_feedback(
            identifier=data.draw(IDS),
            response=data.draw(WORDS),
            status=data.draw(WORDS),
            failure=data.draw(WORDS),
            query=pick_id(data, models.queries),
        )

    @rule(data=st.data())
    def edit_entity(self, data) -> None:
        self.rpc.edit_entity(
            identifier=pick_id(data, models.entities),
            ip=data.draw(WORDS),
            locale=data.draw(WORDS),
            platform=data.draw(WORDS),
        )

    @rule(data=st.data())
    def edit_query(self, data) -> None:
        self.rpc.edit_query(
            identifier=pick_id(data, models.queries),
            status=data.draw(WORDS),
            parameter=data.draw(WORDS),
        )

    @rule(data=st.data())
    def edit_feedback(self, data) -> None:
        self.rpc.edit_feedback(
            identifier=pick_id(data, models.feedbacks),
            response=data.draw(WORDS),
            status=data.draw(WORDS),
        )

    @rule(data=st.data())
    def del_entity(self, data) -> None:
        self.rpc.del_entity(pick_id(data, models.entities))

    @rule(data=st.data())
    def del_query(self, data) -> None:
        self.rpc.del_query(pick_id(data, models.queries))

    @rule(data=st.data())
    def del_feedback(self, data) -> None:
        self.rpc.del_feedback(pick_id(data, models.feedbacks))


RpcMachine.TestCase.settings = settings(
    max_examples=40,
    stateful_step_count=25,
    deadline=None,
    suppress_health_check=(HealthCheck.too_slow,),
)

TestRpcMBT = RpcMachine.TestCase


if __name__ == "__main__":
    unittest.main()
