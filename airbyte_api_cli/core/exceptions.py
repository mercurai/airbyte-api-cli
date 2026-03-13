"""Typed exceptions for the Airbyte CLI."""


class AirbyteCliError(Exception):
    """Base exception for all CLI errors."""

    def __init__(self, message: str, exit_code: int = 1):
        super().__init__(message)
        self.exit_code = exit_code


class ApiError(AirbyteCliError):
    """API returned an error response (4xx/5xx)."""

    def __init__(self, message: str, status_code: int, response_body: dict | None = None):
        super().__init__(message, exit_code=1)
        self.status_code = status_code
        self.response_body = response_body or {}


class AuthError(AirbyteCliError):
    """Authentication failed — invalid/expired credentials."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, exit_code=2)


class ConfigError(AirbyteCliError):
    """Missing or invalid configuration."""

    def __init__(self, message: str):
        super().__init__(message, exit_code=3)


class NetworkError(AirbyteCliError):
    """Network connectivity issue — timeout, connection refused."""

    def __init__(self, message: str):
        super().__init__(message, exit_code=4)
