"""Tests for the builder_projects plugin."""

from __future__ import annotations

import argparse
import unittest
from unittest.mock import MagicMock, call, patch

from airbyte_api_cli.models.common import ApiResponse
from airbyte_api_cli.plugins.builder_projects.models import (
    BuilderProjectPublish,
    BuilderProjectReadStream,
)


def _ctx(mock_client):
    return {"get_config_client": lambda: mock_client, "format": "json"}


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------


class TestBuilderProjectPublish(unittest.TestCase):
    def test_to_dict_all_fields(self):
        payload = BuilderProjectPublish(
            workspace_id="ws1",
            project_id="proj1",
            name="My Connector",
            manifest={"version": "0.1.0"},
            spec={"connectionSpecification": {"type": "object"}},
            description="A great connector",
            version=2,
        )
        d = payload.to_dict()
        self.assertEqual(d["workspaceId"], "ws1")
        self.assertEqual(d["builderProjectId"], "proj1")
        self.assertEqual(d["name"], "My Connector")
        inner = d["initialDeclarativeManifest"]
        self.assertEqual(inner["manifest"], {"version": "0.1.0"})
        self.assertEqual(inner["spec"], {"connectionSpecification": {"type": "object"}})
        self.assertEqual(inner["description"], "A great connector")
        self.assertEqual(inner["version"], 2)

    def test_to_dict_empty_description_still_present(self):
        payload = BuilderProjectPublish(
            workspace_id="ws1",
            project_id="proj1",
            name="Minimal",
            manifest={},
            spec={},
        )
        d = payload.to_dict()
        inner = d["initialDeclarativeManifest"]
        self.assertIn("description", inner)
        self.assertEqual(inner["description"], "")

    def test_to_dict_default_version_zero(self):
        payload = BuilderProjectPublish(
            workspace_id="ws1",
            project_id="proj1",
            name="Minimal",
            manifest={},
            spec={},
        )
        inner = payload.to_dict()["initialDeclarativeManifest"]
        self.assertEqual(inner["version"], 0)

    def test_to_dict_camelcase_keys(self):
        payload = BuilderProjectPublish(
            workspace_id="ws1",
            project_id="proj1",
            name="Test",
            manifest={},
            spec={},
        )
        d = payload.to_dict()
        self.assertIn("workspaceId", d)
        self.assertIn("builderProjectId", d)
        self.assertIn("initialDeclarativeManifest", d)
        self.assertNotIn("workspace_id", d)
        self.assertNotIn("project_id", d)


class TestBuilderProjectReadStream(unittest.TestCase):
    def test_to_dict_required_fields(self):
        payload = BuilderProjectReadStream(
            workspace_id="ws1",
            manifest={"version": "0.1.0"},
            stream_name="users",
            config={"api_key": "secret"},
        )
        d = payload.to_dict()
        self.assertEqual(d["workspaceId"], "ws1")
        self.assertEqual(d["manifest"], {"version": "0.1.0"})
        self.assertEqual(d["streamName"], "users")
        self.assertEqual(d["config"], {"api_key": "secret"})
        self.assertFalse(d["formGeneratedManifest"])

    def test_to_dict_optional_fields_omitted_when_absent(self):
        payload = BuilderProjectReadStream(
            workspace_id="ws1",
            manifest={},
            stream_name="orders",
            config={},
        )
        d = payload.to_dict()
        self.assertNotIn("recordLimit", d)
        self.assertNotIn("pageLimit", d)
        self.assertNotIn("builderProjectId", d)

    def test_to_dict_optional_fields_included_when_set(self):
        payload = BuilderProjectReadStream(
            workspace_id="ws1",
            manifest={"version": "0.2.0"},
            stream_name="events",
            config={},
            project_id="proj-99",
            record_limit=100,
            page_limit=5,
        )
        d = payload.to_dict()
        self.assertEqual(d["builderProjectId"], "proj-99")
        self.assertEqual(d["recordLimit"], 100)
        self.assertEqual(d["pageLimit"], 5)

    def test_to_dict_form_generated_manifest_true(self):
        payload = BuilderProjectReadStream(
            workspace_id="ws1",
            manifest={},
            stream_name="items",
            config={},
            form_generated_manifest=True,
        )
        self.assertTrue(payload.to_dict()["formGeneratedManifest"])

    def test_to_dict_record_limit_none_omitted(self):
        payload = BuilderProjectReadStream(
            workspace_id="ws1",
            manifest={},
            stream_name="s",
            config={},
            record_limit=None,
            page_limit=None,
        )
        d = payload.to_dict()
        self.assertNotIn("recordLimit", d)
        self.assertNotIn("pageLimit", d)


# ---------------------------------------------------------------------------
# API tests
# ---------------------------------------------------------------------------


class TestBuilderProjectsApi(unittest.TestCase):
    def setUp(self):
        self.client = MagicMock()
        from airbyte_api_cli.plugins.builder_projects.api import BuilderProjectsApi
        self.api = BuilderProjectsApi(self.client)

    def test_list_calls_correct_endpoint(self):
        self.client.request.return_value = {"projects": [{"builderProjectId": "p1"}]}
        result = self.api.list("ws1")
        self.client.request.assert_called_once_with(
            "POST",
            "connector_builder_projects/list",
            body={"workspaceId": "ws1"},
        )
        self.assertIsInstance(result, ApiResponse)
        self.assertEqual(result.data[0]["builderProjectId"], "p1")

    def test_list_returns_empty_projects(self):
        self.client.request.return_value = {"projects": []}
        result = self.api.list("ws1")
        self.assertEqual(result.data, [])

    def test_list_missing_key_returns_empty(self):
        self.client.request.return_value = {}
        result = self.api.list("ws1")
        self.assertEqual(result.data, [])

    def test_get_calls_correct_endpoint(self):
        self.client.request.return_value = {
            "builderProjectId": "p1",
            "name": "Test Connector",
        }
        result = self.api.get("ws1", "p1")
        self.client.request.assert_called_once_with(
            "POST",
            "connector_builder_projects/get_with_manifest",
            body={"workspaceId": "ws1", "builderProjectId": "p1"},
        )
        self.assertEqual(result["builderProjectId"], "p1")

    def test_create_calls_correct_endpoint(self):
        self.client.request.return_value = {"builderProjectId": "new-p"}
        result = self.api.create("ws1", "New Project", {"version": "0.1.0"})
        self.client.request.assert_called_once_with(
            "POST",
            "connector_builder_projects/create",
            body={
                "workspaceId": "ws1",
                "builderProject": {
                    "name": "New Project",
                    "draftManifest": {"version": "0.1.0"},
                },
            },
        )
        self.assertEqual(result["builderProjectId"], "new-p")

    def test_create_empty_manifest(self):
        self.client.request.return_value = {"builderProjectId": "p2"}
        self.api.create("ws1", "Empty Manifest Project", {})
        call_body = self.client.request.call_args[1]["body"]
        self.assertEqual(call_body["builderProject"]["draftManifest"], {})

    def test_update_calls_correct_endpoint(self):
        self.client.request.return_value = {}
        result = self.api.update("ws1", "p1", "Updated Name", {"version": "0.2.0"})
        self.client.request.assert_called_once()
        call_args = self.client.request.call_args
        self.assertIn("connector_builder_projects/update", call_args[0][1])
        call_body = call_args[1]["body"]
        self.assertEqual(call_body["workspaceId"], "ws1")
        self.assertEqual(call_body["builderProjectId"], "p1")
        self.assertEqual(call_body["builderProject"]["name"], "Updated Name")
        self.assertEqual(call_body["builderProject"]["draftManifest"], {"version": "0.2.0"})

    def test_update_returns_none(self):
        self.client.request.return_value = {}
        result = self.api.update("ws1", "p1", "Name", {})
        self.assertIsNone(result)

    def test_delete_calls_correct_endpoint(self):
        self.client.request.return_value = {}
        self.api.delete("ws1", "p1")
        self.client.request.assert_called_once_with(
            "POST",
            "connector_builder_projects/delete",
            body={"workspaceId": "ws1", "builderProjectId": "p1"},
        )

    def test_delete_returns_none(self):
        self.client.request.return_value = {}
        result = self.api.delete("ws1", "p1")
        self.assertIsNone(result)

    def test_publish_calls_correct_endpoint(self):
        self.client.request.return_value = {"sourceDefinitionId": "sd1"}
        payload = BuilderProjectPublish(
            workspace_id="ws1",
            project_id="p1",
            name="Published Connector",
            manifest={"version": "1.0.0"},
            spec={"connectionSpecification": {}},
        )
        result = self.api.publish(payload)
        self.client.request.assert_called_once_with(
            "POST",
            "connector_builder_projects/publish",
            body=payload.to_dict(),
        )
        self.assertEqual(result["sourceDefinitionId"], "sd1")

    def test_read_stream_calls_correct_endpoint(self):
        self.client.request.return_value = {"logs": [], "slices": []}
        payload = BuilderProjectReadStream(
            workspace_id="ws1",
            manifest={"version": "0.1.0"},
            stream_name="users",
            config={"api_key": "key"},
        )
        result = self.api.read_stream(payload)
        self.client.request.assert_called_once_with(
            "POST",
            "connector_builder_projects/read_stream",
            body=payload.to_dict(),
        )
        self.assertIn("logs", result)

    def test_read_stream_with_optional_fields(self):
        self.client.request.return_value = {"logs": [], "slices": []}
        payload = BuilderProjectReadStream(
            workspace_id="ws1",
            manifest={"version": "0.1.0"},
            stream_name="events",
            config={},
            project_id="p-99",
            record_limit=50,
        )
        self.api.read_stream(payload)
        call_body = self.client.request.call_args[1]["body"]
        self.assertEqual(call_body["builderProjectId"], "p-99")
        self.assertEqual(call_body["recordLimit"], 50)


# ---------------------------------------------------------------------------
# Command tests
# ---------------------------------------------------------------------------


class TestBuilderProjectsCommands(unittest.TestCase):
    def test_list_command_registered(self):
        from airbyte_api_cli.plugins.builder_projects.commands import register_commands

        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        register_commands(sub, {})
        args = parser.parse_args(["builder_projects", "list", "--workspace-id", "ws1"])
        self.assertEqual(args.action, "list")
        self.assertEqual(args.workspace_id, "ws1")

    def test_get_command_registered(self):
        from airbyte_api_cli.plugins.builder_projects.commands import register_commands

        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        register_commands(sub, {})
        args = parser.parse_args([
            "builder_projects", "get",
            "--workspace-id", "ws1",
            "--id", "p1",
        ])
        self.assertEqual(args.action, "get")
        self.assertEqual(args.project_id, "p1")

    def test_create_command_registered(self):
        from airbyte_api_cli.plugins.builder_projects.commands import register_commands

        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        register_commands(sub, {})
        args = parser.parse_args([
            "builder_projects", "create",
            "--workspace-id", "ws1",
            "--name", "My Project",
        ])
        self.assertEqual(args.action, "create")
        self.assertEqual(args.name, "My Project")

    def test_delete_command_registered(self):
        from airbyte_api_cli.plugins.builder_projects.commands import register_commands

        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        register_commands(sub, {})
        args = parser.parse_args([
            "builder_projects", "delete",
            "--workspace-id", "ws1",
            "--id", "p1",
        ])
        self.assertEqual(args.action, "delete")
        self.assertEqual(args.project_id, "p1")

    def test_publish_command_registered(self):
        from airbyte_api_cli.plugins.builder_projects.commands import register_commands

        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        register_commands(sub, {})
        args = parser.parse_args([
            "builder_projects", "publish",
            "--workspace-id", "ws1",
            "--id", "p1",
            "--manifest", '{"type":"DeclarativeSource"}',
            "--spec", '{"type":"object"}',
            "--name", "Published",
        ])
        self.assertEqual(args.action, "publish")

    def test_read_stream_command_registered(self):
        from airbyte_api_cli.plugins.builder_projects.commands import register_commands

        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        register_commands(sub, {})
        args = parser.parse_args([
            "builder_projects", "read-stream",
            "--workspace-id", "ws1",
            "--stream-name", "users",
            "--config", '{"api_key":"test"}',
        ])
        self.assertEqual(args.action, "read-stream")
        self.assertEqual(args.stream_name, "users")

    def test_handle_no_action_returns_1(self):
        from airbyte_api_cli.plugins.builder_projects.commands import _handle

        args = argparse.Namespace(action=None)
        result = _handle(args, _ctx(MagicMock()))
        self.assertEqual(result, 1)

    def test_handle_list_calls_api(self):
        from airbyte_api_cli.plugins.builder_projects.commands import _handle

        mock_client = MagicMock()
        mock_client.request.return_value = {"projects": [{"builderProjectId": "p1"}]}
        args = argparse.Namespace(action="list", workspace_id="ws1")
        result = _handle(args, _ctx(mock_client))
        self.assertEqual(result, 0)
        mock_client.request.assert_called_once_with(
            "POST",
            "connector_builder_projects/list",
            body={"workspaceId": "ws1"},
        )

    def test_handle_get_calls_api(self):
        from airbyte_api_cli.plugins.builder_projects.commands import _handle

        mock_client = MagicMock()
        mock_client.request.return_value = {"builderProjectId": "p1"}
        args = argparse.Namespace(action="get", workspace_id="ws1", project_id="p1")
        result = _handle(args, _ctx(mock_client))
        self.assertEqual(result, 0)
        mock_client.request.assert_called_once_with(
            "POST",
            "connector_builder_projects/get_with_manifest",
            body={"workspaceId": "ws1", "builderProjectId": "p1"},
        )

    def test_handle_create_calls_api(self):
        from airbyte_api_cli.plugins.builder_projects.commands import _handle

        mock_client = MagicMock()
        mock_client.request.return_value = {"builderProjectId": "new"}
        args = argparse.Namespace(
            action="create",
            workspace_id="ws1",
            name="New Project",
            manifest='{"version": "0.1.0"}',
        )
        result = _handle(args, _ctx(mock_client))
        self.assertEqual(result, 0)
        call_body = mock_client.request.call_args[1]["body"]
        self.assertEqual(call_body["workspaceId"], "ws1")
        self.assertEqual(call_body["builderProject"]["name"], "New Project")

    def test_handle_update_calls_api(self):
        from airbyte_api_cli.plugins.builder_projects.commands import _handle

        mock_client = MagicMock()
        mock_client.request.return_value = {}
        args = argparse.Namespace(
            action="update",
            workspace_id="ws1",
            project_id="p1",
            name="Updated",
            manifest='{"version": "0.2.0"}',
        )
        result = _handle(args, _ctx(mock_client))
        self.assertEqual(result, 0)
        mock_client.request.assert_called_once()
        self.assertIn("update", mock_client.request.call_args[0][1])

    def test_handle_delete_calls_api(self):
        from airbyte_api_cli.plugins.builder_projects.commands import _handle

        mock_client = MagicMock()
        mock_client.request.return_value = {}
        args = argparse.Namespace(action="delete", workspace_id="ws1", project_id="p1")
        result = _handle(args, _ctx(mock_client))
        self.assertEqual(result, 0)
        mock_client.request.assert_called_once_with(
            "POST",
            "connector_builder_projects/delete",
            body={"workspaceId": "ws1", "builderProjectId": "p1"},
        )

    def test_handle_publish_calls_api(self):
        from airbyte_api_cli.plugins.builder_projects.commands import _handle

        mock_client = MagicMock()
        mock_client.request.return_value = {"sourceDefinitionId": "sd1"}
        args = argparse.Namespace(
            action="publish",
            workspace_id="ws1",
            project_id="p1",
            name="Published Connector",
            manifest='{"version": "1.0.0"}',
            spec="{}",
            description="",
            version=0,
        )
        result = _handle(args, _ctx(mock_client))
        self.assertEqual(result, 0)
        call_body = mock_client.request.call_args[1]["body"]
        self.assertEqual(call_body["workspaceId"], "ws1")
        self.assertEqual(call_body["builderProjectId"], "p1")
        self.assertIn("initialDeclarativeManifest", call_body)

    def test_handle_read_stream_with_manifest_arg(self):
        from airbyte_api_cli.plugins.builder_projects.commands import _handle

        mock_client = MagicMock()
        mock_client.request.return_value = {"logs": [], "slices": []}
        args = argparse.Namespace(
            action="read-stream",
            workspace_id="ws1",
            stream_name="users",
            manifest='{"version": "0.1.0"}',
            config="{}",
            project_id="",
            record_limit=None,
            page_limit=None,
            form_generated_manifest=False,
        )
        result = _handle(args, _ctx(mock_client))
        self.assertEqual(result, 0)
        call_body = mock_client.request.call_args[1]["body"]
        self.assertEqual(call_body["streamName"], "users")

    def test_handle_read_stream_with_project_id_fetches_manifest(self):
        from airbyte_api_cli.plugins.builder_projects.commands import _handle

        mock_client = MagicMock()
        mock_client.request.side_effect = [
            # First call: get project manifest
            {"builderProjectId": "p1", "manifest": {"version": "0.1.0"}},
            # Second call: read_stream
            {"logs": [], "slices": []},
        ]
        args = argparse.Namespace(
            action="read-stream",
            workspace_id="ws1",
            stream_name="events",
            manifest=None,
            config="{}",
            project_id="p1",
            record_limit=None,
            page_limit=None,
            form_generated_manifest=False,
        )
        result = _handle(args, _ctx(mock_client))
        self.assertEqual(result, 0)
        self.assertEqual(mock_client.request.call_count, 2)
        first_call = mock_client.request.call_args_list[0]
        self.assertIn("get_with_manifest", first_call[0][1])

    def test_handle_read_stream_no_manifest_no_project_returns_error(self):
        from airbyte_api_cli.plugins.builder_projects.commands import _handle

        mock_client = MagicMock()
        args = argparse.Namespace(
            action="read-stream",
            workspace_id="ws1",
            stream_name="users",
            manifest=None,
            config="{}",
            project_id="",
            record_limit=None,
            page_limit=None,
            form_generated_manifest=False,
        )
        result = _handle(args, _ctx(mock_client))
        self.assertEqual(result, 1)
        mock_client.request.assert_not_called()

    def test_handle_read_stream_explicit_manifest_overrides_project(self):
        from airbyte_api_cli.plugins.builder_projects.commands import _handle

        mock_client = MagicMock()
        mock_client.request.return_value = {"logs": [], "slices": []}
        args = argparse.Namespace(
            action="read-stream",
            workspace_id="ws1",
            stream_name="users",
            manifest='{"version": "0.3.0"}',
            config="{}",
            project_id="p1",
            record_limit=None,
            page_limit=None,
            form_generated_manifest=False,
        )
        result = _handle(args, _ctx(mock_client))
        self.assertEqual(result, 0)
        # Only one request — no fetch for project manifest
        self.assertEqual(mock_client.request.call_count, 1)
        call_body = mock_client.request.call_args[1]["body"]
        self.assertEqual(call_body["manifest"], {"version": "0.3.0"})


# ---------------------------------------------------------------------------
# Plugin registration test
# ---------------------------------------------------------------------------


class TestBuilderProjectsPluginRegistration(unittest.TestCase):
    def setUp(self):
        from airbyte_api_cli.core.registry import Registry
        Registry.reset()

    def test_plugin_registers_on_import(self):
        import importlib

        from airbyte_api_cli.core.registry import Registry
        import airbyte_api_cli.plugins.builder_projects
        importlib.reload(airbyte_api_cli.plugins.builder_projects)
        plugin = Registry.instance().get_plugin("builder_projects")
        self.assertIsNotNone(plugin)
        self.assertEqual(plugin.name, "builder_projects")


if __name__ == "__main__":
    unittest.main()
