"""Tests for shared models."""

import unittest

from airbyte_cli.models.common import ApiResponse, ErrorDetail


class TestApiResponse(unittest.TestCase):
    def test_empty_response(self):
        resp = ApiResponse(data=[])
        self.assertEqual(resp.data, [])
        self.assertIsNone(resp.next_url)
        self.assertIsNone(resp.previous_url)

    def test_response_with_pagination(self):
        resp = ApiResponse(
            data=[{"id": "1"}],
            next_url="https://api.example.com/v1/sources?offset=20",
            previous_url=None,
        )
        self.assertEqual(len(resp.data), 1)
        self.assertIsNotNone(resp.next_url)

    def test_response_with_both_cursors(self):
        resp = ApiResponse(
            data=[{"id": "2"}],
            next_url="https://api.example.com/v1/sources?offset=40",
            previous_url="https://api.example.com/v1/sources?offset=0",
        )
        self.assertIsNotNone(resp.previous_url)
        self.assertIsNotNone(resp.next_url)


class TestErrorDetail(unittest.TestCase):
    def test_to_dict(self):
        err = ErrorDetail(error_type="not_found", message="Source not found", status=404)
        d = err.to_dict()
        self.assertEqual(d["error"], "not_found")
        self.assertEqual(d["message"], "Source not found")
        self.assertEqual(d["status"], 404)

    def test_to_dict_server_error(self):
        err = ErrorDetail(error_type="server_error", message="Internal error", status=500)
        d = err.to_dict()
        self.assertEqual(d["error"], "server_error")
        self.assertEqual(d["status"], 500)


class TestExceptions(unittest.TestCase):
    def test_api_error_has_exit_code_1(self):
        from airbyte_cli.core.exceptions import ApiError
        err = ApiError("Not found", status_code=404)
        self.assertEqual(err.exit_code, 1)
        self.assertEqual(err.status_code, 404)

    def test_auth_error_has_exit_code_2(self):
        from airbyte_cli.core.exceptions import AuthError
        err = AuthError()
        self.assertEqual(err.exit_code, 2)

    def test_config_error_has_exit_code_3(self):
        from airbyte_cli.core.exceptions import ConfigError
        err = ConfigError("Missing base_url")
        self.assertEqual(err.exit_code, 3)

    def test_network_error_has_exit_code_4(self):
        from airbyte_cli.core.exceptions import NetworkError
        err = NetworkError("Connection refused")
        self.assertEqual(err.exit_code, 4)

    def test_api_error_stores_response_body(self):
        from airbyte_cli.core.exceptions import ApiError
        body = {"detail": "resource not found"}
        err = ApiError("Not found", status_code=404, response_body=body)
        self.assertEqual(err.response_body, body)


if __name__ == "__main__":
    unittest.main()
