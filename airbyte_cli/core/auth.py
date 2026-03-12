"""Token acquisition, caching, and refresh for the Airbyte API."""

from __future__ import annotations

import base64
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import TYPE_CHECKING

from airbyte_cli.core.exceptions import AuthError, ConfigError

if TYPE_CHECKING:
    from airbyte_cli.core.config import Config

_TOKEN_FILE = "token.json"
_EXPIRY_BUFFER_SECONDS = 60  # refresh if less than 60s remaining


class TokenManager:
    """Manages Airbyte API token acquisition, caching, and refresh."""

    def __init__(self, config: "Config", config_dir: Path | None = None) -> None:
        from airbyte_cli.core.config import DEFAULT_CONFIG_DIR
        self._config = config
        self._config_dir = config_dir or DEFAULT_CONFIG_DIR
        self._token_path = self._config_dir / _TOKEN_FILE

    def get_token(self) -> str:
        """Return a valid auth header value, from cache or by acquiring a new one.

        Priority: direct token > basic auth > cached OAuth > client_credentials flow.
        """
        # Direct token takes priority — skip everything else
        if self._config.token:
            return self._config.token

        # Basic auth — return full header value
        if self._config.username and self._config.password:
            creds = base64.b64encode(
                f"{self._config.username}:{self._config.password}".encode()
            ).decode()
            return f"Basic {creds}"

        cached = self._load_cached_token()
        if cached:
            return cached

        return self._acquire_token()

    def refresh(self) -> str:
        """Force token refresh regardless of cache state."""
        if self._config.token:
            return self._config.token
        if self._config.username and self._config.password:
            return self.get_token()
        return self._acquire_token()

    def _load_cached_token(self) -> str | None:
        """Return cached token if it exists and has not expired."""
        if not self._token_path.exists():
            return None
        try:
            data = json.loads(self._token_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

        expires_at = data.get("expires_at", 0)
        if time.time() + _EXPIRY_BUFFER_SECONDS < expires_at:
            return data.get("access_token")
        return None

    def _acquire_token(self) -> str:
        """POST to /applications/token to get a new access token."""
        if not self._config.client_id or not self._config.client_secret:
            raise ConfigError(
                "No token or client credentials configured. "
                "Set AIRBYTE_TOKEN, AIRBYTE_USERNAME + AIRBYTE_PASSWORD, "
                "or AIRBYTE_CLIENT_ID + AIRBYTE_CLIENT_SECRET."
            )
        if not self._config.base_url:
            raise ConfigError("base_url is not configured.")

        token_url = self._config.base_url.rstrip("/") + "/applications/token"
        payload = json.dumps({
            "client_id": self._config.client_id,
            "client_secret": self._config.client_secret,
            "grant_type": "client_credentials",
        }).encode("utf-8")
        req = urllib.request.Request(
            token_url,
            data=payload,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self._config.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise AuthError(f"Token acquisition failed (HTTP {exc.code})")
        except urllib.error.URLError as exc:
            raise AuthError(f"Token acquisition network error: {exc.reason}")

        access_token = data.get("access_token")
        expires_in = data.get("expires_in", 3600)
        if not access_token:
            raise AuthError("Token endpoint returned no access_token")

        self._cache_token(access_token, int(expires_in))
        return access_token

    def _cache_token(self, access_token: str, expires_in: int) -> None:
        """Write token to disk with expiry timestamp."""
        self._config_dir.mkdir(parents=True, exist_ok=True)
        cache = {
            "access_token": access_token,
            "expires_at": time.time() + expires_in,
        }
        self._token_path.write_text(json.dumps(cache), encoding="utf-8")
