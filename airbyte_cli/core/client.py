"""HTTP client wrapping urllib.request with retry, auth injection, and error handling."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from airbyte_cli.core.exceptions import ApiError, AuthError, NetworkError

_VERSION = "0.1.0"
_USER_AGENT = f"airbyte-cli/{_VERSION}"
_RETRY_DELAYS = [1, 2, 4]


class HttpClient:
    """Thin HTTP client for the Airbyte public API."""

    def __init__(self, base_url: str, token: str, timeout: int = 30) -> None:
        self.base_url = base_url.rstrip("/")
        # token may be a raw token (Bearer assumed) or a full header value
        if token.startswith(("Bearer ", "Basic ")):
            self._auth_header = token
        else:
            self._auth_header = f"Bearer {token}"
        self.timeout = timeout

    def request(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make an HTTP request. Returns parsed JSON response body.

        Retries on 5xx and network errors (3 attempts with backoff 1s/2s/4s).
        Raises typed exceptions for errors.
        """
        url = self._build_url(path, params)
        data = json.dumps(body).encode("utf-8") if body is not None else None
        headers = self._build_headers(data is not None)

        last_exc: Exception | None = None
        attempts = len(_RETRY_DELAYS) + 1

        for attempt in range(attempts):
            try:
                return self._do_request(method, url, data, headers)
            except (ApiError, AuthError) as exc:
                # Client errors and auth errors — no retry
                raise
            except NetworkError as exc:
                last_exc = exc
                if attempt < len(_RETRY_DELAYS):
                    time.sleep(_RETRY_DELAYS[attempt])
            except _RetryableError as exc:
                last_exc = exc.cause
                if attempt < len(_RETRY_DELAYS):
                    time.sleep(_RETRY_DELAYS[attempt])

        if last_exc is not None:
            raise last_exc
        raise NetworkError("Request failed after retries")  # pragma: no cover

    def _do_request(
        self,
        method: str,
        url: str,
        data: bytes | None,
        headers: dict[str, str],
    ) -> dict[str, Any]:
        """Execute a single HTTP request attempt."""
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read().decode("utf-8")
                if not raw:
                    return {}
                try:
                    return json.loads(raw)
                except json.JSONDecodeError:
                    return {"message": raw.strip()}
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8") if exc.fp else ""
            try:
                body = json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                body = {"detail": raw}

            if exc.code == 401:
                raise AuthError(body.get("message", "Authentication failed"))
            if exc.code >= 500:
                raise _RetryableError(
                    ApiError(
                        body.get("message", f"Server error {exc.code}"),
                        status_code=exc.code,
                        response_body=body,
                    )
                )
            raise ApiError(
                body.get("message", f"API error {exc.code}"),
                status_code=exc.code,
                response_body=body,
            )
        except urllib.error.URLError as exc:
            raise NetworkError(str(exc.reason))
        except TimeoutError as exc:
            raise NetworkError("Request timed out")

    def _build_url(self, path: str, params: dict[str, Any] | None) -> str:
        url = self.base_url + "/" + path.lstrip("/")
        if params:
            filtered = {k: v for k, v in params.items() if v is not None}
            if filtered:
                url = url + "?" + urllib.parse.urlencode(filtered)
        return url

    def _build_headers(self, has_body: bool) -> dict[str, str]:
        headers: dict[str, str] = {
            "Authorization": self._auth_header,
            "Accept": "application/json",
            "User-Agent": _USER_AGENT,
        }
        if has_body:
            headers["Content-Type"] = "application/json"
        return headers


class _RetryableError(Exception):
    """Internal wrapper to signal a retryable server error."""

    def __init__(self, cause: Exception) -> None:
        self.cause = cause
