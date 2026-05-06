# Execute Sula 0.17.0 agent-native project OS upgrade

## Metadata

- date: 2026-05-05
- kind: spec
- project: Sula
- workflow pack: operating-system
- workflow slot: design
- storage provider: local-fs
- execution mode: review-heavy
- design gate: complex-only
- plan gate: multi-step
- review policy: task-checkpoints

## Summary

Implementation spec for the Sula 0.17.0 upgrade described in `docs/reference/sula-0-17-0-agent-native-project-os-whitepaper.md`.

## Problem Statement

Sula already has durable memory, governed projections, workflow scaffolds, artifact routing, orchestration, automation, provider-backed artifact identity, and machine-readable CLI outputs. The remaining gap is agent-native access: external agents still need to know which files to read, which commands to run, and which writes are safe.

0.17.0 must provide a stable control surface that lets humans and agents recover project facts, rules, tasks, artifacts, verification requirements, and handoff state without giving agents arbitrary shell or direct write access to Sula-managed operating files.

## Goals And Non-goals

| Category | Details |
| --- | --- |
| Goals | Add an optional MCP-compatible entrypoint; expose read-only project and portfolio tools; expose controlled record tools; consolidate rules into a project policy view; improve PR/provider closeout evidence; add canary coverage for both software and non-software service projects. |
| Non-goals | Replace the CLI; make MCP a core dependency; open arbitrary shell or file-write access; write provider-native documents by default; automate project business systems such as n8n, POS, databases, or publishing platforms. |

## Constraints And Assumptions

- Preserve the split between centrally managed Sula operating files and project-owned business truth.
- Keep bootstrap dependency-light and compatible with the current Python baseline.
- Reuse existing CLI contracts and core functions before adding new state formats.
- Default tool behavior must be read-only. Write classes must be explicit and policy-gated.
- Sula-managed writes must be performed by Sula, not by external agents directly editing `.sula/`, `STATUS.md`, workflow records, or orchestration records.
- All machine-facing surfaces must return JSON-friendly envelopes.
- Existing profiles and canaries must keep working.

## Proposed Design

1. Add an optional MCP-compatible server entrypoint that resolves allowlisted project roots and delegates to existing Sula command/core behavior.
2. Introduce read-only tools first: `project.bootstrap`, `project.status`, `project.check`, `project.query`, `project.rules`, `artifact.locate`, `orchestration.tasks`, `portfolio.list`, and `portfolio.status`.
3. Add controlled write tools only after read-only behavior is stable: `report.create`, `workflow.scaffold`, `orchestration.intake`, `orchestration.close`, `artifact.register`, `artifact.materialize`, `artifact.refresh`, and `sync.dry_run`.
4. Consolidate policy output from manifest, profile, AI-agent instructions, workflow policy, artifact/document rules, approval categories, and verification commands.
5. Add a thin provider capability report rather than a broad dynamic provider schema layer.
6. Enhance PR closeout verification with structured CI and review state while avoiding full log fetching by default.
7. Preserve existing CLI, templates, report/check/doctor lifecycle, orchestration closeout, and artifact identity behavior.

## Data And Interface Changes

| Surface | Change | Compatibility Impact |
| --- | --- | --- |
| MCP-compatible server entrypoint | New optional integration surface that delegates to Sula commands/core functions | Compatible; CLI remains primary |
| Project bootstrap JSON | Stable summary of identity, status, handoff, rules, tasks, artifacts, providers, and allowed operations | Compatible; new read surface |
| Project rules JSON | Consolidated policy view for agents | Compatible; new read surface |
| Controlled write envelopes | Write tools return changed files, affected artifacts, audit evidence, and verification result | Compatible if routed through existing Sula write paths |
| `.sula/local/mcp-policy.json` | Machine-local allowlist and write-class policy | Local-only; not project truth |
| Provider capability report | Thin registry of available provider actions | Compatible; no provider write requirement |
| PR closeout adapter | Structured CI/review status fields | Compatible; strengthens verification |

## Risks And Open Questions

- MCP write tools can amplify mistakes if write classes are enabled too broadly.
- Policy view could become too broad if it tries to normalize every external tool at once.
- PR review-thread details may require GitHub APIs with permissions not always available.
- Provider capability naming must stay thin enough to avoid becoming a second plugin framework.
- Need to confirm the exact MCP transport/package choice while preserving dependency-light CLI behavior.

## Verification Plan

- Unit tests for project root allowlist, read-only no-write behavior, JSON envelopes, controlled write auditing, provider capability reports, and PR closeout states.
- Fixture canaries for Sula Core, a software-delivery project, a generic non-software service project, and a provider-backed Google Drive style project.
- Release checks:
  - `python3 scripts/sula.py check --project-root .`
  - `python3 scripts/sula.py doctor --project-root . --strict`
  - `python3 -m unittest discover -s tests -v`
