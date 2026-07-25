# Release Sula 0.17.0 agent-native control surface

## Metadata

- date: 2026-05-05
- executor: Codex
- branch: main
- status: published

## Scope

Version the current Sula source tree as `0.17.0` so the agent-native project operating system control surface can roll forward as a coherent minor release. The release adds optional MCP-compatible access, read-only project and portfolio tools, controlled Sula-managed write tools, consolidated policy view, provider capability reporting, structured PR closeout evidence, and non-software service canary coverage.

## Risks

- MCP write tools could amplify mistakes if users enable broad write classes without a local policy review.
- MCP transport is intentionally dependency-light and minimal; richer host-specific integrations should layer on top rather than replace the CLI.
- Provider capability reporting is intentionally a thin report, not dynamic provider execution.
- Launch-facing metadata must stay aligned with the eventual public `v0.17.0` tag.

## Verification

- Final gate passed on 2026-05-05:
  - `python3 scripts/sula.py check --project-root .`
  - `python3 scripts/sula.py doctor --project-root . --strict`
  - `python3 -m unittest discover -s tests -v` (116 tests)
  - `python3 scripts/sula.py canary verify --project-root . --all`

## Publication

- Published through the clean public export strategy required by release readiness.
- Public repository: `https://github.com/irihiyahnj/sula-public.git`
- Public branch: `main`
- Public tag: `v0.17.0`
- Launch descriptor: `site/sula.json` points `source_ref` to `v0.17.0`.

## Rollback

- Revert the MCP control-surface implementation and restore `VERSION` plus `site/sula.json` to the previous published source ref.
- Keep the 0.17.0 whitepaper as a reference if the implementation needs to be re-cut into a later 0.17.x batch.

## Follow-up

- Add richer provider adapters when a real authenticated provider target is selected.
- Add host-specific MCP configuration examples for Hermes or other long-running agents after the minimal stdio surface is proven.
