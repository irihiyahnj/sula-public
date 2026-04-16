# Add machine JSON interfaces, artifact routing, portfolio registry, and Google Drive local-sync contracts

## Metadata

- date: 2026-04-12
- executor: Codex
- branch: codex/bootstrap-sula
- related commit(s): pending
- status: completed

## Background

Sula's project kernel could already adopt unknown repositories, persist kernel state, and answer local queries, but it still behaved mostly like a human CLI. That left a gap for real non-code client projects: external software could not reliably call Sula without scraping text, artifact creation had no formal slot-routing path, portfolio-level project registration was missing, and Drive-synced workspaces still had to masquerade as project types instead of adapters.

## Analysis

- A machine-readable CLI surface was required before chat tools, local agents, or future GUI layers could treat Sula as a control protocol.
- Artifact routing needed to attach to workflow packs instead of stack profiles so client-service and video-production projects could stay portable across storage providers.
- Google Drive needed to land as provider metadata on a storage adapter contract, not as a hard-coded core type, to preserve the future path for Feishu or other providers.
- Portfolio state needed to stay removable and local-first, so a simple JSON registry was preferable to a mandatory service dependency.

## Chosen Plan

- Add JSON envelopes to the core command surface where software integration matters.
- Extend the manifest with optional `workflow`, `storage`, and `portfolio` sections.
- Add `status`, `artifact`, and `portfolio` commands as first-class kernel operations.
- Persist artifact metadata under `.sula/artifacts/catalog.json`.
- Treat `google-drive` as a storage adapter in local-sync mode and document the contract explicitly.

## Execution

- added machine-readable `--json` output paths to `init`, `adopt`, `sync`, `doctor`, `remove`, `record new`, and `memory digest`
- added `status` for structured current-state summaries
- added `artifact create/register/locate` for workflow-routed files and artifact catalog updates
- added `portfolio register/list/status/query` for multi-project workspace registration and retrieval
- extended the manifest schema and example with optional `workflow`, `storage`, and `portfolio` sections
- recorded adapter and workflow contracts in `docs/reference/portfolio-adapter-workflow-contract.md`
- registered `google-drive` as a local-sync storage adapter rather than a project type

## Verification

- `python3 -m py_compile scripts/sula.py tests/test_sula.py`
- `python3 -m unittest discover -s tests -v`
- `python3 scripts/sula.py sync --project-root .`
- `python3 scripts/sula.py sync --project-root examples/okoktoto`
- `python3 scripts/sula.py doctor --project-root . --strict`
- `python3 scripts/sula.py doctor --project-root examples/okoktoto --strict`
- `python3 scripts/sula.py status --project-root . --json`

## Rollback

- revert the implementation commit that introduced the machine JSON, artifact, and portfolio commands
- remove optional manifest sections from adopted projects only if they were added incorrectly for a specific consumer
- delete `.sula/artifacts/catalog.json` and local portfolio registry files if the feature set is intentionally backed out

## Data Side-effects

- adopted projects gain `.sula/artifacts/catalog.json` on next sync or artifact operation
- portfolio registries may be created outside Git in user-selected local roots
- Drive-synced projects can now record provider metadata without introducing a remote dependency

## Follow-up

- validate the new workflow pack and storage adapter semantics against the first real Google Drive client-service workspace
- add richer workflow packs and provider adapters only after real usage proves the abstractions stable
- keep machine JSON envelopes stable enough for external-tool integrations

## Architecture Boundary Check

- highest rule impact: preserved; the new commands and manifest sections add removable operating metadata without promoting provider-specific storage details into project-owned business truth
