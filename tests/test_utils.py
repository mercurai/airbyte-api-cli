"""Tests for shared utilities."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from airbyte_cli.models.common import ApiResponse

from airbyte_cli.core.utils import resolve_json_arg, strip_none, paginate_all


class TestResolveJsonArg(unittest.TestCase):
    def test_inline_json_string(self):
        result = resolve_json_arg('{"name": "test", "value": 42}')
        self.assertEqual(result["name"], "test")
        self.assertEqual(result["value"], 42)

    def test_at_file_path(self):
        data = {"key": "from_file", "nested": {"a": 1}}
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(data, f)
            path = f.name

        result = resolve_json_arg(f"@{path}")
        self.assertEqual(result["key"], "from_file")
        self.assertEqual(result["nested"]["a"], 1)

    def test_invalid_json_raises_value_error(self):
        with self.assertRaises(ValueError):
            resolve_json_arg("{not valid json}")

    def test_missing_file_raises_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            resolve_json_arg("@/nonexistent/path/config.json")

    def test_invalid_json_in_file_raises_value_error(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            f.write("{broken json{{")
            path = f.name

        with self.assertRaises(ValueError):
            resolve_json_arg(f"@{path}")

    def test_empty_object(self):
        result = resolve_json_arg("{}")
        self.assertEqual(result, {})

    def test_complex_nested_json(self):
        data = {"streams": [{"name": "users", "syncMode": "full_refresh"}]}
        result = resolve_json_arg(json.dumps(data))
        self.assertEqual(result["streams"][0]["name"], "users")


class TestStripNone(unittest.TestCase):
    def test_removes_none_values(self):
        result = strip_none({"a": 1, "b": None, "c": "keep"})
        self.assertNotIn("b", result)
        self.assertEqual(result["a"], 1)
        self.assertEqual(result["c"], "keep")

    def test_empty_dict(self):
        result = strip_none({})
        self.assertEqual(result, {})

    def test_no_nones_unchanged(self):
        d = {"a": 1, "b": "two", "c": []}
        result = strip_none(d)
        self.assertEqual(result, d)

    def test_returns_copy_not_original(self):
        d = {"a": 1, "b": None}
        result = strip_none(d)
        self.assertIn("b", d)  # original unchanged


class TestPaginateAll(unittest.TestCase):
    def _make_list_fn(self, pages):
        """Build a mock list_fn that returns pages of ApiResponse objects.

        Args:
            pages: list of lists, each inner list is one page of records.
        """
        call_count = {"n": 0}

        def list_fn(limit=100, offset=0, **kwargs):
            idx = call_count["n"]
            call_count["n"] += 1
            data = pages[idx] if idx < len(pages) else []
            resp = MagicMock(spec=ApiResponse)
            resp.data = data
            return resp

        return list_fn

    def test_single_page(self):
        items = [{"id": "a"}, {"id": "b"}]
        list_fn = self._make_list_fn([items])
        result = paginate_all(list_fn, limit=100)
        self.assertEqual(result, items)

    def test_multiple_pages(self):
        page1 = [{"id": i} for i in range(3)]
        page2 = [{"id": i} for i in range(3, 6)]
        page3 = [{"id": 6}]  # partial page signals end
        list_fn = self._make_list_fn([page1, page2, page3])
        result = paginate_all(list_fn, limit=3)
        self.assertEqual(len(result), 7)
        self.assertEqual(result[0], {"id": 0})
        self.assertEqual(result[6], {"id": 6})

    def test_empty_first_page(self):
        list_fn = self._make_list_fn([[]])
        result = paginate_all(list_fn, limit=100)
        self.assertEqual(result, [])

    def test_kwargs_forwarded(self):
        """Ensure extra kwargs are passed through to list_fn."""
        received = {}

        def list_fn(limit=100, offset=0, **kwargs):
            received.update(kwargs)
            resp = MagicMock(spec=ApiResponse)
            resp.data = []
            return resp

        paginate_all(list_fn, limit=10, workspace_ids=["ws-1"])
        self.assertEqual(received["workspace_ids"], ["ws-1"])

    def test_limit_offset_progression(self):
        """Verify offset increases by limit on each call."""
        calls = []

        def list_fn(limit=100, offset=0, **kwargs):
            calls.append({"limit": limit, "offset": offset})
            resp = MagicMock(spec=ApiResponse)
            # Return full page for first two calls, partial for third
            resp.data = [{"id": i} for i in range(limit)] if len(calls) < 3 else [{"id": "last"}]
            return resp

        paginate_all(list_fn, limit=5)
        self.assertEqual(calls[0]["offset"], 0)
        self.assertEqual(calls[1]["offset"], 5)
        self.assertEqual(calls[2]["offset"], 10)


if __name__ == "__main__":
    unittest.main()
