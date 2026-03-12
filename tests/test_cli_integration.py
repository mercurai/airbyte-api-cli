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

from airbyte_cli.__main__ import main


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


if __name__ == "__main__":
    unittest.main()
