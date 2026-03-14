"""Tests for the attempt_info plugin."""

from __future__ import annotations

import argparse
import unittest
from unittest.mock import MagicMock, patch

from airbyte_api_cli.core.registry import Registry
from airbyte_api_cli.plugins.attempt_info.api import AttemptInfoApi


def _make_context():
    mock_client = MagicMock()
    return {"get_config_client": lambda: mock_client, "format": "json", "_client": mock_client}


class TestAttemptInfoApi(unittest.TestCase):
    def setUp(self):
        self.client = MagicMock()
        self.api = AttemptInfoApi(self.client)

    def test_get_for_job_posts_correct_body(self):
        self.client.request.return_value = {"attempt": {}}
        result = self.api.get_for_job(42, 0)
        self.client.request.assert_called_once_with(
            "POST", "attempt/get_for_job",
            body={"jobId": 42, "attemptNumber": 0},
        )
        self.assertEqual(result, {"attempt": {}})

    def test_get_for_job_second_attempt(self):
        self.client.request.return_value = {"attempt": {"status": "failed"}}
        self.api.get_for_job(7, 1)
        call_body = self.client.request.call_args[1]["body"]
        self.assertEqual(call_body["jobId"], 7)
        self.assertEqual(call_body["attemptNumber"], 1)

    def test_get_debug_info_posts_correct_body(self):
        self.client.request.return_value = {"job": {}, "attempts": []}
        result = self.api.get_debug_info(99)
        self.client.request.assert_called_once_with(
            "POST", "jobs/get_debug_info",
            body={"id": 99},
        )
        self.assertEqual(result, {"job": {}, "attempts": []})

    def test_get_last_replication_job_posts_correct_body(self):
        self.client.request.return_value = {"job": {"jobId": 5}}
        result = self.api.get_last_replication_job("conn-abc")
        self.client.request.assert_called_once_with(
            "POST", "jobs/get_last_replication_job",
            body={"connectionId": "conn-abc"},
        )
        self.assertEqual(result["job"]["jobId"], 5)

    def test_get_last_replication_job_returns_raw_response(self):
        self.client.request.return_value = {}
        result = self.api.get_last_replication_job("conn-xyz")
        self.assertEqual(result, {})


class TestAttemptInfoPluginRegistration(unittest.TestCase):
    def setUp(self):
        Registry.reset()

    def test_plugin_registers_on_import(self):
        import importlib
        import airbyte_api_cli.plugins.attempt_info
        importlib.reload(airbyte_api_cli.plugins.attempt_info)
        plugin = Registry.instance().get_plugin("attempt_info")
        self.assertIsNotNone(plugin)
        self.assertEqual(plugin.name, "attempt_info")

    def test_register_adds_subparser(self):
        from airbyte_api_cli.plugins.attempt_info.commands import register_commands

        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="cmd")
        context = {"get_config_client": lambda: MagicMock(), "format": "json"}
        register_commands(subparsers, context)
        args = parser.parse_args(["attempt_info", "get", "--job-id", "10", "--attempt", "0"])
        self.assertTrue(hasattr(args, "handler"))
        self.assertEqual(args.job_id, 10)
        self.assertEqual(args.attempt_number, 0)


class TestAttemptInfoCommands(unittest.TestCase):
    def test_handle_get(self):
        from airbyte_api_cli.plugins.attempt_info.commands import _handle

        ctx = _make_context()
        ctx["_client"].request.return_value = {"attempt": {"status": "succeeded"}}

        args = argparse.Namespace(action="get", job_id=1, attempt_number=0)
        with patch("airbyte_api_cli.plugins.attempt_info.commands.output") as mock_out:
            result = _handle(args, ctx)
        self.assertEqual(result, 0)
        mock_out.assert_called_once_with({"attempt": {"status": "succeeded"}}, "json")

    def test_handle_debug(self):
        from airbyte_api_cli.plugins.attempt_info.commands import _handle

        ctx = _make_context()
        ctx["_client"].request.return_value = {"job": {}, "attempts": []}

        args = argparse.Namespace(action="debug", job_id=5)
        with patch("airbyte_api_cli.plugins.attempt_info.commands.output") as mock_out:
            result = _handle(args, ctx)
        self.assertEqual(result, 0)
        mock_out.assert_called_once_with({"job": {}, "attempts": []}, "json")

    def test_handle_last_job(self):
        from airbyte_api_cli.plugins.attempt_info.commands import _handle

        ctx = _make_context()
        ctx["_client"].request.return_value = {"job": {"jobId": 3}}

        args = argparse.Namespace(action="last-job", connection_id="conn-1")
        with patch("airbyte_api_cli.plugins.attempt_info.commands.output") as mock_out:
            result = _handle(args, ctx)
        self.assertEqual(result, 0)
        mock_out.assert_called_once_with({"job": {"jobId": 3}}, "json")

    def test_handle_no_action_returns_error(self):
        from airbyte_api_cli.plugins.attempt_info.commands import _handle

        ctx = _make_context()
        args = argparse.Namespace(action=None)
        with patch("airbyte_api_cli.plugins.attempt_info.commands.error") as mock_err:
            result = _handle(args, ctx)
        self.assertEqual(result, 1)
        mock_err.assert_called_once()

    def test_handle_unknown_action_returns_error(self):
        from airbyte_api_cli.plugins.attempt_info.commands import _handle

        ctx = _make_context()
        args = argparse.Namespace(action="unknown")
        with patch("airbyte_api_cli.plugins.attempt_info.commands.error") as mock_err:
            result = _handle(args, ctx)
        self.assertEqual(result, 1)
        mock_err.assert_called_once()

    def test_handle_get_passes_format_to_output(self):
        from airbyte_api_cli.plugins.attempt_info.commands import _handle

        ctx = _make_context()
        ctx["format"] = "table"
        ctx["_client"].request.return_value = {"attempt": {}}

        args = argparse.Namespace(action="get", job_id=2, attempt_number=1)
        with patch("airbyte_api_cli.plugins.attempt_info.commands.output") as mock_out:
            _handle(args, ctx)
        mock_out.assert_called_once_with({"attempt": {}}, "table")

    def test_handle_get_calls_api_with_correct_args(self):
        from airbyte_api_cli.plugins.attempt_info.commands import _handle

        ctx = _make_context()
        ctx["_client"].request.return_value = {}

        args = argparse.Namespace(action="get", job_id=10, attempt_number=3)
        with patch("airbyte_api_cli.plugins.attempt_info.commands.output"):
            _handle(args, ctx)
        ctx["_client"].request.assert_called_once_with(
            "POST", "attempt/get_for_job",
            body={"jobId": 10, "attemptNumber": 3},
        )

    def test_handle_debug_calls_api_with_correct_job_id(self):
        from airbyte_api_cli.plugins.attempt_info.commands import _handle

        ctx = _make_context()
        ctx["_client"].request.return_value = {}

        args = argparse.Namespace(action="debug", job_id=77)
        with patch("airbyte_api_cli.plugins.attempt_info.commands.output"):
            _handle(args, ctx)
        ctx["_client"].request.assert_called_once_with(
            "POST", "jobs/get_debug_info",
            body={"id": 77},
        )

    def test_handle_last_job_calls_api_with_correct_connection_id(self):
        from airbyte_api_cli.plugins.attempt_info.commands import _handle

        ctx = _make_context()
        ctx["_client"].request.return_value = {}

        args = argparse.Namespace(action="last-job", connection_id="conn-xyz")
        with patch("airbyte_api_cli.plugins.attempt_info.commands.output"):
            _handle(args, ctx)
        ctx["_client"].request.assert_called_once_with(
            "POST", "jobs/get_last_replication_job",
            body={"connectionId": "conn-xyz"},
        )


if __name__ == "__main__":
    unittest.main()
