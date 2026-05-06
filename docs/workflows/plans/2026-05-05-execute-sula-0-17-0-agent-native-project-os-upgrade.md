# Execute Sula 0.17.0 agent-native project OS upgrade

## Metadata

- date: 2026-05-05
- kind: plan
- project: Sula
- workflow pack: operating-system
- workflow slot: design
- storage provider: local-fs
- document genre: proposal
- document bundle: problem-solution-workplan-raci

## Summary

Execution plan for implementing the Sula 0.17.0 agent-native project operating system upgrade from the whitepaper.

## Executive Summary

Sula 0.17.0 should turn the current file/CLI operating system into an optional agent-native control surface. The work should be delivered in reviewable slices: read-only MCP-compatible access first, then controlled Sula-managed writes, then policy view, portfolio summary, provider capability reporting, PR closeout strengthening, canaries, and release documentation.

## Objectives And Scope

| Item | Details |
| --- | --- |
| Business objective | Let any human or agent recover project context, rules, task state, evidence requirements, and handoff through stable Sula interfaces without depending on chat memory or direct file mutation. |
| In scope | MCP-compatible server entrypoint, read-only tools, controlled record tools, policy view, portfolio status, provider capability report, PR/CI/review closeout evidence, tests, canaries, docs, and release record. |
| Out of scope | Replacing CLI, making MCP mandatory, arbitrary shell execution, default provider-native writes, production database operations, or business-system automation. |

## Current State And Constraints

- Current version is 0.16.0 with workflow auto-loop, orchestration closeout checks, automation kernel, provider-backed artifacts, and Git-only launch descriptor.
- Existing canaries and adopted projects depend on CLI behavior, managed/project split, profile abstraction, and dependency-light bootstrap.
- Sula-managed writes must remain auditable and must not be bypassed by external agents.
- The first implementation must prefer stable JSON envelopes and fixture-backed tests over broad provider discovery.

## Proposed Approach

1. Build read-only access first: server entrypoint, allowlist resolver, bootstrap/status/rules/tasks/artifacts/portfolio tools, no-write tests.
2. Add controlled record writes through existing Sula commands and core functions: report, workflow scaffold, orchestration intake/close, artifact register/materialize/refresh, sync dry-run.
3. Consolidate project policy view and keep it profile-aware so software and service projects get different rule surfaces.
4. Add provider capability report and PR closeout structured status as bounded verification upgrades.
5. Prove behavior through canaries, docs, and release gates before tagging 0.17.0.

## Milestones And Work Plan

| Milestone | Timing | Owner | Done Definition |
| --- | --- | --- | --- |
| Whitepaper and task package | 2026-05-05 | Sula Core maintainers | Whitepaper, overview, spec, plan, review, and task intake exist in repo. |
| Phase 1 read-only surface | After planning approval | Sula Core maintainers | MCP-compatible entrypoint and read-only tools pass fixture tests with no file writes. |
| Phase 2 controlled writes | After Phase 1 acceptance | Sula Core maintainers | Controlled write tools route through Sula, return changed files/evidence, and pass dirty-worktree tests. |
| Phase 3 policy and portfolio | After Phase 2 acceptance | Sula Core maintainers | Project rules/bootstrap and portfolio status cover software and service canaries. |
| Phase 4 verification adapters | After Phase 3 acceptance | Sula Core maintainers | Provider capability and PR closeout structured checks pass fixtures. |
| Release readiness | After all implementation phases | Sula Core maintainers | `check`, `doctor --strict`, unit tests, and all canaries pass; release docs explain boundaries. |

## Task Package Closeout

| Task Package | Result | Evidence |
| --- | --- | --- |
| `mcp-readonly-surface` | completed | MCP tools/list/call/serve implemented; no-write and stdio tests passed |
| `project-policy-view` | completed | `project.bootstrap` and `project.rules` return stable policy payloads for software and service fixtures |
| `controlled-record-tools` | completed | policy-gated Sula-managed write wrappers and audit events implemented; controlled report test passed |
| `portfolio-control-surface` | completed | `portfolio.list` and `portfolio.status` implemented; multi-project fixture test passed |
| `provider-capability-report` | completed | CLI and MCP provider capability reports implemented for local-fs and Google Drive gaps |
| `pr-closeout-structured-checks` | completed | PR verification now reports CI/review summary and closeout state; remote PR fixture test passed |
| `non-software-canary` | completed | field-ops generic and client-service Drive canaries aligned with 0.17.0; all canaries passed |
| `release-docs-and-rollout` | completed | version metadata, launch descriptor, README/reference docs, changelog, release record, STATUS, and memory digest updated |

## Responsibility Matrix

| Work Package | Responsible R | Accountable A | Consulted C | Informed I |
| --- | --- | --- | --- | --- |
| Whitepaper and task package | Codex | Sula Core maintainers | Future implementers | Adopted project maintainers |
| Read-only control surface | Implementing agent | Sula Core maintainers | Hermes/Codex users | Adopted project maintainers |
| Controlled writes | Implementing agent | Sula Core maintainers | Security/release reviewers | Adopted project maintainers |
| Canaries and release | Implementing agent | Sula Core maintainers | Project owners | Sula consumers |

## Risks And Decisions

- Decide MCP implementation dependency/transport without making it required for CLI users.
- Keep `.sula/local/mcp-policy.json` local-only unless later 0.17.x work proves a manifest field is needed.
- Require explicit policy gates for write classes beyond read/record.
- Avoid service-project pollution from software-specific code rules.
- Treat provider write and runner tools as future strongly approved capabilities, not default 0.17.0 behavior.
