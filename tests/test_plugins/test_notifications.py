"""Tests for the notifications plugin."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from airbyte_api_cli.core.registry import Registry
from airbyte_api_cli.plugins.notifications.api import NotificationsApi


def _make_context():
    mock_client = MagicMock()
    return {"get_config_client": lambda: mock_client, "format": "json", "_client": mock_client}


class TestNotificationsApi(unittest.TestCase):
    def setUp(self):
        self.client = MagicMock()

    def test_try_notification_slack_posts_correct_body(self):
        self.client.request.return_value = {"status": "succeeded"}
        api = NotificationsApi(self.client)
        result = api.try_notification("slack", slack_webhook="https://hooks.slack.com/abc")
        self.client.request.assert_called_once_with(
            "POST", "notifications/try",
            body={
                "notificationType": "slack",
                "slackConfiguration": {"webhook": "https://hooks.slack.com/abc"},
            },
        )
        self.assertEqual(result["status"], "succeeded")

    def test_try_notification_email_posts_correct_body(self):
        self.client.request.return_value = {"status": "succeeded"}
        api = NotificationsApi(self.client)
        result = api.try_notification("email")
        self.client.request.assert_called_once_with(
            "POST", "notifications/try",
            body={"notificationType": "email"},
        )
        self.assertEqual(result["status"], "succeeded")

    def test_try_notification_slack_without_webhook_omits_slack_config(self):
        self.client.request.return_value = {"status": "succeeded"}
        api = NotificationsApi(self.client)
        api.try_notification("slack", slack_webhook=None)
        call_body = self.client.request.call_args[1]["body"]
        self.assertNotIn("slackConfiguration", call_body)


class TestNotificationsPluginRegistration(unittest.TestCase):
    def setUp(self):
        Registry.reset()

    def test_plugin_registers_on_import(self):
        import importlib
        import airbyte_api_cli.plugins.notifications
        importlib.reload(airbyte_api_cli.plugins.notifications)
        plugin = Registry.instance().get_plugin("notifications")
        self.assertIsNotNone(plugin)
        self.assertEqual(plugin.name, "notifications")

    def test_register_adds_subparser(self):
        import argparse
        from airbyte_api_cli.plugins.notifications.commands import register_commands

        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="cmd")
        context = {"get_config_client": lambda: MagicMock(), "format": "json"}
        register_commands(subparsers, context)
        args = parser.parse_args(["notifications", "try", "--type", "slack", "--webhook", "https://hooks.slack.com/x"])
        self.assertTrue(hasattr(args, "handler"))
        self.assertEqual(args.notification_type, "slack")
        self.assertEqual(args.webhook, "https://hooks.slack.com/x")


class TestNotificationsCommands(unittest.TestCase):
    def test_handle_try_slack(self):
        from airbyte_api_cli.plugins.notifications.commands import _handle

        ctx = _make_context()
        ctx["_client"].request.return_value = {"status": "succeeded"}

        args = MagicMock()
        args.action = "try"
        args.notification_type = "slack"
        args.webhook = "https://hooks.slack.com/abc"

        with patch("airbyte_api_cli.plugins.notifications.commands.output") as mock_out:
            result = _handle(args, ctx)
        self.assertEqual(result, 0)
        mock_out.assert_called_once()

    def test_handle_try_email(self):
        from airbyte_api_cli.plugins.notifications.commands import _handle

        ctx = _make_context()
        ctx["_client"].request.return_value = {"status": "succeeded"}

        args = MagicMock()
        args.action = "try"
        args.notification_type = "email"
        args.webhook = None

        with patch("airbyte_api_cli.plugins.notifications.commands.output") as mock_out:
            result = _handle(args, ctx)
        self.assertEqual(result, 0)
        mock_out.assert_called_once()

    def test_handle_try_slack_requires_webhook(self):
        from airbyte_api_cli.plugins.notifications.commands import _handle

        ctx = _make_context()
        args = MagicMock()
        args.action = "try"
        args.notification_type = "slack"
        args.webhook = None

        with patch("airbyte_api_cli.plugins.notifications.commands.error") as mock_err:
            result = _handle(args, ctx)
        self.assertEqual(result, 1)
        mock_err.assert_called_once()

    def test_handle_no_action_returns_error(self):
        from airbyte_api_cli.plugins.notifications.commands import _handle

        ctx = _make_context()
        args = MagicMock()
        args.action = None

        with patch("airbyte_api_cli.plugins.notifications.commands.error") as mock_err:
            result = _handle(args, ctx)
        self.assertEqual(result, 1)
        mock_err.assert_called_once()

    def test_handle_try_passes_format_to_output(self):
        from airbyte_api_cli.plugins.notifications.commands import _handle

        ctx = _make_context()
        ctx["format"] = "table"
        ctx["_client"].request.return_value = {"status": "succeeded"}

        args = MagicMock()
        args.action = "try"
        args.notification_type = "email"
        args.webhook = None

        with patch("airbyte_api_cli.plugins.notifications.commands.output") as mock_out:
            _handle(args, ctx)
        mock_out.assert_called_once_with({"status": "succeeded"}, "table")


if __name__ == "__main__":
    unittest.main()
