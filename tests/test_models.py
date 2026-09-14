"""Tests for the in-memory data access layer."""

import unittest

import models


class TestModels(unittest.TestCase):
    """CRUD and cascade checks for Entity, Query, Feedback."""

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

    def test_get_entities_returns_copy(self) -> None:
        """get_entities returns a copy, not the live list."""
        rows = models.get_entities()
        self.assertEqual(rows, models.entities)
        rows.clear()
        self.assertEqual(len(models.entities), 2)

    def test_edit_query_updates_status(self) -> None:
        """edit_query writes only the provided fields."""
        models.edit_query(identifier=1, status="done")
        row = models.get_queries()[0]
        self.assertEqual(row[6], "done")
        self.assertEqual(row[2], "query1")

    def test_edit_query_missing(self) -> None:
        """edit_query raises when the identifier is unknown."""
        with self.assertRaises(ValueError):
            models.edit_query(identifier=999, status="x")

    def test_del_query_cascades_feedback(self) -> None:
        """Deleting a query also deletes linked feedback."""
        models.del_query(1)
        qids = [row[0] for row in models.get_queries()]
        f_queries = [row[5] for row in models.get_feedbacks()]
        self.assertNotIn(1, qids)
        self.assertNotIn(1, f_queries)

    def test_del_entity_cascades(self) -> None:
        """Deleting an entity also deletes linked queries."""
        models.del_entity(1)
        eids = [row[0] for row in models.get_entities()]
        q_entities = [row[3] for row in models.get_queries()]
        self.assertNotIn(1, eids)
        self.assertNotIn(1, q_entities)
