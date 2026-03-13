"""End-to-end CLI integration tests.

These test the full main() pipeline: argv parsing → config → auth → HTTP → output,
with HTTP responses mocked at the urllib layer.
"""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from airbyte_api_cli.__main__ import main


def _make_config_dir(**overrides):
    """Create a temp config dir with a valid config.json."""
    d = tempfile.mkdtemp()
    config = {
        "base_url": "http://localhost:8000/api/public/v1",
        "username": "airbyte",
        "password": "password",
        "timeout": 5,
        **overrides,
    }
    (Path(d) / "config.json").write_text(json.dumps(config))
    return d


def _mock_urlopen(responses):
    """Build a mock for urllib.request.urlopen that returns responses in order.

    Each response is a dict that will be JSON-serialized.
    """
    call_idx = {"n": 0}

    def urlopen(req, timeout=None):
        idx = call_idx["n"]
        call_idx["n"] += 1
        body = responses[idx] if idx < len(responses) else {}
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(body).encode("utf-8")
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        return mock_resp

    return urlopen


class TestCliPaginationAllFlag(unittest.TestCase):
    """Test --all flag exercises paginate_all through the full CLI pipeline."""

    def test_sources_list_all_paginates(self):
        config_dir = _make_config_dir()
        page1 = {"data": [{"sourceId": f"s{i}"} for i in range(3)]}
        page2 = {"data": [{"sourceId": "s3"}]}

        with patch("urllib.request.urlopen", side_effect=_mock_urlopen([page1, page2])):
            with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
                rc = main(["--config-dir", config_dir, "sources", "list", "--all", "--limit", "3"])

        self.assertEqual(rc, 0)
        output = json.loads(mock_stdout.getvalue())
        self.assertEqual(len(output), 4)
        self.assertEqual(output[0]["sourceId"], "s0")
        self.assertEqual(output[3]["sourceId"], "s3")

    def test_jobs_list_all_paginates(self):
        config_dir = _make_config_dir()
        page1 = {"data": [{"jobId": i} for i in range(2)]}
        page2 = {"data": [{"jobId": 2}]}

        with patch("urllib.request.urlopen", side_effect=_mock_urlopen([page1, page2])):
            with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
                rc = main(["--config-dir", config_dir, "jobs", "list", "--all", "--limit", "2"])

        self.assertEqual(rc, 0)
        output = json.loads(mock_stdout.getvalue())
        self.assertEqual(len(output), 3)

    def test_connections_list_all_paginates(self):
        config_dir = _make_config_dir()
        page1 = {"data": [{"connectionId": "c1"}, {"connectionId": "c2"}]}
        page2 = {"data": [{"connectionId": "c3"}]}

        with patch("urllib.request.urlopen", side_effect=_mock_urlopen([page1, page2])):
            with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
                rc = main(["--config-dir", config_dir, "connections", "list", "--all", "--limit", "2"])

        self.assertEqual(rc, 0)
        output = json.loads(mock_stdout.getvalue())
        self.assertEqual(len(output), 3)


class TestCliJobsWait(unittest.TestCase):
    """Test jobs wait command through the full CLI pipeline."""

    def test_wait_succeeds_immediately(self):
        config_dir = _make_config_dir()
        job_resp = {"jobId": "42", "status": "succeeded", "rowsSynced": 100}

        with patch("urllib.request.urlopen", side_effect=_mock_urlopen([job_resp])):
            with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
                with patch("sys.stderr", new_callable=io.StringIO):
                    rc = main(["--config-dir", config_dir, "jobs", "wait", "--id", "42"])

        self.assertEqual(rc, 0)
        output = json.loads(mock_stdout.getvalue())
        self.assertEqual(output["status"], "succeeded")

    def test_wait_polls_until_succeeded(self):
        config_dir = _make_config_dir()
        responses = [
            {"jobId": "42", "status": "running"},
            {"jobId": "42", "status": "running"},
            {"jobId": "42", "status": "succeeded", "rowsSynced": 500},
        ]

        with patch("urllib.request.urlopen", side_effect=_mock_urlopen(responses)):
            with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
                with patch("sys.stderr", new_callable=io.StringIO):
                    with patch("time.sleep"):
                        rc = main(["--config-dir", config_dir, "jobs", "wait", "--id", "42", "--interval", "0"])

        self.assertEqual(rc, 0)
        output = json.loads(mock_stdout.getvalue())
        self.assertEqual(output["status"], "succeeded")
        self.assertEqual(output["rowsSynced"], 500)

    def test_wait_failed_returns_1(self):
        config_dir = _make_config_dir()
        job_resp = {"jobId": "42", "status": "failed"}

        with patch("urllib.request.urlopen", side_effect=_mock_urlopen([job_resp])):
            with patch("sys.stdout", new_callable=io.StringIO):
                with patch("sys.stderr", new_callable=io.StringIO):
                    rc = main(["--config-dir", config_dir, "jobs", "wait", "--id", "42"])

        self.assertEqual(rc, 1)

    def test_wait_timeout_returns_1(self):
        config_dir = _make_config_dir()
        running = {"jobId": "42", "status": "running"}

        times = iter([100.0, 100.5, 101.5])
        with patch("urllib.request.urlopen", side_effect=_mock_urlopen([running, running])):
            with patch("sys.stdout", new_callable=io.StringIO):
                with patch("sys.stderr", new_callable=io.StringIO):
                    with patch("time.sleep"), patch("time.monotonic", side_effect=times):
                        rc = main([
                            "--config-dir", config_dir,
                            "jobs", "wait", "--id", "42",
                            "--interval", "0", "--timeout", "1",
                        ])

        self.assertEqual(rc, 1)


class TestCliConfigPrefixCollision(unittest.TestCase):
    """Verify --config (subcommand) doesn't collide with --config-dir (global)."""

    def test_source_create_with_config_flag(self):
        config_dir = _make_config_dir()
        create_resp = {"sourceId": "new-src", "name": "Test"}

        with patch("urllib.request.urlopen", side_effect=_mock_urlopen([create_resp])):
            with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
                rc = main([
                    "--config-dir", config_dir,
                    "sources", "create",
                    "--name", "Test",
                    "--workspace-id", "ws-1",
                    "--type", "file",
                    "--config", '{"url": "test.csv"}',
                ])

        self.assertEqual(rc, 0)
        output = json.loads(mock_stdout.getvalue())
        self.assertEqual(output["sourceId"], "new-src")


class TestCliVersionString(unittest.TestCase):
    """Verify version output uses correct product name."""

    def test_version_shows_airbyte_api_cli(self):
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            try:
                main(["--version"])
            except SystemExit:
                pass

        self.assertIn("airbyte-api-cli", mock_stdout.getvalue())
        self.assertNotIn("airbyte-cli ", mock_stdout.getvalue())


class _CliTestBase(unittest.TestCase):
    """Base class providing helpers for CLI integration tests."""

    def setUp(self):
        self.config_dir = _make_config_dir()

    def _run(self, argv, responses):
        """Run main() with mocked HTTP, return (exit_code, stdout_str, stderr_str)."""
        with patch("urllib.request.urlopen", side_effect=_mock_urlopen(responses)):
            with patch("sys.stdout", new_callable=io.StringIO) as out:
                with patch("sys.stderr", new_callable=io.StringIO) as err:
                    rc = main(["--config-dir", self.config_dir] + argv)
        return rc, out.getvalue(), err.getvalue()

    def _run_json(self, argv, responses):
        """Run and parse JSON output."""
        rc, out, err = self._run(argv, responses)
        return rc, json.loads(out) if out.strip() else None


class TestCliHealth(_CliTestBase):
    def test_health(self):
        rc, out, _ = self._run(["health"], [{"message": "Successful operation"}])
        self.assertEqual(rc, 0)
        self.assertIn("Successful operation", out)


class TestCliWorkspaces(_CliTestBase):
    def test_list(self):
        rc, data = self._run_json(["workspaces", "list"], [{"data": [{"workspaceId": "ws-1"}]}])
        self.assertEqual(rc, 0)
        self.assertEqual(len(data), 1)

    def test_get(self):
        rc, data = self._run_json(
            ["workspaces", "get", "--id", "ws-1"],
            [{"workspaceId": "ws-1", "name": "Default"}],
        )
        self.assertEqual(rc, 0)
        self.assertEqual(data["name"], "Default")

    def test_create(self):
        rc, data = self._run_json(
            ["workspaces", "create", "--name", "New WS"],
            [{"workspaceId": "ws-new", "name": "New WS"}],
        )
        self.assertEqual(rc, 0)
        self.assertEqual(data["workspaceId"], "ws-new")

    def test_update(self):
        rc, data = self._run_json(
            ["workspaces", "update", "--id", "ws-1", "--name", "Renamed"],
            [{"workspaceId": "ws-1", "name": "Renamed"}],
        )
        self.assertEqual(rc, 0)
        self.assertEqual(data["name"], "Renamed")

    def test_delete(self):
        rc, _, _ = self._run(["workspaces", "delete", "--id", "ws-1"], [{}])
        self.assertEqual(rc, 0)


class TestCliSources(_CliTestBase):
    def test_list(self):
        rc, data = self._run_json(
            ["sources", "list", "--workspace-id", "ws-1"],
            [{"data": [{"sourceId": "s1"}]}],
        )
        self.assertEqual(rc, 0)
        self.assertEqual(data[0]["sourceId"], "s1")

    def test_get(self):
        rc, data = self._run_json(
            ["sources", "get", "--id", "s1"],
            [{"sourceId": "s1", "name": "Postgres"}],
        )
        self.assertEqual(rc, 0)
        self.assertEqual(data["name"], "Postgres")

    def test_create(self):
        rc, data = self._run_json(
            ["sources", "create", "--name", "PG", "--workspace-id", "ws-1",
             "--type", "postgres", "--config", '{"host":"localhost"}'],
            [{"sourceId": "s-new"}],
        )
        self.assertEqual(rc, 0)
        self.assertEqual(data["sourceId"], "s-new")

    def test_update(self):
        rc, data = self._run_json(
            ["sources", "update", "--id", "s1", "--data", '{"name":"Updated"}'],
            [{"sourceId": "s1", "name": "Updated"}],
        )
        self.assertEqual(rc, 0)

    def test_replace(self):
        rc, data = self._run_json(
            ["sources", "replace", "--id", "s1", "--name", "Replaced",
             "--workspace-id", "ws-1", "--type", "postgres", "--config", '{}'],
            [{"sourceId": "s1"}],
        )
        self.assertEqual(rc, 0)

    def test_delete(self):
        rc, _, _ = self._run(["sources", "delete", "--id", "s1"], [{}])
        self.assertEqual(rc, 0)

    def test_oauth(self):
        rc, data = self._run_json(
            ["sources", "oauth", "--data", '{"workspaceId":"ws-1","sourceType":"github"}'],
            [{"redirectUrl": "https://oauth.example.com"}],
        )
        self.assertEqual(rc, 0)


class TestCliDestinations(_CliTestBase):
    def test_list(self):
        rc, data = self._run_json(
            ["destinations", "list"],
            [{"data": [{"destinationId": "d1"}]}],
        )
        self.assertEqual(rc, 0)

    def test_get(self):
        rc, data = self._run_json(
            ["destinations", "get", "--id", "d1"],
            [{"destinationId": "d1", "name": "BQ"}],
        )
        self.assertEqual(rc, 0)

    def test_create(self):
        rc, data = self._run_json(
            ["destinations", "create", "--name", "BQ", "--workspace-id", "ws-1",
             "--type", "bigquery", "--config", '{"project":"p1"}'],
            [{"destinationId": "d-new"}],
        )
        self.assertEqual(rc, 0)

    def test_update(self):
        rc, _ = self._run_json(
            ["destinations", "update", "--id", "d1", "--data", '{"name":"Updated"}'],
            [{"destinationId": "d1"}],
        )
        self.assertEqual(rc, 0)

    def test_replace(self):
        rc, _ = self._run_json(
            ["destinations", "replace", "--id", "d1", "--name", "Replaced",
             "--workspace-id", "ws-1", "--type", "bigquery", "--config", '{}'],
            [{"destinationId": "d1"}],
        )
        self.assertEqual(rc, 0)

    def test_delete(self):
        rc, _, _ = self._run(["destinations", "delete", "--id", "d1"], [{}])
        self.assertEqual(rc, 0)


class TestCliConnections(_CliTestBase):
    def test_list(self):
        rc, data = self._run_json(
            ["connections", "list"],
            [{"data": [{"connectionId": "c1"}]}],
        )
        self.assertEqual(rc, 0)

    def test_get(self):
        rc, data = self._run_json(
            ["connections", "get", "--id", "c1"],
            [{"connectionId": "c1", "status": "active"}],
        )
        self.assertEqual(rc, 0)
        self.assertEqual(data["status"], "active")

    def test_create(self):
        rc, data = self._run_json(
            ["connections", "create", "--source-id", "s1", "--destination-id", "d1",
             "--name", "My Conn"],
            [{"connectionId": "c-new"}],
        )
        self.assertEqual(rc, 0)

    def test_update(self):
        rc, _ = self._run_json(
            ["connections", "update", "--id", "c1", "--data", '{"status":"inactive"}'],
            [{"connectionId": "c1", "status": "inactive"}],
        )
        self.assertEqual(rc, 0)

    def test_delete(self):
        rc, _, _ = self._run(["connections", "delete", "--id", "c1"], [{}])
        self.assertEqual(rc, 0)


class TestCliJobs(_CliTestBase):
    def test_list(self):
        rc, data = self._run_json(
            ["jobs", "list", "--connection-id", "c1"],
            [{"data": [{"jobId": 1, "status": "succeeded"}]}],
        )
        self.assertEqual(rc, 0)

    def test_get(self):
        rc, data = self._run_json(
            ["jobs", "get", "--id", "1"],
            [{"jobId": 1, "status": "succeeded"}],
        )
        self.assertEqual(rc, 0)

    def test_trigger(self):
        rc, data = self._run_json(
            ["jobs", "trigger", "--connection-id", "c1", "--type", "sync"],
            [{"jobId": 99, "status": "pending"}],
        )
        self.assertEqual(rc, 0)
        self.assertEqual(data["jobId"], 99)

    def test_cancel(self):
        rc, _, _ = self._run(["jobs", "cancel", "--id", "1"], [{}])
        self.assertEqual(rc, 0)


class TestCliStreams(_CliTestBase):
    def test_get(self):
        rc, data = self._run_json(
            ["streams", "get", "--id", "c1"],
            [{"streams": [{"name": "users", "syncMode": "full_refresh"}]}],
        )
        self.assertEqual(rc, 0)
        self.assertEqual(data["streams"][0]["name"], "users")


class TestCliPermissions(_CliTestBase):
    def test_list(self):
        rc, data = self._run_json(
            ["permissions", "list"],
            [{"data": [{"permissionId": "p1"}]}],
        )
        self.assertEqual(rc, 0)

    def test_get(self):
        rc, data = self._run_json(
            ["permissions", "get", "--id", "p1"],
            [{"permissionId": "p1", "permissionType": "organization_admin"}],
        )
        self.assertEqual(rc, 0)

    def test_create(self):
        rc, _ = self._run_json(
            ["permissions", "create", "--permission-type", "workspace_admin",
             "--user-id", "u1", "--workspace-id", "ws-1"],
            [{"permissionId": "p-new"}],
        )
        self.assertEqual(rc, 0)

    def test_delete(self):
        rc, _, _ = self._run(["permissions", "delete", "--id", "p1"], [{}])
        self.assertEqual(rc, 0)


class TestCliOrganizations(_CliTestBase):
    def test_list(self):
        rc, data = self._run_json(
            ["organizations", "list"],
            [{"data": [{"organizationId": "org-1"}]}],
        )
        self.assertEqual(rc, 0)


class TestCliUsers(_CliTestBase):
    def test_list(self):
        rc, data = self._run_json(
            ["users", "list", "--organization-id", "org-1"],
            [{"data": [{"userId": "u1", "name": "Alice"}]}],
        )
        self.assertEqual(rc, 0)


class TestCliTags(_CliTestBase):
    def test_list(self):
        rc, data = self._run_json(
            ["tags", "list", "--workspace-id", "ws-1"],
            [{"data": [{"tagId": "t1", "name": "production"}]}],
        )
        self.assertEqual(rc, 0)

    def test_create(self):
        rc, data = self._run_json(
            ["tags", "create", "--name", "staging", "--workspace-id", "ws-1"],
            [{"tagId": "t-new", "name": "staging"}],
        )
        self.assertEqual(rc, 0)

    def test_delete(self):
        rc, _, _ = self._run(["tags", "delete", "--id", "t1"], [{}])
        self.assertEqual(rc, 0)


class TestCliApplications(_CliTestBase):
    def test_list(self):
        rc, data = self._run_json(
            ["applications", "list"],
            [{"data": [{"applicationId": "app-1"}]}],
        )
        self.assertEqual(rc, 0)

    def test_create(self):
        rc, data = self._run_json(
            ["applications", "create", "--name", "CI Bot"],
            [{"applicationId": "app-new", "clientId": "cid", "clientSecret": "csec"}],
        )
        self.assertEqual(rc, 0)

    def test_delete(self):
        rc, _, _ = self._run(["applications", "delete", "--id", "app-1"], [{}])
        self.assertEqual(rc, 0)

    def test_token(self):
        rc, data = self._run_json(
            ["applications", "token", "--id", "app-1"],
            [{"access_token": "tok123", "expires_in": 3600}],
        )
        self.assertEqual(rc, 0)


class TestCliSourceDefinitions(_CliTestBase):
    def test_list(self):
        rc, data = self._run_json(
            ["source_definitions", "list"],
            [{"sourceDefinitions": [{"sourceDefinitionId": "sd-1", "name": "Postgres"}]}],
        )
        self.assertEqual(rc, 0)

    def test_get(self):
        rc, data = self._run_json(
            ["source_definitions", "get", "--id", "sd-1"],
            [{"sourceDefinitionId": "sd-1", "name": "Postgres"}],
        )
        self.assertEqual(rc, 0)

    def test_create(self):
        rc, _ = self._run_json(
            ["source_definitions", "create", "--name", "Custom",
             "--docker-repository", "airbyte/source-custom", "--docker-image-tag", "0.1.0"],
            [{"sourceDefinitionId": "sd-new"}],
        )
        self.assertEqual(rc, 0)

    def test_delete(self):
        rc, _, _ = self._run(["source_definitions", "delete", "--id", "sd-1"], [{}])
        self.assertEqual(rc, 0)


class TestCliDestinationDefinitions(_CliTestBase):
    def test_list(self):
        rc, data = self._run_json(
            ["destination_definitions", "list"],
            [{"destinationDefinitions": [{"destinationDefinitionId": "dd-1"}]}],
        )
        self.assertEqual(rc, 0)

    def test_get(self):
        rc, data = self._run_json(
            ["destination_definitions", "get", "--id", "dd-1"],
            [{"destinationDefinitionId": "dd-1", "name": "BigQuery"}],
        )
        self.assertEqual(rc, 0)

    def test_create(self):
        rc, _ = self._run_json(
            ["destination_definitions", "create", "--name", "Custom Dest",
             "--docker-repository", "airbyte/destination-custom", "--docker-image-tag", "0.1.0"],
            [{"destinationDefinitionId": "dd-new"}],
        )
        self.assertEqual(rc, 0)

    def test_delete(self):
        rc, _, _ = self._run(["destination_definitions", "delete", "--id", "dd-1"], [{}])
        self.assertEqual(rc, 0)


class TestCliConfigCommand(_CliTestBase):
    def test_config_show(self):
        rc, out, _ = self._run(["config", "show"], [])
        self.assertEqual(rc, 0)
        data = json.loads(out)
        self.assertEqual(data["base_url"], "http://localhost:8000/api/public/v1")
        self.assertEqual(data["username"], "airbyte")

    def test_config_set_base_url(self):
        rc, out, _ = self._run(
            ["config", "set", "--base-url", "http://new-host:8000/api/public/v1"], []
        )
        self.assertEqual(rc, 0)
        # Verify it was saved
        cfg = json.loads((Path(self.config_dir) / "config.json").read_text())
        self.assertEqual(cfg["base_url"], "http://new-host:8000/api/public/v1")


class TestCliFormatFlag(_CliTestBase):
    def test_table_format(self):
        rc, out, _ = self._run(
            ["--format", "table", "workspaces", "list"],
            [{"data": [{"workspaceId": "ws-1", "name": "Default"}]}],
        )
        self.assertEqual(rc, 0)
        self.assertIn("ws-1", out)
        self.assertIn("Default", out)

    def test_compact_format(self):
        rc, out, _ = self._run(
            ["--format", "compact", "workspaces", "list"],
            [{"data": [{"workspaceId": "ws-1", "name": "Default"}]}],
        )
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
