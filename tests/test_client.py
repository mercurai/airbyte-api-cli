"""Tests for the HTTP client."""

import io
import json
import unittest
import urllib.error
import urllib.request
from http.client import HTTPMessage
from unittest.mock import MagicMock, patch, call

from airbyte_api_cli.core.client import HttpClient
from airbyte_api_cli.core.exceptions import ApiError, AuthError, NetworkError


def _make_response(body: dict, status: int = 200) -> MagicMock:
    """Build a mock urlopen response."""
    raw = json.dumps(body).encode("utf-8")
    resp = MagicMock()
    resp.read.return_value = raw
    resp.status = status
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return resp


def _make_http_error(status: int, body: dict) -> urllib.error.HTTPError:
    raw = json.dumps(body).encode("utf-8")
    fp = io.BytesIO(raw)
    fp.read = lambda: raw
    return urllib.error.HTTPError(
        url="http://test.example.com",
        code=status,
        msg="error",
        hdrs=HTTPMessage(),
        fp=fp,
    )


class TestHttpClientRequestBuilding(unittest.TestCase):
    def setUp(self):
        self.client = HttpClient(
            base_url="https://api.example.com/v1",
            token="test_token",
            timeout=30,
        )

    @patch("urllib.request.urlopen")
    def test_get_request_builds_correct_url(self, mock_urlopen):
        mock_urlopen.return_value = _make_response({"data": []})
        self.client.request("GET", "/sources")
        req = mock_urlopen.call_args[0][0]
        self.assertEqual(req.full_url, "https://api.example.com/v1/sources")
        self.assertEqual(req.method, "GET")

    @patch("urllib.request.urlopen")
    def test_get_request_with_params(self, mock_urlopen):
        mock_urlopen.return_value = _make_response({"data": []})
        self.client.request("GET", "/sources", params={"limit": 10, "offset": 0})
        req = mock_urlopen.call_args[0][0]
        self.assertIn("limit=10", req.full_url)
        self.assertIn("offset=0", req.full_url)

    @patch("urllib.request.urlopen")
    def test_get_request_skips_none_params(self, mock_urlopen):
        mock_urlopen.return_value = _make_response({"data": []})
        self.client.request("GET", "/sources", params={"limit": 10, "workspace_id": None})
        req = mock_urlopen.call_args[0][0]
        self.assertNotIn("workspace_id", req.full_url)

    @patch("urllib.request.urlopen")
    def test_post_request_sends_json_body(self, mock_urlopen):
        mock_urlopen.return_value = _make_response({"sourceId": "s1"})
        body = {"name": "test", "sourceType": "postgres"}
        self.client.request("POST", "/sources", body=body)
        req = mock_urlopen.call_args[0][0]
        self.assertEqual(req.get_header("Content-type"), "application/json")
        sent_body = json.loads(req.data.decode("utf-8"))
        self.assertEqual(sent_body["name"], "test")

    @patch("urllib.request.urlopen")
    def test_auth_header_injected(self, mock_urlopen):
        mock_urlopen.return_value = _make_response({})
        self.client.request("GET", "/sources")
        req = mock_urlopen.call_args[0][0]
        self.assertEqual(req.get_header("Authorization"), "Bearer test_token")

    @patch("urllib.request.urlopen")
    def test_user_agent_set(self, mock_urlopen):
        mock_urlopen.return_value = _make_response({})
        self.client.request("GET", "/sources")
        req = mock_urlopen.call_args[0][0]
        self.assertIn("airbyte-api-cli/", req.get_header("User-agent"))

    @patch("urllib.request.urlopen")
    def test_response_json_parsed(self, mock_urlopen):
        expected = {"sourceId": "s_abc", "name": "my-source"}
        mock_urlopen.return_value = _make_response(expected)
        result = self.client.request("GET", "/sources/s_abc")
        self.assertEqual(result["sourceId"], "s_abc")
        self.assertEqual(result["name"], "my-source")

    @patch("urllib.request.urlopen")
    def test_empty_response_returns_empty_dict(self, mock_urlopen):
        resp = MagicMock()
        resp.read.return_value = b""
        resp.__enter__ = lambda s: s
        resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = resp
        result = self.client.request("DELETE", "/sources/s1")
        self.assertEqual(result, {})

    @patch("urllib.request.urlopen")
    def test_base_url_trailing_slash_normalised(self, mock_urlopen):
        client = HttpClient(base_url="https://api.example.com/v1/", token="tok")
        mock_urlopen.return_value = _make_response({})
        client.request("GET", "/sources")
        req = mock_urlopen.call_args[0][0]
        self.assertNotIn("//sources", req.full_url)


class TestHttpClientErrors(unittest.TestCase):
    def setUp(self):
        self.client = HttpClient(
            base_url="https://api.example.com/v1",
            token="test_token",
        )

    @patch("urllib.request.urlopen")
    def test_api_error_raised_on_4xx(self, mock_urlopen):
        mock_urlopen.side_effect = _make_http_error(404, {"message": "not found"})
        with self.assertRaises(ApiError) as ctx:
            self.client.request("GET", "/sources/bad_id")
        self.assertEqual(ctx.exception.status_code, 404)

    @patch("urllib.request.urlopen")
    def test_auth_error_raised_on_401(self, mock_urlopen):
        mock_urlopen.side_effect = _make_http_error(401, {"message": "Unauthorized"})
        with self.assertRaises(AuthError):
            self.client.request("GET", "/sources")

    @patch("urllib.request.urlopen")
    def test_network_error_on_url_error(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")
        with self.assertRaises(NetworkError):
            self.client.request("GET", "/sources")

    @patch("urllib.request.urlopen")
    def test_no_retry_on_client_error(self, mock_urlopen):
        mock_urlopen.side_effect = _make_http_error(400, {"message": "bad request"})
        with self.assertRaises(ApiError):
            self.client.request("GET", "/sources")
        self.assertEqual(mock_urlopen.call_count, 1)

    @patch("urllib.request.urlopen")
    def test_no_retry_on_404(self, mock_urlopen):
        mock_urlopen.side_effect = _make_http_error(404, {"message": "not found"})
        with self.assertRaises(ApiError):
            self.client.request("GET", "/sources/bad")
        self.assertEqual(mock_urlopen.call_count, 1)


class TestHttpClientRetry(unittest.TestCase):
    def setUp(self):
        self.client = HttpClient(
            base_url="https://api.example.com/v1",
            token="test_token",
        )

    @patch("time.sleep")
    @patch("urllib.request.urlopen")
    def test_retry_on_server_error(self, mock_urlopen, mock_sleep):
        """Should retry 3 times total on 500 errors."""
        mock_urlopen.side_effect = _make_http_error(500, {"message": "server error"})
        with self.assertRaises(ApiError):
            self.client.request("GET", "/sources")
        self.assertEqual(mock_urlopen.call_count, 4)  # 1 + 3 retries
        self.assertEqual(mock_sleep.call_count, 3)

    @patch("time.sleep")
    @patch("urllib.request.urlopen")
    def test_retry_succeeds_on_second_attempt(self, mock_urlopen, mock_sleep):
        """Should succeed if second attempt works."""
        success_resp = _make_response({"sourceId": "s1"})
        mock_urlopen.side_effect = [
            _make_http_error(500, {"message": "transient"}),
            success_resp,
        ]
        result = self.client.request("GET", "/sources/s1")
        self.assertEqual(result["sourceId"], "s1")
        self.assertEqual(mock_urlopen.call_count, 2)
        self.assertEqual(mock_sleep.call_count, 1)

    @patch("time.sleep")
    @patch("urllib.request.urlopen")
    def test_retry_backoff_delays(self, mock_urlopen, mock_sleep):
        """Backoff should be 1s, 2s, 4s."""
        mock_urlopen.side_effect = _make_http_error(503, {"message": "unavailable"})
        with self.assertRaises(ApiError):
            self.client.request("GET", "/sources")
        sleep_calls = [c[0][0] for c in mock_sleep.call_args_list]
        self.assertEqual(sleep_calls, [1, 2, 4])

    @patch("time.sleep")
    @patch("urllib.request.urlopen")
    def test_retry_on_network_error(self, mock_urlopen, mock_sleep):
        mock_urlopen.side_effect = urllib.error.URLError("Connection reset")
        with self.assertRaises(NetworkError):
            self.client.request("GET", "/sources")
        self.assertEqual(mock_urlopen.call_count, 4)


if __name__ == "__main__":
    unittest.main()
