"""Model-based tests of the 13 RPC methods via Hypothesis."""

import threading
import time
import unittest

from hypothesis import HealthCheck, settings, strategies as st
from hypothesis.stateful import (
    RuleBasedStateMachine,
    initialize,
    invariant,
    rule,
)

import models
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
from view import NINE_MINUTES


SEED_ENTITIES = [tuple(row) for row in models.entities]
SEED_QUERIES = [tuple(row) for row in models.queries]
SEED_FEEDBACKS = [tuple(row) for row in models.feedbacks]

WORDS = st.text(alphabet="abcxyz", min_size=1, max_size=5)
IDS = st.integers(min_value=3, max_value=25)


def reset_tables() -> None:
    """Restore DAL tables to the seed snapshot."""
    models.entities[:] = [tuple(row) for row in SEED_ENTITIES]
    models.queries[:] = [tuple(row) for row in SEED_QUERIES]
    models.feedbacks[:] = [tuple(row) for row in SEED_FEEDBACKS]


def encoded(rows: list[tuple], names: tuple[str, ...]) -> list[tuple]:
    """Apply the same XML round-trip the RPC client uses."""
    return _rows_from_xml(rows_to_xml(rows, names))


def start_rpc():
    """Listen on an ephemeral port and return server, thread, client."""
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
    """Close the RPC client and stop the TCP server."""
    try:
        client.close()
    except OSError:
        pass
    server.shutdown()
    server.server_close()
    thread.join(timeout=2)


def pick_id(data, table: list[tuple]):
    """Existing identifier or a freshly drawn one."""
    ids = [row[0] for row in table]
    if ids:
        return data.draw(st.one_of(st.sampled_from(ids), IDS))
    return data.draw(IDS)


def last_row(table: list[tuple], identifier: int) -> tuple:
    """Newest row with the given identifier."""
    return [row for row in table if row[0] == identifier][-1]


def patch_row(row: tuple, names: tuple[str, ...], fields: dict) -> tuple:
    """Copy a row, replacing named fields when a value is present."""
    values = list(row)
    for index, name in enumerate(names):
        if name == "identifier":
            continue
        if name in fields and fields[name] is not None:
            values[index] = fields[name]
    return tuple(values)


def replace_row(
    table: list[tuple],
    identifier: int,
    names: tuple[str, ...],
    fields: dict,
) -> list[tuple]:
    """Patch the first matching row; leave the table as-is if missing."""
    result = []
    patched = False
    for row in table:
        if row[0] == identifier and not patched:
            result.append(patch_row(row, names, fields))
            patched = True
        else:
            result.append(row)
    return result


class Mirror:
    """Simplified independent copy of the three DAL tables."""

    def __init__(self) -> None:
        self.entities = [tuple(row) for row in SEED_ENTITIES]
        self.queries = [tuple(row) for row in SEED_QUERIES]
        self.feedbacks = [tuple(row) for row in SEED_FEEDBACKS]

    def capture_entity(self, identifier: int) -> None:
        """Observe a newly created entity from the live DAL."""
        self.entities.append(last_row(models.get_entities(), identifier))

    def capture_query(self, identifier: int) -> None:
        """Observe a newly created query from the live DAL."""
        self.queries.append(last_row(models.get_queries(), identifier))

    def capture_feedback(self, identifier: int) -> None:
        """Observe a newly created feedback from the live DAL."""
        self.feedbacks.append(last_row(models.get_feedbacks(), identifier))

    def edit_entity(self, identifier: int, **fields) -> None:
        """Update the first matching entity."""
        self.entities = replace_row(
            self.entities, identifier, ENTITY_FIELDS, fields
        )

    def edit_query(self, identifier: int, **fields) -> None:
        """Update the first matching query."""
        self.queries = replace_row(
            self.queries, identifier, QUERY_FIELDS, fields
        )

    def edit_feedback(self, identifier: int, **fields) -> None:
        """Update the first matching feedback."""
        self.feedbacks = replace_row(
            self.feedbacks, identifier, FEEDBACK_FIELDS, fields
        )

    def del_feedback(self, identifier: int) -> None:
        """Drop feedback rows with this identifier."""
        self.feedbacks = [
            row for row in self.feedbacks if row[0] != identifier
        ]

    def del_query(self, identifier: int) -> None:
        """Drop a query and cascade to linked feedback."""
        for row in list(self.feedbacks):
            if row[5] == identifier:
                self.del_feedback(row[0])
        self.queries = [
            row for row in self.queries if row[0] != identifier
        ]

    def del_entity(self, identifier: int) -> None:
        """Drop an entity and cascade to linked queries."""
        for row in list(self.queries):
            if row[3] == identifier:
                self.del_query(row[0])
        self.entities = [
            row for row in self.entities if row[0] != identifier
        ]

    def recent_query_feedbacks(self) -> list[tuple]:
        """Join feedbacks with queries from the last 9 minutes."""
        now = time.time()
        recent = [q for q in self.queries if q[1] > now - NINE_MINUTES]
        rows = []
        for query in recent:
            for feedback in self.feedbacks:
                if query[0] == feedback[5]:
                    rows.append((feedback[2], query[4], query[5]))
        return rows


class RpcMachine(RuleBasedStateMachine):
    """Drive every RPC method against both the client and the mirror."""

    @initialize()
    def start(self) -> None:
        """Reset tables, start a server, and connect a client."""
        reset_tables()
        self.model = Mirror()
        self.server, self.thread, self.rpc = start_rpc()

    def teardown(self) -> None:
        """Stop the RPC pair and restore seed tables."""
        if getattr(self, "server", None) is not None:
            stop_rpc(self.server, self.thread, self.rpc)
        reset_tables()

    def check(self, rpc_rows, model_rows, names) -> None:
        """RPC result must match the XML encoding of the model."""
        assert rpc_rows == encoded(model_rows, names)

    @invariant()
    def tables_match(self) -> None:
        """After every step the three tables stay aligned."""
        self.check(self.rpc.get_entities(), self.model.entities, ENTITY_FIELDS)
        self.check(self.rpc.get_queries(), self.model.queries, QUERY_FIELDS)
        self.check(
            self.rpc.get_feedbacks(),
            self.model.feedbacks,
            FEEDBACK_FIELDS,
        )

    @rule()
    def get_entities(self) -> None:
        """RPC get_entities matches the model."""
        self.check(self.rpc.get_entities(), self.model.entities, ENTITY_FIELDS)

    @rule()
    def get_queries(self) -> None:
        """RPC get_queries matches the model."""
        self.check(self.rpc.get_queries(), self.model.queries, QUERY_FIELDS)

    @rule()
    def get_feedbacks(self) -> None:
        """RPC get_feedbacks matches the model."""
        self.check(
            self.rpc.get_feedbacks(),
            self.model.feedbacks,
            FEEDBACK_FIELDS,
        )

    @rule()
    def recent_query_feedbacks(self) -> None:
        """RPC view matches the model join."""
        self.check(
            self.rpc.recent_query_feedbacks(),
            self.model.recent_query_feedbacks(),
            VIEW_FIELDS,
        )

    @rule(identifier=IDS)
    def new_entity(self, identifier: int) -> None:
        """Create an entity on both sides."""
        self.rpc.new_entity(identifier=identifier)
        self.model.capture_entity(identifier)

    @rule(data=st.data())
    def new_query(self, data) -> None:
        """Create a query linked to some entity identifier."""
        identifier = data.draw(IDS)
        entity = pick_id(data, self.model.entities)
        parameter = data.draw(WORDS)
        description = data.draw(WORDS)
        tags = data.draw(WORDS)
        status = data.draw(WORDS)
        self.rpc.new_query(
            identifier=identifier,
            parameter=parameter,
            entity=entity,
            description=description,
            tags=tags,
            status=status,
        )
        self.model.capture_query(identifier)

    @rule(data=st.data())
    def new_feedback(self, data) -> None:
        """Create a feedback linked to some query identifier."""
        identifier = data.draw(IDS)
        query = pick_id(data, self.model.queries)
        response = data.draw(WORDS)
        status = data.draw(WORDS)
        failure = data.draw(WORDS)
        self.rpc.new_feedback(
            identifier=identifier,
            response=response,
            status=status,
            failure=failure,
            query=query,
        )
        self.model.capture_feedback(identifier)

    @rule(data=st.data())
    def edit_entity(self, data) -> None:
        """Edit an entity; missing identifiers leave both sides unchanged."""
        identifier = pick_id(data, self.model.entities)
        platform = data.draw(WORDS)
        locale = data.draw(WORDS)
        ip = data.draw(WORDS)
        self.rpc.edit_entity(
            identifier=identifier,
            ip=ip,
            locale=locale,
            platform=platform,
        )
        self.model.edit_entity(
            identifier,
            ip=ip,
            locale=locale,
            platform=platform,
        )

    @rule(data=st.data())
    def edit_query(self, data) -> None:
        """Edit a query status and parameter."""
        identifier = pick_id(data, self.model.queries)
        status = data.draw(WORDS)
        parameter = data.draw(WORDS)
        self.rpc.edit_query(
            identifier=identifier,
            status=status,
            parameter=parameter,
        )
        self.model.edit_query(
            identifier,
            status=status,
            parameter=parameter,
        )

    @rule(data=st.data())
    def edit_feedback(self, data) -> None:
        """Edit a feedback response and status."""
        identifier = pick_id(data, self.model.feedbacks)
        response = data.draw(WORDS)
        status = data.draw(WORDS)
        self.rpc.edit_feedback(
            identifier=identifier,
            response=response,
            status=status,
        )
        self.model.edit_feedback(
            identifier,
            response=response,
            status=status,
        )

    @rule(data=st.data())
    def del_entity(self, data) -> None:
        """Delete an entity and apply the same cascade on the model."""
        identifier = pick_id(data, self.model.entities)
        self.rpc.del_entity(identifier)
        self.model.del_entity(identifier)

    @rule(data=st.data())
    def del_query(self, data) -> None:
        """Delete a query and apply the same cascade on the model."""
        identifier = pick_id(data, self.model.queries)
        self.rpc.del_query(identifier)
        self.model.del_query(identifier)

    @rule(data=st.data())
    def del_feedback(self, data) -> None:
        """Delete a feedback on both sides."""
        identifier = pick_id(data, self.model.feedbacks)
        self.rpc.del_feedback(identifier)
        self.model.del_feedback(identifier)


RpcMachine.TestCase.settings = settings(
    max_examples=40,
    stateful_step_count=25,
    deadline=None,
    suppress_health_check=(HealthCheck.too_slow,),
)

TestRpcMBT = RpcMachine.TestCase


if __name__ == "__main__":
    unittest.main()
