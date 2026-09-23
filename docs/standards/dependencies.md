---
owner: data-pipeline team
last-reviewed: 2026-09-23
stability: draft
status: active
---

# Dependency Standards — airbyte-api-cli

> Inherits the workspace base: [../../../../docs/standards/dependencies.md](../../../../docs/standards/dependencies.md)
> (GitHub: https://github.com/mercurai/data-pipeline/blob/main/docs/standards/dependencies.md).
> This document records only this repo's layers, observed/standard rows and drift backlog.

## 1. Git-dependency pinning (BLOCK-level)

Not applicable — no git dependencies found in this repo.

## 2. Audit tooling

| ecosystem                                                                                               | tool                                               | observed                                                                       | standard |
| ------------------------------------------------------------------------------------------------------- | -------------------------------------------------- | ------------------------------------------------------------------------------ | -------- |
| Python                                                                                                  | `pip-audit`                                        | **zero-dependency by design** — `core/client.py` wraps stdlib `urllib.request` |
| directly rather than `requests`/`httpx` (`core/client.py:1`: "HTTP client wrapping urllib.request..."), |
| and no `requirements.txt`/`pyproject.toml`/`setup.py`/`setup.cfg` exists anywhere in this repo. This is |
| the **only** feeders repo where the absence of a manifest reflects a deliberate zero-dependency design  |
| choice rather than an oversight — the README states tests use "the Python standard library `unittest`   |
| module... No test dependencies" (README.md:765).                                                        | `pip-audit` is moot while the dependency set stays |
| empty; if `requests`/`httpx` or any third-party package is ever added, that is the trigger to add a     |
| manifest and wire `pip-audit` in the same PR (per §5)                                                   |

**CI snippet**: not applicable — no CI workflow file, and no ecosystem-audit tool needed while the
dependency set is empty.

## 3. License allowlist

Not applicable — no third-party runtime or test dependency exists to license-check.

## 4. Lockfile hygiene

Not applicable — no manifest, hence no lockfile; this is consistent (not a gap) given §2's
zero-dependency design.

## 5. New-dependency justification

|                                                                                                           | rule                                                                                      |
| --------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| **standard**                                                                                              | Any new dependency added to this repo carries a reuse-scan justification in the PR body — |
| "why not stdlib" specifically, given the repo's established zero-dependency precedent.                    |
| **observed**                                                                                              | No PR-body convention formally enforced, but the codebase's own design (stdlib `urllib`   |
| over `requests`) is itself evidence the precedent is already being followed in practice — this section is |
| about writing that precedent down so it survives a maintainer change.                                     |

## 6. Conformance

- [ ] No git dependency pins a branch — vacuously true.
- [ ] Audit tooling configured — not applicable while dependency set is empty; NOT MET the moment one is
      added without a manifest+audit-wiring PR (§2).
- [ ] License allowlist — not applicable (§3).
- [ ] Lockfile matches manifest — not applicable (§4).
- [ ] New-dependency justification — precedent exists in practice, not written down as policy (§5).

## Drift backlog (top items)

1. Write down the zero-dependency-by-design precedent explicitly (e.g. in `CONTRIBUTING.md` or this
   doc's §5) so a future PR adding `requests` doesn't happen without the accompanying manifest+audit
   wiring.
2. If/when a first third-party dependency is added, create `requirements.txt` (runtime) and
   `requirements-dev.txt` (test, still likely empty) in that same PR, per §5.
