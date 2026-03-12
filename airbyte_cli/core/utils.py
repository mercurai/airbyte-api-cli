"""Shared utilities for the Airbyte CLI."""

from __future__ import annotations

import json
from pathlib import Path


def resolve_json_arg(value: str) -> dict:
    """Parse JSON from an inline string or a @filepath reference.

    Args:
        value: Either a JSON string or a path prefixed with '@'.

    Returns:
        Parsed dict.

    Raises:
        ValueError: If the value cannot be parsed as JSON.
        FileNotFoundError: If the @file path does not exist.
    """
    if value.startswith("@"):
        path = Path(value[1:])
        try:
            text = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            raise FileNotFoundError(f"Config file not found: {path}")
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in {path}: {exc}") from exc

    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON: {exc}") from exc


def strip_none(d: dict) -> dict:
    """Return a copy of dict with None values removed."""
    return {k: v for k, v in d.items() if v is not None}


def paginate_all(list_fn, limit=100, **kwargs):
    """Auto-paginate through all pages of a list endpoint.

    Args:
        list_fn: A callable that accepts limit and offset kwargs and returns an ApiResponse.
        limit: Page size per request.
        **kwargs: Additional kwargs passed to list_fn.

    Returns:
        Combined list of all records across all pages.
    """
    all_data = []
    offset = 0
    while True:
        result = list_fn(limit=limit, offset=offset, **kwargs)
        all_data.extend(result.data)
        if len(result.data) < limit:
            break
        offset += limit
    return all_data
