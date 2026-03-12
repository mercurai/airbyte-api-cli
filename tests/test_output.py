"""Tests for output formatters."""

import io
import json
import sys
import unittest
from unittest.mock import patch

from airbyte_cli.core.output import (
    error,
    format_compact,
    format_json,
    format_table,
    output,
)


class TestFormatJson(unittest.TestCase):
    def test_dict_serialised(self):
        result = format_json({"key": "value", "num": 42})
        parsed = json.loads(result)
        self.assertEqual(parsed["key"], "value")
        self.assertEqual(parsed["num"], 42)

    def test_list_serialised(self):
        result = format_json([{"id": "1"}, {"id": "2"}])
        parsed = json.loads(result)
        self.assertEqual(len(parsed), 2)

    def test_indented_output(self):
        result = format_json({"a": 1})
        self.assertIn("\n", result)


class TestFormatTable(unittest.TestCase):
    def test_empty_data_returns_no_results(self):
        result = format_table([])
        self.assertIn("no results", result)

    def test_table_has_header(self):
        data = [{"id": "s1", "name": "my-source"}]
        result = format_table(data)
        self.assertIn("ID", result)
        self.assertIn("NAME", result)

    def test_table_has_separator(self):
        data = [{"id": "s1", "name": "my-source"}]
        result = format_table(data)
        self.assertIn("--", result)

    def test_table_contains_values(self):
        data = [{"id": "s1", "name": "my-source"}]
        result = format_table(data)
        self.assertIn("s1", result)
        self.assertIn("my-source", result)

    def test_custom_columns(self):
        data = [{"id": "s1", "name": "my-source", "type": "postgres"}]
        result = format_table(data, columns=["id", "name"])
        self.assertIn("ID", result)
        self.assertNotIn("TYPE", result)

    def test_multiple_rows(self):
        data = [
            {"id": "s1", "name": "source-a"},
            {"id": "s2", "name": "source-b"},
        ]
        result = format_table(data)
        self.assertIn("source-a", result)
        self.assertIn("source-b", result)


class TestFormatCompact(unittest.TestCase):
    def test_empty_returns_empty_string(self):
        result = format_compact([])
        self.assertEqual(result, "")

    def test_one_row_pipe_separated(self):
        data = [{"id": "s1", "name": "my-source"}]
        result = format_compact(data)
        self.assertIn("|", result)
        self.assertIn("s1", result)
        self.assertIn("my-source", result)

    def test_multiple_rows_one_per_line(self):
        data = [
            {"id": "s1", "name": "a"},
            {"id": "s2", "name": "b"},
        ]
        result = format_compact(data)
        lines = result.strip().split("\n")
        self.assertEqual(len(lines), 2)

    def test_custom_columns(self):
        data = [{"id": "s1", "name": "a", "type": "postgres"}]
        result = format_compact(data, columns=["id"])
        self.assertNotIn("postgres", result)


class TestOutput(unittest.TestCase):
    @patch("sys.stdout", new_callable=io.StringIO)
    def test_output_json_format(self, mock_stdout):
        output({"id": "s1"}, fmt="json")
        printed = mock_stdout.getvalue()
        parsed = json.loads(printed)
        self.assertEqual(parsed["id"], "s1")

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_output_table_format(self, mock_stdout):
        output([{"id": "s1", "name": "src"}], fmt="table")
        printed = mock_stdout.getvalue()
        self.assertIn("ID", printed)

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_output_compact_format(self, mock_stdout):
        output([{"id": "s1", "name": "src"}], fmt="compact")
        printed = mock_stdout.getvalue()
        self.assertIn("|", printed)

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_output_non_list_in_table_mode_uses_json(self, mock_stdout):
        output({"id": "s1"}, fmt="table")
        printed = mock_stdout.getvalue()
        parsed = json.loads(printed)
        self.assertEqual(parsed["id"], "s1")


class TestError(unittest.TestCase):
    @patch("sys.stderr", new_callable=io.StringIO)
    def test_error_output_to_stderr(self, mock_stderr):
        error("not_found", "Resource not found", status=404)
        printed = mock_stderr.getvalue()
        parsed = json.loads(printed)
        self.assertEqual(parsed["error"], "not_found")
        self.assertEqual(parsed["message"], "Resource not found")
        self.assertEqual(parsed["status"], 404)

    @patch("sys.stderr", new_callable=io.StringIO)
    def test_error_without_status(self, mock_stderr):
        error("usage", "No action specified")
        printed = mock_stderr.getvalue()
        parsed = json.loads(printed)
        self.assertNotIn("status", parsed)


if __name__ == "__main__":
    unittest.main()
