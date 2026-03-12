"""Tests for the streams plugin."""

from __future__ import annotations

import argparse
import unittest
from unittest.mock import MagicMock, patch

from airbyte_cli.core.registry import Registry
from airbyte_cli.plugins.streams import api
from airbyte_cli.plugins.streams.commands import register_commands, _handle


def _make_client(return_value=None):
    client = MagicMock()
    client.request.return_value = return_value or {}
    return client


def _make_context(client=None):
    c = client or _make_client()
    return {"get_client": lambda: c, "format": "json"}


class TestStreamsApi(unittest.TestCase):
    def test_get_stream(self):
        payload = {"streamId": "s1", "name": "orders", "sourceId": "src1"}
        client = _make_client(payload)
        result = api.get_stream(client, "s1")
        client.request.assert_called_once_with("GET", "/streams/s1")
        self.assertEqual(result["streamId"], "s1")
        self.assertEqual(result["name"], "orders")

    def test_get_stream_returns_raw_dict(self):
        payload = {"streamId": "s2", "extra_field": [1, 2, 3]}
        client = _make_client(payload)
        result = api.get_stream(client, "s2")
        # Streams returns raw dict, no model transformation
        self.assertIsInstance(result, dict)
        self.assertEqual(result["extra_field"], [1, 2, 3])


class TestStreamsCommands(unittest.TestCase):
    def _run(self, action: str, extra_attrs: dict | None = None, client=None) -> tuple[int, MagicMock]:
        if client is None:
            client = _make_client({})
        args = argparse.Namespace(streams_action=action, format="json")
        if extra_attrs:
            for k, v in extra_attrs.items():
                setattr(args, k, v)
        ctx = _make_context(client)
        with patch("airbyte_cli.plugins.streams.commands.output") as mock_out:
            code = _handle(args, ctx)
        return code, mock_out

    def test_get_calls_api(self):
        client = _make_client({"streamId": "s1", "name": "orders"})
        code, mock_out = self._run("get", {"stream_id": "s1"}, client=client)
        self.assertEqual(code, 0)
        client.request.assert_called_once_with("GET", "/streams/s1")
        mock_out.assert_called_once()

    def test_get_passes_result_to_output(self):
        payload = {"streamId": "s2", "name": "users"}
        client = _make_client(payload)
        code, mock_out = self._run("get", {"stream_id": "s2"}, client=client)
        self.assertEqual(code, 0)
        call_args = mock_out.call_args
        self.assertEqual(call_args[0][0], payload)

    def test_no_action_returns_1(self):
        code, _ = self._run(None)
        self.assertEqual(code, 1)

    def test_register_commands_adds_parser(self):
        Registry.reset()
        import argparse as ap
        root = ap.ArgumentParser()
        sub = root.add_subparsers()
        register_commands(sub, {})
        args = root.parse_args(["streams", "get", "--id", "s1"])
        self.assertEqual(args.streams_action, "get")
        self.assertEqual(args.stream_id, "s1")


if __name__ == "__main__":
    unittest.main()
