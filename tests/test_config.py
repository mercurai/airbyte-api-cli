"""Tests for configuration module."""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from airbyte_api_cli.core.config import Config


class TestConfigFromEnv(unittest.TestCase):
    @patch.dict(os.environ, {"AIRBYTE_BASE_URL": "https://test.example.com/api/public/v1"}, clear=False)
    def test_base_url_from_env(self):
        cfg = Config.load()
        self.assertEqual(cfg.base_url, "https://test.example.com/api/public/v1")

    @patch.dict(os.environ, {"AIRBYTE_TOKEN": "tok_123"}, clear=False)
    def test_token_from_env(self):
        cfg = Config.load()
        self.assertEqual(cfg.token, "tok_123")

    @patch.dict(os.environ, {
        "AIRBYTE_CLIENT_ID": "cid",
        "AIRBYTE_CLIENT_SECRET": "csec",
    }, clear=False)
    def test_client_credentials_from_env(self):
        cfg = Config.load()
        self.assertEqual(cfg.client_id, "cid")
        self.assertEqual(cfg.client_secret, "csec")


class TestConfigFromFile(unittest.TestCase):
    def test_load_from_config_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config_path.write_text(json.dumps({
                "base_url": "https://file.example.com/api/public/v1",
                "client_id": "file_cid",
                "client_secret": "file_csec",
                "default_workspace_id": "ws_123",
                "default_format": "table",
            }))
            cfg = Config.load(config_dir=Path(tmpdir))
            self.assertEqual(cfg.base_url, "https://file.example.com/api/public/v1")
            self.assertEqual(cfg.default_workspace_id, "ws_123")
            self.assertEqual(cfg.default_format, "table")

    def test_missing_config_file_returns_defaults(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = Config.load(config_dir=Path(tmpdir))
            self.assertEqual(cfg.base_url, "")
            self.assertEqual(cfg.default_format, "json")
            self.assertEqual(cfg.timeout, 30)

    def test_malformed_config_file_returns_defaults(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config_path.write_text("not valid json{{{")
            cfg = Config.load(config_dir=Path(tmpdir))
            self.assertEqual(cfg.base_url, "")


class TestConfigPriority(unittest.TestCase):
    @patch.dict(os.environ, {"AIRBYTE_BASE_URL": "https://env.example.com/api/public/v1"}, clear=False)
    def test_env_overrides_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config_path.write_text(json.dumps({"base_url": "https://file.example.com"}))
            cfg = Config.load(config_dir=Path(tmpdir))
            self.assertEqual(cfg.base_url, "https://env.example.com/api/public/v1")

    def test_cli_overrides_all(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = Config.load(
                config_dir=Path(tmpdir),
                cli_overrides={"base_url": "https://cli.example.com"},
            )
            self.assertEqual(cfg.base_url, "https://cli.example.com")

    @patch.dict(os.environ, {"AIRBYTE_BASE_URL": "https://env.example.com"}, clear=False)
    def test_cli_overrides_env(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = Config.load(
                config_dir=Path(tmpdir),
                cli_overrides={"base_url": "https://cli.example.com"},
            )
            self.assertEqual(cfg.base_url, "https://cli.example.com")


class TestConfigSave(unittest.TestCase):
    def test_save_creates_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = Config(
                base_url="https://save.example.com",
                client_id="save_cid",
                client_secret="save_csec",
                default_workspace_id="ws_save",
                default_format="table",
            )
            cfg.save(config_dir=Path(tmpdir))
            saved = json.loads((Path(tmpdir) / "config.json").read_text())
            self.assertEqual(saved["base_url"], "https://save.example.com")
            self.assertEqual(saved["client_id"], "save_cid")

    def test_to_dict_masks_secret(self):
        cfg = Config(client_secret="super_secret")
        d = cfg.to_dict()
        self.assertEqual(d["client_secret"], "***")

    def test_to_dict_empty_secret(self):
        cfg = Config(client_secret="")
        d = cfg.to_dict()
        self.assertEqual(d["client_secret"], "")


if __name__ == "__main__":
    unittest.main()
