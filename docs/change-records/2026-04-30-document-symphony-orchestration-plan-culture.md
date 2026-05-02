# Document Symphony Orchestration Plan Culture

## Metadata

- date: 2026-04-30
- executor: Codex
- branch: unknown
- related commit(s): none
- status: drafted

## Background

Sula is evaluating whether to absorb OpenAI Symphony-style Codex orchestration as a major upgrade. The discussion identified high potential value, but also a clear boundary: Sula should absorb the portable orchestration model and not hardcode a single external tracker, runner, or implementation.

## Analysis

- Symphony-style orchestration can move Sula from a project operating system toward a project execution operating system.
- The completed capability needs durable planning culture so later AI sessions can execute from repository truth instead of chat history.
- The plan must preserve optional adoption, dependency-light Core, project-owned business truth, and explicit safety controls.

## Chosen Plan

- Add a durable reference plan for Symphony-style orchestration absorption.
- Add an execution plan under `docs/workflows/plans/` for future AI implementers.
- Update the documentation map so the new planning surface is discoverable.

## Execution

- Added `docs/reference/symphony-orchestration-absorption-plan.md`.
- Added `docs/workflows/plans/2026-04-30-symphony-orchestration-absorption-plan.md`.
- Updated `docs/README.md` with the workflow planning layer and reference link.

## Verification

- Documentation is source-first Markdown.
- No runtime orchestration behavior was enabled.
- No managed template behavior was changed.

## Rollback

- Remove the two new plan documents.
- Revert the `docs/README.md` documentation-map update.

## Data Side-effects

- None. This is a documentation-only planning change.

## Follow-up

- If implementation begins, start with manifest/schema contracts, local task source, dry-run runner, and run registry before any daemon or external tracker integration.

## Architecture Boundary Check

- highest rule impact: preserved. The documents explicitly keep Sula Core orchestration policy separate from project-owned task and business truth.

