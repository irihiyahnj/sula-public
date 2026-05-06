# Release Sula 0.18.11 supervised executor retry

## Metadata

- date: 2026-05-06
- executor: Codex
- branch: main
- status: verified

## Scope

Version the current Sula source tree as `0.18.11` so adopted projects receive
the supervised retry loop for low-cost executors under high-capability reviewer
control.

## Risks

- Failure classification is intentionally heuristic and should be tuned from
  real runner output.
- Sula passes reviewer feedback to runners, but project-local wrappers still
  need to respect the bounded packet and return structured JSON.
- The runner health score is descriptive, not a hard quality gate.

## Verification

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_sula.SulaCliTests.test_orchestration_review_feedback_feeds_executor_retry_and_health -v`
- `python3 -m py_compile scripts/sula.py tests/test_sula.py`

## Publication

- Public repository: `https://github.com/irihiyahnj/sula-public.git`
- Public branch: `main`
- Public tag target: `v0.18.11`
- Launch descriptor: `site/sula.json` points `source_ref` to `v0.18.11`.

## Rollback

- Restore `VERSION`, `.sula/version.lock`, `.sula/kernel.toml`,
  `site/sula.json`, `site/launch/bootstrap.py`, changelog, and release notes to
  `0.18.10` / `v0.18.10`.
- Revert supervised retry command and runner payload changes if local wrappers
  need a different contract shape.

## Follow-up

- Validate the protocol in a real Claude Code / DeepSeek Flash executor project.
- Tune failure classification and runner health after several real retry loops.
