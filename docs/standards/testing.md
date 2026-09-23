---
owner: data-pipeline team
last-reviewed: 2026-09-23
stability: draft
status: active
---

# Testing Standards — airbyte-api-cli

> Inherits the workspace base: [../../../../docs/standards/testing.md](../../../../docs/standards/testing.md)
> (GitHub: https://github.com/mercurai/data-pipeline/blob/main/docs/standards/testing.md).
> This document records only this repo's layers, observed/standard rows and drift backlog.

## 1. Framework & patterns

| layer                                                                                                  | test framework                                                               | observed                                                     | standard |
| ------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------- | ------------------------------------------------------------ | -------- |
| Python CLI (core)                                                                                      | stdlib `unittest` + `unittest.mock`                                          | `tests/test_client.py`,                                      |
| `test_auth.py`, `test_config.py`, `test_output.py`, `test_utils.py`, `test_registry.py`,               |
| `test_models.py` — 6,564 total lines across `tests/` (largest suite in the feeders group by far);      |
| README's own coverage table (README.md:781-786) states "HTTP request building, retry logic, auth token |
| flow, config priority, formatters, JSON arg resolution"                                                | already close to standard; no test-dependency                                |
| manifest exists (dependencies.md §2) even though `unittest`/`unittest.mock` are stdlib-only — worth    |
| confirming this stays true as the suite grows                                                          |
| Python CLI (plugins)                                                                                   | stdlib `unittest`                                                            | `tests/test_plugins/` — 16 files per the README's own table, |
| covering "command parsing, API call construction, model serialization, plugin registration" across 86  |
| plugin source files                                                                                    | keep 1:1 test-file-to-plugin-module coverage as new resource types are added |

## 2. Delete-bad-tests taxonomy

Sampled `tests/test_client.py`'s imports and structure (not the full 6,564-line suite, per the time-box
instruction): uses `unittest.mock.patch`/`MagicMock` on `urllib.request.urlopen` directly, asserting on
the resulting typed exception's attributes — this is behavior-testing, not mock-echo. No god-test or
mockery-spiral pattern observed in the sampled file. A full pass across all 132 test-adjacent files was
NOT performed this session (time-boxed) — flag for a dedicated follow-up review given the suite's size.

| category                 | file:line | disposition                                   |
| ------------------------ | --------- | --------------------------------------------- |
| (none flagged in sample) | —         | full-suite audit deferred — see drift backlog |

## 3. Mutation score thresholds

| language                                                                                           | tool     | min score                    | observed                             | notes    |
| -------------------------------------------------------------------------------------------------- | -------- | ---------------------------- | ------------------------------------ | -------- |
| Python                                                                                             | `mutmut` | (workspace: none configured) | **not installed** — confirmed absent | of every |
| feeders repo, this one has the test _base_ to make mutation testing immediately useful (real suite |
| already exists); propose `mutmut run` as the first workspace pilot                                 |

**CI snippet**: not applicable — no CI workflow file found in this repo (`find . -path
'*workflows*'` empty, confirmed alongside the other feeders repos).

## 4. Clock-seam mandate

| module                         | observed                                                                         | standard |
| ------------------------------ | -------------------------------------------------------------------------------- | -------- |
| `core/client.py`               | uses `time.sleep()` for retry backoff (`:63`, `:67`) — no wall-clock _read_ that |
| branches logic; not applicable | n/a                                                                              |

## 5. Loading / error / empty-state coverage

Not applicable in the UI sense (this is a CLI, not a GUI) — the closest analogs are: **error** state
(covered — `test_client.py` asserts typed-exception behavior); **empty** state (an API call returning an
empty list) — not confirmed covered in this sample, check `test_output.py`'s `format_table`/
`format_compact` handling of `[]` (both functions have an explicit empty-list branch in source,
`core/output.py:18-19,39-40` — worth a direct test if one doesn't exist).

## 6. Eval-coverage (LLM-facing features)

Not applicable — no LLM call in this repo.

## 7. End-to-end (E2E)

|                                                                                                           | rule                                                                               |
| --------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| **observed**                                                                                              | `tests/test_cli_integration.py` exists (file name suggests it drives `__main__.py` |
| end-to-end rather than unit-testing individual functions) — not read in full this session; if it invokes  |
| the real `main()` entry point with mocked HTTP at the `urlopen` boundary, that is close to this section's |
| standard (drives the real artifact's own dispatch logic) even without a live Airbyte instance. Confirm on |
| next review whether it asserts on persisted/observable state or is a boot-check only.                     |

**Command**: `python -m pytest tests/` (or `python -m unittest discover tests/`, given the framework is
stdlib `unittest`).

## 8. Stress / load

|                                                                                                   | rule                                                                      |
| ------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| **observed**                                                                                      | no stress exercises. The retry/backoff path (`_RETRY_DELAYS = [1, 2, 4]`, |
| `client.py:16`) is unit-tested for correctness but never load-tested against a real or wiremocked |
| Airbyte instance under sustained 5xx/timeout conditions.                                          |

## 9. Benchmarks

Not applicable — a CLI wrapper's performance is dominated by the remote Airbyte API's latency, not by
this codebase.

## 10. Bug-repro tests

| fix                                                                                                       | repro test       | observed failing first | disposition |
| --------------------------------------------------------------------------------------------------------- | ---------------- | ---------------------- | ----------- |
| `ConnectionsApi.update preserves status when omitted` (current HEAD commit message)                       | not confirmed in |
| this sample — check `tests/test_plugins/` for a matching test on the next review                          | unknown          | accepted               |
| pending confirmation — this repo's commit discipline (one-line, specific fix messages) suggests tests are |
| written per-fix, but this session did not verify it directly                                              |

## 11. Surface coverage

This repo's own surface **is** `endpoint-out` calls to the Airbyte public API — ~67 endpoints across 16
resource types per the README. No generated inventory or ledger exists.

| kind                                                                                                     | applies                                                           | disposition    |
| -------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- | -------------- |
| `endpoint-out`                                                                                           | yes — ~67 Airbyte API endpoints, one call site per plugin command | not applicable |
| today — no ledger seeded; this is the single highest-value target for the §11 adoption path in the whole |
| feeders group given the endpoint count is already enumerable from `plugins/`                             |
| `page`/`action`/`endpoint-in`                                                                            | no                                                                | not applicable |

Ledger path (not yet created): `tests/coverage.json`.

## 12. Conformance

- [ ] No test falls into a §2 category — sampled clean; full audit deferred (time-boxed).
- [ ] Mutation tooling configured — NOT MET, but this repo is the best-positioned candidate (§3).
- [ ] Clock seam — not applicable (§4).
- [ ] Loading/error/empty-state — error state covered; empty-state formatter behavior unconfirmed (§5).
- [ ] E2E — PARTIALLY MET, `test_cli_integration.py` exists but its depth wasn't confirmed this session
      (§7).
- [ ] Stress — NOT MET (§8).
- [ ] Benchmarks — not applicable (§9).
- [ ] Bug-repro tests — unconfirmed (§10).
- [ ] Surface inventory + ledger — NOT MET, though the endpoint list is directly derivable from
      `plugins/` (§11).

## Drift backlog (top items)

1. Confirm `tests/test_cli_integration.py`'s depth (real E2E vs. boot-check) on next review (§7).
2. Generate the `endpoint-out` inventory from `plugins/` and seed `tests/coverage.json` — highest-value
   §11 target in the feeders group (67 endpoints, already enumerable).
3. Add empty-list-response tests for `format_table`/`format_compact` if not already present (§5).
4. Pilot `mutmut` here first — this repo has the strongest existing suite to validate against (§3).
