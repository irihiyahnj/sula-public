# Release Sula 0.18.0 remembered agent routing

## Metadata

- date: 2026-05-06
- executor: Codex
- branch: main
- status: verified

## Scope

Version the current Sula source tree as `0.18.0` so adopted projects can immediately use remembered executor routing. The release adds `agent-routing configure`, allowing an operator to choose a local executor runner, CLI command, provider, model, workspace mode, and write-access policy once. Sula then reuses that route until the operator passes `--replace` or explicit new values.

This release is intentionally a Sula Core contract and configuration release. It does not add a mandatory DeepSeek, OpenAI, Claude, or Hermes SDK dependency. Local CLI wrappers and runner adapters remain responsible for their own model/API configuration.

## Risks

- A remembered executor command can mutate a copied workspace when `write_access = true`; projects should keep `workspace_mode = "copy"` unless they deliberately allow root mutation.
- Sula records the command and model/provider labels, but it cannot prove which model a third-party CLI wrapper actually uses internally.
- First-time setup in non-interactive environments must pass explicit flags because Sula cannot prompt without a TTY.

## Verification

- Final gate passed on 2026-05-06:
  - `python3 -m py_compile scripts/sula.py tests/test_sula.py`
  - `python3 -m unittest discover -s tests -v` (120 tests)
  - `python3 scripts/sula.py check --project-root . --json`
  - `python3 scripts/sula.py doctor --project-root . --strict --json`
  - `git diff --check`

## Publication

- Public repository: `https://github.com/irihiyahnj/sula-public.git`
- Public branch: `main`
- Public tag target: `v0.18.0`
- Launch descriptor: `site/sula.json` points `source_ref` to `v0.18.0`.

## Rollback

- Revert the `agent-routing configure` command, remembered-route tests, docs, and release metadata.
- Restore `VERSION`, `.sula/version.lock`, `site/sula.json`, and `site/launch/bootstrap.py` to the previous published `v0.17.0` source ref.

## Follow-up

- Add convenience examples for common Claude Code, Hermes, and custom DeepSeek executor wrapper commands after real-project usage confirms the stable command shapes.
- Consider adding a non-interactive `agent-routing configure --preset` layer only after repeated project setups show clear reusable patterns.
