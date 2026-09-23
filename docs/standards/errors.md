---
owner: data-pipeline team
last-reviewed: 2026-09-23
stability: draft
status: active
---

# Error Standards — airbyte-api-cli

> Inherits the workspace base: [../../../../docs/standards/errors.md](../../../../docs/standards/errors.md)
> (GitHub: https://github.com/mercurai/data-pipeline/blob/main/docs/standards/errors.md).
> This document records only this repo's layers, observed/standard rows and drift backlog.
>
> Shares the [observability spine](./_observability.md) with [logging.md](./logging.md).

## 1. Taxonomy (the shared contract)

| class                                        | meaning                         | recoverable    | example in this repo                          |
| -------------------------------------------- | ------------------------------- | -------------- | --------------------------------------------- |
| **domain**                                   | expected, business-rule failure | yes            | a 4xx `ApiError` (bad resource id, validation |
| reject) — `core/client.py:109-113`           |
| **infrastructure**                           | I/O, network, dependency        | retryable      | a 5xx wrapped in `_RetryableError`            |
| (`:102-107`), or `NetworkError` (`:114-117`) |
| **programmer**                               | a bug / invariant violation     | no — fail fast | `ConfigError` — missing/invalid               |
| config (`core/exceptions.py:28-32`)          |

| module            | type / constructor                          | nodes                          |
| ----------------- | ------------------------------------------- | ------------------------------ |
| `core.exceptions` | `AirbyteCliError(Exception)` (base, `:4-9`) | carries `exit_code`            |
| `core.exceptions` | `ApiError(AirbyteCliError)` (`:12-18`)      | `status_code`, `response_body` |
| `core.exceptions` | `AuthError(AirbyteCliError)` (`:21-25`)     | exit code 2                    |
| `core.exceptions` | `ConfigError(AirbyteCliError)` (`:28-32`)   | exit code 3                    |
| `core.exceptions` | `NetworkError(AirbyteCliError)` (`:35-38`)  | exit code 4                    |

## 2. Typed errors at boundaries

|                                                                                                      | rule                                                                                     |
| ---------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| **standard**                                                                                         | Each module exposes a typed error per taxonomy node; cross-boundary conversion explicit. |
| **observed — MET.**                                                                                  | This is the exemplar in the feeders group for this section: four purpose-built           |
| exception subclasses, each with a distinct `exit_code`, constructed explicitly at the one place that |
| translates a raw `urllib` failure into a typed one (`client.py:92-116`). No bare `except Exception`  |
| anywhere in `core/client.py`.                                                                        |

## 3. No swallowing

**Observed — no violations found** in `core/`. `client.request()`'s retry loop (`:52-72`) either re-raises
immediately (client/auth errors, `:58-60`) or exhausts retries and raises the last captured exception
(`:70-72`) — never silently drops a failure. Plugin-layer code (86 files) was sampled, not exhaustively
read (per the time-box instruction) — spot-checked `plugins/` command handlers rely on the same
`AirbyteCliError` propagation up to `__main__.py`, no local swallowing observed in the sample.

## 4. Context on propagation

**Observed — met.** `ApiError` carries the structured `response_body` dict as a real attribute (`:15-18`),
not just interpolated into a message string — this is the "wrap with the operation + key inputs" rule
done as data, not text, which is stronger than every enrichment-script repo in this group.

## 5. External-endpoint surfacing (BLOCK-level)

**Observed — the closest to full compliance in the feeders group, one gap remains.** MET: HTTP status
code (`exc.code`, `:92` onward) and the response body (`body`, parsed JSON or raw text fallback,
`:94-97`) are both captured into the typed `ApiError`/`_RetryableError`. **NOT bounded** — `raw =
exc.read().decode("utf-8")` (`:93`) reads the full body with no length cap before it's stored on the
exception and could later be printed via `output.error()`; a pathological large error body would be
captured in full rather than truncated. **NOT captured**: correlation/rate-limit headers
(`x-request-id`, `retry-after`, an upstream job id) — `exc.headers` is available from
`urllib.error.HTTPError` but never read. Per the workspace BLOCK rule, the header gap is the more
significant miss; the unbounded-body gap is a hardening item.

## 6. Per-layer handling + surface map

| layer                                                    | handling + surface                                                                           |
| -------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| **CLI**                                                  | typed error → `output.error()` JSON to stderr → **stable exit code** (§5 of the spine doc) — |
| already matches the workspace base doc's CLI row exactly |

## 7. Conformance tests

**Observed — the strongest test coverage in the feeders group.** `tests/test_client.py` exercises the
retry logic and error-status branching directly (`unittest.mock` on `urllib.request.urlopen`); this
already covers "boundary mapping" and much of "external-call surfacing" per §7's conformance list. The
one gap: no test asserts the captured `response_body`/status pair is what a downstream caller (e.g. a
Dagster shell-out) would actually see via `output.error()`'s JSON shape end-to-end.

## Drift backlog (top items)

1. Capture `exc.headers` (correlation/rate-limit headers) into `ApiError`/`_RetryableError` — the one
   BLOCK-level gap remaining (§5).
2. Bound the response-body read (`client.py:93`) to a fixed length before storing it on the exception.
3. Add an end-to-end test asserting `output.error()`'s JSON shape for a captured `ApiError` (§7).
