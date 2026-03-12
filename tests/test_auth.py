"""Tests for the auth module."""

import io
import json
import tempfile
import time
import unittest
import urllib.error
from http.client import HTTPMessage
from pathlib import Path
from unittest.mock import MagicMock, patch

from airbyte_cli.core.auth import TokenManager
from airbyte_cli.core.config import Config
from airbyte_cli.core.exceptions import AuthError, ConfigError


def _make_urlopen_response(body: dict) -> MagicMock:
    raw = json.dumps(body).encode("utf-8")
    resp = MagicMock()
    resp.read.return_value = raw
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return resp


def _make_http_error(status: int, body: dict) -> urllib.error.HTTPError:
    raw = json.dumps(body).encode("utf-8")
    fp = io.BytesIO(raw)
    fp.read = lambda: raw
    return urllib.error.HTTPError("http://test", status, "error", HTTPMessage(), fp)


class TestTokenManagerDirectToken(unittest.TestCase):
    def test_direct_token_returned_immediately(self):
        cfg = Config(token="direct_tok_123", base_url="https://api.example.com")
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = TokenManager(cfg, config_dir=Path(tmpdir))
            self.assertEqual(mgr.get_token(), "direct_tok_123")

    def test_direct_token_skips_credentials_flow(self):
        cfg = Config(
            token="direct_tok",
            client_id="cid",
            client_secret="csec",
            base_url="https://api.example.com",
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = TokenManager(cfg, config_dir=Path(tmpdir))
            with patch("urllib.request.urlopen") as mock_urlopen:
                tok = mgr.get_token()
                mock_urlopen.assert_not_called()
                self.assertEqual(tok, "direct_tok")


class TestTokenManagerAcquire(unittest.TestCase):
    def setUp(self):
        self.cfg = Config(
            client_id="my_client_id",
            client_secret="my_client_secret",
            base_url="https://api.example.com/api/public/v1",
        )

    @patch("urllib.request.urlopen")
    def test_acquire_token_posts_client_credentials(self, mock_urlopen):
        mock_urlopen.return_value = _make_urlopen_response({
            "access_token": "new_tok",
            "expires_in": 3600,
        })
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = TokenManager(self.cfg, config_dir=Path(tmpdir))
            tok = mgr.get_token()
            self.assertEqual(tok, "new_tok")
            req = mock_urlopen.call_args[0][0]
            sent = json.loads(req.data.decode("utf-8"))
            self.assertEqual(sent["grant_type"], "client_credentials")
            self.assertEqual(sent["client_id"], "my_client_id")
            self.assertEqual(sent["client_secret"], "my_client_secret")
            self.assertIn("/applications/token", req.full_url)

    @patch("urllib.request.urlopen")
    def test_token_cached_to_file(self, mock_urlopen):
        mock_urlopen.return_value = _make_urlopen_response({
            "access_token": "cached_tok",
            "expires_in": 3600,
        })
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = TokenManager(self.cfg, config_dir=Path(tmpdir))
            mgr.get_token()
            token_file = Path(tmpdir) / "token.json"
            self.assertTrue(token_file.exists())
            data = json.loads(token_file.read_text())
            self.assertEqual(data["access_token"], "cached_tok")
            self.assertIn("expires_at", data)
            self.assertGreater(data["expires_at"], time.time())

    @patch("urllib.request.urlopen")
    def test_cached_token_loaded_when_valid(self, mock_urlopen):
        with tempfile.TemporaryDirectory() as tmpdir:
            token_file = Path(tmpdir) / "token.json"
            token_file.write_text(json.dumps({
                "access_token": "valid_cached_tok",
                "expires_at": time.time() + 7200,
            }))
            mgr = TokenManager(self.cfg, config_dir=Path(tmpdir))
            tok = mgr.get_token()
            self.assertEqual(tok, "valid_cached_tok")
            mock_urlopen.assert_not_called()

    @patch("urllib.request.urlopen")
    def test_expired_token_triggers_refresh(self, mock_urlopen):
        mock_urlopen.return_value = _make_urlopen_response({
            "access_token": "fresh_tok",
            "expires_in": 3600,
        })
        with tempfile.TemporaryDirectory() as tmpdir:
            token_file = Path(tmpdir) / "token.json"
            token_file.write_text(json.dumps({
                "access_token": "expired_tok",
                "expires_at": time.time() - 100,  # already expired
            }))
            mgr = TokenManager(self.cfg, config_dir=Path(tmpdir))
            tok = mgr.get_token()
            self.assertEqual(tok, "fresh_tok")
            mock_urlopen.assert_called_once()

    @patch("urllib.request.urlopen")
    def test_auth_error_on_invalid_credentials(self, mock_urlopen):
        mock_urlopen.side_effect = _make_http_error(401, {"message": "Unauthorized"})
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = TokenManager(self.cfg, config_dir=Path(tmpdir))
            with self.assertRaises(AuthError):
                mgr.get_token()

    def test_missing_credentials_raises_config_error(self):
        cfg = Config(base_url="https://api.example.com")
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = TokenManager(cfg, config_dir=Path(tmpdir))
            with self.assertRaises(ConfigError):
                mgr.get_token()

    def test_missing_base_url_raises_config_error(self):
        cfg = Config(client_id="cid", client_secret="csec")
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = TokenManager(cfg, config_dir=Path(tmpdir))
            with self.assertRaises(ConfigError):
                mgr.get_token()

    @patch("urllib.request.urlopen")
    def test_token_expiry_buffer_applied(self, mock_urlopen):
        """Token within 60s of expiry should not be returned from cache."""
        mock_urlopen.return_value = _make_urlopen_response({
            "access_token": "refreshed_tok",
            "expires_in": 3600,
        })
        with tempfile.TemporaryDirectory() as tmpdir:
            token_file = Path(tmpdir) / "token.json"
            token_file.write_text(json.dumps({
                "access_token": "almost_expired_tok",
                "expires_at": time.time() + 30,  # expires in 30s < 60s buffer
            }))
            mgr = TokenManager(self.cfg, config_dir=Path(tmpdir))
            tok = mgr.get_token()
            self.assertEqual(tok, "refreshed_tok")

    @patch("urllib.request.urlopen")
    def test_refresh_forces_new_token(self, mock_urlopen):
        """refresh() should bypass cache."""
        mock_urlopen.return_value = _make_urlopen_response({
            "access_token": "forced_tok",
            "expires_in": 3600,
        })
        with tempfile.TemporaryDirectory() as tmpdir:
            token_file = Path(tmpdir) / "token.json"
            token_file.write_text(json.dumps({
                "access_token": "old_tok",
                "expires_at": time.time() + 7200,
            }))
            mgr = TokenManager(self.cfg, config_dir=Path(tmpdir))
            tok = mgr.refresh()
            self.assertEqual(tok, "forced_tok")


if __name__ == "__main__":
    unittest.main()
