"""Tests for the jobs plugin."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from airbyte_cli.core.client import HttpClient
from airbyte_cli.models.common import ApiResponse
from airbyte_cli.plugins.jobs.api import JobsApi
from airbyte_cli.plugins.jobs.models import Job


class TestJobModel(unittest.TestCase):
    def test_from_dict_full(self):
        data = {
            "jobId": 42,
            "status": "succeeded",
            "jobType": "sync",
            "startTime": "2024-01-01T00:00:00Z",
            "connectionId": "conn_1",
            "lastUpdatedAt": "2024-01-01T01:00:00Z",
            "duration": "PT1H",
            "bytesSynced": 1024,
            "rowsSynced": 100,
        }
        job = Job.from_dict(data)
        self.assertEqual(job.job_id, 42)
        self.assertEqual(job.status, "succeeded")
        self.assertEqual(job.job_type, "sync")
        self.assertEqual(job.connection_id, "conn_1")
        self.assertEqual(job.bytes_synced, 1024)
        self.assertEqual(job.rows_synced, 100)

    def test_from_dict_minimal(self):
        job = Job.from_dict({"jobId": 1})
        self.assertEqual(job.job_id, 1)
        self.assertEqual(job.status, "")
        self.assertEqual(job.bytes_synced, 0)

    def test_to_dict_roundtrip(self):
        data = {
            "jobId": 7,
            "status": "failed",
            "jobType": "reset",
            "startTime": "2024-06-01T00:00:00Z",
            "connectionId": "conn_2",
            "lastUpdatedAt": "2024-06-01T00:10:00Z",
            "duration": "PT10M",
            "bytesSynced": 0,
            "rowsSynced": 0,
        }
        job = Job.from_dict(data)
        d = job.to_dict()
        self.assertEqual(d["jobId"], 7)
        self.assertEqual(d["status"], "failed")
        self.assertEqual(d["jobType"], "reset")
        self.assertEqual(d["connectionId"], "conn_2")


class TestJobsApi(unittest.TestCase):
    def setUp(self):
        self.client = MagicMock(spec=HttpClient)
        self.api = JobsApi(self.client)

    def test_list_calls_get_jobs(self):
        self.client.request.return_value = {"data": [{"jobId": 1}]}
        result = self.api.list(limit=10, offset=0)
        self.client.request.assert_called_once_with("GET", "jobs", params={"limit": 10, "offset": 0})
        self.assertIsInstance(result, ApiResponse)
        self.assertEqual(len(result.data), 1)

    def test_list_with_connection_filter(self):
        self.client.request.return_value = {"data": []}
        self.api.list(connectionId="conn_1", status="running")
        self.client.request.assert_called_once_with(
            "GET", "jobs", params={"connectionId": "conn_1", "status": "running"}
        )

    def test_list_with_job_type_filter(self):
        self.client.request.return_value = {"data": []}
        self.api.list(jobType="sync")
        self.client.request.assert_called_once_with("GET", "jobs", params={"jobType": "sync"})

    def test_list_returns_pagination_urls(self):
        self.client.request.return_value = {
            "data": [],
            "next": "https://api/jobs?offset=20",
            "previous": None,
        }
        result = self.api.list()
        self.assertEqual(result.next_url, "https://api/jobs?offset=20")
        self.assertIsNone(result.previous_url)

    def test_trigger_posts_to_jobs(self):
        self.client.request.return_value = {"jobId": 99, "status": "pending"}
        result = self.api.trigger("conn_1", "sync")
        self.client.request.assert_called_once_with(
            "POST",
            "jobs",
            body={"connectionId": "conn_1", "jobType": "sync"},
        )
        self.assertEqual(result["jobId"], 99)

    def test_trigger_reset_job(self):
        self.client.request.return_value = {"jobId": 100, "status": "pending"}
        self.api.trigger("conn_1", "reset")
        call_body = self.client.request.call_args[1]["body"]
        self.assertEqual(call_body["jobType"], "reset")

    def test_get_calls_correct_endpoint(self):
        self.client.request.return_value = {"jobId": 42, "status": "succeeded"}
        result = self.api.get("42")
        self.client.request.assert_called_once_with("GET", "jobs/42")
        self.assertEqual(result["jobId"], 42)

    def test_cancel_calls_delete_endpoint(self):
        self.client.request.return_value = {}
        self.api.cancel("42")
        self.client.request.assert_called_once_with("DELETE", "jobs/42")

    def test_list_empty_data_key(self):
        self.client.request.return_value = {}
        result = self.api.list()
        self.assertEqual(result.data, [])
        self.assertIsNone(result.next_url)


class TestJobsCommands(unittest.TestCase):
    def _make_context(self):
        client = MagicMock(spec=HttpClient)
        client.request.return_value = {}
        return {"client": client, "format": "json"}

    def test_list_command_dispatches(self):
        ctx = self._make_context()
        ctx["client"].request.return_value = {"data": []}
        import argparse
        from airbyte_cli.plugins.jobs.commands import _handle

        args = argparse.Namespace(
            action="list",
            connection_id=None,
            workspace_id=None,
            status=None,
            job_type=None,
            order_by=None,
            limit=20,
            offset=0,
        )
        result = _handle(args, ctx)
        self.assertEqual(result, 0)

    def test_list_with_filters(self):
        ctx = self._make_context()
        ctx["client"].request.return_value = {"data": []}
        import argparse
        from airbyte_cli.plugins.jobs.commands import _handle

        args = argparse.Namespace(
            action="list",
            connection_id="conn_1",
            workspace_id=None,
            status="running",
            job_type="sync",
            order_by="createdAt",
            limit=10,
            offset=5,
        )
        _handle(args, ctx)
        call_params = ctx["client"].request.call_args[1]["params"]
        self.assertEqual(call_params["connectionId"], "conn_1")
        self.assertEqual(call_params["status"], "running")
        self.assertEqual(call_params["jobType"], "sync")
        self.assertEqual(call_params["orderBy"], "createdAt")

    def test_trigger_command_dispatches(self):
        ctx = self._make_context()
        ctx["client"].request.return_value = {"jobId": 1}
        import argparse
        from airbyte_cli.plugins.jobs.commands import _handle

        args = argparse.Namespace(
            action="trigger",
            connection_id="conn_1",
            job_type="sync",
        )
        result = _handle(args, ctx)
        self.assertEqual(result, 0)
        call_body = ctx["client"].request.call_args[1]["body"]
        self.assertEqual(call_body["connectionId"], "conn_1")
        self.assertEqual(call_body["jobType"], "sync")

    def test_get_command_dispatches(self):
        ctx = self._make_context()
        ctx["client"].request.return_value = {"jobId": 5}
        import argparse
        from airbyte_cli.plugins.jobs.commands import _handle

        args = argparse.Namespace(action="get", job_id="5")
        result = _handle(args, ctx)
        self.assertEqual(result, 0)

    def test_cancel_command_dispatches(self):
        ctx = self._make_context()
        ctx["client"].request.return_value = {}
        import argparse
        from airbyte_cli.plugins.jobs.commands import _handle

        args = argparse.Namespace(action="cancel", job_id="5")
        result = _handle(args, ctx)
        self.assertEqual(result, 0)
        ctx["client"].request.assert_called_once_with("DELETE", "jobs/5")

    def test_unknown_action_returns_error(self):
        import argparse
        from airbyte_cli.plugins.jobs.commands import _handle

        ctx = self._make_context()
        args = argparse.Namespace(action=None)
        result = _handle(args, ctx)
        self.assertEqual(result, 1)

    def test_list_none_filters_stripped(self):
        ctx = self._make_context()
        ctx["client"].request.return_value = {"data": []}
        import argparse
        from airbyte_cli.plugins.jobs.commands import _handle

        args = argparse.Namespace(
            action="list",
            connection_id=None,
            workspace_id=None,
            status=None,
            job_type=None,
            order_by=None,
            limit=20,
            offset=0,
        )
        _handle(args, ctx)
        call_params = ctx["client"].request.call_args[1]["params"]
        self.assertNotIn("connectionId", call_params)
        self.assertNotIn("status", call_params)


if __name__ == "__main__":
    unittest.main()
