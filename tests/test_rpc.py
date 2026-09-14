"""Tests for XML helpers and RPC dispatch."""

import unittest

import models
import server
from client import _rows_from_xml, _xml_from_fields


class TestXml(unittest.TestCase):
    """XML encode and decode for RPC payloads."""

    def test_xml_roundtrip_rows(self) -> None:
        """rows_to_xml then _rows_from_xml restores tuples."""
        rows = [(1, "ok")]
        xml = server.rows_to_xml(rows, ("identifier", "status"))
        self.assertEqual(_rows_from_xml(xml), rows)

    def test_fields_from_xml(self) -> None:
        """Integer tags are coerced, others stay strings."""
        xml = _xml_from_fields(identifier=3, status="done")
        fields = server.fields_from_xml(xml)
        self.assertEqual(fields["identifier"], 3)
        self.assertEqual(fields["status"], "done")

    def test_empty_xml(self) -> None:
        """Empty payloads decode to empty values."""
        self.assertEqual(server.fields_from_xml(""), {})
        self.assertEqual(_rows_from_xml(""), [])


class TestDispatch(unittest.TestCase):
    """Opcode routing without a live TCP socket."""

    def setUp(self) -> None:
        """Snapshot tables before each test."""
        self._entities = list(models.entities)
        self._queries = list(models.queries)
        self._feedbacks = list(models.feedbacks)

    def tearDown(self) -> None:
        """Restore tables after each test."""
        models.entities[:] = self._entities
        models.queries[:] = self._queries
        models.feedbacks[:] = self._feedbacks

    def test_get_entities(self) -> None:
        """GET_ENTITIES returns XML with the seed identifier."""
        xml = server.dispatch(server.OP_GET_ENTITIES, "")
        self.assertIn("<identifier>1</identifier>", xml)

    def test_edit_query(self) -> None:
        """EDIT_QUERY updates the in-memory row."""
        body = _xml_from_fields(identifier=1, status="done")
        server.dispatch(server.OP_EDIT_QUERY, body)
        self.assertEqual(models.get_queries()[0][6], "done")

    def test_unknown_opcode(self) -> None:
        """Unknown opcodes raise ValueError."""
        with self.assertRaises(ValueError):
            server.dispatch(99, "")
