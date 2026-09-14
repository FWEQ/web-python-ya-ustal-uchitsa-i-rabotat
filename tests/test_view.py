"""Tests for the recent query-feedback view."""

import time
import unittest

import models
from view import recent_query_feedbacks


class TestView(unittest.TestCase):
    """Join of recent queries with feedbacks."""

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

    def test_recent_join(self) -> None:
        """Rows from the last 9 minutes are joined with feedback."""
        now = time.time()
        models.queries[:] = [
            (9, now, "search", 1, "desc", "tag", "ok"),
        ]
        models.feedbacks[:] = [
            (9, now, "resp", "ok", "", 9),
        ]
        self.assertEqual(
            recent_query_feedbacks(),
            [("resp", "desc", "tag")],
        )

    def test_old_queries_are_skipped(self) -> None:
        """Queries older than 9 minutes are not returned."""
        models.queries[:] = [
            (9, 1, "search", 1, "desc", "tag", "ok"),
        ]
        models.feedbacks[:] = [
            (9, 1, "resp", "ok", "", 9),
        ]
        self.assertEqual(recent_query_feedbacks(), [])
