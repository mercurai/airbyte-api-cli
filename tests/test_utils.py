"""Tests for shared utilities."""

import json
import tempfile
import unittest
from pathlib import Path

from airbyte_cli.core.utils import resolve_json_arg, strip_none


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


if __name__ == "__main__":
    unittest.main()
