---
owner: data-pipeline team
last-reviewed: 2026-09-23
stability: draft
status: active
---

# Logging Standards — airbyte-api-cli

> Inherits the workspace base: [../../../../docs/standards/logging.md](../../../../docs/standards/logging.md)
> (GitHub: https://github.com/mercurai/data-pipeline/blob/main/docs/standards/logging.md).
> This document records only this repo's layers, observed/standard rows and drift backlog.
>
> Shares the [observability spine](./_observability.md) with [errors.md](./errors.md).

## 1. Structured, one canonical logger

|                                                                                                          | rule                                                                                    |
| -------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| **standard** (CLI, per the workspace base doc §6)                                                        | structured or plain to **stderr**, gated by                                             |
| `--log-level`; stdout stays machine-parseable.                                                           |
| **observed**                                                                                             | No `logging` module usage anywhere in this repo (`grep -rl getLogger` returns nothing). |
| `print()` is used exactly where it should be for a CLI: `output()` (`core/output.py:52-67`) writes the   |
| CLI's actual data product to **stdout**, and `error()` (`:69-76`) writes structured JSON to **stderr** — |
| this already matches the "stdout stays machine-parseable" half of the standard. What's missing is a      |
| `--log-level`-gated diagnostic channel distinct from the one error-JSON-on-failure path (e.g. verbose    |
| request/response tracing for debugging an API call), which doesn't exist today.                          |

## 2. Level semantics

**Observed:** no level concept — there is exactly one diagnostic output shape (the error JSON on
failure). Nothing corresponds to WARN/INFO/DEBUG. For a CLI this is a smaller gap than for a
long-running service (no request volume to triage by level), but a `--verbose` flag tracing outbound
requests would help debug the retry/backoff behavior in `core/client.py`.

## 3. Canonical fields

**Observed:** the error JSON (`core/output.py:69-76`) already carries `error_kind`-equivalent
(`error_type`) and `message`; missing `ts`, `trace_id`, `module`. `status` is present when available
(`:73-74`) — closer to the spine's base set than any other feeders repo.

## 4. Redaction (spine §4)

**Observed — met, and the strongest example in the group.** `AirbyteConfig.to_dict()`
(`core/config.py:104-110`) masks `token`/`client_secret`/`password` before they can reach any output
path, including the debug/dump commands that presumably use `to_dict()` (not exhaustively traced in this
pass — spot-checked the masking function itself, which is unconditional).

## 5. Sinks & sampling

**Observed:** stdout (data) / stderr (error JSON) split, no file/collector sink — correct for a CLI
invoked by another process (Dagster) that owns capturing/redirecting output itself.

## 6. Per-layer telemetry + surface map

| layer                                                                                   | logging / telemetry surface                                                                |
| --------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| **CLI**                                                                                 | structured JSON error → stderr; data → stdout; gated by nothing today (no `--log-level`) — |
| already matches the workspace base doc's CLI row's _shape_, missing only the level gate |

## 7. Conformance tests

**Observed:** `tests/test_output.py` tests the formatters (`format_json`/`format_table`/`format_compact`)
directly — real assertions on output shape, not a smoke screen. No test specifically asserts the
redaction behavior in `to_dict()` end-to-end through a CLI invocation (only `test_config.py`'s unit tests
on the config object itself were sampled) — worth confirming on next review whether a redaction-specific
test exists (see testing.md §1).

## Drift backlog (top items)

1. Add a `--log-level`/`--verbose` flag for request/response tracing during debugging (§1, §2).
2. Emit `ts`/`trace_id`/`module` on the existing error JSON once a trace id source is adopted
   (spine §1).
