"""Output formatters — JSON (default), table, compact."""

from __future__ import annotations

import json
import sys
from typing import Any


def format_json(data: Any) -> str:
    """Serialize data to indented JSON."""
    return json.dumps(data, indent=2, default=str)


def format_table(data: list[dict[str, Any]], columns: list[str] | None = None) -> str:
    """Format a list of dicts as an aligned text table."""
    if not data:
        return "(no results)"

    cols = columns or list(data[0].keys())
    # Compute column widths
    widths: dict[str, int] = {col: len(col) for col in cols}
    for row in data:
        for col in cols:
            val = str(row.get(col, ""))
            widths[col] = max(widths[col], len(val))

    # Build header
    header = "  ".join(col.upper().ljust(widths[col]) for col in cols)
    separator = "  ".join("-" * widths[col] for col in cols)
    rows = [
        "  ".join(str(row.get(col, "")).ljust(widths[col]) for col in cols)
        for row in data
    ]
    return "\n".join([header, separator] + rows)


def format_compact(data: list[dict[str, Any]], columns: list[str] | None = None) -> str:
    """Format a list of dicts as one line per record, pipe-separated."""
    if not data:
        return ""

    cols = columns or list(data[0].keys())
    lines = []
    for row in data:
        parts = [str(row.get(col, "")) for col in cols]
        lines.append("|".join(parts))
    return "\n".join(lines)


def output(
    data: Any,
    fmt: str = "json",
    columns: list[str] | None = None,
) -> None:
    """Print formatted data to stdout."""
    if fmt == "table":
        if isinstance(data, list):
            print(format_table(data, columns))
        else:
            print(format_json(data))
    elif fmt == "compact":
        if isinstance(data, list):
            print(format_compact(data, columns))
        else:
            print(format_json(data))
    else:
        print(format_json(data))


def error(error_type: str, message: str, status: int = 0) -> None:
    """Print a JSON error object to stderr."""
    payload: dict[str, Any] = {"error": error_type, "message": message}
    if status:
        payload["status"] = status
    print(json.dumps(payload), file=sys.stderr)
